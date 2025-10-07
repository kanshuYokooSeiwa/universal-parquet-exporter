from typing import List, Dict, Any
import pandas as pd

class ParquetWriter:
    def __init__(self) -> None:
        pass
    
    def write_to_parquet(self, data: List[Dict[str, Any]], file_path: str) -> None:
        # Check if data is not empty
        if not data:
            raise ValueError("Data cannot be empty.")
        
        # Convert the data to a DataFrame (column names come from dict keys)
        df: pd.DataFrame = pd.DataFrame(data)
        
        # Write the DataFrame to a Parquet file
        df.to_parquet(file_path, index=False)