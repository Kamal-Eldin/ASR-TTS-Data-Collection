#!/usr/bin/env python3
"""
Migration script to transfer data from SQLite to MySQL
Run this script if you have existing data in SQLite that you want to migrate to MySQL
"""

import os
import sys
import sqlite3
import pymysql
import json
from datetime import datetime

# Add the backend directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import DatabaseConfig

def connect_sqlite():
    """Connect to SQLite database"""
    try:
        return sqlite3.connect('tts_dataset.db')
    except sqlite3.Error as e:
        print(f"❌ Error connecting to SQLite: {e}")
        return None

def connect_mysql():
    """Connect to MySQL database"""
    try:
        return pymysql.connect(
            host=DatabaseConfig.MYSQL_HOST,
            port=DatabaseConfig.MYSQL_PORT,
            user=DatabaseConfig.MYSQL_USER,
            password=DatabaseConfig.MYSQL_PASSWORD,
            database=DatabaseConfig.MYSQL_DATABASE,
            charset='utf8mb4'
        )
    except pymysql.Error as e:
        print(f"❌ Error connecting to MySQL: {e}")
        return None

def migrate_data():
    """Migrate data from SQLite to MySQL"""
    sqlite_conn = connect_sqlite()
    mysql_conn = connect_mysql()
    
    if not sqlite_conn or not mysql_conn:
        return False
    
    try:
        sqlite_cursor = sqlite_conn.cursor()
        mysql_cursor = mysql_conn.cursor()
        
        print("🔄 Starting migration from SQLite to MySQL...")
        
        # Migrate settings
        print("📝 Migrating settings...")
        sqlite_cursor.execute("SELECT key, value FROM settings")
        settings = sqlite_cursor.fetchall()
        
        for key, value in settings:
            mysql_cursor.execute(
                "INSERT INTO settings (key, value) VALUES (%s, %s) ON DUPLICATE KEY UPDATE value = VALUES(value)",
                (key, value)
            )
        print(f"✅ Migrated {len(settings)} settings")
        
        # Migrate projects
        print("📁 Migrating projects...")
        sqlite_cursor.execute("SELECT id, name, prompts, created_at FROM projects")
        projects = sqlite_cursor.fetchall()
        
        for project_id, name, prompts, created_at in projects:
            # Parse prompts JSON if it's a string
            if isinstance(prompts, str):
                prompts = json.loads(prompts)
            
            mysql_cursor.execute(
                "INSERT INTO projects (id, name, prompts, created_at) VALUES (%s, %s, %s, %s) ON DUPLICATE KEY UPDATE name = VALUES(name), prompts = VALUES(prompts), created_at = VALUES(created_at)",
                (project_id, name, json.dumps(prompts), created_at)
            )
        print(f"✅ Migrated {len(projects)} projects")
        
        # Migrate recordings
        print("🎵 Migrating recordings...")
        sqlite_cursor.execute("SELECT id, text, filename, recorded_at, project_id FROM recordings")
        recordings = sqlite_cursor.fetchall()
        
        for recording_id, text, filename, recorded_at, project_id in recordings:
            mysql_cursor.execute(
                "INSERT INTO recordings (id, text, filename, recorded_at, project_id) VALUES (%s, %s, %s, %s, %s) ON DUPLICATE KEY UPDATE text = VALUES(text), filename = VALUES(filename), recorded_at = VALUES(recorded_at), project_id = VALUES(project_id)",
                (recording_id, text, filename, recorded_at, project_id)
            )
        print(f"✅ Migrated {len(recordings)} recordings")
        
        # Migrate interactions
        print("📊 Migrating interactions...")
        sqlite_cursor.execute("SELECT id, action, details, timestamp FROM interactions")
        interactions = sqlite_cursor.fetchall()
        
        for interaction_id, action, details, timestamp in interactions:
            # Parse details JSON if it's a string
            if isinstance(details, str):
                details = json.loads(details)
            
            mysql_cursor.execute(
                "INSERT INTO interactions (id, action, data, timestamp) VALUES (%s, %s, %s, %s) ON DUPLICATE KEY UPDATE action = VALUES(action), data = VALUES(data), timestamp = VALUES(timestamp)",
                (interaction_id, action, json.dumps(details), timestamp)
            )
        print(f"✅ Migrated {len(interactions)} interactions")
        
        # Commit all changes
        mysql_conn.commit()
        
        print("\n✅ Migration completed successfully!")
        print(f"📊 Summary:")
        print(f"   - Settings: {len(settings)}")
        print(f"   - Projects: {len(projects)}")
        print(f"   - Recordings: {len(recordings)}")
        print(f"   - Interactions: {len(interactions)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        mysql_conn.rollback()
        return False
        
    finally:
        sqlite_conn.close()
        mysql_conn.close()

def backup_sqlite():
    """Create a backup of the SQLite database"""
    import shutil
    from datetime import datetime
    
    backup_name = f"tts_dataset_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
    try:
        shutil.copy2('tts_dataset.db', backup_name)
        print(f"💾 SQLite backup created: {backup_name}")
        return True
    except Exception as e:
        print(f"❌ Failed to create backup: {e}")
        return False

def main():
    print("🚀 SQLite to MySQL Migration Tool")
    print("=" * 40)
    
    # Check if SQLite database exists
    import os
    if not os.path.exists('tts_dataset.db'):
        print("❌ SQLite database 'tts_dataset.db' not found")
        print("   Make sure you're running this script from the backend directory")
        return
    
    # Create backup
    print("💾 Creating backup of SQLite database...")
    if not backup_sqlite():
        print("❌ Backup failed. Aborting migration.")
        return
    
    # Confirm migration
    print("\n⚠️  This will migrate all data from SQLite to MySQL")
    print("   Make sure MySQL is running and configured correctly")
    response = input("\nContinue with migration? (y/N): ")
    
    if response.lower() != 'y':
        print("❌ Migration cancelled")
        return
    
    # Perform migration
    if migrate_data():
        print("\n🎉 Migration completed successfully!")
        print("\n📝 Next steps:")
        print("1. Update your application to use MySQL")
        print("2. Test the application with the new database")
        print("3. Keep the SQLite backup for safety")
        print("4. Once confirmed working, you can remove the old SQLite database")
    else:
        print("\n❌ Migration failed. Check the error messages above.")

if __name__ == "__main__":
    main() 