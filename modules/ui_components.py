from __future__ import annotations

import html
from typing import Iterable

import pandas as pd
import streamlit as st


def inject_css() -> None:
    st.markdown(
        """
        <style>
        :root {
            --ink: #172026;
            --muted: #5b6673;
            --line: #d9dee5;
            --surface: #ffffff;
            --wash: #f6f7f9;
            --teal: #0f766e;
            --blue: #2563eb;
            --amber: #b7791f;
            --rose: #be123c;
        }
        .stApp {
            background: var(--wash);
            color: var(--ink);
        }
        .block-container {
            padding-top: 1.4rem;
            padding-bottom: 3rem;
            max-width: 1280px;
        }
        div[data-testid="stSidebar"] {
            border-right: 1px solid var(--line);
        }
        h1, h2, h3 {
            letter-spacing: 0;
        }
        .hero-band {
            background: var(--surface);
            border: 1px solid var(--line);
            border-left: 6px solid var(--teal);
            border-radius: 8px;
            padding: 1.35rem 1.45rem;
            margin-bottom: 1rem;
        }
        .hero-band h1 {
            margin: 0 0 .35rem 0;
            font-size: clamp(2rem, 4vw, 3.1rem);
            line-height: 1.05;
        }
        .hero-band p {
            margin: 0;
            color: var(--muted);
            font-size: 1.06rem;
        }
        .metric-card {
            background: var(--surface);
            border: 1px solid var(--line);
            border-radius: 8px;
            padding: .9rem .95rem;
            min-height: 112px;
            box-shadow: 0 8px 20px rgba(23, 32, 38, 0.045);
        }
        .metric-label {
            color: var(--muted);
            font-size: .78rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: .03em;
            margin-bottom: .35rem;
        }
        .metric-value {
            color: var(--ink);
            font-size: 1.55rem;
            font-weight: 800;
            line-height: 1.15;
            word-break: break-word;
        }
        .metric-caption {
            color: var(--muted);
            font-size: .82rem;
            margin-top: .35rem;
        }
        .insight-box {
            background: var(--surface);
            border: 1px solid var(--line);
            border-radius: 8px;
            padding: 1rem 1.1rem;
            margin: .65rem 0 1rem 0;
        }
        .insight-box.info { border-left: 5px solid var(--blue); }
        .insight-box.success { border-left: 5px solid var(--teal); }
        .insight-box.warning { border-left: 5px solid var(--amber); }
        .insight-box.risk { border-left: 5px solid var(--rose); }
        .insight-title {
            font-weight: 800;
            margin-bottom: .25rem;
        }
        .insight-body {
            color: var(--muted);
        }
        .small-muted {
            color: var(--muted);
            font-size: .9rem;
        }
        .section-kicker {
            color: var(--teal);
            font-size: .76rem;
            font-weight: 800;
            text-transform: uppercase;
            letter-spacing: .06em;
            margin-bottom: .1rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def page_header(title: str, subtitle: str | None = None, kicker: str | None = None) -> None:
    kicker_html = f"<div class='section-kicker'>{html.escape(kicker)}</div>" if kicker else ""
    subtitle_html = f"<p>{html.escape(subtitle)}</p>" if subtitle else ""
    st.markdown(
        f"""
        <div class="hero-band">
            {kicker_html}
            <h1>{html.escape(title)}</h1>
            {subtitle_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def metric_cards(items: Iterable[tuple[str, str, str | None]], columns: int = 4) -> None:
    items = list(items)
    for start in range(0, len(items), columns):
        cols = st.columns(columns)
        for col, item in zip(cols, items[start : start + columns]):
            label, value, caption = item
            with col:
                st.markdown(
                    f"""
                    <div class="metric-card">
                        <div class="metric-label">{html.escape(label)}</div>
                        <div class="metric-value">{html.escape(value)}</div>
                        <div class="metric-caption">{html.escape(caption or "")}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
        st.write("")


def insight_box(title: str, body: str, tone: str = "info") -> None:
    safe_tone = tone if tone in {"info", "success", "warning", "risk"} else "info"
    st.markdown(
        f"""
        <div class="insight-box {safe_tone}">
            <div class="insight-title">{html.escape(title)}</div>
            <div class="insight-body">{html.escape(body)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def section_title(title: str, caption: str | None = None) -> None:
    st.subheader(title)
    if caption:
        st.markdown(f"<div class='small-muted'>{html.escape(caption)}</div>", unsafe_allow_html=True)


def score_style(df: pd.DataFrame, score_column: str = "Automation Score"):
    if score_column not in df.columns:
        return df

    def color_score(value):
        if value >= 80:
            return "background-color: #dff3ea; color: #0f5132; font-weight: 700"
        if value >= 65:
            return "background-color: #fff4d6; color: #7a4b00; font-weight: 700"
        return "background-color: #fde2e7; color: #8a1230; font-weight: 700"

    return df.style.map(color_score, subset=[score_column])


def percent(value: float) -> str:
    return f"{value * 100:.0f}%"


def money(value: float) -> str:
    return f"${value:,.0f}"


def number(value: float | int, decimals: int = 0) -> str:
    return f"{value:,.{decimals}f}" if decimals else f"{value:,.0f}"
