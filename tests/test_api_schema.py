import pytest
from pydantic import ValidationError

from src.api.schemas import FraudDetectionRequest


def valid_payload() -> dict:
    return {
        "transaction_id": "TX-1",
        "user_id": "USR-1",
        "hour_of_day": 13,
        "day_of_week": 2,
        "is_weekend": 0,
        "amount": 125.5,
        "card_present": 1,
        "device_known": 1,
        "is_foreign_txn": 0,
        "has_2fa": 1,
        "time_since_last_s": 320.0,
        "velocity_1h": 2.0,
        "amount_vs_avg_ratio": 1.3,
        "account_age_days": 250,
        "credit_limit": 5000.0,
        "merchant_category": "grocery",
        "merchant_country": "US",
        "device_type": "mobile_app",
        "mcc_code": 5411,
        "ip_risk_score": 8.0,
    }


def test_schema_accepts_valid_request():
    req = FraudDetectionRequest(**valid_payload())
    assert req.amount == 125.5
    assert req.hour_of_day == 13


def test_schema_rejects_invalid_request():
    payload = valid_payload()
    payload["amount"] = -1

    with pytest.raises(ValidationError):
        FraudDetectionRequest(**payload)
