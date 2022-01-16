#!/usr/bin/env python
#
############################################################################
#
# MODULE:               r.catchment
# AUTHOR(S):            Isaac Ullah, Arizona State University
# PURPOSE:              Creates a raster buffer of specified area around vector
#                       points using cost distances. Module requires r.walk.
# ACKNOWLEDGEMENTS:     National Science Foundation Grant #BCS0410269
# COPYRIGHT:            (C) 2015 by Isaac Ullah, Arizona State University
#                       This program is free software under the GNU General
#                       Public License (>=v2). Read the file COPYING that comes
#                       with GRASS for details.
#
#############################################################################


#%Module
#% description: Creates a raster buffer of specified area around vector points using cost distances using r.walk.
#% keyword: raster
#% keyword: buffer
#%END


#%option G_OPT_R_INPUT
#% key: elevation
#% description: Input elevation map (DEM)
#% required : yes
#%END
#%option G_OPT_R_INPUT
#% key: in_cost
#% description: Input cost map (This will override the input elevation map, if none specified, one will be created from input elevation map with r.walk)
#% required : no
#%END
#%option G_OPT_V_INPUT
#% key: start_points
#% description: Name of input vector site points map
#% required : yes
#%END
#%option G_OPT_R_INPUT
#% key: friction
#% description: Optional map of friction costs. If no map selected, default friction=0 making output reflect time costs only
#% answer:
#% required : no
#%END
#%option
#% key: a
#% type: double
#% description: Coefficients for walking energy formula parameters a,b,c,d
#% answer: 0.72
#% required : no
#%END
#%option
#% key: b
#% type: double
#% description:
#% answer: 6.0
#% required : no
#%END
#%option
#% key: c
#% type: double
#% description:
#% answer: 1.9998
#% required : no
#%END
#%option
#% key: d
#% type: double
#% description:
#% answer: -1.9998
#% required : no
#%END
#%option
#% key: lambda
#% type: double
#% description: Lambda value for cost distance calculation (for combining friction costs with walking costs)
#% answer: 1
#% required : no
#%END
#%option
#% key: slope_factor
#% type: double
#% description: Slope factor determines travel energy cost per height step
#% answer: -0.2125
#% required : no
#%END
#%option G_OPT_R_OUTPUT
#% key: buffer
#% description: Output buffer map
#% required : yes
#%END
#%option
#% key: sigma
#% type: double
#% description: Slope threshold for mask
#% required: no
#%END
#%option
#% key: area
#% type: integer
#% description: Area of buffer (Integer value to nearest 100 square map units)
#% answer: 5000000
#% required: yes
#%END
#%option
#% key: map_val
#% type: integer
#% description: Integer value for output catchment area (all other areas will be Null)
#% answer: 1
#% required : yes
#%END
#%flag
#% key: k
#% description: Use knight's move for calculating cost surface (slower but more accurate)
#%END
#%flag
#% key: c
#% description: Keep cost surface used to calculate buffers
#%END
#%flag
#% key: l
#% description: Show a list of all cost surface values and the area of the catchment that they delimit
#%END


import sys
import os
import subprocess

# Just in case system can't find where grass.script is
grass_install_tree = os.getenv("GISBASE")
sys.path.append(grass_install_tree + os.sep + "etc" + os.sep + "python")


import grass.script as grass


# m is a grass/bash command that will generate some list of keyed info to
# stdout where the keys are numeric values, n is the character that separates
# the key from the data, o is a defined blank dictionary to write results to
def out2dictnum(m, n, o):
    """Execute a grass command, and parse it to a dictionary
    This works differently than standard grass.parse_command syntax"""
    p1 = subprocess.Popen("%s" % m, stdout=subprocess.PIPE, shell="bash")
    p2 = p1.stdout.readlines()
    for y in p2:
        y0, y1 = y.split("%s" % n)
        y0num = float(y0)
        o[y0num] = y1.strip("\n")


# main block of code starts here
def main():
    """Creates a raster buffer of specified area around
    vector points using cost distances using r.walk."""
    pid = os.getpid()
    # setting up variables for use later on
    elevation = options["elevation"]
    start_points = options["start_points"]
    lambda_ = options["lambda"]
    slope_factor = options["slope_factor"]
    a = options["a"]
    b = options["b"]
    c = options["c"]
    d = options["d"]
    sigma = options["sigma"]
    area = float(options["area"])
    buff = options["buffer"]
    mapval = options["map_val"]
    w_coefs = a + "," + b + "," + c + "," + d
    if (
        "MASK" in grass.list_grouped("rast")[grass.gisenv()["MAPSET"]]
        and bool(options["sigma"]) is True
    ):
        grass.message(
            "There is already a MASK in place, and you also have"
            " selected to mask slope values above %s.\n The high slope areas"
            " (slope mask) will be temporarily added to current MASKED areas for"
            " the calculation of the catchment geometry.\n The original MASK will"
            " be restored when the module finishes" % sigma
        )
        ismask = 2
        tempmask = "temporary.mask.%s" % pid
        grass.run_command(
            "g.rename",
            quiet=True,
            overwrite=grass.overwrite(),
            raster="MASK,%s" % tempmask,
        )
    elif "MASK" in grass.list_grouped("rast")[grass.gisenv()["MAPSET"]]:
        grass.message(
            "There is a MASK in place. The areas MASKed out will"
            " be ignored while calculating catchment geometry."
        )
        ismask = 1
    else:
        ismask = 0

    grass.message("Wanted buffer area=%s\n" % int(area))

    ####################################################
    if bool(options["in_cost"]) is True:
        grass.verbose("Using input cost surface")
        cost = options["in_cost"]
    else:
        grass.verbose("step 1 of 4: Calculating cost surface")
        cost = "temporary.cost.%s" % pid
        if bool(options["friction"]) is True:
            grass.verbose("Calculating costs using input friction map")
            friction = options["friction"]
        else:
            grass.verbose("Calculating for time costs only")
            friction = "temporary.friction.%s" % pid
            grass.mapcalc(
                "${out} = if(isnull(${rast1}), null(), 0)",
                overwrite=grass.overwrite(),
                quiet=True,
                out=friction,
                rast1=elevation,
            )
        if flags["k"] is True:
            grass.verbose("Using Knight's move")
            # NOTE! because "lambda" is an internal python variable, it is
            # impossible to enter the value for key "lambda" in r.walk.
            # It ends up with a python error.
            grass.run_command(
                "r.walk",
                quiet=True,
                overwrite=grass.overwrite(),
                flags="k",
                elevation=elevation,
                friction=friction,
                output=cost,
                start_points=start_points,
                walk_coeff=w_coefs,
                memory="100",
                slope_factor=slope_factor,
                lambda_=lambda_,
            )
        else:
            grass.run_command(
                "r.walk",
                quiet=True,
                overwrite=grass.overwrite(),
                elevation=elevation,
                friction=friction,
                output=cost,
                start_points=start_points,
                memory="100",
                walk_coeff=w_coefs,
                slope_factor=slope_factor,
                lambda_=lambda_,
            )
        if bool(options["friction"]) is False:
            grass.run_command(
                "g.remove", quiet=True, flags="f", type="raster", name=friction
            )
    #################################################
    if bool(options["sigma"]) is True:
        grass.verbose("Creating optional slope mask")
        slope = "temporary.slope.%s" % pid
        grass.run_command(
            "r.slope.aspect",
            quiet=True,
            overwrite=grass.overwrite(),
            elevation=elevation,
            slope=slope,
        )
        if ismask == 2:
            grass.mapcalc(
                "MASK=if(${rast1} <= ${sigma}, 1, if(${tempmask}, 1," " null()))",
                overwrite=grass.overwrite(),
                quiet=True,
                sigma=sigma,
                rast1=slope,
                tempmask=tempmask,
            )
        else:
            grass.mapcalc(
                "MASK=if(${rast1} <= ${sigma}, 1, null())",
                overwrite=grass.overwrite(),
                quiet=True,
                sigma=sigma,
                rast1=slope,
            )
    else:
        grass.verbose("No slope mask created")
    ##################################################
    if flags["l"] is True:
        grass.message(
            "Calculating list of possible catchment"
            " configurations...\ncost value | catchment area"
        )
        areadict = {}
        out2dictnum(
            "r.stats -Aani input=" + cost + " separator=, nv=* nsteps=255",
            ",",
            areadict,
        )
        testarea = 0
        # start the loop, and list the values
        for key in sorted(areadict):
            testarea = testarea + int(float(areadict[key]))
            grass.message("%s | %s" % (int(key), testarea))
        if flags["c"] is True:
            if bool(options["in_cost"]) is False:
                grass.run_command(
                    "g.rename",
                    overwrite=grass.overwrite(),
                    quiet=True,
                    rast="temporary.cost.%s,%s_cost_surface" % (pid, buff),
                )
                grass.verbose("Cleaning up...(keeping cost map)")
                grass.run_command(
                    "g.remove",
                    quiet=True,
                    flags="f",
                    type="raster",
                    name="cost.reclass.%s" % pid,
                )
            else:
                grass.verbose("Cleaning up...1")
                grass.run_command(
                    "g.remove",
                    quiet=True,
                    flags="f",
                    type="raster",
                    name="cost.reclass.%s" % pid,
                )
        else:
            if bool(options["in_cost"]) is False:
                grass.verbose("Cleaning up...2")
                grass.run_command(
                    "g.remove",
                    quiet=True,
                    flags="f",
                    type="raster",
                    name="cost.reclass.%s,temporary.cost.%s" % (pid, pid),
                )
            else:
                grass.verbose("Cleaning up...3")
                grass.run_command(
                    "g.remove",
                    quiet=True,
                    flags="f",
                    type="raster",
                    name="cost.reclass.%s" % pid,
                )
        if bool(options["sigma"]) is True:
            grass.run_command(
                "g.remove", quiet=True, flags="f", type="raster", name=slope
            )
        if ismask == 2:
            grass.message("Reinstating original MASK...")
            grass.run_command(
                "g.rename",
                overwrite=grass.overwrite(),
                quiet="True",
                rast=tempmask + ",MASK",
            )
        elif ismask == 0 and bool(options["sigma"]) is True:
            grass.run_command(
                "g.remove", quiet=True, flags="f", type="raster", name="MASK"
            )
        elif ismask == 1:
            grass.message("Keeping original MASK")
        grass.verbose("     DONE!")
        return
    else:
        areadict = {}
        out2dictnum(
            "r.stats -Aani input=" + cost + " separator=, nv=* nsteps=255",
            ",",
            areadict,
        )
        tot_area = 0
        for key in sorted(areadict):
            tot_area = tot_area + int(float(areadict[key]))
            maxcost = key
        grass.message(
            "Maximum cost distance value %s covers an area of %s"
            " square map units" % (int(maxcost), tot_area)
        )
        grass.verbose("Commencing to find a catchment configuration.....")
        testarea = 0
        lastarea = 0
        lastkey = 0
        # start the loop, and home in on the target range
        for key in sorted(areadict):
            testarea = testarea + int(float(areadict[key]))
            if testarea >= area:
                break
            lastkey = key
            lastarea = testarea
        if (testarea - area) <= (area - lastarea):
            cutoff = key
            displayarea = testarea
        else:
            cutoff = lastkey
            displayarea = lastarea
        grass.verbose("Catchment configuration found!")
        grass.message(
            "Cost cutoff %s produces a catchment of %s square map "
            "units." % (int(cutoff), displayarea)
        )
        ####################################################
        grass.verbose("Creating output map")
        t = grass.tempfile()
        temp = open(t, "w+")
        temp.write("0 thru %s = %s\n" % (int(cutoff), mapval))
        temp.flush()
        grass.run_command(
            "r.reclass",
            overwrite=grass.overwrite(),
            input=cost,
            output="cost.reclass.%s" % pid,
            rules=t,
        )
        temp.close()
        grass.mapcalc(
            "${out}=if(isnull(${cost}), null(), ${cost})",
            overwrite=grass.overwrite(),
            quiet=True,
            cost="cost.reclass.%s" % pid,
            out=buff,
        )
        grass.verbose("The output catchment map will be named %s" % buff)
        grass.run_command("r.colors", quiet=True, map=buff, color="ryb")
        if flags["c"] is True:
            if bool(options["in_cost"]) is False:
                grass.run_command(
                    "g.rename",
                    overwrite=grass.overwrite(),
                    quiet=True,
                    rast="temporary.cost.%s,%s_cost_surface" % (pid, buff),
                )
                grass.verbose("Cleaning up...(keeping cost map)")
                grass.run_command(
                    "g.remove",
                    quiet=True,
                    flags="f",
                    type="raster",
                    name="cost.reclass.%s" % pid,
                )
            else:
                grass.verbose("Cleaning up...1")
                grass.run_command(
                    "g.remove",
                    quiet=True,
                    flags="f",
                    type="raster",
                    name="cost.reclass.%s" % pid,
                )
        else:
            if bool(options["in_cost"]) is False:
                grass.verbose("Cleaning up...2")
                grass.run_command(
                    "g.remove",
                    quiet=True,
                    flags="f",
                    type="raster",
                    name="cost.reclass.%s,temporary.cost.%s" % (pid, pid),
                )
            else:
                grass.verbose("Cleaning up...3")
                grass.run_command(
                    "g.remove",
                    quiet=True,
                    flags="f",
                    type="raster",
                    name="cost.reclass.%s" % pid,
                )
        if bool(options["sigma"]) is True:
            grass.run_command(
                "g.remove", quiet=True, flags="f", type="raster", name=slope
            )
        if ismask == 2:
            grass.message("Reinstating original MASK...")
            grass.run_command(
                "g.rename",
                overwrite=grass.overwrite(),
                quiet="True",
                rast=tempmask + ",MASK",
            )
        elif ismask == 0 and bool(options["sigma"]) is True:
            grass.run_command(
                "g.remove", quiet=True, flags="f", type="raster", name="MASK"
            )
        elif ismask == 1:
            grass.message("Keeping original MASK")
        grass.verbose("     DONE!")
        return


# Here is where the code in "main" actually gets executed.
# This way of programming is necessary for the way g.parser needs to
# run in GRASS 7.
if __name__ == "__main__":
    options, flags = grass.parser()
    main()
    exit(0)
