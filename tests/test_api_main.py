from datetime import datetime

from fastapi.testclient import TestClient

from src.api import main as api_main
from src.api.schemas import FraudResponse
from tests.test_api_schema import valid_payload


def test_health_reports_loaded_model(monkeypatch):
    monkeypatch.setattr(
        api_main,
        "load_artifacts",
        lambda: {
            "meta": {"selected_model": "mock", "dataset_branch": "tree"},
            "model": object(),
            "fe_params": {},
            "model_columns": [],
        },
    )

    with TestClient(api_main.app) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
    assert response.json()["model_loaded"] is True


def test_predict_uses_app_state_and_saves_record(monkeypatch):
    saved_records = []

    monkeypatch.setattr(
        api_main,
        "load_artifacts",
        lambda: {
            "meta": {"selected_model": "mock", "dataset_branch": "tree"},
            "model": object(),
            "fe_params": {},
            "model_columns": [],
        },
    )
    monkeypatch.setattr(
        api_main,
        "predict_fraud",
        lambda req, artifacts: FraudResponse(
            is_fraud=False,
            fraud_score=0.1234,
            risk_level="Low",
            triggered_rules=[],
            prediction_time=datetime(2026, 7, 5, 8, 30),
        ),
    )

    def fake_save(record: dict) -> str:
        saved_records.append(record)
        return "predictions/dt=2026-07-05/hour=08/test.parquet"

    monkeypatch.setattr(api_main, "save_prediction_record", fake_save)

    with TestClient(api_main.app) as client:
        response = client.post("/predict", json=valid_payload())

    body = response.json()
    assert response.status_code == 200
    assert body["prediction_id"] == saved_records[0]["prediction_id"]
    assert body["fraud_score"] == 0.1234


def test_batch_saves_records_once(monkeypatch):
    calls = []

    monkeypatch.setattr(
        api_main,
        "load_artifacts",
        lambda: {
            "meta": {"selected_model": "mock", "dataset_branch": "tree"},
            "model": object(),
            "fe_params": {},
            "model_columns": [],
        },
    )
    monkeypatch.setattr(
        api_main,
        "batch_predict",
        lambda reqs, artifacts: [
            FraudResponse(
                is_fraud=False,
                fraud_score=0.11,
                risk_level="Low",
                triggered_rules=[],
                prediction_time=datetime(2026, 7, 5, 8, 30),
            )
            for _ in reqs
        ],
    )

    def fake_save_many(records: list[dict], batch_id: str | None = None) -> str:
        calls.append((records, batch_id))
        return "predictions/dt=2026-07-05/hour=08/batch.parquet"

    monkeypatch.setattr(api_main, "save_prediction_records", fake_save_many)

    payload = valid_payload()
    with TestClient(api_main.app) as client:
        response = client.post("/batch", json=[payload, payload | {"transaction_id": "TX-2"}])

    assert response.status_code == 200
    assert response.json()["total"] == 2
    assert len(calls) == 1
    assert len(calls[0][0]) == 2
