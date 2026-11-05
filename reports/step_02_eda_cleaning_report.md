# Báo cáo Prompt 02 — Phân tích khám phá dữ liệu và làm sạch

- Thời điểm chạy: 2026-11-02T19:29:15+07:00
- Nguồn: Kaggle `yashdev01/vietnam-real-estates`, phiên bản 1; giấy phép CC BY-NC-SA 4.0.
- Phạm vi: các dòng gắn nhãn `Hồ Chí Minh` và `Căn hộ chung cư` trong dữ liệu nguồn.
- Không điền giá trị thiếu; không dùng dữ liệu mô phỏng trong `New folder/`.

## Đối chiếu trước và sau

| Giai đoạn | Số dòng | Số cột |
|---|---:|---:|
| Toàn bộ nguồn trước lọc | 1,000,000 | 19 |
| Căn hộ TP.HCM theo nhãn nguồn | 74,385 | 19 |
| Sau khử trùng và chỉ giữ cột phân tích | 74,385 | 12 |
| Bản ghi đầy đủ dữ liệu, đủ biến và hợp lệ | 54,706 | 12 |
| Nhánh 3σ (`price` và `area`) | 54,598 | 12 |
| Nhánh giữ nguyên ngoại lệ | 54,706 | 12 |
| Trùng chính xác đã bỏ | 0 | — |
| Bị loại do thiếu/giá trị không hợp lệ | 19,679 | — |

Bản ghi trùng chỉ được nhận diện khi mọi cột nguồn giống hệt nhau. Không có mã tin đáng tin cậy để dò tin đăng lại gần giống.

## Tỷ lệ thiếu trước khi lọc

| Cột | Số thiếu | Tỷ lệ |
|---|---:|---:|
| `property_type_name` | 0 | 0.0% |
| `province_name` | 0 | 0.0% |
| `district_name` | 11,495 | 15.5% |
| `ward_name` | 22,605 | 30.4% |
| `price` | 4,112 | 5.5% |
| `area` | 0 | 0.0% |
| `bedroom_count` | 3,881 | 5.2% |
| `bathroom_count` | 5,922 | 8.0% |
| `floor_count` | 74,315 | 99.9% |
| `published_at` | 0 | 0.0% |

Các biến bắt buộc cho mô hình ở giai đoạn thăm dò là `price`, `area`, `bedroom_count`, `bathroom_count`, `district_name`. Các dòng thiếu biến này bị loại khỏi bản ghi đầy đủ dữ liệu (complete-case); không điền bằng trung vị/giá trị phổ biến nhất vì tỷ lệ thiếu vượt 3%. `ward_name` không dùng ở mô hình này và được giữ nguyên nếu thiếu.

## Thống kê mô tả trên bản ghi đầy đủ dữ liệu (đơn vị giá chưa xác minh)

| Quận/huyện theo nhãn nguồn | Số tin | Trung vị của `price` thô | Trung bình của `price` thô |
|---|---:|---:|---:|
| Hóc Môn | 18 | 1.225e+09 | 1.151e+09 |
| Quận 12 | 1,031 | 2.45e+09 | 5.051e+09 |
| Gò Vấp | 855 | 2.85e+09 | 3.273e+09 |
| Bình Chánh | 2,913 | 2.97e+09 | 4.168e+09 |
| Cần Giờ | 7 | 3.16e+09 | 3.631e+09 |
| Bình Tân | 1,797 | 3.2e+09 | 7.912e+09 |
| Quận 8 | 2,945 | 3.35e+09 | 3.427e+09 |
| Quận 11 | 844 | 3.75e+09 | 4.727e+09 |
| Tân Bình | 2,797 | 3.89e+09 | 4.376e+09 |
| Quận 5 | 694 | 3.9e+09 | 7.95e+09 |
| Quận 6 | 1,557 | 4e+09 | 4.372e+09 |
| Tân Phú | 4,561 | 4.2e+09 | 5.906e+09 |
| Nhà Bè | 2,406 | 4.5e+09 | 4.58e+09 |
| Quận 10 | 1,210 | 4.95e+09 | 5.372e+09 |
| Thủ Đức | 11,232 | 5.5e+09 | 1.53e+10 |
| Quận 4 | 1,605 | 6.1e+09 | 1.058e+10 |
| Quận 3 | 551 | 6.18e+09 | 6.719e+09 |
| Phú Nhuận | 1,509 | 6.2e+09 | 6.084e+09 |
| Quận 7 | 11,446 | 6.4e+09 | 7.493e+09 |
| Bình Thạnh | 2,679 | 7.62e+09 | 9.304e+09 |
| Quận 1 | 2,049 | 1.4e+10 | 2.011e+10 |

- Tháng đăng quan sát được: 2025-06, 2025-07, 2025-08, 2025-09, 2025-10, 2025-11, 2025-12.
- Trung vị và trung bình chỉ mô tả giá rao trong tập tin đăng; không đại diện cho giá giao dịch.

## Đối chiếu ngoại lệ 3σ

Ngưỡng dùng cho từng biến là `μ − 3σ` đến `μ + 3σ`, trong đó `σ` là độ lệch chuẩn tổng thể (`ddof=0`). Đây chỉ là một nhánh so sánh, không mặc định là quy tắc đúng cho phân phối giá nhà lệch phải.

| Biến | μ | σ | Ngưỡng dưới | Ngưỡng trên | Ngoài ngưỡng |
|---|---:|---:|---:|---:|---:|
| `price` | 8.612e+09 | 2.684e+11 | -7.966e+11 | 8.138e+11 | 10 |
| `area` | 85.02 | 98.8 | -211.4 | 381.4 | 100 |

- Nhánh 3σ loại 108 dòng; nhánh giữ nguyên không loại ngoại lệ thống kê.
- Cần duyệt nhánh sử dụng trước Prompt 03. Không xóa giá trị cực đoan chỉ vì cao/thấp; cần xác minh đơn vị và bản chất tin rao trước khi diễn giải.

## Biểu đồ

- `reports/figures/fig_01_price_distribution.png` — phân bố log10 của trường giá thô.
- `reports/figures/fig_02_price_by_district.png` — phân bố theo nhãn quận/huyện nguồn.
- `reports/figures/fig_03_monthly_listing_volume.png` — số tin theo tháng đăng.

## Tự kiểm tra

- ĐẠT: bản ghi đầy đủ dữ liệu không rỗng.
- ĐẠT: không còn thiếu ở biến bắt buộc.
- ĐẠT: không còn dòng trùng chính xác trong các cột nguồn.
- ĐẠT: đã tạo đủ ba biểu đồ.

## Điểm dừng trước Prompt 03

- Chọn nhánh `3sigma_strict` hoặc `preserve_extremes`.
- Xác nhận tiếp tục với giá rao và chấp nhận độ tin cậy hạn chế do nguồn không công bố đơn vị giá/phương pháp thu thập chi tiết.
- Kết quả không bao phủ căn hộ Củ Chi; không được diễn giải là mô hình đủ mọi quận.
