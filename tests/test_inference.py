import numpy as np
from sklearn.preprocessing import LabelEncoder

from src.api.inference import predict_fraud
from src.api.schemas import FraudDetectionRequest
from tests.test_api_schema import valid_payload


class DummyModel:
    def predict_proba(self, features):
        scores = np.full(len(features), 0.42)
        return np.column_stack([1 - scores, scores])


def _encoder(values: list[str]) -> LabelEncoder:
    encoder = LabelEncoder()
    encoder.fit(values)
    return encoder


def test_predict_fraud_uses_given_artifacts_without_mutating_encoders():
    encoders = {
        "merchant_category": _encoder(["grocery"]),
        "merchant_country": _encoder(["US"]),
        "device_type": _encoder(["mobile_app"]),
        "mcc_code": _encoder(["5411"]),
        "hour_of_day": _encoder(["13"]),
        "day_of_week": _encoder(["2"]),
    }
    before = {col: tuple(encoder.classes_) for col, encoder in encoders.items()}

    artifacts = {
        "meta": {"dataset_branch": "tree", "threshold": 0.65},
        "model": DummyModel(),
        "fe_params": {
            "amount_q95": 1000.0,
            "ip_q80": 50.0,
            "ratio_q90": 3.0,
            "velocity_q90": 5.0,
            "util_q90": 0.9,
        },
        "model_columns": [
            "merchant_category",
            "merchant_country",
            "device_type",
            "mcc_code",
            "hour_of_day",
            "day_of_week",
            "is_night",
            "high_amount_flag",
        ],
        "label_encoders": encoders,
    }
    payload = valid_payload()
    payload["merchant_category"] = "new_category"

    result = predict_fraud(FraudDetectionRequest(**payload), artifacts)

    assert result.fraud_score == 0.42
    assert not result.is_fraud
    assert before == {col: tuple(encoder.classes_) for col, encoder in encoders.items()}
