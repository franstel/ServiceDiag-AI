# Prompt revision record: v1.1 to v1.2

## Initial run

The first C1 attempt under v1.1 produced 19 valid outputs and 21 validation failures. Twenty failures concerned the required `INVESTIGATE` action target; one concerned missing causal evidence for a specific attribution. These were output-validation failures rather than verified diagnoses.

## Change to the prompt

Version 1.2 clarified the existing output requirements, particularly the `action_code`/`target` mapping and the need to cite causal evidence. The validator, schema, underlying cases and classification definitions were not relaxed or changed as part of this amendment.

After this change, the full set of 40 cases was run again under v1.2 for both C1 and C2. The saved v1.2 outputs and remaining failures are included in `frozen_pilot_outputs/`. The source file remains named `diagnostic_prompt_v1.txt` because that is the filename used by the code; its contents identify version 1.2.

## Interpretation

The amendment followed observed failures in the initial run, so v1.2 was not fixed before the first attempt. The completed pilot is exploratory. Results from different prompt versions should not be pooled as a single run. The initial v1.1 records are retained separately and are not included in this public repository.

The offline checks can be run using the commands in `README.md`. New API calls may produce different results from the stored outputs.
