#!/usr/bin/env python

##############################################################################
# MODULE:    i.hyper.preproc
# AUTHOR(S): Alen Mangafic and Tomaž Žagar, Geodetic Institute of Slovenia
# PURPOSE:   Hyperspectral imagery preprocessing.
# COPYRIGHT: (C) 2025 by Alen Mangafic and the GRASS Development Team
# SPDX-License-Identifier: GPL-2.0-or-later
##############################################################################

# %module
# % description: General hyperspectral data preprocessing
# % keyword: raster
# % keyword: hyperspectral
# % keyword: preprocessing
# %end

# %option G_OPT_R3_INPUT
# % key: input
# % description: Input hyperspectral raster map
# % required: yes
# % guisection: Input
# %end

# %option G_OPT_R3_OUTPUT
# % key: output
# % description: Output preprocessed raster map
# % required: yes
# % guisection: Output
# %end

# %option
# % key: polyorder
# % type: integer
# % description: Polynomial order for Savitzky-Golay filter (0 = skip Savitzky-Golay)
# % required: no
# % answer: 0
# % guisection: Savitzky-Golay
# %end

# %option
# % key: derivative_order
# % type: integer
# % description: Derivative order (0 = smoothing only)
# % required: no
# % answer: 0
# % guisection: Savitzky-Golay
# %end

# %option
# % key: window_length
# % type: integer
# % description: Window length (must be odd number)
# % required: no
# % answer: 11
# % guisection: Savitzky-Golay
# %end

# %option
# % key: dr_method
# % type: string
# % options: pca,kpca,nystroem,fastica,truncatedsvd,nmf,sparsepca
# % description: Dimensionality reduction method (linear or nonlinear)
# % required: no
# % guisection: Dimensionality reduction
# %end

# %option
# % key: dr_components
# % type: integer
# % description: Number of components to retain (PCA,KPCA,Nystroem,FastICA,TruncatedSVD,NMF,SparsePCA). 0 = automatic (up to 10 or number of bands)
# % required: no
# % answer: 0
# % guisection: Dimensionality reduction
# %end

# %option
# % key: dr_kernel
# % type: string
# % options: linear,rbf,poly,sigmoid
# % description: Kernel type (used only for KPCA and Nystroem)
# % required: no
# % answer: rbf
# % guisection: Dimensionality reduction
# %end

# %option
# % key: dr_gamma
# % type: double
# % description: Kernel gamma (KPCA and Nystroem only)
# % required: no
# % answer: 0.01
# % guisection: Dimensionality reduction
# %end

# %option
# % key: dr_degree
# % type: integer
# % description: Polynomial degree (used if kernel=poly)
# % required: no
# % answer: 3
# % guisection: Dimensionality reduction
# %end

# %option
# % key: dr_max_iter
# % type: integer
# % description: Maximum iterations for convergence (FastICA,NMF,SparsePCA)
# % required: no
# % answer: 200
# % guisection: Dimensionality reduction
# %end

# %option
# % key: dr_tol
# % type: double
# % description: Convergence tolerance (FastICA,NMF,SparsePCA)
# % required: no
# % answer: 1e-4
# % guisection: Dimensionality reduction
# %end

# %option
# % key: dr_alpha
# % type: double
# % description: Regularization strength (NMF,SparsePCA)
# % required: no
# % answer: 0.0
# % guisection: Dimensionality reduction
# %end

# %option
# % key: dr_l1_ratio
# % type: double
# % description: L1 ratio in [0,1] (NMF,SparsePCA)
# % required: no
# % answer: 0.0
# % guisection: Dimensionality reduction
# %end

# %option
# % key: dr_random_state
# % type: integer
# % description: Random seed for reproducibility (PCA,FastICA,NMF,SparsePCA,TruncatedSVD)
# % required: no
# % answer: 0
# % guisection: Dimensionality reduction
# %end

# %option
# % key: dr_chunk_size
# % type: integer
# % description: Number of spectra per chunk for dimensionality reduction (0 = automatic; KPCA is approximated if chunked)
# % required: no
# % answer: 0
# % guisection: Dimensionality reduction
# %end

# %option
# % key: dr_bands
# % type: string
# % description: Wavelength intervals or single values to include before reduction (e.g., 400–700,850–1300,2200)
# % required: no
# % guisection: Dimensionality reduction
# %end

# %option G_OPT_F_OUTPUT
# % key: dr_export
# % description: Optional path to export fitted reduction model (.pkl) for reuse
# % required: no
# % guisection: Dimensionality reduction
# %end

# %flag
# % key: b
# % description: Apply baseline correction
# % guisection: Additional corrections
# %end

# %flag
# % key: c
# % description: Apply continuum removal
# % guisection: Additional corrections
# %end

# %flag
# % key: q
# % description: Interpolate missing values in valid bands
# % guisection: Additional corrections
# %end

# %flag
# % key: z
# % description: Clamp negative values to zero
# % guisection: Additional corrections
# %end

import sys
import os
import tempfile
import contextlib
import numpy as np
from scipy.interpolate import interp1d
import grass.script as gs
import grass.script.array as garray
from grass.script.utils import get_lib_path
import importlib.util
import re


def _import_from_i_hyper_lib(module_name):
    path = get_lib_path(modname="i_hyper_lib", libname=module_name)
    if not path:
        gs.fatal(f"Library path for {module_name} not found.")
    if path not in sys.path:
        sys.path.append(path)
    spec = importlib.util.find_spec(module_name)
    if not spec:
        gs.fatal(f"Module {module_name} not found at {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _load_processing_libs():
    savgol = _import_from_i_hyper_lib("sav_gol")
    basecorr = _import_from_i_hyper_lib("base_corr")
    contrem = _import_from_i_hyper_lib("continuum_rem")
    dimred = _import_from_i_hyper_lib("dim_red")
    return (
        savgol._savgol_preserve_nan,
        basecorr._baseline_correction,
        contrem._continuum_removal,
        dimred._apply_dimensionality_reduction,
    )


def _fill_nans_1d(x):
    v = np.asarray(x, dtype=np.float32)
    m = np.isfinite(v)
    if m.sum() < 2:
        return v
    xi = np.arange(v.size, dtype=np.float32)
    f = interp1d(
        xi[m], v[m], kind="linear", fill_value="extrapolate", assume_sorted=True
    )
    return f(xi).astype(np.float32)


def _get_wavelengths_from_r3info(mapname):
    try:
        meta = gs.read_command("r3.info", map=mapname)
    except Exception:
        return None
    wl = []
    for line in meta.splitlines():
        if "wavelength" in line.lower():
            vals = re.findall(r"[\d.]+", line)
            if vals:
                wl = [float(v) for v in vals]
                break
    return wl if wl else None


def _copy_r3_metadata(src, dst):
    fd, tmp = tempfile.mkstemp(prefix="r3hist_", suffix=".txt")
    os.close(fd)
    with contextlib.suppress(FileNotFoundError):
        os.remove(tmp)
    try:
        gs.run_command(
            "r3.support", map=src, savehistory=tmp, overwrite=True, quiet=True
        )
        gs.run_command(
            "r3.support", map=dst, loadhistory=tmp, overwrite=True, quiet=True
        )
        gi = gs.parse_command("r3.info", flags="g", map=src)
        title = gi.get("title")
        vunit = gi.get("vertical_unit")
        if title:
            gs.run_command("r3.support", map=dst, title=title, quiet=True)
        if vunit:
            gs.run_command("r3.support", map=dst, vunit=vunit, quiet=True)
    finally:
        with contextlib.suppress(Exception):
            os.remove(tmp)


def _set_dr_metadata(outmap, method, info):
    lines = []
    name_map = {
        "pca": "PCA",
        "kpca": "Kernel PCA",
        "nystroem": "Nystroem",
        "fastica": "FastICA",
        "truncatedsvd": "TruncatedSVD",
        "nmf": "NMF",
        "sparsepca": "SparsePCA",
    }
    mdisp = name_map.get(method, method.upper())
    if method == "pca" and "explained_variance_ratio" in info:
        var = info["explained_variance_ratio"]
        lines.append(f"Principal Component Analysis ({mdisp})")
        for i, v in enumerate(var, 1):
            lines.append(f"Component {i}: {v * 100:.2f}% variance explained")
    elif method in ["kpca", "nystroem"]:
        lines.append(
            f"{mdisp} (kernel={info.get('kernel')}, gamma={info.get('gamma')}, degree={info.get('degree')})"
        )
        lines.append(f"Components: {info.get('n_components')}")
    if lines:
        gs.run_command(
            "r3.support", map=outmap, description="\n".join(lines), quiet=True
        )


def preprocess_hyperspectral(
    inp,
    out,
    window_length=11,
    polyorder=0,
    derivative_order=0,
    interpolate_nodata=False,
    clamp_negative=False,
    baseline=False,
    continuum=False,
    dr_method=None,
    dr_components=0,
    dr_kernel="rbf",
    dr_gamma=0.01,
    dr_degree=3,
    dr_bands=None,
    dr_export=None,
    dr_chunk_size=0,
    dr_max_iter=200,
    dr_tol=1e-4,
    dr_alpha=0.0,
    dr_l1_ratio=0.0,
    dr_random_state=0,
):
    (
        _savgol_preserve_nan,
        _baseline_correction,
        _continuum_removal,
        _apply_dimensionality_reduction,
    ) = _load_processing_libs()

    if dr_method:
        dr_method = dr_method.lower()

    if (
        int(polyorder) == 0
        and not baseline
        and not continuum
        and not clamp_negative
        and not interpolate_nodata
        and not dr_method
    ):
        gs.fatal(
            "No processing option selected. Use preprocessing or dimensionality reduction parameters."
        )

    if int(window_length) % 2 == 0:
        gs.fatal("Window length must be an odd number")

    steps = []
    if polyorder > 0:
        steps.append("Savitzky–Golay")
    if baseline:
        steps.append("Baseline correction")
    if continuum:
        steps.append("Continuum removal")
    if dr_method:
        steps.append(dr_method.upper())
    gs.message(" → ".join(steps) if steps else "No operations selected")

    arr_in = garray.array3d(mapname=inp, null="nan", dtype=np.float32)
    depth, rows, cols = arr_in.shape
    exterior_mask = ~np.any(np.isfinite(arr_in), axis=0)
    flat = arr_in.reshape(depth, -1).T

    flat_filt = flat
    if polyorder > 0:
        flat_filt = np.apply_along_axis(
            _savgol_preserve_nan,
            1,
            flat,
            window_length,
            polyorder,
            derivative_order,
            interpolate_nodata,
        ).astype(np.float32)

    if baseline:
        flat_filt = np.apply_along_axis(_baseline_correction, 1, flat_filt).astype(
            np.float32
        )

    if continuum:
        flat_filt = np.apply_along_axis(_continuum_removal, 1, flat_filt).astype(
            np.float32
        )

    if interpolate_nodata:
        gs.message("Interpolating missing values across spectral bands...")
        for i in range(flat_filt.shape[0]):
            row = flat_filt[i, :]
            if np.isnan(row).any():
                flat_filt[i, :] = _fill_nans_1d(row)

    if clamp_negative:
        flat_filt = np.where(flat_filt < 0, 0, flat_filt).astype(np.float32)

    wavelengths = _get_wavelengths_from_r3info(inp)
    if dr_bands and wavelengths is None:
        gs.message("No wavelength metadata found; ignoring dr_bands filter.")

    dr_info = None
    if dr_method:
        flat_filt, dr_info = _apply_dimensionality_reduction(
            flat_filt,
            method=dr_method,
            n_components=dr_components,
            kernel=dr_kernel,
            gamma=dr_gamma,
            degree=dr_degree,
            bands=dr_bands,
            wavelengths=wavelengths,
            export_path=dr_export,
            chunk_size=dr_chunk_size if dr_chunk_size > 0 else None,
            memory_limit_gb=8,
            max_iter=dr_max_iter,
            tol=dr_tol,
            alpha=dr_alpha,
            l1_ratio=dr_l1_ratio,
            random_state=dr_random_state,
        )

    n_bands = flat_filt.shape[1]
    arr_out = flat_filt.T.reshape(n_bands, rows, cols)
    arr_out[:, exterior_mask] = np.nan

    if dr_method:
        orig_region = gs.region()
        gs.use_temp_region()
        try:
            gs.run_command(
                "g.region",
                n=orig_region["n"],
                s=orig_region["s"],
                e=orig_region["e"],
                w=orig_region["w"],
                nsres=orig_region["nsres"],
                ewres=orig_region["ewres"],
                b=0,
                t=float(n_bands),
                tbres=1,
                quiet=True,
            )
            out_arr = garray.array3d(dtype=np.float32)
            out_arr[...] = arr_out
            out_arr.write(mapname=out, null="nan", overwrite=True)
        finally:
            gs.del_temp_region()
    else:
        out_arr = garray.array3d(dtype=np.float32)
        out_arr[...] = arr_out
        out_arr.write(mapname=out, null="nan", overwrite=True)

    _copy_r3_metadata(inp, out)
    if dr_method:
        _set_dr_metadata(out, dr_method, dr_info or {})

    cmd_line = "i.hyper.preproc " + " ".join(sys.argv[1:])
    gs.run_command("r3.support", map=out, history=cmd_line, quiet=True)


def main():
    options, flags = gs.parser()

    preprocess_hyperspectral(
        inp=options["input"],
        out=options["output"],
        window_length=int(options["window_length"]),
        polyorder=int(options["polyorder"]),
        derivative_order=int(options["derivative_order"]),
        interpolate_nodata=bool(flags.get("q")),
        clamp_negative=bool(flags.get("z")),
        baseline=bool(flags.get("b")),
        continuum=bool(flags.get("c")),
        dr_method=(options["dr_method"] or "").lower() or None,
        dr_components=int(options["dr_components"]),
        dr_kernel=options["dr_kernel"],
        dr_gamma=float(options["dr_gamma"]),
        dr_degree=int(options["dr_degree"]),
        dr_bands=options["dr_bands"] or None,
        dr_export=options["dr_export"] or None,
        dr_chunk_size=int(options["dr_chunk_size"]),
        dr_max_iter=int(options["dr_max_iter"]),
        dr_tol=float(options["dr_tol"]),
        dr_alpha=float(options["dr_alpha"]),
        dr_l1_ratio=float(options["dr_l1_ratio"]),
        dr_random_state=int(options["dr_random_state"]),
    )


if __name__ == "__main__":
    sys.exit(main())
