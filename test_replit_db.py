#!/usr/bin/env python3
"""
Quick test script for Replit database connection using psycopg2
"""

import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

def test_direct_connection():
    """Test direct psycopg2 connection"""
    print("🔗 Testing direct psycopg2 connection...")
    
    try:
        conn = psycopg2.connect(
            host=os.getenv('PGHOST'),
            database=os.getenv('PGDATABASE'),
            user=os.getenv('PGUSER'),
            password=os.getenv('PGPASSWORD'),
            port=os.getenv('PGPORT', 5432),
            sslmode='require'
        )
        
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()[0]
        print(f"✅ Connected! PostgreSQL version: {version[:50]}...")
        
        # Check existing tables
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name
        """)
        tables = [row[0] for row in cursor.fetchall()]
        print(f"📊 Found {len(tables)} tables: {tables}")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False

def test_metrics_service():
    """Test metrics service connection"""
    print("\n📈 Testing metrics service...")
    
    try:
        import sys
        sys.path.append('src')
        from src.metrics_service import metrics
        
        if metrics.db_pool:
            print("✅ Metrics service has database connection")
            return True
        else:
            print("❌ Metrics service has no database connection")
            return False
            
    except Exception as e:
        print(f"❌ Metrics service test failed: {e}")
        return False

def main():
    print("🧪 REPLIT DATABASE CONNECTION TEST")
    print("="*50)
    
    # Check environment variables
    required_vars = ['PGHOST', 'PGDATABASE', 'PGUSER', 'PGPASSWORD']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"❌ Missing environment variables: {missing_vars}")
        print("   Please check your Replit Secrets")
        return False
    
    print("✅ All required environment variables present")
    
    # Test connections
    success = True
    success &= test_direct_connection()
    success &= test_metrics_service()
    
    print(f"\n{'🎉 ALL TESTS PASSED!' if success else '❌ Some tests failed'}")
    print("Ready for database setup!" if success else "Fix connection issues first")
    
    return success

if __name__ == "__main__":
    main()