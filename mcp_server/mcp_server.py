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

    Path resolution:
    - Local: Resolves to <project_root>/template_files/
    - Docker/Remote: Resolves to /app/template_files/ (template_files copied to container)

    The template files are bundled with the server code, so they exist in the same
    filesystem whether running locally or in a remote Docker container.

    Checks in order:
    1. Relative to this file (local development or Docker: parent.parent/template_files)
    2. Environment variable DATAFLOW_TEMPLATE_DIR
    3. Default relative path (fallback)

    Returns:
        Path to template directory (may not exist)
    """
    # Calculate path relative to this file location
    # Local: <project_root>/mcp_server/mcp_server.py -> <project_root>/template_files/
    # Docker: /app/mcp_server/mcp_server.py -> /app/template_files/
    local_template = Path(__file__).parent.parent / TEMPLATE_DIR_NAME
    logger.debug(
        f"Resolving template directory: __file__={__file__}, "
        f"computed path={local_template}, exists={local_template.exists()}"
    )

    if local_template.exists():
        logger.info(f"Template directory found at: {local_template} (relative to code)")
        return local_template

    env_template = os.getenv("DATAFLOW_TEMPLATE_DIR")
    if env_template:
        env_path = Path(env_template)
        if env_path.exists():
            logger.info(f"Template directory found via env var: {env_path}")
            return env_path

    logger.warning(
        f"Template directory not found at {local_template}, "
        "but returning path anyway (may fail later)"
    )
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


def is_remote_server() -> bool:
    """
    Check if the server is running in remote mode (HTTP/SSE) vs local (stdio).

    Returns:
        True if running remotely, False if running locally
    """
    transport_str = os.getenv("MCP_TRANSPORT", DEFAULT_TRANSPORT).lower()
    if transport_str == "http":
        transport_str = "streamable-http"
    return transport_str in ("streamable-http", "sse")


@mcp.tool()
async def create_dataflow_project(target_dir: str = ".") -> str:
    """
    Creates a Dataflow project from the template.

    When running locally (stdio): Creates files in the target directory.
    When running remotely (HTTP/Cloud Run): Returns instructions and file contents
    for the agent to create files locally.

    Args:
        target_dir: Target directory where the project should be created.
                   Defaults to current directory.

    Returns:
        Success message with file creation details, or instructions for remote mode.
    """
    try:
        template_dir = get_template_dir()
        logger.info(f"Looking for template at: {template_dir}")

        error = validate_template_dir(template_dir)
        if error:
            logger.error(error)
            return error

        # If running remotely, return instructions instead of creating files
        if is_remote_server():
            return _get_remote_creation_instructions(template_dir, target_dir)

        # Local mode: actually create the files
        target_path = Path(target_dir).expanduser().resolve()
        error = validate_target_path(target_path)
        if error:
            logger.error(error)
            return error

        logger.info(f"Creating Dataflow project at: {target_path}")
        try:
            # Ensure target directory exists
            target_path.mkdir(parents=True, exist_ok=True)

            # Copy contents of template_dir into target_path (not the directory itself)
            for item in template_dir.iterdir():
                # Skip hidden files and __pycache__
                if item.name.startswith(".") or item.name == "__pycache__":
                    continue

                dest_item = target_path / item.name
                if item.is_dir():
                    shutil.copytree(item, dest_item, dirs_exist_ok=True)
                else:
                    shutil.copy2(item, dest_item)
        except PermissionError as e:
            return handle_error(e, "Permission denied when creating project")
        except shutil.Error as e:
            return handle_error(e, "Error copying template files")
        except Exception as e:
            return handle_error(e, "Unexpected error")

        success_msg = f"Dataflow project created successfully at: {target_path}"
        logger.info(success_msg)
        return success_msg

    except PermissionError as e:
        return handle_error(e, "Permission denied when creating project")
    except shutil.Error as e:
        return handle_error(e, "Error copying template files")
    except Exception as e:
        return handle_error(e, "Unexpected error")


def _get_remote_creation_instructions(template_dir: Path, target_dir: str) -> str:
    """
    Generate instructions for creating the project when running remotely.

    Args:
        template_dir: Path to template directory
        target_dir: Target directory name

    Returns:
        Instructions with file structure and contents
    """
    try:
        instructions = []
        instructions.append(
            f"Create Dataflow project in '{target_dir}' directory with the following structure:\n"
        )

        # Get file structure
        files_info = []
        for root, dirs, filenames in os.walk(template_dir):
            dirs[:] = [d for d in dirs if not d.startswith(".") and d != "__pycache__"]
            for filename in filenames:
                if filename.startswith(".") or filename.endswith(".pyc"):
                    continue
                file_path = Path(root) / filename
                relative_path = file_path.relative_to(template_dir)
                files_info.append(str(relative_path))

        instructions.append(f"Files to create ({len(files_info)} files):")
        for file_path in sorted(files_info):
            instructions.append(f"  - {target_dir}/{file_path}")

        instructions.append("\n" + "=" * 80)
        instructions.append("CRITICAL: This server is running remotely. You MUST use MCP tools!")
        instructions.append("=" * 80)
        instructions.append("\n⚠️  DO NOT:")
        instructions.append("  - Try to read files using local file paths")
        instructions.append("  - Use read_file() with template paths")
        instructions.append("  - Assume template files exist in your workspace")
        instructions.append("\n✅ DO:")
        instructions.append("  - Call MCP tools: 'get_template_file_content'")
        instructions.append("  - Pass template-relative paths (e.g., 'README.md')")
        instructions.append("  - Use the exact tool name and parameter format below")
        instructions.append("\n📋 STEP-BY-STEP:")
        instructions.append("\n1. For each file above, call the MCP tool:")
        instructions.append('   Tool: "get_template_file_content"')
        instructions.append('   Parameter: {"file_path": "<template_relative_path>"}')
        instructions.append("\n2. The tool returns the file content as a string.")
        instructions.append(
            f"\n3. Create the file locally at: {target_dir}/<template_relative_path>"
        )
        instructions.append("   Use the content returned by the tool.")
        instructions.append("\n4. Repeat for all files listed above.")
        instructions.append("\n📝 CONCRETE EXAMPLES:")
        instructions.append("\nTo create README.md:")
        instructions.append('  → Call: get_template_file_content({"file_path": "README.md"})')
        instructions.append("  → Tool returns: file content string")
        instructions.append(f"  → Create file: {target_dir}/README.md with returned content")
        instructions.append("\nTo create dataflow_starter_kit/pipeline.py:")
        instructions.append(
            "  → Call: get_template_file_content("
            '{"file_path": "dataflow_starter_kit/pipeline.py"})'
        )
        instructions.append("  → Tool returns: file content string")
        instructions.append(
            f"  → Create file: {target_dir}/dataflow_starter_kit/pipeline.py "
            "with returned content"
        )
        instructions.append(
            "\n💡 NOTE: The file_path parameter is relative to the template directory "
            "on the server, NOT a local filesystem path. The server has its own copy "
            "of template files bundled with the code."
        )

        return "\n".join(instructions)
    except Exception as e:
        logger.exception("Error generating remote instructions")
        return f"Error generating instructions: {str(e)}"


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


@mcp.tool()
def list_template_files() -> str:
    """
    List all files in the template directory with folder structure.

    Returns:
        JSON string with list of file paths and folder structure
    """
    try:
        import json

        template_dir = get_template_dir()
        error = validate_template_dir(template_dir)
        if error:
            return error

        files = []
        dirs_list = []
        structure = {"files": [], "directories": [], "tree": ""}

        def build_tree_string(path: Path, prefix: str = "", is_last: bool = True) -> str:
            """Build a tree string representation."""
            lines = []
            connector = "└── " if is_last else "├── "
            item_name = f"{path.name}/" if path.is_dir() else path.name
            lines.append(f"{prefix}{connector}{item_name}")

            if path.is_dir():
                extension = "    " if is_last else "│   "
                filtered_items = [
                    p
                    for p in path.iterdir()
                    if not p.name.startswith(".") and p.name != "__pycache__"
                ]
                children = sorted(filtered_items)
                for i, child in enumerate(children):
                    is_last_child = i == len(children) - 1
                    child_result = build_tree_string(child, prefix + extension, is_last_child)
                    lines.extend(child_result.split("\n"))

            return "\n".join(lines)

        # Build flat list and tree structure
        for root, dirs, filenames in os.walk(template_dir):
            # Filter hidden and cache directories
            dirs[:] = [d for d in dirs if not d.startswith(".") and d != "__pycache__"]

            for dirname in dirs:
                dir_path = Path(root) / dirname
                rel_path = dir_path.relative_to(template_dir)
                if str(rel_path) not in dirs_list:
                    dirs_list.append(str(rel_path))

            for filename in filenames:
                if filename.startswith(".") or filename.endswith(".pyc"):
                    continue
                file_path = Path(root) / filename
                relative_path = file_path.relative_to(template_dir)
                files.append(str(relative_path))

        # Build tree string starting from template root
        tree_lines = [f"{template_dir.name}/"]
        filtered_items = [
            p
            for p in template_dir.iterdir()
            if not p.name.startswith(".") and p.name != "__pycache__"
        ]
        children = sorted(filtered_items)
        for i, child in enumerate(children):
            is_last = i == len(children) - 1
            tree_lines.append(build_tree_string(child, "", is_last))

        structure["files"] = sorted(files)
        structure["directories"] = sorted(dirs_list)
        structure["tree"] = "\n".join(tree_lines)

        return json.dumps(structure, indent=2)
    except Exception as e:
        return handle_error(e, "Error listing template files")


@mcp.tool()
def get_template_file_content(file_path: str) -> str:
    """
    Get the content of a specific template file from the server's template directory.

    How it works:
    - Template files are bundled with the server code (copied into Docker container)
    - When you pass "README.md", server resolves to <template_dir>/README.md
    - In Docker: <template_dir> = /app/template_files/ (copied during Docker build)
    - Server reads from its own filesystem and returns content to you
    - Cursor/agent receives the file content and can create it locally

    IMPORTANT: The file_path is relative to the template directory on the SERVER,
    NOT a path on your local machine. The server has its own copy of template files
    bundled with the code (see Dockerfile line 22: COPY template_files/).

    Args:
        file_path: Template-relative path within server's template directory.
                  Examples:
                  - "README.md" -> resolves to /app/template_files/README.md (in Docker)
                  - "dataflow_starter_kit/pipeline.py"
                  - "dataflow_starter_kit/transforms/transform.py"
                  DO NOT use absolute paths or local filesystem paths.

    Returns:
        File content as string, or error message if file not found or invalid path.
    """
    try:
        template_dir = get_template_dir()
        logger.debug(
            f"get_template_file_content: template_dir={template_dir}, "
            f"requested_file={file_path}"
        )
        error = validate_template_dir(template_dir)
        if error:
            logger.error(f"Template directory validation failed: {error}")
            return error

        file_path_obj = Path(file_path)
        # Prevent path traversal attacks
        if ".." in str(file_path_obj) or file_path_obj.is_absolute():
            logger.warning(f"Invalid file path attempted: {file_path}")
            return "Error: Invalid file path"

        full_path = template_dir / file_path_obj
        logger.debug(f"Resolved full path: {full_path} (exists={full_path.exists()})")
        if not full_path.exists():
            logger.warning(f"File not found: {full_path} (template_dir={template_dir})")
            return f"Error: File not found: {file_path}"

        if not full_path.is_file():
            return f"Error: Path is not a file: {file_path}"

        # Ensure the file is within the template directory
        try:
            full_path.resolve().relative_to(template_dir.resolve())
        except ValueError:
            return "Error: Invalid file path"

        content = full_path.read_text(encoding="utf-8")
        return content
    except UnicodeDecodeError:
        return f"Error: File is not a text file: {file_path}"
    except Exception as e:
        logger.exception(f"Error reading template file: {file_path}")
        return f"Error reading file: {str(e)}"


def get_all_template_files() -> list[str]:
    """
    Get list of all template file paths relative to template directory.

    Returns:
        List of relative file paths
    """
    try:
        template_dir = get_template_dir()
        error = validate_template_dir(template_dir)
        if error:
            return []

        files = []
        for root, dirs, filenames in os.walk(template_dir):
            dirs[:] = [d for d in dirs if not d.startswith(".") and d != "__pycache__"]
            for filename in filenames:
                if filename.startswith(".") or filename.endswith(".pyc"):
                    continue
                file_path = Path(root) / filename
                relative_path = file_path.relative_to(template_dir)
                files.append(str(relative_path))

        return sorted(files)
    except Exception:
        logger.exception("Error getting template files")
        return []


@mcp.resource("template://{file_path}")
async def get_template_file_resource(file_path: str) -> str:
    """
    Get the content of a template file as a resource.

    This allows agents to read template files directly via MCP resources.
    Access using URI: template://path/to/file

    Args:
        file_path: Relative path to the file within the template directory

    Returns:
        File content as string
    """
    try:
        template_dir = get_template_dir()
        error = validate_template_dir(template_dir)
        if error:
            return f"Error: {error}"

        file_path_obj = Path(file_path)
        # Prevent path traversal attacks
        if ".." in str(file_path_obj) or file_path_obj.is_absolute():
            return "Error: Invalid file path"

        full_path = template_dir / file_path_obj
        if not full_path.exists():
            return f"Error: File not found: {file_path}"

        if not full_path.is_file():
            return f"Error: Path is not a file: {file_path}"

        # Ensure the file is within the template directory
        try:
            full_path.resolve().relative_to(template_dir.resolve())
        except ValueError:
            return "Error: Invalid file path"

        content = full_path.read_text(encoding="utf-8")
        return content
    except UnicodeDecodeError:
        return f"Error: File is not a text file: {file_path}"
    except Exception as e:
        logger.exception(f"Error reading template file: {file_path}")
        return f"Error reading file: {str(e)}"


# Note: Template resources are handled by the @mcp.resource decorator above
# which uses a template pattern "template://{file_path}". This allows agents
# to access any template file using the URI pattern.
# Agents should use list_template_files() tool first to discover available files,
# then access them via template:// URIs or get_template_file_content() tool.


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
