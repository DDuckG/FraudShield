import json
from datetime import datetime
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd

from src.api.schemas import FraudDetectionRequest, FraudResponse
from src.features.FeatureEngineering import add_features
from src.features.contracts import CATE_COLS, ID_COLS
from src.settings import env_path


DEFAULT_THRESHOLD = 0.65


def _artifact_paths(models_dir: Path | None = None) -> dict[str, Path]:
    root = models_dir or env_path("MODELS_DIR", "models")
    trained_dir = root / "trained"
    artifact_dir = root / "artifacts"

    return {
        "meta": trained_dir / "trained_model_meta.json",
        "model": trained_dir / "trained_model.pkl",
        "fe_params": trained_dir / "fe_params.pkl",
        "model_columns": trained_dir / "model_columns.pkl",
        "onehot_encoder": artifact_dir / "onehot_encoder.pkl",
        "scaler": artifact_dir / "scaler.pkl",
        "label_encoders": artifact_dir / "label_encoders.pkl",
    }


def _load_json(path: Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _threshold(meta: dict) -> float:
    value = meta.get("threshold", DEFAULT_THRESHOLD)
    return float(value)


def _load_branch_artifacts(artifacts: dict, paths: dict[str, Path], branch: str) -> None:
    if branch == "log":
        artifacts["encoder"] = joblib.load(paths["onehot_encoder"])
        artifacts["scaler"] = joblib.load(paths["scaler"])
        return

    if branch == "tree":
        artifacts["label_encoders"] = joblib.load(paths["label_encoders"])
        return

    raise ValueError(f"dataset_branch không hợp lệ: {branch}")


def load_artifacts(models_dir: Path | None = None) -> dict[str, Any]:
    paths = _artifact_paths(models_dir)
    meta = _load_json(paths["meta"])
    artifacts = {
        "meta": meta,
        "model": joblib.load(paths["model"]),
        "fe_params": joblib.load(paths["fe_params"]),
        "model_columns": joblib.load(paths["model_columns"]),
    }
    _load_branch_artifacts(artifacts, paths, meta["dataset_branch"])
    return artifacts


def _request_to_row(request: FraudDetectionRequest) -> dict:
    row = request.model_dump()
    for col in ID_COLS:
        row.pop(col, None)
    return row


def _requests_to_df(requests: list[FraudDetectionRequest]) -> pd.DataFrame:
    return pd.DataFrame([_request_to_row(req) for req in requests])


def _drop_datetime_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    dt_cols = df.select_dtypes(include=["datetime64[ns]", "datetime64[ns, UTC]"]).columns
    if len(dt_cols) > 0:
        df = df.drop(columns=list(dt_cols))

    if "timestamp" in df.columns and df["timestamp"].dtype == "object":
        parsed = pd.to_datetime(df["timestamp"], errors="coerce")
        if parsed.notna().any():
            df = df.drop(columns=["timestamp"])

    return df


def _preprocess_log(df: pd.DataFrame, artifacts: dict[str, Any]) -> pd.DataFrame:
    df = df.copy()
    cat_cols = [c for c in CATE_COLS if c in df.columns]
    num_cols = [c for c in df.columns if c not in cat_cols]

    for col in cat_cols:
        df[col] = df[col].astype(str)

    encoded = artifacts["encoder"].transform(df[cat_cols]) if cat_cols else np.empty((len(df), 0))
    encoded_cols = artifacts["encoder"].get_feature_names_out(cat_cols) if cat_cols else []
    encoded_df = pd.DataFrame(encoded, columns=encoded_cols, index=df.index)

    scaled = artifacts["scaler"].transform(df[num_cols]) if num_cols else np.empty((len(df), 0))
    scaled_df = pd.DataFrame(scaled, columns=num_cols, index=df.index)

    return pd.concat([scaled_df, encoded_df], axis=1)


def _safe_label_encode(values: pd.Series, encoder: Any) -> pd.Series:
    classes = [str(x) for x in encoder.classes_]
    class_to_code = {value: idx for idx, value in enumerate(classes)}

    # Artifact mới có UNKNOWN từ lúc train; artifact cũ thì rơi về code 0 để không sửa object dùng chung.
    unknown_code = class_to_code.get("UNKNOWN", 0)
    return values.astype(str).map(lambda value: class_to_code.get(value, unknown_code)).astype(int)


def _preprocess_tree(df: pd.DataFrame, artifacts: dict[str, Any]) -> pd.DataFrame:
    df = df.copy()

    for col, encoder in artifacts["label_encoders"].items():
        if col not in df.columns:
            df[col] = 0
            continue

        df[col] = _safe_label_encode(df[col], encoder)

    return df


def _preprocess_by_branch(df: pd.DataFrame, artifacts: dict[str, Any]) -> pd.DataFrame:
    branch = artifacts["meta"]["dataset_branch"]
    if branch == "log":
        return _preprocess_log(df, artifacts)
    return _preprocess_tree(df, artifacts)


def _triggered_rules(row: pd.Series) -> list[str]:
    # Các nhãn này để người review hiểu vì sao điểm rủi ro tăng.
    rule_map = {
        "high_amount_flag": "high_amount",
        "is_night": "night_transaction",
        "high_ip_risk_flag": "high_ip_risk",
        "high_velocity_1h_flag": "velocity_spike",
        "high_utilization_flag": "high_utilization",
    }
    return [label for col, label in rule_map.items() if col in row and row[col] == 1]


def _risk_level(score: float) -> str:
    if score >= 0.8:
        return "High"
    if score >= 0.5:
        return "Medium"
    return "Low"


def _prepare_features(
    requests: list[FraudDetectionRequest],
    artifacts: dict[str, Any],
) -> tuple[pd.DataFrame, list[list[str]]]:
    df = _requests_to_df(requests)
    df, _ = add_features(df, artifacts["fe_params"])
    df = _drop_datetime_columns(df)

    rules = [_triggered_rules(row) for _, row in df.iterrows()]

    df = _preprocess_by_branch(df, artifacts)
    df = df.reindex(columns=artifacts["model_columns"], fill_value=0)
    return df, rules


def _make_response(score: float, rules: list[str], threshold: float) -> FraudResponse:
    score = float(score)
    return FraudResponse(
        is_fraud=score >= threshold,
        fraud_score=round(score, 8),
        risk_level=_risk_level(score),
        triggered_rules=rules,
        prediction_time=datetime.now(),
    )


def predict_fraud(request: FraudDetectionRequest, artifacts: dict[str, Any]) -> FraudResponse:
    features, rules = _prepare_features([request], artifacts)
    score = artifacts["model"].predict_proba(features)[0][1]
    return _make_response(score, rules[0], _threshold(artifacts["meta"]))


def batch_predict(
    requests: list[FraudDetectionRequest],
    artifacts: dict[str, Any],
) -> list[FraudResponse]:
    if not requests:
        return []

    features, rules = _prepare_features(requests, artifacts)
    scores = artifacts["model"].predict_proba(features)[:, 1]
    threshold = _threshold(artifacts["meta"])
    return [_make_response(score, rule, threshold) for score, rule in zip(scores, rules)]
