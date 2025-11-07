#!/usr/bin/env python3
##############################################################################
# MODULE:    i.hyper.composite
# AUTHOR(S): Alen Mangafic and Tomaž Žagar, Geodetic Institute of Slovenia
# PURPOSE:   Create RGB/CIR/SWIR and custom false color composites
#            from a hyperspectral 3D raster.
# COPYRIGHT: (C) 2025 by Alen Mangafic and the GRASS Development Team
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
import grass.script as gs
from grass.pygrass.modules import Module

COMPOSITES = {
    "rgb": [660, 572, 478],
    "cir": [848, 660, 572],
    "swir_agriculture": [848, 1653, 660],
    "swir_geology": [2200, 848, 572],
}

def _band_count(mapname):
    info = gs.parse_command("r3.info", flags="g", map=mapname)
    d = int(info["depths"])
    if d <= 0:
        gs.fatal("Invalid band count (depths) reported by r3.info")
    return d

def _band_wavelengths_from_comments(mapname, expected):
    txt = gs.read_command("r3.info", map=mapname)
    wavelengths = [None] * expected
    num = r"[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?"
    pat = re.compile(
        rf"Band\s+(\d+)\s*:\s*({num})\s*nm(?:,\s*FWHM:\s*({num})\s*nm)?",
        re.IGNORECASE
    )
    for line in txt.splitlines():
        line = line.strip()
        if line.startswith("|"):
            line = line.strip("| ").rstrip("| ").strip()
        m = pat.search(line)
        if m:
            idx = int(m.group(1))
            if 1 <= idx <= expected:
                wavelengths[idx - 1] = float(m.group(2))
    if any(w is None for w in wavelengths):
        missing = [i+1 for i,w in enumerate(wavelengths) if w is None]
        gs.fatal(f"Missing wavelengths in r3.info comments for bands: {missing[:10]}{'...' if len(missing)>10 else ''}")
    return wavelengths

def _explode_cube(cube, tmpbase):
    """Explode cube into 2D rasters using a temporary 3D region."""
    Module("g.region", save="__tmp_orig_region__", quiet=True)
    try:
        Module("g.region", raster_3d=cube, quiet=True)
        Module("r3.to.rast", input=cube, output=tmpbase, overwrite=True, quiet=True)
        maps = gs.read_command("g.list", type="raster", pattern=f"{tmpbase}*").strip().split()
        if not maps:
            gs.fatal("No 2D rasters were produced by r3.to.rast")
        maps.sort(key=lambda m: int(re.search(r'(\d+)$', m).group(1)))
        return maps
    finally:
        Module("g.region", region="__tmp_orig_region__", quiet=True)
        Module("g.remove", type="region", name="__tmp_orig_region__", flags="f", quiet=True)

def _nearest_index(target_nm, wavelengths):
    diffs = [abs(w - target_nm) for w in wavelengths]
    return diffs.index(min(diffs))  # 0-based

def _enhance_and_composite(r, g, b, outname, strength, rgb_preserve):
    if rgb_preserve:
        Module("i.colors.enhance", red=r, green=g, blue=b,
               strength=str(strength), flags="p", quiet=True)
    else:
        Module("i.colors.enhance", red=r, green=g, blue=b,
               strength=str(strength), quiet=True)
    Module("r.composite", red=r, green=g, blue=b,
           output=outname, overwrite=True, quiet=True)

def main():
    options, flags = gs.parser()
    cube    = options["map"]
    outpref = options["output"]
    comps   = options.get("composites")
    custom  = options.get("composites_custom")

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
                gs.fatal(f"Unknown composite '{c}'. Allowed: {', '.join(COMPOSITES.keys())}")

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
    wavelengths = _band_wavelengths_from_comments(cube, band_count)

    tmpbase = f"_ihc_{uuid.uuid4().hex[:8]}_b_"
    maps = _explode_cube(cube, tmpbase)

    if len(maps) != band_count:
        gs.warning(f"Expected {band_count} bands, got {len(maps)}. Using available maps only.")
        maps = maps[:min(len(maps), band_count)]

    try:
        def map_for_nm(nm):
            idx = _nearest_index(nm, wavelengths)
            return maps[idx]

        for comp in requested:
            wl = COMPOSITES[comp]
            r, g, b = map_for_nm(wl[0]), map_for_nm(wl[1]), map_for_nm(wl[2])
            outname = f"{outpref}_{comp.lower().replace('-', '_')}"
            _enhance_and_composite(r, g, b, outname, strength, rgb_preserve=(comp == "rgb"))
            gs.info(f"Generated composite raster: {outname}")

        if custom_wl:
            r, g, b = map_for_nm(custom_wl[0]), map_for_nm(custom_wl[1]), map_for_nm(custom_wl[2])
            outname = f"{outpref}_custom"
            _enhance_and_composite(r, g, b, outname, strength, rgb_preserve=False)
            gs.info(f"Generated custom composite raster: {outname}")

    finally:
        Module("g.remove", type="raster", pattern="_ihc*", flags="f", quiet=True)

if __name__ == "__main__":
    sys.exit(main())
