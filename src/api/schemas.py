from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


class FraudDetectionRequest(BaseModel):
    # Giữ chặt schema để biết ngay khi client gửi nhầm tên biến.
    model_config = ConfigDict(extra="forbid")

    transaction_id: str
    user_id: str

    # Các biến số và biến cờ lấy theo đúng bảng giao dịch.
    hour_of_day: int = Field(..., ge=0, le=23)
    day_of_week: int = Field(..., ge=0, le=6)
    is_weekend: int = Field(..., ge=0, le=1)

    amount: float = Field(..., gt=0)

    card_present: int = Field(..., ge=0, le=1)
    device_known: int = Field(..., ge=0, le=1)
    is_foreign_txn: int = Field(..., ge=0, le=1)
    has_2fa: int = Field(..., ge=0, le=1)

    time_since_last_s: float = Field(..., ge=0)
    velocity_1h: float = Field(..., ge=0)
    amount_vs_avg_ratio: float = Field(..., ge=0)
    account_age_days: int = Field(..., ge=0)

    credit_limit: float = Field(..., gt=0)

    # Nhóm phân loại sẽ được mã hóa giống lúc train.
    merchant_category: str
    merchant_country: str
    device_type: str

    mcc_code: int = Field(..., ge=0)

    ip_risk_score: float = Field(..., ge=0)


class FraudResponse(BaseModel):
    is_fraud: bool
    fraud_score: float
    risk_level: Literal["Low", "Medium", "High"]
    triggered_rules: List[str]
    prediction_time: datetime


class BatchFraudResponse(BaseModel):
    results: List[FraudResponse]
    total: int
    fraud_count: int

class FeedbackRequest(BaseModel):
    prediction_id: str
    actual_label: bool
    feedback_time: Optional[datetime] = None
    source: Literal["manual_review", "chargeback", "system", "other"] = "other"


class FeedbackResponse(BaseModel):
    status: str
    prediction_id: str
    stored_at: datetime
