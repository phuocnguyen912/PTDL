# Báo cáo Prompt 01 — Audit dữ liệu rao căn hộ

- Thời điểm chạy: 2026-11-02T19:28:47+07:00
- Nguồn: [Vietnam Real Estates, Kaggle](https://www.kaggle.com/datasets/yashdev01/vietnam-real-estates), phiên bản 1.
- Giấy phép công bố: CC BY-NC-SA 4.0; cần ghi công và tuân thủ điều khoản nếu chia sẻ sản phẩm phái sinh.
- File nguồn: `data/raw/vietnam_real_estates_v1.zip`.
- Kaggle mô tả bộ này do TiniX AI thu thập/biên soạn, nhưng không nêu URL nguồn tin hoặc phương pháp thu thập chi tiết.
- Nguồn bổ sung đã rà soát: [Real Estate in Vietnam, Kaggle](https://www.kaggle.com/datasets/andyvo1009/real-estate-in-vietnam), giấy phép Apache 2.0; file bán có 42.257 dòng nhưng chỉ có `product_id`, `address`, `price`, `area`, `bedrooms_num`, `bathrooms_num`. Không có cột loại căn hộ/ngày đăng hay trường quận/tỉnh chuẩn hóa; không phát hiện tên TP.HCM trong địa chỉ khi kiểm tra token, nên không thể xác định chắc phạm vi. Không ghép vào bộ chính.
- Hai bộ căn hộ TP.HCM khác trên Kaggle được mô tả là dữ liệu Chotot năm 2021 nhưng ghi giấy phép Unknown; không dùng để bổ sung.
- Số dòng toàn bộ file: 1,000,000.
- Số dòng thuộc địa bàn được nhận diện là TP.HCM: 372,411.
- Khoảng ngày đăng TP.HCM: 2025-06-01 đến 2025-12-30.

## Kiểm tra cấu trúc

- Cột trong file (19): `name`, `description`, `property_type_name`, `province_name`, `district_name`, `ward_name`, `street_name`, `project_name`, `price`, `area`, `floor_count`, `frontage_width`, `house_depth`, `road_width`, `bedroom_count`, `bathroom_count`, `house_direction`, `balcony_direction`, `published_at`
- Cột bắt buộc còn thiếu: không có.
- Dữ liệu là tin rao; giá trong file chưa được coi là giá giao dịch.
- Chưa xóa trùng, điền thiếu hoặc lọc ngoại lệ ở bước audit này.

## Phân bố loại bất động sản trong TP.HCM được nhận diện

| Loại tài sản | Số tin |
|---|---:|
| Nhà | 234,904 |
| Căn hộ chung cư | 74,385 |
| Đất | 43,773 |
| Biệt thự/Nhà liền kề | 16,615 |
| Shophouse | 2,734 |

## Căn hộ chung cư: 74,385 tin

| Địa bàn trong dữ liệu | Số tin căn hộ |
|---|---:|
| Thủ Đức | 13,226 |
| 7 | 13,014 |
| Tân Phú | 4,947 |
| Bình Thạnh | 3,333 |
| 8 | 3,333 |
| Bình Chánh | 3,263 |
| Tân Bình | 3,123 |
| Nhà Bè | 2,737 |
| 1 | 2,323 |
| Bình Tân | 2,000 |
| 4 | 1,879 |
| 6 | 1,784 |
| Phú Nhuận | 1,735 |
| 10 | 1,368 |
| 12 | 1,217 |
| Gò Vấp | 1,086 |
| 11 | 957 |
| 5 | 911 |
| 3 | 604 |
| Cần Giờ | 30 |
| Hóc Môn | 20 |

## Địa bàn và số tin

- Giá trị `province_name` được nhận diện: {'Hồ Chí Minh': 372411}.
- Số tên địa bàn cấp `district_name`: 22.

| Địa bàn trong dữ liệu | Số tin |
|---|---:|
| Thủ Đức | 60,033 |
| 7 | 29,195 |
| Bình Thạnh | 28,977 |
| Gò Vấp | 28,252 |
| Tân Bình | 26,077 |
| Tân Phú | 23,186 |
| Bình Tân | 21,486 |
| 12 | 17,116 |
| Phú Nhuận | 16,828 |
| 1 | 15,617 |
| 3 | 12,359 |
| 10 | 10,840 |
| 8 | 10,607 |
| Nhà Bè | 9,948 |
| Bình Chánh | 9,741 |
| 6 | 5,612 |
| Củ Chi | 5,336 |
| 4 | 4,396 |
| 5 | 4,171 |
| Hóc Môn | 3,916 |
| 11 | 3,776 |
| Cần Giờ | 1,857 |

## Kiểm tra sơ bộ biến số và thời gian

- Min/max `price` trong các dòng TP.HCM: 3.15e+06 / 4.491e+14
- Min/max `area`: 3.611 / 2.994e+07
- Số tháng có tin đăng: 7.
- Số tháng có tin căn hộ: 7.
- Tài liệu nguồn không nêu đơn vị của `price`; mẫu dữ liệu có giá dạng số lớn nhưng chưa đủ để xác nhận đơn vị.

### Phân vị của giá và diện tích căn hộ (giá trị thô, chưa lọc)

| Biến | Min | P50 | P95 | P99 | Max |
|---|---:|---:|---:|---:|---:|
| price | 3.15e+06 | 4.9e+09 | 2.08e+10 | 4.9e+10 | 6.16e+13 |
| area | 6 | 75 | 146 | 255 | 1.7e+04 |

## Tỷ lệ thiếu trong các dòng TP.HCM

| Cột | Số thiếu |
|---|---:|
| area | 0 |
| bathroom_count | 150,415 |
| bedroom_count | 136,427 |
| district_name | 23,085 |
| price | 23,570 |
| property_type_name | 0 |
| province_name | 0 |
| published_at | 0 |
| ward_name | 59,095 |

### Tỷ lệ thiếu riêng cho căn hộ chung cư

| Cột | Số thiếu | Tỷ lệ |
|---|---:|---:|
| area | 0 | 0.0% |
| bathroom_count | 5,922 | 8.0% |
| bedroom_count | 3,881 | 5.2% |
| district_name | 11,495 | 15.5% |
| price | 4,112 | 5.5% |
| property_type_name | 0 | 0.0% |
| province_name | 0 | 0.0% |
| published_at | 0 | 0.0% |
| ward_name | 22,605 | 30.4% |

## Mẫu 5 dòng đầu/cuối

Chỉ hiển thị cột phân loại, địa bàn và biến số; không đưa tiêu đề/mô tả tin vào báo cáo.

### 5 dòng đầu của file

| Loại | Tỉnh/thành | Quận/huyện | Giá thô | Diện tích | PN | PT | Ngày đăng |
|---|---|---|---:|---:|---:|---:|---|
| Nhà | Hà Nội | Hoàng Mai | 10850000000.0 | 70.0 | nan | nan | 2025-06-24T07:19:17.785000 |
| Biệt thự/Nhà liền kề | Hà Nam | Phủ Lý | nan | 97.0 | 4.0 | 3.0 | 2025-10-21T14:34:19.757000 |
| Đất | Đà Nẵng | Ngũ Hành Sơn | 19500000000.0 | 105.0 | nan | nan | 2025-10-16T16:20:41.601000 |
| Nhà | Hồ Chí Minh | 1 | 19000000000.0 | 72.0 | nan | nan | 2025-06-19T02:45:17.993000 |
| Đất | Đà Nẵng | Ngũ Hành Sơn | 46000000000.0 | 128.0 | nan | nan | 2025-10-29T05:40:51.815000 |

### 5 dòng cuối của file

| Loại | Tỉnh/thành | Quận/huyện | Giá thô | Diện tích | PN | PT | Ngày đăng |
|---|---|---|---:|---:|---:|---:|---|
| Nhà | Hồ Chí Minh | 5 | 7500000000.0 | 40.0 | 5.0 | 4.0 | 2025-07-11T15:08:00.272000 |
| Đất | Hải Phòng | Kiến Thụy | 1590000000.0 | 61.8 | nan | nan | 2025-07-07T01:43:39.735000 |
| Căn hộ chung cư | Quảng Ninh | Hạ Long | 4200000000.0 | 90.0 | 3.0 | 2.0 | 2025-10-28T15:41:37.599000 |
| Shophouse | Hà Nội | Đông Anh | 15600000000.0 | 65.0 | 6.0 | 4.0 | 2025-11-13T20:18:38.743000 |
| Nhà | Hồ Chí Minh | Tân Phú | 7900000000.0 | 71.0 | 3.0 | 2.0 | 2025-11-01T20:20:04.914000 |

## Tự kiểm tra và giới hạn

- ĐẠT: tệp nguồn được đọc theo từng khối, không cần tạo dữ liệu mẫu.
- ĐẠT: các cột cốt lõi cho phân tích giá tin rao hiện diện.
- ĐẠT: có dòng được nhận diện tại TP.HCM.
- Chưa thể xác nhận dữ liệu bao phủ đầy đủ mọi quận/huyện; cần đối chiếu danh mục địa bàn và thời điểm thay đổi địa giới.
- Chưa đủ căn cứ diễn giải đơn vị giá hoặc đánh giá dữ liệu đại diện cho toàn thị trường.

Phạm vi phân tích tiếp theo dùng nhãn `Hồ Chí Minh` và `Căn hộ chung cư` có sẵn trong nguồn; kết quả không được hiểu là đại diện cho toàn TP.HCM.
