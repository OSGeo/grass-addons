#!/usr/bin/env python3

##############################################################################
# MODULE:    i.hyper.explore
# AUTHOR(S): Tomaz Zagar <tomaz.zagar@gis.si>
# PURPOSE:   Visualize spectra from hyperspectral 3D raster maps.
# COPYRIGHT: (C) 2025 by Tomaz Zagar and the GRASS Development Team
# SPDX-License-Identifier: GPL-2.0-or-later
##############################################################################

# %module
# % description: Visualize spectra from hyperspectral 3D raster maps.
# % keyword: visualization
# % keyword: hyperspectral
# % keyword: 3D raster
# %end

# %option G_OPT_R3_INPUT
# % key: map
# % description: Input 3D raster map(s) with hyperspectral data (comma-separated)
# % multiple: yes
# % required: yes
# %end

# %option G_OPT_M_COORDS
# % key: coordinates
# % description: Comma separated list of coordinates
# % multiple: yes
# % required: no
# %end

# %option G_OPT_V_INPUT
# % key: points
# % description: Point vector map with query locations
# % required: no
# %end

# %flag
# % key: p
# % description: Print JSON to stdout instead of plotting
# %end

# %option G_OPT_F_OUTPUT
# % key: output
# % required: no
# % label: Output plot file (.png, .pdf, .svg). If not set, opens an interactive window
# %end

# %option
# % key: dpi
# % type: integer
# % label: DPI value for output image (used only with output=)
# % required: no
# % answer: 300
# %end

# %option
# % key: style_scale
# % type: double
# % label: Scale factor for fonts and line widths when exporting (e.g., 1.8)
# % required: no
# % answer: 1.0
# %end

import grass.script as gs
import json
import re


def _band_count(mapname):
    info = gs.parse_command("r3.info", flags="g", map=mapname)
    d = int(info["depths"])
    if d <= 0:
        gs.fatal("Invalid band count (depths) reported by r3.info")
    return d


def _band_wavelengths(mapname, expected):
    """
    Parse wavelengths and FWHM from r3.info description/comments.
    Returns two lists (len == expected):
      - wavelengths[i] -> float or None
      - fwhm[i]        -> float or None
    """
    txt = gs.read_command("r3.info", map=mapname)
    wavelengths = [None] * expected
    fwhm = [None] * expected

    # number pattern handles ints, floats, scientific notation
    num = r"[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?"
    # e.g.: "Band 157: 2369.21 nm, FWHM: 7.47001 nm"
    pat = re.compile(
        rf"Band\s+(\d+)\s*:\s*({num})\s*nm(?:,\s*FWHM:\s*({num})\s*nm)?", re.IGNORECASE
    )

    for line in txt.splitlines():
        line = line.strip()
        if line.startswith("|"):
            line = line.strip("| ").rstrip("| ").strip()
        m = pat.search(line)
        if m:
            idx = int(m.group(1))  # 1-based
            if 1 <= idx <= expected:
                wavelengths[idx - 1] = float(m.group(2))
                if m.group(3) is not None:
                    fwhm[idx - 1] = float(m.group(3))

    return wavelengths, fwhm


def _band_measurement(mapname):
    """
    Return the measurement string (e.g., 'toa_radiance') from r3.info comments.
    If not found, return None.
    """
    txt = gs.read_command("r3.info", map=mapname)
    for raw in txt.splitlines():
        line = raw.strip().strip("| ").rstrip("| ").strip()
        if line.lstrip().lower().startswith("measurement:"):
            val = line.split(":", 1)[1].strip()
            return val if val else None
    return None


def _band_units(mapname):
    """
    Return the 'Measurement Units' string from the r3.info description/comments.
    If not found or 'unitless/none', return None.
    """
    txt = gs.read_command("r3.info", map=mapname)
    for raw in txt.splitlines():
        line = raw.strip().strip("| ").rstrip("| ").strip()
        if line.lstrip().lower().startswith("measurement units:"):
            val = line.split(":", 1)[1].strip()
            if val and val.lower() not in ("unitless", "none", "units", "1"):
                return val
            return None
    return None


def _has_components(mapname):
    """
    Detect whether the 3D raster contains PCA components (affects axis labeling).
    Looks for 'Component N:' lines in r3.info comments.
    Returns the number of components found, or 0 if none.
    """
    txt = gs.read_command("r3.info", map=mapname)
    components_count = 0
    for raw in txt.splitlines():
        line = raw.strip().strip("| ").rstrip("| ").strip()
        if re.search(r"^Component\s+\d+\s*:", line):
            components_count += 1
    return components_count  # Returns the number of components found


def _sample_all_bands_at_point(mapname, e, n, band_count, sep="|", null_marker="*"):
    """
    Calls r3.what once (2D coords) and returns list of band_count values (float or None).
    """
    out = gs.read_command(
        "r3.what",
        input=mapname,
        coordinates=f"{e},{n}",
        separator=sep,
        null_value=null_marker,
        quiet=True,
    )
    line = out.strip().splitlines()
    if not line:
        return [None] * band_count
    cols = line[0].split(sep)
    vals_raw = cols[2:]  # first two values are coordinates
    vals = []
    for v in vals_raw:
        v = v.strip()
        if v == null_marker or v == "":
            vals.append(None)
        else:
            try:
                vals.append(float(v))
            except ValueError:
                vals.append(v)
    if len(vals) < band_count:
        vals += [None] * (band_count - len(vals))
    return vals[:band_count]


def _sample_at_3dpoint(mapname, e, n, z, sep="|", null_marker="*"):
    out = gs.read_command(
        "r3.what",
        input=mapname,
        coordinates_3d=f"{e},{n},{z}",
        separator=sep,
        null_value=null_marker,
        quiet=True,
    )
    return out.strip().split(sep)[-1]


def _plot_results_multi(
    datasets,
    title=None,
    xlabel="Wavelength [nm]",
    ylabel="Value",
    output=None,
    dpi=300,
    style_scale=1.0,
):
    """
    datasets: list of dicts:
      {
        "map": <name>,
        "wavelength_nm": [...],     # may contain None when not available
        "points": [ {"x": E, "y": N, "values": [...]}, ... ],
        "units": <str or None>,     # parsed from metadata
        "components": <int>,        # Number of PCA components present (if any)
        "band_count": <int>,
      }
    Styling:
      - Linestyle varies by MAP
      - Color varies by POINT index (consistent across maps)
    """
    import numpy as np
    import matplotlib as mpl

    if output:
        mpl.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D

    # scale fonts & default line width only when exporting
    if output and style_scale and float(style_scale) != 1.0:
        base_font = plt.rcParams.get("font.size", 10.0)
        base_line = plt.rcParams.get("lines.linewidth", 1.5)
        plt.rcParams.update(
            {
                "font.size": float(base_font) * float(style_scale),
                "lines.linewidth": float(base_line) * float(style_scale),
            }
        )

    linestyles = ["-", "--", "-.", ":", (0, (5, 1)), (0, (3, 1, 1, 1)), (0, (1, 1))]
    fig, ax = plt.subplots()

    # If any dataset indicates components, X label is "Components" and Y label must be plain "Value"
    components_mode = any(ds.get("components", 0) > 0 for ds in datasets)
    if components_mode:
        xlabel = "Components"
        ylabel = "Value"  # <- per requirement: no units if components present
    else:
        # otherwise use wavelength X label and measurement/units logic for Y label
        ds_meas = [ds.get("measurement") for ds in datasets if ds.get("measurement")]
        ds_units = [ds.get("units") for ds in datasets if ds.get("units")]

        common_meas = (
            ds_meas[0] if ds_meas and all(m == ds_meas[0] for m in ds_meas) else None
        )
        common_units = (
            ds_units[0]
            if ds_units and all(u == ds_units[0] for u in ds_units)
            else None
        )

        if common_meas and common_units:
            ylabel = f"{common_meas} [{common_units}]"
        elif common_meas:
            ylabel = common_meas
        elif common_units:
            ylabel = common_units
        else:
            ylabel = "Reflectance"

    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)

    if components_mode:
        ax.xaxis.set_major_locator(mpl.ticker.MaxNLocator(integer=True))

    # How many points total (use max across datasets)
    num_points = max((len(ds["points"]) for ds in datasets), default=0)

    # Colors from current Matplotlib cycle
    prop_cycle = plt.rcParams.get("axes.prop_cycle", None)
    colors = prop_cycle.by_key().get("color", []) if prop_cycle else []
    if not colors:
        colors = ["C0", "C1", "C2", "C3", "C4", "C5", "C6", "C7", "C8", "C9"]

    # Plot: loop by point index to keep color consistent across maps
    for pi in range(num_points):
        color = colors[pi % len(colors)]
        for mi, ds in enumerate(datasets):
            if pi >= len(ds["points"]):
                continue

            # Check if this dataset has components and adjust X (wavelengths or component indices)
            if ds.get("components", 0) > 0:
                # PCA components mode: Use component indices as X axis (just an index)
                wl = np.arange(1, ds["components"] + 1, dtype=float)
                vals = np.asarray(
                    [
                        np.nan if v is None else float(v)
                        for v in ds["points"][pi]["values"]
                    ],
                    dtype=float,
                )
                mask = np.isfinite(vals)
            else:
                # Regular mode: Use wavelengths as X axis
                wl = np.asarray(
                    [np.nan if w is None else float(w) for w in ds["wavelength_nm"]],
                    dtype=float,
                )
                vals = np.asarray(
                    [
                        np.nan if v is None else float(v)
                        for v in ds["points"][pi]["values"]
                    ],
                    dtype=float,
                )
                mask = np.isfinite(wl) & np.isfinite(vals)

            if not np.any(mask):
                continue

            wl = wl[mask]
            vals = vals[mask]

            # Sort by X to avoid wrap-around connection
            order = np.argsort(wl)
            wl = wl[order]
            vals = vals[order]

            ls = linestyles[mi % len(linestyles)]
            lw = 1.6 * (float(style_scale) if (output and style_scale) else 1.0)
            ax.plot(wl, vals, linestyle=ls, linewidth=lw, color=color)

    ax.grid(True, alpha=0.3)

    # Legends: maps (linestyles) and points (colors)
    map_handles = [
        Line2D(
            [0],
            [0],
            linestyle=linestyles[mi % len(linestyles)],
            color="black",
            label=ds["map"],
        )
        for mi, ds in enumerate(datasets)
    ]

    point_handles = []
    first_points = datasets[0]["points"] if datasets and datasets[0]["points"] else []
    for pi in range(num_points):
        label = (
            f"P{pi + 1}"
            if pi >= len(first_points)
            else f"P{pi + 1}: E={first_points[pi]['x']:.3f}, N={first_points[pi]['y']:.3f}"
        )
        point_handles.append(
            Line2D([0], [0], linestyle="-", color=colors[pi % len(colors)], label=label)
        )

    if map_handles:
        legend_maps = ax.legend(
            handles=map_handles,
            title="Map (linestyle)",
            loc="upper left",
            fontsize="small",
            framealpha=0.9,
        )
        ax.add_artist(legend_maps)
    if point_handles:
        ax.legend(
            handles=point_handles,
            title="Point (color)",
            loc="lower right",
            fontsize="small",
            framealpha=0.9,
        )    

    if output:
        fig.savefig(output, bbox_inches="tight", dpi=dpi)
    else:
        plt.show()


def _parse_maps(opt):
    # GRASS may pass list (multiple=yes) or a comma-separated string
    if isinstance(opt, list):
        maps = []
        for m in opt:
            maps.extend([x.strip() for x in str(m).split(",") if x.strip()])
        return maps
    return [x.strip() for x in str(opt).split(",") if x.strip()]


def _parse_coordinates(opt):
    # Accept list or comma-separated string; return flat token list of strings
    if isinstance(opt, list):
        tokens = []
        for part in opt:
            tokens.extend([t for t in str(part).split(",") if t.strip() != ""])
    else:
        tokens = [t for t in str(opt).split(",") if t.strip() != ""]
    if len(tokens) % 2 != 0:
        gs.fatal("Coordinates list must contain an even number of values (E,N pairs)")
    return tokens


def _read_points_from_vector(vmap):
    """
    Returns a list of (E, N) tuples from a point vector map.
    Uses v.out.ascii format=point and takes the first two columns as E,N.
    """
    out = gs.read_command(
        "v.out.ascii",
        input=vmap,
        format="point",
        separator=",",
        quiet=True,
    )
    coords = []
    for line in out.strip().splitlines():
        parts = [p.strip() for p in line.split(",")]
        if len(parts) >= 2:
            try:
                e = float(parts[0])
                n = float(parts[1])
                coords.append((e, n))
            except ValueError:
                pass
    return coords


def main(options, flags):
    maps = _parse_maps(options["map"])

    # Collect query locations from coordinates= and/or points= (vector)
    coords_pairs = []
    if options.get("coordinates"):
        tokens = _parse_coordinates(options["coordinates"])
        for i in range(0, len(tokens), 2):
            try:
                e = float(tokens[i])
                n = float(tokens[i + 1])
            except ValueError:
                gs.fatal(
                    f"Non-numeric coordinate at position {i}: {tokens[i]}, {tokens[i + 1]}"
                )
            coords_pairs.append((e, n))

    if options.get("points"):
        coords_pairs.extend(_read_points_from_vector(options["points"]))

    if not coords_pairs:
        gs.fatal(
            "No query locations provided. Use coordinates= and/or points=<point vector map>."
        )

    gs.use_temp_region()

    datasets = []
    for mapname in maps:
        gs.run_command("g.region", raster_3d=mapname)
        band_count = _band_count(mapname)
        wavelengths, fwhm = _band_wavelengths(mapname, band_count)

        points = []
        for e, n in coords_pairs:
            values = _sample_all_bands_at_point(mapname, e, n, band_count)
            points.append({"x": e, "y": n, "values": values})

        measurement = _band_measurement(mapname)
        units = _band_units(
            mapname
        )  # may be None → assumed reflectance later (if not components)
        has_comp = _has_components(mapname)  # PCA → axis switch

        datasets.append(
            {
                "map": mapname,
                "wavelength_nm": wavelengths,
                "points": points,
                "measurement": measurement,
                "units": units,
                "components": has_comp,
                "band_count": band_count,
            }
        )

    # If -p (print) is given, emit JSON instead of plotting
    if flags.get("p"):
        results = {"maps": [ds["map"] for ds in datasets], "datasets": datasets}
        print(json.dumps(results, ensure_ascii=False))
        return

    # Default behavior: plot
    _plot_results_multi(
        datasets=datasets,
        title="Spectra",
        xlabel="Wavelength [nm]",
        ylabel="Value",
        output=options.get("output"),
        dpi=int(options.get("dpi")),
        style_scale=float(options.get("style_scale") or 1.0),
    )


if __name__ == "__main__":
    options, flags = gs.parser()
    main(options, flags)
