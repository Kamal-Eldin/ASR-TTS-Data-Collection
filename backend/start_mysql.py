#!/usr/bin/env python3
"""
MySQL Setup and Start Script for TTS Dataset Generator
This script helps users start MySQL and set up the database.
"""

import subprocess
import sys
import os
import platform
from . config import DatabaseConfig

def check_mysql_installed():
    """Check if MySQL is installed"""
    try:
        result = subprocess.run(['mysql', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ MySQL is installed: {result.stdout.strip()}")
            return True
        else:
            print("❌ MySQL is not installed or not in PATH")
            return False
    except FileNotFoundError:
        print("❌ MySQL is not installed or not in PATH")
        return False

def start_mysql_service():
    """Start MySQL service based on the operating system"""
    system = platform.system().lower()
    
    if system == "darwin":  # macOS
        print("🐳 Starting MySQL on macOS...")
        try:
            # Try Homebrew first
            result = subprocess.run(['brew', 'services', 'start', 'mysql'], capture_output=True, text=True)
            if result.returncode == 0:
                print("✅ MySQL started via Homebrew")
                return True
            else:
                print("⚠️  Homebrew MySQL not found, trying other methods...")
                # Try system MySQL
                result = subprocess.run(['sudo', 'launchctl', 'load', '-w', '/Library/LaunchDaemons/com.oracle.oss.mysql.mysqld.plist'], capture_output=True, text=True)
                if result.returncode == 0:
                    print("✅ MySQL started via system")
                    return True
                else:
                    print("❌ Failed to start MySQL")
                    return False
        except FileNotFoundError:
            print("❌ Homebrew not found")
            return False
    
    elif system == "linux":
        print("🐧 Starting MySQL on Linux...")
        try:
            result = subprocess.run(['sudo', 'systemctl', 'start', 'mysql'], capture_output=True, text=True)
            if result.returncode == 0:
                print("✅ MySQL started via systemctl")
                return True
            else:
                # Try service command
                result = subprocess.run(['sudo', 'service', 'mysql', 'start'], capture_output=True, text=True)
                if result.returncode == 0:
                    print("✅ MySQL started via service")
                    return True
                else:
                    print("❌ Failed to start MySQL")
                    return False
        except FileNotFoundError:
            print("❌ systemctl not found")
            return False
    
    elif system == "windows":
        print("🪟 Starting MySQL on Windows...")
        try:
            result = subprocess.run(['net', 'start', 'mysql'], capture_output=True, text=True, shell=True)
            if result.returncode == 0:
                print("✅ MySQL started")
                return True
            else:
                print("❌ Failed to start MySQL")
                return False
        except FileNotFoundError:
            print("❌ net command not found")
            return False
    
    else:
        print(f"❌ Unsupported operating system: {system}")
        return False

def test_mysql_connection():
    """Test MySQL connection"""
    try:
        import pymysql
        connection = pymysql.connect(
            host=DatabaseConfig.MYSQL_HOST,
            port=DatabaseConfig.MYSQL_PORT,
            user=DatabaseConfig.MYSQL_USER,
            password=DatabaseConfig.MYSQL_PASSWORD,
            charset='utf8mb4'
        )
        with connection.cursor() as cursor:
            cursor.execute("SELECT VERSION()")
            version = cursor.fetchone()
            print(f"✅ MySQL connection successful: {version[0]}")
        connection.close()
        return True
    except Exception as e:
        print(f"❌ MySQL connection failed: {e}")
        return False

def main():
    print("🚀 MySQL Setup for TTS Dataset Generator")
    print("=" * 50)
    
    # Check if MySQL is installed
    if not check_mysql_installed():
        print("\n📝 To install MySQL:")
        print("   macOS: brew install mysql")
        print("   Ubuntu/Debian: sudo apt install mysql-server")
        print("   Windows: Download from https://dev.mysql.com/downloads/mysql/")
        return
    
    # Start MySQL service
    if not start_mysql_service():
        print("\n❌ Failed to start MySQL service")
        print("   Please start MySQL manually and try again")
        return
    
    # Wait a moment for MySQL to start
    import time
    print("⏳ Waiting for MySQL to start...")
    time.sleep(3)
    
    # Test connection
    if not test_mysql_connection():
        print("\n❌ MySQL connection failed")
        print("   Please check your MySQL configuration in config.py")
        print("   Default settings:")
        print(f"   - Host: {DatabaseConfig.MYSQL_HOST}")
        print(f"   - Port: {DatabaseConfig.MYSQL_PORT}")
        print(f"   - User: {DatabaseConfig.MYSQL_USER}")
        print(f"   - Database: {DatabaseConfig.MYSQL_DATABASE}")
        return
    
    # Setup database
    print("\n📊 Setting up database...")
    try:
        from . setup_database import main as setup_db
        setup_db()
    except Exception as e:
        print(f"❌ Database setup failed: {e}")
    
    print("\n🎉 MySQL setup completed successfully!")
    print("\n📝 Next steps:")
    print("1. Start the FastAPI server: uvicorn main:app --reload")
    print("2. The application will now use MySQL instead of SQLite")
    print("3. Access the application at http://localhost:3000")

if __name__ == "__main__":
    main() 