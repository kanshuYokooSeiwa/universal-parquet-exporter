#!/usr/bin/env python3
"""
Standalone OpenSSL Patch Test
Tests if the OpenSSL patch can be applied and if it affects pyodbc behavior
"""

import os
import sys
import tempfile
import pyodbc

def create_openssl_patch():
    """Create OpenSSL legacy config"""
    config_content = """openssl_conf = openssl_init

[openssl_init]
ssl_conf = ssl_sect

[ssl_sect]
system_default = system_default_sect

[system_default_sect]
CipherString = DEFAULT:@SECLEVEL=0
"""
    
    temp_dir = tempfile.gettempdir()
    config_path = os.path.join(temp_dir, f"test_openssl_patch_{os.getpid()}.cnf")
    
    with open(config_path, 'w') as f:
        f.write(config_content)
    
    return config_path

def test_connection_with_patch():
    """Test connection with OpenSSL patch"""
    
    print("🔬 Standalone OpenSSL Patch Test")
    print("=" * 40)
    
    # Check current OpenSSL config
    current_conf = os.environ.get('OPENSSL_CONF', 'None')
    print(f"Current OPENSSL_CONF: {current_conf}")
    
    # Create patch
    patch_file = create_openssl_patch()
    print(f"Created patch file: {patch_file}")
    
    # Backup current setting
    old_conf = os.environ.get('OPENSSL_CONF')
    
    try:
        # Apply patch
        os.environ['OPENSSL_CONF'] = patch_file
        print(f"Applied OPENSSL_CONF: {os.environ['OPENSSL_CONF']}")
        
        # Test connection with different connection string approaches
        
        # Approach 1: Minimal connection string
        print("\\n1. Testing with minimal connection string...")
        conn_str1 = (
            f"DRIVER={{ODBC Driver 17 for SQL Server}};"
            f"SERVER=192.168.210.21;"
            f"DATABASE=stss;"
            f"UID=spm;"
            f"PWD=spm;"
            f"Encrypt=no;"
            f"TrustServerCertificate=yes;"
        )
        
        try:
            conn = pyodbc.connect(conn_str1)
            print("✅ SUCCESS with minimal connection string!")
            conn.close()
            return True
        except Exception as e:
            print(f"❌ Failed: {e}")
        
        # Approach 2: Try with different drivers
        print("\\n2. Testing with ODBC Driver 18...")
        conn_str2 = conn_str1.replace("ODBC Driver 17", "ODBC Driver 18")
        
        try:
            conn = pyodbc.connect(conn_str2)
            print("✅ SUCCESS with ODBC Driver 18!")
            conn.close()
            return True
        except Exception as e:
            print(f"❌ Failed: {e}")
            
        # Approach 3: Try without database specification
        print("\\n3. Testing without database specification...")
        conn_str3 = (
            f"DRIVER={{ODBC Driver 17 for SQL Server}};"
            f"SERVER=192.168.210.21;"
            f"UID=spm;"
            f"PWD=spm;"
            f"Encrypt=no;"
            f"TrustServerCertificate=yes;"
        )
        
        try:
            conn = pyodbc.connect(conn_str3)
            print("✅ SUCCESS without database specification!")
            # Try to select current database
            cursor = conn.cursor()
            cursor.execute("SELECT DB_NAME()")
            db_name = cursor.fetchone()[0]
            print(f"Connected to database: {db_name}")
            cursor.close()
            conn.close()
            return True
        except Exception as e:
            print(f"❌ Failed: {e}")
        
        return False
            
    finally:
        # Restore original setting
        if old_conf is not None:
            os.environ['OPENSSL_CONF'] = old_conf
        elif 'OPENSSL_CONF' in os.environ:
            del os.environ['OPENSSL_CONF']
            
        # Clean up patch file
        try:
            os.remove(patch_file)
        except:
            pass
        
        print(f"\\nCleaned up and restored OPENSSL_CONF")

if __name__ == "__main__":
    success = test_connection_with_patch()
    if success:
        print("\\n🎉 OpenSSL patch appears to work!")
    else:
        print("\\n💥 OpenSSL patch did not resolve the issue")
        print("This suggests the problem may be:")
        print("  - SQL Server configuration (TCP/IP not enabled)")
        print("  - Network firewall blocking connection")
        print("  - Authentication method not supported")
        print("  - Different root cause than OpenSSL TLS")