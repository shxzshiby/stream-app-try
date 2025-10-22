import streamlit as st
from Login import apply_sidebar_theme

def run():
   st.set_page_config(page_title="Help", layout="wide", page_icon="❓")
   st.title("❓ How to Use LLKK")
   apply_sidebar_theme()

   st.markdown("""
   ### Step-by-Step Guide

   1. **Go to the Home page**
      - Upload your monthly QC Excel file.
      - Make sure your columns include: Lab, Parameter, Level, CV.

   2. **View Battle Log**
      - Shows detailed matchups between labs for each parameter.
      - Uses CV values to determine winners.

   3. **Check Champion**
      - See who won the month based on highest final Elo rating.
      - Bonus/penalty logic is automatically applied.

   4. **Download Results**
      - Export the final Elo ranking table in Excel format.

   5. **Read About Page**
      - Understand the philosophy and structure behind LLKK.

   ### Notes
   - Missing data will be penalized by -10 points per field.
   - Only valid data contributes to ranking.
   - Streamlit session resets on page reload. Re-upload if needed.

   Still need help? Contact MEQARE support.
   """, unsafe_allow_html=True)

   st.markdown("""
      <style>
      /* App background */
      .stApp {
         background: linear-gradient(135deg, #0f172a, #1e293b, #0f172a);
         font-family: 'Poppins', sans-serif;
         color: #e2e8f0;
      }

      /* Page Title (❓ How to Use LLKK) */
      .stMarkdown h1 {
         text-align: center;
         font-size: 2.6rem !important;
         font-weight: bold;
         background: linear-gradient(90deg, #38bdf8, #2563eb);
         -webkit-background-clip: text;
         -webkit-text-fill-color: transparent;
         text-shadow: 0px 0px 12px rgba(56, 189, 248, 0.6);
         margin-bottom: 2rem;
      }

      /* Section headers (### Step-by-Step Guide, ### Notes) */
      .stMarkdown h3 {
         font-size: 1.4rem !important;
         color: #facc15 !important;
         text-shadow: 0px 0px 6px rgba(250, 204, 21, 0.7);
         border-left: 4px solid #facc15;
         padding-left: 10px;
         margin-top: 1.5rem;
         margin-bottom: 1rem;
      }

      /* List items */
      .stMarkdown ul, .stMarkdown ol {
         margin-left: 1.2rem;
         font-size: 1rem !important;
         line-height: 1.7;
      }

      .stMarkdown li {
         margin-bottom: 0.8rem;
      }

      /* Bold highlights */
      .stMarkdown strong {
         color: #38bdf8;
         text-shadow: 0px 0px 5px rgba(56, 189, 248, 0.6);
      }

      /* Footer */
      div[style*="text-align: center; color: gray;"] {
         font-size: 0.9rem !important;
         color: #94a3b8 !important;
         letter-spacing: 0.5px;
      }

      /* Responsive for mobile */
      @media (max-width: 768px) {
         .stMarkdown h1 {
            font-size: 2rem !important;
         }
         .stMarkdown h3 {
            font-size: 1.2rem !important;
         }
         .stMarkdown p, .stMarkdown li {
            font-size: 0.9rem !important;
         }
         .stButton > button {
            width: 100%;
            margin: 5px 0;
         }
         .stSelectbox, .stTextInput {
            width: 100% !important;
         }
      }
      </style>
      """, unsafe_allow_html=True)

   
if __name__ == "__main__":
    run()