from datetime import datetime, timezone

from src.api.prediction_store import (
    _build_batch_gcs_blob_name,
    _build_gcs_blob_name,
    make_prediction_record,
)


def test_gcs_blob_paths_are_partitioned_by_time():
    event_time = datetime(2026, 7, 5, 8, 30, tzinfo=timezone.utc)

    assert _build_gcs_blob_name(event_time, "pred-1") == (
        "predictions/dt=2026-07-05/hour=08/pred-1.parquet"
    )
    assert _build_batch_gcs_blob_name(event_time, "batch-1") == (
        "predictions/dt=2026-07-05/hour=08/batch-1.parquet"
    )


def test_prediction_record_has_monitoring_fields():
    record = make_prediction_record(
        request_id="req-1",
        transaction_id="TX-1",
        user_id="USR-1",
        request_payload={"amount": 10.0},
        response_payload={
            "is_fraud": False,
            "fraud_score": 0.12,
            "risk_level": "Low",
            "triggered_rules": ["night_transaction"],
            "prediction_time": "2026-07-05T08:30:00",
        },
        model_version="local",
        model_type="lightgbm",
        dataset_branch="tree",
    )

    assert record["prediction_id"]
    assert record["request_id"] == "req-1"
    assert record["triggered_rules"] == "night_transaction"
    assert record["amount"] == 10.0
