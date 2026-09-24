# Semantic fidelity audit — Q004–Q006

Q004, Q005, and Q006 are HUMAN_ACCEPTED.

## Q004 rejected revision history

- Parent: INV-3-o1.
- Previous input: Sinh viên tham gia học kỳ hè cần hoàn thành khảo sát lớp học phần học kỳ hè trong thời gian từ 08/09/2026 đến 20/09/2026.
- Previous action: hoàn thành.
- Status: REJECTED_BY_HUMAN_REVIEW.
- Reason: ACTION_SEMANTIC_FIDELITY. The reviewed parent uses thực hiện khảo sát;
  hoàn thành introduces a stronger completion requirement.

## Q004 revised candidate — INV-3-o1

- audience_preserved: YES — the actor remains “Sinh viên tham gia học kỳ hè”.
- action_semantics_preserved: YES — the lexical action is now “thực hiện”.
- material_constraints_preserved: YES — survey action and bounded date range are retained.
- action_audience_entanglement: NO.
- document_audience_entanglement: NO; no document field exists.
- source_only_gold_facts: NO.
- claim boundary: one survey obligation.
- ontology fit: other represents the reviewed thực hiện action.
- human status: HUMAN_ACCEPTED.

## Q005 — INV-26-o1

- audience_preserved: YES — cohort, delayed-progress status, and enrolled-course condition are retained.
- material_constraints_preserved: YES — the full timed range remains in deadline_raw and the terminal date follows the precommitted scalar range convention.
- action_audience_entanglement: NO — the audience enrolment condition is distinct from the target tự đánh giá action.
- document_audience_entanglement: NO; no document field exists.
- source_only_gold_facts: NO.
- claim boundary: one self-evaluation obligation.
- ontology fit: update represents the reviewed self-evaluation action.
- human status: HUMAN_ACCEPTED. The enrolment clause defines the actor population;
  it is not the target tự đánh giá action.

## Q006 — INV-5-o1

- audience_preserved: YES — no audience is asserted because the reviewed parent has none.
- material_constraints_preserved: YES — registration channel/date range and both reviewed exclusions are retained.
- action_audience_entanglement: NO; audience is null.
- document_audience_entanglement: NO; no document field exists.
- source_only_gold_facts: NO.
- claim boundary: one regrade-registration obligation with exclusions.
- ontology fit: register represents the reviewed action.
- human status: HUMAN_ACCEPTED. Null audience is retained because the authored
  input contains no explicit actor.
