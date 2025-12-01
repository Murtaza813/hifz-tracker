# ============================================================================
# FILE: database.py - GOOGLE SHEETS VERSION
# ============================================================================
# Simple Google Sheets implementation - no SQLite, no PostgreSQL needed!

import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
import streamlit as st
from datetime import datetime
import json

# Google Sheets Configuration
SHEET_ID = "1ZkGPICCFMxu_v8x565Zzz30Nljbx73fXaKo1xyXEroQ"
SCOPE = [
    'https://spreadsheets.google.com/feeds',
    'https://www.googleapis.com/auth/drive'
]

def get_google_sheet():
    """Connect to Google Sheets using credentials from Streamlit secrets"""
    try:
        # Get credentials from Streamlit secrets
        credentials_dict = dict(st.secrets["gcp_service_account"])
        credentials = ServiceAccountCredentials.from_json_keyfile_dict(
            credentials_dict, SCOPE
        )
        client = gspread.authorize(credentials)
        spreadsheet = client.open_by_key(SHEET_ID)
        return spreadsheet
    except Exception as e:
        st.error(f"❌ Failed to connect to Google Sheets: {e}")
        return None

def init_db():
    """Initialize Google Sheets with required worksheets"""
    try:
        spreadsheet = get_google_sheet()
        if not spreadsheet:
            return
        
        # Create worksheets if they don't exist
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
            
        print("✅ Google Sheets initialized successfully!")
        
    except Exception as e:
        print(f"❌ Error initializing sheets: {e}")

def get_all_students():
    """Get all students from Google Sheets"""
    try:
        spreadsheet = get_google_sheet()
        if not spreadsheet:
            return {}
        
        worksheet = spreadsheet.worksheet('students')
        data = worksheet.get_all_records()
        
        if not data:
            return {}
        
        return {row['name']: row['id'] for row in data}
    
    except Exception as e:
        print(f"❌ Error getting students: {e}")
        return {}

def student_exists(name):
    """Check if student exists"""
    students = get_all_students()
    return name in students

def save_student_from_excel(parsed_data):
    """Save student and sessions from Excel file"""
    try:
        if 'error' in parsed_data and parsed_data['error']:
            return None
        
        student_info = parsed_data['student_info']
        student_name = student_info['Student_Name'].iloc[0]
        teacher_name = student_info.get('Teacher_Name', pd.Series(['Unknown'])).iloc[0]
        
        # Get or create student
        students = get_all_students()
        
        if student_name in students:
            student_id = students[student_name]
        else:
            # Create new student
            spreadsheet = get_google_sheet()
            students_ws = spreadsheet.worksheet('students')
            
            existing_data = students_ws.get_all_values()
            new_id = len(existing_data)  # Simple ID generation
            
            new_row = [
                new_id,
                student_name,
                teacher_name,
                datetime.now().strftime('%Y-%m-%d'),
                datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            ]
            students_ws.append_row(new_row)
            student_id = new_id
        
        # Save sessions
        sessions_ws = spreadsheet.worksheet('sessions')
        existing_sessions = sessions_ws.get_all_values()
        next_session_id = len(existing_sessions)
        
        for session_type in ['murajaat', 'juzhali', 'jadeed']:
            df = parsed_data[session_type]
            if df.empty:
                continue
            
            for _, row in df.iterrows():
                session_row = [
                    next_session_id,
                    student_id,
                    session_type.capitalize(),
                    pd.Timestamp(row.get('date')).strftime('%Y-%m-%d'),
                    row.get('sipara', ''),
                    row.get('page_tested', row.get('page_count', '')),
                    row.get('jadeed_page', ''),
                    row.get('ending_ayah', ''),
                    row.get('talqeen_count', 0),
                    row.get('tambeeh_count', 0),
                    row.get('core_mistake_type', ''),
                    row.get('specific_mistake', ''),
                    row.get('overall_grade', ''),
                    row.get('notes', ''),
                    parsed_data['format'],
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                ]
                sessions_ws.append_row(session_row)
                next_session_id += 1
        
        return student_id
    
    except Exception as e:
        print(f"❌ Error saving student: {e}")
        return None

def get_all_student_sessions(student_id):
    """Get all sessions for a student"""
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
        
        df['Date'] = pd.to_datetime(df['Date'])
        df = df.sort_values('Date', ascending=False)
        
        return df
    
    except Exception as e:
        print(f"❌ Error getting sessions: {e}")
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
