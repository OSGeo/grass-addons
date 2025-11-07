#!/usr/bin/env python3
"""
Tanager BASIC → GRASS

- Imports Tanager BASIC (radiance or surface_reflectance)
- Projects and resamples to the target map grid defined by Planet_Ortho_Framing
  using bilinear forward splatting with small-neighborhood nearest fill for purely
  geometric gaps (optional; SciPy if available)
- Writes a full 3D raster (bands in Z) and per-band composites
- Preserves nodata (nodata_pixels==1) as NULLs in GRASS
"""

import os
import uuid
import numpy as np
import grass.script as gs
import grass.script.array as garray
from grass.pygrass.modules import Module

from tanager_reader import (
    load_tanager_basic,
    read_planet_map_grid,
    build_splat_plan,
    project_band_to_map_grid,
)

COMPOSITES = {
    "rgb":              [660.0, 572.0, 478.0],
    "cir":              [848.0, 660.0, 572.0],
    "swir_agriculture": [848.0, 1653.0, 660.0],
    "swir_geology":     [2200.0, 848.0, 572.0],
}

# -------------------------- helpers --------------------------

def _require(cond, msg):
    if not cond:
        gs.fatal(msg)

def _resolve_h5(path_like):
    if os.path.isdir(path_like):
        for n in os.listdir(path_like):
            if n.lower().endswith(".h5"):
                return os.path.join(path_like, n)
        gs.fatal("No .h5 file found in the provided folder.")
    return path_like

def _find_nearest_band_1based(target_nm, wavelengths_nm):
    wl = np.asarray(wavelengths_nm, dtype=np.float32)
    return int(np.argmin(np.abs(wl - float(target_nm)))) + 1  # 1-based

def _temp_name(prefix):
    return f"{prefix}_{uuid.uuid4().hex[:8]}"

def _write_float_raster(name, data_2d_float32):
    arr = garray.array(dtype=np.float32)
    arr[:, :] = data_2d_float32
    arr.write(name, null="nan", overwrite=True)  # NaNs -> NULLs

# -------------------------- core --------------------------

def import_tanager(
    input_path: str,
    output_name: str,
    composites=None,
    custom_wavelengths=None,
    strength_val=96,
    import_null=False,
    fill_8_neighbor=True
):
    """
    Import, project, and resample Tanager BASIC to the target map grid. Writes:
      - 3D raster (bands as slices)
      - per-band temporary rasters for composites
      - color-enhanced composites

    Parameters:
      fill_8_neighbor: if True and SciPy is available, fills only geometric gaps
                       via nearest neighbor limited to the 8-neighborhood.
    """
    h5 = _resolve_h5(input_path)
    prod = load_tanager_basic(h5)

    data = prod.data              # (rows, cols, bands), float32 with NaNs where nodata_pixels==1
    wl   = prod.wavelengths_nm
    fwhm = prod.fwhm_nm

    _require(data is not None and data.ndim == 3, "Data cube missing or invalid.")
    _require(prod.lat is not None and prod.lon is not None, "Latitude/Longitude grids missing.")

    # composites list
    wanted = []
    if composites:
        lut = {k.upper(): (k, v) for k, v in COMPOSITES.items()}
        for comp in composites:
            key = comp.strip().upper()
            if key in lut:
                name, vals = lut[key]
                wanted.append((name, vals))
            else:
                gs.warning(f"Ignored unknown composite '{comp}'.")
    else:
        wanted.append(("rgb", COMPOSITES["rgb"]))

    if custom_wavelengths:
        if len(custom_wavelengths) != 3:
            gs.fatal("Custom composites must provide exactly 3 wavelengths, e.g. 850,1650,660")
        wanted.append(("CUSTOM", [float(x) for x in custom_wavelengths]))

    gs.use_temp_region()

    # Read Planet target map grid and set region
    grid = read_planet_map_grid(h5)
    Module("g.region",
           w=grid.west, e=grid.east, s=grid.south, n=grid.north,
           ewres=grid.ewres, nsres=grid.nsres, flags="a", quiet=True)

    # Precompute the per-scene splat plan.
    # Use a band-independent nodata mask (after loader has applied nodata across all bands).
    base_mask = np.isnan(data[..., 0])
    plan = build_splat_plan(prod.lon, prod.lat, grid, nodata_mask=base_mask)

    # Band writer using projection + gridding and caching
    temp_bands = {}
    created_names = []

    def ensure_band_written(idx1):
        if idx1 in temp_bands:
            return temp_bands[idx1]
        k = idx1 - 1
        ortho2d = project_band_to_map_grid(
            band2d=data[:, :, k],
            plan=plan,
            fill_8_neighbor=fill_8_neighbor
        )
        name = _temp_name(f"{output_name}_b{idx1:03d}")
        _write_float_raster(name, ortho2d)
        temp_bands[idx1] = name
        created_names.append(name)
        return name

    # -------------------------- 3D cube write --------------------------
    bands_total = int(data.shape[2])
    try:
        # Mirror 2D res into 3D; Z is band index
        reg2d = gs.region()
        nsres2d = float(reg2d["nsres"])
        ewres2d = float(reg2d["ewres"])
        Module("g.region", nsres3=nsres2d, ewres3=ewres2d, b=0, t=bands_total, tbres=1, quiet=True)

        cube = garray.array3d(dtype=np.float32)
        for k in range(bands_total):
            ortho2d = project_band_to_map_grid(
                band2d=data[:, :, k],
                plan=plan,
                fill_8_neighbor=fill_8_neighbor
            )
            cube[k, :, :] = ortho2d

        cube.write(mapname=f"{output_name}", null="nan", overwrite=True)
        gs.info(f"Created 3D raster with all bands: {output_name} ({bands_total} slices).")

        # r3 metadata (wavelengths & FWHM + Units + Data Field)
        try:
            desc = ["Hyperspectral Metadata:", f"Valid Bands: {bands_total}"]

            if getattr(prod, "data_field", None):
                desc.append(f"Measurement: {prod.data_field}")

            if getattr(prod, "data_units", None):
                desc.append(f"Measurement Units: {prod.data_units}")

            for i in range(bands_total):
                wl_i = float(wl[i])
                fwhm_i = float(fwhm[i]) if i < len(fwhm) else float("nan")
                desc.append(f"Band {i+1}: {wl_i} nm, FWHM: {fwhm_i} nm")
            Module("r3.support",
                   map=output_name,
                   title="Tanager Hyperspectral Data (Projected to Map Grid)",
                   description="\n".join(desc),
                   vunit="nanometers",
                   quiet=True)
        except Exception as e_meta:
            gs.warning(f"Failed to write r3 metadata: {e_meta}")
    except Exception as e:
        gs.warning(f"3D cube creation failed: {e}")

    # -------------------------- composites --------------------------
    rgb_target = COMPOSITES["rgb"]
    rgb_indices_1b = [_find_nearest_band_1based(w, wl) for w in rgb_target]
    for idx1 in rgb_indices_1b:
        ensure_band_written(idx1)
    ref_map = next(iter({i: temp_bands[i] for i in rgb_indices_1b}.values()))
    Module("g.region", raster=ref_map, quiet=True)

    for name, targets in wanted:
        bands_1b = [_find_nearest_band_1based(w, wl) for w in targets]
        maps = []
        for idx1 in bands_1b:
            maps.append(temp_bands[idx1] if idx1 in temp_bands else ensure_band_written(idx1))

        Module("g.region", raster=maps[0], quiet=True)
        if name.upper() == "rgb":
            Module("i.colors.enhance", red=maps[0], green=maps[1], blue=maps[2],
                   strength=str(strength_val), flags="p", quiet=True)
        else:
            Module("i.colors.enhance", red=maps[0], green=maps[1], blue=maps[2],
                   strength=str(strength_val), quiet=True)

        outname = f"{output_name}_{name.lower().replace('-', '_')}"
        Module("r.composite", red=maps[0], green=maps[1], blue=maps[2],
               output=outname, quiet=True, overwrite=True)
        gs.info(f"Generated composite raster: {outname}")

    # cleanup
    if created_names:
        Module("g.remove", type="raster", name=",".join(created_names), flags="f", quiet=True)

    gs.del_temp_region()

# -------------------------- entry --------------------------

def run_import(options, flags):
    custom = None
    if options.get("composites_custom"):
        try:
            custom = [float(x.strip()) for x in options["composites_custom"].split(",")]
            if len(custom) != 3:
                raise ValueError
        except Exception:
            gs.fatal("Invalid format for composites_custom. Example: 850,1650,660")

    strength_opt = options.get("strength")
    if strength_opt is None or str(strength_opt).strip() == "":
        strength_val = 96
    else:
        try:
            strength_val = int(str(strength_opt).strip())
        except Exception:
            gs.fatal("Invalid strength. Provide an integer 0–100.")
        if not (0 <= strength_val <= 100):
            gs.fatal("Invalid strength. Provide an integer 0–100.")

    comps = [c.strip() for c in options["composites"].split(",")] if options.get("composites") else None
    import_null = bool(flags.get("n"))

    import_tanager(
        input_path=options["input"],
        output_name=options["output"],
        composites=comps,
        custom_wavelengths=custom,
        strength_val=strength_val,
        import_null=import_null,
        fill_8_neighbor=True,
    )
