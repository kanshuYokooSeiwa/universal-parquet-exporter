# Integration Examples

This directory contains practical examples demonstrating how to use the SQL to Parquet pandas wrapper with real database connections (MySQL and SQL Server) and data export scenarios.

## Prerequisites

### For MySQL Examples

Before running MySQL examples, ensure you have:

1. **MySQL Server**: Running locally or accessible remotely
2. **Test Database**: Set up according to the main README.md instructions:
   - Database: `testdb`
   - User: `testuser` 
   - Password: `testpass`
   - Tables: `users` and `orders` with sample data
3. **Python Dependencies**: Install via `pip install -r requirements.txt`

### For SQL Server Examples

Before running SQL Server examples, ensure you have:

1. **SQL Server Instance**: Running locally or accessible remotely
2. **ODBC Driver 18**: Installed for SQL Server (see main README.md for platform-specific instructions)
3. **Valid Credentials**: SQL Server authentication credentials or Windows authentication
4. **Python Dependencies**: Install pyodbc via `pip install pyodbc`

## Examples Overview

### MySQL Examples

#### 1. Basic Integration Example (`basic_integration_example.py`)

**Purpose**: Demonstrates fundamental library usage patterns

**What it does**:
- Connects to the test MySQL database
- Executes simple SELECT queries
- Exports data to Parquet files in a `parquetFiles/` directory
- Shows proper connection management and error handling

**Exports created**:
- `users.parquet` - All user records
- `orders.parquet` - All order records  
- `high_value_customers.parquet` - Users with orders > $100

**Usage**:
```bash
cd /path/to/mysql-parquet-lib
python examples/basic_integration_example.py
```

#### 2. Advanced Integration Example (`advanced_integration_example.py`)

**Purpose**: Showcases complex analytics and business intelligence scenarios

**What it does**:
- Validates database connectivity before processing
- Executes complex analytical queries (JOINs, aggregations, window functions)
- Creates timestamped export directories
- Generates comprehensive business analytics reports
- Provides detailed success/failure reporting

**Analytics exports created**:
- `user_order_summary.parquet` - Customer purchase behavior analysis
- `product_performance.parquet` - Product sales and revenue metrics
- `age_demographic_analysis.parquet` - Customer demographic insights
- `high_value_transactions.parquet` - Premium order analysis with rankings
- `customer_lifetime_value.parquet` - Customer segmentation and LTV analysis
- `export_summary.parquet` - Processing metadata and success metrics

**Usage**:
```bash
cd /path/to/mysql-parquet-lib
python examples/advanced_integration_example.py
```

### SQL Server Examples

#### 3. SQL Server Basic Integration Example (`sqlserver_basic_example.py`)

**Purpose**: Demonstrates SQL Server connectivity and basic query patterns using pyodbc

**What it does**:
- Connects to SQL Server using ODBC Driver 18
- Queries system databases and tables
- Exports server properties and metadata
- Shows proper pyodbc connection management

**Exports created**:
- `parquetFiles/sqlserver/system_databases.parquet` - Database information
- `parquetFiles/sqlserver/system_tables.parquet` - Table metadata
- `parquetFiles/sqlserver/server_properties.parquet` - Server configuration

**Environment Variables** (optional):
```bash
# You can generate and load these via the helper:
# source configure_sql_connection_info.sh   # writes .confSQLConnection and exports vars

export SQLSERVER_HOST="localhost"
export SQLSERVER_PORT="1433"
export SQLSERVER_DATABASE="tempdb"
export SQLSERVER_USER="sa"
export SQLSERVER_PASSWORD="YourStrong!Passw0rd"
export SQLSERVER_ENCRYPT="yes"
export SQLSERVER_TRUST_CERT="yes"
```

**Usage**:
```bash
cd /path/to/mysql-parquet-lib
python examples/sqlserver_basic_example.py
```

#### 4. SQL Server Advanced Integration Example (`sqlserver_advanced_example.py`)

**Purpose**: Demonstrates advanced SQL Server analytics with complex queries

**What it does**:
- Database statistics with aggregations and JOINs
- Schema analysis using window functions and CTEs
- Index usage and performance metrics
- Active session monitoring
- Creates timestamped export directories

**Analytics exports created**:
- `database_statistics.parquet` - Database size and configuration analysis
- `schema_analysis.parquet` - Table/object analysis with rankings
- `index_analysis.parquet` - Index usage and performance metrics
- `active_sessions.parquet` - Current database sessions
- `export_summary.parquet` - Export metadata

**Usage**:
```bash
cd /path/to/mysql-parquet-lib
python examples/sqlserver_advanced_example.py
```

## Expected Output Structure

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

## Using the Exported Data

The generated Parquet files can be used with various data analysis tools:

### With Pandas
```python
import pandas as pd

# Load exported data
users_df = pd.read_parquet('parquetFiles/users.parquet')
orders_df = pd.read_parquet('parquetFiles/orders.parquet')

# Analyze the data
print(users_df.info())
print(orders_df.describe())
```

### With Apache Spark
```python
from pyspark.sql import SparkSession

spark = SparkSession.builder.appName("MySQLParquetAnalysis").getOrCreate()

# Load parquet files
users_df = spark.read.parquet('parquetFiles/users.parquet')
analytics_df = spark.read.parquet('parquetFiles/advanced_export_*/user_order_summary.parquet')

users_df.show()
analytics_df.show()
```

### With DuckDB (SQL Analytics)
```python
import duckdb

# Query parquet files directly with SQL
conn = duckdb.connect()
result = conn.execute("""
    SELECT * FROM 'parquetFiles/user_order_summary.parquet'
    WHERE total_spent > 500
    ORDER BY total_spent DESC
""").fetchall()

print(result)
```

## Troubleshooting

### MySQL-Specific Issues

**Database Connection Errors**:
- Verify MySQL is running: `brew services list | grep mysql`
- Test connection: `mysql -h localhost -u testuser -p testdb`
- Check firewall settings and port 3306 accessibility

**Missing Tables**:
- Run the SQL commands from the main README.md to create test tables
- Verify tables exist: `SHOW TABLES;` in MySQL

**Permission Errors**:
- Ensure `testuser` has proper privileges on `testdb`
- Grant permissions: `GRANT ALL PRIVILEGES ON testdb.* TO 'testuser'@'localhost';`

### SQL Server-Specific Issues

**ODBC Driver Not Found**:
- Verify driver installation: `odbcinst -q -d` (Linux/macOS) or check ODBC Data Sources (Windows)
- Ensure driver name matches exactly: `ODBC Driver 18 for SQL Server`
- Reinstall if necessary (see main README.md)

**Connection Timeout**:
- Check SQL Server is running and accessible
- Verify firewall rules allow connections on port 1433
- Ensure SQL Server is configured to accept TCP/IP connections
- Test with `sqlcmd` or other SQL Server client tools

**SSL/TLS Certificate Errors**:
- For dev/test: Use `trust_server_certificate="yes"` in config
- For production: Use valid SSL certificates and set to "no"
- Error: "The certificate chain was issued by an authority that is not trusted"

**Authentication Errors**:
- Verify SQL Server authentication mode (Windows Auth vs SQL Server Auth)
- Check username and password are correct
- Ensure user has appropriate database permissions
- For Windows Auth, use `Trusted_Connection=yes` in connection string

### General Issues

**Import Errors**:
- Run examples from the project root directory
- Ensure all dependencies are installed: `pip install -r requirements.txt`
- For SQL Server: `pip install pyodbc`

### Getting Help

If you encounter issues:

1. Check the main README.md for detailed setup instructions
2. Verify your database setup matches the prerequisites exactly
3. Run the unit tests to ensure the library is working: `python -m pytest tests/ -v`
4. Check that your MySQL version is compatible (MySQL 5.7+ recommended)

## Next Steps

After running these examples successfully:

1. **Modify queries**: Edit the SQL queries to match your actual data needs
2. **Automate exports**: Use cron/scheduler to run exports periodically  
3. **Build dashboards**: Connect BI tools like Tableau/PowerBI to the parquet files
4. **Data pipelines**: Integrate into larger ETL/ELT workflows
5. **Cloud deployment**: Upload parquet files to cloud storage (S3, GCS, etc.)

## File Details

- **Type Safety**: All examples follow strict Python typing conventions
- **Error Handling**: Comprehensive exception handling and validation
- **Resource Management**: Proper database connection cleanup
- **Logging**: Detailed progress reporting and success metrics
- **Modularity**: Reusable functions for common operations