"""Audit dữ liệu rao căn hộ trước khi làm sạch hoặc xây dựng mô hình."""

from collections import Counter
from datetime import datetime
from pathlib import Path
import sys

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = ROOT / "data" / "raw" / "vietnam_real_estates_v1.zip"
REPORT = ROOT / "reports" / "step_01_data_audit_report.md"
EXPECTED_COLUMNS = {
    "property_type_name",
    "province_name",
    "district_name",
    "ward_name",
    "price",
    "area",
    "bedroom_count",
    "bathroom_count",
    "published_at",
}
SAFE_SAMPLE_COLUMNS = [
    "property_type_name",
    "province_name",
    "district_name",
    "price",
    "area",
    "bedroom_count",
    "bathroom_count",
    "published_at",
]


def audit_archive():
    """Đọc CSV theo từng khối, không nạp toàn bộ dữ liệu 1 triệu dòng vào RAM."""
    if not ARCHIVE.is_file():
        raise FileNotFoundError(f"Không tìm thấy dữ liệu nguồn: {ARCHIVE}")

    header = pd.read_csv(ARCHIVE, compression="zip", nrows=0, encoding="utf-8-sig")
    missing_columns = sorted(EXPECTED_COLUMNS - set(header.columns))
    if missing_columns:
        raise ValueError(f"Dữ liệu thiếu cột bắt buộc: {missing_columns}")

    total_rows = 0
    hcmc_rows = 0
    apartment_rows = 0
    missing_counts = Counter()
    district_counts = Counter()
    property_counts = Counter()
    apartment_district_counts = Counter()
    apartment_missing_counts = Counter()
    apartment_month_counts = Counter()
    apartment_prices = []
    apartment_areas = []
    month_counts = Counter()
    hcmc_prices = []
    hcmc_areas = []
    hcmc_dates = []
    safe_head = []
    safe_tail = []
    hcmc_provinces = Counter()

    reader = pd.read_csv(
        ARCHIVE,
        compression="zip",
        encoding="utf-8-sig",
        chunksize=50_000,
        low_memory=False,
    )
    for chunk in reader:
        total_rows += len(chunk)
        hcmc_mask = (
            chunk["province_name"]
            .astype("string")
            .str.normalize("NFC")
            .str.contains(r"ho chi minh|hồ chí minh|hcm", case=False, na=False)
        )
        hcmc = chunk.loc[hcmc_mask]
        hcmc_rows += len(hcmc)
        for column in EXPECTED_COLUMNS:
            missing_counts[column] += int(hcmc[column].isna().sum())

        hcmc_provinces.update(hcmc["province_name"].dropna().astype(str).value_counts().to_dict())
        district_counts.update(hcmc["district_name"].dropna().astype(str).value_counts().to_dict())
        property_counts.update(
            hcmc["property_type_name"].dropna().astype(str).value_counts().to_dict()
        )

        dates = pd.to_datetime(hcmc["published_at"], errors="coerce")
        hcmc_dates.extend(dates.dropna().tolist())
        month_counts.update(dates.dropna().dt.to_period("M").astype(str).value_counts().to_dict())

        apartments = hcmc.loc[hcmc["property_type_name"].eq("Căn hộ chung cư")]
        apartment_rows += len(apartments)
        apartment_district_counts.update(
            apartments["district_name"].dropna().astype(str).value_counts().to_dict()
        )
        for column in EXPECTED_COLUMNS:
            apartment_missing_counts[column] += int(apartments[column].isna().sum())
        apartment_dates = pd.to_datetime(apartments["published_at"], errors="coerce")
        apartment_month_counts.update(
            apartment_dates.dropna().dt.to_period("M").astype(str).value_counts().to_dict()
        )
        apartment_prices.extend(
            pd.to_numeric(apartments["price"], errors="coerce").dropna().tolist()
        )
        apartment_areas.extend(
            pd.to_numeric(apartments["area"], errors="coerce").dropna().tolist()
        )

        prices = pd.to_numeric(hcmc["price"], errors="coerce").dropna()
        areas = pd.to_numeric(hcmc["area"], errors="coerce").dropna()
        if not prices.empty:
            hcmc_prices.extend([float(prices.min()), float(prices.max())])
        if not areas.empty:
            hcmc_areas.extend([float(areas.min()), float(areas.max())])

        if len(safe_head) < 5:
            safe_head.extend(
                chunk.loc[:, SAFE_SAMPLE_COLUMNS].head(5 - len(safe_head)).to_dict("records")
            )
        if not chunk.empty:
            safe_tail = chunk.loc[:, SAFE_SAMPLE_COLUMNS].tail(5).to_dict("records")

    return {
        "columns": list(header.columns),
        "missing_columns": missing_columns,
        "total_rows": total_rows,
        "hcmc_rows": hcmc_rows,
        "apartment_rows": apartment_rows,
        "missing_counts": missing_counts,
        "district_counts": district_counts,
        "property_counts": property_counts,
        "apartment_district_counts": apartment_district_counts,
        "apartment_missing_counts": apartment_missing_counts,
        "apartment_month_counts": apartment_month_counts,
        "apartment_prices": apartment_prices,
        "apartment_areas": apartment_areas,
        "month_counts": month_counts,
        "hcmc_dates": hcmc_dates,
        "hcmc_prices": hcmc_prices,
        "hcmc_areas": hcmc_areas,
        "hcmc_provinces": hcmc_provinces,
        "safe_head": safe_head,
        "safe_tail": safe_tail,
    }


def render_report(result):
    """Viết báo cáo audit với số liệu thực tế và các giới hạn đã xác định."""
    date_values = result["hcmc_dates"]
    dates_text = (
        f"{min(date_values):%Y-%m-%d} đến {max(date_values):%Y-%m-%d}"
        if date_values
        else "không có ngày hợp lệ"
    )
    price_values = result["hcmc_prices"]
    area_values = result["hcmc_areas"]
    lines = [
        "# Báo cáo Prompt 01 — Audit dữ liệu rao căn hộ",
        "",
        f"- Thời điểm chạy: {datetime.now().astimezone().isoformat(timespec='seconds')}",
        "- Nguồn: [Vietnam Real Estates, Kaggle](https://www.kaggle.com/datasets/yashdev01/vietnam-real-estates), phiên bản 1.",
        "- Giấy phép công bố: CC BY-NC-SA 4.0; cần ghi công và tuân thủ điều khoản nếu chia sẻ sản phẩm phái sinh.",
        f"- File nguồn: `{ARCHIVE.relative_to(ROOT).as_posix()}`.",
        "- Kaggle mô tả bộ này do TiniX AI thu thập/biên soạn, nhưng không nêu URL nguồn tin "
        "hoặc phương pháp thu thập chi tiết.",
        "- Nguồn bổ sung đã rà soát: [Real Estate in Vietnam, Kaggle](https://www.kaggle.com/datasets/andyvo1009/real-estate-in-vietnam), giấy phép Apache 2.0; file bán có 42.257 dòng nhưng chỉ có `product_id`, `address`, `price`, `area`, `bedrooms_num`, `bathrooms_num`. Không có cột loại căn hộ/ngày đăng hay trường quận/tỉnh chuẩn hóa; không phát hiện tên TP.HCM trong địa chỉ khi kiểm tra token, nên không thể xác định chắc phạm vi. Không ghép vào bộ chính.",
        "- Hai bộ căn hộ TP.HCM khác trên Kaggle được mô tả là dữ liệu Chotot năm 2021 nhưng ghi giấy phép Unknown; không dùng để bổ sung.",
        f"- Số dòng toàn bộ file: {result['total_rows']:,}.",
        f"- Số dòng thuộc địa bàn được nhận diện là TP.HCM: {result['hcmc_rows']:,}.",
        f"- Khoảng ngày đăng TP.HCM: {dates_text}.",
        "",
        "## Kiểm tra cấu trúc",
        "",
        f"- Cột trong file ({len(result['columns'])}): "
        + ", ".join(f"`{column}`" for column in result["columns"]),
        f"- Cột bắt buộc còn thiếu: {result['missing_columns'] or 'không có'}.",
        "- Dữ liệu là tin rao; giá trong file chưa được coi là giá giao dịch.",
        "- Chưa xóa trùng, điền thiếu hoặc lọc ngoại lệ ở bước audit này.",
        "",
        "## Phân bố loại bất động sản trong TP.HCM được nhận diện",
        "",
        "| Loại tài sản | Số tin |",
        "|---|---:|",
    ]
    lines.extend(
        f"| {property_type} | {count:,} |"
        for property_type, count in result["property_counts"].most_common()
    )
    lines.extend(
        [
            "",
            f"## Căn hộ chung cư: {result['apartment_rows']:,} tin",
            "",
            "| Địa bàn trong dữ liệu | Số tin căn hộ |",
            "|---|---:|",
        ]
    )
    lines.extend(
        f"| {district} | {count:,} |"
        for district, count in result["apartment_district_counts"].most_common()
    )
    lines.extend(
        [
            "",
            "## Địa bàn và số tin",
            "",
            f"- Giá trị `province_name` được nhận diện: "
            f"{dict(result['hcmc_provinces']) or 'không tìm thấy'}.",
            f"- Số tên địa bàn cấp `district_name`: {len(result['district_counts'])}.",
            "",
            "| Địa bàn trong dữ liệu | Số tin |",
            "|---|---:|",
        ]
    )
    lines.extend(
        f"| {district} | {count:,} |"
        for district, count in result["district_counts"].most_common()
    )
    lines.extend(
        [
            "",
            "## Kiểm tra sơ bộ biến số và thời gian",
            "",
            f"- Min/max `price` trong các dòng TP.HCM: "
            f"{min(price_values):,.4g} / {max(price_values):,.4g}"
            if price_values
            else "- `price` không có giá trị số hợp lệ trong dòng TP.HCM.",
            f"- Min/max `area`: {min(area_values):,.4g} / {max(area_values):,.4g}"
            if area_values
            else "- `area` không có giá trị số hợp lệ trong dòng TP.HCM.",
            f"- Số tháng có tin đăng: {len(result['month_counts'])}.",
            f"- Số tháng có tin căn hộ: {len(result['apartment_month_counts'])}.",
            "- Tài liệu nguồn không nêu đơn vị của `price`; mẫu dữ liệu có giá dạng số lớn "
            "nhưng chưa đủ để xác nhận đơn vị.",
            "",
            "### Phân vị của giá và diện tích căn hộ (giá trị thô, chưa lọc)",
            "",
            "| Biến | Min | P50 | P95 | P99 | Max |",
            "|---|---:|---:|---:|---:|---:|",
        ]
    )
    for label, values in (
        ("price", result["apartment_prices"]),
        ("area", result["apartment_areas"]),
    ):
        if values:
            quantiles = np.quantile(values, [0, 0.5, 0.95, 0.99, 1])
            lines.append(
                f"| {label} | "
                + " | ".join(f"{value:,.4g}" for value in quantiles)
                + " |"
            )
    lines.extend(
        [
            "",
            "## Tỷ lệ thiếu trong các dòng TP.HCM",
            "",
            "| Cột | Số thiếu |",
            "|---|---:|",
        ]
    )
    lines.extend(
        f"| {column} | {count:,} |"
        for column, count in sorted(result["missing_counts"].items())
    )
    lines.extend(
        [
            "",
            "### Tỷ lệ thiếu riêng cho căn hộ chung cư",
            "",
            "| Cột | Số thiếu | Tỷ lệ |",
            "|---|---:|---:|",
        ]
    )
    lines.extend(
        f"| {column} | {count:,} | {count / result['apartment_rows']:.1%} |"
        for column, count in sorted(result["apartment_missing_counts"].items())
    )
    lines.extend(
        [
            "",
            "## Mẫu 5 dòng đầu/cuối",
            "",
            "Chỉ hiển thị cột phân loại, địa bàn và biến số; không đưa tiêu đề/mô tả tin vào báo cáo.",
            "",
            "### 5 dòng đầu của file",
            "",
            "| Loại | Tỉnh/thành | Quận/huyện | Giá thô | Diện tích | PN | PT | Ngày đăng |",
            "|---|---|---|---:|---:|---:|---:|---|",
        ]
    )
    for row in result["safe_head"]:
        values = [str(row.get(column, "")) for column in SAFE_SAMPLE_COLUMNS]
        lines.append("| " + " | ".join(value.replace("|", "\\|") for value in values) + " |")
    lines.extend(
        [
            "",
            "### 5 dòng cuối của file",
            "",
            "| Loại | Tỉnh/thành | Quận/huyện | Giá thô | Diện tích | PN | PT | Ngày đăng |",
            "|---|---|---|---:|---:|---:|---:|---|",
        ]
    )
    for row in result["safe_tail"]:
        values = [str(row.get(column, "")) for column in SAFE_SAMPLE_COLUMNS]
        lines.append("| " + " | ".join(value.replace("|", "\\|") for value in values) + " |")
    lines.extend(
        [
            "",
            "## Tự kiểm tra và giới hạn",
            "",
            "- ĐẠT: tệp nguồn được đọc theo từng khối, không cần tạo dữ liệu mẫu.",
            "- ĐẠT: các cột cốt lõi cho phân tích giá tin rao hiện diện.",
            f"- {'ĐẠT' if result['hcmc_rows'] else 'CHƯA ĐẠT'}: có dòng được nhận diện tại TP.HCM.",
            "- Chưa thể xác nhận dữ liệu bao phủ đầy đủ mọi quận/huyện; "
            "cần đối chiếu danh mục địa bàn và thời điểm thay đổi địa giới.",
            "- Chưa đủ căn cứ diễn giải đơn vị giá hoặc đánh giá dữ liệu đại diện "
            "cho toàn thị trường.",
            "",
            "Phạm vi phân tích tiếp theo dùng nhãn `Hồ Chí Minh` và `Căn hộ chung cư` có sẵn "
            "trong nguồn; kết quả không được hiểu là đại diện cho toàn TP.HCM.",
            "",
        ]
    )
    REPORT.write_text("\n".join(lines), encoding="utf-8")


def main():
    """Chạy audit, lưu báo cáo và kiểm tra đầu ra."""
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    result = audit_archive()
    render_report(result)
    assert result["total_rows"] > 0
    assert not result["missing_columns"]
    assert result["hcmc_rows"] > 0
    assert REPORT.is_file() and REPORT.stat().st_size > 0

    print(f"Đã audit {result['total_rows']:,} dòng.")
    print(f"TP.HCM nhận diện được {result['hcmc_rows']:,} dòng, "
          f"{len(result['district_counts'])} địa bàn cấp quận/huyện.")
    print(f"Đã lưu báo cáo: {REPORT.relative_to(ROOT)}")
    for district, count in result["district_counts"].most_common():
        print(f"  {district}: {count:,}")


if __name__ == "__main__":
    main()
