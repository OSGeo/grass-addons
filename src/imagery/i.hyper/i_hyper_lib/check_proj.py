#!/usr/bin/env python3
"""Print CRS/spatial reference information for hyperspectral products (-p flag)."""

from __future__ import annotations

import sys
import importlib.util
import os
import grass.script as gs
from grass.script.utils import get_lib_path


def _load_proj_module(product):
    name = {
        "prisma": "prisma_reader",
        "enmap": "enmap",
        "tanager": "tanager_reader",
        "emit": "emit",
    }.get(product)
    if not name:
        gs.fatal(f"Unsupported product for -p: {product}")

    path = get_lib_path(modname="i_hyper_lib", libname=name)
    if not path:
        gs.fatal(f"Library path for {name} not found.")
    module_file = os.path.join(path, f"{name}.py")
    if not os.path.exists(module_file):
        gs.fatal(f"Module file not found: {module_file}")
    if path not in sys.path:
        sys.path.append(path)
    spec = importlib.util.spec_from_file_location(name, module_file)
    if not spec or not spec.loader:
        gs.fatal(f"Failed to load module spec from {module_file}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


_FUNC_NAMES = {
    "prisma": "get_prisma_proj_info",
    "enmap": "get_enmap_proj_info",
    "tanager": "get_tanager_proj_info",
    "emit": "get_emit_proj_info",
}


def get_proj_info(product, path):
    module = _load_proj_module(product)
    func_name = _FUNC_NAMES.get(product)
    if not func_name or not hasattr(module, func_name):
        gs.fatal(f"Function {func_name} not found in {product} module.")
    return getattr(module, func_name)(path)


def _format_grid(info):
    lines = [f"SRID: {info['srid']}"]
    for key in ("west", "south", "east", "north"):
        val = info.get(key)
        if val is not None:
            lines.append(f"{key}: {val:.6f}")
        else:
            lines.append(f"{key}: not available")
    for key in ("rows", "cols"):
        val = info.get(key)
        if val is not None:
            lines.append(f"{key}: {val}")
    for key in ("ewres", "nsres"):
        val = info.get(key)
        if val is not None:
            lines.append(f"{key}: {val:.6f}")
    lines.append(f"Layout: {info['layout']}")
    return "\n".join(lines)


def _format_swath(info):
    lines = [f"SRID: {info['srid']}"]
    clat = info.get("center_lat")
    clon = info.get("center_lon")
    if clat is not None and clon is not None:
        lines.append(f"Center: {clat:.6f}, {clon:.6f}")
    corners = info.get("corners")
    if corners:
        parts = []
        for key in ("ul", "ur", "ll", "lr"):
            if key in corners:
                parts.append(
                    f"{key.upper()}=({corners[key][0]:.6f}, {corners[key][1]:.6f})"
                )
        if parts:
            lines.append("Corners: " + " ".join(parts))
    for key in ("rows", "cols"):
        val = info.get(key)
        if val is not None:
            lines.append(f"{key}: {val}")
    lines.append(f"Layout: {info['layout']}")
    return "\n".join(lines)


def _format_local(info):
    lines = [f"SRID: {info['srid']}", f"CRS: {info.get('crs', 'XY')}"]
    for key in ("rows", "cols"):
        val = info.get(key)
        if val is not None:
            lines.append(f"{key}: {val}")
    lines.append(f"Layout: {info['layout']}")
    return "\n".join(lines)


_FORMATTERS = {
    "grid": _format_grid,
    "swath": _format_swath,
    "local sensor geometry": _format_local,
}


def format_proj_info(info):
    fmt = _FORMATTERS.get(info.get("layout"))
    if fmt:
        lines = [fmt(info)]
    else:
        lines = ["\n".join(f"{k}: {v}" for k, v in info.items() if v is not None)]

    behavior = info.get("import_behavior")
    if behavior:
        lines.append(f"i.hyper.import behavior: {behavior}")

    requirements = info.get("project_requirements")
    if requirements:
        lines.append(f"Project requirements: {requirements}")

    return "\n".join(lines)


def print_proj_info(product, path):
    info = get_proj_info(product, path)
    gs.message(format_proj_info(info))


def _is_xy_location():
    try:
        proj = gs.parse_command("g.proj", flags="g")
        name = (proj.get("name") or "").strip().lower()
        return name.startswith("xy")
    except Exception:
        return False


def check_import_allowed(product, path):
    """Fatal if product is in local/sensor geometry and GRASS location is not XY."""
    info = get_proj_info(product, path)
    if info.get("layout") != "local sensor geometry":
        return
    if _is_xy_location():
        return
    gs.fatal(
        "This dataset is in local/sensor geometry (CRS: XY), not in a map-projected CRS.\n"
        "Import into the current GRASS location is not supported.\n"
        "Use an XY location for sensor-geometry data, or use a georeferenced product."
    )
