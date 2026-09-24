# V2.2A Q001-Q006 provider qualification policy

`HUMAN_APPROVED — PRE-REGISTERED BEFORE REAL Q001-Q006 EVALUATION`

At approval time, `REAL Q001-Q006 PROVIDER RESULTS HAD NOT BEEN OBSERVED` and
`REAL PROVIDER REQUESTS EXECUTED: 0`.

The qualification harness is `HUMAN_ACCEPTED`. This policy applies only to
the accepted Q001-Q006 batch and the existing Gemini adapter contract.

## Evaluated scope

The current contract evaluates claim count, audience, normalized action,
normalized deadline, normalized amount when present, required documents,
structured-output validity, grounding, and invented-year safety.

It does **not** qualify `object_hint`, `location`, `exceptions`, or
provider-supplied spans. A positive state must therefore be described only as
`QUALIFIED_FOR_EVALUATED_FIELDS_ONLY`.

## Required-document semantics

The annotation guideline says each required document is a separate item but
does not make list order meaningful. The evaluator compares documents as an
exact normalized multiset: case and whitespace differences, and item order,
do not matter; duplicate occurrences remain counted.

## Decision states

### `QUALIFIED_FOR_EVALUATED_FIELDS_ONLY`

Only when all six samples execute successfully; adapter/invalid-output,
grounding, invented-year, and invalid-action counts are zero; claim structure
matches; and every applicable supported gold field is correct.

### `MEASURED_REQUIRES_HUMAN_REVIEW`

The run completed without a blocking adapter/safety error, but has one or more
ordinary structural or supported-field mismatches. It is not qualification.

### `QUALIFICATION_BLOCKED`

The run cannot validly complete because it has an adapter/provider failure,
invalid output, grounding violation, invented-year violation, invalid action,
configuration failure, or otherwise incomplete execution. No automatic retry.

## Runtime boundary

No result from this policy authorizes merging provider output into UniTrust's
student runtime. That remains a separate human gate.
