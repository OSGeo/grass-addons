#!/usr/bin/env python

############################################################################
#
# MODULE:       i.omnicloudmask
# AUTHOR(S):    Paulo van Breugel
# PURPOSE:      Run OmniCloudMask on GRASS rasters or on an external multiband
#               GeoTIFF to detect clouds and cloud shaodows, and import the
#               result into GRASS GIS.
#
# DESCRIPTION:  The module supports two execution paths:
#               1. GRASS rasters to arrays which are used in
#                  predict_from_array()
#               2. External multiband GeoTIFF, used as input directly in
#                  omnicloudmask predict_from_load_func() function.
#
#               The module produces either a categorical class prediction raster
#               or, with -c, four confidence rasters.
#
# COPYRIGHT:    (C) 2026 by Paulo van Breugel and the GRASS Development Team
#
#               This program is free software under the GNU General Public
#               License (>=v2). Read the file COPYING that comes with GRASS
#               for details.
#
# This program is free software under the GNU General Public
# License (>=v2). Read the file COPYING that comes with GRASS
# for details.
#
############################################################################

# %module
# % description: Predict cloud and cloud-shadow classes with OmniCloudMask from GRASS rasters or a multiband GeoTIFF.
# % keyword: imagery
# % keyword: raster
# % keyword: cloud mask
# % keyword: remote sensing
# % keyword: deep learning
# %end

# %option G_OPT_R_INPUT
# % key: red
# % label: Red band raster
# % required: no
# % guisection: GRASS rasters
# %end

# %option G_OPT_R_INPUT
# % key: green
# % label: Green band raster
# % required: no
# % guisection: GRASS rasters
# %end

# %option G_OPT_R_INPUT
# % key: nir
# % label: NIR band raster
# % required: no
# % guisection: GRASS rasters
# %end

# %option G_OPT_F_BIN_INPUT
# % key: geotiff
# % label: Input GeoTIFF
# % description: Optional alternative to red,green,nir input rasters. When used, the whole GeoTIFF is processed with omnicloudmask.predict_from_load_func() and imported into GRASS.
# % required: no
# % guisection: GeoTIFF
# %end

# %option
# % key: geotiff_band_order
# % type: string
# % label: band order
# % description: Comma-separated band numbers for Red,Green,NIR for GeoTIFF input
# % answer: 1,2,4
# % required: no
# % guisection: GeoTIFF
# %end

# %option G_OPT_R_OUTPUT
# % key: output
# % label: Output raster or basename
# % description: Output class raster name, or basename for confidence rasters when -c is used. Class values are 0=Clear, 1=Thick Cloud, 2=Thin Cloud, 3=Cloud Shadow.
# % required: yes
# %end

# %flag
# % key: c
# % label: Export confidence rasters
# % description: Creates four confidence rasters named from output= with suffixes clear, thick_cloud, thin_cloud, cloud_shadow.
# % guisection: Confidence output
# %end

# %flag
# % key: l
# % label: Low-memory mode for confidence output
# % description: Computes softmax normalization in GRASS (r.mapcalc) instead of on the inference device. Use this if GPU or system memory is insufficient for the built-in softmax. Only relevant with -c.
# % guisection: Confidence output
# %end

# %option
# % key: patch_size
# % type: integer
# % answer: 1000
# % description: Patch size for inference
# % required: no
# % guisection: OmniCloudMask
# %end

# %option
# % key: patch_overlap
# % type: integer
# % answer: 300
# % description: Overlap between adjacent patches
# % required: no
# % guisection: OmniCloudMask
# %end

# %option
# % key: batch_size
# % type: integer
# % answer: 1
# % description: Number of patches per inference batch
# % required: no
# % guisection: OmniCloudMask
# %end

# %option
# % key: inference_device
# % type: string
# % options: auto,cpu,cuda,mps
# % answer: auto
# % description: Device for inference
# % required: no
# % guisection: OmniCloudMask
# %end

# %option
# % key: mosaic_device
# % type: string
# % options: auto,cpu,cuda,mps
# % answer: auto
# % description: Device for mosaicking patches
# % required: no
# % guisection: OmniCloudMask
# %end

# %option
# % key: inference_dtype
# % type: string
# % options: fp32,fp16,bf16
# % answer: fp32
# % description: Inference data type
# % required: no
# % guisection: OmniCloudMask
# %end

# %option
# % key: no_data_value
# % type: double
# % answer: 0
# % description: Value indicating no-data pixels in input
# % required: no
# % guisection: OmniCloudMask
# %end

# %flag
# % key: n
# % label: Do not apply OmniCloudMask no-data masking
# % description: By default, no-data regions are masked in the output.
# % guisection: OmniCloudMask
# %end

# %flag
# % key: m
# % label: Compile models with torch.compile
# % description: May improve runtime after compilation overhead.
# % guisection: OmniCloudMask
# %end

# %option
# % key: compile_mode
# % type: string
# % answer: default
# % description: torch.compile mode passed to OmniCloudMask
# % required: no
# % guisection: OmniCloudMask
# %end

# %option
# % key: model_version
# % type: string
# % options: 1.0,2.0,3.0,4.0
# % description: OmniCloudMask model version. Latest is used when omitted.
# % required: no
# % guisection: OmniCloudMask
# %end

# %option G_OPT_M_DIR
# % key: destination_model_dir
# % label: Directory for cached OmniCloudMask models
# % required: no
# % guisection: OmniCloudMask
# %end

# %option
# % key: model_download_source
# % type: string
# % options: hugging_face,google_drive
# % answer: hugging_face
# % description: Model download source
# % required: no
# % guisection: OmniCloudMask
# %end

# %option
# % key: memory
# % type: integer
# % answer: 300
# % description: Maximum memory in MB for r.in.gdal when importing GeoTIFF outputs into GRASS
# % required: no
# % guisection: GRASS import
# %end

# %option
# % key: nprocs
# % type: integer
# % answer: 1
# % description: Number of threads for r.mapcalc parallel computing (used with -l)
# % required: no
# % guisection: Confidence output
# %end

# %flag
# % key: r
# % label: Limit output GeoTIFF import to current region
# % description: Passed to r.in.gdal only when importing GeoTIFF outputs from the file-based workflow.
# % guisection: GRASS import
# %end

# %rules
# % required: red,green,nir, geotiff
# % exclusive: geotiff, red
# % exclusive: geotiff, green
# % exclusive: geotiff, nir
# % collective: red,green,nir
# %end

from __future__ import annotations

import atexit
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Sequence

import numpy as np

import grass.script as gs
import grass.script.array as garray


CATEGORY_RULES = """0:Clear
1:Thick Cloud
2:Thin Cloud
3:Cloud Shadow
"""

COLOR_RULES = """0 255:255:255
1 255:0:0
2 255:192:203
3 88:12:12
nv 0:0:0
default 0:0:0
"""

CONFIDENCE_SUFFIXES = [
    "clear",
    "thick_cloud",
    "thin_cloud",
    "cloud_shadow",
]

CONFIDENCE_TITLES = [
    "Clear confidence",
    "Thick cloud confidence",
    "Thin cloud confidence",
    "Cloud shadow confidence",
]

TEMP_PATHS: list[Path] = []


def cleanup() -> None:
    """Remove temporary files and directories created by the module."""
    for path in reversed(TEMP_PATHS):
        try:
            if path.is_dir():
                shutil.rmtree(path, ignore_errors=True)
            elif path.exists():
                path.unlink()
        except OSError:
            pass


def ensure_dependencies() -> None:
    """Import OmniCloudMask lazily."""
    try:
        import omnicloudmask  # noqa: F401
    except ImportError as error:
        gs.fatal(
            "The Python package 'omnicloudmask' is required but could not be "
            f"imported: {error}"
        )


def parse_band_order(text: str) -> list[int]:
    """Parse a comma-separated GeoTIFF band order specification.

    OmniCloudMask expects 1-indexed band numbers for load_multiband().
    Returns a list of exactly three positive integers.
    """
    try:
        values = [int(item.strip()) for item in text.split(",") if item.strip()]
    except ValueError as error:
        gs.fatal(f"Invalid geotiff_band_order value: {error}")
        return []  # unreachable; satisfies static analysis
    if len(values) != 3:
        gs.fatal("geotiff_band_order must contain exactly three integers")
    if any(value < 1 for value in values):
        gs.fatal("geotiff_band_order must use 1-indexed positive band numbers")
    return values


def omnicloud_common_kwargs(
    options: dict[str, str], flags: dict[str, bool]
) -> dict[str, object]:
    """Build the keyword arguments shared by predict_from_array() and predict_from_load_func().

    Covers patch_size, patch_overlap, batch_size, device settings, no-data
    handling, model compilation, model version, and download source.

    When -l is set, softmax_output is False so OmniCloudMask returns raw
    logits; softmax will be computed in GRASS via r.mapcalc instead.
    """
    kwargs: dict[str, object] = {
        "patch_size": int(options["patch_size"]),
        "patch_overlap": int(options["patch_overlap"]),
        "batch_size": int(options["batch_size"]),
        "inference_dtype": options["inference_dtype"],
        "softmax_output": not flags["l"],
        "no_data_value": float(options["no_data_value"]),
        "apply_no_data_mask": not flags["n"],
        "compile_models": bool(flags["m"]),
        "compile_mode": options["compile_mode"],
        "model_download_source": options["model_download_source"],
    }

    inference_device = none_if_auto(options["inference_device"])
    mosaic_device = none_if_auto(options["mosaic_device"])
    if inference_device is not None:
        kwargs["inference_device"] = inference_device
    if mosaic_device is not None:
        kwargs["mosaic_device"] = mosaic_device
    if options["destination_model_dir"]:
        kwargs["destination_model_dir"] = options["destination_model_dir"]
    if options["model_version"]:
        kwargs["model_version"] = float(options["model_version"])
    return kwargs


def none_if_auto(value: str) -> str | None:
    """Translate the UI value 'auto' to None for OmniCloudMask."""
    if not value or value == "auto":
        return None
    return value


def build_input_array(red: str, green: str, nir: str) -> np.ndarray:
    """Read red, green, and NIR GRASS rasters and stack them into a (3, H, W) array."""
    red_array = raster_to_numpy(red)
    green_array = raster_to_numpy(green)
    nir_array = raster_to_numpy(nir)
    return np.stack([red_array, green_array, nir_array], axis=0)


def raster_to_numpy(map_name: str, dtype: np.dtype = np.float32) -> np.ndarray:
    """Read a GRASS raster into a NumPy array honoring the current region."""
    return np.asarray(garray.array(mapname=map_name), dtype=dtype)


def write_numpy_to_raster(
    array: np.ndarray, map_name: str, title: str | None = None
) -> None:
    """Write a 2-D NumPy array to a GRASS raster map."""
    grass_array = garray.array(dtype=array.dtype)
    grass_array[:] = array
    grass_array.write(mapname=map_name, title=title, overwrite=gs.overwrite())


def apply_categories_and_colors(map_name: str) -> None:
    """Assign category labels and a categorical color table to the class raster."""
    gs.write_command(
        "r.category",
        map=map_name,
        rules="-",
        stdin=CATEGORY_RULES,
        separator=":",
    )
    gs.write_command("r.colors", map=map_name, rules="-", stdin=COLOR_RULES)


def write_support_metadata(
    map_name: str,
    title: str,
    source_description: str,
    inference_description: str,
) -> None:
    """Write raster metadata and processing history."""
    gs.run_command("r.support", map=map_name, title=title)
    gs.run_command(
        "r.support",
        map=map_name,
        history=f"Created by i.omnicloudmask from {source_description}",
    )
    gs.run_command(
        "r.support",
        map=map_name,
        history=f"Inference settings: {inference_description}",
    )
    gs.run_command(
        "r.support",
        map=map_name,
        history="Classes: 0=Clear, 1=Thick Cloud, 2=Thin Cloud, 3=Cloud Shadow",
    )


def write_confidence_metadata(
    map_name: str,
    title: str,
    class_name: str,
    source_description: str,
    inference_description: str,
) -> None:
    """Write metadata for a confidence raster, including history."""
    gs.run_command("r.support", map=map_name, title=title)
    gs.run_command(
        "r.support",
        map=map_name,
        history=f"Created by i.omnicloudmask from {source_description}",
    )
    gs.run_command(
        "r.support",
        map=map_name,
        history=f"Confidence class: {class_name}",
    )
    gs.run_command(
        "r.support",
        map=map_name,
        history=f"Inference settings: {inference_description}",
    )


def confidence_color_rules() -> str:
    """Return a continuous graduated color ramp for confidence rasters with value in the 0-1 range."""
    return """0 245:245:245
0.25 198:219:239
0.5 158:202:225
0.75 49:130:189
1 8:81:156
nv 0:0:0
"""


def apply_confidence_colors(map_name: str) -> None:
    """Apply the 0-1 confidence color ramp."""
    gs.write_command(
        "r.colors", map=map_name, rules="-", stdin=confidence_color_rules()
    )


def apply_softmax_in_grass(basename: str, nprocs: int = 1) -> None:
    """Apply softmax normalization to four raw-logit confidence rasters in GRASS.

    This replicates the normalization that OmniCloudMask performs internally
    (see coordinator() in cloud_mask.py):

        softmax(x_i) = exp(x_i - max(x)) / sum(exp(x_j - max(x)))
        output_i = clip(softmax(x_i) + 0.001, 0.001, 0.999)

    The subtraction of max() before exp() is standard numerical stabilization.
    The computation uses two r.mapcalc calls: the first computes the
    exponentials and their sum, the second normalizes and clips.

    Intermediate maps (_exp_clear, _exp_thick_cloud, _exp_thin_cloud,
    _exp_cloud_shadow, _exp_sum) are removed after normalization.

    Args:
        basename: Base name for the confidence rasters.
        nprocs: Number of threads for r.mapcalc parallel computing.
    """
    b = basename
    map_names = [f"{b}_{s}" for s in CONFIDENCE_SUFFIXES]
    max_expr = f"max({', '.join(map_names)})"

    # Step 1: compute exponentials (with max subtraction) and their sum
    gs.message("Computing softmax normalization in GRASS (low-memory mode)...")
    gs.mapcalc(
        f"{b}_exp_clear = exp({b}_clear - {max_expr});"
        f"{b}_exp_thick_cloud = exp({b}_thick_cloud - {max_expr});"
        f"{b}_exp_thin_cloud = exp({b}_thin_cloud - {max_expr});"
        f"{b}_exp_cloud_shadow = exp({b}_cloud_shadow - {max_expr});"
        f"{b}_exp_sum = {b}_exp_clear + {b}_exp_thick_cloud"
        f" + {b}_exp_thin_cloud + {b}_exp_cloud_shadow",
        overwrite=True,
        nprocs=nprocs,
    )

    # Step 2: normalize, add 0.001 offset, clip to [0.001, 0.999]
    gs.mapcalc(
        f"{b}_clear = min(0.999, max(0.001,"
        f" {b}_exp_clear / {b}_exp_sum + 0.001));"
        f"{b}_thick_cloud = min(0.999, max(0.001,"
        f" {b}_exp_thick_cloud / {b}_exp_sum + 0.001));"
        f"{b}_thin_cloud = min(0.999, max(0.001,"
        f" {b}_exp_thin_cloud / {b}_exp_sum + 0.001));"
        f"{b}_cloud_shadow = min(0.999, max(0.001,"
        f" {b}_exp_cloud_shadow / {b}_exp_sum + 0.001))",
        overwrite=True,
        nprocs=nprocs,
    )

    # Clean up intermediate maps
    intermediate = [
        f"{b}_exp_clear",
        f"{b}_exp_thick_cloud",
        f"{b}_exp_thin_cloud",
        f"{b}_exp_cloud_shadow",
        f"{b}_exp_sum",
    ]
    gs.run_command(
        "g.remove",
        flags="f",
        type="raster",
        name=",".join(intermediate),
        quiet=True,
    )


def import_raster_from_geotiff(
    input_path: Path,
    output_name: str,
    memory_mb: int,
    *,
    limit_to_region: bool,
) -> None:
    """Import a single-band GeoTIFF result into GRASS using r.in.gdal."""
    import_flags = "r" if limit_to_region else ""
    gs.run_command(
        "r.in.gdal",
        input=str(input_path),
        output=output_name,
        memory=memory_mb,
        flags=import_flags,
        overwrite=gs.overwrite(),
    )


def build_inference_description(
    options: dict[str, str], flags: dict[str, bool], *, export_confidence: bool
) -> str:
    """Create a history string summarising inference settings."""
    parts = [
        f"patch_size={options['patch_size']}",
        f"patch_overlap={options['patch_overlap']}",
        f"batch_size={options['batch_size']}",
        f"inference_device={options['inference_device']}",
        f"mosaic_device={options['mosaic_device']}",
        f"inference_dtype={options['inference_dtype']}",
        f"export_confidence={export_confidence}",
        f"no_data_value={options['no_data_value']}",
        f"apply_no_data_mask={not flags['n']}",
        f"compile_models={bool(flags['m'])}",
        f"compile_mode={options['compile_mode']}",
        f"model_download_source={options['model_download_source']}",
    ]
    if flags["l"]:
        parts.append("softmax=grass_mapcalc")
    if options["model_version"]:
        parts.append(f"model_version={options['model_version']}")
    return ", ".join(parts)


def _handle_inference_error(error: RuntimeError, options: dict[str, str]) -> None:
    """Translate common inference errors into actionable GRASS fatal messages.

    CUDA and MPS out-of-memory errors are RuntimeError in PyTorch. This
    function detects them and suggests concrete remedies ordered from least
    to most disruptive.
    """
    error_msg = str(error)
    if "out of memory" in error_msg.lower() or "OutOfMemoryError" in error_msg:
        hints = [
            "mosaic_device=cpu (moves only the patch mosaicking to CPU)",
            "inference_dtype=fp16 (halves GPU memory usage)",
            "the -l flag (computes softmax in GRASS instead of on the device)",
            "a smaller patch_size= (e.g., 500 instead of 1000)",
            "a smaller batch_size=",
            "inference_device=cpu (slow, but avoids GPU memory limits entirely)",
        ]
        gs.fatal(
            f"Device ran out of memory during inference "
            f"(patch_size={options['patch_size']}, "
            f"batch_size={options['batch_size']}, "
            f"inference_dtype={options['inference_dtype']}, "
            f"mosaic_device={options['mosaic_device']}). "
            "To reduce memory usage, try (in order of preference): " + "; ".join(hints)
        )
    gs.fatal(f"OmniCloudMask inference failed: {error}")


def run_array_prediction(
    red: str,
    green: str,
    nir: str,
    options: dict[str, str],
    flags: dict[str, bool],
) -> np.ndarray:
    """Run OmniCloudMask on GRASS rasters and return the class prediction.

    The returned array has shape (1, H, W) with class values 0-3.
    """
    import omnicloudmask

    input_array = build_input_array(red, green, nir)

    common_kwargs = omnicloud_common_kwargs(options, flags)
    common_kwargs["export_confidence"] = False

    try:
        prediction = omnicloudmask.predict_from_array(
            input_array=input_array, **common_kwargs
        )
    except RuntimeError as error:
        _handle_inference_error(error, options)
    return np.asarray(prediction)


def run_array_confidence_prediction(
    red: str,
    green: str,
    nir: str,
    options: dict[str, str],
    flags: dict[str, bool],
) -> np.ndarray:
    """Run OmniCloudMask on GRASS rasters and return confidence maps.

    The returned array has shape (4, H, W) with one band per class.
    When -l is not set, values are softmax probabilities (0-1).
    When -l is set, values are raw logits to be normalized in GRASS.
    """
    import omnicloudmask

    input_array = build_input_array(red, green, nir)

    common_kwargs = omnicloud_common_kwargs(options, flags)
    common_kwargs["export_confidence"] = True

    try:
        confidence = omnicloudmask.predict_from_array(
            input_array=input_array, **common_kwargs
        )
    except RuntimeError as error:
        _handle_inference_error(error, options)
    return np.asarray(confidence)


def write_class_raster(
    class_array: np.ndarray,
    output_name: str,
    source_description: str,
    inference_description: str,
) -> None:
    """Write the class raster and decorate it with categories, colors, and metadata."""
    class_2d = np.asarray(class_array).squeeze().astype(np.int32)
    write_numpy_to_raster(class_2d, output_name, title="OmniCloudMask class prediction")
    apply_categories_and_colors(output_name)
    write_support_metadata(
        output_name,
        title="OmniCloudMask class prediction",
        source_description=source_description,
        inference_description=inference_description,
    )


def write_confidence_rasters(
    confidence_array: np.ndarray,
    basename: str,
) -> list[str]:
    """Write four confidence rasters and return their map names."""
    if confidence_array.shape[0] != 4:
        gs.fatal(
            f"Expected four confidence bands from OmniCloudMask, "
            f"got shape {confidence_array.shape}"
        )

    created_maps: list[str] = []
    for index, suffix in enumerate(CONFIDENCE_SUFFIXES):
        map_name = f"{basename}_{suffix}"
        band = np.asarray(confidence_array[index], dtype=np.float32)
        write_numpy_to_raster(
            band, map_name, title=f"OmniCloudMask {CONFIDENCE_TITLES[index]}"
        )
        created_maps.append(map_name)

    return created_maps


def decorate_confidence_rasters(
    basename: str,
    source_description: str,
    inference_description: str,
) -> None:
    """Apply colors and metadata to the four confidence rasters."""
    for index, suffix in enumerate(CONFIDENCE_SUFFIXES):
        map_name = f"{basename}_{suffix}"
        apply_confidence_colors(map_name)
        write_confidence_metadata(
            map_name,
            title=f"OmniCloudMask {CONFIDENCE_TITLES[index]}",
            class_name=CONFIDENCE_TITLES[index],
            source_description=source_description,
            inference_description=inference_description,
        )


def select_loader_for_geotiff(band_order: Sequence[int]):
    """Return a loader callable compatible with predict_from_load_func().

    The returned function accepts a single file path argument and loads the
    GeoTIFF with the specified Red, Green, NIR band order.
    """
    import omnicloudmask

    def _load_multiband(scene_path: str):
        return omnicloudmask.load_multiband(scene_path, band_order=list(band_order))

    return _load_multiband


def run_geotiff_prediction(
    geotiff: str,
    options: dict[str, str],
    flags: dict[str, bool],
    *,
    export_confidence: bool,
) -> list[Path]:
    """Run the file-based workflow using predict_from_load_func().

    predict_from_load_func() saves GeoTIFF outputs into a temporary directory
    and returns the resulting file path list.  load_multiband() accepts a
    multiband GeoTIFF and optional 1-indexed band_order for Red, Green, NIR.
    """
    import omnicloudmask

    band_order = parse_band_order(options["geotiff_band_order"])
    output_dir = Path(tempfile.mkdtemp(prefix="i_omnicloudmask_"))
    TEMP_PATHS.append(output_dir)

    common_kwargs = omnicloud_common_kwargs(options, flags)
    common_kwargs["export_confidence"] = export_confidence
    common_kwargs["output_dir"] = output_dir
    common_kwargs["overwrite"] = True

    try:
        outputs = omnicloudmask.predict_from_load_func(
            scene_paths=[geotiff],
            load_func=select_loader_for_geotiff(band_order),
            **common_kwargs,
        )
    except RuntimeError as error:
        _handle_inference_error(error, options)
    return [Path(path) for path in outputs]


def process_raster_inputs(options: dict[str, str], flags: dict[str, bool]) -> None:
    """Main workflow for GRASS raster inputs.

    Without -c the module writes a single categorical prediction raster to
    output=. With -c it writes four confidence rasters using output= as the
    basename. Softmax is either already applied by OmniCloudMask or computed
    in GRASS when -l is set.
    """
    output_name = options["output"]
    source_description = (
        f"GRASS rasters red={options['red']}, "
        f"green={options['green']}, nir={options['nir']}"
    )
    inference_description = build_inference_description(
        options, flags, export_confidence=flags["c"]
    )

    if flags["c"]:
        confidence = run_array_confidence_prediction(
            red=options["red"],
            green=options["green"],
            nir=options["nir"],
            options=options,
            flags=flags,
        )
        write_confidence_rasters(confidence, output_name)
        if flags["l"]:
            apply_softmax_in_grass(output_name, nprocs=int(options["nprocs"]))
        decorate_confidence_rasters(
            output_name, source_description, inference_description
        )
        return

    prediction = run_array_prediction(
        red=options["red"],
        green=options["green"],
        nir=options["nir"],
        options=options,
        flags=flags,
    )
    write_class_raster(
        prediction, output_name, source_description, inference_description
    )


def process_geotiff_input(options: dict[str, str], flags: dict[str, bool]) -> None:
    """Main workflow for external GeoTIFF input.

    This path processes the whole raster file and then imports the generated
    GeoTIFF result(s) into the current GRASS mapset. Without -c a single class
    raster is imported to output=. With -c four confidence rasters are imported
    using output= as the basename.
    """
    memory_mb = int(options["memory"])
    limit_to_region = bool(flags["r"])
    source_description = f"GeoTIFF {options['geotiff']}"
    inference_description = build_inference_description(
        options, flags, export_confidence=flags["c"]
    )

    if flags["c"]:
        confidence_paths = run_geotiff_prediction(
            geotiff=options["geotiff"],
            options=options,
            flags=flags,
            export_confidence=True,
        )
        if len(confidence_paths) != 1:
            gs.fatal(f"Expected one confidence file, received {len(confidence_paths)}")
        import_confidence_geotiff(
            confidence_paths[0],
            options["output"],
            memory_mb,
            limit_to_region=limit_to_region,
        )
        if flags["l"]:
            apply_softmax_in_grass(options["output"], nprocs=int(options["nprocs"]))
        decorate_confidence_rasters(
            options["output"], source_description, inference_description
        )
        return

    prediction_paths = run_geotiff_prediction(
        geotiff=options["geotiff"],
        options=options,
        flags=flags,
        export_confidence=False,
    )
    if len(prediction_paths) != 1:
        gs.fatal(f"Expected one prediction file, received {len(prediction_paths)}")

    import_raster_from_geotiff(
        prediction_paths[0],
        options["output"],
        memory_mb,
        limit_to_region=limit_to_region,
    )
    apply_categories_and_colors(options["output"])
    write_support_metadata(
        options["output"],
        title="OmniCloudMask class prediction",
        source_description=source_description,
        inference_description=inference_description,
    )


def import_confidence_geotiff(
    geotiff_path: Path,
    basename: str,
    memory_mb: int,
    *,
    limit_to_region: bool,
) -> None:
    """Import a 4-band confidence GeoTIFF into four GRASS rasters."""
    import_flags = "r" if limit_to_region else ""

    for band_index, suffix in enumerate(CONFIDENCE_SUFFIXES, start=1):
        output_name = f"{basename}_{suffix}"
        gs.run_command(
            "r.in.gdal",
            input=str(geotiff_path),
            output=output_name,
            band=band_index,
            memory=memory_mb,
            flags=import_flags,
            overwrite=gs.overwrite(),
        )


def check_output_exists(output_name: str, *, export_confidence: bool) -> None:
    """Check whether output rasters already exist and --overwrite is not set."""
    if gs.overwrite():
        return

    names_to_check = []
    if export_confidence:
        for suffix in CONFIDENCE_SUFFIXES:
            names_to_check.append(f"{output_name}_{suffix}")
    else:
        names_to_check.append(output_name)

    existing = [
        name for name in names_to_check if gs.find_file(name, element="cell")["name"]
    ]
    if existing:
        gs.fatal(
            f"Raster map(s) already exist: {', '.join(existing)}. "
            "Use --overwrite to allow overwriting."
        )


def validate_options(options: dict[str, str], flags: dict[str, bool]) -> None:
    """Validate cross-option logic."""
    has_geotiff = bool(options["geotiff"])

    if not has_geotiff:
        if flags["r"]:
            gs.warning(
                "The -r flag affects only GeoTIFF imports and is ignored "
                "for GRASS raster inputs"
            )

    if flags["l"] and not flags["c"]:
        gs.warning(
            "The -l flag is only relevant with -c (confidence output) "
            "and will be ignored"
        )


def main(options, flags):
    options, flags = gs.parser()
    ensure_dependencies()
    validate_options(options, flags)
    check_output_exists(options["output"], export_confidence=flags["c"])

    if options["geotiff"]:
        process_geotiff_input(options, flags)
    else:
        process_raster_inputs(options, flags)

    gs.message("OmniCloudMask processing completed successfully.")
    return 0


if __name__ == "__main__":
    atexit.register(cleanup)
    sys.exit(main(*gs.parser()))
