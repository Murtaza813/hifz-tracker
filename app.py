# =========================================================================
# HIFZ TRACKER - CLEAN VERSION
# =========================================================================

import streamlit as st
import pandas as pd
import numpy as np
import os
from datetime import datetime, timedelta
import io
import re
import altair as alt
import plotly.express as px
import plotly.graph_objects as go

from database import (
    init_db, 
    get_all_students, 
    get_student_data, 
    get_all_student_sessions,
    export_student_to_excel, 
    student_exists,
    save_student_from_excel,
    get_data_format_info,
    get_last_jadeed_page,
    get_google_sheet  # ← ADD THIS
)
from excel_handler import (
    parse_excel_file, 
    calculate_juzhali_range, 
    get_murajaat_available_pages, 
    convert_df_for_dashboard, 
    create_sample_excel_template
)

st.set_page_config(page_title="Hifz Progress Tracker", layout="wide", page_icon="📖")

# =========================================================================
# 🔐 ACCESS CODE PROTECTION SYSTEM - SECURE VERSION (FIXED)
# =========================================================================

def check_access_code():
    """Returns `True` if user enters correct access code"""
    
    def code_entered():
        # ✅ FIX: Check if access_code exists in session state first
        if "access_code" in st.session_state and st.session_state["access_code"] == "Aaliquader53":
            st.session_state["access_correct"] = True
            # Don't delete access_code yet, just mark as correct
        else:
            st.session_state["access_correct"] = False

    # Initialize session state variables
    if "access_correct" not in st.session_state:
        st.session_state.access_correct = False
    if "access_code" not in st.session_state:
        st.session_state.access_code = ""

    # First run - show access code input
    if not st.session_state.access_correct:
        st.title("🔐 Hifz Tracker - Access Required")
        st.markdown("---")
        
        col1, col2 = st.columns([2, 1])
        with col1:
            st.text_input(
                "Enter Access Code", 
                type="password", 
                key="access_code",
                placeholder="Enter the secret access code...",
                label_visibility="collapsed"
            )
        with col2:
            st.button("🚀 Enter", on_click=code_entered, use_container_width=True)
        
        # Show error if code was wrong
        if "access_correct" in st.session_state and not st.session_state.access_correct and st.session_state.access_code:
            st.error("❌ **Incorrect access code**")
        
        st.markdown("---")
        st.info("💡 **Contact administrator for access code**")
        return False
    
    # Correct code - show app
    else:
        st.sidebar.success("🔓 Access Granted! Welcome to Hifz Tracker!")
        return True

# =========================================================================
# CUSTOM CSS FOR BEAUTIFUL UI (UPDATED WITH BETTER SIDEBAR)
# =========================================================================

st.markdown("""
<style>
    /* Main color scheme */
    :root {
        --primary-color: #1e3a8a;
        --secondary-color: #3b82f6;
        --success-color: #10b981;
        --warning-color: #f59e0b;
        --danger-color: #ef4444;
        --light-bg: #f8fafc;
    }
    
    /* Sidebar improvements */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1e3a8a 0%, #1e40af 50%, #3b82f6 100%);
    }
    
    /* Sidebar section headers */
    [data-testid="stSidebar"] h3 {
        background: rgba(255, 255, 255, 0.1);
        padding: 12px 15px;
        border-radius: 10px;
        margin: 15px 0 10px 0;
        font-size: 1.1em;
        border-left: 4px solid #fbbf24;
        backdrop-filter: blur(10px);
        color: white !important;
    }
    
    /* Sidebar buttons */
    [data-testid="stSidebar"] .stButton button {
        background: linear-gradient(135deg, #10b981 0%, #059669 100%);
        color: white !important;
        border: 2px solid rgba(255, 255, 255, 0.3);
        border-radius: 10px;
        padding: 12px 20px;
        font-weight: 600;
        transition: all 0.3s ease;
        width: 100%;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.2);
    }
    
    [data-testid="stSidebar"] .stButton button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(0, 0, 0, 0.3);
        background: linear-gradient(135deg, #059669 0%, #047857 100%);
    }
    
    /* Sidebar file uploader - IMPROVED VISIBILITY */
    [data-testid="stSidebar"] .stFileUploader {
        background: rgba(255, 255, 255, 0.15);
        padding: 15px;
        border-radius: 10px;
        border: 2px dashed rgba(255, 255, 255, 0.5);
        backdrop-filter: blur(10px);
    }
    
    [data-testid="stSidebar"] .stFileUploader label {
        color: white !important;
        font-size: 1em !important;
        font-weight: 700 !important;
        text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.3);
    }
    
    [data-testid="stSidebar"] .stFileUploader section {
        background: rgba(255, 255, 255, 0.2) !important;
        border: 2px dashed rgba(255, 255, 255, 0.5) !important;
        border-radius: 8px;
    }
    
    [data-testid="stSidebar"] .stFileUploader section small {
        color: rgba(255, 255, 255, 0.95) !important;
        font-weight: 500 !important;
    }
    
    [data-testid="stSidebar"] .stFileUploader button {
        background: rgba(255, 255, 255, 0.2) !important;
        color: white !important;
        border: 1px solid rgba(255, 255, 255, 0.4) !important;
    }
    
    /* CRITICAL FIX: Sidebar text input - DARK TEXT ON WHITE BACKGROUND */
    [data-testid="stSidebar"] .stTextInput > div > div > input {
        background-color: white !important;
        color: #1f2937 !important;
        border: 2px solid rgba(255, 255, 255, 0.6) !important;
        border-radius: 8px !important;
        padding: 12px 15px !important;
        font-size: 1em !important;
        font-weight: 600 !important;
    }
    
    [data-testid="stSidebar"] .stTextInput > div > div > input::placeholder {
        color: #9ca3af !important;
    }
    
    [data-testid="stSidebar"] .stTextInput > div > div > input:focus {
        border-color: #10b981 !important;
        box-shadow: 0 0 0 3px rgba(16, 185, 129, 0.4) !important;
        background-color: white !important;
        outline: none !important;
    }
    
    [data-testid="stSidebar"] .stTextInput label {
        color: white !important;
        font-weight: 700 !important;
        font-size: 1em !important;
        margin-bottom: 8px !important;
        text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.3);
    }
    
    /* CRITICAL FIX: Sidebar selectbox/dropdown - DARK TEXT ON WHITE BACKGROUND */
    [data-testid="stSidebar"] .stSelectbox {
        background: rgba(255, 255, 255, 0.1);
        padding: 10px;
        border-radius: 10px;
        backdrop-filter: blur(10px);
    }
    
    [data-testid="stSidebar"] .stSelectbox label {
        color: white !important;
        font-weight: 700 !important;
        font-size: 1em !important;
        text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.3);
    }
    
    /* Fix selectbox input field */
    [data-testid="stSidebar"] .stSelectbox > div > div {
        background-color: white !important;
    }
    
    [data-testid="stSidebar"] .stSelectbox > div > div > div {
        color: #1f2937 !important;
        background-color: white !important;
    }
    
    [data-testid="stSidebar"] .stSelectbox input {
        color: #1f2937 !important;
        background-color: white !important;
    }
    
    /* Fix the selected value display */
    [data-testid="stSidebar"] .stSelectbox [data-baseweb="select"] > div {
        background-color: white !important;
        border: 2px solid rgba(255, 255, 255, 0.6) !important;
        border-radius: 8px !important;
    }
    
    [data-testid="stSidebar"] .stSelectbox [data-baseweb="select"] > div > div {
        color: #1f2937 !important;
        font-weight: 600 !important;
    }
    
    /* Fix dropdown arrow icon */
    [data-testid="stSidebar"] .stSelectbox svg {
        fill: #1f2937 !important;
    }
    
    /* Fix dropdown menu when opened */
    [data-testid="stSidebar"] [role="listbox"] {
        background-color: white !important;
    }
    
    [data-testid="stSidebar"] [role="option"] {
        color: #1f2937 !important;
        background-color: white !important;
    }
    
    [data-testid="stSidebar"] [role="option"]:hover {
        background-color: #f3f4f6 !important;
    }
    
    /* Sidebar radio buttons */
    [data-testid="stSidebar"] .stRadio {
        background: rgba(255, 255, 255, 0.05);
        padding: 10px;
        border-radius: 10px;
    }
    
    [data-testid="stSidebar"] .stRadio > div {
        gap: 8px;
    }
    
    [data-testid="stSidebar"] .stRadio label {
        background: rgba(255, 255, 255, 0.1);
        padding: 10px 15px;
        border-radius: 8px;
        transition: all 0.3s ease;
        cursor: pointer;
        backdrop-filter: blur(5px);
        font-weight: 600 !important;
        color: white !important;
    }
    
    [data-testid="stSidebar"] .stRadio label:hover {
        background: rgba(255, 255, 255, 0.2);
        transform: translateX(5px);
    }
    
    /* Sidebar metrics */
    [data-testid="stSidebar"] [data-testid="stMetric"] {
        background: rgba(255, 255, 255, 0.1);
        padding: 12px;
        border-radius: 10px;
        border-left: 4px solid #10b981;
        backdrop-filter: blur(10px);
        margin: 8px 0;
    }
    
    [data-testid="stSidebar"] [data-testid="stMetricLabel"] {
        font-size: 0.9em;
        font-weight: 600;
        color: white !important;
    }
    
    [data-testid="stSidebar"] [data-testid="stMetricValue"] {
        font-size: 1.5em;
        font-weight: bold;
        color: white !important;
    }
    
    /* Sidebar divider */
    [data-testid="stSidebar"] hr {
        border: none;
        height: 2px;
        background: linear-gradient(90deg, transparent, rgba(255,255,255,0.3), transparent);
        margin: 20px 0;
    }
    
    /* Sidebar info/success/error boxes */
    [data-testid="stSidebar"] .stAlert {
        background: rgba(255, 255, 255, 0.15);
        border-radius: 8px;
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.2);
    }
    
    /* Make labels white but keep form inputs dark */
    [data-testid="stSidebar"] p {
        color: white;
    }
    
    /* Metric cards */
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 15px;
        color: white;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        text-align: center;
        margin: 10px 0;
    }
    
    /* Health score cards */
    .health-card {
        padding: 25px;
        border-radius: 15px;
        text-align: center;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        margin: 15px 0;
        transition: transform 0.3s ease;
    }
    
    .health-card:hover {
        transform: translateY(-5px);
    }
    
    .health-excellent {
        background: linear-gradient(135deg, #10b981 0%, #059669 100%);
        color: white;
    }
    
    .health-good {
        background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
        color: white;
    }
    
    .health-warning {
        background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
        color: white;
    }
    
    .health-critical {
        background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
        color: white;
    }
    
    /* Page status boxes */
    .page-box {
        padding: 15px;
        border-radius: 10px;
        text-align: center;
        margin: 5px;
        transition: all 0.3s ease;
        cursor: pointer;
        min-height: 85px;
        display: flex;
        flex-direction: column;
        justify-content: center;
    }
    
    .page-box:hover {
        transform: scale(1.05);
        box-shadow: 0 5px 15px rgba(0,0,0,0.2);
    }
    
    /* Info sections */
    .info-section {
        background: linear-gradient(135deg, #e0f2fe 0%, #bae6fd 100%);
        padding: 20px;
        border-radius: 10px;
        border-left: 5px solid #0284c7;
        margin: 15px 0;
    }
    
    /* Success sections */
    .success-section {
        background: linear-gradient(135deg, #d1fae5 0%, #a7f3d0 100%);
        padding: 20px;
        border-radius: 10px;
        border-left: 5px solid #059669;
        margin: 15px 0;
    }
    
    /* Section headers */
    .section-header {
        background: linear-gradient(90deg, #1e3a8a 0%, #3b82f6 100%);
        color: white;
        padding: 15px 25px;
        border-radius: 10px;
        margin: 20px 0 10px 0;
        font-size: 1.2em;
        font-weight: bold;
    }
    
    /* Streamlit button styling */
    .stButton>button {
        border-radius: 10px;
        padding: 10px 25px;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(0,0,0,0.2);
    }
</style>
""", unsafe_allow_html=True)

# =========================================================================
# STANDARDIZED MISTAKE TERMINOLOGY
# =========================================================================

STANDARD_AHKAAM = [
    'N/A', 'Ghunnah (missed)', 'Madd (shortened)', 'Ikhfa (misapplied)',
    'Idghaam (misapplied)', 'Izhar (misapplied)', 'Qalqalah (missed)',
    'Waqf/Ibtidaa (Incorrect stop/start)', 'Sifaat (Weak/Incorrect)'
]

STANDARD_MAKHARIJ = [
    'N/A', 'Qaf (ق)', 'Kaf (ك)', 'Daad (ض)', 'Dhaal (ذ)', 'Thaa (ث)',
    'Seen (س)', 'Saad (ص)', 'Zaa (ظ)', 'Haa (ح) - Throat Error',
    'Ayn (ع) - Throat Error', 'Other/General Letter Error'
]

STANDARD_HIFZ_MISTAKES = [
    'N/A', 'Skipped Ayah', 'Word Swap', 'Forgot Next Ayah',
    'Similar Ayah Confusion', 'Context Error', 'Tarteeb Error',
    'Beginning of Page Difficulty', 'General Hifz Weakness'
]

# =========================================================================
# INITIALIZE SESSION STATE
# =========================================================================

def init_session_state():
    """Initialize session state with database"""
    init_db()
    
    if "selected_student_id" not in st.session_state:
        st.session_state.selected_student_id = None
    
    if "student_data_df" not in st.session_state:
        st.session_state.student_data_df = None
    
    if "juzhali_length" not in st.session_state:
        st.session_state.juzhali_length = 10

init_session_state()

# =========================================================================
# HELPER FUNCTIONS
# =========================================================================

def grade_to_numeric(grade):
    """Convert grade to numeric score - FIXED FOR ARABIC GRADES"""
    if pd.isna(grade):
        return np.nan
    
    if isinstance(grade, (int, float)):
        return float(grade)
    
    grade_str = str(grade).strip()
    
    # Try to convert directly to float first
    try:
        return float(grade_str)
    except ValueError:
        pass
    
    # Handle Arabic and English grade texts
    grade_lower = grade_str.lower()
    
    # Arabic grade mappings
    if 'جيد جدا' in grade_str or 'jayyid jiddan' in grade_lower or 'excellent' in grade_lower:
        return 10  # ✅ Excellent = 10/10
    elif 'جيد' in grade_str or 'jayyid' in grade_lower or 'good' in grade_lower:
        return 8   # ✅ Good = 8/10  
    elif 'متوسط' in grade_str or 'mutawassit' in grade_lower or 'average' in grade_lower:
        return 6   # ✅ Average = 6/10
    elif 'ضعيف' in grade_str or "da'eef" in grade_lower or 'weak' in grade_lower:
        return 4   # ✅ Weak = 4/10
    
    return np.nan  # Could not convert 

def score_to_grade_status(score):
    """Convert score to grade status with emoji"""
    if score >= 3.5: 
        return "Excellent 🌟"
    elif score >= 2.5: 
        return "Good ✅"
    elif score >= 1.5: 
        return "Average 🟡"
    elif score > 0: 
        return "Weak ❌"
    return "N/A"

def get_health_color_class(score):
    """Get CSS class based on health score"""
    if score >= 80:
        return "health-excellent"
    elif score >= 60:
        return "health-good"
    elif score >= 40:
        return "health-warning"
    else:
        return "health-critical"

def get_health_message(score):
    """Get health status message"""
    if score >= 80:
        return "EXCELLENT RETENTION 💪"
    elif score >= 60:
        return "GOOD PROGRESS ✅"
    elif score >= 40:
        return "NEEDS ATTENTION ⚠️"
    else:
        return "CRITICAL - REQUIRES FOCUS 🚨"

def safe_column_access(df, column_name, default_value=None):
    """Safely access DataFrame columns that might not exist"""
    if column_name in df.columns:
        return df[column_name]
    else:
        # Return a series with default value (same length as df)
        return pd.Series([default_value] * len(df), index=df.index)

def safe_column_access(df, column_name, default_value=None):
    """Safely access DataFrame columns that might not exist"""
    if column_name in df.columns:
        return df[column_name]
    else:
        # Return a series with default value (same length as df)
        return pd.Series([default_value] * len(df), index=df.index)

def is_detailed_data_available(df):
    """Check if DataFrame has detailed session columns"""
    required_columns = ['Core_Mistake', 'Specific_Mistake', 'Mistake_Count', 'Tambeeh_Count']
    return all(col in df.columns for col in required_columns)

def get_data_format_type(df):
    """Determine if data is uploaded (basic) or detailed format"""
    if is_detailed_data_available(df):
        return 'detailed'
    else:
        return 'uploaded'

def show_detailed_data_message():
    """Show consistent message for uploaded data"""
    st.markdown("""
    <div class="info-section">
        <h4>📊 Detailed Analytics Available</h4>
        <p>Start entering sessions using the web forms to unlock:</p>
        <ul>
            <li>🔍 Mistake breakdowns (Talqeen/Tambeeh)</li>
            <li>🎯 Technical focus areas</li> 
            <li>📈 Advanced health scores</li>
            <li>⚠️ Weak page detection</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

# =========================================================================
# JADEED-JUZHALI CONNECTION FUNCTIONS
# =========================================================================

def get_juzhali_last_page(student_data):
    """Fetch the last page from Juzhali sessions"""
    if student_data is None or student_data.empty:
        return None
    
    session_type_col = 'Session_Type' if 'Session_Type' in student_data.columns else 'session_type'
    juzhali_data = student_data[student_data[session_type_col] == 'Juzhali']
    
    if juzhali_data.empty:
        return None
    
    try:
        date_col = 'Date' if 'Date' in student_data.columns else 'date'
        latest_juzhali = juzhali_data.sort_values(date_col, ascending=False).iloc[0]
        
        if 'Page_Range' in latest_juzhali and pd.notna(latest_juzhali['Page_Range']):
            return int(latest_juzhali['Page_Range'])
        elif 'Page' in latest_juzhali and pd.notna(latest_juzhali['Page']):
            return int(latest_juzhali['Page'])
        elif 'juzhali_page' in latest_juzhali and pd.notna(latest_juzhali['juzhali_page']):
            return int(latest_juzhali['juzhali_page'])
        else:
            return None
    except:
        return None

def calculate_jadeed_progress(all_jadeed_data):
    """Calculate total pages and ayahs completed"""
    if all_jadeed_data is None or all_jadeed_data.empty:
        return 0.0, 0.0
    
    total_pages = 0.0
    total_ayahs = 0.0
    
    session_col = 'Session_Type' if 'Session_Type' in all_jadeed_data.columns else 'session_type'
    mistake_col = 'Specific_Mistake' if 'Specific_Mistake' in all_jadeed_data.columns else 'specific_mistake'
    
    progress_entries = all_jadeed_data[
        (all_jadeed_data[session_col].str.lower() == 'jadeed') &
        (all_jadeed_data[mistake_col].fillna('').str.contains('Progress:', na=False))
    ]

    for _, row in progress_entries.iterrows():
        progress_text = str(row[mistake_col])
        
        page_match = re.search(r'Progress:.*?([\d.]+)\s*pages?', progress_text)
        if page_match:
            total_pages += float(page_match.group(1))
        
        ayah_match = re.search(r'(\d+)\s*ayahs?', progress_text)
        if ayah_match:
            total_ayahs += int(ayah_match.group(1))

    return total_pages, total_ayahs

def get_murajaat_available_pages(student_data):
    """Determine which pages are available for Murajaat"""
    
    last_jadeed_page = get_last_jadeed_page(student_data)
    
    if last_jadeed_page is None:
        return {}
    
    current_jadeed_sipara = ((last_jadeed_page - 1) // 20) + 1
    current_jadeed_page_in_sipara = ((last_jadeed_page - 1) % 20) + 1
    
    juzhali_length = st.session_state.get('juzhali_length', 10)
    juzhali_end_absolute = last_jadeed_page
    juzhali_start_absolute = max(1, juzhali_end_absolute - juzhali_length + 1)
    
    juzhali_start_sipara = ((juzhali_start_absolute - 1) // 20) + 1
    juzhali_start_page_in_sipara = ((juzhali_start_absolute - 1) % 20) + 1
    
    murajaat_pages = {}
    
    for sipara in range(1, juzhali_start_sipara):
        murajaat_pages[str(sipara)] = list(range(1, 21))
    
    if juzhali_start_sipara == current_jadeed_sipara:
        if juzhali_start_page_in_sipara > 1:
            murajaat_pages[str(current_jadeed_sipara)] = list(range(1, juzhali_start_page_in_sipara))
    
    return murajaat_pages

def calculate_jadeed_progress(all_jadeed_data):
    """Calculate total pages and ayahs completed"""
    if all_jadeed_data is None or all_jadeed_data.empty:
        return 0.0, 0.0
    
    total_pages = 0.0
    total_ayahs = 0.0
    
    # Check which column names exist
    session_col = 'Session_Type' if 'Session_Type' in all_jadeed_data.columns else 'session_type'
    mistake_col = 'Specific_Mistake' if 'Specific_Mistake' in all_jadeed_data.columns else 'specific_mistake'
    
    # Filter for Jadeed sessions with Progress
    progress_entries = all_jadeed_data[
        (all_jadeed_data[session_col].str.lower() == 'jadeed') &
        (all_jadeed_data[mistake_col].fillna('').str.contains('Progress:', na=False))
    ]

    for _, row in progress_entries.iterrows():
        progress_text = str(row[mistake_col])
        
        # Extract pages
        page_match = re.search(r'Progress:.*?([\d.]+)\s*pages?', progress_text)
        if page_match:
            total_pages += float(page_match.group(1))
        
        # Extract ayahs
        ayah_match = re.search(r'(\d+)\s*ayahs?', progress_text)
        if ayah_match:
            total_ayahs += int(ayah_match.group(1))

    return total_pages, total_ayahs

# =========================================================================
# END OF PART 1
# =========================================================================

# =========================================================================
# ANALYTICS DASHBOARD FUNCTION - FIXED VERSION
# =========================================================================

def run_analytics_dashboard(student_id):
    df = get_all_student_sessions(student_id)
    
    if df is None or len(df) == 0:
        st.warning("📭 No session data found for this student.")
        return
    
    # Fill None values
    if 'Mistake_Count' in df.columns:
        df['Mistake_Count'] = df['Mistake_Count'].fillna(0)
    if 'Tambeeh_Count' in df.columns:
        df['Tambeeh_Count'] = df['Tambeeh_Count'].fillna(0)
    
    # Separate data formats
    new_format_data = df[df['Data_Format'] == 'session_entry']
    old_format_data = df[df['Data_Format'] == 'upload']
    
    # Header
    st.markdown('<div class="section-header">📊 Student Progress Overview</div>', unsafe_allow_html=True)
    
    # Basic metrics
    total_sessions = len(df)
    mura_sessions = len(df[df['Session_Type'] == 'Murajaat'])
    juzhali_sessions = len(df[df['Session_Type'] == 'Juzhali'])
    jadeed_sessions = len(df[df['Session_Type'] == 'Jadeed'])
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <h3 style="margin:0;">📚</h3>
            <h2 style="margin:10px 0;">{total_sessions}</h2>
            <p style="margin:0;">Total Sessions</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-card" style="background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);">
            <h3 style="margin:0;">🔄</h3>
            <h2 style="margin:10px 0;">{mura_sessions}</h2>
            <p style="margin:0;">Murajaat Sessions</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="metric-card" style="background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);">
            <h3 style="margin:0;">🔄</h3>
            <h2 style="margin:10px 0;">{juzhali_sessions}</h2>
            <p style="margin:0;">Juzhali Sessions</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div class="metric-card" style="background: linear-gradient(135deg, #10b981 0%, #059669 100%);">
            <h3 style="margin:0;">✨</h3>
            <h2 style="margin:10px 0;">{jadeed_sessions}</h2>
            <p style="margin:0;">Jadeed Sessions</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Jadeed progress
    last_jadeed_page = get_last_jadeed_page(df)
    if last_jadeed_page:
        progress_percent = (last_jadeed_page / 604) * 100
        st.markdown(f"""
        <div class="success-section">
            <h3 style="margin:0 0 10px 0;">📖 Current Jadeed Progress</h3>
            <h2 style="margin:0; color: #059669;">Page {last_jadeed_page} of 604</h2>
            <div style="background: #e5e7eb; border-radius: 10px; height: 20px; margin-top: 10px; overflow: hidden;">
                <div style="background: linear-gradient(90deg, #10b981 0%, #059669 100%); height: 100%; width: {progress_percent}%; transition: width 0.3s ease;"></div>
            </div>
            <p style="margin:5px 0 0 0; color: #059669; font-weight: bold;">{progress_percent:.1f}% Complete</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Health scores
    st.markdown('<div class="section-header">💪 Health Scores</div>', unsafe_allow_html=True)
    
    # Calculate health scores - USING MARK-BASED CALCULATION FOR MURAJAAT
    if not new_format_data.empty:
        # ✅ UPDATED: Murajaat health based on overall session marks
        mura_data = df[df['Session_Type'] == 'Murajaat']
        
        # Look for overall session marks (Session_Summary entries)
        mura_marks_data = mura_data[
            (mura_data['Core_Mistake'] == 'Session_Summary') & 
            (mura_data['Overall_Grade'].notna())
        ]
        
        if not mura_marks_data.empty:
            # Convert marks to numeric (they should already be 1-10)
            mura_marks = pd.to_numeric(mura_marks_data['Overall_Grade'], errors='coerce').dropna()
            
            if not mura_marks.empty:
                avg_mark = mura_marks.mean()
                mura_health = (avg_mark / 10) * 100  # Convert mark to percentage
            else:
                mura_health = None
        else:
            # Fallback: Use old Talqeen/Tambeeh calculation if no marks available
            if 'Mistake_Count' in mura_data.columns and 'Tambeeh_Count' in mura_data.columns:
                mura_total = mura_data['Mistake_Count'].sum() + mura_data['Tambeeh_Count'].sum()
                mura_talqeen = mura_data['Mistake_Count'].sum()
                mura_health = 100 * (1 - (mura_talqeen / mura_total)) if mura_total > 0 else None
            else:
                mura_health = None

        # ✅ UPDATED: Juzhali health for NEW FORMAT - Use Session_Summary grades
        juzhali_data = df[df['Session_Type'] == 'Juzhali']
        
        # Check if Core_Mistake column exists before using it
        if 'Core_Mistake' in juzhali_data.columns:
            session_summary_data = juzhali_data[
                (juzhali_data['Core_Mistake'] == 'Session_Summary') & 
                (juzhali_data['Overall_Grade'].notna())
            ]
        else:
            # If Core_Mistake doesn't exist, look for any Juzhali sessions with Overall_Grade
            session_summary_data = juzhali_data[juzhali_data['Overall_Grade'].notna()]

        if not session_summary_data.empty:
            juzhali_grades = session_summary_data['Overall_Grade'].apply(grade_to_numeric).dropna()
            if not juzhali_grades.empty:
                avg_grade = juzhali_grades.mean()
                juzhali_health = (avg_grade / 10) * 100
            else:
                juzhali_health = None
        else:
            juzhali_health = None
    else:
        # Old format: Grade-based
        mura_data = df[df['Session_Type'] == 'Murajaat']
        if not mura_data.empty and 'Overall_Grade' in mura_data.columns:
            valid_mura_grades = mura_data['Overall_Grade'].dropna()
            if not valid_mura_grades.empty:
                mura_grades = valid_mura_grades.apply(grade_to_numeric).dropna()
                if not mura_grades.empty:
                    avg_grade = mura_grades.mean()
                    mura_health = (avg_grade / 10) * 100
                else:
                    mura_health = None
            else:
                mura_health = None
        else:
            mura_health = None

        # ✅ FIXED: Juzhali health for OLD FORMAT - Look for ALL Juzhali grades (not just Session_Summary)
        juzhali_data = df[df['Session_Type'] == 'Juzhali']
        
        if not juzhali_data.empty and 'Overall_Grade' in juzhali_data.columns:
            # Get ALL Juzhali grades (not just Session_Summary entries)
            valid_juzhali_grades = juzhali_data['Overall_Grade'].dropna()
            
            if not valid_juzhali_grades.empty:
                # Convert Arabic grades to numeric
                juzhali_grades = valid_juzhali_grades.apply(grade_to_numeric).dropna()
                
                if not juzhali_grades.empty:
                    avg_grade = juzhali_grades.mean()
                    juzhali_health = (avg_grade / 10) * 100
                else:
                    juzhali_health = None
            else:
                juzhali_health = None
        else:
            juzhali_health = None
    
    # Display health scores
    col1, col2 = st.columns(2)
    
    with col1:
        if mura_health is not None:
            health_class = get_health_color_class(mura_health)
            health_msg = get_health_message(mura_health)
            st.markdown(f"""
            <div class="health-card {health_class}">
                <h3 style="margin:0 0 10px 0;">🔄 Murajaat Health</h3>
                <h1 style="margin:0;">{mura_health:.1f}%</h1>
                <p style="margin:10px 0 0 0; font-size: 1.1em;">{health_msg}</p>
                <div style="background: rgba(255,255,255,0.3); border-radius: 10px; height: 10px; margin-top: 15px; overflow: hidden;">
                    <div style="background: white; height: 100%; width: {mura_health}%; transition: width 0.3s ease;"></div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="info-section">
                <h4>🔄 Murajaat Health Score</h4>
                <p>No data available. Start recording Murajaat sessions!</p>
            </div>
            """, unsafe_allow_html=True)
    
    with col2:
        if juzhali_health is not None:
            health_class = get_health_color_class(juzhali_health)
            health_msg = get_health_message(juzhali_health)
            st.markdown(f"""
            <div class="health-card {health_class}">
                <h3 style="margin:0 0 10px 0;">🔄 Juzhali Health</h3>
                <h1 style="margin:0;">{juzhali_health:.1f}%</h1>
                <p style="margin:10px 0 0 0; font-size: 1.1em;">{health_msg}</p>
                <div style="background: rgba(255,255,255,0.3); border-radius: 10px; height: 10px; margin-top: 15px; overflow: hidden;">
                    <div style="background: white; height: 100%; width: {juzhali_health}%; transition: width 0.3s ease;"></div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="info-section">
                <h4>🔄 Juzhali Health Score</h4>
                <p>No data available. Start recording Juzhali sessions!</p>
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Data format notice
    if not old_format_data.empty and new_format_data.empty:
        st.markdown("""
        <div class="info-section">
            <p><strong>📊 Note:</strong> You're viewing basic session information from uploaded data. 
            For detailed analytics, start entering sessions using the web forms!</p>
        </div>
        """, unsafe_allow_html=True)
    elif not old_format_data.empty:
        st.markdown("""
        <div class="info-section">
            <p><strong>📊 Note:</strong> Some sessions are from uploaded data and don't include detailed mistake breakdowns.</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Detailed analytics (only for new format)
    if not new_format_data.empty:
        st.markdown('<div class="section-header">🔍 Detailed Mistake Analytics</div>', unsafe_allow_html=True)
        
        # Murajaat breakdown
        murajaat_data = new_format_data[new_format_data['Session_Type'] == 'Murajaat']
        if not murajaat_data.empty:
            total_mura_mistakes = murajaat_data['Mistake_Count'].sum() + murajaat_data['Tambeeh_Count'].sum()
            mura_talqeen = murajaat_data['Mistake_Count'].sum()
            mura_tambeeh = murajaat_data['Tambeeh_Count'].sum()
            
            st.markdown("**📋 Murajaat Mistake Breakdown**")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown(f"""
                <div style="background: #f3f4f6; padding: 15px; border-radius: 10px; text-align: center;">
                    <h3 style="color: #6b7280; margin: 0;">Total</h3>
                    <h2 style="color: #1f2937; margin: 10px 0;">{int(total_mura_mistakes)}</h2>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                st.markdown(f"""
                <div style="background: #fee2e2; padding: 15px; border-radius: 10px; text-align: center;">
                    <h3 style="color: #991b1b; margin: 0;">Talqeen</h3>
                    <h2 style="color: #dc2626; margin: 10px 0;">{int(mura_talqeen)}</h2>
                </div>
                """, unsafe_allow_html=True)
            
            with col3:
                st.markdown(f"""
                <div style="background: #fef3c7; padding: 15px; border-radius: 10px; text-align: center;">
                    <h3 style="color: #92400e; margin: 0;">Tambeeh</h3>
                    <h2 style="color: #f59e0b; margin: 10px 0;">{int(mura_tambeeh)}</h2>
                </div>
                """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Juzhali breakdown
        juzhali_data = new_format_data[new_format_data['Session_Type'] == 'Juzhali']
        if not juzhali_data.empty:
            total_juzhali_mistakes = juzhali_data['Mistake_Count'].sum() + juzhali_data['Tambeeh_Count'].sum()
            juzhali_talqeen = juzhali_data['Mistake_Count'].sum()
            juzhali_tambeeh = juzhali_data['Tambeeh_Count'].sum()
            
            st.markdown("**📋 Juzhali Mistake Breakdown**")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown(f"""
                <div style="background: #f3f4f6; padding: 15px; border-radius: 10px; text-align: center;">
                    <h3 style="color: #6b7280; margin: 0;">Total</h3>
                    <h2 style="color: #1f2937; margin: 10px 0;">{int(total_juzhali_mistakes)}</h2>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                st.markdown(f"""
                <div style="background: #fee2e2; padding: 15px; border-radius: 10px; text-align: center;">
                    <h3 style="color: #991b1b; margin: 0;">Talqeen</h3>
                    <h2 style="color: #dc2626; margin: 10px 0;">{int(juzhali_talqeen)}</h2>
                </div>
                """, unsafe_allow_html=True)
            
            with col3:
                st.markdown(f"""
                <div style="background: #fef3c7; padding: 15px; border-radius: 10px; text-align: center;">
                    <h3 style="color: #92400e; margin: 0;">Tambeeh</h3>
                    <h2 style="color: #f59e0b; margin: 10px 0;">{int(juzhali_tambeeh)}</h2>
                </div>
                """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Weak area detection
        st.markdown('<div class="section-header">⚠️ Weak Area Detection</div>', unsafe_allow_html=True)
        
        talqeen_data = new_format_data.copy()
        
        col1, col2 = st.columns(2)
        
        with col1:
            mura_sipara_weak = talqeen_data[
                (talqeen_data['Session_Type'] == 'Murajaat') & 
                (talqeen_data['Sipara'].notna())
            ].groupby('Sipara')['Mistake_Count'].sum().nlargest(3)
            
            if not mura_sipara_weak.empty:
                st.markdown("**🔴 Top 3 Weak Siparas (Murajaat)**")
                for sipara, mistakes in mura_sipara_weak.items():
                    st.markdown(f"""
                    <div style="background: #fee2e2; padding: 10px; border-radius: 8px; margin: 5px 0; border-left: 4px solid #dc2626;">
                        <strong>Sipara {sipara}:</strong> {int(mistakes)} Talqeen mistakes
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.success("✅ No weak Siparas detected")
        
        with col2:
            juzhali_page_weak = talqeen_data[
                (talqeen_data['Session_Type'] == 'Juzhali') & 
                (talqeen_data['Page'].notna())
            ].groupby('Page')['Mistake_Count'].sum().nlargest(3)
            
            if not juzhali_page_weak.empty:
                st.markdown("**🔴 Top 3 Weak Pages (Juzhali)**")
                for page, mistakes in juzhali_page_weak.items():
                    st.markdown(f"""
                    <div style="background: #fee2e2; padding: 10px; border-radius: 8px; margin: 5px 0; border-left: 4px solid #dc2626;">
                        <strong>Page {page}:</strong> {int(mistakes)} Talqeen mistakes
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.success("✅ No weak pages detected")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Session history
    st.markdown('<div class="section-header">📜 Session History</div>', unsafe_allow_html=True)
    
    if not df.empty:
        display_df = df[['Date', 'Session_Type', 'Sipara', 'Page', 'Overall_Grade', 'Notes']].copy()
        display_df = display_df.sort_values('Date', ascending=False)
        st.dataframe(display_df, use_container_width=True, height=300)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Download section
    st.markdown('<div class="section-header">⬇️ Download Data</div>', unsafe_allow_html=True)
    
    csv_data = df.to_csv(index=False)
    
    st.download_button(
        label="📥 Download Complete Data as CSV",
        data=csv_data,
        file_name=f"student_{student_id}_data.csv",
        mime="text/csv",
        use_container_width=True
    )

# =========================================================================
# END OF PART 2
# =========================================================================

# =========================================================================
# HELPER FUNCTION: DETECT MURAJAAT-AVAILABLE PAGES
# =========================================================================

def get_murajaat_available_pages(student_data):
    """
    Determine which pages are available for Murajaat based on Jadeed/Juzhali progression.
    
    Returns a dict: {sipara_number: [list of available pages]}
    
    Logic:
    - Get last Jadeed page to determine current sipara and page
    - Calculate Juzhali range (10 pages before Jadeed)
    - Pages BEFORE Juzhali = graduated to Murajaat
    - Completed siparas = all 20 pages available
    """
    
    # Get last Jadeed session
    last_jadeed_page = get_last_jadeed_page(student_data)
    
    if last_jadeed_page is None:
        # No Jadeed yet, no Murajaat pages available
        return {}
    
    # Determine which sipara the last Jadeed page belongs to
    # Each sipara has 20 pages: Sipara 1 = pages 1-20, Sipara 2 = 21-40, etc.
    current_jadeed_sipara = ((last_jadeed_page - 1) // 20) + 1
    current_jadeed_page_in_sipara = ((last_jadeed_page - 1) % 20) + 1
    
    # Calculate Juzhali range
    juzhali_length = st.session_state.get('juzhali_length', 10)
    juzhali_end_absolute = last_jadeed_page
    juzhali_start_absolute = max(1, juzhali_end_absolute - juzhali_length + 1)
    
    # Determine which sipara Juzhali starts in
    juzhali_start_sipara = ((juzhali_start_absolute - 1) // 20) + 1
    juzhali_start_page_in_sipara = ((juzhali_start_absolute - 1) % 20) + 1
    
    murajaat_pages = {}
    
    # 1. Add all COMPLETED siparas (all 20 pages available)
    for sipara in range(1, juzhali_start_sipara):
        murajaat_pages[str(sipara)] = list(range(1, 21))
    
    # 2. If Juzhali starts in a different sipara than Jadeed, 
    #    add pages from Juzhali's sipara that are BEFORE Juzhali window
    if juzhali_start_sipara < current_jadeed_sipara:
        # Pages in the Juzhali start sipara that are BEFORE Juzhali
        if juzhali_start_page_in_sipara > 1:
            murajaat_pages[str(juzhali_start_sipara)] = list(range(1, juzhali_start_page_in_sipara))
        
        # All pages from siparas BETWEEN Juzhali start and current Jadeed sipara
        for sipara in range(juzhali_start_sipara + 1, current_jadeed_sipara):
            murajaat_pages[str(sipara)] = list(range(1, 21))
        
        # Pages in the CURRENT Jadeed sipara that are BEFORE Juzhali
        if current_jadeed_sipara == current_jadeed_sipara and juzhali_start_page_in_sipara > 1:
            # This means Juzhali is within the same sipara
            graduated_pages_in_current = list(range(1, juzhali_start_page_in_sipara))
            if graduated_pages_in_current:
                murajaat_pages[str(current_jadeed_sipara)] = graduated_pages_in_current
    
    # 3. If Juzhali is within the SAME sipara as Jadeed
    elif juzhali_start_sipara == current_jadeed_sipara:
        # Pages BEFORE Juzhali window in the current sipara
        if juzhali_start_page_in_sipara > 1:
            murajaat_pages[str(current_jadeed_sipara)] = list(range(1, juzhali_start_page_in_sipara))
    
    return murajaat_pages


# =========================================================================
# MURAJAAT ASSISTANT FUNCTION - FIXED VERSION (WITH BOTH DATA FORMATS)
# =========================================================================

def run_murajaat_assistant(student_data_df, student_id):
    """Murajaat assistant for long-term review of graduated pages"""
    
    if student_data_df is None or student_data_df.empty:
        st.error("❌ No student data available.")
        return
    
    df = student_data_df.copy()
    
    # Header
    st.markdown("""
    <div style="text-align: center; padding: 30px 0;">
        <h1 style="color: #f59e0b; font-size: 3em; margin: 0;"> 
            🤖 Murajaat Assistant
        </h1>
        <p style="color: #1f2937; font-size: 1.2em; margin-top: 10px;">
            Long-term review of graduated pages • Auto-connected to your progress
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Get Murajaat-available pages
    murajaat_available = get_murajaat_available_pages(df)
    
    if not murajaat_available:
        st.markdown("""
        <div style="background: linear-gradient(135deg, #fee2e2 0%, #fecaca 100%); 
                    padding: 30px; border-radius: 15px; text-align: center; margin: 20px 0;">
            <h2 style="color: #dc2626; margin: 0 0 15px 0;">⚠️ No Pages Available for Murajaat Yet!</h2>
            <p style="color: #991b1b; font-size: 1.1em; margin: 10px 0;">
                Pages graduate to Murajaat when they fall out of the Juzhali window 
                (10 pages before Jadeed).
            </p>
            <div style="background: white; padding: 20px; border-radius: 10px; margin-top: 20px;">
                <h3 style="color: #059669;">💡 Getting Started:</h3>
                <p style="color: #374151;">
                    1. Start by recording <strong>Jadeed sessions</strong><br>
                    2. Once you have 11+ pages, the first page will graduate to Murajaat!<br>
                    3. Keep progressing in Jadeed to unlock more Murajaat pages
                </p>
            </div>
        </div>
        """, unsafe_allow_html=True)
        return
    
    # Get available siparas
    available_siparas = sorted([int(s) for s in murajaat_available.keys()])
    
    # Sipara selection
    st.markdown('<div class="section-header">📖 Select Sipara for Review</div>', unsafe_allow_html=True)
    
    col_select, col_info = st.columns([1, 2])
    
    with col_select:
        selected_sipara = st.selectbox(
            "Choose Sipara", 
            available_siparas,
            format_func=lambda x: f"Sipara {x}",
            label_visibility="collapsed"
        )
    
    with col_info:
        available_pages = murajaat_available[str(selected_sipara)]
        num_pages = len(available_pages)
        
        if num_pages == 20:
            st.markdown(f"""
            <div class="success-section">
                <h3 style="margin: 0;">✅ Sipara {selected_sipara}: Fully Completed</h3>
                <p style="margin: 5px 0 0 0;">All {num_pages} pages available for review</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="info-section">
                <h3 style="margin: 0;">🔗 Sipara {selected_sipara}: Partially Available</h3>
                <p style="margin: 5px 0 0 0;">
                    {num_pages} page{'s' if num_pages != 1 else ''} graduated from Juzhali 
                    (Pages {min(available_pages)}-{max(available_pages)})
                </p>
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # ✅ FIXED: Filter data for this sipara - Simple and clean
    # Convert Sipara to string for consistent comparison
    df['Sipara_Str'] = df['Sipara'].astype(str)
    sipara_data = df[
        (df['Session_Type'] == 'Murajaat') & 
        (df['Sipara_Str'] == str(selected_sipara))
    ]
    
        # =========================================================================
    # 📈 SIPARA PERFORMANCE OVERVIEW WITH TIMELINE CHART
    # =========================================================================
    st.markdown('<div class="section-header">📈 Sipara Performance Overview</div>', unsafe_allow_html=True)
    
    # Get ALL Murajaat data for THIS SIPARA (for timeline chart)
    timeline_data = df[
        (df['Session_Type'] == 'Murajaat') &
        (df['Sipara_Str'] == str(selected_sipara)) &
        (df['Overall_Grade'].notna())
    ].copy()
    
    if timeline_data.empty:
        st.info("📭 No Murajaat sessions recorded for this Sipara yet. Start recording sessions below to see performance analytics!")
    else:
        # Separate data formats
        uploaded_data = timeline_data[timeline_data['Data_Format'] == 'upload']
        detailed_data = timeline_data[timeline_data['Data_Format'] == 'session_entry']
        
        st.success(f"✅ Found {len(timeline_data)} Murajaat session(s) for Sipara {selected_sipara}")
        if len(uploaded_data) > 0:
            st.info(f"📥 {len(uploaded_data)} uploaded sessions")
        if len(detailed_data) > 0:
            st.info(f"✍️ {len(detailed_data)} detailed web entries")
        
        # =========================================================================
        # 📈 TIME-BASED PERFORMANCE CHART
        # =========================================================================
        
        # Convert to numeric marks
        timeline_data['Mark_Numeric'] = pd.to_numeric(timeline_data['Overall_Grade'], errors='coerce')
        valid_marks = timeline_data.dropna(subset=['Mark_Numeric', 'Date'])
        
        if len(valid_marks) > 0:
            # Sort by date
            valid_marks = valid_marks.sort_values('Date')
            
            # Calculate statistics
            total_sessions = len(valid_marks)
            avg_mark = valid_marks['Mark_Numeric'].mean()
            
            # Display statistics above chart
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("📅 Total Sessions", total_sessions)
            with col2:
                st.metric("📊 Average Mark", f"{avg_mark:.1f}/10")
            with col3:
                # Calculate trend (latest - oldest)
                if len(valid_marks) > 1:
                    oldest = valid_marks.iloc[0]['Mark_Numeric']
                    latest = valid_marks.iloc[-1]['Mark_Numeric']
                    trend = latest - oldest
                    st.metric("📈 Trend", f"{trend:+.1f}", delta=f"{trend:+.1f}")
                else:
                    st.metric("📈 Trend", "N/A")
            
            # Create line chart
            st.markdown("#### 📈 Sipara Performance Timeline")
            
            if len(valid_marks) > 1:
                # Prepare data for chart
                chart_data = valid_marks[['Date', 'Mark_Numeric', 'Data_Format']].copy()
                chart_data['Date'] = pd.to_datetime(chart_data['Date'])
                
                # Create figure
                import plotly.graph_objects as go
                fig = go.Figure()
                
                # Add line trace
                fig.add_trace(go.Scatter(
                    x=chart_data['Date'],
                    y=chart_data['Mark_Numeric'],
                    mode='lines+markers',
                    name='Performance',
                    line=dict(color='#3b82f6', width=3),
                    marker=dict(size=10, color='#3b82f6'),
                    hovertemplate='<b>Date:</b> %{x|%b %d}<br><b>Mark:</b> %{y}/10<extra></extra>'
                ))
                
                # Add horizontal reference lines
                fig.add_hline(y=8, line_dash="dash", line_color="green", 
                             annotation_text="Excellent (8+)", 
                             annotation_position="bottom right")
                fig.add_hline(y=6, line_dash="dash", line_color="orange", 
                             annotation_text="Average (6+)", 
                             annotation_position="bottom right")
                fig.add_hline(y=4, line_dash="dash", line_color="red", 
                             annotation_text="Needs Work", 
                             annotation_position="bottom right")
                
                # Update layout
                fig.update_layout(
                    title=f"Sipara {selected_sipara} Performance Over Time",
                    xaxis_title="Session Date",
                    yaxis_title="Mark (out of 10)",
                    yaxis=dict(range=[0, 10.5]),
                    hovermode='x unified',
                    template='plotly_white',
                    height=400
                )
                
                # Color code markers by data source
                uploaded_dates = chart_data[chart_data['Data_Format'] == 'upload']['Date']
                uploaded_marks = chart_data[chart_data['Data_Format'] == 'upload']['Mark_Numeric']
                
                session_dates = chart_data[chart_data['Data_Format'] == 'session_entry']['Date']
                session_marks = chart_data[chart_data['Data_Format'] == 'session_entry']['Mark_Numeric']
                
                if not uploaded_dates.empty:
                    fig.add_trace(go.Scatter(
                        x=uploaded_dates,
                        y=uploaded_marks,
                        mode='markers',
                        name='📥 Uploaded Data',
                        marker=dict(size=12, color='#10b981', symbol='square'),
                        hovertemplate='<b>Uploaded Data</b><br>Date: %{x|%b %d}<br>Mark: %{y}/10<extra></extra>'
                    ))
                
                if not session_dates.empty:
                    fig.add_trace(go.Scatter(
                        x=session_dates,
                        y=session_marks,
                        mode='markers',
                        name='✍️ Session Entry',
                        marker=dict(size=12, color='#f59e0b', symbol='circle'),
                        hovertemplate='<b>Session Entry</b><br>Date: %{x|%b %d}<br>Mark: %{y}/10<extra></extra>'
                    ))
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Data source legend
                st.markdown("""
                <div style="background: #f3f4f6; padding: 10px; border-radius: 8px; margin-top: 10px;">
                    <div style="display: flex; justify-content: center; gap: 20px; color: #6b7280;">
                        <div style="display: flex; align-items: center; gap: 5px;">
                            <div style="width: 12px; height: 12px; background: #10b981; border-radius: 2px;"></div>
                            <span>📥 Uploaded Excel Data</span>
                        </div>
                        <div style="display: flex; align-items: center; gap: 5px;">
                            <div style="width: 12px; height: 12px; background: #f59e0b; border-radius: 50%;"></div>
                            <span>✍️ Web Session Entry</span>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # Show data points table
                with st.expander("📋 View All Data Points", expanded=False):
                    display_data = valid_marks[['Date', 'Mark_Numeric', 'Data_Format']].copy()
                    display_data['Date'] = display_data['Date'].dt.strftime('%Y-%m-%d')
                    display_data['Data_Source'] = display_data['Data_Format'].map({
                        'upload': '📥 Uploaded',
                        'session_entry': '✍️ Session'
                    })
                    display_data = display_data.rename(columns={
                        'Mark_Numeric': 'Mark',
                        'Data_Source': 'Source'
                    })
                    st.dataframe(display_data[['Date', 'Mark', 'Source']], use_container_width=True)
            
            else:
                # Only one data point
                st.info(f"Only one data point available: **{valid_marks.iloc[0]['Mark_Numeric']}/10** on {valid_marks.iloc[0]['Date'].strftime('%b %d, %Y')}")
                st.write("Record more sessions to see performance trends!")
        
        else:
            st.info("No valid marks with dates available for charting.")
    
    st.markdown("<br>", unsafe_allow_html=True)

     # =========================================================================
    # 1. 📊 MURAJAAT RETENTION HEALTH SCORE (USES BOTH DATA SOURCES)
    # =========================================================================
    st.markdown(f'<div class="section-header">📊 Sipara {selected_sipara} Retention Health</div>', unsafe_allow_html=True)
    
    # Get ALL Murajaat data for THIS SIPARA (both uploaded and new entries)
    sipara_all_data = df[
        (df['Session_Type'] == 'Murajaat') &
        (df['Sipara_Str'] == str(selected_sipara)) &
        (df['Overall_Grade'].notna())
    ].copy()
    
    if not sipara_all_data.empty:
        # Separate data sources for analysis
        uploaded_data = sipara_all_data[sipara_all_data['Data_Format'] == 'upload']
        session_data = sipara_all_data[sipara_all_data['Data_Format'] == 'session_entry']
        
        st.info(f"📊 Using {len(uploaded_data)} uploaded marks + {len(session_data)} session marks")
        
        # Convert ALL Overall_Grade values to numeric (1-10)
        sipara_all_data['Mark_Numeric'] = pd.to_numeric(sipara_all_data['Overall_Grade'], errors='coerce')
        valid_marks = sipara_all_data.dropna(subset=['Mark_Numeric'])
        
        if not valid_marks.empty:
            # Calculate average from ALL valid marks
            avg_mark = valid_marks['Mark_Numeric'].mean()
            health_score = (avg_mark / 10) * 100
            
            # Determine health status
            if health_score >= 80:
                color = "#10b981"
                emoji = "✅"
                status = "Excellent Retention"
                message = "This sipara is very well retained!"
            elif health_score >= 70:
                color = "#3b82f6"
                emoji = "👍"
                status = "Good Retention"
                message = "Regular revision is working well."
            elif health_score >= 60:
                color = "#f59e0b"
                emoji = "⚠️"
                status = "Average Retention"
                message = "This sipara needs more focused revision."
            else:
                color = "#ef4444"
                emoji = "❌"
                status = "Needs Improvement"
                message = "Increase revision frequency."
            
            # Display health card
            col1, col2, col3 = st.columns([2, 1, 1])
            
            with col1:
                st.markdown(f"""
                <div style="background: linear-gradient(135deg, {color}15 0%, {color}30 100%);
                            border: 2px solid {color};
                            border-radius: 15px;
                            padding: 20px;
                            text-align: center;">
                    <div style="font-size: 1.2em; color: #6b7280; margin-bottom: 10px;">
                        Sipara {selected_sipara} Retention Health
                    </div>
                    <div style="display: flex; justify-content: center; align-items: center; gap: 15px; margin-bottom: 15px;">
                        <div style="font-size: 3em;">
                            {emoji}
                        </div>
                        <div>
                            <div style="font-size: 2.5em; font-weight: bold; color: {color};">
                                {avg_mark:.1f}/10
                            </div>
                            <div style="color: #374151; font-size: 1.1em;">
                                {status}
                            </div>
                        </div>
                    </div>
                    <div style="color: #6b7280; font-size: 0.9em; margin-top: 10px;">
                        Based on {len(valid_marks)} marks • {message}
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                # Show data source breakdown
                st.markdown("**📊 Data Sources**")
                
                if len(uploaded_data) > 0 and len(session_data) > 0:
                    st.success(f"✅ {len(uploaded_data)} uploaded")
                    st.success(f"✅ {len(session_data)} session")
                elif len(uploaded_data) > 0:
                    st.info(f"📥 {len(uploaded_data)} uploaded")
                else:
                    st.info(f"✍️ {len(session_data)} session")
            
            with col3:
                # Calculate average by data source
                if len(uploaded_data) > 0 and len(session_data) > 0:
                    uploaded_avg = pd.to_numeric(uploaded_data['Overall_Grade'], errors='coerce').mean()
                    session_avg = pd.to_numeric(session_data[session_data['Core_Mistake'] == 'Session_Summary']['Overall_Grade'], errors='coerce').mean()
                    
                    st.metric("📥 Uploaded Avg", f"{uploaded_avg:.1f}")
                    st.metric("✍️ Session Avg", f"{session_avg:.1f}")
            
            # Show trend if enough data
            if len(valid_marks) > 1:
                st.markdown("#### 📈 Performance Timeline")
                
                # Sort by date for timeline
                timeline_data = valid_marks.sort_values('Date')
                
                # Create simple timeline
                cols = st.columns(min(5, len(timeline_data)))
                for idx, (_, mark_row) in enumerate(timeline_data.iterrows()):
                    with cols[idx % 5]:
                        mark = mark_row['Mark_Numeric']
                        date_str = mark_row['Date'].strftime('%m/%d')
                        data_source = "📥" if mark_row['Data_Format'] == 'upload' else "✍️"
                        
                        # Color based on mark
                        if mark >= 8:
                            mark_color = "#10b981"
                        elif mark >= 7:
                            mark_color = "#3b82f6"
                        elif mark >= 6:
                            mark_color = "#f59e0b"
                        else:
                            mark_color = "#ef4444"
                        
                        st.markdown(f"""
                        <div style="background: {mark_color}15;
                                    border: 2px solid {mark_color};
                                    border-radius: 10px;
                                    padding: 12px;
                                    text-align: center;
                                    margin-bottom: 5px;">
                            <div style="color: #6b7280; font-size: 0.7em; margin-bottom: 5px;">
                                {data_source} {date_str}
                            </div>
                            <div style="font-size: 1.5em; font-weight: bold; color: {mark_color};">
                                {mark:.1f}
                            </div>
                            <div style="color: #6b7280; font-size: 0.7em;">
                                /10
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                
                # Show combined average
                st.info(f"**Combined Average: {avg_mark:.1f}/10** (from {len(uploaded_data)} uploaded + {len(session_data)} session marks)")
        
        else:
            st.warning("No valid numeric marks found in the data.")
    
    else:
        # NO DATA for this sipara
        st.info(f"""
        **📝 No Murajaat Data for Sipara {selected_sipara}**
        
        **To see retention health:**
        1. Upload Excel data with Murajaat marks (1-10)
        2. OR record new sessions with Overall Marks
        3. Both data sources will be combined!
        """)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
        # =========================================================================
    # 3. 🔍 MISTAKE PATTERN ANALYSIS - FIXED FOR YOUR COLUMN NAMES
    # =========================================================================
    st.markdown('<div class="section-header">🔍 Mistake Pattern Analysis</div>', unsafe_allow_html=True)
    
    # Check for detailed session data with mistake counts
    # FIX: Look for Mistake_Count and Tambeeh_Count (your actual column names!)
    if not sipara_data.empty and 'Mistake_Count' in sipara_data.columns and 'Tambeeh_Count' in sipara_data.columns:
        # Get detailed session entries (not Session_Summary)
        detailed_sessions = sipara_data[
            (sipara_data['Data_Format'] == 'session_entry') &
            (sipara_data['Core_Mistake'] != 'Session_Summary') &
            (sipara_data['Mistake_Count'].notna() | sipara_data['Tambeeh_Count'].notna())
        ]
        
        if not detailed_sessions.empty:
            # Calculate totals
            total_talqeen = detailed_sessions['Mistake_Count'].sum()
            total_tambeeh = detailed_sessions['Tambeeh_Count'].sum()
            total_mistakes = total_talqeen + total_tambeeh
            total_pages = len(detailed_sessions)
            
            st.success(f"✅ Analyzing {total_pages} detailed page entries")
            
            # Display metrics
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("🔴 Talqeen Mistakes", f"{int(total_talqeen)}")
                st.caption("Mistake_Count column")
            
            with col2:
                st.metric("🟡 Tambeeh Mistakes", f"{int(total_tambeeh)}")
                st.caption("Tambeeh_Count column")
            
            with col3:
                st.metric("📊 Total Mistakes", f"{int(total_mistakes)}")
            
            with col4:
                if total_pages > 0:
                    mistakes_per_page = total_mistakes / total_pages
                    st.metric("📈 Avg per Page", f"{mistakes_per_page:.1f}")
                else:
                    st.metric("📈 Avg per Page", "0.0")
            
            # Show detailed breakdown
            st.markdown("#### 📋 Page-by-Page Breakdown")
            
            # Create a table of pages with mistakes
            mistake_table = detailed_sessions[['Page', 'Mistake_Count', 'Tambeeh_Count']].copy()
            mistake_table = mistake_table.rename(columns={
                'Page': '📄 Page',
                'Mistake_Count': '🔴 Talqeen',
                'Tambeeh_Count': '🟡 Tambeeh'
            })
            
            # Calculate total per page
            mistake_table['📊 Total'] = mistake_table['🔴 Talqeen'] + mistake_table['🟡 Tambeeh']
            
            # Sort by total mistakes (highest first)
            mistake_table = mistake_table.sort_values('📊 Total', ascending=False)
            
            # Display as metrics
            st.dataframe(mistake_table, use_container_width=True)
            
            # Mistake ratio analysis
            if total_mistakes > 0:
                talqeen_percent = (total_talqeen / total_mistakes) * 100
                tambeeh_percent = (total_tambeeh / total_mistakes) * 100
                
                st.markdown("#### 📊 Mistake Ratio Analysis")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    # Talqeen ratio gauge
                    st.markdown(f"""
                    <div style="background: linear-gradient(135deg, #fee2e2 0%, #fecaca 100%);
                                border: 2px solid #ef4444;
                                border-radius: 10px;
                                padding: 20px;
                                text-align: center;
                                margin-bottom: 10px;">
                        <div style="color: #991b1b; font-size: 1.1em; margin-bottom: 10px;">
                            🔴 Talqeen Ratio
                        </div>
                        <div style="font-size: 2.5em; font-weight: bold; color: #dc2626;">
                            {talqeen_percent:.0f}%
                        </div>
                        <div style="color: #991b1b; font-size: 0.9em; margin-top: 10px;">
                            Memory/Recitation Errors
                        </div>
                        <div style="color: #dc2626; font-size: 0.8em; margin-top: 5px;">
                            {int(total_talqeen)} out of {int(total_mistakes)} mistakes
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col2:
                    # Tambeeh ratio gauge
                    st.markdown(f"""
                    <div style="background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
                                border: 2px solid #f59e0b;
                                border-radius: 10px;
                                padding: 20px;
                                text-align: center;
                                margin-bottom: 10px;">
                        <div style="color: #92400e; font-size: 1.1em; margin-bottom: 10px;">
                            🟡 Tambeeh Ratio
                        </div>
                        <div style="font-size: 2.5em; font-weight: bold; color: #d97706;">
                            {tambeeh_percent:.0f}%
                        </div>
                        <div style="color: #92400e; font-size: 0.9em; margin-top: 10px;">
                            Fluency/Smoothness Errors
                        </div>
                        <div style="color: #d97706; font-size: 0.8em; margin-top: 5px;">
                            {int(total_tambeeh)} out of {int(total_mistakes)} mistakes
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                
                # What does this mean?
                st.markdown("#### 💡 Analysis & Recommendations")
                
                # Show your specific data
                st.info(f"""
                **📊 Your Sipara 3 Mistake Analysis:**
                
                Based on {total_pages} pages reviewed:
                - **Total Mistakes:** {int(total_mistakes)}
                - **Talqeen (Memory):** {int(total_talqeen)} ({talqeen_percent:.0f}%)
                - **Tambeeh (Fluency):** {int(total_tambeeh)} ({tambeeh_percent:.0f}%)
                """)
                
                # Page-specific analysis
                st.markdown("**📄 Page-by-Page Analysis:**")
                for _, row in mistake_table.iterrows():
                    page = row['📄 Page']
                    tal = row['🔴 Talqeen']
                    tam = row['🟡 Tambeeh']
                    total = row['📊 Total']
                    
                    if total > 0:
                        if tal > tam:
                            issue = "Memory issues"
                        elif tam > tal:
                            issue = "Fluency issues"
                        else:
                            issue = "Balanced issues"
                        
                        st.write(f"- **Page {page}:** {tal}T/{tam}H → {issue}")
                
                # Recommendations based on ratios
                if talqeen_percent > 60:
                    st.warning("""
                    **🎯 Primary Issue: Memory Accuracy (Talqeen)**
                    
                    **Recommendations:**
                    1. Focus on memorization drills for weak pages
                    2. Break problematic verses into smaller sections
                    3. Increase repetition for accuracy
                    4. Use visualization techniques for memory retention
                    """)
                elif tambeeh_percent > 60:
                    st.warning("""
                    **🎯 Primary Issue: Reading Fluency (Tambeeh)**
                    
                    **Recommendations:**
                    1. Practice reading with proper tajweed rules
                    2. Work on connecting verses smoothly
                    3. Focus on breath control and pace
                    4. Listen to Qari recitations for rhythm
                    """)
                else:
                    st.info("""
                    **📊 Balanced Issues**
                    
                    **Work on both equally:**
                    1. Memory accuracy drills
                    2. Reading fluency practice
                    3. Regular revision schedule
                    """)
            
            else:
                st.success("🎉 **Perfect!** No mistakes recorded in detailed sessions.")
        
        else:
            st.info("""
            **📊 No Detailed Page Data Found**
            
            **To see mistake pattern analysis:**
            1. Make sure you're recording individual page entries (not just Session Summary)
            2. Enter Mistake_Count (Talqeen) and Tambeeh_Count for each page
            3. The analysis will appear here!
            
            **Debug Info:**
            - ✅ Found 'Mistake_Count' column
            - ✅ Found 'Tambeeh_Count' column  
            - ❌ No detailed page entries with these columns filled
            """)
    
    else:
        st.info("""
        **🔍 No Mistake Pattern Data Available**
        
        **Looking for columns:** 'Mistake_Count' and 'Tambeeh_Count'
        
        **Your data has these columns:**
        - ✅ Mistake_Count (Talqeen mistakes)
        - ✅ Tambeeh_Count (Tambeeh mistakes)
        - ✅ Core_Mistake (to filter out Session_Summary)
        
        **The analysis should work now!** If not, check:
        1. Do you have rows with Data_Format = 'session_entry'?
        2. Do those rows have Core_Mistake ≠ 'Session_Summary'?
        3. Are Mistake_Count and Tambeeh_Count filled with numbers?
        """)
    
    st.markdown("<br>", unsafe_allow_html=True)


    # =========================================================================
    # PAGE PERFORMANCE MAP
    # =========================================================================
    
    st.markdown('<div class="section-header">🗺️ Page Performance Map</div>', unsafe_allow_html=True)
    
    # Check if we have data
    if sipara_data.empty:
        st.warning(f"⚠️ No Murajaat data found for Sipara {selected_sipara}")
        st.info("Add session data below to see page performance")
    else:
        # Create page health map
        page_health_map = {}
        
        for page_num in available_pages:
            page_num_str = str(page_num)
            
            # Filter data for this page - CHECK BOTH FORMATS
            p_data = sipara_data[sipara_data['Page'].astype(str) == page_num_str]
            
            if p_data.empty:
                # No data for this page
                page_health_map[page_num] = {
                    "status": "untested", 
                    "color": "#e5e7eb", 
                    "text": "#9ca3af", 
                    "summary": "Not tested"
                }
            else:
                # We have data for this page
                status = "reviewed"
                color_code = "#dbeafe"
                font_color = "#1d4ed8"
                summary = "Reviewed"
                
                # Check for uploaded data grades first
                uploaded_grades = p_data[p_data['Data_Format'] == 'upload']['Overall_Grade']
                if not uploaded_grades.empty and not uploaded_grades.isna().all():
                    try:
                        avg_grade = float(uploaded_grades.iloc[0])
                        summary = f"Grade: {avg_grade:.1f}"
                        
                        # Apply the same grade-based color logic
                        if avg_grade >= 8:
                            status = "good"
                            color_code = "#d1fae5"
                            font_color = "#059669"
                        elif avg_grade >= 7:
                            status = "weak"
                            color_code = "#fef3c7"
                            font_color = "#d97706"
                        else:  # avg_grade < 7
                            status = "critical"
                            color_code = "#fee2e2"
                            font_color = "#dc2626"
                    except:
                        pass
                
                # ✅ CORRECTED: Check for detailed data mistakes with GRADE CALCULATION
                elif 'Mistake_Count' in p_data.columns and 'Tambeeh_Count' in p_data.columns:
                    detailed_data = p_data[p_data['Data_Format'] == 'session_entry']
                    if not detailed_data.empty:
                        talqeen_sum = detailed_data['Mistake_Count'].sum()
                        tambeeh_sum = detailed_data['Tambeeh_Count'].sum()
                        
                        # Calculate grade based on your rules
                        calculated_grade = 10 - (talqeen_sum * 1) - (tambeeh_sum * 0.5)
                        
                        # Format summary
                        summary = f"{int(talqeen_sum)}T/{int(tambeeh_sum)}H"
                        
                        # Determine color based on calculated grade
                        if calculated_grade >= 8:
                            status = "good"
                            color_code = "#d1fae5"
                            font_color = "#059669"
                            summary = f"{summary} ({calculated_grade:.1f})"
                        elif calculated_grade >= 7:
                            status = "weak"
                            color_code = "#fef3c7"
                            font_color = "#d97706"
                            summary = f"{summary} ({calculated_grade:.1f})"
                        else:  # calculated_grade < 7
                            status = "critical"
                            color_code = "#fee2e2"
                            font_color = "#dc2626"
                            summary = f"{summary} ({calculated_grade:.1f})"
                
                page_health_map[page_num] = {
                    "status": status, 
                    "color": color_code, 
                    "text": font_color, 
                    "summary": summary
                }
        
        # Display page map
        num_cols = 5
        num_rows = (len(available_pages) + num_cols - 1) // num_cols
        
        for row_idx in range(num_rows):
            cols = st.columns(num_cols)
            for col_idx in range(num_cols):
                page_idx = row_idx * num_cols + col_idx
                if page_idx >= len(available_pages):
                    break
                
                page_num = available_pages[page_idx]
                data = page_health_map[page_num]
                
                with cols[col_idx]:
                    st.markdown(f"""
                    <div class="page-box" style="background-color: {data['color']}; 
                                                border: 2px solid {data['text']};
                                                padding: 10px;
                                                border-radius: 8px;
                                                text-align: center;
                                                margin-bottom: 10px;
                                                min-height: 80px;
                                                display: flex;
                                                flex-direction: column;
                                                justify-content: center;">
                        <div style="color: {data['text']}; font-size: 1.2em; font-weight: bold;">
                            Page {page_num}
                        </div>
                        <div style="color: {data['text']}; font-size: 0.85em; margin-top: 5px;">
                            {data['summary']}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
    
    st.markdown("<br><br>", unsafe_allow_html=True)
    
    # Focus Areas
    st.markdown('<div class="section-header">🎯 Focus Areas</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**🔴 Weak Pages (Priority Review)**")
        
        if not sipara_data.empty:
            weak_pages = []
            for page_num, data in page_health_map.items():
                if data['status'] in ['critical', 'weak']:
                    weak_pages.append(page_num)
            
            if weak_pages:
                st.success(f"**Pages needing review:** {', '.join(map(str, sorted(weak_pages)))}")
            else:
                st.info("No weak pages detected")
        else:
            st.info("No session data available")
    
    with col2:
        st.markdown("**🕸️ Neglected Pages (Review Soon)**")
        
        if not sipara_data.empty and 'Date' in sipara_data.columns:
            # Simple logic: pages without recent data
            recent_pages = []
            try:
                sipara_data['Date'] = pd.to_datetime(sipara_data['Date'])
                recent_date = sipara_data['Date'].max()
                
                for page_num in available_pages:
                    page_data = sipara_data[sipara_data['Page'].astype(str) == str(page_num)]
                    if not page_data.empty:
                        page_latest = page_data['Date'].max()
                        if (recent_date - page_latest).days <= 7:
                            recent_pages.append(page_num)
            except:
                recent_pages = []
            
            neglected = sorted([p for p in available_pages if p not in recent_pages])
            
            if neglected:
                st.warning(f"**Pages not reviewed recently:** {', '.join(map(str, neglected[:5]))}")
            else:
                st.success("All pages reviewed recently")
        else:
            st.info("No date data available")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Rest of the function continues...
    
    # Technical focus (only for detailed format)
    detailed_data = sipara_data[sipara_data['Data_Format'] == 'session_entry']
    if not detailed_data.empty and 'Core_Mistake' in detailed_data.columns:
        st.markdown('<div class="section-header">🎯 Technical Focus Areas</div>', unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**🗣️ Makharij to Watch**")
            makh = detailed_data[detailed_data['Core_Mistake'] == 'Makharij']['Specific_Mistake'].value_counts().head(3)
            if not makh.empty:
                for letter, count in makh.items():
                    st.markdown(f"""
                    <div style="background: #dbeafe; padding: 10px; border-radius: 8px; 
                                margin: 5px 0; border-left: 3px solid #3b82f6;">
                        <strong style="color: #1e40af;">{letter}</strong>
                        <span style="color: #1e3a8a;"> • {int(count)} errors</span>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.success("✅ No Makharij issues recorded")
        
        with col2:
            st.markdown("**📏 Ahkaam to Watch**")
            taj = detailed_data[detailed_data['Core_Mistake'] == 'Tajweed']['Specific_Mistake'].value_counts().head(3)
            if not taj.empty:
                for rule, count in taj.items():
                    st.markdown(f"""
                    <div style="background: #dbeafe; padding: 10px; border-radius: 8px; 
                                margin: 5px 0; border-left: 3px solid #3b82f6;">
                        <strong style="color: #1e40af;">{rule}</strong>
                        <span style="color: #1e3a8a;"> • {int(count)} errors</span>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.success("✅ No Tajweed issues recorded")
        
        st.markdown("<br>", unsafe_allow_html=True)
    
    st.markdown('<div class="section-header">📝 Record New Session</div>', unsafe_allow_html=True)
    
    with st.form(key='murajaat_session_form'):
        col1, col2 = st.columns(2)
        with col1:
            session_date = st.date_input("📅 Session Date", datetime.now().date())
        with col2:
            session_type = st.selectbox("📋 Session Type", ['Murajaat', 'Tasmeel Juz'], index=0)
        
        st.markdown("---")
        
        selected_pages = st.multiselect(
            "📄 Select Pages Tested (in order)", 
            options=[str(p) for p in available_pages],
            help="Choose pages you reviewed in this session"
        )
        
        start_entry = st.form_submit_button("✅ Start Recording Mistakes", type="primary", use_container_width=True)
    
    # Initialize session state
    if 'mura_page_entries' not in st.session_state:
        st.session_state.mura_page_entries = {}
    
    if 'mura_session_started' not in st.session_state:
        st.session_state.mura_session_started = False
    
    if start_entry and selected_pages:
        st.session_state.mura_session_started = True
        st.session_state.mura_session_date = session_date
        st.session_state.mura_session_type = session_type
        st.session_state.mura_current_sipara = selected_sipara
        st.session_state.mura_selected_pages = selected_pages
        st.session_state.mura_page_entries = {}
    
    # Page-by-page entry
    if st.session_state.mura_session_started and hasattr(st.session_state, 'mura_selected_pages'):
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown('<div class="section-header">📄 Page-by-Page Entry</div>', unsafe_allow_html=True)
        
        for idx, page_num in enumerate(st.session_state.mura_selected_pages):
            with st.expander(f"📄 Page {page_num} - Question #{idx + 1}", expanded=(idx == 0)):
                
                col1, col2 = st.columns(2)
                with col1:
                    talqeen = st.number_input(
                        "🔴 Talqeen Mistakes", 
                        min_value=0, step=1, 
                        key=f'mura_talqeen_{page_num}_{idx}'
                    )
                with col2:
                    tambeeh = st.number_input(
                        "🟡 Tambeeh Mistakes", 
                        min_value=0, step=1, 
                        key=f'mura_tambeeh_{page_num}_{idx}'
                    )
                
                st.markdown("**📏 Tajweed Classification (Optional)**")
                col1, col2 = st.columns(2)
                with col1:
                    tajweed_mistake = st.selectbox(
                        "Ahkaam Error", 
                        STANDARD_AHKAAM, 
                        key=f'mura_ahkaam_{page_num}_{idx}'
                    )
                with col2:
                    tajweed_note = st.text_input(
                        "Additional Note", 
                        placeholder="Optional", 
                        key=f'mura_taj_note_{page_num}_{idx}'
                    )
                
                st.markdown("**🗣️ Makharij Classification (Optional)**")
                col1, col2 = st.columns(2)
                with col1:
                    makharij_mistake = st.selectbox(
                        "Makharij Error", 
                        STANDARD_MAKHARIJ, 
                        key=f'mura_makh_{page_num}_{idx}'
                    )
                with col2:
                    makharij_note = st.text_input(
                        "Additional Note", 
                        placeholder="Optional", 
                        key=f'mura_makh_note_{page_num}_{idx}'
                    )
                
                # Determine core mistake
                specific_details = []
                core_mistake = 'Hifz'
                
                if tajweed_mistake != 'N/A':
                    core_mistake = 'Tajweed'
                    detail = tajweed_mistake
                    if tajweed_note:
                        detail += f" ({tajweed_note})"
                    specific_details.append(detail)
                
                if makharij_mistake != 'N/A':
                    core_mistake = 'Makharij'
                    detail = makharij_mistake
                    if makharij_note:
                        detail += f" - {makharij_note}"
                    specific_details.append(detail)
                
                if tajweed_mistake != 'N/A' and makharij_mistake != 'N/A':
                    core_mistake = 'Mixed'
                
                specific_mistake_detail = "; ".join(specific_details) if specific_details else f"Page {page_num}"
                
                st.session_state.mura_page_entries[page_num] = {
                    'talqeen': talqeen,
                    'tambeeh': tambeeh,
                    'core_mistake': core_mistake,
                    'specific_mistake': specific_mistake_detail
                }
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # =========================================================================
        # ✅ NEW: OVERALL SESSION MARK SECTION (for Murajaat)
        # =========================================================================
        st.markdown('<div class="section-header">🎯 Overall Session Mark</div>', unsafe_allow_html=True)
        
        st.markdown("""
        <div style="background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%); 
                    padding: 20px; border-radius: 10px; margin-bottom: 20px;">
            <h4 style="color: #92400e; margin: 0 0 10px 0;">📊 Session Performance Summary</h4>
            <p style="color: #78350f; margin: 0;">
                Based on today's Murajaat performance across all pages, provide an overall mark (1-10).
                This mark will be used to calculate your Murajaat Health Score.
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            overall_mark = st.slider(
                "Overall Session Mark (1-10)",
                min_value=1,
                max_value=10,
                value=7,
                help="Overall evaluation of today's Murajaat session",
                key="mura_overall_mark_slider"  # ✅ Different key
            )
        
        with col2:
            # Show what this mark means for health score
            mark_to_health = {
                10: "100%",
                9: "90%",
                8: "80%",
                7: "70%",
                6: "60%",
                5: "50%",
                4: "40%",
                3: "30%",
                2: "20%",
                1: "10%"
            }
            st.markdown(f"""
            <div style="background: rgba(251, 191, 36, 0.2); 
                        padding: 15px; border-radius: 8px; text-align: center;
                        border: 2px solid #fbbf24;">
                <p style="margin: 0; color: #92400e; font-size: 0.9em;">Health Impact</p>
                <h3 style="margin: 5px 0 0 0; color: #d97706;">{mark_to_health[overall_mark]}</h3>
            </div>
            """, unsafe_allow_html=True)
        
        # Session notes
        session_notes = st.text_area(
            "Session Notes (Optional)",
            placeholder="Any observations about today's Murajaat session...",
            height=80,
            key="mura_session_notes_input"  # ✅ Different key
        )
        
        # Store overall mark in session state
        st.session_state.mura_overall_mark = overall_mark
        st.session_state.mura_session_notes = session_notes
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # =========================================================================
        # ✅ UPDATED SUBMIT BUTTON - SAVES OVERALL MARK
        # =========================================================================
        if st.button("💾 Submit Complete Session", type="primary", use_container_width=True):
            # Save logic
            try:
                from database import append_new_session
                
                # Save individual page entries
                for page_num, page_data in st.session_state.mura_page_entries.items():
                    session_data = {
                        'date': st.session_state.mura_session_date,
                        'sipara': st.session_state.mura_current_sipara,
                        'page_tested': page_num,
                        'talqeen_count': page_data['talqeen'],
                        'tambeeh_count': page_data['tambeeh'],
                        'core_mistake_type': page_data['core_mistake'],
                        'specific_mistake': page_data['specific_mistake'],
                        'overall_grade': None,  # Individual pages don't get marks
                        'notes': f"Page {page_num} - {st.session_state.mura_session_notes}" if st.session_state.mura_session_notes else f"Page {page_num}"
                    }
                    
                    # Save each page entry
                    append_new_session(student_id, st.session_state.mura_session_type, session_data)
                
                # ✅ Save OVERALL SESSION with mark
                overall_session_data = {
                    'date': st.session_state.mura_session_date,
                    'sipara': st.session_state.mura_current_sipara,
                    'page_tested': f"Pages {', '.join(st.session_state.mura_selected_pages)}",
                    'talqeen_count': 0,
                    'tambeeh_count': 0,
                    'core_mistake_type': 'Session_Summary',
                    'specific_mistake': 'Overall Session Evaluation',
                    'overall_grade': st.session_state.mura_overall_mark,  # ✅ Save the mark!
                    'notes': st.session_state.mura_session_notes or "Murajaat session completed"
                }
                
                append_new_session(student_id, st.session_state.mura_session_type, overall_session_data)
                
                # Reset session state
                st.session_state.mura_session_started = False
                st.session_state.mura_page_entries = {}
                st.session_state.mura_overall_mark = None
                st.session_state.mura_session_notes = None
                
                st.success(f"✅ Successfully recorded Murajaat session for {len(st.session_state.mura_selected_pages)} pages with mark: {st.session_state.mura_overall_mark}/10!")
                st.balloons()
                
                # Auto-refresh
                import time
                with st.spinner("Refreshing in 3 seconds..."):
                    time.sleep(3)
                
                st.rerun()
                
            except Exception as e:
                st.error(f"❌ Error saving session: {str(e)}")

# =========================================================================
# END OF PART 3
# =========================================================================

# =========================================================================
# JUZHALI ASSISTANT FUNCTION - UPDATED WITH OVERALL GRADE
# =========================================================================

def run_juzhali_assistant(student_data_df, student_id):
    """Juzhali assistant for rolling page revision"""
    
    if student_data_df is None or student_data_df.empty:
        st.error("❌ No student data available.")
        return
    
    df = student_data_df.copy()
    
    # Header
    st.markdown("""
    <div style="text-align: center; padding: 30px 0;">
        <h1 style="background: linear-gradient(90deg, #3b82f6 0%, #2563eb 100%); 
                   -webkit-background-clip: text; -webkit-text-fill-color: transparent;
                   font-size: 3em; margin: 0;">
            🔄 Juzhali Assistant
        </h1>
        <p style="color: #6b7280; font-size: 1.2em; margin-top: 10px;">
            Rolling 10-page revision before new Jadeed • Track retention & performance
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Auto-detect Juzhali range
    last_jadeed_page = get_last_jadeed_page(df)
    
    if last_jadeed_page is None:
        st.markdown("""
        <div style="background: linear-gradient(135deg, #fee2e2 0%, #fecaca 100%); 
                    padding: 30px; border-radius: 15px; text-align: center; margin: 20px 0;">
            <h2 style="color: #dc2626; margin: 0 0 15px 0;">⚠️ No Jadeed Sessions Found!</h2>
            <p style="color: #991b1b; font-size: 1.1em; margin: 10px 0;">
                Juzhali tracks the 10 pages BEFORE your current Jadeed page.
            </p>
            <div style="background: white; padding: 20px; border-radius: 10px; margin-top: 20px;">
                <h3 style="color: #3b82f6;">💡 Getting Started:</h3>
                <p style="color: #374151;">
                    Record your first <strong>Jadeed session</strong> to activate Juzhali tracking!
                </p>
            </div>
        </div>
        """, unsafe_allow_html=True)
        return
    
    if 'juzhali_length' not in st.session_state:
        st.session_state.juzhali_length = 10
    
    # Calculate range
    juzhali_end = last_jadeed_page
    juzhali_start = max(1, juzhali_end - st.session_state.juzhali_length + 1)
    
    # FIX 1: Define page_range_list here
    page_range_list = list(range(juzhali_start, juzhali_end + 1))
    
    # Display current range
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #dbeafe 0%, #bfdbfe 100%); 
                    padding: 20px; border-radius: 15px; border-left: 5px solid #3b82f6;">
            <h2 style="color: #1e40af; margin: 0 0 10px 0;">
                📖 Current Juzhali Range: Pages {juzhali_start} - {juzhali_end}
            </h2>
            <p style="color: #1e3a8a; margin: 5px 0;">
                🔗 Auto-connected: Last Jadeed = Page {juzhali_end} | {st.session_state.juzhali_length}-page window
            </p>
            <p style="color: #059669; margin: 5px 0; font-weight: bold;">
                ✅ Next Jadeed will start from Page {juzhali_end + 1}
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        if st.button("⚙️ Settings", use_container_width=True):
            st.session_state.show_juzhali_config = True
    
    # Configuration
    if st.session_state.get('show_juzhali_config', False):
        with st.expander("⚙️ Juzhali Configuration", expanded=True):
            st.markdown(f"""
            <div style="background: #f3f4f6; padding: 15px; border-radius: 10px; margin-bottom: 15px;">
                <p style="margin: 0; color: #374151;">
                    <strong>Current Jadeed:</strong> Page {juzhali_end}<br>
                    <strong>How it works:</strong> Juzhali = X pages BEFORE your current Jadeed page
                </p>
            </div>
            """, unsafe_allow_html=True)
            
            new_length = st.selectbox(
                "Juzhali Window Size (pages to review)",
                options=[10, 15, 20, 25, 30],
                index=[10, 15, 20, 25, 30].index(st.session_state.juzhali_length),
                help="How many pages to review before Jadeed"
            )
            
            preview_start = max(1, juzhali_end - new_length + 1)
            st.info(f"📊 Preview: Pages {preview_start} to {juzhali_end}")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("💾 Save Changes", type="primary", use_container_width=True):
                    st.session_state.juzhali_length = new_length
                    st.session_state.show_juzhali_config = False
                    st.success("Settings updated!")
                    st.rerun()
            with col2:
                if st.button("❌ Cancel", use_container_width=True):
                    st.session_state.show_juzhali_config = False
                    st.rerun()
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Filter Juzhali data
    temp_data = df.copy()
    temp_data['Page_Str'] = temp_data['Page'].astype(str)
    temp_data['Is_Single_Page'] = temp_data['Page_Str'].str.match(r'^\d+$')
    temp_data['Page_Numeric'] = pd.to_numeric(temp_data['Page_Str'], errors='coerce')
    
    juzhali_data = temp_data[
        (temp_data['Session_Type'] == 'Juzhali') &
        (temp_data['Is_Single_Page'] == True) &
        (temp_data['Page_Numeric'].notna()) &
        (temp_data['Page_Numeric'] >= juzhali_start) &
        (temp_data['Page_Numeric'] <= juzhali_end)
    ].copy()
    
    # Health Score - NEW LOGIC WITH GRAPHS
    st.markdown("### 📊 Juzhali Retention Health")
    
    # Get ALL Juzhali Session_Summary entries (not filtered by page range!)
    all_juzhali_grades = temp_data[
        (temp_data['Session_Type'] == 'Juzhali') &
        (temp_data['Core_Mistake'] == 'Session_Summary') &
        (temp_data['Overall_Grade'].notna())
    ]
    
    if not all_juzhali_grades.empty:
        # Sort by date
        all_juzhali_grades = all_juzhali_grades.sort_values('Date')
        
        # 1. SHOW LATEST GRADE
        latest = all_juzhali_grades.iloc[-1]  # Most recent
        st.markdown(f"#### 🎯 Latest Retention Test: **{latest['Overall_Grade']}**")
        
        # 2. TREND CHART (Line Graph)
        st.markdown("#### 📈 Retention Trend Over Time")
        
        # Convert grades to numbers for chart
        grade_map = {'ضعيف': 1, 'متوسط': 2, 'جيد': 3, 'جيد جدا': 4}
        all_juzhali_grades['Grade_Score'] = all_juzhali_grades['Overall_Grade'].map(grade_map)
        
        if len(all_juzhali_grades) > 1:
            fig = px.line(all_juzhali_grades, x='Date', y='Grade_Score',
                          title='Juzhali Retention Trend',
                          markers=True,
                          labels={'Grade_Score': 'Grade Level', 'Date': 'Test Date'})
            
            # Add horizontal lines for grade levels
            fig.add_hline(y=4, line_dash="dash", line_color="green", annotation_text="جيد جدا")
            fig.add_hline(y=3, line_dash="dash", line_color="blue", annotation_text="جيد")
            fig.add_hline(y=2, line_dash="dash", line_color="orange", annotation_text="متوسط")
            fig.add_hline(y=1, line_dash="dash", line_color="red", annotation_text="ضعيف")
            
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("📊 *Record more sessions to see the trend chart*")
        
        # 3. GRADE DISTRIBUTION PIE CHART
        st.markdown("#### 📊 Grade Distribution")
        
        grade_counts = all_juzhali_grades['Overall_Grade'].value_counts()
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # Pie chart
            fig2 = px.pie(values=grade_counts.values, 
                         names=grade_counts.index,
                         title='Grade Distribution',
                         color=grade_counts.index,
                         color_discrete_map={
                             'جيد جدا': '#10b981',
                             'جيد': '#3b82f6', 
                             'متوسط': '#f59e0b',
                             'ضعيف': '#ef4444'
                         })
            st.plotly_chart(fig2, use_container_width=True)
        
        with col2:
            # Show grade metrics
            st.write("**Session Count:**")
            for grade, count in grade_counts.items():
                if grade == 'جيد جدا':
                    emoji = "✅"
                elif grade == 'جيد':
                    emoji = "👍"
                elif grade == 'متوسط':
                    emoji = "⚠️"
                else:
                    emoji = "❌"
                
                st.write(f"{emoji} **{grade}:** {count} sessions")
            
            # Calculate average
            avg_score = all_juzhali_grades['Grade_Score'].mean()
            st.metric("📊 Average Grade Score", f"{avg_score:.1f}/4.0")
        
        # 4. WHAT TO TEST NEXT
        st.markdown("#### 📅 What to Test Next")
        
        # Get last Jadeed page
        last_jadeed = get_last_jadeed_page(df)
        if last_jadeed:
            next_juzhali_start = max(1, last_jadeed - 9)
            next_juzhali_end = last_jadeed
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("📖 Next Juzhali Range", f"{next_juzhali_start}-{next_juzhali_end}")
            
            with col2:
                # Days since last test
                days_ago = (pd.Timestamp.now() - latest['Date']).days
                st.metric("⏰ Days Since Last Test", f"{days_ago} days")
            
            with col3:
                if days_ago > 2:
                    status = "⏳ Due for Test"
                    color = "orange"
                else:
                    status = "✅ On Track"
                    color = "green"
                st.metric("📋 Status", status)
            
            st.info(f"**💡 Recommendation:** Test pages **{next_juzhali_start}-{next_juzhali_end}** in your next Juzhali session")
        
    else:
        # NO GRADES YET
        st.info("""
        **📝 No Retention Data Yet**
        
        **Juzhali Retention Health** will appear here once you record Juzhali sessions with Overall Grades.
        
        **How to see retention health:**
        1. Test OLD memorized pages (9-10 days old)
        2. Record mistakes during recitation  
        3. **CRITICAL:** Select Overall Session Grade at bottom
        4. Submit the session
        
        **The Overall Grade (جيد جدا/جيد/متوسط/ضعيف) IS the retention measurement!**
        """)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Page performance map
    st.markdown('<div class="section-header">🗺️ Page Performance Map</div>', unsafe_allow_html=True)
    st.markdown(f"""
    <p style="text-align: center; color: #6b7280; font-size: 1.1em;">
        Performance overview of Pages {juzhali_start} - {juzhali_end}
    </p>
    """, unsafe_allow_html=True)
    
    # Debug: Check how many pages we have
    st.info(f"📊 Displaying {len(page_range_list)} pages: {page_range_list[0]} to {page_range_list[-1]}")
    
    page_health_map = {}
    
    for page_num in page_range_list:
        p_data = juzhali_data[juzhali_data['Page_Numeric'] == page_num]
        
        if p_data.empty:
            page_health_map[page_num] = {
                "color": "#e5e7eb",
                "text": "#9ca3af",
                "summary": "Not tested"
            }
        else:
            color_code = "#dbeafe"
            font_color = "#1d4ed8"
            summary = "Reviewed"
            
            if 'Mistake_Count' in p_data.columns and 'Tambeeh_Count' in p_data.columns:
                detailed_data = p_data[p_data['Data_Format'] == 'session_entry']
                if not detailed_data.empty:
                    talqeen_sum = detailed_data['Mistake_Count'].sum()
                    tambeeh_sum = detailed_data['Tambeeh_Count'].sum()
                    calculated_grade = 10 - (talqeen_sum * 1) - (tambeeh_sum * 0.5)
                    
                    if talqeen_sum > 0 or tambeeh_sum > 0:
                        summary = f"{int(talqeen_sum)}T/{int(tambeeh_sum)}H ({calculated_grade:.1f})"
                    else:
                        summary = f"Perfect! ({calculated_grade:.1f})"
                    
                    if calculated_grade >= 8:
                        color_code = "#d1fae5"
                        font_color = "#059669"
                    elif calculated_grade >= 7:
                        color_code = "#fef3c7"
                        font_color = "#d97706"
                    else:
                        color_code = "#fee2e2"
                        font_color = "#dc2626"
            
            elif 'Overall_Grade' in p_data.columns:
                uploaded_grades = p_data[p_data['Data_Format'] == 'upload']['Overall_Grade']
                if not uploaded_grades.empty and not uploaded_grades.isna().all():
                    try:
                        avg_grade = float(uploaded_grades.iloc[0])
                        summary = f"Grade: {avg_grade:.1f}"
                        
                        if avg_grade >= 8:
                            color_code = "#d1fae5"
                            font_color = "#059669"
                        elif avg_grade >= 7:
                            color_code = "#fef3c7"
                            font_color = "#d97706"
                        else:
                            color_code = "#fee2e2"
                            font_color = "#dc2626"
                    except:
                        pass
            
            page_health_map[page_num] = {
                "color": color_code,
                "text": font_color,
                "summary": summary
            }
    
    # SINGLE DISPLAY LOOP - NO DUPLICATES!
    num_cols = 5
    num_rows = (len(page_range_list) + num_cols - 1) // num_cols
    
    for row_idx in range(num_rows):
        cols = st.columns(num_cols)
        for col_idx in range(num_cols):
            page_idx = row_idx * num_cols + col_idx
            if page_idx >= len(page_range_list):
                break
            
            page_num = page_range_list[page_idx]
            data = page_health_map[page_num]
            
            with cols[col_idx]:
                st.markdown(f"""
                <div class="page-box" style="background-color: {data['color']}; 
                                            border: 2px solid {data['text']};
                                            padding: 10px;
                                            border-radius: 8px;
                                            text-align: center;
                                            margin-bottom: 10px;
                                            min-height: 80px;
                                            display: flex;
                                            flex-direction: column;
                                            justify-content: center;">
                    <div style="color: {data['text']}; font-size: 1.2em; font-weight: bold;">
                        Page {page_num}
                    </div>
                    <div style="color: {data['text']}; font-size: 0.85em; margin-top: 5px;">
                        {data['summary']}
                    </div>
                </div>
                """, unsafe_allow_html=True)
    
    st.markdown("<br><br>", unsafe_allow_html=True)
    

    
    # Session entry
    st.markdown('<div class="section-header">📝 Record New Session</div>', unsafe_allow_html=True)
    
    with st.form(key='juzhali_session_form'):
        col1, col2 = st.columns(2)
        with col1:
            session_date = st.date_input("📅 Session Date", datetime.now().date())
        with col2:
            st.markdown(f"**Session Type:** Juzhali (Pages {juzhali_start}-{juzhali_end})")
        
        st.markdown("---")
        
        selected_pages = st.multiselect(
            "📄 Select Pages Tested (in order)",
            options=[str(i) for i in page_range_list],
            help="Choose pages you tested in this session"
        )
        
        # FIX 2: Add submit button to the form
        start_entry = st.form_submit_button("✅ Start Recording Mistakes", type="primary", use_container_width=True)
    
    # Initialize session state
    if 'juz_page_entries' not in st.session_state:
        st.session_state.juz_page_entries = {}
    
    if 'juz_session_started' not in st.session_state:
        st.session_state.juz_session_started = False
    
    if start_entry and selected_pages:
        st.session_state.juz_session_started = True
        st.session_state.juz_session_date = session_date
        st.session_state.juz_selected_pages = selected_pages
        st.session_state.juz_page_entries = {}
    
    # Page-by-page entry
    if st.session_state.juz_session_started and hasattr(st.session_state, 'juz_selected_pages'):
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown('<div class="section-header">📄 Page-by-Page Entry</div>', unsafe_allow_html=True)
        
        for idx, page_num in enumerate(st.session_state.juz_selected_pages):
            with st.expander(f"📄 Page {page_num} - Question #{idx + 1}", expanded=(idx == 0)):
                
                col1, col2 = st.columns(2)
                with col1:
                    talqeen = st.number_input(
                        "🔴 Talqeen Mistakes",
                        min_value=0, step=1,
                        key=f'juz_talqeen_{page_num}_{idx}'
                    )
                with col2:
                    tambeeh = st.number_input(
                        "🟡 Tambeeh Mistakes",
                        min_value=0, step=1,
                        key=f'juz_tambeeh_{page_num}_{idx}'
                    )
                
                st.markdown("**📏 Tajweed Classification (Optional)**")
                col1, col2 = st.columns(2)
                with col1:
                    tajweed_mistake = st.selectbox(
                        "Ahkaam Error",
                        STANDARD_AHKAAM,
                        key=f'juz_ahkaam_{page_num}_{idx}'
                    )
                with col2:
                    tajweed_note = st.text_input(
                        "Additional Note",
                        placeholder="Optional",
                        key=f'juz_taj_note_{page_num}_{idx}'
                    )
                
                st.markdown("**🗣️ Makharij Classification (Optional)**")
                col1, col2 = st.columns(2)
                with col1:
                    makharij_mistake = st.selectbox(
                        "Makharij Error",
                        STANDARD_MAKHARIJ,
                        key=f'juz_makh_{page_num}_{idx}'
                    )
                with col2:
                    makharij_note = st.text_input(
                        "Additional Note",
                        placeholder="Optional",
                        key=f'juz_makh_note_{page_num}_{idx}'
                    )
                
                specific_details = []
                core_mistake = 'Hifz'
                
                if tajweed_mistake != 'N/A':
                    core_mistake = 'Tajweed'
                    detail = tajweed_mistake
                    if tajweed_note:
                        detail += f" ({tajweed_note})"
                    specific_details.append(detail)
                
                if makharij_mistake != 'N/A':
                    core_mistake = 'Makharij'
                    detail = makharij_mistake
                    if makharij_note:
                        detail += f" - {makharij_note}"
                    specific_details.append(detail)
                
                if tajweed_mistake != 'N/A' and makharij_mistake != 'N/A':
                    core_mistake = 'Mixed'
                
                specific_mistake_detail = "; ".join(specific_details) if specific_details else f"Page {page_num}"
                
                st.session_state.juz_page_entries[page_num] = {
                    'talqeen': talqeen,
                    'tambeeh': tambeeh,
                    'core_mistake': core_mistake,
                    'specific_mistake': specific_mistake_detail
                }
        
        # =========================================================================
        # NEW: OVERALL SESSION GRADE SECTION
        # =========================================================================
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown('<div class="section-header">🎯 Overall Session Grade</div>', unsafe_allow_html=True)
        
        st.markdown("""
        <div style="background: linear-gradient(135deg, #dbeafe 0%, #bfdbfe 100%); 
                    padding: 20px; border-radius: 10px; margin-bottom: 20px;">
            <h4 style="color: #1e40af; margin: 0 0 10px 0;">📊 Session Performance Summary</h4>
            <p style="color: #374151; margin: 0;">
                Based on today's performance across all pages, provide an overall grade for this Juzhali session.
                This grade will be used to calculate your Juzhali Health Score.
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            overall_grade = st.selectbox(
                "Overall Session Grade",
                options=["جيد جدا", "جيد", "متوسط", "ضعيف"],
                format_func=lambda x: {
                    "جيد جدا": "جيد جدا 🌟 (Excellent)",
                    "جيد": "جيد ✅ (Good)", 
                    "متوسط": "متوسط 🟡 (Average)",
                    "ضعيف": "ضعيف ❌ (Weak)"
                }[x],
                help="Overall evaluation of today's Juzhali session"
            )
        
        with col2:
            # Show what this grade means for health score
            grade_to_score = {
                "جيد جدا": "100%",
                "جيد": "80%", 
                "متوسط": "60%",
                "ضعيف": "40%"
            }
            st.markdown(f"""
            <div style="background: rgba(16, 185, 129, 0.1); 
                        padding: 15px; border-radius: 8px; text-align: center;
                        border: 2px solid #10b981;">
                <p style="margin: 0; color: #047857; font-size: 0.9em;">Health Impact</p>
                <h3 style="margin: 5px 0 0 0; color: #059669;">{grade_to_score[overall_grade]}</h3>
            </div>
            """, unsafe_allow_html=True)
        
        # Session notes
        session_notes = st.text_area(
            "Session Notes (Optional)",
            placeholder="Any observations about today's session...",
            height=80
        )
        
        # Store overall grade in session state
        st.session_state.juz_overall_grade = overall_grade
        st.session_state.juz_session_notes = session_notes
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # =========================================================================
        # SUBMIT BUTTON - UPDATED TO SAVE OVERALL GRADE
        # =========================================================================
        if st.button("💾 Submit Complete Session", type="primary", use_container_width=True):
            # Save logic here - including overall grade
            try:
                from database import append_new_session
                
                # Save individual page entries
                for page_num, page_data in st.session_state.juz_page_entries.items():
                    session_data = {
                        'date': st.session_state.juz_session_date,
                        'sipara': None,
                        'page_tested': page_num,
                        'talqeen_count': page_data['talqeen'],
                        'tambeeh_count': page_data['tambeeh'],
                        'core_mistake_type': page_data['core_mistake'],
                        'specific_mistake': page_data['specific_mistake'],
                        'overall_grade': None,  # Individual pages don't get grades
                        'notes': f"Page {page_num} - {st.session_state.juz_session_notes}" if st.session_state.juz_session_notes else f"Page {page_num}"
                    }
                    
                    # Save each page entry
                    append_new_session(student_id, 'Juzhali', session_data)
                
                # Save OVERALL SESSION with grade
                overall_session_data = {
                    'date': st.session_state.juz_session_date,
                    'sipara': None,
                    'page_tested': f"Pages {', '.join(st.session_state.juz_selected_pages)}",
                    'talqeen_count': 0,
                    'tambeeh_count': 0,
                    'core_mistake_type': 'Session_Summary',
                    'specific_mistake': 'Overall Session Evaluation',
                    'overall_grade': st.session_state.juz_overall_grade,  # ✅ This is the key line!
                    'notes': st.session_state.juz_session_notes or "Juzhali session completed"
                }
                
                append_new_session(student_id, 'Juzhali', overall_session_data)
                
                # Reset session state
                st.session_state.juz_session_started = False
                st.session_state.juz_page_entries = {}
                st.session_state.juz_overall_grade = None
                st.session_state.juz_session_notes = None
                
                st.success(f"✅ Successfully recorded session for {len(st.session_state.juz_selected_pages)} pages with overall grade: {overall_grade}!")
                st.markdown(f"""
                <div class="success-section">
                    <p style="margin: 0; text-align: center;">
                        🔗 Next Jadeed will automatically start from Page <strong>{juzhali_end + 1}</strong>
                    </p>
                </div>
                """, unsafe_allow_html=True)
                st.balloons()
                
                # Auto-refresh after 3 seconds
                import time
                with st.spinner("Refreshing in 3 seconds..."):
                    time.sleep(3)
                
                st.rerun()
                
            except Exception as e:
                st.error(f"❌ Error saving session: {str(e)}")

# =========================================================================
# END OF PART 4
# =========================================================================

# =========================================================================
# JADEED ASSISTANT FUNCTION
# =========================================================================

def run_jadeed_assistant(student_data_df, student_id):
    """Jadeed assistant for new Hifz learning sessions"""
    
    from database import get_last_jadeed_page
    
    if student_data_df is None or student_data_df.empty:
        st.error("❌ No student data available.")
        return
    
    df = student_data_df.copy()
    
    # Header
    st.markdown("""
    <div style="text-align: center; padding: 30px 0;">
        <h1 style="color: #10b981; font-size: 3em; margin: 0;"> 
            ✨ Jadeed Assistant
        </h1>
        <p style="color: #1f2937; font-size: 1.2em; margin-top: 10px;">
            Track new learning sessions • Auto-connects to Juzhali progression
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    jadeed_data = df[df['Session_Type'] == 'Jadeed'].copy()
    jadeed_data_sorted = jadeed_data.sort_values(by='Date', ascending=False).reset_index(drop=True)

    # ✅ ADD THIS CHECK:
    data_format = get_data_format_type(jadeed_data_sorted)
    
    # Progress Analytics
    st.markdown('<div class="section-header">📊 Jadeed Progress Analytics</div>', unsafe_allow_html=True)
    
    # ✅ CORRECT FORMAT CHECK:
    if data_format == 'uploaded':
        show_detailed_data_message()
    else:
        # Your existing progress analytics code here
        if 'Specific_Mistake' in jadeed_data_sorted.columns:
            jadeed_progress_entries = jadeed_data_sorted[
                jadeed_data_sorted['Specific_Mistake'].str.contains('Progress:', na=False)
            ].copy()
        else:
            jadeed_progress_entries = pd.DataFrame()  # Empty DataFrame if column doesn't exist
    
        if not jadeed_progress_entries.empty:
            # Metrics
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if not jadeed_data_sorted.empty:
                    last_jadeed_date = jadeed_data_sorted['Date'].max()
                    days_since = (datetime.now().date() - last_jadeed_date.date()).days
                    st.markdown(f"""
                    <div class="metric-card" style="background: linear-gradient(135deg, #10b981 0%, #059669 100%);">
                        <h3 style="margin:0;">📅</h3>
                        <h2 style="margin:10px 0;">{days_since}</h2>
                        <p style="margin:0;">Days Since Last Session</p>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.info("No data")
            
            with col2:
                total_pages, total_ayahs = calculate_jadeed_progress(jadeed_data_sorted)
                display_parts = []
                if total_pages > 0:
                    display_parts.append(f"{total_pages:.1f} page{'s' if total_pages != 1 else ''}")
                if total_ayahs > 0:
                    display_parts.append(f"{int(total_ayahs)} ayah{'s' if total_ayahs != 1 else ''}")
                
                display_text = " + ".join(display_parts) if display_parts else "0"
                st.markdown(f"""
                <div class="metric-card" style="background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);">
                    <h3 style="margin:0;">📖</h3>
                    <h2 style="margin:10px 0; font-size: 1.5em;">{display_text}</h2>
                    <p style="margin:0;">Total Progress</p>
                </div>
                """, unsafe_allow_html=True)
            
            with col3:
                st.markdown(f"""
                <div class="metric-card" style="background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);">
                    <h3 style="margin:0;">🎯</h3>
                    <h2 style="margin:10px 0;">{len(jadeed_progress_entries)}</h2>
                    <p style="margin:0;">Total Sessions</p>
                </div>
                """, unsafe_allow_html=True)
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            # Grade trend
            st.markdown("**📉 Grade Trend (Last 5 Sessions)**")
            
            grade_data_for_chart = jadeed_progress_entries.copy()
            
            if 'Final_Grade' in grade_data_for_chart.columns:
                grade_data_for_chart['Grade_Numeric'] = pd.to_numeric(grade_data_for_chart['Final_Grade'], errors='coerce')
            elif 'Overall_Grade' in grade_data_for_chart.columns:
                grade_data_for_chart['Grade_Numeric'] = pd.to_numeric(grade_data_for_chart['Overall_Grade'], errors='coerce')
            else:
                grade_data_for_chart['Grade_Numeric'] = None

            grade_data_for_chart = grade_data_for_chart.dropna(subset=['Grade_Numeric'])
            
            if not grade_data_for_chart.empty:
                recent_grades = grade_data_for_chart.head(5).sort_values('Date')
                if len(recent_grades) > 1:
                    chart = alt.Chart(recent_grades).mark_line(point=True, color='#10b981').encode(
                        x=alt.X('Date:T', title='Session Date', axis=alt.Axis(format="%m-%d")),
                        y=alt.Y('Grade_Numeric:Q', title='Grade (1-10)', scale=alt.Scale(domain=[1, 10])),
                        tooltip=['Date:T', 'Grade_Numeric:Q']
                    ).properties(
                        height=250,
                        title="Jadeed Grade Trend"
                    ).configure_view(
                        strokeWidth=0
                    ).configure_axis(
                        grid=True,
                        gridColor='#e5e7eb'
                    )
                    st.altair_chart(chart, use_container_width=True)
                elif len(recent_grades) == 1:
                    st.markdown(f"""
                    <div class="info-section">
                        <p style="margin: 0; text-align: center;">
                            Last session: <strong>{int(recent_grades['Grade_Numeric'].iloc[0])}/10</strong> 
                            on {recent_grades['Date'].iloc[0].strftime('%Y-%m-%d')}
                        </p>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.info("Not enough graded sessions for trend")
            else:
                st.info("No graded sessions available")
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            # Technical focus (only for new format)
            if data_format == 'detailed':
                if 'Core_Mistake' in jadeed_data_sorted.columns and 'Specific_Mistake' in jadeed_data_sorted.columns:
                    st.markdown('<div class="section-header">🎯 Technical Focus Areas</div>', unsafe_allow_html=True)
            
                    jadeed_mistake_entries = jadeed_data_sorted[
                        (jadeed_data_sorted['Core_Mistake'].isin(['Tajweed', 'Makharij', 'Hifz'])) |
                        (jadeed_data_sorted['Specific_Mistake'].isin(STANDARD_HIFZ_MISTAKES))
                    ].copy()
            
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown("**📏 Ahkaam to Watch**")
                        taj = jadeed_mistake_entries[
                            (jadeed_mistake_entries['Core_Mistake'] == 'Tajweed') &
                            (jadeed_mistake_entries['Specific_Mistake'] != 'N/A')
                        ]['Specific_Mistake'].value_counts().head(3)
                        
                        if not taj.empty:
                            for rule, count in taj.items():
                                st.markdown(f"""
                                <div style="background: #dbeafe; padding: 10px; border-radius: 8px; 
                                            margin: 5px 0; border-left: 3px solid #3b82f6;">
                                    <strong style="color: #1e40af;">{rule}</strong>
                                    <span style="color: #1e3a8a;"> • {int(count)} times</span>
                                </div>
                                """, unsafe_allow_html=True)
                        else:
                            st.success("✅ No Tajweed issues")
                    
                    with col2:
                        st.markdown("**🗣️ Makharij to Watch**")
                        makh = jadeed_mistake_entries[
                            (jadeed_mistake_entries['Core_Mistake'] == 'Makharij') &
                            (jadeed_mistake_entries['Specific_Mistake'] != 'N/A')
                        ]['Specific_Mistake'].value_counts().head(3)
                        
                        if not makh.empty:
                            for letter, count in makh.items():
                                st.markdown(f"""
                                <div style="background: #dbeafe; padding: 10px; border-radius: 8px; 
                                            margin: 5px 0; border-left: 3px solid #3b82f6;">
                                    <strong style="color: #1e40af;">{letter}</strong>
                                    <span style="color: #1e3a8a;"> • {int(count)} times</span>
                                </div>
                                """, unsafe_allow_html=True)
                        else:
                            st.success("✅ No Makharij issues")
        else:
            st.markdown("""
            <div class="info-section">
                <h3 style="margin: 0 0 10px 0;">📝 No Jadeed Sessions Yet</h3>
                <p style="margin: 0;">Start recording your first learning session below!</p>
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Session Entry Form
    st.markdown('<div class="section-header">📝 Record New Jadeed Session</div>', unsafe_allow_html=True)
    
    # Get last Jadeed page
    jadeed_last_page = get_last_jadeed_page(df)
    
    if jadeed_last_page is None:
        jadeed_start_page = 1
        st.markdown("""
        <div class="info-section">
            <p style="margin: 0; text-align: center;">
                ℹ️ <strong>Starting from Page 1</strong> (No previous Jadeed sessions found)
            </p>
        </div>
        """, unsafe_allow_html=True)
    else:
        jadeed_start_page = jadeed_last_page + 1
        st.markdown(f"""
        <div class="success-section">
            <p style="margin: 0; text-align: center;">
                🔗 <strong>Auto-continuing from Page {jadeed_start_page}</strong> 
                (Last Jadeed: Page {jadeed_last_page})
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    with st.form(key='jadeed_entry_form'):
        col1, col2 = st.columns(2)
        with col1:
            session_date = st.date_input("📅 Session Date", datetime.now().date())
        with col2:
            st.markdown("**Session Type:** ✨ Jadeed (New Learning)")
        
        st.markdown("---")
        
        st.markdown(f"""
        <div style="background: #f3f4f6; padding: 15px; border-radius: 10px; margin-bottom: 15px;">
            <h4 style="margin: 0 0 10px 0; color: #374151;">📖 Page Range</h4>
            <p style="margin: 0; color: #6b7280;">
                <strong>Starting Page:</strong> {jadeed_start_page} (Auto-set)<br>
                <strong>Enter your ending position below:</strong>
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            end_page = st.number_input(
                "Ending Page",
                min_value=jadeed_start_page,
                max_value=604,
                value=jadeed_start_page,
                help="Last page you reached in this session"
            )
        with col2:
            end_ayah = st.number_input(
                "Ending Ayah",
                min_value=1,
                max_value=286,
                value=10,
                help="Ayah number on the ending page"
            )
        
        st.markdown("---")
        st.markdown("**📊 Session Performance**")
        
        col1, col2 = st.columns(2)
        with col1:
            tambeeh_count = st.number_input(
                "🟡 Tambeeh Mistakes",
                min_value=0,
                step=1,
                help="Minor corrections during learning"
            )
        with col2:
            final_grade = st.slider(
                "Final Grade (1-10)",
                min_value=1,
                max_value=10,
                value=7,
                help="Overall session quality"
            )
        
        st.markdown("---")
        st.markdown("**📏 Today's Progress**")
        st.caption("💡 Example: 1 full page = '1 page + 0 ayahs' | Partial = '0 pages + 5 ayahs'")
        
        col1, col2 = st.columns(2)
        
        with col1:
            pages_completed = st.selectbox(
                "Pages Completed",
                options=[0, 0.5, 1, 1.5, 2],
                format_func=lambda x: f"{x} page{'s' if x != 1 else ''}" if x > 0 else "0 pages",
                index=2
            )
        
        with col2:
            ayahs_completed = st.number_input(
                "Additional Ayahs",
                min_value=0,
                max_value=286,
                value=0,
                step=1,
                help="Extra ayahs beyond complete pages"
            )
        
        st.markdown("---")
        st.markdown("**🎯 Mistake Classification (Optional)**")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**📏 Tajweed Errors**")
            session_ahkaam_list = st.multiselect(
                "Select Ahkaam Issues",
                [item for item in STANDARD_AHKAAM if item != 'N/A'],
                label_visibility="collapsed"
            )
            session_tajweed_note = st.text_area(
                "Tajweed Notes",
                placeholder="Optional details about Tajweed errors...",
                height=80
            )
        
        with col2:
            st.markdown("**🗣️ Makharij Errors**")
            session_makharij_list = st.multiselect(
                "Select Makharij Issues",
                [item for item in STANDARD_MAKHARIJ if item != 'N/A'],
                label_visibility="collapsed"
            )
            session_makharij_note = st.text_area(
                "Makharij Notes",
                placeholder="Optional details about Makharij errors...",
                height=80
            )
        
        session_hifz_issue = st.selectbox(
            "Primary Hifz Issue (if any)",
            STANDARD_HIFZ_MISTAKES
        )
        
        general_note = st.text_area(
            "General Session Notes (Optional)",
            placeholder="Any observations about the session...",
            height=80
        )
        
        submit_jadeed = st.form_submit_button(
            "💾 Submit Jadeed Session",
            type="primary",
            use_container_width=True
        )
    
    # Submit handler
    if submit_jadeed:
        progress_parts = []
        if pages_completed > 0:
            progress_parts.append(f"{pages_completed} pages")
        if ayahs_completed > 0:
            progress_parts.append(f"{ayahs_completed} ayahs")
        
        if not progress_parts:
            st.error("⚠️ Please enter progress! Add at least pages OR ayahs completed.")
            st.stop()
        
        progress_str = " + ".join(progress_parts)
        
        # Prepare session data
        session_data = {
            'date': session_date,
            'sipara': None,
            'page_tested': jadeed_start_page,
            'jadeed_page': end_page,
            'start_ayah': 1,
            'end_ayah': end_ayah,
            'talqeen_count': 0,
            'tambeeh_count': tambeeh_count,
            'core_mistake_type': 'Jadeed_Learning',
            'specific_mistake': f"Progress: {progress_str}",
            'overall_grade': final_grade,
            'notes': general_note or f"Progress: {progress_str}"
        }
        
        # Save to database
        try:
            from database import append_new_session, get_all_student_sessions
            student_id = st.session_state.selected_student_id
            
            if student_id is None:
                st.error("❌ No student selected. Please select a student first.")
                st.stop()
            
            success = append_new_session(student_id, 'Jadeed', session_data)
            
            if success:
                st.markdown("""
                <div class="success-section" style="text-align: center; padding: 30px;">
                    <h2 style="color: #059669; margin: 0 0 15px 0;">✅ Session Saved Successfully!</h2>
                    <p style="color: #047857; margin: 0; font-size: 1.1em;">
                        Your progress has been recorded and connected to the Juzhali system.
                    </p>
                </div>
                """, unsafe_allow_html=True)
                
                # Reload data
                new_data = get_all_student_sessions(student_id)
                st.session_state.student_data_df = new_data
                
                # Show next steps
                st.markdown(f"""
                <div class="info-section">
                    <h3 style="margin: 0 0 10px 0;">🔗 What's Next?</h3>
                    <p style="margin: 0;">
                        ✨ Your next Jadeed session will start from <strong>Page {end_page + 1}</strong><br>
                        🔄 Juzhali range will update automatically<br>
                        📊 Check Analytics Dashboard for updated progress
                    </p>
                </div>
                """, unsafe_allow_html=True)
                
                st.balloons()
                
                # Auto-refresh after 3 seconds
                import time
                with st.spinner("Refreshing in 3 seconds..."):
                    time.sleep(3)
                
                st.rerun()
            else:
                st.error("❌ Failed to save session. Please try again.")
                
        except Exception as e:
            st.error(f"❌ Error saving session: {str(e)}")
# =========================================================================
# DATA STATUS & HELP FUNCTIONS
# =========================================================================

def display_data_status_badge(student_id):
    """Display badge showing what data is available"""
    if student_id is None:
        return
        
    info = get_data_format_info(student_id)
    
    st.markdown('<div class="section-header">📊 Data Status</div>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if info['has_uploaded']:
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #d1fae5 0%, #a7f3d0 100%); 
                        padding: 15px; border-radius: 10px; text-align: center; border: 2px solid #059669;">
                <h3 style="color: #059669; margin: 0;">✅</h3>
                <p style="color: #047857; margin: 5px 0 0 0; font-weight: bold;">
                    {info['uploaded_count']} Uploaded Sessions
                </p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style="background: #f3f4f6; padding: 15px; border-radius: 10px; text-align: center; border: 2px solid #9ca3af;">
                <h3 style="color: #6b7280; margin: 0;">📥</h3>
                <p style="color: #6b7280; margin: 5px 0 0 0;">No Uploaded Data</p>
            </div>
            """, unsafe_allow_html=True)
    
    with col2:
        if info['has_detailed']:
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #dbeafe 0%, #bfdbfe 100%); 
                        padding: 15px; border-radius: 10px; text-align: center; border: 2px solid #3b82f6;">
                <h3 style="color: #3b82f6; margin: 0;">✍️</h3>
                <p style="color: #1e40af; margin: 5px 0 0 0; font-weight: bold;">
                    {info['detailed_count']} Web Entries
                </p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style="background: #f3f4f6; padding: 15px; border-radius: 10px; text-align: center; border: 2px solid #9ca3af;">
                <h3 style="color: #6b7280; margin: 0;">✍️</h3>
                <p style="color: #6b7280; margin: 5px 0 0 0;">No Web Entries Yet</p>
            </div>
            """, unsafe_allow_html=True)
    
    with col3:
        if info['has_uploaded'] and not info['has_detailed']:
            st.markdown("""
            <div style="background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%); 
                        padding: 15px; border-radius: 10px; text-align: center; border: 2px solid #f59e0b;">
                <h3 style="color: #d97706; margin: 0;">💡</h3>
                <p style="color: #92400e; margin: 5px 0 0 0; font-size: 0.9em;">
                    Start entering sessions for detailed analytics!
                </p>
            </div>
            """, unsafe_allow_html=True)
        elif info['has_detailed']:
            st.markdown("""
            <div style="background: linear-gradient(135deg, #d1fae5 0%, #a7f3d0 100%); 
                        padding: 15px; border-radius: 10px; text-align: center; border: 2px solid #059669;">
                <h3 style="color: #059669; margin: 0;">🎯</h3>
                <p style="color: #047857; margin: 5px 0 0 0;">Full Analytics Active</p>
            </div>
            """, unsafe_allow_html=True)

def run_help_section():
    """Help and templates page"""
    
    st.markdown("""
    <div style="text-align: center; padding: 30px 0;">
        <h1 style="background: linear-gradient(90deg, #667eea 0%, #764ba2 100%); 
                   -webkit-background-clip: text; -webkit-text-fill-color: transparent;
                   font-size: 3em; margin: 0;">
            📝 Help & Resources
        </h1>
        <p style="color: #6b7280; font-size: 1.2em; margin-top: 10px;">
            Everything you need to get started with the Hifz Tracker
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown('<div class="section-header">🚀 Quick Start Guide</div>', unsafe_allow_html=True)
    
    st.markdown("""
    <div style="background: linear-gradient(135deg, #e0f2fe 0%, #bae6fd 100%); 
                padding: 25px; border-radius: 15px; margin: 20px 0;">
        <h3 style="color: #0284c7; margin: 0 0 15px 0;">📋 5 Easy Steps:</h3>
        <ol style="color: #0c4a6e; line-height: 2; margin: 0; padding-left: 20px;">
            <li><strong>Upload Excel File:</strong> Use the uploader in the sidebar (or download template below)</li>
            <li><strong>Select Student:</strong> Choose from the dropdown after upload</li>
            <li><strong>Navigate Sections:</strong> Use sidebar menu to access different assistants</li>
            <li><strong>Record Sessions:</strong> Enter daily/weekly progress in each section</li>
            <li><strong>Track Progress:</strong> View analytics dashboard for insights</li>
        </ol>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    st.markdown('<div class="section-header">📊 Excel File Format</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div style="background: #f8fafc; padding: 20px; border-radius: 10px; border-left: 4px solid #3b82f6;">
            <h4 style="color: #1e40af; margin: 0 0 10px 0;">📄 Required Sheets:</h4>
            <ul style="color: #475569; margin: 0; padding-left: 20px;">
                <li><strong>STUDENT_INFO:</strong> Name, teacher, start date</li>
                <li><strong>JADEED:</strong> New learning sessions</li>
                <li><strong>JUZHALI:</strong> Rolling page reviews</li>
                <li><strong>MURAJAAT:</strong> Long-term Sipara reviews</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div style="background: #f8fafc; padding: 20px; border-radius: 10px; border-left: 4px solid #10b981;">
            <h4 style="color: #047857; margin: 0 0 10px 0;">✅ Two Formats Supported:</h4>
            <ul style="color: #475569; margin: 0; padding-left: 20px;">
                <li><strong>Simple:</strong> Just dates, pages, and marks</li>
                <li><strong>Detailed:</strong> Full mistake tracking (Talqeen/Tambeeh)</li>
            </ul>
            <p style="color: #059669; margin: 10px 0 0 0; font-style: italic;">
                Both formats work! Use what fits your workflow.
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Download template
    st.markdown('<div class="section-header">⬇️ Download Excel Template</div>', unsafe_allow_html=True)
    
    template = create_sample_excel_template()
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.download_button(
            label="📥 Download Sample Excel Template",
            data=template,
            file_name="HifzTracker_Template.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
            type="primary"
        )
    
    st.markdown("<br><br>", unsafe_allow_html=True)
    
    # FAQ Section
    st.markdown('<div class="section-header">❓ Frequently Asked Questions</div>', unsafe_allow_html=True)
    
    with st.expander("🌟 What is Jadeed?", expanded=False):
        st.markdown("""
        <div style="padding: 15px;">
            <p style="color: #374151; line-height: 1.8; margin: 0;">
                <strong>Jadeed</strong> (جديد) means <em>"new"</em> in Arabic. It refers to the pages 
                a student is learning for the first time. This is where new memorization happens.
            </p>
            <p style="color: #059669; margin: 10px 0 0 0; font-weight: bold;">
                📖 Example: Today you memorized Page 45 for the first time = Jadeed
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    with st.expander("🔄 What is Juzhali?", expanded=False):
        st.markdown("""
        <div style="padding: 15px;">
            <p style="color: #374151; line-height: 1.8; margin: 0;">
                <strong>Juzhali</strong> refers to the <strong>rolling 10-page window</strong> right before 
                your current Jadeed page. These are recently memorized pages that need frequent revision 
                to ensure retention.
            </p>
            <p style="color: #3b82f6; margin: 10px 0 0 0; font-weight: bold;">
                🔄 Example: If your Jadeed is Page 50, your Juzhali is Pages 40-49
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    with st.expander("🤖 What is Murajaat?", expanded=False):
        st.markdown("""
        <div style="padding: 15px;">
            <p style="color: #374151; line-height: 1.8; margin: 0;">
                <strong>Murajaat</strong> (مراجعة) means <em>"revision"</em>. These are pages that have 
                <strong>graduated from Juzhali</strong> and need periodic long-term review to maintain 
                memorization quality.
            </p>
            <p style="color: #f59e0b; margin: 10px 0 0 0; font-weight: bold;">
                🎯 Example: Pages 1-39 (if your Juzhali is 40-49) are in Murajaat
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    with st.expander("📐 How are pages organized?", expanded=False):
        st.markdown("""
        <div style="padding: 15px;">
            <p style="color: #374151; line-height: 1.8; margin: 0;">
                The Quran is divided into <strong>30 Siparas (Juz)</strong>. Each Sipara contains 
                <strong>20 pages</strong>, making a total of <strong>604 pages</strong>.
            </p>
            <div style="background: #f3f4f6; padding: 15px; border-radius: 8px; margin-top: 15px;">
                <p style="color: #1f2937; margin: 0;">
                    📚 <strong>Sipara 1:</strong> Pages 1-20<br>
                    📚 <strong>Sipara 2:</strong> Pages 21-40<br>
                    📚 <strong>Sipara 3:</strong> Pages 41-60<br>
                    <em style="color: #6b7280;">...and so on until Sipara 30</em>
                </p>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with st.expander("📤 How do I export my data?", expanded=False):
        st.markdown("""
        <div style="padding: 15px;">
            <ol style="color: #374151; line-height: 2; margin: 0; padding-left: 20px;">
                <li>Select a student from the sidebar</li>
                <li>Click <strong>"📥 Export Student Data to Excel"</strong> button</li>
                <li>The merged file (original + new sessions) downloads automatically</li>
                <li>You can re-upload this file anytime to continue tracking</li>
            </ol>
        </div>
        """, unsafe_allow_html=True)
    
    with st.expander("🔢 What's the difference between Talqeen and Tambeeh?", expanded=False):
        st.markdown("""
        <div style="padding: 15px;">
            <p style="color: #374151; line-height: 1.8; margin: 0;">
                <strong style="color: #dc2626;">Talqeen (تلقين):</strong> A <strong>major mistake</strong> 
                where the student needed direct correction/prompting from the teacher. They couldn't 
                self-correct.
            </p>
            <p style="color: #374151; line-height: 1.8; margin: 15px 0 0 0;">
                <strong style="color: #f59e0b;">Tambeeh (تنبيه):</strong> A <strong>minor mistake</strong> 
                where a simple reminder was enough. The student recognized and corrected it quickly.
            </p>
            <div style="background: #dbeafe; padding: 15px; border-radius: 8px; margin-top: 15px; border-left: 4px solid #3b82f6;">
                <p style="color: #1e40af; margin: 0; font-weight: bold;">
                    💡 Health Score = Based on Talqeen ratio. Fewer Talqeen = Better retention!
                </p>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<br><br>", unsafe_allow_html=True)
    
    # Features overview
    st.markdown('<div class="section-header">✨ Key Features</div>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div style="background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%); 
                    padding: 20px; border-radius: 15px; height: 200px;">
            <h3 style="color: #92400e; margin: 0 0 10px 0;">🔗 Auto-Connected</h3>
            <p style="color: #78350f; margin: 0; line-height: 1.6;">
                Jadeed, Juzhali, and Murajaat automatically update based on your progress. 
                No manual range calculation needed!
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div style="background: linear-gradient(135deg, #dbeafe 0%, #bfdbfe 100%); 
                    padding: 20px; border-radius: 15px; height: 200px;">
            <h3 style="color: #1e40af; margin: 0 0 10px 0;">📊 Smart Analytics</h3>
            <p style="color: #1e3a8a; margin: 0; line-height: 1.6;">
                Health scores, weak page detection, technical focus areas, and performance 
                trends - all calculated automatically.
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div style="background: linear-gradient(135deg, #d1fae5 0%, #a7f3d0 100%); 
                    padding: 20px; border-radius: 15px; height: 200px;">
            <h3 style="color: #047857; margin: 0 0 10px 0;">💾 Flexible Data</h3>
            <p style="color: #065f46; margin: 0; line-height: 1.6;">
                Upload existing Excel data OR enter sessions directly in the app. 
                Mix and match both methods seamlessly!
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<br><br>", unsafe_allow_html=True)
    
    # Footer
    st.markdown("""
    <div style="text-align: center; padding: 30px; background: linear-gradient(135deg, #f8fafc 0%, #e5e7eb 100%); 
                border-radius: 15px; margin-top: 30px;">
        <h3 style="color: #1f2937; margin: 0 0 10px 0;">Need More Help?</h3>
        <p style="color: #6b7280; margin: 0;">
            Questions or feedback? Use the feedback button in the sidebar or contact your administrator.
        </p>
    </div>
    """, unsafe_allow_html=True)

# =========================================================================
# MAIN FUNCTION - SIDEBAR NAVIGATION
# =========================================================================

def main():
    """Main application with sidebar navigation"""
    
    # 🔐 CHECK ACCESS CODE FIRST
    if not check_access_code():
        st.stop()  # Don't run the rest if access code is wrong
    
    # ✅ ACCESS GRANTED - Show the main app
    st.sidebar.title("📚 Hifz Tracker System")
    # ... rest of your existing code continues here
    
    # Sidebar header with better styling
    st.sidebar.markdown("""
    <div style="text-align: center; padding: 25px 10px; 
                background: rgba(255, 255, 255, 0.1); 
                border-radius: 15px; 
                margin-bottom: 20px;
                backdrop-filter: blur(10px);
                border: 2px solid rgba(255, 255, 255, 0.2);">
        <h1 style="color: white; margin: 0; font-size: 2.5em;">📚</h1>
        <h2 style="color: white; margin: 10px 0 5px 0; font-size: 1.5em;">Hifz Tracker</h2>
        <p style="color: rgba(255,255,255,0.9); margin: 0; font-size: 1em; font-weight: 500;">
            Smart Progress Management
        </p>
    </div>
    """, unsafe_allow_html=True)
    
# ========================================================================
    # UPLOAD DATA SECTION - IMPROVED
    # ========================================================================
    st.sidebar.markdown("""
    <div style="background: rgba(255, 255, 255, 0.1); 
                padding: 15px; 
                border-radius: 10px; 
                border-left: 4px solid #fbbf24;
                backdrop-filter: blur(10px);
                margin: 15px 0;">
        <h3 style="margin: 0 0 5px 0; font-size: 1.2em;">📤 Upload Data</h3>
        <p style="margin: 0; font-size: 0.85em; opacity: 0.9;">
            Upload your Excel file to get started
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    uploaded_file = st.sidebar.file_uploader(
        "Choose Excel File (xlsx/xls)",
        type=['xlsx', 'xls'],
        help="Upload your student tracking Excel file",
        key='main_file_uploader'
    )
    
    if uploaded_file:
        file_key = f"{uploaded_file.name}_{uploaded_file.size}"
        
        if 'last_uploaded_file' not in st.session_state or st.session_state.last_uploaded_file != file_key:
            
            with st.spinner("⏳ Processing file..."):  # ✅ Changed from st.sidebar.spinner
                parsed_data = parse_excel_file(uploaded_file)
                # 🔍 ADD THIS DEBUG SECTION HERE:
                st.sidebar.write("🔍 DEBUG INFO:")
                st.sidebar.write(f"Error in parsed_data: {parsed_data.get('error', 'None')}")
                st.sidebar.write(f"Has student_info: {'student_info' in parsed_data}")
                if 'student_info' in parsed_data:
                    st.sidebar.write(f"Student info shape: {parsed_data['student_info'].shape}")
                    st.sidebar.write(f"Student info columns: {list(parsed_data['student_info'].columns)}")
                    st.sidebar.write(f"Student name: {parsed_data['student_info']['Student_Name'].iloc[0] if not parsed_data['student_info'].empty else 'EMPTY'}")
                # 🔍 END DEBUG SECTION
                if parsed_data.get('error'):
                    st.sidebar.error(f"❌ {parsed_data['error']}")
                else:
                    detected_format = parsed_data['format']
                    
                    if detected_format == 'upload':
                        st.sidebar.success("📊 Format Detected: **Basic (Marks Only)**")
                    elif detected_format == 'session_entry':
                        st.sidebar.success("📊 Format Detected: **Detailed (Full Tracking)**")
                    
                    try:
                        student_id = save_student_from_excel(parsed_data)
                        
                        if student_id:
                            student_name = parsed_data['student_info']['Student_Name'].iloc[0]
                            st.sidebar.success(f"✅ **{student_name}** loaded successfully!")
            
                            st.session_state.last_uploaded_file = file_key
                            st.session_state.selected_student_id = student_id
                            st.rerun()
                        else:
                            st.sidebar.error("❌ Failed to save data - student_id is None")
                            st.sidebar.write("Debug: Check database.py save_student_from_excel function")
                            
                            st.sidebar.write("🔍 Testing Google Sheets connection...")
                            from database import get_google_sheet
                            test_sheet = get_google_sheet()
                            if test_sheet:
                                st.sidebar.success("✅ Google Sheets connected!")
                                st.sidebar.write(f"Sheet name: {test_sheet.title}")
                            else:
                                st.sidebar.error("❌ Google Sheets connection FAILED!")
                                st.sidebar.write("Check your secrets.toml file!")
                                
                    except Exception as e:
                        st.sidebar.error(f"❌ Save Error: {str(e)}")
                        import traceback
                        st.sidebar.code(traceback.format_exc())
        else:
            st.sidebar.markdown("""
            <div style="background: rgba(16, 185, 129, 0.2); 
                        padding: 12px; 
                        border-radius: 8px; 
                        border: 2px solid #10b981;
                        text-align: center;">
                <p style="margin: 0; font-weight: 600; color: #10b981;">✅ File Already Loaded</p>
            </div>
            """, unsafe_allow_html=True)
    
    st.sidebar.markdown("---")
    
    # ========================================================================
    # SELECT STUDENT SECTION - IMPROVED
    # ========================================================================
    st.sidebar.markdown("""
    <div style="background: rgba(255, 255, 255, 0.1); 
                padding: 15px; 
                border-radius: 10px; 
                border-left: 4px solid #3b82f6;
                backdrop-filter: blur(10px);
                margin: 15px 0;">
        <h3 style="margin: 0 0 5px 0; font-size: 1.2em;">👤 Select Student</h3>
        <p style="margin: 0; font-size: 0.85em; opacity: 0.9;">
            Choose a student to view/edit data
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    all_students = get_all_students()
    
    if all_students:
        student_names = sorted(list(all_students.keys()))
        selected_name = st.sidebar.selectbox(
            "Student Name:",
            student_names,
            key='student_selector_main'
        )
        
        selected_id = all_students[selected_name]
        st.session_state.selected_student_id = selected_id
        
        # Load data
        try:
            all_data = get_all_student_sessions(selected_id)
            st.session_state.student_data_df = all_data
            
            # Student profile with better styling
            st.sidebar.markdown("---")
            st.sidebar.markdown(f"""
            <div style="background: rgba(255, 255, 255, 0.1); 
                        padding: 15px; 
                        border-radius: 10px; 
                        border-left: 4px solid #10b981;
                        backdrop-filter: blur(10px);
                        margin: 10px 0;">
                <h3 style="margin: 0 0 10px 0; font-size: 1.2em;">📋 {selected_name}</h3>
            </div>
            """, unsafe_allow_html=True)
            
            info = get_data_format_info(selected_id)
            
            # Metrics in a nicer layout
            col1, col2 = st.sidebar.columns(2)
            
            with col1:
                if info['has_uploaded']:
                    st.metric("📥 Uploaded", info['uploaded_count'])
                else:
                    st.markdown("""
                    <div style="background: rgba(107, 114, 128, 0.2); 
                                padding: 10px; 
                                border-radius: 8px; 
                                text-align: center;">
                        <p style="margin: 0; font-size: 0.9em; color: #9ca3af;">📥 No uploads</p>
                    </div>
                    """, unsafe_allow_html=True)
            
            with col2:
                if info['has_detailed']:
                    st.metric("✍️ Entries", info['detailed_count'])
                else:
                    st.markdown("""
                    <div style="background: rgba(107, 114, 128, 0.2); 
                                padding: 10px; 
                                border-radius: 8px; 
                                text-align: center;">
                        <p style="margin: 0; font-size: 0.9em; color: #9ca3af;">✍️ No entries</p>
                    </div>
                    """, unsafe_allow_html=True)
            
            # Last Jadeed page
            last_jadeed = get_last_jadeed_page(all_data)
            if last_jadeed:
                st.sidebar.markdown(f"""
                <div style="background: rgba(16, 185, 129, 0.2); 
                            padding: 12px; 
                            border-radius: 8px; 
                            border: 2px solid #10b981;
                            text-align: center;
                            margin: 10px 0;">
                    <p style="margin: 0; font-size: 0.85em; color: rgba(255,255,255,0.8);">📖 Last Jadeed Page</p>
                    <h2 style="margin: 5px 0 0 0; color: #10b981;">Page {last_jadeed}</h2>
                </div>
                """, unsafe_allow_html=True)
            
            st.sidebar.markdown("---")
            
            # ========================================================================
            # EXPORT DATA SECTION - ALREADY GOOD, KEEPING IT
            # ========================================================================
            st.sidebar.markdown("""
            <div style="background: rgba(255, 255, 255, 0.1); 
                        padding: 15px; 
                        border-radius: 10px; 
                        border-left: 4px solid #10b981;
                        backdrop-filter: blur(10px);
                        margin: 15px 0;">
                <h3 style="margin: 0 0 5px 0; font-size: 1.2em;">📥 Export Data</h3>
                <p style="margin: 0; font-size: 0.85em; opacity: 0.9;">
                    Download complete student data
                </p>
            </div>
            """, unsafe_allow_html=True)
            
            if st.sidebar.button("📥 Export to Excel", use_container_width=True, key='export_main', type='primary'):
                try:
                    export_path = export_student_to_excel(selected_id)
                    with open(export_path, 'rb') as f:
                        st.sidebar.download_button(
                            label="⬇️ Download Excel File",
                            data=f.read(),
                            file_name=f"{selected_name}_HifzData.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            use_container_width=True,
                            type="primary"
                        )
                    st.sidebar.success("✅ Ready to download!")
                except Exception as e:
                    st.sidebar.error(f"❌ Error: {str(e)}")
        
        except Exception as e:
            st.sidebar.error(f"❌ Load error: {str(e)}")
    
    else:
        # No students message
        st.sidebar.markdown("""
        <div style="background: rgba(251, 191, 36, 0.2); 
                    padding: 15px; 
                    border-radius: 10px; 
                    border: 2px solid #fbbf24;
                    text-align: center;
                    margin: 10px 0;">
            <p style="margin: 0 0 5px 0; font-weight: 600; font-size: 1.1em;">ℹ️ No Students Yet</p>
            <p style="margin: 0; font-size: 0.9em; opacity: 0.9;">Upload a file to begin</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.sidebar.markdown("---")
    
    # Navigation with clear header
    st.sidebar.markdown("""
    <div style="background: rgba(255, 255, 255, 0.1); 
                padding: 15px; 
                border-radius: 10px; 
                border-left: 4px solid #f59e0b;
                backdrop-filter: blur(10px);
                margin: 15px 0;">
        <h3 style="margin: 0 0 5px 0; font-size: 1.2em;">🧭 Navigate</h3>
        <p style="margin: 0; font-size: 0.85em; opacity: 0.9;">
            Choose a section to view
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    app_mode = st.sidebar.radio(
        "Navigation Menu:",
        [
            "📊 Analytics Dashboard",
            "🤖 Murajaat Assistant",
            "🔄 Juzhali Assistant",
            "✨ Jadeed Assistant",
            "📝 Help & Templates"
        ],
        key='nav_radio_main'
    )
    
    st.sidebar.markdown("---")
    
    # Footer
    st.sidebar.markdown("""
    <div style="background: rgba(255, 255, 255, 0.1); 
                padding: 12px; 
                border-radius: 10px; 
                text-align: center;
                backdrop-filter: blur(10px);">
        <p style="margin: 0; font-size: 0.85em; opacity: 0.9;">
            Hifz Tracker v2.0<br>
            Built with ❤️ for Huffaz
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Main content routing (rest of the function remains the same)
    if not st.session_state.selected_student_id and app_mode != "📝 Help & Templates":
        st.markdown("""
        <div style="text-align: center; padding: 60px 20px;">
            <h1 style="color: #1f2937; font-size: 2.5em;">👋 Welcome to Hifz Tracker!</h1>
            <p style="color: #6b7280; font-size: 1.2em; margin-top: 20px;">
                Start by uploading a student file or visit Help & Templates
            </p>
            <div style="margin-top: 40px;">
                <p style="color: #3b82f6; font-size: 1.1em;">📤 Upload Excel file in the sidebar</p>
                <p style="color: #10b981; font-size: 1.1em; margin-top: 10px;">
                    📝 Or download a template from Help & Templates
                </p>
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        # Show data status
        if app_mode != "📝 Help & Templates" and st.session_state.selected_student_id:
            display_data_status_badge(st.session_state.selected_student_id)
            st.markdown("<br>", unsafe_allow_html=True)
        
        # Route to sections
        if app_mode == "📊 Analytics Dashboard":
            if st.session_state.selected_student_id is not None:
                run_analytics_dashboard(st.session_state.selected_student_id)
            else:
                st.error("❌ No student selected")

        elif app_mode == "🤖 Murajaat Assistant":
            if st.session_state.student_data_df is not None:
                run_murajaat_assistant(st.session_state.student_data_df, st.session_state.selected_student_id)
            else:
                st.error("❌ No data loaded")

        elif app_mode == "🔄 Juzhali Assistant":
            if st.session_state.student_data_df is not None:
                run_juzhali_assistant(st.session_state.student_data_df, st.session_state.selected_student_id)
            else:
                st.error("❌ No data loaded")

        elif app_mode == "✨ Jadeed Assistant":
            if st.session_state.student_data_df is not None:
                run_jadeed_assistant(st.session_state.student_data_df, st.session_state.selected_student_id)
            else:
                st.error("❌ No data loaded")

        elif app_mode == "📝 Help & Templates":
            run_help_section()

# =========================================================================
# APPLICATION ENTRY POINT
# =========================================================================

if __name__ == "__main__":
    main()

# =========================================================================
# END OF APPLICATION - CLEAN VERSION COMPLETE! 🎉
# =========================================================================
