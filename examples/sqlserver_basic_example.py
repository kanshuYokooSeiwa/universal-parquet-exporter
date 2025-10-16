#!/usr/bin/env python3
"""
Basic SQL Server Integration Example

This example demonstrates how to:
1. Connect to a Microsoft SQL Server database using pyodbc
2. Execute simple queries
3. Export results to Parquet files
4. Properly manage connections

Prerequisites:
- SQL Server instance running and accessible
- ODBC Driver 18 for SQL Server installed
- pyodbc Python package installed (pip install pyodbc)
- Valid SQL Server credentials

Usage:
    python examples/sqlserver_basic_example.py
"""

import os
import sys
from pathlib import Path
from typing import List, Dict, Any

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.sqlserver_config import SQLServerConfig
from src.database.sqlserver_connection import SQLServerConnection
from src.query.query_executor import QueryExecutor
from src.export.parquet_writer import ParquetWriter


def main() -> None:
    """Main execution function for SQL Server basic integration example."""
    
    print("=" * 70)
    print("SQL Server to Parquet - Basic Integration Example")
    print("=" * 70)
    print()
    
    # Configure SQL Server connection
    # You can use environment variables or hardcode credentials (not recommended for production)
    config = SQLServerConfig(
        host=os.getenv("MSSQL_HOST", "localhost"),
        port=int(os.getenv("MSSQL_PORT", "1433")),
        database=os.getenv("MSSQL_DATABASE", "tempdb"),
        user=os.getenv("MSSQL_USER", "sa"),
        password=os.getenv("MSSQL_PASSWORD", "YourStrong!Passw0rd"),
        encrypt=os.getenv("MSSQL_ENCRYPT", "yes"),
        trust_server_certificate=os.getenv("MSSQL_TRUST_CERT", "yes"),
    )
    
    print(f"Connecting to SQL Server: {config.host}:{config.port}")
    print(f"Database: {config.database}")
    print(f"User: {config.user}")
    print()
    
    # Create connection
    sql_conn = SQLServerConnection(config)
    
    try:
        # Establish connection
        connection = sql_conn.connect()
        print("✓ Connected to SQL Server successfully!")
        print()

        # Create query executor
        query_executor = QueryExecutor(connection)

        # Show all tables in the selected database
        print("-" * 70)
        print("All tables in the selected database:")
        print("-" * 70)
        show_tables_query = '''
        SELECT s.name AS schema_name, t.name AS table_name
        FROM sys.tables t
        INNER JOIN sys.schemas s ON t.schema_id = s.schema_id
        ORDER BY s.name, t.name
        '''
        tables = query_executor.execute_query(show_tables_query)
        if tables:
            for i, tbl in enumerate(tables, 1):
                print(f"  {i}. {tbl['schema_name']}.{tbl['table_name']}")
        else:
            print("  (No tables found)")
        print()

        # Create parquet writer
        parquet_writer = ParquetWriter()

        # Create output directory
        output_dir = Path(os.getcwd()) / "parquetFiles" / "sqlserver"
        output_dir.mkdir(parents=True, exist_ok=True)
        print(f"Output directory: {output_dir}")
        print()
        
        # Example 1: Query system databases
        print("-" * 70)
        print("Example 1: Exporting System Databases Information")
        print("-" * 70)
        
        databases_query = """
        SELECT 
            database_id,
            name as database_name,
            create_date,
            compatibility_level,
            state_desc as database_state
        FROM sys.databases
        ORDER BY database_id
        """
        
        print("Executing query...")
        databases_result: List[Dict[str, Any]] = query_executor.execute_query(databases_query)
        print(f"Retrieved {len(databases_result)} databases")
        
        if databases_result:
            databases_file = output_dir / "system_databases.parquet"
            parquet_writer.write_to_parquet(databases_result, str(databases_file))
            print(f"✓ Exported to: {databases_file}")
            
            # Display sample data
            print("\nSample data (first 3 records):")
            for i, db in enumerate(databases_result[:3], 1):
                print(f"  {i}. {db.get('database_name')} (ID: {db.get('database_id')})")
        print()
        
        # Example 2: Query system tables
        print("-" * 70)
        print("Example 2: Exporting System Tables Information")
        print("-" * 70)
        
        tables_query = """
        SELECT TOP 20
            t.name as table_name,
            s.name as schema_name,
            t.create_date,
            t.modify_date,
            p.rows as row_count
        FROM sys.tables t
        INNER JOIN sys.schemas s ON t.schema_id = s.schema_id
        LEFT JOIN sys.partitions p ON t.object_id = p.object_id AND p.index_id IN (0, 1)
        ORDER BY t.name
        """
        
        print("Executing query...")
        tables_result: List[Dict[str, Any]] = query_executor.execute_query(tables_query)
        print(f"Retrieved {len(tables_result)} tables")
        
        if tables_result:
            tables_file = output_dir / "system_tables.parquet"
            parquet_writer.write_to_parquet(tables_result, str(tables_file))
            print(f"✓ Exported to: {tables_file}")
            
            # Display sample data
            print("\nSample data (first 5 records):")
            for i, table in enumerate(tables_result[:5], 1):
                print(f"  {i}. {table.get('schema_name')}.{table.get('table_name')} ({table.get('row_count')} rows)")
        print()
        
        # Example 3: Query server properties
        print("-" * 70)
        print("Example 3: Exporting Server Properties")
        print("-" * 70)
        
        properties_query = """
        SELECT 
            SERVERPROPERTY('ServerName') as server_name,
            SERVERPROPERTY('ProductVersion') as product_version,
            SERVERPROPERTY('ProductLevel') as product_level,
            SERVERPROPERTY('Edition') as edition,
            SERVERPROPERTY('EngineEdition') as engine_edition,
            SERVERPROPERTY('Collation') as collation,
            GETDATE() as query_time
        """
        
        print("Executing query...")
        properties_result: List[Dict[str, Any]] = query_executor.execute_query(properties_query)
        
        if properties_result:
            properties_file = output_dir / "server_properties.parquet"
            parquet_writer.write_to_parquet(properties_result, str(properties_file))
            print(f"✓ Exported to: {properties_file}")
            
            # Display server info
            if len(properties_result) > 0:
                props = properties_result[0]
                print("\nServer Information:")
                print(f"  Server: {props.get('server_name')}")
                print(f"  Version: {props.get('product_version')}")
                print(f"  Edition: {props.get('edition')}")
        print()
        
        # Summary
        print("=" * 70)
        print("Export Summary")
        print("=" * 70)
        print(f"✓ All queries executed successfully!")
        print(f"✓ Parquet files saved to: {output_dir}")
        print(f"✓ Total files created: 3")
        print()
        
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    finally:
        # Clean up connection
        sql_conn.close()
        print("✓ Connection closed")
        print()


if __name__ == "__main__":
    main()
