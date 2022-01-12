#!/usr/bin/env python
#
############################################################################
#
# MODULE:		FIDIMO Fish Dispersal Model for River Networks for GRASS 7
#
# AUTHOR(S):		Johannes Radinger
#
# VERSION:		V0.1 Beta
#
# DATE:			2013-04-11
#
#############################################################################
#%Module
#% description: Calculating fish dispersal in a river network from source populations with species specific dispersal parameters
#% keyword: Fish Dispersal Model
#%End
#%option
#% key: river
#% type: string
#% gisprompt: old,cell,raster
#% description: River network (raster, e.g. output from r.watershed)
#% required: no
#% guisection: Stream parameters
#%end
#%option
#% key: coors
#% type: string
#% required: no
#% multiple: no
#% key_desc: x,y
#% description: River networks' outlet coordinates: E,N
#% guisection: Stream parameters
#%End
#%option
#% key: barriers
#% type: string
#% gisprompt:old,vector,vector
#% description: Barrier point file (vector map)
#% required: no
#% guisection: Stream parameters
#%end
#%option
#% key: passability_col
#% type: string
#% required: no
#% multiple: no
#% key_desc: name
#% description: Column name indicating passability value (0-1) of barrier
#% guisection: Stream parameters
#%End
#%option
#% key: n_source
#% type: string
#% key_desc: number[%]
#% description: Either: Number of random cells with source populations
#% required: no
#% guisection: Source populations
#%end
#%option
#% key: source_populations
#% type: string
#% gisprompt: old,cell,raster
#% description: Or: Source population raster (relative or absolute occurrence)
#% required: no
#% guisection: Source populations
#%end
#%Option
#% key: species
#% type: string
#% required: no
#% multiple: no
#% options:Custom species,Catostomus commersoni,Moxostoma duquesnii,Moxostoma erythrurum,Ambloplites rupestris,Lepomis auritus,Lepomis cyanellus,Lepomis macrochirus,Lepomis megalotis,Micropterus dolomieui,Micropterus punctulatus,Micropterus salmoides,Pomoxis annularis,Cottus bairdii,Cottus gobio,Abramis brama,Barbus barbus,Cyprinus carpio carpio,Gobio gobio,Leuciscus idus,Rutilus rutilus,Squalius cephalus,Tinca tinca,Esox lucius,Fundulus heteroclitus heteroclitus,Ameiurus natalis,Ictalurus punctatus,Morone americana,Etheostoma flabellare,Etheostoma nigrum,Perca fluviatilis,Percina nigrofasciata,Sander lucioperca,Oncorhynchus mykiss, Oncorhynchus gilae,Salmo salar,Salmo trutta fario,Salvelinus fontinalis,Salvelinus malma malma,Thymallus thymallus,Aplodinotus grunniens,Salmo trutta,Gobio gobio,Rutilus rutilus
#% description: Select fish species
#% guisection: Dispersal parameters
#%End
#%Option
#% key: l
#% type: integer
#% required: no
#% multiple: no
#% description: Fish Length [mm] (If no species is given, range=39-810)
#% guisection: Dispersal parameters
#%End
#%Option
#% key: ar
#% type: double
#% required: no
#% multiple: no
#% description: Aspect Ratio of Caudal Fin (If no species is given) (valid range 0.51 - 2.29)
#% guisection: Dispersal parameters
#%End
#%Option
#% key: t
#% type: integer
#% required: no
#% multiple: no
#% description: Time interval for model step [d]
#% guisection: Dispersal parameters
#% options: 1-3650
#% answer: 30
#%End
#%option
#% key: p
#% type: double
#% required: no
#% multiple: no
#% description: Share of the stationary component (valid range 0 - 1)
#% answer:0.67
#% guisection: Dispersal parameters
#%End
#%option
#% key: habitat_attract
#% type: string
#% gisprompt: old,cell,raster
#% description: Attractiveness of habitat used as weighting factor (sink effect, habitat-dependent dispersal)
#% required: no
#% guisection: Habitat dependency
#%end
#%option
#% key: habitat_p
#% type: string
#% gisprompt: old,cell,raster
#% description: Spatially varying and habitat-dependent p factor (float: 0-1, source effect, habitat-dependent dispersal)
#% required: no
#% guisection: Habitat dependency
#%end
#%Flag
#% key: b
#% description: Don't keep basic vector maps (source_points, barriers)
#%end
#%Flag
#% key: a
#% description: Keep all temporal vector and raster maps
#%end
#%Flag
#% key: r
#% description: Source population input are real fish counts per cell. Backtransformation into fish counts will be performed.
#%end
#%Option
#% key: truncation
#% type: string
#% required: no
#% multiple: no
#% options: 0.9,0.95,0.99,0.995,0.999,0.99999,0.999999999,inf
#% description: kernel truncation criterion (precision)
#% answer: 0.99
#% guisection: Optional
#%End
#%Option
#% key: seed1
#% type: integer
#% required: no
#% multiple: no
#% description: fixed seed for generating dispersal parameters
#% guisection: Optional
#%End
#%Option
#% key: seed2
#% type: integer
#% required: no
#% multiple: no
#% description: fixed seed for multinomial realisation step
#% guisection: Optional
#%End
#%Option
#% key: output
#% type: string
#% gisprompt: new
#% required: no
#% multiple: no
#% key_desc: name
#% description: Base name for output raster
#% guisection: Output
#% answer: fidimo_out
#%end
#%Option
#% key: statistical_interval
#% type: string
#% required: no
#% multiple: no
#% key_desc: name
#% description: Statistical Intervals
#% guisection: Output
#% options:no,Confidence Interval,Prediction Interval,Random Value within Confidence Interval
#% answer:no
#%end


# import required base modules
import sys
import os
import atexit
import time
import sqlite3
import math  # for function sqrt()
import csv
import random

# import required grass modules
import grass.script as grass
import grass.script.setup as gsetup
import grass.script.array as garray

# lazy imports: numpy and scipy


tmp_map_rast = None
tmp_map_vect = None


def cleanup():
    if (tmp_map_rast or tmp_map_vect) and not flags["a"]:
        grass.run_command(
            "g.remove",
            flags="f",
            type="raster",
            name=[f + str(os.getpid()) for f in tmp_map_rast],
            quiet=True,
        )
        grass.run_command(
            "g.remove",
            flags="f",
            type="vector",
            name=[f + str(os.getpid()) for f in tmp_map_vect],
            quiet=True,
        )


def main():

    # lazy import required numpy and scipy modules
    import numpy
    from scipy import stats
    from scipy import optimize

    ############ DEFINITION CLEANUP TEMPORARY FILES ##############
    # global variables for cleanup
    global tmp_map_rast
    global tmp_map_vect

    tmp_map_rast = [
        "density_final_",
        "density_final_corrected_",
        "density_from_point_tmp_",
        "density_from_point_unmasked_tmp_",
        "distance_from_point_tmp_",
        "distance_raster_tmp_",
        "distance_raster_buffered_tmp_",
        "distance_raster_buffered_div_tmp_",
        "distance_raster_grow_tmp_",
        "division_overlay_tmp_",
        "downstream_drain_tmp_",
        "drainage_tmp_",
        "flow_direction_tmp_",
        "lower_distance_tmp_",
        "realised_density_final_",
        "rel_upstream_shreve_tmp_",
        "river_raster_cat_tmp_",
        "river_raster_tmp_",
        "river_raster_combine_tmp_",
        "river_raster_buffer_tmp_",
        "river_raster_grow_start_tmp_",
        "river_raster_nearest_tmp_",
        "shreve_tmp_",
        "source_populations_scalar_tmp_",
        "source_populations_scalar_corrected_tmp_",
        "strahler_tmp_",
        "stream_rwatershed_tmp_",
        "upper_distance_tmp_",
        "upstream_part_tmp_",
        "upstream_shreve_tmp_",
    ]

    tmp_map_vect = [
        "river_points_tmp_",
        "river_vector_tmp_",
        "river_vector_nocat_tmp_",
        "source_points_",
    ]

    if options["barriers"]:
        tmp_map_rast = tmp_map_rast + [
            "downstream_barrier_density_tmp_",
            "distance_barrier_tmp_",
            "distance_downstream_barrier_tmp_",
            "distance_upstream_point_tmp_",
            "inv_distance_downstream_barrier_tmp_",
            "lower_distance_barrier_tmp_",
            "upper_distance_barrier_tmp_",
            "upstream_barrier_tmp_",
            "upstream_barrier_density_tmp_",
        ]
        tmp_map_vect = tmp_map_vect + ["barriers_", "barriers_tmp_"]

    ############ PARAMETER INPUT ##############
    # Stream parameters input
    river = options["river"]
    coors = options["coors"]

    # Barrier input
    if options["barriers"]:
        input_barriers = options["barriers"].split("@")[0]
        # check if barrier file exists in current mapset (Problem when file in other mapset!!!!)
        if not grass.find_file(name=input_barriers, element="vector")["file"]:
            grass.fatal(_("Barriers map not found in current mapset"))
        # check if passability_col is provided and existing
        if not options["passability_col"]:
            grass.fatal(
                _(
                    "Please provide column name that holds the barriers' passability values ('passability_col')"
                )
            )
        if not options["passability_col"] in grass.read_command(
            "db.columns", table=input_barriers
        ).split("\n"):
            grass.fatal(
                _(
                    "Please provide correct column name that holds the barriers' passability values ('passability_col')"
                )
            )
        passability_col = options["passability_col"]

    # Source population input
    if (options["source_populations"] and options["n_source"]) or (
        str(options["source_populations"]) == "" and str(options["n_source"]) == ""
    ):
        grass.fatal(_("Provide either fixed or random source population"))
    if options["n_source"] and flags["r"]:
        grass.fatal(
            _(
                "Realisation (flag: 'r') in combination with random source populations (n_source) not possible. Please choose either random source populations or provide source populations to calculate realisation"
            )
        )

    n_source = options["n_source"]  # number of random source points
    source_populations = options["source_populations"]

    # Habitat attractiveness maps
    if options["habitat_attract"]:
        habitat_attract = options["habitat_attract"]

    # multiplication value as workaround for very small FLOAT values
    # important for transformation of source population raster into point vector
    scalar = 10000

    # Statistical interval
    if str(options["statistical_interval"]) == "Prediction Interval":
        interval = "prediction"
    else:
        interval = "confidence"

    # Output
    output_fidimo = options["output"]
    if (
        grass.find_file(name=output_fidimo + "_" + "fit", element="cell")["file"]
        and not grass.overwrite()
    ):
        grass.fatal(
            _(
                "Output file exists already, either change output name or set overwrite-flag"
            )
        )

    ############ FISHMOVE ##############

    # import required rpy2 module
    import rpy2.robjects as robjects
    from rpy2.robjects.packages import importr

    fm = importr("fishmove")

    # Dispersal parameter input
    if str(options["species"] != "Custom species") and (options["l"] or options["ar"]):
        grass.message(_("Species settings will be overwritten with l and ar"))
    species = str(options["species"])
    if options["l"]:
        l = float(options["l"])
    if options["ar"]:
        ar = float(options["ar"])
    t = float(options["t"])
    # Setting Stream order to a vector of 1:9 and calculate fishmove for all streamorders at once
    so = robjects.IntVector((1, 2, 3, 4, 5, 6, 7, 8, 9))
    m = 0  # m-parameter in dispersal function

    # Share of mobile/stationary individuals
    if options["habitat_p"] or (options["p"] and options["habitat_p"]):
        grass.message(
            _("Map of habitat dependent share of mobile/stationary will be used")
        )
        habitat_p = options["habitat_p"]
    elif float(options["p"]) >= 0 and float(options["p"]) < 1:
        p_fixed = float(options["p"])
    else:
        grass.fatal(_("Valid range for p: 0 - 1"))

    ##### Calculating 'fishmove' depending on species or L & AR
    # Set fixed seed if specified
    if options["seed1"]:
        seed = ",seed=" + str(options["seed1"])
    else:
        seed = ""

    if species == "Custom species":
        fishmove = eval(
            "fm.fishmove(L=l,AR=ar,SO=so,T=t,interval=interval,rep=200%s)" % (seed)
        )
    else:
        fishmove = eval(
            "fm.fishmove(L=l,AR=ar,SO=so,T=t,interval=interval,rep=200%s)" % (seed)
        )

    # using only part of fishmove results (only regression coeffients)
    fishmove = fishmove[1]
    nrun = ["fit", "lwr", "upr"]

    ############ REGION, DB-CONNECTION ##############
    # Setting region to extent of input River
    grass.run_command(
        "g.region", flags="a", rast=river, overwrite=True, save="region_Fidimo"
    )

    # Getting resultion, res=cellsize
    res = int(
        grass.read_command("g.region", flags="m").strip().split("\n")[4].split("=")[1]
    )

    # database-connection
    env = grass.gisenv()
    gisdbase = env["GISDBASE"]
    location = env["LOCATION_NAME"]
    mapset = env["MAPSET"]
    grass.run_command(
        "db.connect",
        driver="sqlite",
        database="$GISDBASE/$LOCATION_NAME/$MAPSET/sqlite.db",
    )
    database = sqlite3.connect(os.path.join(gisdbase, location, mapset, "sqlite.db"))
    db = database.cursor()

    #############################################
    #############################################

    ################ Preparation River Raster (Distance-Raster) ################

    # Populate input-river (raster) with value of resolution
    # *1.0 to get float raster instead of integer
    grass.mapcalc(
        "$river_raster = if(!isnull($river),$res*1.0,null())",
        river_raster="river_raster_tmp_%d" % os.getpid(),
        river=river,
        res=res,
        overwrite=True,
    )

    # Converting river_raster to river_vector
    grass.run_command(
        "r.to.vect",
        overwrite=True,
        input="river_raster_tmp_%d" % os.getpid(),
        output="river_vector_tmp_%d" % os.getpid(),
        type="line",
    )

    # Converting river_raster to river_point
    grass.run_command(
        "r.to.vect",
        overwrite=True,
        input="river_raster_tmp_%d" % os.getpid(),
        output="river_points_tmp_%d" % os.getpid(),
        type="point",
    )

    # Prepare Barriers/Snap barriers to river_vector
    if options["barriers"]:
        grass.run_command(
            "g.copy", vector=input_barriers + "," + "barriers_tmp_%d" % os.getpid()
        )

        grass.run_command(
            "v.db.addcolumn",
            map="barriers_tmp_%d" % os.getpid(),
            columns="adj_X DOUBLE, adj_Y DOUBLE",
        )
        grass.run_command(
            "v.distance",
            overwrite=True,
            from_="barriers_tmp_%d" % os.getpid(),
            to="river_vector_tmp_%d" % os.getpid(),
            upload="to_x,to_y",
            column="adj_X,adj_Y",
        )
        grass.run_command(
            "v.in.db",
            overwrite=True,
            table="barriers_tmp_%d" % os.getpid(),
            x="adj_X",
            y="adj_Y",
            key="cat",
            output="barriers_%d" % os.getpid(),
        )
        grass.run_command(
            "v.db.addcolumn", map="barriers_%d" % os.getpid(), columns="dist DOUBLE"
        )
        # Making barriers permanent
        grass.run_command(
            "g.copy",
            vector="barriers_%d" % os.getpid() + "," + output_fidimo + "_barriers",
        )

        # Breaking river_vector at position of barriers to get segments
        for adj_X, adj_Y in db.execute(
            "SELECT adj_X, adj_Y FROM barriers_%d" % os.getpid()
        ):
            barrier_coors = str(adj_X) + "," + str(adj_Y)

            grass.run_command(
                "v.edit",
                map="river_vector_tmp_%d" % os.getpid(),
                tool="break",
                thresh="1,0,0",
                coords=barrier_coors,
            )

    # Getting category values (ASC) for river_network segments
    grass.run_command(
        "v.category",
        overwrite=True,
        input="river_vector_tmp_%d" % os.getpid(),
        option="del",
        output="river_vector_nocat_tmp_%d" % os.getpid(),
    )
    grass.run_command(
        "v.category",
        overwrite=True,
        input="river_vector_nocat_tmp_%d" % os.getpid(),
        option="add",
        output="river_vector_tmp_%d" % os.getpid(),
    )

    # Check if outflow coors are on river
    # For GRASS7 snap coors to river. Check r.stream.snap - add on
    # !!!!!!

    # Calculation of distance from outflow and flow direction for total river
    grass.run_command(
        "r.cost",
        flags="n",
        overwrite=True,
        input="river_raster_tmp_%d" % os.getpid(),
        output="distance_raster_tmp_%d" % os.getpid(),
        start_coordinates=coors,
    )

    largest_cost_value = grass.raster_info("distance_raster_tmp_%d" % os.getpid())[
        "max"
    ]

    # buffer
    grass.run_command(
        "r.grow.distance",
        overwrite=True,
        input="distance_raster_tmp_%d" % os.getpid(),
        value="river_raster_nearest_tmp_%d" % os.getpid(),
    )

    # get value of the nearest river cell
    grass.run_command(
        "r.grow",
        overwrite=True,
        input="distance_raster_tmp_%d" % os.getpid(),
        output="distance_raster_grow_tmp_%d" % os.getpid(),
        radius=2.01,
        old=1,
        new=largest_cost_value * 2,
    )

    # remove buffer for start
    grass.mapcalc(
        "$river_raster_grow_start_tmp = if($river_raster_nearest_tmp==0,null(),$distance_raster_grow_tmp)",
        river_raster_grow_start_tmp="river_raster_grow_start_tmp_%d" % os.getpid(),
        river_raster_nearest_tmp="river_raster_nearest_tmp_%d" % os.getpid(),
        distance_raster_grow_tmp="distance_raster_grow_tmp_%d" % os.getpid(),
    )

    # grow by one cell to make sure that the start point is the only cell
    grass.run_command(
        "r.grow",
        overwrite=True,
        input="river_raster_grow_start_tmp_%d" % os.getpid(),
        output="river_raster_buffer_tmp_%d" % os.getpid(),
        radius=1.01,
        old=largest_cost_value * 2,
        new=largest_cost_value * 2,
    )

    # patch river raster with buffer
    grass.run_command(
        "r.patch",
        overwrite=True,
        input="distance_raster_tmp_%d,river_raster_buffer_tmp_%d"
        % (os.getpid(), os.getpid()),
        output="distance_raster_buffered_tmp_%d" % os.getpid(),
    )

    # Get maximum value and divide if to large (>2200000)
    max_buffer = grass.raster_info("distance_raster_buffered_tmp_%d" % os.getpid())[
        "max"
    ]

    if max_buffer > 2100000:
        grass.message(
            _(
                "River network is very large and r.watershed (and e.g stream order extract) might not work"
            )
        )
        grass.mapcalc(
            "$distance_raster_buffered_div = $distance_raster_buffered/1000.0",
            distance_raster_buffered_div="distance_raster_buffered_div_tmp_%d"
            % os.getpid(),
            distance_raster_buffered="distance_raster_buffered_tmp_%d" % os.getpid(),
        )
        # Getting flow direction and stream segments
        grass.run_command(
            "r.watershed",
            flags="m",  # depends on memory!! #
            elevation="distance_raster_buffered_div_tmp_%d" % os.getpid(),
            drainage="drainage_tmp_%d" % os.getpid(),
            stream="stream_rwatershed_tmp_%d" % os.getpid(),
            threshold=3,
            overwrite=True,
        )

    else:
        # Getting flow direction and stream segments
        grass.run_command(
            "r.watershed",
            flags="m",  # depends on memory!! #
            elevation="distance_raster_buffered_tmp_%d" % os.getpid(),
            drainage="drainage_tmp_%d" % os.getpid(),
            stream="stream_rwatershed_tmp_%d" % os.getpid(),
            threshold=3,
            overwrite=True,
        )

    grass.mapcalc(
        "$flow_direction_tmp = if($stream_rwatershed_tmp,$drainage_tmp,null())",
        flow_direction_tmp="flow_direction_tmp_%d" % os.getpid(),
        stream_rwatershed_tmp="stream_rwatershed_tmp_%d" % os.getpid(),
        drainage_tmp="drainage_tmp_%d" % os.getpid(),
    )

    # Stream segments depicts new river_raster (corrected for small tributaries of 1 cell)
    grass.mapcalc(
        "$river_raster_combine_tmp = if(!isnull($stream_rwatershed_tmp) && !isnull($river_raster_tmp),$res*1.0,null())",
        river_raster_combine_tmp="river_raster_combine_tmp_%d" % os.getpid(),
        river_raster_tmp="river_raster_tmp_%d" % os.getpid(),
        stream_rwatershed_tmp="stream_rwatershed_tmp_%d" % os.getpid(),
        res=res,
    )
    grass.run_command(
        "g.copy",
        overwrite=True,
        raster="river_raster_combine_tmp_%d" % os.getpid() + ","
        "river_raster_tmp_%d" % os.getpid(),
    )

    # Calculation of stream order (Shreve/Strahler)
    grass.run_command(
        "r.stream.order",
        stream_rast="stream_rwatershed_tmp_%d" % os.getpid(),
        direction="flow_direction_tmp_%d" % os.getpid(),
        shreve="shreve_tmp_%d" % os.getpid(),
        strahler="strahler_tmp_%d" % os.getpid(),
        overwrite=True,
    )

    ################ Preparation Source Populations ################
    # Defining source points either as random points in the river or from input raster
    if options["n_source"]:
        grass.run_command(
            "r.random",
            overwrite=True,
            input="river_raster_tmp_%d" % os.getpid(),
            n=n_source,
            vector_output="source_points_%d" % os.getpid(),
        )
        grass.run_command(
            "v.db.addcolumn",
            map="source_points_%d" % os.getpid(),
            columns="n_fish INT, prob_scalar DOUBLE",
        )

        # Set starting probability of occurrence to 1.0*scalar for all random source_points
        grass.write_command(
            "db.execute",
            input="-",
            stdin="UPDATE source_points_%d SET prob_scalar=%d"
            % (os.getpid(), scalar * 1.0),
        )
        grass.write_command(
            "db.execute",
            input="-",
            stdin="UPDATE source_points_%d SET n_fish=%d" % (os.getpid(), 1.0),
        )

    # if source population raster is provided, then use it, transform raster in vector points
    # create an attribute column "prob_scalar" and "n_fish" and update it with the values from the raster map
    if options["source_populations"]:
        # Multiplying source probability with very large scalar to avoid problems
        # with very small floating points (problem: precision of FLOAT); needs retransforamtion in the end
        grass.mapcalc(
            "$source_populations_scalar_tmp = $source_populations*$scalar",
            source_populations=source_populations,
            source_populations_scalar_tmp="source_populations_scalar_tmp_%d"
            % os.getpid(),
            scalar=scalar,
        )

        # Exclude source Populations that are outside the river_raster
        grass.mapcalc(
            "$source_populations_scalar_corrected_tmp = if($river_raster_tmp,$source_populations_scalar_tmp)",
            source_populations_scalar_corrected_tmp="source_populations_scalar_corrected_tmp_%d"
            % os.getpid(),
            river_raster_tmp="river_raster_tmp_%d" % os.getpid(),
            source_populations_scalar_tmp="source_populations_scalar_tmp_%d"
            % os.getpid(),
        )

        # Convert to source population points
        grass.run_command(
            "r.to.vect",
            overwrite=True,
            input="source_populations_scalar_corrected_tmp_%d" % os.getpid(),
            output="source_points_%d" % os.getpid(),
            type="point",
        )
        grass.run_command(
            "v.db.addcolumn",
            map="source_points_%d" % os.getpid(),
            columns="n_fish INT, prob_scalar DOUBLE",
        )

        # populate n_fish and sample prob from input source_populations raster (multiplied by scalar)
        if flags["r"]:
            grass.run_command(
                "v.what.rast",
                map="source_points_%d" % os.getpid(),
                raster=source_populations,
                column="n_fish",
            )

        grass.run_command(
            "v.what.rast",
            map="source_points_%d" % os.getpid(),
            raster="source_populations_scalar_tmp_%d" % os.getpid(),
            column="prob_scalar",
        )

    # Adding columns and coordinates to source points
    grass.run_command(
        "v.db.addcolumn",
        map="source_points_%d" % os.getpid(),
        columns="X DOUBLE, Y DOUBLE, segment INT, Strahler INT, habitat_attract DOUBLE, p DOUBLE",
    )
    grass.run_command(
        "v.to.db",
        map="source_points_%d" % os.getpid(),
        type="point",
        option="coor",
        columns="X,Y",
    )

    # Convert river from vector to raster format and get cat-value
    grass.run_command(
        "v.to.rast",
        input="river_vector_tmp_%d" % os.getpid(),
        overwrite=True,
        output="river_raster_cat_tmp_%d" % os.getpid(),
        use="cat",
    )

    # Adding information of segment to source points
    grass.run_command(
        "v.what.rast",
        map="source_points_%d" % os.getpid(),
        raster="river_raster_cat_tmp_%d" % os.getpid(),
        column="segment",
    )

    # Adding information of Strahler stream order to source points
    grass.run_command(
        "v.what.rast",
        map="source_points_%d" % os.getpid(),
        raster="strahler_tmp_%d" % os.getpid(),
        column="Strahler",
    )

    # Adding information of habitat attractiveness to source points
    if options["habitat_attract"]:
        grass.run_command(
            "v.what.rast",
            map="source_points_%d" % os.getpid(),
            raster=habitat_attract,
            column="habitat_attract",
        )

    # Adding information of p (share of stationary/mobiles) to source points
    if options["habitat_p"]:
        grass.run_command(
            "v.what.rast",
            map="source_points_%d" % os.getpid(),
            raster=habitat_p,
            column="p",
        )
    else:
        grass.run_command(
            "v.db.update",
            map="source_points_%d" % os.getpid(),
            value=p_fixed,
            column="p",
        )

    # Make source points permanent
    grass.run_command(
        "g.copy",
        vector="source_points_%d" % os.getpid()
        + ","
        + output_fidimo
        + "_source_points",
    )

    ########### Looping over nrun, over segments, over source points ##########

    if (
        str(options["statistical_interval"]) == "no"
        or str(options["statistical_interval"])
        == "Random Value within Confidence Interval"
    ):
        nrun = ["fit"]
    else:
        nrun = ["fit", "lwr", "upr"]

    for i in nrun:
        database = sqlite3.connect(
            os.path.join(gisdbase, location, mapset, "sqlite.db")
        )
        # update database-connection
        db = database.cursor()

        mapcalc_list_Ba = []
        mapcalc_list_Bb = []

        ########## Loop over segments ############
        # Extract Segments-Info to loop over
        segment_list = grass.read_command(
            "db.select",
            flags="c",
            sql="SELECT segment FROM source_points_%d" % os.getpid(),
        ).split("\n")[
            :-1
        ]  # remove last (empty line)
        segment_list = map(int, segment_list)
        segment_list = sorted(list(set(segment_list)))

        for j in segment_list:

            segment_cat = str(j)
            grass.debug(_("This is segment nr.: " + str(segment_cat)))

            mapcalc_list_Aa = []
            mapcalc_list_Ab = []

            # Loop over Source points
            source_points_list = grass.read_command(
                "db.select",
                flags="c",
                sql="SELECT cat, X, Y, n_fish, prob_scalar, Strahler, habitat_attract, p FROM source_points_%d WHERE segment=%d"
                % (os.getpid(), int(j)),
            ).split("\n")[
                :-1
            ]  # remove last (empty line)
            source_points_list = list(csv.reader(source_points_list, delimiter="|"))

            for k in source_points_list:

                cat = int(k[0])
                X = float(k[1])
                Y = float(k[2])
                prob_scalar = float(k[4])
                Strahler = int(k[5])
                coors = str(X) + "," + str(Y)
                if flags["r"]:
                    n_fish = int(k[3])
                if options["habitat_attract"]:
                    source_habitat_attract = float(k[6])
                p = float(k[7])

                # Progress bar
                # TODO: add here progress bar

                # Debug messages
                grass.debug(_("Start looping over source points"))
                grass.debug(
                    _(
                        "Source point coors:"
                        + coors
                        + " in segment nr: "
                        + str(segment_cat)
                    )
                )

                # Select dispersal parameters
                SO = "SO=" + str(Strahler)
                grass.debug(_("This is i:" + str(i)))
                grass.debug(_("This is " + str(SO)))

                # if Random Value within Confidence Interval then select a sigma value that is within the CI assuming a normal distribution of sigma within the CI
                if (
                    str(options["statistical_interval"])
                    == "Random Value within Confidence Interval"
                ):
                    random.seed(int(options["seed1"]))
                    sigma_stat = random.gauss(
                        mu=fishmove.rx("fit", "sigma_stat", 1, 1, SO, 1)[0],
                        sigma=(
                            fishmove.rx("upr", "sigma_stat", 1, 1, SO, 1)[0]
                            - fishmove.rx("lwr", "sigma_stat", 1, 1, SO, 1)[0]
                        )
                        / 4,
                    )
                    random.seed(int(options["seed1"]))
                    sigma_mob = random.gauss(
                        mu=fishmove.rx("fit", "sigma_mob", 1, 1, SO, 1)[0],
                        sigma=(
                            fishmove.rx("upr", "sigma_mob", 1, 1, SO, 1)[0]
                            - fishmove.rx("lwr", "sigma_mob", 1, 1, SO, 1)[0]
                        )
                        / 4,
                    )
                else:
                    sigma_stat = fishmove.rx(i, "sigma_stat", 1, 1, SO, 1)
                    sigma_mob = fishmove.rx(i, "sigma_mob", 1, 1, SO, 1)

                grass.debug(
                    _(
                        "Dispersal parameters: prob_scalar="
                        + str(prob_scalar)
                        + ", sigma_stat="
                        + str(sigma_stat)
                        + ", sigma_mob="
                        + str(sigma_mob)
                        + ", p="
                        + str(p)
                    )
                )

                # Getting maximum distance (cutting distance) based on truncation criterion
                def func(x, sigma_stat, sigma_mob, m, truncation, p):
                    return (
                        p * stats.norm.cdf(x, loc=m, scale=sigma_stat)
                        + (1 - p) * stats.norm.cdf(x, loc=m, scale=sigma_mob)
                        - truncation
                    )

                if options["truncation"] == "inf":
                    max_dist = 0
                else:
                    truncation = float(options["truncation"])
                    max_dist = int(
                        optimize.zeros.newton(
                            func, 1.0, args=(sigma_stat, sigma_mob, m, truncation, p)
                        )
                    )

                grass.debug(
                    _(
                        "Distance from each source point is calculated up to a threshold of: "
                        + str(max_dist)
                    )
                )

                grass.run_command(
                    "r.cost",
                    flags="n",
                    overwrite=True,
                    input="river_raster_tmp_%d" % os.getpid(),
                    output="distance_from_point_tmp_%d" % os.getpid(),
                    start_coordinates=coors,
                    max_cost=max_dist,
                )

                # Getting upper and lower distance (cell boundaries) based on the fact that there are different flow lengths through a cell depending on the direction (diagonal-orthogonal)
                grass.mapcalc(
                    "$upper_distance = if($flow_direction==2||$flow_direction==4||$flow_direction==6||$flow_direction==8||$flow_direction==-2||$flow_direction==-4||$flow_direction==-6||$flow_direction==-8, $distance_from_point+($ds/2.0), $distance_from_point+($dd/2.0))",
                    upper_distance="upper_distance_tmp_%d" % os.getpid(),
                    flow_direction="flow_direction_tmp_%d" % os.getpid(),
                    distance_from_point="distance_from_point_tmp_%d" % os.getpid(),
                    ds=res,
                    dd=math.sqrt(2) * res,
                    overwrite=True,
                )

                grass.mapcalc(
                    "$lower_distance = if($flow_direction==2||$flow_direction==4||$flow_direction==6||$flow_direction==8||$flow_direction==-2||$flow_direction==-4||$flow_direction==-6||$flow_direction==-8, $distance_from_point-($ds/2.0), $distance_from_point-($dd/2.0))",
                    lower_distance="lower_distance_tmp_%d" % os.getpid(),
                    flow_direction="flow_direction_tmp_%d" % os.getpid(),
                    distance_from_point="distance_from_point_tmp_%d" % os.getpid(),
                    ds=res,
                    dd=math.sqrt(2) * res,
                    overwrite=True,
                )

                # MAIN PART: leptokurtic probability density kernel based on fishmove
                grass.debug(
                    _("Begin with core of fidimo, application of fishmove on garray")
                )

                def cdf(x):
                    return (
                        p * stats.norm.cdf(x, loc=m, scale=sigma_stat)
                        + (1 - p) * stats.norm.cdf(x, loc=m, scale=sigma_mob)
                    ) * prob_scalar

                # Calculation Kernel Density from Distance Raster
                # only for m=0 because of cdf-function
                if grass.find_file(
                    name="density_from_point_unmasked_tmp_%d" % os.getpid(),
                    element="cell",
                )["file"]:
                    grass.run_command(
                        "g.remove",
                        flags="f",
                        type="raster",
                        name="density_from_point_unmasked_tmp_%d" % os.getpid(),
                    )

                x1 = garray.array("lower_distance_tmp_%d" % os.getpid())
                x2 = garray.array("upper_distance_tmp_%d" % os.getpid())
                Density = garray.array()
                Density[...] = cdf(x2) - cdf(x1)
                grass.debug(_("Write density from point to garray. unmasked"))
                Density.write("density_from_point_unmasked_tmp_%d" % os.getpid())

                # Mask density output because Density.write doesn't provide nulls()
                grass.mapcalc(
                    "$density_from_point = if($distance_from_point>=0, $density_from_point_unmasked, null())",
                    density_from_point="density_from_point_tmp_%d" % os.getpid(),
                    distance_from_point="distance_from_point_tmp_%d" % os.getpid(),
                    density_from_point_unmasked="density_from_point_unmasked_tmp_%d"
                    % os.getpid(),
                    overwrite=True,
                )

                # Defining up and downstream of source point
                grass.debug(_("Defining up and downstream of source point"))

                # Defining area upstream source point
                grass.run_command(
                    "r.stream.basins",
                    overwrite=True,
                    direction="flow_direction_tmp_%d" % os.getpid(),
                    coordinates=coors,
                    basins="upstream_part_tmp_%d" % os.getpid(),
                )

                # Defining area downstream source point
                grass.run_command(
                    "r.drain",
                    input="distance_raster_tmp_%d" % os.getpid(),
                    output="downstream_drain_tmp_%d" % os.getpid(),
                    overwrite=True,
                    start_coordinates=coors,
                )

                # Applying upstream split at network nodes based on inverse Shreve stream order
                grass.debug(
                    _(
                        "Applying upstream split at network nodes based on inverse Shreve stream order"
                    )
                )

                grass.mapcalc(
                    "$upstream_shreve = if($upstream_part, $shreve)",
                    upstream_shreve="upstream_shreve_tmp_%d" % os.getpid(),
                    upstream_part="upstream_part_tmp_%d" % os.getpid(),
                    shreve="shreve_tmp_%d" % os.getpid(),
                    overwrite=True,
                )
                max_shreve = grass.raster_info("upstream_shreve_tmp_%d" % os.getpid())[
                    "max"
                ]
                grass.mapcalc(
                    "$rel_upstream_shreve = $upstream_shreve / $max_shreve",
                    rel_upstream_shreve="rel_upstream_shreve_tmp_%d" % os.getpid(),
                    upstream_shreve="upstream_shreve_tmp_%d" % os.getpid(),
                    max_shreve=max_shreve,
                    overwrite=True,
                )

                grass.mapcalc(
                    "$division_overlay = if(isnull($downstream_drain), $rel_upstream_shreve, $downstream_drain)",
                    division_overlay="division_overlay_tmp_%d" % os.getpid(),
                    downstream_drain="downstream_drain_tmp_%d" % os.getpid(),
                    rel_upstream_shreve="rel_upstream_shreve_tmp_%d" % os.getpid(),
                    overwrite=True,
                )
                grass.mapcalc(
                    "$density = if($density_from_point, $density_from_point*$division_overlay, null())",
                    density="density_" + str(cat),
                    density_from_point="density_from_point_tmp_%d" % os.getpid(),
                    division_overlay="division_overlay_tmp_%d" % os.getpid(),
                    overwrite=True,
                )

                grass.run_command("r.null", map="density_" + str(cat), null="0")

                ###### Barriers per source point #######
                if options["barriers"]:
                    grass.mapcalc(
                        "$distance_upstream_point = if($upstream_part, $distance_from_point, null())",
                        distance_upstream_point="distance_upstream_point_tmp_%d"
                        % os.getpid(),
                        upstream_part="upstream_part_tmp_%d" % os.getpid(),
                        distance_from_point="distance_from_point_tmp_%d" % os.getpid(),
                        overwrite=True,
                    )

                    # Getting distance of barriers and information if barrier is involved/affected
                    grass.run_command(
                        "v.what.rast",
                        map="barriers_%d" % os.getpid(),
                        raster="distance_upstream_point_tmp_%d" % os.getpid(),
                        column="dist",
                    )

                    # Loop over the affected barriers (from most downstream barrier to most upstream barrier)
                    # Initally affected = all barriers where density > 0
                    barriers_list = grass.read_command(
                        "db.select",
                        flags="c",
                        sql="SELECT cat, adj_X, adj_Y, dist, %s FROM barriers_%d WHERE dist > 0 ORDER BY dist"
                        % (passability_col, os.getpid()),
                    ).split("\n")[
                        :-1
                    ]  # remove last (empty line)
                    barriers_list = list(csv.reader(barriers_list, delimiter="|"))

                    # if affected barriers then define the last loop (find the upstream most barrier)
                    if barriers_list:
                        last_barrier = float(barriers_list[-1][3])

                    for l in barriers_list:

                        barrier_cat = int(l[0])
                        adj_X = float(l[1])
                        adj_Y = float(l[2])
                        dist = float(l[3])
                        passability = float(l[4])
                        coors_barriers = str(adj_X) + "," + str(adj_Y)

                        grass.debug(
                            _(
                                "Starting with calculating barriers-effect (coors_barriers: "
                                + coors_barriers
                                + ")"
                            )
                        )

                        # Defining upstream the barrier
                        grass.run_command(
                            "r.stream.basins",
                            overwrite=True,
                            direction="flow_direction_tmp_%d" % os.getpid(),
                            coordinates=coors_barriers,
                            basins="upstream_barrier_tmp_%d" % os.getpid(),
                        )

                        grass.run_command(
                            "r.null", map="density_" + str(cat), setnull="0"
                        )

                        # Getting density upstream barrier only
                        grass.mapcalc(
                            "$upstream_barrier_density = if($upstream_barrier, $density, null())",
                            upstream_barrier_density="upstream_barrier_density_tmp_%d"
                            % os.getpid(),
                            upstream_barrier="upstream_barrier_tmp_%d" % os.getpid(),
                            density="density_" + str(cat),
                            overwrite=True,
                        )

                        # Getting sum of upstream density and density to relocate downstream
                        d = {
                            "n": 5,
                            "min": 6,
                            "max": 7,
                            "mean": 9,
                            "sum": 14,
                            "median": 16,
                            "range": 8,
                        }
                        univar_upstream_barrier_density = grass.read_command(
                            "r.univar",
                            map="upstream_barrier_density_tmp_%d" % os.getpid(),
                            flags="e",
                        )
                        if univar_upstream_barrier_density:
                            sum_upstream_barrier_density = float(
                                univar_upstream_barrier_density.split("\n")[
                                    d["sum"]
                                ].split(":")[1]
                            )
                        else:
                            # if no upstream density to allocate than stop that "barrier-loop" and continue with next barrier
                            grass.message(
                                _(
                                    "No upstream density to allocate downstream for that barrier: "
                                    + coors_barriers
                                )
                            )
                            continue

                        density_for_downstream = sum_upstream_barrier_density * (
                            1 - passability
                        )

                        # barrier_effect = Length of Effect of barriers (linear decrease up to max (barrier_effect)
                        barrier_effect = 200  # units as in mapset (m)

                        # Calculating distance from barriers (up- and downstream)
                        grass.run_command(
                            "r.cost",
                            overwrite=True,
                            input="river_raster_tmp_%d" % os.getpid(),
                            output="distance_barrier_tmp_%d" % os.getpid(),
                            start_coordinates=coors_barriers,
                            max_cost=barrier_effect,
                        )

                        # Getting distance map for downstream of barrier only
                        grass.mapcalc(
                            "$distance_downstream_barrier = if(isnull($upstream_barrier), $distance_barrier, null())",
                            distance_downstream_barrier="distance_downstream_barrier_tmp_%d"
                            % os.getpid(),
                            upstream_barrier="upstream_barrier_tmp_%d" % os.getpid(),
                            distance_barrier="distance_barrier_tmp_%d" % os.getpid(),
                            overwrite=True,
                        )

                        # Getting inverse distance map for downstream of barrier only
                        grass.mapcalc(
                            "$inv_distance_downstream_barrier = 1.0/$distance_downstream_barrier",
                            inv_distance_downstream_barrier="inv_distance_downstream_barrier_tmp_%d"
                            % os.getpid(),
                            distance_downstream_barrier="distance_downstream_barrier_tmp_%d"
                            % os.getpid(),
                            overwrite=True,
                        )

                        # Getting parameters for distance weighted relocation of densities downstream the barrier (inverse to distance (reciprocal), y=(density/sum(1/distance))/distance)
                        univar_distance_downstream_barrier = grass.read_command(
                            "r.univar",
                            map="inv_distance_downstream_barrier_tmp_%d" % os.getpid(),
                            flags="e",
                        )
                        sum_inv_distance_downstream_barrier = float(
                            univar_distance_downstream_barrier.split("\n")[
                                d["sum"]
                            ].split(":")[1]
                        )
                        grass.debug(
                            _(
                                "sum_inv_distance_downstream_barrier: "
                                + str(sum_inv_distance_downstream_barrier)
                            )
                        )

                        # Calculation Density downstream the barrier
                        grass.mapcalc(
                            "$downstream_barrier_density = ($density_for_downstream/$sum_inv_distance_downstream_barrier)/$distance_downstream_barrier",
                            downstream_barrier_density="downstream_barrier_density_tmp_%d"
                            % os.getpid(),
                            density_for_downstream=density_for_downstream,
                            sum_inv_distance_downstream_barrier=sum_inv_distance_downstream_barrier,
                            distance_downstream_barrier="distance_downstream_barrier_tmp_%d"
                            % os.getpid(),
                            overwrite=True,
                        )

                        # Combination upstream and downstream density from barrier
                        grass.run_command("r.null", map="density_" + str(cat), null="0")
                        grass.run_command(
                            "r.null",
                            map="downstream_barrier_density_tmp_%d" % os.getpid(),
                            null="0",
                        )

                        grass.mapcalc(
                            "$density_point = if(isnull($upstream_barrier), $downstream_barrier_density+$density_point, $upstream_barrier_density*$passability)",
                            density_point="density_" + str(cat),
                            upstream_barrier="upstream_barrier_tmp_%d" % os.getpid(),
                            downstream_barrier_density="downstream_barrier_density_tmp_%d"
                            % os.getpid(),
                            upstream_barrier_density="upstream_barrier_density_tmp_%d"
                            % os.getpid(),
                            passability=passability,
                            overwrite=True,
                        )

                        if dist == last_barrier:
                            grass.run_command(
                                "r.null", map="density_" + str(cat), null="0"
                            )
                        else:
                            grass.run_command(
                                "r.null", map="density_" + str(cat), setnull="0"
                            )

                # Get a list of all densities processed so far within this segment
                mapcalc_list_Aa.append("density_" + str(cat))

                if options["habitat_attract"]:
                    # Multiply (Weight) density point with relative attractiveness. relative attractive in relation to habitat attractiveness at source
                    grass.mapcalc(
                        "$density_point_attract = $density_point*($habitat_attract/$source_habitat_attract)",
                        density_point_attract="density_attract_" + str(cat),
                        density_point="density_" + str(cat),
                        habitat_attract=habitat_attract,
                        source_habitat_attract=source_habitat_attract,
                        overwrite=True,
                    )

                    grass.run_command(
                        "g.rename",
                        raster="density_attract_"
                        + str(cat)
                        + ","
                        + "density_"
                        + str(cat),
                        overwrite=True,
                    )

                if flags["r"]:
                    # Realisation of Probability raster, Multinomial backtransformation from probability into fish counts per cell
                    grass.debug(
                        _(
                            "Write Realisation (fish counts) from point to garray. This is point cat: "
                            + str(cat)
                        )
                    )
                    CorrectedDensity = garray.array("density_" + str(cat))

                    RealisedDensity = garray.array()
                    if options["seed2"]:
                        numpy.random.seed(int(options["seed2"]))
                    RealisedDensity[...] = numpy.random.multinomial(
                        n_fish,
                        (CorrectedDensity / numpy.sum(CorrectedDensity)).flat,
                        size=1,
                    ).reshape(CorrectedDensity.shape)

                    RealisedDensity.write("realised_density_" + str(cat))

                    grass.run_command(
                        "r.null", map="realised_density_" + str(cat), null="0"
                    )

                    # Get a list of all realised densities processed so far within this segment
                    mapcalc_list_Ab.append("realised_density_" + str(cat))

            # Aggregation per segment
            mapcalc_string_Aa_aggregate = "+".join(mapcalc_list_Aa)
            mapcalc_string_Aa_removal = ",".join(mapcalc_list_Aa)

            grass.mapcalc(
                "$density_segment = $mapcalc_string_Aa_aggregate",
                density_segment="density_segment_" + segment_cat,
                mapcalc_string_Aa_aggregate=mapcalc_string_Aa_aggregate,
                overwrite=True,
            )
            grass.run_command(
                "g.remove", flags="bf", type="raster", name=mapcalc_string_Aa_removal
            )

            grass.run_command(
                "r.null", map="density_segment_" + segment_cat, null="0"
            )  # Final density map per segment, set 0 for aggregation with r.mapcalc

            mapcalc_list_Ba.append("density_segment_" + segment_cat)

            if flags["r"]:
                mapcalc_string_Ab_aggregate = "+".join(mapcalc_list_Ab)
                mapcalc_string_Ab_removal = ",".join(mapcalc_list_Ab)
                grass.mapcalc(
                    "$realised_density_segment = $mapcalc_string_Ab_aggregate",
                    realised_density_segment="realised_density_segment_" + segment_cat,
                    mapcalc_string_Ab_aggregate=mapcalc_string_Ab_aggregate,
                    overwrite=True,
                )
                grass.run_command(
                    "g.remove",
                    flags="bf",
                    type="raster",
                    name=mapcalc_string_Ab_removal,
                )

                grass.run_command(
                    "r.null", map="realised_density_segment_" + segment_cat, null="0"
                )  # Final density map per segment, set 0 for aggregation with r.mapcalc
                mapcalc_list_Bb.append("realised_density_segment_" + segment_cat)

        # Overall aggregation
        mapcalc_string_Ba_aggregate = "+".join(mapcalc_list_Ba)
        mapcalc_string_Ba_removal = ",".join(mapcalc_list_Ba)

        # Final raster map, Final map is sum of all
        # density maps (for each segment), All contributing maps (string_Ba_removal) are deleted
        # in the end.
        grass.mapcalc(
            "$density_final = $mapcalc_string_Ba_aggregate",
            density_final="density_final_%d" % os.getpid(),
            mapcalc_string_Ba_aggregate=mapcalc_string_Ba_aggregate,
            overwrite=True,
        )

        if flags["r"]:
            mapcalc_string_Bb_aggregate = "+".join(mapcalc_list_Bb)
            mapcalc_string_Bb_removal = ",".join(mapcalc_list_Bb)
            grass.mapcalc(
                "$realised_density_final = $mapcalc_string_Bb_aggregate",
                realised_density_final="realised_density_final_%d" % os.getpid(),
                mapcalc_string_Bb_aggregate=mapcalc_string_Bb_aggregate,
                overwrite=True,
            )
            grass.run_command(
                "g.copy",
                raster="realised_density_final_%d" % os.getpid()
                + ",realised_"
                + output_fidimo
                + "_"
                + i,
            )

            # Set all 0-values to NULL, Backgroundvalues
            grass.run_command(
                "r.null", map="realised_" + output_fidimo + "_" + i, setnull="0"
            )

            grass.run_command(
                "g.remove", flags="bf", type="raster", name=mapcalc_string_Bb_removal
            )

        # backtransformation (divide by scalar which was defined before)
        grass.mapcalc(
            "$density_final_corrected = $density_final/$scalar",
            density_final_corrected="density_final_corrected_%d" % os.getpid(),
            density_final="density_final_%d" % os.getpid(),
            scalar=scalar,
            overwrite=True,
        )

        grass.run_command(
            "g.copy",
            raster="density_final_corrected_%d" % os.getpid()
            + ","
            + output_fidimo
            + "_"
            + i,
        )

        # Set all 0-values to NULL, Backgroundvalues
        grass.run_command("r.null", map=output_fidimo + "_" + i, setnull="0")

        grass.run_command(
            "g.remove", flags="bf", type="raster", name=mapcalc_string_Ba_removal
        )

    # Delete basic maps if flag "b" is set
    if flags["b"]:
        grass.run_command(
            "g.remove", flags="bf", type="vector", name=output_fidimo + "_source_points"
        )
        if options["barriers"]:
            grass.run_command(
                "g.remove", flags="bf", type="vector", name=output_fidimo + "_barriers"
            )

    return 0


if __name__ == "__main__":
    options, flags = grass.parser()
    atexit.register(cleanup)
    sys.exit(main())
