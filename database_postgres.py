# =========================================================================
# DATABASE POSTGRES - USER ACCOUNTS SYSTEM
# =========================================================================

import os
import pandas as pd
from sqlalchemy import create_engine, text
import psycopg2
import hashlib
import secrets

def get_db_connection():
    """Get PostgreSQL database connection"""
    database_url = os.environ.get('DATABASE_URL')
    
    if not database_url:
        raise ValueError("DATABASE_URL environment variable not set")
    
    # Fix for Render.com URL format
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)
    
    engine = create_engine(database_url)
    return engine.connect()

def init_postgres_db():
    """Initialize PostgreSQL database tables with user accounts"""
    try:
        conn = get_db_connection()
        
        # Create users table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username VARCHAR(100) UNIQUE NOT NULL,
                email VARCHAR(255) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                user_type VARCHAR(50) DEFAULT 'teacher',
                full_name VARCHAR(255),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP
            )
        """))
        
        # Create students table - LINKED TO USER
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS students (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL,
                student_id VARCHAR(100) NOT NULL,
                student_name VARCHAR(255) NOT NULL,
                teacher_name VARCHAR(255),
                start_date DATE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id),
                UNIQUE(user_id, student_id)
            )
        """))
        
        # Create sessions table - LINKED TO USER
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS sessions (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL,
                student_id VARCHAR(100) NOT NULL,
                date DATE NOT NULL,
                session_type VARCHAR(50) NOT NULL,
                sipara VARCHAR(10),
                page VARCHAR(20),
                page_range VARCHAR(50),
                mistake_count INTEGER DEFAULT 0,
                tambeeh_count INTEGER DEFAULT 0,
                core_mistake VARCHAR(100),
                specific_mistake TEXT,
                overall_grade VARCHAR(50),
                notes TEXT,
                data_format VARCHAR(50),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """))
        
        conn.commit()
        conn.close()
        print("PostgreSQL database with user accounts initialized!")
        
    except Exception as e:
        print(f"Error initializing PostgreSQL: {e}")

def hash_password(password):
    """Hash a password for storing"""
    salt = secrets.token_hex(16)
    return f"{salt}${hashlib.sha256((salt + password).encode()).hexdigest()}"

def verify_password(stored_password, provided_password):
    """Verify a stored password against one provided by user"""
    if not stored_password or '$' not in stored_password:
        return False
    salt, hash_value = stored_password.split('$')
    return hash_value == hashlib.sha256((salt + provided_password).encode()).hexdigest()

def create_user(username, email, password, full_name="", user_type="teacher"):
    """Create a new user"""
    try:
        conn = get_db_connection()
        
        password_hash = hash_password(password)
        
        conn.execute(text("""
            INSERT INTO users (username, email, password_hash, full_name, user_type)
            VALUES (:username, :email, :password_hash, :full_name, :user_type)
        """), {
            'username': username,
            'email': email,
            'password_hash': password_hash,
            'full_name': full_name,
            'user_type': user_type
        })
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Error creating user: {e}")
        return False

def authenticate_user(username, password):
    """Authenticate a user"""
    try:
        conn = get_db_connection()
        
        result = conn.execute(text("""
            SELECT id, username, email, password_hash, full_name, user_type 
            FROM users WHERE username = :username
        """), {'username': username})
        
        user = result.fetchone()
        conn.close()
        
        if user and verify_password(user['password_hash'], password):
            # Update last login
            conn = get_db_connection()
            conn.execute(text("""
                UPDATE users SET last_login = CURRENT_TIMESTAMP 
                WHERE id = :user_id
            """), {'user_id': user['id']})
            conn.commit()
            conn.close()
            
            return {
                'id': user['id'],
                'username': user['username'],
                'email': user['email'],
                'full_name': user['full_name'],
                'user_type': user['user_type']
            }
        return None
    except Exception as e:
        print(f"Error authenticating user: {e}")
        return None

def save_student_to_postgres(student_info, user_id):
    """Save student to PostgreSQL - USER ISOLATED"""
    try:
        conn = get_db_connection()
        
        conn.execute(text("""
            INSERT INTO students (user_id, student_id, student_name, teacher_name, start_date)
            VALUES (:user_id, :student_id, :student_name, :teacher_name, :start_date)
            ON CONFLICT (user_id, student_id) DO NOTHING
        """), {
            'user_id': user_id,
            'student_id': student_info['student_id'],
            'student_name': student_info['student_name'],
            'teacher_name': student_info.get('teacher_name'),
            'start_date': student_info.get('start_date')
        })
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Error saving student to PostgreSQL: {e}")
        return False

def get_all_students_postgres(user_id):
    """Get all students from PostgreSQL - ONLY CURRENT USER'S"""
    try:
        conn = get_db_connection()
        
        result = conn.execute(text("""
            SELECT student_id, student_name FROM students 
            WHERE user_id = :user_id
            ORDER BY student_name
        """), {'user_id': user_id})
        
        students = result.fetchall()
        conn.close()
        
        return {student['student_name']: student['student_id'] for student in students}
    except Exception as e:
        print(f"Error fetching students from PostgreSQL: {e}")
        return {}

def get_all_student_sessions_postgres(user_id, student_id):
    """Get all sessions for a student from PostgreSQL - ONLY CURRENT USER'S"""
    try:
        conn = get_db_connection()
        
        result = conn.execute(text("""
            SELECT * FROM sessions 
            WHERE user_id = :user_id AND student_id = :student_id
            ORDER BY date DESC
        """), {
            'user_id': user_id,
            'student_id': student_id
        })
        
        sessions = result.fetchall()
        conn.close()
        
        if sessions:
            df = pd.DataFrame([dict(session) for session in sessions])
            return df
        else:
            return pd.DataFrame()
            
    except Exception as e:
        print(f"Error fetching sessions from PostgreSQL: {e}")
        return pd.DataFrame()

def save_session_to_postgres(user_id, student_id, session_type, session_data):
    """Save session to PostgreSQL"""
    try:
        conn = get_db_connection()
        
        conn.execute(text("""
            INSERT INTO sessions (
                user_id, student_id, date, session_type, sipara, page, page_range,
                mistake_count, tambeeh_count, core_mistake, specific_mistake,
                overall_grade, notes, data_format
            ) VALUES (
                :user_id, :student_id, :date, :session_type, :sipara, :page, :page_range,
                :mistake_count, :tambeeh_count, :core_mistake, :specific_mistake,
                :overall_grade, :notes, :data_format
            )
        """), {
            'user_id': user_id,
            'student_id': student_id,
            'date': session_data.get('date'),
            'session_type': session_type,
            'sipara': session_data.get('sipara'),
            'page': session_data.get('page_tested'),
            'page_range': session_data.get('page_range'),
            'mistake_count': session_data.get('talqeen_count', 0),
            'tambeeh_count': session_data.get('tambeeh_count', 0),
            'core_mistake': session_data.get('core_mistake_type'),
            'specific_mistake': session_data.get('specific_mistake'),
            'overall_grade': session_data.get('overall_grade'),
            'notes': session_data.get('notes'),
            'data_format': 'session_entry'
        })
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Error saving session to PostgreSQL: {e}")
        return False

def create_default_admin():
    """Create default admin account if none exists"""
    try:
        conn = get_db_connection()
        result = conn.execute(text("SELECT COUNT(*) as count FROM users"))
        count = result.fetchone()['count']
        conn.close()
        
        if count == 0:
            create_user("admin", "admin@hifztracker.com", "admin123", "System Administrator", "teacher")
            print("Default admin account created: admin / admin123")
    except Exception as e:
        print(f"Error creating default admin: {e}")
