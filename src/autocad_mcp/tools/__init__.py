"""MCP tool definitions, grouped by subject.

Importing this package registers every tool onto the shared FastMCP instance in
``core.registry`` — the decorators run at import time, so ``register_all()``
only has to make sure each module is imported once.
"""

from __future__ import annotations


def register_all() -> None:
    """Import every tool module, registering its tools on the shared server."""
    from . import (  # noqa: F401
        advanced,
        annotate,
        batch,
        blocks,
        convert,
        coordinates,
        dimensions,
        document,
        drafting,
        draw,
        drawing_tools,
        geometry_tools,
        labels,
        layers,
        materials,
        modify,
        patterns,
        query,
        resources,
        sequence,
        settings,
        shapes,
        sheets,
        solids,
        standards,
        takeoff,
        text_tools,
        views,
        xrefs,
    )


__all__ = ["register_all"]
