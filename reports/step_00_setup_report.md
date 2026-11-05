# Báo cáo Prompt 00 — Khởi tạo hệ thống

- Thời điểm chạy: 2026-11-02T19:28:06+07:00
- Python: 3.11.9
- Gói dữ liệu đã tải: có tại `data/raw/vietnam_real_estates_v1.zip`.

## Cấu trúc thư mục

- PASS: `data\raw/`
- PASS: `data\interim/`
- PASS: `data\processed/`
- PASS: `src/`
- PASS: `reports/`
- PASS: `reports\figures/`

## Thư viện

- PASS: `pandas` — 3.1.0
- PASS: `numpy` — 2.4.6
- PASS: `statsmodels` — 0.15.0
- PASS: `scikit-learn` — 1.9.1
- PASS: `matplotlib` — 3.11.2
- PASS: `seaborn` — 0.13.2

## Dữ liệu hiện có

- File dữ liệu trong `data/raw/`: ['vietnam_real_estates_v1.zip']
- File dữ liệu khác trong workspace: chưa có
- `raw_hcmc_apartments.csv` và `clean_hcmc_apartments.csv` trong `New folder/` được tạo ngẫu nhiên bởi `New folder/DA.py`; không dùng làm dữ liệu thị trường thực tế.

## Nguồn dữ liệu và trạng thái workflow

- Kaggle `yashdev01/vietnam-real-estates`, phiên bản 1; giấy phép CC BY-NC-SA 4.0.
- Mô tả nguồn: 1.000.000 tin rao toàn quốc, thời gian 06–12/2025; CSV khoảng 922 MB, gói ZIP tải về khoảng 299 MB.
- Prompt 01 đã đọc file theo từng khối: 74.385 tin căn hộ TP.HCM, có tin ở 21/22 địa bàn được ghi nhận; Củ Chi không có tin căn hộ.
- Tỷ lệ thiếu của giá, quận/huyện, phòng ngủ và phòng tắm vượt ngưỡng 3%; các dòng thiếu biến bắt buộc được loại khỏi bản complete-case, không tự điền.
- Đây là giá rao, không phải giá giao dịch; cần xác minh đơn vị giá và chất lượng ngoại lệ. Chỉ có 7 tháng dữ liệu trong 2025.
- Các Prompt 02–08 đã được thực hiện; xem báo cáo từng bước trong `reports/`.

## Tự kiểm tra

- ĐẠT: báo cáo được tạo tại `reports\step_00_setup_report.md`.
- Prompt 01–08 đã chạy theo các giới hạn dữ liệu đã nêu; không tạo dự báo AR/ARIMA vì chỉ có 7 kỳ tháng.
