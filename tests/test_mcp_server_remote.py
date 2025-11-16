"""Test MCP server remotely via HTTP client."""

import asyncio
import os

from fastmcp import Client


async def test_server():
    """Test the MCP server using streamable-http transport."""
    # Get URL from environment variable or use default
    server_url = os.getenv(
        "MCP_SERVER_URL", "https://dataflow-mcp-server-308763801667.us-central1.run.app/mcp"
    )

    print(f"Connecting to MCP server at: {server_url}")

    try:
        async with Client(server_url) as client:
            # List available tools
            print("\n>>> Listing available tools...")
            tools = await client.list_tools()
            for tool in tools:
                print(f">>> 🛠️  Tool found: {tool.name}")
                if hasattr(tool, "description"):
                    print(f"    Description: {tool.description}")

            # Test health_check tool
            print("\n>>> 🪛  Calling health_check tool...")
            try:
                result = await client.call_tool("health_check", {})
                # CallToolResult has content attribute, not text
                if hasattr(result, "content"):
                    # content is typically a list of TextContent objects
                    if result.content:
                        content_item = result.content[0]
                        text = content_item.text if hasattr(content_item, "text") else content_item
                        print(f"<<< ✅ Result: {text}")
                    else:
                        print(f"<<< ✅ Result: {result}")
                elif hasattr(result, "text"):
                    print(f"<<< ✅ Result: {result.text}")
                else:
                    print(f"<<< ✅ Result: {result}")
            except Exception as e:
                print(f"<<< ❌ Error calling health_check: {e}")
                import traceback

                traceback.print_exc()

            # Test create_dataflow_project tool (with a test directory)
            print("\n>>> 🪛  Calling create_dataflow_project tool...")
            try:
                # Use /tmp for testing to avoid permission issues
                result = await client.call_tool(
                    "create_dataflow_project", {"target_dir": "/tmp/test_dataflow_project"}
                )
                # CallToolResult has content attribute
                if hasattr(result, "content"):
                    if result.content:
                        content_item = result.content[0]
                        text = content_item.text if hasattr(content_item, "text") else content_item
                        print(f"<<< ✅ Result: {text}")
                    else:
                        print(f"<<< ✅ Result: {result}")
                elif hasattr(result, "text"):
                    print(f"<<< ✅ Result: {result.text}")
                else:
                    print(f"<<< ✅ Result: {result}")
            except Exception as e:
                print(f"<<< ❌ Error calling create_dataflow_project: {e}")
                import traceback

                traceback.print_exc()

            # Test list_template_files tool
            print("\n>>> 🪛  Calling list_template_files tool...")
            try:
                result = await client.call_tool("list_template_files", {})
                if hasattr(result, "content"):
                    if result.content:
                        content_item = result.content[0]
                        text = content_item.text if hasattr(content_item, "text") else content_item
                        print(f"<<< ✅ Result (first 500 chars): {text[:500]}")
                    else:
                        print(f"<<< ✅ Result: {result}")
                elif hasattr(result, "text"):
                    print(f"<<< ✅ Result (first 500 chars): {result.text[:500]}")
                else:
                    print(f"<<< ✅ Result: {result}")
            except Exception as e:
                print(f"<<< ❌ Error calling list_template_files: {e}")
                import traceback

                traceback.print_exc()

            # Test get_template_file_content tool
            print("\n>>> 🪛  Calling get_template_file_content tool...")
            test_files = [
                "README.md",
                "pyproject.toml",
                "dataflow_starter_kit/pipeline.py",
            ]
            for file_path in test_files:
                try:
                    print(f"\n>>>   Testing file: {file_path}")
                    result = await client.call_tool(
                        "get_template_file_content", {"file_path": file_path}
                    )
                    if hasattr(result, "content"):
                        if result.content:
                            content_item = result.content[0]
                            text = (
                                content_item.text if hasattr(content_item, "text") else content_item
                            )
                            # Show first 200 chars and total length
                            preview = text[:200].replace("\n", "\\n")
                            print(f"<<< ✅ Success! Content length: {len(text)} chars")
                            print(f"<<<   Preview (first 200 chars): {preview}...")
                        else:
                            print(f"<<< ✅ Result: {result}")
                    elif hasattr(result, "text"):
                        preview = result.text[:200].replace("\n", "\\n")
                        print(f"<<< ✅ Success! Content length: {len(result.text)} chars")
                        print(f"<<<   Preview (first 200 chars): {preview}...")
                    else:
                        print(f"<<< ✅ Result: {result}")
                except Exception as e:
                    print(f"<<< ❌ Error getting file {file_path}: {e}")
                    import traceback

                    traceback.print_exc()

            # Test error cases
            print("\n>>> 🪛  Testing error cases...")
            error_tests = [
                ("non_existent_file.py", "Should return file not found error"),
                ("../outside_file.py", "Should return invalid path error"),
                ("", "Should handle empty path"),
            ]
            for file_path, description in error_tests:
                try:
                    print(f"\n>>>   {description}: {file_path}")
                    result = await client.call_tool(
                        "get_template_file_content", {"file_path": file_path}
                    )
                    if hasattr(result, "content"):
                        if result.content:
                            content_item = result.content[0]
                            text = (
                                content_item.text if hasattr(content_item, "text") else content_item
                            )
                            print(f"<<< ✅ Error handled: {text[:100]}")
                    elif hasattr(result, "text"):
                        print(f"<<< ✅ Error handled: {result.text[:100]}")
                except Exception as e:
                    print(f"<<< ✅ Exception caught: {e}")

    except Exception as e:
        print(f"\n❌ Failed to connect to server: {e}")
        print("Make sure the server is running and accessible.")


if __name__ == "__main__":
    asyncio.run(test_server())
