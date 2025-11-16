"""Test script for get_template_file_content function."""

import sys
from pathlib import Path

# Add the project root to the path so we can import mcp_server
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from mcp_server.mcp_server import get_template_file_content  # noqa: E402


def test_get_template_file_content():
    """Test get_template_file_content function directly."""
    print("Testing get_template_file_content function\n")
    print("=" * 60)

    # Test valid files
    test_files = [
        "README.md",
        "pyproject.toml",
        "Dockerfile",
        "dataflow_starter_kit/pipeline.py",
        "dataflow_starter_kit/__init__.py",
        "dataflow_starter_kit/transforms/transform.py",
        "dataflow_starter_kit/utils/config.py",
    ]

    print("\n1. Testing valid files:")
    print("-" * 60)
    for file_path in test_files:
        print(f"\n📄 Testing: {file_path}")
        try:
            result = get_template_file_content(file_path)
            if result.startswith("Error:"):
                print(f"   ❌ Error: {result}")
            else:
                preview = result[:100].replace("\n", "\\n")
                print(f"   ✅ Success! Content length: {len(result)} chars")
                print(f"   Preview: {preview}...")
        except Exception as e:
            print(f"   ❌ Exception: {e}")

    # Test error cases
    print("\n\n2. Testing error cases:")
    print("-" * 60)
    error_tests = [
        ("non_existent_file.py", "Non-existent file"),
        ("../outside_file.py", "Path traversal attempt"),
        ("../../etc/passwd", "Path traversal attempt"),
        ("", "Empty path"),
        ("/absolute/path/file.py", "Absolute path"),
    ]

    for file_path, description in error_tests:
        print(f"\n🚫 {description}: {file_path}")
        try:
            result = get_template_file_content(file_path)
            if result.startswith("Error:") or "not found" in result:
                print(f"   ✅ Error correctly handled: {result[:80]}")
            else:
                print(f"   ⚠️  Unexpected result: {result[:80]}")
        except Exception as e:
            print(f"   ⚠️  Exception raised: {e}")

    print("\n" + "=" * 60)
    print("Testing complete!")


if __name__ == "__main__":
    test_get_template_file_content()
