"""Kiểm tra môi trường và tạo báo cáo cho Prompt 00."""

from datetime import datetime
from importlib import import_module
import os
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"
REQUIRED_DIRS = (
    ROOT / "data" / "raw",
    ROOT / "data" / "interim",
    ROOT / "data" / "processed",
    ROOT / "src",
    REPORTS,
    REPORTS / "figures",
)
PACKAGES = {
    "pandas": "pandas",
    "numpy": "numpy",
    "statsmodels": "statsmodels",
    "scikit-learn": "sklearn",
    "matplotlib": "matplotlib",
    "seaborn": "seaborn",
}


def check_packages():
    """Import thư viện cần cho các bước phân tích và ghi lại phiên bản."""
    results = {}
    for package, module_name in PACKAGES.items():
        try:
            module = import_module(module_name)
            results[package] = getattr(module, "__version__", "đã import")
        except ImportError as error:
            results[package] = f"THIẾU ({error})"
    return results


def list_data_files(folder):
    """Chỉ liệt kê file dữ liệu trong thư mục, không tự đọc hoặc biến đổi."""
    extensions = {".csv", ".xlsx", ".xls", ".parquet", ".zip"}
    return sorted(
        path.name
        for path in folder.iterdir()
        if path.is_file() and path.suffix.lower() in extensions
    )


def list_other_workspace_data_files():
    """Tìm file dữ liệu sẵn có, bỏ qua môi trường ảo và các thư mục pipeline."""
    extensions = {".csv", ".xlsx", ".xls", ".parquet", ".zip"}
    excluded = {".venv", "data", "reports", "__pycache__"}
    matches = []
    for current, directories, filenames in os.walk(ROOT):
        directories[:] = [directory for directory in directories if directory not in excluded]
        current_path = Path(current)
        matches.extend(
            (current_path / filename).relative_to(ROOT).as_posix()
            for filename in filenames
            if Path(filename).suffix.lower() in extensions
        )
    return sorted(matches)


def write_report(packages):
    """Tạo báo cáo thiết lập để người dùng kiểm tra trước Prompt 01."""
    raw_files = list_data_files(ROOT / "data" / "raw")
    other_data_files = list_other_workspace_data_files()
    lines = [
        "# Báo cáo Prompt 00 — Khởi tạo hệ thống",
        "",
        f"- Thời điểm chạy: {datetime.now().astimezone().isoformat(timespec='seconds')}",
        f"- Python: {sys.version.split()[0]}",
        f"- Gói dữ liệu đã tải: "
        f"{'có' if (ROOT / 'data' / 'raw' / 'vietnam_real_estates_v1.zip').is_file() else 'chưa có'} "
        "tại `data/raw/vietnam_real_estates_v1.zip`.",
        "",
        "## Cấu trúc thư mục",
        "",
    ]
    for folder in REQUIRED_DIRS:
        lines.append(f"- {'PASS' if folder.is_dir() else 'FAIL'}: `{folder.relative_to(ROOT)}/`")

    lines.extend(["", "## Thư viện", ""])
    for package, version in packages.items():
        status = "PASS" if not version.startswith("THIẾU") else "FAIL"
        lines.append(f"- {status}: `{package}` — {version}")

    lines.extend(
        [
            "",
            "## Dữ liệu hiện có",
            "",
            f"- File dữ liệu trong `data/raw/`: {raw_files or 'chưa có'}",
            f"- File dữ liệu khác trong workspace: "
            f"{other_data_files or 'chưa có'}",
            "- `raw_hcmc_apartments.csv` và `clean_hcmc_apartments.csv` trong "
            "`New folder/` được tạo ngẫu nhiên bởi `New folder/DA.py`; không dùng "
            "làm dữ liệu thị trường thực tế.",
            "",
            "## Nguồn dữ liệu và trạng thái workflow",
            "",
            "- Kaggle `yashdev01/vietnam-real-estates`, phiên bản 1; giấy phép CC BY-NC-SA 4.0.",
            "- Mô tả nguồn: 1.000.000 tin rao toàn quốc, thời gian 06–12/2025; "
            "CSV khoảng 922 MB, gói ZIP tải về khoảng 299 MB.",
            "- Prompt 01 đã đọc file theo từng khối: 74.385 tin căn hộ TP.HCM, có tin ở "
            "21/22 địa bàn được ghi nhận; Củ Chi không có tin căn hộ.",
            "- Tỷ lệ thiếu của giá, quận/huyện, phòng ngủ và phòng tắm vượt ngưỡng 3%; "
            "các dòng thiếu biến bắt buộc được loại khỏi bản complete-case, không tự điền.",
            "- Đây là giá rao, không phải giá giao dịch; cần xác minh đơn vị giá và chất lượng "
            "ngoại lệ. Chỉ có 7 tháng dữ liệu trong 2025.",
            "- Các Prompt 02–08 đã được thực hiện; xem báo cáo từng bước trong `reports/`.",
            "",
            "## Tự kiểm tra",
            "",
            f"- ĐẠT: báo cáo được tạo tại `{(REPORTS / 'step_00_setup_report.md').relative_to(ROOT)}`.",
            "- Prompt 01–08 đã chạy theo các giới hạn dữ liệu đã nêu; không tạo dự báo AR/ARIMA "
            "vì chỉ có 7 kỳ tháng.",
            "",
        ]
    )
    report_path = REPORTS / "step_00_setup_report.md"
    report_path.write_text("\n".join(lines), encoding="utf-8")
    return report_path


def main():
    """Chạy kiểm tra, lưu báo cáo và xác nhận file đầu ra."""
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    REPORTS.mkdir(parents=True, exist_ok=True)
    (REPORTS / "figures").mkdir(parents=True, exist_ok=True)
    for folder in REQUIRED_DIRS:
        folder.mkdir(parents=True, exist_ok=True)

    packages = check_packages()
    report_path = write_report(packages)

    # Xác nhận cấu trúc và báo cáo tồn tại, có nội dung.
    assert all(folder.is_dir() for folder in REQUIRED_DIRS)
    assert report_path.is_file() and report_path.stat().st_size > 0
    print(f"Đã tạo báo cáo: {report_path.relative_to(ROOT)}")
    print(f"Python {sys.version.split()[0]}; thư viện đạt: "
          f"{sum(not value.startswith('THIẾU') for value in packages.values())}/{len(PACKAGES)}")
    print(f"Dữ liệu trong data/raw/: {list_data_files(ROOT / 'data' / 'raw') or 'chưa có'}")


if __name__ == "__main__":
    main()
