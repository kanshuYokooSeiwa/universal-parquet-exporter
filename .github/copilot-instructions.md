# Copilot Instructions for universal-parquet-exporter

## Repository Overview
Lightweight pandas wrapper for MySQL-to-Parquet data export. Pure Python library with 3 core components: MySQLConnection, QueryExecutor, ParquetWriter.

**Key Info**: Python 3.6+ | Dependencies: mysql-connector-python, pandas, pyarrow | No build step | No linters configured | No CI/CD

## Critical Setup
**ALWAYS run first**: `pip install -r requirements.txt`

## Testing (No MySQL Required)
```bash
python -m pytest tests/ -v  # Primary: 25 passed, 11 skipped (~1 sec)
python -m unittest discover tests/ -v  # Alternative
coverage run -m pytest tests/ && coverage report -m  # With coverage
```
**Key**: Mock-based tests work without MySQL. Integration tests (test_query_executor_realDB.py) auto-skip if no database. Install pytest/coverage if needed: `pip install pytest coverage`

## Project Structure
```
├── config/database_config.py       # DatabaseConfig class for connection params
├── src/
│   ├── database/mysql_connection.py  # MySQLConnection: connect(), close()
│   ├── export/parquet_writer.py      # ParquetWriter: write_to_parquet()
│   └── query/query_executor.py       # QueryExecutor: execute_query() → List[Dict]
├── tests/                          # All mock-based, no MySQL needed
│   ├── test_*_realDB.py           # Integration tests (auto-skipped)
└── examples/                       # Require MySQL setup
```

## Core Architecture
**Data Flow**: `MySQL → QueryExecutor → List[Dict[str, Any]] → ParquetWriter → .parquet`

**CRITICAL**: QueryExecutor returns `List[Dict[str, Any]]` (NOT tuples) for meaningful column names in parquet files.

Example: `[{'id': 1, 'name': 'John'}, {'id': 2, 'name': 'Jane'}]` ✅
NOT: `[(1, 'John'), (2, 'Jane')]` ❌

## Type Safety Standards (MANDATORY)
All code follows strict typing - see Claude.md for details:
```python
from typing import List, Dict, Any

def process_data(data: List[Dict[str, Any]], path: str) -> bool:
    result: bool = do_something(data)
    return result
```
**Rules**: Type hints on ALL parameters, return types, and variables. Import types from `typing`.

## Development Workflow
1. Install dependencies: `pip install -r requirements.txt`
2. Make changes to src/ files
3. Run tests: `python -m pytest tests/ -v` (expect 25 passed, 11 skipped)
4. Add tests following mock patterns in existing test files

**Component-specific testing**:
```bash
python -m pytest tests/test_mysql_connection.py -v   # Database connection
python -m pytest tests/test_query_executor.py -v     # Query execution
python -m pytest tests/test_parquet_writer.py -v     # Parquet writing
python -m pytest tests/test_database_config.py -v    # Configuration
```

## Common Pitfalls
1. **Missing dependencies**: Run `pip install -r requirements.txt` first
2. **Changing data format**: Keep `List[Dict[str, Any]]` - NOT tuples
3. **Running integration tests**: They auto-skip without MySQL (EXPECTED)
4. **Missing type imports**: Import from `typing` module
5. **Modifying working tests**: Add new tests, don't modify existing patterns

## Troubleshooting Common Errors
**Import errors** (`ModuleNotFoundError`): Run `pip install -r requirements.txt`
**Test failures** (unexpected): Check if you changed data format or removed type hints
**MySQL connection errors**: Integration tests skip automatically - this is normal
**Parquet write errors**: Verify data is `List[Dict[str, Any]]`, not tuples or other format

## Pre-Commit Validation
```bash
python -m pytest tests/ -v  # Must show: 25 passed, 11 skipped
```
- Verify all type hints present on modified code
- Check data format stays `List[Dict[str, Any]]`
- Ensure .gitignore excludes *.parquet, htmlcov/, __pycache__

## Key Files Reference
- **requirements.txt**: Dependencies (install first)
- **setup.py**: Package config (library name: mysql-parquet-lib)
- **Claude.md**: Type safety standards & examples
- **README.md**: Comprehensive usage documentation
- **.gitignore**: Excludes *.parquet, venv/, htmlcov/

## Trust These Instructions
These instructions are complete and validated. Search for more info only if:
- Instructions incomplete for your task
- Encountering undocumented errors  
- Need implementation details beyond what's here

See README.md for usage examples. See Claude.md for type safety patterns.
