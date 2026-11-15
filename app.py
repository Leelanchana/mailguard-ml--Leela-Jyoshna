"""MailGuard ML - single-file Streamlit app (white / purple theme).

Page 1: Home  (project heading with names + navigation cards for every page)
Page 2: Email Analyzer  (samples, file upload, verdict card, indicators)
Other pages (Evaluation, Monitoring, Model Information) still load from views/.

Run locally:  streamlit run app.py
"""

from __future__ import annotations

import html
import re
from email import message_from_bytes, policy

import streamlit as st

APP_NAME = "MailGuard ML"
APP_TAGLINE = "AI-powered email spam detection"
NAME_1, NAME_2 = "Leela", "Jyoshna"

st.set_page_config(
    page_title=f"{APP_NAME} | Email Spam Analyzer",
    page_icon=":material/shield:",
    layout="wide",
    initial_sidebar_state="expanded",
)

from src.app_resources import get_model_bundle, get_service  # noqa: E402

# ==================================================
# THEME  (white + purple)
# ==================================================

CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Playfair+Display:ital,wght@0,600;0,700;1,600&display=swap');

:root {
    --accent: #7c3aed; --accent-2: #a855f7; --accent-soft: #f5f3ff;
    --bg: #ffffff; --panel: #ffffff; --panel-tint: #faf7ff;
    --border: rgba(124,58,237,0.16); --muted: #6b6485;
    --text: #1f1235; --text-soft: #4a4263;
    --ok: #16a34a; --warn: #d97706; --bad: #dc2626;
    color-scheme: light;
}
html, body, [class*="css"], .stApp { font-family: 'Inter', sans-serif; color: var(--text); }
html { font-size: 16px; }
.stApp {
    background:
        radial-gradient(900px 420px at 88% -10%, rgba(168,85,247,0.16), transparent 60%),
        radial-gradient(700px 420px at -10% 8%, rgba(124,58,237,0.10), transparent 60%),
        var(--bg);
}
.block-container { padding-top: 1.5rem; padding-bottom: 3rem; max-width: 1200px; }
#MainMenu, footer { visibility: hidden; }
header[data-testid="stHeader"] { background: transparent; }

/* Force a light look on built-in widgets, so no .streamlit/config.toml is needed */
[data-testid="stToolbar"] *, [data-testid="stSidebarCollapseButton"] * { color: var(--text) !important; }
[data-testid="stFileUploaderDropzone"] { background: var(--accent-soft); }
[data-testid="stFileUploaderDropzone"] *, [data-testid="stFileUploader"] small { color: var(--text-soft) !important; }
[data-testid="stFileUploaderDropzone"] button { background: #ffffff; color: var(--accent) !important; border: 1px solid var(--border); }
[data-testid="stSpinner"] *, [data-testid="stExpander"] summary p { color: var(--text-soft); }

/* Typography */
.stMarkdown p, .stMarkdown li, [data-testid="stCaptionContainer"] {
    font-size: 1rem; line-height: 1.7; color: var(--text-soft);
}
.stMarkdown strong { color: var(--text); font-weight: 600; }
label, [data-testid="stWidgetLabel"] p {
    font-size: 0.92rem !important; font-weight: 600 !important; color: var(--text) !important;
}
h1, h2, h3, h4 { letter-spacing: -0.015em; font-weight: 700; color: var(--text); }
h1 { font-size: 2rem; } h2 { font-size: 1.45rem; } h3 { font-size: 1.15rem; }
textarea, input { font-size: 0.97rem !important; line-height: 1.6 !important; border-radius: 10px !important; }

/* Names */
.credits {
    font-family: 'Playfair Display', Georgia, serif; font-style: italic; font-weight: 600;
    font-size: 1.2rem; line-height: 1.25; margin-top: 0.3rem; letter-spacing: 0.02em;
}
.credits .n1 { color: #6d28d9; } .credits .n2 { color: #b7791f; }
.credits .amp { color: var(--muted); font-size: 1rem; margin: 0 0.4rem; }
.credits-sm { font-size: 0.98rem; margin-top: 0; }

/* Sidebar (navigation links removed - only brand + status remain) */
section[data-testid="stSidebar"] { background: var(--accent-soft); border-right: 1px solid var(--border); }
[data-testid="stSidebarNav"], [data-testid="stSidebarNavItems"], [data-testid="stSidebarNavSeparator"] { display: none !important; }
.brand { display: flex; align-items: center; gap: 0.65rem; padding: 0.3rem 0 0.4rem; }
.brand-logo {
    width: 40px; height: 40px; border-radius: 12px; font-size: 1.3rem;
    display: flex; align-items: center; justify-content: center;
    background: linear-gradient(135deg, #7c3aed, #a855f7); box-shadow: 0 6px 18px rgba(124,58,237,0.35);
}
.brand-name { font-size: 1.1rem; font-weight: 700; line-height: 1.1; color: var(--text); }
.brand-tag { font-size: 0.72rem; color: var(--muted); }
.side-card {
    margin-top: 1rem; padding: 0.8rem 0.95rem; border-radius: 12px;
    background: #ffffff; border: 1px solid var(--border); font-size: 0.82rem; color: var(--text);
}
.side-card .row { display: flex; align-items: center; gap: 0.5rem; font-weight: 600; }
.side-card .meta { color: var(--muted); margin-top: 0.25rem; }
.privacy-note { margin-top: 1rem; font-size: 0.74rem; line-height: 1.5; color: var(--muted); }
.dot { width: 8px; height: 8px; border-radius: 50%; display: inline-block; }
.dot-ok { background: var(--ok); box-shadow: 0 0 8px var(--ok); }
.dot-err { background: var(--bad); box-shadow: 0 0 8px var(--bad); }

/* Components */
div[data-testid="stMetric"] { background: var(--panel); border: 1px solid var(--border); border-radius: 14px; padding: 0.9rem 1.1rem; box-shadow: 0 2px 10px rgba(124,58,237,0.06); }
div[data-testid="stMetricLabel"] { color: var(--muted); }
div[data-testid="stMetricValue"] { font-weight: 800; color: var(--text); }
.stButton > button, .stDownloadButton > button {
    border-radius: 10px; font-weight: 600; padding: 0.55rem 1.3rem;
    border: 1px solid var(--border); background: #ffffff; color: var(--accent); transition: all 0.15s ease;
}
.stButton > button[kind="primary"] { background: linear-gradient(90deg, #7c3aed, #a855f7); border: none; color: #ffffff; }
.stButton > button:hover { transform: translateY(-1px); border-color: var(--accent); box-shadow: 0 8px 20px rgba(124,58,237,0.22); }
textarea { background: #ffffff !important; color: var(--text) !important; border: 1px solid var(--border) !important; }
textarea::placeholder { color: #9a93b5 !important; }
textarea:focus { border-color: var(--accent) !important; box-shadow: 0 0 0 3px rgba(124,58,237,0.18) !important; }
div[data-testid="stFileUploader"] section {
    border: 2px dashed rgba(124,58,237,0.4); border-radius: 14px; background: var(--accent-soft);
}
div[data-testid="stFileUploader"] section:hover { background: #ede9fe; border-color: var(--accent); }
div[data-testid="stExpander"] { border-radius: 14px; border: 1px solid var(--border); background: var(--panel); }
div[data-testid="stDataFrame"] { border-radius: 12px; overflow: hidden; }
div[data-testid="stAlert"] { border-radius: 12px; }
.stTabs [data-baseweb="tab-list"] { gap: 0.4rem; border-bottom: 1px solid var(--border); }
.stTabs [data-baseweb="tab"] { font-weight: 600; }
.stTabs [aria-selected="true"] { color: var(--accent); }

/* Page links styled as elegant buttons */
a[data-testid="stPageLink-NavLink"] {
    justify-content: center; gap: 0.5rem; padding: 0.62rem 1rem; border-radius: 12px;
    border: 1px solid var(--border); background: #ffffff;
    transition: all 0.18s ease; text-decoration: none;
}
a[data-testid="stPageLink-NavLink"] p { font-weight: 600; font-size: 0.93rem; color: var(--accent); margin: 0; }
a[data-testid="stPageLink-NavLink"]:hover {
    border-color: var(--accent); background: var(--accent-soft);
    transform: translateY(-1px); box-shadow: 0 8px 22px rgba(124,58,237,0.2);
}
a[data-testid="stPageLink-NavLink"][aria-current="page"] { background: var(--accent-soft); border-color: var(--accent); }

/* Top bar (replaces the side navigation on inner pages) */
[class*="st-key-topbar"] { margin-bottom: 1.2rem; padding-bottom: 1rem; border-bottom: 1px solid var(--border); }
[class*="st-key-topbar"] a[data-testid="stPageLink-NavLink"] { padding: 0.45rem 0.8rem; border-radius: 999px; }
[class*="st-key-topbar"] a[data-testid="stPageLink-NavLink"] p { font-size: 0.85rem; }

/* Primary call-to-action */
[class*="st-key-cta"] a[data-testid="stPageLink-NavLink"] {
    padding: 0.95rem 1.6rem; border: none; border-radius: 14px;
    background: linear-gradient(90deg, #7c3aed, #a855f7);
    box-shadow: 0 10px 28px rgba(124,58,237,0.35);
}
[class*="st-key-cta"] a[data-testid="stPageLink-NavLink"] p { color: #ffffff; font-size: 1.05rem; font-weight: 700; letter-spacing: 0.01em; }
[class*="st-key-cta"] a[data-testid="stPageLink-NavLink"]:hover {
    background: linear-gradient(90deg, #6d28d9, #9333ea); box-shadow: 0 14px 34px rgba(124,58,237,0.5);
    transform: translateY(-2px);
}
[class*="st-key-cta"] a[data-testid="stPageLink-NavLink"]:hover p { color: #ffffff; }

/* Home */
.landing {
    text-align: center; padding: 3.2rem 1.5rem 2.6rem; margin-bottom: 1.2rem;
    border-radius: 22px; border: 1px solid var(--border);
    background: radial-gradient(600px 260px at 50% 0%, rgba(168,85,247,0.20), transparent 70%),
                linear-gradient(160deg, #ffffff, #f5f0ff);
    box-shadow: 0 10px 40px rgba(124,58,237,0.10);
}
.landing-badge {
    display: inline-block; padding: 0.3rem 0.9rem; border-radius: 999px; font-size: 0.78rem; font-weight: 600;
    letter-spacing: 0.08em; text-transform: uppercase; color: #6d28d9;
    border: 1px solid rgba(124,58,237,0.35); background: rgba(124,58,237,0.08);
}
.landing-title {
    font-size: 3.6rem; font-weight: 800; letter-spacing: -0.03em; line-height: 1.05; margin: 1rem 0 0.4rem;
    background: linear-gradient(90deg, #6d28d9, #c026d3); -webkit-background-clip: text; -webkit-text-fill-color: transparent;
}
.landing-names {
    font-family: 'Playfair Display', Georgia, serif; font-style: italic; font-weight: 600;
    font-size: 1.9rem; letter-spacing: 0.03em; margin-bottom: 0.9rem;
}
.landing-names .n1 { color: #6d28d9; } .landing-names .n2 { color: #b7791f; }
.landing-names .amp { color: var(--muted); font-size: 1.5rem; margin: 0 0.6rem; }
.landing-sub { max-width: 640px; margin: 0 auto 0.4rem; color: var(--text-soft); font-size: 1.05rem; line-height: 1.7; }
.feature { padding: 1.3rem 1.2rem; border-radius: 16px; height: 100%; background: var(--panel); border: 1px solid var(--border); box-shadow: 0 2px 12px rgba(124,58,237,0.06); }
.feature .icon { font-size: 1.6rem; margin-bottom: 0.4rem; }
.feature .ft { font-weight: 700; color: var(--text); margin-bottom: 0.25rem; }
.feature .fd { color: var(--muted); font-size: 0.92rem; line-height: 1.6; }

/* Home: navigation cards */
[class*="st-key-navcard"] {
    position: relative; padding: 1.35rem 1.25rem 1.1rem; border-radius: 18px;
    background: linear-gradient(160deg, #ffffff, var(--panel-tint));
    border: 1px solid var(--border); box-shadow: 0 2px 12px rgba(124,58,237,0.06); transition: all 0.2s ease;
}
[class*="st-key-navcard"]:hover {
    border-color: rgba(124,58,237,0.5); transform: translateY(-3px);
    box-shadow: 0 16px 36px rgba(124,58,237,0.18);
}
.nav-icon {
    width: 46px; height: 46px; border-radius: 13px; font-size: 1.35rem; margin-bottom: 0.85rem;
    display: flex; align-items: center; justify-content: center;
    background: linear-gradient(135deg, rgba(124,58,237,0.16), rgba(168,85,247,0.10));
    border: 1px solid rgba(124,58,237,0.25);
}
.nav-title { font-weight: 700; font-size: 1.05rem; color: var(--text); margin-bottom: 0.3rem; }
.nav-desc { color: var(--muted); font-size: 0.88rem; line-height: 1.55; min-height: 4.1rem; margin-bottom: 0.7rem; }

/* Analyzer */
.page-head { margin-bottom: 1.2rem; }
.page-head .t { font-size: 1.9rem; font-weight: 800; color: var(--text); letter-spacing: -0.02em; }
.page-head .s { color: var(--muted); font-size: 0.95rem; margin-top: 0.15rem; }
.section-label {
    font-size: 0.75rem; font-weight: 700; letter-spacing: 0.1em; text-transform: uppercase;
    color: var(--accent); margin: 1.1rem 0 0.4rem;
}
.section-label.center { text-align: center; margin: 1.8rem 0 1rem; }
.result-card { border-radius: 18px; padding: 1.4rem 1.5rem; border: 1px solid var(--border); background: var(--panel); margin-top: 0.8rem; }
.result-card.spam { border-color: rgba(220,38,38,0.5); background: linear-gradient(135deg, rgba(220,38,38,0.10), rgba(220,38,38,0.02)); }
.result-card.warn { border-color: rgba(217,119,6,0.5); background: linear-gradient(135deg, rgba(217,119,6,0.12), rgba(217,119,6,0.02)); }
.result-card.ok { border-color: rgba(22,163,74,0.5); background: linear-gradient(135deg, rgba(22,163,74,0.10), rgba(22,163,74,0.02)); }
.verdict { font-size: 1.7rem; font-weight: 800; letter-spacing: -0.02em; }
.verdict.spam { color: #b91c1c; } .verdict.warn { color: #b45309; } .verdict.ok { color: #15803d; }
.verdict-sub { color: var(--text-soft); font-size: 0.95rem; margin-top: 0.2rem; }
.bar { height: 10px; border-radius: 999px; background: rgba(124,58,237,0.12); overflow: hidden; margin-top: 0.9rem; }
.bar > div { height: 100%; border-radius: 999px; }
.bar-spam { background: linear-gradient(90deg, #f59e0b, #ef4444); }
.bar-warn { background: linear-gradient(90deg, #a855f7, #f59e0b); }
.bar-ok { background: linear-gradient(90deg, #7c3aed, #22c55e); }
.flag { display: flex; gap: 0.6rem; align-items: flex-start; padding: 0.65rem 0.9rem; border-radius: 12px;
        background: var(--panel); border: 1px solid var(--border); margin-bottom: 0.5rem; font-size: 0.93rem; color: var(--text-soft); }
.flag b { color: var(--text); }
.source-note { font-size: 0.78rem; color: var(--muted); margin-top: 0.7rem; }

.app-footer { margin-top: 3rem; padding-top: 1rem; text-align: center; font-size: 0.78rem; color: var(--muted); border-top: 1px solid var(--border); }
@media (max-width: 768px) {
    .block-container { padding: 1rem 1rem 3rem; }
    .landing-title { font-size: 2.4rem; } .landing-names { font-size: 1.5rem; }
    .nav-desc { min-height: 0; }
}
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

NAMES_HTML = f'<span class="n1">{NAME_1}</span><span class="amp">&amp;</span><span class="n2">{NAME_2}</span>'

# ==================================================
# ANALYSIS LOGIC
# ==================================================

SAMPLES = {
    "Prize scam": (
        "Subject: CONGRATULATIONS!!! You have WON $1,000,000\n\n"
        "Dear lucky winner, you have been selected in our GLOBAL LOTTERY. "
        "Click here http://bit.ly/claim-prize-now to CLAIM your FREE cash prize immediately. "
        "This is URGENT - offer expires in 24 hours! Send your bank details and password to verify your account."
    ),
    "Phishing alert": (
        "Subject: Action required: your account has been suspended\n\n"
        "We noticed unusual activity. Verify your account within 12 hours or it will be permanently locked: "
        "http://secure-login.account-verify.example.net/update . Confirm your password and card number to restore access."
    ),
    "Work email": (
        "Subject: Project meeting notes\n\n"
        "Hi team, thanks for joining today's sync. Attached are the notes and action items. "
        "Priya will share the updated timeline by Thursday, and we will review the budget on Monday. "
        "Let me know if I missed anything. Regards, Arjun"
    ),
    "Friendly note": (
        "Subject: Lunch this weekend?\n\n"
        "Hey! It was great catching up last week. Are you free for lunch on Saturday? "
        "There's a new cafe near the park I've been wanting to try. Let me know what works for you."
    ),
}

SPAM_WORDS = ["winner", "won", "free", "prize", "lottery", "cash", "claim", "congratulations", "offer expires",
              "act now", "limited time", "100%", "guaranteed", "cheap", "viagra", "credit", "loan", "bonus"]
URGENCY_WORDS = ["urgent", "immediately", "within 24 hours", "expires", "final notice", "act now", "suspended", "locked"]
SENSITIVE_WORDS = ["password", "bank details", "card number", "verify your account", "ssn", "social security", "otp", "pin"]
SHORTENERS = ["bit.ly", "tinyurl", "t.co/", "goo.gl", "ow.ly", "is.gd", "cutt.ly"]


def extract_features(text: str) -> dict:
    low = text.lower()
    letters = [c for c in text if c.isalpha()]
    caps = sum(1 for c in letters if c.isupper()) / len(letters) if letters else 0.0
    urls = re.findall(r"https?://\S+|www\.\S+", text, flags=re.I)
    return {
        "words": len(text.split()),
        "links": len(urls),
        "exclaims": text.count("!"),
        "caps": caps,
        "money": len(re.findall(r"[$€£₹]\s?\d|\d+\s?(?:usd|dollars|rupees)", low)),
        "spam_hits": [w for w in SPAM_WORDS if w in low],
        "urgency_hits": [w for w in URGENCY_WORDS if w in low],
        "sensitive_hits": [w for w in SENSITIVE_WORDS if w in low],
        "shortener": any(s in low for s in SHORTENERS),
    }


def build_flags(f: dict) -> list[tuple[str, str, str]]:
    flags = []
    if f["spam_hits"]:
        flags.append(("🎯", "Spam-style wording", "Found: " + ", ".join(f["spam_hits"][:6])))
    if f["urgency_hits"]:
        flags.append(("⏰", "Pressure / urgency", "Found: " + ", ".join(f["urgency_hits"][:5])))
    if f["sensitive_hits"]:
        flags.append(("🔑", "Asks for sensitive information", "Found: " + ", ".join(f["sensitive_hits"][:5])))
    if f["shortener"]:
        flags.append(("🔗", "Shortened link", "Link shorteners hide the real destination."))
    elif f["links"] >= 3:
        flags.append(("🔗", "Many links", f"{f['links']} links in one message."))
    if f["money"]:
        flags.append(("💰", "Money amounts mentioned", f"{f['money']} currency reference(s)."))
    if f["caps"] > 0.30 and f["words"] > 8:
        flags.append(("🔠", "Excessive capital letters", f"{f['caps']:.0%} of letters are uppercase."))
    if f["exclaims"] >= 3:
        flags.append(("❗", "Heavy exclamation marks", f"{f['exclaims']} exclamation marks."))
    return flags


def heuristic_score(f: dict) -> float:
    score = (
        0.12 * min(len(f["spam_hits"]), 4)
        + 0.10 * min(len(f["urgency_hits"]), 3)
        + 0.18 * min(len(f["sensitive_hits"]), 2)
        + 0.15 * f["shortener"]
        + 0.04 * min(f["links"], 3)
        + 0.06 * min(f["money"], 2)
        + 0.15 * (f["caps"] > 0.30)
        + 0.04 * min(f["exclaims"], 3)
    )
    return max(0.02, min(0.98, score))


def predict_email(text: str, f: dict) -> tuple[float, str]:
    """Return (spam_probability, source).

    Tries your trained model first (scikit-learn style `predict_proba`).
    If your model object exposes a different interface, adapt the lines inside the try block.
    Falls back to a transparent rule-based score so the page always works.
    """
    model, _ = get_model_bundle()
    if model is not None:
        for obj in (model, getattr(model, "pipeline", None), getattr(model, "model", None)):
            if obj is not None and hasattr(obj, "predict_proba"):
                try:
                    proba = obj.predict_proba([text])[0]
                    classes = list(getattr(obj, "classes_", [0, 1]))
                    idx = next((i for i, c in enumerate(classes) if str(c).lower() in ("spam", "1", "true")), len(proba) - 1)
                    return float(proba[idx]), f"Trained model: {model.display_name} v{model.version}"
                except Exception:
                    continue
    return heuristic_score(f), "Rule-based fallback (trained model not connected to this page)"


def parse_uploaded_email(name: str, data: bytes) -> str:
    if name.lower().endswith(".eml"):
        msg = message_from_bytes(data, policy=policy.default)
        subject = msg.get("subject", "") or ""
        body_part = msg.get_body(preferencelist=("plain", "html"))
        body = body_part.get_content() if body_part else ""
        if body_part is not None and body_part.get_content_type() == "text/html":
            body = re.sub(r"<[^>]+>", " ", body)
        body = re.sub(r"\s+", " ", body).strip()
        return f"Subject: {subject}\n\n{body}"
    return data.decode("utf-8", errors="ignore")


def load_sample(key: str) -> None:
    st.session_state.email_text = SAMPLES[key]
    st.session_state.result = None


def clear_all() -> None:
    st.session_state.email_text = ""
    st.session_state.result = None


# ==================================================
# PAGES
# ==================================================

def home_page() -> None:
    model, _ = get_model_bundle()
    status = "● Model online" if model is not None else "● Model offline"
    st.markdown(
        f"""
        <div class="landing">
            <span class="landing-badge">{status}</span>
            <div class="landing-title">{APP_NAME}</div>
            <div class="landing-names">{NAMES_HTML}</div>
            <div class="landing-sub">
                An intelligent email spam detector built with machine learning.
                Paste or upload an email and get an instant verdict with the reasons behind it.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Primary call-to-action
    _, mid, _ = st.columns([1.2, 1, 1.2])
    with mid:
        with st.container(key="cta"):
            st.page_link(analyzer_pg, label="Analyze an email", icon=":material/mail:", use_container_width=True)

    # Navigation cards: one per page, each with its own button
    st.markdown('<div class="section-label center">Explore MailGuard</div>', unsafe_allow_html=True)
    nav_items = [
        ("✉️", "Email Analyzer", "Paste, upload or try a sample email and get an instant spam verdict.", analyzer_pg, "Open analyzer", ":material/arrow_forward:"),
        ("📈", "Model Evaluation", "Review accuracy, precision, recall and the confusion matrix.", evaluation_pg, "View results", ":material/arrow_forward:"),
        ("📡", "Monitoring", "Track live predictions, volumes and model health over time.", monitoring_pg, "Open dashboard", ":material/arrow_forward:"),
        ("🧠", "Model Information", "Learn how the model was trained, its data and its limits.", model_info_pg, "Read details", ":material/arrow_forward:"),
    ]
    cols = st.columns(4, gap="medium")
    for i, (col, (icon, title, desc, page, label, ico)) in enumerate(zip(cols, nav_items)):
        with col:
            with st.container(key=f"navcard_{i}"):
                st.markdown(
                    f'<div class="nav-icon">{icon}</div>'
                    f'<div class="nav-title">{title}</div>'
                    f'<div class="nav-desc">{desc}</div>',
                    unsafe_allow_html=True,
                )
                st.page_link(page, label=label, icon=ico, use_container_width=True)

    st.markdown('<div class="section-label center">Why MailGuard</div>', unsafe_allow_html=True)
    cols = st.columns(3, gap="medium")
    feats = [
        ("⚡", "Instant analysis", "Get a spam or legitimate verdict with a confidence score in seconds."),
        ("🔒", "Private by design", "Emails are processed in memory and are never stored or logged."),
        ("📊", "Transparent model", "Review accuracy, evaluation results and live monitoring on their own pages."),
    ]
    for col, (icon, title, desc) in zip(cols, feats):
        with col:
            st.markdown(
                f'<div class="feature"><div class="icon">{icon}</div><div class="ft">{title}</div><div class="fd">{desc}</div></div>',
                unsafe_allow_html=True,
            )


def analyzer_page() -> None:
    st.session_state.setdefault("email_text", "")
    st.session_state.setdefault("result", None)

    st.markdown(
        '<div class="page-head"><div class="t">Email Analyzer</div>'
        '<div class="s">Check whether an email looks like spam. Paste the text, upload a file, or try a sample.</div></div>',
        unsafe_allow_html=True,
    )

    left, right = st.columns([3, 2], gap="large")

    with right:
        st.markdown('<div class="section-label">Try a sample</div>', unsafe_allow_html=True)
        for key in SAMPLES:
            st.button(key, key=f"s_{key}", on_click=load_sample, args=(key,), use_container_width=True)

        st.markdown('<div class="section-label">Upload an email</div>', unsafe_allow_html=True)
        up = st.file_uploader("Upload .eml or .txt", type=["eml", "txt"], label_visibility="collapsed")
        if up is not None and st.session_state.get("_last_upload") != (up.name, up.size):
            st.session_state._last_upload = (up.name, up.size)
            st.session_state.email_text = parse_uploaded_email(up.name, up.getvalue())
            st.session_state.result = None
            st.toast(f"Loaded {up.name}", icon=":material/check_circle:")

    with left:
        st.markdown('<div class="section-label">Email content</div>', unsafe_allow_html=True)
        st.text_area(
            "Email text",
            key="email_text",
            height=300,
            placeholder="Paste the full email here, including the subject line...",
            label_visibility="collapsed",
        )
        b1, b2, _ = st.columns([2, 1, 3])
        analyze = b1.button("Analyze email", type="primary", icon=":material/search:", use_container_width=True)
        b2.button("Clear", on_click=clear_all, use_container_width=True)

    if analyze:
        text = st.session_state.email_text.strip()
        if len(text) < 15:
            st.warning("Please enter at least a few words of email text.", icon=":material/warning:")
        else:
            with st.spinner("Analyzing..."):
                feats = extract_features(text)
                prob, source = predict_email(text, feats)
                st.session_state.result = {"prob": prob, "source": source, "feats": feats, "flags": build_flags(feats)}

    res = st.session_state.result
    if res:
        prob, feats = res["prob"], res["feats"]
        if prob >= 0.70:
            cls, title, sub = "spam", "🚫 Likely spam", "This email shows strong spam or phishing characteristics."
        elif prob >= 0.40:
            cls, title, sub = "warn", "⚠️ Suspicious", "Some warning signs were found. Treat links and attachments with care."
        else:
            cls, title, sub = "ok", "✅ Looks legitimate", "No strong spam signals were detected."
        st.markdown(
            f"""
            <div class="result-card {cls}">
                <div class="verdict {cls}">{title}</div>
                <div class="verdict-sub">{sub}</div>
                <div class="bar"><div class="bar-{cls}" style="width:{prob*100:.0f}%"></div></div>
                <div class="verdict-sub" style="margin-top:0.5rem">Spam probability: <b>{prob:.0%}</b></div>
                <div class="source-note">{html.escape(res['source'])}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Words", feats["words"])
        m2.metric("Links", feats["links"])
        m3.metric("Exclamation marks", feats["exclaims"])
        m4.metric("Uppercase letters", f"{feats['caps']:.0%}")

        st.markdown('<div class="section-label">Why this result</div>', unsafe_allow_html=True)
        if res["flags"]:
            for icon, head, detail in res["flags"]:
                st.markdown(
                    f'<div class="flag"><div>{icon}</div><div><b>{html.escape(head)}</b><br>{html.escape(detail)}</div></div>',
                    unsafe_allow_html=True,
                )
        else:
            st.markdown('<div class="flag"><div>👍</div><div><b>No warning signs</b><br>Wording, links and formatting look normal.</div></div>', unsafe_allow_html=True)
        st.caption("Automated analysis can make mistakes. Never share passwords or card details by email.")


# ==================================================
# NAVIGATION
# ==================================================

home_pg = st.Page(home_page, title="Home", icon=":material/home:", url_path="home", default=True)
analyzer_pg = st.Page(analyzer_page, title="Email Analyzer", icon=":material/mail:", url_path="analyzer")
evaluation_pg = st.Page("views/evaluation.py", title="Model Evaluation", icon=":material/analytics:")
monitoring_pg = st.Page("views/monitoring.py", title="Monitoring", icon=":material/monitor_heart:")
model_info_pg = st.Page("views/model_info.py", title="Model Information", icon=":material/info:")

pages = [home_pg, analyzer_pg, evaluation_pg, monitoring_pg, model_info_pg]

get_service()  # warm up model + metrics store once per process
model, model_error = get_model_bundle()

if model is not None:
    side_status = (
        '<div class="row"><span class="dot dot-ok"></span>Model online</div>'
        f'<div class="meta">{model.display_name} · v{model.version}</div>'
    )
else:
    side_status = (
        '<div class="row"><span class="dot dot-err"></span>Model unavailable</div>'
        '<div class="meta">See Model Information for details.</div>'
    )

with st.sidebar:
    st.markdown(
        f"""
        <div class="brand">
            <div class="brand-logo">🛡️</div>
            <div>
                <div class="brand-name">{APP_NAME}</div>
                <div class="credits credits-sm">{NAMES_HTML}</div>
                <div class="brand-tag">{APP_TAGLINE}</div>
            </div>
        </div>
        <div class="side-card">{side_status}</div>
        <div class="privacy-note">
            🔒 Educational demo trained on the public SpamAssassin corpus.
            Emails you analyse are processed in memory and never stored or logged.
        </div>
        """,
        unsafe_allow_html=True,
    )

current_pg = st.navigation(pages)

# The sidebar link list is hidden (see CSS); inner pages get a slim top bar instead,
# so there is always a way back to Home and between pages.
if current_pg.title != "Home":
    with st.container(key="topbar"):
        bar_cols = st.columns(len(pages), gap="small")
        for bar_col, pg in zip(bar_cols, pages):
            bar_col.page_link(pg, use_container_width=True)

current_pg.run()

st.markdown(
    f'<div class="app-footer">{APP_NAME} · Built with Streamlit &amp; scikit-learn · For educational use only</div>',
    unsafe_allow_html=True,
)