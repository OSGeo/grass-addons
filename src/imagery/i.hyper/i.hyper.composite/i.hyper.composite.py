#!/usr/bin/env python3
##############################################################################
# MODULE:    i.hyper.composite
# AUTHOR(S): Alen Mangafic and Tomaž Žagar, Geodetic Institute of Slovenia
# PURPOSE:   Create RGB/CIR/SWIR and custom false color composites
#            from a hyperspectral 3D raster.
# SPDX-FileCopyrightText: 2025 Alen Mangafic
# SPDX-FileCopyrightText: Other GRASS authors
# SPDX-License-Identifier: GPL-2.0-or-later
##############################################################################

# %module
# % description: Create RGB/CIR/SWIR and custom false color composites from a hyperspectral 3D raster map.
# % keyword: imagery
# % keyword: hyperspectral
# % keyword: composite
# %end

# %option G_OPT_R3_INPUT
# % key: map
# % description: Input hyperspectral 3D raster map
# % required: yes
# % guisection: Input
# %end

# %option
# % key: output
# % type: string
# % description: Output name prefix for composites
# % required: yes
# % guisection: Output
# %end

# %option
# % key: composites
# % type: string
# % multiple: yes
# % options: rgb,cir,swir_agriculture,swir_geology
# % description: Which composites to generate
# % guisection: Composites
# %end

# %option
# % key: composites_custom
# % type: string
# % description: Custom wavelengths (nm) as R,G,B (e.g., 2200,848,572)
# % guisection: Composites
# %end

# %option
# % key: strength
# % type: integer
# % answer: 96
# % description: i.colors.enhance 'strength' (0-100). RGB uses -p; others no -p.
# % guisection: Optional
# %end

import sys
import re
import uuid
import importlib.util
import grass.script as gs
from grass.pygrass.modules import Module
from grass.script.utils import get_lib_path

COMPOSITES = {
    "rgb": [660, 572, 478],
    "cir": [848, 660, 572],
    "swir_agriculture": [848, 1653, 660],
    "swir_geology": [2200, 848, 572],
}


def _get_hyper_meta_class():
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
    return module.HyperMetadata


def _band_count(mapname):
    info = gs.parse_command("r3.info", flags="g", map=mapname)
    d = int(info["depths"])
    if d <= 0:
        gs.fatal("Invalid band count (depths) reported by r3.info")
    return d


def _band_wavelengths(mapname, expected, hyper_meta_class):
    if hyper_meta_class is None:
        gs.fatal(
            "Failed to load hyper_meta library. JSON metadata support is required."
        )

    try:
        meta = hyper_meta_class.load(mapname)
    except Exception as error:
        gs.fatal(f"Failed to read JSON metadata for {mapname}: {error}")

    wl_arr = meta.get_wavelengths_array()
    if wl_arr is None:
        gs.fatal(f"Missing 'bands.wavelength' in JSON metadata for {mapname}.")

    wavelengths = [None if (w is None or w != w) else float(w) for w in wl_arr.tolist()]
    if len(wavelengths) < expected:
        gs.fatal(
            f"Metadata wavelength count ({len(wavelengths)}) is lower than band count ({expected}) for {mapname}."
        )

    wavelengths = wavelengths[:expected]
    if any(w is None for w in wavelengths):
        missing = [i + 1 for i, w in enumerate(wavelengths) if w is None]
        gs.fatal(
            f"Missing JSON wavelengths for bands: {missing[:10]}{'...' if len(missing) > 10 else ''}"
        )

    return [float(w) for w in wavelengths]


def _explode_cube(cube, tmpbase):
    """Explode cube into 2D rasters using a temporary 3D region."""
    Module("g.region", raster_3d=cube, quiet=True)
    Module("r3.to.rast", input=cube, output=tmpbase, overwrite=True, quiet=True)
    maps = (
        gs.read_command("g.list", type="raster", pattern=f"{tmpbase}*").strip().split()
    )
    if not maps:
        gs.fatal("No 2D rasters were produced by r3.to.rast")
    maps.sort(key=lambda m: int(re.search(r"(\d+)$", m).group(1)))
    return maps


def _nearest_index(target_nm, wavelengths):
    diffs = [abs(w - target_nm) for w in wavelengths]
    return diffs.index(min(diffs))  # 0-based


def _enhance_and_composite(r, g, b, outname, strength, rgb_preserve):
    Module("g.region", raster=r, quiet=True)
    if rgb_preserve:
        Module(
            "i.colors.enhance",
            red=r,
            green=g,
            blue=b,
            strength=str(strength),
            flags="p",
            quiet=True,
        )
    else:
        Module(
            "i.colors.enhance",
            red=r,
            green=g,
            blue=b,
            strength=str(strength),
            quiet=True,
        )
    Module(
        "r.composite",
        red=r,
        green=g,
        blue=b,
        output=outname,
        overwrite=True,
        quiet=True,
    )


def main():
    options, flags = gs.parser()
    cube = options["map"]
    outpref = options["output"]
    comps = options.get("composites")
    custom = options.get("composites_custom")

    try:
        strength = int(options.get("strength") or 96)
    except Exception:
        gs.fatal("Invalid strength. Provide an integer 0–100.")
    if not (0 <= strength <= 100):
        gs.fatal("Invalid strength. Provide an integer 0–100.")

    requested = []
    if comps:
        requested = [c.strip() for c in comps.split(",") if c.strip()]
        for c in requested:
            if c not in COMPOSITES:
                gs.fatal(
                    f"Unknown composite '{c}'. Allowed: {', '.join(COMPOSITES.keys())}"
                )

    custom_wl = None
    if custom:
        try:
            custom_wl = [float(x.strip()) for x in custom.split(",")]
            if len(custom_wl) != 3:
                raise ValueError
        except Exception:
            gs.fatal("Invalid composites_custom. Use format like 850,1650,660")

    band_count = _band_count(cube)
    if band_count < 3:
        gs.fatal(f"{cube} contains only {band_count} band(s). Cannot build composites.")
    hyper_meta_class = _get_hyper_meta_class()
    wavelengths = _band_wavelengths(cube, band_count, hyper_meta_class)

    tmpbase = f"_ihc_{uuid.uuid4().hex[:8]}_b_"
    gs.use_temp_region()
    try:
        maps = _explode_cube(cube, tmpbase)

        if len(maps) != band_count:
            gs.warning(
                f"Expected {band_count} bands, got {len(maps)}. Using available maps only."
            )
            maps = maps[: min(len(maps), band_count)]

        def map_for_nm(nm):
            idx = _nearest_index(nm, wavelengths)
            return maps[idx]

        for comp in requested:
            wl = COMPOSITES[comp]
            r, g, b = map_for_nm(wl[0]), map_for_nm(wl[1]), map_for_nm(wl[2])
            outname = f"{outpref}_{comp.lower().replace('-', '_')}"
            _enhance_and_composite(
                r, g, b, outname, strength, rgb_preserve=(comp.upper() == "RGB")
            )
            gs.info(f"Generated composite raster: {outname}")

        if custom_wl:
            r, g, b = (
                map_for_nm(custom_wl[0]),
                map_for_nm(custom_wl[1]),
                map_for_nm(custom_wl[2]),
            )
            outname = f"{outpref}_custom"
            _enhance_and_composite(r, g, b, outname, strength, rgb_preserve=False)
            gs.info(f"Generated custom composite raster: {outname}")

    finally:
        Module("g.remove", type="raster", pattern="_ihc*", flags="f", quiet=True)
        gs.del_temp_region()


if __name__ == "__main__":
    sys.exit(main())
