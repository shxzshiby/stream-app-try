import streamlit as st
import pandas as pd
import numpy as np
import itertools
import os
from pathlib import Path
import mysql.connector
import base64
import json
import mimetypes
import streamlit.components.v1 as components
import time 
from datetime import datetime 
from Login import apply_sidebar_theme
import traceback
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

# EFLM Targets
EFLM_TARGETS = {
    "Albumin": 2.1, "ALT": 6.0, "ALP": 3.98, "AST": 5.3, "Bilirubin (Total)": 8.6,
    "Cholesterol": 2.9, "TG": 4.98, "Creatinine": 3.4, "Glucose": 2.9,
    "HDL Cholesterol": 4.0, "CL": 0.83, "Potassium": 1.8, "Sodium": 0.9,
    "Protein (Total)": 2.0, "Urea": 3.9, "Uric Acid": 3.3
}

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

# Resolve any avatar value (name / filename / relative path) to an actual file path
def resolve_avatar_path(value: str) -> str:
    """
    Accepts:
      - Display name (e.g. 'zareth')
      - Filename only (e.g. 'zareth.png')
      - Relative path (e.g. 'avatars/zareth.png')
      - Absolute path
    Returns a path that exists, or DEFAULT_AVATAR if not found.
    """
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
    """Return data:<mime>;base64,<...> for an image file path."""
    resolved = resolve_avatar_path(path) 
    mime, _ = mimetypes.guess_type(resolved)
    mime = mime or "image/png"
    with open(resolved, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("ascii")
    return f"data:{mime};base64,{b64}"

def get_db_connection():
    return mysql.connector.connect(
        host="145.223.18.115",
        port=3306,
        user="admin",
        password="@Cittamall13",         
        database="gamifiedqc" 
    )

def fetch_lab_data(lab=None):
    conn = get_db_connection()
    query = "SELECT * FROM submissions"
    params = ()

    if lab:
        query += " WHERE lab = %s"
        params = (lab,)

    df = pd.read_sql(query, conn, params=params)
    conn.close()
    return df.reset_index(drop=True)

def get_lab_avatars():
    """
    Returns {username: avatar_name} mapping
    """
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT username, avatar FROM labs_users")
    rows = cursor.fetchall()
    conn.close()
    
    avatar_map = {}
    for row in rows:
        avatar_map[row['username']] = row['avatar'] or row['username']
    return avatar_map

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

DEFAULT_AVATAR_DATA_URI = file_to_data_uri(DEFAULT_AVATAR)

def encode_image_to_base64(image_path):
    try:
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode()
    except FileNotFoundError:
        st.error(f"Background image not found at: {image_path}")
        return None
    
def insert_submission(data):
    conn = get_db_connection()
    cursor = conn.cursor()
    sql = """
        INSERT INTO submissions (lab, parameter, level, month, `CV(%)`, Ratio, `n(QC)`, `Working_Days`)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """
    cursor.execute(sql, (
        data["Lab"], data["Parameter"], data["Level"], data["Month"],
        data.get("CV(%)"), data.get("Ratio"), data.get("n(QC)"), data.get("Working_Days")
    ))
    conn.commit()
    conn.close()

def save_monthly_final(month, lab, lab_rank, monthly_final_elo):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO monthly_final (month, lab, lab_rank, monthly_final_elo)
        VALUES (%s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE lab_rank = %s, monthly_final_elo = %s
    """, (month, lab, lab_rank, monthly_final_elo, lab_rank, monthly_final_elo))
    
    conn.commit()
    conn.close()

def get_monthly_final(month=None):
    conn = get_db_connection()
    
    if month:
        query = "SELECT * FROM monthly_final WHERE month = %s ORDER BY lab_rank ASC"
        df = pd.read_sql(query, conn, params=(month,))
    else:
        query = "SELECT * FROM monthly_final ORDER BY month DESC, lab_rank ASC"
        df = pd.read_sql(query, conn)
    
    conn.close()
    return df

def save_battle_log(lab_a, lab_b, winner, loser, updated_rating_a, updated_rating_b, month=None):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT MAX(CAST(round_num AS UNSIGNED)) FROM battle_logs")
    last_round = cursor.fetchone()[0]

    if last_round is None:
        round_num_to_store = 1
    else:
        round_num_to_store = int(last_round) + 1 

    cursor.execute("""
        INSERT INTO battle_logs
        (round_num, lab_a, lab_b, winner, loser, updated_rating_a, updated_rating_b, month)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """, (
        round_num_to_store,
        lab_a, lab_b, winner, loser, updated_rating_a, updated_rating_b, month
    ))

    conn.commit()
    cursor.close()
    conn.close()

def run_battlelog(auto_play=False, user_role="admin", user_lab=None,selected_months=None, show_all_data=True):
    
    conn = get_db_connection()

    simulation_months = st.session_state.get('simulation_months')
    run_all_months = st.session_state.get('run_all_months', True)
    
    if simulation_months and not run_all_months:
        placeholders = ','.join(['%s'] * len(simulation_months))
        battle_logs_query = f"SELECT * FROM battle_logs WHERE month IN ({placeholders}) ORDER BY CAST(round_num AS UNSIGNED) ASC"
        battle_logs_df = pd.read_sql(battle_logs_query, conn, params=simulation_months)
    else:
        battle_logs_df = pd.read_sql("SELECT * FROM battle_logs ORDER BY CAST(round_num AS UNSIGNED) ASC", conn)

    if simulation_months and not run_all_months:
        placeholders = ','.join(['%s'] * len(simulation_months))
        monthly_rankings_query = f"SELECT * FROM monthly_rankings WHERE month IN ({placeholders}) ORDER BY parameter, level, ranking ASC"
        monthly_rankings_df = pd.read_sql(monthly_rankings_query, conn, params=simulation_months)
    else:
        monthly_rankings_df = pd.read_sql("SELECT * FROM monthly_rankings ORDER BY parameter, level, ranking ASC", conn)
  
    if simulation_months and not run_all_months:
        placeholders = ','.join(['%s'] * len(simulation_months))
        monthly_final_query = f"SELECT * FROM monthly_final WHERE month IN ({placeholders}) ORDER BY month DESC, lab_rank ASC"
        monthly_final_df = pd.read_sql(monthly_final_query, conn, params=simulation_months)
    else:
        monthly_final_df = pd.read_sql("SELECT * FROM monthly_final ORDER BY month DESC, lab_rank ASC", conn)

    battle_logs_df = pd.read_sql(
        "SELECT * FROM battle_logs ORDER BY CAST(round_num AS UNSIGNED) ASC", 
        conn
    )

    all_battle_logs_df = pd.read_sql("SELECT * FROM battle_logs ORDER BY CAST(round_num AS UNSIGNED) ASC", conn)
    
    if user_role == "admin":
        battle_logs_df = all_battle_logs_df
    elif user_role == "lab" and user_lab:
        battle_logs_df = all_battle_logs_df[
            (all_battle_logs_df['lab_a'] == user_lab) | 
            (all_battle_logs_df['lab_b'] == user_lab)
        ]
    else:
        battle_logs_df = pd.DataFrame()

    monthly_rankings_df = pd.read_sql("SELECT * FROM monthly_rankings ORDER BY parameter, level, ranking ASC", conn)
    monthly_final_df = pd.read_sql("SELECT * FROM monthly_final ORDER BY month DESC, lab_rank ASC", conn)
    lab_ratings_df = pd.read_sql("SELECT * FROM lab_ratings", conn)
    submissions_data = pd.read_sql("SELECT Lab, `CV(%)` AS cv_value, Ratio AS ratio_value FROM submissions", conn)
    conn.close()

    # Convert Timestamp objects to strings for JSON serialization
    for df in [battle_logs_df, monthly_rankings_df, monthly_final_df, lab_ratings_df, submissions_data]:
        for col in df.columns:
            if pd.api.types.is_datetime64_any_dtype(df[col]):
                df[col] = df[col].astype(str)
        df = df.where(pd.notnull(df), None)

    # Convert to JSON for frontend
    battle_logs_json = battle_logs_df.to_dict(orient="records")
    monthly_rankings_json = monthly_rankings_df.to_dict(orient="records")
    lab_ratings_json = lab_ratings_df.to_dict(orient="records")
    submission_json = submissions_data.to_dict(orient="records")
    monthly_final_json = monthly_final_df.to_dict(orient="records")
    
    avatar_name_map = get_lab_avatars()
    
    st.components.v1.html(render_visual_battle(
        battle_logs_json, 
        monthly_rankings_json, 
        lab_ratings_json, 
        submission_json, 
        get_avatar_data_uri_map(), 
        avatar_name_map, 
        auto_play, 
        monthly_final_json, 
        user_role,
        user_lab,
        selected_months,  
        show_all_data    
    ), height=1000, scrolling=True)

#audio cheering 
with open("sounds/cheering.mp3", "rb") as f:
    b64 = base64.b64encode(f.read()).decode()

def render_visual_battle(battle_logs, monthly_rankings, lab_ratings, submissions, avatar_map, avatar_name_map, auto_play=False, monthly_final=None,user_role="admin", user_lab=None, selected_months=None, show_all_data=True):

    selected_months_json = json.dumps(selected_months or [])
    show_all_data_js = str(show_all_data).lower()

    battle_logs_json = json.dumps(battle_logs)
    monthly_rankings_with_movement = []
    for ranking in monthly_rankings:
        ranking_copy = ranking.copy()
        month = ranking_copy.get('month', '')
        
        if not month or month.endswith('-01') or month == 'Jan':
            ranking_copy['movement'] = "-"
        else:
            prev_rankings = get_previous_month_rankings(month)
            
            prev_rank_dict = {}
            for rank in prev_rankings:
                key = f"{rank['lab']}_{rank['parameter']}_{rank['level']}"
                prev_rank_dict[key] = rank['ranking']
            
            key = f"{ranking_copy['lab']}_{ranking_copy['parameter']}_{ranking_copy['level']}"
            
            if key not in prev_rank_dict:
                ranking_copy['movement'] = "NEW"
            else:
                prev_rank = prev_rank_dict[key]
                current_rank = ranking_copy['ranking']
                
                if current_rank < prev_rank:
                    ranking_copy['movement'] = f"↑{prev_rank - current_rank}"
                elif current_rank > prev_rank:
                    ranking_copy['movement'] = f"↓{current_rank - prev_rank}"
                else:
                    ranking_copy['movement'] = "–"  

        monthly_rankings_with_movement.append(ranking_copy)

    monthly_rankings_json = json.dumps(monthly_rankings_with_movement)
    lab_ratings_json = json.dumps(lab_ratings)
    submission_json = json.dumps(submissions)
    avatar_map_json = json.dumps(avatar_map)
    avatar_name_map_json = json.dumps(avatar_name_map)
    monthly_final_json = json.dumps(monthly_final)
    default_avatar_data_uri = DEFAULT_AVATAR_DATA_URI

    bg_image_base64 = encode_image_to_base64("arenabg.jpg")

    narration_phrases = [
    "💥 First Blood! {attacker} draws first blood!",
    "🔥 {attacker} is on a Killing Spree!",
    "⚡ Mega Kill! {attacker} can’t be stopped!",
    "💣 Unstoppable! {attacker} is tearing through the battlefield!",
    "🔥 Dominating! {attacker} shows no mercy!",
    "💥 Savage strike! {attacker} crushes the opposition!",
    "⚔️ Legendary! {attacker} is rewriting history!",
    "🚀 {attacker} with a Godlike performance!",
    "🔥 Victory is close — {attacker} leads the charge!",
    "💥 What a finish! {attacker} seals the game in style!"
]

    bg_css = f"""
    body {{
        font-family: 'Arial', sans-serif;
        background-image: url("data:image/jpg;base64,{bg_image_base64}");
        background-size: cover;
        background-position: center;
        background-repeat: no-repeat;
        background-attachment: fixed;
        color: white;
        margin: 0;
        padding: 20px;
        min-height: 100vh;
    }}
    """ if bg_image_base64 else """
    body {{
        font-family: 'Arial', sans-serif;
        background: linear-gradient(135deg, #1a2a6c, #b21f1f, #fdbb2d);
        color: white;
        margin: 0;
        padding: 20px;
        min-height: 100vh;
    }}
    """

    return f"""
    <html>
    <head>
      <meta name="viewport" content="width=device-width, initial-scale=1.0">
      <script src="https://cdn.jsdelivr.net/npm/three@0.128.0/build/three.min.js"></script>
      <script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js"></script>
      <style>
        @import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@400;700&family=MedievalSharp&display=swap');
        
        {bg_css}

        :root{{ 
        --mlbb-primary: #ff4d8d;
        --mlbb-secondary: #4a00e0;F
        --mlbb-accent: #ff9a8b;
        --mlbb-gold: #ffd700;
        --mlbb-silver: #c0c0c0;
        --mlbb-bronze: #cd7f32;
        --mlbb-dark: #0a0f1e;
        --mlbb-darker: #070a14;
        --mlbb-light: #f8f9ff;
        --mlbb-gradient: linear-gradient(135deg, var(--mlbb-secondary) 0%, var(--mlbb-primary) 100%);
        --mlbb-glow: 0 0 20px rgba(255, 77, 141, 0.6);
        --mlbb-glow-intense: 0 0 35px rgba(255, 77, 141, 0.9);
        --mlbb-border-radius: 16px;
        --mlbb-transition: all 0.4s cubic-bezier(0.25, 0.8, 0.25, 1);
        --mlbb-card-bg: rgba(15, 20, 40, 0.8);
        --mlbb-card-border: 1px solid rgba(255, 255, 255, 0.15);
      }}
        
        body {{
            font-family: 'Cinzel', serif;
            background: linear-gradient(rgba(10, 15, 30, 0.85), rgba(10, 15, 30, 0.85)), 
                        url("data:image/jpg;base64,{bg_image_base64}") if bg_image_base64 else "none";
            background-size: cover;
            background-position: center;
            background-repeat: no-repeat;
            background-attachment: fixed;
            color: #e0e0ff;
            margin: 0;
            padding: 10px;
            min-height: 100vh;
            text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.7);
        }}

          @media (max-width: 768px) {{
          #arena {{
              grid-template-rows: 120px 200px 40px;
              padding: 15px;
              margin: 5px;
              max-width: 100%; /* biar auto ikut screen */
          }}

          .avatar {{
              width: 120px;
              height: 120px;
          }}

          .avatar-hp-bar {{
              width: 120px;
          }}

          .narrator-box {{
              flex-direction: column;
              padding: 15px;
          }}

          #narrator-text {{
              font-size: 18px;
              width: 100%;
              margin: 10px 0;
          }}

          .battle-log, .rankings-section {{
              padding: 15px;
              margin: 10px;
          }}
      }}

      @media (max-width: 480px) {{
          .avatar-area {{
              gap: 40px;
          }}

          .avatar {{
              width: 100px;
              height: 100px;
          }}

          .countdown-text {{
              font-size: 80px;
          }}

          button {{
              padding: 10px 20px;
              margin: 0 10px;
              font-size: 14px;
          }}
      }}
        
        #arena {{
          display: grid;
          grid-template-columns: 1fr;
          grid-template-rows: auto auto auto;
          grid-template-areas: 
            "narrator"
            "avatars"
            "center-space";
          align-items: center;
          margin: 10px auto;
          max-width: 1000px;
          background: rgba(10, 15, 30, 0.6);
          padding: 30px;
          border-radius: 20px;
          box-shadow: 0 0 30px rgba(102, 51, 153, 0.6);
          border: 2px solid rgba(123, 104, 238, 0.4);
          position: relative;
          overflow: hidden;
        }}

        body::before{{
          content: '';
          position: fixed;
          top: 0;
          left: 0;
          width: 100%;
          height: 100%;
          background: 
            radial-gradient(2px 2px at 20% 30%, rgba(255, 255, 255, 0.3) 0%, transparent 100%),
            radial-gradient(2px 2px at 80% 70%, rgba(255, 154, 139, 0.4) 0%, transparent 100%),
            radial-gradient(3px 3px at 40% 20%, rgba(123, 104, 238, 0.4) 0%, transparent 100%),
            radial-gradient(2px 2px at 60% 80%, rgba(155, 89, 182, 0.3) 0%, transparent 100%);
          background-size: 300px 300px, 250px 250px, 400px 400px, 350px 350px;
          animation: particlesMove 20s infinite linear;
          pointer-events: none;
          z-index: -1;
        }}

        @keyframes particlesMove{{
          from {{ background-position: 0 0, 0 0, 0 0, 0 0; }}
          to {{ background-position: 300px 300px, 250px 250px, 400px 400px, 350px 350px; }}
        }}
        
        #arena::before {{
          content: '';
          position: absolute;
          top: 0;
          left: 0;
          right: 0;
          bottom: 0;
          background: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100" viewBox="0 0 100 100"><path fill="rgba(123, 104, 238, 0.1)" d="M30,30 Q50,10 70,30 T90,50 T70,70 T50,90 T30,70 T10,50 T30,30 Z" /></svg>');
          background-size: 200px;
          opacity: 0.2;
          z-index: -1;
        }}

        #arena::after{{
          content: '';
          position: absolute;
          top: -2px;
          left: -2px;
          right: -2px;
          bottom: -2px;
          background: linear-gradient(45deg, 
            transparent, 
            transparent, 
            var(--mlbb-primary), 
            var(--mlbb-secondary),
            transparent, 
            transparent);
          background-size: 400% 400%;
          border-radius: var(--mlbb-border-radius);
          animation: energyFlow 6s linear infinite;
          z-index: -1;
          opacity: 0.7;
          filter: blur(8px);
        }}

        @keyframes energyFlow{{
          0% {{ background-position: 0% 50%; }}
          50% {{ background-position: 100% 50%; }}
          100% {{ background-position: 0% 50%; }}
        }}

        .lab::before{{
          content: '';
          position: absolute;
          top: 0;
          left: 0;
          right: 0;
          bottom: 0;
          background: radial-gradient(circle at center, transparent 30%, rgba(123, 104, 238, 0.1) 100%);
          border-radius: 18px;
          opacity: 0;
          transition: opacity 0.5s ease;
          z-index: -1;
        }}

        .lab:hover{{
          transform: translateY(-8px) rotateX(5deg);
          box-shadow: 
            0 15px 35px rgba(0, 0, 0, 0.5),
            0 0 25px rgba(102, 51, 153, 0.7),
            var(--mlbb-glow);
        }}

        .lab:hover::before{{
          opacity: 1;
        }}

        .lab-left{{
          grid-area: left-lab;
          justify-self: end;
        }}

        .lab-right{{
          grid-area: right-lab;
          justify-self: start;
        }}

        .avatar-area {{
          grid-area: avatars;
          display: flex;
          justify-content: center;
          align-items: center;
          margin: 20px 0;
          position: relative;
          z-index: 3;
          gap: 100px;
        }}

        .avatar-container {{
          display: flex;
          flex-direction: column;
          align-items: center;
          width: 150px;
          position: relative;
        }}

        .avatar {{
          width: 180px;
          height: 180px;
          object-fit: cover;
          background: linear-gradient(135deg, #2c3e50, #4a69bd);
          box-shadow: 
            0 0 25px rgba(123, 104, 238, 0.7),
            0 15px 35px rgba(0, 0, 0, 0.5),
            inset 0 2px 10px rgba(255, 255, 255, 0.1);
          transition: all 0.4s cubic-bezier(0.25, 0.8, 0.25, 1);
          position: relative;
          overflow: hidden;
          border: 3px solid #7b68ee;
          border-radius: 12px;
          transform: perspective(800px) rotateX(5deg) rotateY(0deg);
          filter: 
            drop-shadow(0 10px 20px rgba(0, 0, 0, 0.4))
            drop-shadow(0 0 15px rgba(123, 104, 238, 0.3));
          z-index: 1
        }}

        /* Enhanced 3D hover effects */
        .avatar:hover {{
          transform: perspective(800px) rotateX(8deg) rotateY(5deg) translateZ(20px);
          box-shadow: 
            0 0 35px rgba(123, 104, 238, 0.9),
            0 25px 50px rgba(0, 0, 0, 0.6),
            inset 0 2px 15px rgba(255, 255, 255, 0.2);
          filter: 
            drop-shadow(0 15px 30px rgba(0, 0, 0, 0.6))
            drop-shadow(0 0 25px rgba(123, 104, 238, 0.5))
            brightness(1.1);
        }}

        /* 3D depth effect with multiple layers */
        .avatar::before {{
          content: '';
          position: absolute;
          top: -3px;
          left: -3px;
          right: -3px;
          bottom: -3px;
          background: linear-gradient(135deg, rgba(255, 255, 255, 0.2), transparent 50%);
          border-radius: 15px;
          z-index: 1;
          pointer-events: none;
        }}

        .avatar::after {{
          content: '';
          position: absolute;
          top: 0;
          left: 0;
          right: 0;
          bottom: 0;
          background: linear-gradient(
            135deg,
            rgba(123, 104, 238, 0.1) 0%,
            transparent 30%,
            rgba(255, 77, 141, 0.1) 70%,
            rgba(255, 215, 0, 0.1) 100%
          );
          border-radius: 12px;
          z-index: 2;
          pointer-events: none;
          animation: avatarAura 3s infinite ease-in-out;
        }}

        @keyframes avatarAura {{
          0%, 100% {{ opacity: 0.3; transform: scale(1); }}
          50% {{ opacity: 0.6; transform: scale(1.02); }}
        }}


        @keyframes avatarShine {{
          0% {{ transform: translateX(-100%) translateY(-100%) rotate(30deg); }}
          100% {{ transform: translateX(100%) translateY(100%) rotate(30deg); }}
        }}

        .avatar-hp-bar {{
          width: 180px;
          height: 18px;
          background: rgba(44, 62, 80, 0.7);
          border-radius: 8px;
          overflow: hidden;
          margin: 10px 0;
          border: 1px solid rgba(123, 104, 238, 0.3);
          box-shadow: 0 0 5px rgba(123, 104, 238, 0.3) inset;
          position: relative;
        }}

        .avatar-hp-fill {{
          height: 100%;
          background: linear-gradient(90deg, #8e44ad, #3498db);
          width: 100%;
          transition: width 1.5s cubic-bezier(0.25, 0.46, 0.45, 0.94);
          box-shadow: 0 0 15px rgba(142, 68, 173, 0.7);
          animation: hpPulse 2s infinite ease-in-out;
        }}


        .countdown-overlay{{
          position: fixed;
          top: 0;
          left: 0;
          width: 100%;
          height: 100%;
          background: rgba(10, 15, 30, 0.95);
          display: flex;
          justify-content: center;
          align-items: center;
          z-index: 1000;
        }}

        .countdown-text{{
          font-size: 140px;
          color: #9b59b6;
          font-weight: bold;
          text-shadow: 0 0 25px rgba(155, 89, 182, 0.9);
          animation: pulse 1s infinite;
          font-family: 'MedievalSharp', cursive;
          position: relative;
        }}

        .countdown-text::after{{
          content: '';
          position: absolute;
          top: 0;
          left: 0;
          right: 0;
          bottom: 0;
          background: radial-gradient(circle at center, rgba(155, 89, 182, 0.4) 0%, transparent 70%);
          border-radius: 50%;
          animation: pulse 2s infinite alternate;
          z-index: -1;
        }}

        @keyframes pulse{{
          0% {{ transform: scale(1); text-shadow: 0 0 20px rgba(155, 89, 182, 0.8); }}
          50% {{ transform: scale(1.2); text-shadow: 0 0 40px rgba(155, 89, 182, 1); }}
          100% {{ transform: scale(1); text-shadow: 0 0 20px rgba(155, 89, 182, 0.8); }}
        }}


        @keyframes hpPulse{{
          0%, 100% {{ filter: brightness(1); }}
          50% {{ filter: brightness(1.2); }}
        }}

        .stats{{
          font-size: 15px;
          margin: 10px 0;
          color: #aabbff;
          text-shadow: 0 1px 2px rgba(0, 0, 0, 0.8);
          position: relative;
          padding-left: 20px;
        }}

        .stats::before{{
          content: '✦';
          position: absolute;
          left: 0;
          color: var(--mlbb-accent);
          font-size: 12px;
        }}

        .lab-name{{
          font-weight: bold;
          font-size: 22px;
          margin-top: 18px;
          text-shadow: 2px 2px 5px rgba(0, 0, 0, 0.9);
          color: orange;
          font-family: 'MedievalSharp', cursive;
          letter-spacing: 1.5px;
          position: relative;
          display: inline-block;
        }}

        .lab-name::after{{
          content: '';
          position: absolute;
          bottom: -5px;
          left: 0;
          width: 100%;
          height: 2px;
          background: linear-gradient(90deg, transparent, var(--mlbb-primary), transparent);
          transform: scaleX(0);
          transition: transform 0.5s ease;
        }}

        .lab:hover .lab-name::after{{
          transform: scaleX(1);
        }}

        .narrator-box {{
          grid-area: narrator;
          text-align: center;
          padding: 25px;
          background: rgba(20, 25, 45, 0.8);
          border-radius: 18px;
          margin-bottom: 20px;
          box-shadow: 0 0 20px rgba(102, 51, 153, 0.5);
          border: 1px solid rgba(123, 104, 238, 0.4);
          position: relative;
          overflow: hidden;
          display: flex;
          justify-content: space-between;
          align-items: center;
        }}

        .narrator-lab-info {{
          display: flex;
          flex-direction: column;
          align-items: center;
          width: 30%;
        }}

        .narrator-lab-name {{
          font-weight: bold;
          font-size: 18px;
          text-shadow: 2px 2px 5px rgba(0, 0, 0, 0.9);
          color: orange;
          font-family: 'MedievalSharp', cursive;
          letter-spacing: 1px;
          margin-bottom: 8px;
        }}

        .narrator-lab-stats {{
          font-size: 14px;
          color: #aabbff;
          text-shadow: 0 1px 2px rgba(0, 0, 0, 0.8);
        }}

        #narrator-text {{
          font-size: 28px;
          font-weight: bold;
          color: white;
          text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.9);
          min-height: 80px;
          display: flex;
          align-items: center;
          justify-content: center;
          font-family: 'MedievalSharp', cursive;
          letter-spacing: 2px;
          position: relative;
          animation: textGlow 2s infinite alternate;
          width: 40%;
          padding: 0 15px;
        }}

        .lab{{
          display: none;
        }}


        .narrator-box::before{{
          content: '';
          position: absolute;
          top: 0;
          left: 0;
          right: 0;
          height: 4px;
          background: linear-gradient(90deg, 
            transparent, 
            var(--mlbb-primary), 
            var(--mlbb-secondary),
            transparent);
          animation: narratorGlow 3s infinite linear;
        }}

        @keyframes narratorGlow{{
          0% {{ background-position: -100% 0; }}
          100% {{ background-position: 200% 0; }}
        }}

        .narrator-box::after{{
          content: '';
          position: absolute;
          top: 6px;
          left: 6px;
          right: 6px;
          bottom: 6px;
          border: 1px solid rgba(123, 104, 238, 0.2);
          border-radius: 14px;
          pointer-events: none;
        }}
        
        @keyframes textGlow{{
          from {{ text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.9), 0 0 15px rgba(255, 255, 255, 0.5); }}
          to {{ text-shadow: 2px 2px 6px rgba(0, 0, 0, 0.9), 0 0 25px rgba(255, 255, 255, 0.8); }}
        }}

        .battle-log{{
          max-width: 1200px;
          margin: 25px auto;
          background: rgba(20, 25, 45, 0.7);
          padding: 25px;
          border-radius: 18px;
          max-height: 280px;
          overflow-y: auto;
          box-shadow: 0 0 20px rgba(102, 51, 153, 0.4);
          border: 1px solid rgba(123, 104, 238, 0.3);
          position: relative;
        }}

        .battle-log::before{{
          content: '';
          position: absolute;
          top: 0;
          left: 0;
          right: 0;
          bottom: 0;
          background: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100" viewBox="0 0 100 100"><path fill="rgba(123, 104, 238, 0.1)" d="M0,0 L100,0 L100,100 L0,100 Z" /></svg>');
          background-size: 50px;
          opacity: 0.1;
          pointer-events: none;
        }}

        .battle-log h3{{
          color: #7b68ee;
          text-align: center;
          border-bottom: 2px solid rgba(123, 104, 238, 0.5);
          padding-bottom: 12px;
          margin-top: 0;
          font-family: 'MedievalSharp', cursive;
          font-size: 22px;
          text-shadow: 0 2px 4px rgba(0, 0, 0, 0.8);
          position: relative;
        }}

        .battle-log h3::after{{
          content: '⚔️';
          position: absolute;
          right: 20px;
          animation: bounce 2s infinite;
        }}

        @keyframes bounce{{
          0%, 100% {{ transform: translateY(0) rotate(0deg); }}
          50% {{ transform: translateY(-5px) rotate(10deg); }}
        }}

        .battle-log-entry{{
          padding: 12px;
          margin: 10px 0;
          background: rgba(30, 35, 55, 0.5);
          border-radius: 10px;
          font-size: 16px;
          border-left: 4px solid #7b68ee;
          box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
          transition: transform 0.3s ease, box-shadow 0.3s ease;
          animation: logEntry 0.5s ease-out;
        }}

        @keyframes logEntry{{
          from {{ opacity: 0; transform: translateX(-20px); }}
          to {{ opacity: 1; transform: translateX(0); }}
        }}

        .battle-log-entry:hover{{
          transform: translateX(5px);
          box-shadow: 0 4px 12px rgba(0, 0, 0, 0.4);
        }}

        .rankings-section, .ratings-section{{
          max-width: 1200px;
          margin: 20px auto;
          background: rgba(20, 25, 45, 0.7);
          padding: 20px;
          border-radius: 18px;
          box-shadow: 0 0 25px rgba(102, 51, 153, 0.4);
          border: 1px solid rgba(123, 104, 238, 0.3);
          position: relative;
          overflow: hidden;
        }}

        .rankings-section::before, .ratings-section::before{{
          content: '';
          position: absolute;
          top: 0;
          left: 0;
          right: 0;
          height: 4px;
          background: linear-gradient(90deg, 
            transparent, 
            var(--mlbb-primary), 
            var(--mlbb-secondary),
            transparent);
          animation: sectionGlow 4s infinite linear;
        }}

        @keyframes sectionGlow{{
          0% {{ background-position: -100% 0; }}
          100% {{ background-position: 200% 0; }}
        }}

        .rankings-section h2, .ratings-section h2{{
          color: #9b59b6;
          text-align: center;
          border-bottom: 2px solid rgba(123, 104, 238, 0.5);
          padding-bottom: 18px;
          margin-top: 0;
          font-family: 'MedievalSharp', cursive;
          font-size: 28px;
          text-shadow: 0 3px 6px rgba(0, 0, 0, 0.8);
          position: relative;
        }}

        .rankings-section h2::after, .ratings-section h2::after{{
          content: '🏆';
          position: absolute;
          right: 20px;
          animation: spin 4s infinite linear;
        }}

        @keyframes spin{{
          from {{ transform: rotate(0deg); }}
          to {{ transform: rotate(360deg); }}
        }}

        .rankings-table{{
          width: 100%;
          border-collapse: separate;
          border-spacing: 0;
          margin-top: 25px;
          position: relative;
        }}

        .rankings-table th, .rankings-table td{{
          padding: 15px;
          text-align: left;
          border-bottom: 1px solid rgba(123, 104, 238, 0.3);
          position: relative;
        }}

        .rankings-table th{{
          background: rgba(123, 104, 238, 0.2);
          color: #7b68ee;
          font-family: 'MedievalSharp', cursive;
          font-size: 18px;
          text-shadow: 0 1px 2px rgba(0, 0, 0, 0.8);
        }}

        .rankings-table tr{{
          transition: transform 0.3s ease, background 0.3s ease;
        }}

        .rankings-table tr:hover{{
          background: rgba(123, 104, 238, 0.1);
          transform: translateX(5px);
        }}

        .rank-1{{ 
          color: var(--mlbb-gold); 
          font-weight: bold; 
          text-shadow: 0 0 8px rgba(255, 215, 0, 0.8);
          position: relative;
        }}

        .rank-1::before{{
          content: '👑';
          position: absolute;
          left: -25px;
          animation: bounce 2s infinite;
        }}

        .rank-2::before{{
          content: '🥈';
          position: absolute;
          left: -25px;
          animation: bounce 2s infinite;
        }}

        .rank-2{{ 
          color: var(--mlbb-silver); 
          font-weight: bold; 
          text-shadow: 0 0 8px rgba(192, 192, 192, 0.8);
        }}

        .rank-3::before{{
          content: '🥉';
          position: absolute;
          left: -25px;
          animation: bounce 2s infinite;
        }}

        .rank-3{{ 
          color: var(--mlbb-bronze); 
          font-weight: bold; 
          text-shadow: 0 0 8px rgba(205, 127, 50, 0.8);
        }}

        .controls{{
          text-align: center;
          margin: -150px 15px 15px 15px;
          position: relative;
        }}

        .controls::before{{
          content: '';
          position: absolute;
          top: -20px;
          left: 50%;
          transform: translateX(-50%);
          width: 100px;
          height: 3px;
          background: linear-gradient(90deg, transparent, var(--mlbb-primary), transparent);
        }}

        button{{
          background: linear-gradient(135deg, #6c5ce7, #8e44ad);
          color: white;
          border: none;
          padding: 15px 35px;
          border-radius: 35px;
          font-weight: bold;
          cursor: pointer;
          margin: 0 20px;
          transition: all 0.4s cubic-bezier(0.25, 0.8, 0.25, 1);
          font-family: 'Cinzel', serif;
          box-shadow: 0 8px 20px rgba(0, 0, 0, 0.4);
          text-shadow: 1px 1px 3px rgba(0, 0, 0, 0.8);
          position: relative;
          overflow: hidden;
          letter-spacing: 1px;
          animation: buttonGlow 3s infinite alternate;
        }}

        @keyframes buttonGlow{{
          from {{ box-shadow: 0 8px 20px rgba(0, 0, 0, 0.4), 0 0 15px rgba(108, 92, 231, 0.6); }}
          to {{ box-shadow: 0 8px 25px rgba(0, 0, 0, 0.5), 0 0 25px rgba(108, 92, 231, 0.8); }}
        }}

        button::before{{
          content: '';
          position: absolute;
          top: 0;
          left: -100%;
          width: 100%;
          height: 100%;
          background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
          transition: left 0.5s ease;
        }}

        button:hover{{
          transform: translateY(-5px) scale(1.05);
          box-shadow: 
            0 12px 25px rgba(0, 0, 0, 0.5),
            0 0 25px rgba(108, 92, 231, 0.8),
            var(--mlbb-glow);
        }}

        button:hover::before{{
          left: 100%;
        }}

        button:active{{
          transform: translateY(2px) scale(0.98);
          box-shadow: 0 4px 15px rgba(0, 0, 0, 0.4);
        }}

        .hidden{{
          display: none;
        }}

        .lab-left{{
          position: relative;
          z-index: 2;
        }}

        .lab-right{{
          position: relative;
          z-index: 2;
        }}

        @keyframes attack-left {{
          0% {{ transform: perspective(800px) rotateX(5deg) rotateY(0deg) translateX(0) translateZ(0); }}
          25% {{ transform: perspective(800px) rotateX(8deg) rotateY(-10deg) translateX(30px) translateZ(15px); }}
          50% {{ transform: perspective(800px) rotateX(12deg) rotateY(-5deg) translateX(50px) translateZ(25px); }}
          75% {{ transform: perspective(800px) rotateX(8deg) rotateY(5deg) translateX(20px) translateZ(10px); }}
          100% {{ transform: perspective(800px) rotateX(5deg) rotateY(0deg) translateX(0) translateZ(0); }}
        }}

        @keyframes attack-right {{
          0% {{ transform: perspective(800px) rotateX(5deg) rotateY(0deg) translateX(0) translateZ(0); }}
          25% {{ transform: perspective(800px) rotateX(8deg) rotateY(10deg) translateX(-30px) translateZ(15px); }}
          50% {{ transform: perspective(800px) rotateX(12deg) rotateY(5deg) translateX(-50px) translateZ(25px); }}
          75% {{ transform: perspective(800px) rotateX(8deg) rotateY(-5deg) translateX(-20px) translateZ(10px); }}
          100% {{ transform: perspective(800px) rotateX(5deg) rotateY(0deg) translateX(0) translateZ(0); }}
        }}

        @keyframes hit-flash{{
          0% {{ filter: brightness(1) contrast(1); }}
          25% {{ filter: brightness(2) contrast(2) drop-shadow(0 0 15px #9b59b6); }}
          50% {{ filter: brightness(2.5) contrast(2.5) drop-shadow(0 0 25px #9b59b6); }}
          75% {{ filter: brightness(2) contrast(2) drop-shadow(0 0 15px #9b59b6); }}
          100% {{ filter: brightness(1) contrast(1); }}
        }}

        @keyframes shake{{
          0% {{ transform: perspective(800px) rotateX(5deg) translateX(0); }}
          15% {{ transform: perspective(800px) rotateX(5deg) translateX(-8px); }}
          30% {{ transform: perspective(800px) rotateX(5deg) translateX(8px); }}
          45% {{ transform: perspective(800px) rotateX(5deg) translateX(-8px); }}
          60% {{ transform: perspective(800px) rotateX(5deg) translateX(8px); }}
          75% {{ transform: perspective(800px) rotateX(5deg) translateX(-5px); }}
          90% {{ transform: perspective(800px) rotateX(5deg) translateX(5px); }}
          100% {{ transform: perspective(800px) rotateX(5deg) translateX(0); }}
        }}

        .impact-effect{{
          position: absolute;
          width: 60px;
          height: 60px;
          background: radial-gradient(circle, 
            rgba(255, 77, 141, 0.9) 0%, 
            rgba(155, 89, 182, 0.7) 30%, 
            rgba(123, 104, 238, 0) 70%);
          border-radius: 50%;
          pointer-events: none;
          opacity: 0;
          z-index: 3;
          filter: blur(5px);
        }}

        .attacking-left {{
          animation: attack-left 0.6s cubic-bezier(0.25, 0.8, 0.25, 1);
          z-index: 4;
        }}

        .attacking-right {{
          animation: attack-right 0.6s cubic-bezier(0.25, 0.8, 0.25, 1);
          z-index: 4;
        }}

        .taking-hit {{
          animation: 
            hit-flash 0.4s ease-in-out, 
            shake 0.4s ease-in-out;
        }}

        .show-impact{{
          animation: show-impact 0.6s ease-out;
        }}

        @keyframes show-impact{{
          0% {{ opacity: 0; transform: scale(0.3); }}
          50% {{ opacity: 1; transform: scale(1.3); }}
          100% {{ opacity: 0; transform: scale(1.8); }}
        }}

        @keyframes winner-glow{{
          0% {{ 
            box-shadow: 0 0 15px gold;
            transform: scale(1) rotate(0deg);
          }}
          25% {{ 
            box-shadow: 0 0 25px gold;
            transform: scale(1.05) rotate(2deg);
          }}
          50% {{ 
            box-shadow: 0 0 35px gold;
            transform: scale(1.1) rotate(0deg);
          }}
          75% {{ 
            box-shadow: 0 0 25px gold;
            transform: scale(1.05) rotate(-2deg);
          }}
          100% {{ 
            box-shadow: 0 0 15px gold;
            transform: scale(1) rotate(0deg);
          }}
        }}

        .winner-glow {{
          animation: winner-glow 1.5s infinite;
          position: relative;
          z-index: 5;
        }}

        .winner-glow::before {{
          content: '';
          position: absolute;
          top: -10px;
          left: -10px;
          right: -10px;
          bottom: -10px;
          background: radial-gradient(circle, rgba(255, 215, 0, 0.2) 0%, transparent 70%);
          border-radius: 50%;
          animation: pulse 2s infinite;
          z-index: -1;
        }}

        .center-space {{
          grid-area: center-space;
          width: 200px;
          height: 200px;
          display: flex;
          justify-content: center;
          align-items: center;
          position: relative;
          z-index: 1;
        }}

        .center-space::before {{
          content: '';
          position: absolute;
          width: 150px;
          height: 150px;
          background: radial-gradient(circle, rgba(123, 104, 238, 0.3) 0%, rgba(123, 104, 238, 0) 70%);
          border-radius: 50%;
          animation: pulse 3s infinite;
          z-index: -1;
        }}

        .center-space::after {{
          content: '';
          position: absolute;
          font-size: 40px;
          filter: drop-shadow(0 0 5px rgba(123, 104, 238, 0.8));
        }}

        ::-webkit-scrollbar{{
          width: 10px;
        }}

        ::-webkit-scrollbar-track{{
          background: rgba(26, 26, 46, 0.6);
          border-radius: 5px;
        }}

        ::-webkit-scrollbar-thumb{{
          background: var(--mlbb-gradient);
          border-radius: 5px;
          box-shadow: inset 0 0 5px rgba(255, 255, 255, 0.2);
        }}

        ::-webkit-scrollbar-thumb:hover{{
          background: var(--mlbb-primary);
          box-shadow: inset 0 0 5px rgba(255, 255, 255, 0.3);
        }}

        *:focus{{
          outline: 2px solid var(--mlbb-accent);
          outline-offset: 3px;
          box-shadow: 0 0 10px var(--mlbb-accent);
        }}

        ::selection{{
          background: var(--mlbb-primary);
          color: white;
          text-shadow: none;
        }}

        .particles{{
          position: fixed;
          top: 0;
          left: 0;
          width: 100%;
          height: 100%;
          pointer-events: none;
          z-index: -1;
        }}

        .particle{{
          position: absolute;
          border-radius: 50%;
          background: var(--mlbb-primary);
          opacity: 0;
          animation: float 15s infinite linear;
        }}

        .particle:nth-child(1){{
          top: 20%;
          left: 10%;
          width: 3px;
          height: 3px;
          animation-delay: 0s;
          animation-duration: 20s;
        }}

        .particle:nth-child(2){{
          top: 60%;
          left: 80%;
          width: 5px;
          height: 5px;
          animation-delay: 2s;
          animation-duration: 25s;
        }}

        .particle:nth-child(3){{
          top: 40%;
          left: 30%;
          width: 2px;
          height: 2px;
          animation-delay: 4s;
          animation-duration: 18s;
        }}

        .particle:nth-child(4){{
          top: 80%;
          left: 50%;
          width: 4px;
          height: 4px;
          animation-delay: 6s;
          animation-duration: 22s;
        }}

        .particle:nth-child(5){{
          top: 10%;
          left: 70%;
          width: 3px;
          height: 3px;
          animation-delay: 8s;
          animation-duration: 19s;
        }}

        @keyframes float{{
          0% {{ opacity: 0; transform: translateY(0) translateX(0) rotate(0deg) scale(0.5); }}
          10% {{ opacity: 0.7; }}
          90% {{ opacity: 0.7; }}
          100% {{ opacity: 0; transform: translateY(-100vh) translateX(100vw) rotate(360deg) scale(1.5); }}
        }}
        
        @keyframes levelUp{{
          0% {{ opacity: 0; transform: scale(0.5); filter: brightness(1); }}
          50% {{ opacity: 1; transform: scale(1.2); filter: brightness(3); }}
          100% {{ opacity: 0; transform: scale(1.5); filter: brightness(1); }}
        }}

        .level-up-flash{{
          position: absolute;
          top: 0;
          left: 0;
          right: 0;
          bottom: 0;
          background: radial-gradient(circle, 
            rgba(255, 215, 0, 0.8) 0%, 
            transparent 70%);
          border-radius: inherit;
          animation: levelUp 1s ease-out;
          pointer-events: none;
          z-index: 10;
        }}

        .controls button {{
          margin: 0 20px;
          padding: 12px 24px;
          font-size: 16px;
          background: linear-gradient(135deg, #6c5ce7, #8e44ad);
          color: white;
          border: none;
          border-radius: 30px;
          cursor: pointer;
          transition: all 0.3s ease;
      }}

        .controls button:hover {{
            transform: translateY(-3px);
            box-shadow: 0 5px 15px rgba(0, 0, 0, 0.3);
        }}

        #monthly-rankings-section {{
            margin-top: 30px;
            padding: 40px;
            background: rgba(20, 25, 45, 0.8);
            border-radius: 10px;
            border: 1px solid rgba(123, 104, 238, 0.3);
        }}

        #monthly-rankings-section h2 {{
            text-align: center;
            color: #9b59b6;
            margin-bottom: 20px;
            font-family: 'MedievalSharp', cursive;
        }}

        .avatar-container {{
            position: relative;
            display: flex;
            flex-direction: column;
            align-items: center;
            width: 180px; 
        }}
          
        /* 3D Avatar Effect */
        .avatar-3d {{
            transform: perspective(800px) rotateY(0deg) rotateX(0deg);
            transition: transform 0.5s ease, box-shadow 0.5s ease;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
        }}
          
        .avatar-container:hover .avatar-3d {{
            transform: perspective(800px) rotateY(5deg) rotateX(5deg);
            box-shadow: 0 15px 40px rgba(123, 104, 238, 0.4);
        }}

        /* Enhanced 3D Weapon Styles */
        .weapon-container {{
          position: absolute;
          width: 80px;
          height: 80px;
          z-index: 9999;
          pointer-events: none;
          transform-origin: center center;
          bottom: 0;
        }}
          
        .weapon-left {{
          bottom: 60px;  
          right: -40px;
          transform: scale(1.2) rotate(-15deg);
        }}
          
        .weapon-right {{
          bottom: 60px;
          left  : -40px;
          transform: scale(1.2) rotate(-15deg);
        }}
        
        /* Weapon SLASH animations */
        @keyframes weapon-slash-left {{
          0% {{ 
            transform: scale(1.2) rotate(-15deg) translateX(0) translateY(0);
            filter: drop-shadow(2px 4px 6px rgba(0, 0, 0, 0.7));
          }}
          25% {{ 
            transform: scale(1.4) rotate(-45deg) translateX(-30px) translateY(-20px);
            filter: drop-shadow(0 0 20px rgba(255, 215, 0, 0.9)) brightness(1.5);
          }}
          50% {{ 
            transform: scale(1.6) rotate(30deg) translateX(40px) translateY(10px);
            filter: drop-shadow(0 0 30px rgba(255, 0, 0, 0.8)) brightness(2);
          }}
          75% {{ 
            transform: scale(1.4) rotate(0deg) translateX(20px) translateY(-10px);
            filter: drop-shadow(0 0 15px rgba(255, 154, 139, 0.7)) brightness(1.3);
          }}
          100% {{ 
            transform: scale(1.2) rotate(-15deg) translateX(0) translateY(0);
            filter: drop-shadow(2px 4px 6px rgba(0, 0, 0, 0.7));
          }}
        }}

        @keyframes weapon-slash-right {{
          0% {{ 
            transform: scale(1.2) rotate(15deg) translateX(0) translateY(0);
            filter: drop-shadow(2px 4px 6px rgba(0, 0, 0, 0.7));
          }}
          25% {{ 
            transform: scale(1.4) rotate(45deg) translateX(30px) translateY(-20px);
            filter: drop-shadow(0 0 20px rgba(255, 215, 0, 0.9)) brightness(1.5);
          }}
          50% {{ 
            transform: scale(1.6) rotate(-30deg) translateX(-40px) translateY(10px);
            filter: drop-shadow(0 0 30px rgba(255, 0, 0, 0.8)) brightness(2);
          }}
          75% {{ 
            transform: scale(1.4) rotate(0deg) translateX(-20px) translateY(-10px);
            filter: drop-shadow(0 0 15px rgba(255, 154, 139, 0.7)) brightness(1.3);
          }}
          100% {{ 
            transform: scale(1.2) rotate(15deg) translateX(0) translateY(0);
            filter: drop-shadow(2px 4px 6px rgba(0, 0, 0, 0.7));
          }}
        }}

        /* Apply slash animations */
        .slashing-left {{
          animation: weapon-slash-left 0.4s cubic-bezier(0.4, 0, 0.2, 1) forwards;
        }}

        .slashing-right {{
          animation: weapon-slash-right 0.4s cubic-bezier(0.4, 0, 0.2, 1) forwards;
        }}      
          
        /* Add a glow effect when attacking */
        @keyframes weapon-glow {{
            0% {{ filter: drop-shadow(2px 4px 6px rgba(0, 0, 0, 0.7)); }}
            50% {{ filter: drop-shadow(0 0 15px rgba(255, 215, 0, 0.8)); }}
            100% {{ filter: drop-shadow(2px 4px 6px rgba(0, 0, 0, 0.7)); }}
        }}
          
        .attacking-left .weapon-container,
        .attacking-right .weapon-container {{
            animation: weapon-swing-left 0.6s cubic-bezier(0.25, 0.8, 0.25, 1), 
                      weapon-glow 0.6s ease-in-out;
        }}
        .bonus-notice {{
          position: absolute;
          bottom: 10px;
          right: 10px;
          color: #ffd700;
          font-size: 12px;
          font-weight: bold;
          text-align: right;
          text-shadow: 1px 1px 2px black;
      }}
        
      </style>
    </head>
    <body>
       <div id="arena">
        <div class="narrator-box">
          <div class="narrator-lab-info" id="narrator-labA-info">
            <div id="narrator-labA-name" class="narrator-lab-name">Waiting...</div>
            <div id="narrator-labA-cv" class="narrator-lab-stats">CV: -</div>
            <div id="narrator-labA-ratio" class="narrator-lab-stats">Ratio: -</div>
          </div>
          
          <div id="narrator-text">Celestia Battlegrounds</div>
          
          <div class="narrator-lab-info" id="narrator-labB-info">
            <div id="narrator-labB-name" class="narrator-lab-name">Waiting...</div>
            <div id="narrator-labB-cv" class="narrator-lab-stats">CV: -</div>
            <div id="narrator-labB-ratio" class="narrator-lab-stats">Ratio: -</div>
          </div>
        </div>
        
        <div class="avatar-area">
          <div class="avatar-container" id="avatar-container-A">
            <img id="labA-avatar" class="avatar" src="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='180' height='180'%3E%3Crect width='180' height='180' fill='%234a69bd'/%3E%3C/svg%3E" alt="">
            <div class="avatar-hp-bar"><div id="labA-hp" class="avatar-hp-fill"></div></div>
            <div id="weapon-container-A" class="weapon-container weapon-left"></div>
          </div>

          <div class="avatar-container" id="avatar-container-B">
            <img id="labB-avatar" class="avatar" src="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='180' height='180'%3E%3Crect width='180' height='180' fill='%234a69bd'/%3E%3C/svg%3E" alt="">
            <div class="avatar-hp-bar"><div id="labB-hp" class="avatar-hp-fill"></div></div>
            <div id="weapon-container-B" class="weapon-container weapon-right"></div>
          </div>
        </div>
      </div>

        <div class="lab lab-left">
        </div>
        <div class="center-space"></div>
        <div class="lab lab-right">
        </div>
      </div>

      <div class="controls">
        <button onclick="startBattles()">🎥 Watch Battle</button>
      </div> 
      <!--
      <audio id="cheer-sound">
        <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
      </audio>
      -->
      <div class="battle-log">
        <h3>Chronicle of Battles</h3>
        <div id="battle-log-entries"></div>
      </div>

      <div class="bonus-notice">
        Bonus awaits those who <br> achieve the target CV & Ratio!
      </div>

      <div id="rankings-section" class="rankings-section hidden">
        <h2>ANCIENT SCROLLS OF POWER</h2>
        <div id="rankings-container"></div>
      </div>

      <div id="monthly-final-section" class="rankings-section hidden">
        <h2>MONTHLY CHAMPIONS</h2>
        <div id="monthly-final-container"></div>
      </div>

      <script>
        const battleLogs = {battle_logs_json};
        const monthlyRankings = {monthly_rankings_json};
        const labRatings = {lab_ratings_json};
        const avatarMap = {avatar_map_json}; 
        const DEFAULT_AVATAR = "{default_avatar_data_uri}";
        const narrationPhrases = {json.dumps(narration_phrases)};
        const submissions = {submission_json};
        const avatarNameMap = {avatar_name_map_json};
        const autoPlay = {str(auto_play).lower()};  
        const monthlyFinalData = {monthly_final_json};
        const userRole = "{user_role}";
        const userLab = "{user_lab or ''}";
        const selectedMonths = {selected_months_json};
        const showAllData = {show_all_data_js};

        // --- MONTH FILTERING FUNCTION ---
        function filterDataByMonths(data) {{
            if (showAllData || !selectedMonths || selectedMonths.length === 0) {{
                return data;
            }}
            return data.filter(item => selectedMonths.includes(item.month));
        }}

        // --- APPLY FILTERS TO ALL DATA ---
        const filteredBattleLogs = filterDataByMonths(battleLogs);
        const filteredMonthlyRankings = filterDataByMonths(monthlyRankings);
        const filteredMonthlyFinalData = filterDataByMonths(monthlyFinalData);
        const filteredSubmissions = filterDataByMonths(submissions);

        // Display filter info
        if (selectedMonths && selectedMonths.length > 0 && !showAllData) {{
            console.log(`🎯 Displaying data for months: ${{selectedMonths.join(', ')}}`);
            // You can also show this message in the UI
            document.getElementById('narrator-text').innerText = `Battles for: ${{selectedMonths.join(', ')}}`;
        }}
        
        let currentBattleIndex = 0;
        let isAutoPlaying = autoPlay;
        let isPaused = false;

        // Auto-start battles with countdown if autoPlay is true
        if (autoPlay) {{
            showCountdown();
        }}

        function getDisplayName(labName) {{
          return avatarNameMap[labName] || labName;
        }}
        
        function showCountdown() {{
          const countdownOverlay = document.createElement('div');
          countdownOverlay.className = 'countdown-overlay';
          countdownOverlay.innerHTML = '<div class="countdown-text">3</div>';
          document.body.appendChild(countdownOverlay);
          
          let count = 3;
          const countdown = setInterval(() => {{
              count--;
              if (count > 0) {{
                  countdownOverlay.innerHTML = '<div class="countdown-text">' + count + '</div>';
              }} else {{
                  clearInterval(countdown);
                  countdownOverlay.innerHTML = '<div class="countdown-text">GO!</div>';
                  
                  // Play cheer sound when countdown finishes
                  // const cheer = document.getElementById("cheer-sound");
                  // cheer.volume = 0.5; // Set appropriate volume
                  //cheer.play();
                  
                  // Remove overlay after a brief delay
                  setTimeout(() => {{
                      document.body.removeChild(countdownOverlay);
                      
                      // Start battles after countdown
                      setTimeout(() => {{
                          startBattles();
                      }}, 500);
                  }}, 800); // Keep "GO!" visible for 800ms
              }}
          }}, 1000);
        }}

        // Add this to your JavaScript section
        function adjustLayoutForScreenSize() {{
          const isMobile = window.innerWidth <= 768;
          const controlsDiv = document.querySelector('.controls');
          
          if (isMobile) {{
            // Stack buttons vertically on mobile
            controlsDiv.style.flexDirection = 'column';
            controlsDiv.style.alignItems = 'center';
            
            const buttons = controlsDiv.querySelectorAll('button');
            buttons.forEach(button => {{
              button.style.margin = '10px 0';
              button.style.width = '80%';
              button.style.maxWidth = '250px';
            }});
          }} else {{
            // Arrange buttons horizontally on desktop/tablet
            controlsDiv.style.flexDirection = 'row';
            controlsDiv.style.alignItems = 'center';
            
            const buttons = controlsDiv.querySelectorAll('button');
            buttons.forEach(button => {{
              button.style.margin = '0 20px';
              button.style.width = 'auto';
            }});
          }}
        }}

        // Call on load and resize
        window.addEventListener('load', adjustLayoutForScreenSize);
        window.addEventListener('resize', adjustLayoutForScreenSize);


        function showMonthlyFinal() {{
          console.log("Show Monthly Final clicked");
          console.log("Monthly Final Data:", filteredMonthlyFinalData);
          
          if (!filteredMonthlyFinalData || filteredMonthlyFinalData.length === 0) {{
              alert("No monthly final data available!");
              return;
          }}
          
          document.getElementById('monthly-final-section').classList.remove('hidden');
          renderMonthlyFinal();
          document.getElementById('monthly-final-section').scrollIntoView({{behavior: 'smooth'}});
      }}
        
        function renderMonthlyFinal() {{
          const container = document.getElementById('monthly-final-container');
          container.innerHTML = '';
          
          console.log("Monthly Final Data:", filteredMonthlyFinalData);
          
          if (!filteredMonthlyFinalData || filteredMonthlyFinalData.length === 0) {{
              container.innerHTML = '<p>No monthly final data available.</p>';
              return;
          }}
          
          if (monthlyFinalData.length > 0) {{
              console.log("First item keys:", Object.keys(monthlyFinalData[0]));
          }}
          
          const groupedByMonth = {{}};
          filteredMonthlyFinalData.forEach(row => {{
              const month = row.month;
              if (!groupedByMonth[month]) {{
                  groupedByMonth[month] = [];
              }}
              groupedByMonth[month].push(row);
          }});
          
          for (const [month, rankings] of Object.entries(groupedByMonth)) {{
              const table = document.createElement('table');
              table.className = 'rankings-table';
              
              const thead = document.createElement('thead');
              thead.innerHTML = `
                  
                  <tr colspan="3" style="text-align:center;">
                      <th>Rank</th>
                      <th>Lab</th>
                      <th>Monthly Final Elo</th>
                  </tr>
              `;
              table.appendChild(thead);
              
              const tbody = document.createElement('tbody');
              rankings.sort((a, b) => a.lab_rank - b.lab_rank).forEach(row => {{
                  const tr = document.createElement('tr');
                  tr.innerHTML = `
                    <td class="rank-${{row.lab_rank}}">${{row.lab_rank}}</td>
                    <td>${{getDisplayName(row.lab)}}</td>
                    <td>${{row.monthly_final_elo}}</td>
                  `;
                  tbody.appendChild(tr);
              }});
              
              table.appendChild(tbody);
              container.appendChild(table);
              container.appendChild(document.createElement('br'));
          }}
      }}
              
        const controlsDiv = document.querySelector('.controls');
        const monthlyFinalButton = document.createElement('button');
        monthlyFinalButton.textContent = '🏆 Monthly Final'; 
        monthlyFinalButton.onclick = showMonthlyFinal;
        controlsDiv.appendChild(monthlyFinalButton); 

        // Initialize 3D weapons
         function initWeapons() {{
          console.log("Initializing weapons...");
  
          // Check if Three.js is loaded
          if (typeof THREE === 'undefined') {{
            console.error("Three.js not loaded!");
            return;
          }}
         
          // Create weapons for each avatar
          createWeapon('weapon-container-A', 'sword');
          createWeapon('weapon-container-B', 'axe');
        }}

        function createWeapon(containerId, type) {{
          const container = document.getElementById(containerId);
          if (!container) return;
          
          const width = 80;
          const height = 80;
          
          // Create scene
          const scene = new THREE.Scene();
          
          // Create camera
          const camera = new THREE.PerspectiveCamera(40, width / height, 0.1, 1000);
          camera.position.z = 6;
          camera.position.y = 1;
          
          // Create renderer with better quality
          const renderer = new THREE.WebGLRenderer({{ 
              alpha: true,
              antialias: true 
          }});
          renderer.setSize(width, height);
          renderer.setClearColor(0x000000, 0);
          renderer.setPixelRatio(window.devicePixelRatio);
          container.appendChild(renderer.domElement);
          
          // Add enhanced lighting
          const ambientLight = new THREE.AmbientLight(0xffffff, 0.6);
          scene.add(ambientLight);

          const directionalLight = new THREE.DirectionalLight(0xffffff, 1.2);
          directionalLight.position.set(5, 8, 5);
          scene.add(directionalLight);

          const pointLight = new THREE.PointLight(0xff6600, 1.5, 100);
          pointLight.position.set(0, 3, 5);
          scene.add(pointLight);

          // Add combat-style lighting
          const combatLight = new THREE.PointLight(0xaa0000, 0.8, 50);
          combatLight.position.set(-5, 2, 3);
          scene.add(combatLight);

          const steelLight = new THREE.PointLight(0x3333ff, 0.6, 50);
          steelLight.position.set(5, 2, 3);
          scene.add(steelLight);
          
          // Create weapon based on type
          let weapon;
          if (type === 'axe') {{
              // Create a combat battle axe
              const handleGeometry = new THREE.CylinderGeometry(0.15, 0.2, 3.5, 16);
              const handleMaterial = new THREE.MeshPhongMaterial({{ 
                  color: "#00CED1", 
                  shininess: 20,
                  emissive: 0x000000
              }});
              const handle = new THREE.Mesh(handleGeometry, handleMaterial);
              
              // Add metal rings to handle
              const ringGeometry = new THREE.TorusGeometry(0.2, 0.04, 16, 32);
              const ringMaterial = new THREE.MeshPhongMaterial({{ 
                  color: 0xffffff, 
                  shininess: 80
              }});
              
              for (let i = 0; i < 4; i++) {{
                  const ring = new THREE.Mesh(ringGeometry, ringMaterial);
                  ring.position.y = -1 + i * 0.6;
                  ring.rotation.x = Math.PI / 2;
                  handle.add(ring);
              }}
              
              const bladeGeometry = new THREE.CylinderGeometry(0, 1.4, 0.3, 5);
              const bladeMaterial = new THREE.MeshPhongMaterial({{ 
                  color: "#C0C0C0", 
                  shininess: 100,
                  specular: 0x666666,
                  emissive: 0x222222
              }});
              const blade = new THREE.Mesh(bladeGeometry, bladeMaterial);
              blade.position.y = 2;
              blade.rotation.x = Math.PI / 2;
              
              // Add combat edge to blade
              const bladeEdgeGeometry = new THREE.CylinderGeometry(0, 1.5, 0.06, 5);
              const bladeEdgeMaterial = new THREE.MeshPhongMaterial({{ 
                  color: "#8A2BE2", 
                  shininess: 100,
                  emissive: 0x440000,
                  transparent: true,
                  opacity: 0.9
              }});
              const bladeEdge = new THREE.Mesh(bladeEdgeGeometry, bladeEdgeMaterial);
              bladeEdge.position.y = 2;
              bladeEdge.rotation.x = Math.PI / 2;
              bladeEdge.position.z = 0.08;
              
              const spikeGeometry = new THREE.CylinderGeometry(0, 0.8, 0.3, 5);
              const spikeMaterial = new THREE.MeshPhongMaterial({{ 
                  color: "#FF1493", 
                  shininess: 100,
                  emissive: 0x222222
              }});
              
              const spike = new THREE.Mesh(spikeGeometry, spikeMaterial);
              spike.position.y = 2;
              spike.position.x = -0.8;
              spike.rotation.x = Math.PI / 2;
              spike.rotation.z = Math.PI;
              
              // Add combat edge to spike
              const spikeEdgeGeometry = new THREE.CylinderGeometry(0, 0.9, 0.06, 5);
              const spikeEdgeMaterial = new THREE.MeshPhongMaterial({{ 
                  color: "#4682B4", 
                  shininess: 100,
                  emissive: 0x440000,
                  transparent: true,
                  opacity: 0.9
              }});
              const spikeEdge = new THREE.Mesh(spikeEdgeGeometry, spikeEdgeMaterial);
              spikeEdge.position.y = 2;
              spikeEdge.position.x = -0.8;
              spikeEdge.rotation.x = Math.PI / 2;
              spikeEdge.rotation.z = Math.PI;
              spikeEdge.position.z = 0.08;
              
              const connectorGeometry = new THREE.BoxGeometry(0.5, 0.5, 0.5);
              const connectorMaterial = new THREE.MeshPhongMaterial({{ 
                  color: "#4682B4", 
                  shininess: 50,
                  emissive: 0x330000
              }});
              const connector = new THREE.Mesh(connectorGeometry, connectorMaterial);
              connector.position.y = 2;
              
              const connectorGemGeometry = new THREE.SphereGeometry(0.2, 16, 16);
              const connectorGemMaterial = new THREE.MeshPhongMaterial({{ 
                  color: "#8A2BE2", 
                  shininess: 100,
                  specular: 0x660000,
                  emissive: 0x220000
              }});
              const connectorGem = new THREE.Mesh(connectorGemGeometry, connectorGemMaterial);
              connectorGem.position.y = 2;
              connectorGem.position.z = 0.4;
              
              weapon = new THREE.Group();
              weapon.add(handle);
              weapon.add(blade);
              weapon.add(bladeEdge);
              weapon.add(spike);
              weapon.add(spikeEdge);
              weapon.add(connector);
              weapon.add(connectorGem);
              
          }} else {{
              // Create combat sword
              const handleGeometry = new THREE.CylinderGeometry(0.3, 0.3, 1.2, 16);
              const handleMaterial = new THREE.MeshPhongMaterial({{ 
                  color: "#FF4500", 
                  shininess: 60,
                  specular: 0x333333
              }});
              const handle = new THREE.Mesh(handleGeometry, handleMaterial);
              handle.position.y = -0.8;
              
              const spiralGeometry = new THREE.TorusGeometry(0.32, 0.02, 16, 32);
              const spiralMaterial = new THREE.MeshPhongMaterial({{ 
                  color: "#FFD700",
              }});
              for (let i = 0; i < 5; i++) {{
                  const spiral = new THREE.Mesh(spiralGeometry, spiralMaterial);
                  spiral.position.y = -0.8 + i * 0.2;
                  spiral.rotation.x = Math.PI / 2;
                  handle.add(spiral);
              }}
              
              const guardGeometry = new THREE.CylinderGeometry(0.6, 0.6, 0.15, 6);
              const guardMaterial = new THREE.MeshPhongMaterial({{ 
                  color: "#E6E6FA", 
                  shininess: 100,
                  specular: 0x333333
              }});
              const guard = new THREE.Mesh(guardGeometry, guardMaterial);
              guard.position.y = -0.15;
              
              const gemGeometry = new THREE.SphereGeometry(0.12, 16, 16);
              const gemMaterial = new THREE.MeshPhongMaterial({{ 
                  color: "#808080", 
                  shininess: 100,
                  specular: 0x660000,
                  emissive: 0x220000
              }});
              
              for (let i = 0; i < 6; i++) {{
                  const angle = (i / 6) * Math.PI * 2;
                  const gem = new THREE.Mesh(gemGeometry, gemMaterial);
                  gem.position.set(Math.cos(angle) * 0.5, -0.15, Math.sin(angle) * 0.5);
                  guard.add(gem);
              }}
              
              const bladeGeometry = new THREE.CylinderGeometry(0.08, 0.5, 4, 16);
              const bladeMaterial = new THREE.MeshPhongMaterial({{ 
                  color: "#ffffff", 
                  shininess: 120,
                  specular: 0x666666,
                  emissive: 0x222222
              }});
              const blade = new THREE.Mesh(bladeGeometry, bladeMaterial);
              blade.position.y = 1.8;
              
              const runeGeometry = new THREE.BoxGeometry(0.3, 0.08, 0.04);
              const runeMaterial = new THREE.MeshPhongMaterial({{ 
                  color: "#FFD700", 
                  shininess: 100,
                  emissive: 0x330000,
                  transparent: true,
                  opacity: 0.9
              }});
              
              const rune1 = new THREE.Mesh(runeGeometry, runeMaterial);
              rune1.position.set(0, 2.2, 0.09);
              rune1.rotation.z = Math.PI / 4;
              
              const rune2 = new THREE.Mesh(runeGeometry, runeMaterial);
              rune2.position.set(0, 3, 0.09);
              rune2.rotation.z = -Math.PI / 4;
              
              const pommelGeometry = new THREE.SphereGeometry(0.3, 32, 32);
              const pommelMaterial = new THREE.MeshPhongMaterial({{ 
                  color: "#1E90FF",
                  shininess: 100,
                  specular: 0x333333
              }});
              const pommel = new THREE.Mesh(pommelGeometry, pommelMaterial);
              pommel.position.y = -1.5;
              
              const pommelGemGeometry = new THREE.SphereGeometry(0.18, 16, 16);
              const pommelGemMaterial = new THREE.MeshPhongMaterial({{ 
                  color: "#1E90FF", 
                  shininess: 100,
                  specular: 0x660000,
                  emissive: 0x220000
              }});
              const pommelGem = new THREE.Mesh(pommelGemGeometry, pommelGemMaterial);
              pommelGem.position.y = -1.5;
              pommelGem.position.z = 0.25;
              
              weapon = new THREE.Group();
              weapon.add(handle);
              weapon.add(guard);
              weapon.add(blade);
              weapon.add(rune1);
              weapon.add(rune2);
              weapon.add(pommel);
              weapon.add(pommelGem);
          }}
          
          // Position weapon appropriately for each side
          if (containerId === 'weapon-container-A') {{
              weapon.rotation.x = -Math.PI / 6;
              weapon.rotation.y = Math.PI / 8;
              weapon.rotation.z = Math.PI / 12;
          }} else {{
              weapon.rotation.x = -Math.PI / 6;
              weapon.rotation.y = -Math.PI / 8;
              weapon.rotation.z = -Math.PI / 12;
          }}
          
          scene.add(weapon);

          container.weaponGroup = weapon;
          container.scene = scene;
          container.camera = camera;
          container.renderer = renderer;

          function render() {{
            renderer.render(scene, camera);
          }}

          render();
            
          window.addEventListener('resize', () => {{
              const newWidth = container.offsetWidth;
              const newHeight = container.offsetHeight;
              renderer.setSize(newWidth, newHeight);
              camera.aspect = newWidth / newHeight;
              camera.updateProjectionMatrix();
              render();
          }});

          function animate() {{
            requestAnimationFrame(animate);
            
            if (weapon) {{
              weapon.rotation.y += 0.005;
              weapon.position.y = Math.sin(Date.now() * 0.002) * 0.1;
            }}
            
            render();
          }}
          animate();

            renderer.domElement.addEventListener("webglcontextlost", function (event) {{
              event.preventDefault();
              console.warn("⚠️ WebGL context lost!");
            }});

            renderer.domElement.addEventListener("webglcontextrestored", function () {{
              console.log("✅ WebGL context restored, reloading scene...");
              createWeapon(containerId, type); // re-initialize weapon for this container
        }});
        }}

        function triggerWeaponSlash(attackerSide) {{
              const weaponContainer = attackerSide === 'left' ? 
                document.getElementById('weapon-container-A') : 
                document.getElementById('weapon-container-B');
              
              if (!weaponContainer || !weaponContainer.weaponGroup) return;
              
              weaponContainer.classList.remove('slashing-left', 'slashing-right');
              
              void weaponContainer.offsetWidth;
              
              if (attackerSide === 'left') {{
                weaponContainer.classList.add('slashing-left');
              }} else {{
                weaponContainer.classList.add('slashing-right');
              }}
              
              setTimeout(() => {{
                weaponContainer.classList.remove('slashing-left', 'slashing-right');
              }}, 600);
        }}

        window.addEventListener('load', initWeapons)
        
        function getRandomNarration(attacker) {{
          const randomIndex = Math.floor(Math.random() * narrationPhrases.length);
          const attackerDisplay = getDisplayName(attacker);
          return narrationPhrases[randomIndex].replace("{{attacker}}", attackerDisplay);
        }}

        function updateLabStats(labData, isLabA) {{
          const prefix = isLabA ? "labA" : "labB";
          const narratorPrefix = isLabA ? "narrator-labA" : "narrator-labB";
          
          // Get the lab username 
          const labUsername = labData.lab || labData.Lab || "Unknown Lab";
          
          // Get the avatar path from the resolved avatar mapping
          const avatarPath = avatarMap[labUsername] || DEFAULT_AVATAR;
          
          // Get the display name (avatar name) instead of username
          const displayName = avatarNameMap[labUsername] || labUsername;
          
          document.getElementById(`${{narratorPrefix}}-name`).innerText = displayName;
          document.getElementById(`${{prefix}}-avatar`).src = avatarPath;
          
          // Apply 3D effect to avatar
          document.getElementById(`${{prefix}}-avatar`).classList.add('avatar-3d');
          
          // Only show CV and Ratio if they exist
          document.getElementById(`${{narratorPrefix}}-cv`).innerText = `CV: ${{labData.cv_value || 'N/A'}}`;
          document.getElementById(`${{narratorPrefix}}-ratio`).innerText = `Ratio: ${{labData.ratio_value || 'N/A'}}`;
        }}

        function calculateDamage(rating, opponentRating) {{
          // Calculate damage based on rating difference
          const diff = rating - opponentRating;
          // Normalize to 0-100 scale
          return Math.max(10, Math.min(90, 50 + (diff / 30)));
        }}

        function addBattleLog(message) {{
          const logEntry = document.createElement('div');
          logEntry.className = 'battle-log-entry';
          
          // Add month filter info to the first entry
          if (document.getElementById('battle-log-entries').children.length === 0) {{
              if (selectedMonths && selectedMonths.length > 0 && !showAllData) {{
                  const filterInfo = document.createElement('div');
                  filterInfo.className = 'battle-log-entry';
                  filterInfo.style.background = 'rgba(255, 215, 0, 0.2)';
                  filterInfo.innerHTML = `📅 <strong>Displaying battles for months:</strong> ${{selectedMonths.join(', ')}}`;
                  document.getElementById('battle-log-entries').appendChild(filterInfo);
              }}
          }}
          
          logEntry.innerHTML = message;
          document.getElementById('battle-log-entries').appendChild(logEntry);
          document.getElementById('battle-log-entries').scrollTop = document.getElementById('battle-log-entries').scrollHeight;
        }}

        function addRankingsButton() {{
          const controlsDiv = document.querySelector('.controls');
          // Remove existing rankings button if it exists
          const existingBtn = document.getElementById('show-rankings-btn');
          if (existingBtn) {{
              existingBtn.remove();
          }}
          
          const rankingsButton = document.createElement('button');
          rankingsButton.id = 'show-rankings-btn';
          rankingsButton.textContent = '📊 Show Rankings';
          rankingsButton.onclick = function() {{
              showRankings();
              document.getElementById('rankings-section').scrollIntoView({{behavior: 'smooth'}});
          }};
          
          // Insert after the Watch Battle button
          controlsDiv.appendChild(rankingsButton);
      }}

      // Call this when the page loads
      window.addEventListener('load', function() {{
          addRankingsButton();
      }});


        async function playBattle() {{
          if (currentBattleIndex >= battleLogs.length || isPaused) return;
          
          const battle = filteredBattleLogs[currentBattleIndex];
          
          // Find lab data from submissions
          const labAData = submissions.find(s => s.Lab === battle.lab_a) || {{lab: battle.lab_a}};
          const labBData = submissions.find(s => s.Lab === battle.lab_b) || {{lab: battle.lab_b}};

          // Update lab info 
          updateLabStats(labAData, true);
          updateLabStats(labBData, false);
          
          // Initial narration
          document.getElementById('narrator-text').innerText = `Round ${{battle.round_num}}: ${{getDisplayName(battle.lab_a)}} vs ${{getDisplayName(battle.lab_b)}}`;
          addBattleLog(`🔔 Round ${{battle.round_num}}: ${{getDisplayName(battle.lab_a)}} vs ${{getDisplayName(battle.lab_b)}}`);

          await sleep(1500);
          
          // Get avatar elements
          const avatarA = document.getElementById('labA-avatar');
          const avatarB = document.getElementById('labB-avatar');
          
          // Simulate battle sequence
          const attacks = [
            {{
              attacker: battle.lab_a, 
              target: battle.lab_b,
              damage: calculateDamage(battle.updated_rating_a, battle.updated_rating_b), 
              message: getRandomNarration(battle.lab_a),
              side: 'left' // Lab A attacks from left
            }},
            {{
              attacker: battle.lab_b, 
              target: battle.lab_a,
              damage: calculateDamage(battle.updated_rating_b, battle.updated_rating_a), 
              message: getRandomNarration(battle.lab_b),
              side: 'right' // Lab B attacks from right
            }}
          ];

          for (const attack of attacks) {{
            if (isPaused) break;
            
            const attackerDisplay = getDisplayName(attack.attacker);
            addBattleLog(`⚡ ${{attack.message.replace("{{attacker}}", attackerDisplay)}}`);
            
            // Trigger weapon slash animation
            triggerWeaponSlash(attack.side);
            
            // Apply animations to avatars
            if (attack.attacker === battle.lab_a) {{
              avatarA.classList.add('attacking-left');
              await sleep(300);
              avatarB.classList.add('taking-hit');
              createImpactEffect(avatarB, true);
            }} else {{
              avatarB.classList.add('attacking-right');
              await sleep(300);
              avatarA.classList.add('taking-hit');
              createImpactEffect(avatarA, false);
            }}
            
            // Apply damage to opponent
            const targetHp = attack.attacker === battle.lab_a ? 'labB-hp' : 'labA-hp';
            document.getElementById(targetHp).style.width = (100 - attack.damage) + '%';
            
            await sleep(700);
            
            // Remove animation classes
            avatarA.classList.remove('attacking-left', 'taking-hit');
            avatarB.classList.remove('attacking-right', 'taking-hit');
          }}

          
          // Announce winner
          if (battle.winner && battle.winner !== "Draw") {{
            const winnerDisplay = getDisplayName(battle.winner);
            const loserDisplay = getDisplayName(battle.loser);
            document.getElementById('narrator-text').innerText = `🏆 ${{winnerDisplay}} WINS!`;
            addBattleLog(`🎉 ${{winnerDisplay}} defeats ${{loserDisplay}}! ELO: ${{battle.updated_rating_a}} - ${{battle.updated_rating_b}}`);

            // Add winner glow effect to avatar
            if (battle.winner === battle.lab_a) {{
              avatarA.classList.add('winner-glow');
            }} else {{
              avatarB.classList.add('winner-glow');
            }}
          }} else {{
            const labADisplay = getDisplayName(battle.lab_a);
            const labBDisplay = getDisplayName(battle.lab_b);
            document.getElementById('narrator-text').innerText = `🤝 IT'S A DRAW!`;
            addBattleLog(`🤝 Draw between ${{labADisplay}} and ${{labBDisplay}}`);
          }}
          
          currentBattleIndex++;

          if (isAutoPlaying && !isPaused) {{
            await sleep(2000);
            
            // Remove winner glow before next battle
            avatarA.classList.remove('winner-glow');
            avatarB.classList.remove('winner-glow');

            // Check if this is the last battle 
            if (currentBattleIndex >= battleLogs.length) {{
              // All battles are finished - show rankings
              showRankings();
              document.getElementById('rankings-section').scrollIntoView({{behavior: 'smooth'}});
            }} else {{
              // Continue with next battle
              playBattle();
            }}
          }} else if (currentBattleIndex >= battleLogs.length) {{
            // Manual mode and all battles are finished - show rankings
            showRankings();
            document.getElementById('rankings-section').scrollIntoView({{behavior: 'smooth'}});
          }}
        }}

        function displayFilterInfo() {{
            if (selectedMonths && selectedMonths.length > 0 && !showAllData) {{
                const filterInfo = document.createElement('div');
                document.querySelector('.battle-log').insertBefore(filterInfo, document.querySelector('.battle-log h3'));
            }}
        }}

        // Call this when the page loads
        window.addEventListener('load', displayFilterInfo);

        function createImpactEffect(targetElement, isRightSide) {{
            const rect = targetElement.getBoundingClientRect();
            const impact = document.createElement('div');
            impact.className = 'impact-effect show-impact';

            impact.style.top = `${{rect.top + rect.height/2 - 20}}px`;
            impact.style.left = `${{rect.left + (isRightSide ? -20 : rect.width - 20)}}px`;

            document.body.appendChild(impact);

            setTimeout(() => {{
                document.body.removeChild(impact);
            }}, 500);
        }}
        
        function startBattles() {{
          resetDisplay();
          isAutoPlaying = true;
          isPaused = false;
          playBattle();
              // lepas countdown baru play audio
              // const cheer = document.getElementById("cheer-sound");
              // cheer.volume = 0.5;
              // cheer.play();
            }}
        
        function showRankings() {{
          document.getElementById('rankings-section').classList.remove('hidden');
          
          const container = document.getElementById('rankings-container');
          container.innerHTML = '';
          
          if (filteredMonthlyRankings.length === 0) {{
              container.innerHTML = '<p>No ranking data available for selected months.</p>';
              return;
          }}
          
          // Group by parameter and level
          const groupedData = {{}};
          filteredMonthlyRankings.forEach(row => {{
              const key = `${{row.parameter}}|${{row.level}}`;
              if (!groupedData[key]) {{
                  groupedData[key] = [];
              }}
              groupedData[key].push(row);
          }});

          // Create tables for each group
          for (const [key, rankings] of Object.entries(groupedData)) {{
              const [parameter, level] = key.split('|');
              
              // Group rankings by month
              const rankingsByMonth = {{}};
              rankings.forEach(row => {{
                  if (!rankingsByMonth[row.month]) {{
                      rankingsByMonth[row.month] = [];
                  }}
                  rankingsByMonth[row.month].push(row);
              }});
              
              // Sort months chronologically
              const sortedMonths = Object.keys(rankingsByMonth).sort((a, b) => {{
                  const monthOrder = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
                  
                  if (a.includes('-') && b.includes('-')) {{
                      // YYYY-MM format
                      return new Date(a) - new Date(b);
                  }} else {{
                     
                      const aIndex = monthOrder.indexOf(a);
                      const bIndex = monthOrder.indexOf(b);
                      return aIndex - bIndex;
                  }}
              }});
              
              sortedMonths.forEach((month, monthIndex) => {{
                  const currentMonthRankings = rankingsByMonth[month].sort((a, b) => a.ranking - b.ranking);
                  
                  const table = document.createElement('table');
                  table.className = 'rankings-table';
                  
                
                  const thead = document.createElement('thead');
                  thead.innerHTML = `
                      <tr>
                          <th colspan="7" style="text-align:center;">
                              ${{parameter}} - ${{level}} (Month: ${{month}})
                          </th>
                      </tr>
                      <tr>
                          <th>Rank</th>
                          <th>Lab</th>
                          <th>Elo Before Bonus</th>
                          <th>Bonus</th>
                          <th>Final Elo</th>
                          <th>Movement</th>
                      </tr>
                  `;
                  table.appendChild(thead);
                
                  
                  const tbody = document.createElement('tbody');
                  
                  currentMonthRankings.forEach(row => {{
                      const tr = document.createElement('tr');
                      
                      // Calculate movement
                      let movementHtml = '';
                      
                      if (monthIndex === 0) {{
                          // First month - show "NEW"
                          movementHtml = '<span style="color: #00ff00; font-weight: bold;">NEW</span>';
                      }} else {{
                          // Get previous month's ranking for this lab
                          const prevMonth = sortedMonths[monthIndex - 1];
                          const prevMonthRankings = rankingsByMonth[prevMonth];
                          const prevRank = prevMonthRankings.find(prev => prev.lab === row.lab);
                          
                          if (!prevRank) {{
                              // New lab this month
                              movementHtml = '<span style="color: #00ff00; font-weight: bold;">NEW</span>';
                          }} else {{
                              const movement = prevRank.ranking - row.ranking; 
                              
                              if (movement > 0) {{
                                  // Rank improved - green up arrow
                                  movementHtml = `<span style="color: #00ff00; font-weight: bold;">↑ ${{movement}}</span>`;
                              }} else if (movement < 0) {{
                                  // Rank dropped - red down arrow  
                                  movementHtml = `<span style="color: #ff4444; font-weight: bold;">↓ ${{Math.abs(movement)}}</span>`;
                              }} else {{
                                  movementHtml = `<span style="color: #ffff00; font-weight: bold;">-</span>`;
                              }}
                          }}
                      }}
                      
                      tr.innerHTML = `
                          <td class="rank-${{row.ranking}}">${{row.ranking}}</td>
                          <td>${{getDisplayName(row.lab)}}</td>
                          <td>${{row.elo_before_bonus}}</td>
                          <td>+${{row.bonus}}</td>
                          <td>${{row.final_elo}}</td>
                          <td>${{movementHtml}}</td>
                      `;
                      tbody.appendChild(tr);
                  }});
                  
                  table.appendChild(tbody);
                  container.appendChild(table);
                  container.appendChild(document.createElement('br'));
              }});
          }}
      }}   
        
        function resetDisplay() {{
          document.getElementById('labA-hp').style.width = '100%';
          document.getElementById('labB-hp').style.width = '100%';
          document.getElementById('narrator-text').innerText = 'Battle Arena';
          document.getElementById('battle-log-entries').innerHTML = '';
          
          // Reset narrator box info
          document.getElementById('narrator-labA-name').innerText = 'Waiting...';
          document.getElementById('narrator-labB-name').innerText = 'Waiting...';
          document.getElementById('narrator-labA-cv').innerText = 'CV: -';
          document.getElementById('narrator-labB-cv').innerText = 'CV: -';
          document.getElementById('narrator-labA-ratio').innerText = 'Ratio: -';
          document.getElementById('narrator-labB-ratio').innerText = 'Ratio: -';
          
          document.getElementById('labA-avatar').src = DEFAULT_AVATAR;
          document.getElementById('labB-avatar').src = DEFAULT_AVATAR;
          
          // Remove any animation classes
          document.getElementById('labA-avatar').classList.remove('attacking-left', 'taking-hit', 'winner-glow');
          document.getElementById('labB-avatar').classList.remove('attacking-right', 'taking-hit', 'winner-glow');
          
          document.getElementById('rankings-section').classList.add('hidden');
        }}

        
        function sleep(ms) {{
          return new Promise(resolve => setTimeout(resolve, ms));
        }}
        
      </script>
    </body>
    </html>
    """

def fetch_battle_logs():
    conn = get_db_connection()
    df = pd.read_sql("SELECT * FROM battle_logs ORDER BY id ASC", conn)
    conn.close()
    return df

def get_lab_rating(lab, parameter, level):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("""
        SELECT rating FROM lab_ratings 
        WHERE lab = %s AND parameter = %s AND level = %s
    """, (lab, parameter, level))
    
    result = cursor.fetchone()
    conn.close()
    
    return result['rating'] if result else 1500  


def update_lab_rating(lab, parameter, level, rating):
    """Update or insert a lab's rating for a parameter-level combination"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO lab_ratings (lab, parameter, level, rating) 
        VALUES (%s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE rating = %s, last_updated = CURRENT_TIMESTAMP
    """, (lab, parameter, level, rating, rating))
    
    conn.commit()
    conn.close()


def save_monthly_ranking(lab, parameter, level, month, elo_before_bonus, bonus, final_elo, ranking):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO monthly_rankings 
        (lab, parameter, level, month, elo_before_bonus, bonus, final_elo, ranking)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """, (lab, parameter, level, month, elo_before_bonus, bonus, final_elo, ranking))
    
    conn.commit()
    conn.close()

def get_previous_month_rankings(current_month):   
    if not current_month:
        return []
    
    try:
        if '-' in current_month:
            year, month_num = map(int, current_month.split('-'))
            if month_num == 1:
                prev_month = f"{year-1}-12"
            else:
                prev_month = f"{year}-{month_num-1:02d}"
        else:
            month_order = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                          'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
            current_year = datetime.now().year
            
            if current_month in month_order:
                month_index = month_order.index(current_month)
                if month_index == 0:
                    prev_month = f"{current_year-1}-Dec"
                else:
                    prev_month = f"{current_year}-{month_order[month_index-1]}"
            else:
                return []
        
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT lab, parameter, level, ranking 
            FROM monthly_rankings 
            WHERE month = %s
        """, (prev_month,))
        
        prev_rankings = cursor.fetchall()
        conn.close()
        
        return prev_rankings
        
    except Exception as e:
        print(f"Error getting previous month rankings: {e}")
        return []

def clear_battlelog():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM battle_logs")
    
    conn.commit()
    conn.close()

def simulate_fadzly_algorithm(df, selected_months=None, run_all_months=True):
    try:
        st.subheader("⚔️ LLKK Battle Arena")
        st.session_state.simulation_run_this_month = True

        st.session_state.simulation_months = selected_months if not run_all_months else None
        st.session_state.run_all_months = run_all_months

        original_df = df.copy()
        
        if selected_months and not run_all_months:
            df = df[df['Month'].isin(selected_months)]
            st.success(f"🎯 Simulation running for months: {', '.join(selected_months)}")
        else:
            st.success("🎯 Simulation running for ALL available months")
        
        if df.empty:
            st.error("❌ No data available for the selected months!")
            return

        df["CV(%)"] = pd.to_numeric(df["CV(%)"], errors="coerce")
        df["Ratio"] = pd.to_numeric(df["Ratio"], errors="coerce")
        df = df.dropna(subset=["n(QC)", "Working_Days"])

        # Initialize rating from database
        ratings = {}
        battle_logs = []
        rating_progression = []
        K = 32

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT lab, parameter, level, rating FROM lab_ratings")
        existing_ratings = cursor.fetchall()
        conn.close()
        
        # Create a dictionary for quick lookup
        rating_lookup = {}
        for row in existing_ratings:
            key = f"{row['lab']}_{row['parameter']}_{row['level']}"
            rating_lookup[key] = row['rating']
        
        month_order = {
            'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4, 'May': 5, 'Jun': 6,
            'Jul': 7, 'Aug': 8, 'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12
        }
        
        def get_month_value(month_str):
            if '-' in month_str:  
                return month_str
            else:  
                current_year = datetime.now().year
                month_num = month_order.get(month_str, 1)
                return f"{current_year}-{month_num:02d}"

        sorted_months = sorted(df["Month"].unique(), key=lambda x: get_month_value(x))
        
        all_labs = df["Lab"].unique().tolist()
        all_params = df["Parameter"].unique().tolist()
        all_levels = df["Level"].unique().tolist()

        months_to_process = df["Month"].unique()
        
        for month in sorted(months_to_process, key=lambda x: get_month_value(x)):
            monthly_data = df[df["Month"] == month]
            
            for (param, level), group in monthly_data.groupby(["Parameter", "Level"]):
                key_prefix = f"{param}_{level}"

                for lab in group["Lab"].unique():
                    lab_key = f"{lab}_{key_prefix}"
                    if lab_key not in ratings:
                        ratings[lab_key] = rating_lookup.get(lab_key, 1500)

            
                expected_labs = all_labs
                actual_labs = group["Lab"].unique()
                missing_labs = set(expected_labs) - set(actual_labs)
                
                for missing_lab in missing_labs:
                    missing_key = f"{missing_lab}_{key_prefix}"
                    if missing_key not in ratings:
                        ratings[missing_key] = rating_lookup.get(missing_key, 1500)
                    ratings[missing_key] -= 10
                    update_lab_rating(missing_lab, param, level, ratings[missing_key])

                labs = group.to_dict("records")
                
                # All pairings
                for lab1, lab2 in itertools.combinations(labs, 2):
                    labA, labB = lab1["Lab"], lab2["Lab"]
                    cvA, cvB = lab1.get("CV(%)"), lab2.get("CV(%)")
                    rA, rB = lab1.get("Ratio"), lab2.get("Ratio")

                    labA_key = f"{labA}_{key_prefix}"
                    labB_key = f"{labB}_{key_prefix}"

                  
                    if pd.isna(cvA) and pd.isna(cvB):
                        cv_score_A = cv_score_B = 0.5
                    elif pd.isna(cvA):
                        cv_score_A, cv_score_B = 0, 1
                    elif pd.isna(cvB):
                        cv_score_A, cv_score_B = 1, 0
                    elif cvA < cvB:
                        cv_score_A, cv_score_B = 1, 0
                    elif cvA > cvB:
                        cv_score_A, cv_score_B = 0, 1
                    else:
                        cv_score_A = cv_score_B = 0.5

                  
                    if pd.isna(rA) and pd.isna(rB):
                        ratio_score_A = ratio_score_B = 0.5
                    elif pd.isna(rA):
                        ratio_score_A, ratio_score_B = 0, 1
                    elif pd.isna(rB):
                        ratio_score_A, ratio_score_B = 1, 0
                    elif abs(rA - 1.0) < abs(rB - 1.0):
                        ratio_score_A, ratio_score_B = 1, 0
                    elif abs(rA - 1.0) > abs(rB - 1.0):
                        ratio_score_A, ratio_score_B = 0, 1
                    else:
                        ratio_score_A = ratio_score_B = 0.5

                    # Composite score
                    S_A = (cv_score_A + ratio_score_A) / 2
                    S_B = (cv_score_B + ratio_score_B) / 2

                    # ELO calculation
                    Ra, Rb = ratings[labA_key], ratings[labB_key]
                    Ea = 1 / (1 + 10 ** ((Rb - Ra) / 400))
                    Eb = 1 / (1 + 10 ** ((Ra - Rb) / 400))

                    ratings[labA_key] += K * (S_A - Ea)
                    ratings[labB_key] += K * (S_B - Eb)

                    update_lab_rating(labA, param, level, ratings[labA_key])
                    update_lab_rating(labB, param, level, ratings[labB_key])

                    updatedA = round(ratings[labA_key], 1)
                    updatedB = round(ratings[labB_key], 1)

                    battle_logs.append({
                        "Lab_A": labA, "Lab_B": labB,
                        "Parameter": param, "Level": level, "Month": month,
                        "CV_A": cvA, "CV_B": cvB,
                        "Ratio_A": rA, "Ratio_B": rB,
                        "Updated_Points_A": updatedA,
                        "Updated_Points_B": updatedB
                    })

                    if updatedA > updatedB:
                        winner, loser = labA, labB
                    elif updatedB > updatedA:
                        winner, loser = labB, labA
                    else:
                        winner, loser = "Draw", "Draw"

                    save_battle_log(
                      lab_a=labA,
                      lab_b=labB,
                      winner=winner,
                      loser=loser,
                      updated_rating_a=updatedA,
                      updated_rating_b=updatedB,
                      month=month  
                  )

                
                for lab in group["Lab"].unique():
                    lab_key = f"{lab}_{key_prefix}"
                    cv_value = group[group["Lab"] == lab]["CV(%)"].values[0]
                    ratio_value = group[group["Lab"] == lab]["Ratio"].values[0]

                    if not pd.isna(cv_value) and param in EFLM_TARGETS and cv_value <= EFLM_TARGETS[param]:
                        ratings[lab_key] += 5
                        update_lab_rating(lab, param, level, ratings[lab_key])

                    if not pd.isna(ratio_value) and ratio_value == 1.0:
                        ratings[lab_key] += 5
                        update_lab_rating(lab, param, level, ratings[lab_key])

                    update_lab_rating(lab, param, level, ratings[lab_key])

                # Record rating progression for this month
                for lab in group["Lab"].unique():
                    lab_key = f"{lab}_{key_prefix}"
                    rating_progression.append({
                        "Lab": lab,
                        "Parameter": param,
                        "Level": level,
                        "Month": month,
                        "Points": round(ratings[lab_key], 2)
                    })

        lab_elos = {}
        lab_counts = {}
        for key, elo in ratings.items():
            parts = key.split("_")
            lab = "_".join(parts[:-2])
            lab_elos[lab] = lab_elos.get(lab, 0) + elo
            lab_counts[lab] = lab_counts.get(lab, 0) + 1

        avatars = get_lab_avatars()

        summary_df = pd.DataFrame([{
            "Lab": lab,
            "Avatar": resolve_avatar_path(avatars.get(lab, "default.png")),
            "Final Points": round(lab_elos[lab] / lab_counts[lab], 2),
        } for lab in lab_elos]).sort_values(by="Final Points", ascending=False).reset_index(drop=True)

        summary_df["Medal"] = ""
        if len(summary_df) >= 1: summary_df.loc[0, "Medal"] = "🥇"
        if len(summary_df) >= 2: summary_df.loc[1, "Medal"] = "🥈"
        if len(summary_df) >= 3: summary_df.loc[2, "Medal"] = "🥉"
      
        summary_tables = []
        for month in months_to_process:
              month_data = df[df["Month"] == month]
              
              for (param, level), group in month_data.groupby(["Parameter", "Level"]):
                  rows = []
                  for lab in group["Lab"].unique():
                      lab_key = f"{lab}_{param}_{level}"
                      if lab_key in ratings:
                          current_rating = ratings[lab_key]
                          
                          cv = group[group["Lab"] == lab]["CV(%)"].values[0]
                          ratio_val = group[group["Lab"] == lab]["Ratio"].values[0]

                          cv_bonus = 5 if (not pd.isna(cv) and param in EFLM_TARGETS and cv <= EFLM_TARGETS[param]) else 0
                          ratio_bonus = 5 if (not pd.isna(ratio_val) and ratio_val == 1.0) else 0
                          bonus = cv_bonus + ratio_bonus

                          elo_before_bonus = current_rating - bonus
                          final_elo = current_rating

                          rows.append({
                              "Lab": lab,
                              "Test": param,
                              "Level": level,
                              "Month": month,
                              "Elo (before bonus)": round(elo_before_bonus, 1),
                              "Bonus": f"+{bonus}",
                              "Final Elo": round(final_elo, 1)
                          })

                  if rows:
                      df_table = pd.DataFrame(rows).sort_values("Final Elo", ascending=False).reset_index(drop=True)
                      df_table.index += 1
                      df_table.insert(0, "Rank", df_table.index)
                      summary_tables.append(df_table)

                      st.markdown(f"### {param} — {level} (Month: {month}) (target CV {EFLM_TARGETS.get(param, 'n/a')})")
                      st.dataframe(df_table)
                      
                      for _, row in df_table.iterrows():
                          save_monthly_ranking(
                              lab=row["Lab"],
                              parameter=param,
                              level=level,
                              month=row["Month"],
                              elo_before_bonus=row["Elo (before bonus)"],
                              bonus=int(row["Bonus"].replace("+", "")),
                              final_elo=row["Final Elo"],
                              ranking=row["Rank"]
                        )

        if summary_tables:
            monthly = pd.concat(summary_tables)
            monthly_test_avg = monthly.groupby(["Lab", "Test", "Month"])["Final Elo"].mean().reset_index()
            monthly_final = monthly_test_avg.groupby(["Lab", "Month"])["Final Elo"].mean().reset_index()
            for month in months_to_process:
                month_data = monthly_final[monthly_final["Month"] == month].copy()
                month_data = month_data.sort_values("Final Elo", ascending=False).reset_index(drop=True)
                month_data.index += 1
                month_data["Rank"] = month_data.index
                
                for _, row in month_data.iterrows():
                    save_monthly_final(
                        month=row["Month"],
                        lab=row["Lab"],
                        lab_rank=row["Rank"],
                        monthly_final_elo=round(row["Final Elo"], 2)
                    )
            
            st.markdown("### 🏆 Overall Monthly Ranking (Simulated Months)")
            pivot_data = monthly_final.pivot(index="Lab", columns="Month", values="Final Elo")
            st.dataframe(pivot_data)

        st.session_state.simulation_results = {
            "summary_tables": summary_tables,
        }  

        st.session_state["elo_history"] = ratings
        st.session_state["elo_progression"] = pd.DataFrame(rating_progression)
        st.session_state["fadzly_battles"] = summary_df

        st.success("✅ Battle simulation completed and saved to database.")
    except Exception:
        st.error("❌ An unexpected error occurred in the simulation:")
        st.code(traceback.format_exc())

def run():
    apply_sidebar_theme()
    st.markdown("""
    <style>
  /* Main Container */
  .main .block-container {
      background: linear-gradient(135deg, 
          #1a0033 0%, 
          #2d1b4e 25%, 
          #4a2c7a 50%, 
          #2d1b4e 75%, 
          #1a0033 100%
      );
      min-height: 100vh;
      padding: 2rem 1rem;
      position: relative;
      overflow-x: hidden;
  }

  /* Animated Background Elements */
  .main .block-container::before {
      content: '';
      position: fixed;
      top: 0;
      left: 0;
      width: 100%;
      height: 100%;
      background: 
          radial-gradient(circle at 20% 80%, rgba(138, 43, 226, 0.3) 0%, transparent 50%),
          radial-gradient(circle at 80% 20%, rgba(255, 215, 0, 0.2) 0%, transparent 50%),
          radial-gradient(circle at 40% 40%, rgba(65, 105, 225, 0.25) 0%, transparent 50%);
      pointer-events: none;
      z-index: -1;
      animation: backgroundPulse 8s ease-in-out infinite alternate;
  }

  @keyframes backgroundPulse {
      0% { opacity: 0.7; transform: scale(1); }
      100% { opacity: 1; transform: scale(1.05); }
  }

  /* Title Styling */
  h1 {
      font-family: 'Cinzel', serif !important;
      font-size: 85px !important;
      font-weight: 900 !important;
      text-align: center !important;
      background: linear-gradient(45deg, #8A2BE2, #6A0DAD, #4169E1, #8A2BE2) !important;
      background-size: 400% 400% !important;
      -webkit-background-clip: text !important;
      -webkit-text-fill-color: transparent !important;
      background-clip: text !important;
      animation: titleGlow 3s ease-in-out infinite alternate, titleShine 4s linear infinite !important;
      text-shadow: 0 0 30px rgba(138, 43, 226, 0.7) !important;
      margin-bottom: 2rem !important;
      position: relative !important;
  }

  @keyframes titleGlow {
      0% { filter: brightness(1) drop-shadow(0 0 10px rgba(138, 43, 226, 0.8)); }
      100% { filter: brightness(1.3) drop-shadow(0 0 25px rgba(65, 105, 225, 1)); }
  }

  @keyframes titleShine {
      0% { background-position: 0% 50%; }
      50% { background-position: 100% 50%; }
      100% { background-position: 0% 50%; }
  }

  /* Status Messages */
  .stAlert > div {
      border-radius: 15px !important;
      border: 2px solid transparent !important;
      background: linear-gradient(135deg, rgba(138, 43, 226, 0.15), rgba(65, 105, 225, 0.1)) !important;
      backdrop-filter: blur(10px) !important;
      padding: 1rem 1.5rem !important;
      font-family: 'Rajdhani', sans-serif !important;
      font-weight: 600 !important;
      font-size: 1.1rem !important;
      position: relative !important;
      overflow: hidden !important;
      color: #e0e0ff !important;
  }

  .stAlert > div::before {
      content: '';
      position: absolute;
      top: 0;
      left: -100%;
      width: 100%;
      height: 100%;
      background: linear-gradient(90deg, transparent, rgba(255, 215, 0, 0.3), transparent);
      animation: shimmer 2s infinite;
  }

  @keyframes shimmer {
      0% { left: -100%; }
      100% { left: 100%; }
  }

  /* Success Alert */
  div[data-testid="stAlert"][data-baseweb="notification"] > div {
      background: linear-gradient(135deg, rgba(138, 43, 226, 0.25), rgba(75, 0, 130, 0.15)) !important;
      border: 2px solid #8A2BE2 !important;
      box-shadow: 0 0 20px rgba(138, 43, 226, 0.4) !important;
  }

  /* Info Alert */
  .stAlert [role="alert"]:has([data-testid="stMarkdownContainer"]:contains("Lab View")) {
      background: linear-gradient(135deg, rgba(65, 105, 225, 0.25), rgba(30, 144, 255, 0.15)) !important;
      border: 2px solid #4169E1 !important;
      box-shadow: 0 0 20px rgba(65, 105, 225, 0.4) !important;
  }

  /* Warning Alert */
  .stAlert [role="alert"]:has([data-testid="stMarkdownContainer"]:contains("Please log in")) {
      background: linear-gradient(135deg, rgba(255, 215, 0, 0.25), rgba(255, 165, 0, 0.15)) !important;
      border: 2px solid #FFD700 !important;
      box-shadow: 0 0 20px rgba(255, 215, 0, 0.4) !important;
  }

  /* Avatar Container Enhancement */
  .avatar-container {
      width: 100px !important;
      height: 100px !important;
      border-radius: 50% !important;
      border: 1px solid #FFD700 !important;
      overflow: hidden !important;
      display: flex !important;
      align-items: center !important;
      justify-content: center !important;
      background: linear-gradient(135deg, #8A2BE2 0%, #4169E1 50%, #6A5ACD 100%) !important;
      box-shadow: 
          0 0 25px rgba(138, 43, 226, 0.6),
          inset 0 0 20px rgba(255, 215, 0, 0.2) !important;
      position: relative !important;
      animation: avatarGlow 2s ease-in-out infinite alternate !important;
  }

  .avatar-container::before {
      content: '';
      position: absolute;
      top: -4px;
      left: -4px;
      right: -4px;
      bottom: -4px;
      border-radius: 50%;
      background: linear-gradient(45deg, #FFD700, #8A2BE2, #4169E1, #FFD700);
      background-size: 400% 400%;
      animation: borderRotate 3s linear infinite;
      z-index: -1;
  }

  @keyframes avatarGlow {
      0% { box-shadow: 0 0 25px rgba(138, 43, 226, 0.6), inset 0 0 20px rgba(255, 215, 0, 0.2); }
      100% { box-shadow: 0 0 40px rgba(65, 105, 225, 0.8), inset 0 0 30px rgba(255, 215, 0, 0.3); }
  }

  @keyframes borderRotate {
      0% { background-position: 0% 50%; }
      50% { background-position: 100% 50%; }
      100% { background-position: 0% 50%; }
  }

  .avatar-img {
      width: 100% !important;
      height: 100% !important;
      object-fit: cover !important;
      border-radius: 50% !important;
  }

  /* User Info Text */
  p:contains("Logged in as") {
      font-family: 'Rajdhani', sans-serif !important;
      font-size: 1.2rem !important;
      font-weight: 700 !important;
      color: #FFD700 !important;
      text-shadow: 0 2px 10px rgba(255, 215, 0, 0.6) !important;
  }

  /* DataFrames */
  .stDataFrame {
      border-radius: 15px !important;
      overflow: hidden !important;
      box-shadow: 0 10px 30px rgba(138, 43, 226, 0.3) !important;
      border: 2px solid rgba(255, 215, 0, 0.4) !important;
      background: linear-gradient(135deg, rgba(138, 43, 226, 0.1), rgba(65, 105, 225, 0.05)) !important;
      backdrop-filter: blur(15px) !important;
  }

  .stDataFrame > div {
      background: transparent !important;
  }

  .stDataFrame table {
      background: linear-gradient(135deg, rgba(26, 0, 51, 0.9), rgba(45, 27, 78, 0.9)) !important;
      border-collapse: separate !important;
      border-spacing: 0 !important;
  }

  .stDataFrame th {
      background: linear-gradient(135deg, #FFD700, #8A2BE2, #4169E1) !important;
      color: #ffffff !important;
      font-family: 'Orbitron', monospace !important;
      font-weight: 700 !important;
      text-align: center !important;
      padding: 15px 10px !important;
      border: none !important;
      position: relative !important;
  }

  .stDataFrame th::after {
      content: '';
      position: absolute;
      bottom: 0;
      left: 0;
      width: 100%;
      height: 2px;
      background: linear-gradient(90deg, transparent, rgba(255, 215, 0, 0.8), transparent);
  }

  .stDataFrame td {
      background: rgba(45, 27, 78, 0.8) !important;
      color: #e0e0ff !important;
      font-family: 'Rajdhani', sans-serif !important;
      font-weight: 500 !important;
      padding: 12px 10px !important;
      border: 1px solid rgba(138, 43, 226, 0.3) !important;
      text-align: center !important;
      transition: all 0.3s ease !important;
  }

  .stDataFrame td:hover {
      background: rgba(138, 43, 226, 0.2) !important;
      color: #FFD700 !important;
      box-shadow: inset 0 0 15px rgba(255, 215, 0, 0.3) !important;
  }

  /* Buttons */
  .stButton > button {
      background: linear-gradient(135deg, #4169E1 0%, #8A2BE2 50%, #4169E1 100%) !important;
      border: 2px solid #8A2BE2 !important;
      color: white !important;
      font-family: 'Orbitron', monospace !important;
      font-weight: 700 !important;
      font-size: 1rem !important;
      padding: 5px 10px !important;
      transition: all 0.3s ease !important;
      position: relative !important;
      overflow: hidden !important;
      text-transform: uppercase !important;
      letter-spacing: 1px !important;
      box-shadow: 0 5px 20px rgba(138, 43, 226, 0.5) !important;
  }

  .stButton > button::before {
      content: '';
      position: absolute;
      top: 0;
      left: -100%;
      width: 100%;
      height: 100%;
      background: linear-gradient(90deg, transparent, rgba(255, 215, 0, 0.3), transparent);
      transition: left 0.5s;
  }

  .stButton > button:hover::before {
      left: 100% !important;
  }

  .stButton > button:active {
      transform: translateY(0) !important;
      box-shadow: 0 3px 15px rgba(138, 43, 226, 0.4) !important;
  }

  @keyframes battleButtonPulse {
      0% { box-shadow: 0 5px 20px rgba(138, 43, 226, 0.5); }
      100% { box-shadow: 0 8px 30px rgba(255, 215, 0, 0.8); }
  }

  /* Tabs */
  .stTabs {
      background: rgba(138, 43, 226, 0.1) !important;
      border-radius: 15px !important;
      padding: 10px !important;
      backdrop-filter: blur(10px) !important;
      border: 1px solid rgba(255, 215, 0, 0.4) !important;
  }

  .stTabs [data-baseweb="tab-list"] {
      gap: 10px !important;
  }

  .stTabs [data-baseweb="tab"] {
      background: linear-gradient(135deg, rgba(138, 43, 226, 0.2), rgba(65, 105, 225, 0.1)) !important;
      border: 2px solid rgba(255, 215, 0, 0.4) !important;
      border-radius: 20px !important;
      color: #e0e0ff !important;
      font-family: 'Rajdhani', sans-serif !important;
      font-weight: 600 !important;
      padding: 12px 25px !important;
      transition: all 0.3s ease !important;
  }

  .stTabs [data-baseweb="tab"][aria-selected="true"] {
      background: linear-gradient(135deg, #FFD700, #8A2BE2, #4169E1) !important;
      color: #ffffff !important;
      border-color: #FFD700 !important;
      box-shadow: 0 5px 20px rgba(255, 215, 0, 0.5) !important;
  }

  .stTabs [data-baseweb="tab"]:hover {
      background: linear-gradient(135deg, rgba(255, 215, 0, 0.2), rgba(138, 43, 226, 0.2)) !important;
      border-color: #8A2BE2 !important;
     
  }

  h2, h3 {
      font-family: 'Orbitron', monospace !important;
      background: linear-gradient(45deg, #8A2BE2, #4169E1, #6A5ACD, #8A2BE2) !important;
      -webkit-background-clip: text !important;
      -webkit-text-fill-color: transparent !important;
      background-clip: text !important;
      text-shadow: 0 2px 10px rgba(138, 43, 226, 0.6) !important;
      border-bottom: 2px solid rgba(255, 215, 0, 0.4) !important;
      padding-bottom: 10px !important;
      margin-bottom: 20px !important;
      position: relative !important;
  }

  h3::before {
      content: '⚡';
      margin-right: 10px !important;
      color: #FFD700 !important;
      animation: lightning 1.5s ease-in-out infinite alternate !important;
  }

  @keyframes lightning {
      0% { color: #FFD700; text-shadow: 0 0 5px rgba(255, 215, 0, 0.6); }
      100% { color: #8A2BE2; text-shadow: 0 0 15px rgba(138, 43, 226, 0.8); }
  }

  /* Countdown Styling */
  div[style*="text-align: center"][style*="font-size: 48px"] {
      background: linear-gradient(45deg, #8A2BE2, #4169E1, #FFD700) !important;
      -webkit-background-clip: text !important;
      -webkit-text-fill-color: transparent !important;
      background-clip: text !important;
      filter: drop-shadow(0 0 20px rgba(138, 43, 226, 0.8)) !important;
      animation: countdownPulse 0.5s ease-in-out !important;
  }

  @keyframes countdownPulse {
      0% { transform: scale(1); }
      50% { transform: scale(1.2); }
      100% { transform: scale(1); }
  }

  /* Error Messages */
  .stError > div {
      background: linear-gradient(135deg, rgba(138, 43, 226, 0.2), rgba(75, 0, 130, 0.1)) !important;
      border: 2px solid #8A2BE2 !important;
      border-radius: 15px !important;
      color: #e0e0ff !important;
      font-family: 'Rajdhani', sans-serif !important;
      font-weight: 600 !important;
      box-shadow: 0 0 20px rgba(138, 43, 226, 0.4) !important;
  }

  /* Responsive Design */
  @media (max-width: 768px) {
      h1 {
          font-size: 2.5rem !important;
      }

      h1::before, h1::after {
          display: none !important;
      }

      .avatar-container {
          width: 80px !important;
          height: 80px !important;
      }

      .stDataFrame {
          font-size: 12px !important;
      }

      .stButton > button {
          width: 100% !important;
          margin: 5px 0 !important;
          font-size: 0.9rem !important;
          padding: 10px 20px !important;
      }

      .main .block-container {
          padding: 1rem 0.5rem !important;
      }
  }

  
  .stSpinner > div {
      border-color: #8A2BE2 !important;
      animation: loadingPulse 1s ease-in-out infinite !important;
  }

  @keyframes loadingPulse {
      0%, 100% { opacity: 1; }
      50% { opacity: 0.5; }
  }

  /* Scrollbar Styling */
  ::-webkit-scrollbar {
      width: 12px !important;
  }

  ::-webkit-scrollbar-track {
      background: linear-gradient(135deg, #1a0033, #2d1b4e) !important;
      border-radius: 10px !important;
  }

  ::-webkit-scrollbar-thumb {
      background: linear-gradient(135deg, #8A2BE2, #FFD700, #4169E1) !important;
      border-radius: 10px !important;
      border: 2px solid #1a0033 !important;
  }

  ::-webkit-scrollbar-thumb:hover {
      background: linear-gradient(135deg, #4169E1, #FFD700, #8A2BE2) !important;
  }

  .main .block-container::after {
      content: '⚔️ 🛡️ ⚔️';
      position: fixed;
      bottom: 20px;
      right: 20px;
      font-size: 1.5rem;
      opacity: 0.4;
      animation: floatElements 3s ease-in-out infinite alternate;
      pointer-events: none;
  }

  @keyframes floatElements {
      0% { transform: translateY(0px) rotate(0deg); }
      100% { transform: translateY(-10px) rotate(5deg); }
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
    </style>
    """, unsafe_allow_html=True)

    st.title("⚔️ LLKK BATTLE LOG")

    if "logged_in_lab" not in st.session_state:
        st.warning("Please log in to access this page.")
        st.stop()
    
    st.sidebar.markdown("---")
    st.sidebar.subheader("🎯 Simulation Month Selection")
    
    # Get available months from database
    conn = get_db_connection()
    months_df = pd.read_sql("SELECT DISTINCT month FROM submissions ORDER BY month", conn)
    conn.close()
    
    available_months = months_df['month'].tolist()
    
    if not available_months:
        st.sidebar.info("No monthly data available yet.")
        selected_months = []
    else:
        selected_months = st.sidebar.multiselect(
            "Select months to run simulation:",
            options=available_months,
            default=available_months,  
            help="Only selected months will be processed in the simulation"
        )

    run_all_months = st.sidebar.checkbox("Run simulation on ALL months", value=True)
    
    st.sidebar.markdown("---")

    logged_lab = st.session_state.get("logged_in_lab")

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT role, avatar FROM labs_users WHERE username = %s", (logged_lab,))
    result = cursor.fetchone()
    conn.close()

    role = result["role"] if result else "lab"
    avatar_name = result["avatar"] if result and result["avatar"] else "Unknown Avatar"

    if role == "admin":
        st.success(f"🛡️ Admin View: You can see all battles")
    else:
        st.info(f"🙂 Lab View: You will only see battles involving {logged_lab}")

    badge_cols = st.columns([0.18, 1.20])
    if role == "admin":
        with badge_cols[1]:
            st.markdown(f"**Logged in as :** `{logged_lab}`")
    else:
        avatars_map = get_lab_avatars()
        avatar_name = avatars_map.get(logged_lab, logged_lab) 
        my_avatar_path = resolve_avatar_path(avatar_name)

        with badge_cols[0]:
            st.markdown("""
            <style>
            .avatar-container {
                width: 100px;
                height: 100px;
                border-radius: 50%;
                border: 3px solid #2196F3;
                overflow: hidden;
                display: flex;
                align-items: center;
                justify-content: center;
                background: white;
            }
            .avatar-img {
                width: 100%;
                height: 100%;
                object-fit: cover;
            }
            </style>
            """, unsafe_allow_html=True)

            st.markdown(f"""
            <div class="avatar-container">
                <img src="data:image/png;base64,{encode_image_to_base64(my_avatar_path)}" class="avatar-img">
            </div>
            """, unsafe_allow_html=True)

        with badge_cols[1]:
            st.markdown("<br>", unsafe_allow_html=True) 
            st.markdown(f"**Logged in as:** `{logged_lab}`")
            st.markdown(f"**Your Avatar:** `{avatar_name}`")


    if role == "admin":
        df = fetch_lab_data()  # Admin sees all
    else:
        df = fetch_lab_data(lab=logged_lab)  # Lab sees only their own data

    st.session_state["llkk_data"] = df

    if df.empty:
        st.error("🚫 No data found. Please enter data in the Data Entry tab.")
        return

    st.markdown("### Submitted Data")
    st.dataframe(df, use_container_width=True, hide_index=True)

      # Load cached Elo history/progression if present
    if "elo_history" not in st.session_state and os.path.exists("data/elo_history.csv"):
        hist_df = pd.read_csv("data/elo_history.csv")
        st.session_state["elo_history"] = dict(zip(hist_df["Unnamed: 0"], hist_df["elo"]))

    if "elo_progression" not in st.session_state and os.path.exists("data/elo_progression.csv"):
        st.session_state["elo_progression"] = pd.read_csv("data/elo_progression.csv")

    # Initialize simulation state
    if "battle_simulation_started" not in st.session_state:
        st.session_state.battle_simulation_started = False
    if "show_countdown" not in st.session_state:
        st.session_state.show_countdown = False
    if "countdown_value" not in st.session_state:
        st.session_state.countdown_value = 0

    if role == "admin":
        st.markdown("---")
        st.subheader(" Admin Control Panel")
        
        tab1, tab2 = st.tabs(["Battle Simulation", "Battle Visualization"])
        
        with tab1:
            if st.button("🚀 Start Fadzly Battle Simulation", key="start_battle_sim"):
                simulate_fadzly_algorithm(df, selected_months=selected_months, run_all_months=run_all_months)
                st.session_state.battle_simulation_started = True
                st.session_state.show_countdown = True
                st.session_state.countdown_value = 3
                
            if st.button("❌ Clear All Elo History", key="clear_elo_history"):
                clear_battlelog()
                for key in ["elo_history", "elo_progression", "fadzly_battles", "battle_simulation_started", "show_countdown", "countdown_value"]:
                    st.session_state.pop(key, None)
                st.success("✅ All historical data cleared from database.")

                time.sleep(2) #delay 2sec 
                st.rerun()
        
        with tab2:
          if st.session_state.get("show_countdown", False):
              countdown_placeholder = st.empty()
              
              # Countdown animation
              for i in range(st.session_state.countdown_value, 0, -1):
                  countdown_placeholder.markdown(f"""
                  <div style="text-align: center; font-size: 48px; color: #ff6b6b; font-weight: bold;">
                      {i}
                  </div>
                  """, unsafe_allow_html=True)
                  time.sleep(1)
              
              countdown_placeholder.empty()
              st.session_state.show_countdown = False
              
              run_battlelog(
                  auto_play=True,
                  user_role=role,
                  user_lab=logged_lab if role != "admin" else None,
                  selected_months=selected_months,
                  show_all_data=run_all_months
              )

          else:
              run_battlelog(
                  user_role=role,
                  user_lab=logged_lab if role != "admin" else None,
                  selected_months=selected_months,
                  show_all_data=run_all_months
              )

    else:
          run_battlelog(
              user_role=role,
              user_lab=logged_lab,
              selected_months=selected_months,
              show_all_data=run_all_months
          )

if __name__ == "__main__":
    run()