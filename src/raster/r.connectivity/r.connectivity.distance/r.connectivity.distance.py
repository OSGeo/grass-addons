#!/usr/bin/env python
# -*- coding: UTF-8 -*-

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


COPYRIGHT:    (C) 2018 by the Norwegian Institute for Nature Research
                              (NINA)


              This program is free software under the GNU General Public
              License (>=v2). Read the file COPYING that comes with
              GRASS for details.

Todo:
- Implement walking distance (r.walk)
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

##%flag
##% key: w
##% description: Use the use walking distance (r.walk) instead of cost distance (r.cost)
##% guisection: Settings
##%end

##%option
##% key: walk_coeff
##% type: string
##% description: Coefficients for walking energy formula parameters a,b,c,d
##% required : no
##% answer : 0.72,6.0,1.9998,-1.9998
##% guisection: Movement
##%end

##%option
##% key: lambda
##% type: float
##% description: Lambda coefficients for combining walking energy and friction cost
##% required : no
##% answer : 1.0
##% guisection: Movement
##%end

##%option
##% key: slope_factor
##% type: float
##% description: Slope factor determines travel energy cost per height step
##% required : no
##% answer : -0.2125
##% guisection: Movement
##%end

import atexit
import os
import sys
import string
import random
import subprocess
from io import BytesIO
import numpy as np
import grass.script as grass
from grass.pygrass.vector import VectorTopo
from grass.pygrass.vector.basic import Bbox
from grass.pygrass.raster.history import History
from grass.pygrass.vector.geometry import Centroid
from grass.pygrass.vector.geometry import Point
from grass.pygrass.vector.geometry import Line

# check if GRASS is running or not
if "GISBASE" not in os.environ:
    sys.exit("You must be in GRASS GIS to run this program")

# Define additional variables
# global TMP_PREFIX
TMP_PREFIX = grass.tempname(12)


def cleanup():
    """Remove temporary data"""
    grass.del_temp_region()
    tmp_maps = grass.read_command(
        "g.list",
        type=["vector", "raster"],
        pattern="{}*".format(TMP_PREFIX),
        separator=",",
    )

    if tmp_maps:
        grass.run_command(
            "g.remove",
            type=["vector", "raster"],
            pattern="{}*".format(TMP_PREFIX),
            quiet=True,
            flags="f",
        )


def main():
    """Do the main processing"""

    # Lazy import GDAL python bindings
    try:
        from osgeo import gdal, osr, ogr
    except ImportError as e:
        grass.fatal(_("Module requires GDAL python bindings: {}").format(e))

    # Parse input options:
    patch_map = options["input"]
    patches = patch_map.split("@")[0]
    patches_mapset = patch_map.split("@")[1] if len(patch_map.split("@")) > 1 else None
    pop_proxy = options["pop_proxy"]
    layer = options["layer"]
    costs = options["costs"]
    cutoff = float(options["cutoff"])
    border_dist = int(options["border_dist"])
    conefor_dir = options["conefor_dir"]
    memory = int(options["memory"])

    # Parse output options:
    prefix = options["prefix"]
    edge_map = "{}_edges".format(prefix)
    vertex_map = "{}_vertices".format(prefix)
    shortest_paths = "{}_shortest_paths".format(prefix)

    # Parse flags:
    p_flag = flags["p"]
    t_flag = flags["t"]
    r_flag = flags["r"]

    dist_flags = "kn" if flags["k"] else "n"

    lin_cat = 1
    zero_dist = None

    folder = grass.tempdir()
    if not os.path.exists(folder):
        os.makedirs(folder)

    # Setup counter for progress message
    counter = 0

    # Check if location is lat/lon (only in lat/lon geodesic distance
    # measuring is supported)
    if grass.locn_is_latlong():
        grass.verbose(
            "Location is lat/lon: Geodesic distance \
                      measure is used"
        )

    # Check if prefix is legal GRASS name
    if not grass.legal_name(prefix):
        grass.fatal(
            "{} is not a legal name for GRASS \
                    maps.".format(
                prefix
            )
        )

    if prefix[0].isdigit():
        grass.fatal(
            "Tables names starting with a digit are not SQL \
                    compliant.".format(
                prefix
            )
        )

    # Check if output maps not already exists or could be overwritten
    for output in [edge_map, vertex_map, shortest_paths]:
        if grass.db.db_table_exist(output) and not grass.overwrite():
            grass.fatal("Vector map <{}> already exists".format(output))

    # Check if input has required attributes
    in_db_connection = grass.vector.vector_db(patch_map)
    if not int(layer) in in_db_connection.keys():
        grass.fatal(
            "No attribute table connected vector map {} at \
                    layer {}.".format(
                patches, layer
            )
        )

    # Check if cat column exists
    pcols = grass.vector.vector_columns(patch_map, layer=layer)

    # Check if cat column exists
    if "cat" not in pcols.keys():
        grass.fatal(
            "Cannot find the reqired column cat in vector map \
                    {}.".format(
                patches
            )
        )

    # Check if pop_proxy column exists
    if pop_proxy not in pcols.keys():
        grass.fatal(
            "Cannot find column {} in vector map \
                    {}".format(
                pop_proxy, patches
            )
        )

    # Check if pop_proxy column is numeric type
    if not pcols[pop_proxy]["type"] in ["INTEGER", "REAL", "DOUBLE PRECISION"]:
        grass.fatal(
            "Column {} is of type {}. Only numeric types \
                    (integer or double precision) \
                    allowed!".format(
                pop_proxy, pcols[pop_proxy]["type"]
            )
        )

    # Check if pop_proxy column does not contain values <= 0
    pop_vals = np.fromstring(
        grass.read_command(
            "v.db.select", flags="c", map=patches, columns=pop_proxy, nv=-9999
        ).rstrip("\n"),
        dtype=float,
        sep="\n",
    )

    if np.min(pop_vals) <= 0:
        grass.fatal(
            "Column {} contains values <= 0 or NULL. Neither \
                    values <= 0 nor NULL allowed!}".format(
                pop_proxy
            )
        )

    ##############################################
    # Use pygrass region instead of grass.parse_command !?!
    start_reg = grass.parse_command("g.region", flags="ugp")

    max_n = start_reg["n"]
    min_s = start_reg["s"]
    max_e = start_reg["e"]
    min_w = start_reg["w"]
    # cost_nsres = reg['nsres']
    # cost_ewres = reg['ewres']

    # Rasterize patches
    # http://www.gdal.org/gdal_tutorial.html
    # http://geoinformaticstutorial.blogspot.no/2012/11/convert-
    # shapefile-to-raster-with-gdal.html
    if t_flag:
        # Rasterize patches with "all-touched" mode using GDAL
        # Read region-settings (not needed canuse max_n, min_s, max_e,
        # min_w nsres, ewres...
        prast = os.path.join(folder, "patches_rast.tif")

        # Check if GDAL-GRASS plugin is installed
        if ogr.GetDriverByName("GRASS"):
            # With GDAL-GRASS plugin
            # Locate file for patch vector map
            pfile = grass.parse_command(
                "g.findfile", element="vector", file=patches, mapset=patches_mapset
            )["file"]
            pfile = os.path.join(pfile, "head")

        else:
            # Without GDAL-GRASS-plugin
            grass.warning(
                "Cannot find GDAL-GRASS plugin. Consider \
                          installing it in order to save time for \
                          all-touched rasterisation"
            )
            pfile = os.path.join(folder, "patches_vect.gpkg")
            # Export patch vector map to temp-file in a GDAL-readable
            # format (shp)
            grass.run_command(
                "v.out.ogr",
                flags="m",
                quiet=True,
                input=patch_map,
                type="area",
                layer=layer,
                output=pfile,
                lco="GEOMETRY_NAME=geom",
            )

        # Rasterize vector map with all-touched option
        os.system(
            "gdal_rasterize -l {} -at -tr {} {} \
                  -te {} {} {} {} -ot Uint32 -a cat \
                  {} {} -q".format(
                patches,
                start_reg["ewres"],
                start_reg["nsres"],
                start_reg["w"],
                start_reg["s"],
                start_reg["e"],
                start_reg["n"],
                pfile,
                prast,
            )
        )

        if not ogr.GetDriverByName("GRASS"):
            # Remove vector temp-file
            os.remove(os.path.join(folder, "patches_vect.gpkg"))

        # Import rasterized patches
        grass.run_command(
            "r.external",
            flags="o",
            quiet=True,
            input=prast,
            output="{}_patches_pol".format(TMP_PREFIX),
        )

    else:
        # Simple rasterisation (only area)
        # in G 7.6 also with support for 'centroid'
        if float(grass.version()["version"][:3]) >= 7.6:
            conv_types = ["area", "centroid"]
        else:
            conv_types = ["area"]
        grass.run_command(
            "v.to.rast",
            quiet=True,
            input=patches,
            use="cat",
            type=conv_types,
            output="{}_patches_pol".format(TMP_PREFIX),
        )

    # Extract boundaries from patch raster map
    grass.run_command(
        "r.mapcalc",
        expression="{p}_patches_boundary=if(\
    {p}_patches_pol,\
    if((\
    (isnull({p}_patches_pol[-1,0])||| \
    {p}_patches_pol[-1,0]!={p}_patches_pol)||| \
    (isnull({p}_patches_pol[0,1])||| \
    {p}_patches_pol[0,1]!={p}_patches_pol)||| \
    (isnull({p}_patches_pol[1,0])||| \
    {p}_patches_pol[1,0]!={p}_patches_pol)||| \
    (isnull({p}_patches_pol[0,-1])||| \
    {p}_patches_pol[0,-1]!={p}_patches_pol)), \
    {p}_patches_pol,null()), null())".format(
            p=TMP_PREFIX
        ),
        quiet=True,
    )

    rasterized_cats = (
        grass.read_command(
            "r.category",
            separator="newline",
            map="{p}_patches_boundary".format(p=TMP_PREFIX),
        )
        .replace("\t", "")
        .strip("\n")
    )
    rasterized_cats = list(
        map(int, set([x for x in rasterized_cats.split("\n") if x != ""]))
    )

    # Init output vector maps if they are requested by user
    network = VectorTopo(edge_map)
    network_columns = [
        ("cat", "INTEGER PRIMARY KEY"),
        ("from_p", "INTEGER"),
        ("to_p", "INTEGER"),
        ("min_dist", "DOUBLE PRECISION"),
        ("dist", "DOUBLE PRECISION"),
        ("max_dist", "DOUBLE PRECISION"),
    ]
    network.open("w", tab_name=edge_map, tab_cols=network_columns)

    vertex = VectorTopo(vertex_map)
    vertex_columns = [
        ("cat", "INTEGER PRIMARY KEY"),
        (pop_proxy, "DOUBLE PRECISION"),
    ]
    vertex.open("w", tab_name=vertex_map, tab_cols=vertex_columns)

    if p_flag:
        # Init cost paths file for start-patch
        grass.run_command("v.edit", quiet=True, map=shortest_paths, tool="create")
        grass.run_command(
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

    start_region_bbox = Bbox(
        north=float(max_n), south=float(min_s), east=float(max_e), west=float(min_w)
    )
    vpatches = VectorTopo(patches, mapset=patches_mapset)
    vpatches.open("r", layer=int(layer))

    ###Loop through patches
    vpatch_ids = np.array(
        vpatches.features_to_wkb_list(feature_type="centroid", bbox=start_region_bbox),
        dtype=[("vid", "uint32"), ("cat", "uint32"), ("geom", "|S10")],
    )
    cats = set(vpatch_ids["cat"])
    n_cats = len(cats)
    if n_cats < len(vpatch_ids["cat"]):
        grass.verbose(
            "At least one MultiPolygon found in patch map.\n \
                      Using average coordinates of the centroids for \
                      visual representation of the patch."
        )

    for cat in cats:
        if cat not in rasterized_cats:
            grass.warning(
                "Patch {} has not been rasterized and will \
                          therefore not be treated as part of the \
                          network. Consider using t-flag or change \
                          resolution.".format(
                    cat
                )
            )

            continue
        grass.verbose(
            "Calculating connectivity-distances for patch \
                      number {}".format(
                cat
            )
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

            # Get centroid
            if not from_centroid:
                continue
        else:
            xcoords = []
            ycoords = []
            for f_p in from_vpatch["vid"]:
                from_centroid = Centroid(v_id=int(f_p), c_mapinfo=vpatches.c_mapinfo)
                xcoords.append(from_centroid.x)
                ycoords.append(from_centroid.y)

                # Get centroid
                if not from_centroid:
                    continue
            from_x = np.average(xcoords)
            from_y = np.average(ycoords)

        # Get BoundingBox
        from_bbox = grass.parse_command(
            "v.db.select", map=patch_map, flags="r", where="cat={}".format(cat)
        )

        attr_filter = vpatches.table.filters.select(pop_proxy)
        attr_filter = attr_filter.where("cat={}".format(cat))
        proxy_val = vpatches.table.execute().fetchone()

        # Prepare start patch
        start_patch = "{}_patch_{}".format(TMP_PREFIX, cat)
        reclass_rule = grass.encode("{} = 1\n* = NULL".format(cat))
        recl = grass.feed_command(
            "r.reclass",
            quiet=True,
            input="{}_patches_boundary".format(TMP_PREFIX),
            output=start_patch,
            rules="-",
        )
        recl.stdin.write(reclass_rule)
        recl.stdin.close()
        recl.wait()

        # Check if patch was rasterised (patches smaller raster resolution and close to larger patches may not be rasterised)
        # start_check = grass.parse_command('r.info', flags='r', map=start_patch)
        # start_check = grass.parse_command('r.univar', flags='g', map=start_patch)
        # print(start_check)
        """if start_check['min'] != '1':
            grass.warning('Patch {} has not been rasterized and will \
                          therefore not be treated as part of the \
                          network. Consider using t-flag or change \
                          resolution.'.format(cat))

            grass.run_command('g.remove', flags='f', vector=start_patch,
                              raster=start_patch, quiet=True)
            grass.del_temp_region()
            continue"""

        # Prepare stop patches
        ############################################
        reg = grass.parse_command(
            "g.region",
            flags="ug",
            quiet=True,
            raster=start_patch,
            n=float(from_bbox["n"]) + float(cutoff),
            s=float(from_bbox["s"]) - float(cutoff),
            e=float(from_bbox["e"]) + float(cutoff),
            w=float(from_bbox["w"]) - float(cutoff),
            align="{}_patches_pol".format(TMP_PREFIX),
        )

        north = reg["n"] if max_n > reg["n"] else max_n
        south = reg["s"] if min_s < reg["s"] else min_s
        east = reg["e"] if max_e < reg["e"] else max_e
        west = reg["w"] if min_w > reg["w"] else min_w

        # Set region to patch search radius
        grass.use_temp_region()
        grass.run_command(
            "g.region",
            quiet=True,
            n=north,
            s=south,
            e=east,
            w=west,
            align="{}_patches_pol".format(TMP_PREFIX),
        )

        # Create buffer around start-patch as a mask
        # for cost distance analysis
        grass.run_command(
            "r.buffer", quiet=True, input=start_patch, output="MASK", distances=cutoff
        )
        grass.run_command(
            "r.mapcalc",
            quiet=True,
            expression="{pf}_patch_{p}_neighbours_contur=\
                                     if({pf}_patches_boundary=={p},\
                                     null(),\
                                     {pf}_patches_boundary)".format(
                pf=TMP_PREFIX, p=cat
            ),
        )
        grass.run_command("r.mask", flags="r", quiet=True)

        # Calculate cost distance
        cost_distance_map = "{}_patch_{}_cost_dist".format(prefix, cat)
        grass.run_command(
            "r.cost",
            flags=dist_flags,
            quiet=True,
            overwrite=True,
            input=costs,
            output=cost_distance_map,
            start_rast=start_patch,
            memory=memory,
        )

        # grass.run_command('g.region', flags='up')
        # grass.raster.raster_history(cost_distance_map)
        cdhist = History(cost_distance_map)
        cdhist.clear()
        cdhist.creator = os.environ["USER"]
        cdhist.write()
        # History object cannot modify description
        grass.run_command(
            "r.support",
            map=cost_distance_map,
            description="Generated by r.connectivity.distance",
            history=os.environ["CMDLINE"],
        )

        # Export distance at boundaries
        maps = "{0}_patch_{1}_neighbours_contur,{2}_patch_{1}_cost_dist"
        maps = (maps.format(TMP_PREFIX, cat, prefix),)

        connections = grass.encode(
            grass.read_command(
                "r.stats", flags="1ng", quiet=True, input=maps, separator=";"
            ).rstrip("\n")
        )
        if connections:
            con_array = np.genfromtxt(
                BytesIO(connections),
                delimiter=";",
                dtype=None,
                names=["x", "y", "cat", "dist"],
            )
        else:
            grass.warning("No connections for patch {}".format(cat))

            # Write centroid to vertex map
            vertex.write(Point(from_x, from_y), cat=int(cat), attrs=proxy_val)
            vertex.table.conn.commit()

            # Remove temporary map data
            grass.run_command(
                "g.remove",
                quiet=True,
                flags="f",
                type=["raster", "vector"],
                pattern="{}*{}*".format(TMP_PREFIX, cat),
            )
            grass.del_temp_region()
            continue

        # Find closest points on neigbour patches
        to_cats = set(np.atleast_1d(con_array["cat"]))
        to_coords = []
        for to_cat in to_cats:
            connection = con_array[con_array["cat"] == to_cat]
            connection.sort(order=["dist"])
            pixel = (
                border_dist if len(connection) > border_dist else len(connection) - 1
            )
            # closest_points_x = connection['x'][pixel]
            # closest_points_y = connection['y'][pixel]
            closest_points_to_cat = to_cat
            closest_points_min_dist = connection["dist"][0]
            closest_points_dist = connection["dist"][pixel]
            closest_points_max_dist = connection["dist"][-1]
            to_patch_ids = vpatch_ids[vpatch_ids["cat"] == int(to_cat)]["vid"]

            if len(to_patch_ids) == 1:
                to_centroid = Centroid(v_id=to_patch_ids, c_mapinfo=vpatches.c_mapinfo)
                to_x = to_centroid.x
                to_y = to_centroid.y
            elif len(to_patch_ids) >= 1:
                xcoords = []
                ycoords = []
                for t_p in to_patch_ids:
                    to_centroid = Centroid(v_id=int(t_p), c_mapinfo=vpatches.c_mapinfo)
                    xcoords.append(to_centroid.x)
                    ycoords.append(to_centroid.y)

                    # Get centroid
                    if not to_centroid:
                        continue
                to_x = np.average(xcoords)
                to_y = np.average(ycoords)

            to_coords.append(
                "{},{},{},{},{},{}".format(
                    connection["x"][0],
                    connection["y"][0],
                    to_cat,
                    closest_points_min_dist,
                    closest_points_dist,
                    closest_points_max_dist,
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
        # vector map (r.drain limited to 1024 points) if requested
        if p_flag:
            grass.verbose(
                "Extracting shortest paths for patch number \
                          {}...".format(
                    cat
                )
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
                sp = grass.feed_command(
                    "v.in.ascii",
                    flags="nr",
                    overwrite=True,
                    quiet=True,
                    input="-",
                    stderr=subprocess.PIPE,
                    output="{}_{}_cp".format(TMP_PREFIX, cat),
                    separator=",",
                    columns="x double precision,\
                                           y double precision,\
                                           to_p integer,\
                                           dist_min double precision,\
                                           dist double precision,\
                                           dist_max double precision",
                )
                sp.stdin.write(grass.encode("\n".join(to_coords)))
                sp.stdin.close()
                sp.wait()

                # Extract shortest paths for start-patch in chunks of
                # 1024 points
                cost_paths = "{}_{}_cost_paths".format(TMP_PREFIX, cat)
                start_points = "{}_{}_cp".format(TMP_PREFIX, cat)
                grass.run_command(
                    "r.drain",
                    overwrite=True,
                    quiet=True,
                    input=cost_distance_map,
                    output=cost_paths,
                    drain=cost_paths,
                    start_points=start_points,
                )

                grass.run_command(
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
                grass.run_command(
                    "v.db.update",
                    map=cost_paths,
                    column="from_p",
                    value=cat,
                    quiet=True,
                )
                grass.run_command(
                    "v.distance",
                    quiet=True,
                    from_=cost_paths,
                    to=start_points,
                    upload="to_attr",
                    column="to_p",
                    to_column="to_p",
                )
                grass.run_command(
                    "v.db.join",
                    quiet=True,
                    map=cost_paths,
                    column="to_p",
                    other_column="to_p",
                    other_table=start_points,
                    subset_columns="dist_min,dist,dist_max",
                )

                # grass.run_command('v.info', flags='c',
                #                  map=cost_paths)
                grass.run_command(
                    "v.patch",
                    flags="ae",
                    overwrite=True,
                    quiet=True,
                    input=cost_paths,
                    output=shortest_paths,
                )

                # Remove temporary map data
                grass.run_command(
                    "g.remove",
                    quiet=True,
                    flags="f",
                    type=["raster", "vector"],
                    pattern="{}*{}*".format(TMP_PREFIX, cat),
                )

        # Remove temporary map data for patch
        if r_flag:
            grass.run_command(
                "g.remove", flags="f", type="raster", name=cost_distance_map, quiet=True
            )

        vertex.write(Point(from_x, from_y), cat=int(cat), attrs=proxy_val)

        vertex.table.conn.commit()

        # Print progress message
        grass.percent(i=int((float(counter) / n_cats) * 100), n=100, s=3)

        # Update counter for progress message
        counter = counter + 1

    if zero_dist:
        grass.warning(
            "Some patches are directly adjacent to others. \
                       Minimum distance set to 0.0000000001"
        )

    # Close vector maps and build topology
    network.close()
    vertex.close()

    # Add vertex attributes
    # grass.run_command('v.db.addtable', map=vertex_map)
    # grass.run_command('v.db.join', map=vertex_map, column='cat',
    #                   other_table=in_db_connection[int(layer)]['table'],
    #                   other_column='cat', subset_columns=pop_proxy,
    #                   quiet=True)

    # Add history and meta data to produced maps
    grass.run_command(
        "v.support",
        flags="h",
        map=edge_map,
        person=os.environ["USER"],
        cmdhist=os.environ["CMDLINE"],
    )

    grass.run_command(
        "v.support",
        flags="h",
        map=vertex_map,
        person=os.environ["USER"],
        cmdhist=os.environ["CMDLINE"],
    )

    if p_flag:
        grass.run_command(
            "v.support",
            flags="h",
            map=shortest_paths,
            person=os.environ["USER"],
            cmdhist=os.environ["CMDLINE"],
        )

    # Output also Conefor files if requested
    if conefor_dir:
        query = """SELECT p_from, p_to, avg(dist) FROM
                 (SELECT
                 CASE
                 WHEN from_p > to_p THEN to_p
                 ELSE from_p END AS p_from,
                    CASE
                 WHEN from_p > to_p THEN from_p
                 ELSE to_p END AS p_to,
                 dist
                 FROM {}) AS x
                 GROUP BY p_from, p_to""".format(
            edge_map
        )
        with open(
            os.path.join(conefor_dir, "undirected_connection_file"), "w"
        ) as edges:
            edges.write(grass.read_command("db.select", sql=query, separator=" "))
        with open(os.path.join(conefor_dir, "directed_connection_file"), "w") as edges:
            edges.write(
                grass.read_command(
                    "v.db.select", map=edge_map, separator=" ", flags="c"
                )
            )
        with open(os.path.join(conefor_dir, "node_file"), "w") as nodes:
            nodes.write(
                grass.read_command(
                    "v.db.select", map=vertex_map, separator=" ", flags="c"
                )
            )


if __name__ == "__main__":
    options, flags = grass.parser()
    atexit.register(cleanup)
    sys.exit(main())
