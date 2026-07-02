from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]

TARGET = "is_fraud"

# Mấy cột này chỉ để lần vết giao dịch, không đưa vào mô hình.
ID_COLS = ("transaction_id", "account_id", "user_id")

# Nhóm phân loại dùng chung cho cả lúc train và lúc API chạy dự đoán.
CATE_COLS = (
    "merchant_category",
    "merchant_country",
    "device_type",
    "mcc_code",
    "hour_of_day",
    "day_of_week",
)

KAGGLE_DATASET_URL = (
    "https://www.kaggle.com/api/v1/datasets/download/"
    "sergionefedov/fraud-detection-1m-transactions-7-fraud-types"
)
KAGGLE_TRANSACTION_FILE = "transactions.csv"


def project_path(*parts: str) -> Path:
    return PROJECT_ROOT.joinpath(*parts)
