"""Simple MCP client for testing."""

import asyncio
import sys
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def test_hello_server():
    """Test hello world MCP server."""
    print("Connecting to hello-world server...")

    project_root = Path(__file__).resolve().parents[2]
    server_script = project_root / "src" / "mcp" / "hello_server.py"

    # Server parameters
    server_params = StdioServerParameters(
        command=sys.executable,
        args=[str(server_script)],
        cwd=str(project_root),
    )

    # Connect to server
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # Initialize
            await session.initialize()

            # List available tools
            tools = await session.list_tools()
            print("\nAvailable tools:")
            for tool in tools.tools:
                print(f"  - {tool.name}: {tool.description}")

            # Call greet tool
            print("\nCalling 'greet' tool...")
            result = await session.call_tool("greet", {"name": "Alice"})
            print(f"   Result: {result.content[0].text}")

            # Call add tool
            print("\nCalling 'add' tool...")
            result = await session.call_tool("add", {"a": 5, "b": 3})
            print(f"   Result: {result.content[0].text}")

            print("\nMCP communication working!")


if __name__ == "__main__":
    asyncio.run(test_hello_server())
