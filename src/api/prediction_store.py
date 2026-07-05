import io
import uuid
from datetime import datetime, timezone

import pandas as pd
from google.cloud import storage

from src.settings import env


GCS_BUCKET = env("GCS_BUCKET_NAME")
PREDICTION_PREFIX = env("PREDICTION_PREFIX", "predictions")


_gcs_client: storage.Client | None = None


def _get_gcs_client() -> storage.Client:
    global _gcs_client
    if _gcs_client is None:
        _gcs_client = storage.Client()
    return _gcs_client


def _build_gcs_blob_name(event_time: datetime, prediction_id: str) -> str:
    dt = event_time.strftime("%Y-%m-%d")
    hour = event_time.strftime("%H")
    return f"{PREDICTION_PREFIX}/dt={dt}/hour={hour}/{prediction_id}.parquet"


def _build_batch_gcs_blob_name(event_time: datetime, batch_id: str) -> str:
    dt = event_time.strftime("%Y-%m-%d")
    hour = event_time.strftime("%H")
    return f"{PREDICTION_PREFIX}/dt={dt}/hour={hour}/{batch_id}.parquet"


def _event_time(value: str | datetime) -> datetime:
    return datetime.fromisoformat(value) if isinstance(value, str) else value


def _records_to_buffer(records: list[dict]) -> io.BytesIO:
    df = pd.DataFrame(records)

    buffer = io.BytesIO()
    df.to_parquet(
        buffer,
        engine="pyarrow",
        compression="snappy",
        index=False,
    )
    buffer.seek(0)
    return buffer


def _upload_parquet(records: list[dict], blob_name: str) -> str:
    if not GCS_BUCKET:
        raise RuntimeError("Missing GCS_BUCKET_NAME environment variable")

    buffer = _records_to_buffer(records)

    client = _get_gcs_client()
    bucket = client.bucket(GCS_BUCKET)
    blob = bucket.blob(blob_name)
    blob.upload_from_file(buffer, content_type="application/octet-stream")

    return blob_name


def save_prediction_record(record: dict) -> str:
    event_time = _event_time(record["event_time"])
    blob_name = _build_gcs_blob_name(event_time, record["prediction_id"])
    return _upload_parquet([record], blob_name)


def save_prediction_records(records: list[dict], batch_id: str | None = None) -> str:
    if not records:
        raise ValueError("records không được rỗng")

    event_time = _event_time(records[0]["event_time"])
    blob_name = _build_batch_gcs_blob_name(event_time, batch_id or str(uuid.uuid4()))
    return _upload_parquet(records, blob_name)


def make_prediction_record(
    *,
    request_id: str | None,
    transaction_id: str,
    user_id: str,
    request_payload: dict,
    response_payload: dict,
    model_version: str,
    model_type: str,
    dataset_branch: str,
) -> dict:
    event_time = datetime.now(timezone.utc)
    prediction_id = str(uuid.uuid4())

    return {
        "prediction_id": prediction_id,
        "request_id": request_id,
        "event_time": event_time.isoformat(),
        "transaction_id": transaction_id,
        "user_id": user_id,
        "model_version": model_version,
        "model_type": model_type,
        "dataset_branch": dataset_branch,
        "is_fraud": response_payload["is_fraud"],
        "fraud_score": response_payload["fraud_score"],
        "risk_level": response_payload["risk_level"],
        "triggered_rules": ",".join(response_payload.get("triggered_rules", [])),
        "prediction_time": response_payload["prediction_time"],
        # Giữ lại input thô để sau này nối với feedback hoặc kiểm tra drift.
        **request_payload,
    }
