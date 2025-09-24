#!/usr/bin/env python3
"""
Database setup script for TTS Dataset Generator
This script creates the MySQL database and tables if they don't exist.
"""

import os
import sys
import pymysql

# Add the backend directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import DatabaseConfig

def create_database_if_not_exists():
    """Create the database if it doesn't exist"""
    try:
        # Connect to MySQL server (without specifying database)
        connection = pymysql.connect(
            host=DatabaseConfig.MYSQL_HOST,
            port=DatabaseConfig.MYSQL_PORT,
            user=DatabaseConfig.MYSQL_USER,
            password=DatabaseConfig.get_db_password(),
            charset='utf8mb4'
        )
        
        with connection.cursor() as cursor:
            # Create database if it doesn't exist
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{DatabaseConfig.MYSQL_DATABASE}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
            print(f"✅ Database '{DatabaseConfig.MYSQL_DATABASE}' is ready")
            
        connection.close()
        
    except pymysql.Error as e:
        print(f"❌ Error connecting to MySQL: {e}")
        print("\nPlease make sure:")
        print("1. MySQL server is running")
        print("2. MySQL credentials are correct in config.py")
        print("3. The MySQL user has CREATE DATABASE privileges")
        return False
    
    return True

def test_db_connection():
    """Test the database connection"""
    try:
        connection = pymysql.connect(
            host=DatabaseConfig.MYSQL_HOST,
            port=DatabaseConfig.MYSQL_PORT,
            user=DatabaseConfig.MYSQL_USER,
            password=DatabaseConfig.get_db_password(),
            database=DatabaseConfig.MYSQL_DATABASE,
            charset='utf8mb4'
        )
        
        with connection.cursor() as cursor:
            cursor.execute("SELECT VERSION()")
            version = cursor.fetchone()
            print(f"✅ Connected to MySQL {version[0]}")
            
        connection.close()
        return True
        
    except pymysql.Error as e:
        print(f"❌ Error testing connection: {e}")
        return False

def main():
    print("🚀 Setting up MySQL database for TTS Dataset Generator...")
    print(f"📊 Database: {DatabaseConfig.MYSQL_DATABASE}")
    print(f"🔗 Host: {DatabaseConfig.MYSQL_HOST}:{DatabaseConfig.MYSQL_PORT}")
    print(f"👤 User: {DatabaseConfig.MYSQL_USER}")
    print()
    
    # Create database
    if not create_database_if_not_exists():
        print(f"failed to connect to mysql server or create database {DatabaseConfig.MYSQL_DATABASE}")
    
    # Test connection
    if not test_db_connection():
        print(f"failed to connect to database {DatabaseConfig.MYSQL_DATABASE}")
    
    print("\n✅ Database setup completed successfully!")
    print("\n📝 Next steps:")
    print("1. Start the FastAPI server: uvicorn main:app --reload")
    print("2. The tables will be created automatically when the server starts")
    print("3. Access the application at http://localhost:3000")

if __name__ == "__main__":
    main() 