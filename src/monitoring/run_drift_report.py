import os
from dataclasses import dataclass

import numpy as np
import pandas as pd
from evidently import ColumnMapping
from evidently.metric_preset import DataDriftPreset
from evidently.report import Report
from google.cloud import bigquery

from src.monitoring.report_store import GCS_BUCKET, upload_drift_report
from src.settings import env, env_int


@dataclass(frozen=True)
class DriftConfig:
    project_id: str
    dataset: str
    reference_data_path: str
    min_rows: int
    min_unique: int
    output_path: str


def load_config() -> DriftConfig:
    return DriftConfig(
        project_id=env("PROJECT_ID"),
        dataset=env("BQ_DATASET", "fraud_monitoring"),
        reference_data_path=env("REFERENCE_DATA_PATH", "data/raw/transactions.csv"),
        min_rows=env_int("MIN_ROWS", 50),
        min_unique=env_int("MIN_UNIQUE", 2),
        output_path=env("DRIFT_OUTPUT_PATH", "reports/drift_report.html"),
    )


def build_current_query(project_id: str, dataset: str) -> str:
    return f"""
SELECT
  amount,
  hour_of_day,
  day_of_week,
  merchant_category,
  merchant_country,
  device_type,
  mcc_code,
  ip_risk_score,
  velocity_1h,
  amount_vs_avg_ratio,
  account_age_days,
  credit_limit,
  card_present,
  device_known,
  is_foreign_txn,
  has_2fa
FROM `{project_id}.{dataset}.predictions_ext`
"""


def preprocess(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.replace([np.inf, -np.inf], np.nan, inplace=True)
    return df


def select_valid_cols(
    reference_df: pd.DataFrame,
    current_df: pd.DataFrame,
    *,
    min_rows: int,
    min_unique: int,
) -> list[str]:
    common_cols = [c for c in current_df.columns if c in reference_df.columns]
    valid_cols: list[str] = []

    for col in common_cols:
        ref_col = reference_df[col]
        cur_col = current_df[col]

        # Các cột quá nghèo tín hiệu làm Evidently báo nhiễu hơn là giúp mình nhìn drift.
        if cur_col.isna().all() or ref_col.isna().all():
            continue
        if cur_col.nunique(dropna=True) < min_unique:
            continue
        if ref_col.nunique(dropna=True) < min_unique:
            continue
        if cur_col.dropna().shape[0] < min_rows:
            continue

        valid_cols.append(col)

    return valid_cols


def align_reference_types(reference_df: pd.DataFrame, current_df: pd.DataFrame) -> pd.DataFrame:
    reference_df = reference_df.copy()

    for col in current_df.columns:
        try:
            reference_df[col] = reference_df[col].astype(current_df[col].dtype)
        except Exception:
            pass

    return reference_df


def build_column_mapping(current_df: pd.DataFrame) -> ColumnMapping:
    numeric_cols = [
        c
        for c in current_df.columns
        if current_df[c].dtype in ["float64", "int64", "int32", "float32"]
    ]
    cat_cols = [c for c in current_df.columns if current_df[c].dtype == "object"]

    column_mapping = ColumnMapping()
    column_mapping.numerical_features = numeric_cols
    column_mapping.categorical_features = cat_cols
    return column_mapping


def run_report(
    reference_df: pd.DataFrame,
    current_df: pd.DataFrame,
    output_path: str,
) -> None:
    column_mapping = build_column_mapping(current_df)
    report = Report(metrics=[DataDriftPreset(cat_stattest_threshold=0.05)])
    report.run(
        reference_data=reference_df,
        current_data=current_df,
        column_mapping=column_mapping,
    )

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    report.save_html(output_path)


def prepare_report_frames(
    reference_df: pd.DataFrame,
    current_df: pd.DataFrame,
    *,
    min_rows: int,
    min_unique: int,
) -> tuple[pd.DataFrame, pd.DataFrame, list[str]]:
    reference_df = preprocess(reference_df)
    current_df = preprocess(current_df)

    valid_cols = select_valid_cols(
        reference_df,
        current_df,
        min_rows=min_rows,
        min_unique=min_unique,
    )
    if not valid_cols:
        return reference_df.iloc[:, 0:0], current_df.iloc[:, 0:0], []

    reference_df = reference_df[valid_cols].copy()
    current_df = current_df[valid_cols].copy()
    reference_df = align_reference_types(reference_df, current_df)

    # NaN ở đây không phải tín hiệu chính, nên điền gọn để report chạy ổn định.
    return reference_df.fillna(0), current_df.fillna(0), valid_cols


def main() -> None:
    config = load_config()
    client = bigquery.Client(project=config.project_id)

    print("Loading reference data...")
    reference_df = pd.read_csv(config.reference_data_path)
    print("Reference shape:", reference_df.shape)

    print("Loading current data from BigQuery...")
    current_df = client.query(build_current_query(config.project_id, config.dataset)).to_dataframe()
    print("Current shape:", current_df.shape)

    if len(current_df) < config.min_rows:
        print(f"Not enough data: {len(current_df)} rows (min {config.min_rows}). Skipping report.")
        return

    reference_df, current_df, valid_cols = prepare_report_frames(
        reference_df,
        current_df,
        min_rows=config.min_rows,
        min_unique=config.min_unique,
    )
    print(f"Valid columns: {valid_cols}")

    if not valid_cols:
        print("No valid columns. Skipping report.")
        return

    print("Running Evidently report...")
    run_report(reference_df, current_df, config.output_path)
    print(f"Report saved locally: {config.output_path}")

    result = upload_drift_report(config.output_path)
    print(f"Archive report uploaded to: gs://{GCS_BUCKET}/{result['archive_blob']}")
    print(f"Latest report uploaded to: gs://{GCS_BUCKET}/{result['latest_blob']}")


if __name__ == "__main__":
    main()
