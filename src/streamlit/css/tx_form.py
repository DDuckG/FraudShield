from __future__ import annotations

from datetime import datetime

import streamlit as st


FORM_CSS = """
<style>
.form-shell {
    border: 1px solid var(--line);
    background: linear-gradient(180deg, rgba(17, 24, 39, .96), rgba(9, 14, 22, .98));
    border-radius: var(--radius-lg);
    padding: var(--s-4);
    box-shadow: var(--shadow-soft);
}
.form-kicker {
    color: var(--primary);
    font: 700 var(--fs-xs) 'JetBrains Mono', monospace;
    letter-spacing: .12em;
    text-transform: uppercase;
    margin-bottom: var(--s-2);
}
.form-title {
    color: var(--text);
    font: 800 var(--fs-2xl) 'Space Grotesk', sans-serif;
    line-height: 1.15;
    margin-bottom: var(--s-2);
}
.form-copy {
    color: var(--text-soft);
    line-height: 1.6;
    font-size: var(--fs-md);
    margin-bottom: var(--s-4);
}
.preset-note {
    border: 1px solid rgba(45, 212, 191, .22);
    background: rgba(45, 212, 191, .08);
    color: var(--text-soft);
    border-radius: var(--radius-md);
    padding: var(--s-3);
    font-size: var(--fs-sm);
    line-height: 1.5;
    margin: var(--s-3) 0 var(--s-3);
}
.section-title {
    color: var(--muted);
    font: 700 var(--fs-xs) 'JetBrains Mono', monospace;
    text-transform: uppercase;
    letter-spacing: .12em;
    border-bottom: 1px solid var(--line);
    padding-bottom: var(--s-2);
    margin: var(--s-4) 0 var(--s-3);
}
.api-pill {
    display: flex;
    align-items: center;
    gap: var(--s-2);
    border: 1px solid rgba(45, 212, 191, .22);
    background: rgba(45, 212, 191, .08);
    border-radius: var(--radius-md);
    padding: var(--s-3);
    color: var(--text-soft);
    font-size: var(--fs-sm);
    line-height: 1.5;
}
.api-dot {
    width: var(--s-2);
    height: var(--s-2);
    border-radius: 999px;
    background: var(--primary);
    box-shadow: 0 0 var(--s-3) rgba(45, 212, 191, .72);
    flex: 0 0 auto;
}
@media (max-width: 720px) {
    .form-shell {
        padding: var(--s-3);
        border-radius: var(--radius-md);
    }
    .form-title {
        font-size: var(--fs-xl);
    }
}
</style>
"""

MERCHANT_CATEGORIES = [
    "grocery",
    "online_retail",
    "restaurant",
    "gas_station",
    "atm",
    "clothing",
    "pharmacy",
    "electronics",
    "hotel",
    "travel",
]

DEVICE_TYPES = ["mobile_app", "pos_terminal", "web_browser", "atm", "phone_ivr"]

DAY_OPTIONS = {
    "Thứ hai": 0,
    "Thứ ba": 1,
    "Thứ tư": 2,
    "Thứ năm": 3,
    "Thứ sáu": 4,
    "Thứ bảy": 5,
    "Chủ nhật": 6,
}

DEMO_CASES = {
    "Rủi ro cao - đêm, thiết bị lạ": {
        "transaction_id": "TX-DEMO-HIGH",
        "user_id": "USR-7821",
        "hour_of_day": 2,
        "day_label": "Thứ bảy",
        "is_weekend": True,
        "amount": 250.0,
        "merchant_country": "US",
        "merchant_category": "electronics",
        "mcc_code": 5732,
        "device_type": "mobile_app",
        "ip_risk_score": 0.72,
        "card_present": False,
        "device_known": False,
        "is_foreign_txn": True,
        "has_2fa": False,
        "time_since_last_s": 120.0,
        "velocity_1h": 4.0,
        "amount_vs_avg_ratio": 2.5,
        "account_age_days": 120,
        "credit_limit": 5000.0,
    },
    "Bình thường - cửa hàng quen": {
        "transaction_id": "TX-DEMO-LOW",
        "user_id": "USR-2044",
        "hour_of_day": 14,
        "day_label": "Thứ tư",
        "is_weekend": False,
        "amount": 42.5,
        "merchant_country": "US",
        "merchant_category": "grocery",
        "mcc_code": 5411,
        "device_type": "pos_terminal",
        "ip_risk_score": 0.06,
        "card_present": True,
        "device_known": True,
        "is_foreign_txn": False,
        "has_2fa": True,
        "time_since_last_s": 7200.0,
        "velocity_1h": 1.0,
        "amount_vs_avg_ratio": 0.8,
        "account_age_days": 840,
        "credit_limit": 8000.0,
    },
}


def _section(label: str) -> None:
    st.markdown(f'<div class="section-title">{label}</div>', unsafe_allow_html=True)


def _idx(options: list[str], value: str) -> int:
    return options.index(value) if value in options else 0


def _parse_int(label: str, value: str, min_value: int = 0, max_value: int | None = None) -> int | None:
    try:
        parsed = int(str(value).strip())
    except ValueError:
        st.error(f"Cảnh báo: {label} cần là số nguyên.")
        return None
    if parsed < min_value or (max_value is not None and parsed > max_value):
        st.error(f"Cảnh báo: {label} cần nằm trong khoảng hợp lệ.")
        return None
    return parsed


def _parse_float(label: str, value: str, min_value: float = 0.0) -> float | None:
    try:
        parsed = float(str(value).strip())
    except ValueError:
        st.error(f"Cảnh báo: {label} cần là số.")
        return None
    if parsed < min_value:
        st.error(f"Cảnh báo: {label} không được âm.")
        return None
    return parsed


def render_tx_form() -> dict | None:
    st.markdown(FORM_CSS, unsafe_allow_html=True)
    st.markdown(
        """
        <div class="form-shell">
            <div class="form-kicker">FraudShield demo trực tiếp</div>
            <div class="form-title">Nhập giao dịch cần kiểm tra</div>
            <div class="form-copy">
                Form này gửi payload thật tới FastAPI <b>/predict</b>. Có thể dùng mẫu sẵn để demo nhanh,
                hoặc chỉnh từng trường để xem mô hình phản ứng như thế nào.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    case_name = st.selectbox("Mẫu giao dịch", list(DEMO_CASES.keys()))
    case = DEMO_CASES[case_name]

    st.markdown(
        """
        <div class="preset-note">
            Mẫu chỉ là điểm bắt đầu. Các trường bên dưới vẫn có thể chỉnh trước khi bấm phân tích.
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.form("tx_form", clear_on_submit=False):
        _section("Định danh")
        col1, col2 = st.columns(2)
        with col1:
            transaction_id = st.text_input("Mã giao dịch", value=f"{case['transaction_id']}-{datetime.now().strftime('%H%M%S')}")
        with col2:
            user_id = st.text_input("Mã người dùng", value=case["user_id"])

        _section("Thời gian")
        col1, col2, col3 = st.columns(3)
        with col1:
            hour_of_day_raw = st.text_input("Giờ giao dịch", value=str(case["hour_of_day"]))
        with col2:
            day_label = st.selectbox("Ngày trong tuần", list(DAY_OPTIONS.keys()), index=_idx(list(DAY_OPTIONS.keys()), case["day_label"]))
        with col3:
            is_weekend = st.toggle("Cuối tuần", value=bool(case["is_weekend"]))

        _section("Giao dịch")
        col1, col2 = st.columns(2)
        with col1:
            amount_raw = st.text_input("Số tiền", value=f"{case['amount']:.2f}")
        with col2:
            credit_limit_raw = st.text_input("Hạn mức thẻ", value=f"{case['credit_limit']:.2f}")

        col1, col2, col3 = st.columns(3)
        with col1:
            merchant_country = st.text_input("Quốc gia đơn vị bán", value=case["merchant_country"], max_chars=3)
        with col2:
            merchant_category = st.selectbox("Nhóm đơn vị bán", MERCHANT_CATEGORIES, index=_idx(MERCHANT_CATEGORIES, case["merchant_category"]))
        with col3:
            mcc_code_raw = st.text_input("Mã MCC", value=str(case["mcc_code"]))

        _section("Thiết bị và bảo mật")
        col1, col2 = st.columns(2)
        with col1:
            device_type = st.selectbox("Thiết bị", DEVICE_TYPES, index=_idx(DEVICE_TYPES, case["device_type"]))
        with col2:
            ip_risk_score_raw = st.text_input("Điểm rủi ro IP", value=f"{case['ip_risk_score']:.2f}")

        col1, col2 = st.columns(2)
        with col1:
            card_present = st.toggle("Có thẻ", value=bool(case["card_present"]))
        with col2:
            device_known = st.toggle("Thiết bị quen", value=bool(case["device_known"]))
        col1, col2 = st.columns(2)
        with col1:
            is_foreign_txn = st.toggle("Giao dịch ngoại", value=bool(case["is_foreign_txn"]))
        with col2:
            has_2fa = st.toggle("Có 2FA", value=bool(case["has_2fa"]))

        _section("Hành vi tài khoản")
        col1, col2 = st.columns(2)
        with col1:
            time_since_last_s_raw = st.text_input("Giây từ giao dịch trước", value=f"{case['time_since_last_s']:.0f}")
        with col2:
            velocity_1h_raw = st.text_input("Số giao dịch trong 1h", value=f"{case['velocity_1h']:.0f}")
        col1, col2 = st.columns(2)
        with col1:
            amount_vs_avg_ratio_raw = st.text_input("Tỷ lệ so với trung bình", value=f"{case['amount_vs_avg_ratio']:.2f}")
        with col2:
            account_age_days_raw = st.text_input("Tuổi tài khoản (ngày)", value=str(case["account_age_days"]))

        submitted = st.form_submit_button("Phân tích giao dịch", use_container_width=True)

    st.markdown(
        """
        <div class="api-pill">
            <div class="api-dot"></div>
            <div>Payload được gửi tới FastAPI, kết quả hiển thị ở panel bên phải và có thể gửi feedback lại hệ thống.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if not submitted:
        return None

    hour_of_day = _parse_int("Giờ giao dịch", hour_of_day_raw, 0, 23)
    amount = _parse_float("Số tiền", amount_raw, 0.01)
    credit_limit = _parse_float("Hạn mức thẻ", credit_limit_raw, 0.01)
    mcc_code = _parse_int("Mã MCC", mcc_code_raw, 0, 9999)
    ip_risk_score = _parse_float("Điểm rủi ro IP", ip_risk_score_raw, 0.0)
    time_since_last_s = _parse_float("Giây từ giao dịch trước", time_since_last_s_raw, 0.0)
    velocity_1h = _parse_float("Số giao dịch trong 1h", velocity_1h_raw, 0.0)
    amount_vs_avg_ratio = _parse_float("Tỷ lệ so với trung bình", amount_vs_avg_ratio_raw, 0.0)
    account_age_days = _parse_int("Tuổi tài khoản", account_age_days_raw, 0)

    if None in {
        hour_of_day,
        amount,
        credit_limit,
        mcc_code,
        ip_risk_score,
        time_since_last_s,
        velocity_1h,
        amount_vs_avg_ratio,
        account_age_days,
    }:
        return None

    return {
        "transaction_id": transaction_id.strip(),
        "user_id": user_id.strip(),
        "hour_of_day": int(hour_of_day),
        "day_of_week": int(DAY_OPTIONS[day_label]),
        "is_weekend": int(is_weekend),
        "amount": float(amount),
        "card_present": int(card_present),
        "device_known": int(device_known),
        "is_foreign_txn": int(is_foreign_txn),
        "has_2fa": int(has_2fa),
        "time_since_last_s": float(time_since_last_s),
        "velocity_1h": float(velocity_1h),
        "amount_vs_avg_ratio": float(amount_vs_avg_ratio),
        "account_age_days": int(account_age_days),
        "credit_limit": float(credit_limit),
        "merchant_category": merchant_category,
        "merchant_country": merchant_country.strip().upper(),
        "device_type": device_type,
        "mcc_code": int(mcc_code),
        "ip_risk_score": float(ip_risk_score),
    }
