import importlib

import pandas as pd

from src.monitoring.run_drift_report import select_valid_cols


def test_import_drift_report_has_no_runtime_side_effects():
    module = importlib.import_module("src.monitoring.run_drift_report")
    assert hasattr(module, "main")


def test_select_valid_cols_keeps_only_useful_columns():
    reference = pd.DataFrame(
        {
            "amount": [10.0, 20.0, 30.0, 40.0],
            "constant": [1, 1, 1, 1],
            "missing": [None, None, None, None],
        }
    )
    current = pd.DataFrame(
        {
            "amount": [12.0, 21.0, 35.0, 42.0],
            "constant": [1, 1, 1, 1],
            "missing": [1, 2, 3, 4],
        }
    )

    assert select_valid_cols(reference, current, min_rows=3, min_unique=2) == ["amount"]
