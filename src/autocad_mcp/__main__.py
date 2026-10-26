"""Allow ``python -m autocad_mcp`` as well as the installed console script."""

from .server import main

if __name__ == "__main__":
    raise SystemExit(main())
