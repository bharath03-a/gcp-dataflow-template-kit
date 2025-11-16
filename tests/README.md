# Testing Guide

This directory contains tests for the dataflow_template MCP server.

## Test Files

- `test_get_template_file_content.py` - Local unit tests for the `get_template_file_content` function
- `test_mcp_server_remote.py` - Remote integration tests via HTTP client

## Running Tests

### 1. Local Unit Tests (Direct Function Testing)

Test the `get_template_file_content` function directly without needing the MCP server:

```bash
# From project root
python tests/test_get_template_file_content.py
```

This will test:
- Reading valid template files (README.md, pyproject.toml, pipeline.py, etc.)
- Error handling (non-existent files, path traversal attempts, etc.)

### 2. Remote Integration Tests (MCP Server via HTTP)

Test the MCP server tools via HTTP client:

```bash
# From project root
python tests/test_mcp_server_remote.py
```

This requires:
- The MCP server to be running (either locally or remote)
- Set `MCP_SERVER_URL` environment variable to override default URL

```bash
# Use custom server URL
MCP_SERVER_URL=https://your-server-url/mcp python tests/test_mcp_server_remote.py
```

This will test:
- `health_check` tool
- `create_dataflow_project` tool
- `list_template_files` tool
- `get_template_file_content` tool
- Error cases for all tools

### 3. Using Pytest (Optional)

If you have `pytest` installed, you can run tests with pytest:

```bash
# Install pytest (optional)
pip install pytest

# Run all tests
pytest tests/

# Run specific test file
pytest tests/test_get_template_file_content.py

# Run with verbose output
pytest tests/ -v

# Run with coverage (if pytest-cov is installed)
pytest tests/ --cov=mcp_server --cov-report=html
```

## Quick Test Commands

```bash
# Test template file reading locally
python tests/test_get_template_file_content.py

# Test remote MCP server (default URL)
python tests/test_mcp_server_remote.py

# Test remote MCP server (custom URL)
MCP_SERVER_URL=http://localhost:8000/mcp python tests/test_mcp_server_remote.py
```

## Adding New Tests

1. Create test files with prefix `test_*.py`
2. Import functions from `mcp_server.mcp_server`
3. Use pytest-style test functions or direct execution with `if __name__ == "__main__"`
4. The `conftest.py` handles path setup automatically

