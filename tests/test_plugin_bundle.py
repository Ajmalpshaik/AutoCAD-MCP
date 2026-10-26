"""The HeronAutoCAD.bundle layout and the installer, without AutoCAD."""

from __future__ import annotations

import importlib.util
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def _load(name: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / "tools" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


build = _load("build_plugin")
install = _load("install_plugin")


@pytest.fixture
def built(tmp_path):
    folders = {}
    for tfm in ("net48", "net8.0-windows", "net10.0-windows"):
        folder = tmp_path / "bin" / tfm
        (folder / "Resources").mkdir(parents=True)
        (folder / "Heron.AutoCAD.Addin.dll").write_bytes(b"MZ")
        (folder / "Resources" / "BridgeConnected.png").write_bytes(b"png")
        folders[tfm] = folder
    return folders


def test_bundle_has_one_folder_per_autocad_series(built, tmp_path):
    bundle = build.make_bundle(built, tmp_path / "dist")
    assert bundle.name == "HeronAutoCAD.bundle"
    for series in ("R24", "R25", "R26"):
        assert (bundle / "Contents" / series / "Heron.AutoCAD.Addin.dll").is_file()
        assert (bundle / "Contents" / series / "Resources" / "BridgeConnected.png").is_file()


def test_package_contents_maps_versions_to_builds(built, tmp_path):
    bundle = build.make_bundle(built, tmp_path / "dist")
    root = ET.parse(bundle / "PackageContents.xml").getroot()
    rows = []
    for components in root.findall("Components"):
        req = components.find("RuntimeRequirements")
        entry = components.find("ComponentEntry")
        rows.append((req.get("SeriesMin"), req.get("SeriesMax"), entry.get("ModuleName"), entry.get("LoadOnAutoCADStartup")))
    assert rows == [
        ("R24.0", "R24.3", "./Contents/R24/Heron.AutoCAD.Addin.dll", "True"),
        ("R25.0", "R25.1", "./Contents/R25/Heron.AutoCAD.Addin.dll", "True"),
        ("R26.0", "R26.9", "./Contents/R26/Heron.AutoCAD.Addin.dll", "True"),
    ]
    assert root.get("Name") == "Heron AI for AutoCAD"


def test_rebuilding_replaces_the_old_bundle(built, tmp_path):
    bundle = build.make_bundle(built, tmp_path / "dist")
    (bundle / "Contents" / "R24" / "stale.dll").write_bytes(b"old")
    bundle = build.make_bundle(built, tmp_path / "dist")
    assert not (bundle / "Contents" / "R24" / "stale.dll").exists()


def test_install_refuses_while_autocad_runs(built, tmp_path, monkeypatch):
    bundle = build.make_bundle(built, tmp_path / "dist")
    monkeypatch.setattr(install, "autocad_running", lambda: True)
    with pytest.raises(SystemExit) as err:
        install.install(bundle, tmp_path / "plugins")
    assert "Close AutoCAD" in str(err.value)
    assert not (tmp_path / "plugins" / "HeronAutoCAD.bundle").exists()


def test_install_and_uninstall(built, tmp_path, monkeypatch):
    bundle = build.make_bundle(built, tmp_path / "dist")
    monkeypatch.setattr(install, "autocad_running", lambda: False)
    target = install.install(bundle, tmp_path / "plugins")
    assert (target / "PackageContents.xml").is_file()
    install.uninstall(tmp_path / "plugins")
    assert not target.exists()
