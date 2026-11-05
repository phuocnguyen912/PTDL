# Mô tả đề tài đồ án phân tích dữ liệu

## 1. Tên đề tài

**Phân tích các yếu tố liên quan đến giá rao bán căn hộ chung cư tại TP. Hồ Chí Minh bằng phương pháp thống kê và học máy**

## 2. Bối cảnh và vấn đề

Thị trường căn hộ tại TP. Hồ Chí Minh có sự khác biệt về giá rao giữa các khu vực và giữa các căn hộ có diện tích, số phòng khác nhau. Việc phân tích dữ liệu tin rao có thể giúp nhận diện những mối liên hệ này và đánh giá khả năng xây dựng mô hình ước lượng giá rao từ các thuộc tính cơ bản của căn hộ.

Đồ án tập trung vào **giá rao trong dữ liệu**, không xem đây là giá giao dịch hay giá thị trường chính thức. Mục tiêu là khảo sát dữ liệu, phân tích mối liên hệ và thử nghiệm mô hình hồi quy có thể tái lập; không nhằm cung cấp dịch vụ định giá hoặc khuyến nghị mua bán.

## 3. Mục tiêu và câu hỏi phân tích

Đồ án hướng đến các mục tiêu sau:

1. Khảo sát phạm vi, cấu trúc, chất lượng và mức độ thiếu dữ liệu của các tin rao căn hộ được gắn nhãn TP. Hồ Chí Minh.
2. Mô tả sự khác biệt của giá rao theo địa bàn, diện tích, số phòng ngủ, số phòng tắm và tháng đăng.
3. Đánh giá mối liên hệ giữa các thuộc tính căn hộ và trường giá rao; kiểm tra giới hạn của mô hình hồi quy tuyến tính.
4. So sánh mô hình OLS với hồi quy Huber để xem kết quả nhạy thế nào trước các giá trị cực đoan.
5. Phân cụm khám phá các tin rao theo đặc điểm căn hộ và xem xét liệu dữ liệu có đủ dài để phân tích, dự báo xu hướng theo thời gian hay không.

Các câu hỏi nghiên cứu tương ứng:

- Dữ liệu có bao phủ các địa bàn và khoảng thời gian nào; những trường nào thiếu hoặc có giá trị bất thường?
- Giá rao trong mẫu thay đổi ra sao theo diện tích, số phòng và nhãn quận/huyện?
- Mô hình OLS dự đoán trường giá rao tốt đến mức nào trên tập kiểm tra ngẫu nhiên cùng giai đoạn?
- Kết quả hệ số và sai số dự đoán thay đổi thế nào khi dùng sai số chuẩn HC3 hoặc hồi quy Huber?
- Có thể nhận diện nhóm tin rao có đặc điểm tương tự bằng phân cụm hay không, và các nhóm đó nên được diễn giải ở mức độ nào?

## 4. Dữ liệu

- **Nguồn:** [Vietnam Real Estates trên Kaggle](https://www.kaggle.com/datasets/yashdev01/vietnam-real-estates), phiên bản 1.
- **Quy mô nguồn:** 1.000.000 tin rao bất động sản trên toàn quốc, thời gian được mô tả từ tháng 06 đến tháng 12/2025.
- **Đơn vị quan sát:** một dòng tương ứng với một tin rao trong tệp dữ liệu; không xác định được liệu các tin giống hoặc gần giống có phải cùng một căn hộ hay không.
- **Phạm vi ban đầu:** 74.385 tin được gắn nhãn `Căn hộ chung cư` và `Hồ Chí Minh`.
- **Tập dùng cho phân tích và mô hình:** 54.706 dòng đầy đủ các biến bắt buộc. Không điền giá trị thiếu; 0 dòng trùng hoàn toàn được phát hiện trong phạm vi các cột nguồn đã kiểm tra.
- **Biến mục tiêu:** trường `price` trong nguồn, được phân tích ở dạng logarit cho mô hình hồi quy. Tài liệu nguồn không xác nhận đơn vị tiền tệ, cũng không nói rõ đây là tổng giá căn hộ hay giá theo diện tích.
- **Biến giải thích chính:** diện tích, số phòng ngủ, số phòng tắm, nhãn quận/huyện và tháng đăng tin.
- **Giới hạn bao phủ:** có 21 nhãn địa bàn trong tập đầy đủ biến; không có tin căn hộ Củ Chi. Cần Giờ và Hóc Môn chỉ lần lượt có 7 và 18 dòng trong tập này.
- **Giấy phép và rủi ro truy cập:** Kaggle ghi giấy phép CC BY-NC-SA 4.0. Cần ghi công và tuân thủ điều khoản khi sử dụng hoặc chia sẻ sản phẩm phái sinh. Nguồn không nêu URL tin gốc, cách thu thập chi tiết hoặc đơn vị của trường giá; đây là các rủi ro về khả năng xác minh và diễn giải.

## 5. Quy trình và kỹ thuật

Quy trình gồm: kiểm tra môi trường và nguồn → kiểm tra cấu trúc, phạm vi và dữ liệu thiếu → làm sạch và phân tích khám phá → tạo đặc trưng → chia tập huấn luyện/kiểm tra → xây dựng mô hình → đánh giá và chẩn đoán → phân tích độ nhạy → phân cụm khám phá → tổng hợp báo cáo.

Các bước xử lý chính:

- Giữ lại các dòng có nhãn loại căn hộ và địa bàn phù hợp; loại các dòng thiếu biến bắt buộc cho complete-case thay vì tự điền giá trị thiếu.
- Tạo hai bản dữ liệu để so sánh: nhánh giữ nguyên ngoại lệ và nhánh tham khảo có lọc 3σ. Theo quyết định trong đồ án, mô hình chính dùng nhánh giữ nguyên; không xóa ngoại lệ tự động.
- Mã hóa địa bàn theo one-hot, chia diện tích thành các nhóm phân vị để mô tả, và tạo bản chuẩn hóa z-score/Min-Max phục vụ khám phá.
- Dùng Spearman để mô tả tương quan; không diễn giải tương quan là quan hệ nhân quả.
- Dùng OLS với `log(price)` làm biến mục tiêu, diện tích liên tục, số phòng, địa bàn và tháng đăng làm biến giải thích. Tập dữ liệu được chia ngẫu nhiên 80/20 với `random_state=42`; chỉ số đánh giá tính trên thang log.
- So sánh OLS với baseline trung vị của tập huấn luyện và hồi quy Huber; dùng sai số chuẩn HC3 để kiểm tra độ nhạy của suy luận thống kê trước hiện tượng phương sai sai số thay đổi.
- Kiểm tra phần dư, dạng hàm, đa cộng tuyến và điểm ảnh hưởng. Phân cụm K-means mini-batch trên các biến đã biến đổi log và chuẩn hóa robust; chọn số cụm theo silhouette mẫu.
- Không tạo dự báo AR/ARIMA: dữ liệu chỉ có bảy kỳ tháng, không đủ cơ sở để kiểm định dự báo chuỗi thời gian đáng tin cậy.

## 6. Thực nghiệm và kết quả chính

Trên tập kiểm tra ngẫu nhiên, OLS đạt R² `0,4976` và MAE `0,3736` trên thang log giá; baseline trung vị có MAE `0,5277`. Hồi quy Huber đạt R² `0,5591` và MAE `0,3273` trên cùng tập kiểm tra. Đây là kết quả thăm dò trong cùng giai đoạn dữ liệu, không chứng minh khả năng dự báo giá tương lai.

Chẩn đoán cho thấy OLS có dấu hiệu vi phạm giả định về phương sai sai số và dạng hàm; nhiều quan sát có ảnh hưởng lớn. Với sai số chuẩn HC3, hệ số diện tích và số phòng tắm không có ý nghĩa thống kê ở ngưỡng 5%. Một số giá trị diện tích hoặc số phòng rất bất thường nhưng chưa được xác minh từ tin gốc. Vì vậy, không thể kết luận Huber là mô hình định giá đáng tin cậy chỉ dựa trên chỉ số holdout tốt hơn.

Phân tích mô tả ghi nhận trung vị trường giá thô trong mẫu tăng `10,11%` từ tháng 06 đến tháng 12/2025. Thay đổi này có thể phản ánh sự thay đổi cơ cấu tin rao, không nhất thiết là mức tăng giá của cùng loại căn hộ. Phân cụm khám phá chọn `k=2` với silhouette mẫu `0,2930`; các cụm phụ thuộc vào tập biến và cách chuẩn hóa, không phải phân khúc thị trường đã được xác nhận.

## 7. Sản phẩm và khả năng tái lập

Đồ án cung cấp các script Python theo từng bước, báo cáo audit và phân tích, các tệp CSV trung gian/đã xử lý, bảng dự đoán kiểm tra, bảng hệ số và chẩn đoán mô hình, kết quả gán cụm, cùng 12 biểu đồ có chú thích tiếng Việt. Quy trình có thể chạy lại với cùng tệp nguồn và các tham số ngẫu nhiên đã ghi nhận. Đồ án hiện không bao gồm ứng dụng web hay bảng điều khiển tương tác.

## 8. Giới hạn và phương án dự phòng

Kết quả hiện chỉ phù hợp cho bài tập phân tích thăm dò. Chưa xác minh được đơn vị và ý nghĩa của `price`; dữ liệu chỉ có bảy tháng, thiếu Củ Chi, có địa bàn rất ít mẫu và một số trường có giá trị bất thường. Chia tập ngẫu nhiên không đánh giá khả năng dự báo sang thời gian tương lai hoặc sang địa bàn chưa thấy.

Nếu không thể xác minh đơn vị giá hoặc chất lượng các giá trị bất thường, đồ án vẫn hoàn thành ở phạm vi **mô tả dữ liệu, so sánh mô hình thăm dò và trình bày giới hạn**, không chuyển kết quả thành giá trị tiền để tư vấn giao dịch. Hướng phát triển tiếp theo là bổ sung dữ liệu có nguồn gốc/đơn vị rõ ràng, thời gian dài hơn, bao phủ địa bàn đầy đủ; sau đó đánh giá lại bằng cách chia tập theo thời gian và theo khu vực.
