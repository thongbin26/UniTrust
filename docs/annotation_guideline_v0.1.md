# UniTrust Obligation Annotation Guideline v0.1

## Principle

Annotate only what the official notice explicitly supports.

Do not use outside knowledge.
Do not guess missing values.
Do not use an LLM to create ground-truth labels.

## 1. Obligation splitting

Create a separate obligation when there is a materially different:

- action,
- audience,
- deadline,
- amount,
- or instruction.

Do not split merely because a sentence is long.

## 2. Audience

Record only explicitly stated audience conditions.

Supported profile dimensions:

- faculty
- major
- cohort
- program

If the notice says "all students",
set `applies_to_all_students=true`.

Do not infer an audience from your knowledge of the university.

## 3. Action

Write a concise normalized action.

Examples:

- đăng ký kiểm tra tiếng Anh
- nộp học phí
- nộp hồ sơ
- tham dự buổi hướng dẫn

Choose the closest ActionType.

## 4. Deadline

Keep the original text in `raw_text`.

Normalized format:

Date:
YYYY-MM-DD

Datetime:
YYYY-MM-DDTHH:MM:SS+07:00

Never invent missing date components.

If the deadline cannot be normalized safely:

normalized = null
precision = unknown

## 5. Amount

Normalize VND to integer dong.

450.000 đồng -> 450000

Keep the original wording in `raw_text`.

Do not infer an amount not explicitly stated.

## 6. Location

Copy only an explicitly stated location.

Do not infer the building/room from university knowledge.

## 7. Required documents

Each required document is a separate item.

Example:

- CCCD
- đơn đăng ký
- biên lai học phí

## 8. Exceptions

Record only explicit exceptions, exemptions,
special cases, or conditional rules.

## 9. Evidence

Every material annotated value should have
at least one EvidenceSpan whenever possible.

Evidence text must be copied exactly from raw_text.

Do not paraphrase evidence.

## 10. Temporal relations

Only annotate temporal relations when there
is evidence that one notice:

- amends
- supersedes
- duplicates
- or is directly related to another notice.

Do not infer supersession merely because
two notices discuss a similar topic.

Synthetic temporal histories must never be
presented as real historical relations.

## 11. Uncertainty

If uncertain:

- leave normalized fields null where allowed;
- add an annotation note;
- request a second annotator review.

Do not force a label.