DARK_THEME_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600;700&family=Space+Grotesk:wght@400;500;600;700;800&display=swap');

:root {
    --bg: #090e16;
    --surface: #111827;
    --surface-2: #172033;
    --surface-soft: rgba(255, 255, 255, .04);
    --line: rgba(148, 163, 184, .18);
    --line-strong: rgba(148, 163, 184, .30);
    --text: #f8fafc;
    --text-soft: #cbd5e1;
    --muted: #94a3b8;
    --muted-2: #64748b;
    --primary: #2dd4bf;
    --primary-strong: #14b8a6;
    --accent: #60a5fa;
    --danger: #fb7185;
    --warning: #fbbf24;
    --success: #34d399;

    --s-1: 4px;
    --s-2: 8px;
    --s-3: 16px;
    --s-4: 24px;
    --s-5: 32px;
    --s-6: 40px;
    --s-7: 48px;
    --s-8: 64px;

    --fs-xs: 10px;
    --fs-sm: 12px;
    --fs-md: 14px;
    --fs-lg: 16px;
    --fs-xl: 20px;
    --fs-2xl: 24px;
    --fs-3xl: 32px;

    --radius-sm: 8px;
    --radius-md: 12px;
    --radius-lg: 16px;
    --shadow-soft: 0 16px 48px rgba(0, 0, 0, .28);
}

html, body, [class*="css"] {
    font-family: 'Space Grotesk', sans-serif !important;
    background: var(--bg) !important;
    color: var(--text) !important;
}

#MainMenu, footer, header { visibility: hidden; }
.stApp {
    background:
        linear-gradient(180deg, rgba(96, 165, 250, .06), transparent 320px),
        var(--bg) !important;
}
.block-container {
    max-width: 1184px !important;
    padding: var(--s-6) var(--s-4) var(--s-7) !important;
}
[data-testid="stHorizontalBlock"] {
    gap: var(--s-4) !important;
}

[data-testid="stSidebar"] {
    background: #0d1422 !important;
    border-right: 1px solid var(--line) !important;
}
[data-testid="stSidebar"] > div:first-child {
    padding-top: var(--s-5) !important;
}

label, [data-testid="stWidgetLabel"] {
    color: var(--muted) !important;
    font: 700 var(--fs-xs) 'JetBrains Mono', monospace !important;
    text-transform: uppercase !important;
    letter-spacing: .08em !important;
}

[data-testid="stTextInput"] input,
[data-testid="stNumberInput"] input,
[data-baseweb="select"] > div {
    background: var(--surface-soft) !important;
    border: 1px solid rgba(148, 163, 184, .24) !important;
    border-radius: var(--radius-md) !important;
    color: var(--text) !important;
    min-height: var(--s-7) !important;
    height: var(--s-7) !important;
    box-shadow: none !important;
    font-size: var(--fs-md) !important;
    line-height: 20px !important;
}

[data-baseweb="input"],
[data-baseweb="input"] > div,
[data-baseweb="input"] input,
input[type="text"],
input[type="number"],
textarea {
    background-color: var(--surface-soft) !important;
    color: var(--text) !important;
    -webkit-text-fill-color: var(--text) !important;
    caret-color: var(--primary) !important;
    outline: none !important;
}

[data-testid="stTextInput"] input,
[data-testid="stNumberInput"] input {
    padding: 0 var(--s-3) 2px !important;
}

[data-baseweb="input"],
[data-baseweb="input"] > div {
    border-radius: var(--radius-md) !important;
    align-items: center !important;
}

[data-baseweb="select"] > div,
[data-baseweb="select"] div {
    align-items: center !important;
}

[data-baseweb="select"] [role="button"],
[data-baseweb="select"] [role="combobox"] {
    min-height: var(--s-7) !important;
    align-items: center !important;
}

input:-webkit-autofill,
input:-webkit-autofill:hover,
input:-webkit-autofill:focus {
    box-shadow: 0 0 0 1000px var(--surface-2) inset !important;
    -webkit-text-fill-color: var(--text) !important;
}

[data-testid="stNumberInput"] div[data-baseweb="input"],
[data-testid="stNumberInput"] div[data-baseweb="input"] > div,
[data-testid="stNumberInput"] button {
    background: var(--surface-soft) !important;
    border-color: var(--line-strong) !important;
    color: var(--text) !important;
}

[data-testid="stNumberInput"] input {
    -webkit-text-fill-color: var(--text) !important;
}

[data-testid="stTextInput"] input:focus,
[data-testid="stNumberInput"] input:focus,
[data-baseweb="select"] > div:focus-within,
[data-baseweb="input"]:focus-within,
[data-baseweb="input"] > div:focus-within {
    border-color: rgba(248, 250, 252, .72) !important;
    box-shadow: none !important;
    outline: none !important;
}

[aria-invalid="true"],
[data-baseweb="input"]:has([aria-invalid="true"]),
[data-baseweb="input"] > div:has([aria-invalid="true"]) {
    border-color: var(--danger) !important;
    border-radius: var(--radius-md) !important;
}

[data-testid="stToggle"] label {
    text-transform: none !important;
    letter-spacing: 0 !important;
    font-family: 'Space Grotesk', sans-serif !important;
    font-size: var(--fs-sm) !important;
}

[data-testid="stButton"] button,
[data-testid="stFormSubmitButton"] button {
    border: 1px solid rgba(45, 212, 191, .30) !important;
    background: linear-gradient(135deg, var(--primary), var(--accent)) !important;
    color: #071018 !important;
    border-radius: var(--radius-md) !important;
    min-height: var(--s-7) !important;
    font-weight: 800 !important;
    letter-spacing: .01em !important;
    transition: transform .12s ease, filter .12s ease, box-shadow .12s ease !important;
}
[data-testid="stButton"] button:hover,
[data-testid="stFormSubmitButton"] button:hover {
    filter: brightness(1.05) !important;
    transform: translateY(-1px);
    box-shadow: 0 var(--s-2) var(--s-4) rgba(20, 184, 166, .18) !important;
}
[data-testid="stButton"] button:active,
[data-testid="stFormSubmitButton"] button:active {
    transform: translateY(0);
    filter: brightness(.96) !important;
}
[data-testid="stButton"] button:focus,
[data-testid="stFormSubmitButton"] button:focus {
    box-shadow: 0 0 0 var(--s-1) rgba(45, 212, 191, .20) !important;
}
[data-testid="stButton"] button:disabled {
    background: rgba(148, 163, 184, .14) !important;
    color: var(--muted-2) !important;
    border-color: var(--line) !important;
    box-shadow: none !important;
    transform: none !important;
}

[data-testid="stAlert"] {
    border-radius: var(--radius-md) !important;
    border: 1px solid var(--line) !important;
    font-size: var(--fs-md) !important;
}
hr {
    border-color: var(--line) !important;
}
.stExpander {
    border: 1px solid var(--line) !important;
    border-radius: var(--radius-md) !important;
    background: var(--surface-soft) !important;
}

@media (max-width: 720px) {
    .block-container {
        padding: var(--s-4) var(--s-3) var(--s-6) !important;
    }
    [data-testid="stHorizontalBlock"] {
        gap: var(--s-3) !important;
    }
    [data-testid="stSidebar"] {
        width: min(310px, 86vw) !important;
    }
    label, [data-testid="stWidgetLabel"] {
        font-size: var(--fs-xs) !important;
        line-height: 1.3 !important;
    }
}
</style>
"""


def inject_theme():
    import streamlit as st

    st.markdown(DARK_THEME_CSS, unsafe_allow_html=True)
