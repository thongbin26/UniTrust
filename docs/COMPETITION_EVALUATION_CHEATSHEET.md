# Competition evaluation cheat sheet

## Main slide

- **Cross-obligation safety:** 0 false conflicts on N=7 controlled safety
  stress cases.
- **Retrieval:** curated source-derived diagnostic N=18, Hit@1 88.89%,
  Hit@3 100%, MRR 0.9444.
- **Extraction:** action 18/18; deadline 12/12 on the same curated diagnostic.
- **Unsupported same-set diagnostic:** 9/9 safely insufficient, 0 false
  VERIFIED, 0 false CONFLICT.
- **Warmed local text verification:** N=54, p50 25.78 ms, p95 30.33 ms;
  this is not production latency.

## Technical / Q&A

The same-set post-fix comparison changed source-derived outcomes from 11/18
VERIFIED, 5 false CONFLICT, 2 insufficient to 16/18 VERIFIED, 0 false
CONFLICT, 2 insufficient. Say: “Trên cùng bộ chẩn đoán, năm false conflict đã
được loại bỏ sau hai sửa lỗi an toàn xác định; không có regression mới.”

## Do not claim

- “88.89% accuracy in the real world.”
- Scam detection, 100% OCR accuracy, measured temporal accuracy, amount
  extraction accuracy, universal URL coverage, or production latency.
- Independent evaluation or generalization from the same-set comparison.

## Short Q&A

**AI ở đâu?** E5 hỗ trợ truy hồi ngữ nghĩa; PaddleOCR đọc ảnh khi sidecar cục
bộ sẵn sàng. Chuẩn hóa, applicability, đối chiếu và verdict là logic xác định.

**Điểm mới là gì?** Quy trình tích hợp nguồn chính thức, version, claim-level
verification, personalization và abstention an toàn cho thông tin đại học.

**Tại sao không dùng chatbot?** Chatbot không tự bảo đảm nguồn hiện hành,
khả năng áp dụng hay phát hiện mâu thuẫn theo trường; UniTrust hiển thị bằng
chứng chính thức.

**Dữ liệu lấy ở đâu?** Pilot DUT hiện có 41 notices/current versions, 10
reviewed notices và 18 reviewed obligations.

**Đã đánh giá thế nào?** Step13 là baseline lịch sử; Step18H gồm retrieval
N=18, safety N=7, unsupported N=9, extraction và latency cục bộ.

**Tại sao benchmark nhỏ/synthetic?** Đây là pilot có nhãn reviewed; synthetic
deadline mutations chỉ kiểm tra conflict có kiểm soát, không phải tin nhắn thật.

**Không tìm thấy bằng chứng thì sao?** Hệ thống trả “Chưa đủ bằng chứng”,
không kết luận nội dung sai.

**Có phát hiện lừa đảo không?** Không. CONFLICT không đồng nghĩa lừa đảo.

**Có áp dụng trường khác không?** Kiến trúc có thể mở rộng, dữ liệu hiện là
pilot DUT.

**Hạn chế/bước tiếp theo?** Mở rộng reviewed corpus, temporal transitions,
OCR evaluation, và giảm abstention top-1/same-action ambiguity an toàn.
