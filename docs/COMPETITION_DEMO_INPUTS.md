# Competition demo inputs

Copy these locally before presenting. “Controlled” means a deliberately altered
message derived from reviewed official DUT evidence; it is not a collected
student message.

## Demo case table

| Role | Exact input | Expected result | Official basis | Demo status |
|---|---|---|---|---|
| Primary VERIFIED | `Sinh viên khóa 2022 ngành CNTT ký tên theo danh sách lớp và nộp 01 ảnh thẻ 2x3 trước 16h00 ngày 26/06/2026.` | **Đã xác minh** | Notice 13; reviewed SUBMIT deadline `2026-06-26`. | Live demo |
| Backup VERIFIED | `Sinh viên K26 cần đăng ký kiểm tra xếp lớp đầu vào trước ngày 18/09/2026.` | **Đã xác minh** | Notice 1; reviewed REGISTER deadline `2026-09-18`. | Live demo |
| Primary CONTROLLED CONFLICT | `Sinh viên K26 cần đăng ký kiểm tra xếp lớp đầu vào trước ngày 25/09/2026.` | **Có mâu thuẫn** | Notice 1 / obligation `o1`; same REGISTER action, deadline deliberately changed from `18/09/2026` to `25/09/2026`. | **CONTROLLED DEMONSTRATION — NOT REAL USER MESSAGE** |
| Backup CONTROLLED CONFLICT | `Hãy thực hiện khảo sát lớp học phần hè trước ngày 27/09/2026.` | **Có mâu thuẫn** | Notice 3 / obligation `o1`; same OTHER action, deadline deliberately changed from `20/09/2026` to `27/09/2026`. | **CONTROLLED DEMONSTRATION — NOT REAL USER MESSAGE** |
| Primary INSUFFICIENT | `Sinh viên phải nộp phí giữ xe 200.000 đồng mỗi tháng.` | **Chưa đủ bằng chứng** | No applicable official payment field. | **INSUFFICIENT_EVIDENCE does NOT mean false.** |
| Backup INSUFFICIENT | `Đại học yêu cầu sinh viên đi học mặc áo màu đỏ.` | **Chưa đủ bằng chứng** | Unsupported claim field. | **INSUFFICIENT_EVIDENCE does NOT mean false.** |

## Presenter framing for controlled conflicts

For the primary controlled case, say: “Giả sử sinh viên nhận được một tin
nhắn chuyển tiếp ghi hạn đăng ký là 25/09. UniTrust sẽ không dựa vào việc câu
này có vẻ hợp lý, mà đối chiếu với deadline trong nguồn chính thức.” Do not
describe either controlled case as collected real-world misinformation.

## For You profile

Use **Khoa Công nghệ Thông tin / Công nghệ thông tin / K2026**. It surfaces
the reviewed placement-test obligation from notice 1 as applicable. As of the
competition checkpoint date, the accepted corpus has no applicable obligation
with an open deadline: surfaced deadlines are expired or absent. Present the
status transparently; do not claim a currently open notice. Do not claim
faculty ownership beyond the catalog's displayed confidence.
