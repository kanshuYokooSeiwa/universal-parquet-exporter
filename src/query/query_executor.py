from typing import List, Dict, Any
from mysql.connector import MySQLConnection

class QueryExecutor:
    def __init__(self, connection: MySQLConnection) -> None:
        self.connection: MySQLConnection = connection

    def execute_query(self, query: str) -> List[Dict[str, Any]]:
        """
        Execute a SQL query and return results as list of dictionaries.
        
        Args:
            query: SQL query string
            
        Returns:
            List of dictionaries with column names as keys
        """
        cursor = self.connection.cursor()
        try:
            cursor.execute(query)
            
            # Get column names from cursor description
            column_names = [desc[0] for desc in cursor.description]
            
            # Fetch all results
            rows = cursor.fetchall()
            
            # Convert to list of dictionaries
            result = []
            for row in rows:
                row_dict = dict(zip(column_names, row))
                result.append(row_dict)
                
            return result
            
        finally:
            cursor.close()