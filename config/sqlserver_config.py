import os
from dataclasses import dataclass
from typing import Optional, Dict, List

@dataclass
class SQLServerConfig:
    """
    Configuration for SQL Server database connection using pyodbc.
    
    Attributes:
        host: SQL Server hostname or IP address
        database: Database name to connect to
        user: Username for authentication
        password: Password for authentication
        port: SQL Server port (default: 1433)
        driver: ODBC driver name (default: "ODBC Driver 18 for SQL Server")
        encrypt: Enable encryption (yes/no, default: yes)
        trust_server_certificate: Trust server certificate without validation (yes/no, default: yes for dev/test)
        mars: Enable Multiple Active Result Sets (yes/no, default: no)
        extra: Additional connection string parameters as key-value pairs
    """
    host: str
    database: str
    user: str
    password: str
    port: int = 1433
    driver: str = "ODBC Driver 18 for SQL Server"
    encrypt: str = "no"  # Changed default to match sqlcmd behavior for local connections
    trust_server_certificate: str = "yes"  # Required for local SQL Server 2022
    mars: str = "no"
    extra: Optional[Dict[str, str]] = None
    
    def __post_init__(self) -> None:
        """Validate configuration parameters."""
        if not self.host:
            raise ValueError("Host cannot be empty")
        if not self.database:
            raise ValueError("Database cannot be empty")
        if not self.user:
            raise ValueError("User cannot be empty")
        if not self.password:
            raise ValueError("Password cannot be empty")
        if self.port <= 0 or self.port > 65535:
            raise ValueError(f"Invalid port number: {self.port}")
        if self.encrypt not in ["yes", "no"]:
            raise ValueError("Encrypt must be 'yes' or 'no'")
        if self.trust_server_certificate not in ["yes", "no"]:
            raise ValueError("TrustServerCertificate must be 'yes' or 'no'")
        if self.mars not in ["yes", "no"]:
            raise ValueError("MARS_Connection must be 'yes' or 'no'")
    
    @classmethod
    def from_environment(cls) -> 'SQLServerConfig':
        """
        Create configuration from .confSQLConnection environment variables.
        
        This method reads SQL Server connection parameters from environment
        variables set by the configure_sql_connection_info.sh script.
        
        Returns:
            SQLServerConfig instance with values from environment
            
        Raises:
            ValueError: If required environment variables are missing
        """
        # Required variables
        host = os.getenv('SQLSERVER_HOST')
        database = os.getenv('SQLSERVER_DATABASE') 
        user = os.getenv('SQLSERVER_USER')
        password = os.getenv('SQLSERVER_PASSWORD')
        
        # Check for required variables
        missing_vars = []
        if not host:
            missing_vars.append('SQLSERVER_HOST')
        if not database:
            missing_vars.append('SQLSERVER_DATABASE')
        if not user:
            missing_vars.append('SQLSERVER_USER')
        if not password:
            missing_vars.append('SQLSERVER_PASSWORD')
        
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
        
        # Optional variables with defaults
        port = int(os.getenv('SQLSERVER_PORT', '1433'))
        driver = os.getenv('SQLSERVER_DRIVER', 'ODBC Driver 18 for SQL Server')
        encrypt = os.getenv('SQLSERVER_ENCRYPT', 'no')  # Match sqlcmd default
        trust_cert = os.getenv('SQLSERVER_TRUST_CERT', 'yes')  # Required for local connections
        
        return cls(
            host=host,
            port=port,
            database=database, 
            user=user,
            password=password,
            driver=driver,
            encrypt=encrypt,
            trust_server_certificate=trust_cert
        )
    
    def validate(self) -> List[str]:
        """
        Validate configuration and return list of issues.
        
        Returns:
            List of validation error messages (empty if valid)
        """
        issues = []
        
        if not self.host.strip():
            issues.append("Host cannot be empty")
        if not self.database.strip():
            issues.append("Database name cannot be empty")
        if not self.user.strip():
            issues.append("Username cannot be empty")
        if not self.password.strip():
            issues.append("Password cannot be empty")
        
        if self.port <= 0 or self.port > 65535:
            issues.append(f"Invalid port number: {self.port}")
        
        if self.encrypt.lower() not in ["yes", "no"]:
            issues.append("Encrypt must be 'yes' or 'no'")
        
        if self.trust_server_certificate.lower() not in ["yes", "no"]:
            issues.append("TrustServerCertificate must be 'yes' or 'no'")
        
        if self.mars.lower() not in ["yes", "no"]:
            issues.append("MARS_Connection must be 'yes' or 'no'")
        
        return issues
