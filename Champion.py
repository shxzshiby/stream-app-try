import streamlit as st
import pandas as pd
import altair as alt
import mysql.connector
import itertools
import numpy as np
from datetime import datetime, date
from Login import apply_sidebar_theme
import base64
import os
from pathlib import Path
import mimetypes

# EFLM Targets 
EFLM_TARGETS = {
    "Albumin": 2.1, "ALT": 6.0, "ALP": 3.98, "AST": 5.3, "Bilirubin (Total)": 8.6,
    "Cholesterol": 2.9, "TG": 4.98, "Creatinine": 3.4, "Glucose": 2.9,
    "HDL Cholesterol": 4.0, "CL": 0.83, "Potassium": 1.8, "Sodium": 0.9,
    "Protein (Total)": 2.0, "Urea": 3.9, "Uric Acid": 3.3
}

# MLBB Theme CSS
def apply_mlbb_theme():
    st.markdown("""
    <style>
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

    /* Main App Background */
    .stApp .block-container{
    background: linear-gradient(135deg, #0a0f1e 0%, #1a1a2e 50%, #16213e 100%);
    background-attachment: fixed;
    color: var(--mlbb-light);
    font-family: 'Rajdhani', sans-serif;
    }

    /* Title Styling */
    .main-title {
        font-family: 'Cinzel', serif;
        font-size: 4rem;
        font-weight: 700;
        text-align: center;
        background: var(--mlbb-gradient);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        text-shadow: 0 0 30px rgba(255, 77, 141, 0.8);
        margin: 2rem 0;
        position: relative;
        animation: titleGlow 3s ease-in-out infinite alternate;
    }

    @keyframes titleGlow {
        0% { text-shadow: 0 0 20px rgba(255, 77, 141, 0.6); }
        100% { text-shadow: 0 0 40px rgba(255, 77, 141, 1), 0 0 60px rgba(74, 0, 224, 0.8); }
    }

    .stApp h1:not(.stSidebar *), 
    .stApp h2:not(.stSidebar *), 
    .stApp h3:not(.stSidebar *) {
        font-family: 'Cinzel', serif;
        color: var(--mlbb-light);
        text-shadow: 0 2px 4px rgba(0, 0, 0, 0.8);
        position: relative;
    }

    .stApp h2:not(.stSidebar *) {
        font-size: 2.5rem;
        color: white;
        border-bottom: 2px solid var(--mlbb-primary);
        padding-bottom: 1rem;
        margin-bottom: 1.5rem;
    }

    .stApp h3:not(.stSidebar *) {
        font-size: 2rem;
        color: var(--mlbb-gold);
    }

    .stApp .element-container:not(.stSidebar *),
    .stApp .stDataFrame:not(.stSidebar *),
    .stApp .stSelectbox:not(.stSidebar *),
    .stApp .stAlert:not(.stSidebar *) {
        background: var(--mlbb-card-bg) !important;
        border: var(--mlbb-card-border) !important;
        border-radius: var(--mlbb-border-radius) !important;
        backdrop-filter: blur(10px) !important;
        box-shadow: 
            0 8px 32px rgba(0, 0, 0, 0.3),
            0 0 20px rgba(255, 77, 141, 0.1) !important;
        transition: var(--mlbb-transition) !important;
        position: relative;
        overflow: hidden;
    }

    /* Card Hover Effects */
    .stApp .element-container:not(.stSidebar *):hover,
    .stApp .stDataFrame:not(.stSidebar *):hover {
        transform: translateY(-2px);
        box-shadow: 
            0 12px 40px rgba(0, 0, 0, 0.4),
            var(--mlbb-glow) !important;
    }

    .stApp .element-container:not(.stSidebar *)::before {
        content: '';
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 2px;
        background: linear-gradient(90deg, #ff66cc, #9933ff);
        transition: left 0.8s ease;
    }

    .stApp .element-container:not(.stSidebar *):hover::before {
        left: 100%;
    }
                
    .stApp .main .stDataFrame {
        margin: 2rem 0;
    }
    
    .stApp .main .stDataFrame table {
        background: transparent !important;
        border-collapse: separate !important;
        border-spacing: 0 8px !important;
        width: 100% !important;
    }

    .stApp .main .stDataFrame th {
        background: var(--mlbb-gradient) !important;
        color: white !important;
        font-family: 'Orbitron', monospace !important;
        font-weight: 700 !important;
        font-size: 1.1rem !important;
        text-transform: uppercase !important;
        padding: 1rem !important;
        border: none !important;
        text-shadow: 0 2px 4px rgba(0, 0, 0, 0.8) !important;
        text-align: center !important;
    }

    .stApp .main .stDataFrame td {
        background: rgba(255, 255, 255, 0.05) !important;
        color: var(--mlbb-light) !important;
        font-family: 'Rajdhani', sans-serif !important;
        font-size: 1.1rem !important;
        font-weight: 600 !important;
        padding: 1rem !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        transition: all 0.3s ease !important;
        text-align: center !important;
    }

    .stApp .main .stDataFrame tr:hover td {
        background: rgba(255, 77, 141, 0.2) !important;
        box-shadow: 0 0 15px rgba(255, 77, 141, 0.4) !important;
        transform: scale(1.02) !important;
    }

    
    .stApp .main .stAlert {
        font-family: 'Rajdhani', sans-serif !important;
        font-size: 1.2rem !important;
        font-weight: 600 !important;
        border-left: 4px solid var(--mlbb-primary) !important;
    }

    .stApp .main .stSuccess {
        background: linear-gradient(135deg, rgba(0, 255, 127, 0.1), rgba(50, 205, 50, 0.1)) !important;
        border-left-color: #00ff7f !important;
        color: #00ff7f !important;
    }

    .stApp .main .stWarning {
        background: linear-gradient(135deg, rgba(255, 165, 0, 0.1), rgba(255, 140, 0, 0.1)) !important;
        border-left-color: #ffa500 !important;
        color: #ffa500 !important;
    }

    .stApp .main .stInfo {
        background: linear-gradient(135deg, rgba(0, 191, 255, 0.1), rgba(30, 144, 255, 0.1)) !important;
        border-left-color: #00bfff !important;
        color: #00bfff !important;
    }

   
    .stApp .main .stSelectbox select {
        background: var(--mlbb-card-bg) !important;
        color: var(--mlbb-light) !important;
        border: 2px solid var(--mlbb-primary) !important;
        border-radius: var(--mlbb-border-radius) !important;
        font-family: 'Rajdhani', sans-serif !important;
        font-size: 1.1rem !important;
        font-weight: 600 !important;
        padding: 0.75rem !important;
        box-shadow: var(--mlbb-glow) !important;
    }

    .stApp .main .stSelectbox select:focus {
        border-color: var(--mlbb-accent) !important;
        box-shadow: 0 0 25px rgba(255, 77, 141, 0.8) !important;
    }

    /* Champion Announcement  */
    .stApp .champion-card {
        background: linear-gradient(135deg, 
            rgba(255, 215, 0, 0.2) 0%, 
            rgba(255, 77, 141, 0.2) 50%, 
            rgba(74, 0, 224, 0.2) 100%) !important;
        border: 3px solid var(--mlbb-gold) !important;
        border-radius: 20px !important;
        padding: 3rem !important;
        margin: 2rem 0 !important;
        text-align: center !important;
        box-shadow: 
            0 0 50px rgba(255, 215, 0, 0.6),
            inset 0 0 50px rgba(255, 215, 0, 0.1) !important;
        animation: championGlow 2s ease-in-out infinite alternate !important;
        position: relative !important;
        overflow: hidden !important;
    }

    @keyframes championGlow {
        0% { 
            box-shadow: 0 0 30px rgba(255, 215, 0, 0.6);
            transform: scale(1);
        }
        100% { 
            box-shadow: 0 0 60px rgba(255, 215, 0, 0.9), 0 0 100px rgba(255, 77, 141, 0.5);
            transform: scale(1.02);
        }
    }

    .stApp .champion-card::before {
        content: '';
        position: absolute;
        top: -50%;
        left: -50%;
        width: 200%;
        height: 200%;
        background: conic-gradient(
            transparent,
            rgba(255, 215, 0, 0.3),
            transparent,
            rgba(255, 77, 141, 0.3),
            transparent
        );
        animation: rotate 4s linear infinite;
        z-index: -1;
    }

    @keyframes rotate {
        from { transform: rotate(0deg); }
        to { transform: rotate(360deg); }
    }

    .stApp .champion-name {
        font-family: 'Cinzel', serif !important;
        font-size: 4rem !important;
        font-weight: 700 !important;
        color: var(--mlbb-gold) !important;
        text-shadow: 
            0 0 20px rgba(255, 215, 0, 0.8),
            2px 2px 4px rgba(0, 0, 0, 0.8) !important;
        margin: 1rem 0 !important;
        animation: textPulse 2s ease-in-out infinite alternate !important;
    }

    @keyframes textPulse {
        0% { text-shadow: 0 0 20px rgba(255, 215, 0, 0.8); }
        100% { text-shadow: 0 0 40px rgba(255, 215, 0, 1), 0 0 60px rgba(255, 77, 141, 0.8); }
    }

    .stApp .champion-elo {
        font-family: 'Orbitron', monospace !important;
        font-size: 2rem !important;
        font-weight: 700 !important;
        color: var(--mlbb-light) !important;
        background: rgba(255, 215, 0, 0.2) !important;
        padding: 1rem 2rem !important;
        border-radius: 10px !important;
        border: 2px solid var(--mlbb-gold) !important;
        display: inline-block !important;
        margin: 1rem 0 !important;
    }

    .stApp .champion-medal {
        font-size: 6rem !important;
        animation: medalSpin 3s ease-in-out infinite !important;
        display: block !important;
        margin: 1rem 0 !important;
    }

    @keyframes medalSpin {
        0%, 100% { transform: rotate(0deg) scale(1); }
        25% { transform: rotate(-10deg) scale(1.1); }
        75% { transform: rotate(10deg) scale(1.1); }
    }

    /* Rank Styling */
    .stApp .rank-gold {
        color: var(--mlbb-gold) !important;
        font-weight: 700 !important;
        text-shadow: 0 0 10px rgba(255, 215, 0, 0.8) !important;
        animation: goldShimmer 2s ease-in-out infinite alternate !important;
    }

    .stApp .rank-silver {
        color: var(--mlbb-silver) !important;
        font-weight: 700 !important;
        text-shadow: 0 0 10px rgba(192, 192, 192, 0.8) !important;
    }

    .stApp .rank-bronze {
        color: var(--mlbb-bronze) !important;
        font-weight: 700 !important;
        text-shadow: 0 0 10px rgba(205, 127, 50, 0.8) !important;
    }

    @keyframes goldShimmer {
        0% { text-shadow: 0 0 10px rgba(255, 215, 0, 0.8); }
        100% { text-shadow: 0 0 20px rgba(255, 215, 0, 1), 0 0 30px rgba(255, 215, 0, 0.8); }
    }

    /* Chart Styling  */
    .stApp .vega-embed {
        background: var(--mlbb-card-bg) !important;
        border-radius: var(--mlbb-border-radius) !important;
        border: var(--mlbb-card-border) !important;
    }

    /* Battle Status */
    .stApp .battle-status {
        text-align: center !important;
        font-family: 'Orbitron', monospace !important;
        font-size: 1.5rem !important;
        font-weight: 700 !important;
        padding: 2rem !important;
        margin: 2rem 0 !important;
        border: 2px solid var(--mlbb-primary) !important;
        border-radius: var(--mlbb-border-radius) !important;
        background: var(--mlbb-card-bg) !important;
        box-shadow: var(--mlbb-glow) !important;
    }

    .stApp .countdown-text {
        font-size: 30px !important;
        color: white !important;
        text-shadow: 0 0 20px rgba(255, 154, 139, 0.8) !important;
        animation: countdownPulse 1s ease-in-out infinite alternate !important;
        font-family: 'Cinzel', serif !important;
        margin-bottom: 15px;
        font-weight: 600; 
    }

    @keyframes countdownPulse {
        0% { transform: scale(1); text-shadow: 0 0 20px rgba(255, 154, 139, 0.8); }
        100% { transform: scale(1.05); text-shadow: 0 0 30px rgba(255, 154, 139, 1); }
    }

    .stApp ::-webkit-scrollbar {
        width: 12px;
    }

    .stApp ::-webkit-scrollbar-track {
        background: var(--mlbb-darker);
        border-radius: 10px;
    }

    .stApp ::-webkit-scrollbar-thumb {
        background: var(--mlbb-gradient);
        border-radius: 10px;
        box-shadow: inset 0 0 5px rgba(255, 255, 255, 0.2);
    }

    .stApp ::-webkit-scrollbar-thumb:hover {
        background: var(--mlbb-primary);
    }

    .stApp .stMarkdown {
        text-align: center;
    }
    
    .stApp .stMarkdown h1, 
    .stApp .stMarkdown h2, 
    .stApp .stMarkdown h3 {
        text-align: center;
    }

    @media (max-width: 768px) {
        .stApp .main-title {
            font-size: 2.5rem;
        }
        
        .stApp .champion-name {
            font-size: 2.5rem !important;
        }
        
        .stApp .champion-medal {
            font-size: 4rem !important;
        }
        
        .stApp .stDataFrame th, 
        .stApp .stDataFrame td {
            padding: 0.5rem !important;
            font-size: 0.9rem !important;
        }
    }
    </style>
    """, unsafe_allow_html=True)

def get_db_connection():
    return mysql.connector.connect(
        host="145.223.18.115",
        port=3306,
        user="admin",
        password="@Cittamall13",         
        database="gamifiedqc" 
    )

def is_battle_started():
    today = date.today()
    return today.day >= 20

def get_available_months():
    conn = get_db_connection()
    months_df = pd.read_sql("SELECT DISTINCT month FROM monthly_final ORDER BY month DESC", conn)
    conn.close()
    return months_df['month'].tolist()

def get_previous_month(current_month=None):
    """Calculate previous month for a given month"""
    if not current_month:
        current_month = datetime.now().strftime("%Y-%m")
    
    if '-' in current_month:  # YYYY-MM format
        year, month = map(int, current_month.split('-'))
        if month == 1:
            return f"{year-1}-12"
        else:
            return f"{year}-{month-1:02d}"
    else:  # Month name format like 'Jan', 'Feb'
        month_order = {'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4, 'May': 5, 'Jun': 6,
                      'Jul': 7, 'Aug': 8, 'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12}
        current_year = datetime.now().year
        current_month_num = month_order.get(current_month, 1)
        
        if current_month_num == 1:
            return f"{current_year-1}-Dec"
        else:
            prev_month_num = current_month_num - 1
            prev_month_name = list(month_order.keys())[list(month_order.values()).index(prev_month_num)]
            return f"{current_year}-{prev_month_name}"

def calculate_champion_ranking(selected_month=None):
    """
    Calculate champion ranking for a specific month using the continuous ELO system
    This uses the monthly_final table which contains the final ELO after simulation
    """
    conn = get_db_connection()
    
    if selected_month:
        # Get final rankings for the selected month
        query = "SELECT * FROM monthly_final WHERE month = %s ORDER BY lab_rank ASC"
        rankings_df = pd.read_sql(query, conn, params=(selected_month,))
    else:
        query = "SELECT * FROM monthly_final WHERE month = (SELECT MAX(month) FROM monthly_final) ORDER BY lab_rank ASC"
        rankings_df = pd.read_sql(query, conn)
    
    conn.close()
    
    if rankings_df.empty:
        return pd.DataFrame()
    
    champion_df = rankings_df[['lab', 'monthly_final_elo', 'lab_rank']].copy()
    champion_df.columns = ['Lab', 'Final Elo', 'Rank']
    
    medals = ["🥇", "🥈", "🥉"]
    champion_df["Medal"] = ""
    for i in range(min(3, len(champion_df))):
        champion_df.loc[i, "Medal"] = medals[i]
    
    return champion_df

AVATAR_NAME_TO_PATH = {
    "Zareth":"avatars/zareth.png",
    "Dreadon":"avatars/Dreadon.png",
    "Selindra":"avatars/Selindra.png",
    "Raviel":"avatars/Raviel.png",
    "Takeshi":"avatars/Takeshi.png",
    "Synkro":"avatars/Synkro.png",
    "Zyphira":"avatars/Zyphira.png",
    "Umbra":"avatars/Umbra.png",
    "Kaira":"avatars/Kaira.png",
    "Ignar":"avatars/Ignar.png",
    "Ryden":"avatars/Ryden.png",
    "Nyra":"avatars/Nyra.png",
    "Kaen":"avatars/Kaen.png",
    "Raika":"avatars/Raika.png",
    "Dain":"avatars/Dain.png",
    "Veyra":"avatars/Veyra.png",
    "Reiko":"avatars/Reiko.png",
    "Kane & Lyra":"avatars/kanenlyra.png",
    "Mimi":"avatars/Mimi.png",
    "Rowan":"avatars/Rowan.png",
    "Taro":"avatars/Taro.png",
    "Eldric":"avatars/Eldric.png",
    "Noel":"avatars/Noel.png",
    "Elias":"avatars/Elias.png",
    "Finn":"avatars/Finn.png",
}
DEFAULT_AVATAR = "avatars/default.png"

def resolve_avatar_path(value: str) -> str:
    if not value:
        return DEFAULT_AVATAR

    if value in AVATAR_NAME_TO_PATH:
        candidate = AVATAR_NAME_TO_PATH[value]
    else:
        if not any(sep in value for sep in ("/", "\\")) and value.lower().endswith((".png", ".jpg", ".jpeg", ".webp")):
            candidate = f"avatars/{value}"
        else:
            candidate = value

    if os.path.exists(candidate):
        return candidate

    try_paths = []
    try:
        here = Path(__file__).resolve().parent
        project_root = here.parent
        try_paths.append(project_root / candidate)
        try_paths.append(here / candidate)
    except Exception:
        pass

    for p in try_paths:
        if p.exists():
            return str(p)

    return DEFAULT_AVATAR if os.path.exists(DEFAULT_AVATAR) else candidate

def file_to_data_uri(path: str) -> str:
    resolved = resolve_avatar_path(path)
    mime, _ = mimetypes.guess_type(resolved)
    mime = mime or "image/png"
    with open(resolved, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("ascii")
    return f"data:{mime};base64,{b64}"

def get_avatar_data_uri_map():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT username, avatar FROM labs_users")
    rows = cursor.fetchall()
    conn.close()

    out = {}
    for row in rows:
        avatar_value = row["avatar"] or DEFAULT_AVATAR
        try:
            out[row["username"]] = file_to_data_uri(avatar_value)
        except Exception:
            out[row["username"]] = file_to_data_uri(DEFAULT_AVATAR)
    return out

def get_avatar_names():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT username, avatar FROM labs_users")
    rows = cursor.fetchall()
    conn.close()
    
    return {row['username']: row['avatar'] for row in rows}

def get_lab_ratings_progression(lab_name):
    conn = get_db_connection()

    query = """
    SELECT * FROM battle_logs 
    WHERE lab_a = %s OR lab_b = %s 
    ORDER BY CAST(round_num AS UNSIGNED) ASC
    """
    prog_df = pd.read_sql(query, conn, params=(lab_name, lab_name))
    conn.close()
    
    if prog_df.empty:
        return pd.DataFrame()
    
    progression = []
    battle_count = 0
    
    for _, battle in prog_df.iterrows():
        battle_count += 1
        
        if battle['lab_a'] == lab_name:
            elo = battle['updated_rating_a']
            opponent = battle['lab_b']
        else:
            elo = battle['updated_rating_b']
            opponent = battle['lab_a']
        
        progression.append({
            'Battle': battle_count,
            'Elo': elo,
            'Opponent': opponent,
            'Round': battle['round_num'],
            'Month': battle.get('month', 'Unknown')
        })
    
    return pd.DataFrame(progression)

def run():
    apply_mlbb_theme()
    apply_sidebar_theme()
    
    st.markdown("""
    <div class="main-title">
        ⚔️ LLKK CHAMPION BOARD ⚔️
    </div>
    """, unsafe_allow_html=True)

    # Check if battle has started (after 20th of month)
    if not is_battle_started():
        today = date.today()
        days_left = 20 - today.day
        
        st.markdown("""
        <div class="battle-status">
            <h2>⏳ The Battle Arena is Sealed</h2>
            <p>The ancient battlegrounds remain locked until the 20th day of each moon cycle.</p>
        </div>
        """, unsafe_allow_html=True)
        
        if today.day < 20:
            st.markdown(f"""
            <div class="countdown-text">
                🗓️ {days_left} days until the gates open...
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="countdown-text">
                ⚔️ The battle should commence today! Return soon, warrior!
            </div>
            """, unsafe_allow_html=True)
        
        return
    
    st.markdown("""
    <div class="battle-status">
        <h2>🏆 The Battle Has Concluded!</h2>
        <p>Victory has been claimed and a new champion rises!</p>
    </div>
    """, unsafe_allow_html=True)

    available_months = get_available_months()
    
    if not available_months:
        st.error("""
        ⚠️ No battle data available yet! 

        """)
        return
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        selected_month = st.selectbox(
            "🎯 Select Month to Display", 
            available_months,
        )
    
    with col2:
        if selected_month:
            st.info(f"📅 Showing: **{selected_month}**")
    
    avatar_map = get_avatar_names()
 
    champion_df = calculate_champion_ranking(selected_month)
    
    if champion_df.empty:
        st.error(f"⚠️ No champion data available for {selected_month}")
        return
    
    leaderboard_df = champion_df.copy()
    leaderboard_df["Avatar"] = leaderboard_df["Lab"].map(avatar_map)
    leaderboard_df["Avatar"] = leaderboard_df["Avatar"].fillna(leaderboard_df["Lab"])  
    
    display_df = leaderboard_df[["Rank", "Avatar", "Final Elo", "Medal"]]
    
    st.markdown("## 🏅 Hall of Champions")
    
    styled_df = display_df.style \
        .format({"Final Elo": "{:.2f}"}) \
        .set_properties(**{
            'background-color': 'rgba(15, 20, 40, 0.7)',
            'color': '#f8f9ff',
            'border': '1px solid rgba(255, 255, 255, 0.1)',
            'text-align': 'center'
        }) \
        .set_table_styles([{
            'selector': 'th',
            'props': [('background', 'linear-gradient(135deg, #4a00e0 0%, #ff4d8d 100%)'),
                     ('color', 'white'),
                     ('font-family', "'Orbitron', monospace"),
                     ('font-weight', '700'),
                     ('text-transform', 'uppercase'),
                     ('text-align', 'center')]
        }])
    
    st.dataframe(styled_df, use_container_width=True, height=(len(display_df) + 1) * 35 + 3, hide_index=True)

    champ_row = display_df.iloc[0]
    avatar_data_uri_map = get_avatar_data_uri_map()
    lab_username = champion_df.iloc[0]['Lab']  
    avatar_data_uri = avatar_data_uri_map.get(lab_username, file_to_data_uri(DEFAULT_AVATAR))

    st.markdown(f"""
    <div class="champion-card">
        <h2>👑 CHAMPION OF THE REALM 👑</h2>
        <div class="champion-name">{champ_row['Avatar']}</div>
        <img src="{avatar_data_uri}" alt="Champion Avatar" 
             style="width: 230px; height: 230px; border-radius: 15px; border: 0px solid gold; margin: 20px auto; display: block;">
        <div class="champion-elo">Final Elo Rating: {champ_row['Final Elo']:.2f}</div>
        <div class="champion-medal">{champ_row['Medal']}</div>
        <p style="font-family: 'Cinzel', serif; font-size: 1.5rem; margin-top: 2rem; color: var(--mlbb-light);">
            Glory eternal! The realm bows to your supremacy!
        </p>
    </div>
    """, unsafe_allow_html=True)

    # ELO progression chart 
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SHOW TABLES LIKE 'battle_logs'")
    table_exists = cursor.fetchone()
    
    if table_exists:
        prog_df = pd.read_sql("SELECT * FROM battle_logs ORDER BY id", conn)
        conn.close()

        if not prog_df.empty:
            st.markdown("## 📈 Warrior's Journey")
            
            lab_options = {}
            for lab in set(prog_df["lab_a"]).union(set(prog_df["lab_b"])):
                lab_options[avatar_map.get(lab, lab)] = lab
            
            selected_avatar = st.selectbox("Select Avatar", list(lab_options.keys()))
            selected_lab = lab_options[selected_avatar]

            prog_long = pd.concat([
                prog_df[["id", "lab_a", "updated_rating_a", "month"]].rename(
                    columns={"lab_a": "Lab", "updated_rating_a": "Elo"}
                ),
                prog_df[["id", "lab_b", "updated_rating_b", "month"]].rename(
                    columns={"lab_b": "Lab", "updated_rating_b": "Elo"}
                )
            ])
            prog_long["Month"] = prog_long["month"]
            
            filtered = prog_long[prog_long["Lab"] == selected_lab]
            
            if not filtered.empty:
                chart = alt.Chart(filtered).mark_line(
                    color="#518ee4",
                    strokeWidth=3
                ).encode(
                    x=alt.X("Month:N", title="Month", axis=alt.Axis(labelAngle=0)),
                    y=alt.Y("Elo:Q", title="Elo Score", scale=alt.Scale(zero=False)),
                    tooltip=["Month", "Elo"]
                ).properties(
                    title={
                        "text": f"{selected_avatar} — Elo Progression",
                        "fontSize": 26,
                        "font": "Cinzel",
                        "anchor": "middle",
                        "color": "#ffd700",
                    },
                    width=700,
                    height=400
                ).configure_axis(
                    gridColor='rgba(255, 255, 255, 0.1)',
                    domainColor='#ff4d8d',
                    labelColor='#f8f9ff',
                    titleColor="#ffd700"
                ).configure_view(
                    strokeWidth=0,
                    fill='rgba(15, 20, 40, 0)'
                )
                
                st.altair_chart(chart, use_container_width=True)
            else:
                st.info("ℹ️ No rating data available for this avatar.")
        else:
            conn.close()
            st.info("ℹ️ No battle logs available yet.")
    else:
        conn.close()
        st.info("ℹ️ No battle logs available yet.")


if __name__ == "__main__":
    run()