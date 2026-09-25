# Q004–Q006 human review packet

Candidates only — not frozen benchmark gold.

## Q004
**Provenance:** SOURCE_DERIVED
**Difficulty:** MEDIUM
**Source / parent:** INV-3-o1
**Input:**
> Sinh viên tham gia học kỳ hè cần thực hiện khảo sát lớp học phần học kỳ hè trong thời gian từ 08/09/2026 đến 20/09/2026.

**Expected claim count:** 1
**Claim 1:**
- Audience: Sinh viên tham gia học kỳ hè
- Action: thực hiện (other)
- Object: khảo sát lớp học phần học kỳ hè
- Deadline: 08/09/2026 đến 20/09/2026 → 2026-09-20
- Amount: None
- Documents: []
- Location: None
- Exceptions: []
**Grounded spans:**
- audience: 0:28 → Sinh viên tham gia học kỳ hè
- action: 33:42 → thực hiện
- object_hint: 43:74 → khảo sát lớp học phần học kỳ hè
- deadline_raw: 94:119 → 08/09/2026 đến 20/09/2026
**Why this candidate exists:** Revised source-derived summer-term survey obligation with the reviewed action semantics.
**Authoring audit:** PASS
**Audit note:** Revision preserves the reviewed thực hiện action; audience remains actor-only and all gold fields are explicit.
**Human review:** HUMAN_ACCEPTED
**Reviewer decision:** [ ] ACCEPT  [ ] EDIT  [ ] REJECT
**Human notes:**

## Q005
**Provenance:** CONTROLLED_PARAPHRASE
**Difficulty:** HARD
**Source / parent:** INV-26-o1
**Input:**
> Sinh viên khóa 2021, khóa 2022 và các lớp trễ tiến độ có đăng ký học phần trong học kỳ II năm học 2025-2026 cần tự đánh giá kết quả rèn luyện học kỳ II năm học 2025-2026 từ 15h00 ngày 16/7/2026 đến hết ngày 17/7/2026.

**Expected claim count:** 1
**Claim 1:**
- Audience: Sinh viên khóa 2021, khóa 2022 và các lớp trễ tiến độ có đăng ký học phần trong học kỳ II năm học 2025-2026
- Action: tự đánh giá (update)
- Object: kết quả rèn luyện học kỳ II năm học 2025-2026
- Deadline: 15h00 ngày 16/7/2026 đến hết ngày 17/7/2026 → 2026-07-17
- Amount: None
- Documents: []
- Location: None
- Exceptions: []
**Grounded spans:**
- audience: 0:107 → Sinh viên khóa 2021, khóa 2022 và các lớp trễ tiến độ có đăng ký học phần trong học kỳ II năm học 2025-2026
- action: 112:123 → tự đánh giá
- object_hint: 124:169 → kết quả rèn luyện học kỳ II năm học 2025-2026
- deadline_raw: 173:216 → 15h00 ngày 16/7/2026 đến hết ngày 17/7/2026
**Why this candidate exists:** Controlled paraphrase retaining the reviewed eligibility condition and timed date range.
**Authoring audit:** PASS
**Audit note:** Audience answers who must act; its enrolment condition is not the target update action. The raw deadline retains its time and range.
**Human review:** HUMAN_ACCEPTED
**Reviewer decision:** [ ] ACCEPT  [ ] EDIT  [ ] REJECT
**Human notes:**

## Q006
**Provenance:** SOURCE_DERIVED
**Difficulty:** HARD
**Source / parent:** INV-5-o1
**Input:**
> Đăng ký phúc khảo điểm thi cuối kỳ hè trên hệ thống thông tin sinh viên từ 23/8/2026 đến 25/8/2026; không áp dụng phúc khảo cho học phần thi vấn đáp và không nộp đơn.

**Expected claim count:** 1
**Claim 1:**
- Audience: None
- Action: Đăng ký (register)
- Object: phúc khảo điểm thi cuối kỳ hè trên hệ thống thông tin sinh viên
- Deadline: 23/8/2026 đến 25/8/2026 → 2026-08-25
- Amount: None
- Documents: []
- Location: None
- Exceptions: ['không áp dụng phúc khảo cho học phần thi vấn đáp', 'không nộp đơn']
**Grounded spans:**
- action: 0:7 → Đăng ký
- object_hint: 8:71 → phúc khảo điểm thi cuối kỳ hè trên hệ thống thông tin sinh viên
- deadline_raw: 75:98 → 23/8/2026 đến 25/8/2026
- exception_1: 100:148 → không áp dụng phúc khảo cho học phần thi vấn đáp
- exception_2: 152:165 → không nộp đơn
**Why this candidate exists:** Source-derived registration obligation retaining both reviewed exclusions.
**Authoring audit:** PASS
**Audit note:** No audience is invented; both exclusions remain explicit, grounded, and attached to the same obligation.
**Human review:** HUMAN_ACCEPTED
**Reviewer decision:** [ ] ACCEPT  [ ] EDIT  [ ] REJECT
**Human notes:**
