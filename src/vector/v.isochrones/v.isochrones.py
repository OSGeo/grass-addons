#!/usr/bin/env python
############################################################################
#
# MODULE:       v.isochrones
# AUTHOR:       Moritz Lennert
# PURPOSE:      Takes a map of roads and starting points and creates
#               isochrones around the starting points
#
# COPYRIGHT:    (c) 2014 Moritz Lennert, and the GRASS Development Team
#               This program is free software under the GNU General Public
#               License (>=v2). Read the file COPYING that comes with GRASS
#               for details.
#
#############################################################################

# %module
# % description: Creates isochrones from a road map and starting points
# % keyword: vector
# % keyword: network
# % keyword: isochrones
# %end
# %option G_OPT_V_MAP
# % label: Roads with speed attribute
# % required: yes
# %end
# %option G_OPT_V_FIELD
# % key: roads_layer
# % label: Layer number of the roads with relevant attributes
# % required: yes
# %end
# %option G_OPT_V_FIELD
# % key: node_layer
# % label: Layer number of the nodes on the network (for method=v.net.iso)
# % required: no
# % answer: 2
# % guisection: v.net.iso
# %end
# %option G_OPT_DB_COLUMN
# % key: cost_column
# % description: Name of speed attribute column (in km/h) or cost column (in minutes)
# % required: yes
# %end
# %option G_OPT_V_INPUT
# % key: start_points
# % label: Vector map with starting points for isochrones
# % required: yes
# %end
# %option G_OPT_V_OUTPUT
# % key: isochrones
# % label: Output vector map with isochrone polygons (Output prefix with flag -i)
# % required: yes
# %end
# %option
# % key: time_steps
# % type: double
# % description: Time steps of isochrones (in minutes)
# % multiple: yes
# % required: yes
# %end
# %option G_OPT_R_OUTPUT
# % key: timemap
# % label: Optional output raster map with continuous time from starting points
# % required: no
# % guisection: r.cost
# %end
# %option
# % key: offroad_speed
# % type: double
# % description: Speed for off-road areas (in km/h > 0)
# % required: no
# % answer: 5.0
# % guisection: r.cost
# %end
# %option
# % key: memory
# % description: Amount of memory (in MB) use
# % type: integer
# % required: no
# % answer: 300
# % guisection: r.cost
# %end
# %option
# % key: max_distance
# % type: double
# % description: Maximum distance (m) from network to include into isochrones
# % required: no
# % guisection: v.net.iso
# %end
# %option
# % key: method
# % description: Method to use for isochrone calculation
# % type: string
# % required: yes
# % options: v.net.iso,r.cost
# % answer: v.net.iso
# %end
# %flag
# % key: i
# % description: Create individual isochrone map for each starting point
# % guisection: v.net.iso
# %end


import os
import atexit
import math
import grass.script as grass

global isoraw
global isos_extract
global isos_extract_rast
global isos_grow_cat
global isos_grow_cat_int
global isos_grow_distance
global isos_grow_distance_recode
global isos_poly_all
global isos_final

isoraw = None
isos_extract = None
isos_extract_rast = None
isos_grow_cat = None
isos_grow_cat_int = None
isos_grow_distance = None
isos_grow_distance_recode = None
isos_poly_all = None
isos_final = None


def cleanup():

    if method == "r.cost":
        # remove temporary cost column from road map
        if grass.vector_db(roads)[int(layer)]["driver"] == "dbf":
            grass.run_command(
                "v.db.dropcolumn",
                layer=layer,
                map=roads,
                column=tmp_cost_column,
                quiet=True,
            )

        if grass.find_file(tmp_cost_map, element="cell")["name"]:
            grass.run_command(
                "g.remove", flags="f", type="raster", name=tmp_cost_map, quiet=True
            )
        if grass.find_file(tmp_time_map, element="cell")["name"]:
            grass.run_command(
                "g.remove", flags="f", type="raster", name=tmp_time_map, quiet=True
            )
        if grass.find_file(tmp_region_map, element="cell")["name"]:
            grass.run_command(
                "g.remove", flags="f", type="raster", name=tmp_region_map, quiet=True
            )

    elif method == "v.net.iso":
        if grass.find_file(isoraw, element="vector")["name"]:
            grass.run_command(
                "g.remove", flags="f", type="vector", name=isoraw, quiet=True
            )
        if grass.find_file(isos_extract, element="vector")["name"]:
            grass.run_command(
                "g.remove", flags="f", type="vector", name=isos_extract, quiet=True
            )
        if grass.find_file(isos_extract_rast, element="cell")["name"]:
            grass.run_command(
                "g.remove", flags="f", type="raster", name=isos_extract_rast, quiet=True
            )
        if grass.find_file(isos_grow_cat, element="cell")["name"]:
            grass.run_command(
                "g.remove", flags="f", type="raster", name=isos_grow_cat, quiet=True
            )
        if grass.find_file(isos_grow_cat_int, element="cell")["name"]:
            grass.run_command(
                "g.remove", flags="f", type="raster", name=isos_grow_cat_int, quiet=True
            )
        if grass.find_file(isos_grow_distance, element="cell")["name"]:
            grass.run_command(
                "g.remove",
                flags="f",
                type="raster",
                name=isos_grow_distance,
                quiet=True,
            )
        if grass.find_file(isos_grow_distance_recode, element="cell")["name"]:
            grass.run_command(
                "g.remove",
                flags="f",
                type="raster",
                name=isos_grow_distance_recode,
                quiet=True,
            )
        if grass.find_file(isos_poly_all, element="vector")["name"]:
            grass.run_command(
                "g.remove", flags="f", type="vector", name=isos_poly_all, quiet=True
            )
        if grass.find_file(isos_final, element="vector")["name"]:
            grass.run_command(
                "g.remove", flags="f", type="vector", name=isos_final, quiet=True
            )


def isocalc(isoraw):

    global isos_extract
    global isos_extract_rast
    global isos_grow_cat
    global isos_grow_cat_int
    global isos_grow_distance
    global isos_grow_distance_recode
    global isos_poly_all

    isos_extract = "isos_extract_%d" % os.getpid()
    isos_extract_rast = "isos_extract_rast_%d" % os.getpid()
    isos_grow_cat = "isos_grow_cat_%d" % os.getpid()
    isos_grow_cat_int = "isos_grow_cat_int_%d" % os.getpid()
    isos_grow_distance = "isos_grow_distance_%d" % os.getpid()
    isos_grow_distance_recode = "isos_grow_distance_recode_%d" % os.getpid()
    isos_poly_all = "isos_poly_all_%d" % os.getpid()

    grass.use_temp_region()

    grass.run_command(
        "v.extract",
        input_=isoraw,
        cat=output_cats[0:-1],
        output=isos_extract,
        overwrite=True,
    )
    grass.run_command("g.region", vect=isos_extract, flags="a")
    grass.run_command(
        "v.to.rast",
        input_=isos_extract,
        use="cat",
        output=isos_extract_rast,
        overwrite=True,
    )
    grass.run_command(
        "r.grow.distance",
        input=isos_extract_rast,
        value=isos_grow_cat,
        distance=isos_grow_distance,
        flags="m",
        overwrite=True,
    )
    grass.mapcalc(isos_grow_cat_int + " = int(" + isos_grow_cat + ")")
    if max_distance:
        recode_str = "0:%f:1\n%f:*:0" % (max_distance, max_distance)
        grass.write_command(
            "r.recode",
            input_=isos_grow_distance,
            output=isos_grow_distance_recode,
            rules="-",
            stdin=recode_str,
            overwrite=True,
        )
        grass.run_command(
            "r.mask", raster=isos_grow_distance_recode, maskcats=1, overwrite=True
        )
    grass.run_command(
        "r.to.vect",
        input_=isos_grow_cat_int,
        output=isos_poly_all,
        type_="area",
        flags="sv",
        overwrite=True,
    )
    grass.run_command(
        "v.extract", input_=isos_poly_all, output=isos_final, cats=output_cats[0:-1]
    )
    if max_distance:
        grass.run_command("r.mask", flags="r")


def main():

    # Input for all methods
    global roads
    roads = options["map"]
    global layer
    layer = options["roads_layer"]
    node_layer = options["node_layer"]
    cost_column = options["cost_column"]
    start_points = options["start_points"]
    time_steps = options["time_steps"].split(",")
    isochrones = options["isochrones"]
    global method
    method = options["method"]

    if method == "r.cost":
        offroad_speed = float(options["offroad_speed"])
        if offroad_speed == 0:
            grass.message(_("Offroad speed has to be > 0. Set to 0.00001."))
            offroad_speed = 0.00001

        memory = int(options["memory"])
        # Output
        if options["timemap"]:
            timemap = options["timemap"]
        else:
            timemap = None

        global tmp_cost_map
        global tmp_time_map
        global tmp_region_map
        global tmp_cost_column

        tmp_cost_map = "cost_map_tmp_%d" % os.getpid()
        tmp_time_map = "time_map_tmp_%d" % os.getpid()
        tmp_region_map = "region_map_tmp_%d" % os.getpid()

        # get current resolution
        region = grass.region()
        resolution = math.sqrt(float(region["nsres"]) * float(region["ewres"]))

        if grass.vector_db(roads)[int(layer)]["driver"] == "dbf":
            # add cost column to road vector
            tmp_cost_column = "tmp%d" % os.getpid()
            def_cost_column = tmp_cost_column + " DOUBLE PRECISION"
            grass.run_command(
                "v.db.addcolumn",
                map=roads,
                layer=layer,
                column=def_cost_column,
                quiet=True,
            )

            # calculate cost (in minutes) depending on speed
            # (resolution/(speed (in km/h) * 1000 / 60))
            query_value = "%s / (%s * 1000 / 60)" % (resolution, cost_column)
            grass.run_command(
                "v.db.update", map=roads, column=tmp_cost_column, qcolumn=query_value
            )
        else:
            tmp_cost_column = "%s / (%s * 1000 / 60)" % (resolution, cost_column)

        # transform to raster
        grass.run_command(
            "v.to.rast",
            input=roads,
            output=tmp_cost_map,
            use="attr",
            attrcolumn=tmp_cost_column,
            type="line",
            memory=memory,
        )

        # replace null values with cost for off-road areas
        # (resolution/(off-road speed * 1000 / 60))
        null_value = resolution / (offroad_speed * 1000 / 60)
        grass.run_command("r.null", map=tmp_cost_map, null=null_value)

        # limit the cumulated cost surface calculation to the max time distance
        # requested
        max_cost = time_steps[-1]

        # calculate time distance from starting points
        grass.run_command(
            "r.cost",
            input=tmp_cost_map,
            start_points=start_points,
            output=tmp_time_map,
            max_cost=max_cost,
            memory=memory,
        )

        if timemap:
            grass.run_command("g.copy", raster=(tmp_time_map, timemap))
            grass.run_command("r.colors", map=timemap, color="grey", flags="ne")

        # recode time distance to time steps
        recode_rules = "0:%s:%s\n" % (time_steps[0], time_steps[0])
        for count in range(1, len(time_steps)):
            recode_rules += time_steps[count - 1] + ":"
            recode_rules += time_steps[count] + ":"
            recode_rules += time_steps[count] + "\n"

        grass.write_command(
            "r.recode",
            input=tmp_time_map,
            output=tmp_region_map,
            rules="-",
            stdin=recode_rules,
        )

        # transform to vector areas
        grass.run_command(
            "r.to.vect",
            input=tmp_region_map,
            output=isochrones,
            type="area",
            column="traveltime",
            flags="s",
        )

        # give the polygons a default color table
        grass.run_command(
            "v.colors", map=isochrones, use="attr", column="traveltime", color="grey"
        )

    elif method == "v.net.iso":
        global max_distance
        if options["max_distance"]:
            max_distance = float(options["max_distance"])
        else:
            max_distance = None
        global output_cats
        output_cats = []
        for i in range(1, len(time_steps) + 2):
            output_cats.append(i)
        startpoints = grass.read_command(
            "v.distance",
            from_=start_points,
            to=roads,
            to_type="point",
            to_layer=node_layer,
            upload="cat",
            flags="p",
            quiet=True,
        ).split("\n")[1:-1]

        global isoraw
        isoraw = "isoraw_temp_%d" % os.getpid()
        global isos_final
        isos_final = "isos_final_%d" % os.getpid()

        if flags["i"]:
            for point in startpoints:
                startpoint_cat = point.split("|")[0]
                startnode_cat = point.split("|")[1]
                grass.run_command(
                    "v.net.iso",
                    input_=roads,
                    output=isoraw,
                    center_cats=startnode_cat,
                    costs=time_steps,
                    arc_column=cost_column,
                    overwrite=True,
                )
                isocalc(isoraw)
                outname = isochrones + "_" + startpoint_cat
                grass.run_command("g.rename", vect=isos_final + "," + outname)
                # give the polygons a default color table
                grass.run_command("v.colors", map=outname, use="cat", color="grey")

        else:
            startnodes = []
            for point in startpoints:
                startnodes.append(point.split("|")[1])
            grass.run_command(
                "v.net.iso",
                input_=roads,
                output=isoraw,
                center_cats=startnodes,
                costs=time_steps,
                arc_column=cost_column,
                overwrite=True,
            )
            isocalc(isoraw)
            grass.run_command("g.rename", vect=isos_final + "," + isochrones)
            # give the polygons a default color table
            grass.run_command("v.colors", map=isochrones, use="cat", color="grey")

    else:
        grass.fatal(_("You need to chose at least one of the methods"))


if __name__ == "__main__":
    options, flags = grass.parser()
    atexit.register(cleanup)
    main()
