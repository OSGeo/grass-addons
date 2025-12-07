#!/usr/bin/env python

############################################################################
#
# MODULE:       r.in.ahn
# AUTHOR:       Paulo van Breugel
# PURPOSE:      Imports the dtm or dsm from the AHN (Actueel Hoogtebestand
#               Nederland (AHN), versions 2–6) by downloading 1x1 km tiles,
#               clipped to the region. Region is extended to ensure that it
#               aligns with the original AHN
#
# COPYRIGHT:    (c) 2024-2025 Paulo van Breugel, and the GRASS Development
#               Team. This program is free software under the GNU General
#               Public License (>=v2). Read the file COPYING that comes with
#               GRASS for details.
#
#############################################################################

# %module
# % description: Imports the dtm or dsm from the AHN (Actueel Hoogtebestand Nederland (AHN), versions 2–6.
# % keyword: dem
# % keyword: raster
# % keyword: import
# %end

# %option
# % key: product
# % type: string
# % label: Product
# % description: Choose which product to download (dtm, dsm or chm)
# % options: dtm,dsm,chm
# % required: yes
# %end

# %option
# % key: version
# % type: string
# % label: AHN version
# % description: AHN version to download
# % options: 2,3,4,5,6
# % answer: 4
# % required: yes
# %end

# %option
# % key: resolution
# % type: double
# % label: Resolution
# % description: Resolution in meters (0.5 or 5)
# % options: 0.5,5
# % answer: 0.5
# % required: yes
# %end

# %option G_OPT_MEMORYMB
# %end

# %option G_OPT_M_NPROCS
# %end

# %option
# % key: max_inputs
# % type: integer
# % label: Maximum number of rasters passed to a single r.patch call
# % description: Larger values reduce number of intermediate batches but may exceed OS command length limits
# % required: no
# % answer: 250
# %end

# %option G_OPT_R_OUTPUT
# %end

# %flag
# % key: g
# % label: Set to original computational region
# % description: After downloading and importing, set the region back to the original computation region.
# %end

import atexit
import sys
from math import floor, ceil
from math import floor
from multiprocessing import Pool
import uuid

import grass.script as gs

# AHN overall 1x1 km grid extent (EPSG:28992)
AHN_MIN_X = 12000.0
AHN_MAX_X = 287000.0
AHN_MIN_Y = 304000.0
AHN_MAX_Y = 621000.0
TILE_SIZE = 1000.0

# create set to store names of temporary maps to be deleted upon exit
CLEAN_LAY = []


def cleanup():
    """Remove temporary maps specified in the global list and restore region"""
    maps = reversed(CLEAN_LAY)
    mapset = gs.gisenv()["MAPSET"]
    for map_name in maps:
        for element in ("raster", "vector"):
            found = gs.find_file(name=map_name, element=element, mapset=mapset)
            if found["file"]:
                gs.run_command(
                    "g.remove",
                    flags="f",
                    type=element,
                    name=map_name,
                    quiet=True,
                )
    gs.del_temp_region()


def create_unique_name(prefix):
    """
    Create a unique GRASS map name by appending a UUID hex string.
    """
    return f"{prefix}_{uuid.uuid4().hex}"


def create_temporary_name(prefix):
    """
    Create a unique temporary map name and register it for cleanup.
    """
    tmp_name = create_unique_name(prefix)
    CLEAN_LAY.append(tmp_name)
    return tmp_name


def get_tile_url(version, product, resolution, x, y):
    """
    Construct the download URL for a single 1x1 km tile.

    version: '2','3','4','5','6'
    product: 'dtm' or 'dsm'
    resolution: 0.5 or 5 (float)
    x, y: lower-left corner coordinates (integers, EPSG:28992)
    """

    base = "https://fsn1.your-objectstorage.com/hwh-ahn"

    # Version-dependent directory and filename prefix
    if version in ("2", "3", "4", "5"):
        vdir = f"AHN{version}_KM"
        prefix_base = f"AHN{version}"
    elif version == "6":
        # AHN6 uses AHN6/.. and AHN6_2025_* filenames
        vdir = "AHN6"
        prefix_base = "AHN6_2025"
    else:
        gs.fatal(_("Unsupported AHN version: {v}").format(v=version))

    # Product + resolution dependent subdir and suffix
    if product == "dtm":
        if resolution == 0.5:
            subdir = "02a_DTM_50cm"
            suffix = "M"
        elif resolution == 5.0:
            subdir = "02b_DTM_5m"
            suffix = "M5"
        else:
            gs.fatal(_("Unsupported resolution for DTM: {r}").format(r=resolution))
    elif product == "dsm":
        if resolution == 0.5:
            subdir = "03a_DSM_50cm"
            suffix = "R"
        elif resolution == 5.0:
            subdir = "03b_DSM_5m"
            suffix = "R5"
        else:
            gs.fatal(_("Unsupported resolution for DSM: {r}").format(r=resolution))
    else:
        gs.fatal(_("Unsupported product: {p}").format(p=product))

    filename = f"{prefix_base}_{suffix}_{int(x):06d}_{int(y):06d}.TIF"
    url = f"{base}/{vdir}/{subdir}/{filename}"
    return url


def overlap_with_ahn(region_current):
    """
    Compute the overlap of the current region with the AHN extent.
    Returns (n_ov, s_ov, w_ov, e_ov) and emits a warning if clamped.
    """

    n_cur = float(region_current["n"])
    s_cur = float(region_current["s"])
    w_cur = float(region_current["w"])
    e_cur = float(region_current["e"])

    n_ov = min(n_cur, AHN_MAX_Y)
    s_ov = max(s_cur, AHN_MIN_Y)
    w_ov = max(w_cur, AHN_MIN_X)
    e_ov = min(e_cur, AHN_MAX_X)

    # Check overlap
    if n_ov <= s_ov or e_ov <= w_ov:
        gs.fatal(
            _(
                "The current computational region lies completely outside "
                "the AHN extent "
                "([{xmin}, {ymin}] – [{xmax}, {ymax}] in EPSG:28992)."
            ).format(
                xmin=AHN_MIN_X,
                ymin=AHN_MIN_Y,
                xmax=AHN_MAX_X,
                ymax=AHN_MAX_Y,
            )
        )

    # Warn if clamped
    if (n_ov != n_cur) or (s_ov != s_cur) or (w_ov != w_cur) or (e_ov != e_cur):
        gs.warning(
            _(
                "The current computational region extends outside the AHN extent "
                "([{xmin}, {ymin}] – [{xmax}, {ymax}] in EPSG:28992). "
                "Only the overlapping part will be imported:\n"
                "  n={n}, s={s}, w={w}, e={e}"
            ).format(
                xmin=AHN_MIN_X,
                ymin=AHN_MIN_Y,
                xmax=AHN_MAX_X,
                ymax=AHN_MAX_Y,
                n=n_ov,
                s=s_ov,
                w=w_ov,
                e=e_ov,
            )
        )

    return n_ov, s_ov, w_ov, e_ov


def tiles_for_region(n, s, w, e):
    """
    Compute the list of 1x1 km tile lower-left coordinates (x,y)
    that intersect the given region [w,e] x [s,n].
    """

    # Determine tile index ranges in x and y
    # lower-left coordinates are multiples of TILE_SIZE
    x_start = max(AHN_MIN_X, floor(w / TILE_SIZE) * TILE_SIZE)
    x_end = min(AHN_MAX_X - TILE_SIZE, floor((e - 1e-9) / TILE_SIZE) * TILE_SIZE)

    y_start = max(AHN_MIN_Y, floor(s / TILE_SIZE) * TILE_SIZE)
    y_end = min(AHN_MAX_Y - TILE_SIZE, floor((n - 1e-9) / TILE_SIZE) * TILE_SIZE)

    xs = []
    ys = []

    x_val = x_start
    while x_val <= x_end:
        xs.append(x_val)
        x_val += TILE_SIZE

    y_val = y_start
    while y_val <= y_end:
        ys.append(y_val)
        y_val += TILE_SIZE

    tiles = [(x, y) for y in ys for x in xs]
    return tiles


def _import_tile(args):
    """
    Worker function for parallel r.in.gdal.

    args = (url, tmp_name, x, y, memory)
    Returns tmp_name on success, or None on failure.
    """
    url, tmp_name, x, y, memory = args
    in_args = {
        "input": f"/vsicurl/{url}",
        "output": tmp_name,
        "flags": "ro",
        "gdal_config": "GDAL_DISABLE_READDIR_ON_OPEN=EMPTY_DIR",
    }
    if memory > 0:
        in_args["memory"] = memory

    try:
        gs.message(f"Downloading and importing tile {int(x)},{int(y)} from:\n{url}")
        gs.run_command("r.in.gdal", **in_args)
        return tmp_name
    except Exception as e:
        gs.warning(
            _(
                "Failed to import tile {x}_{y} from {url}. "
                "Skipping this tile. Error: {err}"
            ).format(x=int(x), y=int(y), url=url, err=e)
        )
        return None


def patch_in_batches(input_maps, output, memory, nprocs, max_inputs):
    """
    Patch many maps safely, avoiding command-line length / r.patch limits.

    If len(input_maps) <= max_inputs:
        - run r.patch once directly into 'output'.

    Else:
        - split into chunks of size max_inputs
        - patch each chunk into an intermediate mosaic
        - recursively patch the intermediates into 'output'
    """
    if len(input_maps) <= max_inputs:
        gs.message(
            f"Patching {len(input_maps)} maps into <{output}> "
            f"(memory={memory}MB, nprocs={nprocs})"
        )
        args = {
            "input": ",".join(input_maps),
            "output": output,
            "flags": "s",
            "overwrite": True,
        }
        if memory > 0:
            args["memory"] = memory
        if nprocs > 1:
            args["nprocs"] = nprocs

        gs.run_command("r.patch", **args)
        return

    # Too many maps: batch them
    gs.message(
        f"{len(input_maps)} maps > max_inputs={max_inputs}: patching in batches ..."
    )

    intermediate = []
    for i in range(0, len(input_maps), max_inputs):
        chunk = input_maps[i : i + max_inputs]
        tmp = create_temporary_name(f"{output}_batch")
        gs.message(
            f"  Creating intermediate mosaic <{tmp}> from "
            f"{len(chunk)} maps ({i}–{i+len(chunk)-1})"
        )

        args = {
            "input": ",".join(chunk),
            "output": tmp,
            "flags": "s",
            "overwrite": True,
        }
        if memory > 0:
            args["memory"] = memory
        if nprocs > 1:
            args["nprocs"] = nprocs

        gs.run_command("r.patch", **args)
        intermediate.append(tmp)

    # Recursively patch the intermediates
    patch_in_batches(
        input_maps=intermediate,
        output=output,
        memory=memory,
        nprocs=nprocs,
        max_inputs=max_inputs,
    )


def grass_version_at_least(major_req, minor_req):
    """
    Returns True if the running GRASS version is >= major_req.minor_req.
    """
    info = gs.parse_command("g.version", flags="g")
    version = info.get("version", "0.0.0")

    try:
        major, minor, *_ = version.split(".")
        major = int(major)
        minor = int(minor)
    except Exception:
        gs.warning(f"Unable to parse GRASS version string: {version}")
        return False

    return (major > major_req) or (major == major_req and minor >= minor_req)


def import_product(product, version, res, tiles, outname, memory, nprocs, max_inputs):
    """
    Import and patch AHN tiles for a single product (dtm or dsm).
    """

    # Build jobs for parallel download/import
    jobs = []
    for x, y in tiles:
        url = get_tile_url(version, product, res, x, y)
        tmp_name = create_temporary_name(f"{outname}")
        jobs.append((url, tmp_name, x, y, memory))

    # Download and import tiles (in parallel if nprocs > 1)
    if nprocs > 1 and len(jobs) > 1:
        gs.message(
            f"Importing {len(jobs)} {product.upper()} tiles in parallel using {nprocs} processes ..."
        )
        with Pool(processes=nprocs) as pool:
            results = pool.map(_import_tile, jobs)
    else:
        gs.message(f"Importing {len(jobs)} {product.upper()} tiles sequentially ...")
        results = [_import_tile(job) for job in jobs]

    tile_rasters = [r for r in results if r is not None]

    if not tile_rasters:
        gs.fatal(_("Import of all requested AHN tiles failed."))

    # Patch tiles into a single raster
    gs.message(f"Patching imported {product.upper()} tiles into a single raster layer ...")
    found = gs.find_file(name="MASK", element="cell")
    if nprocs > 1 and found["name"] == "MASK":
        if grass_version_at_least(8, 5):
            with gs.MaskManager():
                patch_in_batches(
                    input_maps=tile_rasters,
                    output=outname,
                    memory=memory,
                    nprocs=nprocs,
                    max_inputs=max_inputs,
                )
        else:
            # GRASS < 8.5: emulate MaskManager by temporary renaming MASK
            backup_name = create_temporary_name("MASK_backup")
            gs.run_command(
                "g.rename",
                raster=f"MASK,{backup_name}",
                quiet=True,
            )
            try:
                patch_in_batches(
                    input_maps=tile_rasters,
                    output=outname,
                    memory=memory,
                    nprocs=nprocs,
                    max_inputs=max_inputs,
                )
            finally:
                # Restore original MASK
                gs.run_command(
                    "g.rename",
                    raster=f"{backup_name},MASK",
                    quiet=True,
                )
    else:
        patch_in_batches(
            input_maps=tile_rasters,
            output=outname,
            memory=memory,
            nprocs=nprocs,
            max_inputs=max_inputs,
        )

    # Apply elevation color table
    gs.run_command("r.colors", map=outname, color="elevation")

    # Metadata
    if res == 0.5:
        res_label = "05m"
    else:
        res_label = "5m"

    title = f"{product}_{res_label} AHN version {version}"

    gs.run_command(
        "r.support",
        map=outname,
        title=title,
        units="meters",
        source1="https://www.ahn.nl",
    )
    gs.run_command(
        "r.support",
        map=outname,
        history="The main steps by r.in.ahn are:",
    )
    hist_tiles = (
        f"Downloaded and patched AHN{version} {product} tiles "
        f"({len(tile_rasters)} tiles, resolution {res} m, "
        f"memory={memory}MB, nprocs={nprocs})"
    )
    gs.run_command("r.support", map=outname, history=hist_tiles)

    gs.message(
        "-----------------"
        "The AHN {prod} (version {ver}, {res} m) has been downloaded and "
        "imported as {out}".format(prod=product, ver=version, res=res, out=outname)
    )


def main(options, flags):
    """
    Download AHN tiles (DTM/DSM, 0.5 or 5 m) and patch them into a single raster.
    If chm is selected, create the chm layer.
    """

    # Check if the projection is RD New (EPSG:28992)
    proj_info = gs.parse_command("g.proj", flags="g")
    if proj_info["srid"] != "EPSG:28992" and proj_info["name"] != "Amersfoort / RD New":
        gs.fatal(_("This module only works with locations with projection EPSG=28992"))

    product = options["product"]
    version = options["version"]
    res = float(options["resolution"])
    outname = options["output"]
    memory = int(options["memory"])
    nprocs = int(options["nprocs"])
    if nprocs < 1:
        nprocs = 1

    if res not in (0.5, 5.0):
        gs.fatal(_("Resolution must be 0.5 or 5 meters."))

    # Use temp region if we want to restore original region afterwards
    if flags["g"]:
        gs.use_temp_region()
    region_current = gs.parse_command("g.region", flags="gu")

    # Compute overlap of region with AHN extent
    n_ov, s_ov, w_ov, e_ov = overlap_with_ahn(region_current)

    # Compute which tiles we need based on this overlap
    tiles = tiles_for_region(n_ov, s_ov, w_ov, e_ov)
    if not tiles:
        gs.fatal(_("No AHN tiles intersect the requested region."))

    # Compute snapped region (NO clamping necessary)
    n_sn = res * ceil(n_ov / res)
    s_sn = res * floor(s_ov / res)
    w_sn = res * floor(w_ov / res)
    e_sn = res * ceil(e_ov / res)

    # Derive final region from the selected tiles
    w_tiles = min(x for x, _ in tiles)
    e_tiles = max(x for x, _ in tiles) + TILE_SIZE
    s_tiles = min(y for _, y in tiles)
    n_tiles = max(y for _, y in tiles) + TILE_SIZE

    # Final region = intersection of snapped region with tile union
    n_final = min(n_sn, n_tiles)
    s_final = max(s_sn, s_tiles)
    w_final = max(w_sn, w_tiles)
    e_final = min(e_sn, e_tiles)

    gs.message(
        "The region's extent and resolution have been adjusted to exactly "
        "match the selected AHN tiles:\n"
        f"  n={n_final}, s={s_final}, w={w_final}, e={e_final}, res={res}"
    )
    gs.run_command("g.region", n=n_final, s=s_final, e=e_final, w=w_final, res=res)

    max_inputs = int(options["max_inputs"])

    # Handle CHM (DTM+DSM) or single product (DTM/DSM)
    if product == "chm":
        # Derive names for component maps and CHM
        dtm_out = f"{outname}_dtm"
        dsm_out = f"{outname}_dsm"
        chm_out = f"{outname}_chm"

        # Import DTM
        import_product(
            product="dtm",
            version=version,
            res=res,
            tiles=tiles,
            outname=dtm_out,
            memory=memory,
            nprocs=nprocs,
            max_inputs=max_inputs,
        )

        # Import DSM
        import_product(
            product="dsm",
            version=version,
            res=res,
            tiles=tiles,
            outname=dsm_out,
            memory=memory,
            nprocs=nprocs,
            max_inputs=max_inputs,
        )

        # Compute CHM = DSM - DTM
        gs.message("Calculating CHM (DSM - DTM) ...")
        expr = f"{chm_out} = {dsm_out} - {dtm_out}"
        gs.run_command("r.mapcalc", expression=expr, quiet=True)
        gs.run_command("r.colors", map=chm_out, color="elevation", quiet=True)

        # Metadata for CHM
        if res == 0.5:
            res_label = "05m"
        else:
            res_label = "5m"

        chm_title = f"chm_{res_label} AHN version {version}"

        gs.run_command(
            "r.support",
            map=chm_out,
            title=chm_title,
            units="meters",
            source1="https://www.ahn.nl",
        )
        gs.run_command(
            "r.support",
            map=chm_out,
            history="CHM = DSM - DTM calculated by r.in.ahn",
        )

        gs.message(
            "-----------------"
            "The AHN CHM (version {ver}, {res} m) has been calculated as {chm} "
            "from {dsm} (DSM) and {dtm} (DTM)".format(
                ver=version, res=res, chm=chm_out, dsm=dsm_out, dtm=dtm_out
            )
        )

    else:
        # Single product (DTM or DSM)
        import_product(
            product=product,
            version=version,
            res=res,
            tiles=tiles,
            outname=outname,
            memory=memory,
            nprocs=nprocs,
            max_inputs=max_inputs,
        )

    return 0


if __name__ == "__main__":
    atexit.register(cleanup)
    sys.exit(main(*gs.parser()))
