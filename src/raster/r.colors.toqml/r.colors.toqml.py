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

# %option
# % key: discrete
# % type: string
# % options: auto,yes,no
# % answer: auto
# # label: For continuous rasters, write singlebandpseudocolor as discrete (yes) or interpolated (no).
# % description: For continuous rasters, write singlebandpseudocolor as discrete or interpolate. The option auto tries to infer from raster type/labels.
# % required: no
# %end

import os
import re
import xml.etree.ElementTree as ET

import grass.script as gs


def _rgb_to_hex(rgb_str: str) -> str:
    """
    Convert 'r:g:b' to '#RRGGBB'. If already '#RRGGBB' (or '#AARRGGBB'), normalize.
    """
    s = (rgb_str or "").strip()
    if s.startswith("#"):
        s = s.upper()
        if len(s) == 9:  # #AARRGGBB -> drop alpha
            return "#" + s[-6:]
        if len(s) == 7:
            return s
        gs.fatal(f"Unsupported hex color: {rgb_str!r}")

    parts = s.split(":")
    if len(parts) < 3:
        gs.fatal(f"Unsupported color format: {rgb_str!r} (expected r:g:b or #RRGGBB)")
    try:
        r, g, b = (int(parts[0]), int(parts[1]), int(parts[2]))
    except ValueError:
        gs.fatal(f"Invalid r:g:b color: {rgb_str!r}")
    for v in (r, g, b):
        if v < 0 or v > 255:
            gs.fatal(f"Color values must be 0..255: {rgb_str!r}")
    return "#{:02X}{:02X}{:02X}".format(r, g, b)


def _try_float(x: str):
    try:
        return float(x)
    except Exception:
        return None


def _sort_key_value(v: str):
    f = _try_float(v)
    return (0, f) if f is not None else (1, v)


def raster_datatype(raster: str) -> str:
    info = gs.parse_command("r.info", map=raster, flags="g")
    return (info.get("datatype") or "").strip().upper()


def raster_range(raster: str):
    """
    Get raster range (min, max) using r.info -r.
    """
    txt = gs.read_command("r.info", map=raster, flags="r")
    mn = mx = None
    for line in txt.splitlines():
        line = line.strip()
        if line.startswith("min="):
            mn = float(line.split("=", 1)[1])
        elif line.startswith("max="):
            mx = float(line.split("=", 1)[1])
    if mn is None or mx is None:
        gs.fatal("Could not determine raster range (min/max) from r.info -r.")
    return mn, mx


def entries_numeric_minmax(entries):
    """
    Compute numeric min/max from color-rule breakpoints.
    Returns (min, max) or None if not enough numeric values.
    """
    nums = []
    for e in entries:
        f = _try_float(str(e.get("value", "")))
        if f is not None:
            nums.append(f)
    if len(nums) < 2:
        return None
    return min(nums), max(nums)


def present_cell_values(raster: str):
    """
    Return a set of CELL values actually present in the current region/MASK.
    Uses r.stats (honors region + MASK).
    """
    sep = "|"
    try:
        txt = gs.read_command("r.stats", input=raster, flags="n", separator=sep)
    except Exception as e:
        gs.fatal(
            _("Failed to run r.stats to determine present categories: {}").format(e)
        )

    vals = set()
    for raw in txt.splitlines():
        line = raw.strip()
        if not line:
            continue
        first = line.split(sep, 1)[0].strip()
        if first:
            vals.add(first)
    return vals


def read_category_labels(raster: str):
    """
    Read categories via r.category (only meaningful for CELL rasters).
    For floating point rasters, return {} because r.category requires values=.
    """
    if raster_datatype(raster) != "CELL":
        return {}

    sep_char = "|"
    txt = gs.read_command("r.category", map=raster, separator=sep_char)

    labels = {}
    for line in txt.splitlines():
        if not line.strip():
            continue
        if sep_char not in line:
            continue
        v, lbl = line.split(sep_char, 1)
        labels[v.strip()] = (lbl or "").strip()
    return labels


def read_color_rules(raster: str):
    """
    Export GRASS colors via r.colors.out and parse to entries:
      [{"value": str, "color": "#RRGGBB"} ...]

    Always fails fast on percentage-based breakpoints.
    """
    try:
        txt = gs.read_command(
            "r.colors.out", map=raster, format="plain", color_format="hex"
        )
    except Exception:
        txt = gs.read_command("r.colors.out", map=raster)

    # Fail fast on percentage-based breakpoints.
    offenders = []
    for raw in txt.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        low = line.lower()
        if low.startswith("nv ") or low.startswith("default "):
            continue
        parts = line.split()
        if len(parts) == 2:
            if "%" in parts[0]:
                offenders.append(line)
        elif len(parts) >= 4:
            if "%" in parts[0] or "%" in parts[1]:
                offenders.append(line)

    if offenders:
        gs.fatal(
            _(
                "The GRASS color table includes percentage-based color rules."
                "These cannot be faithfully exported to a QGIS QML style"
            )
        )

    entries = []
    for raw in txt.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        low = line.lower()
        if low.startswith("nv ") or low.startswith("default "):
            continue

        parts = line.split()
        if len(parts) < 2:
            continue

        # "value color"
        if len(parts) == 2:
            value, color = parts
            entries.append({"value": value, "color": _rgb_to_hex(color)})
            continue

        # Gradients: expand to two items (breakpoints).
        if len(parts) >= 4:
            v1, v2, c1, c2 = parts[0], parts[1], parts[2], parts[3]
            entries.append({"value": v1, "color": _rgb_to_hex(c1)})
            entries.append({"value": v2, "color": _rgb_to_hex(c2)})

    # Deduplicate by value keeping last, then sort
    dedup = {}
    for e in entries:
        dedup[str(e["value"])] = e["color"]
    out = [{"value": v, "color": c} for v, c in dedup.items()]
    out.sort(key=lambda e: _sort_key_value(str(e["value"])))
    return out


def infer_renderer_type(raster: str, labels: dict):
    """
    Heuristic:
      - If CELL datatype (integer) and labels exist -> paletted.
      - Otherwise -> singlebandpseudocolor.
    """
    if raster_datatype(raster) == "CELL" and bool(labels):
        return "paletted"
    return "singlebandpseudocolor"


def build_qml_paletted(entries, labels: dict, allowed_values=None):
    """
    Build QML for paletted raster.

    If allowed_values is provided (set of strings), only those categories are written
    (categories actually present in current region/MASK).
    """
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
            "nodataColor": "",
        },
    )

    palette = ET.SubElement(renderer, "colorPalette")

    for e in entries:
        v = str(e["value"])
        if allowed_values is not None and v not in allowed_values:
            continue
        lbl = labels.get(v, "")
        ET.SubElement(
            palette,
            "paletteEntry",
            attrib={
                "value": v,
                "color": e["color"],  # #RRGGBB
                "label": lbl,
                "alpha": "255",
            },
        )
    return qgis


def build_qml_singleband(
    entries, labels: dict, color_ramp_type: str, vmin: float, vmax: float
):
    """
    Build minimal QML for singlebandpseudocolor with a color ramp shader.
    Explicitly writes min/max into the QML to avoid QGIS defaulting to 0..0.
    """
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
            "nodataColor": "",
        },
    )

    ET.SubElement(
        renderer, "rasterTransparency"
    )  # matches QGIS files; harmless if empty

    shader = ET.SubElement(renderer, "rastershader")
    crs = ET.SubElement(
        shader,
        "colorrampshader",
        attrib={
            "colorRampType": color_ramp_type,  # INTERPOLATED or DISCRETE
            "classificationMode": "1",
            "clip": "0",
            "minimumValue": str(vmin),
            "maximumValue": str(vmax),
        },
    )

    for e in entries:
        v = str(e["value"])
        lbl = labels.get(v, "")
        ET.SubElement(
            crs,
            "item",
            attrib={
                "value": v,
                "color": e["color"],
                "label": lbl,
                "alpha": "255",
            },
        )

    return qgis


def write_xml(elem: ET.Element, out_path: str):
    # Pretty printing
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

    indent(elem)
    tree = ET.ElementTree(elem)
    tree.write(out_path, encoding="utf-8", xml_declaration=True)


def main(options, flags):
    raster = options["map"]
    out_qml = options["output"]
    do_tif = flags["r"]
    discrete_opt = (options.get("discrete") or "auto").strip().lower()

    labels = read_category_labels(raster)
    entries = read_color_rules(raster)
    if not entries:
        gs.fatal(_("No color rules could be read from the raster"))

    renderer_type = infer_renderer_type(raster, labels)

    # Decide discrete vs interpolated for continuous renderer
    color_ramp_type = "INTERPOLATED"
    if renderer_type == "singlebandpseudocolor":
        if discrete_opt == "yes":
            color_ramp_type = "DISCRETE"
        elif discrete_opt == "no":
            color_ramp_type = "INTERPOLATED"
        else:
            # auto: CELL+labels paletted; continuous interpolated
            color_ramp_type = "INTERPOLATED"

    gs.verbose(f"Renderer: {renderer_type}")
    gs.verbose(f"Entries: {len(entries)}  Labels: {len(labels)}")

    if renderer_type == "paletted":
        # Filter only those categories actually present in the current region/MASK.
        allowed = present_cell_values(raster)
        qml_root = build_qml_paletted(entries, labels, allowed_values=allowed)
    else:
        # Prefer min/max from breakpoints
        mm = entries_numeric_minmax(entries)
        if mm is None:
            vmin, vmax = raster_range(raster)
        else:
            vmin, vmax = mm
        qml_root = build_qml_singleband(entries, labels, color_ramp_type, vmin, vmax)

    # Ensure output directory exists
    out_dir = os.path.dirname(os.path.abspath(out_qml)) or "."
    if out_dir and not os.path.isdir(out_dir):
        os.makedirs(out_dir, exist_ok=True)

    write_xml(qml_root, out_qml)
    gs.message(f"Wrote QML style: {out_qml}")

    if do_tif:
        base, _ext = os.path.splitext(out_qml)
        out_tif = base + ".tif"

        # Export raster to GeoTIFF
        gs.run_command(
            "r.out.gdal",
            input=raster,
            output=out_tif,
            format="GTiff",
            createopt="COMPRESS=LZW",
            overwrite=True,
        )
        gs.message(f"Exported GeoTIFF: {out_tif}")

    return 0


if __name__ == "__main__":
    import sys

    sys.exit(main(*gs.parser()))
