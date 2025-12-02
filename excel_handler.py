# ============================================================================
# FILE: excel_handler.py - COMPLETE FILE FOR PART 2
# ============================================================================
# This is your COMPLETE excel_handler.py file with format detection & parsing

import pandas as pd
import numpy as np
from io import BytesIO
import openpyxl

# ===== FUNCTION 1: DETECT FORMAT =====
def detect_excel_format(xls):
    """
    Detect which format the Excel file is in.
    
    Format 1 (UPLOAD): Date, Sipara, Overall_Grade, Notes
    Format 2 (SESSION): Has Talqeen and Tambeeh columns
    
    Returns: 'upload', 'session_entry', or 'unknown'
    """
    
    sheets = xls.sheet_names
    
    if 'MURAJAAT' not in sheets:
        return 'unknown'
    
    try:
        # Read just the header row
        mura_df = pd.read_excel(xls, 'MURAJAAT', nrows=0)
        mura_cols = set(mura_df.columns)
        
        # Check for detailed format columns
        has_talqeen = 'Talqeen' in mura_cols or 'talqeen' in mura_cols
        has_tambeeh = 'Tambeeh' in mura_cols or 'tambeeh' in mura_cols
        
        if has_talqeen and has_tambeeh:
            return 'session_entry'
        else:
            return 'upload'
    
    except Exception as e:
        print(f"Error detecting format: {e}")
        return 'unknown'

# ===== FUNCTION 2: PARSE UPLOAD FORMAT =====
def parse_upload_format(xls):
    """
    Parse old teacher format (marks only).
    
    Expected columns:
    MURAJAAT: Date, Sipara, Overall_Grade, Notes
    JUZHALI: Date, Page_Range, Overall_Grade, Notes
    JADEED: Date, Page, Ending_Ayah, Final_Grade, Notes
    """
    
    try:
        # Read STUDENT_INFO
        student_info = pd.read_excel(xls, 'STUDENT_INFO')
        
        # Read MURAJAAT (Sipara + Mark)
        murajaat_raw = pd.read_excel(xls, 'MURAJAAT')
        murajaat = murajaat_raw.copy()
        
        # Standardize column names
        murajaat.columns = [col.strip().lower() for col in murajaat.columns]
        murajaat = murajaat.rename(columns={
            'date': 'date',
            'sipara': 'sipara',
            'overall_grade': 'overall_grade',
            'notes': 'notes'
        })
        
        murajaat['session_type'] = 'Murajaat'
        murajaat['data_format'] = 'upload'
        
        # Read JUZHALI (Page_Range + Mark)
        juzhali_raw = pd.read_excel(xls, 'JUZHALI')
        juzhali = juzhali_raw.copy()
        
        juzhali.columns = [col.strip().lower() for col in juzhali.columns]
        juzhali = juzhali.rename(columns={
            'date': 'date',
            'page_range': 'page_count',
            'overall_grade': 'overall_grade',
            'notes': 'notes'
        })
        
        juzhali['page_count'] = pd.to_numeric(juzhali['page_count'], errors='coerce')
        juzhali['session_type'] = 'Juzhali'
        juzhali['data_format'] = 'upload'
        
        # Read JADEED (Page + Ending_Ayah + Mark)
        jadeed_raw = pd.read_excel(xls, 'JADEED')
        jadeed = jadeed_raw.copy()
        
        jadeed.columns = [col.strip().lower() for col in jadeed.columns]
        jadeed = jadeed.rename(columns={
            'date': 'date',
            'page': 'jadeed_page',
            'ending_ayah': 'ending_ayah',
            'final_grade': 'overall_grade',
            'notes': 'notes'
        })
        
        jadeed['jadeed_page'] = pd.to_numeric(jadeed['jadeed_page'], errors='coerce')
        jadeed['ending_ayah'] = pd.to_numeric(jadeed['ending_ayah'], errors='coerce')
        jadeed['session_type'] = 'Jadeed'
        jadeed['data_format'] = 'upload'
        
        return {
            'student_info': student_info,
            'murajaat': murajaat,
            'juzhali': juzhali,
            'jadeed': jadeed,
            'format': 'upload',
            'error': None
        }
    
    except Exception as e:
        return {
            'error': f"Error parsing upload format: {str(e)}",
            'format': None
        }

# ===== FUNCTION 3: PARSE SESSION ENTRY FORMAT =====
def parse_session_entry_format(xls):
    """
    Parse new detailed format (with Talqeen/Tambeeh).
    
    Expected columns:
    MURAJAAT: Date, Sipara, Page, Talqeen, Tambeeh, Overall_Grade, Notes
    JUZHALI: Date, Page, Talqeen, Tambeeh, Overall_Grade, Notes
    JADEED: Date, Page, Start_Ayah, End_Ayah, Tambeeh, Final_Grade, Notes
    """
    
    try:
        # Read STUDENT_INFO
        student_info = pd.read_excel(xls, 'STUDENT_INFO')
        
        # Read MURAJAAT
        murajaat_raw = pd.read_excel(xls, 'MURAJAAT')
        murajaat = murajaat_raw.copy()
        
        murajaat.columns = [col.strip().lower() for col in murajaat.columns]
        murajaat = murajaat.rename(columns={
            'date': 'date',
            'sipara': 'sipara',
            'page': 'page_tested',
            'talqeen': 'talqeen_count',
            'tambeeh': 'tambeeh_count',
            'overall_grade': 'overall_grade',
            'notes': 'notes'
        })
        
        murajaat['session_type'] = 'Murajaat'
        murajaat['data_format'] = 'session_entry'
        
        # Read JUZHALI
        juzhali_raw = pd.read_excel(xls, 'JUZHALI')
        juzhali = juzhali_raw.copy()
        
        juzhali.columns = [col.strip().lower() for col in juzhali.columns]
        juzhali = juzhali.rename(columns={
            'date': 'date',
            'page': 'juzhali_page',
            'talqeen': 'talqeen_count',
            'tambeeh': 'tambeeh_count',
            'overall_grade': 'overall_grade',
            'notes': 'notes'
        })
        
        juzhali['session_type'] = 'Juzhali'
        juzhali['data_format'] = 'session_entry'
        
        # Read JADEED
        jadeed_raw = pd.read_excel(xls, 'JADEED')
        jadeed = jadeed_raw.copy()
        
        jadeed.columns = [col.strip().lower() for col in jadeed.columns]
        jadeed = jadeed.rename(columns={
            'date': 'date',
            'page': 'jadeed_page',
            'start_ayah': 'start_ayah',
            'end_ayah': 'end_ayah',
            'tambeeh': 'tambeeh_count',
            'final_grade': 'overall_grade',
            'notes': 'notes'
        })
        
        jadeed['session_type'] = 'Jadeed'
        jadeed['data_format'] = 'session_entry'
        
        # Convert numeric columns
        for df in [murajaat, juzhali, jadeed]:
            numeric_cols = ['page_tested', 'juzhali_page', 'jadeed_page', 
                          'start_ayah', 'end_ayah', 'talqeen_count', 'tambeeh_count', 'sipara']
            for col in numeric_cols:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
        
        return {
            'student_info': student_info,
            'murajaat': murajaat,
            'juzhali': juzhali,
            'jadeed': jadeed,
            'format': 'session_entry',
            'error': None
        }
    
    except Exception as e:
        return {
            'error': f"Error parsing session entry format: {str(e)}",
            'format': None
        }

# ===== FUNCTION 4: MAIN PARSE FUNCTION =====
def parse_excel_file(uploaded_file):
    """
    Main function to parse Excel file - auto-detects format.
    
    Returns:
    {
        'student_info': DataFrame,
        'murajaat': DataFrame,
        'juzhali': DataFrame,
        'jadeed': DataFrame,
        'format': 'upload' or 'session_entry',
        'error': None or error message
    }
    """
    
    try:
        xls = pd.ExcelFile(uploaded_file)
        
        # Step 1: Detect format
        detected_format = detect_excel_format(xls)
        
        if detected_format == 'unknown':
            return {
                'error': "Could not detect file format. Check MURAJAAT sheet columns.",
                'format': None
            }
        
        # Step 2: Parse based on format
        if detected_format == 'upload':
            return parse_upload_format(xls)
        elif detected_format == 'session_entry':
            return parse_session_entry_format(xls)
        
    except Exception as e:
        return {
            'error': f"Error parsing Excel: {str(e)}",
            'format': None
        }

# ===== EXISTING FUNCTIONS (Keep these) =====

def calculate_juzhali_range(last_jadeed_page, juzhali_length=10):
    """Calculate Juzhali page range from last Jadeed page"""
    if last_jadeed_page is None:
        return None, None
    
    juzhali_end = last_jadeed_page
    juzhali_start = max(1, juzhali_end - juzhali_length + 1)
    
    return juzhali_start, juzhali_end

def get_murajaat_available_pages(last_jadeed_page, juzhali_length=10):
    """Get pages available for Murajaat review"""
    if last_jadeed_page is None:
        return {}
    
    juzhali_start, _ = calculate_juzhali_range(last_jadeed_page, juzhali_length)
    
    murajaat_pages = {}
    
    # Add all completed siparas (pages before Juzhali)
    for page in range(1, juzhali_start):
        sipara = ((page - 1) // 20) + 1
        page_in_sipara = ((page - 1) % 20) + 1
        
        if str(sipara) not in murajaat_pages:
            murajaat_pages[str(sipara)] = []
        
        murajaat_pages[str(sipara)].append(page_in_sipara)
    
    return murajaat_pages

def convert_df_for_dashboard(jadeed_df, juzhali_df, murajaat_df):
    """Convert data for dashboard use"""
    
    all_data = pd.concat([jadeed_df, juzhali_df, murajaat_df], ignore_index=True)
    return all_data if not all_data.empty else pd.DataFrame()

def create_sample_excel_template():
    """Create sample Excel template for upload"""
    
    output = BytesIO()
    
    # Create Excel writer
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        
        # STUDENT_INFO sheet
        student_info = pd.DataFrame({
            'Student_Name': ['Ahmed Ali'],
            'Teacher_Name': ['Ustadh Ahmed'],
            'Start_Date': ['2025-01-15']
        })
        student_info.to_excel(writer, sheet_name='STUDENT_INFO', index=False)
        
        # MURAJAAT sheet (Upload format)
        murajaat = pd.DataFrame({
            'Date': ['2025-11-01', '2025-11-02'],
            'Sipara': [1, 2],
            'Overall_Grade': [8, 7],
            'Notes': ['Good session', 'Page 15 weak']
        })
        murajaat.to_excel(writer, sheet_name='MURAJAAT', index=False)
        
        # JUZHALI sheet (Upload format)
        juzhali = pd.DataFrame({
            'Date': ['2025-11-01', '2025-11-02'],
            'Page_Range': [10, 10],
            'Overall_Grade': ['جيد', 'جيد جدا'],
            'Notes': ['10 pages tested', 'Better today']
        })
        juzhali.to_excel(writer, sheet_name='JUZHALI', index=False)
        
        # JADEED sheet (Upload format)
        jadeed = pd.DataFrame({
            'Date': ['2025-11-01', '2025-11-02', '2025-11-03'],
            'Page': [33, 33, 34],
            'Ending_Ayah': [23, 46, 70],
            'Final_Grade': [8, 7, 8],
            'Notes': ['Half page', '2nd half', 'Full page']
        })
        jadeed.to_excel(writer, sheet_name='JADEED', index=False)
    
    output.seek(0)
    return output.getvalue()
