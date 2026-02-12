# OpenSSL TLS Fix Implementation Plan

**Date**: February 12, 2026  
**Objective**: Integrate OpenSSL 3.0 TLS compatibility fix for SQL Server connections on macOS  
**Root Cause**: TCP Provider Error 10054 caused by OpenSSL 3.0 strict security standards rejecting legacy SQL Server TLS  

## Solution Analysis

### 🔍 **Problem Identification**
The provided solution correctly identifies the root cause of our persistent SQL Server connection issues:

**OpenSSL 3.0 TLS Protocol Mismatch**:
- macOS M4 Pro/Sequoia 15.x uses OpenSSL 3.0 with strict security (`SECLEVEL=1+`)
- ODBC Driver 18 uses system OpenSSL library
- On-premise SQL Server 2022 uses legacy/weak TLS parameters
- OpenSSL 3.0 terminates handshake due to security standard mismatch
- `sqlcmd` works because it bypasses system OpenSSL checks

### 📋 **Proposed Solution**
**Temporary OpenSSL Security Level Reduction**:
1. Create `openssl_legacy.cnf` with `CipherString = DEFAULT:@SECLEVEL=0`
2. Set `OPENSSL_CONF` environment variable before pyodbc import
3. Maintain `Encrypt=no` and `TrustServerCertificate=yes`

## Integration Plan

### **Phase 1: Enhanced SQLServerConnection Class** 🔧

**File**: [src/database/sqlserver_connection.py](src/database/sqlserver_connection.py)

**Tasks**:
1. **Add OpenSSL Patch Method**
   ```python
   def _apply_openssl_macos_patch(self) -> str:
       \"\"\"Apply OpenSSL 3.0 compatibility patch for legacy SQL Server connections\"\"\"
       # Create temporary openssl_legacy.cnf with SECLEVEL=0
       # Return path for cleanup
   ```

2. **Integrate Patch in Connection Flow**
   ```python
   def connect(self) -> pyodbc.Connection:
       # Step 1: Apply OpenSSL patch if on macOS and connection fails
       # Step 2: Attempt connection with current logic
       # Step 3: If TCP Provider 10054, apply patch and retry
   ```

3. **Add Patch Detection & Cleanup**
   ```python
   def _cleanup_openssl_patch(self, patch_file: str):
       \"\"\"Clean up temporary OpenSSL config file\"\"\"
       
   def _is_openssl_patch_needed(self, error: Exception) -> bool:
       \"\"\"Detect if OpenSSL patch is needed based on error\"\"\"
   ```

### **Phase 2: Configuration Updates** ⚙️

**Files**: 
- [config/sqlserver_config.py](config/sqlserver_config.py)
- [.confSQLConnection](.confSQLConnection)

**Tasks**:
1. **Add OpenSSL Patch Control**
   ```python
   @dataclass
   class SQLServerConfig:
       # ... existing fields ...
       auto_apply_openssl_patch: bool = True  # Enable automatic OpenSSL patching
       openssl_patch_on_error: bool = True   # Apply patch on TCP Provider errors
   ```

2. **Update Default Configuration**
   - Ensure `encrypt="no"` is default (already done)
   - Add OpenSSL patch environment variables to configure script

### **Phase 3: Test Script Enhancement** 🧪

**File**: [test_sqlserver_connection.py](test_sqlserver_connection.py)

**Tasks**:
1. **Add OpenSSL Diagnostics**
   ```python
   def test_openssl_compatibility():
       \"\"\"Test OpenSSL version and compatibility\"\"\"
       # Check OpenSSL version
       # Detect macOS version
       # Test SECLEVEL configuration
   ```

2. **Add Patch Testing Mode**
   ```python
   def test_with_openssl_patch():
       \"\"\"Test connection with OpenSSL patch applied\"\"\"
       # Apply patch manually
       # Test connection
       # Report results
   ```

### **Phase 4: Notebook Updates** 📓

**File**: [connectionTest.ipynb](connectionTest.ipynb)

**Tasks**:
1. **Add OpenSSL Patch Cell**
   - Manual patch application option
   - Patch status verification
   - Before/after connection comparison

2. **Enhanced Error Handling**
   - Detect TCP Provider 10054 specifically
   - Automatic patch suggestion
   - Clear troubleshooting guidance

## Detailed Implementation

### **1. OpenSSL Patch Integration**

**Location**: [src/database/sqlserver_connection.py](src/database/sqlserver_connection.py)

```python
import os
import sys
import tempfile
from pathlib import Path
from typing import Optional

class SQLServerConnection:
    def __init__(self, config: SQLServerConfig) -> None:
        self.config: SQLServerConfig = config
        self._connection: Optional[pyodbc.Connection] = None
        self._openssl_patch_file: Optional[str] = None  # Track patch file for cleanup
    
    def _is_macos_openssl_issue(self, error: Exception) -> bool:
        \"\"\"Detect if error is likely macOS OpenSSL 3.0 TLS issue\"\"\"
        error_str = str(error).lower()
        return (
            sys.platform == "darwin" and  # macOS only
            "tcp provider" in error_str and 
            ("10054" in error_str or "0x2746" in error_str)
        )
    
    def _apply_openssl_legacy_patch(self) -> str:
        \"\"\"
        Create temporary OpenSSL config to allow legacy TLS connections.
        
        Returns:
            Path to temporary config file for cleanup
        \"\"\"
        # OpenSSL configuration content
        config_content = \"\"\"openssl_conf = openssl_init

[openssl_init]
ssl_conf = ssl_sect

[ssl_sect]
system_default = system_default_sect

[system_default_sect]
CipherString = DEFAULT:@SECLEVEL=0
\"\"\"
        
        # Create temporary config file
        temp_dir = tempfile.gettempdir()
        config_path = os.path.join(temp_dir, f"openssl_legacy_{os.getpid()}.cnf")
        
        with open(config_path, 'w') as f:
            f.write(config_content)
        
        # Set environment variable BEFORE importing pyodbc or making connections
        os.environ['OPENSSL_CONF'] = config_path
        
        return config_path
    
    def _cleanup_openssl_patch(self) -> None:
        \"\"\"Clean up temporary OpenSSL configuration\"\"\"
        if self._openssl_patch_file and os.path.exists(self._openssl_patch_file):
            try:
                os.remove(self._openssl_patch_file)
                # Remove from environment
                if 'OPENSSL_CONF' in os.environ:
                    del os.environ['OPENSSL_CONF']
            except Exception:
                pass  # Silent cleanup failure
            finally:
                self._openssl_patch_file = None
    
    def connect(self) -> pyodbc.Connection:
        \"\"\"Enhanced connection with OpenSSL patch fallback\"\"\"
        if self._connection is None:
            conn_str: str = self._build_connection_string()
            
            # First attempt - normal connection
            try:
                self._connection = pyodbc.connect(conn_str)
                return self._connection
            except pyodbc.Error as e:
                # Check if this is the OpenSSL TLS issue on macOS
                if (self.config.auto_apply_openssl_patch and 
                    self._is_macos_openssl_issue(e)):
                    
                    print("🔧 Detected macOS OpenSSL TLS compatibility issue")
                    print("💡 Applying OpenSSL legacy patch (SECLEVEL=0)...")
                    
                    # Apply OpenSSL patch and retry
                    try:
                        self._openssl_patch_file = self._apply_openssl_legacy_patch()
                        print(f"✅ OpenSSL patch applied: {self._openssl_patch_file}")
                        
                        # Retry connection with patch
                        self._connection = pyodbc.connect(conn_str)
                        print("✅ Connection successful with OpenSSL patch!")
                        return self._connection
                        
                    except pyodbc.Error as patch_error:
                        # Clean up patch file on failure
                        self._cleanup_openssl_patch()
                        raise Exception(f"Connection failed even with OpenSSL patch: {patch_error}")
                
                # Re-raise original error if not OpenSSL issue or patch disabled
                raise Exception(self._build_error_message(e))
        
        return self._connection
    
    def close(self) -> None:
        \"\"\"Enhanced close with OpenSSL patch cleanup\"\"\"
        if self._connection is not None:
            try:
                self._connection.close()
            except pyodbc.Error as e:
                print(f"Warning: Error closing connection: {e}")
            finally:
                self._connection = None
        
        # Clean up OpenSSL patch
        self._cleanup_openssl_patch()
```

### **2. Configuration Enhancement**

**Location**: [config/sqlserver_config.py](config/sqlserver_config.py)

```python
@dataclass
class SQLServerConfig:
    # ... existing fields ...
    auto_apply_openssl_patch: bool = True  # Automatically apply OpenSSL patch on macOS TLS errors
    
    @classmethod
    def from_environment(cls) -> 'SQLServerConfig':
        # ... existing code ...
        
        # OpenSSL patch configuration
        auto_patch = os.getenv('SQLSERVER_AUTO_OPENSSL_PATCH', 'true').lower() == 'true'
        
        return cls(
            # ... existing parameters ...
            auto_apply_openssl_patch=auto_patch
        )
```

### **3. Test Script Enhancement**

**Location**: [test_sqlserver_connection.py](test_sqlserver_connection.py)

```python
def test_openssl_environment():
    \"\"\"Test OpenSSL version and macOS compatibility\"\"\"
    print("\\n🔍 Testing OpenSSL Environment...")
    
    # Check platform
    print(f"Platform: {sys.platform}")
    if sys.platform == "darwin":
        print("✅ macOS detected - OpenSSL patch may be needed")
    
    # Check OpenSSL version if available
    try:
        import ssl
        print(f"SSL Module: {ssl.OPENSSL_VERSION}")
        
        # Check if OpenSSL 3.0+
        version = ssl.OPENSSL_VERSION_NUMBER
        if version >= 0x30000000:  # OpenSSL 3.0.0
            print("⚠️  OpenSSL 3.0+ detected - may need SECLEVEL=0 for legacy SQL Server")
        else:
            print("✅ OpenSSL version should be compatible")
            
    except Exception as e:
        print(f"Could not determine OpenSSL version: {e}")
    
    # Check current OPENSSL_CONF setting
    current_conf = os.getenv('OPENSSL_CONF')
    if current_conf:
        print(f"Current OPENSSL_CONF: {current_conf}")
    else:
        print("No custom OpenSSL configuration active")

def test_connection_with_patch_modes(config: SQLServerConfig):
    \"\"\"Test connection with different patch modes\"\"\"
    print("\\n🧪 Testing Connection Modes...")
    
    # Test 1: Without patch
    print("\\n1️⃣ Testing without OpenSSL patch...")
    config_no_patch = SQLServerConfig(
        **{k: v for k, v in config.__dict__.items()},
        auto_apply_openssl_patch=False  # Disable patch
    )
    
    sql_conn_no_patch = SQLServerConnection(config_no_patch)
    try:
        conn = sql_conn_no_patch.connect()
        print("✅ Connection successful without patch")
        sql_conn_no_patch.close()
        return True  # No patch needed
    except Exception as e:
        print(f"❌ Connection failed without patch: {str(e)[:100]}...")
    
    # Test 2: With automatic patch
    print("\\n2️⃣ Testing with automatic OpenSSL patch...")
    sql_conn_patch = SQLServerConnection(config)  # auto_apply_openssl_patch=True by default
    try:
        conn = sql_conn_patch.connect()
        print("✅ Connection successful with OpenSSL patch!")
        sql_conn_patch.close()
        return True
    except Exception as e:
        print(f"❌ Connection failed even with patch: {str(e)[:100]}...")
    
    return False

# Update main() function to include OpenSSL testing
def main():
    # ... existing code ...
    
    # Add OpenSSL environment testing
    test_openssl_environment()
    
    # ... existing configuration loading ...
    
    # Enhanced connection testing with patch modes
    success = test_connection_with_patch_modes(config)
    
    # ... rest of main() ...
```

### **4. Configuration Script Update**

**Location**: [configure_sql_connection_info.sh](configure_sql_connection_info.sh)

```bash
# Add after existing environment variables
if [ -z "$SQLSERVER_AUTO_OPENSSL_PATCH" ]; then 
    SQLSERVER_AUTO_OPENSSL_PATCH="true"
fi

# Update the config file output section
cat > "$conf_file" << EOF
export SQLSERVER_HOST="$SQLSERVER_HOST"
export SQLSERVER_PORT="$SQLSERVER_PORT"
export SQLSERVER_DATABASE="$SQLSERVER_DATABASE"
export SQLSERVER_USER="$SQLSERVER_USER"
export SQLSERVER_PASSWORD="$SQLSERVER_PASSWORD"
export SQLSERVER_ENCRYPT="$SQLSERVER_ENCRYPT"
export SQLSERVER_TRUST_CERT="$SQLSERVER_TRUST_CERT"
export SQLSERVER_AUTO_OPENSSL_PATCH="$SQLSERVER_AUTO_OPENSSL_PATCH"
EOF
```

## Implementation Timeline

### 🚀 **Phase 1 - Core Integration (Day 1)**
- ✅ Add OpenSSL patch methods to SQLServerConnection
- ✅ Implement automatic patch detection and application  
- ✅ Add configuration controls for patch behavior

### 📋 **Phase 2 - Testing & Validation (Day 1)**  
- ✅ Enhance test script with OpenSSL diagnostics
- ✅ Test both patch and non-patch modes
- ✅ Validate cleanup and error handling

### 📓 **Phase 3 - Documentation & Examples (Day 2)**
- ✅ Update notebook with patch examples
- ✅ Add troubleshooting documentation
- ✅ Update configuration script

## Success Criteria

✅ **Primary Goal**: SQL Server connection succeeds on macOS with OpenSSL 3.0  
✅ **Automatic Handling**: Patch applied automatically on TCP Provider 10054 error  
✅ **Clean Fallback**: Graceful handling when patch fails  
✅ **Resource Management**: Proper cleanup of temporary configuration files  
✅ **Backward Compatibility**: Works on systems where patch is not needed  

## Risk Mitigation

🚨 **Risk**: OpenSSL patch affects other system connections  
🛡️ **Mitigation**: Use process-specific temporary config files, automatic cleanup  

🚨 **Risk**: Patch doesn't solve underlying issue  
🛡️ **Mitigation**: Fallback error reporting, alternative driver detection  

🚨 **Risk**: Security implications of SECLEVEL=0  
🛡️ **Mitigation**: Temporary files only, process-local scope, clear documentation  

## Notes

- **Scope**: Targets TCP Provider Error 10054 on macOS specifically
- **Temporary**: OpenSSL patch is process-local and temporary
- **Fallback**: Maintains current error handling for non-OpenSSL issues  
- **Security**: Users should understand SECLEVEL=0 implications for production use

---
*Generated on February 12, 2026 for OpenSSL 3.0 TLS compatibility fix*