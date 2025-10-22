# Download.py
from Login import apply_sidebar_theme
import streamlit as st
import pandas as pd
from io import BytesIO
import mysql.connector

def get_connection():
    return mysql.connector.connect(
        host="145.223.18.115",
        port=3306,
        user="admin",
        password="@Cittamall13",         
        database="gamifiedqc" 
    )

def get_avatar_names():
    """
    Returns {username: avatar_name} mapping
    """
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT username, avatar FROM labs_users")
    rows = cursor.fetchall()
    conn.close()

    avatar_map = {}
    for row in rows:
        avatar_map[row['username']] = row['avatar'] or row['username']
    return avatar_map

def download_theme():
    st.markdown("""<style>
        /* Import MLBB-style fonts */
    @import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@400;600;700&family=Orbitron:wght@400;700;900&family=Rajdhani:wght@300;400;600;700&display=swap');

    /* MLBB Color Palette */
    :root {
        --mlbb-primary: #ff4d8d;
        --mlbb-secondary: #4a00e0;
        --mlbb-accent: #ff9a8b;
        --mlbb-gold: #ffd700;
        --mlbb-silver: #c0c0c0;
        --mlbb-bronze: #cd7f32;
        --mlbb-dark: #0a0f1e;
        --mlbb-darker: #070a14;
        --mlbb-light: #f8f9ff;
        --mlbb-gradient: linear-gradient(135deg, var(--mlbb-secondary) 0%, var(--mlbb-primary) 100%);
        --mlbb-glow: 0 0 20px rgba(255, 77, 141, 0.6);
        --mlbb-border-radius: 16px;
        --mlbb-transition: all 0.4s cubic-bezier(0.25, 0.8, 0.25, 1);
        --mlbb-card-bg: rgba(15, 20, 40, 0.85);
        --mlbb-card-border: 1px solid rgba(255, 255, 255, 0.15);
    }

    /* Global Styles */
    .stApp {
        background: linear-gradient(135deg, var(--mlbb-darker) 0%, var(--mlbb-dark) 50%, var(--mlbb-darker) 100%);
        background-attachment: fixed;
        font-family: 'Rajdhani', sans-serif;
        color: var(--mlbb-light);
    }

    .stApp::before {
        content: '';
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: 
            radial-gradient(circle at 20% 30%, rgba(255, 77, 141, 0.1) 0%, transparent 50%),
            radial-gradient(circle at 80% 70%, rgba(74, 0, 224, 0.1) 0%, transparent 50%),
            radial-gradient(circle at 50% 50%, rgba(255, 154, 139, 0.05) 0%, transparent 50%);
        pointer-events: none;
        z-index: -1;
    }

    /* Header Styling */
    .stApp > header {
        background: var(--mlbb-card-bg);
        backdrop-filter: blur(20px);
        border-bottom: var(--mlbb-card-border);
        box-shadow: 0 4px 30px rgba(0, 0, 0, 0.3);
    }

    /* Main Title */
    h1 {
        font-family: 'Cinzel', serif !important;
        background: var(--mlbb-gradient) !important;
        -webkit-background-clip: text !important;
        -webkit-text-fill-color: transparent !important;
        background-clip: text !important;
        text-align: center !important;
        font-size: 3.5rem !important;
        font-weight: 700 !important;
        text-shadow: 0 0 30px rgba(255, 77, 141, 0.5) !important;
        margin-bottom: 2rem !important;
        letter-spacing: 2px !important;
    }

    /* Subheaders */
    h2, h3 {
        font-family: 'Orbitron', monospace !important;
        color: var(--mlbb-accent) !important;
        text-shadow: 0 0 15px rgba(255, 154, 139, 0.4) !important;
        font-weight: 600 !important;
        margin: 1.5rem 0 1rem 0 !important;
    }

    /* Tab Styling */
    .stTabs [data-baseweb="tab-list"] {
        background: var(--mlbb-card-bg) !important;
        border-radius: var(--mlbb-border-radius) !important;
        padding: 0.5rem !important;
        margin-bottom: 2rem !important;
        backdrop-filter: blur(20px) !important;
        border: var(--mlbb-card-border) !important;
    }

    .stTabs [data-baseweb="tab"] {
        background: transparent !important;
        color: var(--mlbb-light) !important;
        font-family: 'Orbitron', monospace !important;
        font-weight: 600 !important;
        border-radius: 12px !important;
        margin: 0 0.25rem !important;
        padding: 0.75rem 1.5rem !important;
        transition: var(--mlbb-transition) !important;
        border: 1px solid transparent !important;
    }

    .stTabs [data-baseweb="tab"]:hover {
        background: rgba(255, 77, 141, 0.1) !important;
        border: 1px solid rgba(255, 77, 141, 0.3) !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 25px rgba(255, 77, 141, 0.2) !important;
    }

    .stTabs [aria-selected="true"] {
        background: var(--mlbb-gradient) !important;
        color: white !important;
        box-shadow: var(--mlbb-glow) !important;
        transform: translateY(-2px) !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
    }

    /* Card/Container Styling */
    .stContainer {
        background: var(--mlbb-card-bg) !important;
        border-radius: var(--mlbb-border-radius) !important;
        border: var(--mlbb-card-border) !important;
        backdrop-filter: blur(20px) !important;
        padding: 2rem !important;
        margin: 1rem 0 !important;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3) !important;
        transition: var(--mlbb-transition) !important;
    }

    .stContainer:hover {
        transform: translateY(-4px) !important;
        box-shadow: 0 12px 40px rgba(255, 77, 141, 0.15) !important;
        border: 1px solid rgba(255, 77, 141, 0.3) !important;
    }

    /* Button Styling */
    .stButton > button {
        background: var(--mlbb-gradient) !important;
        color: white !important;
        border: none !important;
        border-radius: var(--mlbb-border-radius) !important;
        font-family: 'Orbitron', monospace !important;
        font-weight: 700 !important;
        font-size: 1rem !important;
        padding: 0.75rem 2rem !important;
        transition: var(--mlbb-transition) !important;
        text-transform: uppercase !important;
        letter-spacing: 1px !important;
        box-shadow: 0 4px 20px rgba(255, 77, 141, 0.3) !important;
        position: relative !important;
        overflow: hidden !important;
    }

    .stButton > button::before {
        content: '' !important;
        position: absolute !important;
        top: 0 !important;
        left: -100% !important;
        width: 100% !important;
        height: 100% !important;
        background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent) !important;
        transition: left 0.5s ease !important;
    }

    .stButton > button:hover {
        transform: translateY(-3px) scale(1.05) !important;
        box-shadow: var(--mlbb-glow), 0 8px 30px rgba(0, 0, 0, 0.3) !important;
    }

    .stButton > button:hover::before {
        left: 100% !important;
    }

    .stButton > button:active {
        transform: translateY(-1px) scale(1.02) !important;
    }

    /* Download Button Special Styling */
    .stDownloadButton > button {
        background: linear-gradient(135deg, var(--mlbb-gold) 0%, #ffaa00 100%) !important;
        color: var(--mlbb-dark) !important;
        box-shadow: 0 4px 20px rgba(255, 215, 0, 0.4) !important;
    }

    .stDownloadButton > button:hover {
        box-shadow: 0 0 25px rgba(255, 215, 0, 0.8), 0 8px 30px rgba(0, 0, 0, 0.3) !important;
    }

    /* DataFrames Styling */
    .stDataFrame {
        background: var(--mlbb-card-bg) !important;
        border-radius: var(--mlbb-border-radius) !important;
        border: var(--mlbb-card-border) !important;
        backdrop-filter: blur(20px) !important;
        overflow: hidden !important;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3) !important;
    }

    .stDataFrame table {
        background: transparent !important;
        color: var(--mlbb-light) !important;
        font-family: 'Rajdhani', sans-serif !important;
    }

    .stDataFrame thead tr {
        background: var(--mlbb-gradient) !important;
        color: white !important;
        font-weight: 700 !important;
        font-family: 'Orbitron', monospace !important;
        text-transform: uppercase !important;
        letter-spacing: 1px !important;
    }

    .stDataFrame tbody tr:nth-child(odd) {
        background: rgba(255, 77, 141, 0.05) !important;
    }

    .stDataFrame tbody tr:nth-child(even) {
        background: rgba(74, 0, 224, 0.05) !important;
    }

    .stDataFrame tbody tr:hover {
        background: rgba(255, 154, 139, 0.1) !important;
        transform: scale(1.01) !important;
        transition: var(--mlbb-transition) !important;
    }

    /* Alert/Message Styling */
    .stAlert {
        border-radius: var(--mlbb-border-radius) !important;
        border: none !important;
        backdrop-filter: blur(20px) !important;
        font-family: 'Rajdhani', sans-serif !important;
        font-weight: 600 !important;
    }

    .stSuccess {
        background: linear-gradient(135deg, rgba(0, 255, 127, 0.2) 0%, rgba(0, 200, 100, 0.2) 100%) !important;
        border: 1px solid rgba(0, 255, 127, 0.3) !important;
        color: #00ff7f !important;
    }

    .stError {
        background: linear-gradient(135deg, rgba(255, 69, 58, 0.2) 0%, rgba(255, 45, 85, 0.2) 100%) !important;
        border: 1px solid rgba(255, 69, 58, 0.3) !important;
        color: #ff6b6b !important;
    }

    .stWarning {
        background: linear-gradient(135deg, rgba(255, 214, 0, 0.2) 0%, rgba(255, 193, 7, 0.2) 100%) !important;
        border: 1px solid rgba(255, 214, 0, 0.3) !important;
        color: var(--mlbb-gold) !important;
    }

    .stInfo {
        background: linear-gradient(135deg, rgba(74, 144, 226, 0.2) 0%, rgba(74, 0, 224, 0.2) 100%) !important;
        border: 1px solid rgba(74, 144, 226, 0.3) !important;
        color: #4a90e2 !important;
    }

    /* Input Fields */
    .stTextInput input, .stSelectbox select, .stNumberInput input {
        background: var(--mlbb-card-bg) !important;
        border: var(--mlbb-card-border) !important;
        border-radius: 12px !important;
        color: var(--mlbb-light) !important;
        font-family: 'Rajdhani', sans-serif !important;
        font-weight: 500 !important;
        padding: 0.75rem 1rem !important;
        transition: var(--mlbb-transition) !important;
    }

    .stTextInput input:focus, .stSelectbox select:focus, .stNumberInput input:focus {
        border: 2px solid var(--mlbb-primary) !important;
        box-shadow: 0 0 15px rgba(255, 77, 141, 0.3) !important;
        outline: none !important;
    }

    /* Column Layout Enhancement */
    .stColumn {
        padding: 0 1rem !important;
    }

    /* Metric Styling */
    .metric-container {
        background: var(--mlbb-card-bg) !important;
        border-radius: var(--mlbb-border-radius) !important;
        border: var(--mlbb-card-border) !important;
        padding: 1.5rem !important;
        text-align: center !important;
        backdrop-filter: blur(20px) !important;
        transition: var(--mlbb-transition) !important;
    }

    .metric-container:hover {
        transform: translateY(-5px) scale(1.02) !important;
        box-shadow: 0 10px 30px rgba(255, 77, 141, 0.2) !important;
    }

    /* Footer Styling */
    .stApp > footer {
        background: var(--mlbb-card-bg) !important;
        backdrop-filter: blur(20px) !important;
        border-top: var(--mlbb-card-border) !important;
        padding: 1rem !important;
        margin-top: 3rem !important;
    }

    /* Scrollbar Styling */
    ::-webkit-scrollbar {
        width: 12px !important;
        height: 12px !important;
    }

    ::-webkit-scrollbar-track {
        background: var(--mlbb-darker) !important;
        border-radius: 8px !important;
    }

    ::-webkit-scrollbar-thumb {
        background: var(--mlbb-gradient) !important;
        border-radius: 8px !important;
        border: 2px solid var(--mlbb-darker) !important;
    }

    ::-webkit-scrollbar-thumb:hover {
        background: linear-gradient(135deg, var(--mlbb-primary) 0%, var(--mlbb-secondary) 50%, var(--mlbb-accent) 100%) !important;
    }

    /* Responsive Design */
    @media (max-width: 768px) {
        h1 {
            font-size: 2.5rem !important;
        }
        
        .stDataFrame {
            font-size: 12px !important;
        }
        
        .stButton > button {
            width: 100% !important;
            margin: 5px 0 !important;
            padding: 1rem !important;
        }
        
        .stColumn {
            padding: 0 0.5rem !important;
        }
        
        .stContainer {
            padding: 1rem !important;
        }
    }

    /* Loading Animations */
    @keyframes mlbbGlow {
        0% { box-shadow: 0 0 10px rgba(255, 77, 141, 0.4); }
        50% { box-shadow: 0 0 30px rgba(255, 77, 141, 0.8); }
        100% { box-shadow: 0 0 10px rgba(255, 77, 141, 0.4); }
    }

    @keyframes mlbbPulse {
        0% { transform: scale(1); }
        50% { transform: scale(1.05); }
        100% { transform: scale(1); }
    }

    .mlbb-loading {
        animation: mlbbGlow 2s ease-in-out infinite, mlbbPulse 2s ease-in-out infinite !important;
    }
                
    @media (max-width: 768px) {
            .stDataFrame {
                font-size: 12px;
            }
            .stButton > button {
                width: 100%;
                margin: 5px 0;
            }
            .stSelectbox, .stTextInput {
                width: 100% !important;
            }
        }    
    </style>""", unsafe_allow_html=True)

def run():
    st.set_page_config(page_title="LLKK - Lab Legend Kingdom Kvalis", layout="wide")
    download_theme()
    st.title("📥 Download Final Elo Table")
    apply_sidebar_theme()

    user_role = st.session_state.get("user_role", "lab")
    user_lab = st.session_state.get("logged_in_lab", "")
    
    avatar_map = get_avatar_names()
   
    try:
        conn = get_connection()
        
        if user_role == "admin":
            monthly_final_query = "SELECT * FROM monthly_final ORDER BY month DESC, lab_rank ASC"
            monthly_rankings_query = "SELECT * FROM monthly_rankings ORDER BY month DESC, parameter, level, ranking ASC"
        else:
            monthly_final_query = f"SELECT * FROM monthly_final WHERE lab = '{user_lab}' ORDER BY month DESC, lab_rank ASC"
            monthly_rankings_query = f"SELECT * FROM monthly_rankings WHERE lab = '{user_lab}' ORDER BY month DESC, parameter, level, ranking ASC"
        
        monthly_final_df = pd.read_sql(monthly_final_query, conn)
        monthly_rankings_df = pd.read_sql(monthly_rankings_query, conn)
        
        conn.close()
        
    except Exception as e:
        st.error(f"❌ Error fetching data from database: {e}")
        return

    # Replace lab names with avatar names for labs
    if user_role != "admin":
        pass
    else:
        if not monthly_final_df.empty:
            monthly_final_df['avatar_name'] = monthly_final_df['lab'].map(lambda x: avatar_map.get(x, "Unknown"))
        
        if not monthly_rankings_df.empty:
            monthly_rankings_df['avatar_name'] = monthly_rankings_df['lab'].map(lambda x: avatar_map.get(x, "Unknown"))

    tab1, tab2 = st.tabs(["📊 Monthly Final Rankings", "📈 Detailed Monthly Rankings"])

    with tab1:
        st.subheader("Monthly Final Rankings")
        if monthly_final_df.empty:
            st.warning("No monthly final data available. Please run the simulation first.")
        else:
            # For admin, show both lab and avatar name
            if user_role == "admin":
                cols = monthly_final_df.columns.tolist()
                if 'avatar_name' in cols:
                    cols.remove('avatar_name')
                    cols.insert(cols.index('lab') + 1, 'avatar_name')
                    monthly_final_df = monthly_final_df[cols]
            
            st.dataframe(monthly_final_df, use_container_width=True,hide_index=True)
            
            # Excel for monthly_final
            def to_excel_monthly_final(df):
                output = BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    df.to_excel(writer, index=False, sheet_name='Monthly_Final_Rankings')
                return output.getvalue()

            excel_data_monthly_final = to_excel_monthly_final(monthly_final_df)
            csv_data_monthly_final = monthly_final_df.to_csv(index=False).encode("utf-8")

            col1, col2, col3 = st.columns([1,1,2])
            with col2:
                st.download_button(
                    "📥 Download Monthly Final Excel", 
                    data=excel_data_monthly_final, 
                    file_name="LLKK_Monthly_Final_Elo.xlsx",
                    key="monthly_final_excel"
                )
            with col3:
                st.download_button(
                    "📑 Download Monthly Final CSV", 
                    data=csv_data_monthly_final, 
                    file_name="LLKK_Monthly_Final_Elo.csv", 
                    mime="text/csv",
                    key="monthly_final_csv"
                )

    with tab2:  
        st.subheader("Detailed Monthly Elo")
        if monthly_rankings_df.empty:
            st.warning("No monthly rankings data available. Please run the simulation first.")
        else:
            if user_role == "admin":
          
                cols = monthly_rankings_df.columns.tolist()
                if 'avatar_name' in cols:
                    cols.remove('avatar_name')
                    cols.insert(cols.index('lab') + 1, 'avatar_name')
                    monthly_rankings_df = monthly_rankings_df[cols]
            
            st.dataframe(monthly_rankings_df, use_container_width=True, hide_index=True)
          
            def to_excel_monthly_rankings(df):
                output = BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    df.to_excel(writer, index=False, sheet_name='Monthly_Detailed_Rankings')
                return output.getvalue()

            excel_data_monthly_rankings = to_excel_monthly_rankings(monthly_rankings_df)
            csv_data_monthly_rankings = monthly_rankings_df.to_csv(index=False).encode("utf-8")

            # Download buttons for monthly_rankings
            col1, col2, col3 = st.columns([1,1,2])
            with col2:
                st.download_button(
                    "📥 Download Detailed Elo Excel", 
                    data=excel_data_monthly_rankings, 
                    file_name="LLKK_Detailed_Monthly_Elo.xlsx",
                    key="monthly_elo_excel"
                )
            with col3:
                st.download_button(
                    "🧾 Download Detailed Elo CSV", 
                    data=csv_data_monthly_rankings, 
                    file_name="LLKK_Detailed_Monthly_Elo.csv", 
                    mime="text/csv",
                    key="monthly_elo_csv"
                )

    if user_role == "admin":
        st.success(f"🛡️ Admin View: You can see all data")
    else:
        st.info(f"🗃️ Lab View: You can view only your data")

    # Footer
    st.markdown("<hr style='margin-top: 2rem; margin-bottom: 1rem;'>"
                "<div style='text-align: center; color: gray;'>"
                "© 2025 Lab Legend Kingdom Kvalis — Powered by MEQARE"
                "</div>", unsafe_allow_html=True)

if __name__ == "__main__":
    run()