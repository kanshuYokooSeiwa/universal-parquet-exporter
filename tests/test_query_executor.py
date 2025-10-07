import unittest
from unittest.mock import Mock, MagicMock
from typing import List, Tuple, Any
from mysql.connector import MySQLConnection

from src.query.query_executor import QueryExecutor


class TestQueryExecutor(unittest.TestCase):
    
    def setUp(self) -> None:
        """Set up test fixtures before each test method."""
        self.mock_connection: Mock = Mock(spec=MySQLConnection)
        self.query_executor: QueryExecutor = QueryExecutor(self.mock_connection)
    
    def test_execute_query_success(self):
        """Test successful query execution returns list of dictionaries."""
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [('John', 25), ('Jane', 30)]
        mock_cursor.description = [('name',), ('age',)]
        
        self.mock_connection.cursor.return_value = mock_cursor
        
        executor = QueryExecutor(self.mock_connection)
        result = executor.execute_query("SELECT name, age FROM users")
        
        expected = [{'name': 'John', 'age': 25}, {'name': 'Jane', 'age': 30}]
        self.assertEqual(result, expected)

    def test_execute_aggregate_query(self):
        """Test aggregate query execution."""
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [(5,)]
        mock_cursor.description = [('count',)]
        
        self.mock_connection.cursor.return_value = mock_cursor
        
        executor = QueryExecutor(self.mock_connection)
        result = executor.execute_query("SELECT COUNT(*) as count FROM users")
        
        expected = [{'count': 5}]
        self.assertEqual(result, expected)

    def test_execute_group_by_query(self):
        """Test GROUP BY query execution."""
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [('Engineering', 3), ('Marketing', 2)]
        mock_cursor.description = [('department',), ('count',)]
        
        self.mock_connection.cursor.return_value = mock_cursor
        
        executor = QueryExecutor(self.mock_connection)
        result = executor.execute_query("SELECT department, COUNT(*) as count FROM users GROUP BY department")
        
        expected = [{'department': 'Engineering', 'count': 3}, {'department': 'Marketing', 'count': 2}]
        self.assertEqual(result, expected)

    def test_execute_join_query(self):
        """Test JOIN query execution."""
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [('John', 'Product A'), ('Jane', 'Product B')]
        mock_cursor.description = [('user_name',), ('product_name',)]
        
        self.mock_connection.cursor.return_value = mock_cursor
        
        executor = QueryExecutor(self.mock_connection)
        result = executor.execute_query("SELECT u.name as user_name, p.name as product_name FROM users u JOIN products p ON u.id = p.user_id")
        
        expected = [{'user_name': 'John', 'product_name': 'Product A'}, {'user_name': 'Jane', 'product_name': 'Product B'}]
        self.assertEqual(result, expected)

    def test_execute_limit_offset_query(self):
        """Test LIMIT and OFFSET query execution."""
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [('Jane', 30)]
        mock_cursor.description = [('name',), ('age',)]
        
        self.mock_connection.cursor.return_value = mock_cursor
        
        executor = QueryExecutor(self.mock_connection)
        result = executor.execute_query("SELECT name, age FROM users LIMIT 1 OFFSET 1")
        
        expected = [{'name': 'Jane', 'age': 30}]
        self.assertEqual(result, expected)

    def test_execute_order_by_query(self):
        """Test ORDER BY query execution."""
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [('Jane', 30), ('John', 25)]
        mock_cursor.description = [('name',), ('age',)]
        
        self.mock_connection.cursor.return_value = mock_cursor
        
        executor = QueryExecutor(self.mock_connection)
        result = executor.execute_query("SELECT name, age FROM users ORDER BY age DESC")
        
        expected = [{'name': 'Jane', 'age': 30}, {'name': 'John', 'age': 25}]
        self.assertEqual(result, expected)

    def test_execute_query_with_null_values(self):
        """Test query execution with NULL values."""
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [('John', None), ('Jane', 30)]
        mock_cursor.description = [('name',), ('age',)]
        
        self.mock_connection.cursor.return_value = mock_cursor
        
        executor = QueryExecutor(self.mock_connection)
        result = executor.execute_query("SELECT name, age FROM users")
        
        expected = [{'name': 'John', 'age': None}, {'name': 'Jane', 'age': 30}]
        self.assertEqual(result, expected)

    def test_execute_query_with_special_characters(self):
        """Test query execution with special characters."""
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [("O'Connor", "john@example.com")]
        mock_cursor.description = [('name',), ('email',)]
        
        self.mock_connection.cursor.return_value = mock_cursor
        
        executor = QueryExecutor(self.mock_connection)
        result = executor.execute_query("SELECT name, email FROM users WHERE name = 'O''Connor'")
        
        expected = [{'name': "O'Connor", 'email': "john@example.com"}]
        self.assertEqual(result, expected)

    def test_execute_query_with_where_clause(self):
        """Test query execution with WHERE clause."""
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [('Jane', 30)]
        mock_cursor.description = [('name',), ('age',)]
        
        self.mock_connection.cursor.return_value = mock_cursor
        
        executor = QueryExecutor(self.mock_connection)
        result = executor.execute_query("SELECT name, age FROM users WHERE age > 25")
        
        expected = [{'name': 'Jane', 'age': 30}]
        self.assertEqual(result, expected)

    def test_execute_simple_select_query(self):
        """Test simple SELECT query execution."""
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [('John',), ('Jane',)]
        mock_cursor.description = [('name',)]
        
        self.mock_connection.cursor.return_value = mock_cursor
        
        executor = QueryExecutor(self.mock_connection)
        result = executor.execute_query("SELECT name FROM users")
        
        expected = [{'name': 'John'}, {'name': 'Jane'}]
        self.assertEqual(result, expected)

    def test_execute_query_empty_results(self) -> None:
        """Test query execution with empty results."""
        mock_cursor: Mock = MagicMock()
        expected_results: List[Tuple[Any, ...]] = []
        mock_cursor.fetchall.return_value = expected_results
        self.mock_connection.cursor.return_value = mock_cursor
        
        query: str = "SELECT * FROM empty_table"
        results: List[Tuple[Any, ...]] = self.query_executor.execute_query(query)
        
        self.assertEqual(results, expected_results)
        mock_cursor.close.assert_called_once()
    
    def test_execute_query_with_exception(self) -> None:
        """Test query execution with database exception."""
        mock_cursor: Mock = MagicMock()
        mock_cursor.execute.side_effect = Exception("SQL syntax error")
        self.mock_connection.cursor.return_value = mock_cursor
        
        query: str = "INVALID SQL QUERY"
        
        with self.assertRaises(Exception):
            self.query_executor.execute_query(query)
        
        # Ensure cursor is still closed even on exception
        mock_cursor.close.assert_called_once()


if __name__ == '__main__':
    unittest.main()