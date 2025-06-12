#!/usr/bin/env python3
"""
Quick test script to verify Neon PostgreSQL database connection
"""

import sys
import os
from dotenv import load_dotenv

# Add src to path
sys.path.append('src')

load_dotenv()

def test_neon_connection():
    """Test connection to Neon PostgreSQL database"""
    print("🧪 Testing Neon PostgreSQL Connection")
    print("="*50)
    
    # Check environment variables
    required_vars = ['PGHOST', 'PGDATABASE', 'PGUSER', 'PGPASSWORD']
    
    print("📋 Checking environment variables...")
    for var in required_vars:
        value = os.getenv(var)
        if value:
            if var == 'PGPASSWORD':
                print(f"✅ {var}: ****{value[-4:]}")  # Show last 4 chars
            else:
                print(f"✅ {var}: {value}")
        else:
            print(f"❌ {var}: Not set")
            return False
    
    # Test database connection
    print("\n🔗 Testing database connection...")
    try:
        import psycopg2
        from psycopg2.extras import RealDictCursor
        
        connection = psycopg2.connect(
            host=os.getenv('PGHOST'),
            port=os.getenv('PGPORT', 5432),
            database=os.getenv('PGDATABASE'),
            user=os.getenv('PGUSER'),
            password=os.getenv('PGPASSWORD'),
            cursor_factory=RealDictCursor
        )
        
        print("✅ Connected to Neon PostgreSQL!")
        
        # Test basic query
        with connection.cursor() as cursor:
            cursor.execute("SELECT version()")
            version = cursor.fetchone()
            print(f"✅ PostgreSQL Version: {version['version'][:50]}...")
            
            # Test table existence
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name
            """)
            tables = cursor.fetchall()
            
            if tables:
                print(f"✅ Found {len(tables)} tables:")
                for table in tables:
                    print(f"   - {table['table_name']}")
            else:
                print("⚠️  No tables found - run setup_neon_database.py first")
        
        connection.close()
        return True
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False

def test_metrics_service():
    """Test metrics service with Neon database"""
    print("\n🧪 Testing Metrics Service...")
    try:
        from src.metrics_service import metrics
        
        if metrics.db_pool:
            print("✅ Metrics service connected to database")
            
            # Test creating a session
            test_email = {
                'sender_email': 'test@neon-test.com',
                'sender_name': 'Neon Test User',
                'subject': 'Neon Database Test',
                'email_text': 'Testing Neon database connection'
            }
            
            session_id = metrics.start_email_session(test_email)
            print(f"✅ Created test session: {session_id}")
            
            # Complete the session
            metrics.end_email_session('completed')
            print("✅ Session completed successfully")
            
            return True
        else:
            print("❌ Metrics service failed to connect")
            return False
            
    except Exception as e:
        print(f"❌ Metrics service test failed: {e}")
        return False

def test_dashboard_service():
    """Test dashboard service with Neon database"""
    print("\n🧪 Testing Dashboard Service...")
    try:
        from src.dashboard_service import dashboard
        
        if dashboard.db_pool:
            print("✅ Dashboard service connected to database")
            
            # Test getting overview stats
            stats = dashboard.get_overview_stats(days=7)
            print(f"✅ Retrieved overview stats: {stats.get('total_sessions', 0)} sessions")
            
            return True
        else:
            print("❌ Dashboard service failed to connect")
            return False
            
    except Exception as e:
        print(f"❌ Dashboard service test failed: {e}")
        return False

def main():
    """Run all Neon database tests"""
    print("🚀 Neon PostgreSQL Database Test Suite")
    print("="*60)
    
    tests = [
        ("Basic Connection", test_neon_connection),
        ("Metrics Service", test_metrics_service), 
        ("Dashboard Service", test_dashboard_service)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "="*60)
    print("📊 TEST RESULTS")
    print("="*60)
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:<20} {status}")
        if result:
            passed += 1
    
    print("="*60)
    print(f"Total: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("🎉 All tests passed! Neon database is ready.")
        print("\n🚀 Next steps:")
        print("1. Run: python setup_neon_database.py (if tables not found)")
        print("2. Start dashboard: python start_dashboard.py")
        print("3. Start Slack endpoint: python start_slack_endpoint.py")
    else:
        print("⚠️  Some tests failed. Check your .env file and credentials.")

if __name__ == "__main__":
    main()