#!/usr/bin/env python3
"""
PRISMA L2D importer:
- Loads VNIR+SWIR PRISMA L2D data and builds a full 3D raster (r3) of reflectance (float32).
- Creates selected 3-band composites (RGB, CIR, SWIR_* or custom wavelengths) by nearest-band lookup.
- Sets region to match the transposed (E, N) raster layout and writes NULLs outside the valid footprint.
- Enhances colors via i.colors.enhance and assembles final composites with r.composite; temp bands are cleaned up.
Entry points:
  - import_prisma(input_path, output_name, composites=None, custom_wavelengths=None, strength_val=96, import_null=False)
  - run_import(options, flags)  # wrapper for module CLI
Requires: prisma_reader.{load_prisma_l2d, concatenate_hyperspectral}
"""

import os
import uuid
import numpy as np
import grass.script as gs
import grass.script.array as garray
from grass.pygrass.modules import Module

from prisma_reader import load_prisma_l2d, concatenate_hyperspectral

COMPOSITES = {
    "rgb": [660.0, 572.0, 478.0],
    "cir": [848.0, 660.0, 572.0],
    "swir_agriculture": [848.0, 1653.0, 660.0],
    "swir_geology": [2200.0, 848.0, 572.0],
}


# -------------------------- helpers --------------------------
def _require(cond, msg):
    if not cond:
        gs.fatal(msg)


def _resolve_he5(path_like):
    if os.path.isdir(path_like):
        for n in os.listdir(path_like):
            if n.lower().endswith(".he5"):
                return os.path.join(path_like, n)
        gs.fatal("No .he5 file found in the provided folder.")
    return path_like


def _find_nearest_band_1based(target_nm, wavelengths_nm):
    wl = np.asarray(wavelengths_nm, dtype=np.float32)
    return int(np.argmin(np.abs(wl - float(target_nm)))) + 1  # 1-based


def _temp_name(prefix):
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


# -------------------------- region --------------------------
def _compute_edges_from_centers(ul_e, ul_n, ur_e, ur_n, ll_e, ll_n, rows, cols):
    """
    Edges from pixel-center corners.
    Called with rows=E (UL→LL samples) and cols=N (UL→UR samples) AFTER transposing.
    """
    if any(v is None for v in (ul_e, ul_n, ur_e, ur_n, ll_e, ll_n)):
        gs.fatal("PRISMA corners missing (need UL, UR, LL).")
    if rows < 2 or cols < 2:
        gs.fatal("Invalid raster shape (<2).")

    ew_c2c = (ur_e - ul_e) / float(cols - 1)  # columns axis = easting
    ns_c2c = (ul_n - ll_n) / float(rows - 1)  # rows axis = northing

    west = ul_e - 0.5 * ew_c2c
    east = ur_e + 0.5 * ew_c2c
    north = ul_n + 0.5 * ns_c2c
    south = ll_n - 0.5 * ns_c2c
    return west, east, south, north


def _force_region_exact_for_transposed(geo, rows_E, cols_N):
    west, east, south, north = _compute_edges_from_centers(
        geo.ul_e,
        geo.ul_n,
        geo.ur_e,
        geo.ur_n,
        geo.ll_e,
        geo.ll_n,
        rows=rows_E,
        cols=cols_N,
    )
    gs.run_command("g.region", w=west, e=east, s=south, n=north, quiet=True)
    gs.run_command("g.region", rows=rows_E, cols=cols_N, quiet=True)
    reg = gs.region()
    if int(reg["rows"]) != rows_E or int(reg["cols"]) != cols_N:
        gs.fatal(
            f"Region is {reg['rows']}x{reg['cols']} but transposed data is {rows_E}x{cols_N}"
        )


# -------------------------- writers --------------------------
def _write_float_raster(name, data_2d_float32):
    arr = garray.array(dtype=np.float32)
    arr[:, :] = data_2d_float32
    arr.write(name, null="nan", overwrite=True)


# -------------------------- public core --------------------------
def import_prisma(
    input_path,
    output_name,
    composites=None,
    custom_wavelengths=None,
    strength_val=96,
    import_null=False,
):
    """
    Writes composite rasters (only) following the EnMAP composite flow:
      - pick nearest bands by wavelength,
      - enhance RGB with -p flag, others without,
      - build composite from three band maps,
      - only final composites remain (temp bands removed).
    Reflectance is float32; per-band temp rasters are created on demand and reused across composites.
    """
    he5 = _resolve_he5(input_path)
    prod = load_prisma_l2d(he5, load_pan=False)

    _require(prod.hco_geo is not None, "HCO geolocation missing.")
    _require(prod.vnir and prod.vnir.dn is not None, "VNIR cube missing.")
    _require(prod.swir and prod.swir.dn is not None, "SWIR cube missing.")

    # Reflectance cube (N,E,B) and wavelengths
    refl, wavelengths, fwhm = concatenate_hyperspectral(prod)  # float32 0..1
    _require(refl.ndim == 3, f"Unexpected reflectance shape: {refl.shape}")

    # --- a mask where every band is zero
    bg_mask = None  # (N,E)

    # VNIR contribution (consider only kept bands)
    if prod.vnir and prod.vnir.dn is not None and prod.vnir.bands is not None:
        v_idx = prod.vnir.bands.kept_indices
        v_bg = np.all(prod.vnir.dn[:, :, v_idx] == 0, axis=2)  # (N,E)
        bg_mask = v_bg if bg_mask is None else (bg_mask & v_bg)

    # SWIR contribution (consider only kept bands)
    if prod.swir and prod.swir.dn is not None and prod.swir.bands is not None:
        s_idx = prod.swir.bands.kept_indices
        s_bg = np.all(prod.swir.dn[:, :, s_idx] == 0, axis=2)  # (N,E)
        bg_mask = s_bg if bg_mask is None else (bg_mask & s_bg)

    # Apply: set only outside-footprint pixels to NaN across all bands (real 0.0 reflectance stays)
    if bg_mask is not None:
        refl[bg_mask, :] = np.nan  # GRASS will store these as NULLs on write

    # Determine transposed shape (E,N) from any band
    first_band = refl[:, :, 0].T  # (E,N)
    rows_E, cols_N = first_band.shape

    # Fix region exactly to transposed shape and metadata extents
    gs.use_temp_region()
    _force_region_exact_for_transposed(prod.hco_geo, rows_E, cols_N)

    # Build list of composites to make (default RGB)
    wanted = []
    if composites:
        comp_lookup = {k.upper(): (k, v) for k, v in COMPOSITES.items()}
        for comp in composites:
            compu = comp.strip().upper()
            if compu in comp_lookup:
                orig_name, vals = comp_lookup[compu]
                wanted.append((orig_name, vals))
            else:
                gs.warning(f"Unknown composite '{comp}' ignored.")
    else:
        wanted.append(("rgb", COMPOSITES["rgb"]))

    if custom_wavelengths:
        if len(custom_wavelengths) != 3:
            gs.fatal(
                "Custom composites must provide exactly 3 wavelengths (e.g., 850,1650,660)"
            )
        wanted.append(("CUSTOM", [float(x) for x in custom_wavelengths]))

    # create temp rasters only for bands we need, and reuse them via a dict keyed by 1-based band index.
    temp_bands = {}  # {band_idx_1based: raster_name}
    created_names = []  # for final cleanup

    def ensure_band_written(idx1):
        """Write reflectance band idx1 (1-based) as a temp raster (E,N) if not already created."""
        if idx1 in temp_bands:
            return temp_bands[idx1]
        # Extract band; refl is (N,E,B) with 0-based k
        k = idx1 - 1
        band_EN = refl[:, :, k].T.astype(np.float32)
        name = _temp_name(f"{output_name}_b{idx1:03d}")
        _write_float_raster(name, band_EN)
        temp_bands[idx1] = name
        created_names.append(name)
        return name

    # Prime the "rgb_enhanced" mapping:
    rgb_target = COMPOSITES["rgb"]
    rgb_indices_1b = [_find_nearest_band_1based(w, wavelengths) for w in rgb_target]
    # Create these bands now and cache
    for idx1 in rgb_indices_1b:
        ensure_band_written(idx1)
    rgb_enhanced = {idx1: temp_bands[idx1] for idx1 in rgb_indices_1b}

    # -------------------------- build full hyperspectral 3D cube (all bands) --------------------------
    try:
        bands_total = int(refl.shape[2])

        # 1) Peg 2D region to an existing temp band (guarantees XY extents & 2D res match slices)
        ref_map_for_region = next(iter(rgb_enhanced.values()))
        Module("g.region", raster=ref_map_for_region, quiet=True)

        # 2) Read the (now pegged) 2D region to mirror its XY resolutions into the 3D region
        reg2d = gs.region()
        nsres2d = float(reg2d["nsres"])
        ewres2d = float(reg2d["ewres"])

        # -------- spectral (Z) axis in nanometers --------
        if wavelengths is not None and len(wavelengths) > 0:
            wl = np.asarray(wavelengths, dtype=float)
            if wl.size > 1:
                # Use exact spacing from endpoints (sum of diffs) to avoid accumulating FP error
                tbres_nm = float((wl[-1] - wl[0]) / (bands_total - 1))
            else:
                tbres_nm = 1.0
            bottom_nm = float(wl[0])
            # set t = b + tbres * bands_total to get depth == bands_total
            top_nm = bottom_nm + tbres_nm * bands_total
        else:
            bottom_nm, top_nm, tbres_nm = 0.0, float(bands_total), 1.0

        gs.run_command(
            "g.region",
            nsres3=nsres2d,
            ewres3=ewres2d,
            b=0,
            t=bands_total,
            tbres=1,
            quiet=True,
        )

        # Create and fill the 3D array: (band, row(E), col(N))
        cube = garray.array3d(dtype=np.float32)
        for k in range(bands_total):
            cube[k, :, :] = refl[:, :, k].T.astype(np.float32)

        # write 3D raster under the final output name
        cube.write(
            mapname=f"{output_name}", null="nan", overwrite=True
        )  # NaNs -> NULLs
        gs.info(
            f"Created 3D raster with all bands: {output_name} ({bands_total} slices)."
        )

        # -------- r3 metadata --------
        try:
            count_meta = int(min(bands_total, len(wavelengths)))
            desc_lines = ["Hyperspectral Metadata:", f"Valid Bands: {count_meta}"]
            for i in range(count_meta):
                wl_i = float(wavelengths[i])
                fwhm_i = float(fwhm[i]) if i < len(fwhm) else float("nan")
                desc_lines.append(f"Band {i + 1}: {wl_i} nm, FWHM: {fwhm_i} nm")
            Module(
                "r3.support",
                map=output_name,
                title="PRISMA Hyperspectral Data",
                description="\n".join(desc_lines),
                vunit="nanometers",
                quiet=True,
            )
        except Exception as e_meta:
            gs.warning(f"Failed to write r3 metadata: {e_meta}")
        # -----------------------------------------------------------------
    except Exception as e:
        gs.warning(f"3D cube creation failed: {e}")
    # -------------------------------------------------------------------------------------------------------

    # For each requested composite, select bands and build r.composite
    for name, targets in wanted:
        bands_1b = [_find_nearest_band_1based(w, wavelengths) for w in targets]
        rgb_maps = []
        for idx1 in bands_1b:
            if idx1 in rgb_enhanced:
                rgb_maps.append(rgb_enhanced[idx1])
            else:
                rgb_maps.append(ensure_band_written(idx1))

        Module("g.region", raster=rgb_maps[0], quiet=True)
        if name.upper() == "rgb":
            Module(
                "i.colors.enhance",
                red=rgb_maps[0],
                green=rgb_maps[1],
                blue=rgb_maps[2],
                strength=str(strength_val),
                flags="p",
                quiet=True,
            )
            outname = f"{output_name}_{name.lower().replace('-', '_')}"
        else:
            Module(
                "i.colors.enhance",
                red=rgb_maps[0],
                green=rgb_maps[1],
                blue=rgb_maps[2],
                strength=str(strength_val),
                quiet=True,
            )
            outname = f"{output_name}_{name.lower().replace('-', '_')}"

        Module(
            "r.composite",
            red=rgb_maps[0],
            green=rgb_maps[1],
            blue=rgb_maps[2],
            output=outname,
            quiet=True,
            overwrite=True,
        )
        gs.info(f"Generated composite raster: {outname}")

    # Clean up temp bands after all composites are made
    if created_names:
        Module(
            "g.remove",
            type="raster",
            name=",".join(created_names),
            flags="f",
            quiet=True,
        )

    gs.del_temp_region()


def run_import(options, flags):
    custom = None
    if options.get("composites_custom"):
        try:
            custom = [float(x.strip()) for x in options["composites_custom"].split(",")]
            if len(custom) != 3:
                raise ValueError
        except Exception:
            gs.fatal(
                "Invalid format for composites_custom. Usage example: 850,1650,660"
            )

    strength_opt = options.get("strength")
    if strength_opt is None or str(strength_opt).strip() == "":
        strength_val = 96
    else:
        try:
            strength_val = int(str(strength_opt).strip())
        except Exception:
            gs.fatal("Invalid strength. Provide an integer 0-100.")
        if not (0 <= strength_val <= 100):
            gs.fatal("Invalid strength. Provide an integer 0-100.")

    comps = (
        [c.strip() for c in options["composites"].split(",")]
        if options.get("composites")
        else None
    )
    import_null = bool(flags.get("n"))

    import_prisma(
        input_path=options["input"],
        output_name=options["output"],
        composites=comps,
        custom_wavelengths=custom,
        strength_val=strength_val,
        import_null=import_null,
    )
