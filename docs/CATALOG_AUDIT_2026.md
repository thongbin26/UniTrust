# Audit catalog khoa/ngành DUT 2026

Ngày audit: 20/09/2026. Phạm vi là dữ liệu public chính thức; không dùng search snippet làm bằng chứng cuối. Đây là audit catalog, không thay đổi verification, retrieval, temporal resolver, actionability, annotations hay benchmark.

## Kết luận

- Cơ cấu hiện hành có 9 khoa chuyên môn, hiệu lực từ hội nghị công bố quyết định ngày 20/08/2026.
- Danh mục tuyển sinh 2026 được reconcile thành 49 ngành/chuyên ngành/chương trình. Con số 49 được thông báo chính thức ngày 25/08/2026.
- Audit ownership hiện có: **1 VERIFIED, 44 PROVISIONAL, 4 UNVERIFIED**.
- Con số 49 ở cấp trường không đồng nghĩa 49 quan hệ ngành → khoa đã được xác minh.
- Migration table bên dưới chưa đầy đủ.

## Nguồn chính

| Mã | Nguồn | Ngày công bố | Hiệu lực | Vai trò |
|---|---|---:|---:|---|
| `org_restructure_2026` | [Thông báo kiện toàn tổ chức](https://dut.udn.vn/Tintuc/Tintuc/id/12201) | 22/08/2026 | 20/08/2026 | Xác nhận 9 khoa; không xác nhận ownership |
| `current_directory_2026` | [Danh bạ DUT](https://dut.udn.vn/Danhba/id/53) | Không nêu | Không nêu | Xác nhận tên khoa hiện hành |
| `program_inventory_2026` | [Ngành và chỉ tiêu tuyển sinh 2026](https://tuyensinh.dut.udn.vn/nganh-va-chi-tieu-tuyen-sinh) | Không nêu | Năm 2026 | Danh mục 49; nhóm lĩnh vực không phải khoa |
| `k2026_confirmation` | [DUT chào đón K2026](https://dut.udn.vn/TrangNCKH/Thongbao/id/12208) | 25/08/2026 | 25/08/2026 | Xác nhận 49, 7 chương trình tài năng, 4 chương trình mới |
| `thermal_current_faculty_2026` | [Khoa Cơ khí Giao thông và Năng lượng](https://dut.udn.vn/khoackgt) | 05/09/2026 | Sau 20/08/2026 | Bằng chứng trực tiếp cho Kỹ thuật nhiệt |
| `pre_restructure_ownership_2020` | [Danh sách chương trình năm 2020](https://dut.udn.vn/Tuyensinh2020/Gioithieu/id/3990) | 15/06/2020 | Trước tái cơ cấu | Lịch sử ownership, không override nguồn mới |
| `cntt_2026_pre_restructure` | [Thông tin tuyển sinh CNTT 2026](https://dut.udn.vn/Tintuc/Thongbao/id/11804) | 11/03/2026 | Trước tái cơ cấu | Tên/mã và ownership cũ của nhóm CNTT |

`project_owner_dsai` là provenance nội bộ không có URL và không phải nguồn chính thức.

## Cơ cấu 9 khoa

1. Khoa Điện tử và Trí tuệ nhân tạo
2. Khoa Cơ khí Giao thông và Năng lượng
3. Khoa Hóa, Môi trường và Khoa học Sự sống
4. Khoa Xây dựng
5. Khoa Điện
6. Khoa Cơ khí
7. Khoa Công nghệ Thông tin
8. Khoa Quản lý Dự án và Công nghiệp
9. Khoa Kiến trúc

## Bảng mapping 49 chương trình

| # | Chương trình | Khoa hiện dùng trong catalog | Trạng thái |
|---:|---|---|---|
| 1 | Công nghệ thông tin | Khoa Công nghệ Thông tin | PROVISIONAL |
| 2 | Công nghệ thông tin (ngoại ngữ Nhật) | Khoa Công nghệ Thông tin | PROVISIONAL |
| 3 | Công nghệ thông tin, chuyên ngành Khoa học dữ liệu và Trí tuệ nhân tạo | Khoa Điện tử và Trí tuệ nhân tạo | PROVISIONAL |
| 4 | Kỹ sư tài năng Công nghệ thông tin (định hướng DSAI) | Chưa xác định khoa | UNVERIFIED |
| 5 | Kỹ thuật máy tính | Khoa Điện tử và Trí tuệ nhân tạo | PROVISIONAL |
| 6 | Công nghệ thông tin, chuyên ngành An toàn thông tin trên không gian số | Khoa Công nghệ Thông tin | PROVISIONAL |
| 7 | Công nghệ sinh học | Khoa Hóa, Môi trường và Khoa học Sự sống | PROVISIONAL |
| 8 | Công nghệ sinh học Y Dược | Khoa Hóa, Môi trường và Khoa học Sự sống | PROVISIONAL |
| 9 | Công nghệ kỹ thuật vật liệu xây dựng | Khoa Xây dựng | PROVISIONAL |
| 10 | Công nghệ chế tạo máy | Khoa Cơ khí | PROVISIONAL |
| 11 | Quản lý công nghiệp | Khoa Quản lý Dự án và Công nghiệp | PROVISIONAL |
| 12 | Công nghệ dầu khí và khai thác dầu | Khoa Hóa, Môi trường và Khoa học Sự sống | PROVISIONAL |
| 13 | Kỹ thuật cơ khí - Cơ khí động lực | Khoa Cơ khí Giao thông và Năng lượng | PROVISIONAL |
| 14 | PFIEV | Chưa xác định khoa | UNVERIFIED |
| 15 | Kỹ thuật phương tiện đường sắt tốc độ cao | Khoa Cơ khí Giao thông và Năng lượng | PROVISIONAL |
| 16 | Kỹ thuật cơ điện tử | Khoa Cơ khí | PROVISIONAL |
| 17 | Kỹ sư tài năng Kỹ thuật cơ điện tử | Khoa Cơ khí | PROVISIONAL |
| 18 | Kỹ thuật nhiệt | Khoa Cơ khí Giao thông và Năng lượng | VERIFIED |
| 19 | Kỹ thuật nhiệt - Quản lý năng lượng | Khoa Cơ khí Giao thông và Năng lượng | PROVISIONAL |
| 20 | Kỹ thuật tàu thủy | Khoa Cơ khí Giao thông và Năng lượng | PROVISIONAL |
| 21 | Kỹ thuật điện | Khoa Điện | PROVISIONAL |
| 22 | Kỹ sư tài năng Kỹ thuật điện | Khoa Điện | PROVISIONAL |
| 23 | Kỹ thuật điện tử - viễn thông | Khoa Điện tử và Trí tuệ nhân tạo | PROVISIONAL |
| 24 | Kỹ sư tài năng Kỹ thuật điện tử - viễn thông | Khoa Điện tử và Trí tuệ nhân tạo | PROVISIONAL |
| 25 | Vi điện tử - thiết kế vi mạch | Khoa Điện tử và Trí tuệ nhân tạo | PROVISIONAL |
| 26 | Kỹ thuật điều khiển và tự động hóa | Khoa Điện | PROVISIONAL |
| 27 | Kỹ sư tài năng Kỹ thuật điều khiển và tự động hóa | Khoa Điện | PROVISIONAL |
| 28 | Kỹ thuật hóa học | Khoa Hóa, Môi trường và Khoa học Sự sống | PROVISIONAL |
| 29 | Kỹ thuật môi trường | Khoa Hóa, Môi trường và Khoa học Sự sống | PROVISIONAL |
| 30 | Kỹ thuật hệ thống công nghiệp | Khoa Cơ khí Giao thông và Năng lượng | PROVISIONAL |
| 31 | Kỹ thuật cơ khí - Cơ khí hàng không | Khoa Cơ khí | PROVISIONAL |
| 32 | Kỹ thuật ô tô | Khoa Cơ khí Giao thông và Năng lượng | PROVISIONAL |
| 33 | Kỹ sư tài năng Kỹ thuật ô tô | Khoa Cơ khí Giao thông và Năng lượng | PROVISIONAL |
| 34 | Chương trình tiên tiến Việt - Mỹ Điện tử viễn thông | Chưa xác định khoa | UNVERIFIED |
| 35 | Chương trình tiên tiến Việt - Mỹ Hệ thống nhúng và IoT | Chưa xác định khoa | UNVERIFIED |
| 36 | Cơ khí hàng không (hợp tác doanh nghiệp, tiếng Anh) | Khoa Cơ khí | PROVISIONAL |
| 37 | Công nghệ thực phẩm | Khoa Hóa, Môi trường và Khoa học Sự sống | PROVISIONAL |
| 38 | Kiến trúc | Khoa Kiến trúc | PROVISIONAL |
| 39 | Kỹ thuật xây dựng - Xây dựng dân dụng & Công nghiệp | Khoa Xây dựng | PROVISIONAL |
| 40 | Kỹ thuật xây dựng - Tin học xây dựng | Khoa Xây dựng | PROVISIONAL |
| 41 | Kỹ thuật và quản lý xây dựng đô thị thông minh | Khoa Xây dựng | PROVISIONAL |
| 42 | Mô hình thông tin và trí tuệ nhân tạo trong xây dựng | Khoa Xây dựng | PROVISIONAL |
| 43 | Kỹ sư tài năng Kỹ thuật xây dựng | Khoa Xây dựng | PROVISIONAL |
| 44 | Kỹ thuật xây dựng công trình thủy | Khoa Xây dựng | PROVISIONAL |
| 45 | Kỹ thuật xây dựng công trình giao thông | Khoa Xây dựng | PROVISIONAL |
| 46 | Xây dựng đường sắt tốc độ cao và đường sắt đô thị | Khoa Xây dựng | PROVISIONAL |
| 47 | Kinh tế xây dựng | Khoa Quản lý Dự án và Công nghiệp | PROVISIONAL |
| 48 | Kỹ thuật cơ sở hạ tầng | Khoa Xây dựng | PROVISIONAL |
| 49 | Quản lý tài nguyên và môi trường | Khoa Hóa, Môi trường và Khoa học Sự sống | PROVISIONAL |

## Migration audit subset

| Program | Pre-restructure faculty | Current faculty | Old source | New source | Effective date | Status |
|---|---|---|---|---|---|---|
| CNTT, chuyên ngành Khoa học dữ liệu và Trí tuệ nhân tạo | Khoa Công nghệ Thông tin | Khoa Điện tử và Trí tuệ nhân tạo | `cntt_2026_pre_restructure` (11/03/2026) | `project_owner_dsai` (ghi nhận 20/09/2026) | Chưa xác lập | PROVISIONAL |

Migration table is not complete.

## Conflict và mục chưa resolve

- DSAI: nguồn chính thức trước tái cơ cấu đặt chương trình dưới Khoa CNTT; project owner báo current state thuộc Khoa Điện tử và Trí tuệ nhân tạo. Chưa tìm được tài liệu chính thức hậu 20/08 xác nhận trực tiếp, nên giữ `PROVISIONAL`.
- Kỹ thuật máy tính: catalog cũ của UniTrust đặt dưới Khoa CNTT, trong khi tài liệu chính thức cũ đặt dưới Khoa Điện tử - Viễn thông. Mapping hiện tại chỉ `PROVISIONAL` ở khoa kế nhiệm, không giữ false-verified.
- “Kỹ thuật phần mềm” không xuất hiện như một entry độc lập trong danh mục 49 hiện hành; chỉ xuất hiện như nhánh của PFIEV, nên không giữ làm program độc lập trong dropdown.
- “Logistics và Quản lý chuỗi cung ứng” được nguồn khoa mô tả là chuyên ngành bên trong Quản lý công nghiệp, nhưng không là một entry riêng trong danh mục 49; không tính thêm thành program thứ 50.
- Bốn program `UNVERIFIED` được lưu ở `unassigned_programs` và không tham gia personalization theo khoa.

## Research log rút gọn

Các query discovery chính: tên 9 khoa + “20/08/2026”; “49 ngành/chuyên ngành 2026”; từng tên program với tên khoa giả thuyết và mốc sau 20/08. Mọi kết luận trong catalog trỏ đến trang DUT/tuyển sinh DUT đã mở; crawl date chỉ được lưu là `retrieved_date`, không thay cho `effective_date`.

Các website khoa hiện hành là nguồn đáng audit tiếp ở Step 17C hoặc đợt bổ sung provenance, nhưng Step 17B không thêm crawler hay source registry ingestion mới.
