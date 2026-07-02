from datetime import datetime, timezone
from google.cloud import storage

from src.settings import env


GCS_BUCKET = env("GCS_BUCKET_NAME")
DRIFT_REPORT_PREFIX = env("DRIFT_REPORT_PREFIX", "drift-reports")


_gcs_client: storage.Client | None = None


def _get_gcs_client() -> storage.Client:
    global _gcs_client
    if _gcs_client is None:
        _gcs_client = storage.Client()
    return _gcs_client


def upload_drift_report(local_path: str) -> dict:
    if not GCS_BUCKET:
        raise RuntimeError("Missing GCS_BUCKET_NAME environment variable")

    now = datetime.now(timezone.utc)
    dt = now.strftime("%Y-%m-%d")
    hour = now.strftime("%H")
    ts = now.strftime("%Y%m%dT%H%M%SZ")

    archive_blob = (
        f"{DRIFT_REPORT_PREFIX}/archive/dt={dt}/hour={hour}/"
        f"drift_report_{ts}.html"
    )
    latest_blob = f"{DRIFT_REPORT_PREFIX}/latest/drift_report.html"

    client = _get_gcs_client()
    bucket = client.bucket(GCS_BUCKET)

    # Một bản lưu theo thời gian để xem lại lịch sử.
    archive = bucket.blob(archive_blob)
    archive.upload_from_filename(local_path, content_type="text/html")

    # Một bản cố định cho dashboard/link nhanh.
    latest = bucket.blob(latest_blob)
    latest.upload_from_filename(local_path, content_type="text/html")

    return {
        "archive_blob": archive_blob,
        "latest_blob": latest_blob,
    }
