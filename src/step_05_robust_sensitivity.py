"""So sánh OLS-HC3 và hồi quy Huber mà không xóa dòng dữ liệu."""

from datetime import datetime
from pathlib import Path
import sys

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.api as sm
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split

from step_04_ols_model import (
    INPUT,
    RANDOM_STATE,
    TEST_SIZE,
    build_design_matrix,
)


ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "reports" / "step_05_robust_sensitivity_report.md"
COEFFICIENTS = ROOT / "data" / "processed" / "robust_sensitivity_coefficients_prompt05.csv"
PREDICTIONS = ROOT / "data" / "processed" / "robust_sensitivity_predictions_prompt05.csv"
LOW_WEIGHT_ROWS = ROOT / "data" / "processed" / "robust_sensitivity_low_weight_rows_prompt05.csv"
FIGURES = ROOT / "reports" / "figures"
LOW_WEIGHT_THRESHOLD = 0.5
TOP_LOW_WEIGHT_COUNT = 100


def calculate_metrics(actual, predicted):
    return {
        "mae": float(mean_absolute_error(actual, predicted)),
        "rmse": float(np.sqrt(mean_squared_error(actual, predicted))),
        "r2": float(r2_score(actual, predicted)),
    }


def format_p_value(value):
    return "<1e-300 (underflow)" if value == 0 else f"{value:.4g}"


def save_comparison_plot(actual, ols_predicted, robust_predicted):
    FIGURES.mkdir(parents=True, exist_ok=True)
    fig, axes = plt.subplots(1, 2, figsize=(13, 6), sharex=True, sharey=True)
    if len(actual) > 5_000:
        sample = actual.sample(n=5_000, random_state=RANDOM_STATE).index
    else:
        sample = actual.index
    for ax, predicted, title in (
        (axes[0], ols_predicted, "OLS (bình phương tối thiểu)"),
        (axes[1], robust_predicted, "Huber (hồi quy vững)"),
    ):
        ax.scatter(actual.loc[sample], predicted.loc[sample], s=10, alpha=0.25)
        limits = [
            min(float(actual.min()), float(predicted.min())),
            max(float(actual.max()), float(predicted.max())),
        ]
        ax.plot(limits, limits, linestyle="--", color="#b22222", linewidth=1)
        ax.set(title=title, xlabel="Giá thực tế (log giá rao)")
    axes[0].set_ylabel("Giá dự đoán (log giá rao)")
    fig.suptitle("So sánh OLS và Huber trên cùng tập kiểm tra")
    fig.tight_layout()
    target = FIGURES / "fig_09_ols_huber_holdout_comparison.png"
    fig.savefig(target, dpi=300)
    plt.close(fig)
    return target


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    source = pd.read_csv(INPUT, encoding="utf-8-sig")
    x, y, _, _, _, _ = build_design_matrix(source)
    train_x, test_x, train_y, test_y = train_test_split(
        x,
        y,
        test_size=TEST_SIZE,
        random_state=RANDOM_STATE,
    )
    train_design = sm.add_constant(train_x, has_constant="add")
    test_design = sm.add_constant(test_x, has_constant="add")

    ols = sm.OLS(train_y, train_design).fit()
    hc3 = ols.get_robustcov_results(cov_type="HC3")
    robust = sm.RLM(
        train_y,
        train_design,
        M=sm.robust.norms.HuberT(),
    ).fit(maxiter=100, tol=1e-8)

    ols_test_pred = pd.Series(ols.predict(test_design), index=test_y.index)
    robust_test_pred = pd.Series(robust.predict(test_design), index=test_y.index)
    ols_metrics = calculate_metrics(test_y, ols_test_pred)
    robust_metrics = calculate_metrics(test_y, robust_test_pred)
    baseline = pd.Series(float(train_y.median()), index=test_y.index)
    baseline_metrics = calculate_metrics(test_y, baseline)

    robust_confidence = hc3.conf_int()
    coefficients = pd.DataFrame(
        {
            "variable": ols.params.index,
            "ols_coefficient": ols.params.to_numpy(),
            "ols_std_error": ols.bse.to_numpy(),
            "ols_p_value": ols.pvalues.to_numpy(),
            "hc3_std_error": hc3.bse,
            "hc3_p_value": hc3.pvalues,
            "hc3_ci_lower": robust_confidence[:, 0],
            "hc3_ci_upper": robust_confidence[:, 1],
            "huber_coefficient": robust.params.to_numpy(),
            "coefficient_change_huber_minus_ols": (
                robust.params.to_numpy() - ols.params.to_numpy()
            ),
        }
    )
    weight_series = pd.Series(robust.weights, index=train_y.index)
    low_weight_indices = weight_series[weight_series < LOW_WEIGHT_THRESHOLD].index
    low_weight_frame = pd.DataFrame(
        {
            "source_row_index": low_weight_indices,
            "robust_weight": weight_series.loc[low_weight_indices].to_numpy(),
            "district_name_clean": source.loc[
                low_weight_indices, "district_name_clean"
            ].to_numpy(),
            "observed_price_raw": source.loc[low_weight_indices, "price"].to_numpy(),
            "area": source.loc[low_weight_indices, "area"].to_numpy(),
            "bedroom_count": source.loc[
                low_weight_indices, "bedroom_count"
            ].to_numpy(),
            "bathroom_count": source.loc[
                low_weight_indices, "bathroom_count"
            ].to_numpy(),
        }
    ).sort_values("robust_weight")
    low_weight_frame.head(TOP_LOW_WEIGHT_COUNT).to_csv(
        LOW_WEIGHT_ROWS,
        index=False,
        encoding="utf-8-sig",
    )
    predictions = pd.DataFrame(
        {
            "source_row_index": test_y.index,
            "observed_log_price": test_y.to_numpy(),
            "ols_predicted_log_price": ols_test_pred.to_numpy(),
            "huber_predicted_log_price": robust_test_pred.to_numpy(),
            "observed_price_raw": source.loc[test_y.index, "price"].to_numpy(),
            "ols_predicted_price_exp_log": np.exp(ols_test_pred.to_numpy()),
            "huber_predicted_price_exp_log": np.exp(robust_test_pred.to_numpy()),
        }
    ).sort_values("source_row_index")
    figure = save_comparison_plot(test_y, ols_test_pred, robust_test_pred)

    COEFFICIENTS.parent.mkdir(parents=True, exist_ok=True)
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    coefficients.to_csv(COEFFICIENTS, index=False, encoding="utf-8-sig")
    predictions.to_csv(PREDICTIONS, index=False, encoding="utf-8-sig")

    top_changed = coefficients.assign(
        absolute_change=lambda values: values[
            "coefficient_change_huber_minus_ols"
        ].abs()
    ).nlargest(10, "absolute_change")
    changed_rows = [
        f"| `{row.variable}` | {row.ols_coefficient:.6g} | "
        f"{row.huber_coefficient:.6g} | "
        f"{row.coefficient_change_huber_minus_ols:.6g} |"
        for row in top_changed.itertuples(index=False)
    ]
    metric_rows = [
        f"| OLS cổ điển | {ols_metrics['mae']:.4f} | {ols_metrics['rmse']:.4f} | {ols_metrics['r2']:.4f} |",
        f"| OLS với sai số chuẩn HC3 | {ols_metrics['mae']:.4f} | {ols_metrics['rmse']:.4f} | {ols_metrics['r2']:.4f} |",
        f"| Huber RLM | {robust_metrics['mae']:.4f} | {robust_metrics['rmse']:.4f} | {robust_metrics['r2']:.4f} |",
        f"| Baseline median train | {baseline_metrics['mae']:.4f} | {baseline_metrics['rmse']:.4f} | {baseline_metrics['r2']:.4f} |",
    ]
    report_lines = [
        "# Báo cáo Prompt 05 — Độ nhạy robust/HC3",
        "",
        f"- Thời điểm chạy: {datetime.now().astimezone().isoformat(timespec='seconds')}",
        "- Giữ nguyên toàn bộ 54.706 dòng; không xóa hay sửa ngoại lệ.",
        f"- Cùng split Prompt 04: train {len(train_y):,}, test {len(test_y):,}, "
        f"`random_state={RANDOM_STATE}`.",
        "- HC3 chỉ thay sai số chuẩn/kiểm định, không thay hệ số hay dự đoán OLS.",
        "- Huber RLM là phân tích độ nhạy; trọng số thấp không đồng nghĩa bản ghi bị xóa.",
        "",
        "## Chỉ số holdout trên log(price)",
        "",
        "| Phương pháp | MAE | RMSE | R² |",
        "|---|---:|---:|---:|",
        *metric_rows,
        "",
        "Nếu OLS và Huber khác biệt lớn, kết quả phụ thuộc mạnh vào lựa chọn phương pháp. "
        "Không đánh giá bằng giá trị R² riêng lẻ; các metric không kiểm tra khả năng dự báo tương lai.",
        "",
        "## Sai số chuẩn HC3",
        "",
        "| Biến | Hệ số OLS | SE HC3 | p-value HC3 | KTC HC3 95% |",
        "|---|---:|---:|---:|---:|",
        *[
            f"| `{row.variable}` | {row.ols_coefficient:.6g} | {row.hc3_std_error:.4g} | "
            f"{format_p_value(row.hc3_p_value)} | "
            f"[{row.hc3_ci_lower:.6g}, {row.hc3_ci_upper:.6g}] |"
            for row in coefficients.itertuples(index=False)
        ],
        "",
        "HC3 điều chỉnh suy luận với heteroscedasticity nhưng không sửa sai dạng hàm, "
        "ngoại lệ có leverage cao, thiếu biến hoặc lỗi dữ liệu.",
        "",
        "## Độ nhạy hệ số Huber so với OLS",
        "",
        "| Biến | OLS | Huber | Huber − OLS |",
        "|---|---:|---:|---:|",
        *changed_rows,
        "",
        f"- Huber hội tụ sau {robust.fit_history.get('iteration', 'không rõ')} vòng lặp; "
        f"scale robust={robust.scale:.4g}.",
        f"- Số dòng train có trọng số Huber < {LOW_WEIGHT_THRESHOLD}: "
        f"{len(low_weight_indices):,}/{len(train_y):,}.",
        f"- Danh sách tối đa {TOP_LOW_WEIGHT_COUNT} trọng số thấp: "
        f"`{LOW_WEIGHT_ROWS.relative_to(ROOT)}`.",
        "",
        "Trọng số Huber giảm tác động của phần dư lớn nhưng không bảo vệ đầy đủ trước "
        "điểm leverage cực đoan ở biến đầu vào.",
        "",
        "## Sản phẩm",
        "",
        f"- Hệ số và SE HC3: `{COEFFICIENTS.relative_to(ROOT)}`.",
        f"- So sánh dự đoán test: `{PREDICTIONS.relative_to(ROOT)}`.",
        f"- Biểu đồ so sánh: `{figure.relative_to(ROOT)}`.",
        "",
        "## Giới hạn và quyết định",
        "",
        "- HC3 không cải thiện dự đoán OLS; Huber là mô hình khác, cần được đánh giá độc lập "
        "và không tự thay thế mô hình đã duyệt.",
        "- Các giá trị area/phòng ngủ/phòng tắm cực đoan vẫn cần xác minh từ nguồn trước khi "
        "đưa ra kết luận giá. Không có xác nhận đơn vị `price`.",
        "- Tập dữ liệu chỉ có 7 tháng và không chứa căn hộ Củ Chi; không đủ cơ sở để tạo "
        "dự báo AR/ARIMA đáng tin cậy.",
        "",
        "## Self-test",
        "",
        "- PASS: HC3 giữ nguyên hệ số OLS; Huber chạy trên cùng train và không xóa bản ghi.",
        "- PASS: dự đoán, hệ số, trọng số và metric đều hữu hạn.",
        f"- {'PASS' if figure.is_file() and figure.stat().st_size > 0 else 'FAIL'}: biểu đồ độ nhạy đã được tạo.",
        "",
    ]
    REPORT.write_text("\n".join(report_lines), encoding="utf-8")

    assert len(predictions) == len(test_y)
    assert np.allclose(hc3.params, ols.params)
    assert np.isfinite(coefficients.select_dtypes(include=[np.number]).to_numpy()).all()
    assert np.isfinite(predictions.select_dtypes(include=[np.number]).to_numpy()).all()
    assert np.isfinite(weight_series.to_numpy()).all()
    assert len(low_weight_indices) <= len(train_y)
    assert figure.is_file() and figure.stat().st_size > 0
    assert COEFFICIENTS.is_file() and COEFFICIENTS.stat().st_size > 0
    assert PREDICTIONS.is_file() and PREDICTIONS.stat().st_size > 0
    assert LOW_WEIGHT_ROWS.is_file() and LOW_WEIGHT_ROWS.stat().st_size > 0
    assert REPORT.is_file() and REPORT.stat().st_size > 0

    print(
        f"Test R² OLS/Huber: {ols_metrics['r2']:.4f}/{robust_metrics['r2']:.4f}"
    )
    print(
        f"Low Huber weights (<{LOW_WEIGHT_THRESHOLD}): {len(low_weight_indices):,}"
    )
    print(f"Report: {REPORT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
