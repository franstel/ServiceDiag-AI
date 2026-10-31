#!/usr/bin/env python3
"""Offline replay of VALIDATED-output accounting, not case-level gold-key scoring."""
from __future__ import annotations
import collections, hashlib, json
from pathlib import Path
from servicediag_core import load_contract, read_jsonl, validate_diagnosis, digest, SCHEMA_FILE
ROOT=Path(__file__).resolve().parent
DATA={"C1":"condition_C1_transcript_only.jsonl","C2":"condition_C2_and_C3_context.jsonl"}
EXPECTED={"C1":40,"C2":36}
HISTORICAL_PROMPT_HASH="148a413d37b7040d4621bb5c00b1a4cd0306928d1597be66b2c3e2534a86d6ba"

def main():
    report={"conditions":{},"frozen_prompt_sha256":HISTORICAL_PROMPT_HASH}
    schema_hash=digest(SCHEMA_FILE.read_bytes());prompt,_=load_contract();prompt_hash=digest(prompt.encode("utf-8"))
    report.update({"packaged_prompt_sha256":prompt_hash,"prompt_hashes_match":prompt_hash==HISTORICAL_PROMPT_HASH,"schema_sha256":schema_hash})
    for condition,filename in DATA.items():
        input_path=ROOT/'pilot_inputs'/filename
        input_cases=read_jsonl(input_path,condition)
        input_hash=digest(input_path.read_bytes())
        cases={c['case_id']:c for c in input_cases}
        responses=[json.loads(line) for line in (ROOT/'frozen_pilot_outputs'/f'{condition}_results_v12.jsonl').read_text(encoding='utf-8').splitlines() if line.strip()]
        seen=set()
        for r in responses:
            cid=r['case_id'];assert cid in cases and cid not in seen,(condition,cid);seen.add(cid)
            assert r['condition']==condition and r['status']=='success'
            assert r['audit']['schema_sha256']==schema_hash
            assert r['audit']['prompt_sha256']==HISTORICAL_PROMPT_HASH
            assert r['batch_audit']['dataset_sha256']==input_hash
            assert r['audit']['case_sha256']==digest(json.dumps(cases[cid],ensure_ascii=False,sort_keys=True,separators=(',',':')).encode('utf-8'))
            validate_diagnosis(r['diagnosis'],cases[cid],condition)
        assert len(responses)==EXPECTED[condition]
        report['conditions'][condition]={"inputs":len(cases),"validated_outputs":len(responses),"input_sha256":input_hash,"validated_output_contracts":len(seen)}
    failures=json.loads((ROOT/'frozen_pilot_outputs'/'C2_results_v12_failures.json').read_text(encoding='utf-8'))
    fail_ids={f['case_id'] for f in failures};success_ids={json.loads(line)['case_id'] for line in (ROOT/'frozen_pilot_outputs'/'C2_results_v12.jsonl').read_text(encoding='utf-8').splitlines() if line.strip()}
    expected_ids={f'SD-C{i:03d}' for i in range(1,41)}
    assert len(fail_ids)==4 and not fail_ids.intersection(success_ids) and fail_ids|success_ids==expected_ids
    report['c2_failures']={"n":len(failures),"case_ids":sorted(fail_ids),"all_mixed_action_rule":all('MIX requires employee and organisational intervention categories.' in f.get('validation_reason','') for f in failures)}
    report['warning']='Reference-key accuracy and reviewer agreement cannot be independently recomputed without private reference data.'
    print(json.dumps(report,indent=2,ensure_ascii=False))
    if not report['prompt_hashes_match']:
        print('WARNING: archived outputs and available amended prompt have different SHA-256 hashes; exact historical rerun not verified.')
    return report
if __name__=='__main__':main()
