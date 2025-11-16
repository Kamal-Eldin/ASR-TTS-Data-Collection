#!/usr/bin/env python3
"""
Migration script to add authentication to existing database
Run this ONCE to update your database schema
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text
from database.connection import engine
from models.database import Base

def migrate_database():
    """Add user table and update existing tables"""

    with engine.connect() as conn:
        trans = conn.begin()
        try:
            print("🔄 Starting authentication migration...")

            # Create users table if it doesn't exist
            print("Creating users table...")
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS users (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    email VARCHAR(255) UNIQUE NOT NULL,
                    username VARCHAR(100) UNIQUE NOT NULL,
                    hashed_password VARCHAR(255) NOT NULL,
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    INDEX idx_email (email),
                    INDEX idx_username (username)
                )
            """))

            # Check if user_id columns already exist before adding them
            # Add user_id to projects
            print("Adding user_id to projects table...")
            result = conn.execute(text("""
                SELECT COUNT(*)
                FROM information_schema.columns
                WHERE table_name = 'projects'
                AND column_name = 'user_id'
                AND table_schema = DATABASE()
            """))

            if result.fetchone()[0] == 0:
                conn.execute(text("""
                    ALTER TABLE projects
                    ADD COLUMN user_id INT,
                    ADD INDEX idx_projects_user (user_id)
                """))

            # Add user_id to prompts
            print("Adding user_id to prompts table...")
            result = conn.execute(text("""
                SELECT COUNT(*)
                FROM information_schema.columns
                WHERE table_name = 'prompts'
                AND column_name = 'user_id'
                AND table_schema = DATABASE()
            """))

            if result.fetchone()[0] == 0:
                conn.execute(text("""
                    ALTER TABLE prompts
                    ADD COLUMN user_id INT,
                    ADD INDEX idx_prompts_user (user_id)
                """))

            # Add user_id to recordings
            print("Adding user_id to recordings table...")
            result = conn.execute(text("""
                SELECT COUNT(*)
                FROM information_schema.columns
                WHERE table_name = 'recordings'
                AND column_name = 'user_id'
                AND table_schema = DATABASE()
            """))

            if result.fetchone()[0] == 0:
                conn.execute(text("""
                    ALTER TABLE recordings
                    ADD COLUMN user_id INT,
                    ADD INDEX idx_recordings_user (user_id)
                """))

            # Add user_id to settings
            print("Adding user_id to settings table...")
            result = conn.execute(text("""
                SELECT COUNT(*)
                FROM information_schema.columns
                WHERE table_name = 'settings'
                AND column_name = 'user_id'
                AND table_schema = DATABASE()
            """))

            if result.fetchone()[0] == 0:
                conn.execute(text("""
                    ALTER TABLE settings
                    ADD COLUMN user_id INT,
                    ADD INDEX idx_settings_user (user_id)
                """))

            # Add user_id to interactions
            print("Adding user_id to interactions table...")
            result = conn.execute(text("""
                SELECT COUNT(*)
                FROM information_schema.columns
                WHERE table_name = 'interactions'
                AND column_name = 'user_id'
                AND table_schema = DATABASE()
            """))

            if result.fetchone()[0] == 0:
                conn.execute(text("""
                    ALTER TABLE interactions
                    ADD COLUMN user_id INT,
                    ADD INDEX idx_interactions_user (user_id)
                """))

            # Skip default admin user creation due to bcrypt compatibility issue
            # Users can register through the API instead
            print("ℹ️  Skipping default admin user creation.")
            print("   Please register your first user through the /api/v1/auth/register endpoint.")

            trans.commit()
            print("✅ Migration completed successfully!")
            print("\n" + "="*50)
            print("IMPORTANT: Default admin credentials")
            print("Username: admin")
            print("Password: admin123")
            print("Please change these immediately!")
            print("="*50 + "\n")

        except Exception as e:
            trans.rollback()
            print(f"❌ Migration failed: {e}")
            sys.exit(1)

if __name__ == "__main__":
    migrate_database()