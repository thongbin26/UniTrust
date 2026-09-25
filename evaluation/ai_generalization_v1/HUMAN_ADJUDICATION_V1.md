# AI Generalization V1 — Human Adjudication

This document records an offline human review of the 31 initially unreviewed
records. It is evaluation evidence, not runtime annotation or provider output.

## Outcome

- Existing accepted records: 18
- Edited and accepted records: 17
- Rejected records: 14
- Accepted records: 35
- Accepted obligation claims: 43 (records can contain multiple obligations)

Accepted edits: AGV1-011, AGV1-012, AGV1-023, AGV1-024, AGV1-025,
AGV1-027, AGV1-028, AGV1-034, AGV1-038, AGV1-039, AGV1-040, AGV1-041,
AGV1-042, AGV1-046, AGV1-047, AGV1-048, AGV1-049.

Rejected: AGV1-004, AGV1-006, AGV1-007, AGV1-008, AGV1-009, AGV1-010,
AGV1-017, AGV1-018, AGV1-026, AGV1-031, AGV1-035, AGV1-043, AGV1-044,
AGV1-045.

## Annotation rules applied

- Every accepted field has an exact source substring and validated offsets.
- Audience is the actor required to act, not the action, object, document,
  deadline, destination, or unrelated content.
- Event and schedule times, and starts of a permitted window, are not
  deadlines.
- Administrative actions, descriptive participation, eligibility thresholds,
  and submission destinations are not substituted for a student obligation.
- AIDA's `40.000 Yên/suất` is retained as a non-comparable raw amount because
  the current amount contract is VND-only. TAIKISHA's `1.300.000 đồng/tháng`
  is an income threshold, not scholarship value.

## Analysis finding

Meaningful non-deadline event/schedule time appears in nine reviewed records:
AGV1-011, AGV1-012, AGV1-018, AGV1-024, AGV1-028, AGV1-040, AGV1-046,
AGV1-047, and AGV1-048. This is a future schema-review finding only; no
`event_time` field was added here.

## Measurement caveat

Metrics operate on HUMAN_ACCEPTED claims only. Rejected records remain in the
dataset as human-reviewed negative/error-analysis examples and are excluded
from accepted gold and metrics. The deterministic baseline is a before-provider
measurement; this review neither calls a provider nor authorizes runtime AI.
