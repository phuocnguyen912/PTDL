"""Phân tích mô tả theo tháng; không tạo forecast khi chỉ có 7 kỳ."""

from datetime import datetime
from pathlib import Path
import sys

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "data" / "processed" / "hcmc_apartments_prompt03_preserve_extremes.csv"
OUTPUT = ROOT / "data" / "processed" / "monthly_listing_summary_prompt06.csv"
REPORT = ROOT / "reports" / "step_06_monthly_analysis_report.md"
FIGURES = ROOT / "reports" / "figures"
EXPECTED_MONTHS = 7


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    source = pd.read_csv(INPUT, encoding="utf-8-sig")
    dated = source.loc[source["listing_month"].notna()].copy()
    if dated.empty:
        raise ValueError("Không có tháng đăng hợp lệ để phân tích.")

    summary = (
        dated.groupby("listing_month")
        .agg(
            listings=("price", "size"),
            median_price_raw=("price", "median"),
            q1_price_raw=("price", lambda values: values.quantile(0.25)),
            q3_price_raw=("price", lambda values: values.quantile(0.75)),
            median_area=("area", "median"),
            districts=("district_name_clean", "nunique"),
        )
        .reset_index()
        .sort_values("listing_month")
        .reset_index(drop=True)
    )
    summary["median_price_change_pct"] = (
        summary["median_price_raw"].pct_change() * 100
    )
    known_months = summary["listing_month"].tolist()
    missing_month_count = int(source["listing_month"].isna().sum())
    first_month = summary.iloc[0]
    last_month = summary.iloc[-1]
    first_to_last_change_pct = (
        (last_month["median_price_raw"] / first_month["median_price_raw"]) - 1
    ) * 100

    FIGURES.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(
        summary["listing_month"],
        summary["median_price_raw"],
        marker="o",
        color="#3267a8",
    )
    ax.set(
        title="Trung vị giá rao căn hộ theo tháng",
        xlabel="Tháng đăng tin",
        ylabel="Trung vị trường giá thô",
    )
    ax.tick_params(axis="x", rotation=45)
    fig.tight_layout()
    median_plot = FIGURES / "fig_10_monthly_median_price_descriptive.png"
    fig.savefig(median_plot, dpi=300)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.bar(
        summary["listing_month"],
        summary["listings"],
        color="#40a080",
    )
    ax.set(
        title="Số tin rao căn hộ theo tháng",
        xlabel="Tháng đăng tin",
        ylabel="Số tin rao",
    )
    ax.tick_params(axis="x", rotation=45)
    fig.tight_layout()
    volume_plot = FIGURES / "fig_11_monthly_listing_volume_descriptive.png"
    fig.savefig(volume_plot, dpi=300)
    plt.close(fig)

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    summary.to_csv(OUTPUT, index=False, encoding="utf-8-sig")
    month_rows = [
        f"| {row.listing_month} | {int(row.listings):,} | "
        f"{row.median_price_raw:,.4g} | {row.q1_price_raw:,.4g} | "
        f"{row.q3_price_raw:,.4g} | {row.median_area:,.4g} | {int(row.districts)} |"
        for row in summary.itertuples(index=False)
    ]
    report_lines = [
        "# Báo cáo Prompt 06 — Phân tích mô tả theo tháng",
        "",
        f"- Thời điểm chạy: {datetime.now().astimezone().isoformat(timespec='seconds')}",
        "- Dữ liệu là giá rao; đơn vị `price` chưa được nguồn xác nhận.",
        f"- Số kỳ tháng hợp lệ: {len(summary)}; số dòng không có tháng phân tích được: "
        f"{missing_month_count:,} (giữ ngoài bảng chuỗi thời gian, không điền ngày).",
        f"- Các tháng: {', '.join(known_months)}.",
        "",
        "## Tóm tắt tháng",
        "",
        "| Tháng | Số tin | Median price thô | Q1 price | Q3 price | Median area | Số địa bàn |",
        "|---|---:|---:|---:|---:|---:|---:|",
        *month_rows,
        "",
        f"- Median price thô từ {first_month['listing_month']} đến "
        f"{last_month['listing_month']} thay đổi {first_to_last_change_pct:+.2f}% "
        "(mô tả mẫu tin, không phải chỉ số giá thị trường).",
        f"- CSV: `{OUTPUT.relative_to(ROOT)}`.",
        f"- Median price: `{median_plot.relative_to(ROOT)}`.",
        f"- Volume: `{volume_plot.relative_to(ROOT)}`.",
        "",
        "## Giới hạn chuỗi thời gian",
        "",
        f"- Chỉ có {len(summary)} điểm tháng (06–12/2025), không đủ chu kỳ để ước lượng "
        "và xác nhận AR/ARIMA đáng tin cậy; không tạo forecast.",
        "- Thay đổi median có thể do cơ cấu địa bàn/diện tích/phòng ngủ của tin đăng thay đổi, "
        "không nhất thiết do giá của cùng loại căn hộ biến động.",
        "- Dữ liệu không đại diện cho giá giao dịch, không bao phủ căn hộ Củ Chi, "
        "và không đủ cơ sở suy rộng sang 2026.",
        "",
        "## Self-test",
        "",
        f"- {'PASS' if len(summary) == EXPECTED_MONTHS else 'FAIL'}: xác nhận {EXPECTED_MONTHS} tháng quan sát, không forecast.",
        f"- {'PASS' if int(summary['listings'].sum()) == len(dated) else 'FAIL'}: số tin tổng hợp khớp số dòng có tháng.",
        f"- {'PASS' if median_plot.is_file() and median_plot.stat().st_size > 0 and volume_plot.is_file() and volume_plot.stat().st_size > 0 else 'FAIL'}: biểu đồ tồn tại.",
        "",
    ]
    REPORT.write_text("\n".join(report_lines), encoding="utf-8")

    assert len(summary) == EXPECTED_MONTHS
    assert int(summary["listings"].sum()) == len(dated)
    assert summary["median_price_raw"].gt(0).all()
    assert median_plot.is_file() and median_plot.stat().st_size > 0
    assert volume_plot.is_file() and volume_plot.stat().st_size > 0
    assert OUTPUT.is_file() and OUTPUT.stat().st_size > 0
    assert REPORT.is_file() and REPORT.stat().st_size > 0
    print(f"Months: {len(summary)}; listings with valid month: {len(dated):,}")
    print(f"First-to-last median change: {first_to_last_change_pct:+.2f}% (descriptive)")
    print("AR/ARIMA forecast: skipped (insufficient time periods)")
    print(f"Report: {REPORT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
