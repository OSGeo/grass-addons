#!/usr/bin/env python3
#############################################################################
#
# MODULE:       v.surf.icw
#
# AUTHOR:       M. Hamish Bowman, Dunedin, New Zealand
#                Originally written aboard the NZ DoC ship M/V Renown,
#                Bligh Sound, Fiordland National Park, November 2003
#                With thanks to Franz Smith and Steve Wing for support
#                Ported to Python for GRASS 7 December 2011
#
# PURPOSE:      Like IDW interpolation, but distance is cost to get to any
#                other site.
#
# COPYRIGHT:    (c) 2003-2024 Hamish Bowman
#               This program is free software under the GNU General Public
#               License (>=v2). Read the file COPYING that comes with GRASS
#               for details.
#
#############################################################################
#
# Description:
#  Non-euclidean, non-polluting IDW from areas separated by null cells
#  e.g.
#   - two parallel lakes, connected at one end (water chemistry in arms of a fjord)
#   - Population abundance constrained by topography (Kiwis crossing a land-bridge)
#
#  w(d)= 1/d^p    where p is user definable, usually 2.
#
# Notes:
#  A cost surface containing molasses barrier data may be used as well.
#  Input data points need not have direct line of sight to each other.
#  Try and keep the number of input sites to under a few dozen, as the
#  process is very computationally expensive. You might consider creating
#  a few hundred MB RAM-disk for a temporary mapset to avoid thrashing your
#  hard drive (r.cost is heavy on disk IO).


# %Module
# % description: IDW interpolation, but distance is cost to get to any other site.
# % keyword: vector
# % keyword: surface
# % keyword: interpolation
# % keyword: ICW
# %End
# %option
# % key: input
# % type: string
# % gisprompt: old,vector,vector
# % description: Name of existing vector points map containing seed data
# % required : yes
# %end
# %option
# % key: column
# % type: string
# % description: Column name in points map that contains data values
# % required : yes
# %end
# %option
# % key: output
# % type: string
# % gisprompt: new,cell,raster
# % description: Name for output raster map
# % required : yes
# %end
# %option
# % key: cost_map
# % type: string
# % gisprompt: old,cell,raster
# % description: Name of existing raster map containing cost information
# % required : yes
# %end
# %option
# % key: friction
# % type: double
# % description: Friction of distance, (the 'n' in 1/d^n)
# % answer: 2
# % options: 1-6
# % required : no
# %end
# %option
# % key: layer
# % type: integer
# % answer: 1
# % description: Layer number of data in points map
# % required: no
# %end
# %option
# % key: where
# % type: string
# % label: WHERE conditions of SQL query statement without 'where' keyword
# % description: Example: income < 1000 and inhab >= 10000
# % required : no
# %end

##%option
##% key: max_cost
##% type: integer
##% description: Optional maximum cumulative cost before setting weight to zero
##% required : no
##%end

# %option
# % key: post_mask
# % type: string
# % gisprompt: old,cell,raster
# % description: Name of existing raster map to be used as post-processing MASK
# % required : no
# %end
# %flag
# % key: r
# % description: Use (d^n)*log(d) instead of 1/(d^n) for radial basis function
# %end
# %option
# % key: workers
# % type: integer
# % options: 1-256
# % answer: 1
# % description: Number of parallel processes to launch
# %end

from __future__ import unicode_literals
from builtins import str
from builtins import range
import sys
import os
import atexit
import grass.script as grass
from grass.exceptions import CalledModuleError

TMP_FILE = None


def cleanup():
    grass.verbose(_("Cleanup.."))
    tmp_base = "tmp_icw_" + str(os.getpid()) + "_"
    grass.run_command(
        "g.remove", flags="f", type="raster", pattern=tmp_base + "*", quiet=True
    )
    grass.try_remove(TMP_FILE)


def main():

    pts_input = options["input"]
    output = options["output"]
    cost_map = options["cost_map"]
    post_mask = options["post_mask"]
    column = options["column"]
    friction = float(options["friction"])
    layer = options["layer"]
    where = options["where"]
    workers = int(options["workers"])

    if workers == 1 and "WORKERS" in os.environ:
        workers = int(os.environ["WORKERS"])
    if workers < 1:
        workers = 1

    pid = str(os.getpid())
    tmp_base = "tmp_icw_" + pid + "_"

    # do the maps exist?
    if not grass.find_file(pts_input, element="vector")["file"]:
        grass.fatal(_("Vector map <%s> not found") % pts_input)
    if post_mask:
        if grass.find_file("MASK")["file"]:
            grass.fatal(
                _("A MASK already exists; remove it before using the post_mask option.")
            )
        if not grass.find_file(post_mask)["file"]:
            grass.fatal(_("Raster map <%s> not found") % post_mask)

    grass.verbose(_("v.surf.icw -- Inverse Cost Weighted Interpolation"))
    grass.verbose(
        _("Processing %s -> %s, column=%s, Cf=%g")
        % (pts_input, output, column, friction)
    )

    if flags["r"]:
        grass.verbose(_("Using (d^n)*log(d) radial basis function."))

    grass.verbose(
        "------------------------------------------------------------------------"
    )

    # adjust so that tiny numbers don't hog all the FP precision space
    #  if friction = 4: divisor ~ 10.0
    #  if friction = 5: divisor ~ 100.0
    #  if friction = 6: divisor ~ 500.0
    if friction >= 4:
        divisor = 0.01 * pow(friction, 6)
    else:
        divisor = 1

    # Check that we have the column and it is the correct type
    try:
        coltype = grass.vector_columns(pts_input, layer)[column]
    except KeyError:
        grass.fatal(
            _("Data column <%s> not found in vector points map <%s>")
            % (column, pts_input)
        )

    if coltype["type"] not in ("INTEGER", "DOUBLE PRECISION"):
        grass.fatal(_("Data column must be numberic"))

    # cleanse cost area mask to a flat =1 for my porpoises
    area_mask = tmp_base + "area"
    grass.mapcalc(
        "$result = if($cost_map, 1, null())",
        result=area_mask,
        cost_map=cost_map,
        quiet=True,
    )

    ## done with prep work,
    ########################################################################
    ## Commence crunching ..

    # crop out only points in region
    addl_opts = {}
    if where:
        addl_opts["where"] = "%s" % where

    points_list = grass.read_command(
        "v.out.ascii", input=pts_input, output="-", flags="r", **addl_opts
    ).splitlines()

    # Needed to strip away empty entries from MS Windows newlines
    #   list() is needed for Python 3 compatibility
    points_list = list([_f for _f in points_list if _f])

    # convert into a 2D list, drop unneeded cat column
    # to drop cat col, add this to the end of the line [:-1]
    # fixme: how does this all react for 3D starting points?
    for i in range(len(points_list)):
        points_list[i] = points_list[i].split("|")

    # count number of starting points (n). This value will later be decremented
    #  if points are found to be off the cost map or out of region.
    n = len(points_list)

    if n > 200:
        grass.warning(
            _(
                "Computation is expensive! Please consider "
                + "fewer points or get ready to wait a while ..."
            )
        )
        import time

        time.sleep(5)

    #### generate cost maps for each site in range
    grass.message(_("Generating cost maps ..."))

    # avoid do-it-yourself brain surgery
    points_list_orig = list(points_list)

    proc = {}
    num = 1
    for i in range(n):
        position = points_list_orig[i]
        easting = position[0]
        northing = position[1]
        cat = int(position[-1])

        # retrieve data value from vector's attribute table:
        data_value = grass.vector_db_select(pts_input, columns=column)["values"][cat][0]

        if not data_value:
            grass.message(
                _("Site %d of %d,  e=%.4f  n=%.4f  cat=%d  data=?")
                % (num, n, float(easting), float(northing), cat)
            )
            grass.message(_(" -- Skipping, no data here."))
            del points_list[num - 1]
            n -= 1
            continue
        else:
            grass.message(
                _("Site %d of %d,  e=%.4f  n=%.4f  cat=%d  data=%.8g")
                % (num, n, float(easting), float(northing), cat, float(data_value))
            )

        # we know the point is in the region, but is it in a non-null area of the cost surface?
        rast_val = (
            grass.read_command(
                "r.what",
                map=area_mask,
                coordinates="%s,%s" % (position[0], position[1]),
            )
            .strip()
            .split("|")[-1]
        )
        if rast_val == "*":
            grass.message(_(" -- Skipping, point lays outside of cost_map."))
            del points_list[num - 1]
            n -= 1
            continue

        # it's ok to proceed
        try:
            data_value = float(data_value)
        except:
            grass.fatal("Data value [%s] is non-numeric" % data_value)

        cost_site_name = tmp_base + "cost_site." + "%05d" % num
        proc[num - 1] = grass.start_command(
            "r.cost",
            flags="k",
            input=area_mask,
            output=cost_site_name,
            start_coordinates=easting + "," + northing,
            quiet=True,
        )
        # stall to wait for the nth worker to complete,
        if num % workers == 0:
            proc[num - 1].wait()

        num += 1

    # make sure everyone is finished
    for i in range(n):
        if proc[i].wait() != 0:
            grass.fatal(_("Problem running %s") % "r.cost")

    grass.message(_("Removing anomalies at site positions ..."))

    proc = {}
    for i in range(n):
        cost_site_name = tmp_base + "cost_site." + "%05d" % (i + 1)
        # max_cost="$GIS_OPT_MAX_COST"  : commented out until r.null cleansing/continue code is sorted out
        # start_points=tmp_idw_cost_site_$$

        # we do this so the divisor exists and the weighting is huge at the exact sample spots
        # more efficient to reclass to 1?
        proc[i] = grass.mapcalc_start(
            "$cost_n_cleansed = if($cost_n == 0, 0.1, $cost_n)",
            cost_n_cleansed=cost_site_name + ".cleansed",
            cost_n=cost_site_name,
            quiet=True,
        )
        # stall to wait for the nth worker to complete,
        if (i + 1) % workers == 0:
            # print('stalling ...')
            proc[i].wait()

    # make sure everyone is finished
    for i in range(n):
        if proc[i].wait() != 0:
            grass.fatal(_("Problem running %s") % "r.mapcalc")

    grass.message(_("Applying radial decay ..."))

    proc = {}
    for i in range(n):
        cost_site_name = tmp_base + "cost_site." + "%05d" % (i + 1)
        grass.run_command(
            "g.remove", flags="f", type="raster", name=cost_site_name, quiet=True
        )
        grass.run_command(
            "g.rename",
            raster=cost_site_name + ".cleansed" + "," + cost_site_name,
            quiet=True,
        )

        # r.to.vect then r.patch output
        # v.to.rast in=tmp_idw_cost_site_29978 out=tmp_idw_cost_val_$$ use=val val=10

        if not flags["r"]:
            #  exp(3,2) is 3^2  etc.  as is pow(3,2)
            # r.mapcalc "1by_cost_site_sqrd.$NUM =  1.0 / exp(cost_site.$NUM , $FRICTION)"
            #      EXPRESSION="1.0 / pow(cost_site.$NUM $DIVISOR, $FRICTION )"
            expr = "1.0 / pow($cost_n / " + str(divisor) + ", $friction)"
        else:
            # use log10() or ln() ?
            #      EXPRESSION="1.0 / ( pow(cost_site.$NUM, $FRICTION) * log (cost_site.$NUM) )"
            expr = '1.0 / ( pow($cost_n, $friction) * log($cost_n) )"'

        grass.debug("r.mapcalc expression is: [%s]" % expr)

        one_by_cost_site_sq_n = tmp_base + "1by_cost_site_sq." + "%05d" % (i + 1)

        proc[i] = grass.mapcalc_start(
            "$result = " + expr,
            result=one_by_cost_site_sq_n,
            cost_n=cost_site_name,
            friction=friction,
            quiet=True,
        )
        # stall to wait for the nth worker to complete,
        if (i + 1) % workers == 0:
            # print('stalling ...')
            proc[i].wait()

        # r.patch in=1by_cost_site_sqrd.${NUM},tmp_idw_cost_val_$$ out=1by_cost_site_sqrd.${NUM} --o
        # g.remove type=rast name=cost_site.$NUM -f

    # make sure everyone is finished
    for i in range(n):
        if proc[i].wait() != 0:
            grass.fatal(_("Problem running %s") % "r.mapcalc")

    grass.run_command(
        "g.remove",
        flags="f",
        type="raster",
        pattern=tmp_base + "cost_site.*",
        quiet=True,
    )
    # grass.run_command('g.list', type = 'raster', mapset = '.')

    #######################################################
    #### Step 3) find sum(cost^2)
    grass.verbose("\n" + _("Finding sum of squares ..."))

    # todo: test if MASK exists already, fatal exit if it does?
    if post_mask:
        grass.message(_("Setting post_mask <%s>"), post_mask)
        grass.mapcalc("MASK = $maskmap", maskmap=post_mask, overwrite=True)

    grass.message(_("Summation of cost weights ..."))

    input_maps = tmp_base + "1by_cost_site_sq.%05d" % 1

    global TMP_FILE
    TMP_FILE = grass.tempfile()
    with open(TMP_FILE, "w") as maplist:
        for i in range(2, n + 1):
            mapname = "%s1by_cost_site_sq.%05d" % (tmp_base, i)
            maplist.write(mapname + "\n")

    # grass.run_command('g.list', type = 'raster', mapset = '.')

    sum_of_1by_cost_sqs = tmp_base + "sum_of_1by_cost_sqs"
    try:
        grass.run_command(
            "r.series", method="sum", file=TMP_FILE, output=sum_of_1by_cost_sqs
        )
    except CalledModuleError:
        grass.fatal(_("Problem running %s") % "r.series")

    if post_mask:
        grass.message(_("Removing post_mask <%s>"), post_mask)
        grass.run_command("g.remove", flags="f", name="MASK", quiet=True)

    #######################################################
    #### Step 4) ( 1/di^2 / sum(1/d^2) ) *  ai
    grass.message("\n" + _("Creating partial weights ..."))

    proc = {}
    num = 1
    for position in points_list:
        easting = position[0]
        northing = position[1]
        cat = int(position[-1])
        data_value = grass.vector_db_select(pts_input, columns=column)["values"][cat][0]
        data_value = float(data_value)

        # failsafe: at this point the data values should all be valid
        if not data_value:
            grass.message(_("Site %d of %d,  cat = %d, data value = ?") % (num, n, cat))
            grass.message(_(" -- Skipping, no data here. [Probably programmer error]"))
            n -= 1
            continue
        else:
            grass.message(
                _("Site %d of %d,  cat = %d, data value = %.8g")
                % (num, n, cat, data_value)
            )

        # we know the point is in the region, but is it in a non-null area of the cost surface?
        rast_val = (
            grass.read_command(
                "r.what",
                map=area_mask,
                coordinates="%s,%s" % (position[0], position[1]),
            )
            .strip()
            .split("|")[-1]
        )
        if rast_val == "*":
            grass.message(
                _(
                    " -- Skipping, point lays outside of cost_map. [Probably programmer error]"
                )
            )
            n -= 1
            continue

        partial_n = tmp_base + "partial." + "%05d" % num
        one_by_cost_site_sq = tmp_base + "1by_cost_site_sq." + "%05d" % num

        # "( $DATA_VALUE / $N ) * (1.0 - ( cost_sq_site.$NUM / sum_of_cost_sqs ))"
        # "( cost_sq_site.$NUM / sum_of_cost_sqs ) * ( $DATA_VALUE / $N )"

        proc[num - 1] = grass.mapcalc_start(
            "$partial_n = ($data * $one_by_cost_sq) / $sum_of_1by_cost_sqs",
            partial_n=partial_n,
            data=data_value,
            one_by_cost_sq=one_by_cost_site_sq,
            sum_of_1by_cost_sqs=sum_of_1by_cost_sqs,
            quiet=True,
        )

        # stall to wait for the nth worker to complete,
        if num % workers == 0:
            proc[num - 1].wait()

        # free up disk space ASAP
        # grass.run_command('g.remove', flags = 'f', type = 'raster', name = one_by_cost_site_sq, quiet = True)

        num += 1
        if num > n:
            break

    # make sure everyone is finished
    for i in range(n):
        proc[i].wait()

    # free up disk space ASAP
    grass.run_command(
        "g.remove",
        flags="f",
        type="raster",
        pattern=tmp_base + "1by_cost_site_sq.*",
        quiet=True,
    )
    # grass.run_command('g.list', type = 'raster', mapset = '.')

    #######################################################
    grass.message("\n" + _("Calculating final values ..."))

    input_maps = tmp_base + "partial.%05d" % 1
    for i in range(2, n + 1):
        input_maps += ",%spartial.%05d" % (tmp_base, i)

    try:
        grass.run_command("r.series", method="sum", input=input_maps, output=output)
    except CalledModuleError:
        grass.fatal(_("Problem running %s") % "r.series")

    # TODO: r.patch in v.to.rast of values at exact seed site locations. currently set to null

    grass.run_command("r.colors", map=output, color="bcyr", quiet=True)
    grass.run_command(
        "r.support", map=output, history=" ", title="Inverse cost-weighted interpolation"
    )
    grass.run_command("r.support", map=output, history="v.surf.icw interpolation:")
    grass.run_command(
        "r.support",
        map=output,
        history="  input map=" + pts_input + "   attribute column=" + column,
    )
    grass.run_command(
        "r.support",
        map=output,
        history="  cost map="
        + cost_map
        + "   coefficient of friction="
        + str(friction),
    )
    if flags["r"]:
        grass.run_command(
            "r.support", map=output, history="  (d^n)*log(d) as radial basis function"
        )
    if post_mask:
        grass.run_command(
            "r.support", map=output, history="  post-processing mask=" + post_mask
        )
    if where:
        grass.run_command(
            "r.support", map=output, history="  SQL query= WHERE " + where
        )

    # save layer #? to metadata?   command line hist?

    #######################################################
    # Step 5) rm cost and cost_sq maps, tmp_icw_points, etc
    cleanup()

    #######################################################
    # Step 6) done!
    grass.message(_("Done! Results written to <%s>." % output))


if __name__ == "__main__":
    options, flags = grass.parser()
    atexit.register(cleanup)
    main()
