# Báo cáo Prompt 06 — Phân tích mô tả theo tháng

- Thời điểm chạy: 2026-11-05T13:04:20+07:00
- Dữ liệu là giá rao; đơn vị `price` chưa được nguồn xác nhận.
- Số kỳ tháng hợp lệ: 7; số dòng không có tháng phân tích được: 49 (giữ ngoài bảng chuỗi thời gian, không điền ngày).
- Các tháng: 2025-06, 2025-07, 2025-08, 2025-09, 2025-10, 2025-11, 2025-12.

## Tóm tắt tháng

| Tháng | Số tin | Median price thô | Q1 price | Q3 price | Median area | Số địa bàn |
|---|---:|---:|---:|---:|---:|---:|
| 2025-06 | 5,249 | 4.45e+09 | 2.85e+09 | 7.8e+09 | 76 | 20 |
| 2025-07 | 7,031 | 4.33e+09 | 2.9e+09 | 7.3e+09 | 76 | 20 |
| 2025-08 | 6,520 | 4.5e+09 | 3.1e+09 | 7.68e+09 | 75 | 20 |
| 2025-09 | 6,908 | 4.75e+09 | 3.1e+09 | 7.7e+09 | 75 | 19 |
| 2025-10 | 9,429 | 4.9e+09 | 3.35e+09 | 7.7e+09 | 76 | 21 |
| 2025-11 | 9,174 | 4.8e+09 | 3.37e+09 | 7.5e+09 | 75 | 20 |
| 2025-12 | 10,346 | 4.9e+09 | 3.4e+09 | 7.998e+09 | 75 | 21 |

- Median price thô từ 2025-06 đến 2025-12 thay đổi +10.11% (mô tả mẫu tin, không phải chỉ số giá thị trường).
- CSV: `data\processed\monthly_listing_summary_prompt06.csv`.
- Median price: `reports\figures\fig_10_monthly_median_price_descriptive.png`.
- Volume: `reports\figures\fig_11_monthly_listing_volume_descriptive.png`.

## Giới hạn chuỗi thời gian

- Chỉ có 7 điểm tháng (06–12/2025), không đủ chu kỳ để ước lượng và xác nhận AR/ARIMA đáng tin cậy; không tạo forecast.
- Thay đổi median có thể do cơ cấu địa bàn/diện tích/phòng ngủ của tin đăng thay đổi, không nhất thiết do giá của cùng loại căn hộ biến động.
- Dữ liệu không đại diện cho giá giao dịch, không bao phủ căn hộ Củ Chi, và không đủ cơ sở suy rộng sang 2026.

## Self-test

- PASS: xác nhận 7 tháng quan sát, không forecast.
- PASS: số tin tổng hợp khớp số dòng có tháng.
- PASS: biểu đồ tồn tại.
