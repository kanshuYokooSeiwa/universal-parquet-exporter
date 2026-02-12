# SQL Server Connection Issue on macOS (OpenSSL 3.0)

## The Problem

When attempting to connect to an on-premise SQL Server from a modern macOS environment (e.g., M4 Pro, Sequoia 15.x) using Python 3 and **ODBC Driver 18 for SQL Server**, the connection fails with the following error:

> `[08001] [Microsoft][ODBC Driver 18 for SQL Server]TCP Provider: Error code 0x2746 (10054) (SQLDriverConnect)`

However, the native command-line tool `sqlcmd` connects successfully.

## Root Cause Analysis

This is a **TLS Protocol Mismatch** caused by security hardening in macOS.

1. **OpenSSL 3.0:** Newer macOS versions use OpenSSL 3.0, which enforces strict security standards by default. It rejects legacy TLS handshakes or weak keys (often found in older on-premise SQL Servers or self-signed certificates).
2. **ODBC Driver 18:** This driver utilizes the system's OpenSSL library. When it attempts to handshake with the legacy SQL Server, OpenSSL 3.0 terminates the connection because the server's encryption parameters do not meet the default security level (`SECLEVEL=1` or higher).
3. **Why `sqlcmd` worked:** The `sqlcmd` utility is often statically linked or configured to allow permissive legacy connections, bypassing the strict system-wide OpenSSL checks.

## The Solution

To fix this without altering the global system security or the on-premise server, we must **temporarily lower the OpenSSL security level** only for the Python process.

**The Fix Steps:**

1. **Configuration:** Explicitly set `Encrypt=no` (or permissive mode) in the ODBC connection string.
2. **Runtime Patch:** The Python script generates a temporary `openssl_legacy.cnf` file that sets `CipherString = DEFAULT:@SECLEVEL=0`.
3. **Environment Injection:** The script sets the `OPENSSL_CONF` environment variable to point to this file *before* loading the ODBC driver.

---

## 1. Configuration File (`db_config.xml`)

This file holds the connection parameters. Note the `<encrypt>no</encrypt>` setting.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<configuration>
    <database>
        <server>192.168.210.21</server>
        <username>spm</username>
        <password>spm</password>
        <name>stss</name>
    </database>
    
    <settings>
        <trust_certificate>yes</trust_certificate>
        <encrypt>no</encrypt>
    </settings>

    <command>
        <![CDATA[
        SELECT DB_NAME() AS CurrentDB, * FROM sys.databases 
        WHERE name = 'stss';
        ]]>
    </command>
</configuration>

```

---

## 2. Python Connector Script (`mssql_connector.py`)

This script implements the dynamic OpenSSL patch and executes the query.

```python
import pyodbc
import xml.etree.ElementTree as ET
import sys
import os

def patch_openssl():
    """
    Creates a temporary OpenSSL config to allow connection to legacy SQL Servers
    on macOS with OpenSSL 3.0 (Fixes error 0x2746).
    """
    cnf_content = """openssl_conf = openssl_init

[openssl_init]
ssl_conf = ssl_sect

[ssl_sect]
system_default = system_default_sect

[system_default_sect]
CipherString = DEFAULT:@SECLEVEL=0
"""
    # Create a local config file
    cnf_path = os.path.join(os.getcwd(), 'openssl_legacy.cnf')
    
    # Only write if it doesn't exist or is different (simple check)
    with open(cnf_path, 'w') as f:
        f.write(cnf_content)
    
    # Point OpenSSL to this config
    # This must be done BEFORE the driver is loaded by pyodbc
    os.environ['OPENSSL_CONF'] = cnf_path
    print(f"--- Applied OpenSSL Security Patch (SECLEVEL=0) via {cnf_path} ---")

def load_config(xml_file):
    """Parses the XML configuration file and returns a dictionary of settings."""
    try:
        tree = ET.parse(xml_file)
        root = tree.getroot()
        
        config = {
            'server': root.find('./database/server').text,
            'user': root.find('./database/username').text,
            'password': root.find('./database/password').text,
            'database': root.find('./database/name').text,
            'trust_cert': root.find('./settings/trust_certificate').text,
            # Ensure we default to 'no' if missing to prevent 0x2746 error
            'encrypt': root.find('./settings/encrypt').text or 'no',
            'query': root.find('./command').text.strip()
        }
        return config
    except Exception as e:
        print(f"Error reading config file: {e}")
        sys.exit(1)

def connect_and_query():
    # 1. Apply the OpenSSL patch
    patch_openssl()

    # 2. Load Configuration
    config = load_config('db_config.xml')
    
    # 3. Construct Connection String
    conn_str = (
        f"DRIVER={{ODBC Driver 18 for SQL Server}};"
        f"SERVER={config['server']};"
        f"DATABASE={config['database']};"
        f"UID={config['user']};"
        f"PWD={config['password']};"
        f"TrustServerCertificate={config['trust_cert']};"
        f"Encrypt={config['encrypt']};"
    )

    print(f"Connecting to {config['server']}...")

    try:
        # 4. Establish Connection
        with pyodbc.connect(conn_str) as conn:
            print("Successfully connected!")
            
            # 5. Execute Query
            cursor = conn.cursor()
            print(f"Executing query: {config['query']}")
            cursor.execute(config['query'])

            # 6. Fetch and Print Results
            if cursor.description:
                columns = [column[0] for column in cursor.description]
                print(f"\n{columns}")
                print("-" * 50)
                
                rows = cursor.fetchall()
                for row in rows:
                    print(row)
            else:
                print("\nQuery executed successfully (no results returned).")

    except pyodbc.Error as ex:
        print(f"\nConnection Error: {ex}")
        if "0x2746" in str(ex):
            print("\n*** TROUBLESHOOTING TIP ***")
            print("The OpenSSL patch might not have taken effect automatically.")
            print("Try running this command in your terminal before the script:")
            print(f"export OPENSSL_CONF={os.path.join(os.getcwd(), 'openssl_legacy.cnf')}")

if __name__ == "__main__":
    connect_and_query()

```