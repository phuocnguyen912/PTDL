"""Mã hóa, rời rạc hóa, scaling và tương quan cho nhánh giữ nguyên ngoại lệ."""

from datetime import datetime
from pathlib import Path
import re
import sys
import unicodedata

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from sklearn.preprocessing import MinMaxScaler, StandardScaler


ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "data" / "processed" / "hcmc_apartments_preserve_extremes.csv"
OUTPUT = ROOT / "data" / "processed" / "hcmc_apartments_prompt03_preserve_extremes.csv"
REPORT = ROOT / "reports" / "step_03_feature_engineering_report.md"
CORRELATION_CSV = ROOT / "reports" / "step_03_spearman_correlation.csv"
FIGURES = ROOT / "reports" / "figures"
NUMERIC_FEATURES = ["area", "bedroom_count", "bathroom_count"]
CORRELATION_COLUMNS = ["price", "area", "bedroom_count", "bathroom_count"]


def safe_feature_name(value):
    """Tạo tên cột ASCII ổn định từ nhãn danh mục, tránh tên cột trùng."""
    normalized = unicodedata.normalize(
        "NFKD", str(value).replace("Đ", "D").replace("đ", "d")
    )
    ascii_value = normalized.encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^A-Za-z0-9]+", "_", ascii_value).strip("_")


def engineer_features(frame):
    """Tạo các biến dẫn xuất mà không thay đổi giá trị gốc hoặc số dòng."""
    if frame.empty:
        raise ValueError("Tệp đầu vào không có bản ghi.")
    if frame[CORRELATION_COLUMNS + ["district_name_clean"]].isna().any().any():
        raise ValueError("Tệp đầu vào còn thiếu biến bắt buộc từ Prompt 02.")
    if (frame[["price", "area"]] <= 0).any().any():
        raise ValueError("price và area phải dương trước khi biến đổi.")

    engineered = frame.copy()
    quantiles = engineered["area"].quantile([0, 0.25, 0.5, 0.75, 1]).to_numpy()
    area_edges = pd.Index(quantiles).drop_duplicates().to_numpy(dtype=float)
    if len(area_edges) < 2:
        raise ValueError("Không đủ giá trị diện tích riêng biệt để rời rạc hóa.")

    area_labels = [f"Q{index + 1}" for index in range(len(area_edges) - 1)]
    engineered["area_bin"] = pd.cut(
        engineered["area"],
        bins=area_edges,
        labels=area_labels,
        include_lowest=True,
        duplicates="drop",
    )
    if engineered["area_bin"].isna().any():
        raise ValueError("Có diện tích không được gán vào nhóm tứ phân vị.")

    reference_district = engineered["district_name_clean"].value_counts().idxmax()
    other_districts = sorted(
        set(engineered["district_name_clean"]) - {reference_district}
    )
    district_categories = [reference_district, *other_districts]
    district_values = pd.Categorical(
        engineered["district_name_clean"],
        categories=district_categories,
        ordered=False,
    )
    district_dummies = pd.get_dummies(
        district_values,
        prefix="district",
        drop_first=True,
        dtype="int8",
    )
    district_names = {
        column: f"district__{safe_feature_name(column.removeprefix('district_'))}"
        for column in district_dummies.columns
    }
    if len(set(district_names.values())) != len(district_names):
        raise ValueError("Tên cột mã hóa địa bàn bị trùng sau chuẩn hóa.")
    district_dummies = district_dummies.rename(columns=district_names)
    engineered = pd.concat([engineered, district_dummies], axis=1)

    area_dummies = pd.get_dummies(
        engineered["area_bin"],
        prefix="area_bin",
        drop_first=True,
        dtype="int8",
    )
    engineered = pd.concat([engineered, area_dummies], axis=1)

    scaler_statistics = {}
    for suffix, scaler in (
        ("z", StandardScaler()),
        ("minmax", MinMaxScaler()),
    ):
        scaled = scaler.fit_transform(engineered[NUMERIC_FEATURES])
        for index, column in enumerate(NUMERIC_FEATURES):
            output_column = f"{column}_{suffix}"
            engineered[output_column] = scaled[:, index]
        if suffix == "z":
            scaler_statistics = {
                column: {
                    "mean": float(scaler.mean_[index]),
                    "scale": float(scaler.scale_[index]),
                }
                for index, column in enumerate(NUMERIC_FEATURES)
            }

    correlation = engineered[CORRELATION_COLUMNS].corr(method="spearman")
    area_summary = (
        engineered.groupby("area_bin", observed=False)
        .agg(
            listings=("price", "size"),
            area_min=("area", "min"),
            area_max=("area", "max"),
            median_price=("price", "median"),
        )
        .reset_index()
    )
    district_mapping = [
        {
            "district_label": district,
            "feature_column": "(reference; all district indicators = 0)"
            if district == reference_district
            else f"district__{safe_feature_name(district)}",
            "is_reference": district == reference_district,
            "listing_count": int(
                engineered["district_name_clean"].eq(district).sum()
            ),
        }
        for district in district_categories
    ]
    return (
        engineered,
        correlation,
        area_summary,
        area_edges,
        district_mapping,
        reference_district,
        scaler_statistics,
    )


def save_correlation_plot(correlation):
    sns.set_theme(style="white")
    fig, ax = plt.subplots(figsize=(8, 6))
    sns.heatmap(
        correlation,
        annot=True,
        fmt=".2f",
        cmap="vlag",
        vmin=-1,
        vmax=1,
        center=0,
        square=True,
        ax=ax,
    )
    labels = {
        "price": "Giá rao",
        "area": "Diện tích",
        "bedroom_count": "Số phòng ngủ",
        "bathroom_count": "Số phòng tắm",
    }
    ax.set_title("Tương quan Spearman giữa giá rao và đặc điểm căn hộ")
    ax.set_xticklabels([labels[label.get_text()] for label in ax.get_xticklabels()])
    ax.set_yticklabels([labels[label.get_text()] for label in ax.get_yticklabels()])
    fig.tight_layout()
    target = FIGURES / "fig_04_spearman_correlation.png"
    fig.savefig(target, dpi=300)
    plt.close(fig)
    return target


def write_report(
    source,
    engineered,
    correlation,
    area_summary,
    area_edges,
    district_mapping,
    reference_district,
    scaler_statistics,
    figure,
):
    area_rows = [
        f"| {row.area_bin} | {int(row.listings):,} | {row.area_min:,.2f} | "
        f"{row.area_max:,.2f} | {row.median_price:,.4g} |"
        for row in area_summary.itertuples(index=False)
    ]
    district_rows = [
        f"| {item['district_label']} | {item['feature_column']} | "
        f"{'Có' if item['is_reference'] else 'Không'} | {item['listing_count']:,} |"
        for item in district_mapping
    ]
    scaler_rows = [
        f"| `{column}` | {values['mean']:,.4g} | {values['scale']:,.4g} |"
        for column, values in scaler_statistics.items()
    ]
    correlation_rows = [
        f"| `{row}` | "
        + " | ".join(f"{correlation.loc[row, column]:.3f}" for column in correlation.columns)
        + " |"
        for row in correlation.index
    ]
    correlation_header = "| Biến | " + " | ".join(
        f"`{column}`" for column in correlation.columns
    ) + " |"
    lines = [
        "# Báo cáo Prompt 03 — Mã hóa và biến đổi đặc trưng",
        "",
        f"- Thời điểm chạy: {datetime.now().astimezone().isoformat(timespec='seconds')}",
        "- Nhánh đầu vào đã được người dùng chọn: `preserve_extremes`.",
        "- Không loại ngoại lệ, không điền thiếu, không thay đổi số dòng hoặc các giá trị gốc.",
        f"- Đầu vào: `{INPUT.relative_to(ROOT)}` ({len(source):,} dòng, {len(source.columns)} cột).",
        f"- Đầu ra: `{OUTPUT.relative_to(ROOT)}` ({len(engineered):,} dòng, {len(engineered.columns)} cột).",
        "- `price` vẫn là trường giá rao có đơn vị chưa xác minh; không được diễn giải là giá giao dịch.",
        "",
        "## Rời rạc hóa diện tích",
        "",
        "Chia `area` thành tối đa 4 nhóm theo các phân vị 0%, 25%, 50%, 75% và 100%. "
        "Nếu các ngưỡng trùng nhau, nhóm thừa được gộp. Biến `area_bin` được giữ để "
        "diễn giải; các biến giả dùng nhóm nhỏ nhất làm nhóm tham chiếu.",
        "",
        f"- Các ngưỡng diện tích quan sát: {', '.join(f'{edge:,.4g}' for edge in area_edges)}.",
        "",
        "| Nhóm | Số tin | Min area | Max area | Median price thô |",
        "|---|---:|---:|---:|---:|",
        *area_rows,
        "",
        "## Mã hóa địa bàn",
        "",
        "Địa bàn là biến danh nghĩa nên được mã hóa one-hot, không gán số thứ tự. "
        f"Nhóm tham chiếu (địa bàn có nhiều tin nhất): **{reference_district}**. "
        "Cột tham chiếu được lược bỏ để tránh đồng tuyến tính hoàn hảo với intercept.",
        "",
        "| Nhãn địa bàn | Cột đặc trưng | Tham chiếu | Số tin |",
        "|---|---|---:|---:|",
        *district_rows,
        "",
        "## Scaling",
        "",
        "Tạo cả z-score (`*_z`) và Min-Max [0, 1] (`*_minmax`) cho `area`, "
        "`bedroom_count` và `bathroom_count`. Không scale `price`, vì đây là biến "
        "mục tiêu và đơn vị chưa xác minh.",
        "",
        "| Biến | Mean dùng cho z-score | Scale (độ lệch chuẩn) |",
        "|---|---:|---:|",
        *scaler_rows,
        "",
        "Các tham số trên được fit trên toàn bộ tập thăm dò để đáp ứng bước EDA. "
        "Nếu đánh giá dự báo bằng train/test hoặc cross-validation, phải fit lại "
        "scaler chỉ trên từng tập train bên trong pipeline để tránh leakage.",
        "",
        "## Tương quan Spearman",
        "",
        "Dùng Spearman trên các trường số gốc để hạn chế ảnh hưởng của lệch phân phối "
        "và ngoại lệ. Tương quan chỉ mô tả liên hệ đơn biến, không chứng minh nhân quả "
        "hay quan hệ tuyến tính.",
        "",
        correlation_header,
        "|---|" + "---:|" * len(correlation.columns),
        *correlation_rows,
        "",
        f"- Ma trận: `{CORRELATION_CSV.relative_to(ROOT)}`.",
        f"- Heatmap: `{figure.relative_to(ROOT)}`.",
        "",
        "## Giới hạn sử dụng",
        "",
        "- Giá trị gốc được giữ nguyên; đơn vị `price` và phương pháp thu thập không được nguồn xác nhận.",
        "- Dữ liệu chỉ gồm tin rao tháng 06–12/2025, nhãn căn hộ TP.HCM của nguồn; "
        "không có tin căn hộ Củ Chi trong tập complete-case.",
        "- Một số địa bàn có rất ít mẫu (Cần Giờ 7 tin, Hóc Môn 18 tin sau complete-case); "
        "hệ số riêng cho các nhóm này sẽ rất thiếu ổn định.",
        "- Không dùng các biến one-hot area cùng `area` liên tục trong cùng một mô hình; "
        "đó là hai cách biểu diễn thay thế của diện tích.",
        "- Z-score/Min-Max hiện phục vụ EDA; mô hình có đánh giá holdout cần pipeline "
        "fit theo tập train.",
        "",
        "## Self-test",
        "",
        f"- PASS: giữ nguyên {len(source):,} dòng, không lọc thêm ngoại lệ.",
        "- PASS: giá và diện tích gốc giữ nguyên; các biến bắt buộc không bị thiếu.",
        "- PASS: one-hot địa bàn dùng nhóm tham chiếu và không tạo cột tên trùng.",
        "- PASS: mỗi dòng được gán đúng một nhóm diện tích; các biến scale hữu hạn.",
        f"- {'PASS' if figure.is_file() and figure.stat().st_size > 0 else 'FAIL'}: heatmap đã được tạo.",
        "",
        "## Điểm dừng trước Prompt 04",
        "",
        "- Duyệt lựa chọn biến cho mô hình: `area` liên tục hay nhóm `area_bin`; "
        "không đưa cả hai vào cùng một mô hình.",
        "- Chốt biến mục tiêu: giá rao thô (đơn vị chưa xác minh) hay biến đổi mục tiêu "
        "có giải thích rõ. Không trình bày kết quả như giá giao dịch.",
        "",
    ]
    REPORT.write_text("\n".join(lines), encoding="utf-8")


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    FIGURES.mkdir(parents=True, exist_ok=True)

    source = pd.read_csv(INPUT, encoding="utf-8-sig")
    (
        engineered,
        correlation,
        area_summary,
        area_edges,
        district_mapping,
        reference_district,
        scaler_statistics,
    ) = engineer_features(source)
    figure = save_correlation_plot(correlation)

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    CORRELATION_CSV.parent.mkdir(parents=True, exist_ok=True)
    engineered.to_csv(OUTPUT, index=False, encoding="utf-8-sig")
    correlation.to_csv(CORRELATION_CSV, encoding="utf-8-sig")
    write_report(
        source,
        engineered,
        correlation,
        area_summary,
        area_edges,
        district_mapping,
        reference_district,
        scaler_statistics,
        figure,
    )

    district_feature_columns = [
        column for column in engineered.columns if column.startswith("district__")
    ]
    area_feature_columns = [
        column for column in engineered.columns if column.startswith("area_bin_")
    ]
    scaled_columns = [
        f"{column}_{suffix}"
        for column in NUMERIC_FEATURES
        for suffix in ("z", "minmax")
    ]
    assert len(engineered) == len(source)
    assert engineered["price"].equals(source["price"])
    assert engineered["area"].equals(source["area"])
    assert not engineered[CORRELATION_COLUMNS + ["district_name_clean"]].isna().any().any()
    assert len(district_feature_columns) == source["district_name_clean"].nunique() - 1
    assert len(area_feature_columns) == engineered["area_bin"].nunique() - 1
    assert not engineered[scaled_columns].isna().any().any()
    assert np.isfinite(engineered[scaled_columns].to_numpy()).all()
    assert correlation.shape == (len(CORRELATION_COLUMNS), len(CORRELATION_COLUMNS))
    assert np.isfinite(correlation.to_numpy()).all()
    assert figure.is_file() and figure.stat().st_size > 0
    assert OUTPUT.is_file() and OUTPUT.stat().st_size > 0
    assert CORRELATION_CSV.is_file() and CORRELATION_CSV.stat().st_size > 0
    assert REPORT.is_file() and REPORT.stat().st_size > 0

    print(f"Input branch: {INPUT.relative_to(ROOT)} ({len(source):,} rows)")
    print(f"Prompt 03 output: {OUTPUT.relative_to(ROOT)} ({len(engineered.columns)} columns)")
    print(f"District reference: {reference_district}")
    print(f"Report: {REPORT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
