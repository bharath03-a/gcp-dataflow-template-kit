# Dataflow Template MCP Server

MCP server for creating standardized Dataflow projects via AI coding assistants.

## Usage

This server is designed to be used by AI coding assistants (Cursor, Claude Desktop, etc.), not for manual interaction.

### For AI Assistants (Local/Stdio)

Add this to your MCP client configuration:

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

### Hosted Deployment (HTTP/SSE)

The server can be hosted online and accessed via HTTP or SSE transport.

#### Environment Variables

- `MCP_TRANSPORT`: Transport type - `stdio` (default), `http`, or `sse`
- `MCP_HOST`: Host to bind to (default: `0.0.0.0`)
- `MCP_PORT`: Port to bind to (default: `8000`)
- `DATAFLOW_TEMPLATE_DIR`: Optional override for template directory path

#### Running as HTTP Server

```bash
# Set environment variables
export MCP_TRANSPORT=http
export MCP_HOST=0.0.0.0
export MCP_PORT=8000

# Run the server
python -m mcp_server.mcp_server
```

#### Running as SSE Server

```bash
export MCP_TRANSPORT=sse
python -m mcp_server.mcp_server
```

#### Docker Deployment

```dockerfile
FROM python:3.12-slim

WORKDIR /app
COPY . .
RUN pip install -e .

ENV MCP_TRANSPORT=http
ENV MCP_HOST=0.0.0.0
ENV MCP_PORT=8000

EXPOSE 8000
CMD ["python", "-m", "mcp_server.mcp_server"]
```

#### Cloud Deployment Examples

**Cloud Run:**

```bash
gcloud run deploy dataflow-mcp-server \
  --source . \
  --set-env-vars MCP_TRANSPORT=http,MCP_PORT=8000 \
  --port 8000
```

**Docker Compose:**

```yaml
version: "3.8"
services:
  mcp-server:
    build: .
    ports:
      - "8000:8000"
    environment:
      - MCP_TRANSPORT=http
      - MCP_HOST=0.0.0.0
      - MCP_PORT=8000
      - DATAFLOW_TEMPLATE_DIR=/app/template_files
```

### Available Tools

- **create_dataflow_project**: Creates a new Dataflow project from the template
  - Parameters:
    - `target_dir` (optional): Target directory where the project should be created. Defaults to current directory.
- **health_check**: Check if MCP server is running and template is accessible

### Manual Testing

For manual testing, use the CLI instead:

```bash
python -m cli.cli create my-project
# or
dataflow-create create my-project
```

### Error Handling

The server includes comprehensive error handling:

- Validates template directory exists
- Handles permission errors
- Validates target directory paths
- Provides detailed error messages with logging

### Logging

The server logs all operations at INFO level. Logs include:

- Server startup configuration
- Template directory resolution
- Project creation attempts
- Error details
