from __future__ import annotations

import logging
import re

import requests

from src.settings import env


log = logging.getLogger(__name__)

BASE_URL = env("FRAUD_API_URL", "http://136.111.173.2").rstrip("/")
TIMEOUT = 120


def _post(path: str, payload: dict) -> dict:
    response = requests.post(f"{BASE_URL}{path}", json=payload, timeout=TIMEOUT)
    response.raise_for_status()
    return response.json()


def _get(path: str, params: dict | None = None) -> dict:
    response = requests.get(f"{BASE_URL}{path}", params=params, timeout=TIMEOUT)
    response.raise_for_status()
    return response.json()


def _clean_text(value: object) -> str:
    return re.sub(r"<[^>]+>", "", str(value)).strip()


def _normalize(raw: dict) -> dict:
    rules = raw.get("triggered_rules", raw.get("risk_factors", []))
    normalized_rules = []

    for rule in rules:
        if isinstance(rule, dict):
            name = _clean_text(rule.get("name", "Unknown"))
            detail = _clean_text(rule.get("detail", ""))
        else:
            name = _clean_text(rule)
            detail = ""

        if name:
            normalized_rules.append({"name": name.replace("_", " ").title(), "detail": detail})

    # Panel cũ đang đọc bộ tên này, nên client đổi tên response một lần ở đây.
    return {
        "is_fraud": bool(raw.get("is_fraud", False)),
        "confidence": float(raw.get("fraud_score", raw.get("confidence", 0.0))),
        "severity": str(raw.get("risk_level", raw.get("severity", "Low"))).upper(),
        "risk_factors": normalized_rules,
        "prediction_time": raw.get("prediction_time", "-"),
        "origin_node": raw.get("origin_node", "-"),
        "latency": raw.get("latency", "-"),
        "_raw": raw,
    }


def analyze_transaction(tx_data: dict) -> dict:
    raw = _post("/predict", tx_data)
    return _normalize(raw)


def health_check() -> dict:
    return _get("/health")


def safe_analyze(tx_data: dict) -> tuple[dict | None, str | None]:
    try:
        return analyze_transaction(tx_data), None
    except requests.RequestException as exc:
        message = f"Không gọi được API ở {BASE_URL}: {exc}"
        log.warning(message)
        return None, message
