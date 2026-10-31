"""Reproducible C1/C2 pilot runner. Does not handle confidential reference keys."""
import argparse
import csv
import hashlib
import json
import random
import sys
from pathlib import Path
from servicediag_core import assess_case, read_jsonl, digest, load_contract, SCHEMA_FILE, OutputError

FILE_NAMES = {
    'C1': 'condition_C1_transcript_only.jsonl',
    'C2': 'condition_C2_and_C3_context.jsonl',
}


def append_jsonl(dest, record):
    with dest.open('a', encoding='utf-8') as file:
        file.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + '\n')
        file.flush()


def main():
    parser = argparse.ArgumentParser(description='ServiceDiag-AI C1/C2 research runner')
    parser.add_argument('--condition', required=True, choices=['C1','C2'])
    parser.add_argument('--input', type=Path, required=True)
    parser.add_argument('--output', type=Path, default=None)
    parser.add_argument('--dry-run', action='store_true', help='Validate locally; no API requests.')
    parser.add_argument('--confirm-pilot-run', action='store_true', help='Explicitly permit requests on the frozen 40 cases.')
    parser.add_argument('--development', action='store_true', help='Permit separate development examples only.')
    parser.add_argument('--model', default=None, help='Record exact requested model version; freeze before pilot.')
    parser.add_argument('--seed', type=int, default=20261017)
    args = parser.parse_args()
    if not args.dry_run and not args.confirm_pilot_run and not args.development:
        parser.error('No API calls without --confirm-pilot-run or --development.')
    if args.development and args.confirm_pilot_run:
        parser.error('Development and pilot modes cannot be combined.')
    if not args.development and args.input.name != FILE_NAMES[args.condition]:
        parser.error('Approved pilot requires the exact C1/C2 filename; confidential files are rejected.')
    if args.development and not args.input.name.startswith('dev_'):
        parser.error('Development files must begin with dev_.')
    cases = read_jsonl(args.input, args.condition)
    if args.confirm_pilot_run and len(cases) != 40:
        parser.error('Formal pilot must contain exactly 40 approved cases.')
    if args.confirm_pilot_run and {x['case_id'] for x in cases} != {f'SD-C{i:03d}' for i in range(1,41)}:
        parser.error('Formal pilot must contain SD-C001 through SD-C040 exactly.')
    print(f'Condition {args.condition}: {len(cases)} cases, unique IDs; valid schema / evidence isolation.')
    dataset_hash = digest(args.input.read_bytes())
    prompt_hash = digest(load_contract()[0].encode('utf-8'))
    schema_hash = digest(SCHEMA_FILE.read_bytes())
    print(f'Input SHA-256: {dataset_hash}')
    if args.dry_run:
        print('DRY RUN COMPLETE. Zero API calls; no diagnosis outputs generated.')
        return
    if args.output is None:
        parser.error('--output required for a real run.')
    args.output = args.output.resolve()
    if args.output == args.input.resolve():
        parser.error('Output cannot overwrite the input dataset.')
    args.output.parent.mkdir(parents=True, exist_ok=True)
    existing = {}
    if args.output.exists():
        for line in args.output.read_text(encoding='utf-8').splitlines():
            if line.strip():
                item = json.loads(line)
                if item.get('condition') != args.condition:
                    parser.error('Output contains data from another condition.')
                aud = item.get('audit', {})
                batch = item.get('batch_audit', {})
                if (aud.get('prompt_sha256') != prompt_hash or aud.get('schema_sha256') != schema_hash or batch.get('dataset_sha256') != dataset_hash or batch.get('seed') != args.seed):
                    parser.error('Resume provenance conflict: different dataset, prompt, schema or random seed. Choose a new output.')
                if args.model is not None and aud.get('model_requested') != args.model:
                    parser.error('Resume model conflict; choose a new output filename.')
                if item['case_id'] in existing:
                    parser.error('Duplicate case ID already in output; stop and inspect results.')
                existing[item['case_id']] = item
        print(f'Resume: {len(existing)} saved outputs; successfully processed cases will be skipped.')
    # Randomisation changes processing order only. Each request remains independent.
    random.Random(args.seed).shuffle(cases)
    failures = []
    for index, case in enumerate(cases, 1):
        cid = case['case_id']
        if cid in existing:
            if existing[cid].get('audit',{}).get('case_sha256') != digest(json.dumps(case, sort_keys=True, ensure_ascii=False, separators=(',',':')).encode('utf-8')):
                parser.error(f'Resume provenance conflict for {cid}; use a new output filename.')
            continue
        try:
            result = assess_case(case, args.condition, model=args.model)
            result['batch_audit'] = {'dataset_sha256': dataset_hash, 'seed': args.seed,
                                     'input_filename': args.input.name,
                                     'study_phase': 'development' if args.development else 'pilot'}
            append_jsonl(args.output, result)
            print(f'[{index}/{len(cases)}] {cid}: saved validated {args.condition} output')
        except Exception as exc:
            # Do not automatically treat schema errors as a valid scientific diagnosis.
            entry = {'case_id': cid, 'condition': args.condition, 'error_type': type(exc).__name__}
            # Only expose local validation errors, not raw API responses or credentials.
            if isinstance(exc, OutputError):
                entry['validation_reason'] = str(exc)[:900]
            failures.append(entry)
            detail = f': {exc}' if isinstance(exc, OutputError) else ''
            print(f'[{index}/{len(cases)}] {cid}: FAILED ({type(exc).__name__}){detail}', file=sys.stderr)
    if failures:
        failed_path = args.output.with_name(args.output.stem + '_failures.json')
        failed_path.write_text(json.dumps(failures, indent=2), encoding='utf-8')
        print(f'{len(failures)} cases failed validation or execution; see {failed_path}. No missing results were imputed.')
        sys.exit(1)
    print(f'Run finished: {len(cases)} case IDs covered by existing/saved records.')

if __name__ == '__main__':
    main()
