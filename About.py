import streamlit as st
from Login import apply_sidebar_theme

def run():
    st.set_page_config(page_title="About LLKK", layout="wide", page_icon="ℹ️")
    st.title("ℹ️ About Lab Legend Kingdom Kvalis")
    apply_sidebar_theme()

    st.markdown("""
    ## What is LLKK?

    **Lab Legend Kingdom Kvalis (LLKK)** is a gamified Quality Control (QC) evaluation platform developed under the MEQARE initiative.
    It uses a modified **Elo rating system** to rank laboratories based on their analytical performance.

    Each lab submits monthly QC results, which are then compared in simulated 'battles' where lower Coefficient of Variation (CV) wins.

    ## Features:
    - Monthly CV-based battles between labs
    - Elo-based ranking system with bonuses and penalties
    - Intuitive dashboards, champion highlights, and exportable results

    ## Purpose:
    To promote continuous improvement, transparency, and engagement in laboratory performance monitoring — turning QC into a competitive and rewarding journey.

    ## Developed by:
    MEQARE, Malaysia's EQA innovation hub.
    """, unsafe_allow_html=True)

    st.markdown("<hr style='margin-top: 2rem; margin-bottom: 1rem;'>"
                "<div style='text-align: center; color: gray;'>"
                "© 2025 Lab Legend Kingdom Kvalis — Powered by MEQARE"
                "</div>", unsafe_allow_html=True)

    st.markdown("""
        <style>
        /* Whole app background */
        .stApp {
            background: linear-gradient(135deg, #0f172a, #1e293b, #0f172a);
            font-family: 'Poppins', sans-serif;
            color: #f1f5f9;
        }

        /* Title (About LLKK) */
        .stMarkdown h1 {
            text-align: center;
            font-size: 2.8rem !important;
            font-weight: bold;
            background: linear-gradient(90deg, #ffd700, #facc15, #fbbf24);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            text-shadow: 0px 0px 12px rgba(255, 215, 0, 0.6);
            margin-bottom: 2rem;
        }

        /* Section headers (## What is LLKK, Features, Purpose...) */
        .stMarkdown h2 {
            font-size: 1.5rem !important;
            color: #38bdf8 !important;
            text-shadow: 0px 0px 8px rgba(56, 189, 248, 0.6);
            border-left: 4px solid #38bdf8;
            padding-left: 10px;
            margin-top: 2rem;
            margin-bottom: 1rem;
        }

        /* Paragraphs */
        .stMarkdown p {
            font-size: 1rem !important;
            line-height: 1.7;
            color: #e2e8f0;
        }

        /* Highlighted bold words */
        .stMarkdown strong {
            color: #facc15;
            text-shadow: 0px 0px 6px rgba(250, 204, 21, 0.7);
        }

        /* Footer style */
        div[style*="text-align: center; color: gray;"] {
            font-size: 0.9rem !important;
            color: #94a3b8 !important;
            letter-spacing: 0.5px;
        }

        /* Mobile responsive */
        @media (max-width: 768px) {
            .stMarkdown p {
                font-size: 0.9rem !important;
            }
            .stMarkdown h1 {
                font-size: 2rem !important;
            }
            .stButton > button {
                width: 100%;
            }
        }
        </style>
        """, unsafe_allow_html=True)


if __name__ == "__main__":
    run()