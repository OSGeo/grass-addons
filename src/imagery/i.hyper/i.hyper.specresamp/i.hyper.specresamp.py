#!/usr/bin/env python3
##############################################################################
# MODULE:    i.hyper.specresamp
# AUTHOR(S): Alen Mangafic, Geodetic Institute of Slovenia
# PURPOSE:   Spectral resampling of hyperspectral imagery.
# COPYRIGHT: (C) 2026 by Alen Mangafic and the GRASS Development Team
# SPDX-License-Identifier: GPL-2.0-or-later
##############################################################################

# %module
# % description: Spectral resampling of hyperspectral imagery.
# % keyword: imagery
# % keyword: hyperspectral
# % keyword: resampling
# %end

# %option G_OPT_R3_INPUT
# % key: input
# % description: Input hyperspectral 3D raster map
# % required: yes
# % guisection: Main
# %end

# %option G_OPT_R3_INPUT
# % key: reference
# % description: Reference 3D raster map (reads target wavelengths from its metadata)
# % required: no
# % guisection: Main
# %end

# %option G_OPT_R3_OUTPUT
# % key: output
# % description: Output resampled 3D raster map
# % required: yes
# % guisection: Main
# %end

# %option
# % key: method
# % type: string
# % options: gaussian,linear,nearest
# % answer: gaussian
# % description: Resampling method
# % required: no
# % guisection: Main
# %end

# %option
# % key: wavelengths
# % type: string
# % description: Output wavelength ranges (e.g. 400-700,700-2500) or explicit comma-separated values
# % required: no
# % guisection: Custom
# %end

# %option
# % key: fwhm
# % type: string
# % description: FWHM (nm) per range for Gaussian (e.g. 8.3,11.5). Also sets band spacing within range.
# % required: no
# % guisection: Custom
# %end

# %flag
# % key: i
# % description: Print resampling plan and exit (info mode)
# %end

# %flag
# % key: v
# % description: Use only valid bands from input metadata
# %end

import sys
import numpy as np

import grass.script as gs
import grass.script.array as garray
from grass.script.utils import get_lib_path
import importlib.util


def _import_from_i_hyper_lib(module_name):
    path = get_lib_path(modname="i_hyper_lib", libname=module_name)
    if not path:
        gs.fatal(f"Library path for {module_name} not found.")
    if path not in sys.path:
        sys.path.append(path)
    spec = importlib.util.find_spec(module_name)
    if not spec or not spec.loader:
        gs.fatal(f"Module {module_name} not found at {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    try:
        spec.loader.exec_module(module)
    except Exception:
        sys.modules.pop(spec.name, None)
        raise
    return module


def _load_hyper_meta_class():
    path = get_lib_path(modname="i_hyper_lib", libname="hyper_meta")
    if not path:
        gs.fatal("Library path for hyper_meta not found.")
    if path not in sys.path:
        sys.path.append(path)
    spec = importlib.util.find_spec("hyper_meta")
    if not spec or not spec.loader:
        gs.fatal(f"Module hyper_meta not found at {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    try:
        spec.loader.exec_module(module)
    except Exception:
        sys.modules.pop(spec.name, None)
        raise
    return module.HyperMetadata


def _to_full_map_name(mapname):
    if "@" in mapname:
        return mapname
    mapset = gs.gisenv().get("MAPSET", "")
    return f"{mapname}@{mapset}" if mapset else mapname


def _get_raster_depth(mapname):
    try:
        info = gs.parse_command("r3.info", map=mapname, flags="g")
        return int(float(info["depths"]))
    except Exception as error:
        gs.fatal(f"Failed to read 3D raster depth for '{mapname}': {error}")


def _load_input_meta(mapname, hyper_meta_class, depth, valid_only):
    """Load input metadata, return (meta, wl, fwhm, band_indices).

    *wl* and *fwhm* correspond to the raster depth axis after optional validity filtering.
    *band_indices* are the depth indices into the 3D raster (0-based).
    """
    try:
        meta = hyper_meta_class.load(mapname)
    except Exception as error:
        gs.fatal(f"Failed to read metadata for '{mapname}': {error}")

    axis = meta.resolve_band_axis(depth)
    source_wl = axis["wavelengths"]
    source_fwhm = axis["fwhm"]
    depth_to_source = axis["depth_to_source"]
    depth_validity = np.asarray(axis["validity"], dtype=bool)[depth_to_source]

    raw_wl = source_wl[depth_to_source] if source_wl is not None else None
    raw_fwhm = source_fwhm[depth_to_source] if source_fwhm is not None else None

    if raw_wl is None:
        gs.fatal(f"No wavelength metadata found for '{mapname}'.")

    if valid_only:
        idx = np.flatnonzero(depth_validity)
        wl = raw_wl[idx]
        fwhm = raw_fwhm[idx] if raw_fwhm is not None else None
    else:
        idx = np.arange(depth)
        wl = raw_wl
        fwhm = raw_fwhm

    if len(wl) == 0:
        gs.fatal(f"No valid bands found in metadata for '{mapname}'.")

    return meta, wl, fwhm, idx


def _resolve_target_wavelengths(options, hyper_meta_class, specresamp):
    """Determine output wavelengths and FWHM.

    Priority:
      1. ``reference`` raster → read from its metadata.
      2. ``wavelengths`` option → parse via *specresamp.parse_wavelength_ranges*.

    Returns (out_wl, out_fwhm).
    """
    ref = options.get("reference") or ""
    wl_str = options.get("wavelengths") or ""

    if ref and wl_str:
        gs.fatal("Both 'reference' and 'wavelengths' provided. Use only one.")
    if not ref and not wl_str:
        gs.fatal("Either 'reference' or 'wavelengths' is required.")

    if ref:
        try:
            meta = hyper_meta_class.load(ref)
        except Exception as error:
            gs.fatal(f"Failed to read reference metadata: {error}")
        if meta.wavelengths is None:
            gs.fatal("Reference raster has no wavelength metadata.")
        out_wl = np.array(meta.wavelengths, dtype=np.float64)
        out_fwhm = None
        if meta.fwhm is not None:
            out_fwhm = np.array(meta.fwhm, dtype=np.float64)
        return out_wl, out_fwhm

    fwhm_str = options.get("fwhm") or None
    try:
        out_wl, out_fwhm = specresamp.parse_wavelength_ranges(wl_str, fwhm_str)
    except ValueError as error:
        gs.fatal(str(error))
    if len(out_wl) == 0:
        gs.fatal("No output wavelengths generated.")
    return out_wl, out_fwhm


def _clip_to_input_range(out_wl, out_fwhm, in_min, in_max):
    """Remove output wavelengths outside input range (no extrapolation).

    Returns (clipped_wl, clipped_fwhm, n_clipped).
    """
    keep = (out_wl >= in_min) & (out_wl <= in_max)
    n_clipped = int((~keep).sum())
    out_wl_out = out_wl[keep]
    if out_fwhm is not None and len(out_fwhm) == len(out_wl):
        out_fwhm_out = out_fwhm[keep]
    else:
        out_fwhm_out = out_fwhm
    return out_wl_out, out_fwhm_out, n_clipped


def _write_resampled_metadata(
    inmap,
    outmap,
    out_wl,
    out_fwhm,
    out_validity,
    cmd_params,
    hyper_meta_class,
):
    """Write hyperspectral metadata for the resampled output."""
    try:
        src_meta = hyper_meta_class.load(inmap)
        src_dataset_id = src_meta.dataset_id
    except Exception as error:
        gs.warning(f"Failed to read source metadata: {error}")
        return

    meta = hyper_meta_class.for_spectral_data(
        wavelengths=out_wl,
        fwhm=out_fwhm,
        sensor=src_meta.sensor,
        radiometric_quantity=src_meta.radiometric_quantity,
        radiometric_units=src_meta.radiometric_units,
        acquisition_datetime=src_meta.acquisition_datetime,
    )
    meta.dataset_id = hyper_meta_class.new_dataset_id()
    meta.derived = True
    meta.set_validity(out_validity)

    command = meta._command_from_module_params("i.hyper.specresamp", cmd_params)
    meta.add_history_entry(
        command=command,
        inputs=[{"id": src_dataset_id, "map_name": _to_full_map_name(inmap)}],
        outputs=[{"id": meta.dataset_id, "map_name": _to_full_map_name(outmap)}],
    )
    meta.save(outmap)


def main():
    options, flags = gs.parser()

    specresamp = _import_from_i_hyper_lib("specresamp")
    hyper_meta_class = _load_hyper_meta_class()

    inmap = options["input"]
    outmap = options["output"]
    method = (options.get("method") or "gaussian").lower()
    valid_only = bool(flags.get("v"))
    info_only = bool(flags.get("i"))

    # ── resolve target wavelengths ─────────────────────────────────
    out_wl, out_fwhm_from_target = _resolve_target_wavelengths(
        options, hyper_meta_class, specresamp
    )

    # ── read input metadata ────────────────────────────────────────
    depth = _get_raster_depth(inmap)
    in_meta, in_wl, in_fwhm, band_idx = _load_input_meta(
        inmap, hyper_meta_class, depth, valid_only
    )
    n_in = len(band_idx)
    in_min, in_max = float(in_wl.min()), float(in_wl.max())

    # ── clip to input range (no extrapolation) ────────────────────
    out_wl, out_fwhm_used, n_clipped = _clip_to_input_range(
        out_wl, out_fwhm_from_target, in_min, in_max
    )
    if len(out_wl) == 0:
        gs.fatal(
            "No output wavelengths fall within the input spectral range "
            f"[{in_min:.1f}, {in_max:.1f}] nm."
        )

    # ── resolve FWHM for Gaussian ──────────────────────────────────
    fwhm_for_kernel = None
    if method == "gaussian":
        if out_fwhm_used is not None and len(out_fwhm_used) == len(out_wl):
            fwhm_for_kernel = out_fwhm_used
        elif out_fwhm_from_target is not None and len(out_fwhm_from_target) > 0:
            fwhm_for_kernel = float(out_fwhm_from_target[0])
            gs.message(
                f"Using single FWHM = {fwhm_for_kernel:.2f} nm for all output bands."
            )
        elif in_fwhm is not None:
            fwhm_for_kernel = float(np.nanmean(in_fwhm))
            gs.message(
                f"Using mean input FWHM = {fwhm_for_kernel:.2f} nm for Gaussian kernel."
            )
        else:
            fwhm_for_kernel = 10.0
            gs.message(f"No FWHM found; using default {fwhm_for_kernel:.1f} nm.")

    # ── info mode ──────────────────────────────────────────────────
    n_out = len(out_wl)
    gs.message(f"Input:  {inmap} ({n_in} bands, {in_min:.1f}–{in_max:.1f} nm)")
    gs.message(f"Output: {outmap} ({n_out} bands, {out_wl[0]:.1f}–{out_wl[-1]:.1f} nm)")
    gs.message(f"Method: {method}")
    if method == "gaussian" and fwhm_for_kernel is not None:
        if isinstance(fwhm_for_kernel, np.ndarray):
            gs.message(
                f"FWHM:   {float(fwhm_for_kernel.min()):.2f} – "
                f"{float(fwhm_for_kernel.max()):.2f} nm (per‑band)"
            )
        else:
            gs.message(f"FWHM:   {fwhm_for_kernel:.2f} nm")
    if n_clipped > 0:
        gs.warning(
            f"{n_clipped} output wavelength(s) outside input range and will be omitted."
        )
    if info_only:
        return

    # ── resample ───────────────────────────────────────────────────
    gs.use_temp_region()
    try:
        gs.run_command("g.region", raster_3d=inmap, quiet=True)

        arr_in = garray.array3d(mapname=inmap, null="nan", dtype=np.float32)
        depth, rows, cols = arr_in.shape

        if n_in < depth:
            arr_in = arr_in[band_idx, :, :]

        exterior_mask = ~np.any(np.isfinite(arr_in), axis=0)

        flat = arr_in.reshape(n_in, -1).T  # (n_pixels, n_in)

        flat_out = specresamp.resample(
            flat, in_wl, out_wl, method=method, fwhm=fwhm_for_kernel
        )

        n_out_actual = flat_out.shape[1]
        arr_out = flat_out.T.reshape(n_out_actual, rows, cols)
        arr_out[:, exterior_mask] = np.nan
        out_validity = np.any(np.isfinite(arr_out), axis=(1, 2)).tolist()

        orig_region = gs.region()
        gs.run_command(
            "g.region",
            n=orig_region["n"],
            s=orig_region["s"],
            e=orig_region["e"],
            w=orig_region["w"],
            nsres=orig_region["nsres"],
            ewres=orig_region["ewres"],
            b=0,
            t=float(n_out_actual),
            tbres=1,
            quiet=True,
        )

        out_arr = garray.array3d(dtype=np.float32)
        out_arr[...] = arr_out
        out_arr.write(mapname=outmap, null="nan", overwrite=True)

        # ── save metadata ──────────────────────────────────────────
        cmd_params = {
            "input": inmap,
            "output": outmap,
            "method": method,
        }
        if valid_only:
            cmd_params["valid_only"] = True
        if options.get("reference"):
            cmd_params["reference"] = options["reference"]
        if options.get("wavelengths"):
            cmd_params["wavelengths"] = options["wavelengths"]
            cmd_params["fwhm"] = options.get("fwhm") or ""
        _write_resampled_metadata(
            inmap,
            outmap,
            out_wl,
            out_fwhm_used,
            out_validity,
            cmd_params,
            hyper_meta_class,
        )

    finally:
        gs.del_temp_region()


if __name__ == "__main__":
    sys.exit(main())
