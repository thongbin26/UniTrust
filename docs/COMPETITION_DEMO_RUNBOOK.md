# UniTrust competition runbook

## Before presentation

1. Connect power, disable sleep, and start at least two minutes early.
2. Run `.venv\Scripts\python scripts\competition_preflight.py` while ports
   are free.
3. Run `powershell -ExecutionPolicy Bypass -File scripts\start_demo.ps1`.
4. Wait for `http://127.0.0.1:8000/health` and
   `http://127.0.0.1:8501/_stcore/health` to return ready.
5. Open Home, Xác minh, Bằng chứng, and Dành cho bạn. OCR is optional:
   start its isolated runtime only with `UNITRUST_OCR_PYTHON` configured.
6. Copy the inputs from `COMPETITION_DEMO_INPUTS.md`; keep terminals hidden.

## Five-minute script

| Time | Page / action | Exact input / expected output | Say | Do not say |
|---|---|---|---|---|
| 0:00–0:30 | Home | Show slogan and three modes | “Sinh viên nhận tin từ nhiều kênh nhưng khó biết nguồn nào đang áp dụng.” | “Đây là chatbot.” |
| 0:30–1:35 | Verify text | Primary verified input; **Đã xác minh** | “UniTrust cấu trúc nội dung, tìm nguồn chính thức rồi đối chiếu action và deadline.” | “AI tự quyết đúng sai.” |
| 1:35–2:15 | Result | Show comparison and official source | “Kết luận luôn đi cùng bằng chứng chính thức.” | Internal IDs/enums. |
| 2:15–2:55 | Verify text | Primary controlled conflict (notice 1: REGISTER deadline changed from 18/09 to 25/09); **Có mâu thuẫn** | “Giả sử sinh viên nhận được một tin nhắn chuyển tiếp ghi hạn đăng ký là 25/09. UniTrust đối chiếu với deadline trong nguồn chính thức.” | “Đây là tin nhắn thật.” |
| 2:55–3:30 | Verify text | Primary insufficient; **Chưa đủ bằng chứng** | “Không đủ bằng chứng phù hợp không có nghĩa nội dung sai.” | “Đây là thông tin giả.” |
| 3:30–4:05 | For You | CNTT / K2026 profile | “Hồ sơ giúp nhóm nghĩa vụ có thể liên quan và phần còn chưa chắc. Trạng thái thời hạn được hiển thị minh bạch; dữ liệu demo hiện chưa có nghĩa vụ khớp hồ sơ còn hạn.” | Fabricated relevance or an open deadline. |
| 4:05–4:30 | Modes | Mention screenshot and URL | “Ảnh dùng OCR cục bộ khi sẵn sàng; URL là tùy chọn vì cần mạng.” | OCR accuracy claim. |
| 4:30–5:00 | Architecture / metrics | Show cheat sheet | “AI hỗ trợ tìm/đọc; nguồn chính thức và logic xác định tạo quyết định tin cậy.” | Independent 88.89% accuracy. |

## Fallbacks

| Failure | Action | Core demo impact |
|---|---|---|
| Internet unavailable | Skip live URL | None |
| OCR sidecar unavailable | Skip live screenshot | None |
| Cold start slow | Start early; health-check before judges arrive | None once ready |
| Streamlit reload | Refresh after backend health succeeds | Low |
| A case differs | Use listed backup; do not improvise a truth claim | Controlled |

## Shutdown

Press Ctrl+C once in the demo supervisor terminal. It stops only services it
started. Do not use broad process-kill commands.
