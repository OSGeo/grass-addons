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
# % description: Default color
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
import xml.etree.ElementTree as ET
import matplotlib as mpl

import grass.script as gs


def _strip_ns(tag: str) -> str:
    return tag.rsplit("}", maxsplit=1)[-1] if "}" in tag else tag


def _hex_to_rgb(color_hex: str):
    """Parse #RRGGBB or #AARRGGBB (alpha ignored) into (r,g,b)."""
    s = (color_hex or "").strip()
    if not s.startswith("#"):
        gs.fatal(
            f"Unsupported color format: {color_hex!r} (expected #RRGGBB or #AARRGGBB)"
        )
    s = s[1:]
    if len(s) == 8:
        s = s[2:]  # drop alpha
    if len(s) != 6 or not re.fullmatch(r"[0-9A-Fa-f]{6}", s):
        gs.fatal(f"Invalid hex color: {color_hex!r}")
    return int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16)


def get_valid_color(color):
    """Return a valid Matplotlib color as an r:g:b string (0–255)

    :param str color: input color (e.g. 'blue', '#ff00ff', '255:0:255')
    :return str: color in 'r:g:b' format
    """
    # Handle r:g:b input
    if isinstance(color, str) and ":" in color:
        parts = color.split(":")
        if len(parts) not in (3, 4):
            gs.fatal(_("{} is not a valid r:g:b color").format(color))
        try:
            r, g, b = (int(x) for x in parts[:3])
        except ValueError:
            gs.fatal(_("{} is not a valid color.").format(color))

        if not all(0 <= v <= 255 for v in (r, g, b)):
            gs.fatal(_("{} values must be between 0 and 255").format(color))

        rgb = (r / 255, g / 255, b / 255)
    else:
        if not mpl.colors.is_color_like(color):
            raise ValueError(f"{color} is not a valid Matplotlib color")

        rgb = mpl.colors.to_rgb(color)

    r, g, b = (round(v * 255) for v in rgb)
    return f"{r}:{g}:{b}"


def separator_to_char(sep: str) -> str:
    """Map GRASS separator keywords to actual characters."""
    mapping = {
        "pipe": "|",
        "comma": ",",
        "space": " ",
        "tab": "\t",
        "newline": "\n",
    }
    if sep in mapping:
        return mapping[sep]
    if len(sep) == 1:
        return sep
    gs.fatal(
        "Invalid separator. Use pipe, comma, space, tab, newline or a single character like ':'"
    )


def clean_label(s: str, sep_char: str) -> str:
    if s is None:
        return ""
    s = s.replace("\r", " ").replace("\n", " ")
    if sep_char in s:
        s = s.replace(sep_char, " ")
    return s


def _try_float(x: str):
    try:
        return float(x)
    except Exception:
        return None


def sort_entries(entries):
    def key(e):
        v = _try_float(e["value"])
        return (0, v) if v is not None else (1, str(e["value"]))

    entries.sort(key=key)
    return entries


def dedup_by_value_keep_last(entries):
    """Return entries with unique 'value', keeping the last occurrence (after sort)."""
    out = []
    last_val = object()
    for e in entries:
        if e["value"] == last_val:
            out[-1] = e
        else:
            out.append(e)
            last_val = e["value"]
    return out


def stepify_breakpoints(entries):
    """
    Create stepped (discrete) rules using ordered breakpoints
    """
    if len(entries) < 2:
        return entries
    stepped = []
    for i in range(len(entries) - 1):
        a = entries[i]
        b = entries[i + 1]
        stepped.append(a)
        # repeat boundary with previous color
        stepped.append(
            {"value": b["value"], "rgb": a["rgb"], "label": a.get("label", "")}
        )
    # include last real breakpoint
    stepped.append(entries[-1])
    return stepped


def make_discrete(entries):
    """Duplicate breakpoints to emulate stepped colors in r.colors rules."""
    if len(entries) < 2:
        return entries
    out = []
    for i, e in enumerate(entries):
        out.append(e)
        if i < len(entries) - 1:
            # duplicate next value with current color
            nxt = entries[i + 1]
            out.append(
                {"value": nxt["value"], "rgb": e["rgb"], "label": e.get("label", "")}
            )
    return out


def parse_qml(qml_path: str):
    """Return (renderer_type, entries, shader_ramp_type)."""
    try:
        tree = ET.parse(qml_path)
        root = tree.getroot()
    except Exception as e:
        gs.fatal(f"Failed to parse QML as XML: {e}")

    rasterrenderer = None
    for el in root.iter():
        if _strip_ns(el.tag) == "rasterrenderer":
            rasterrenderer = el
            break
    if rasterrenderer is None:
        gs.fatal("No <rasterrenderer> element found in QML.")

    rtype = (rasterrenderer.attrib.get("type") or "").strip().lower()
    entries = []
    shader_ramp_type = None

    if rtype == "paletted":
        for el in root.iter():
            if _strip_ns(el.tag) != "paletteEntry":
                continue
            value = el.attrib.get("value")
            color = el.attrib.get("color")
            label = el.attrib.get("label", "")
            if value is None or color is None:
                continue
            try:
                rgb = _hex_to_rgb(color)
            except ValueError as e:
                gs.warning(str(e))
                continue
            entries.append({"value": value, "rgb": rgb, "label": label})

    elif rtype == "singlebandpseudocolor":
        # detect interpolation mode from <colorrampshader colorRampType="...">
        for el in root.iter():
            if _strip_ns(el.tag) == "colorrampshader":
                shader_ramp_type = (
                    el.attrib.get("colorRampType") or ""
                ).strip().upper() or None
                break
        for el in root.iter():
            if _strip_ns(el.tag) != "item":
                continue
            value = el.attrib.get("value")
            color = el.attrib.get("color")
            label = el.attrib.get("label", "")
            if value is None or color is None:
                continue
            try:
                rgb = _hex_to_rgb(color)
            except ValueError as e:
                gs.warning(str(e))
                continue
            entries.append({"value": value, "rgb": rgb, "label": label})

    else:
        gs.fatal(
            f"Unsupported rasterrenderer type={rtype!r}. Supported: paletted, singlebandpseudocolor."
        )

    if not entries:
        gs.fatal(f"No style entries found for renderer type {rtype!r}.")

    entries = sort_entries(entries)
    if rtype == "singlebandpseudocolor":
        # Ensure continuous ramp breakpoints: unique values only
        entries = dedup_by_value_keep_last(entries)

    return rtype, entries, shader_ramp_type


def write_r_colors_rules(entries, path, default_color):
    """Write r.colors rules file (EOF terminates)."""
    with open(path, "w", encoding="utf-8") as f:
        for e in entries:
            r, g, b = e["rgb"]
            f.write(f"{e['value']} {r}:{g}:{b}\n")
        f.write(f"nv {default_color}\n")
        f.write(f"default {default_color}\n")


def write_r_category_rules(entries, path, sep_char):
    with open(path, "w", encoding="utf-8") as f:
        for e in entries:
            lbl = clean_label(e.get("label", ""), sep_char)
            f.write(f"{e['value']}{sep_char}{lbl}\n")


def main(options, flags):
    raster = options["map"]
    qml = options["qml"]
    sep_opt = options["separator"]
    sep_char = separator_to_char(sep_opt)

    default_color_opt = get_valid_color(options["default_color"])
    null_value_opt = (options.get("null_value") or "").strip()

    # Optionally convert specific value(s) to NULL before applying colors/labels
    if null_value_opt:
        gs.run_command("r.null", map=raster, setnull=null_value_opt)
        gs.message(_("The value {} is set to null").format(null_value_opt))

    do_colors = True
    do_labels = True
    if flags["c"] or flags["l"]:
        do_colors = flags["c"]
        do_labels = flags["l"]

    rtype, entries, shader_ramp_type = parse_qml(qml)
    if flags.get("d"):
        if rtype != "singlebandpseudocolor":
            gs.warning("-d flag ignored: renderer is not singlebandpseudocolor")
        else:
            entries = make_discrete(entries)
    gs.verbose(f"Detected QML rasterrenderer type: {rtype}")
    gs.verbose(f"Parsed {len(entries)} style entries")

    color_entries = entries
    if flags["d"] and rtype == "singlebandpseudocolor":
        # Only stepify if QML declares DISCRETE or EXACT interpolation
        if shader_ramp_type in ("DISCRETE", "EXACT"):
            gs.verbose(
                f"QML colorRampType={shader_ramp_type}: writing stepped r.colors rules"
            )
            color_entries = stepify_breakpoints(entries)
        else:
            gs.verbose(
                f"QML colorRampType={shader_ramp_type or 'UNKNOWN'}: keeping continuous ramp"
            )

    if flags["n"]:
        if do_colors:
            gs.message("### r.colors rules ###")
            for e in color_entries:
                r, g, b = e["rgb"]
                sys.stdout.write(f"{e['value']} {r}:{g}:{b}\n")
            sys.stdout.write(f"nv {default_color_opt}\n")
            sys.stdout.write(f"default {default_color_opt}\n\n")
        if do_labels:
            gs.message("### r.category rules ###")
            for e in entries:
                lbl = clean_label(e.get("label", ""), sep_char)
                sys.stdout.write(f"{e['value']}{sep_char}{lbl}\n")
        return 0

    colors_rules = "/home/paulo/Desktop/test.txt"
    cats_rules = gs.tempfile()

    if do_colors:
        write_r_colors_rules(color_entries, colors_rules, default_color_opt)
        gs.run_command("r.colors", map=raster, rules=colors_rules)

    if do_labels:
        write_r_category_rules(entries, cats_rules, sep_char)
        gs.run_command("r.category", map=raster, rules=cats_rules, separator=sep_opt)

    gs.message(f"Applied QML style from {qml} to raster {raster}.")
    return 0


if __name__ == "__main__":
    sys.exit(main(*gs.parser()))
