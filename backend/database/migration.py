from sqlalchemy import text
from .connection import engine, SessionLocal
from .session import session_lock
from utils.logging import logger

def migrate_schema():
    """Handle schema migrations for existing databases"""
    with session_lock:
        db = SessionLocal()
        try:
            # Check if we're using SQLite
            if 'sqlite' in str(engine.url):
                print("🔄 Checking SQLite database schema...")
                
                # Check if prompt_id column exists in recordings table
                try:
                    db.execute(text("SELECT prompt_id FROM recordings LIMIT 1"))
                    print("✅ Recordings table schema is up to date")
                except Exception:
                    print("🔄 Migrating recordings table schema...")
                    
                    # Add prompt_id column to recordings table
                    try:
                        db.execute(text("ALTER TABLE recordings ADD COLUMN prompt_id INTEGER"))
                        print("✅ Added prompt_id column to recordings table")
                    except Exception as e:
                        print(f"⚠️  Could not add prompt_id column: {e}")
                
                # Check if is_rtl column exists in projects table
                try:
                    db.execute(text("SELECT is_rtl FROM projects LIMIT 1"))
                    print("✅ Projects table schema is up to date")
                except Exception:
                    print("🔄 Migrating projects table schema...")
                    
                    # Add is_rtl column to projects table
                    try:
                        db.execute(text("ALTER TABLE projects ADD COLUMN is_rtl INTEGER DEFAULT 0"))
                        print("✅ Added is_rtl column to projects table")
                    except Exception as e:
                        print(f"⚠️  Could not add is_rtl column: {e}")
                    
                    # Check if prompts table exists
                    try:
                        db.execute(text("SELECT COUNT(*) FROM prompts"))
                        print("✅ Prompts table exists")
                    except Exception:
                        print("🔄 Creating prompts table...")
                        # Create prompts table manually for SQLite
                        db.execute(text("""
                            CREATE TABLE prompts (
                                id INTEGER PRIMARY KEY AUTOINCREMENT,
                                project_id INTEGER NOT NULL,
                                text TEXT NOT NULL,
                                order_index INTEGER NOT NULL,
                                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                            )
                        """))
                        print("✅ Created prompts table")
                    
                    db.commit()
                    print("✅ Schema migration completed")
            
            # For MySQL, check and add missing columns
            else:
                print("🔄 Checking MySQL database schema...")
                
                # Check if prompt_id column exists in recordings table
                try:
                    db.execute(text("SELECT prompt_id FROM recordings LIMIT 1"))
                    print("✅ Recordings table schema is up to date")
                except Exception:
                    print("🔄 Migrating recordings table schema...")
                    
                    # Add prompt_id column to recordings table
                    try:
                        db.execute(text("ALTER TABLE recordings ADD COLUMN prompt_id INT"))
                        print("✅ Added prompt_id column to recordings table")
                    except Exception as e:
                        print(f"⚠️  Could not add prompt_id column: {e}")
                
                # Check if is_rtl column exists in projects table
                try:
                    db.execute(text("SELECT is_rtl FROM projects LIMIT 1"))
                    print("✅ Projects table schema is up to date")
                except Exception:
                    print("🔄 Migrating projects table schema...")
                    
                    # Add is_rtl column to projects table
                    try:
                        db.execute(text("ALTER TABLE projects ADD COLUMN is_rtl INT DEFAULT 0"))
                        print("✅ Added is_rtl column to projects table")
                    except Exception as e:
                        print(f"⚠️  Could not add is_rtl column: {e}")
                    
                    # Check if prompts table exists
                    try:
                        db.execute(text("SELECT COUNT(*) FROM prompts"))
                        print("✅ Prompts table exists")
                    except Exception:
                        print("🔄 Creating prompts table...")
                        # Create prompts table manually for MySQL
                        db.execute(text("""
                            CREATE TABLE prompts (
                                id INT AUTO_INCREMENT PRIMARY KEY,
                                project_id INT NOT NULL,
                                text TEXT NOT NULL,
                                order_index INT NOT NULL,
                                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                            )
                        """))
                        print("✅ Created prompts table")
                    
                    db.commit()
                    print("✅ Schema migration completed")
                
        except Exception as e:
            print(f"⚠️  Schema migration check failed: {e}")
        finally:
            db.close() 