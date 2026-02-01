#!/usr/bin/env python3

############################################################################
#
# MODULE:       r.colors.toqml
# AUTHOR:       Paulo van Breugel
# PURPOSE:      Export GRASS raster colors + category labels to a QGIS .qml
#               raster style (paletted or singlebandpseudocolor)
# COPYRIGHT:    (C) 2026
#               This program is free software under the GNU GPL (>=v2).
#
#############################################################################

# %module
# % description: Exports GRASS raster colors and category labels to a QGIS .qml style file. Optionally exports the raster to GeoTIFF with the same basename.
# % keyword: raster
# % keyword: color table
# % keyword: category
# % keyword: QGIS
# %end

# %option G_OPT_R_MAP
# % key: map
# % description: Input GRASS raster map
# % required: yes
# %end

# %option G_OPT_F_OUTPUT
# % key: output
# % description: Output QGIS .qml style file
# % required: yes
# %end

# %flag
# % key: r
# % label: Export raster as GeoTIFF
# % description: Export the raster to GeoTIFF with the same basename as the QML
# %end

# %flag
# % key: d
# % label: Force discrete/paletted style
# % description: For CELL: force 'Paletted' (unique values) even if no categories exist. For FCELL/DCELL: force 'SinglebandPseudocolor' with DISCRETE interpolation (bins).
# %end

# %flag
# % key: c
# % label: Force continuous/linear style
# % description: Force 'SinglebandPseudocolor' with LINEAR interpolation. If CELL map has categories, they are ignored.
# %end

# %rules
# % exclusive: -d,-c
# %end

import os
import xml.etree.ElementTree as ET
import grass.script as gs


def _rgb_to_hex(rgb_str: str) -> str:
    """Convert 'r:g:b' to '#RRGGBB'."""
    s = (rgb_str or "").strip()
    if s.startswith("#"):
        s = s.upper()
        # Handle #AARRGGBB by dropping alpha
        if len(s) == 9:
            return "#" + s[-6:]
        if len(s) == 7:
            return s
        gs.fatal(f"Unsupported hex color: {rgb_str!r}")

    parts = s.split(":")
    if len(parts) < 3:
        gs.fatal(f"Unsupported color format: {rgb_str!r}")
    try:
        r, g, b = (int(parts[0]), int(parts[1]), int(parts[2]))
    except ValueError:
        gs.fatal(f"Invalid r:g:b color: {rgb_str!r}")
    return "#{:02X}{:02X}{:02X}".format(r, g, b)


def _try_float(x: str):
    """Try converting string to float; return None on failure."""
    try:
        return float(x)
    except Exception:
        return None


def _sort_key_value(v: str):
    """Sort helper: floats numerically, strings lexically."""
    f = _try_float(v)
    return (0, f) if f is not None else (1, v)


def raster_datatype(raster: str) -> str:
    """Get GRASS raster datatype (CELL, FCELL, DCELL)."""
    info = gs.parse_command("r.info", map=raster, flags="g")
    return (info.get("datatype") or "").strip().upper()


def raster_range(raster: str):
    """Get raster min/max from metadata (r.info -r)."""
    txt = gs.read_command("r.info", map=raster, flags="r")
    mn = mx = None
    for line in txt.splitlines():
        line = line.strip()
        if line.startswith("min="):
            mn = float(line.split("=", 1)[1])
        elif line.startswith("max="):
            mx = float(line.split("=", 1)[1])
    if mn is None or mx is None:
        gs.fatal("Could not determine raster range from r.info -r.")
    return mn, mx


def entries_numeric_minmax(entries):
    """Calculate min/max directly from color rule breakpoints."""
    nums = [
        f for e in entries if (f := _try_float(str(e.get("value", "")))) is not None
    ]
    return (min(nums), max(nums)) if len(nums) >= 2 else None


def present_cell_values(raster: str):
    """Get set of CELL values actually present (honors region/mask)."""
    # Used to prevent creating massive palettes for sparse integer maps
    sep = "|"
    try:
        txt = gs.read_command("r.stats", input=raster, flags="n", separator=sep)
    except Exception as e:
        gs.fatal(_("Failed to run r.stats: {}").format(e))
    return {line.split(sep, 1)[0].strip() for line in txt.splitlines() if line.strip()}


def read_category_labels(raster: str):
    """Read category labels for CELL maps."""
    if raster_datatype(raster) != "CELL":
        return {}
    sep_char = "|"
    txt = gs.read_command("r.category", map=raster, separator=sep_char)
    labels = {}
    for line in txt.splitlines():
        if not line.strip() or sep_char not in line:
            continue
        v, lbl = line.split(sep_char, 1)
        if lbl.strip():
            labels[v.strip()] = lbl.strip()
    return labels


def read_color_rules(raster: str):
    """Read and parse r.colors rules into a list of dictionaries."""
    # Prefer hex output from r.colors.out
    try:
        txt = gs.read_command(
            "r.colors.out", map=raster, format="plain", color_format="hex"
        )
    except Exception:
        txt = gs.read_command("r.colors.out", map=raster)

    entries = []
    nv_color = None

    for raw in txt.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        low = line.lower()

        # Handle NoData (nv) and Default
        if low.startswith("nv "):
            parts = line.split()
            if len(parts) >= 2:
                nv_color = _rgb_to_hex(parts[1])
            continue
        if low.startswith("default "):
            continue  # Default usually white, ignored here

        parts = line.split()
        # Case 1: value color
        if len(parts) == 2 and "%" not in parts[0]:
            entries.append({"value": parts[0], "color": _rgb_to_hex(parts[1])})
        # Case 2: val1 val2 col1 col2 (Gradient/Interval)
        elif len(parts) >= 4 and "%" not in parts[0] and "%" not in parts[1]:
            entries.append({"value": parts[0], "color": _rgb_to_hex(parts[2])})
            entries.append({"value": parts[1], "color": _rgb_to_hex(parts[3])})

    # Sort required for QGIS processing
    entries.sort(key=lambda e: _sort_key_value(str(e["value"])))
    return entries, nv_color


def is_ramp_stepped(entries):
    """Returns True if color table consists PURELY of flat bins and vertical jumps."""
    if len(entries) < 2:
        return False
    for i in range(len(entries) - 1):
        e1, e2 = entries[i], entries[i + 1]
        # If values differ (range) but colors also differ, it is a gradient -> Interpolated
        if str(e1["value"]) != str(e2["value"]) and e1["color"] != e2["color"]:
            return False
    return True


def make_discrete_items(entries):
    """Convert GRASS rules to QGIS Discrete items (Upper Bound -> Color)."""
    # For DISCRETE, QGIS uses the color of the upper bound.
    if not entries:
        return []
    discrete = []
    for i in range(len(entries) - 1):
        # Determine breakpoint where color changes
        if entries[i]["color"] != entries[i + 1]["color"]:
            discrete.append(entries[i])
    discrete.append(entries[-1])
    return discrete


def determine_renderer(raster, labels, entries, flags):
    """Determine QGIS renderer type and mode based on flags and data."""
    dtype = raster_datatype(raster)
    has_cats = bool(labels)

    # 1. Flag -c: Force Continuous Linear
    # (g.parser ensures d and c are exclusive)
    if flags["c"]:
        if dtype == "CELL" and has_cats:
            gs.message(
                _(
                    "Warning: Categories found on CELL map. Ignoring them due to '-c' flag."
                )
            )
        return "singlebandpseudocolor", "INTERPOLATED"

    # 2. Flag -d: Force Discrete/Paletted
    if flags["d"]:
        if dtype == "CELL":
            return "paletted", None  # Force unique values
        return "singlebandpseudocolor", "DISCRETE"  # Force bins

    # 3. Default Logic (No flags)
    if dtype == "CELL":
        if has_cats:
            return "paletted", None  # CELL + Cats -> Paletted
        # CELL without cats -> Linear (Continuous)
        return "singlebandpseudocolor", "INTERPOLATED"
    else:
        # FCELL / DCELL
        if has_cats:
            gs.message(
                _(
                    "Warning: Categories found on floating point map. Ignoring for styling."
                )
            )

        # Check if rules are purely stepped (bins) or contain gradients
        if is_ramp_stepped(entries):
            gs.verbose(_("Detected stepped color rules: using DISCRETE mode."))
            return "singlebandpseudocolor", "DISCRETE"

        # Default fallback for FCELL -> Linear
        return "singlebandpseudocolor", "INTERPOLATED"


def build_qml_paletted(entries, labels, allowed_values=None, nodata_color=None):
    """Construct XML for Paletted renderer."""
    qgis = ET.Element(
        "qgis",
        attrib={"version": "3.34.0", "styleCategories": "LayerConfiguration|Symbology"},
    )
    pipe = ET.SubElement(qgis, "pipe")
    renderer = ET.SubElement(
        pipe,
        "rasterrenderer",
        attrib={
            "type": "paletted",
            "band": "1",
            "opacity": "1",
            "alphaBand": "-1",
            "nodataColor": nodata_color or "",
        },
    )
    palette = ET.SubElement(renderer, "colorPalette")

    # Filter entries to those present in raster (if allowed_values provided)
    unique_entries = {
        str(e["value"]): e["color"]
        for e in entries
        if allowed_values is None or str(e["value"]) in allowed_values
    }
    sorted_keys = sorted(unique_entries.keys(), key=_sort_key_value)

    for v in sorted_keys:
        ET.SubElement(
            palette,
            "paletteEntry",
            attrib={
                "value": str(v),
                "color": unique_entries[v],
                "label": labels.get(v, ""),
                "alpha": "255",
            },
        )
    return qgis


def build_qml_singleband(entries, ramp_mode, vmin, vmax, nodata_color=None):
    """Construct XML for SinglebandPseudocolor renderer."""
    qgis = ET.Element(
        "qgis",
        attrib={"version": "3.34.0", "styleCategories": "LayerConfiguration|Symbology"},
    )
    pipe = ET.SubElement(qgis, "pipe")
    renderer = ET.SubElement(
        pipe,
        "rasterrenderer",
        attrib={
            "type": "singlebandpseudocolor",
            "band": "1",
            "opacity": "1",
            "alphaBand": "-1",
            "classificationMin": str(vmin),
            "classificationMax": str(vmax),
            "nodataColor": nodata_color or "",
        },
    )
    ET.SubElement(renderer, "rasterTransparency")
    shader = ET.SubElement(renderer, "rastershader")

    # Setup Shader (DISCRETE or INTERPOLATED)
    crs = ET.SubElement(
        shader,
        "colorrampshader",
        attrib={
            "colorRampType": ramp_mode,
            "classificationMode": "1",
            "clip": "0",
            "minimumValue": str(vmin),
            "maximumValue": str(vmax),
        },
    )

    for e in entries:
        # Add color items. For INTERPOLATED, duplicate values (hard breaks) are allowed/preserved.
        ET.SubElement(
            crs,
            "item",
            attrib={
                "value": str(e["value"]),
                "color": e["color"],
                "label": "",
                "alpha": "255",
            },
        )
    return qgis


def main(options, flags):
    raster, out_qml = options["map"], options["output"]
    labels = read_category_labels(raster)
    entries, nv_color = read_color_rules(raster)

    if not entries:
        gs.fatal(_("No color rules could be read."))

    # Determine Style
    renderer, mode = determine_renderer(raster, labels, entries, flags)

    qml_root = None
    if renderer == "paletted":
        # Check actual values to optimize palette size
        allowed = present_cell_values(raster)
        qml_root = build_qml_paletted(
            entries, labels, allowed_values=allowed, nodata_color=nv_color
        )
    else:
        # Calculate min/max for shader
        mm = entries_numeric_minmax(entries)
        vmin, vmax = mm if mm else raster_range(raster)

        # Optimize entries if Discrete mode is used
        final_entries = make_discrete_items(entries) if mode == "DISCRETE" else entries
        qml_root = build_qml_singleband(
            final_entries, mode, vmin, vmax, nodata_color=nv_color
        )

    # Ensure output dir exists
    if (d := os.path.dirname(os.path.abspath(out_qml))) and not os.path.isdir(d):
        os.makedirs(d, exist_ok=True)

    # Indentation helper for pretty XML
    def indent(e, level=0):
        i = "\n" + level * "  "
        if len(e):
            if not e.text or not e.text.strip():
                e.text = i + "  "
            for child in e:
                indent(child, level + 1)
            if not e.tail or not e.tail.strip():
                e.tail = i
        else:
            if level and (not e.tail or not e.tail.strip()):
                e.tail = i

    indent(qml_root)
    ET.ElementTree(qml_root).write(out_qml, encoding="utf-8", xml_declaration=True)
    gs.message(f"Wrote QML style: {out_qml}")

    # Export GeoTIFF if requested
    if flags["r"]:
        base, _ext = os.path.splitext(out_qml)
        gs.run_command(
            "r.out.gdal",
            input=raster,
            output=f"{base}.tif",
            format="GTiff",
            createopt="COMPRESS=LZW",
            overwrite=True,
        )

    return 0


if __name__ == "__main__":
    import sys

    sys.exit(main(*gs.parser()))
