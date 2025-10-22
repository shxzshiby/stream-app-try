import streamlit as st
import pandas as pd
import mysql.connector
from BattleLog import simulate_fadzly_algorithm  
from Login import apply_sidebar_theme

def get_connection():
    return mysql.connector.connect(
        host="145.223.18.115",
        port=3306,
        user="admin",
        password="@Cittamall13",         
        database="gamifiedqc" 
    )

def clear_alldata():
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM battle_logs")
    cursor.execute("DELETE FROM lab_ratings")
    cursor.execute("DELETE FROM monthly_final")
    cursor.execute("DELETE FROM monthly_rankings")
    
    conn.commit()
    conn.close()

def run():
    st.markdown("""
    <style>
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
    </style>
    """, unsafe_allow_html=True)

    apply_sidebar_theme()
    st.title("🛡️ Admin Control Center")

    if st.session_state.get("user_role") != "admin":
        st.warning("Access denied. This page is for admin only.")
        return
    
    st.subheader("📋 All Submitted Data")
    try:
        conn = get_connection()
        submissions_df = pd.read_sql("SELECT * FROM submissions ORDER BY id ASC", conn)
        conn.close()

        if not submissions_df.empty:
            st.dataframe(submissions_df,hide_index=True)

            csv = submissions_df.to_csv(index=False).encode("utf-8")
            st.download_button("📤 Download All Data", csv, "llkk_all_data.csv", "text/csv")
        else:
            st.info("No lab data submitted yet.")

    except Exception as e:
        st.error(f"⚠️ Could not load submissions: {e}")

    st.subheader("🥷 Admin Management")

    with st.expander("➕ Add New Admin"):  
        with st.form("add_user_form", clear_on_submit=True):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            role = st.selectbox("Role", ["admin"])
            submitted = st.form_submit_button("💾 Save ")

            if submitted:
                try:
                    conn = get_connection()
                    cur = conn.cursor()
                    cur.execute(
                        "INSERT INTO labs_users (username, password, role) VALUES (%s, %s, %s)",
                        (username, password, role)
                    )
                    conn.commit()
                    cur.close()
                    conn.close()

                    st.success(f"✅ User `{username}` added with role `{role}`!")

                except mysql.connector.Error as err:
                    st.error(f"❌ Database error: {err}")

    # Show All Users 
    st.subheader("📋 Registered Warriors")
    try:
        conn = get_connection()
        df = pd.read_sql("SELECT id, username, role, avatar FROM labs_users", conn)  
        conn.close()
        st.dataframe(df,hide_index=True)
    except Exception as e:
        st.error(f"⚠️ Could not load admin: {e}")


    # Simulation 
    st.subheader("⚔️ Simulate Battles Across All Labs")
    if st.button("🚀 Start Battle Simulation Now"):
        simulate_fadzly_algorithm(st.session_state.get("llkk_data", pd.DataFrame()))
        st.success("✅ Battle simulation complete!")

    # Danger Zone 
    st.subheader("🧨 Danger Zone")
    if st.button("❌ Clear All LLKK Data"):
        clear_alldata()
        for key in ["fadzly_battles", "elo_history", "elo_progression","llkk_data"]:
            st.session_state.pop(key, None)
        st.success("All LLKK and battle data has been reset.")
