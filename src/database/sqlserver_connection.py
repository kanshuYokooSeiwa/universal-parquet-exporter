import pyodbc
from typing import Optional
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
    
    def _build_connection_string(self) -> str:
        """
        Build ODBC connection string from configuration.
        
        Returns:
            Formatted connection string for pyodbc
        """
        parts = [
            f"DRIVER={{{self.config.driver}}}",
            f"SERVER={self.config.host},{self.config.port}",
            f"DATABASE={self.config.database}",
            f"UID={self.config.user}",
            f"PWD={self.config.password}",
            f"Encrypt={self.config.encrypt}",
            f"TrustServerCertificate={self.config.trust_server_certificate}",
            f"MARS_Connection={self.config.mars}",
        ]
        
        # Add any extra connection string parameters
        if self.config.extra:
            for key, value in self.config.extra.items():
                parts.append(f"{key}={value}")
        
        return ";".join(parts)
    
    def connect(self) -> pyodbc.Connection:
        """
        Establish connection to SQL Server.
        
        Returns:
            pyodbc.Connection object
            
        Raises:
            pyodbc.Error: If connection fails
        """
        if self._connection is None:
            conn_str: str = self._build_connection_string()
            try:
                self._connection = pyodbc.connect(conn_str)
            except pyodbc.Error as e:
                raise Exception(f"Failed to connect to SQL Server: {e}")
        
        return self._connection
    
    def close(self) -> None:
        """
        Close the SQL Server connection if it's open.
        """
        if self._connection is not None:
            try:
                self._connection.close()
            except pyodbc.Error as e:
                print(f"Warning: Error closing connection: {e}")
            finally:
                self._connection = None
    
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
