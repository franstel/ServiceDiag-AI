# Pilot records and reproducibility limits

**Pilot:** 40 synthetic cases; C1 transcript only (40 validated responses); C2 transcript + organisational context (36 validated responses, four validation failures). The C3 component was an independent, reference-blinded **audit** of C2 outputs; it was not a third experimental treatment.

**Design and interpretation:** The underlying cause stipulated by scenario authors differs from the conclusion justified by evidence disclosed to assessors. C1 and C2 have condition-specific reference standards and cannot be interpreted as a simple causal treatment comparison.

**Prompt amendment:** A first run under an earlier prompt produced validation failures; the prompt was clarified and all 40 cases were rerun for each condition under v1.2. This is post-first-run adjustment, not prespecified at the outset. See `docs/prompt_amendment_v1.2.md`.

**Prompt hashes:** The v1.2 prompt text file alone has SHA-256 `91ae95411f8d5c7ed54ff00a266a9d4357628a5f4c7c36c973337bf7b928bc1f`. However, `servicediag_core.load_contract()` appends the JSON schema as executable prompt instructions. This **effective full prompt** hashes to `148a413d37b7040d4621bb5c00b1a4cd0306928d1597be66b2c3e2534a86d6ba`, which exactly matches the hash recorded in both C1 and C2 frozen output logs. The schema also matches, as do the recorded `max_output_tokens=3000` and the patched runner's `MAX_OUTPUT_TOKENS=3000`. The packaged prompt and stored output hashes agree. New API responses may differ, even under the same settings.

**Reference data:** The shared files do not include condition-specific reference labels or the raw reviewer ratings. The public code checks output validity, but the reported classification accuracy and reviewer agreement cannot be recalculated without those separate records. Release of these data requires authorisation.

**Model:** gpt-4o-mini, model-returned identifier gpt-4o-mini-2024-07-18, as recorded in frozen outputs. A new model call need not yield exactly the historical content even with the same nominal model or temperature. API access incurs cost.
