# Báo cáo Prompt 07 — Phân cụm khám phá

- Thời điểm chạy: 2026-11-05T13:04:22+07:00
- Số dòng đưa vào: 54,706; không xóa ngoại lệ.
- Dùng log(price), log(area), log1p số phòng và mã one-hot địa bàn; các biến số được RobustScaler.
- Candidate k từ 2 đến 6; silhouette tính trên mẫu tối đa 2,500 dòng, seed 42.
- Chọn k=2 do silhouette mẫu cao nhất (0.2930); đây là lựa chọn kỹ thuật khám phá, không chứng minh tồn tại đúng số phân khúc thị trường.

## Chọn số cụm

| k | Silhouette mẫu | Kích thước cụm nhỏ nhất |
|---:|---:|---:|
| 2 | 0.2930 | 20,312 |
| 3 | 0.2803 | 6,066 |
| 4 | 0.2438 | 2,706 |
| 5 | 0.2093 | 5,102 |
| 6 | 0.1666 | 2,586 |

## Tóm tắt cụm

| Cụm | Số tin | Median price thô | Median area | Median bedrooms | Median bathrooms | Số địa bàn |
|---:|---:|---:|---:|---:|---:|---:|
| 0 | 20,312 | 8.5e+09 | 104 | 3.00 | 2.00 | 20 |
| 1 | 34,394 | 3.59e+09 | 68 | 2.00 | 2.00 | 21 |

### Ba địa bàn có nhiều tin nhất trong từng cụm

| Cụm | Địa bàn | Số tin |
|---:|---|---:|
| 0 | Quận 7 | 6,056 |
| 0 | Thủ Đức | 4,214 |
| 0 | Tân Phú | 2,012 |
| 1 | Thủ Đức | 7,018 |
| 1 | Quận 7 | 5,390 |
| 1 | Tân Phú | 2,549 |

- Gán cụm theo từng dòng: `data\processed\hcmc_apartment_clusters_prompt07.csv`.
- Biểu đồ lấy mẫu tối đa 10.000 dòng: `reports\figures\fig_12_apartment_clusters.png`.

## Giới hạn

- `price` là giá rao chưa xác minh đơn vị; phân cụm không phải định giá hoặc dự báo.
- Tập giữ các giá trị cực đoan; log/RobustScaler giảm nhưng không loại bỏ ảnh hưởng của dữ liệu nhập sai và điểm leverage.
- Silhouette dùng mẫu ngẫu nhiên và có thể không ổn định với cụm nhỏ; địa bàn Cần Giờ và Hóc Môn có ít tin.
- Các cụm phụ thuộc vào tập biến, cách scale, metric và k; không diễn giải nhân quả hay xem nhãn cụm là nhóm pháp lý/hành chính.

## Self-test

- PASS: giữ nguyên 54,706 dòng và mọi dòng nhận đúng một nhãn cụm.
- PASS: k=2, có 2 nhãn cụm không rỗng.
- PASS: biểu đồ cụm tồn tại.
