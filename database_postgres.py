import os
import pandas as pd
from sqlalchemy import create_engine, text
import psycopg2
import hashlib
import secrets

def get_db_connection():
    """Get PostgreSQL database connection - PRODUCTION VERSION"""
    try:
        database_url = os.environ.get('DATABASE_URL')
        
        if not database_url:
            print("❌ DEBUG: No DATABASE_URL found")
            return None
            
        if database_url.startswith("postgres://"):
            database_url = database_url.replace("postgres://", "postgresql://", 1)
        
        engine = create_engine(database_url)
        conn = engine.connect()
        print("✅ DEBUG: Database connection successful")
        return conn
    except Exception as e:
        print(f"❌ DEBUG: PostgreSQL connection failed: {e}")
        return None

def init_postgres_db():
    """Initialize PostgreSQL database tables - PRODUCTION"""
    try:
        conn = get_db_connection()
        if not conn:
            return False
            
        print("✅ DEBUG: Initializing database tables...")
        
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
        print("✅ DEBUG: Database tables initialized successfully")
        return True
        
    except Exception as e:
        print(f"❌ DEBUG: PostgreSQL init failed: {e}")
        return False

def hash_password(password):
    """Hash a password for storing - IMPROVED VERSION"""
    try:
        print(f"🔧 DEBUG: Hashing password for user")
        salt = secrets.token_hex(16)
        password_hash = hashlib.sha256((salt + password).encode()).hexdigest()
        result = f"{salt}${password_hash}"
        print(f"🔧 DEBUG: Password hashed successfully")
        return result
    except Exception as e:
        print(f"❌ DEBUG: Error hashing password: {e}")
        return None

def verify_password(stored_password, provided_password):
    """Verify a stored password against one provided by user - IMPROVED VERSION"""
    try:
        print(f"🔧 DEBUG: Verifying password...")
        
        if not stored_password or not provided_password:
            print("❌ DEBUG: Missing password data")
            return False
            
        if '$' not in stored_password:
            print("❌ DEBUG: Invalid stored password format")
            return False
            
        salt, stored_hash = stored_password.split('$')
        print(f"🔧 DEBUG: Salt: {salt[:10]}..., Stored hash: {stored_hash[:10]}...")
        
        # Recompute the hash with the provided password
        computed_hash = hashlib.sha256((salt + provided_password).encode()).hexdigest()
        print(f"🔧 DEBUG: Computed hash: {computed_hash[:10]}...")
        
        # Use constant-time comparison to prevent timing attacks
        match = secrets.compare_digest(stored_hash, computed_hash)
        print(f"🔧 DEBUG: Password match: {match}")
        
        return match
    except Exception as e:
        print(f"❌ DEBUG: Error verifying password: {e}")
        return False

def create_user(username, email, password, full_name="", user_type="teacher"):
    """Create a new user - DEBUG VERSION"""
    try:
        print(f"🔧 DEBUG: Creating user: {username}, {email}")
        
        conn = get_db_connection()
        if not conn:
            print("❌ DEBUG: No database connection")
            return False
        
        # Check if user already exists
        result = conn.execute(text("SELECT id FROM users WHERE username = :username OR email = :email"), {
            'username': username, 'email': email
        })
        existing_user = result.fetchone()
        if existing_user:
            print(f"❌ DEBUG: User already exists with ID: {existing_user['id']}")
            conn.close()
            return False
        
        # Hash password
        password_hash = hash_password(password)
        if not password_hash:
            print("❌ DEBUG: Failed to hash password")
            conn.close()
            return False
        
        print(f"🔧 DEBUG: Password hash created: {password_hash[:50]}...")
        
        # Insert new user
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
        print("✅ DEBUG: User created successfully")
        return True
    except Exception as e:
        print(f"❌ DEBUG: Error creating user: {e}")
        return False

def authenticate_user(username, password):
    """Authenticate a user - DEBUG VERSION"""
    try:
        print(f"🔧 DEBUG: Authenticating user: {username}")
        
        conn = get_db_connection()
        if not conn:
            print("❌ DEBUG: No database connection for auth")
            return None
            
        result = conn.execute(text("""
            SELECT id, username, email, password_hash, full_name, user_type 
            FROM users WHERE username = :username
        """), {'username': username})
        
        user = result.fetchone()
        conn.close()
        
        print(f"🔧 DEBUG: Database returned user: {user is not None}")
        
        if user:
            print(f"🔧 DEBUG: User found - ID: {user['id']}, Username: {user['username']}")
            print(f"🔧 DEBUG: Stored hash: {user['password_hash'][:50]}...")
            
            password_match = verify_password(user['password_hash'], password)
            print(f"🔧 DEBUG: Password verification result: {password_match}")
            
            if password_match:
                user_dict = {
                    'id': user['id'],
                    'username': user['username'],
                    'email': user['email'],
                    'full_name': user['full_name'],
                    'user_type': user['user_type']
                }
                print(f"✅ DEBUG: Authentication successful for user: {user_dict}")
                return user_dict
            else:
                print("❌ DEBUG: Password verification failed")
        else:
            print("❌ DEBUG: No user found with that username")
            
        return None
    except Exception as e:
        print(f"❌ DEBUG: Error authenticating user: {e}")
        return None

def create_default_admin():
    """Create default admin account if none exists"""
    try:
        print("🔧 DEBUG: Checking for default admin...")
        conn = get_db_connection()
        if not conn:
            return
            
        result = conn.execute(text("SELECT COUNT(*) as count FROM users"))
        count = result.fetchone()['count']
        conn.close()
        
        print(f"🔧 DEBUG: Current user count: {count}")
        
        if count == 0:
            success = create_user("admin", "admin@hifztracker.com", "admin123", "System Administrator", "teacher")
            if success:
                print("✅ Default admin account created: admin / admin123")
            else:
                print("❌ Failed to create default admin account")
        else:
            print("✅ Users already exist, skipping default admin creation")
    except Exception as e:
        print(f"Error creating default admin: {e}")
