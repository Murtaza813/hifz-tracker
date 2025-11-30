import os
import pandas as pd
from sqlalchemy import create_engine, text
import psycopg2
import hashlib
import secrets

def get_db_connection():
    """Get PostgreSQL database connection - STREAMLIT DEBUG VERSION"""
    import streamlit as st
    
    try:
        st.sidebar.write("🔧 DATABASE DEBUG: Starting connection...")
        
        # Show all relevant environment variables
        database_url = os.environ.get('DATABASE_URL')
        st.sidebar.write(f"🔧 DATABASE_URL exists: {bool(database_url)}")
        
        if not database_url:
            st.sidebar.error("❌ DATABASE_URL not found in environment!")
            st.sidebar.write("🔧 Checking common alternative names...")
            
            # Check common alternative names
            alternatives = ['POSTGRES_URL', 'RAILWAY_DATABASE_URL', 'POSTGRESQL_URL', 'DB_URL']
            for alt in alternatives:
                alt_url = os.environ.get(alt)
                st.sidebar.write(f"🔧 {alt}: {bool(alt_url)}")
                if alt_url:
                    database_url = alt_url
                    st.sidebar.success(f"✅ Found in {alt}!")
                    break
            
            if not database_url:
                st.sidebar.error("❌ No database URL found in any environment variable!")
                return None
        
        st.sidebar.write(f"🔧 URL starts with: {database_url[:20]}..." if database_url else "No URL")
        
        # Fix common URL format issues
        if database_url.startswith("postgres://"):
            database_url = database_url.replace("postgres://", "postgresql://", 1)
            st.sidebar.write("🔧 Converted postgres:// to postgresql://")
        
        st.sidebar.write("🔧 Creating database engine...")
        engine = create_engine(database_url)
        
        st.sidebar.write("🔧 Attempting connection...")
        conn = engine.connect()
        
        st.sidebar.success("✅ Database connection successful!")
        return conn
        
    except Exception as e:
        st.sidebar.error(f"❌ Database connection failed: {str(e)}")
        return None

def init_postgres_db():
    """Initialize PostgreSQL database tables - SAFE"""
    try:
        conn = get_db_connection()
        if not conn:
            return False
            
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
        
        conn.commit()
        conn.close()
        print("✅ PostgreSQL database initialized!")
        return True
        
    except Exception as e:
        print(f"❌ PostgreSQL init failed: {e}")
        return False

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
        if not conn:
            return False
            
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
        if not conn:
            return None
            
        result = conn.execute(text("""
            SELECT id, username, email, password_hash, full_name, user_type 
            FROM users WHERE username = :username
        """), {'username': username})
        
        user = result.fetchone()
        conn.close()
        
        if user and verify_password(user['password_hash'], password):
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

def create_default_admin():
    """Create default admin account if none exists"""
    try:
        conn = get_db_connection()
        if not conn:
            return
            
        result = conn.execute(text("SELECT COUNT(*) as count FROM users"))
        count = result.fetchone()['count']
        conn.close()
        
        if count == 0:
            create_user("admin", "admin@hifztracker.com", "admin123", "System Administrator", "teacher")
            print("Default admin account created: admin / admin123")
    except Exception as e:
        print(f"Error creating default admin: {e}")
