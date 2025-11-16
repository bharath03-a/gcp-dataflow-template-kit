# Dataflow Template MCP Server

MCP server and CLI tool for creating standardized Dataflow projects from templates. Created to help developers get started on a standard format without worrying much about the structure of their pipeline package and its deployment setup.

## What's Included

- MCP server for AI coding assistants (Cursor, Claude, etc.)
- CLI tool for manual project creation
- Standardized Dataflow template structure
- GitHub Actions workflow for automated deployment

## Getting Started

Clone the repository:

```bash
git clone https://github.com/bharath03-a/gcp-dataflow-template-kit
cd gcp-dataflow-template-kit
```

## Installation

```bash
# Install dependencies
pip install -e .

# Or using uv
uv sync

# Install pre-commit hooks
pre-commit install
```

## Usage

### CLI Tool

Create a new Dataflow project:

```bash
dataflow-create create /path/to/new-project
```

Or run the template locally:

```bash
dataflow-create run-template
```

### MCP Server (Local/Stdio)

Add to your MCP client configuration (e.g., `~/.cursor/mcp.json`):

```json
{
  "mcpServers": {
    "dataflow-template": {
      "command": "python",
      "args": ["-m", "mcp_server.mcp_server"],
      "cwd": "/path/to/dataflow_template"
    }
  }
}
```

### MCP Server (HTTP/Cloud Run)

The server can run as an HTTP service for remote access.

Set environment variables:

```bash
export MCP_TRANSPORT=streamable-http
export MCP_HOST=0.0.0.0
export MCP_PORT=8000
```

Run the server:

```bash
python -m mcp_server.mcp_server
```

## Deployment

### Local Docker Build

```bash
docker build -t dataflow-mcp-server .
docker run -p 8080:8080 \
  -e MCP_TRANSPORT=streamable-http \
  -e MCP_HOST=0.0.0.0 \
  dataflow-mcp-server
```

### Cloud Run Deployment

The project includes a GitHub Actions workflow for automatic deployment to Cloud Run.

1. Set up GitHub Secrets:

   - `GCP_PROJECT_ID`: Your Google Cloud project ID
   - `GCP_SA_KEY`: Service account JSON key

2. Push to main branch to trigger deployment

3. Manual deployment:

```bash
gcloud run deploy dataflow-mcp-server \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars MCP_TRANSPORT=streamable-http \
  --port 8080
```

## Testing

Test the MCP server:

```bash
python tests/test_mcp_server_remote.py
```

Set `MCP_SERVER_URL` environment variable to test against a remote server.

## Project Structure

```
.
├── mcp_server/          # MCP server implementation
├── cli/                 # CLI tool
├── template_files/      # Dataflow template files
├── tests/               # Test script
├── .github/workflows/   # GitHub Actions workflow
└── Dockerfile           # Docker configuration
```

## Development

Run linting:

```bash
ruff check .
ruff format .
```

## Available Tools

- `create_dataflow_project`: Creates a new Dataflow project from the template
- `health_check`: Checks if the MCP server is running and template is accessible

---

With love, from a fellow frustrated data engineer
