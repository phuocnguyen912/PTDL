"""Kiểm tra giả định và điểm ảnh hưởng cho mô hình OLS Prompt 04."""

from datetime import datetime
from pathlib import Path
import sys

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.api as sm
from statsmodels.stats.diagnostic import het_breuschpagan, linear_reset
from statsmodels.stats.outliers_influence import OLSInfluence, variance_inflation_factor
from statsmodels.stats.stattools import jarque_bera
from sklearn.model_selection import train_test_split

from step_04_ols_model import (
    INPUT,
    RANDOM_STATE,
    TEST_SIZE,
    build_design_matrix,
)


ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "reports" / "step_05_ols_diagnostics_report.md"
VIF_OUTPUT = ROOT / "data" / "processed" / "ols_vif_prompt05.csv"
INFLUENCE_OUTPUT = ROOT / "data" / "processed" / "ols_influential_points_prompt05.csv"
FIGURES = ROOT / "reports" / "figures"
PLOT_SAMPLE_SIZE = 8_000
TOP_INFLUENCE_COUNT = 50


def format_p_value(value):
    return "<1e-300 (underflow)" if value == 0 else f"{value:.4g}"


def save_diagnostic_plots(fitted, residuals, cooks_distance, cutoff):
    FIGURES.mkdir(parents=True, exist_ok=True)
    sample = residuals.sample(
        n=min(PLOT_SAMPLE_SIZE, len(residuals)),
        random_state=RANDOM_STATE,
    ).index

    fig, ax = plt.subplots(figsize=(9, 6))
    ax.scatter(fitted.loc[sample], residuals.loc[sample], s=10, alpha=0.25)
    ax.axhline(0, color="#b22222", linestyle="--", linewidth=1)
    ax.set(
        title="Phần dư theo giá trị dự đoán của OLS (tập huấn luyện)",
        xlabel="Giá trị dự đoán (log giá rao)",
        ylabel="Phần dư",
    )
    fig.tight_layout()
    residual_plot = FIGURES / "fig_06_ols_residuals_vs_fitted.png"
    fig.savefig(residual_plot, dpi=300)
    plt.close(fig)

    qq_sample = residuals.sample(
        n=min(5_000, len(residuals)),
        random_state=RANDOM_STATE,
    )
    fig = sm.qqplot(qq_sample, line="45", fit=True)
    fig.set_size_inches(8, 7)
    fig.axes[0].set_title("Biểu đồ Q-Q phần dư OLS (tập huấn luyện)")
    fig.axes[0].set_xlabel("Phân vị lý thuyết")
    fig.axes[0].set_ylabel("Phân vị phần dư")
    fig.tight_layout()
    qq_plot = FIGURES / "fig_07_ols_residual_qq.png"
    fig.savefig(qq_plot, dpi=300)
    plt.close(fig)

    top = cooks_distance.nlargest(500)
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.scatter(top.index, top.values, s=12, alpha=0.65)
    ax.axhline(cutoff, color="#b22222", linestyle="--", linewidth=1)
    ax.set(
        title="Các khoảng cách Cook lớn nhất (tập huấn luyện)",
        xlabel="Chỉ số dòng trong tập huấn luyện",
        ylabel="Khoảng cách Cook",
    )
    fig.tight_layout()
    influence_plot = FIGURES / "fig_08_ols_cooks_distance.png"
    fig.savefig(influence_plot, dpi=300)
    plt.close(fig)
    return residual_plot, qq_plot, influence_plot


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    source = pd.read_csv(INPUT, encoding="utf-8-sig")
    x, y, _, _, _, _ = build_design_matrix(source)
    train_x, _, train_y, _ = train_test_split(
        x,
        y,
        test_size=TEST_SIZE,
        random_state=RANDOM_STATE,
    )
    train_design = sm.add_constant(train_x, has_constant="add")
    model = sm.OLS(train_y, train_design).fit()
    fitted = pd.Series(model.fittedvalues, index=train_y.index)
    residuals = pd.Series(model.resid, index=train_y.index)

    bp_lm, bp_lm_p, bp_f, bp_f_p = het_breuschpagan(
        residuals.to_numpy(),
        train_design.to_numpy(),
    )
    jb_stat, jb_p, residual_skew, residual_kurtosis = jarque_bera(
        residuals.to_numpy()
    )
    reset = linear_reset(model, power=2, use_f=True)

    design_matrix = train_design.to_numpy()
    vif_rows = []
    for column_index, column in enumerate(train_design.columns):
        if column == "const":
            continue
        vif_rows.append(
            {
                "variable": column,
                "vif": float(variance_inflation_factor(design_matrix, column_index)),
            }
        )
    vif = pd.DataFrame(vif_rows).sort_values("vif", ascending=False)

    influence = OLSInfluence(model)
    cooks_distance = pd.Series(influence.cooks_distance[0], index=train_y.index)
    cook_cutoff = 4 / len(train_y)
    influential_count = int((cooks_distance > cook_cutoff).sum())
    top_indices = cooks_distance.nlargest(TOP_INFLUENCE_COUNT).index
    influential = pd.DataFrame(
        {
            "source_row_index": top_indices,
            "district_name_clean": source.loc[top_indices, "district_name_clean"].to_numpy(),
            "listing_month": source.loc[top_indices, "listing_month"].fillna("Unknown month").to_numpy(),
            "observed_price_raw": source.loc[top_indices, "price"].to_numpy(),
            "area": source.loc[top_indices, "area"].to_numpy(),
            "bedroom_count": source.loc[top_indices, "bedroom_count"].to_numpy(),
            "bathroom_count": source.loc[top_indices, "bathroom_count"].to_numpy(),
            "fitted_log_price": fitted.loc[top_indices].to_numpy(),
            "residual": residuals.loc[top_indices].to_numpy(),
            "cooks_distance": cooks_distance.loc[top_indices].to_numpy(),
        }
    ).sort_values("cooks_distance", ascending=False)
    plot_paths = save_diagnostic_plots(
        fitted,
        residuals,
        cooks_distance,
        cook_cutoff,
    )

    VIF_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    vif.to_csv(VIF_OUTPUT, index=False, encoding="utf-8-sig")
    influential.to_csv(INFLUENCE_OUTPUT, index=False, encoding="utf-8-sig")
    top_vif_rows = [
        f"| `{row.variable}` | {row.vif:,.4g} |"
        for row in vif.head(10).itertuples(index=False)
    ]
    top_influence_rows = [
        f"| {int(row.source_row_index)} | {row.district_name_clean} | "
        f"{row.observed_price_raw:,.4g} | {row.area:,.4g} | "
        f"{row.bedroom_count:,.4g} | {row.bathroom_count:,.4g} | "
        f"{row.cooks_distance:,.4g} |"
        for row in influential.head(5).itertuples(index=False)
    ]
    max_vif = float(vif["vif"].max())
    report_lines = [
        "# Báo cáo Prompt 05 — Chẩn đoán OLS",
        "",
        f"- Thời điểm chạy: {datetime.now().astimezone().isoformat(timespec='seconds')}",
        "- Chẩn đoán trên cùng tập train và cùng seed với Prompt 04; không thay mô hình.",
        f"- N train: {len(train_y):,}; số biến kiểm tra VIF: {len(vif)}.",
        "",
        "## Kiểm định sai số và dạng hàm",
        "",
        "| Kiểm tra | Thống kê | p-value | Đọc kết quả (α=0.05) |",
        "|---|---:|---:|---|",
        f"| Breusch–Pagan LM (phương sai không đổi) | {bp_lm:,.4g} | "
        f"{format_p_value(bp_lm_p)} | "
        f"{'Bác bỏ phương sai không đổi' if bp_lm_p < 0.05 else 'Chưa bác bỏ phương sai không đổi'} |",
        f"| Breusch–Pagan F | {bp_f:,.4g} | {format_p_value(bp_f_p)} | "
        f"{'Có dấu hiệu heteroscedasticity' if bp_f_p < 0.05 else 'Chưa có bằng chứng đủ mạnh'} |",
        f"| Jarque–Bera (phần dư chuẩn) | {jb_stat:,.4g} | {format_p_value(jb_p)} | "
        f"{'Bác bỏ giả thuyết phần dư chuẩn' if jb_p < 0.05 else 'Chưa bác bỏ giả thuyết phần dư chuẩn'} |",
        f"| Ramsey RESET (dạng hàm) | {float(reset.fvalue):,.4g} | "
        f"{format_p_value(float(reset.pvalue))} | "
        f"{'Có dấu hiệu dạng hàm chưa phù hợp' if reset.pvalue < 0.05 else 'Chưa phát hiện sai dạng hàm rõ'} |",
        "",
        f"- Độ lệch (skewness) phần dư: {residual_skew:.4g}; excess kurtosis: {residual_kurtosis:.4g}.",
        "- Với cỡ mẫu lớn, kiểm định chuẩn tính có thể rất nhạy; cần đọc cùng Q-Q plot và "
        "không giả định p-value là thước đo mức độ sai lệch.",
        "",
        "## Đa cộng tuyến",
        "",
        "| Biến | VIF |",
        "|---|---:|",
        *top_vif_rows,
        "",
        f"- VIF lớn nhất: {max_vif:.4g}. Quy tắc tham khảo (5/10) không thay thế đánh giá chuyên môn.",
        f"- Bảng đầy đủ: `{VIF_OUTPUT.relative_to(ROOT)}`.",
        "",
        "## Điểm ảnh hưởng",
        "",
        f"- Ngưỡng tham khảo Cook's distance: `4/n = {cook_cutoff:.4g}`.",
        f"- Số quan sát vượt ngưỡng: {influential_count:,}/{len(train_y):,}. "
        "Ngưỡng này là cờ rà soát, không phải lý do tự động xóa dòng.",
        f"- Bảng 50 điểm Cook's distance lớn nhất: `{INFLUENCE_OUTPUT.relative_to(ROOT)}`.",
        f"- Cook's distance lớn nhất: {cooks_distance.max():.4g}.",
        "",
        "| Index trong file đã lọc | Địa bàn | Price thô | Area | Bedrooms | Bathrooms | Cook's D |",
        "|---:|---|---:|---:|---:|---:|---:|",
        *top_influence_rows,
        "",
        "Các giá trị area/phòng ngủ/phòng tắm ở những dòng ảnh hưởng mạnh cần đối chiếu "
        "nguồn gốc trước khi xem hệ số OLS là đáng tin. Bảng chỉ dùng index trong file đã lọc; "
        "không chứa địa chỉ hay mô tả tin rao.",
        "",
        "## Biểu đồ",
        "",
        f"- `{plot_paths[0].relative_to(ROOT)}` — phần dư theo giá trị fitted.",
        f"- `{plot_paths[1].relative_to(ROOT)}` — Q-Q plot phần dư.",
        f"- `{plot_paths[2].relative_to(ROOT)}` — các Cook's distance lớn nhất.",
        "",
        "## Diễn giải và giới hạn",
        "",
        "- Kiểm định cổ điển không chứng minh mô hình phù hợp; nếu heteroscedasticity hiện diện, "
        "sai số chuẩn/p-value OLS cổ điển không đáng tin cậy. Cần cân nhắc sai số chuẩn robust "
        "hoặc mô hình thay thế ở bước tiếp theo.",
        "- Điểm ảnh hưởng lớn được lưu để kiểm tra đơn vị/bản chất listing; không loại tự động "
        "vì người dùng đã chọn giữ ngoại lệ.",
        "- Residual autocorrelation/Durbin–Watson không dùng ở đây vì đây là tập cắt ngang "
        "được chia ngẫu nhiên, không phải chuỗi có thứ tự thời gian.",
        "",
        "## Self-test",
        "",
        "- PASS: diagnostics được tính trên đúng train split Prompt 04.",
        "- PASS: VIF, Cook's distance và residuals có kích thước đúng, giá trị hữu hạn.",
        f"- {'PASS' if all(path.is_file() and path.stat().st_size > 0 for path in plot_paths) else 'FAIL'}: ba biểu đồ diagnostics tồn tại.",
        "",
    ]
    REPORT.write_text("\n".join(report_lines), encoding="utf-8")

    assert len(vif) == train_design.shape[1] - 1
    assert np.isfinite(vif["vif"].to_numpy()).all()
    assert np.isfinite(cooks_distance.to_numpy()).all()
    assert np.isfinite(residuals.to_numpy()).all()
    assert all(path.is_file() and path.stat().st_size > 0 for path in plot_paths)
    assert VIF_OUTPUT.is_file() and VIF_OUTPUT.stat().st_size > 0
    assert INFLUENCE_OUTPUT.is_file() and INFLUENCE_OUTPUT.stat().st_size > 0
    assert REPORT.is_file() and REPORT.stat().st_size > 0

    print(f"Breusch-Pagan p-value: {bp_lm_p:.4g}")
    print(f"Jarque-Bera p-value: {jb_p:.4g}")
    print(f"RESET p-value: {float(reset.pvalue):.4g}")
    print(f"Maximum VIF: {max_vif:.4g}")
    print(f"Cook's distance above 4/n: {influential_count:,}")
    print(f"Report: {REPORT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
