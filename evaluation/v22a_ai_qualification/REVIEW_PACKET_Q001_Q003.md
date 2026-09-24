# Q001–Q003 human review packet

Candidates only — not frozen benchmark gold.

## Q001
**Provenance:** SOURCE_DERIVED
**Difficulty:** MEDIUM
**Source / parent:** INV-1-o1
**Input:**
> Sinh viên đã được xếp lớp theo phương thức 1 hoặc 2, nếu muốn đổi lớp thì đăng ký kiểm tra xếp lớp đầu vào tại Khu hành chính 1 cửa, khu A, từ 14/9/2026 đến 18/9/2026.

**Expected claim count:** 1
**Claim 1:**
- Audience: Sinh viên đã được xếp lớp theo phương thức 1 hoặc 2, nếu muốn đổi lớp
- Action: đăng ký (register)
- Object: kiểm tra xếp lớp đầu vào
- Deadline: 14/9/2026 đến 18/9/2026 → 2026-09-18
- Amount: None
- Documents: []
- Location: Khu hành chính 1 cửa, khu A
- Exceptions: []
**Grounded spans:**
- audience: 0:69 → Sinh viên đã được xếp lớp theo phương thức 1 hoặc 2, nếu muốn đổi lớp
- action: 74:81 → đăng ký
- object_hint: 82:106 → kiểm tra xếp lớp đầu vào
- deadline_raw: 143:166 → 14/9/2026 đến 18/9/2026
- location: 111:138 → Khu hành chính 1 cửa, khu A
**Why this candidate exists:** Direct reconstruction of the reviewed registration obligation; no payment or document claim.
**Authoring audit:** PASS
**Audit note:** Human review accepted after adding the explicit đổi lớp applicability condition to audience.
**Human review:** ACCEPT
**Reviewer decision:** [ ] ACCEPT  [ ] EDIT  [ ] REJECT
**Human notes:**

## Q002
**Provenance:** CONTROLLED_PARAPHRASE
**Difficulty:** HARD
**Source / parent:** INV-26-o2
**Input:**
> Tất cả các lớp khóa 2021, khóa 2022 và các lớp trễ tiến độ phải nộp hồ sơ ĐGRL HK2/2025-2026 về Khoa trước ngày 30/07/2026. Nếu nộp hồ sơ trễ, Nhà trường có thể hoãn xét học bổng khuyến khích học tập và trừ điểm thi đua khen thưởng.

**Expected claim count:** 1
**Claim 1:**
- Audience: Tất cả các lớp khóa 2021, khóa 2022 và các lớp trễ tiến độ
- Action: nộp (submit)
- Object: hồ sơ ĐGRL HK2/2025-2026 về Khoa
- Deadline: 30/07/2026 → 2026-07-30
- Amount: None
- Documents: []
- Location: None
- Exceptions: ['Nếu nộp hồ sơ trễ, Nhà trường có thể hoãn xét học bổng khuyến khích học tập và trừ điểm thi đua khen thưởng.']
**Grounded spans:**
- audience: 0:58 → Tất cả các lớp khóa 2021, khóa 2022 và các lớp trễ tiến độ
- action: 64:67 → nộp
- object_hint: 68:100 → hồ sơ ĐGRL HK2/2025-2026 về Khoa
- deadline_raw: 112:122 → 30/07/2026
- exception: 124:232 → Nếu nộp hồ sơ trễ, Nhà trường có thể hoãn xét học bổng khuyến khích học tập và trừ điểm thi đua khen thưởng.
**Why this candidate exists:** Paraphrase of the reviewed ĐGRL dossier obligation, retaining its deadline and stated late-submission consequence.
**Authoring audit:** PASS
**Audit note:** Fresh second pass: audience is a standalone population, every gold field is explicit, and the material consequence is retained.
**Human review:** ACCEPT
**Reviewer decision:** [ ] ACCEPT  [ ] EDIT  [ ] REJECT
**Human notes:**

## Q003
**Provenance:** CONTROLLED_SYNTHETIC
**Difficulty:** HARD
**Source / parent:** None (synthetic)
**Input:**
> Bạn K26 nhớ nộp CCCD trước ngày 18/09 nhé.

**Expected claim count:** 1
**Claim 1:**
- Audience: K26
- Action: nộp (submit)
- Object: None
- Deadline: 18/09 → None
- Amount: None
- Documents: ['CCCD']
- Location: None
- Exceptions: []
**Grounded spans:**
- audience: 4:7 → K26
- action: 12:15 → nộp
- deadline_raw: 32:37 → 18/09
- required_document: 16:20 → CCCD
**Why this candidate exists:** Deliberate synthetic CCCD/missing-year safety case; it is not a DUT notice.
**Authoring audit:** PASS
**Audit note:** Synthetic provenance is explicit; the missing year remains unresolved and every gold field occurs in the input.
**Human review:** ACCEPT
**Reviewer decision:** [ ] ACCEPT  [ ] EDIT  [ ] REJECT
**Human notes:**
