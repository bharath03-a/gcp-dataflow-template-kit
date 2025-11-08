"""
MCP server for Dataflow Template Toolkit.

Enables AI coding agents (Cursor, Copilot, Claude) to create standard
Dataflow projects automatically.
"""

import logging
import os
import shutil
from enum import Enum
from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP

TEMPLATE_DIR_NAME = "template_files"
DEFAULT_TRANSPORT = "stdio"
DEFAULT_HOST = "0.0.0.0"
DEFAULT_PORT = 8000

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

mcp = FastMCP[Any](name="Dataflow Template MCP", stateless_http=True)


class TransportType(str, Enum):
    """Supported transport types for the MCP server."""

    STDIO = "stdio"
    HTTP = "streamable-http"
    SSE = "sse"


def get_template_dir() -> Path:
    """
    Get the template directory path, handling both local and installed deployments.

    Checks in order:
    1. Relative to this file (local development)
    2. Environment variable DATAFLOW_TEMPLATE_DIR
    3. Default relative path (fallback)

    Returns:
        Path to template directory (may not exist)
    """
    local_template = Path(__file__).parent.parent / TEMPLATE_DIR_NAME
    if local_template.exists():
        return local_template

    env_template = os.getenv("DATAFLOW_TEMPLATE_DIR")
    if env_template:
        env_path = Path(env_template)
        if env_path.exists():
            return env_path

    return local_template


def validate_template_dir(template_dir: Path) -> str | None:
    """
    Validate that the template directory exists and is accessible.

    Args:
        template_dir: Path to validate

    Returns:
        Error message if validation fails, None otherwise
    """
    if not template_dir.exists():
        return (
            f"Template directory not found at {template_dir}. "
            "Please ensure template_files directory exists or set "
            "DATAFLOW_TEMPLATE_DIR environment variable."
        )

    if not template_dir.is_dir():
        return f"Template path exists but is not a directory: {template_dir}"

    return None


def validate_target_path(target_path: Path) -> str | None:
    """
    Validate that the target path is valid for creating a project.

    Args:
        target_path: Target path to validate

    Returns:
        Error message if validation fails, None otherwise
    """
    if not target_path.parent.exists():
        return f"Parent directory does not exist: {target_path.parent}"

    return None


def handle_error(error: Exception, context: str) -> str:
    """
    Handle and log errors consistently.

    Args:
        error: The exception that occurred
        context: Contextual information about where the error occurred

    Returns:
        Formatted error message for the user
    """
    error_msg = f"{context}: {str(error)}"
    logger.error(error_msg, exc_info=True)
    return error_msg


@mcp.tool()
async def create_dataflow_project(target_dir: str = ".") -> str:
    """
    Copies the standard Dataflow template into the given target directory.

    Args:
        target_dir: Target directory where the project should be created.
                   Defaults to current directory.

    Returns:
        Success or error message.
    """
    try:
        template_dir = get_template_dir()
        logger.info(f"Looking for template at: {template_dir}")

        error = validate_template_dir(template_dir)
        if error:
            logger.error(error)
            return error

        target_path = Path(target_dir).expanduser().resolve()
        error = validate_target_path(target_path)
        if error:
            logger.error(error)
            return error

        logger.info(f"Creating Dataflow project at: {target_path}")
        shutil.copytree(template_dir, target_path, dirs_exist_ok=True)

        success_msg = f"Dataflow project created successfully at: {target_path}"
        logger.info(success_msg)
        return success_msg

    except PermissionError as e:
        return handle_error(e, "Permission denied when creating project")
    except shutil.Error as e:
        return handle_error(e, "Error copying template files")
    except Exception as e:
        return handle_error(e, "Unexpected error")


@mcp.tool()
def health_check() -> str:
    """
    Check if MCP server is running and template is accessible.

    Returns:
        Status message indicating server and template availability
    """
    try:
        template_dir = get_template_dir()
        if template_dir.exists():
            return f"MCP server is alive. Template found at: {template_dir}"
        return f"MCP server is alive, but template not found at: {template_dir}"
    except Exception as e:
        logger.exception("Error in health check")
        return f"MCP server is alive, but health check failed: {str(e)}"


def get_server_config() -> tuple[TransportType, str, int]:
    """
    Get server configuration from environment variables.

    Cloud Run compatibility: Checks PORT env var first (set by Cloud Run),
    then falls back to MCP_PORT.

    Returns:
        Tuple of (transport_type, host, port)
    """
    transport_str = os.getenv("MCP_TRANSPORT", DEFAULT_TRANSPORT).lower()
    # Map "http" to "streamable-http" for backward compatibility
    if transport_str == "http":
        transport_str = "streamable-http"

    try:
        transport = TransportType(transport_str)
    except ValueError:
        logger.warning(f"Invalid transport '{transport_str}', defaulting to {DEFAULT_TRANSPORT}")
        transport = TransportType.STDIO

    host = os.getenv("MCP_HOST", DEFAULT_HOST)
    # Cloud Run sets PORT environment variable, check that first
    port_str = os.getenv("PORT") or os.getenv("MCP_PORT", str(DEFAULT_PORT))
    try:
        port = int(port_str)
    except ValueError:
        logger.warning(f"Invalid port '{port_str}', defaulting to {DEFAULT_PORT}")
        port = DEFAULT_PORT

    return transport, host, port


def run_server():
    """Run the MCP server with the configured transport."""
    transport, host, port = get_server_config()

    if transport == TransportType.STDIO:
        logger.info("Starting stdio server")
        mcp.run(transport=transport.value)
    elif transport == TransportType.HTTP:
        # For HTTP transport, use uvicorn with the ASGI app
        import uvicorn

        logger.info(f"Starting HTTP server on {host}:{port}")
        app = mcp.streamable_http_app()
        uvicorn.run(app, host=host, port=port, log_level="info")
    elif transport == TransportType.SSE:
        logger.info(f"Starting SSE server on {host}:{port}")
        # For SSE, use the SSE app with uvicorn
        import uvicorn

        app = mcp.sse_app()
        uvicorn.run(app, host=host, port=port, log_level="info")
    else:
        raise ValueError(f"Unsupported transport type: {transport}")


def main():
    """Main entry point for the MCP server."""
    run_server()


if __name__ == "__main__":
    main()
