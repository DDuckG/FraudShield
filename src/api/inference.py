import json
from datetime import datetime
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from src.api.schemas import FraudDetectionRequest, FraudResponse
from src.features.FeatureEngineering import add_features
from src.features.contracts import CATE_COLS, ID_COLS
from src.settings import env_path


DEFAULT_THRESHOLD = 0.65


def _models_dir() -> Path:
    return env_path("MODELS_DIR", "models")


MODELS_DIR = _models_dir()
TRAINED_DIR = MODELS_DIR / "trained"
ARTIFACT_DIR = MODELS_DIR / "artifacts"

META_PATH = TRAINED_DIR / "trained_model_meta.json"
MODEL_PATH = TRAINED_DIR / "trained_model.pkl"
FE_PARAMS_PATH = TRAINED_DIR / "fe_params.pkl"
COLUMNS_PATH = TRAINED_DIR / "model_columns.pkl"


def _load_json(path: Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _threshold(meta: dict) -> float:
    value = meta.get("threshold", DEFAULT_THRESHOLD)
    return float(value)


def _load_branch_artifacts(artifacts: dict, branch: str) -> None:
    if branch == "log":
        artifacts["encoder"] = joblib.load(ARTIFACT_DIR / "onehot_encoder.pkl")
        artifacts["scaler"] = joblib.load(ARTIFACT_DIR / "scaler.pkl")
        return

    if branch == "tree":
        artifacts["label_encoders"] = joblib.load(ARTIFACT_DIR / "label_encoders.pkl")
        return

    raise ValueError(f"dataset_branch không hợp lệ: {branch}")


def load_artifacts() -> dict:
    meta = _load_json(META_PATH)
    artifacts = {
        "meta": meta,
        "model": joblib.load(MODEL_PATH),
        "fe_params": joblib.load(FE_PARAMS_PATH),
        "model_columns": joblib.load(COLUMNS_PATH),
    }
    _load_branch_artifacts(artifacts, meta["dataset_branch"])
    return artifacts


ARTIFACTS: dict = load_artifacts()
_META = ARTIFACTS["meta"]
_MODEL = ARTIFACTS["model"]
_FE_PARAMS = ARTIFACTS["fe_params"]
_MODEL_COLUMNS = ARTIFACTS["model_columns"]
THRESHOLD = _threshold(_META)


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


def _preprocess_log(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    cat_cols = [c for c in CATE_COLS if c in df.columns]
    num_cols = [c for c in df.columns if c not in cat_cols]

    for col in cat_cols:
        df[col] = df[col].astype(str)

    encoded = ARTIFACTS["encoder"].transform(df[cat_cols]) if cat_cols else np.empty((len(df), 0))
    encoded_cols = ARTIFACTS["encoder"].get_feature_names_out(cat_cols) if cat_cols else []
    encoded_df = pd.DataFrame(encoded, columns=encoded_cols, index=df.index)

    scaled = ARTIFACTS["scaler"].transform(df[num_cols]) if num_cols else np.empty((len(df), 0))
    scaled_df = pd.DataFrame(scaled, columns=num_cols, index=df.index)

    return pd.concat([scaled_df, encoded_df], axis=1)


def _preprocess_tree(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    for col, encoder in ARTIFACTS["label_encoders"].items():
        if col not in df.columns:
            df[col] = 0
            continue

        known = set(encoder.classes_)
        if "UNKNOWN" not in known:
            encoder.classes_ = np.append(encoder.classes_, "UNKNOWN")
            known.add("UNKNOWN")

        df[col] = df[col].astype(str).map(lambda x: x if x in known else "UNKNOWN")
        df[col] = encoder.transform(df[col])

    return df


def _preprocess_by_branch(df: pd.DataFrame) -> pd.DataFrame:
    branch = _META["dataset_branch"]
    if branch == "log":
        return _preprocess_log(df)
    return _preprocess_tree(df)


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


def _prepare_features(requests: list[FraudDetectionRequest]) -> tuple[pd.DataFrame, list[list[str]]]:
    df = _requests_to_df(requests)
    df, _ = add_features(df, _FE_PARAMS)
    df = _drop_datetime_columns(df)

    rules = [_triggered_rules(row) for _, row in df.iterrows()]

    df = _preprocess_by_branch(df)
    df = df.reindex(columns=_MODEL_COLUMNS, fill_value=0)
    return df, rules


def _make_response(score: float, rules: list[str]) -> FraudResponse:
    score = float(score)
    return FraudResponse(
        is_fraud=score >= THRESHOLD,
        fraud_score=round(score, 4),
        risk_level=_risk_level(score),
        triggered_rules=rules,
        prediction_time=datetime.now(),
    )


def predict_fraud(request: FraudDetectionRequest) -> FraudResponse:
    features, rules = _prepare_features([request])
    score = _MODEL.predict_proba(features)[0][1]
    return _make_response(score, rules[0])


def batch_predict(requests: list[FraudDetectionRequest]) -> list[FraudResponse]:
    if not requests:
        return []

    features, rules = _prepare_features(requests)
    scores = _MODEL.predict_proba(features)[:, 1]
    return [_make_response(score, rule) for score, rule in zip(scores, rules)]
