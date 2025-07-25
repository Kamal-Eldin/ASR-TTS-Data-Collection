#!/usr/bin/env python3
"""
Migration script to migrate from JSON prompts in Project table to separate Prompt table
This script migrates existing data to the new schema.
"""

import os
import sys
import json
from datetime import datetime

# Add the backend directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import DatabaseConfig
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import pymysql

def check_old_schema():
    """Check if the old schema exists (projects table with prompts JSON column)"""
    try:
        # Try to connect to database
        DATABASE_URL = DatabaseConfig.get_database_url()
        engine = create_engine(DATABASE_URL, pool_pre_ping=True, pool_recycle=3600)
        
        with engine.connect() as conn:
            # Check if projects table has prompts column
            result = conn.execute(text("""
                SELECT COLUMN_NAME 
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_NAME = 'projects' 
                AND COLUMN_NAME = 'prompts'
            """)).fetchone()
            
            if result:
                print("✅ Found old schema with prompts JSON column")
                return True
            else:
                print("ℹ️  No old schema found - already using new schema")
                return False
                
    except Exception as e:
        print(f"❌ Error checking schema: {e}")
        return False

def migrate_data():
    """Migrate data from old schema to new schema"""
    try:
        DATABASE_URL = DatabaseConfig.get_database_url()
        engine = create_engine(DATABASE_URL, pool_pre_ping=True, pool_recycle=3600)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        
        db = SessionLocal()
        
        print("🔄 Starting migration from JSON prompts to Prompt table...")
        
        # Get all projects with prompts JSON
        projects = db.execute(text("""
            SELECT id, name, prompts 
            FROM projects 
            WHERE prompts IS NOT NULL AND prompts != '[]'
        """)).fetchall()
        
        print(f"📁 Found {len(projects)} projects to migrate")
        
        for project in projects:
            project_id = project[0]
            project_name = project[1]
            prompts_json = project[2]
            
            print(f"  📝 Migrating project: {project_name}")
            
            try:
                # Parse prompts JSON
                if isinstance(prompts_json, str):
                    prompts = json.loads(prompts_json)
                else:
                    prompts = prompts_json
                
                # Insert prompts into new table
                for index, prompt_text in enumerate(prompts):
                    db.execute(text("""
                        INSERT INTO prompts (project_id, text, order_index, created_at)
                        VALUES (:project_id, :text, :order_index, :created_at)
                    """), {
                        "project_id": project_id,
                        "text": prompt_text,
                        "order_index": index,
                        "created_at": datetime.utcnow()
                    })
                
                print(f"    ✅ Migrated {len(prompts)} prompts")
                
            except Exception as e:
                print(f"    ❌ Failed to migrate project {project_name}: {e}")
                continue
        
        # Update recordings to link to prompts
        print("🔗 Linking recordings to prompts...")
        
        recordings = db.execute(text("""
            SELECT r.id, r.text, r.project_id 
            FROM recordings r 
            WHERE r.prompt_id IS NULL
        """)).fetchall()
        
        print(f"  🎵 Found {len(recordings)} recordings to link")
        
        for recording in recordings:
            recording_id = recording[0]
            recording_text = recording[1]
            project_id = recording[2]
            
            # Find matching prompt
            prompt = db.execute(text("""
                SELECT id FROM prompts 
                WHERE project_id = :project_id AND text = :text
            """), {
                "project_id": project_id,
                "text": recording_text
            }).fetchone()
            
            if prompt:
                # Update recording with prompt_id
                db.execute(text("""
                    UPDATE recordings 
                    SET prompt_id = :prompt_id 
                    WHERE id = :recording_id
                """), {
                    "prompt_id": prompt[0],
                    "recording_id": recording_id
                })
                print(f"    ✅ Linked recording {recording_id} to prompt {prompt[0]}")
            else:
                print(f"    ⚠️  No matching prompt found for recording {recording_id}")
        
        # Remove prompts column from projects table
        print("🧹 Cleaning up old schema...")
        try:
            db.execute(text("ALTER TABLE projects DROP COLUMN prompts"))
            print("  ✅ Removed prompts column from projects table")
        except Exception as e:
            print(f"  ⚠️  Could not remove prompts column: {e}")
        
        db.commit()
        print("\n✅ Migration completed successfully!")
        
        # Show summary
        total_projects = db.execute(text("SELECT COUNT(*) FROM projects")).fetchone()[0]
        total_prompts = db.execute(text("SELECT COUNT(*) FROM prompts")).fetchone()[0]
        total_recordings = db.execute(text("SELECT COUNT(*) FROM recordings")).fetchone()[0]
        
        print(f"\n📊 Migration Summary:")
        print(f"   - Projects: {total_projects}")
        print(f"   - Prompts: {total_prompts}")
        print(f"   - Recordings: {total_recordings}")
        
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        if 'db' in locals():
            db.rollback()
        return False
    finally:
        if 'db' in locals():
            db.close()

def main():
    print("🚀 Migration to Prompt Table Schema")
    print("=" * 40)
    
    # Check if old schema exists
    if not check_old_schema():
        print("\n✅ No migration needed - already using new schema")
        return
    
    # Confirm migration
    print("\n⚠️  This will migrate your data from the old JSON prompts schema to the new Prompt table schema")
    print("   This is a one-way migration. Make sure you have a backup of your database.")
    response = input("\nContinue with migration? (y/N): ")
    
    if response.lower() != 'y':
        print("❌ Migration cancelled")
        return
    
    # Perform migration
    if migrate_data():
        print("\n🎉 Migration completed successfully!")
        print("\n📝 Next steps:")
        print("1. Restart your FastAPI server")
        print("2. Test the application to ensure everything works correctly")
        print("3. The new schema provides better data structure and querying capabilities")
    else:
        print("\n❌ Migration failed. Check the error messages above.")

if __name__ == "__main__":
    main() 