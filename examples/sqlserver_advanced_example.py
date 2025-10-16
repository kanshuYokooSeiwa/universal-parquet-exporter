#!/usr/bin/env python3
"""
Advanced SQL Server Integration Example

This example demonstrates advanced usage patterns:
1. Complex queries with JOINs and aggregations
2. Window functions and CTEs (Common Table Expressions)
3. Parameterized queries for security
4. Batch processing with multiple exports
5. Error handling and connection management

Prerequisites:
- SQL Server instance with a sample database (e.g., AdventureWorks)
- ODBC Driver 18 for SQL Server installed
- pyodbc Python package installed
- Valid SQL Server credentials

Usage:
    python examples/sqlserver_advanced_example.py
"""

import os
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.sqlserver_config import SQLServerConfig
from src.database.sqlserver_connection import SQLServerConnection
from src.query.query_executor import QueryExecutor
from src.export.parquet_writer import ParquetWriter


def create_timestamped_directory(base_dir: str = "parquetFiles/sqlserver") -> Path:
    """
    Create a timestamped directory for organized exports.
    
    Args:
        base_dir: Base directory path
        
    Returns:
        Path object for the created directory
    """
    timestamp: str = datetime.now().strftime("%Y%m%d_%H%M%S")
    export_dir: Path = Path(os.getcwd()) / base_dir / f"export_{timestamp}"
    export_dir.mkdir(parents=True, exist_ok=True)
    return export_dir


def validate_connection(sql_conn: SQLServerConnection) -> bool:
    """
    Validate SQL Server connection before processing.
    
    Args:
        sql_conn: SQLServerConnection instance
        
    Returns:
        True if connection is valid, False otherwise
    """
    try:
        connection = sql_conn.connect()
        cursor = connection.cursor()
        cursor.execute("SELECT @@VERSION as version")
        result = cursor.fetchone()
        cursor.close()
        
        if result:
            print(f"✓ SQL Server version: {result[0][:80]}...")
            return True
        return False
    except Exception as e:
        print(f"✗ Connection validation failed: {e}")
        return False


def main() -> None:
    """Main execution function for SQL Server advanced integration example."""
    
    print("=" * 80)
    print("SQL Server to Parquet - Advanced Integration Example")
    print("=" * 80)
    print()
    
    # Configure SQL Server connection
    config = SQLServerConfig(
        host=os.getenv("MSSQL_HOST", "localhost"),
        port=int(os.getenv("MSSQL_PORT", "1433")),
        database=os.getenv("MSSQL_DATABASE", "tempdb"),
        user=os.getenv("MSSQL_USER", "sa"),
        password=os.getenv("MSSQL_PASSWORD", "YourStrong!Passw0rd"),
        encrypt=os.getenv("MSSQL_ENCRYPT", "yes"),
        trust_server_certificate=os.getenv("MSSQL_TRUST_CERT", "yes"),
    )
    
    print(f"Target Server: {config.host}:{config.port}")
    print(f"Database: {config.database}")
    print()
    
    # Create connection
    sql_conn = SQLServerConnection(config)
    
    try:
        # Validate connection
        print("Validating connection...")
        if not validate_connection(sql_conn):
            raise Exception("Connection validation failed")
        print()
        
        connection = sql_conn.connect()
        query_executor = QueryExecutor(connection)
        parquet_writer = ParquetWriter()
        
        # Create timestamped export directory
        export_dir = create_timestamped_directory()
        print(f"Export directory: {export_dir}")
        print()
        
        # Track export results
        exports: List[Dict[str, Any]] = []
        
        # Example 1: Database statistics with aggregations
        print("-" * 80)
        print("Example 1: Database Statistics Analysis")
        print("-" * 80)
        
        stats_query = """
        SELECT 
            d.name as database_name,
            d.state_desc,
            d.recovery_model_desc,
            CAST(SUM(mf.size) * 8.0 / 1024 AS DECIMAL(10,2)) as total_size_mb,
            d.create_date,
            d.compatibility_level
        FROM sys.databases d
        LEFT JOIN sys.master_files mf ON d.database_id = mf.database_id
        WHERE d.database_id > 4  -- Skip system databases
        GROUP BY d.name, d.state_desc, d.recovery_model_desc, d.create_date, d.compatibility_level
        ORDER BY total_size_mb DESC
        """
        
        print("Executing database statistics query...")
        stats_result = query_executor.execute_query(stats_query)
        
        if stats_result:
            stats_file = export_dir / "database_statistics.parquet"
            parquet_writer.write_to_parquet(stats_result, str(stats_file))
            print(f"✓ Exported {len(stats_result)} databases to: {stats_file.name}")
            exports.append({
                "query_name": "Database Statistics",
                "file_name": stats_file.name,
                "row_count": len(stats_result)
            })
        print()
        
        # Example 2: Schema analysis with window functions
        print("-" * 80)
        print("Example 2: Schema Object Analysis with Rankings")
        print("-" * 80)
        
        schema_query = """
        WITH object_stats AS (
            SELECT 
                s.name as schema_name,
                t.name as table_name,
                t.type_desc as object_type,
                p.rows as row_count,
                CAST(SUM(a.total_pages) * 8.0 / 1024 AS DECIMAL(10,2)) as total_size_mb,
                t.create_date
            FROM sys.tables t
            INNER JOIN sys.schemas s ON t.schema_id = s.schema_id
            LEFT JOIN sys.partitions p ON t.object_id = p.object_id AND p.index_id IN (0, 1)
            LEFT JOIN sys.allocation_units a ON p.partition_id = a.container_id
            GROUP BY s.name, t.name, t.type_desc, p.rows, t.create_date
        )
        SELECT 
            schema_name,
            table_name,
            object_type,
            row_count,
            total_size_mb,
            create_date,
            ROW_NUMBER() OVER (ORDER BY total_size_mb DESC) as size_rank,
            RANK() OVER (PARTITION BY schema_name ORDER BY row_count DESC) as row_rank_in_schema
        FROM object_stats
        WHERE total_size_mb > 0
        ORDER BY total_size_mb DESC
        """
        
        print("Executing schema analysis query...")
        schema_result = query_executor.execute_query(schema_query)
        
        if schema_result:
            schema_file = export_dir / "schema_analysis.parquet"
            parquet_writer.write_to_parquet(schema_result, str(schema_file))
            print(f"✓ Exported {len(schema_result)} objects to: {schema_file.name}")
            
            # Display top 5 largest objects
            print("\nTop 5 largest objects:")
            for i, obj in enumerate(schema_result[:5], 1):
                print(f"  {i}. {obj.get('schema_name')}.{obj.get('table_name')} - "
                      f"{obj.get('total_size_mb')} MB ({obj.get('row_count')} rows)")
            
            exports.append({
                "query_name": "Schema Analysis",
                "file_name": schema_file.name,
                "row_count": len(schema_result)
            })
        print()
        
        # Example 3: Index analysis
        print("-" * 80)
        print("Example 3: Index Usage and Performance Analysis")
        print("-" * 80)
        
        index_query = """
        SELECT TOP 50
            OBJECT_SCHEMA_NAME(i.object_id) as schema_name,
            OBJECT_NAME(i.object_id) as table_name,
            i.name as index_name,
            i.type_desc as index_type,
            i.is_unique,
            i.is_primary_key,
            CAST(SUM(s.used_page_count) * 8.0 / 1024 AS DECIMAL(10,2)) as index_size_mb,
            us.user_seeks,
            us.user_scans,
            us.user_lookups,
            us.user_updates,
            us.last_user_seek,
            us.last_user_scan
        FROM sys.indexes i
        INNER JOIN sys.dm_db_partition_stats s ON i.object_id = s.object_id AND i.index_id = s.index_id
        LEFT JOIN sys.dm_db_index_usage_stats us ON i.object_id = us.object_id AND i.index_id = us.index_id
        WHERE OBJECTPROPERTY(i.object_id, 'IsUserTable') = 1
        GROUP BY 
            i.object_id, i.name, i.type_desc, i.is_unique, i.is_primary_key,
            us.user_seeks, us.user_scans, us.user_lookups, us.user_updates,
            us.last_user_seek, us.last_user_scan
        ORDER BY index_size_mb DESC
        """
        
        print("Executing index analysis query...")
        index_result = query_executor.execute_query(index_query)
        
        if index_result:
            index_file = export_dir / "index_analysis.parquet"
            parquet_writer.write_to_parquet(index_result, str(index_file))
            print(f"✓ Exported {len(index_result)} indexes to: {index_file.name}")
            exports.append({
                "query_name": "Index Analysis",
                "file_name": index_file.name,
                "row_count": len(index_result)
            })
        print()
        
        # Example 4: Active sessions and connections
        print("-" * 80)
        print("Example 4: Active Sessions Analysis")
        print("-" * 80)
        
        sessions_query = """
        SELECT 
            s.session_id,
            s.login_name,
            s.host_name,
            s.program_name,
            s.status,
            s.cpu_time,
            s.memory_usage,
            s.total_elapsed_time,
            s.login_time,
            s.last_request_start_time,
            c.num_reads,
            c.num_writes,
            DB_NAME(s.database_id) as database_name
        FROM sys.dm_exec_sessions s
        LEFT JOIN sys.dm_exec_connections c ON s.session_id = c.session_id
        WHERE s.is_user_process = 1
        ORDER BY s.total_elapsed_time DESC
        """
        
        print("Executing active sessions query...")
        sessions_result = query_executor.execute_query(sessions_query)
        
        if sessions_result:
            sessions_file = export_dir / "active_sessions.parquet"
            parquet_writer.write_to_parquet(sessions_result, str(sessions_file))
            print(f"✓ Exported {len(sessions_result)} sessions to: {sessions_file.name}")
            print(f"  Active user sessions: {len(sessions_result)}")
            exports.append({
                "query_name": "Active Sessions",
                "file_name": sessions_file.name,
                "row_count": len(sessions_result)
            })
        print()
        
        # Create export summary
        print("-" * 80)
        print("Creating Export Summary")
        print("-" * 80)
        
        summary_data = [{
            "export_timestamp": datetime.now(),
            "server": config.host,
            "database": config.database,
            "total_exports": len(exports),
            "export_directory": str(export_dir.name)
        }]
        
        summary_file = export_dir / "export_summary.parquet"
        parquet_writer.write_to_parquet(summary_data, str(summary_file))
        print(f"✓ Export summary saved to: {summary_file.name}")
        print()
        
        # Final summary
        print("=" * 80)
        print("Export Summary")
        print("=" * 80)
        print(f"Export directory: {export_dir}")
        print(f"Total exports: {len(exports) + 1}")  # +1 for summary file
        print()
        print("Exported files:")
        for i, export in enumerate(exports, 1):
            print(f"  {i}. {export['file_name']} - {export['row_count']} rows ({export['query_name']})")
        print(f"  {len(exports) + 1}. {summary_file.name} - Export metadata")
        print()
        print("✓ All operations completed successfully!")
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
