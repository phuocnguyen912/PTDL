"""Khám phá và làm sạch dữ liệu căn hộ theo lựa chọn không tự điền giá trị thiếu."""

from datetime import datetime
from pathlib import Path
import sys

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = ROOT / "data" / "raw" / "vietnam_real_estates_v1.zip"
INTERIM = ROOT / "data" / "interim"
PROCESSED = ROOT / "data" / "processed"
FIGURES = ROOT / "reports" / "figures"
REPORT = ROOT / "reports" / "step_02_eda_cleaning_report.md"
LOCATION_COLUMNS = [
    "property_type_name",
    "province_name",
    "district_name",
    "ward_name",
    "price",
    "area",
    "bedroom_count",
    "bathroom_count",
    "floor_count",
    "published_at",
]
REQUIRED_FOR_MODEL = [
    "price",
    "area",
    "bedroom_count",
    "bathroom_count",
    "district_name",
]
NUMERIC_COLUMNS = ["price", "area", "bedroom_count", "bathroom_count", "floor_count"]


def load_apartment_listings():
    """Lọc tin căn hộ TP.HCM, chỉ giữ cột phân tích và bỏ nội dung mô tả khỏi đầu ra."""
    chunks = []
    total_rows = 0
    for chunk in pd.read_csv(
        ARCHIVE,
        compression="zip",
        encoding="utf-8-sig",
        chunksize=50_000,
        low_memory=False,
    ):
        total_rows += len(chunk)
        province = (
            chunk["province_name"]
            .astype("string")
            .str.normalize("NFC")
            .str.strip()
        )
        property_type = (
            chunk["property_type_name"]
            .astype("string")
            .str.normalize("NFC")
            .str.strip()
        )
        mask = province.eq("Hồ Chí Minh") & property_type.eq("Căn hộ chung cư")
        if mask.any():
            chunks.append(chunk.loc[mask].copy())

    if not chunks:
        raise ValueError("Không tìm thấy tin căn hộ TP.HCM theo nhãn trong dữ liệu.")

    source = pd.concat(chunks, ignore_index=True)
    original_rows = len(source)
    source_column_count = len(source.columns)
    missing_before = source.loc[:, LOCATION_COLUMNS].isna().sum()

    # Chỉ xóa các dòng giống hệt nhau ở mọi cột nguồn; không gộp tin tương tự.
    source = source.drop_duplicates().copy()
    exact_duplicates = original_rows - len(source)
    source_is_unique = not source.duplicated().any()
    scoped = source.loc[:, LOCATION_COLUMNS].copy()

    for column in NUMERIC_COLUMNS:
        scoped[column] = pd.to_numeric(scoped[column], errors="coerce")
    scoped["published_at"] = pd.to_datetime(scoped["published_at"], errors="coerce")
    scoped["district_name_clean"] = scoped["district_name"].astype("string").str.strip()
    numeric_district = scoped["district_name_clean"].str.fullmatch(r"\d+", na=False)
    scoped.loc[numeric_district, "district_name_clean"] = (
        "Quận " + scoped.loc[numeric_district, "district_name_clean"]
    )
    scoped["listing_month"] = scoped["published_at"].dt.to_period("M").astype("string")

    invalid_numeric = (
        scoped["price"].le(0)
        | scoped["area"].le(0)
        | scoped["bedroom_count"].lt(0)
        | scoped["bathroom_count"].lt(0)
    ).fillna(False)
    complete_mask = scoped[REQUIRED_FOR_MODEL].notna().all(axis=1)
    complete_mask &= ~invalid_numeric
    complete = scoped.loc[complete_mask].copy()
    complete = complete.replace([np.inf, -np.inf], np.nan)
    complete = complete.dropna(subset=REQUIRED_FOR_MODEL)

    if complete.empty:
        raise ValueError("Không còn dòng đầy đủ để phân tích sau khi lọc giá trị thiếu.")

    return {
        "total_source_rows": total_rows,
        "source_column_count": source_column_count,
        "original_apartment_rows": original_rows,
        "exact_duplicates": exact_duplicates,
        "source_is_unique": source_is_unique,
        "missing_before": missing_before,
        "scoped": scoped,
        "complete": complete,
        "invalid_numeric_rows": int(invalid_numeric.sum()),
    }


def make_outlier_variants(complete):
    """So sánh nhánh giữ nguyên với nhánh lọc giá/diện tích ngoài μ ± 3σ."""
    sigma_rules = {}
    strict_mask = pd.Series(True, index=complete.index)
    for column in ("price", "area"):
        mean = float(complete[column].mean())
        std = float(complete[column].std(ddof=0))
        lower = mean - 3 * std
        upper = mean + 3 * std
        outside = ~complete[column].between(lower, upper)
        sigma_rules[column] = {
            "mean": mean,
            "std": std,
            "lower": lower,
            "upper": upper,
            "outside_count": int(outside.sum()),
        }
        strict_mask &= ~outside

    strict = complete.loc[strict_mask].copy()
    preserved = complete.copy()
    return strict, preserved, sigma_rules


def save_figures(complete):
    """Tạo biểu đồ mô tả dữ liệu thô hợp lệ, không dùng để kết luận nhân quả."""
    sns.set_theme(style="whitegrid")

    positive_price = complete.loc[complete["price"] > 0, "price"]
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.hist(np.log10(positive_price), bins=40, color="#3267a8", alpha=0.85)
    ax.set(
        title="Phân bố giá rao căn hộ (trường giá thô, thang log10)",
        xlabel="log10(trường price)",
        ylabel="Số tin rao",
    )
    fig.tight_layout()
    fig.savefig(FIGURES / "fig_01_price_distribution.png", dpi=300)
    plt.close(fig)

    order = (
        complete.groupby("district_name_clean")["price"]
        .median()
        .sort_values()
        .index.tolist()
    )
    fig, ax = plt.subplots(figsize=(15, 8))
    sns.boxplot(
        data=complete,
        x="district_name_clean",
        y="price",
        order=order,
        showfliers=False,
        color="#74a9cf",
        ax=ax,
    )
    ax.set_yscale("log")
    ax.set(
        title="Phân bố giá rao căn hộ theo quận/huyện trong dữ liệu",
        xlabel="Quận/huyện theo nhãn nguồn",
        ylabel="Trường giá thô (thang log)",
    )
    ax.tick_params(axis="x", rotation=55)
    fig.tight_layout()
    fig.savefig(FIGURES / "fig_02_price_by_district.png", dpi=300)
    plt.close(fig)

    month_counts = complete["listing_month"].value_counts().sort_index()
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.bar(month_counts.index.astype(str), month_counts.values, color="#40a080")
    ax.set(
        title="Số tin rao căn hộ theo tháng đăng",
        xlabel="Tháng đăng",
        ylabel="Số tin rao",
    )
    ax.tick_params(axis="x", rotation=45)
    fig.tight_layout()
    fig.savefig(FIGURES / "fig_03_monthly_listing_volume.png", dpi=300)
    plt.close(fig)


def write_report(result, strict, preserved, sigma_rules):
    """Ghi log trước/sau, thống kê, lựa chọn chưa chốt và kết quả self-test."""
    scoped = result["scoped"]
    complete = result["complete"]
    missing_before = result["missing_before"]
    district_stats = (
        complete.groupby("district_name_clean")["price"]
        .agg(["count", "median", "mean"])
        .sort_values("median")
    )
    missing_rows = []
    for column, count in missing_before.items():
        missing_rows.append(
            f"| `{column}` | {int(count):,} | {count / result['original_apartment_rows']:.1%} |"
        )
    district_rows = [
        f"| {district} | {int(row['count']):,} | {row['median']:,.4g} | {row['mean']:,.4g} |"
        for district, row in district_stats.iterrows()
    ]
    rule_rows = [
        f"| `{column}` | {rule['mean']:,.4g} | {rule['std']:,.4g} | "
        f"{rule['lower']:,.4g} | {rule['upper']:,.4g} | {rule['outside_count']:,} |"
        for column, rule in sigma_rules.items()
    ]
    lines = [
        "# Báo cáo Prompt 02 — Phân tích khám phá dữ liệu và làm sạch",
        "",
        f"- Thời điểm chạy: {datetime.now().astimezone().isoformat(timespec='seconds')}",
        "- Nguồn: Kaggle `yashdev01/vietnam-real-estates`, phiên bản 1; giấy phép CC BY-NC-SA 4.0.",
        "- Phạm vi: các dòng gắn nhãn `Hồ Chí Minh` và `Căn hộ chung cư` trong dữ liệu nguồn.",
        "- Không điền giá trị thiếu; không dùng dữ liệu mô phỏng trong `New folder/`.",
        "",
        "## Đối chiếu trước và sau",
        "",
        "| Giai đoạn | Số dòng | Số cột |",
        "|---|---:|---:|",
        f"| Toàn bộ nguồn trước lọc | {result['total_source_rows']:,} | {result['source_column_count']} |",
        f"| Căn hộ TP.HCM theo nhãn nguồn | {result['original_apartment_rows']:,} | {result['source_column_count']} |",
        f"| Sau khử trùng và chỉ giữ cột phân tích | {len(scoped):,} | {len(scoped.columns)} |",
        f"| Bản ghi đầy đủ dữ liệu, đủ biến và hợp lệ | {len(complete):,} | {len(complete.columns)} |",
        f"| Nhánh 3σ (`price` và `area`) | {len(strict):,} | {len(strict.columns)} |",
        f"| Nhánh giữ nguyên ngoại lệ | {len(preserved):,} | {len(preserved.columns)} |",
        f"| Trùng chính xác đã bỏ | {result['exact_duplicates']:,} | — |",
        f"| Bị loại do thiếu/giá trị không hợp lệ | {len(scoped) - len(complete):,} | — |",
        "",
        "Bản ghi trùng chỉ được nhận diện khi mọi cột nguồn giống hệt nhau. "
        "Không có mã tin đáng tin cậy để dò tin đăng lại gần giống.",
        "",
        "## Tỷ lệ thiếu trước khi lọc",
        "",
        "| Cột | Số thiếu | Tỷ lệ |",
        "|---|---:|---:|",
        *missing_rows,
        "",
        "Các biến bắt buộc cho mô hình ở giai đoạn thăm dò là `price`, `area`, "
        "`bedroom_count`, `bathroom_count`, `district_name`. Các dòng thiếu biến "
        "này bị loại khỏi bản ghi đầy đủ dữ liệu (complete-case); không điền bằng "
        "trung vị/giá trị phổ biến nhất vì tỷ lệ thiếu "
        "vượt 3%. `ward_name` không dùng ở mô hình này và được giữ nguyên nếu thiếu.",
        "",
        "## Thống kê mô tả trên bản ghi đầy đủ dữ liệu (đơn vị giá chưa xác minh)",
        "",
        "| Quận/huyện theo nhãn nguồn | Số tin | Trung vị của `price` thô | Trung bình của `price` thô |",
        "|---|---:|---:|---:|",
        *district_rows,
        "",
        f"- Tháng đăng quan sát được: {', '.join(complete['listing_month'].dropna().sort_values().unique())}.",
        "- Trung vị và trung bình chỉ mô tả giá rao trong tập tin đăng; không đại diện cho giá giao dịch.",
        "",
        "## Đối chiếu ngoại lệ 3σ",
        "",
        "Ngưỡng dùng cho từng biến là `μ − 3σ` đến `μ + 3σ`, trong đó `σ` là độ lệch "
        "chuẩn tổng thể (`ddof=0`). Đây chỉ là một nhánh so sánh, không mặc định là "
        "quy tắc đúng cho phân phối giá nhà lệch phải.",
        "",
        "| Biến | μ | σ | Ngưỡng dưới | Ngưỡng trên | Ngoài ngưỡng |",
        "|---|---:|---:|---:|---:|---:|",
        *rule_rows,
        "",
        f"- Nhánh 3σ loại {len(complete) - len(strict):,} dòng; nhánh giữ nguyên không "
        "loại ngoại lệ thống kê.",
        "- Cần duyệt nhánh sử dụng trước Prompt 03. Không xóa giá trị cực đoan chỉ vì "
        "cao/thấp; cần xác minh đơn vị và bản chất tin rao trước khi diễn giải.",
        "",
        "## Biểu đồ",
        "",
        "- `reports/figures/fig_01_price_distribution.png` — phân bố log10 của trường giá thô.",
        "- `reports/figures/fig_02_price_by_district.png` — phân bố theo nhãn quận/huyện nguồn.",
        "- `reports/figures/fig_03_monthly_listing_volume.png` — số tin theo tháng đăng.",
        "",
        "## Tự kiểm tra",
        "",
        f"- {'ĐẠT' if len(complete) > 0 else 'CHƯA ĐẠT'}: bản ghi đầy đủ dữ liệu không rỗng.",
        f"- {'ĐẠT' if not complete[REQUIRED_FOR_MODEL].isna().any().any() else 'CHƯA ĐẠT'}: "
        "không còn thiếu ở biến bắt buộc.",
        f"- {'ĐẠT' if result['source_is_unique'] else 'CHƯA ĐẠT'}: không còn dòng trùng chính xác trong các cột nguồn.",
        f"- {'ĐẠT' if all((FIGURES / name).is_file() and (FIGURES / name).stat().st_size > 0 for name in ('fig_01_price_distribution.png', 'fig_02_price_by_district.png', 'fig_03_monthly_listing_volume.png')) else 'CHƯA ĐẠT'}: đã tạo đủ ba biểu đồ.",
        "",
        "## Điểm dừng trước Prompt 03",
        "",
        "- Chọn nhánh `3sigma_strict` hoặc `preserve_extremes`.",
        "- Xác nhận tiếp tục với giá rao và chấp nhận độ tin cậy hạn chế do nguồn không công bố "
        "đơn vị giá/phương pháp thu thập chi tiết.",
        "- Kết quả không bao phủ căn hộ Củ Chi; không được diễn giải là mô hình đủ mọi quận.",
        "",
    ]
    REPORT.write_text("\n".join(lines), encoding="utf-8")


def main():
    """Chạy EDA, tạo hai nhánh dữ liệu và kiểm thử các điều kiện đầu ra."""
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    for folder in (INTERIM, PROCESSED, FIGURES):
        folder.mkdir(parents=True, exist_ok=True)

    result = load_apartment_listings()
    scoped = result["scoped"].copy()
    complete = result["complete"].copy()
    strict, preserved, sigma_rules = make_outlier_variants(complete)

    # Không lưu tiêu đề, mô tả, địa chỉ đường phố hoặc nội dung tin rao.
    for name, frame in (
        ("hcmc_apartments_scoped.csv", scoped),
        ("hcmc_apartments_complete_cases.csv", complete),
        ("hcmc_apartments_3sigma_strict.csv", strict),
        ("hcmc_apartments_preserve_extremes.csv", preserved),
    ):
        target = INTERIM / name if name.endswith("_scoped.csv") else PROCESSED / name
        frame.to_csv(target, index=False, encoding="utf-8-sig")

    save_figures(complete)
    write_report(result, strict, preserved, sigma_rules)

    # Self-test về nội dung dữ liệu, hai nhánh ngoại lệ và file đầu ra.
    assert len(complete) > 0
    assert not complete[REQUIRED_FOR_MODEL].isna().any().any()
    assert result["source_is_unique"]
    assert len(strict) <= len(preserved)
    assert REPORT.is_file() and REPORT.stat().st_size > 0
    assert all(
        (FIGURES / name).is_file() and (FIGURES / name).stat().st_size > 0
        for name in (
            "fig_01_price_distribution.png",
            "fig_02_price_by_district.png",
            "fig_03_monthly_listing_volume.png",
        )
    )

    print(f"Tin căn hộ TP.HCM: {len(scoped):,}")
    print(f"Complete-case không điền thiếu: {len(complete):,}")
    print(f"Nhánh 3σ: {len(strict):,}; giữ ngoại lệ: {len(preserved):,}")
    print(f"Báo cáo: {REPORT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
