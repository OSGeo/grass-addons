#!/usr/bin/env python

##############################################################################
# MODULE:    i.hyper.preproc
# AUTHOR(S): Alen Mangafic and Tomaž Žagar, Geodetic Institute of Slovenia
# PURPOSE:   Hyperspectral imagery preprocessing.
# SPDX-FileCopyrightText: 2025 Alen Mangafic
# SPDX-FileCopyrightText: Other GRASS authors
# SPDX-License-Identifier: GPL-2.0-or-later
##############################################################################

# %module
# % description: General hyperspectral data preprocessing
# % keyword: imagery
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


def _get_wavelengths(mapname, hyper_meta_class):
    try:
        meta = hyper_meta_class.load(mapname)
    except Exception:
        return None
    arr = meta.get_wavelengths_array()
    if arr is not None:
        return arr
    return None


def _to_full_map_name(mapname):
    if "@" in mapname:
        return mapname
    mapset = gs.gisenv().get("MAPSET", "")
    return f"{mapname}@{mapset}" if mapset else mapname


def _copy_and_update_hyper_metadata(src, dst, cmd_params, hyper_meta_class):
    try:
        meta = hyper_meta_class.load(src)
        src_dataset_id = meta.dataset_id

        # Derived dataset gets a new stable identity and its own local history entry.
        meta.dataset_id = hyper_meta_class.new_dataset_id()
        meta.derived = True
        meta.processing_history = []
        meta.dimensionality_reduction = None

        command = meta._command_from_module_params("i.hyper.preproc", cmd_params)
        meta.add_history_entry(
            command=command,
            inputs=[
                {
                    "id": src_dataset_id,
                    "map_name": _to_full_map_name(src),
                }
            ],
            outputs=[
                {
                    "id": meta.dataset_id,
                    "map_name": _to_full_map_name(dst),
                }
            ],
        )
        meta.save(dst)
    except Exception as error:
        gs.warning(f"Failed to write JSON hyperspectral metadata: {error}")


def _set_dr_metadata_payload(meta, method, info, n_components):
    dr_meta = {}
    name_map = {
        "pca": "PCA",
        "kpca": "Kernel PCA",
        "nystroem": "Nystroem",
        "fastica": "FastICA",
        "truncatedsvd": "TruncatedSVD",
        "nmf": "NMF",
        "sparsepca": "SparsePCA",
    }

    dr_meta["method"] = method
    dr_meta["method_display"] = name_map.get(method, method.upper())
    dr_meta["n_components"] = int(n_components or 0)

    kernel = info.get("kernel")
    if kernel is not None:
        dr_meta["kernel"] = str(kernel)
    gamma = info.get("gamma")
    if gamma is not None:
        dr_meta["gamma"] = float(gamma)
    degree = info.get("degree")
    if degree is not None:
        dr_meta["degree"] = int(degree)

    explained = info.get("explained_variance_ratio")
    if explained is not None:
        if hasattr(explained, "tolist"):
            explained = explained.tolist()
        explained = [float(v) for v in explained]
        dr_meta["explained_variance_ratio"] = explained
        dr_meta["explained_variance_percent"] = [float(v * 100.0) for v in explained]
    meta.dimensionality_reduction = dr_meta


def _set_dr_metadata(inmap, outmap, method, info, cmd_params, hyper_meta_class=None):
    try:
        src_meta = hyper_meta_class.load(inmap)
        explained = info.get("explained_variance_ratio")
        if explained is not None and hasattr(explained, "tolist"):
            explained = explained.tolist()

        n_components = info.get("n_components")
        if n_components is None:
            n_components = len(explained or [])
        if n_components is None:
            n_components = cmd_params.get("dr_components", 0)

        meta = hyper_meta_class.for_components(
            n_components=int(n_components or 0),
            explained_variance_ratio=explained,
        )
        _set_dr_metadata_payload(meta, method, info, n_components)

        command = meta._command_from_module_params("i.hyper.preproc", cmd_params)
        meta.add_history_entry(
            command=command,
            inputs=[
                {
                    "id": src_meta.dataset_id,
                    "map_name": _to_full_map_name(inmap),
                }
            ],
            outputs=[
                {
                    "id": meta.dataset_id,
                    "map_name": _to_full_map_name(outmap),
                }
            ],
        )
        meta.save(outmap)
    except Exception as error:
        gs.warning(f"Failed to write JSON hyperspectral metadata: {error}")


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
    hyper_meta_class = _load_hyper_meta_class()

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

    metadata_cmd_params = {
        "input": inp,
        "output": out,
        "polyorder": int(polyorder),
        "derivative_order": int(derivative_order),
        "window_length": int(window_length),
        "baseline": bool(baseline),
        "continuum": bool(continuum),
        "interpolate_nodata": bool(interpolate_nodata),
        "clamp_negative": bool(clamp_negative),
    }
    if dr_method:
        metadata_cmd_params.update(
            {
                "dr_method": dr_method,
                "dr_components": int(dr_components),
                "dr_kernel": dr_kernel,
                "dr_gamma": float(dr_gamma),
                "dr_degree": int(dr_degree),
                "dr_bands": dr_bands,
                "dr_export": dr_export,
                "dr_chunk_size": int(dr_chunk_size),
                "dr_max_iter": int(dr_max_iter),
                "dr_tol": float(dr_tol),
                "dr_alpha": float(dr_alpha),
                "dr_l1_ratio": float(dr_l1_ratio),
                "dr_random_state": int(dr_random_state),
            }
        )

    gs.use_temp_region()
    try:
        # Always operate in input cube region (XY and Z) to avoid region-driven
        # shape mismatches and all-NULL outputs.
        gs.run_command("g.region", raster_3d=inp, quiet=True)

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

        wavelengths = _get_wavelengths(inp, hyper_meta_class)
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

        if dr_method:
            dr_meta_info = dict(dr_info or {})
            dr_meta_info.setdefault("n_components", n_bands)
            _set_dr_metadata(
                inp,
                out,
                dr_method,
                dr_meta_info,
                metadata_cmd_params,
                hyper_meta_class=hyper_meta_class,
            )
        else:
            _copy_and_update_hyper_metadata(
                inp,
                out,
                metadata_cmd_params,
                hyper_meta_class,
            )
    finally:
        gs.del_temp_region()


def main():
    options, flags = gs.parser()
    try:
        from scipy.interpolate import interp1d  # noqa: E402
    except ModuleNotFoundError:
        gs.fatal(_("SciPy library not installed"))

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

