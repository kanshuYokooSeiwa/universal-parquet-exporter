# SQL to Parquet Pandas Wrapper

This is a lightweight **pandas wrapper** designed to simplify the process of extracting data from relational databases (MySQL, SQL Server, and more) and converting it to Apache Parquet format. Rather than being a standalone library, this tool provides a convenient interface around pandas functionality to streamline SQL-to-Parquet workflows.

## What This Is

This wrapper provides a **simplified interface** for:
- Connecting to multiple database types (MySQL, SQL Server) with minimal configuration
- Executing SQL queries and automatically handling results as pandas-compatible data structures
- Converting query results to Apache Parquet format using pandas' built-in capabilities
- Managing database connections and error handling

## Key Benefits

- **Multi-Database Support**: Works with MySQL, SQL Server (via pyodbc), and any DB-API 2.0 compliant database
- **Pandas-based**: Leverages pandas' robust DataFrame functionality and parquet support
- **Simplified Workflow**: Reduces boilerplate code for common SQL-to-Parquet operations  
- **Type Safety**: Full type annotations for better development experience
- **Flexible Data Format**: Handles data as dictionaries with meaningful column names (not generic column_0, column_1, etc.)
- **Easy Integration**: Drop-in solution for data pipelines requiring database data extraction

## Prerequisites

### MySQL Server
This library requires access to a MySQL database server. **MySQL must be installed on your local computer if you plan to run tests** or develop with this library.

**Installation Options:**
- **macOS**: Install via Homebrew: `brew install mysql`
- **Ubuntu/Debian**: `sudo apt-get install mysql-server`
- **Windows**: Download from [MySQL official website](https://dev.mysql.com/downloads/mysql/)
- **Docker**: `docker run --name mysql-server -e MYSQL_ROOT_PASSWORD=password -p 3306:3306 -d mysql:8.0`

**Important Database Connection Requirements:**
- **Connection Information**: You must have valid connection credentials (host, user, password, database name)
- **Network Access**: Ensure your computer can connect to the target MySQL server
- **Firewall Settings**: Verify that the MySQL server allows connections from your computer's IP address
- **Database Permissions**: The user account must have appropriate privileges (SELECT for queries, CREATE/INSERT for tests)

**Before using this library**, test your database connection using a MySQL client:
```bash
mysql -h your_host -u your_username -p your_database
```

### SQL Server (Microsoft SQL Server) with pyodbc

This library supports Microsoft SQL Server connections using the **pyodbc** driver. Follow the platform-specific instructions below to set up ODBC drivers.

#### macOS

**Step 1: Install unixODBC**
```bash
brew update
brew install unixodbc
```

**Step 2: Add Microsoft's tap and install SQL Server ODBC driver**
```bash
brew tap microsoft/mssql-release https://github.com/Microsoft/homebrew-mssql-release
brew update
ACCEPT_EULA=Y brew install msodbcsql18 mssql-tools18
```

**Step 3: Verify installation**
```bash
# List installed ODBC drivers
odbcinst -q -d

# Should show: [ODBC Driver 18 for SQL Server]
```

**Step 4: Install Python pyodbc package**
```bash
pip install pyodbc
```

#### Windows

**Step 1: Download and install Microsoft ODBC Driver**
- Visit: [Microsoft ODBC Driver for SQL Server](https://learn.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server)
- Download **ODBC Driver 18 for SQL Server** (or latest version)
- Run the installer (`.msi` file) and follow the installation wizard
- Accept the license agreement and complete installation

**Step 2: Verify installation**
- Open **ODBC Data Sources (64-bit)** from Start Menu
- Go to the **Drivers** tab
- Look for "ODBC Driver 18 for SQL Server" in the list

**Step 3: Install Python pyodbc package**
```cmd
pip install pyodbc
```

**Alternative: Using Windows Package Manager (winget)**
```cmd
winget install Microsoft.ODBC.18
```

#### Linux (Ubuntu/Debian)

**Step 1: Install unixODBC**
```bash
sudo apt-get update
sudo apt-get install -y unixodbc-dev unixodbc
```

**Step 2: Add Microsoft repository and install ODBC driver**
```bash
# Add Microsoft repository (Ubuntu 22.04 example - adjust version as needed)
curl https://packages.microsoft.com/keys/microsoft.asc | sudo tee /etc/apt/trusted.gpg.d/microsoft.asc
curl https://packages.microsoft.com/config/ubuntu/22.04/prod.list | sudo tee /etc/apt/sources.list.d/mssql-release.list

# Update and install
sudo apt-get update
sudo ACCEPT_EULA=Y apt-get install -y msodbcsql18 mssql-tools18

# Optional: Add SQL Server tools to PATH
echo 'export PATH="$PATH:/opt/mssql-tools18/bin"' >> ~/.bashrc
source ~/.bashrc
```

**For other Linux distributions:**
- **Red Hat/CentOS/Fedora**: See [Microsoft's RHEL installation guide](https://learn.microsoft.com/en-us/sql/connect/odbc/linux-mac/installing-the-microsoft-odbc-driver-for-sql-server)
- **SUSE**: See [Microsoft's SUSE installation guide](https://learn.microsoft.com/en-us/sql/connect/odbc/linux-mac/installing-the-microsoft-odbc-driver-for-sql-server)

**Step 3: Verify installation**
```bash
# List installed ODBC drivers
odbcinst -q -d

# Should show: [ODBC Driver 18 for SQL Server]
```

**Step 4: Install Python pyodbc package**
```bash
pip install pyodbc
```

#### Testing SQL Server Connection

After installing the ODBC driver and pyodbc, test your connection:

```python
import pyodbc

# List available drivers
drivers = [driver for driver in pyodbc.drivers()]
print("Available ODBC drivers:", drivers)

# Test connection (adjust credentials)
conn_str = (
    "DRIVER={ODBC Driver 18 for SQL Server};"
    "SERVER=your_server,1433;"
    "DATABASE=your_database;"
    "UID=your_username;"
    "PWD=your_password;"
    "Encrypt=yes;"
    "TrustServerCertificate=yes;"
)

try:
    conn = pyodbc.connect(conn_str)
    print("✓ SQL Server connection successful!")
    conn.close()
except Exception as e:
    print(f"✗ Connection failed: {e}")
```

#### Common Issues and Solutions

**Issue: "Data source name not found"**
- Verify driver installation: `odbcinst -q -d` (Linux/macOS) or check ODBC Data Sources (Windows)
- Ensure driver name matches exactly: `ODBC Driver 18 for SQL Server`

**Issue: "SSL Provider: The certificate chain was issued by an authority that is not trusted"**
- Add `TrustServerCertificate=yes` to connection string (dev/test environments only)
- For production, use proper SSL certificates

**Issue: "Login timeout expired"**
- Check server hostname/IP and port (default: 1433)
- Verify firewall rules allow SQL Server connections
- Ensure SQL Server is configured to accept TCP/IP connections

**Issue: "Login failed for user"**
- Verify username and password
- Check SQL Server authentication mode (Windows Auth vs SQL Server Auth)
- Ensure user has appropriate database permissions

### Python Dependencies
To install the required Python dependencies, run:

```bash
pip install -r requirements.txt
```

For SQL Server support, also install:
```bash
pip install pyodbc
```

## Usage

### Connecting to MySQL

To connect to a MySQL database, create an instance of the `MySQLConnection` class from the `mysql_connection` module and provide the necessary configuration.

### Executing Queries

Use the `QueryExecutor` class from the `query_executor` module to execute your SQL queries. Pass the SQL query as a parameter to the `execute_query` method.

### Exporting to Parquet

To save the results of your query in Parquet format, use the `ParquetWriter` class from the `parquet_writer` module. Call the `write_to_parquet` method with the query results.

## Quick Start Example

```python
from src.database.mysql_connection import MySQLConnection
from src.query.query_executor import QueryExecutor
from src.export.parquet_writer import ParquetWriter
from config.database_config import DatabaseConfig

# Create database configuration
config = DatabaseConfig(
    host="localhost",
    user="your_username",
    password="your_password",
    database="your_database"
)

# Connect to MySQL
mysql_conn = MySQLConnection(config)
connection = mysql_conn.connect()

# Execute query and get results as list of dictionaries
# (This ensures meaningful column names in the parquet file)
query_executor = QueryExecutor(connection)
results = query_executor.execute_query("SELECT id, name, email FROM users")
# Results format: [{'id': 1, 'name': 'John', 'email': 'john@example.com'}, ...]

# Convert to Parquet using pandas under the hood
parquet_writer = ParquetWriter()
parquet_writer.write_to_parquet(results, 'users.parquet')
# Output parquet file will have columns: id, name, email (not column_0, column_1, etc.)

# Clean up
mysql_conn.close()
```

### Data Format

The wrapper expects data in **dictionary format** for meaningful column names:
- ✅ **Correct**: `[{'id': 1, 'name': 'John'}, {'id': 2, 'name': 'Jane'}]`
- ❌ **Avoid**: `[(1, 'John'), (2, 'Jane')]` (results in column_0, column_1)

## SQL Server Example

```python
from src.database.sqlserver_connection import SQLServerConnection
from src.query.query_executor import QueryExecutor
from src.export.parquet_writer import ParquetWriter
from config.sqlserver_config import SQLServerConfig

# Create SQL Server configuration
config = SQLServerConfig(
    host="your_server",
    port=1433,
    database="your_database",
    user="your_username",
    password="your_password",
    encrypt="yes",
    trust_server_certificate="yes"  # Use "no" for production with valid certificates
)

# Connect to SQL Server
sql_conn = SQLServerConnection(config)
connection = sql_conn.connect()

# Execute query and get results as list of dictionaries
query_executor = QueryExecutor(connection)
results = query_executor.execute_query("SELECT TOP 10 name, database_id FROM sys.databases")
# Results format: [{'name': 'master', 'database_id': 1}, ...]

# Convert to Parquet
parquet_writer = ParquetWriter()
parquet_writer.write_to_parquet(results, 'databases.parquet')

# Clean up
sql_conn.close()
```

## Integration Examples

The library includes comprehensive integration examples that demonstrate real-world usage patterns with test databases. These examples show how to connect to MySQL and SQL Server, execute various types of queries, and export results to organized Parquet files.

### Prerequisites for Examples

Before running the integration examples, ensure you have:

1. **MySQL Server**: Running locally with the test database set up (see [Step-by-Step Database Setup](#step-by-step-database-setup))
2. **Test Database**: Database `testdb` with user `testuser` and sample data
3. **Python Dependencies**: All requirements installed (`pip install -r requirements.txt`)

### Basic Integration Example

**File**: `examples/basic_integration_example.py`

**Purpose**: Demonstrates fundamental library usage patterns with simple queries and exports.

**What it does**:
- Connects to the test MySQL database
- Executes simple SELECT queries  
- Exports data to Parquet files in a `parquetFiles/` directory
- Shows proper connection management and error handling

**Usage**:
```bash
# From the project root directory
python examples/basic_integration_example.py
```

**Generated Files**:
- `parquetFiles/users.parquet` - All user records
- `parquetFiles/orders.parquet` - All order records
- `parquetFiles/high_value_customers.parquet` - Users with orders > $100

### SQL Server Basic Integration Example

**File**: `examples/sqlserver_basic_example.py`

**Purpose**: Demonstrates SQL Server connectivity and basic query patterns using pyodbc.

**What it does**:
- Connects to SQL Server using ODBC Driver 18
- Queries system databases and tables
- Exports server properties and metadata
- Shows proper pyodbc connection management

**Usage**:
```bash
# Set environment variables (optional)
export MSSQL_HOST="localhost"
export MSSQL_PORT="1433"
export MSSQL_DATABASE="tempdb"
export MSSQL_USER="sa"
export MSSQL_PASSWORD="YourStrong!Passw0rd"

# From the project root directory
python examples/sqlserver_basic_example.py
```

**Generated Files**:
- `parquetFiles/sqlserver/system_databases.parquet` - Database information
- `parquetFiles/sqlserver/system_tables.parquet` - Table metadata
- `parquetFiles/sqlserver/server_properties.parquet` - Server configuration

### SQL Server Advanced Integration Example

**File**: `examples/sqlserver_advanced_example.py`

**Purpose**: Demonstrates advanced SQL Server analytics with complex queries.

**What it does**:
- Database statistics with aggregations and JOINs
- Schema analysis using window functions and CTEs
- Index usage and performance metrics
- Active session monitoring
- Creates timestamped export directories

**Usage**:
```bash
# From the project root directory
python examples/sqlserver_advanced_example.py
```

**Generated Analytics Files**:
- `database_statistics.parquet` - Database size and configuration analysis
- `schema_analysis.parquet` - Table/object analysis with rankings
- `index_analysis.parquet` - Index usage and performance metrics
- `active_sessions.parquet` - Current database sessions
- `export_summary.parquet` - Export metadata

### Advanced Integration Example (MySQL)

**File**: `examples/advanced_integration_example.py`

**Purpose**: Showcases complex analytics and business intelligence scenarios.

**What it does**:
- Validates database connectivity before processing
- Executes complex analytical queries (JOINs, aggregations, window functions)
- Creates timestamped export directories for organized data management
- Generates comprehensive business analytics reports
- Provides detailed success/failure reporting

**Usage**:
```bash
# From the project root directory
python examples/advanced_integration_example.py
```

**Generated Analytics Files**:
- `user_order_summary.parquet` - Customer purchase behavior analysis
- `product_performance.parquet` - Product sales and revenue metrics
- `age_demographic_analysis.parquet` - Customer demographic insights  
- `high_value_transactions.parquet` - Premium order analysis with rankings
- `customer_lifetime_value.parquet` - Customer segmentation and LTV analysis
- `export_summary.parquet` - Processing metadata and success metrics

### Expected Output Structure

After running the examples, you'll have the following directory structure:

```
mysql-parquet-lib/
├── parquetFiles/
│   ├── users.parquet                           # MySQL basic example
│   ├── orders.parquet
│   ├── high_value_customers.parquet
│   ├── sqlserver/                              # SQL Server basic example
│   │   ├── system_databases.parquet
│   │   ├── system_tables.parquet
│   │   └── server_properties.parquet
│   ├── advanced_export_YYYYMMDD_HHMMSS/       # MySQL advanced example
│   │   ├── user_order_summary.parquet
│   │   ├── product_performance.parquet
│   │   ├── age_demographic_analysis.parquet
│   │   ├── high_value_transactions.parquet
│   │   ├── customer_lifetime_value.parquet
│   │   └── export_summary.parquet
│   └── sqlserver/export_YYYYMMDD_HHMMSS/      # SQL Server advanced example
│       ├── database_statistics.parquet
│       ├── schema_analysis.parquet
│       ├── index_analysis.parquet
│       ├── active_sessions.parquet
│       └── export_summary.parquet
```
│       ├── product_performance.parquet
│       ├── age_demographic_analysis.parquet
│       ├── high_value_transactions.parquet
│       ├── customer_lifetime_value.parquet
│       └── export_summary.parquet
```

### Using the Generated Parquet Files

The exported Parquet files can be analyzed with various tools:

**With Pandas**:
```python
import pandas as pd

# Load exported data
users_df = pd.read_parquet('parquetFiles/users.parquet')
orders_df = pd.read_parquet('parquetFiles/orders.parquet')

# Analyze the data
print(users_df.info())
print(orders_df.describe())
```

**With DuckDB (SQL Analytics)**:
```python
import duckdb

# Query parquet files directly with SQL
conn = duckdb.connect()
result = conn.execute("""
    SELECT * FROM 'parquetFiles/advanced_export_*/user_order_summary.parquet'
    WHERE total_spent > 500
    ORDER BY total_spent DESC
""").fetchall()
```

### Troubleshooting Examples

**Database Connection Issues**:
- Verify MySQL is running: `brew services list | grep mysql`
- Test connection: `mysql -h localhost -u testuser -p testdb`
- Check that test tables exist and have data

**Import Path Issues**:
- Always run examples from the project root directory
- Ensure the project structure is intact

**Permission Errors**:
- Verify `testuser` has proper privileges on `testdb`
- Check that the `parquetFiles/` directory can be created

**SQL Server Connection Issues**:
- Verify ODBC driver is installed: `odbcinst -q -d` (macOS/Linux) or check ODBC Data Sources (Windows)
- Test SQL Server connectivity and firewall rules
- Check authentication mode (SQL Server Auth vs Windows Auth)
- Verify `TrustServerCertificate` setting matches your environment

For detailed examples documentation, see [`examples/README.md`](examples/README.md).

## Running Tests

This project includes comprehensive unit tests with proper typing. 

### Test Database Setup

**Important**: Most tests use mocking and don't require a real database connection. However, if you want to test with a real MySQL database, you'll need:

1. **MySQL Server Running**: Ensure MySQL is installed and running on your local machine
2. **Test Database**: Create a test database (optional, as tests use mocked connections)
3. **Connection Credentials**: The tests use mock connections with these sample credentials:
   - Host: `localhost`
   - User: `testuser`
   - Password: `testpass`
   - Database: `testdb`

**Note**: The unit tests are designed to work without a real database connection using Python's `unittest.mock` library. They test the code logic and behavior without requiring actual MySQL connectivity.

### Running Tests

To run the tests:

### Run All Tests

```bash
# From the project root directory
python -m pytest tests/ -v
```

### Run Individual Test Files

```bash
# Test MySQL connection
python -m pytest tests/test_mysql_connection.py -v

# Test query executor (mock-based unit tests)
python -m pytest tests/test_query_executor.py -v

# Test query executor with real database (integration tests)
python -m pytest tests/test_query_executor_realDB.py -v

# Test both query executor files
python -m pytest tests/test_query_executor*.py -v

# Test parquet writer
python -m pytest tests/test_parquet_writer.py -v

# Test database config
python -m pytest tests/test_database_config.py -v
```

### Run Tests with Coverage

```bash
# Install coverage if not already installed
pip install coverage pytest

# Run tests with coverage
coverage run -m pytest tests/
coverage report -m
coverage html  # Generate HTML coverage report
```

### Run Tests Using unittest

Alternatively, you can run tests using Python's built-in unittest module:

```bash
# Run all tests
python -m unittest discover tests/ -v

# Run individual test files
python -m unittest tests.test_mysql_connection -v
python -m unittest tests.test_query_executor -v
python -m unittest tests.test_parquet_writer -v
python -m unittest tests.test_database_config -v
```

## Development

### Test Requirements

For development and testing, install additional dependencies:

```bash
pip install pytest coverage
```

### Setting Up a Test Database (Optional)

If you want to test with a real MySQL database instead of mocked connections:

1. **Install MySQL** on your local machine (see Prerequisites section)
2. **Start MySQL service**:
   ```bash
   # macOS (if installed via Homebrew)
   brew services start mysql
   
   # Linux
   sudo systemctl start mysql
   
   # Or using Docker
   docker run --name test-mysql -e MYSQL_ROOT_PASSWORD=password -p 3306:3306 -d mysql:8.0
   ```
3. **Create a test database and user**:

#### Step-by-Step Database Setup

**Step 1: Connect to MySQL as root**
```bash
mysql -u root -p
```
Enter your root password when prompted.

**Step 2: Create the database testdb**
```sql
CREATE DATABASE testdb;
```
This creates a new database named `testdb` for testing purposes.

**Step 3: Create the user testuser with the password testpass**
```sql
CREATE USER 'testuser'@'localhost' IDENTIFIED BY 'testpass';
```
This command creates a user that can only connect from your local machine (localhost).

**Step 4: Grant all privileges on testdb to testuser**
```sql
GRANT ALL PRIVILEGES ON testdb.* TO 'testuser'@'localhost';
```
This command gives your new user full control (create, read, update, delete, etc.) over only the testdb database.

**Step 5: Apply the changes**
```sql
FLUSH PRIVILEGES;
```
This command reloads the permission tables to ensure your new user's privileges are active immediately.

**Step 6: Exit MySQL**
```sql
EXIT;
```

**Step 7: Test the new connection**
```bash
mysql -h localhost -u testuser -p testdb
```
Enter `testpass` when prompted. If successful, you should be connected to the testdb database as testuser.

**Step 8: Create test tables and insert sample data**
```sql
-- Ensure you're using the testdb database
USE testdb;

-- Create test tables
CREATE TABLE users (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    age INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE orders (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT,
    product_name VARCHAR(100) NOT NULL,
    quantity INT DEFAULT 1,
    price DECIMAL(10,2),
    order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Insert test data
INSERT INTO users (name, email, age) VALUES
('John Doe', 'john@example.com', 30),
('Jane Smith', 'jane@example.com', 25),
('Bob Johnson', 'bob@example.com', 35),
('Alice Brown', 'alice@example.com', 28);

INSERT INTO orders (user_id, product_name, quantity, price) VALUES
(1, 'Laptop', 1, 999.99),
(1, 'Mouse', 2, 25.50),
(2, 'Keyboard', 1, 75.00),
(3, 'Monitor', 1, 299.99),
(4, 'Headphones', 1, 150.00);
```

**Step 9: Exit MySQL**
```sql
EXIT;
```

**Note**: The current unit tests use mocking and don't require a real database connection. This setup is only needed if you plan to write integration tests or test with real data. The real database integration tests are available in `test_query_executor_realDB.py`.

### Code Quality

All code follows strict typing conventions:
- Function parameters have type hints
- Return types are annotated
- Variables within functions are explicitly typed
- All necessary types are imported from the `typing` module

## Architecture

This wrapper is built around core components that support multiple database types:

### Database Connections

#### 1. MySQLConnection (`src/database/mysql_connection.py`)
- Handles MySQL database connectivity
- Wraps standard MySQL connection management
- Configuration via `DatabaseConfig`

#### 2. SQLServerConnection (`src/database/sqlserver_connection.py`)
- Handles Microsoft SQL Server connectivity using pyodbc
- ODBC Driver 18 support with SSL/TLS configuration
- Configuration via `SQLServerConfig`
- Context manager support for automatic cleanup

### Query Execution

#### 3. QueryExecutor (`src/query/query_executor.py`) 
- **Database-agnostic**: Works with any DB-API 2.0 compliant connection
- Executes SQL queries and returns structured data
- Converts results to dictionary format for meaningful column names
- Uses `cursor.description` to extract column metadata
- Compatible with both MySQL and SQL Server connections

### Data Export

#### 4. ParquetWriter (`src/export/parquet_writer.py`)
- **Pandas Wrapper**: Uses `pd.DataFrame.to_parquet()` internally
- Accepts data as `List[Dict[str, Any]]` to preserve column names
- Leverages pandas' optimized parquet writing capabilities
- Database-agnostic: works with data from any source

## Why This Wrapper?

Instead of manually writing:
```python
import pandas as pd
import mysql.connector

# Manual approach - more boilerplate
conn = mysql.connector.connect(host=..., user=..., password=..., database=...)
cursor = conn.cursor(dictionary=True)
cursor.execute("SELECT * FROM users")
data = cursor.fetchall()
df = pd.DataFrame(data)
df.to_parquet('output.parquet', index=False)
conn.close()
```

Use this wrapper:
```python
# Cleaner, reusable approach
config = DatabaseConfig(host=..., user=..., password=..., database=...)
mysql_conn = MySQLConnection(config)
connection = mysql_conn.connect()
query_executor = QueryExecutor(connection)
results = query_executor.execute_query("SELECT * FROM users")
ParquetWriter().write_to_parquet(results, 'output.parquet')
mysql_conn.close()
```

## Contributing

Contributions are welcome! Please ensure:
1. All new code includes proper type annotations
2. Unit tests are provided for new functionality  
3. Tests pass before submitting pull requests
4. Follow the existing code style and typing conventions
5. Maintain compatibility with pandas DataFrame operations

## License

This project is licensed under the MIT License. See the LICENSE file for more details.