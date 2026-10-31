# ServiceDiag-AI: research code and pilot data

*Research materials accompanying the Stage 1 proposal (October 2026).*

This repository contains code, inputs and saved outputs from a pilot using 40 fictional customer-service cases. Under C1, the model received a transcript only. Under C2, it received the same transcript plus policy, workflow and system records. The code checks the structure of diagnoses, source IDs and intervention rules, and records outputs that fail validation. Two human reviewers subsequently examined valid C2 diagnoses (C3); this was not a third AI condition.

## Repository contents

- `servicediag_core.py` — prompt and schema loading, input and output checks, and model calls.
- `run_experiment.py` — runs the C1 and C2 assessments and controls API use.
- `diagnostic_schema_v1.json`, `diagnostic_prompt_v1.txt` — the instructions and required output structure.
- `pilot_inputs/` — the 40 fictional cases under C1 and C2, without reference labels.
- `frozen_pilot_outputs/` — 40 valid C1 outputs, 36 valid C2 outputs and four C2 failure records.
- `development_examples/`, `tests/` — development examples and 11 automated tests.
- `reproduce_public.py` — offline checks of file hashes, output structure, result counts and failed cases.
- `docs/prompt_amendment_v1.2.md` — records the prompt change between the initial run and the completed pilot. The manuscript and supplement are submitted separately.

## Run the offline checks

From the repository directory with Python 3.10+:

```bash
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
python run_experiment.py --condition C1 --input pilot_inputs/condition_C1_transcript_only.jsonl --dry-run
python run_experiment.py --condition C2 --input pilot_inputs/condition_C2_and_C3_context.jsonl --dry-run
python reproduce_public.py
```

These commands do not make API requests. `reproduce_public.py` checks the saved records and reports output-validity counts. It cannot calculate classification accuracy or reviewer agreement without the separate reference labels and review data.

## Optional model run (uses the API)

Supply `OPENAI_API_KEY` through a local environment variable; never commit your `.env`. For example:

```bash
python run_experiment.py --condition C1 --input development_examples/dev_C1.jsonl --development --output results/dev_c1_new.jsonl
```

Keep any new model responses separate from the saved pilot outputs. The hash of the full prompt, including the schema added by `load_contract()`, matches the stored pilot records. Later calls may produce different answers even with the same settings. See `PROVENANCE_AND_LIMITATIONS.md` for details.

## Pilot findings and limits

C1 produced 40 valid outputs. C2 produced 36 valid outputs and four failed mixed-cause diagnoses. Against separate condition-specific reference classifications, 29/36 matched the C1 reference (80.6%) and 28/36 matched the C2 reference (77.8%). Across all 40 C2 attempts, 28 were valid and matched the reference (70%). These figures are not a causal comparison of evidence conditions. Two reviewers assessed valid C2 outputs without seeing reference labels. The pilot did not test whether auditing improves decisions or observe organisational outcomes.

## Sharing and anonymity

The repository excludes scenario reference classifications and private human-review records. Those data are needed to reproduce the reported accuracy and reviewer-agreement results. The research files are intended for anonymous review; see `ETHICS_AND_DATA.md` for data-sharing limits.

## Licence

No open-source licence has been approved. See `LICENSE_PENDING.md`.

## Technical notes

See `PROVENANCE_AND_LIMITATIONS.md` for the recorded prompt, model settings and reproducibility limits.
