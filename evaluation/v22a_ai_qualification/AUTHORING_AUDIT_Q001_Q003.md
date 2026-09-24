# Authoring audit and human-review trail — Q001–Q003

This is an authoring record for draft candidates only. It is not frozen gold,
provider output, or benchmark evaluation.

## Human adjudication

| Candidate | Human decision | Active revision |
|---|---|---|
| Q001 | ACCEPT after minor audience correction | Yes |
| Q002 | HUMAN_ACCEPTED (Revision 3) | Yes |
| Q003 | ACCEPT with metadata cleanup | Yes |

## Q001 second pass

- Every gold field occurs in the input: yes.
- Source-only gold facts: none.
- Claim boundary and grounded spans: one claim; exact.
- Audience now includes the explicit “nếu muốn đổi lớp” applicability condition.
- Date range convention: retain the raw range and normalize to its terminal date
  in the scalar deadline field.

## Q002 rejected revision trail

Revision 1 parent: INV-24-o1  
Revision 1 status: REJECTED_BY_HUMAN_REVIEW

Revision 1 reasons:

1. The paraphrase narrowed the parent object from the full policy set
   (miễn, giảm học phí; trợ cấp xã hội; hỗ trợ chi phí học tập) to only
   miễn, giảm học phí.
2. It omitted the reviewed submission-hour constraint of 07h30–11h00,
   Monday through Friday, by replacing “Từ nay đến hết ngày 10/9/2026” with
   “chậm nhất ngày 10/9/2026”.

Revision 2 parent: INV-13-o4  
Revision 2 status: REJECTED_BY_HUMAN_REVIEW

Revision 2 reasons:

1. The audience could be interpreted more broadly than the parent subgroup of
   students who need to supplement certificates.
2. The audience gold overlapped the action and document/object text, creating
   unnecessary field-ownership ambiguity.

## Q002 replacement second pass

Parent: INV-26-o2

- Audience scope is a standalone class/cohort population, not an action-defined
  subgroup.
- Every gold field is explicit in the replacement input: yes.
- Parent meaning: the ĐGRL dossier submission obligation is preserved.
- Material parent constraints dropped: none; the late-submission consequence is
  present in the candidate exception field.
- Source-only gold facts: none.
- Claim boundary and grounded spans: one claim; exact.
- Ontology fit: submit action, full deadline, and exception are all supported.
- Authoring audit status: PASS.
- Human status: HUMAN_ACCEPTED (Revision 3).

## Q003 second pass

- Synthetic provenance is explicit; there is no DUT source reference.
- CCCD, K26, action, and missing-year date are all grounded in the input.
- The date remains unresolved; no year was inferred.
- Claim boundary and grounded spans: one claim; exact.

## Duplicate and overlap audit

- Exact duplicate within Q001–Q003: 0
- Normalized duplicate within Q001–Q003: 0
- Near-duplicate concern: 0
- Historical exact normalized-input overlap across available evaluation/v22a and
  evaluation/step18h JSONL files: 0

## Locked annotation rule

Audience answers “who must perform the action?” (Ai phải làm?). It contains
the actor or obligated population only; it must not absorb the action, object,
required documents, deadline, destination, or unrelated context. Action,
object_hint, required_documents, location, deadline, and exceptions remain
separate grounded fields. Gold must be derivable from the final benchmark input;
source-only gold is prohibited.

Actor-defining qualifications may remain in audience when they materially
identify who must perform the target action. For example, an enrolment condition
can define the eligible population without absorbing a different target action.
