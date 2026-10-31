import copy
import json
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace as NS

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from servicediag_core import (
    InputError, OutputError, read_jsonl, validate_case, validate_diagnosis,
    assess_case, load_contract,
)

BASE = Path(__file__).resolve().parents[1]
C1 = read_jsonl(BASE/'development_examples'/'dev_C1.jsonl', 'C1')
C2 = read_jsonl(BASE/'development_examples'/'dev_C2.jsonl', 'C2')


def valid_emp(case_id='SD-C901'):
    return {
        'case_id': case_id,
        'service_problem': {'code':'P05', 'summary':'Employee did not complete the request.', 'evidence_turn_ids':['T01','T02']},
        'diagnosis': {
            'classification':'EMP', 'rationale':'Employee reports not saving the requested change.',
            'causal_evidence':[{'source_id':'T02','supported_claim':'Employee forgot to save the extension.'}],
            'alternative_explanations':['System failure not established.'], 'missing_information': [],
            'evidence_sufficiency':'adequate', 'uncertainty_level':'moderate',
        },
        'recommended_interventions':[{'action_code':'COACHING','target':'employee','rationale':'Check request completion.','evidence_ids':['T02']}],
    }


class FakeCompletions:
    def __init__(self, payload):
        self.payload = payload
        self.calls=[]
    def create(self, **kwargs):
        self.calls.append(kwargs)
        return NS(
            id='offline-fake-id', model=kwargs['model'],
            choices=[NS(message=NS(content=json.dumps(self.payload)), finish_reason='stop')],
            usage=NS(prompt_tokens=10,completion_tokens=10,total_tokens=20),
        )


class TestDiagnosticContract(unittest.TestCase):
    def test_development_inputs_valid(self):
        self.assertEqual(len(C1),2)
        self.assertEqual(len(C2),2)
        self.assertEqual(len(validate_case(C2[0],'C2')),4)

    def test_c1_rejects_organisational_evidence(self):
        with self.assertRaises(InputError): validate_case(C2[0], 'C1')

    def test_c2_requires_organisational_evidence(self):
        with self.assertRaises(InputError): validate_case(C1[0], 'C2')

    def test_rejects_extra_answer_leak_field(self):
        c=copy.deepcopy(C1[0]);c['true_cause']='EMP'
        with self.assertRaises(InputError): validate_case(c, 'C1')

    def test_valid_diagnosis(self):
        validate_diagnosis(valid_emp(),C1[0],'C1')

    def test_rejects_fake_citation(self):
        d=valid_emp();d['diagnosis']['causal_evidence'][0]['source_id']='E01'
        with self.assertRaises(OutputError):validate_diagnosis(d,C1[0],'C1')

    def test_rejects_mismatched_case_id(self):
        with self.assertRaises(OutputError):validate_diagnosis(valid_emp('SD-C902'),C1[0],'C1')

    def test_une_requires_high_uncertainty(self):
        d=valid_emp();d['diagnosis']['classification']='UNE';d['diagnosis']['uncertainty_level']='moderate';d['diagnosis']['evidence_sufficiency']='insufficient';d['recommended_interventions']=[{'action_code':'INVESTIGATE','target':'investigation','rationale':'Review logs','evidence_ids':['T02']}]
        with self.assertRaises(OutputError):validate_diagnosis(d,C1[0],'C1')

    def test_wrong_intervention_target(self):
        d=valid_emp();d['recommended_interventions'][0]['target']='organisation'
        with self.assertRaises(OutputError):validate_diagnosis(d,C1[0],'C1')

    def test_api_call_is_isolated_and_consistent(self):
        fake=FakeCompletions(valid_emp());client=NS(chat=NS(completions=fake))
        out=assess_case(C1[0],'C1',client=client,model='offline-test-model')
        self.assertEqual(out['status'],'success')
        self.assertEqual(out['diagnosis']['diagnosis']['classification'],'EMP')
        self.assertEqual(fake.calls[0]['temperature'],0)
        self.assertEqual(fake.calls[0]['response_format'],{'type':'json_object'})
        self.assertEqual(len(fake.calls[0]['messages']),2)
        self.assertNotIn('E01',fake.calls[0]['messages'][1]['content'])

    def test_same_prompt_in_c1_c2(self):
        prompt,_=load_contract(); self.assertIn('Assign exactly ONE',prompt)

if __name__=='__main__':unittest.main()
