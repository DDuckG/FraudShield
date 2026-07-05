import streamlit as st


SIDEBAR_CSS = """
<style>
.side-brand {
    padding: var(--s-1) var(--s-1) var(--s-4);
    border-bottom: 1px solid var(--line);
    margin-bottom: var(--s-4);
}
.side-logo {
    width: var(--s-6);
    height: var(--s-6);
    border-radius: var(--radius-md);
    background: linear-gradient(135deg, var(--primary), var(--accent));
    color: #071018;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 900;
    margin-bottom: var(--s-3);
}
.side-title {
    color: var(--text);
    font: 800 var(--fs-xl) 'Space Grotesk', sans-serif;
}
.side-copy {
    color: var(--muted);
    font-size: var(--fs-sm);
    line-height: 1.5;
    margin-top: var(--s-2);
}
.side-section {
    color: var(--muted-2);
    font: 700 var(--fs-xs) 'JetBrains Mono', monospace;
    letter-spacing: .12em;
    text-transform: uppercase;
    margin: var(--s-4) 0 var(--s-2);
}
.side-step {
    display: flex;
    gap: var(--s-2);
    align-items: flex-start;
    padding: var(--s-3);
    border: 1px solid var(--line);
    background: var(--surface-soft);
    border-radius: var(--radius-md);
    margin-bottom: var(--s-2);
}
.step-index {
    width: var(--s-4);
    height: var(--s-4);
    border-radius: var(--radius-sm);
    background: rgba(45, 212, 191, .12);
    color: var(--primary);
    display: flex;
    align-items: center;
    justify-content: center;
    font: 800 var(--fs-xs) 'JetBrains Mono', monospace;
    flex: 0 0 auto;
}
.step-title {
    color: var(--text-soft);
    font-weight: 700;
    font-size: var(--fs-md);
}
.step-sub {
    color: var(--muted);
    font-size: var(--fs-sm);
    margin-top: var(--s-1);
    line-height: 1.4;
}
.side-footer {
    margin-top: var(--s-4);
    border-top: 1px solid var(--line);
    padding-top: var(--s-3);
    color: var(--muted-2);
    font: 600 var(--fs-xs) 'JetBrains Mono', monospace;
}
</style>
"""


def render_sidebar() -> str:
    st.markdown(SIDEBAR_CSS, unsafe_allow_html=True)

    with st.sidebar:
        st.markdown(
            """
            <div class="side-brand">
                <div class="side-logo">FS</div>
                <div class="side-title">FraudShield</div>
                <div class="side-copy">
                    Demo kiểm tra gian lận theo thời gian gần thực, nối trực tiếp FastAPI model service.
                </div>
            </div>
            <div class="side-section">Luồng xử lý</div>
            <div class="side-step">
                <div class="step-index">1</div>
                <div>
                    <div class="step-title">Nhập giao dịch</div>
                    <div class="step-sub">Dùng mẫu có sẵn hoặc chỉnh từng tín hiệu.</div>
                </div>
            </div>
            <div class="side-step">
                <div class="step-index">2</div>
                <div>
                    <div class="step-title">Gọi FastAPI</div>
                    <div class="step-sub">Payload đi qua endpoint /predict thật.</div>
                </div>
            </div>
            <div class="side-step">
                <div class="step-index">3</div>
                <div>
                    <div class="step-title">Lưu feedback</div>
                    <div class="step-sub">Prediction và nhãn review được ghi về GCS.</div>
                </div>
            </div>
            <div class="side-footer">
                LUỒNG MODEL<br>
                DVC → MLflow → FastAPI → GCS
            </div>
            """,
            unsafe_allow_html=True,
        )

    return "demo"
