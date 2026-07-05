import sys
from pathlib import Path

import requests
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from css.panel import render_empty_panel, render_result_panel
from css.sidebar import render_sidebar
from css.theme import inject_theme
from css.tx_form import render_tx_form
from web import health_check, safe_analyze, safe_feedback


st.set_page_config(
    page_title="FraudShield Demo",
    page_icon="FS",
    layout="wide",
    initial_sidebar_state="collapsed",
)

inject_theme()
render_sidebar()


def _api_status() -> tuple[dict | None, str | None]:
    try:
        return health_check(), None
    except requests.RequestException as exc:
        return None, str(exc)


def _render_header(status: dict | None, error: str | None) -> None:
    is_live = bool(status and status.get("status") == "healthy")
    badge_color = "var(--success)" if is_live else "var(--warning)"
    badge_text = "API đang chạy" if is_live else "API chưa sẵn sàng"
    model_text = "-"
    if status:
        model_text = f"{status.get('model_type', '-')}/{status.get('dataset_branch', '-')}"

    st.markdown(
        f"""
        <style>
        .hero {{
            border: 1px solid rgba(141, 153, 174, .18);
            background:
                linear-gradient(135deg, rgba(45, 212, 191, .09), rgba(96, 165, 250, .06)),
                rgba(17, 24, 39, .80);
            border-radius: var(--radius-lg);
            padding: var(--s-4);
            margin-bottom: var(--s-4);
        }}
        .hero-top {{
            display: grid;
            grid-template-columns: minmax(0, 8fr) minmax(220px, 4fr);
            justify-content: space-between;
            gap: var(--s-4);
            align-items: flex-start;
        }}
        .hero-kicker {{
            color: var(--primary);
            font: 700 var(--fs-xs) 'JetBrains Mono', monospace;
            text-transform: uppercase;
            letter-spacing: .12em;
            margin-bottom: var(--s-2);
        }}
        .hero-title {{
            color: var(--text);
            font: 800 var(--fs-3xl) 'Space Grotesk', sans-serif;
            line-height: 1.1;
            margin-bottom: var(--s-2);
        }}
        .hero-copy {{
            color: var(--text-soft);
            max-width: 680px;
            line-height: 1.6;
            font-size: var(--fs-md);
        }}
        .status-stack {{
            display: grid;
            gap: var(--s-2);
        }}
        .status-badge {{
            border: 1px solid var(--line);
            background: var(--surface-soft);
            border-radius: var(--radius-md);
            padding: var(--s-3);
        }}
        .status-label {{
            color: var(--muted);
            font: 700 var(--fs-xs) 'JetBrains Mono', monospace;
            text-transform: uppercase;
            letter-spacing: .08em;
        }}
        .status-value {{
            color: var(--text);
            font-weight: 800;
            margin-top: var(--s-1);
        }}
        .status-dot {{
            display: inline-block;
            width: var(--s-2);
            height: var(--s-2);
            border-radius: 999px;
            background: {badge_color};
            margin-right: var(--s-2);
            box-shadow: 0 0 var(--s-3) {badge_color};
        }}
        @media (max-width: 720px) {{
            .hero {{
                padding: var(--s-3);
                border-radius: var(--radius-md);
            }}
            .hero-top {{
                grid-template-columns: 1fr;
            }}
            .hero-title {{
                font-size: var(--fs-2xl);
            }}
            .status-stack {{
                margin-top: 0;
            }}
        }}
        </style>
        <div class="hero">
            <div class="hero-top">
                <div>
                    <div class="hero-kicker">FraudShield kiểm tra giao dịch</div>
                    <div class="hero-title">Kiểm tra rủi ro giao dịch</div>
                    <div class="hero-copy">
                        Demo này gọi trực tiếp FastAPI model service, trả về fraud score, rule giải thích
                        và cho phép gửi feedback để lưu nhãn review.
                    </div>
                </div>
                <div class="status-stack">
                    <div class="status-badge">
                        <div class="status-label">Trạng thái API</div>
                        <div class="status-value"><span class="status-dot"></span>{badge_text}</div>
                    </div>
                    <div class="status-badge">
                        <div class="status-label">Model đang dùng</div>
                        <div class="status-value">{model_text}</div>
                    </div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if error:
        st.warning(f"Không đọc được /health: {error}")


status, health_error = _api_status()
_render_header(status, health_error)

left_col, right_col = st.columns([7, 5], gap="medium")

with left_col:
    form_data = render_tx_form()

if "last_result" not in st.session_state:
    st.session_state["last_result"] = None
if "last_warning" not in st.session_state:
    st.session_state["last_warning"] = None
if "feedback_notice" not in st.session_state:
    st.session_state["feedback_notice"] = None

if form_data:
    with st.spinner("Đang gọi FastAPI model service..."):
        result, warning = safe_analyze(form_data)
    st.session_state["last_result"] = result
    st.session_state["last_warning"] = warning
    st.session_state["feedback_notice"] = None

with right_col:
    if st.session_state["last_warning"]:
        st.error(st.session_state["last_warning"])

    if st.session_state["feedback_notice"]:
        st.success(st.session_state["feedback_notice"])

    result = st.session_state["last_result"]
    if result:
        action = render_result_panel(result)
        if action:
            actual_label = bool(result.get("is_fraud")) if action == "confirm" else not bool(result.get("is_fraud"))
            feedback, warning = safe_feedback(result["prediction_id"], actual_label)
            if warning:
                st.session_state["feedback_notice"] = None
                st.error(warning)
            else:
                st.session_state["feedback_notice"] = f"Đã lưu feedback cho prediction {feedback['prediction_id']}."
                st.rerun()
    else:
        render_empty_panel()
