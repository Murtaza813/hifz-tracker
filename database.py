# ============================================================================
# FILE: database.py - GOOGLE SHEETS VERSION (AUTO LOCAL/PRODUCTION)
# ============================================================================
# Automatically uses TEST sheet locally, PRODUCTION sheet when deployed!

import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
import streamlit as st
from datetime import datetime
import os
import time

# Google Sheets Configuration
PRODUCTION_SHEET_ID = "1b1sNaNVNWN_wJXaeX0nEJPSgvXJxIPKrzS1IRu0T5yk"  # Real data (deployed)
TEST_SHEET_ID = "1b1sNaNVNWN_wJXaeX0nEJPSgvXJxIPKrzS1IRu0T5yk"  # Test data (local)

SCOPE = [
    'https://spreadsheets.google.com/feeds',
    'https://www.googleapis.com/auth/drive'
]

def is_running_locally():
    """Detect if app is running locally or on Streamlit Cloud"""
    return not os.getenv('STREAMLIT_SHARING_MODE') and not os.getenv('STREAMLIT_SERVER_HEADLESS')

def get_current_sheet_id():
    """Get the appropriate Sheet ID based on environment"""
    if is_running_locally():
        print("🧪 Running LOCALLY - Using TEST database")
        return TEST_SHEET_ID
    else:
        print("🌐 Running on STREAMLIT CLOUD - Using PRODUCTION database")
        return PRODUCTION_SHEET_ID

import time

def get_google_sheet():
    """Connect to Google Sheets using credentials from Streamlit secrets with retry logic"""
    max_retries = 5
    backoff_factor = 2
    
    for attempt in range(max_retries):
        try:
            sheet_id = get_current_sheet_id()
            credentials_dict = dict(st.secrets["gcp_service_account"])
            credentials = ServiceAccountCredentials.from_json_keyfile_dict(
                credentials_dict, SCOPE
            )
            client = gspread.authorize(credentials)
            spreadsheet = client.open_by_key(sheet_id)
            
            print(f"✅ Google Sheets connected successfully (Attempt {attempt + 1}/{max_retries})")
            return spreadsheet
            
        except gspread.exceptions.APIError as e:
            error_code = e.response.status_code if hasattr(e, 'response') else None
            
            # Check if it's a rate limit error (429)
            if error_code == 429 and attempt < max_retries - 1:
                wait_time = backoff_factor ** attempt
                print(f"⚠️ Rate limited (429). Waiting {wait_time}s before retry...")
                time.sleep(wait_time)
                continue
            else:
                # Other API errors or final attempt
                st.error(f"❌ Google Sheets API Error (Code: {error_code}): {str(e)}")
                if attempt == max_retries - 1:
                    st.error(f"❌ Failed to connect after {max_retries} attempts")
                raise e
                
        except Exception as e:
            error_str = str(e).lower()
            
            # Check for other rate limit messages
            if ('quota' in error_str or 'rate limit' in error_str) and attempt < max_retries - 1:
                wait_time = backoff_factor ** attempt
                print(f"⚠️ Quota exceeded. Waiting {wait_time}s before retry...")
                time.sleep(wait_time)
                continue
            else:
                if attempt == max_retries - 1:
                    st.error(f"❌ Failed to connect after {max_retries} attempts: {str(e)}")
                raise e
    
    return None

def init_db():
    """Initialize Google Sheets with required worksheets"""
    try:
        spreadsheet = get_google_sheet()
        if not spreadsheet:
            return
        
        existing_sheets = [ws.title for ws in spreadsheet.worksheets()]
        
        required_sheets = {
            'students': ['id', 'name', 'teacher_name', 'start_date', 'created_at'],
            'sessions': ['id', 'student_id', 'session_type', 'date', 'sipara', 
                        'page', 'jadeed_page', 'ending_ayah', 'talqeen_count', 
                        'tambeeh_count', 'core_mistake', 'specific_mistake', 
                        'overall_grade', 'notes', 'data_format', 'created_at']
        }
        
        for sheet_name, headers in required_sheets.items():
            if sheet_name not in existing_sheets:
                worksheet = spreadsheet.add_worksheet(title=sheet_name, rows=1000, cols=len(headers))
                worksheet.update('A1', [headers])
        
        env = "TEST (Local)" if is_running_locally() else "PRODUCTION (Cloud)"
        print(f"✅ Google Sheets ({env}) initialized successfully!")
        
    except Exception as e:
        print(f"❌ Error initializing sheets: {e}")

def get_all_students():
    """Get all students from Google Sheets with retry logic"""
    max_retries = 3
    
    for attempt in range(max_retries):
        try:
            spreadsheet = get_google_sheet()
            if not spreadsheet:
                return {}
            
            worksheet = spreadsheet.worksheet('students')
            data = worksheet.get_all_records()
            
            if not data:
                return {}
            
            return {row['name']: row['id'] for row in data}
        
        except gspread.exceptions.APIError as e:
            if hasattr(e, 'response') and e.response.status_code == 429:
                wait_time = 2 ** attempt
                print(f"Rate limited loading students. Waiting {wait_time}s...")
                time.sleep(wait_time)
                continue
            print(f"❌ Error getting students: {e}")
            return {}
    
    return {}

def student_exists(name):
    """Check if student exists"""
    students = get_all_students()
    return name in students

def save_student_from_excel(parsed_data):
    """Save student and sessions from Excel file with retry logic"""
    max_retries = 3
    
    for attempt in range(max_retries):
        try:
            # ... [keep all your existing code up to the batch upload section] ...
            
            # Write all rows at once (BATCH UPLOAD - 1 API call instead of 247!)
            if all_session_rows:
                st.sidebar.info(f"📤 Uploading {len(all_session_rows)} sessions in batch (Attempt {attempt + 1}/{max_retries})...")
                
                # Add retry for the batch upload
                for upload_attempt in range(3):
                    try:
                        sessions_ws.append_rows(all_session_rows, value_input_option='USER_ENTERED')
                        st.sidebar.success(f"✅ Saved {len(all_session_rows)} sessions for student {student_name}")
                        return student_id
                    except gspread.exceptions.APIError as e:
                        if hasattr(e, 'response') and e.response.status_code == 429:
                            wait_time = 2 ** upload_attempt
                            st.sidebar.warning(f"Upload rate limited. Waiting {wait_time}s...")
                            time.sleep(wait_time)
                            continue
                        raise e
                
            else:
                st.sidebar.warning("⚠️ No sessions to save")
            
            return student_id
        
        except gspread.exceptions.APIError as e:
            if hasattr(e, 'response') and e.response.status_code == 429:
                wait_time = 2 ** attempt
                st.sidebar.warning(f"Rate limited overall. Waiting {wait_time}s before retry...")
                time.sleep(wait_time)
                continue
            st.sidebar.error(f"❌ Error in save_student_from_excel: {str(e)}")
            import traceback
            st.sidebar.code(traceback.format_exc())
            return None
    
    return None

def get_all_student_sessions(student_id):
    """Get all sessions for a student - UPDATED TO HANDLE EMPTY GRADES with retry"""
    max_retries = 3
    
    for attempt in range(max_retries):
        try:
            spreadsheet = get_google_sheet()
            if not spreadsheet:
                return pd.DataFrame()
            
            worksheet = spreadsheet.worksheet('sessions')
            data = worksheet.get_all_records()
            
            if not data:
                return pd.DataFrame()
            
            df = pd.DataFrame(data)
            df = df[df['student_id'] == student_id]
            
            # Standardize column names
            df = df.rename(columns={
                'session_type': 'Session_Type',
                'date': 'Date',
                'sipara': 'Sipara',
                'page': 'Page',
                'jadeed_page': 'Jadeed_Page',
                'ending_ayah': 'Ending_Ayah',
                'talqeen_count': 'Mistake_Count',
                'tambeeh_count': 'Tambeeh_Count',
                'core_mistake': 'Core_Mistake',
                'specific_mistake': 'Specific_Mistake',
                'overall_grade': 'Overall_Grade',
                'notes': 'Notes',
                'data_format': 'Data_Format'
            })
            
            # ✅ ADD THIS: Convert empty strings to None for Overall_Grade
            df['Overall_Grade'] = df['Overall_Grade'].replace('', None)
            
            # Convert numeric columns
            df['Mistake_Count'] = pd.to_numeric(df['Mistake_Count'], errors='coerce').fillna(0)
            df['Tambeeh_Count'] = pd.to_numeric(df['Tambeeh_Count'], errors='coerce').fillna(0)
            
            df['Date'] = pd.to_datetime(df['Date'])
            df = df.sort_values('Date', ascending=False)
            
            return df
        
        except gspread.exceptions.APIError as e:
            if hasattr(e, 'response') and e.response.status_code == 429:
                wait_time = 2 ** attempt
                print(f"Rate limited loading sessions. Waiting {wait_time}s...")
                time.sleep(wait_time)
                continue
            print(f"❌ Error getting sessions: {e}")
            return pd.DataFrame()
    
    return pd.DataFrame()

def get_student_data(student_id):
    """Get all data for a student by type"""
    all_sessions = get_all_student_sessions(student_id)
    
    if all_sessions.empty:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
    
    jadeed = all_sessions[all_sessions['Session_Type'] == 'Jadeed']
    juzhali = all_sessions[all_sessions['Session_Type'] == 'Juzhali']
    murajaat = all_sessions[all_sessions['Session_Type'] == 'Murajaat']
    
    return jadeed, juzhali, murajaat

def append_new_session(student_id, session_type, session_data):
    """Add a new session"""
    try:
        spreadsheet = get_google_sheet()
        if not spreadsheet:
            return False
        
        worksheet = spreadsheet.worksheet('sessions')
        existing_data = worksheet.get_all_values()
        new_id = len(existing_data)
        
        date_str = session_data['date']
        if hasattr(date_str, 'strftime'):
            date_str = date_str.strftime('%Y-%m-%d')
        
        new_row = [
            new_id,
            student_id,
            session_type,
            date_str,
            session_data.get('sipara', ''),
            session_data.get('page_tested', ''),
            session_data.get('jadeed_page', ''),
            session_data.get('end_ayah', ''),
            session_data.get('talqeen_count', 0),
            session_data.get('tambeeh_count', 0),
            session_data.get('core_mistake_type', ''),
            session_data.get('specific_mistake', ''),
            session_data.get('overall_grade', ''),
            session_data.get('notes', ''),
            'session_entry',
            datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        ]
        
        worksheet.append_row(new_row)
        return True
    
    except Exception as e:
        print(f"❌ Error saving session: {e}")
        return False

def export_student_to_excel(student_id):
    """Export student data to Excel"""
    try:
        jadeed, juzhali, murajaat = get_student_data(student_id)
        
        output_path = f"student_{student_id}_export.xlsx"
        
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            if not jadeed.empty:
                jadeed.to_excel(writer, sheet_name='JADEED', index=False)
            if not juzhali.empty:
                juzhali.to_excel(writer, sheet_name='JUZHALI', index=False)
            if not murajaat.empty:
                murajaat.to_excel(writer, sheet_name='MURAJAAT', index=False)
        
        return output_path
    except Exception as e:
        print(f"❌ Error exporting: {e}")
        return None

def get_data_format_info(student_id):
    """Get info about data formats"""
    try:
        df = get_all_student_sessions(student_id)
        
        if df.empty:
            return {
                'has_uploaded': False,
                'has_detailed': False,
                'uploaded_count': 0,
                'detailed_count': 0
            }
        
        uploaded = df[df['Data_Format'] == 'upload']
        detailed = df[df['Data_Format'] == 'session_entry']
        
        return {
            'has_uploaded': len(uploaded) > 0,
            'has_detailed': len(detailed) > 0,
            'uploaded_count': len(uploaded),
            'detailed_count': len(detailed)
        }
    except:
        return {
            'has_uploaded': False,
            'has_detailed': False,
            'uploaded_count': 0,
            'detailed_count': 0
        }

def get_last_jadeed_page(all_data_df):
    """Get the last Jadeed page"""
    try:
        if all_data_df is None or all_data_df.empty:
            return None
        
        jadeed = all_data_df[all_data_df['Session_Type'] == 'Jadeed'].copy()
        if jadeed.empty:
            return None
        
        jadeed['Date'] = pd.to_datetime(jadeed['Date'])
        jadeed = jadeed.sort_values('Date', ascending=False)
        latest = jadeed.iloc[0]
        
        if 'Jadeed_Page' in latest.index and pd.notna(latest['Jadeed_Page']):
            return int(latest['Jadeed_Page'])
        elif 'Page' in latest.index and pd.notna(latest['Page']):
            return int(latest['Page'])
        
        return None
    except Exception as e:
        print(f"❌ Error getting last jadeed page: {e}")
        return None

