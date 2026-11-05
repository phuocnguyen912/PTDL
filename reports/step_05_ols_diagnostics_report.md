# Báo cáo Prompt 05 — Chẩn đoán OLS

- Thời điểm chạy: 2026-11-02T19:29:32+07:00
- Chẩn đoán trên cùng tập train và cùng seed với Prompt 04; không thay mô hình.
- N train: 43,764; số biến kiểm tra VIF: 30.

## Kiểm định sai số và dạng hàm

| Kiểm tra | Thống kê | p-value | Đọc kết quả (α=0.05) |
|---|---:|---:|---|
| Breusch–Pagan LM (phương sai không đổi) | 1.25e+04 | <1e-300 (underflow) | Bác bỏ phương sai không đổi |
| Breusch–Pagan F | 582.8 | <1e-300 (underflow) | Có dấu hiệu heteroscedasticity |
| Jarque–Bera (phần dư chuẩn) | 2.756e+07 | <1e-300 (underflow) | Bác bỏ giả thuyết phần dư chuẩn |
| Ramsey RESET (dạng hàm) | 4,287 | <1e-300 (underflow) | Có dấu hiệu dạng hàm chưa phù hợp |

- Độ lệch (skewness) phần dư: -2.263; excess kurtosis: 125.9.
- Với cỡ mẫu lớn, kiểm định chuẩn tính có thể rất nhạy; cần đọc cùng Q-Q plot và không giả định p-value là thước đo mức độ sai lệch.

## Đa cộng tuyến

| Biến | VIF |
|---|---:|
| `month_2025-12` | 2.433 |
| `bedroom_count` | 2.43 |
| `bathroom_count` | 2.381 |
| `month_2025-10` | 2.331 |
| `month_2025-11` | 2.296 |
| `month_2025-07` | 2.046 |
| `month_2025-09` | 2.023 |
| `month_2025-08` | 1.974 |
| `district__Thu_Duc` | 1.607 |
| `district__Tan_Phu` | 1.287 |

- VIF lớn nhất: 2.433. Quy tắc tham khảo (5/10) không thay thế đánh giá chuyên môn.
- Bảng đầy đủ: `data\processed\ols_vif_prompt05.csv`.

## Điểm ảnh hưởng

- Ngưỡng tham khảo Cook's distance: `4/n = 9.14e-05`.
- Số quan sát vượt ngưỡng: 1,483/43,764. Ngưỡng này là cờ rà soát, không phải lý do tự động xóa dòng.
- Bảng 50 điểm Cook's distance lớn nhất: `data\processed\ols_influential_points_prompt05.csv`.
- Cook's distance lớn nhất: 42.36.

| Index trong file đã lọc | Địa bàn | Price thô | Area | Bedrooms | Bathrooms | Cook's D |
|---:|---|---:|---:|---:|---:|---:|
| 28067 | Tân Phú | 1.18e+11 | 760 | 73 | 73 | 42.36 |
| 19344 | Thủ Đức | 2.21e+12 | 1.7e+04 | 3 | 3 | 34.04 |
| 49221 | Quận 1 | 2.524e+10 | 1.286e+04 | 3 | 2 | 10.63 |
| 48445 | Thủ Đức | 6.16e+13 | 2,200 | 2 | 3 | 0.06392 |
| 25958 | Hóc Môn | 3.4e+08 | 65 | 3 | 2 | 0.02004 |

Các giá trị area/phòng ngủ/phòng tắm ở những dòng ảnh hưởng mạnh cần đối chiếu nguồn gốc trước khi xem hệ số OLS là đáng tin. Bảng chỉ dùng index trong file đã lọc; không chứa địa chỉ hay mô tả tin rao.

## Biểu đồ

- `reports\figures\fig_06_ols_residuals_vs_fitted.png` — phần dư theo giá trị fitted.
- `reports\figures\fig_07_ols_residual_qq.png` — Q-Q plot phần dư.
- `reports\figures\fig_08_ols_cooks_distance.png` — các Cook's distance lớn nhất.

## Diễn giải và giới hạn

- Kiểm định cổ điển không chứng minh mô hình phù hợp; nếu heteroscedasticity hiện diện, sai số chuẩn/p-value OLS cổ điển không đáng tin cậy. Cần cân nhắc sai số chuẩn robust hoặc mô hình thay thế ở bước tiếp theo.
- Điểm ảnh hưởng lớn được lưu để kiểm tra đơn vị/bản chất listing; không loại tự động vì người dùng đã chọn giữ ngoại lệ.
- Residual autocorrelation/Durbin–Watson không dùng ở đây vì đây là tập cắt ngang được chia ngẫu nhiên, không phải chuỗi có thứ tự thời gian.

## Self-test

- PASS: diagnostics được tính trên đúng train split Prompt 04.
- PASS: VIF, Cook's distance và residuals có kích thước đúng, giá trị hữu hạn.
- PASS: ba biểu đồ diagnostics tồn tại.
