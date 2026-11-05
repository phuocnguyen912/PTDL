# Phân tích và dự đoán thăm dò giá rao căn hộ TP.HCM

## Tóm tắt điều hành

Đã thực hiện các bước dữ liệu, biến đổi, OLS, chẩn đoán, phân tích độ nhạy robust và phân cụm trên nguồn tin rao Kaggle. Người dùng chọn nhánh **giữ nguyên ngoại lệ**; không tự điền giá trị thiếu hay xóa điểm cực đoan.

**Chưa có cơ sở để công bố mô hình này như công cụ định giá hoặc dự báo thị trường.** Trường `price` chưa được nguồn xác nhận đơn vị; OLS vi phạm các giả định quan trọng và chịu ảnh hưởng mạnh từ một số giá trị đầu vào bất thường. Holdout là chia ngẫu nhiên trong cùng giai đoạn, không đánh giá khả năng dự báo tương lai. Dữ liệu chỉ có bảy tháng và không có tin căn hộ Củ Chi.

## Dữ liệu và phạm vi

- Nguồn: [Vietnam Real Estates trên Kaggle](https://www.kaggle.com/datasets/yashdev01/vietnam-real-estates), phiên bản 1; giấy phép ghi nhận là **CC BY-NC-SA 4.0**.
- Đây là dữ liệu **rao bán**, không phải giá giao dịch. Tài liệu nguồn không xác nhận đơn vị giá hoặc chi tiết phương pháp thu thập.
- Có 74.385 tin được gắn nhãn căn hộ chung cư tại TP.HCM; 0 trùng lặp chính xác. Complete-case giữ 54.706 dòng, không điền giá trị thiếu.
- Complete-case có 21 nhãn quận/huyện; không có tin căn hộ Củ Chi. Cần Giờ và Hóc Môn chỉ có 7 và 18 dòng complete-case.
- Ngày đăng hợp lệ trải từ 2025-06 đến 2025-12; 49 dòng không phân tích được tháng và được giữ trong mô hình dưới nhóm riêng, không tự điền ngày.
- Giá cực trị trong nguồn lên đến `6,16e13`; diện tích lên đến `17.000`; có giá trị phòng ngủ/phòng tắm lên đến `73`. Các trường này cần xác minh trước khi dùng kết quả để định giá.

## Kết quả chính

### Biến đổi và tương quan

Địa bàn được one-hot encode, diện tích được chia tứ phân vị để mô tả, và các biến đầu vào có cả z-score lẫn Min-Max. Giá và diện tích gốc vẫn được giữ. Spearman giữa giá và diện tích là `0,673`; giữa diện tích và số phòng ngủ là `0,788`. Đây là tương quan, không phải quan hệ nhân quả.

### OLS và độ nhạy

Mô hình đã duyệt dùng `log(price)` làm mục tiêu, `area` liên tục, số phòng, one-hot địa bàn và tháng đăng. Split 80/20 ngẫu nhiên (`random_state=42`):

| Phương pháp | R² test trên log(price) | MAE test trên log(price) |
|---|---:|---:|
| OLS | 0,4976 | 0,3736 |
| OLS với sai số chuẩn HC3 | 0,4976 | 0,3736 |
| Huber RLM | 0,5591 | 0,3273 |

HC3 không đổi hệ số hay dự đoán; nó chỉ điều chỉnh sai số chuẩn. Với HC3, hệ số `area` (`p=0,3316`) và `bathroom_count` (`p=0,5263`) không có ý nghĩa thống kê ở ngưỡng 5%. Huber đạt chỉ số holdout tốt hơn trong split này, nhưng hệ số thay đổi đáng kể và 1.380 dòng train nhận trọng số dưới 0,5. Điều này cho thấy kết quả nhạy với cách xử lý ngoại lệ; Huber không xác minh được bản chất dữ liệu.

### Chẩn đoán

- Breusch–Pagan, Jarque–Bera và Ramsey RESET đều bác bỏ các giả định tương ứng ở `p < 1e-300`.
- 1.483 dòng vượt ngưỡng Cook’s distance tham khảo `4/n`; cực đại là `42,36`.
- Một số dòng ảnh hưởng nhất có diện tích `760`, `17.000`, `12.865` hoặc số phòng ngủ/phòng tắm `73`. Chưa xóa các dòng này; cần xác minh nguồn.
- Holdout có 20/21 địa bàn và không có Cần Giờ. Kết quả holdout không xác nhận chất lượng dự đoán cho từng quận/huyện.

### Theo tháng và phân cụm

- Median trường giá thô từ tháng 06 đến tháng 12 tăng `10,11%` trong mẫu tin. Không thể kết luận đây là mức tăng của thị trường vì cơ cấu diện tích, địa bàn và loại căn hộ có thể thay đổi.
- Chỉ có 7 kỳ tháng; **không tạo forecast AR/ARIMA** vì không đủ dữ liệu để kiểm định dự báo đáng tin cậy.
- Phân cụm khám phá chọn `k=2` theo silhouette mẫu `0,2930`. Nhãn cụm phụ thuộc biến và cách scale; không phải phân khúc thị trường đã được xác nhận.

## Kết luận và khuyến nghị

Kết quả hiện phù hợp cho **bài tập phân tích thăm dò**, không phù hợp để đưa ra giá bán, tư vấn giao dịch hoặc dự báo năm 2026. Trước khi phát triển mô hình định giá:

1. Xác minh đơn vị `price`, nguồn tin và các dòng có diện tích/số phòng bất thường.
2. Thu thập dữ liệu dài hạn hơn, có phủ địa bàn đầy đủ và chuẩn hóa địa giới; ưu tiên giá giao dịch nếu mục tiêu là định giá giao dịch.
3. Sau khi xác minh dữ liệu, đánh giá lại bằng split theo thời gian và theo địa bàn, so sánh mô hình robust/phi tuyến, đồng thời báo cáo sai số trên thang giá có đơn vị rõ ràng.

## Các tệp Python

Mỗi script tương ứng với một bước phân tích đang dùng; không có script riêng nào chỉ phục vụ đề tài khác. Đã bỏ kiểm tra gói `openpyxl` và phụ thuộc khai báo trực tiếp `scipy` vì mã đề tài không dùng chúng trực tiếp; cũng đã bỏ một biến dự đoán không được sử dụng và tránh quét môi trường ảo khi tìm dữ liệu.

- [step_00_environment_check.py](../src/step_00_environment_check.py) — kiểm tra môi trường và dữ liệu đầu vào.
- [step_01_merge_and_audit.py](../src/step_01_merge_and_audit.py) — audit dữ liệu nguồn.
- [step_02_eda_and_cleaning.py](../src/step_02_eda_and_cleaning.py) — EDA, làm sạch và tạo các nhánh ngoại lệ.
- [step_03_feature_engineering.py](../src/step_03_feature_engineering.py) — biến đổi và mã hóa đặc trưng.
- [step_04_ols_model.py](../src/step_04_ols_model.py) — OLS và đánh giá holdout.
- [step_05_ols_diagnostics.py](../src/step_05_ols_diagnostics.py) — chẩn đoán OLS.
- [step_05_robust_sensitivity.py](../src/step_05_robust_sensitivity.py) — so sánh HC3/Huber theo lựa chọn đã duyệt.
- [step_06_monthly_descriptive_analysis.py](../src/step_06_monthly_descriptive_analysis.py) — mô tả dữ liệu theo tháng, không forecast.
- [step_07_apartment_clustering.py](../src/step_07_apartment_clustering.py) — phân cụm khám phá.

## Báo cáo và đầu ra

- [Audit và phạm vi dữ liệu](./step_01_data_audit_report.md)
- [EDA và làm sạch](./step_02_eda_cleaning_report.md)
- [Mã hóa và biến đổi đặc trưng](./step_03_feature_engineering_report.md)
- [Hồi quy OLS](./step_04_ols_report.md)
- [Chẩn đoán OLS](./step_05_ols_diagnostics_report.md)
- [Độ nhạy robust/HC3](./step_05_robust_sensitivity_report.md)
- [Phân tích mô tả theo tháng](./step_06_monthly_analysis_report.md)
- [Phân cụm khám phá](./step_07_clustering_report.md)

Không chia sẻ lại dữ liệu nguồn hoặc sản phẩm phái sinh nếu chưa tuân thủ đầy đủ điều khoản CC BY-NC-SA 4.0 và ghi công nguồn.
