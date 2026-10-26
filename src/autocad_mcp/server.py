"""Entry point for the autocad-mcp server.

Run over stdio (the default, and what Claude Desktop and Claude Code launch):

    autocad-mcp

Or over HTTP, for a client on another machine on the same network:

    autocad-mcp --transport http --port 8000
"""

from __future__ import annotations

import argparse
import sys

from . import __version__
from .core.registry import mcp
from .tools import register_all


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="autocad-mcp",
        description=(
            "MCP server connecting Claude to a running AutoCAD on this machine "
            "via its COM Automation interface."
        ),
    )
    parser.add_argument(
        "--transport",
        choices=["stdio", "http"],
        default="stdio",
        help=(
            "stdio (default) for a local client such as Claude Desktop or "
            "Claude Code; http to serve other machines on the network."
        ),
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help=(
            "Interface to bind when --transport http. Defaults to localhost; "
            "AutoCAD control is unauthenticated, so only widen this on a "
            "network you trust."
        ),
    )
    parser.add_argument(
        "--port", type=int, default=8000, help="Port to bind when --transport http."
    )
    parser.add_argument(
        "--list-tools",
        action="store_true",
        help="Print the registered tools and exit, without contacting AutoCAD.",
    )
    parser.add_argument("--version", action="version", version=f"autocad-mcp {__version__}")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    register_all()

    if args.list_tools:
        import asyncio

        tools = asyncio.run(mcp.list_tools())
        print(f"autocad-mcp {__version__} — {len(tools)} tools\n")
        for tool in sorted(tools, key=lambda t: t.name):
            summary = (tool.description or "").strip().splitlines()
            print(f"  {tool.name:<32} {summary[0] if summary else ''}")
        return 0

    if args.transport == "http":
        # Log to stderr: stdout carries protocol traffic on stdio transport,
        # and keeping the habit avoids corrupting it if the flag is dropped.
        print(
            f"autocad-mcp {__version__} serving on http://{args.host}:{args.port}/mcp",
            file=sys.stderr,
        )
        mcp.run(transport="streamable-http", host=args.host, port=args.port)
    else:
        mcp.run(transport="stdio")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
