import unittest
from unittest.mock import patch, Mock, MagicMock
from typing import List, Tuple, Any
import pandas as pd
import tempfile
import os

from src.export.parquet_writer import ParquetWriter


class TestParquetWriter(unittest.TestCase):
    
    def setUp(self) -> None:
        """Set up test fixtures before each test method."""
        self.parquet_writer: ParquetWriter = ParquetWriter()
        self.test_data: List[Tuple[Any, ...]] = [
            (1, 'John', 'Doe', 25),
            (2, 'Jane', 'Smith', 30),
            (3, 'Bob', 'Johnson', 35)
        ]
    
    @patch('src.export.parquet_writer.pd.DataFrame')
    def test_write_to_parquet_success(self, mock_dataframe: Mock) -> None:
        """Test successful parquet file writing."""
        mock_df: Mock = MagicMock()
        mock_dataframe.return_value = mock_df
        
        file_path: str = 'test_output.parquet'
        
        self.parquet_writer.write_to_parquet(self.test_data, file_path)
        
        # Verify DataFrame creation
        mock_dataframe.assert_called_once_with(self.test_data)
        
        # Verify parquet writing
        mock_df.to_parquet.assert_called_once_with(file_path, index=False)
    
    def test_write_to_parquet_integration(self) -> None:
        """Test actual parquet file writing (integration test)."""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path: str = os.path.join(temp_dir, 'test_output.parquet')
            
            self.parquet_writer.write_to_parquet(self.test_data, file_path)
            
            # Verify file was created
            self.assertTrue(os.path.exists(file_path))
            
            # Verify file content by reading it back
            df_read: pd.DataFrame = pd.read_parquet(file_path)
            
            # Check basic properties
            self.assertEqual(len(df_read), 3)  # 3 rows of data
            self.assertEqual(len(df_read.columns), 4)  # 4 columns
            
            # Check specific values
            self.assertEqual(df_read.iloc[0, 0], 1)
            self.assertEqual(df_read.iloc[0, 1], 'John')
            self.assertEqual(df_read.iloc[1, 2], 'Smith')
    
    def test_write_to_parquet_empty_data(self):
        """Test that empty data raises ValueError."""
        writer = ParquetWriter()
        with self.assertRaises(ValueError):
            writer.write_to_parquet([], "test.parquet")
    
    @patch('src.export.parquet_writer.pd.DataFrame')
    def test_write_to_parquet_with_exception(self, mock_dataframe: Mock) -> None:
        """Test parquet writing with exception."""
        mock_df: Mock = MagicMock()
        mock_df.to_parquet.side_effect = Exception("Write error")
        mock_dataframe.return_value = mock_df
        
        file_path: str = 'test_output.parquet'
        
        with self.assertRaises(Exception):
            self.parquet_writer.write_to_parquet(self.test_data, file_path)


if __name__ == '__main__':
    unittest.main()