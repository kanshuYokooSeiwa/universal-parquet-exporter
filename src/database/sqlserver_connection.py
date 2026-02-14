import pyodbc
import os
import sys
import tempfile
from typing import Optional, List, Dict, Any
from config.sqlserver_config import SQLServerConfig


class SQLServerConnection:
    """
    Manages connection to Microsoft SQL Server using pyodbc.
    
    This class provides a simple interface for connecting to SQL Server databases
    using ODBC drivers. It supports various connection parameters including encryption,
    certificate validation, and custom connection string options.
    """
    
    def __init__(self, config: SQLServerConfig) -> None:
        """
        Initialize SQL Server connection manager.
        
        Args:
            config: SQLServerConfig object containing connection parameters
        """
        self.config: SQLServerConfig = config
        self._connection: Optional[pyodbc.Connection] = None
        self._openssl_patch_file: Optional[str] = None  # Track patch file for cleanup
    
    def _detect_odbc_drivers(self) -> List[str]:
        """
        Detect available SQL Server ODBC drivers on the system.
        
        Returns:
            List of available drivers in preference order
        """
        try:
            all_drivers = pyodbc.drivers()
            sql_drivers = []
            
            # Preferred driver order for SQL Server 2022 compatibility
            preferred_drivers = [
                "ODBC Driver 18 for SQL Server",
                "ODBC Driver 17 for SQL Server", 
                "SQL Server Native Client 11.0",
                "SQL Server"
            ]
            
            for preferred in preferred_drivers:
                if preferred in all_drivers:
                    sql_drivers.append(preferred)
            
            # Add any other SQL Server drivers found
            for driver in all_drivers:
                if "SQL Server" in driver and driver not in sql_drivers:
                    sql_drivers.append(driver)
                    
            return sql_drivers
        except Exception:
            return []
    
    def _is_macos_openssl_issue(self, error: Exception) -> bool:
        """
        Detect if error is likely macOS OpenSSL 3.0 TLS compatibility issue.
        
        Args:
            error: Exception from connection attempt
            
        Returns:
            True if this appears to be the OpenSSL TLS issue
        """
        error_str = str(error).lower()
        return (
            sys.platform == "darwin" and  # macOS only
            "tcp provider" in error_str and 
            ("10054" in error_str or "0x2746" in error_str)
        )
    
    def _apply_openssl_legacy_patch(self) -> str:
        """
        Create temporary OpenSSL config to allow legacy TLS connections.
        
        This creates a process-specific OpenSSL configuration that sets
        SECLEVEL=0 to allow connections to SQL Servers with legacy TLS.
        
        Returns:
            Path to temporary config file for cleanup
        """
        # OpenSSL configuration content to allow legacy TLS
        config_content = """openssl_conf = openssl_init

[openssl_init]
ssl_conf = ssl_sect

[ssl_sect]
system_default = system_default_sect

[system_default_sect]
CipherString = DEFAULT:@SECLEVEL=0
"""
        
        # Create temporary config file with unique name
        temp_dir = tempfile.gettempdir()
        config_path = os.path.join(temp_dir, f"openssl_legacy_mysql_parquet_{os.getpid()}.cnf")
        
        with open(config_path, 'w') as f:
            f.write(config_content)
        
        # Set environment variable BEFORE making any ODBC connections
        os.environ['OPENSSL_CONF'] = config_path
        
        return config_path
    
    def _cleanup_openssl_patch(self) -> None:
        """
        Clean up temporary OpenSSL configuration.
        
        Removes the temporary config file and environment variable.
        """
        if self._openssl_patch_file and os.path.exists(self._openssl_patch_file):
            try:
                os.remove(self._openssl_patch_file)
                # Remove from environment if it points to our file
                if (os.environ.get('OPENSSL_CONF') == self._openssl_patch_file):
                    del os.environ['OPENSSL_CONF']
            except Exception:
                pass  # Silent cleanup failure
            finally:
                self._openssl_patch_file = None
    
    def _build_error_message(self, error: pyodbc.Error) -> str:
        """
        Build enhanced error message with troubleshooting suggestions.
        
        Args:
            error: The pyodbc error that occurred
            
        Returns:
            Enhanced error message with suggestions
        """
        error_msg = str(error).lower()
        suggestions = []
        
        if "tcp provider" in error_msg and ("10054" in error_msg or "10061" in error_msg):
            suggestions.extend([
                "Check if SQL Server is running and accepting TCP connections",
                "Verify firewall allows port 1433 (or your custom port)",
                "Try: nc -zv {0} 1433 to test network connectivity".format(self.config.host),
                "Consider setting encrypt=no and trust_server_certificate=yes for local connections"
            ])
            
            # Add macOS-specific suggestion
            if sys.platform == "darwin":
                suggestions.append("On macOS: This may be an OpenSSL 3.0 TLS compatibility issue")
                
        elif "login failed" in error_msg:
            suggestions.extend([
                "Verify username and password are correct",
                "Check if SQL Server authentication is enabled (not just Windows auth)",
                "Ensure user has permission to access the database"
            ])
        elif "cannot open database" in error_msg:
            suggestions.extend([
                "Verify database name is correct", 
                "Check if user has access to the specified database",
                "Try connecting without specifying database first"
            ])
        elif "ssl" in error_msg or "certificate" in error_msg:
            suggestions.extend([
                "Try setting encrypt=no for local connections",
                "Set trust_server_certificate=yes for self-signed certificates",
                "Check SSL/TLS configuration on SQL Server"
            ])
        
        suggestion_text = "\n".join([f"  - {s}" for s in suggestions]) if suggestions else ""
        error_details = f"Failed to connect to SQL Server: {error}"
        if suggestion_text:
            error_details += f"\n\nTroubleshooting suggestions:\n{suggestion_text}"
        
        return error_details
    
    def _build_connection_string(self) -> str:
        """
        Build optimized ODBC connection string for SQL Server 2022/macOS compatibility.
        
        Returns:
            Formatted connection string for pyodbc
        """
        # Use configured driver if available, otherwise detect best match
        available_drivers = self._detect_odbc_drivers()
        if self.config.driver in available_drivers:
            driver = self.config.driver  # Respect user's driver choice
        else:
            driver = available_drivers[0] if available_drivers else self.config.driver
        
        # Base connection string - separate SERVER from port for better compatibility
        parts = [
            f"DRIVER={{{driver}}}",
            f"SERVER={self.config.host}",  # No port in SERVER for better compatibility
            f"DATABASE={self.config.database}",
            f"UID={self.config.user}",
            f"PWD={self.config.password}",
        ]
        
        # SSL/Encryption settings optimized for local SQL Server 2022
        # Match sqlcmd default behavior for better compatibility
        if self.config.encrypt.lower() == "no":
            parts.extend([
                "Encrypt=no",
                "TrustServerCertificate=yes"  # Required even with Encrypt=no for modern SQL Server
            ])
        else:
            parts.extend([
                f"Encrypt={self.config.encrypt}",
                f"TrustServerCertificate={self.config.trust_server_certificate}"
            ])
        
        # MARS connection if enabled
        if self.config.mars.lower() == "yes":
            parts.append(f"MARS_Connection={self.config.mars}")
        
        # Timeout settings for better stability
        parts.extend([
            "Connection Timeout=30",
            "Login Timeout=30"
        ])
        
        # Port handling - add as separate parameter if not default
        if self.config.port != 1433:
            parts.append(f"Port={self.config.port}")
        
        # Add any extra connection string parameters
        if self.config.extra:
            for key, value in self.config.extra.items():
                parts.append(f"{key}={value}")
        
        return ";".join(parts)
    
    def connect(self) -> pyodbc.Connection:
        """
        Establish connection to SQL Server with enhanced error handling and OpenSSL patch fallback.
        
        Returns:
            pyodbc.Connection object
            
        Raises:
            Exception: If connection fails with detailed error information
        """
        if self._connection is None:
            conn_str: str = self._build_connection_string()
            
            # Check if OpenSSL configuration is already set externally
            if os.environ.get('OPENSSL_CONF'):
                # Skip auto-patching if OPENSSL_CONF is already configured
                # This is common when launched from a script that pre-configures OpenSSL
                try:
                    self._connection = pyodbc.connect(conn_str)
                    return self._connection
                except pyodbc.Error as e:
                    # Re-raise with enhanced error message
                    raise Exception(self._build_error_message(e))
            
            # First attempt - normal connection
            try:
                self._connection = pyodbc.connect(conn_str)
                return self._connection
                
            except pyodbc.Error as e:
                # Check if this is the macOS OpenSSL TLS issue and auto-patch is enabled
                if (getattr(self.config, 'auto_apply_openssl_patch', True) and 
                    self._is_macos_openssl_issue(e)):
                    
                    print("🔧 Detected macOS OpenSSL TLS compatibility issue (TCP Provider 10054)")
                    print("💡 Applying OpenSSL legacy patch (SECLEVEL=0) for SQL Server compatibility...")
                    
                    # Apply OpenSSL patch and retry
                    try:
                        self._openssl_patch_file = self._apply_openssl_legacy_patch()
                        print(f"✅ OpenSSL patch applied: {os.path.basename(self._openssl_patch_file)}")
                        
                        # Retry connection with patch
                        self._connection = pyodbc.connect(conn_str)
                        print("✅ Connection successful with OpenSSL legacy patch!")
                        return self._connection
                        
                    except pyodbc.Error as patch_error:
                        # Clean up patch file on failure
                        self._cleanup_openssl_patch()
                        
                        # Build combined error message
                        error_details = f"Connection failed even with OpenSSL patch: {patch_error}"
                        error_details += f"\n\nOriginal error: {e}"
                        error_details += "\n\nThis suggests the issue may not be OpenSSL TLS compatibility."
                        error_details += "\nPlease check SQL Server configuration and network connectivity."
                        
                        raise Exception(error_details)
                
                # Re-raise with enhanced error message if not OpenSSL issue or patch disabled
                raise Exception(self._build_error_message(e))
        
    def validate_connection_prerequisites(self) -> Dict[str, Any]:
        """
        Pre-flight validation before connection attempts.
        
        Returns:
            Dictionary with validation results and diagnostic info
        """
        results = {
            'odbc_drivers_available': [],
            'recommended_driver': None,
            'pyodbc_version': None,
            'config_valid': True,
            'config_issues': []
        }
        
        # Check pyodbc availability and version
        try:
            results['pyodbc_version'] = pyodbc.version
        except Exception as e:
            results['config_issues'].append(f"pyodbc error: {e}")
            results['config_valid'] = False
        
        # Check available ODBC drivers
        available_drivers = self._detect_odbc_drivers()
        results['odbc_drivers_available'] = available_drivers
        
        if available_drivers:
            results['recommended_driver'] = available_drivers[0]
        else:
            results['config_issues'].append("No SQL Server ODBC drivers found")
            results['config_valid'] = False
        
        # Basic config validation
        try:
            if not self.config.host:
                results['config_issues'].append("Host cannot be empty")
                results['config_valid'] = False
            if not self.config.user:
                results['config_issues'].append("Username cannot be empty") 
                results['config_valid'] = False
            if not self.config.password:
                results['config_issues'].append("Password cannot be empty")
                results['config_valid'] = False
        except Exception as e:
            results['config_issues'].append(f"Config validation error: {e}")
            results['config_valid'] = False
        
        return results
    
    def close(self) -> None:
        """
        Close the SQL Server connection and clean up OpenSSL patch if applied.
        """
        if self._connection is not None:
            try:
                self._connection.close()
            except pyodbc.Error as e:
                print(f"Warning: Error closing connection: {e}")
            finally:
                self._connection = None
        
        # Clean up OpenSSL patch
        self._cleanup_openssl_patch()
    
    def is_connected(self) -> bool:
        """
        Check if connection is active.
        
        Returns:
            True if connected, False otherwise
        """
        if self._connection is None:
            return False
        
        try:
            # Try to execute a simple query to check connection
            cursor = self._connection.cursor()
            cursor.execute("SELECT 1")
            cursor.close()
            return True
        except (pyodbc.Error, AttributeError):
            return False
    
    def __enter__(self) -> pyodbc.Connection:
        """
        Context manager entry.
        
        Returns:
            pyodbc.Connection object
        """
        return self.connect()
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """
        Context manager exit - closes connection.
        """
        self.close()
