# ============================================================================
# FILE: database.py - COMPLETE FILE FOR PART 1
# ============================================================================
# This is your COMPLETE database.py file with new two-format support

import sqlite3
import pandas as pd
from datetime import datetime
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "hifz_tracker.db")

def get_db_connection():
    """Create and return database connection"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize database with all tables"""
    conn = get_db_connection()
    print("✅ DEBUG: Database connected!")
    cursor = conn.cursor()
    
    # ===== TABLE 1: STUDENTS =====
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            teacher_name TEXT,
            start_date DATE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # ===== TABLE 2: UPLOADED_SESSIONS (Old format - marks only) =====
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS uploaded_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            session_type TEXT NOT NULL,
            date DATE NOT NULL,
            
            sipara INTEGER,
            page_count INTEGER,
            jadeed_page INTEGER,
            ending_ayah INTEGER,
            starting_ayah INTEGER,
            
            overall_grade TEXT,
            notes TEXT,
            
            data_format TEXT DEFAULT 'upload',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            FOREIGN KEY (student_id) REFERENCES students(id)
        )
    ''')
    
    # ===== TABLE 3: DETAILED_SESSIONS (New format - with Talqeen/Tambeeh) =====
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS detailed_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            session_type TEXT NOT NULL,
            date DATE NOT NULL,
            
            sipara INTEGER,
            page_tested INTEGER,
            juzhali_page INTEGER,
            jadeed_page INTEGER,
            start_ayah INTEGER,
            end_ayah INTEGER,
            
            talqeen_count INTEGER DEFAULT 0,
            tambeeh_count INTEGER DEFAULT 0,
            
            core_mistake_type TEXT,
            specific_mistake TEXT,
            
            overall_grade TEXT,
            notes TEXT,
            
            data_format TEXT DEFAULT 'session_entry',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            FOREIGN KEY (student_id) REFERENCES students(id)
        )
    ''')
    
    conn.commit()
    conn.close()

# ===== NEW FUNCTION: Save to uploaded_sessions =====
def save_to_uploaded_sessions(student_id, parsed_data):
    """Save old format data (marks only) to uploaded_sessions table"""
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        for session_type in ['murajaat', 'juzhali', 'jadeed']:
            df = parsed_data[session_type]
            
            print(f"🔍 DEBUG: Processing {session_type} - {len(df)} rows")
            
            if df.empty:
                print(f"🔍 DEBUG: {session_type} is empty, skipping")
                continue
            
            for idx, row in df.iterrows():
                # Convert date to string
                date_val = pd.Timestamp(row.get('date')).strftime('%Y-%m-%d')
                
                print(f"🔍 DEBUG: Saving {session_type} row {idx}: Date={date_val}")
                
                cursor.execute('''
                    INSERT INTO uploaded_sessions 
                    (student_id, session_type, date, sipara, page_count,
                     jadeed_page, ending_ayah, overall_grade, notes, data_format)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', [
                    student_id,
                    row.get('session_type'),
                    date_val,
                    row.get('sipara') if pd.notna(row.get('sipara')) else None,
                    row.get('page_count') if pd.notna(row.get('page_count')) else None,
                    row.get('jadeed_page') if pd.notna(row.get('jadeed_page')) else None,
                    row.get('ending_ayah') if pd.notna(row.get('ending_ayah')) else None,
                    row.get('overall_grade'),
                    row.get('notes'),
                    'upload'
                ])
        
        conn.commit()
        print("✅ DEBUG: All sessions saved successfully!")
        return True
    
    except Exception as e:
        print(f"❌ ERROR saving to uploaded_sessions: {e}")
        import traceback
        traceback.print_exc()
        conn.rollback()
        return False
    
    finally:
        conn.close()

# ===== NEW FUNCTION: Save to detailed_sessions =====
def save_to_detailed_sessions(student_id, parsed_data):
    """Save new format data (with mistakes) to detailed_sessions table"""
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        for session_type in ['murajaat', 'juzhali', 'jadeed']:
            df = parsed_data[session_type]
            
            if df.empty:
                continue
            
            for _, row in df.iterrows():
                date_val = pd.Timestamp(row.get('date')).strftime('%Y-%m-%d')
                
                cursor.execute('''
                    INSERT INTO detailed_sessions 
                    (student_id, session_type, date, sipara, page_tested,
                     juzhali_page, jadeed_page, start_ayah, end_ayah,
                     talqeen_count, tambeeh_count, overall_grade, notes, data_format)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', [
                    student_id,
                    row.get('session_type'),
                    date_val,
                    row.get('sipara') if pd.notna(row.get('sipara')) else None,
                    row.get('page_tested') if pd.notna(row.get('page_tested')) else None,
                    row.get('juzhali_page') if pd.notna(row.get('juzhali_page')) else None,
                    row.get('jadeed_page') if pd.notna(row.get('jadeed_page')) else None,
                    row.get('start_ayah') if pd.notna(row.get('start_ayah')) else None,
                    row.get('end_ayah') if pd.notna(row.get('end_ayah')) else None,
                    row.get('talqeen_count') if pd.notna(row.get('talqeen_count')) else 0,
                    row.get('tambeeh_count') if pd.notna(row.get('tambeeh_count')) else 0,
                    row.get('overall_grade'),
                    row.get('notes'),
                    'session_entry'
                ])
        
        conn.commit()
        return True
    
    except Exception as e:
        print(f"Error saving to detailed_sessions: {e}")
        conn.rollback()
        return False
    
    finally:
        conn.close()

# ===== NEW FUNCTION: Save student from Excel =====
def save_student_from_excel(parsed_data):
    """Save student and all sessions based on detected format"""
    
    if 'error' in parsed_data and parsed_data['error']:
        print(f"❌ Cannot save: {parsed_data['error']}")
        return None
    
    data_format = parsed_data['format']
    student_info = parsed_data['student_info']
    
    try:
        # Get student info
        student_name = student_info['Student_Name'].iloc[0]
        teacher_name = student_info['Teacher_Name'].iloc[0] if 'Teacher_Name' in student_info else 'Unknown'

        # Convert start_date to string format
        if 'Start_Date' in student_info and pd.notna(student_info['Start_Date'].iloc[0]):
            start_date = pd.to_datetime(student_info['Start_Date'].iloc[0]).strftime('%Y-%m-%d')
        else:
            start_date = None
        
        print(f"🔍 DEBUG: Trying to save student: {student_name}")
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if student exists
        cursor.execute('SELECT id FROM students WHERE name = ?', [student_name])
        result = cursor.fetchone()
        
        if result:
            student_id = result[0]
            print(f"✅ DEBUG: Student '{student_name}' already exists with ID: {student_id}")
        else:
            # Insert new student
            cursor.execute('''
                INSERT INTO students (name, teacher_name, start_date)
                VALUES (?, ?, ?)
            ''', [student_name, teacher_name, start_date])
            conn.commit()
            
            # Get the new student ID
            student_id = cursor.lastrowid
            print(f"✅ DEBUG: NEW Student '{student_name}' created with ID: {student_id}")
        
        conn.close()
        
        # Debug: Show session counts
        print(f"🔍 DEBUG: Session counts - Murajaat: {len(parsed_data['murajaat'])}, Juzhali: {len(parsed_data['juzhali'])}, Jadeed: {len(parsed_data['jadeed'])}")
        
        # Save sessions based on format
        if data_format == 'upload':
            print("🔍 DEBUG: Saving to uploaded_sessions table...")
            success = save_to_uploaded_sessions(student_id, parsed_data)
        elif data_format == 'session_entry':
            print("🔍 DEBUG: Saving to detailed_sessions table...")
            success = save_to_detailed_sessions(student_id, parsed_data)
        else:
            print(f"❌ DEBUG: Unknown format: {data_format}")
            return None
        
        if success:
            print(f"✅ DEBUG: All sessions saved successfully! Returning student_id: {student_id}")
            return student_id
        else:
            print(f"❌ DEBUG: Failed to save sessions")
            return None
    
    except Exception as e:
        print(f"❌ ERROR in save_student_from_excel: {e}")
        import traceback
        traceback.print_exc()
        return None

# ===== NEW FUNCTION: Get all student sessions =====
def get_all_student_sessions(student_id):
    """Get all sessions from both tables (uploaded + detailed) - FIXED VERSION"""
    
    try:
        conn = get_db_connection()
        
        print(f"🔍 DEBUG: Loading data for student_id: {student_id}")
        
        # Fetch from uploaded_sessions
        uploaded = pd.read_sql('''
            SELECT * FROM uploaded_sessions 
            WHERE student_id = ?
        ''', conn, params=[student_id])
        
        # Fetch from detailed_sessions
        detailed = pd.read_sql('''
            SELECT * FROM detailed_sessions 
            WHERE student_id = ?
        ''', conn, params=[student_id])
        
        conn.close()
        
        print(f"🔍 DEBUG: Loaded {len(uploaded)} uploaded sessions and {len(detailed)} detailed sessions")
        
        # If both empty
        if uploaded.empty and detailed.empty:
            print("🔍 DEBUG: Both tables are empty")
            return pd.DataFrame()
        
        # Handle column standardization separately for each DataFrame
        def standardize_columns(df, source_type):
            """Standardize column names for compatibility"""
            if df.empty:
                return df
                
            df = df.copy()
            
            # Add source identifier
            df['Data_Source'] = source_type
            
            # Standardize column names - be more flexible
            column_mappings = [
                # Session info
                ('session_type', 'Session_Type'),
                ('date', 'Date'),
                
                # Page/Sipara info
                ('sipara', 'Sipara'),
                ('page_tested', 'Page'),
                ('page_count', 'Page'),
                ('juzhali_page', 'Page'),
                
                # Jadeed specific
                ('jadeed_page', 'Jadeed_Page'),
                
                # Ayah info
                ('start_ayah', 'Starting_Ayah'),
                ('end_ayah', 'Ending_Ayah'),
                ('ending_ayah', 'Ending_Ayah'),
                ('starting_ayah', 'Starting_Ayah'),
                
                # Mistake info (for detailed sessions)
                ('talqeen_count', 'Mistake_Count'),
                ('tambeeh_count', 'Tambeeh_Count'),
                ('core_mistake_type', 'Core_Mistake'),
                ('specific_mistake', 'Specific_Mistake'),
                
                # Grade info
                ('overall_grade', 'Overall_Grade'),
                ('notes', 'Notes'),
                ('data_format', 'Data_Format')
            ]
            
            # Apply column mappings that exist in the DataFrame
            for old_col, new_col in column_mappings:
                if old_col in df.columns and new_col not in df.columns:
                    df[new_col] = df[old_col]
            
            return df
        
        # Standardize both dataframes
        uploaded_std = standardize_columns(uploaded, 'uploaded')
        detailed_std = standardize_columns(detailed, 'detailed')
        
        print(f"🔍 DEBUG: Uploaded columns after standardization: {uploaded_std.columns.tolist() if not uploaded_std.empty else 'Empty'}")
        print(f"🔍 DEBUG: Detailed columns after standardization: {detailed_std.columns.tolist() if not detailed_std.empty else 'Empty'}")
        
        # Combine the dataframes
        if uploaded_std.empty:
            combined_data = detailed_std
        elif detailed_std.empty:
            combined_data = uploaded_std
        else:
            # Get all unique columns from both dataframes
            all_columns = set(uploaded_std.columns) | set(detailed_std.columns)
            
            # Add missing columns to each dataframe
            for col in all_columns:
                if col not in uploaded_std.columns:
                    uploaded_std[col] = None
                if col not in detailed_std.columns:
                    detailed_std[col] = None
            
            # Now combine
            combined_data = pd.concat([uploaded_std, detailed_std], ignore_index=True, sort=False)
        
        # Ensure we have Session_Type column (critical for the app)
        if not combined_data.empty:
            if 'Session_Type' not in combined_data.columns:
                # Try to find alternative session type column
                for col in combined_data.columns:
                    if 'session' in col.lower() and 'type' in col.lower():
                        combined_data['Session_Type'] = combined_data[col]
                        break
            
            # Sort by date if available
            if 'Date' in combined_data.columns:
                combined_data['Date'] = pd.to_datetime(combined_data['Date'], errors='coerce')
                combined_data = combined_data.sort_values('Date', ascending=False)
            
            print(f"🔍 DEBUG: Final combined data shape: {combined_data.shape}")
            print(f"🔍 DEBUG: Session types in combined data: {combined_data['Session_Type'].unique() if 'Session_Type' in combined_data.columns else 'No Session_Type column'}")
        
        return combined_data
    
    except Exception as e:
        print(f"❌ ERROR in get_all_student_sessions: {e}")
        import traceback
        traceback.print_exc()
        return pd.DataFrame()

# ===== DEBUG FUNCTION =====
def debug_get_all_student_sessions(student_id):
    """Debug function to see what's happening with data loading"""
    print(f"🔍 DEBUG: Loading data for student_id: {student_id}")
    
    conn = get_db_connection()
    
    # Check uploaded_sessions
    uploaded = pd.read_sql('''
        SELECT * FROM uploaded_sessions 
        WHERE student_id = ?
    ''', conn, params=[student_id])
    print(f"🔍 DEBUG: uploaded_sessions count: {len(uploaded)}")
    
    # Check detailed_sessions  
    detailed = pd.read_sql('''
        SELECT * FROM detailed_sessions 
        WHERE student_id = ?
    ''', conn, params=[student_id])
    print(f"🔍 DEBUG: detailed_sessions count: {len(detailed)}")
    
    conn.close()
    
    return uploaded, detailed

# ===== EXISTING FUNCTIONS =====

def get_all_students():
    """Get all students from database"""
    try:
        conn = get_db_connection()
        students = pd.read_sql('SELECT id, name FROM students ORDER BY name', conn)
        conn.close()
        
        if students.empty:
            return {}
        
        return dict(zip(students['name'], students['id']))
    except:
        return {}

def get_student_data(student_id):
    """Get all data for a student (both formats)"""
    all_sessions = get_all_student_sessions(student_id)
    
    if all_sessions.empty:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
    
    jadeed_data = all_sessions[all_sessions['Session_Type'] == 'Jadeed']
    juzhali_data = all_sessions[all_sessions['Session_Type'] == 'Juzhali']
    murajaat_data = all_sessions[all_sessions['Session_Type'] == 'Murajaat']
    
    return jadeed_data, juzhali_data, murajaat_data

def student_exists(name):
    """Check if student already exists"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT id FROM students WHERE name = ?', [name])
        result = cursor.fetchone()
        conn.close()
        return result is not None
    except:
        return False

def append_new_session(student_id, session_type, session_data):
    """Add a new session to detailed_sessions table"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Convert date to string if it's a datetime object
        date_str = session_data['date']
        if hasattr(date_str, 'strftime'):
            date_str = date_str.strftime('%Y-%m-%d')
        
        cursor.execute('''
            INSERT INTO detailed_sessions 
            (student_id, session_type, date, sipara, page_tested,
             juzhali_page, jadeed_page, start_ayah, end_ayah,
             talqeen_count, tambeeh_count, core_mistake_type, specific_mistake,
             overall_grade, notes, data_format)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', [
            student_id,
            session_type,
            date_str,
            session_data.get('sipara'),
            session_data.get('page_tested'),
            session_data.get('juzhali_page'),
            session_data.get('jadeed_page'),
            session_data.get('start_ayah'),
            session_data.get('end_ayah'),
            session_data.get('talqeen_count', 0),
            session_data.get('tambeeh_count', 0),
            session_data.get('core_mistake_type'),
            session_data.get('specific_mistake'),
            session_data.get('overall_grade'),
            session_data.get('notes'),
            'session_entry'
        ])
        
        conn.commit()
        print(f"✅ DEBUG: Saved {session_type} session for student {student_id}")
        return True
        
    except Exception as e:
        print(f"❌ ERROR saving session: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def export_student_to_excel(student_id):
    """Export student data to Excel file"""
    try:
        conn = get_db_connection()
        
        # Get all data
        jadeed_df, juzhali_df, murajaat_df = get_student_data(student_id)
        
        # Create Excel file
        output_path = f"student_{student_id}_export.xlsx"
        
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            if not jadeed_df.empty:
                jadeed_df.to_excel(writer, sheet_name='JADEED', index=False)
            if not juzhali_df.empty:
                juzhali_df.to_excel(writer, sheet_name='JUZHALI', index=False)
            if not murajaat_df.empty:
                murajaat_df.to_excel(writer, sheet_name='MURAJAAT', index=False)
        
        conn.close()
        return output_path
    except Exception as e:
        print(f"Error exporting: {e}")
        return None

def convert_df_for_dashboard(jadeed_df, juzhali_df, murajaat_df):
    """Convert data for dashboard (already done in Part 2)"""
    all_data = pd.concat([jadeed_df, juzhali_df, murajaat_df], ignore_index=True)
    return all_data if not all_data.empty else pd.DataFrame()

def get_data_format_info(student_id):
    """Get info about what data formats exist for a student"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Count uploaded sessions
        cursor.execute('SELECT COUNT(*) FROM uploaded_sessions WHERE student_id = ?', [student_id])
        uploaded_count = cursor.fetchone()[0]
        
        # Count detailed sessions
        cursor.execute('SELECT COUNT(*) FROM detailed_sessions WHERE student_id = ?', [student_id])
        detailed_count = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            'has_uploaded': uploaded_count > 0,
            'has_detailed': detailed_count > 0,
            'uploaded_count': uploaded_count,
            'detailed_count': detailed_count
        }
    except Exception as e:
        print(f"❌ ERROR in get_data_format_info(): {e}")
        return {
            'has_uploaded': False,
            'has_detailed': False,
            'uploaded_count': 0,
            'detailed_count': 0
        }

def get_last_jadeed_page(all_data_df):
    """Get the last Jadeed ENDING page from combined data - FIXED VERSION"""
    try:
        if all_data_df is None or all_data_df.empty:
            return None
        
        # Handle both uppercase and lowercase column names
        session_col = 'Session_Type' if 'Session_Type' in all_data_df.columns else 'session_type'
        
        jadeed = all_data_df[all_data_df[session_col].str.lower() == 'jadeed'].copy()
        if jadeed.empty:
            return None
        
        # ✅ CRITICAL FIX: Sort by BOTH date AND id to get the truly latest entry
        jadeed['Date'] = pd.to_datetime(jadeed['Date'])
        
        # If 'id' column exists, use it for tie-breaking same-date entries
        if 'id' in jadeed.columns:
            jadeed = jadeed.sort_values(['Date', 'id'], ascending=[False, False])
        else:
            # Fallback: just sort by date
            jadeed = jadeed.sort_values('Date', ascending=False)
        
        latest = jadeed.iloc[0]
        
        print(f"🔍 DEBUG get_last_jadeed_page: Selected row with id={latest.get('id')}, date={latest.get('Date')}")
        print(f"🔍 DEBUG: jadeed_page value = {latest.get('jadeed_page')}")
        print(f"🔍 DEBUG: page_tested value = {latest.get('page_tested')}")
        
        # ✅ PRIORITY: Return the ENDING page (jadeed_page), NOT the starting page (page_tested)
        if 'jadeed_page' in latest.index and pd.notna(latest['jadeed_page']):
            result = int(latest['jadeed_page'])
            print(f"✅ DEBUG: Returning jadeed_page = {result}")
            return result
        elif 'Jadeed_Page' in latest.index and pd.notna(latest['Jadeed_Page']):
            result = int(latest['Jadeed_Page'])
            print(f"✅ DEBUG: Returning Jadeed_Page = {result}")
            return result
        elif 'Page' in latest.index and pd.notna(latest['Page']):
            result = int(latest['Page'])
            print(f"✅ DEBUG: Returning Page = {result}")
            return result
        
        # ⚠️ FALLBACK ONLY
        elif 'page_tested' in latest.index and pd.notna(latest['page_tested']):
            result = int(latest['page_tested'])
            print(f"⚠️ WARNING: Using page_tested as fallback = {result}")
            return result
        
        print("❌ DEBUG: No valid page column found!")
        return None
    except Exception as e:
        print(f"❌ ERROR in get_last_jadeed_page(): {e}")
        import traceback
        traceback.print_exc()
        return None