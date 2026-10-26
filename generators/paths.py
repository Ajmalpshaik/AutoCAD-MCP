"""Folder locations shared by every generator, worked out from this file.

Nothing here is typed as a drive letter, so the repository runs from any folder.
"""
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SERVER = os.path.join(ROOT, ".venv", "Scripts", "autocad-mcp.exe")
DRAWINGS = os.path.join(ROOT, "drawings")
AHU_OUT = os.path.join(DRAWINGS, "AHU")
CCTV_OUT = os.path.join(DRAWINGS, "CCTV")
ENCL_OUT = os.path.join(CCTV_OUT, "ENCLOSURE")

# drawings/ is not in git (docs/DECISIONS.md D-11), so a fresh clone has none of these yet
for _folder in (AHU_OUT, CCTV_OUT, ENCL_OUT):
    os.makedirs(_folder, exist_ok=True)
