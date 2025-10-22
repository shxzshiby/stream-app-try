import streamlit as st
import pandas as pd
import numpy as np
import os
import mysql.connector
import time 
from datetime import datetime, date
from Login import apply_sidebar_theme

def get_connection():
    return mysql.connector.connect(
        host="145.223.18.115",
        port=3306,
        user="admin",
        password="@Cittamall13",         
        database="gamifiedqc" 
    )

# Function to check if submission is allowed based on current date
def is_submission_allowed():
    today = date.today()
    return 1 <= today.day <= 19

def count_current_month_submissions(lab):
    today = date.today()
    current_month = today.month
    current_year = today.year
    
    conn = get_connection()
    cursor = conn.cursor()
    
    query = """
        SELECT COUNT(*) FROM submissions 
        WHERE Lab = %s AND MONTH(created_at) = %s AND YEAR(created_at) = %s
    """
    cursor.execute(query, (lab, current_month, current_year))
    count = cursor.fetchone()[0]
    
    cursor.close()
    conn.close()
    
    return count

def get_user_parameters(lab):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT selected_parameters FROM labs_users WHERE username = %s", (lab,))
    result = cur.fetchone()
    cur.close()
    conn.close()
    
    if result and result[0]:
        return result[0].split(',')
    return []

def check_required_parameters(lab):
    today = date.today()
    current_month = today.month
    current_year = today.year
    
    conn = get_connection()
    query = """
        SELECT Parameter, Level FROM submissions 
        WHERE Lab = %s AND MONTH(created_at) = %s AND YEAR(created_at) = %s
    """
    submitted_df = pd.read_sql(query, conn, params=[lab, current_month, current_year])
    conn.close()
    
    user_parameters = get_user_parameters(lab)
    
    missing_params = []
    for param in user_parameters:  
        param_data = submitted_df[submitted_df['Parameter'] == param]
        if len(param_data) == 0:
            missing_params.append(f"{param} (both levels)")
        elif 'L1' not in param_data['Level'].values:
            missing_params.append(f"{param} (L1)")
        elif 'L2' not in param_data['Level'].values:
            missing_params.append(f"{param} (L2)")
    
    return missing_params

# Function to check if parameter already has data for the selected month
def check_existing_parameter_month(lab, parameter, month, level=None):
    today = date.today()
    current_year = today.year
    
    conn = get_connection()
    cursor = conn.cursor()
    
    if level:
        query = """
            SELECT COUNT(*) FROM submissions 
            WHERE Lab = %s AND Parameter = %s AND Month = %s AND Level = %s 
            AND YEAR(created_at) = %s
        """
        cursor.execute(query, (lab, parameter, month, level, current_year))
    else:
        query = """
            SELECT COUNT(*) FROM submissions 
            WHERE Lab = %s AND Parameter = %s AND Month = %s 
            AND YEAR(created_at) = %s
        """
        cursor.execute(query, (lab, parameter, month, current_year))
    
    count = cursor.fetchone()[0]
    
    cursor.close()
    conn.close()
    
    return count

def get_parameter_ratio(lab, parameter, month):
    today = date.today()
    current_year = today.year
    
    conn = get_connection()
    query = """
        SELECT Ratio FROM submissions 
        WHERE Lab = %s AND Parameter = %s AND Month = %s 
        AND YEAR(created_at) = %s
        LIMIT 1
    """
    df = pd.read_sql(query, conn, params=[lab, parameter, month, current_year])
    conn.close()
    
    if not df.empty:
        return df.iloc[0]['Ratio']
    return None

def validate_ratio(n_qc, wd, parameter, level, month):
    if n_qc > 0 and wd > 0:
        ratio = n_qc / wd
        if ratio < 1:
            return f"Ratio for {parameter} - {level} in {month} must be ≥ 1"
    return None

def validate_both_levels_submitted(input_data):
    errors = []
    
    parameter_month_groups = {}
    
    for data in input_data:
        key = f"{data['Parameter']}_{data['Month']}"
        if key not in parameter_month_groups:
            parameter_month_groups[key] = set()
        parameter_month_groups[key].add(data['Level'])
   
    for key, levels in parameter_month_groups.items():
        parameter, month = key.split('_')
        if len(levels) == 1:
            missing_level = "L2" if "L1" in levels else "L1"
            errors.append(f"{parameter} in {month}: Missing {missing_level} level")
        elif "L1" not in levels or "L2" not in levels:
            errors.append(f"{parameter} in {month}: Both L1 and L2 levels are required")
    
    return errors

def get_all_submissions(lab):
    conn = get_connection()
    query = """
        SELECT * FROM submissions 
        WHERE Lab = %s
        ORDER BY created_at DESC
    """
    all_df = pd.read_sql(query, conn, params=[lab])
    conn.close()
    return all_df

# Function to get submissions for CSV export
def get_submissions_for_csv(lab, month=None, year=None):
    conn = get_connection()
    
    if month and year:
        query = """
            SELECT * FROM submissions 
            WHERE Lab = %s AND MONTH(created_at) = %s AND YEAR(created_at) = %s
            ORDER BY created_at DESC
        """
        df = pd.read_sql(query, conn, params=[lab, month, year])
    else:
        query = """
            SELECT * FROM submissions 
            WHERE Lab = %s
            ORDER BY created_at DESC
        """
        df = pd.read_sql(query, conn, params=[lab])
    
    conn.close()
    return df

DATA_DIR = "data"

def run():
    apply_sidebar_theme()
    st.markdown("""
    <style>
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
                
    h1 {
        font-family: 'Cinzel', serif !important;
        font-size: 67px !important;
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
    
    h2, h3 {
        font-family: 'Orbitron', monospace !important;
        background: linear-gradient(45deg, #8A2BE2, #6A0DAD, #4169E1, #8A2BE2) !important;
        background-size: 300% 300% !important;
        -webkit-background-clip: text !important;
        -webkit-text-fill-color: transparent !important;
        background-clip: text !important;
        animation: titleShine 3s linear infinite !important;
        text-shadow: 0 2px 10px rgba(138, 43, 226, 0.6) !important;
        border-bottom: 2px solid rgba(255, 215, 0, 0.4) !important;
        padding-bottom: 10px !important;
        margin: 20px 0 !important;
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
        100% { color: #FF1493; text-shadow: 0 0 15px rgba(255, 20, 147, 0.8); }
        }
    
    /* Status Messages - Success */
        .stAlert[data-baseweb="notification"] > div {
            border-radius: 15px !important;
            border: 2px solid transparent !important;
            backdrop-filter: blur(10px) !important;
            padding: 1rem 1.5rem !important;
            font-family: 'Rajdhani', sans-serif !important;
            font-weight: 600 !important;
            font-size: 1.1rem !important;
            position: relative !important;
            overflow: hidden !important;
            animation: slideIn 0.5s ease-out !important;
        }
    
    /* Success Alert */
    div[data-testid="stAlert"][class*="success"] {
        background: linear-gradient(135deg, rgba(138, 43, 226, 0.25), rgba(75, 0, 130, 0.15)) !important;
        border: 2px solid #8A2BE2 !important;
        box-shadow: 0 0 20px rgba(138, 43, 226, 0.4) !important;
        color: #e0ffe0 !important;
    }
    
   .stButton > button {
        background: var(--mlbb-gradient) !important;
        color: white !important;
        border: none !important;
        border-radius: 10px !important;
        font-family: 'Orbitron', monospace !important;
        font-weight: 700 !important;
        font-size: 1rem !important;
        padding: 10px 20px !important;
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

    @keyframes buttonPulse {
        0% { box-shadow: 0 5px 20px rgba(255, 215, 0, 0.5); }
        100% { box-shadow: 0 8px 30px rgba(255, 20, 147, 0.8); }
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
    
    st.title("📋 LLKK DIRECT DATA ENTRY")

    if "logged_in_lab" not in st.session_state:
        st.warning("Please log in from the sidebar to access data entry.")
        st.stop()

    lab = st.session_state["logged_in_lab"]
    
    if not is_submission_allowed():
        st.error("🚫 Data submission is only allowed from the 1st to the 14th of each month.")
        st.info("The battle begins on the 15th. Please come back next month for data submission.")
        st.stop()
    
    user_parameters = get_user_parameters(lab)
    expected_total = len(user_parameters) * 2
    submission_count = count_current_month_submissions(lab)
    missing_params = check_required_parameters(lab)
    
    status_col1, status_col2 = st.columns([1, 3])
    with status_col1:
        if submission_count == expected_total and not missing_params:
            st.success(f"✅ Ready for battle! ({submission_count}/{expected_total})") 
        else:
            st.warning(f"⚠️ Incomplete ({submission_count}/{expected_total})")
    
    with status_col2:
        today = date.today()
        days_left = 19 - today.day
        st.info(f"📅 Submission window: 1st-19th ({days_left} days left)")
    
    if missing_params:
        with st.expander("Show missing parameters", expanded=False):
            st.warning("⚠️ Missing submissions for:")  
            for param in missing_params:
                st.write(f"- {param}")  
   
    all_submissions_df = get_all_submissions(lab)
    
    st.subheader("Previously Submitted Data")
    
    # filter options
    filter_col1, filter_col2 = st.columns(2)
    with filter_col1:
        view_option = st.radio("Filter by:", 
                              ["Current month", "All time", "Specific month"])
    
    if view_option == "Current month":
        today = date.today()
        current_month = today.month
        current_year = today.year
        
        conn = get_connection()
        query = """
            SELECT * FROM submissions 
            WHERE Lab = %s AND MONTH(created_at) = %s AND YEAR(created_at) = %s
            ORDER BY created_at DESC
        """
        view_df = pd.read_sql(query, conn, params=[lab, current_month, current_year])
        conn.close()
        
    elif view_option == "All time":
        view_df = all_submissions_df
        
    else: 
        today = date.today()
        current_year = today.year
        current_month = today.month
        
        available_months = []
        
        for month in range(1, 13):
            month_str = f"{current_year}-{month:02d}"
            available_months.append(month_str)
        
        available_months = sorted(set(available_months), reverse=True)
        
        selected_month = st.selectbox("Select month:", available_months)
        year, month_num = selected_month.split('-')
        
        month_text = [
            'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
            'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'
        ]
        month_text = month_text[int(month_num) - 1]
        
        conn = get_connection()
        query = """
            SELECT * FROM submissions 
            WHERE Lab = %s AND month = %s AND YEAR(created_at) = %s
            ORDER BY created_at DESC
        """
        view_df = pd.read_sql(query, conn, params=[lab, month_text, int(year)])
        conn.close()

    if "edit_mode" not in st.session_state:
        st.session_state.edit_mode = False

    col1, col2, col3 = st.columns([6, 1, 1])  

    with col2:
        if st.button("✏️ Edit", key="edit_records_button", use_container_width=True):  
            st.session_state.edit_mode = True
            st.session_state.edit_lab = lab
            st.rerun()

    with col3:
        if st.button("🗑️ Delete", key="delete_records_button", use_container_width=True):  
            st.session_state.delete_mode = True
            st.session_state.delete_lab = lab
            st.rerun()

    st.dataframe(view_df,hide_index=True)

   
    if st.session_state.get("delete_mode", False):
        if st.button("← Back to Data Entry"):
            st.session_state.delete_mode = False
            st.rerun()
        
        today = date.today()
        current_month = today.month
        current_year = today.year
        
        conn = get_connection()
        query = """
            SELECT DISTINCT Parameter, Level FROM submissions 
            WHERE Lab = %s AND MONTH(created_at) = %s AND YEAR(created_at) = %s 
            ORDER BY Parameter, Level
        """
        params_df = pd.read_sql(query, conn, params=[lab, current_month, current_year])
        conn.close()
        
        if params_df.empty:
            st.error("No records found for deletion.")
        else:
            parameters = sorted(params_df['Parameter'].unique())
            selected_param = st.selectbox("Select Parameter", parameters, key="delete_param")
            
            available_levels = params_df[params_df['Parameter'] == selected_param]['Level'].unique()
            selected_level = st.selectbox("Select Level", available_levels, key="delete_level")
            
            st.warning(f" ⚠️ You are about to delete ALL records for: {selected_param} - {selected_level} This action cannot be undone!")
            
            conn = get_connection()
            query = """
                SELECT COUNT(*) as count FROM submissions 
                WHERE Lab = %s AND Parameter = %s AND Level = %s 
                AND MONTH(created_at) = %s AND YEAR(created_at) = %s
            """
            count_df = pd.read_sql(query, conn, params=[lab, selected_param, selected_level, current_month, current_year])
            record_count = count_df.iloc[0]['count']
            conn.close()
            
            st.write(f"Number of records that will be deleted: **{record_count}**")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("✅ Confirm Delete", type="primary",  use_container_width=True):
                    
                    conn = get_connection()
                    cursor = conn.cursor()
                    cursor.execute(
                        """
                        DELETE FROM submissions 
                        WHERE Lab = %s AND Parameter = %s AND Level = %s 
                        AND MONTH(created_at) = %s AND YEAR(created_at) = %s
                        """,
                        (lab, selected_param, selected_level, current_month, current_year)
                    )
                    conn.commit()
                    cursor.close()
                    conn.close()
                    
                    st.success(f"✅ Deleted {record_count} records for {selected_param} - {selected_level}")
                    
                    countdown_placeholder = st.empty()
                    for i in range(5, 0, -1):
                        countdown_placeholder.info(f"Returning to data entry in {i} seconds...")
                        time.sleep(1)
                    
                    st.session_state.delete_mode = False
                    st.rerun()
            
            with col2:
                if st.button("❌ Cancel Delete", use_container_width=True):
                    st.session_state.delete_mode = False
                    st.rerun()

   
    if st.session_state.get("edit_mode", False):
        today = date.today()
        current_month = today.month
        current_year = today.year
        
        conn = get_connection()
        query = """
            SELECT DISTINCT Parameter, Level FROM submissions 
            WHERE Lab = %s AND MONTH(created_at) = %s AND YEAR(created_at) = %s 
            ORDER BY Parameter, Level
        """
        params_df = pd.read_sql(query, conn, params=[lab, current_month, current_year])
        conn.close()
        
        if params_df.empty:
            st.error("No records found for editing.")
        else:
            parameters = sorted(params_df['Parameter'].unique())
            selected_param = st.selectbox("Select Parameter", parameters, key="edit_param")
            
            available_levels = params_df[params_df['Parameter'] == selected_param]['Level'].unique()
            selected_level = st.selectbox("Select Level", available_levels, key="edit_level")
    
            conn = get_connection()
            query = """
                SELECT * FROM submissions 
                WHERE Lab = %s AND Parameter = %s AND Level = %s 
                AND MONTH(created_at) = %s AND YEAR(created_at) = %s
            """
            records_df = pd.read_sql(query, conn, params=[lab, selected_param, selected_level, current_month, current_year])
            conn.close()
            
            if records_df.empty:
                st.error("No records found for the selected parameter and level.")
            else:
                st.subheader(f"Editing {selected_param} - {selected_level}")
                
             
                with st.form("edit_form"):
                    updated_data = []
                    
                    all_parameters = sorted([
                    "Albumin", "ALT", "AST", "Bilirubin (Total)", "Cholesterol",
                    "Creatinine", "ALP", "Glucose", "HDL Cholesterol",
                    "CL", "Potassium", "Protein (Total)", "Sodium",
                    "Triglycerides", "Urea", "Uric Acid"
                    ])
                    all_levels = ["L1", "L2"]
                    
                    edit_validation_errors = []

                    for idx, record in records_df.iterrows():
                        st.markdown(f"**Record {idx+1}**")

                        new_param = st.selectbox(
                            "Parameter", 
                            all_parameters,
                            index=all_parameters.index(record['Parameter']),
                            key=f"param_{record['id']}"
                        )
                    
                        new_level = st.selectbox(
                            "Level", 
                            all_levels,
                            index=all_levels.index(record['Level']),
                            key=f"level_{record['id']}"
                        )
                        
                        month = st.selectbox(
                            "Month", 
                            ["Jan", "Feb", "Mar", "Apr", "May", "Jun", 
                            "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
                            index=["Jan", "Feb", "Mar", "Apr", "May", "Jun", 
                                "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"].index(record['Month']),
                            key=f"month_{record['id']}"
                        )
                        
                        cv = st.number_input(
                            "CV(%)", 
                            min_value=0.0, 
                            max_value=100.0, 
                            value=float(record['CV(%)']),
                            key=f"cv_{record['id']}"
                        )
                        
                        n_qc = st.number_input(
                            "n(QC)", 
                            min_value=0, 
                            max_value=100, 
                            value=int(record['n(QC)']),
                            key=f"nqc_{record['id']}"
                        )
                        
                        wd = st.number_input(
                            "Working_Days", 
                            min_value=1, 
                            max_value=31, 
                            value=int(record['Working_Days']),
                            key=f"wd_{record['id']}"
                        )
                        
                        ratio_error = validate_ratio(n_qc, wd, new_param, new_level, month)
                        if ratio_error:
                            edit_validation_errors.append(ratio_error)
                        
                        ratio = round(n_qc / wd, 2) if n_qc > 0 and wd > 0 else 0.0
                        st.number_input("Ratio", value=ratio, disabled=True, key=f"ratio_{record['id']}")
                        
                        updated_data.append({
                            "id": record['id'],
                            "parameter": new_param,
                            "level": new_level,
                            "month": month,
                            "cv": cv,
                            "n_qc": n_qc,
                            "wd": wd,
                            "ratio": ratio
                        })
                    
                    if edit_validation_errors:
                        st.error("🚫 Ratio Validation Errors:")
                        for error in edit_validation_errors:
                            st.write(f"- {error}")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        update_submitted = st.form_submit_button("Update Records", disabled=bool(edit_validation_errors))
                    with col2:
                        cancel_edit = st.form_submit_button("Cancel Edit")
                    
                    if update_submitted and not edit_validation_errors:
                       
                        conn = get_connection()
                        cursor = conn.cursor()
                        
                        for data in updated_data:
                            cursor.execute("""
                                UPDATE submissions 
                                SET Parameter = %s, Level = %s, Month = %s, 
                                    `CV(%)` = %s, `n(QC)` = %s, 
                                    `Working_Days` = %s, Ratio = %s
                                WHERE id = %s
                            """, (
                                data['parameter'], data['level'], data['month'], 
                                data['cv'], data['n_qc'], data['wd'], data['ratio'], 
                                data['id']
                            ))

                        conn.commit()
                        cursor.close()
                        conn.close()
                        
                        st.success("✅ Records updated successfully!")
                        st.session_state.edit_mode = False
                        
                        countdown_placeholder = st.empty()
                        for i in range(5, 0, -1):
                            countdown_placeholder.info(f"Returning to data entry in {i} seconds...")
                            time.sleep(1)
                        
                        st.rerun()
                    
                    if cancel_edit:
                        st.session_state.edit_mode = False
                        st.rerun()

    user_parameters = get_user_parameters(lab)
    expected_total = len(user_parameters) * 2
    submission_count = count_current_month_submissions(lab)
    missing_params = check_required_parameters(lab)
    
    all_data_complete = (submission_count == expected_total and not missing_params)
    
    if not all_data_complete and not st.session_state.edit_mode:
        
        parameters = sorted([
            "Albumin", "ALT", "AST", "Bilirubin (Total)", "Cholesterol",
            "Creatinine", "ALP", "Glucose", "HDL Cholesterol",
            "CL", "Potassium", "Protein (Total)", "Sodium",
            "Triglycerides", "Urea", "Uric Acid"
        ])
        levels = ["L1", "L2"]
        current_month_num = date.today().month
        months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", 
                "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        current_month = months[current_month_num - 1]

        st.subheader(f"Enter Data for: :green[{lab}]")
            
        default_col1, default_col2 = st.columns(2)
    
        with default_col1:
            default_wd = st.number_input(
                "Default Working Days", 
                min_value=1, 
                max_value=31, 
                value=24,
                key="default_wd",
                help="This value will apply to ALL parameters"
            )
        
        with default_col2:
            default_n_qc = st.number_input(
                "Default n(QC)", 
                min_value=0, 
                max_value=100, 
                value=0,
                key="default_n_qc",
                help="This is the default value, but you can change it for each parameter"
            )

        input_data = []
        validation_errors = []
        seen_ratio_errors = set()
        
        if "parameter_n_qc" not in st.session_state:
            st.session_state.parameter_n_qc = {}

        entry_counter = 0
        for parameter in sorted(user_parameters):
            for level in ["L1", "L2"]:
                cols = st.columns(7)
                    
                cols[0].text_input("Parameter", value=parameter, disabled=True, key=f"param_{entry_counter}")
                    
                cols[1].text_input("Level", value=level, disabled=True, key=f"level_{entry_counter}")
                    
                month = cols[2].text_input("Month", value=current_month, disabled=True, key=f"month_{entry_counter}")
                cv = cols[3].number_input("CV(%)", min_value=0.0, max_value=100.0, key=f"cv_{entry_counter}")
                
                n_qc_key = f"n_{parameter}_{level}"
                current_n_qc = st.session_state.parameter_n_qc.get(n_qc_key, default_n_qc)
                n_qc = cols[4].number_input(
                    "n(QC)", 
                    min_value=0, 
                    max_value=100, 
                    value=current_n_qc,
                    key=f"n_{entry_counter}",
                    on_change=lambda p=parameter, l=level, k=f"n_{entry_counter}": st.session_state.parameter_n_qc.update({f"n_{p}_{l}": st.session_state[k]})
                )
            
                wd = cols[5].number_input(
                    "Working_Days", 
                    min_value=1, 
                    max_value=31, 
                    value=default_wd,
                    disabled=True, 
                    key=f"wd_{entry_counter}"
                )
                    
                ratio = round(n_qc / wd, 2) if n_qc > 0 and wd > 0 else 0.0
                    
                ratio_error = validate_ratio(n_qc, wd, parameter, level, current_month)
                if ratio_error:
                    validation_errors.append(ratio_error)

                cols[6].number_input("Ratio", value=ratio, disabled=True, key=f"ratio_{entry_counter}")

                existing_count = check_existing_parameter_month(lab, parameter, current_month, level)
                if existing_count > 0:
                    validation_errors.append(f" {parameter} - {level} for {current_month} already exists!")
                
                existing_ratio = get_parameter_ratio(lab, parameter, current_month)
                if existing_ratio is not None and ratio != existing_ratio:
                    if (parameter, current_month) not in seen_ratio_errors:
                        validation_errors.append(f"Ratio for {parameter} in {current_month} must be the same for both levels!")
                        seen_ratio_errors.add((parameter, current_month))

                input_data.append({
                    "Lab": lab,
                    "Parameter": parameter,
                    "Level": level,
                    "Month": current_month,
                    "CV(%)": cv,
                    "n(QC)": n_qc,
                    "Working_Days": wd,
                    "Ratio": ratio
                })
                
                entry_counter += 1

        df = pd.DataFrame()
        for data in input_data:
            if data["n(QC)"] > 0 and data["Working_Days"] > 0:
                ratio = data["n(QC)"] / data["Working_Days"]
                if ratio >= 1:
                    df = pd.concat([df, pd.DataFrame([data])], ignore_index=True)
        
        st.subheader("Preview of Valid Entries")
        if not df.empty:
            st.dataframe(df)
        else:
            st.info("No valid entries with ratio ≥ 1")
        
        
        if validation_errors:
            st.error("🚫 Validation Errors:")
            for error in validation_errors:
                st.write(f"- {error}")
        
        if not view_df.empty:
            csv_data = view_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Download Submitted Data",
                data=csv_data,
                file_name=f"{lab}_llkk_data_entry.csv",
                mime="text/csv",
                key="download_submitted_data"
            )
        else:
            st.info("No submitted data available to download")

        submission_key = f"submission_made_{lab}"  

        if submission_key not in st.session_state:
            st.session_state[submission_key] = False

        if not st.session_state[submission_key]:
            if st.button("💾 Submit to battle", disabled=bool(validation_errors)):
                if validation_errors:
                    st.error("🚫 Please fix validation errors before submitting!")
                    st.session_state[submission_key] = False
                else:
                    st.session_state[submission_key] = True  
                    if not df.empty:
                        final_level_errors = validate_both_levels_submitted(input_data)
                        if final_level_errors:
                            st.error("🚫 Level submission errors:")
                            for error in final_level_errors:
                                st.write(f"- {error}")
                            st.session_state[submission_key] = False
                        else:
                            conn = get_connection()
                            cursor = conn.cursor()
                            saved_rows = 0

                            for _, row in df.iterrows():
                                cursor.execute("""
                                    INSERT INTO submissions 
                                    (Lab, Parameter, Level, Month, `CV(%)`, `n(QC)`, `Working_Days`, Ratio)
                                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                                """, (
                                    row["Lab"], row["Parameter"], row["Level"], row["Month"],
                                    row["CV(%)"], row["n(QC)"], row["Working_Days"], row["Ratio"]
                                ))
                                saved_rows += 1

                            conn.commit()
                            cursor.close()
                            conn.close()

                            if saved_rows > 0:
                                st.success(f"✅ Data saved and submitted into battlefield successfully !")
                                time.sleep(3)
                                
                                st.session_state.parameter_n_qc = {}
                                
                                st.rerun()
                    else:
                        st.warning("⚠️ Please complete all fields before submitting.")
                        st.session_state[submission_key] = False  
        else:
            st.button("💾 Submit to battle", disabled=True, help="Submission already made. Refresh page to submit again.")
    
    elif all_data_complete and not st.session_state.edit_mode:
        st.info("The data entry form is hidden because all required parameters have been submitted.")
        
        if not view_df.empty:
            csv_data = view_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Download Submitted Data",
                data=csv_data,
                file_name=f"{lab}_llkk_data_entry.csv",
                mime="text/csv",
                key="download_submitted_data"
            )
        else:
            st.info("No submitted data available to download")

if __name__ == "__main__":
    run()