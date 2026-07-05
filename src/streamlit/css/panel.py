from __future__ import annotations

import re

import streamlit as st


PANEL_CSS = """
<style>
.result-shell {
    border: 1px solid var(--line);
    background: linear-gradient(180deg, rgba(17, 24, 39, .96), rgba(9, 14, 22, .98));
    border-radius: var(--radius-lg);
    padding: var(--s-4);
    box-shadow: var(--shadow-soft);
}
.result-eyebrow {
    color: var(--muted);
    font: 700 var(--fs-xs) 'JetBrains Mono', monospace;
    text-transform: uppercase;
    letter-spacing: .12em;
    margin-bottom: var(--s-2);
}
.result-status {
    display: grid;
    grid-template-columns: minmax(0, 1fr) auto;
    align-items: flex-start;
    justify-content: space-between;
    gap: var(--s-3);
    border-radius: var(--radius-md);
    padding: var(--s-3);
    margin-bottom: var(--s-3);
}
.result-status.safe {
    border: 1px solid rgba(52, 211, 153, .26);
    background: rgba(52, 211, 153, .08);
}
.result-status.risky {
    border: 1px solid rgba(251, 113, 133, .30);
    background: rgba(251, 113, 133, .09);
}
.status-title {
    color: var(--text);
    font: 800 var(--fs-2xl) 'Space Grotesk', sans-serif;
    line-height: 1.15;
    margin-bottom: var(--s-2);
}
.status-copy {
    color: var(--text-soft);
    font-size: var(--fs-md);
    line-height: 1.55;
}
.score-chip {
    min-width: 112px;
    text-align: right;
}
.score-label {
    color: var(--muted);
    font: 700 var(--fs-xs) 'JetBrains Mono', monospace;
    text-transform: uppercase;
    letter-spacing: .08em;
}
.score-value {
    color: var(--success);
    font: 800 var(--fs-3xl) 'JetBrains Mono', monospace;
}
.score-value.high { color: var(--danger); }
.metric-grid {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: var(--s-3);
    margin: var(--s-3) 0 var(--s-4);
}
.metric-card.wide {
    grid-column: 1 / -1;
}
.metric-card {
    border: 1px solid var(--line);
    background: var(--surface-soft);
    border-radius: var(--radius-md);
    padding: var(--s-3);
}
.metric-label {
    color: var(--muted);
    font: 700 var(--fs-xs) 'JetBrains Mono', monospace;
    text-transform: uppercase;
    letter-spacing: .08em;
    margin-bottom: var(--s-1);
}
.metric-value {
    color: var(--text);
    font-weight: 700;
    word-break: normal;
}
.metric-value.mono {
    font-family: 'JetBrains Mono', monospace;
    font-size: var(--fs-sm);
    overflow-wrap: anywhere;
}
.rules-title {
    margin-top: var(--s-3);
    margin-bottom: var(--s-2);
}
.rules-list {
    display: grid;
    gap: var(--s-2);
    margin-top: 0;
}
.rule-item {
    display: flex;
    align-items: center;
    gap: var(--s-2);
    border: 1px solid var(--line);
    background: var(--surface-soft);
    border-radius: var(--radius-md);
    padding: var(--s-3);
}
.rule-dot {
    width: var(--s-2);
    height: var(--s-2);
    border-radius: 999px;
    background: var(--warning);
    flex: 0 0 auto;
}
.rule-name {
    color: var(--text-soft);
    font-weight: 650;
    font-size: var(--fs-md);
}
.empty-result {
    min-height: 560px;
    border: 1px dashed var(--line-strong);
    background: linear-gradient(180deg, rgba(17, 24, 39, .72), rgba(9, 14, 22, .88));
    border-radius: var(--radius-lg);
    display: flex;
    align-items: center;
    justify-content: center;
    text-align: center;
    padding: var(--s-4);
}
.empty-mark {
    width: var(--s-8);
    height: var(--s-8);
    margin: 0 auto var(--s-3);
    border-radius: var(--radius-lg);
    border: 1px solid rgba(45, 212, 191, .28);
    background: rgba(45, 212, 191, .08);
    display: flex;
    align-items: center;
    justify-content: center;
    color: var(--primary);
    font-size: var(--fs-2xl);
}
.empty-title {
    color: var(--text);
    font: 800 var(--fs-xl) 'Space Grotesk', sans-serif;
    margin-bottom: var(--s-2);
}
.empty-copy {
    color: var(--text-soft);
    max-width: 360px;
    line-height: 1.6;
}
.feedback-note {
    color: var(--muted);
    font-size: var(--fs-sm);
    margin: var(--s-3) 0 var(--s-2);
}
@media (max-width: 720px) {
    .result-shell,
    .empty-result {
        min-height: auto;
        padding: var(--s-3);
        border-radius: var(--radius-md);
    }
    .result-status {
        grid-template-columns: 1fr;
    }
    .score-chip {
        min-width: 0;
        text-align: left;
        margin-top: var(--s-2);
    }
    .metric-grid {
        grid-template-columns: 1fr;
    }
}
</style>
"""

_SEVERITY_TEXT = {
    "HIGH": "Cao",
    "MEDIUM": "Trung bình",
    "LOW": "Thấp",
}

_RULE_TEXT = {
    "high_amount": "Số tiền cao",
    "high amount": "Số tiền cao",
    "night_transaction": "Giao dịch ban đêm",
    "night transaction": "Giao dịch ban đêm",
    "high_ip_risk": "IP rủi ro cao",
    "high ip risk": "IP rủi ro cao",
    "velocity_spike": "Tần suất tăng bất thường",
    "velocity spike": "Tần suất tăng bất thường",
    "high_utilization": "Dùng hạn mức cao",
    "high utilization": "Dùng hạn mức cao",
}


def _clean(text: object) -> str:
    text = re.sub(r"</?[^>]+>", "", str(text or ""))
    key = text.strip().lower()
    if key in _RULE_TEXT:
        return _RULE_TEXT[key]
    return text.replace("_", " ").strip().title()


def _fmt_time(value: object) -> str:
    raw = str(value or "-")
    if "T" in raw:
        return raw.replace("T", " ").split(".")[0]
    return raw


def _fmt_score(score: float) -> str:
    percent = score * 100
    if percent == 0:
        return "0%"
    if percent < 0.01:
        return f"{percent:.4f}%"
    if percent < 0.1:
        return f"{percent:.3f}%"
    if percent < 1:
        return f"{percent:.2f}%"
    return f"{percent:.1f}%"


def render_result_panel(result: dict) -> str | None:
    st.markdown(PANEL_CSS, unsafe_allow_html=True)

    is_fraud = bool(result.get("is_fraud", False))
    score = float(result.get("confidence", 0.0))
    severity = str(result.get("severity", "LOW")).upper()
    prediction_id = result.get("prediction_id")
    factors = result.get("risk_factors", [])

    status_class = "risky" if is_fraud else "safe"
    score_class = "high" if is_fraud else ""
    status_title = "Gian lận" if is_fraud else "An toàn"
    status_copy = (
        "Mô hình đánh dấu giao dịch này là gian lận. Nên giữ lại để kiểm tra."
        if is_fraud
        else "Mô hình chưa thấy tín hiệu gian lận rõ."
    )

    st.markdown(
        f"""
        <div class="result-shell">
            <div class="result-eyebrow">Kết quả phân tích</div>
            <div class="result-status {status_class}">
                <div>
                    <div class="status-title">{status_title}</div>
                    <div class="status-copy">{status_copy}</div>
                </div>
                <div class="score-chip">
                    <div class="score-label">Điểm gian lận</div>
                    <div class="score-value {score_class}">{_fmt_score(score)}</div>
                </div>
            </div>
            <div class="metric-grid">
                <div class="metric-card">
                    <div class="metric-label">Mức rủi ro</div>
                    <div class="metric-value">{_SEVERITY_TEXT.get(severity, severity)}</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Thời điểm</div>
                    <div class="metric-value">{_fmt_time(result.get("prediction_time"))}</div>
                </div>
                <div class="metric-card wide">
                    <div class="metric-label">Mã dự đoán</div>
                    <div class="metric-value mono">{prediction_id or "-"}</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<div class="result-eyebrow rules-title">Tín hiệu kích hoạt</div>', unsafe_allow_html=True)
    if factors:
        st.markdown('<div class="rules-list">', unsafe_allow_html=True)
        for factor in factors[:6]:
            name = _clean(factor.get("name") if isinstance(factor, dict) else factor)
            if not name:
                continue
            st.markdown(
                f"""
                <div class="rule-item">
                    <div class="rule-dot"></div>
                    <div class="rule-name">{name}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.caption("Không có rule giải thích nào được kích hoạt.")

    st.markdown('<div class="feedback-note">Gửi feedback để lưu nhãn thực tế cho prediction này.</div>', unsafe_allow_html=True)
    action = None
    col1, col2 = st.columns(2)
    disabled = not bool(prediction_id)
    with col1:
        if st.button("Kết quả đúng", disabled=disabled, use_container_width=True):
            action = "confirm"
    with col2:
        if st.button("Kết quả sai", disabled=disabled, use_container_width=True):
            action = "correct"

    with st.expander("Phản hồi API gốc"):
        st.json(result.get("_raw", result))

    return action


def render_empty_panel() -> None:
    st.markdown(PANEL_CSS, unsafe_allow_html=True)
    st.markdown(
        """
        <div class="empty-result">
            <div>
                <div class="empty-mark">⌁</div>
                <div class="empty-title">Sẵn sàng phân tích</div>
                <div class="empty-copy">
                    Chọn một mẫu giao dịch hoặc chỉnh từng trường bên trái, sau đó chạy phân tích.
                    Kết quả sẽ lấy trực tiếp từ FastAPI model service.
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
