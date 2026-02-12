#!/usr/bin/env python3
"""
SQL Server Connection Test Script
Created: February 12, 2026
Purpose: Debug and validate SQL Server connectivity for mysql-parquet-lib

This script mirrors connectionTest.ipynb functionality with enhanced diagnostics
and troubleshooting for SQL Server connections on macOS.
"""

import os
import sys
import traceback
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from src.database.sqlserver_connection import SQLServerConnection
from config.sqlserver_config import SQLServerConfig

def load_config_from_env() -> SQLServerConfig:
    """Load configuration from .confSQLConnection environment variables"""
    
    # Check if .confSQLConnection exists and provide guidance
    conf_file = Path(".confSQLConnection")
    if conf_file.exists():
        print(f"✅ Found configuration file: {conf_file}")
        print("💡 Make sure to source it: source .confSQLConnection")
        print("   Or run this script with: source .confSQLConnection && python test_sqlserver_connection.py")
    else:
        print("❌ No .confSQLConnection file found")
        print("💡 Run: ./configure_sql_connection_info.sh to create it")
        print("   This will interactively configure your SQL Server connection settings")
        
    # Try to load configuration from environment
    try:
        config = SQLServerConfig.from_environment()
        print("✅ Configuration loaded from environment variables")
        return config
    except ValueError as e:
        print(f"❌ Configuration error: {e}")
        print("\n🔧 Manual configuration required. Please run:")
        print("   ./configure_sql_connection_info.sh")
        print("   source .confSQLConnection")
        print("   python test_sqlserver_connection.py")
        sys.exit(1)

def test_prerequisites():
    """Test system prerequisites for SQL Server connectivity"""
    print("\n🔍 Testing Prerequisites...")
    success = True
    
    # Test pyodbc import
    try:
        import pyodbc
        print(f"✅ pyodbc version: {pyodbc.version}")
    except ImportError as e:
        print(f"❌ pyodbc not installed: {e}")
        print("💡 Install with: pip install pyodbc")
        success = False
    
    # List available ODBC drivers
    try:
        import pyodbc
        all_drivers = pyodbc.drivers()
        sql_drivers = [driver for driver in all_drivers if 'SQL Server' in driver]
        
        if sql_drivers:
            print(f"✅ Available SQL Server ODBC drivers:")
            for i, driver in enumerate(sql_drivers, 1):
                print(f"   {i}. {driver}")
        else:
            print("❌ No SQL Server ODBC drivers found")
            print("💡 Install Microsoft ODBC Driver for SQL Server:")
            print("   https://docs.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server")
            success = False
            
    except Exception as e:
        print(f"❌ Error checking ODBC drivers: {e}")
        success = False
    
    return success

def test_connection_prerequisites(config: SQLServerConfig):
    """Test connection prerequisites using the SQLServerConnection class"""
    print(f"\n🔧 Testing Connection Prerequisites...")
    
    sql_conn = SQLServerConnection(config)
    prereq_results = sql_conn.validate_connection_prerequisites()
    
    # Display results
    if prereq_results['pyodbc_version']:
        print(f"✅ pyodbc version: {prereq_results['pyodbc_version']}")
    
    if prereq_results['odbc_drivers_available']:
        print(f"✅ Available ODBC drivers:")
        for driver in prereq_results['odbc_drivers_available']:
            print(f"   - {driver}")
        print(f"💡 Recommended driver: {prereq_results['recommended_driver']}")
    else:
        print("❌ No ODBC drivers available")
    
    if prereq_results['config_issues']:
        print("❌ Configuration issues:")
        for issue in prereq_results['config_issues']:
            print(f"   - {issue}")
        return False
    else:
        print("✅ Configuration validation passed")
    
    return prereq_results['config_valid']

def test_connection(config: SQLServerConfig):
    """Test SQL Server connection with detailed diagnostics"""
    print(f"\n🔌 Testing Connection to {config.host}:{config.port}...")
    
    # Create connection object
    sql_conn = SQLServerConnection(config)
    
    try:
        # Build and display connection string (with masked password)
        conn_str = sql_conn._build_connection_string()
        masked_conn_str = conn_str.replace(f"PWD={config.password}", "PWD=********")
        print(f"📝 Connection String: {masked_conn_str}")
        
        # Display configuration summary
        print(f"📋 Connection Configuration:")
        print(f"   Host: {config.host}")
        print(f"   Port: {config.port}")
        print(f"   Database: {config.database}")
        print(f"   User: {config.user}")
        print(f"   Driver: {config.driver}")
        print(f"   Encrypt: {config.encrypt}")
        print(f"   Trust Certificate: {config.trust_server_certificate}")
        
        # Attempt connection
        print("🔄 Attempting connection...")
        connection = sql_conn.connect()
        
        if connection:
            print("✅ Connection successful!")
            
            # Test basic query (matching user's sqlcmd test: SELECT DB_NAME())
            print("🔄 Testing basic query...")
            cursor = connection.cursor()
            
            cursor.execute("SELECT DB_NAME() as current_database")
            result = cursor.fetchone()
            print(f"📊 Current Database: {result[0]}")
            
            # Additional system info to verify connectivity
            cursor.execute("SELECT @@VERSION as sql_version")
            version = cursor.fetchone()[0]
            version_line = version.split('\\n')[0] if '\\n' in version else version
            print(f"🔧 SQL Server Version: {version_line}")
            
            # Test query similar to connectionTest.ipynb
            print("🔄 Testing sample query...")
            cursor.execute("SELECT TOP 5 name, database_id FROM sys.databases ORDER BY name")
            databases = cursor.fetchall()
            print("📋 Available databases:")
            for db in databases:
                print(f"   - {db[0]} (ID: {db[1]})")
            
            cursor.close()
            print("✅ All tests completed successfully!")
            
            return True
            
    except Exception as e:
        print(f"❌ Connection failed: {str(e)}")
        print(f"🔍 Error type: {type(e).__name__}")
        
        # The enhanced error handling is now in SQLServerConnection.connect()
        # so the detailed troubleshooting suggestions are already included
        
        print(f"\n🔧 Additional troubleshooting:")
        print(f"   - Verify SQL Server is running on {config.host}:{config.port}")
        print(f"   - Test network connectivity: telnet {config.host} {config.port}")
        print(f"   - Compare with working sqlcmd: sqlcmd -S {config.host} -U {config.user} -P ****")
        
        return False
        
    finally:
        # Clean up
        if sql_conn:
            sql_conn.close()

def run_diagnostic_mode():
    """Enhanced diagnostic mode with system information"""
    print("\n🔬 Running Diagnostic Mode...")
    
    print("🖥️  System Information:")
    print(f"   Platform: {sys.platform}")
    print(f"   Python: {sys.version}")
    
    print("\n📁 Working Directory:")
    print(f"   Current: {os.getcwd()}")
    print(f"   Script location: {Path(__file__).parent}")
    
    print("\n🔗 Environment Variables:")
    env_vars = ['SQLSERVER_HOST', 'SQLSERVER_PORT', 'SQLSERVER_DATABASE', 
                'SQLSERVER_USER', 'SQLSERVER_ENCRYPT', 'SQLSERVER_TRUST_CERT']
    
    for var in env_vars:
        value = os.getenv(var, 'Not set')
        if var == 'SQLSERVER_PASSWORD':
            value = '********' if os.getenv(var) else 'Not set'
        print(f"   {var}: {value}")

def main():
    """Main test execution"""
    print("🚀 SQL Server Connection Test")
    print("=" * 50)
    print("Purpose: Debug SQL Server connectivity issues for mysql-parquet-lib")
    print("Target: SQL Server 2022 on macOS with pyodbc")
    print()
    
    # Check for diagnostic mode
    if len(sys.argv) > 1 and sys.argv[1] in ['--diagnostic', '-d']:
        run_diagnostic_mode()
    
    # Test prerequisites
    print("📋 Step 1: Prerequisites Check")
    if not test_prerequisites():
        print("\n❌ Prerequisites check failed. Please resolve the issues above.")
        sys.exit(1)
    
    # Load configuration
    print("\n📋 Step 2: Configuration Loading")
    try:
        config = load_config_from_env()
        
        # Validate configuration
        issues = config.validate()
        if issues:
            print("❌ Configuration validation failed:")
            for issue in issues:
                print(f"   - {issue}")
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        sys.exit(1)
    
    # Test connection prerequisites
    print("\\n📋 Step 3: Connection Prerequisites")
    if not test_connection_prerequisites(config):
        print("\\n❌ Connection prerequisites check failed.")
        sys.exit(1)
    
    # Test connection
    print("\\n📋 Step 4: Connection Test")
    success = test_connection(config)
    
    print("\\n" + "=" * 50)
    if success:
        print("🎉 SUCCESS: SQL Server connection test completed successfully!")
        print("💡 Your SQL Server connection is working correctly.")
        print("   You can now use this configuration in your applications.")
    else:
        print("💥 FAILED: SQL Server connection test failed.")
        print("💡 Please review the error messages above and:")
        print("   1. Check SQL Server is running and accessible")
        print("   2. Verify your credentials are correct")
        print("   3. Ensure network connectivity to the server")
        print("   4. Consider running with --diagnostic for more details")
        sys.exit(1)

if __name__ == "__main__":
    main()