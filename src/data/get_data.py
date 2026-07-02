import argparse
import sys
import tempfile
import zipfile
from pathlib import Path
from urllib.request import urlretrieve
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.features.contracts import (
    KAGGLE_DATASET_URL,
    KAGGLE_TRANSACTION_FILE,
    project_path,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Tải đúng bảng giao dịch từ Kaggle.")
    parser.add_argument("--dataset-url", default=KAGGLE_DATASET_URL)
    parser.add_argument("--zip-member", default=KAGGLE_TRANSACTION_FILE)
    parser.add_argument("--raw-output", default="data/raw/transactions.csv")
    return parser.parse_args()


def _path(value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else project_path(value)


def download_dataset(url: str, output_zip: Path) -> None:
    output_zip.parent.mkdir(parents=True, exist_ok=True)
    print(f"Tải archive Kaggle về: {output_zip}")
    urlretrieve(url, output_zip)


def extract_transactions(zip_path: Path, member_name: str, output_csv: Path) -> None:
    output_csv.parent.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(zip_path) as archive:
        # Dataset có vài bảng phụ, pipeline này chỉ cần bảng giao dịch.
        with archive.open(member_name) as source, open(output_csv, "wb") as target:
            target.write(source.read())

    print(f"Đã lưu dữ liệu giao dịch: {output_csv}")


def show_quick_check(raw_csv: Path) -> None:
    # Chỉ cần cột thời gian để kiểm tra nhanh file tải về có đúng bảng chính không.
    df = pd.read_csv(raw_csv, usecols=["timestamp"])
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    print(f"Số dòng: {len(df):,}")
    print(f"Thời gian: {df['timestamp'].min()} -> {df['timestamp'].max()}")


def main() -> None:
    args = parse_args()

    raw_output = _path(args.raw_output)

    with tempfile.TemporaryDirectory() as tmp_dir:
        zip_path = Path(tmp_dir) / "kaggle_fraud_dataset.zip"
        download_dataset(args.dataset_url, zip_path)
        extract_transactions(zip_path, args.zip_member, raw_output)

    show_quick_check(raw_output)


if __name__ == "__main__":
    main()
