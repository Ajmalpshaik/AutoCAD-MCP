"""Option definitions and payload helpers shared across tool modules.

The layer / colour / linetype / space options appear on most creation tools.
Defining them once means the wording an agent reads is identical everywhere,
and a change to the guidance lands in every tool at once.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from pydantic import Field

from ..acad.entities import describe
from ..core.errors import AutocadError
from ..core.variants import apoint

LAYER_OPT = Field(
    default=None,
    description=(
        "Layer to draw on. Created automatically if it does not exist. "
        "Omit to use the drawing's current layer."
    ),
)

COLOR_OPT = Field(
    default=None,
    description=(
        "Colour as a name ('red', 'green', 'cyan', 'bylayer') or an AutoCAD "
        "Color Index number 0-256. Omit to inherit from the layer."
    ),
)

LINETYPE_OPT = Field(
    default=None,
    description=(
        "Linetype name such as 'CONTINUOUS', 'HIDDEN', 'CENTER', 'DASHED'. "
        "Loaded from AutoCAD's linetype file automatically if needed."
    ),
)

SPACE_OPT = Field(
    default="model",
    description="'model' for model space, or 'paper' for the current layout.",
    pattern="^(model|paper)$",
)

HANDLES_OPT = Field(
    description=(
        "Handles of the entities to act on, e.g. ['1A4', '1A5']. Get them from "
        "autocad_list_entities, autocad_get_selection, or from the tool that "
        "created the entity."
    ),
    min_length=1,
)


def point(value: Sequence[float] | None, name: str) -> Any:
    """Validate a coordinate list and convert it to AutoCAD's point VARIANT."""
    if not value or len(value) < 2:
        raise AutocadError(
            f"'{name}' must be a coordinate list of at least [x, y], got {value!r}."
        )
    z = float(value[2]) if len(value) > 2 else 0.0
    return apoint(float(value[0]), float(value[1]), z)


def created_payload(
    entity: Any, notes: dict[str, Any], **extra: Any
) -> dict[str, Any]:
    """Uniform success payload for every creation tool.

    Each creation tool returns the new entity's handle in the same field, so
    results chain directly into the modify, query and hatch tools.
    """
    payload: dict[str, Any] = {
        "created": True,
        "handle": str(entity.Handle),
        "type": describe(entity, include_geometry=False)["type"],
        "layer": str(entity.Layer),
    }
    payload.update({k: v for k, v in extra.items() if v is not None})
    payload.update(notes)
    # Read the new object back by its handle: a reply that says "created" is
    # only trusted once the drawing agrees.
    try:
        found = entity.Document.HandleToObject(payload["handle"])
        payload["verified"] = str(found.ObjectName) == str(entity.ObjectName)
    except Exception:  # noqa: BLE001 - any failure to read back is the finding
        payload["verified"] = False
    if not payload["verified"]:
        payload["warning"] = (
            f"The new object {payload['handle']} could not be read back from the "
            "drawing. Check it with autocad_get_entity before building on it."
        )
    return payload
