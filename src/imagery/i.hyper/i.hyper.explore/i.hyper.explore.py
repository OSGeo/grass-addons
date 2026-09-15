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

# %option G_OPT_R3_INPUT
# % key: uncertainty
# % description: Optional standard uncertainty 3D raster map for a single input map
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
import os
import shlex
import sys
import importlib.util
from grass.script.utils import get_lib_path

_HYPER_META_CLASS = None


def _get_hyper_meta_class():
    global _HYPER_META_CLASS
    if _HYPER_META_CLASS is not None:
        return _HYPER_META_CLASS

    path = get_lib_path(modname="i_hyper_lib", libname="hyper_meta")
    if not path:
        return None

    if path not in sys.path:
        sys.path.append(path)

    spec = importlib.util.find_spec("hyper_meta")
    if not spec or not spec.loader:
        return None

    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    try:
        spec.loader.exec_module(module)
    except Exception:
        sys.modules.pop(spec.name, None)
        return None
    _HYPER_META_CLASS = module.HyperMetadata
    return _HYPER_META_CLASS


def _pad_or_trim(values, expected):
    values = list(values or [])
    if len(values) >= expected:
        return values[:expected]
    return values + [None] * (expected - len(values))


def _band_count(mapname):
    info = gs.parse_command("r3.info", flags="g", map=mapname)
    d = int(info["depths"])
    if d <= 0:
        gs.fatal("Invalid band count (depths) reported by r3.info")
    return d


def _dataset_metadata(mapname, band_count, hyper_meta_class):
    """Return wavelengths, validity, measurement, units and component count."""
    if hyper_meta_class is None:
        gs.fatal(
            "Failed to load hyper_meta library. JSON metadata support is required."
        )

    try:
        meta = hyper_meta_class.load(mapname)
    except Exception as error:
        gs.fatal(f"Failed to read JSON metadata for {mapname}: {error}")

    measurement = meta.radiometric_quantity
    units = meta.radiometric_units
    has_components = int(
        meta.n_components
        or (len(meta.explained_variance_ratio) if meta.explained_variance_ratio else 0)
        or (len(meta.component_labels) if meta.component_labels else 0)
    )

    if has_components > 0:
        wavelengths = [None] * band_count
        validity = None
    else:
        if meta.wavelengths is None:
            gs.fatal(f"Missing 'bands.wavelength' in JSON metadata for {mapname}.")
        wavelengths_raw = list(meta.wavelengths or [])
        validity_raw = list(getattr(meta, "validity", []) or [])
        has_full_validity = len(validity_raw) == len(wavelengths_raw) and any(
            not bool(v) for v in validity_raw
        )

        if has_full_validity:
            # Keep full source axis to allow visual gaps at invalid bands.
            wavelengths = wavelengths_raw
            validity = [bool(v) for v in validity_raw]
        else:
            # Backward-compatible behavior for old metadata.
            wavelengths = _pad_or_trim(wavelengths_raw, band_count)
            validity = None

    return wavelengths, validity, measurement, units, has_components


def _full_map_name(mapname):
    if "@" in mapname:
        return mapname
    mapset = gs.gisenv().get("MAPSET", "")
    return f"{mapname}@{mapset}" if mapset else mapname


def _command_options(command):
    """Return command options from a stored GRASS command line."""
    try:
        tokens = shlex.split(command)
    except ValueError:
        return {}
    if not tokens or os.path.basename(tokens[0]) != "i.hyper.atcorr":
        return {}
    return {
        key: value
        for token in tokens[1:]
        if "=" in token
        for key, value in [token.split("=", 1)]
    }


def _candidate_uncertainty_maps(mapname, hyper_meta_class):
    """Return likely uncertainty maps, preferring the recorded atcorr output."""
    candidates = []
    try:
        metadata = hyper_meta_class.load(mapname)
    except Exception:
        metadata = None

    if metadata is not None:
        for step in reversed(metadata.processing_history or []):
            options = _command_options(step.get("command", ""))
            if not options:
                continue
            output = options.get("output")
            if output and _full_map_name(output) != _full_map_name(mapname):
                continue
            uncertainty = options.get("uncertainty")
            if uncertainty:
                candidates.append(uncertainty)
                break

    base = mapname.split("@", 1)[0]
    candidates.extend(
        [f"{base}_uncertainty", f"{base}_unc", base.replace("_l2a", "_uncertainty")]
    )
    return list(dict.fromkeys(candidates))


def _is_compatible_uncertainty(mapname, uncertainty, hyper_meta_class):
    """Check that an uncertainty 3D raster map matches mapname and type."""
    found = gs.find_file(uncertainty, element="grid3")
    if not found.get("fullname"):
        return None
    uncertainty = found["fullname"]
    try:
        metadata = hyper_meta_class.load(uncertainty)
    except Exception:
        return None
    if metadata.radiometric_quantity != "reflectance_uncertainty":
        return None

    try:
        source_info = gs.parse_command("r3.info", map=mapname, flags="g")
        uncertainty_info = gs.parse_command("r3.info", map=uncertainty, flags="g")
    except Exception:
        return None
    for key in ("rows", "cols", "depths", "north", "south", "east", "west"):
        if source_info.get(key) != uncertainty_info.get(key):
            return None
    return uncertainty


def _find_uncertainty_map(mapname, hyper_meta_class, explicit=None):
    """Return a compatible uncertainty 3D raster map, or None if none matches."""
    candidates = (
        [explicit]
        if explicit
        else _candidate_uncertainty_maps(mapname, hyper_meta_class)
    )
    for candidate in candidates:
        uncertainty = _is_compatible_uncertainty(mapname, candidate, hyper_meta_class)
        if uncertainty:
            return uncertainty
    if explicit:
        gs.fatal(
            f"Uncertainty 3D raster map '{explicit}' is missing, incompatible, or is not a reflectance uncertainty 3D raster map"
        )
    return None


def _expand_values_with_validity(values, validity):
    """Expand sampled valid-band values to full source-band length using validity flags."""
    if not validity:
        return None
    n_valid = sum(1 for v in validity if bool(v))
    if n_valid != len(values):
        return None
    out = []
    it = iter(values)
    for v in validity:
        out.append(next(it) if bool(v) else None)
    return out


def _align_values_to_source_axis(values, validity):
    """Return values aligned to the metadata source axis."""
    if not validity:
        return list(values)
    validity = [bool(v) for v in validity]
    values = list(values)
    if len(values) == len(validity):
        return [v if validity[i] else None for i, v in enumerate(values)]
    expanded = _expand_values_with_validity(values, validity)
    return expanded if expanded is not None else values


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
    from matplotlib.patches import Patch

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

    def plot_uncertainty(wavelengths, values, uncertainty, color):
        if uncertainty is None:
            return False
        sigma = np.asarray(
            [np.nan if value is None else float(value) for value in uncertainty],
            dtype=float,
        )
        if len(sigma) != len(wavelengths) or len(values) != len(wavelengths):
            return False
        valid = np.isfinite(wavelengths) & np.isfinite(values) & np.isfinite(sigma)
        if not np.any(valid):
            return False
        lower = values - sigma
        upper = values + sigma
        ax.fill_between(
            wavelengths,
            lower,
            upper,
            where=valid,
            color=color,
            alpha=0.22,
            linewidth=0,
        )
        # Thin boundaries keep small intervals visible without hiding the spectrum.
        ax.plot(
            wavelengths, lower, color=color, alpha=0.8, linewidth=0.8, linestyle=":"
        )
        ax.plot(
            wavelengths, upper, color=color, alpha=0.8, linewidth=0.8, linestyle=":"
        )
        return True

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
    has_uncertainty_buffer = False
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
                vals_src = _align_values_to_source_axis(
                    ds["points"][pi]["values"], ds.get("validity")
                )
                vals = np.asarray(
                    [np.nan if v is None else float(v) for v in vals_src], dtype=float
                )
                has_uncertainty_buffer = (
                    plot_uncertainty(
                        wl,
                        vals,
                        _align_values_to_source_axis(
                            ds["points"][pi].get("uncertainty_values", []),
                            ds.get("validity"),
                        )
                        if "uncertainty_values" in ds["points"][pi]
                        else None,
                        color,
                    )
                    or has_uncertainty_buffer
                )

                if len(vals) == len(wl):
                    # Keep NaNs from invalid bands to force visible line breaks.
                    if np.any(np.isfinite(vals)):
                        ls = linestyles[mi % len(linestyles)]
                        lw = 1.6 * (
                            float(style_scale) if (output and style_scale) else 1.0
                        )
                        ax.plot(wl, vals, linestyle=ls, linewidth=lw, color=color)
                    continue

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
    if has_uncertainty_buffer:
        map_handles.append(
            Patch(
                facecolor="gray",
                edgecolor="gray",
                alpha=0.22,
                label="Reflectance +/- 1 sigma uncertainty",
            )
        )

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
            title="Map (linestyle) and uncertainty",
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
    explicit_uncertainty = options.get("uncertainty")
    if explicit_uncertainty and len(maps) != 1:
        gs.fatal("uncertainty= can be used only with a single map=")

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
    HyperMetadata = _get_hyper_meta_class()
    if HyperMetadata is None:
        gs.fatal(
            "Failed to load hyper_meta library. JSON metadata support is required."
        )
    for mapname in maps:
        gs.run_command("g.region", raster_3d=mapname)
        band_count = _band_count(mapname)
        wavelengths, validity, measurement, units, has_comp = _dataset_metadata(
            mapname, band_count, HyperMetadata
        )
        uncertainty_map = None
        if has_comp and explicit_uncertainty:
            gs.fatal("uncertainty= is not supported for component datasets")
        if not has_comp:
            uncertainty_map = _find_uncertainty_map(
                mapname, HyperMetadata, explicit=explicit_uncertainty
            )

        points = []
        for e, n in coords_pairs:
            values = _align_values_to_source_axis(
                _sample_all_bands_at_point(mapname, e, n, band_count),
                validity,
            )
            point = {"x": e, "y": n, "values": values}
            if uncertainty_map:
                point["uncertainty_values"] = _align_values_to_source_axis(
                    _sample_all_bands_at_point(uncertainty_map, e, n, band_count),
                    validity,
                )
            points.append(point)

        datasets.append(
            {
                "map": mapname,
                "wavelength_nm": wavelengths,
                "validity": validity,
                "points": points,
                "measurement": measurement,
                "units": units,
                "components": has_comp,
                "band_count": band_count,
                "uncertainty_map": uncertainty_map,
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
