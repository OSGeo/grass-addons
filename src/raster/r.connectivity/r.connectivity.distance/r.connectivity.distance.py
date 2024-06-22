#!/usr/bin/env python3

"""
MODULE:       r.connectivity.distance
AUTHOR(S):    Stefan Blumentrath <stefan . blumentrath at nina . no >
PURPOSE:      Compute cost-distance between all polygons (patches) of an
              input vector map within a user defined Euclidean distance
              threshold

              Recently, graph-theory has been characterised as an
              efficient and useful tool for conservation planning (e.g.
              Bunn et al. 2000, Calabrese & Fagan 2004,
              Minor & Urban 2008, Zetterberg et. al. 2010).
              As a part of the r.connectivity.* tool-chain,
              r.connectivity.distance is intended to make graph-theory
              more easily available to conservation planning.

              r.connectivity.distance is the first tool of the
              r.connectivity.*-toolchain (followed by
              r.connectivity.network and r.connectivity.corridor).
              r.connectivity.distance loops through all polygons in the
              input vector map and calculates the cost-distance to all
              the other polygons within a user-defined Euclidean
              distance threshold.

              It produces two vector maps that hold the network:
               - an edge-map (connections between patches) and a
               - vertex-map (centroid representations of the patches).

              Attributes of the edge-map are:
              cat: line category
              from_patch: category of the start patch
              to_patch: category of the destination patch
              dist: cost-distance from from_patch to to_patch

              Attributes of the vertex-map are:
              cat: category of the input patches
              pop_proxy: containing the user defined population proxy
                         used in further analysis, representing a proxy
                         for the amount of organisms potentially
                         dispersing from a patch (e.g. habitat area).


              In addition, r.connectivity.distance outputs a cost
              distance raster map for every input polygon which later on
              are used in r.connectivity.corridors (together with output
              from r.connectivity.network) for corridor identification.

              Distance between patches is measured as border to border
              distance. The user can define the number of cells (n)
              along the border to be used for distance measuring.
              The distance from a (start) polygon to another (end) is
              measured as the n-th closest cell on the border of the
              other (end) polygon. An increased number of border cells
              used for distance measuring affects (increases) also the
              width of possible corridors computed with
              r.connectivity.corridor later on.

              If the conefor_dir option is also specified, output in
              CONEFOR format will be produced, namely
               - a node file
               - a directed connection file, and
               - an undirected connection file


COPYRIGHT:    (C) 2018-2024 by the Norwegian Institute for Nature Research
                  (NINA), Stefan Blumentrath and the GRASS GIS Development
                  Team


              This program is free software under the GNU General Public
              License (>=v2). Read the file COPYING that comes with
              GRASS for details.

Todo:
- Implement points mode
- Write extra module for CONEFOR export?
    - probability output (exponent, base, weight option)
    - choose directed vs undirected output
    - select included/excluded nodes
    - different distance measures
"""

# %module
# % description: Compute cost-distances between patches of an input vector map
# % keyword: raster
# % keyword: vector
# % keyword: connectivity
# % keyword: cost distance
# % keyword: walking distance
# % keyword: least cost path
# % keyword: Conefor
# %end

# %option G_OPT_V_INPUT
# % required: yes
# % key_desc: patches (input)
# % description: Name of input vector map containing habitat patches
# %end

# %option G_OPT_V_FIELD
# % required: yes
# % answer: 1
# % description: layer containing patch geometries
# %end

# %option G_OPT_DB_COLUMN
# % key: pop_proxy
# % required: yes
# % key_desc: pop_proxy
# % description: Column containing proxy for population size (not NULL and > 0)
# %end

# %option G_OPT_R_INPUT
# % key: costs
# % required: no
# % key_desc: costs (input)
# % description: Name of input costs raster map
# %end

# %option G_OPT_R_ELEV
# % required: no
# %end

# %option G_OPT_M_NPROCS
# % required: no
# %end

# %option
# % key: prefix
# % type: string
# % description: Prefix used for all output of the module (network vector map(s) and cost distance raster maps)
# % required : yes
# % guisection: Output
# %end

# %option
# % key: cutoff
# % type: double
# % description: Maximum search distance around patches in meter
# % required: no
# % guisection: Settings
# % answer: 10000
# %end

# %option
# % key: border_dist
# % type: integer
# % description: Number of border cells used for distance measuring
# % required : no
# % guisection: Settings
# % answer : 50
# %end

# %option
# % key: memory
# % type: integer
# % description: Maximum memory to be used in MB
# % required : no
# % guisection: Settings
# % answer : 300
# %end

# %option G_OPT_M_DIR
# % key: conefor_dir
# % description: Directory for additional output in Conefor format
# % required : no
# % guisection: Output
# %end

# %flag
# % key: P
# % description: Points mode: patch maps contains points or centroids should be used
# % guisection: Settings
# %end

# %flag
# % key: p
# % description: Extract and save shortest paths and closest points into a vector map
# % guisection: Settings
# %end

# %flag
# % key: t
# % description: Rasterize patch borders with "all-touched" option using GDAL
# % guisection: Settings
# %end

# %flag
# % key: r
# % description: Remove distance maps (saves disk-space but disables computation of corridors)
# % guisection: Settings
# %end

# %flag
# % key: k
# % description: Use the 'Knight's move'; slower, but more accurate
# % guisection: Settings
# %end

# %option
# % key: walk_coeff
# % type: string
# % description: Coefficients for walking energy formula parameters a,b,c,d
# % required : no
# % answer : 0.72,6.0,1.9998,-1.9998
# % guisection: Movement
# %end

# %option
# % key: lambda
# % type: double
# % description: Lambda coefficients for combining walking energy and friction cost
# % required : no
# % answer : 1.0
# % guisection: Movement
# %end

# %option
# % key: slope_factor
# % type: double
# % description: Slope factor determines travel energy cost per height step
# % required : no
# % answer : -0.2125
# % guisection: Movement
# %end

import atexit
import os
import sys
import shutil
import subprocess

from copy import deepcopy
from functools import partial
from io import BytesIO
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import grass.script as gs

# from grass.pygrass.modules import Module
from grass.pygrass.vector import VectorTopo
from grass.pygrass.vector.basic import Bbox
from grass.pygrass.raster.history import History
from grass.pygrass.vector.geometry import Centroid
from grass.pygrass.vector.geometry import Point
from grass.pygrass.vector.geometry import Line

from grass.script.setup import write_gisrc

# check if GRASS is running or not
if "GISBASE" not in os.environ:
    sys.exit("You must be in GRASS GIS to run this program")

# Define additional global variables
TMP_PREFIX = gs.tempname(12)


def cleanup():
    """Remove temporary data"""
    gs.del_temp_region()
    tmp_maps = gs.read_command(
        "g.list",
        type=["vector", "raster"],
        pattern=f"{TMP_PREFIX}*",
        separator=",",
    )

    if tmp_maps:
        gs.run_command(
            "g.remove",
            type=["vector", "raster"],
            pattern=f"{TMP_PREFIX}*",
            quiet=True,
            flags="f",
        )
    if TMP_PREFIX and len(TMP_PREFIX) == 12:
        shutil.rmtree(os.path.join(*list(gs.gisenv().values())[0:2], f"{TMP_PREFIX}*"))


def copy_from_temp_mapsets(source_mapset, prefix=None):
    gs.run_command(
        "g.copyall", mapset=source_mapset, datatype="rast", filter_=f"{prefix}*"
    )


def prepare_patches(grass_options, grass_flags, start_region):
    """Rasterize patches and return relevant categories"""
    patch_map = grass_options["input"]
    patches = patch_map.split("@")[0]
    patches_mapset = patch_map.split("@")[1] if len(patch_map.split("@")) > 1 else None

    if grass_flags["P"]:
        start_region_bbox = Bbox(
            north=float(start_region["n"]),
            south=float(start_region["s"]),
            east=float(start_region["e"]),
            west=float(start_region["w"]),
        )

        vpatches = VectorTopo(patches, mapset=patches_mapset)
        vpatches.open("r", layer=int(grass_options["layer"]))

        # Geometrytype 1 = POINT, 8 = CENTROID; POINTS (9) is not allowed
        return list(
            set(
                [
                    point.cat
                    for point in vpatches.find_by_bbox.geos(start_region_bbox)
                    if point.gtype in [1, 8]
                ]
            )
        )

    # Rasterize patches
    # http://www.gdal.org/gdal_tutorial.html
    # http://geoinformaticstutorial.blogspot.no/2012/11/convert-
    # shapefile-to-raster-with-gdal.html
    if grass_flags["t"]:
        # Rasterize patches with "all-touched" mode using GDAL
        # Read region-settings (not needed canuse max_n, min_s, max_e,
        # min_w nsres, ewres...
        folder = Path(gs.tempdir())

        prast = folder / "patches_rast.tif"

        # Check if GDAL-GRASS plugin is installed
        if ogr.GetDriverByName("GRASS"):
            # With GDAL-GRASS plugin
            # Locate file for patch vector map
            pfile = gs.parse_command(
                "g.findfile", element="vector", file=patches, mapset=patches_mapset
            )["file"]
            pfile = Path(pfile) / "head"

        else:
            # Without GDAL-GRASS-plugin
            gs.warning(
                _(
                    "Cannot find GDAL-GRASS plugin. Consider \
                          installing it in order to save time for \
                          all-touched rasterisation"
                )
            )
            pfile = folder / "patches_vect.gpkg"
            # Export patch vector map to temp-file in a GDAL-readable
            # format (shp)
            gs.run_command(
                "v.out.ogr",
                flags="m",
                quiet=True,
                input=patch_map,
                type="area",
                layer=grass_options["layer"],
                output=str(pfile),
                lco="GEOMETRY_NAME=geom",
            )

        # Rasterize vector map with all-touched option
        os.system(
            f"gdal_rasterize -l {patches} -at \
             -tr {start_region['ewres']} {start_region['nsres']} \
             -te {start_region['w']} {start_region['s']} {start_region['e']} {start_region['n']} \
             -ot Uint32 -a cat {pfile} {prast} -q"
        )

        if not ogr.GetDriverByName("GRASS"):
            # Remove vector temp-file
            (folder / "patches_vect.gpkg").unlink()

        # Import rasterized patches
        gs.run_command(
            "r.external",
            flags="o",
            quiet=True,
            input=str(prast),
            output=f"{TMP_PREFIX}_patches_pol",
        )

    else:
        # Simple rasterisation (only area)
        gs.run_command(
            "v.to.rast",
            quiet=True,
            input=patches,
            use="cat",
            type=["area", "centroid"],
            output=f"{TMP_PREFIX}_patches_pol",
        )

    # Extract boundaries from patch raster map
    gs.run_command(
        "r.mapcalc",
        expression=f"{TMP_PREFIX}_patches_boundary=if(\
            {TMP_PREFIX}_patches_pol,\
            if((\
            (isnull({TMP_PREFIX}_patches_pol[-1,0])||| \
            {TMP_PREFIX}_patches_pol[-1,0]!={TMP_PREFIX}_patches_pol)||| \
            (isnull({TMP_PREFIX}_patches_pol[0,1])||| \
            {TMP_PREFIX}_patches_pol[0,1]!={TMP_PREFIX}_patches_pol)||| \
            (isnull({TMP_PREFIX}_patches_pol[1,0])||| \
            {TMP_PREFIX}_patches_pol[1,0]!={TMP_PREFIX}_patches_pol)||| \
            (isnull({TMP_PREFIX}_patches_pol[0,-1])||| \
            {TMP_PREFIX}_patches_pol[0,-1]!={TMP_PREFIX}_patches_pol)), \
            {TMP_PREFIX}_patches_pol,null()), null())",
        quiet=True,
    )

    rasterized_cats = (
        gs.read_command(
            "r.category",
            separator="newline",
            map=f"{TMP_PREFIX}_patches_boundary",
        )
        .replace("\t", "")
        .strip("\n")
    )
    rasterized_cats = list({int(x) for x in rasterized_cats.split("\n") if x != ""})

    return rasterized_cats


def prepare_start_stop_patch_region(cat, patch_map, cutoff, start_region):
    """Create start and stop patches for category and set region
    according to cutoff"""
    # Get BoundingBox
    from_bbox = gs.parse_command(
        "v.db.select", map=patch_map, flags="r", where=f"cat={cat}"
    )
    start_patch = f"{TMP_PREFIX}_patch_{cat}"
    reclass_rule = gs.encode(f"{cat} = 1\n* = NULL")
    recl = gs.feed_command(
        "r.reclass",
        quiet=True,
        input=f"{TMP_PREFIX}_patches_boundary",
        output=start_patch,
        rules="-",
    )
    recl.stdin.write(reclass_rule)
    recl.stdin.close()
    recl.wait()

    # Prepare stop patches
    ############################################
    reg = gs.parse_command(
        "g.region",
        flags="ug",
        quiet=True,
        raster=start_patch,
        n=float(from_bbox["n"]) + float(cutoff),
        s=float(from_bbox["s"]) - float(cutoff),
        e=float(from_bbox["e"]) + float(cutoff),
        w=float(from_bbox["w"]) - float(cutoff),
        align=f"{TMP_PREFIX}_patches_pol",
    )

    north = min(float(reg["n"]), float(start_region["n"]))
    south = max(float(reg["s"]), float(start_region["s"]))
    east = min(float(reg["e"]), float(start_region["e"]))
    west = max(float(reg["w"]), float(start_region["w"]))

    # Set region to patch search radius
    gs.use_temp_region()
    gs.run_command(
        "g.region",
        quiet=True,
        n=north,
        s=south,
        e=east,
        w=west,
        align=f"{TMP_PREFIX}_patches_pol",
    )

    # Create buffer around start-patch as a mask
    # for cost distance analysis
    gs.run_command(
        "r.buffer",
        quiet=True,
        input=start_patch,
        output="MASK",
        distances=float(options["cutoff"]),
    )
    gs.run_command(
        "r.mapcalc",
        quiet=True,
        expression=f"{TMP_PREFIX}_patch_{cat}_neighbours_contur=\
                    if({TMP_PREFIX}_patches_boundary=={cat},\
                    null(),\
                    {TMP_PREFIX}_patches_boundary)",
    )
    gs.run_command("r.mask", flags="r", quiet=True)

    return start_patch


def compute_distances(
    cat_chunk,
    grass_environment,
    source_mapset=None,
    rasterized_cats=None,
    prefix=None,
    patches=None,
    patches_mapset=None,
    start_region=None,
    memory=None,
):
    """"""

    lin_cat = 1
    zero_dist = 0
    counter = 0
    edge_map = f"{prefix}_edges"
    vertex_map = f"{prefix}_vertices"
    shortest_paths = f"{prefix}_shortest_paths"

    if not patches_mapset:
        patches_mapset = source_mapset

    if not (
        Path(grass_environment["GISDBASE"])
        / grass_environment["LOCATION_NAME"]
        / grass_environment["MAPSET"]
    ).exists():
        (
            Path(grass_environment["GISDBASE"])
            / grass_environment["LOCATION_NAME"]
            / grass_environment["MAPSET"]
        ).mkdir()
        gisrc_chunk = write_gisrc(
            grass_environment["GISDBASE"],
            grass_environment["LOCATION_NAME"],
            grass_environment["MAPSET"],
        )
        env = os.environ
        env["GISRC"] = gisrc_chunk
        gs.run_command("g.region", flags="d")
        gs.run_command(
            "g.region",
            n=start_region["n"],
            s=start_region["s"],
            e=start_region["e"],
            w=start_region["w"],
            ewres=start_region["ewres"],
            nsres=start_region["nsres"],
        )
        gs.run_command("g.mapsets", operation="add", mapset=source_mapset)

    start_region_bbox = Bbox(
        north=float(start_region["n"]),
        south=float(start_region["s"]),
        east=float(start_region["e"]),
        west=float(start_region["w"]),
    )

    vpatches = VectorTopo(patches, mapset=patches_mapset)
    vpatches.open("r", layer=int(options["layer"]))

    ###Loop through patches
    vpatch_ids = np.array(
        vpatches.features_to_wkb_list(feature_type="centroid", bbox=start_region_bbox),
        dtype=[("vid", "uint32"), ("cat", "uint32"), ("geom", "|S10")],
    )
    cats = set(vpatch_ids["cat"])
    n_cats = len(cats)
    if source_mapset:
        lin_cat = (
            n_cats * len(cat_chunk) * int(grass_environment["MAPSET"].split("_")[-1])
        )
    if n_cats < len(vpatch_ids["cat"]):
        gs.verbose(
            _(
                "At least one MultiPolygon found in patch map.\n \
                 Using average coordinates of the centroids for \
                 visual representation of the patch."
            )
        )

    # Init output vector maps if they are requested by user
    network = VectorTopo(edge_map, grass_environment["MAPSET"])
    network_columns = [
        ("cat", "INTEGER PRIMARY KEY"),
        ("from_p", "INTEGER"),
        ("to_p", "INTEGER"),
        ("min_dist", "DOUBLE PRECISION"),
        ("dist", "DOUBLE PRECISION"),
        ("max_dist", "DOUBLE PRECISION"),
    ]
    network.open("w", tab_name=edge_map, tab_cols=network_columns)

    vertex = VectorTopo(vertex_map, grass_environment["MAPSET"])
    vertex_columns = [
        ("cat", "INTEGER PRIMARY KEY"),
        (options["pop_proxy"], "DOUBLE PRECISION"),
    ]
    vertex.open("w", tab_name=vertex_map, tab_cols=vertex_columns)

    if flags["p"]:
        # Init cost paths file for start-patch
        gs.run_command("v.edit", quiet=True, map=shortest_paths, tool="create")
        gs.run_command(
            "v.db.addtable",
            quiet=True,
            map=shortest_paths,
            columns="cat integer,\
                     from_p integer,\
                     to_p integer,\
                     dist_min double precision,\
                     dist double precision,\
                     dist_max double precision",
        )

    for cat in cat_chunk:
        if cat not in rasterized_cats:
            gs.warning(
                _(
                    "Patch {} has not been rasterized and will \
                     therefore not be treated as part of the \
                     network. Consider using t-flag or change \
                     resolution."
                ).format(cat)
            )

            continue
        gs.verbose(
            _("Calculating connectivity-distances for patch number {}").format(cat)
        )

        # Filter
        from_vpatch = vpatch_ids[vpatch_ids["cat"] == cat]

        # Get patch ID
        if from_vpatch["vid"].size == 1:
            from_centroid = Centroid(
                v_id=int(from_vpatch["vid"]), c_mapinfo=vpatches.c_mapinfo
            )
            from_x = from_centroid.x
            from_y = from_centroid.y

            # # Get centroid
            # if not from_centroid:
            #     continue
        else:
            xcoords = []
            ycoords = []
            for f_p in from_vpatch["vid"]:
                from_centroid = Centroid(v_id=int(f_p), c_mapinfo=vpatches.c_mapinfo)
                xcoords.append(from_centroid.x)
                ycoords.append(from_centroid.y)

                # # Get centroid
                # if not from_centroid:
                #     continue
            from_x = np.average(xcoords)
            from_y = np.average(ycoords)

        attr_filter = vpatches.table.filters.select(options["pop_proxy"])
        attr_filter = attr_filter.where(f"cat={cat}")
        proxy_val = vpatches.table.execute().fetchone()

        # Prepare start patch
        start_patch = prepare_start_stop_patch_region(
            cat,
            f"{patches}@{patches_mapset}" if patches_mapset else patches,
            float(options["cutoff"]),
            start_region,
        )

        cost_distance_map = f"{options['prefix']}_patch_{cat}_cost_dist"
        kwargs = {
            "flags": "kn" if flags["k"] else "n",
            "quiet": True,
            "overwrite": True,
            "start_rast": start_patch,
            "memory": memory,
            "output": cost_distance_map,
        }

        if flags["p"]:
            kwargs["outdir"] = f"{TMP_PREFIX}_direction"

        # Calculate cost distance
        if options["elevation"]:
            gs.run_command(
                "r.walk",
                friction=options["costs"],
                elevation=options["elevation"],
                slope_factor=options["slope_factor"],
                lambda_=options["lambda"],
                walk_coeff=options["walk_coeff"],
                **kwargs,
            )
        else:
            gs.run_command("r.cost", input=options["costs"], **kwargs)

        # gs.run_command('g.region', flags='up')
        # gs.raster.raster_history(cost_distance_map)
        write_raster_history(cost_distance_map)

        # Export distance at boundaries
        maps = f"{TMP_PREFIX}_patch_{cat}_neighbours_contur,{options['prefix']}_patch_{cat}_cost_dist"

        connections = gs.encode(
            gs.read_command(
                "r.stats", flags="1ng", quiet=True, input=maps, separator=";"
            ).rstrip("\n")
        )

        # In Points-mode use r.what here
        # if grass_flags["P"]:
        #     connections = gs.encode(
        #     gs.read_command(
        #         "r.what", flags="cv", quiet=True, map=f"{options['prefix']}_patch_{cat}_cost_dist", points=vertices, separator=";"
        #     ).rstrip("\n")
        # )

        if connections:
            con_array = np.genfromtxt(
                BytesIO(connections),
                delimiter=";",
                dtype=None,
                names=["x", "y", "cat", "dist"],
            )
        else:
            gs.warning(_("No connections for patch {}").format(cat))

            # Write centroid to vertex map
            vertex.write(Point(from_x, from_y), cat=int(cat), attrs=proxy_val)
            vertex.table.conn.commit()

            # Remove temporary map data
            gs.run_command(
                "g.remove",
                quiet=True,
                flags="f",
                type=["raster", "vector"],
                pattern=f"{TMP_PREFIX}*{cat}*",
            )
            gs.del_temp_region()
            continue

        # Find closest points on neigbour patches
        to_cats = set(np.atleast_1d(con_array["cat"]))
        to_coords = []
        for to_cat in to_cats:
            connection = con_array[con_array["cat"] == to_cat]
            connection.sort(order=["dist"])
            pixel = (
                int(options["border_dist"])
                if len(connection) > int(options["border_dist"])
                else len(connection) - 1
            )
            closest_points_to_cat = to_cat
            closest_points_min_dist = connection["dist"][0]
            closest_points_dist = connection["dist"][pixel]
            closest_points_max_dist = connection["dist"][-1]
            to_patch_ids = vpatch_ids[vpatch_ids["cat"] == int(to_cat)]["vid"]

            if len(to_patch_ids) == 1:
                to_centroid = Centroid(
                    v_id=to_patch_ids[0], c_mapinfo=vpatches.c_mapinfo
                )
                to_x = to_centroid.x
                to_y = to_centroid.y
            elif len(to_patch_ids) >= 1:
                xcoords = []
                ycoords = []
                for t_p in to_patch_ids:
                    to_centroid = Centroid(v_id=int(t_p), c_mapinfo=vpatches.c_mapinfo)
                    xcoords.append(to_centroid.x)
                    ycoords.append(to_centroid.y)

                    # # Get centroid
                    # if not to_centroid:
                    #     continue
                to_x = np.average(xcoords)
                to_y = np.average(ycoords)

            to_coords.append(
                ",".join(
                    [
                        str(connection["x"][0]),
                        str(connection["y"][0]),
                        str(to_cat),
                        str(closest_points_min_dist),
                        str(closest_points_dist),
                        str(closest_points_max_dist),
                    ]
                )
            )

            # Save edges to network dataset
            if closest_points_dist <= 0:
                zero_dist = 1

            # Write data to network
            network.write(
                Line([(from_x, from_y), (to_x, to_y)]),
                cat=lin_cat,
                attrs=(
                    cat,
                    int(closest_points_to_cat),
                    closest_points_min_dist,
                    closest_points_dist,
                    closest_points_max_dist,
                ),
            )
            network.table.conn.commit()

            lin_cat = lin_cat + 1

        # Save closest points and shortest paths through cost raster as
        # vector map (r.drain limited to 1024 points; ) if requested
        if flags["p"]:
            gs.verbose(
                _("Extracting shortest paths for patch number {}...").format(cat)
            )

            points_n = len(to_cats)

            tiles = int(points_n / 1024.0)
            rest = points_n % 1024
            if not rest == 0:
                tiles = tiles + 1

            tile_n = 0
            while tile_n < tiles:
                tile_n = tile_n + 1
                # Import closest points for start-patch in 1000er blocks
                v_in_ascii = gs.feed_command(
                    "v.in.ascii",
                    flags="nr",
                    overwrite=True,
                    quiet=True,
                    input="-",
                    stderr=subprocess.PIPE,
                    output=f"{TMP_PREFIX}_{cat}_cp",
                    separator=",",
                    columns="x double precision,\
                             y double precision,\
                             to_p integer,\
                             dist_min double precision,\
                             dist double precision,\
                             dist_max double precision",
                )
                v_in_ascii.stdin.write(gs.encode("\n".join(to_coords)))
                v_in_ascii.stdin.close()
                v_in_ascii.wait()

                # Extract shortest paths for start-patch in chunks of
                # 1024 points
                cost_paths = f"{TMP_PREFIX}_{cat}_cost_paths"
                start_points = f"{TMP_PREFIX}_{cat}_cp"

                gs.run_command(
                    "r.path",
                    overwrite=True,
                    quiet=True,
                    input=f"{TMP_PREFIX}_direction",
                    # output=cost_paths,
                    vector_path=cost_paths,
                    start_points=start_points,
                )

                gs.run_command(
                    "v.db.addtable",
                    map=cost_paths,
                    quiet=True,
                    columns="cat integer,\
                             from_p integer,\
                             to_p integer,\
                             dist_min double precision,\
                             dist double precision,\
                             dist_max double precision",
                )

                gs.run_command(
                    "v.db.update",
                    map=cost_paths,
                    column="from_p",
                    value=cat,
                    quiet=True,
                )

                gs.run_command(
                    "v.distance",
                    quiet=True,
                    from_=cost_paths,
                    to=start_points,
                    upload="to_attr",
                    column="to_p",
                    to_column="to_p",
                )

                gs.run_command(
                    "v.db.join",
                    quiet=True,
                    map=cost_paths,
                    column="to_p",
                    other_column="to_p",
                    # exclude_columns="cat",
                    other_table=start_points,
                    subset_columns="dist_min,dist,dist_max",
                )

                gs.run_command(
                    "v.patch",
                    flags="ae",
                    overwrite=True,
                    quiet=True,
                    input=cost_paths,
                    output=shortest_paths,
                )

                # Remove temporary map data
                gs.run_command(
                    "g.remove",
                    quiet=True,
                    flags="f",
                    type=["raster", "vector"],
                    pattern=f"{TMP_PREFIX}*{cat}*",
                )

        # Remove temporary map data for patch
        if flags["r"]:
            gs.run_command(
                "g.remove", flags="f", type="raster", name=cost_distance_map, quiet=True
            )

        vertex.write(Point(from_x, from_y), cat=int(cat), attrs=proxy_val)
        vertex.table.conn.commit()

        # Print progress message
        gs.percent(i=int((float(counter) / len(cat_chunk)) * 100), n=100, s=3)

        # Update counter for progress message
        counter = counter + 1

    if zero_dist:
        gs.warning(
            _(
                "Some patches are directly adjacent to others. \
                       Minimum distance set to 0.0000000001"
            )
        )

    # Close vector maps and build topology
    network.close()
    vertex.close()


def write_raster_history(raster_map):
    """Re-write raster map history"""
    raster_history = History(raster_map)
    raster_history.clear()
    raster_history.creator = os.environ["USER"]
    raster_history.write()
    # History object cannot modify description
    gs.run_command(
        "r.support",
        map=raster_map,
        description="Generated by r.connectivity.distance",
        history=os.environ["CMDLINE"],
    )


def write_vector_history(vector_map):
    """Write vector map history"""
    gs.run_command(
        "v.support",
        flags="h",
        map=vector_map,
        person=os.environ["USER"],
        cmdhist=os.environ["CMDLINE"],
    )


def main():
    """Do the main processing"""

    # Parse input options:
    patch_map = options["input"]
    patches = patch_map.split("@")[0]
    patches_mapset = patch_map.split("@")[1] if len(patch_map.split("@")) > 1 else None
    conefor_dir = Path(options["conefor_dir"])
    memory = int(options["memory"])
    nprocs = int(options["nprocs"])
    if nprocs > 1 and not flags["r"] and not gs.find_program("g.copyall"):
        # Check if g.copyall is available
        gs.fatal(_("For parallel processing with nprocs > 1, g.copyall is required."))

    # Parse output options:
    edge_map = f"{options['prefix']}_edges"
    vertex_map = f"{options['prefix']}_vertices"
    shortest_paths = f"{options['prefix']}_shortest_paths"

    lin_cat = 1
    zero_dist = None

    # Setup counter for progress message
    counter = 0

    # Check if location is lat/lon (only in lat/lon geodesic distance
    # measuring is supported)
    if gs.locn_is_latlong():
        gs.verbose(_("Location is lat/lon: Geodesic distance measure is used"))

    # Check if prefix is legal GRASS name
    if not gs.legal_name(options["prefix"]):
        gs.fatal(_("{} is not a legal name for GRASS maps.").format(options["prefix"]))

    if options["prefix"][0].isdigit():
        gs.fatal(
            _("Tables names starting with a digit are not SQL compliant.").format(
                options["prefix"]
            )
        )

    # Check if output maps not already exists or could be overwritten
    for output in [edge_map, vertex_map, shortest_paths]:
        if gs.db.db_table_exist(output) and not gs.overwrite():
            gs.fatal(_("Vector map <{}> already exists").format(output))

    # Check if input has required attributes
    in_db_connection = gs.vector.vector_db(patch_map)
    if not int(options["layer"]) in in_db_connection.keys():
        gs.fatal(
            _("No attribute table connected vector map {} at layer {}.").format(
                patches, options["layer"]
            )
        )

    # Check if cat column exists
    pcols = gs.vector.vector_columns(patch_map, layer=options["layer"])

    # Check if cat column exists
    if "cat" not in pcols.keys():
        gs.fatal(
            _("Cannot find the reqired column cat in vector map {}.").format(patches)
        )

    # Check if pop_proxy column exists
    if options["pop_proxy"] not in pcols.keys():
        gs.fatal(
            _("Cannot find column {} in vector map {}").format(
                options["pop_proxy"], patches
            )
        )

    # Check if pop_proxy column is numeric type
    if not pcols[options["pop_proxy"]]["type"] in [
        "INTEGER",
        "REAL",
        "DOUBLE PRECISION",
    ]:
        gs.fatal(
            _(
                "Column {} is of type {}. Only numeric types \
                    (integer or double precision) allowed!"
            ).format(options["pop_proxy"], pcols[options["pop_proxy"]]["type"])
        )

    # Check if pop_proxy column does not contain values <= 0
    pop_vals = np.fromstring(
        gs.read_command(
            "v.db.select",
            flags="c",
            map=patches,
            columns=options["pop_proxy"],
            nv=-9999,
        ).rstrip("\n"),
        dtype=float,
        sep="\n",
    )

    if np.min(pop_vals) <= 0:
        gs.fatal(
            _(
                "Column {} contains values <= 0 or NULL. Neither \
                    values <= 0 nor NULL allowed!"
            ).format(options["pop_proxy"])
        )

    # nprocs = int(options["nprocs"])
    # if nprocs > 1:
    #     compute_distance(cat_chunks, points_mode)
    # else:
    # Create mapset environment
    # Create mapset if needed
    # Loop through chunk of categories
    # patch results from all mapsets
    # remove temporary mapsets

    ##############################################
    # Use pygrass region instead of gs.parse_command !?!
    start_reg = gs.parse_command("g.region", flags="ugp")

    # Prepare patches
    rasterized_cats = prepare_patches(options, flags, start_reg)

    # if nprocs > 1:
    # else:
    #     compute_distances(cat_chunk, grass_environment, patches=None, patches_mapset=None, start_region=start_reg)
    # Add vertex attributes

    ####################################################################
    # Run distance computation for each patch
    if nprocs == 1:
        compute_distances(
            rasterized_cats,
            gs.gisenv(),
            rasterized_cats=rasterized_cats,
            prefix=options["prefix"],
            patches=patches,
            patches_mapset=patches_mapset,
            start_region=start_reg,
            memory=memory,
        )
    elif nprocs > 1:
        grass_env = dict(gs.gisenv())
        compute_distances_parallel = partial(
            compute_distances,
            source_mapset=grass_env["MAPSET"],
            rasterized_cats=rasterized_cats,
            prefix=options["prefix"],
            patches=patches,
            patches_mapset=patches_mapset,
            start_region=start_reg,
            memory=memory,
        )
        copy_from_all_temp_mapsets = partial(
            copy_from_temp_mapsets, prefix=options["prefix"]
        )
        cat_chunks = [
            (rasterized_cats[proc::nprocs], deepcopy(grass_env))
            for proc in range(nprocs)
        ]
        for proc in range(nprocs):
            cat_chunks[proc][1]["MAPSET"] = f"{TMP_PREFIX}_{proc + 1}"

        with Pool(nprocs) as pool:
            pool.starmap(compute_distances_parallel, cat_chunks)
            if not flags["r"]:
                pool.map(
                    copy_from_all_temp_mapsets,
                    [cat_chunks[proc][1]["MAPSET"] for proc in range(nprocs)],
                )
        gs.verbose(_("Merging results from parallel processing"))
        gs.run_command(
            "v.patch",
            flags="e",
            overwrite=True,
            quiet=True,
            input=[
                f"{edge_map}@{cat_chunks[proc][1]['MAPSET']}" for proc in range(nprocs)
            ],
            output=edge_map,
        )
        gs.run_command(
            "v.patch",
            flags="e",
            overwrite=True,
            quiet=True,
            input=[
                f"{vertex_map}@{cat_chunks[proc][1]['MAPSET']}"
                for proc in range(nprocs)
            ],
            output=vertex_map,
        )

        if flags["p"]:
            gs.run_command(
                "v.patch",
                flags="e",
                overwrite=True,
                quiet=True,
                input=[
                    f"{shortest_paths}@{cat_chunks[proc][1]['MAPSET']}"
                    for proc in range(nprocs)
                ],
                output=shortest_paths,
            )

    # Add history and meta data to produced maps
    write_vector_history(edge_map)
    write_vector_history(vertex_map)
    if flags["p"]:
        write_vector_history(shortest_paths)

    # Output also Conefor files if requested
    if conefor_dir:
        if not conefor_dir.exists():
            conefor_dir.mkdir(parents=True)
        query = f"""SELECT p_from, p_to, avg(dist) FROM
                 (SELECT
                 CASE
                 WHEN from_p > to_p THEN to_p
                 ELSE from_p END AS p_from,
                    CASE
                 WHEN from_p > to_p THEN from_p
                 ELSE to_p END AS p_to,
                 dist
                 FROM {edge_map}) AS x
                 GROUP BY p_from, p_to"""
        (conefor_dir / "undirected_connection_file").write_text(
            gs.read_command("db.select", sql=query, separator=" ")
        )
        (conefor_dir / "directed_connection_file").write_text(
            gs.read_command("v.db.select", map=edge_map, separator=" ", flags="c")
        )
        (conefor_dir / "node_file").write_text(
            gs.read_command("v.db.select", map=vertex_map, separator=" ", flags="c")
        )


if __name__ == "__main__":
    options, flags = gs.parser()
    # atexit.register(cleanup)
    # Lazy import GDAL python bindings
    try:
        from osgeo import ogr
    except ImportError as e:
        gs.fatal(_("Module requires GDAL python bindings: {}").format(e))

    sys.exit(main())
