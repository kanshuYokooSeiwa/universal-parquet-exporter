# SQL Server Connection Implementation Plan

**Date**: February 12, 2026  
**Objective**: Fix SQL Server connection issues in mysql-parquet-lib for macOS environment  
**Target Environment**: macOS 15.7.3, M4 Pro, SQL Server 2022 on 192.168.210.21  

## Current Status Analysis

### ✅ Working Components
- **sqlcmd connectivity**: Successfully connects to `192.168.210.21` database `stss`
- **Configuration system**: [configure_sql_connection_info.sh](configure_sql_connection_info.sh) creates `.confSQLConnection` files
- **SQL Server classes**: [src/database/sqlserver_connection.py](src/database/sqlserver_connection.py) and [config/sqlserver_config.py](config/sqlserver_config.py) exist

### ❌ Current Issues
1. **TCP Provider Error 10054**: Connection failures in Python despite working sqlcmd
2. **Connection String Format**: Mismatch between sqlcmd parameters and pyodbc connection string
3. **SSL/Certificate Configuration**: `trust_server_certificate` and `encrypt` settings incompatible with SQL Server 2022
4. **macOS ODBC Driver**: Potential compatibility issues with "ODBC Driver 18 for SQL Server"

### 📋 Root Cause Analysis
- **sqlcmd working parameters**: `-S 192.168.210.21 -U spm -P spm`
- **Python failing**: Connection string format not matching sqlcmd's implicit defaults
- **Network connectivity**: Confirmed working via sqlcmd, issue is configuration/driver level

## Implementation Plan

### Phase 1: Connection String Debugging 🔍

**Files to modify**: 
- [src/database/sqlserver_connection.py](src/database/sqlserver_connection.py)
- [config/sqlserver_config.py](config/sqlserver_config.py)

**Tasks**:

1. **Update SQLServerConnection.build_connection_string()**
   ```python
   # Current problematic format
   DRIVER={ODBC Driver 18 for SQL Server};SERVER=192.168.210.21,1433;...;Encrypt=yes;TrustServerCertificate=no
   
   # Target format (matching sqlcmd behavior)
   DRIVER={ODBC Driver 18 for SQL Server};SERVER=192.168.210.21;DATABASE=stss;UID=spm;PWD=spm;Encrypt=no;TrustServerCertificate=yes
   ```

2. **Add connection string validation**
   - Pre-flight checks for ODBC driver availability
   - Validate connection parameters before attempting connection
   - Add verbose error reporting with suggested fixes

3. **Implement fallback connection formats**
   ```python
   # Primary: Modern format with SSL disabled (matches sqlcmd default)
   # Fallback 1: Legacy format for older ODBC drivers  
   # Fallback 2: Alternative driver detection ("SQL Server" vs "ODBC Driver 18")
   ```

### Phase 2: Configuration Integration 🔧

**Files to modify**:
- [config/sqlserver_config.py](config/sqlserver_config.py)

**Tasks**:

1. **Environment Variable Integration**
   ```python
   @classmethod
   def from_environment(cls) -> 'SQLServerConfig':
       """Load configuration from .confSQLConnection environment variables"""
       return cls(
           host=os.getenv('SQLSERVER_HOST', 'localhost'),
           port=int(os.getenv('SQLSERVER_PORT', '1433')),
           # ... etc
       )
   ```

2. **Default Value Updates**
   - Change defaults to match user's working sqlcmd setup
   - `encrypt="no"` (sqlcmd default for local SQL Server)
   - `trust_server_certificate="yes"` (required for self-signed certificates)
   - `driver` auto-detection with fallbacks

3. **Validation Rules**
   - Ensure host/port combination is valid
   - Validate database name format
   - Check authentication parameters

### Phase 3: macOS Compatibility Fixes 🍎

**Files to modify**:
- [src/database/sqlserver_connection.py](src/database/sqlserver_connection.py)

**Tasks**:

1. **ODBC Driver Detection**
   ```python
   def detect_available_drivers(self) -> List[str]:
       """Detect available SQL Server ODBC drivers on macOS"""
       # Check: ODBC Driver 18, ODBC Driver 17, SQL Server
       # Return: List of available drivers in preference order
   ```

2. **Connection Health Checks**
   ```python
   def validate_connection_prerequisites(self) -> Dict[str, bool]:
       """Pre-flight validation before connection attempts"""
       return {
           'odbc_driver_available': bool,
           'network_reachable': bool, 
           'ssl_compatible': bool
       }
   ```

3. **Enhanced Error Handling**
   - Map pyodbc error codes to actionable messages
   - Specific handling for TCP Provider errors (10054, 10061, etc.)
   - SSL/TLS certificate troubleshooting guides

### Phase 4: Test Script Implementation 📝

**New file**: `test_sqlserver_connection.py`

**Requirements**:
- Mirror [connectionTest.ipynb](connectionTest.ipynb) functionality as executable script
- Use `.confSQLConnection` configuration approach  
- Include comprehensive diagnostics and troubleshooting

**Script Structure**:
```python
#!/usr/bin/env python3
"""
SQL Server Connection Test Script
Mirrors connectionTest.ipynb functionality with enhanced diagnostics
"""

def main():
    # 1. Load configuration from .confSQLConnection
    # 2. Validate prerequisites (driver, network, etc.)
    # 3. Attempt connection with detailed error reporting
    # 4. Execute test query (SELECT DB_NAME())
    # 5. Report connection success and performance metrics
    
def diagnostic_mode():
    # Enhanced troubleshooting output
    # Connection string analysis
    # ODBC driver enumeration
    # Network connectivity tests
```

### Phase 5: Integration Testing 🧪

**Test Cases**:

1. **Configuration Workflow**
   ```bash
   # Test the full configuration workflow
   ./configure_sql_connection_info.sh
   # Should create .confSQLConnection with user's values
   python test_sqlserver_connection.py
   # Should connect successfully
   ```

2. **Connection String Variants**
   - Test all fallback connection string formats
   - Validate with/without SSL configurations
   - Test different ODBC driver versions

3. **Error Scenarios**
   - Wrong password (should give clear auth error)
   - Wrong host (should give network error) 
   - Missing database (should give database error)

## Detailed Implementation Steps

### Step 1: Fix Connection String Building

**File**: [src/database/sqlserver_connection.py](src/database/sqlserver_connection.py)

**Current Issue Analysis**:
```python
# Problem: Connection string not optimized for SQL Server 2022/macOS
# User's working sqlcmd: sqlcmd -S 192.168.210.21 -U spm -P spm  
# Implicit sqlcmd defaults: No encryption, trust certificate, port 1433
```

**Implementation**:
```python
def build_connection_string(self) -> str:
    """Build optimized connection string for SQL Server 2022/macOS"""
    
    # Detect available ODBC drivers
    available_drivers = self._detect_odbc_drivers()
    driver = available_drivers[0] if available_drivers else self.config.driver
    
    # Base connection string optimized for SQL Server 2022
    conn_str_parts = [
        f"DRIVER={{{driver}}}",
        f"SERVER={self.config.host}",  # No port in SERVER for better compatibility
        f"DATABASE={self.config.database}",
        f"UID={self.config.user}",
        f"PWD={self.config.password}",
    ]
    
    # SSL/Encryption settings optimized for local SQL Server 2022
    if self.config.encrypt.lower() == "no":
        # Match sqlcmd default behavior (no encryption for local connections)
        conn_str_parts.extend([
            "Encrypt=no",
            "TrustServerCertificate=yes"  # Required even with Encrypt=no
        ])
    else:
        # Production settings with proper SSL
        conn_str_parts.extend([
            f"Encrypt={self.config.encrypt}",
            f"TrustServerCertificate={self.config.trust_server_certificate}"
        ])
    
    # Timeout settings for better stability
    conn_str_parts.extend([
        "Connection Timeout=30",
        "Login Timeout=30"
    ])
    
    return ";".join(conn_str_parts)
```

### Step 2: Environment Variable Integration

**File**: [config/sqlserver_config.py](config/sqlserver_config.py)

**Implementation**:
```python
import os
from typing import Optional

@dataclass
class SQLServerConfig:
    # ... existing fields ...
    
    @classmethod
    def from_environment(cls) -> 'SQLServerConfig':
        """Create configuration from .confSQLConnection environment variables"""
        return cls(
            host=os.getenv('SQLSERVER_HOST', '192.168.210.21'),  # User's default
            port=int(os.getenv('SQLSERVER_PORT', '1433')),
            database=os.getenv('SQLSERVER_DATABASE', 'stss'),    # User's database
            user=os.getenv('SQLSERVER_USER', ''),
            password=os.getenv('SQLSERVER_PASSWORD', ''),
            driver=os.getenv('SQLSERVER_DRIVER', 'ODBC Driver 18 for SQL Server'),
            encrypt=os.getenv('SQLSERVER_ENCRYPT', 'no'),        # Match sqlcmd default
            trust_server_certificate=os.getenv('SQLSERVER_TRUST_CERT', 'yes')  # Required for local
        )
    
    def validate(self) -> List[str]:
        """Validate configuration and return list of issues"""
        issues = []
        if not self.user:
            issues.append("Username is required")
        if not self.password:
            issues.append("Password is required")
        if not self.database:
            issues.append("Database name is required")
        # Add more validation rules...
        return issues
```

### Step 3: Create Test Script

**File**: `test_sqlserver_connection.py`

**Full Implementation**:
```python
#!/usr/bin/env python3
"""
SQL Server Connection Test Script
Created: February 12, 2026
Purpose: Debug and validate SQL Server connectivity for mysql-parquet-lib
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
    
    # Check if .confSQLConnection exists and source it
    conf_file = Path(".confSQLConnection")
    if conf_file.exists():
        print(f"✅ Found configuration file: {conf_file}")
        print("💡 Make sure to source it: source .confSQLConnection")
    else:
        print("❌ No .confSQLConnection file found")
        print("💡 Run: ./configure_sql_connection_info.sh to create it")
    
    # Load from environment
    config = SQLServerConfig.from_environment()
    
    # Validate configuration
    issues = config.validate()
    if issues:
        print("❌ Configuration issues found:")
        for issue in issues:
            print(f"   - {issue}")
        sys.exit(1)
    
    return config

def test_prerequisites():
    """Test system prerequisites for SQL Server connectivity"""
    print("\n🔍 Testing Prerequisites...")
    
    # Test pyodbc import
    try:
        import pyodbc
        print(f"✅ pyodbc version: {pyodbc.version}")
    except ImportError:
        print("❌ pyodbc not installed. Run: pip install pyodbc")
        return False
    
    # List available ODBC drivers
    try:
        drivers = [driver for driver in pyodbc.drivers() if 'SQL Server' in driver]
        if drivers:
            print(f"✅ Available SQL Server ODBC drivers:")
            for driver in drivers:
                print(f"   - {driver}")
        else:
            print("❌ No SQL Server ODBC drivers found")
            print("💡 Install: https://docs.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server")
            return False
    except Exception as e:
        print(f"❌ Error checking ODBC drivers: {e}")
        return False
    
    return True

def test_connection(config: SQLServerConfig):
    """Test SQL Server connection with detailed diagnostics"""
    print(f"\n🔌 Testing Connection to {config.host}:{config.port}...")
    
    # Create connection object
    sql_conn = SQLServerConnection(config)
    
    try:
        # Build and display connection string (with masked password)
        conn_str = sql_conn.build_connection_string()
        masked_conn_str = conn_str.replace(f"PWD={config.password}", "PWD=********")
        print(f"📝 Connection String: {masked_conn_str}")
        
        # Attempt connection
        print("🔄 Attempting connection...")
        connection = sql_conn.connect()
        
        if connection:
            print("✅ Connection successful!")
            
            # Test basic query (matching user's sqlcmd test)
            cursor = connection.cursor()
            cursor.execute("SELECT DB_NAME() as current_database")
            result = cursor.fetchone()
            print(f"📊 Current Database: {result[0]}")
            
            # Additional system info
            cursor.execute("SELECT @@VERSION as sql_version")
            version = cursor.fetchone()[0]
            print(f"🔧 SQL Server Version: {version.split('\\n')[0]}")
            
            cursor.close()
            
    except Exception as e:
        print(f"❌ Connection failed: {str(e)}")
        print(f"🔍 Error type: {type(e).__name__}")
        
        # Specific error analysis
        error_msg = str(e).lower()
        if "tcp provider" in error_msg and "10054" in error_msg:
            print("\n💡 TCP Provider Error 10054 Troubleshooting:")
            print("   - Check if SQL Server is accepting TCP connections")
            print("   - Verify firewall allows port 1433")
            print("   - Try: telnet 192.168.210.21 1433")
            print("   - Consider changing encrypt=no and trust_server_certificate=yes")
        elif "login failed" in error_msg:
            print("\n💡 Authentication Error:")
            print("   - Verify username/password are correct")
            print("   - Check if SQL Server authentication is enabled")
        elif "cannot open database" in error_msg:
            print("\n💡 Database Access Error:")
            print("   - Verify database name is correct")
            print("   - Check user has access to the database")
        
        print(f"\n🔧 Full error traceback:")
        traceback.print_exc()
        
    finally:
        # Clean up
        if sql_conn:
            sql_conn.close()

def main():
    """Main test execution"""
    print("🚀 SQL Server Connection Test")
    print("=" * 50)
    
    # Test prerequisites
    if not test_prerequisites():
        sys.exit(1)
    
    # Load configuration  
    try:
        config = load_config_from_env()
        print(f"\n📋 Configuration loaded:")
        print(f"   Host: {config.host}")
        print(f"   Port: {config.port}")  
        print(f"   Database: {config.database}")
        print(f"   User: {config.user}")
        print(f"   Driver: {config.driver}")
        print(f"   Encrypt: {config.encrypt}")
        print(f"   Trust Certificate: {config.trust_server_certificate}")
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        sys.exit(1)
    
    # Test connection
    test_connection(config)

if __name__ == "__main__":
    main()
```

## Timeline & Priorities

### 🔥 Immediate (Day 1)
1. **Fix connection string format** - Address TCP Provider 10054 error
2. **Update default SSL settings** - Match sqlcmd behavior (`encrypt=no`, `trust_server_certificate=yes`)
3. **Create test script** - Enable rapid iteration and debugging

### 📈 Short Term (Days 2-3)  
1. **Environment variable integration** - Seamless `.confSQLConnection` workflow
2. **ODBC driver detection** - Handle macOS compatibility issues
3. **Enhanced error reporting** - Clear diagnostics for troubleshooting

### 🎯 Medium Term (Week 1)
1. **Comprehensive testing** - Validate all connection scenarios
2. **Documentation updates** - Reflect new configuration approach
3. **Integration with existing examples** - Ensure backward compatibility

## Success Criteria

✅ **Primary Goal**: `python test_sqlserver_connection.py` connects successfully to 192.168.210.21  
✅ **Configuration**: `./configure_sql_connection_info.sh` → `.confSQLConnection` → successful connection  
✅ **Compatibility**: Works with user's macOS + SQL Server 2022 environment  
✅ **Diagnostics**: Clear error messages and troubleshooting guidance  

## Risk Mitigation

🚨 **Risk**: pyodbc incompatibilities on macOS M4  
🛡️ **Mitigation**: Add fallback to pymssql or sqlalchemy-based connection  

🚨 **Risk**: ODBC Driver 18 SSL issues with SQL Server 2022  
🛡️ **Mitigation**: Multiple connection string formats with SSL disabled  

🚨 **Risk**: Network/firewall configuration changes  
🛡️ **Mitigation**: Connection health checks and network validation  

## Notes

- **Focus**: Connection issues only (defer type safety and broader testing)
- **Constraint**: Keep pyodbc unless compatibility issues force alternatives  
- **Configuration**: Use existing `.confSQLConnection` approach, not environment prompts
- **Validation**: Must match working sqlcmd behavior exactly

---
*Generated on February 12, 2026 for mysql-parquet-lib SQL Server connectivity fixes*