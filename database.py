import os
import pandas as pd
from sqlalchemy import create_engine, text
from datetime import datetime

def get_db_connection():
    """Get PostgreSQL database connection for Railway"""
    try:
        database_url = os.environ.get('DATABASE_URL')
        
        if not database_url:
            return None
            
        if database_url.startswith("postgres://"):
            database_url = database_url.replace("postgres://", "postgresql://", 1)
        
        engine = create_engine(database_url)
        return engine.connect()
    except Exception as e:
        print(f"Database connection error: {e}")
        return None

def init_db():
    """Initialize PostgreSQL database tables"""
    conn = get_db_connection()
    if not conn:
        return
        
    try:
        # Students table
        conn.execute(text('''
            CREATE TABLE IF NOT EXISTS students (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) UNIQUE NOT NULL,
                teacher_name VARCHAR(255),
                start_date DATE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        '''))
        
        # Uploaded sessions table (old format)
        conn.execute(text('''
            CREATE TABLE IF NOT EXISTS uploaded_sessions (
                id SERIAL PRIMARY KEY,
                student_id INTEGER NOT NULL,
                session_type VARCHAR(50) NOT NULL,
                date DATE NOT NULL,
                sipara INTEGER,
                page_count INTEGER,
                jadeed_page INTEGER,
                ending_ayah INTEGER,
                starting_ayah INTEGER,
                overall_grade VARCHAR(100),
                notes TEXT,
                data_format VARCHAR(50) DEFAULT 'upload',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (student_id) REFERENCES students(id)
            )
        '''))
        
        # Detailed sessions table (new format)
        conn.execute(text('''
            CREATE TABLE IF NOT EXISTS detailed_sessions (
                id SERIAL PRIMARY KEY,
                student_id INTEGER NOT NULL,
                session_type VARCHAR(50) NOT NULL,
                date DATE NOT NULL,
                sipara INTEGER,
                page_tested INTEGER,
                juzhali_page INTEGER,
                jadeed_page INTEGER,
                start_ayah INTEGER,
                end_ayah INTEGER,
                talqeen_count INTEGER DEFAULT 0,
                tambeeh_count INTEGER DEFAULT 0,
                core_mistake_type VARCHAR(100),
                specific_mistake TEXT,
                overall_grade VARCHAR(100),
                notes TEXT,
                data_format VARCHAR(50) DEFAULT 'session_entry',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (student_id) REFERENCES students(id)
            )
        '''))
        
        conn.commit()
        
    except Exception as e:
        print(f"Error initializing database: {e}")
    finally:
        conn.close()

# ===== Save to uploaded_sessions =====
def save_to_uploaded_sessions(student_id, parsed_data):
    """Save old format data to uploaded_sessions table"""
    conn = get_db_connection()
    if not conn:
        return False
    
    try:
        for session_type in ['murajaat', 'juzhali', 'jadeed']:
            df = parsed_data[session_type]
            
            if df.empty:
                continue
            
            for idx, row in df.iterrows():
                date_val = pd.Timestamp(row.get('date')).strftime('%Y-%m-%d')
                
                conn.execute(text('''
                    INSERT INTO uploaded_sessions 
                    (student_id, session_type, date, sipara, page_count,
                     jadeed_page, ending_ayah, overall_grade, notes, data_format)
                    VALUES (:student_id, :session_type, :date, :sipara, :page_count,
                            :jadeed_page, :ending_ayah, :overall_grade, :notes, :data_format)
                '''), {
                    'student_id': student_id,
                    'session_type': row.get('session_type'),
                    'date': date_val,
                    'sipara': row.get('sipara') if pd.notna(row.get('sipara')) else None,
                    'page_count': row.get('page_count') if pd.notna(row.get('page_count')) else None,
                    'jadeed_page': row.get('jadeed_page') if pd.notna(row.get('jadeed_page')) else None,
                    'ending_ayah': row.get('ending_ayah') if pd.notna(row.get('ending_ayah')) else None,
                    'overall_grade': row.get('overall_grade'),
                    'notes': row.get('notes'),
                    'data_format': 'upload'
                })
        
        conn.commit()
        return True
    
    except Exception as e:
        print(f"Error saving to uploaded_sessions: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

# ===== Save to detailed_sessions =====
def save_to_detailed_sessions(student_id, parsed_data):
    """Save new format data to detailed_sessions table"""
    conn = get_db_connection()
    if not conn:
        return False
    
    try:
        for session_type in ['murajaat', 'juzhali', 'jadeed']:
            df = parsed_data[session_type]
            
            if df.empty:
                continue
            
            for _, row in df.iterrows():
                date_val = pd.Timestamp(row.get('date')).strftime('%Y-%m-%d')
                
                conn.execute(text('''
                    INSERT INTO detailed_sessions 
                    (student_id, session_type, date, sipara, page_tested,
                     juzhali_page, jadeed_page, start_ayah, end_ayah,
                     talqeen_count, tambeeh_count, overall_grade, notes, data_format)
                    VALUES (:student_id, :session_type, :date, :sipara, :page_tested,
                            :juzhali_page, :jadeed_page, :start_ayah, :end_ayah,
                            :talqeen_count, :tambeeh_count, :overall_grade, :notes, :data_format)
                '''), {
                    'student_id': student_id,
                    'session_type': row.get('session_type'),
                    'date': date_val,
                    'sipara': row.get('sipara') if pd.notna(row.get('sipara')) else None,
                    'page_tested': row.get('page_tested') if pd.notna(row.get('page_tested')) else None,
                    'juzhali_page': row.get('juzhali_page') if pd.notna(row.get('juzhali_page')) else None,
                    'jadeed_page': row.get('jadeed_page') if pd.notna(row.get('jadeed_page')) else None,
                    'start_ayah': row.get('start_ayah') if pd.notna(row.get('start_ayah')) else None,
                    'end_ayah': row.get('end_ayah') if pd.notna(row.get('end_ayah')) else None,
                    'talqeen_count': row.get('talqeen_count') if pd.notna(row.get('talqeen_count')) else 0,
                    'tambeeh_count': row.get('tambeeh_count') if pd.notna(row.get('tambeeh_count')) else 0,
                    'overall_grade': row.get('overall_grade'),
                    'notes': row.get('notes'),
                    'data_format': 'session_entry'
                })
        
        conn.commit()
        return True
    
    except Exception as e:
        print(f"Error saving to detailed_sessions: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

# ===== Save student from Excel =====
def save_student_from_excel(parsed_data):
    """Save student and all sessions based on detected format"""
    if 'error' in parsed_data and parsed_data['error']:
        return None
    
    data_format = parsed_data['format']
    student_info = parsed_data['student_info']
    
    try:
        # Get student info
        student_name = student_info['Student_Name'].iloc[0]
        teacher_name = student_info['Teacher_Name'].iloc[0] if 'Teacher_Name' in student_info else 'Unknown'

        if 'Start_Date' in student_info and pd.notna(student_info['Start_Date'].iloc[0]):
            start_date = pd.to_datetime(student_info['Start_Date'].iloc[0]).strftime('%Y-%m-%d')
        else:
            start_date = None
        
        conn = get_db_connection()
        if not conn:
            return None
        
        # Check if student exists
        result = conn.execute(text('SELECT id FROM students WHERE name = :name'), {'name': student_name})
        existing_student = result.fetchone()
        
        if existing_student:
            student_id = existing_student['id']
        else:
            # Insert new student
            result = conn.execute(text('''
                INSERT INTO students (name, teacher_name, start_date)
                VALUES (:name, :teacher_name, :start_date)
                RETURNING id
            '''), {
                'name': student_name,
                'teacher_name': teacher_name,
                'start_date': start_date
            })
            student_id = result.fetchone()['id']
            conn.commit()
        
        conn.close()
        
        # Save sessions based on format
        if data_format == 'upload':
            success = save_to_uploaded_sessions(student_id, parsed_data)
        elif data_format == 'session_entry':
            success = save_to_detailed_sessions(student_id, parsed_data)
        else:
            return None
        
        return student_id if success else None
    
    except Exception as e:
        print(f"Error in save_student_from_excel: {e}")
        return None

# ===== Get all student sessions =====
def get_all_student_sessions(student_id):
    """Get all sessions from both tables"""
    try:
        conn = get_db_connection()
        if not conn:
            return pd.DataFrame()
        
        # Fetch from uploaded_sessions
        uploaded = pd.read_sql(text('''
            SELECT * FROM uploaded_sessions 
            WHERE student_id = :student_id
        '''), conn, params={'student_id': student_id})
        
        # Fetch from detailed_sessions
        detailed = pd.read_sql(text('''
            SELECT * FROM detailed_sessions 
            WHERE student_id = :student_id
        '''), conn, params={'student_id': student_id})
        
        conn.close()
        
        # If both empty
        if uploaded.empty and detailed.empty:
            return pd.DataFrame()
        
        # Standardize columns
        def standardize_columns(df, source_type):
            if df.empty:
                return df
            df = df.copy()
            df['Data_Source'] = source_type
            
            column_mappings = [
                ('session_type', 'Session_Type'),
                ('date', 'Date'),
                ('sipara', 'Sipara'),
                ('page_tested', 'Page'),
                ('page_count', 'Page'),
                ('juzhali_page', 'Page'),
                ('jadeed_page', 'Jadeed_Page'),
                ('start_ayah', 'Starting_Ayah'),
                ('end_ayah', 'Ending_Ayah'),
                ('ending_ayah', 'Ending_Ayah'),
                ('starting_ayah', 'Starting_Ayah'),
                ('talqeen_count', 'Mistake_Count'),
                ('tambeeh_count', 'Tambeeh_Count'),
                ('core_mistake_type', 'Core_Mistake'),
                ('specific_mistake', 'Specific_Mistake'),
                ('overall_grade', 'Overall_Grade'),
                ('notes', 'Notes'),
                ('data_format', 'Data_Format')
            ]
            
            for old_col, new_col in column_mappings:
                if old_col in df.columns and new_col not in df.columns:
                    df[new_col] = df[old_col]
            
            return df
        
        uploaded_std = standardize_columns(uploaded, 'uploaded')
        detailed_std = standardize_columns(detailed, 'detailed')
        
        # Combine dataframes
        if uploaded_std.empty:
            combined_data = detailed_std
        elif detailed_std.empty:
            combined_data = uploaded_std
        else:
            all_columns = set(uploaded_std.columns) | set(detailed_std.columns)
            for col in all_columns:
                if col not in uploaded_std.columns:
                    uploaded_std[col] = None
                if col not in detailed_std.columns:
                    detailed_std[col] = None
            combined_data = pd.concat([uploaded_std, detailed_std], ignore_index=True, sort=False)
        
        # Ensure Session_Type column
        if not combined_data.empty and 'Session_Type' not in combined_data.columns:
            for col in combined_data.columns:
                if 'session' in col.lower() and 'type' in col.lower():
                    combined_data['Session_Type'] = combined_data[col]
                    break
        
        # Sort by date
        if 'Date' in combined_data.columns:
            combined_data['Date'] = pd.to_datetime(combined_data['Date'], errors='coerce')
            combined_data = combined_data.sort_values('Date', ascending=False)
        
        return combined_data
    
    except Exception as e:
        print(f"Error in get_all_student_sessions: {e}")
        return pd.DataFrame()

# ===== Other functions =====
def get_all_students():
    """Get all students from database"""
    try:
        conn = get_db_connection()
        if not conn:
            return {}
        
        students = pd.read_sql(text('SELECT id, name FROM students ORDER BY name'), conn)
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
        if not conn:
            return False
        
        result = conn.execute(text('SELECT id FROM students WHERE name = :name'), {'name': name})
        exists = result.fetchone() is not None
        conn.close()
        return exists
    except:
        return False

def append_new_session(student_id, session_type, session_data):
    """Add a new session to detailed_sessions table"""
    conn = get_db_connection()
    if not conn:
        return False
    
    try:
        date_str = session_data['date']
        if hasattr(date_str, 'strftime'):
            date_str = date_str.strftime('%Y-%m-%d')
        
        conn.execute(text('''
            INSERT INTO detailed_sessions 
            (student_id, session_type, date, sipara, page_tested,
             juzhali_page, jadeed_page, start_ayah, end_ayah,
             talqeen_count, tambeeh_count, core_mistake_type, specific_mistake,
             overall_grade, notes, data_format)
            VALUES (:student_id, :session_type, :date, :sipara, :page_tested,
                    :juzhali_page, :jadeed_page, :start_ayah, :end_ayah,
                    :talqeen_count, :tambeeh_count, :core_mistake_type, :specific_mistake,
                    :overall_grade, :notes, :data_format)
        '''), {
            'student_id': student_id,
            'session_type': session_type,
            'date': date_str,
            'sipara': session_data.get('sipara'),
            'page_tested': session_data.get('page_tested'),
            'juzhali_page': session_data.get('juzhali_page'),
            'jadeed_page': session_data.get('jadeed_page'),
            'start_ayah': session_data.get('start_ayah'),
            'end_ayah': session_data.get('end_ayah'),
            'talqeen_count': session_data.get('talqeen_count', 0),
            'tambeeh_count': session_data.get('tambeeh_count', 0),
            'core_mistake_type': session_data.get('core_mistake_type'),
            'specific_mistake': session_data.get('specific_mistake'),
            'overall_grade': session_data.get('overall_grade'),
            'notes': session_data.get('notes'),
            'data_format': 'session_entry'
        })
        
        conn.commit()
        return True
        
    except Exception as e:
        print(f"Error saving session: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def export_student_to_excel(student_id):
    """Export student data to Excel file"""
    try:
        jadeed_df, juzhali_df, murajaat_df = get_student_data(student_id)
        
        output_path = f"student_{student_id}_export.xlsx"
        
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            if not jadeed_df.empty:
                jadeed_df.to_excel(writer, sheet_name='JADEED', index=False)
            if not juzhali_df.empty:
                juzhali_df.to_excel(writer, sheet_name='JUZHALI', index=False)
            if not murajaat_df.empty:
                murajaat_df.to_excel(writer, sheet_name='MURAJAAT', index=False)
        
        return output_path
    except Exception as e:
        print(f"Error exporting: {e}")
        return None

def get_data_format_info(student_id):
    """Get info about what data formats exist for a student"""
    try:
        conn = get_db_connection()
        if not conn:
            return {'has_uploaded': False, 'has_detailed': False, 'uploaded_count': 0, 'detailed_count': 0}
        
        # Count uploaded sessions
        result = conn.execute(text('SELECT COUNT(*) as count FROM uploaded_sessions WHERE student_id = :student_id'), 
                            {'student_id': student_id})
        uploaded_count = result.fetchone()['count']
        
        # Count detailed sessions
        result = conn.execute(text('SELECT COUNT(*) as count FROM detailed_sessions WHERE student_id = :student_id'), 
                            {'student_id': student_id})
        detailed_count = result.fetchone()['count']
        
        conn.close()
        
        return {
            'has_uploaded': uploaded_count > 0,
            'has_detailed': detailed_count > 0,
            'uploaded_count': uploaded_count,
            'detailed_count': detailed_count
        }
    except Exception as e:
        return {
            'has_uploaded': False,
            'has_detailed': False,
            'uploaded_count': 0,
            'detailed_count': 0
        }

def get_last_jadeed_page(all_data_df):
    """Get the last Jadeed ENDING page from combined data"""
    try:
        if all_data_df is None or all_data_df.empty:
            return None
        
        session_col = 'Session_Type' if 'Session_Type' in all_data_df.columns else 'session_type'
        
        jadeed = all_data_df[all_data_df[session_col].str.lower() == 'jadeed'].copy()
        if jadeed.empty:
            return None
        
        jadeed['Date'] = pd.to_datetime(jadeed['Date'])
        
        if 'id' in jadeed.columns:
            jadeed = jadeed.sort_values(['Date', 'id'], ascending=[False, False])
        else:
            jadeed = jadeed.sort_values('Date', ascending=False)
        
        latest = jadeed.iloc[0]
        
        if 'jadeed_page' in latest.index and pd.notna(latest['jadeed_page']):
            return int(latest['jadeed_page'])
        elif 'Jadeed_Page' in latest.index and pd.notna(latest['Jadeed_Page']):
            return int(latest['Jadeed_Page'])
        elif 'Page' in latest.index and pd.notna(latest['Page']):
            return int(latest['Page'])
        elif 'page_tested' in latest.index and pd.notna(latest['page_tested']):
            return int(latest['page_tested'])
        
        return None
    except Exception as e:
        print(f"Error in get_last_jadeed_page: {e}")
        return None
