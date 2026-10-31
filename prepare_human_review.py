"""Construct blinded C3 review rows from preserved C2 outputs.

Never opens design keys. Human reviewers should save a NEW filled copy of the CSV,
not edit C2 outputs or overwrite the source file.
"""
import argparse
import csv
import json
from pathlib import Path

HEADERS = [
    'case_id', 'ai_classification', 'ai_uncertainty_level', 'ai_evidence_sufficiency',
    'ai_rationale', 'ai_causal_source_ids', 'ai_actions',
    'human_classification_EMP_ORG_MIX_UNE', 'human_evidence_sufficiency',
    'human_uncertainty_level', 'human_causal_source_ids',
    'human_recommended_actions', 'human_rationale', 'human_reviewer_id', 'review_date',
]

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--c2-results', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    args=p.parse_args()
    if args.output.exists():
        p.error('Output already exists; would overwrite prior human ratings.')
    rows=[]; seen=set()
    for i,line in enumerate(args.c2_results.read_text(encoding='utf-8').splitlines(),1):
        if not line.strip(): continue
        r=json.loads(line)
        if r.get('condition')!='C2' or r.get('status')!='success':
            p.error(f'Line {i} is not a valid C2 success result.')
        case_id=r['case_id']
        if case_id in seen: p.error(f'Duplicate: {case_id}')
        seen.add(case_id)
        d=r['diagnosis']['diagnosis']; acts=r['diagnosis']['recommended_interventions']
        rows.append({
            'case_id':case_id,
            'ai_classification':d['classification'],
            'ai_uncertainty_level':d['uncertainty_level'],
            'ai_evidence_sufficiency':d['evidence_sufficiency'],
            'ai_rationale':d['rationale'],
            'ai_causal_source_ids':';'.join(e['source_id'] for e in d['causal_evidence']),
            'ai_actions':';'.join(e['action_code'] for e in acts),
        })
    args.output.parent.mkdir(parents=True,exist_ok=True)
    with args.output.open('w',encoding='utf-8-sig',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=HEADERS);writer.writeheader();writer.writerows(sorted(rows,key=lambda x:x['case_id']))
    print(f'Prepared {len(rows)} C3 human-review rows: {args.output}')

if __name__=='__main__': main()
