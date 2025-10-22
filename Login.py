import streamlit as st
import mysql.connector

def get_connection():
    return mysql.connector.connect(
        host="145.223.18.115",
        port=3306,
        user="admin",
        password="@Cittamall13",         
        database="gamifiedqc" 
    )

def validate_user(username, password):
    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM labs_users WHERE username=%s AND password=%s", (username, password))
    user = cur.fetchone()
    cur.close(); conn.close()
    return user

def apply_sidebar_theme():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Exo+2:wght@300;400;600;700&family=Rajdhani:wght@500;600;700&display=swap');

    /* ===== MLBB PURPLE-BLUE THEME VARIABLES ===== */
    :root {
        --mlbb-primary: #8a2be2;      /* Deep purple - Violet */
        --mlbb-secondary: #4a00e0;    /* Royal purple */
        --mlbb-accent: #9370db;       /* Medium purple */
        --mlbb-blue: #4169e1;         /* Royal blue */
        --mlbb-cyan: #00ced1;         /* Dark cyan */
        --mlbb-dark: #0a0f1e;         /* Deep navy */
        --mlbb-darker: #070a14;       /* Almost black */
        --mlbb-light: #e6e6fa;        /* Lavender */
        --mlbb-gold: #ffd700;         /* Gold accent */
        --mlbb-silver: #c0c0c0;       /* Silver accent */
        
        --glow-intensity: 0.6;
        --border-glow: 0 0 15px rgba(138, 43, 226, 0.7);
        --text-glow: 0 0 10px rgba(147, 112, 219, 0.8);
        --button-glow: 0 0 20px rgba(138, 43, 226, 0.6);
    }

    /* ===== SIDEBAR SCROLL ===== */
    section[data-testid="stSidebar"] > div:first-child {
        background: linear-gradient(180deg, var(--mlbb-darker) 0%, var(--mlbb-dark) 100%) !important;
        border-right: 2px solid transparent !important;
        border-image: linear-gradient(180deg, var(--mlbb-primary), var(--mlbb-blue)) 1 !important;
        box-shadow: 5px 0 25px rgba(138, 43, 226, 0.4) !important;
        position: relative !important;
        overflow: auto !important;
        height: 100vh !important;
    }

    /* ===== LOGIN TITLE ===== */
    section[data-testid="stSidebar"] h1 {
        font-family: 'Orbitron', monospace !important;
        font-weight: 900 !important;
        background: linear-gradient(135deg, var(--mlbb-primary), var(--mlbb-blue), var(--mlbb-cyan)) !important;
        -webkit-background-clip: text !important;
        -webkit-text-fill-color: transparent !important;
        text-shadow: var(--text-glow) !important;
        text-align: center !important;
        margin: 1.5rem 0 2rem 0 !important;
        font-size: 2rem !important;
        letter-spacing: 2px !important;
        position: relative;
        padding-bottom: 15px;
    }

    section[data-testid="stSidebar"] h1::after {
        content: '';
        position: absolute;
        bottom: 0;
        left: 25%;
        width: 50%;
        height: 3px;
        background: linear-gradient(90deg, transparent, var(--mlbb-primary), var(--mlbb-blue), transparent);
        animation: titleUnderline 3s ease-in-out infinite;
    }

    @keyframes titleUnderline {
        0%, 100% { opacity: 0.7; transform: scaleX(0.8); }
        50% { opacity: 1; transform: scaleX(1); }
    }

    /* ===== INPUT FIELDS  ===== */
    section[data-testid="stSidebar"] .stTextInput > div > div > input {
        background: rgba(10, 15, 30, 0.4) !important;
        border: 2px solid rgba(138, 43, 226, 0.4) !important;
        border-radius: 12px !important;
        color: var(--mlbb-light) !important;
        font-family: 'Rajdhani', sans-serif !important;
        font-weight: 600 !important;
        padding: 14px 18px !important;
        backdrop-filter: blur(10px) !important;
        transition: all 0.3s ease !important;
        box-shadow: inset 0 0 15px rgba(138, 43, 226, 0.1) !important;
        width: 100% !important;
    }

    section[data-testid="stSidebar"] .stTextInput > div > div > input:focus {
        border-color: var(--mlbb-cyan) !important;
        box-shadow: 0 0 20px rgba(0, 206, 209, 0.6), inset 0 0 20px rgba(138, 43, 226, 0.2) !important;
        outline: none !important;
        background: rgba(10, 15, 30, 0.6) !important;
        transform: translateY(-2px);
    }

    section[data-testid="stSidebar"] .stTextInput > div > div > input::placeholder {
        color: rgba(230, 230, 250, 0.6) !important;
        font-style: italic !important;
        font-family: 'Rajdhani', sans-serif !important;
    }

    /* ===== INPUT LABELS ===== */
    section[data-testid="stSidebar"] .stTextInput label {
        color: var(--mlbb-accent) !important;
        font-family: 'Exo 2', sans-serif !important;
        font-weight: 700 !important;
        text-shadow: var(--text-glow) !important;
        margin-bottom: 8px !important;
        font-size: 2rem !important;
        letter-spacing: 0.5px;
    }

    /* ===== LOGIN BUTTON ===== */
    section[data-testid="stSidebar"] .stButton > button {
        background: linear-gradient(135deg, var(--mlbb-primary), var(--mlbb-secondary)) !important;
        border: 2px solid transparent !important;
        color: white !important;
        font-family: 'Orbitron', monospace !important;
        font-weight: 700 !important;
        padding: 5px 25px !important;
        letter-spacing: 1.5px !important;
        box-shadow: var(--button-glow), 0 8px 25px rgba(0, 0, 0, 0.4) !important;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
        position: relative !important;
        overflow: hidden !important;
        margin: 20px 0 10px 0 !important;
        font-size: 1.2rem !important;
        text-transform: uppercase;
        width: 100% !important;
    }

    section[data-testid="stSidebar"] .stButton > button:hover {
        transform: translateY(-3px) scale(1.05) !important;
        box-shadow: 0 15px 35px rgba(138, 43, 226, 0.8), 0 8px 25px rgba(0, 0, 0, 0.5) !important;
        background: linear-gradient(135deg, var(--mlbb-secondary), var(--mlbb-primary)) !important;
    }

    section[data-testid="stSidebar"] .stButton > button:active {
        transform: translateY(-1px) scale(1.02) !important;
    }

    /* Button magical effect */
    section[data-testid="stSidebar"] .stButton > button::before {
        content: '';
        position: absolute;
        top: -50%;
        left: -50%;
        width: 200%;
        height: 200%;
        background: linear-gradient(45deg, transparent, rgba(255, 255, 255, 0.1), transparent);
        transform: rotate(45deg);
        transition: all 0.5s ease;
    }

    section[data-testid="stSidebar"] .stButton > button:hover::before {
        animation: buttonShine 1.5s ease-in-out;
    }

    @keyframes buttonShine {
        0% { left: -100%; }
        100% { left: 100%; }
    }

    /* ===== STATUS MESSAGES ===== */
    section[data-testid="stSidebar"] .stAlert {
        border-radius: 12px !important;
        border: none !important;
        backdrop-filter: blur(10px) !important;
        font-family: 'Rajdhani', sans-serif !important;
        font-weight: 600 !important;
        margin: 15px 0 !important;
        animation: alertSlideIn 0.4s ease-out !important;
    }

    @keyframes alertSlideIn {
        0% { transform: translateX(-20px); opacity: 0; }
        100% { transform: translateX(0); opacity: 1; }
    }

    section[data-testid="stSidebar"] .stSuccess {
        background: rgba(0, 206, 209, 0.15) !important;
        border: 2px solid var(--mlbb-cyan) !important;
        color: var(--mlbb-light) !important;
        box-shadow: 0 0 25px rgba(0, 206, 209, 0.3) !important;
    }

    section[data-testid="stSidebar"] .stError {
        background: rgba(255, 0, 0, 0.15) !important;
        border: 2px solid #ff3366 !important;
        color: var(--mlbb-light) !important;
        box-shadow: 0 0 25px rgba(255, 51, 102, 0.3) !important;
    }

    /* ===== LOGGED IN STATUS ===== */
    section[data-testid="stSidebar"] .stMarkdown p {
        color: var(--mlbb-light) !important;
        font-family: 'Rajdhani', sans-serif !important;
        font-weight: 600 !important;
        background: rgba(138, 43, 226, 0.1) !important;
        padding: 12px 16px !important;
        border-radius: 10px !important;
        border: 1px solid rgba(147, 112, 219, 0.3) !important;
        backdrop-filter: blur(5px) !important;
        margin: 10px 0 !important;
        text-align: center;
    }

    section[data-testid="stSidebar"] .stMarkdown code {
        background: rgba(74, 0, 224, 0.2) !important;
        color: var(--mlbb-cyan) !important;
        font-family: 'Orbitron', monospace !important;
        font-weight: 600 !important;
        padding: 4px 8px !important;
        border-radius: 6px !important;
        border: 1px solid rgba(0, 206, 209, 0.3) !important;
    }

    /* ===== LOGOUT BUTTON ===== */
    section[data-testid="stSidebar"] .stButton:last-child > button {
        background: linear-gradient(135deg, #ff3366, #cc0044) !important;
        border-color: #ff3366 !important;
        margin-top: 10px !important;
    }

    section[data-testid="stSidebar"] .stButton:last-child > button:hover {
        background: linear-gradient(135deg, #cc0044, #990033) !important;
        box-shadow: 0 15px 35px rgba(255, 51, 102, 0.6) !important;
    }

    /* ===== MOBILE RESPONSIVENESS ===== */
    @media (max-width: 768px) {
        section[data-testid="stSidebar"] h1 {
            font-size: 1.6rem !important;
            margin: 1rem 0 1.5rem 0 !important;
        }
        
        section[data-testid="stSidebar"] .stButton > button {
            padding: 14px 24px !important;
            font-size: 1rem !important;
            margin: 15px 0 10px 0 !important;
        }
        
        section[data-testid="stSidebar"] .stTextInput > div > div > input {
            padding: 12px 16px !important;
            font-size: 16px !important;
        }
    }

    /* ===== SPECIAL EFFECTS ===== */
    .login-success-pulse {
        animation: successPulse 0.8s ease-out;
    }

    @keyframes successPulse {
        0% { transform: scale(1); box-shadow: 0 0 20px rgba(0, 206, 209, 0.8); }
        50% { transform: scale(1.05); box-shadow: 0 0 40px rgba(0, 206, 209, 1); }
        100% { transform: scale(1); box-shadow: 0 0 20px rgba(0, 206, 209, 0.8); }
    }

    /* Floating animation for login elements */
    section[data-testid="stSidebar"] .stTextInput,
    section[data-testid="stSidebar"] .stButton {
        animation: floatIn 0.6s ease-out;
    }

    @keyframes floatIn {
        0% { transform: translateY(20px); opacity: 0; }
        100% { transform: translateY(0); opacity: 1; }
    }

    /* Delay animations for sequential appearance */
    section[data-testid="stSidebar"] .stTextInput:nth-child(1) { animation-delay: 0.1s; }
    section[data-testid="stSidebar"] .stTextInput:nth-child(2) { animation-delay: 0.2s; }
    section[data-testid="stSidebar"] .stButton { animation-delay: 0.3s; }

    /* ===== SCROLLBAR STYLING ===== */
    section[data-testid="stSidebar"] > div:first-child::-webkit-scrollbar {
        width: 8px;
    }

    section[data-testid="stSidebar"] > div:first-child::-webkit-scrollbar-track {
        background: rgba(138, 43, 226, 0.1);
        border-radius: 4px;
    }

    section[data-testid="stSidebar"] > div:first-child::-webkit-scrollbar-thumb {
        background: linear-gradient(180deg, var(--mlbb-primary), var(--mlbb-blue));
        border-radius: 4px;
    }

    section[data-testid="stSidebar"] > div:first-child::-webkit-scrollbar-thumb:hover {
        background: linear-gradient(180deg, var(--mlbb-blue), var(--mlbb-cyan));
    }
    </style>
    """, unsafe_allow_html=True)

#sidebar n login 
def run_login():
    st.sidebar.title("🔐 Lab Login")

    if "logged_in_lab" not in st.session_state:
        username = st.sidebar.text_input("Username")
        password = st.sidebar.text_input("Password", type="password")

        if st.sidebar.button("Login"):
            user = validate_user(username, password)
            if user:
                st.session_state["logged_in_lab"] = user["username"]
                st.session_state["user_role"] = user["role"]
                st.session_state["login_success"] = True
                st.rerun()
            else:
                st.session_state["login_success"] = False
                st.sidebar.error("❌ Incorrect username or password")

    if "logged_in_lab" in st.session_state:
        st.sidebar.markdown(f"✅ Logged in as: `{st.session_state['logged_in_lab']}`")
        st.sidebar.markdown(f"🧩 Role: `{st.session_state['user_role']}`")
        if st.sidebar.button("Logout"):
            for key in ["logged_in_lab", "user_role", "login_success"]:
                st.session_state.pop(key, None)
            st.rerun()