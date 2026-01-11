#!/usr/bin/env python3
"""
Test script to simulate SQLite migration scenario
"""

import os
import sys
import sqlite3
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Add the backend directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_sqlite_migration():
    """Test SQLite schema migration"""
    print("🧪 Testing SQLite schema migration...")
    
    # Create a test SQLite database with old schema
    db_path = "test_migration.db"
    if os.path.exists(db_path):
        os.remove(db_path)
    
    # Create old schema
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create old tables
    cursor.execute("""
        CREATE TABLE projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            prompts TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    cursor.execute("""
        CREATE TABLE recordings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            text TEXT,
            filename TEXT UNIQUE,
            recorded_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            project_id INTEGER
        )
    """)
    
    cursor.execute("""
        CREATE TABLE settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key TEXT UNIQUE NOT NULL,
            value TEXT
        )
    """)
    
    cursor.execute("""
        CREATE TABLE interactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            action TEXT,
            data TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Add some test data
    cursor.execute("""
        INSERT INTO projects (name, prompts) 
        VALUES ('Test Project', '["Hello", "World", "Test"]')
    """)
    
    cursor.execute("""
        INSERT INTO recordings (text, filename, project_id) 
        VALUES ('Hello', 'abc123.wav', 1)
    """)
    
    conn.commit()
    conn.close()
    
    print("✅ Created test database with old schema")
    
    # Now test the migration
    try:
        # Import main with SQLite fallback
        import main
        print("✅ Migration test completed successfully")
        
        # Verify the new schema
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if prompt_id column exists
        cursor.execute("PRAGMA table_info(recordings)")
        columns = [col[1] for col in cursor.fetchall()]
        if 'prompt_id' in columns:
            print("✅ prompt_id column added to recordings table")
        else:
            print("❌ prompt_id column not found")
        
        # Check if prompts table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='prompts'")
        if cursor.fetchone():
            print("✅ prompts table created")
        else:
            print("❌ prompts table not found")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Migration test failed: {e}")
    
    # Clean up
    if os.path.exists(db_path):
        os.remove(db_path)
        print("🧹 Cleaned up test database")

if __name__ == "__main__":
    test_sqlite_migration() 