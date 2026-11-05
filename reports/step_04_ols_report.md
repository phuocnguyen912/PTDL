# Báo cáo Prompt 04 — Hồi quy OLS

- Thời điểm chạy: 2026-11-02T19:29:24+07:00
- Dữ liệu: nhánh `preserve_extremes`; giữ nguyên mọi ngoại lệ đã duyệt.
- Biến mục tiêu được duyệt: `log(price)`; giá rao trong nguồn chưa xác minh đơn vị.
- Diện tích được duyệt: `area` liên tục; không đưa `area_bin` vào mô hình này.
- Quan sát: 54,706; train 43,764; test 10,942.
- Biến giải thích: 30 (có intercept), split test=20%, `random_state=42`.

## Đặc tả mô hình

`log(price) ~ area + bedroom_count + bathroom_count + district indicators + month indicators`.
- Nhóm địa bàn tham chiếu: Quận 7 (các cột địa bàn từ Prompt 03: 20).
- Nhóm tháng tham chiếu: 2025-06; các tháng hợp lệ: 2025-06, 2025-07, 2025-08, 2025-09, 2025-10, 2025-11, 2025-12.
- Giữ 49 ngày không phân tích được trong nhóm riêng `Unknown month`; không tự điền ngày.
- Mô hình dùng các biến số gốc chưa scale. Không dùng scaler fit trên toàn tập EDA.

## Kết quả

| Tập | MAE log(price) | RMSE log(price) | R² log(price) |
|---|---:|---:|---:|
| Train | 0.3778 | 0.5170 | 0.4476 |
| Test | 0.3736 | 0.4892 | 0.4976 |
| Baseline test (median log-price train) | 0.5277 | 0.6958 | -0.0161 |

Test là holdout ngẫu nhiên cùng giai đoạn dữ liệu, không phải kiểm tra dự báo tương lai. MAE/RMSE tính trên thang log, không phải đơn vị tiền.
- Test có 20/21 nhãn địa bàn; không có dòng holdout cho: Cần Giờ.

## Hệ số OLS

Hệ số cho biến liên tục mô tả thay đổi log-price khi biến tăng một đơn vị, giữ các biến khác không đổi. Hệ số dummy địa bàn/tháng so với nhóm tham chiếu. Đây là liên hệ thống kê, không phải tác động nhân quả.
p-value và khoảng tin cậy bên dưới dùng sai số chuẩn OLS cổ điển; cần xem kết quả chẩn đoán Prompt 05 trước khi dùng suy luận thống kê.

| Biến | Hệ số | Sai số chuẩn | p-value | KTC 95% |
|---|---:|---:|---:|---:|
| `const` | 21.5502 | 0.0126 | <1e-300 (underflow) | [21.5255, 21.5749] |
| `area` | 0.000861721 | 2.352e-05 | 1.758e-289 | [0.000815621, 0.000907821] |
| `bedroom_count` | 0.303642 | 0.005082 | <1e-300 (underflow) | [0.293681, 0.313603] |
| `bathroom_count` | 0.074445 | 0.005932 | 4.66e-36 | [0.0628172, 0.0860727] |
| `district__Binh_Chanh` | -0.650211 | 0.01206 | <1e-300 (underflow) | [-0.673847, -0.626575] |
| `district__Binh_Thanh` | 0.139692 | 0.01237 | 1.584e-29 | [0.115444, 0.16394] |
| `district__Binh_Tan` | -0.586589 | 0.01468 | <1e-300 (underflow) | [-0.615359, -0.557819] |
| `district__Can_Gio` | -0.711328 | 0.1956 | 0.000276 | [-1.09466, -0.327996] |
| `district__Go_Vap` | -0.645713 | 0.02045 | 1.74e-216 | [-0.685786, -0.60564] |
| `district__Hoc_Mon` | -1.58163 | 0.1295 | 2.836e-34 | [-1.83536, -1.3279] |
| `district__Nha_Be` | -0.336576 | 0.01301 | 1.646e-146 | [-0.362072, -0.31108] |
| `district__Phu_Nhuan` | -0.0421763 | 0.01588 | 0.007923 | [-0.0733071, -0.0110455] |
| `district__Quan_1` | 0.904191 | 0.01391 | <1e-300 (underflow) | [0.876921, 0.931461] |
| `district__Quan_10` | -0.177487 | 0.01745 | 2.817e-24 | [-0.211687, -0.143287] |
| `district__Quan_11` | -0.340118 | 0.02078 | 4.745e-60 | [-0.380842, -0.299395] |
| `district__Quan_12` | -0.787187 | 0.01891 | <1e-300 (underflow) | [-0.824245, -0.750128] |
| `district__Quan_3` | 0.00718493 | 0.02545 | 0.7777 | [-0.042698, 0.0570678] |
| `district__Quan_4` | 0.0174145 | 0.01547 | 0.2603 | [-0.0129044, 0.0477334] |
| `district__Quan_5` | -0.125011 | 0.02264 | 3.392e-08 | [-0.169392, -0.0806299] |
| `district__Quan_6` | -0.383651 | 0.01557 | 4e-133 | [-0.414171, -0.353131] |
| `district__Quan_8` | -0.580876 | 0.01202 | <1e-300 (underflow) | [-0.604435, -0.557317] |
| `district__Thu_Duc` | 0.0739722 | 0.007757 | 1.559e-21 | [0.0587679, 0.0891764] |
| `district__Tan_Binh` | -0.3702 | 0.01222 | 1.938e-199 | [-0.394157, -0.346243] |
| `district__Tan_Phu` | -0.287164 | 0.01019 | 3.161e-173 | [-0.307134, -0.267195] |
| `month_2025-07` | 0.0105297 | 0.01055 | 0.3182 | [-0.0101461, 0.0312055] |
| `month_2025-08` | 0.0539574 | 0.01074 | 5.134e-07 | [0.0328985, 0.0750163] |
| `month_2025-09` | 0.041398 | 0.01062 | 9.647e-05 | [0.0205909, 0.062205] |
| `month_2025-10` | 0.0857468 | 0.009969 | 8.146e-18 | [0.0662071, 0.105287] |
| `month_2025-11` | 0.0786644 | 0.01005 | 5.03e-15 | [0.0589703, 0.0983584] |
| `month_2025-12` | 0.103497 | 0.009842 | 7.859e-26 | [0.0842064, 0.122788] |
| `month_Unknown month` | 0.0715023 | 0.08119 | 0.3785 | [-0.0876312, 0.230636] |

p-value hiển thị `<1e-300 (underflow)` thay vì 0 khi giá trị số bị underflow.
- Bảng đầy đủ: `data\processed\ols_coefficients_prompt04.csv`.
- Dự đoán holdout: `data\processed\ols_test_predictions_prompt04.csv`.
- Biểu đồ dự đoán/quan sát: `reports\figures\fig_05_ols_test_predictions.png` (trên thang log).

Khi lấy `exp(predicted log-price)`, kết quả gần với trung vị có điều kiện/geometric scale; không tự xem đó là giá trung bình kỳ vọng. Muốn báo giá ở thang gốc cần đánh giá hiệu chỉnh retransformation riêng.

## Giới hạn

- Split ngẫu nhiên có thể đo độ khớp nội suy trong cùng giai đoạn; không kiểm tra khả năng dự báo sang 2026 hoặc thị trường tương lai.
- Chỉ 7 tháng dữ liệu; không bao phủ căn hộ Củ Chi. Cần Giờ và Hóc Môn có rất ít mẫu, nên hệ số nhóm này có thể bất ổn.
- Không có thông tin dự án, tuổi căn hộ, tầng, pháp lý hoặc tọa độ đầy đủ; mô hình có thể bỏ sót biến quan trọng.
- Do ngoại lệ được giữ theo lựa chọn của người dùng, chỉ số ở thang giá gốc có thể nhạy với một số tin cực đoan.

## Self-test

- PASS: train/test không giao nhau; target và mọi feature hữu hạn.
- PASS: hệ số, dự đoán và các chỉ số holdout hữu hạn.
- PASS: baseline được tính trên cùng test set.
- PASS: biểu đồ holdout đã tạo.

## Điểm dừng trước Prompt 05

- Tiếp theo là chẩn đoán giả định OLS (tuyến tính, phương sai sai số, phân phối phần dư, đa cộng tuyến và điểm ảnh hưởng).
- Không dùng p-value như bằng chứng nhân quả hoặc tuyên bố dự báo mọi quận.
