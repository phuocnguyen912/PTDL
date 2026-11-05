"""Phân cụm khám phá các tin rao căn hộ, giữ nguyên mọi dòng."""

from datetime import datetime
from pathlib import Path
import sys

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.cluster import MiniBatchKMeans
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import RobustScaler


ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "data" / "processed" / "hcmc_apartments_prompt03_preserve_extremes.csv"
OUTPUT = ROOT / "data" / "processed" / "hcmc_apartment_clusters_prompt07.csv"
REPORT = ROOT / "reports" / "step_07_clustering_report.md"
FIGURES = ROOT / "reports" / "figures"
K_VALUES = range(2, 7)
RANDOM_STATE = 42
SILHOUETTE_SAMPLE_SIZE = 2_500


def build_cluster_matrix(frame):
    """Log-transform skewed positive fields, robust-scale numerics, retain district flags."""
    numeric = pd.DataFrame(
        {
            "log_price": np.log(frame["price"].astype(float)),
            "log_area": np.log(frame["area"].astype(float)),
            "log1p_bedrooms": np.log1p(frame["bedroom_count"].astype(float)),
            "log1p_bathrooms": np.log1p(frame["bathroom_count"].astype(float)),
        },
        index=frame.index,
    )
    scaler = RobustScaler()
    numeric_scaled = scaler.fit_transform(numeric)
    district_columns = [
        column for column in frame.columns if column.startswith("district__")
    ]
    if not district_columns:
        raise ValueError("Không tìm thấy mã hóa địa bàn từ Prompt 03.")
    district_flags = frame[district_columns].astype(float).to_numpy()
    matrix = np.column_stack([numeric_scaled, district_flags]).astype(np.float32)
    if not np.isfinite(matrix).all():
        raise ValueError("Ma trận phân cụm có giá trị không hữu hạn.")
    return matrix, list(numeric.columns) + district_columns


def fit_and_score(matrix):
    results = []
    selected = None
    for k in K_VALUES:
        model = MiniBatchKMeans(
            n_clusters=k,
            random_state=RANDOM_STATE,
            n_init=10,
            batch_size=4096,
            max_iter=200,
        )
        labels = model.fit_predict(matrix)
        if len(np.unique(labels)) < 2:
            raise ValueError(f"KMeans tạo ít hơn 2 cụm cho k={k}.")
        score = float(
            silhouette_score(
                matrix,
                labels,
                sample_size=min(SILHOUETTE_SAMPLE_SIZE, len(matrix)),
                random_state=RANDOM_STATE,
            )
        )
        counts = pd.Series(labels).value_counts()
        results.append(
            {
                "k": k,
                "silhouette_sample": score,
                "smallest_cluster": int(counts.min()),
            }
        )
        if selected is None or score > selected[0]:
            selected = (score, model, labels)
    if selected is None:
        raise RuntimeError("Không có kết quả phân cụm.")
    return pd.DataFrame(results), selected[1], selected[2]


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    source = pd.read_csv(INPUT, encoding="utf-8-sig")
    if source[["price", "area", "bedroom_count", "bathroom_count"]].isna().any().any():
        raise ValueError("Đầu vào phân cụm còn thiếu biến số bắt buộc.")
    if (source[["price", "area"]] <= 0).any().any():
        raise ValueError("price và area phải dương để log-transform.")

    matrix, _ = build_cluster_matrix(source)
    scores, model, labels = fit_and_score(matrix)
    best_k = int(model.n_clusters)
    clustered = source[
        [
            "district_name_clean",
            "listing_month",
            "price",
            "area",
            "bedroom_count",
            "bathroom_count",
        ]
    ].copy()
    clustered["cluster"] = labels
    summary = (
        clustered.groupby("cluster")
        .agg(
            listings=("price", "size"),
            median_price_raw=("price", "median"),
            median_area=("area", "median"),
            median_bedrooms=("bedroom_count", "median"),
            median_bathrooms=("bathroom_count", "median"),
            districts=("district_name_clean", "nunique"),
        )
        .reset_index()
    )
    top_districts = (
        clustered.groupby(["cluster", "district_name_clean"])
        .size()
        .rename("listings")
        .reset_index()
        .sort_values(["cluster", "listings"], ascending=[True, False])
        .groupby("cluster")
        .head(3)
    )

    FIGURES.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(RANDOM_STATE)
    plot_indices = rng.choice(
        len(clustered),
        size=min(10_000, len(clustered)),
        replace=False,
    )
    plot_data = clustered.iloc[plot_indices]
    fig, ax = plt.subplots(figsize=(10, 7))
    for cluster in sorted(clustered["cluster"].unique()):
        group = plot_data.loc[plot_data["cluster"] == cluster]
        ax.scatter(
            np.log(group["area"]),
            np.log(group["price"]),
            s=12,
            alpha=0.35,
            label=f"Cụm {cluster}",
        )
    ax.set(
        title="Các cụm tin rao căn hộ (phân tích khám phá)",
        xlabel="Logarit diện tích",
        ylabel="Logarit giá rao thô",
    )
    ax.legend()
    fig.tight_layout()
    figure = FIGURES / "fig_12_apartment_clusters.png"
    fig.savefig(figure, dpi=300)
    plt.close(fig)

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    clustered.to_csv(OUTPUT, index=False, encoding="utf-8-sig")
    score_rows = [
        f"| {int(row.k)} | {row.silhouette_sample:.4f} | {int(row.smallest_cluster):,} |"
        for row in scores.itertuples(index=False)
    ]
    summary_rows = [
        f"| {int(row.cluster)} | {int(row.listings):,} | {row.median_price_raw:,.4g} | "
        f"{row.median_area:,.4g} | {row.median_bedrooms:.2f} | "
        f"{row.median_bathrooms:.2f} | {int(row.districts)} |"
        for row in summary.itertuples(index=False)
    ]
    district_rows = [
        f"| {int(row.cluster)} | {row.district_name_clean} | {int(row.listings):,} |"
        for row in top_districts.itertuples(index=False)
    ]
    report_lines = [
        "# Báo cáo Prompt 07 — Phân cụm khám phá",
        "",
        f"- Thời điểm chạy: {datetime.now().astimezone().isoformat(timespec='seconds')}",
        f"- Số dòng đưa vào: {len(source):,}; không xóa ngoại lệ.",
        "- Dùng log(price), log(area), log1p số phòng và mã one-hot địa bàn; "
        "các biến số được RobustScaler.",
        f"- Candidate k từ {min(K_VALUES)} đến {max(K_VALUES)}; silhouette tính trên "
        f"mẫu tối đa {SILHOUETTE_SAMPLE_SIZE:,} dòng, seed {RANDOM_STATE}.",
        f"- Chọn k={best_k} do silhouette mẫu cao nhất ({scores.loc[scores['k'].eq(best_k), 'silhouette_sample'].iloc[0]:.4f}); "
        "đây là lựa chọn kỹ thuật khám phá, không chứng minh tồn tại đúng số phân khúc thị trường.",
        "",
        "## Chọn số cụm",
        "",
        "| k | Silhouette mẫu | Kích thước cụm nhỏ nhất |",
        "|---:|---:|---:|",
        *score_rows,
        "",
        "## Tóm tắt cụm",
        "",
        "| Cụm | Số tin | Median price thô | Median area | Median bedrooms | Median bathrooms | Số địa bàn |",
        "|---:|---:|---:|---:|---:|---:|---:|",
        *summary_rows,
        "",
        "### Ba địa bàn có nhiều tin nhất trong từng cụm",
        "",
        "| Cụm | Địa bàn | Số tin |",
        "|---:|---|---:|",
        *district_rows,
        "",
        f"- Gán cụm theo từng dòng: `{OUTPUT.relative_to(ROOT)}`.",
        f"- Biểu đồ lấy mẫu tối đa 10.000 dòng: `{figure.relative_to(ROOT)}`.",
        "",
        "## Giới hạn",
        "",
        "- `price` là giá rao chưa xác minh đơn vị; phân cụm không phải định giá hoặc dự báo.",
        "- Tập giữ các giá trị cực đoan; log/RobustScaler giảm nhưng không loại bỏ ảnh hưởng "
        "của dữ liệu nhập sai và điểm leverage.",
        "- Silhouette dùng mẫu ngẫu nhiên và có thể không ổn định với cụm nhỏ; địa bàn Cần Giờ "
        "và Hóc Môn có ít tin.",
        "- Các cụm phụ thuộc vào tập biến, cách scale, metric và k; không diễn giải nhân quả "
        "hay xem nhãn cụm là nhóm pháp lý/hành chính.",
        "",
        "## Self-test",
        "",
        f"- PASS: giữ nguyên {len(source):,} dòng và mọi dòng nhận đúng một nhãn cụm.",
        f"- PASS: k={best_k}, có {clustered['cluster'].nunique()} nhãn cụm không rỗng.",
        f"- {'PASS' if figure.is_file() and figure.stat().st_size > 0 else 'FAIL'}: biểu đồ cụm tồn tại.",
        "",
    ]
    REPORT.write_text("\n".join(report_lines), encoding="utf-8")

    assert len(clustered) == len(source)
    assert clustered["cluster"].notna().all()
    assert clustered["cluster"].nunique() == best_k
    assert set(scores["k"]) == set(K_VALUES)
    assert np.isfinite(scores["silhouette_sample"].to_numpy()).all()
    assert figure.is_file() and figure.stat().st_size > 0
    assert OUTPUT.is_file() and OUTPUT.stat().st_size > 0
    assert REPORT.is_file() and REPORT.stat().st_size > 0
    print(f"Best exploratory k: {best_k}")
    print(f"Silhouette: {scores.loc[scores['k'].eq(best_k), 'silhouette_sample'].iloc[0]:.4f}")
    print(f"Clusters report: {REPORT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
