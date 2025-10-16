from dataclasses import dataclass
from typing import Optional, Dict

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
    encrypt: str = "yes"
    trust_server_certificate: str = "yes"
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
