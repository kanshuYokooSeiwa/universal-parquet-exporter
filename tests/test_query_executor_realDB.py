import unittest
import os
from typing import List, Dict, Any, Optional
from unittest import skipIf
import mysql.connector
from mysql.connector import Error

from src.database.mysql_connection import MySQLConnection
from src.query.query_executor import QueryExecutor
from config.database_config import DatabaseConfig


class TestQueryExecutorRealDB(unittest.TestCase):
    """
    Integration tests for QueryExecutor using real MySQL database.
    
    This test class automatically sets up the required test database and tables.
    """
    
    @classmethod
    def setUpClass(cls) -> None:
        """Set up test database configuration and create test data."""
        cls.config: DatabaseConfig = DatabaseConfig(
            host="localhost",
            user="testuser",
            password="testpass",
            database="testdb"
        )
        
        # Check if we can connect to MySQL server
        cls.db_available: bool = cls._check_mysql_server_availability()
        
        if cls.db_available:
            cls._setup_test_database()
            cls.mysql_connection: MySQLConnection = MySQLConnection(cls.config)
            cls.connection = cls.mysql_connection.connect()
            cls.query_executor: QueryExecutor = QueryExecutor(cls.connection)
    
    @classmethod
    def tearDownClass(cls) -> None:
        """Clean up database connection and optionally drop test data."""
        if hasattr(cls, 'mysql_connection') and cls.mysql_connection:
            # Optionally clean up test data
            # cls._cleanup_test_database()
            cls.mysql_connection.close()
    
    @classmethod
    def _check_mysql_server_availability(cls) -> bool:
        """Check if MySQL server is available."""
        try:
            # Try to connect to MySQL server (without specifying database)
            test_connection = mysql.connector.connect(
                host=cls.config.host,
                user=cls.config.user,
                password=cls.config.password
            )
            test_connection.close()
            return True
        except Error as e:
            print(f"MySQL server not available: {e}")
            return False
    
    @classmethod
    def _setup_test_database(cls) -> None:
        """Create test database and tables with sample data."""
        try:
            # Connect to MySQL server
            connection = mysql.connector.connect(
                host=cls.config.host,
                user=cls.config.user,
                password=cls.config.password
            )
            cursor = connection.cursor()
            
            # Create database if it doesn't exist
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {cls.config.database}")
            cursor.execute(f"USE {cls.config.database}")
            
            # Create users table
            create_users_table = """
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                email VARCHAR(100) NOT NULL UNIQUE,
                age INT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
            cursor.execute(create_users_table)
            
            # Create orders table
            create_orders_table = """
            CREATE TABLE IF NOT EXISTS orders (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT,
                product_name VARCHAR(100) NOT NULL,
                quantity INT NOT NULL,
                price DECIMAL(10, 2) NOT NULL,
                order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
            """
            cursor.execute(create_orders_table)
            
            # Clear existing test data
            cursor.execute("DELETE FROM orders")
            cursor.execute("DELETE FROM users")
            cursor.execute("ALTER TABLE users AUTO_INCREMENT = 1")
            cursor.execute("ALTER TABLE orders AUTO_INCREMENT = 1")
            
            # Insert sample users
            insert_users = """
            INSERT INTO users (name, email, age) VALUES
            ('John Doe', 'john.doe@example.com', 30),
            ('Jane Smith', 'jane.smith@example.com', 25),
            ('Bob Johnson', 'bob.johnson@example.com', 35),
            ('Alice Brown', 'alice.brown@example.com', 28),
            ('Charlie Wilson', 'charlie.wilson@example.com', 32)
            """
            cursor.execute(insert_users)
            
            # Insert sample orders
            insert_orders = """
            INSERT INTO orders (user_id, product_name, quantity, price) VALUES
            (1, 'Laptop', 1, 999.99),
            (1, 'Mouse', 2, 25.50),
            (2, 'Keyboard', 1, 75.00),
            (2, 'Monitor', 1, 299.99),
            (3, 'Tablet', 1, 499.99),
            (4, 'Headphones', 1, 199.99),
            (4, 'Webcam', 1, 89.99),
            (5, 'Smartphone', 1, 699.99)
            """
            cursor.execute(insert_orders)
            
            connection.commit()
            cursor.close()
            connection.close()
            
            print("✓ Test database and sample data created successfully")
            
        except Error as e:
            raise unittest.SkipTest(f"Could not set up test database: {e}")
    
    @classmethod
    def _cleanup_test_database(cls) -> None:
        """Clean up test database (optional)."""
        try:
            connection = mysql.connector.connect(
                host=cls.config.host,
                user=cls.config.user,
                password=cls.config.password
            )
            cursor = connection.cursor()
            
            # Optionally drop the test database
            # cursor.execute(f"DROP DATABASE IF EXISTS {cls.config.database}")
            # Or just clear the tables
            cursor.execute(f"USE {cls.config.database}")
            cursor.execute("DELETE FROM orders")
            cursor.execute("DELETE FROM users")
            
            connection.commit()
            cursor.close()
            connection.close()
            
        except Error as e:
            print(f"Warning: Could not clean up test database: {e}")
    
    def setUp(self) -> None:
        """Set up for each test method."""
        if not self.db_available:
            self.skipTest("Database not available")
    
    def test_execute_simple_select_query(self) -> None:
        """Test executing a simple SELECT query."""
        query: str = "SELECT id, name, email FROM users ORDER BY id LIMIT 2"
        
        results: List[Dict[str, Any]] = self.query_executor.execute_query(query)
        
        # Verify results structure
        self.assertIsInstance(results, list)
        self.assertGreater(len(results), 0)
        self.assertEqual(len(results), 2)  # LIMIT 2
        
        # Verify each row is a dictionary with expected keys
        for row in results:
            self.assertIsInstance(row, dict)
            self.assertIn('id', row)
            self.assertIn('name', row)
            self.assertIn('email', row)
            self.assertIsInstance(row['id'], int)
            self.assertIsInstance(row['name'], str)
            self.assertIsInstance(row['email'], str)
    
    def test_execute_query_with_where_clause(self) -> None:
        """Test executing a query with WHERE clause."""
        query: str = "SELECT name, age FROM users WHERE age > 25 ORDER BY age"
        
        results: List[Dict[str, Any]] = self.query_executor.execute_query(query)
        
        self.assertIsInstance(results, list)
        self.assertGreater(len(results), 0)
        
        # Verify age filtering worked
        for row in results:
            self.assertGreater(row['age'], 25)
    
    def test_execute_join_query(self) -> None:
        """Test executing a JOIN query."""
        query: str = """
        SELECT u.name, u.email, o.product_name, o.quantity, o.price
        FROM users u
        JOIN orders o ON u.id = o.user_id
        ORDER BY u.name, o.product_name
        """
        
        results: List[Dict[str, Any]] = self.query_executor.execute_query(query)
        
        self.assertIsInstance(results, list)
        self.assertGreater(len(results), 0)
        
        # Verify join structure
        for row in results:
            self.assertIn('name', row)
            self.assertIn('email', row)
            self.assertIn('product_name', row)
            self.assertIn('quantity', row)
            self.assertIn('price', row)
            self.assertIsInstance(row['name'], str)
            self.assertIsInstance(row['email'], str)
            self.assertIsInstance(row['product_name'], str)
            self.assertIsInstance(row['quantity'], int)
    
    def test_execute_aggregate_query(self) -> None:
        """Test executing an aggregate query."""
        query: str = """
        SELECT COUNT(*) as user_count, AVG(age) as avg_age, MIN(age) as min_age, MAX(age) as max_age
        FROM users
        """
        
        results: List[Dict[str, Any]] = self.query_executor.execute_query(query)
        
        self.assertIsInstance(results, list)
        self.assertEqual(len(results), 1)  # Aggregate should return 1 row
        
        row: Dict[str, Any] = results[0]
        self.assertIn('user_count', row)
        self.assertIn('avg_age', row)
        self.assertIn('min_age', row)
        self.assertIn('max_age', row)
        
        self.assertGreater(row['user_count'], 0)
        self.assertGreater(row['avg_age'], 0)
        self.assertGreaterEqual(row['max_age'], row['min_age'])
    
    def test_execute_empty_result_query(self) -> None:
        """Test executing a query that returns no results."""
        query: str = "SELECT * FROM users WHERE age > 100"
        
        results: List[Dict[str, Any]] = self.query_executor.execute_query(query)
        
        self.assertIsInstance(results, list)
        self.assertEqual(len(results), 0)
    
    def test_execute_invalid_query(self) -> None:
        """Test executing an invalid SQL query."""
        query: str = "SELECT * FROM non_existent_table"
        
        with self.assertRaises(Exception):
            self.query_executor.execute_query(query)
    
    def test_execute_query_with_special_characters(self) -> None:
        """Test executing a query with special characters in data."""
        # First, insert a test record with special characters
        setup_query: str = """
        INSERT IGNORE INTO users (name, email, age) 
        VALUES ('Test User & Co.', 'test+special@example.com', 30)
        """
        
        try:
            # Setup test data
            cursor = self.connection.cursor()
            cursor.execute(setup_query)
            self.connection.commit()
            cursor.close()
            
            # Test the query
            query: str = "SELECT name, email FROM users WHERE name LIKE '%&%'"
            results: List[Dict[str, Any]] = self.query_executor.execute_query(query)
            
            self.assertIsInstance(results, list)
            if len(results) > 0:
                self.assertIn('&', results[0]['name'])  # name should contain &
                
        except Exception as e:
            self.fail(f"Query with special characters failed: {e}")
    
    def test_execute_query_with_null_values(self) -> None:
        """Test executing a query that may return NULL values."""
        # Insert a user with a NULL age
        setup_query: str = """
        INSERT IGNORE INTO users (name, email, age) 
        VALUES ('Test User NULL', 'test_null@example.com', NULL)
        """
        
        try:
            # Setup test data
            cursor = self.connection.cursor()
            cursor.execute(setup_query)
            self.connection.commit()
            cursor.close()
            
            # Test the query
            query: str = "SELECT name, email, age FROM users WHERE name = 'Test User NULL'"
            results: List[Dict[str, Any]] = self.query_executor.execute_query(query)
            
            self.assertIsInstance(results, list)
            if len(results) > 0:
                self.assertIsNone(results[0]['age'])  # age should be None
                
        except Exception as e:
            self.fail(f"Query with NULL values failed: {e}")
    
    def test_execute_order_by_query(self) -> None:
        """Test executing a query with ORDER BY clause."""
        query: str = "SELECT name, age FROM users ORDER BY age DESC"
        
        results: List[Dict[str, Any]] = self.query_executor.execute_query(query)
        
        self.assertIsInstance(results, list)
        self.assertGreater(len(results), 0)
        
        # Verify ordering (should be descending by age)
        previous_age: Optional[int] = None
        for row in results:
            current_age: Optional[int] = row['age']
            if previous_age is not None and current_age is not None:
                self.assertGreaterEqual(previous_age, current_age)
            previous_age = current_age
    
    def test_execute_group_by_query(self) -> None:
        """Test executing a query with GROUP BY clause."""
        query: str = """
        SELECT u.name, COUNT(o.id) as order_count, SUM(o.price) as total_spent
        FROM users u
        LEFT JOIN orders o ON u.id = o.user_id
        GROUP BY u.id, u.name
        ORDER BY u.name
        """
        
        results: List[Dict[str, Any]] = self.query_executor.execute_query(query)
        
        self.assertIsInstance(results, list)
        self.assertGreater(len(results), 0)
        
        # Verify group by structure
        for row in results:
            self.assertEqual(len(row), 3)  # name, order_count, total_spent
            self.assertIsInstance(row['name'], str)  # name
            self.assertIsInstance(row['order_count'], int)  # order_count
            # total_spent can be None (for users with no orders) or Decimal
    
    def test_execute_limit_offset_query(self) -> None:
        """Test executing a query with LIMIT and OFFSET."""
        query: str = "SELECT id, name, email FROM users ORDER BY id LIMIT 1 OFFSET 1"
        
        results: List[Dict[str, Any]] = self.query_executor.execute_query(query)
        
        # Should return exactly 1 row (LIMIT 1) starting from the 2nd record (OFFSET 1)
        self.assertIsInstance(results, list)
        self.assertEqual(len(results), 1)
        
        # Verify the structure of the returned dictionary
        row: Dict[str, Any] = results[0]
        self.assertIsInstance(row, dict)
        self.assertIn('id', row)
        self.assertIn('name', row) 
        self.assertIn('email', row)
        
        # Since OFFSET 1, this should be the second user (id=2)
        self.assertEqual(row['id'], 2)
        self.assertIsInstance(row['name'], str)
        self.assertIsInstance(row['email'], str)


if __name__ == '__main__':
    unittest.main()