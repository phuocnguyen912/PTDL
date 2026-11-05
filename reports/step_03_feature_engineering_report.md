# Báo cáo Prompt 03 — Mã hóa và biến đổi đặc trưng

- Thời điểm chạy: 2026-11-02T19:29:19+07:00
- Nhánh đầu vào đã được người dùng chọn: `preserve_extremes`.
- Không loại ngoại lệ, không điền thiếu, không thay đổi số dòng hoặc các giá trị gốc.
- Đầu vào: `data\processed\hcmc_apartments_preserve_extremes.csv` (54,706 dòng, 12 cột).
- Đầu ra: `data\processed\hcmc_apartments_prompt03_preserve_extremes.csv` (54,706 dòng, 42 cột).
- `price` vẫn là trường giá rao có đơn vị chưa xác minh; không được diễn giải là giá giao dịch.

## Rời rạc hóa diện tích

Chia `area` thành tối đa 4 nhóm theo các phân vị 0%, 25%, 50%, 75% và 100%. Nếu các ngưỡng trùng nhau, nhóm thừa được gộp. Biến `area_bin` được giữ để diễn giải; các biến giả dùng nhóm nhỏ nhất làm nhóm tham chiếu.

- Các ngưỡng diện tích quan sát: 6, 65, 75, 95, 1.7e+04.

| Nhóm | Số tin | Min area | Max area | Median price thô |
|---|---:|---:|---:|---:|
| Q1 | 14,556 | 6.00 | 65.00 | 3e+09 |
| Q2 | 12,978 | 65.10 | 75.00 | 3.95e+09 |
| Q3 | 13,590 | 75.10 | 95.00 | 5.4e+09 |
| Q4 | 13,582 | 95.10 | 17,000.00 | 9.1e+09 |

## Mã hóa địa bàn

Địa bàn là biến danh nghĩa nên được mã hóa one-hot, không gán số thứ tự. Nhóm tham chiếu (địa bàn có nhiều tin nhất): **Quận 7**. Cột tham chiếu được lược bỏ để tránh đồng tuyến tính hoàn hảo với intercept.

| Nhãn địa bàn | Cột đặc trưng | Tham chiếu | Số tin |
|---|---|---:|---:|
| Quận 7 | (reference; all district indicators = 0) | Có | 11,446 |
| Bình Chánh | district__Binh_Chanh | Không | 2,913 |
| Bình Thạnh | district__Binh_Thanh | Không | 2,679 |
| Bình Tân | district__Binh_Tan | Không | 1,797 |
| Cần Giờ | district__Can_Gio | Không | 7 |
| Gò Vấp | district__Go_Vap | Không | 855 |
| Hóc Môn | district__Hoc_Mon | Không | 18 |
| Nhà Bè | district__Nha_Be | Không | 2,406 |
| Phú Nhuận | district__Phu_Nhuan | Không | 1,509 |
| Quận 1 | district__Quan_1 | Không | 2,049 |
| Quận 10 | district__Quan_10 | Không | 1,210 |
| Quận 11 | district__Quan_11 | Không | 844 |
| Quận 12 | district__Quan_12 | Không | 1,031 |
| Quận 3 | district__Quan_3 | Không | 551 |
| Quận 4 | district__Quan_4 | Không | 1,605 |
| Quận 5 | district__Quan_5 | Không | 694 |
| Quận 6 | district__Quan_6 | Không | 1,557 |
| Quận 8 | district__Quan_8 | Không | 2,945 |
| Thủ Đức | district__Thu_Duc | Không | 11,232 |
| Tân Bình | district__Tan_Binh | Không | 2,797 |
| Tân Phú | district__Tan_Phu | Không | 4,561 |

## Scaling

Tạo cả z-score (`*_z`) và Min-Max [0, 1] (`*_minmax`) cho `area`, `bedroom_count` và `bathroom_count`. Không scale `price`, vì đây là biến mục tiêu và đơn vị chưa xác minh.

| Biến | Mean dùng cho z-score | Scale (độ lệch chuẩn) |
|---|---:|---:|
| `area` | 85.02 | 98.8 |
| `bedroom_count` | 2.22 | 0.7454 |
| `bathroom_count` | 1.879 | 0.6278 |

Các tham số trên được fit trên toàn bộ tập thăm dò để đáp ứng bước EDA. Nếu đánh giá dự báo bằng train/test hoặc cross-validation, phải fit lại scaler chỉ trên từng tập train bên trong pipeline để tránh leakage.

## Tương quan Spearman

Dùng Spearman trên các trường số gốc để hạn chế ảnh hưởng của lệch phân phối và ngoại lệ. Tương quan chỉ mô tả liên hệ đơn biến, không chứng minh nhân quả hay quan hệ tuyến tính.

| Biến | `price` | `area` | `bedroom_count` | `bathroom_count` |
|---|---:|---:|---:|---:|
| `price` | 1.000 | 0.673 | 0.480 | 0.403 |
| `area` | 0.673 | 1.000 | 0.788 | 0.693 |
| `bedroom_count` | 0.480 | 0.788 | 1.000 | 0.637 |
| `bathroom_count` | 0.403 | 0.693 | 0.637 | 1.000 |

- Ma trận: `reports\step_03_spearman_correlation.csv`.
- Heatmap: `reports\figures\fig_04_spearman_correlation.png`.

## Giới hạn sử dụng

- Giá trị gốc được giữ nguyên; đơn vị `price` và phương pháp thu thập không được nguồn xác nhận.
- Dữ liệu chỉ gồm tin rao tháng 06–12/2025, nhãn căn hộ TP.HCM của nguồn; không có tin căn hộ Củ Chi trong tập complete-case.
- Một số địa bàn có rất ít mẫu (Cần Giờ 7 tin, Hóc Môn 18 tin sau complete-case); hệ số riêng cho các nhóm này sẽ rất thiếu ổn định.
- Không dùng các biến one-hot area cùng `area` liên tục trong cùng một mô hình; đó là hai cách biểu diễn thay thế của diện tích.
- Z-score/Min-Max hiện phục vụ EDA; mô hình có đánh giá holdout cần pipeline fit theo tập train.

## Self-test

- PASS: giữ nguyên 54,706 dòng, không lọc thêm ngoại lệ.
- PASS: giá và diện tích gốc giữ nguyên; các biến bắt buộc không bị thiếu.
- PASS: one-hot địa bàn dùng nhóm tham chiếu và không tạo cột tên trùng.
- PASS: mỗi dòng được gán đúng một nhóm diện tích; các biến scale hữu hạn.
- PASS: heatmap đã được tạo.

## Điểm dừng trước Prompt 04

- Duyệt lựa chọn biến cho mô hình: `area` liên tục hay nhóm `area_bin`; không đưa cả hai vào cùng một mô hình.
- Chốt biến mục tiêu: giá rao thô (đơn vị chưa xác minh) hay biến đổi mục tiêu có giải thích rõ. Không trình bày kết quả như giá giao dịch.
