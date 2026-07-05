import pandas as pd

from src.features.FeatureEngineering import fit_params, prepare_tree_branch
from src.features.contracts import ID_COLS, TARGET


def _frame(start: str) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "transaction_id": ["TX-1", "TX-2", "TX-3"],
            "account_id": ["ACC-1", "ACC-2", "ACC-3"],
            "user_id": ["USR-1", "USR-2", "USR-3"],
            "timestamp": pd.date_range(start, periods=3, freq="h"),
            "amount": [20.0, 80.0, 140.0],
            "hour_of_day": [9, 13, 23],
            "day_of_week": [1, 2, 5],
            "is_weekend": [0, 0, 1],
            "card_present": [1, 1, 0],
            "device_known": [1, 1, 0],
            "is_foreign_txn": [0, 0, 1],
            "has_2fa": [1, 1, 0],
            "time_since_last_s": [500.0, 300.0, 50.0],
            "velocity_1h": [1.0, 2.0, 6.0],
            "amount_vs_avg_ratio": [0.8, 1.5, 4.0],
            "account_age_days": [100, 200, 20],
            "credit_limit": [1000.0, 3000.0, 500.0],
            "merchant_category": ["grocery", "electronics", "travel"],
            "merchant_country": ["US", "US", "DE"],
            "device_type": ["mobile_app", "web", "mobile_app"],
            "mcc_code": [5411, 5732, 4722],
            "ip_risk_score": [3.0, 15.0, 80.0],
            TARGET: [0, 0, 1],
        }
    )


def test_tree_branch_does_not_keep_id_columns_in_model_frame():
    train = _frame("2024-01-01")
    valid = _frame("2024-02-01")
    test = _frame("2024-03-01")
    params = fit_params(train)

    train_tree, valid_tree, test_tree, _ = prepare_tree_branch(train, valid, test, params)

    for frame in [train_tree, valid_tree, test_tree]:
        assert not set(ID_COLS).intersection(frame.columns)
        assert "timestamp" not in frame.columns
        assert TARGET in frame.columns
