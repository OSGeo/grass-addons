#!/usr/bin/env python3

############################################################################
#
# MODULE:       r.colors.qml
# AUTHOR:       Paulo van Breugel
# PURPOSE:      Apply QGIS QML raster style (paletted or singlebandpseudocolor)
#               to a GRASS raster.
# COPYRIGHT:    (C) 2026
#               This program is free software under the GNU GPL (>=v2).
#
#############################################################################

# %module
# % description: Applies GRASS raster colors and category labels from a QGIS .qml style file. Supports paletted and singleband pseudocolor renderers.
# % keyword: raster
# % keyword: color table
# % keyword: category
# % keyword: QGIS
# %end

# %option G_OPT_R_MAP
# % key: map
# % description: Raster map to style
# % required: yes
# %end

# %option G_OPT_F_BIN_INPUT
# % key: qml
# % description: Input QGIS .qml style file
# % required: yes
# %end

# %option G_OPT_F_SEP
# % key: separator
# % description: Field separator for category rules
# % answer: tab
# %end

# %option G_OPT_C
# % key: default_color
# % type: string
# % description: Default color (used for out-of-range values when clip is enabled)
# % answer: 255:255:255
# % required: no
# %end

# %option
# % key: null_value
# % type: double
# % description: Value(s) to set to NULL
# % required: no
# %end

# %flag
# % key: c
# % description: Apply colors only
# %end

# %flag
# % key: l
# % description: Apply labels only
# %end

# %flag
# % key: n
# % description: Only print color and category rules to stdout
# %end

# %flag
# % key: d
# % description: For singlebandpseudocolor, force discrete (stepped) color rules
# %end

import sys
import re
import math
import xml.etree.ElementTree as ET
import grass.script as gs


def _strip_ns(tag: str) -> str:
    """Remove XML namespace."""
    return tag.rsplit("}", maxsplit=1)[-1] if "}" in tag else tag


def _try_float(val):
    """Safely convert to float or return None."""
    try:
        return float(val)
    except (ValueError, TypeError):
        return None


def _hex_to_rgb(color_hex: str):
    """Parse #RRGGBB or #AARRGGBB into (r, g, b)."""
    s = (color_hex or "").strip()
    if not s.startswith("#"):
        return (255, 255, 255)
    s = s.lstrip("#")
    if len(s) == 8:  # AARRGGBB
        s = s[2:]
    if len(s) == 6:
        return tuple(int(s[i : i + 2], 16) for i in (0, 2, 4))
    return (255, 255, 255)


def parse_color_string(color_str):
    """Parse 'r:g:b' string to tuple (r, g, b)."""
    try:
        parts = color_str.split(":")
        if len(parts) == 3:
            return tuple(map(int, parts))
    except ValueError:
        pass
    return (255, 255, 255)  # Default fallback


def get_separator_char(sep_str):
    """Convert GRASS separator name to actual character."""
    separators = {
        "pipe": "|",
        "comma": ",",
        "space": " ",
        "tab": "\t",
        "newline": "\n",
        "colon": ":",
    }
    return separators.get(sep_str, sep_str)


def clean_label(label, sep_char):
    """Remove separator character from label to prevent parsing errors."""
    if not label:
        return ""
    # Replace the separator with a space if found in the label
    return label.replace(sep_char, " ")


def interpolate_rgb(val, entries):
    """
    Linearly interpolate RGB for a value 'val' based on sorted entries.
    entries: list of dict {'value': float, 'rgb': (r,g,b)}
    """
    if not entries:
        return (255, 255, 255)

    # Check boundaries
    if val <= entries[0]["value"]:
        return entries[0]["rgb"]
    if val >= entries[-1]["value"]:
        return entries[-1]["rgb"]

    # Find bracketing entries
    for i in range(len(entries) - 1):
        e1 = entries[i]
        e2 = entries[i + 1]
        v1, v2 = e1["value"], e2["value"]

        if v1 <= val <= v2:
            if v2 == v1:
                return e1["rgb"]

            frac = (val - v1) / (v2 - v1)
            c1 = e1["rgb"]
            c2 = e2["rgb"]

            r = c1[0] + (c2[0] - c1[0]) * frac
            g = c1[1] + (c2[1] - c1[1]) * frac
            b = c1[2] + (c2[2] - c1[2]) * frac
            return (int(round(r)), int(round(g)), int(round(b)))

    return entries[-1]["rgb"]


def get_discrete_color_for_val(val, entries):
    """
    For discrete, usually QGIS defines bins: value <= entry['value'].
    We find the first entry where val <= entry['value'].
    """
    if not entries:
        return (255, 255, 255)
    for e in entries:
        if val <= e["value"]:
            return e["rgb"]
    return entries[-1]["rgb"]


def parse_qml(qml_file):
    """Parse QGIS QML file."""
    try:
        tree = ET.parse(qml_file)
    except ET.ParseError as e:
        gs.fatal(f"Failed to parse QML: {e}")

    root = tree.getroot()

    # Locate rasterrenderer
    rr = None
    for el in root.iter():
        if _strip_ns(el.tag) == "rasterrenderer":
            rr = el
            break

    if rr is None:
        gs.fatal("No <rasterrenderer> found in QML.")

    q_meta = {
        "type": rr.attrib.get("type", "unknown"),
        "opacity": rr.attrib.get("opacity", "1"),
    }

    entries = []

    # Handle SingleBandPseudoColor
    crs = None
    for el in rr:
        if _strip_ns(el.tag) == "rastershader":
            for sub in el:
                if _strip_ns(sub.tag) == "colorrampshader":
                    crs = sub
                    break

    # Seems some versions put colorrampshader directly under rasterrenderer
    if crs is None:
        for el in rr.iter():
            if _strip_ns(el.tag) == "colorrampshader":
                crs = el
                break

    if crs is not None:
        q_meta["clip"] = crs.attrib.get("clip") == "1"
        q_meta["shader_type"] = crs.attrib.get("colorRampType", "INTERPOLATED")
        q_meta["shader_min"] = crs.attrib.get("minimumValue")
        q_meta["shader_max"] = crs.attrib.get("maximumValue")
        q_meta["class_min"] = crs.attrib.get("classificationMode")

        # Parse items
        for item in crs.iter():
            if _strip_ns(item.tag) == "item":
                val = _try_float(item.attrib.get("value"))
                color = item.attrib.get("color", "#000000")
                lbl = item.attrib.get("label", "")

                if val is not None:
                    entries.append(
                        {"value": val, "rgb": _hex_to_rgb(color), "label": lbl}
                    )

    # Handle Paletted
    elif q_meta["type"] == "paletted":
        q_meta["shader_type"] = "EXACT"
        # Search for palette entries
        for pal in rr.iter():
            if _strip_ns(pal.tag) == "paletteEntry":
                val = _try_float(pal.attrib.get("value"))
                color = pal.attrib.get("color", "#000000")
                lbl = pal.attrib.get("label", "")
                if val is not None:
                    entries.append(
                        {"value": val, "rgb": _hex_to_rgb(color), "label": lbl}
                    )

    # Sort entries by value
    entries.sort(key=lambda x: x["value"])

    return q_meta, entries


def generate_rules(entries, q_meta, flags, default_rgb):
    """
    Generate final r.colors rules based on renderer type, clip settings,
    and interpolation mode.
    """
    if not entries:
        return []

    # Determine Interpolation Mode
    shader_type = q_meta.get("shader_type", "INTERPOLATED")
    is_discrete = False

    if shader_type == "DISCRETE":
        is_discrete = True
    elif shader_type == "INTERPOLATED" and flags.get("d"):
        # Force discrete if user requested -d on continuous
        is_discrete = True
    elif shader_type == "EXACT":
        is_discrete = False

    clip_enabled = q_meta.get("clip", False)

    # Determine Effective Range (Min/Max)
    s_min = _try_float(q_meta.get("shader_min"))
    s_max = _try_float(q_meta.get("shader_max"))

    if s_min is None or not math.isfinite(s_min):
        s_min = entries[0]["value"]
    if s_max is None or not math.isfinite(s_max):
        s_max = entries[-1]["value"]

    if s_min > s_max:
        s_min, s_max = s_max, s_min

    # Generate "Core" Rules within [s_min, s_max]
    core_rules = []

    valid_items = [e for e in entries if s_min < e["value"] < s_max]

    if is_discrete:
        c_min = get_discrete_color_for_val(s_min, entries)
        c_max = get_discrete_color_for_val(s_max, entries)
    else:
        c_min = interpolate_rgb(s_min, entries)
        c_max = interpolate_rgb(s_max, entries)

    points = []
    points.append({"value": s_min, "rgb": c_min})
    for item in valid_items:
        points.append({"value": item["value"], "rgb": item["rgb"]})
    points.append({"value": s_max, "rgb": c_max})

    # Convert Points to Rules based on Mode
    final_rule_lines = []

    if is_discrete:
        for i in range(len(points) - 1):
            p_start = points[i]
            p_end = points[i + 1]
            seg_color = p_end["rgb"]

            # Add rule
            final_rule_lines.append({"value": p_start["value"], "rgb": seg_color})
            final_rule_lines.append({"value": p_end["value"], "rgb": seg_color})

    else:
        for p in points:
            final_rule_lines.append(p)

    # Apply Clipping / Extension (Padding)
    padded_rules = []

    if clip_enabled:
        padded_rules.append({"value": "-inf", "rgb": default_rgb})
        padded_rules.append({"value": s_min, "rgb": default_rgb})
        padded_rules.extend(final_rule_lines)
        padded_rules.append({"value": s_max, "rgb": default_rgb})
        padded_rules.append({"value": "inf", "rgb": default_rgb})

    else:
        start_color = final_rule_lines[0]["rgb"]
        padded_rules.append({"value": "-inf", "rgb": start_color})
        padded_rules.extend(final_rule_lines)
        end_color = final_rule_lines[-1]["rgb"]
        padded_rules.append({"value": "inf", "rgb": end_color})

    return padded_rules


def main():
    options, flags = gs.parser()

    map_name = options["map"]
    qml_file = options["qml"]
    sep_option = options["separator"]
    default_color_str = options["default_color"]
    null_val = options.get("null_value")

    do_colors = True
    do_labels = True
    if flags["c"]:
        do_labels = False
    if flags["l"]:
        do_colors = False

    default_rgb = parse_color_string(default_color_str)

    # Resolve separator
    sep_char = get_separator_char(sep_option)

    # Parse QML
    q_meta, entries = parse_qml(qml_file)

    if not entries:
        gs.fatal("No color entries found in QML file.")

    # Generate Rules
    color_rules = generate_rules(entries, q_meta, flags, default_rgb)

    # Output Logic
    if flags["n"]:
        # Print to stdout
        if do_colors:
            gs.message("### r.colors rules ###")
            for r in color_rules:
                val = r["value"]
                rgb = r["rgb"]
                print(f"{val} {rgb[0]}:{rgb[1]}:{rgb[2]}")

            print(f"nv {default_color_str}")
            print(f"default {default_color_str}")
            print("")

        if do_labels:
            gs.message("### r.category rules ###")
            for e in entries:
                raw_lbl = e.get("label", "")
                clean_lbl = clean_label(raw_lbl, sep_char)
                print(f"{e['value']}{sep_char}{clean_lbl}")
        return 0

    # Apply to map
    if do_colors:
        cr_file = gs.tempfile()
        with open(cr_file, "w") as f:
            for r in color_rules:
                val = r["value"]
                rgb = r["rgb"]
                f.write(f"{val} {rgb[0]}:{rgb[1]}:{rgb[2]}\n")

            f.write(f"nv {default_color_str}\n")
            f.write(f"default {default_color_str}\n")

        gs.run_command("r.colors", map=map_name, rules=cr_file)

    if do_labels:
        cat_file = gs.tempfile()
        with open(cat_file, "w") as f:
            for e in entries:
                raw_lbl = e.get("label", "")
                if raw_lbl:
                    clean_lbl = clean_label(raw_lbl, sep_char)
                    f.write(f"{e['value']}{sep_char}{clean_lbl}\n")

        # Pass the original option string 'sep_option' (e.g. "tab") to r.category
        # because r.category handles the mapping of "tab" -> \t internally when reading the file.
        gs.run_command("r.category", map=map_name, rules=cat_file, separator=sep_option)

    if null_val:
        gs.run_command("r.null", map=map_name, setnull=null_val)

    return 0


if __name__ == "__main__":
    sys.exit(main())
