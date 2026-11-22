"""`python -m mcp_server.abletonbridge_mcp` arranca el servidor MCP stdio (T-016)."""
import sys

from .stdio_server import main

if __name__ == "__main__":
    sys.exit(main())
