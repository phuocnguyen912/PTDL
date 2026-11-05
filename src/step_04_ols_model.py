"""Fit và đánh giá OLS thăm dò cho giá rao căn hộ TP.HCM."""

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


ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "data" / "processed" / "hcmc_apartments_prompt03_preserve_extremes.csv"
COEFFICIENTS = ROOT / "data" / "processed" / "ols_coefficients_prompt04.csv"
PREDICTIONS = ROOT / "data" / "processed" / "ols_test_predictions_prompt04.csv"
REPORT = ROOT / "reports" / "step_04_ols_report.md"
FIGURES = ROOT / "reports" / "figures"
TARGET = "price"
CONTINUOUS_FEATURES = ["area", "bedroom_count", "bathroom_count"]
TEST_SIZE = 0.2
RANDOM_STATE = 42


def build_design_matrix(frame):
    """Lấy các biến đã duyệt và tạo biến giả tháng với nhóm tham chiếu rõ ràng."""
    required = CONTINUOUS_FEATURES + [
        "price",
        "district_name_clean",
    ]
    if frame[required].isna().any().any():
        raise ValueError("Tệp Prompt 03 còn thiếu biến dùng cho OLS.")
    if (frame[TARGET] <= 0).any():
        raise ValueError("log(price) yêu cầu tất cả giá trị price phải dương.")

    district_columns = [
        column for column in frame.columns if column.startswith("district__")
    ]
    if not district_columns:
        raise ValueError("Không tìm thấy các cột one-hot quận/huyện từ Prompt 03.")

    x = frame[CONTINUOUS_FEATURES + district_columns].astype(float).copy()
    raw_months = frame["listing_month"].astype("string")
    valid_months = sorted(raw_months.dropna().unique())
    missing_month_count = int(raw_months.isna().sum())
    month_categories = valid_months + (
        ["Unknown month"] if missing_month_count else []
    )
    month_strings = raw_months.fillna("Unknown month").astype(str)
    month_values = pd.Categorical(
        month_strings,
        categories=month_categories,
        ordered=False,
    )
    month_dummies = pd.get_dummies(
        month_values,
        prefix="month",
        drop_first=True,
        dtype="int8",
    )
    month_reference = valid_months[0] if valid_months else "Unknown month"
    x = pd.concat([x, month_dummies.astype(float)], axis=1)
    if not x.columns.is_unique:
        raise ValueError("Tên biến giải thích bị trùng.")

    y = np.log(frame[TARGET].astype(float))
    return (
        x,
        y,
        district_columns,
        month_categories,
        month_reference,
        missing_month_count,
    )


def calculate_metrics(actual, predicted):
    return {
        "mae": float(mean_absolute_error(actual, predicted)),
        "rmse": float(np.sqrt(mean_squared_error(actual, predicted))),
        "r2": float(r2_score(actual, predicted)),
    }


def format_p_value(value):
    return "<1e-300 (underflow)" if value == 0 else f"{value:.4g}"


def save_prediction_plot(actual, predicted):
    FIGURES.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(8, 7))
    if len(actual) > 5_000:
        sample = actual.sample(n=5_000, random_state=RANDOM_STATE).index
        actual_plot = actual.loc[sample]
        predicted_plot = predicted.loc[sample]
    else:
        actual_plot = actual
        predicted_plot = predicted
    ax.scatter(actual_plot, predicted_plot, s=12, alpha=0.25, color="#3267a8")
    limits = [
        min(float(actual.min()), float(predicted.min())),
        max(float(actual.max()), float(predicted.max())),
    ]
    ax.plot(limits, limits, linestyle="--", color="#b22222", linewidth=1.5)
    ax.set(
        title="Giá dự đoán và giá thực tế trên tập kiểm tra (log giá rao)",
        xlabel="Giá thực tế (log giá rao)",
        ylabel="Giá dự đoán (log giá rao)",
    )
    fig.tight_layout()
    target = FIGURES / "fig_05_ols_test_predictions.png"
    fig.savefig(target, dpi=300)
    plt.close(fig)
    return target


def write_report(
    source,
    design,
    model,
    train_metrics,
    test_metrics,
    baseline_metrics,
    coefficients,
    district_columns,
    month_categories,
    month_reference,
    missing_month_count,
    plot_path,
    predictions,
):
    coefficient_rows = []
    for row in coefficients.itertuples(index=False):
        coefficient_rows.append(
            f"| `{row.variable}` | {row.coefficient:.6g} | {row.std_error:.4g} | "
            f"{format_p_value(row.p_value)} | "
            f"[{row.ci_lower:.6g}, {row.ci_upper:.6g}] |"
        )
    test_districts = set(predictions["district_name_clean"])
    omitted_test_districts = sorted(
        set(source["district_name_clean"]) - test_districts
    )
    lines = [
        "# Báo cáo Prompt 04 — Hồi quy OLS",
        "",
        f"- Thời điểm chạy: {datetime.now().astimezone().isoformat(timespec='seconds')}",
        "- Dữ liệu: nhánh `preserve_extremes`; giữ nguyên mọi ngoại lệ đã duyệt.",
        "- Biến mục tiêu được duyệt: `log(price)`; giá rao trong nguồn chưa xác minh đơn vị.",
        "- Diện tích được duyệt: `area` liên tục; không đưa `area_bin` vào mô hình này.",
        f"- Quan sát: {len(source):,}; train {len(model.model.endog):,}; test {len(predictions):,}.",
        f"- Biến giải thích: {design.shape[1]} (có intercept), split test={TEST_SIZE:.0%}, "
        f"`random_state={RANDOM_STATE}`.",
        "",
        "## Đặc tả mô hình",
        "",
        "`log(price) ~ area + bedroom_count + bathroom_count + district indicators + month indicators`.",
        f"- Nhóm địa bàn tham chiếu: Quận 7 (các cột địa bàn từ Prompt 03: {len(district_columns)}).",
        f"- Nhóm tháng tham chiếu: {month_reference}; các tháng hợp lệ: "
        f"{', '.join(month for month in month_categories if month != 'Unknown month')}.",
        f"- Giữ {missing_month_count:,} ngày không phân tích được trong nhóm riêng "
        "`Unknown month`; không tự điền ngày.",
        "- Mô hình dùng các biến số gốc chưa scale. Không dùng scaler fit trên toàn tập EDA.",
        "",
        "## Kết quả",
        "",
        "| Tập | MAE log(price) | RMSE log(price) | R² log(price) |",
        "|---|---:|---:|---:|",
        f"| Train | {train_metrics['mae']:.4f} | {train_metrics['rmse']:.4f} | {train_metrics['r2']:.4f} |",
        f"| Test | {test_metrics['mae']:.4f} | {test_metrics['rmse']:.4f} | {test_metrics['r2']:.4f} |",
        f"| Baseline test (median log-price train) | {baseline_metrics['mae']:.4f} | "
        f"{baseline_metrics['rmse']:.4f} | {baseline_metrics['r2']:.4f} |",
        "",
        "Test là holdout ngẫu nhiên cùng giai đoạn dữ liệu, không phải kiểm tra dự báo tương lai. "
        "MAE/RMSE tính trên thang log, không phải đơn vị tiền.",
        f"- Test có {len(test_districts)}/{source['district_name_clean'].nunique()} "
        f"nhãn địa bàn; không có dòng holdout cho: {', '.join(omitted_test_districts) or 'không có'}.",
        "",
        "## Hệ số OLS",
        "",
        "Hệ số cho biến liên tục mô tả thay đổi log-price khi biến tăng một đơn vị, giữ "
        "các biến khác không đổi. Hệ số dummy địa bàn/tháng so với nhóm tham chiếu. "
        "Đây là liên hệ thống kê, không phải tác động nhân quả.",
        "p-value và khoảng tin cậy bên dưới dùng sai số chuẩn OLS cổ điển; cần xem kết quả "
        "chẩn đoán Prompt 05 trước khi dùng suy luận thống kê.",
        "",
        "| Biến | Hệ số | Sai số chuẩn | p-value | KTC 95% |",
        "|---|---:|---:|---:|---:|",
        *coefficient_rows,
        "",
        "p-value hiển thị `<1e-300 (underflow)` thay vì 0 khi giá trị số bị underflow.",
        f"- Bảng đầy đủ: `{COEFFICIENTS.relative_to(ROOT)}`.",
        f"- Dự đoán holdout: `{PREDICTIONS.relative_to(ROOT)}`.",
        f"- Biểu đồ dự đoán/quan sát: `{plot_path.relative_to(ROOT)}` (trên thang log).",
        "",
        "Khi lấy `exp(predicted log-price)`, kết quả gần với trung vị có điều kiện/geometric "
        "scale; không tự xem đó là giá trung bình kỳ vọng. Muốn báo giá ở thang gốc cần "
        "đánh giá hiệu chỉnh retransformation riêng.",
        "",
        "## Giới hạn",
        "",
        "- Split ngẫu nhiên có thể đo độ khớp nội suy trong cùng giai đoạn; không kiểm tra "
        "khả năng dự báo sang 2026 hoặc thị trường tương lai.",
        "- Chỉ 7 tháng dữ liệu; không bao phủ căn hộ Củ Chi. Cần Giờ và Hóc Môn có rất ít mẫu, "
        "nên hệ số nhóm này có thể bất ổn.",
        "- Không có thông tin dự án, tuổi căn hộ, tầng, pháp lý hoặc tọa độ đầy đủ; "
        "mô hình có thể bỏ sót biến quan trọng.",
        "- Do ngoại lệ được giữ theo lựa chọn của người dùng, chỉ số ở thang giá gốc "
        "có thể nhạy với một số tin cực đoan.",
        "",
        "## Self-test",
        "",
        "- PASS: train/test không giao nhau; target và mọi feature hữu hạn.",
        "- PASS: hệ số, dự đoán và các chỉ số holdout hữu hạn.",
        "- PASS: baseline được tính trên cùng test set.",
        f"- {'PASS' if plot_path.is_file() and plot_path.stat().st_size > 0 else 'FAIL'}: biểu đồ holdout đã tạo.",
        "",
        "## Điểm dừng trước Prompt 05",
        "",
        "- Tiếp theo là chẩn đoán giả định OLS (tuyến tính, phương sai sai số, phân phối phần dư, "
        "đa cộng tuyến và điểm ảnh hưởng).",
        "- Không dùng p-value như bằng chứng nhân quả hoặc tuyên bố dự báo mọi quận.",
        "",
    ]
    REPORT.write_text("\n".join(lines), encoding="utf-8")


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    source = pd.read_csv(INPUT, encoding="utf-8-sig")
    (
        x,
        y,
        district_columns,
        month_categories,
        month_reference,
        missing_month_count,
    ) = build_design_matrix(source)
    train_x, test_x, train_y, test_y = train_test_split(
        x,
        y,
        test_size=TEST_SIZE,
        random_state=RANDOM_STATE,
    )
    train_design = sm.add_constant(train_x, has_constant="add")
    test_design = sm.add_constant(test_x, has_constant="add")
    model = sm.OLS(train_y, train_design).fit()

    train_pred = pd.Series(model.predict(train_design), index=train_y.index)
    test_pred = pd.Series(model.predict(test_design), index=test_y.index)
    train_metrics = calculate_metrics(train_y, train_pred)
    test_metrics = calculate_metrics(test_y, test_pred)
    baseline = pd.Series(float(train_y.median()), index=test_y.index)
    baseline_metrics = calculate_metrics(test_y, baseline)

    coefficients = pd.DataFrame(
        {
            "variable": model.params.index,
            "coefficient": model.params.to_numpy(),
            "std_error": model.bse.to_numpy(),
            "t_value": model.tvalues.to_numpy(),
            "p_value": model.pvalues.to_numpy(),
            "ci_lower": model.conf_int()[0].to_numpy(),
            "ci_upper": model.conf_int()[1].to_numpy(),
        }
    )
    prediction_frame = pd.DataFrame(
        {
            "source_row_index": test_y.index,
            "district_name_clean": source.loc[test_y.index, "district_name_clean"].to_numpy(),
            "listing_month": source.loc[test_y.index, "listing_month"]
            .fillna("Unknown month")
            .to_numpy(),
            "observed_price_raw": source.loc[test_y.index, TARGET].to_numpy(),
            "observed_log_price": test_y.to_numpy(),
            "predicted_log_price": test_pred.to_numpy(),
            "predicted_price_exp_log": np.exp(test_pred.to_numpy()),
        }
    ).sort_values("source_row_index")
    plot_path = save_prediction_plot(test_y, test_pred)

    COEFFICIENTS.parent.mkdir(parents=True, exist_ok=True)
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    coefficients.to_csv(COEFFICIENTS, index=False, encoding="utf-8-sig")
    prediction_frame.to_csv(PREDICTIONS, index=False, encoding="utf-8-sig")
    write_report(
        source,
        x,
        model,
        train_metrics,
        test_metrics,
        baseline_metrics,
        coefficients,
        district_columns,
        month_categories,
        month_reference,
        missing_month_count,
        plot_path,
        prediction_frame,
    )

    assert len(train_y) + len(test_y) == len(source)
    assert train_y.index.intersection(test_y.index).empty
    assert np.isfinite(train_design.to_numpy()).all()
    assert np.isfinite(test_design.to_numpy()).all()
    assert np.isfinite(model.params.to_numpy()).all()
    assert np.isfinite(test_pred.to_numpy()).all()
    assert len(prediction_frame) == len(test_y)
    assert COEFFICIENTS.is_file() and COEFFICIENTS.stat().st_size > 0
    assert PREDICTIONS.is_file() and PREDICTIONS.stat().st_size > 0
    assert REPORT.is_file() and REPORT.stat().st_size > 0
    assert plot_path.is_file() and plot_path.stat().st_size > 0

    print(f"OLS train/test: {len(train_y):,}/{len(test_y):,}")
    print(f"Test R² on log(price): {test_metrics['r2']:.4f}")
    print(f"Test MAE on log(price): {test_metrics['mae']:.4f}")
    print(f"Report: {REPORT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
