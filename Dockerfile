# Use Python 3.12 slim image for smaller size
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies if needed
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency files first for better layer caching
COPY pyproject.toml ./

# Install dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -e .

# Copy application code
COPY mcp_server/ ./mcp_server/
COPY cli/ ./cli/
COPY template_files/ ./template_files/

# Set environment variables for Cloud Run
ENV MCP_TRANSPORT=streamable-http
ENV MCP_HOST=0.0.0.0
# PORT will be set by Cloud Run automatically

# Expose port (Cloud Run will override this, but good practice)
EXPOSE 8080

# Run the MCP server
CMD ["python", "-m", "mcp_server.mcp_server"]

