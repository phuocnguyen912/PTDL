# Báo cáo Prompt 05 — Độ nhạy robust/HC3

- Thời điểm chạy: 2026-11-02T19:29:39+07:00
- Giữ nguyên toàn bộ 54.706 dòng; không xóa hay sửa ngoại lệ.
- Cùng split Prompt 04: train 43,764, test 10,942, `random_state=42`.
- HC3 chỉ thay sai số chuẩn/kiểm định, không thay hệ số hay dự đoán OLS.
- Huber RLM là phân tích độ nhạy; trọng số thấp không đồng nghĩa bản ghi bị xóa.

## Chỉ số holdout trên log(price)

| Phương pháp | MAE | RMSE | R² |
|---|---:|---:|---:|
| OLS cổ điển | 0.3736 | 0.4892 | 0.4976 |
| OLS với sai số chuẩn HC3 | 0.3736 | 0.4892 | 0.4976 |
| Huber RLM | 0.3273 | 0.4584 | 0.5591 |
| Baseline median train | 0.5277 | 0.6958 | -0.0161 |

Nếu OLS và Huber khác biệt lớn, kết quả phụ thuộc mạnh vào lựa chọn phương pháp. Không đánh giá bằng giá trị R² riêng lẻ; các metric không kiểm tra khả năng dự báo tương lai.

## Sai số chuẩn HC3

| Biến | Hệ số OLS | SE HC3 | p-value HC3 | KTC HC3 95% |
|---|---:|---:|---:|---:|
| `const` | 21.5502 | 0.2885 | <1e-300 (underflow) | [20.9848, 22.1156] |
| `area` | 0.000861721 | 0.0008875 | 0.3316 | [-0.000877834, 0.00260128] |
| `bedroom_count` | 0.303642 | 0.03613 | 4.423e-17 | [0.23283, 0.374455] |
| `bathroom_count` | 0.074445 | 0.1175 | 0.5263 | [-0.155824, 0.304714] |
| `district__Binh_Chanh` | -0.650211 | 0.0227 | 9.072e-179 | [-0.694706, -0.605716] |
| `district__Binh_Thanh` | 0.139692 | 0.02077 | 1.765e-11 | [0.0989847, 0.1804] |
| `district__Binh_Tan` | -0.586589 | 0.04154 | 3.478e-45 | [-0.668001, -0.505177] |
| `district__Can_Gio` | -0.711328 | 0.1674 | 2.155e-05 | [-1.03948, -0.383171] |
| `district__Go_Vap` | -0.645713 | 0.02897 | 2.081e-109 | [-0.702504, -0.588922] |
| `district__Hoc_Mon` | -1.58163 | 0.1211 | 6.549e-39 | [-1.81899, -1.34427] |
| `district__Nha_Be` | -0.336576 | 0.01606 | 4.775e-97 | [-0.368053, -0.305099] |
| `district__Phu_Nhuan` | -0.0421763 | 0.02689 | 0.1168 | [-0.0948904, 0.0105377] |
| `district__Quan_1` | 0.904191 | 0.02913 | 2.733e-209 | [0.8471, 0.961281] |
| `district__Quan_10` | -0.177487 | 0.0412 | 1.652e-05 | [-0.258242, -0.0967325] |
| `district__Quan_11` | -0.340118 | 0.02256 | 3.109e-51 | [-0.384335, -0.295901] |
| `district__Quan_12` | -0.787187 | 0.03748 | 1.976e-97 | [-0.860657, -0.713716] |
| `district__Quan_3` | 0.00718493 | 0.05387 | 0.8939 | [-0.0983971, 0.112767] |
| `district__Quan_4` | 0.0174145 | 0.02952 | 0.5552 | [-0.0404454, 0.0752744] |
| `district__Quan_5` | -0.125011 | 0.03438 | 0.0002767 | [-0.192391, -0.0576312] |
| `district__Quan_6` | -0.383651 | 0.01765 | 3.394e-104 | [-0.418247, -0.349054] |
| `district__Quan_8` | -0.580876 | 0.02105 | 3.626e-166 | [-0.622138, -0.539615] |
| `district__Thu_Duc` | 0.0739722 | 0.01888 | 8.912e-05 | [0.0369746, 0.11097] |
| `district__Tan_Binh` | -0.3702 | 0.0323 | 2.259e-30 | [-0.433504, -0.306896] |
| `district__Tan_Phu` | -0.287164 | 0.01458 | 4.877e-86 | [-0.315732, -0.258597] |
| `month_2025-07` | 0.0105297 | 0.01161 | 0.3645 | [-0.0122295, 0.033289] |
| `month_2025-08` | 0.0539574 | 0.01159 | 3.241e-06 | [0.0312407, 0.076674] |
| `month_2025-09` | 0.041398 | 0.01155 | 0.0003376 | [0.0187637, 0.0640322] |
| `month_2025-10` | 0.0857468 | 0.01117 | 1.698e-14 | [0.0638471, 0.107647] |
| `month_2025-11` | 0.0786644 | 0.01319 | 2.506e-09 | [0.0528046, 0.104524] |
| `month_2025-12` | 0.103497 | 0.01166 | 6.977e-19 | [0.0806514, 0.126343] |
| `month_Unknown month` | 0.0715023 | 0.0731 | 0.328 | [-0.0717725, 0.214777] |

HC3 điều chỉnh suy luận với heteroscedasticity nhưng không sửa sai dạng hàm, ngoại lệ có leverage cao, thiếu biến hoặc lỗi dữ liệu.

## Độ nhạy hệ số Huber so với OLS

| Biến | OLS | Huber | Huber − OLS |
|---|---:|---:|---:|
| `const` | 21.5502 | 21.3045 | -0.245695 |
| `bedroom_count` | 0.303642 | 0.0623303 | -0.241312 |
| `district__Hoc_Mon` | -1.58163 | -1.34777 | 0.233862 |
| `district__Can_Gio` | -0.711328 | -0.494673 | 0.216655 |
| `district__Quan_12` | -0.787187 | -0.638923 | 0.148263 |
| `district__Quan_3` | 0.00718493 | 0.148173 | 0.140988 |
| `district__Binh_Tan` | -0.586589 | -0.448501 | 0.138088 |
| `district__Go_Vap` | -0.645713 | -0.512258 | 0.133455 |
| `district__Binh_Chanh` | -0.650211 | -0.518027 | 0.132184 |
| `district__Quan_10` | -0.177487 | -0.0690117 | 0.108475 |

- Huber hội tụ sau 41 vòng lặp; scale robust=0.3817.
- Số dòng train có trọng số Huber < 0.5: 1,380/43,764.
- Danh sách tối đa 100 trọng số thấp: `data\processed\robust_sensitivity_low_weight_rows_prompt05.csv`.

Trọng số Huber giảm tác động của phần dư lớn nhưng không bảo vệ đầy đủ trước điểm leverage cực đoan ở biến đầu vào.

## Sản phẩm

- Hệ số và SE HC3: `data\processed\robust_sensitivity_coefficients_prompt05.csv`.
- So sánh dự đoán test: `data\processed\robust_sensitivity_predictions_prompt05.csv`.
- Biểu đồ so sánh: `reports\figures\fig_09_ols_huber_holdout_comparison.png`.

## Giới hạn và quyết định

- HC3 không cải thiện dự đoán OLS; Huber là mô hình khác, cần được đánh giá độc lập và không tự thay thế mô hình đã duyệt.
- Các giá trị area/phòng ngủ/phòng tắm cực đoan vẫn cần xác minh từ nguồn trước khi đưa ra kết luận giá. Không có xác nhận đơn vị `price`.
- Tập dữ liệu chỉ có 7 tháng và không chứa căn hộ Củ Chi; không đủ cơ sở để tạo dự báo AR/ARIMA đáng tin cậy.

## Self-test

- PASS: HC3 giữ nguyên hệ số OLS; Huber chạy trên cùng train và không xóa bản ghi.
- PASS: dự đoán, hệ số, trọng số và metric đều hữu hạn.
- PASS: biểu đồ độ nhạy đã được tạo.
