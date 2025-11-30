import os
import pandas as pd
from sqlalchemy import create_engine, text
import psycopg2
import hashlib
import secrets

def get_db_connection():
    """Get PostgreSQL database connection - ENHANCED DEBUG"""
    try:
        database_url = os.environ.get('DATABASE_URL')
        
        if not database_url:
            print("❌ DEBUG: No DATABASE_URL environment variable found")
            return None
            
        print(f"🔧 DEBUG: DATABASE_URL found: {database_url[:50]}...")
        
        if database_url.startswith("postgres://"):
            database_url = database_url.replace("postgres://", "postgresql://", 1)
            print("🔧 DEBUG: Fixed database URL format")
        
        engine = create_engine(database_url)
        conn = engine.connect()
        
        # Test the connection
        result = conn.execute(text("SELECT 1 as test"))
        test_result = result.fetchone()
        print(f"✅ DEBUG: Database connection test successful: {test_result['test']}")
        
        return conn
    except Exception as e:
        print(f"❌ DEBUG: PostgreSQL connection failed: {e}")
        return None

def init_postgres_db():
    """Initialize PostgreSQL database tables - ENHANCED DEBUG"""
    try:
        print("🔧 DEBUG: Starting database initialization...")
        conn = get_db_connection()
        if not conn:
            print("❌ DEBUG: No database connection for initialization")
            return False
        
        # Check if users table exists
        result = conn.execute(text("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'users'
            );
        """))
        users_table_exists = result.fetchone()[0]
        print(f"🔧 DEBUG: Users table exists: {users_table_exists}")
        
        # Create users table if it doesn't exist
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
        
        # Check current user count
        result = conn.execute(text("SELECT COUNT(*) as count FROM users"))
        user_count = result.fetchone()['count']
        print(f"🔧 DEBUG: Current users in database: {user_count}")
        
        conn.commit()
        conn.close()
        print("✅ DEBUG: Database initialization completed successfully")
        return True
        
    except Exception as e:
        print(f"❌ DEBUG: PostgreSQL init failed: {e}")
        return False

def hash_password(password):
    """Hash a password for storing - ENHANCED DEBUG"""
    try:
        print(f"🔧 DEBUG: Hashing password (length: {len(password)})")
        salt = secrets.token_hex(16)
        print(f"🔧 DEBUG: Generated salt: {salt}")
        
        password_hash = hashlib.sha256((salt + password).encode()).hexdigest()
        result = f"{salt}${password_hash}"
        
        print(f"🔧 DEBUG: Final hash: {result[:30]}...")
        return result
    except Exception as e:
        print(f"❌ DEBUG: Error hashing password: {e}")
        return None

def verify_password(stored_password, provided_password):
    """Verify a stored password against one provided by user - ENHANCED DEBUG"""
    try:
        print(f"🔧 DEBUG: Starting password verification")
        print(f"🔧 DEBUG: Stored password length: {len(stored_password) if stored_password else 'None'}")
        print(f"🔧 DEBUG: Provided password length: {len(provided_password) if provided_password else 'None'}")
        
        if not stored_password:
            print("❌ DEBUG: No stored password provided")
            return False
            
        if not provided_password:
            print("❌ DEBUG: No provided password")
            return False
            
        if '$' not in stored_password:
            print(f"❌ DEBUG: Invalid stored password format (no $ found): {stored_password[:50]}...")
            return False
            
        parts = stored_password.split('$')
        if len(parts) != 2:
            print(f"❌ DEBUG: Invalid stored password format (wrong parts): {parts}")
            return False
            
        salt, stored_hash = parts
        print(f"🔧 DEBUG: Salt extracted: {salt}")
        print(f"🔧 DEBUG: Stored hash: {stored_hash[:20]}...")
        
        # Recompute the hash with the provided password
        computed_hash = hashlib.sha256((salt + provided_password).encode()).hexdigest()
        print(f"🔧 DEBUG: Computed hash: {computed_hash[:20]}...")
        
        # Compare
        match = secrets.compare_digest(stored_hash, computed_hash)
        print(f"🔧 DEBUG: Password match result: {match}")
        
        return match
    except Exception as e:
        print(f"❌ DEBUG: Error in verify_password: {e}")
        return False

def create_user(username, email, password, full_name="", user_type="teacher"):
    """Create a new user - ENHANCED DEBUG"""
    try:
        print(f"🔧 DEBUG: Creating user: username='{username}', email='{email}', full_name='{full_name}'")
        
        conn = get_db_connection()
        if not conn:
            print("❌ DEBUG: No database connection for user creation")
            return False
        
        # Check if user already exists
        print(f"🔧 DEBUG: Checking if user '{username}' already exists...")
        result = conn.execute(text("SELECT id, username FROM users WHERE username = :username OR email = :email"), {
            'username': username, 'email': email
        })
        existing_user = result.fetchone()
        
        if existing_user:
            print(f"❌ DEBUG: User already exists - ID: {existing_user['id']}, Username: {existing_user['username']}")
            conn.close()
            return False
        else:
            print("✅ DEBUG: No existing user found, proceeding with creation")
        
        # Hash password
        password_hash = hash_password(password)
        if not password_hash:
            print("❌ DEBUG: Failed to hash password")
            conn.close()
            return False
        
        # Insert new user
        print("🔧 DEBUG: Inserting new user into database...")
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
        
        # Verify the user was created
        result = conn.execute(text("SELECT id FROM users WHERE username = :username"), {
            'username': username
        })
        new_user = result.fetchone()
        
        if new_user:
            print(f"✅ DEBUG: User created successfully! New user ID: {new_user['id']}")
        else:
            print("❌ DEBUG: User creation failed - no ID returned")
            
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ DEBUG: Error creating user: {e}")
        import traceback
        traceback.print_exc()
        return False

def authenticate_user(username, password):
    """Authenticate a user - ENHANCED DEBUG"""
    try:
        print(f"🔧 DEBUG: Starting authentication for user: '{username}'")
        
        conn = get_db_connection()
        if not conn:
            print("❌ DEBUG: No database connection for authentication")
            return None
            
        print(f"🔧 DEBUG: Querying database for user '{username}'...")
        result = conn.execute(text("""
            SELECT id, username, email, password_hash, full_name, user_type 
            FROM users WHERE username = :username
        """), {'username': username})
        
        user = result.fetchone()
        conn.close()
        
        if user:
            print(f"✅ DEBUG: User found in database - ID: {user['id']}, Username: {user['username']}")
            print(f"🔧 DEBUG: Stored password hash: {user['password_hash'][:30]}...")
            
            password_match = verify_password(user['password_hash'], password)
            
            if password_match:
                user_dict = {
                    'id': user['id'],
                    'username': user['username'],
                    'email': user['email'],
                    'full_name': user['full_name'],
                    'user_type': user['user_type']
                }
                print(f"🎉 DEBUG: AUTHENTICATION SUCCESSFUL for user: {user_dict}")
                return user_dict
            else:
                print("❌ DEBUG: PASSWORD VERIFICATION FAILED")
                return None
        else:
            print(f"❌ DEBUG: No user found with username: '{username}'")
            return None
            
    except Exception as e:
        print(f"❌ DEBUG: Error in authenticate_user: {e}")
        import traceback
        traceback.print_exc()
        return None

def create_default_admin():
    """Create default admin account if none exists"""
    try:
        print("🔧 DEBUG: Checking for default admin account...")
        conn = get_db_connection()
        if not conn:
            return
            
        result = conn.execute(text("SELECT COUNT(*) as count FROM users"))
        count = result.fetchone()['count']
        conn.close()
        
        print(f"🔧 DEBUG: Total users in database: {count}")
        
        if count == 0:
            print("🔧 DEBUG: No users found, creating default admin...")
            success = create_user("admin", "admin@hifztracker.com", "admin123", "System Administrator", "teacher")
            if success:
                print("✅ DEBUG: Default admin account created: admin / admin123")
            else:
                print("❌ DEBUG: Failed to create default admin account")
        else:
            print(f"✅ DEBUG: Database already has {count} user(s), skipping default admin creation")
    except Exception as e:
        print(f"❌ DEBUG: Error creating default admin: {e}")
