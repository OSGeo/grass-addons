#!/usr/bin/env python3
#
############################################################################
#
# MODULE:       r.slopeunits.create for GRASS 8
# AUTHOR(S):    Ivan Marchesini, Massimiliano Alvioli, Markus Metz (Refactoring)
# PURPOSE:      To create a raster layer of slope units
# COPYRIGHT:    (C) 2004-2024 by the GRASS Development Team
#
#               This program is free software under the GNU General Public
#               License (>=v2). Read the file COPYING that comes with GRASS
#               for details.
#
#############################################################################
#
# %module
# % description: Create a raster layer of slope units
# % keywords: raster
# % keywords: elevation
# % keywords: slopeunits
# %end

# %option G_OPT_R_INPUT
# % key: demmap
# % description: Input digital elevation model
# % required: yes
# %end

# %option G_OPT_R_INPUT
# % key: plainsmap
# % description: Input raster map of alluvial plains
# % required: no
# %end

# %option G_OPT_R_OUTPUT
# % key: slumap
# % description: Output Slope Units layer (the main output)
# % required: yes
# %end

# %option G_OPT_V_OUTPUT
# % key: slumapvect
# % description: Output Slope Units layer as vector layer
# % required: no
# %end

# %option G_OPT_R_OUTPUT
# % key: circvarmap
# % description: Output Circular Variance layer
# % required: no
# %end

# %option G_OPT_R_OUTPUT
# % key: areamap
# % description: Output Area layer; values in square meters
# % required: no
# %end

# %option
# % key: thresh
# % type: double
# % description: Initial threshold (m^2).
# % required: yes
# %end

# %option
# % key: areamin
# % type: double
# % description: Minimum area (m^2) below which the slope unit is not further segmented
# % required: yes
# %end

# %option
# % key: areamax
# % type: double
# % description: Maximum area (m^2) above which the slope unit is segmented irrespective of aspect
# % required: no
# %end

# %option
# % key: cvmin
# % type: double
# % description: Minimum value of the circular variance (0.0-1.0) below which the slope unit is not further segmented
# % required: yes
# %end

# %option
# % key: rf
# % type: integer
# % description: Factor used to iterativelly reduce initial threshold: newthresh=thresh-thresh/reductionfactor
# % required: yes
# %end

# %option
# % key: maxiteration
# % type: integer
# % description: maximum number of iteration to do before the procedure is in any case stopped
# % required: yes
# %end

# %option
# % key: generalize_treshold
# % type: double
# % description: Threshold for maximal tolerance value for v.generalize
# % options: 0-1000000000
# % answer: 20
# %end

# %option
# % key: convergence
# % type: integer
# % label: Convergence factor for MFD in r.watershed (1-10)
# % description: 1 = most diverging flow, 10 = most converging flow. Recommended: 5
# % answer: 5
# %end

# %flag
# % key: g
# % description: Generalize Slope Units vector layer
# % guisection: flags
# %end

# %flag
# % key: s
# % label: SFD (D8) flow in r.watershed (default is MFD)
# % description: SFD: single flow direction, MFD: multiple flow direction
# % guisection: flags
# %end

# %rules
# % requires: -g,slumapvect
# %end

# pylint: disable=C0302 (too-many-lines)

import atexit
import os

# import sys

import grass.script as gs

# initialize global vars
rm_rasters = []
rm_vectors = []


def cleanup():
    """Cleanup function"""
    nuldev = open(os.devnull, "w")
    kwargs = {"flags": "f", "quiet": True, "stderr": nuldev}
    for rmrast in rm_rasters:
        if gs.find_file(name=rmrast, element="cell")["file"]:
            gs.run_command("g.remove", type="raster", name=rmrast, **kwargs)
    for rmvect in rm_vectors:
        if gs.find_file(name=rmvect, element="vector")["file"]:
            gs.run_command("g.remove", type="vector", name=rmvect, **kwargs)

    if gs.find_file("MASK")["file"]:
        # gs.run_command('r.mask', flags='r')
        gs.run_command("g.remove", type="raster", name="MASK", flags="f", quiet=True)


def slope_units(
    dem=None,
    plains=None,
    slumap=None,
    circvarmap=None,
    areamap=None,
    thr=-1.0,
    amin=-1.0,
    cvarmin=-1.0,
    red=-1,
    maxiter=0,
    convergence=5,
):
    """core slope unit calculation"""

    global rm_rasters, rm_vectors
    global thc

    # estimating values of parameters in cells units
    region = gs.region()
    nsres = region["nsres"]
    ewres = region["ewres"]
    thc = int(thr / (nsres * ewres))
    aminc = int(amin / (nsres * ewres))
    if options["areamax"]:
        # in square meters
        amax = float(options["areamax"])
        # in cells units
        amaxc = int(amax / (nsres * ewres))

    # a MASK must not exist already
    if gs.find_file(name="MASK", element="cell")["file"]:
        gs.fatal("Please remove the raster MASK first, before running this module")

    # setting the mask on the DTM
    exp = "$out = if(isnull($mask), null(), 1)"
    gs.mapcalc(exp, out="MASK", mask=dem, quiet=True)
    rm_rasters.append("MASK")

    # generating the aspect layer
    gs.run_command(
        "r.slope.aspect",
        elevation=dem,
        aspect="aspectslutmp",
        quiet=True,
    )
    rm_rasters.append("aspectslutmp")

    # printing something
    gs.message(f"Initial threshold (cells) is : {thc}")
    gs.message(f"Initial minimum area (cells) is : {aminc}")

    # calculating sin and cosin of the aspect layer
    exp = "$out = cos($a)"
    gs.mapcalc(exp, out="coseno", a="aspectslutmp", quiet=True)
    exp = "$out = sin($a)"
    gs.mapcalc(exp, out="seno", a="aspectslutmp", quiet=True)

    gs.run_command(
        "g.remove", type="raster", name="aspectslutmp", flags="f", quiet=True
    )
    rm_rasters.append("coseno")
    rm_rasters.append("seno")

    # setting counters and base layers for the next "while loop"
    counter = 0
    last_counter = counter - 1
    control = 1
    i = gs.raster_info(dem)
    # control_lastrun = int(i["cells"])
    gs.mapcalc("$out = null()", out="slu_r_0", quiet=True)
    gs.mapcalc("$out = null()", out="cvar_0", quiet=True)
    gs.mapcalc("$out = null()", out="count_0", quiet=True)
    gs.mapcalc("$out = 1", out="slu_r_todo", quiet=True)
    gs.mapcalc("$out = 1", out="slu_r_todo_0", quiet=True)
    rm_rasters.append("slu_r_0")
    rm_rasters.append("cvar_0")
    rm_rasters.append("count_0")
    rm_rasters.append("slu_r_todo")
    rm_rasters.append("slu_r_todo_0")

    # starting the loop. The loop stops when: there are no halfbasins extracted
    # (control=0),
    # OR the number of allowed iteration is exceeded (counter>maxiter) OR the
    # threshold
    # (cells) is greater/equal than the reduction factor (thc >= red) otherwise
    # int(thc-thc/red)
    # remains equal to thc
    while control > 0 and counter < maxiter and thc >= red:

        # generating half-basins
        # gs.run_command(
        #     'r.watershed',
        #     elevation=dem,
        #     hbasin='slu_r_tmp',
        #     thresh=thc,
        #     flags='abs',
        #     overwrite=True,
        #     quiet=True,
        # )
        gs.run_command(
            "g.remove", type="raster", name="slu_r_tmp", flags="f", quiet=True
        )
        if flags["s"]:
            rwflags = "abs"
        else:
            rwflags = "ab"
        gs.run_command(
            "r.watershed",
            elevation=dem,
            hbasin="slu_r_tmp",
            thresh=thc,
            convergence=convergence,
            flags=rwflags,
            quiet=True,
        )
        rm_rasters.append("slu_r_tmp")

        # remove output map from previous run
        gs.run_command("g.remove", type="raster", name="slu_r", flags="f", quiet=True)
        if plains:
            exp = "$out = if(isnull($a), $b, null())"
            gs.mapcalc(exp, out="slu_r", a=plains, b="slu_r_tmp", quiet=True)
        else:
            gs.run_command("g.copy", rast="slu_r_tmp,slu_r", quiet=True)

        rm_rasters.append("slu_r")

        if gs.find_file(name="MASK", element="cell")["file"]:
            gs.run_command("r.mask", flags="r", quiet=True)
        exp = "$out = if(isnull($mask), null(), 1)"
        gs.mapcalc(exp, out="MASK", mask="slu_r_todo", quiet=True)

        if gs.find_file(name="count", element="cell")["file"]:
            gs.run_command(
                "g.remove",
                type="raster",
                name="count",
                flags="f",
                quiet=True,
            )

        gs.run_command(
            "r.stats.zonal",
            base="slu_r",
            cover="coseno",
            method="count",
            output="count",
            quiet=True,
        )
        rm_rasters.append("count")

        if gs.find_file(name="sumcoseno", element="cell")["file"]:
            gs.run_command(
                "g.remove",
                type="raster",
                name="sumcoseno",
                flags="f",
                quiet=True,
            )
        gs.run_command(
            "r.stats.zonal",
            base="slu_r",
            cover="coseno",
            method="sum",
            output="sumcoseno",
            quiet=True,
        )
        rm_rasters.append("sumcoseno")

        if gs.find_file(name="sumseno", element="cell")["file"]:
            gs.run_command(
                "g.remove",
                type="raster",
                name="sumseno",
                flags="f",
                quiet=True,
            )
        gs.run_command(
            "r.stats.zonal",
            base="slu_r",
            cover="seno",
            method="sum",
            output="sumseno",
            quiet=True,
        )
        rm_rasters.append("sumseno")

        # creating, for each half-basin, the layer where the circular variance
        # is stored (cvar).
        # Circular variance is 1-R/n, R is the magnitude of the vectorial sum
        # of all the unit
        # vectors of the aspect layer in each polygon and n is the number of
        # unit vectors (and
        # cells) involved in the sum
        exp = "$out = 1 - ((sqrt(($a)^2 + ($b)^2)) / $c)"
        if gs.find_file(name="cvar", element="cell")["file"]:
            gs.run_command(
                "g.remove", type="raster", name="cvar", flags="f", quiet=True
            )
        gs.mapcalc(
            exp,
            out="cvar",
            a="sumseno",
            b="sumcoseno",
            c="count",
            quiet=True,
        )
        rm_rasters.append("cvar")

        gs.run_command("r.mask", flags="r", quiet=True)

        # selecting half-basins where area is larger than the minimum area and
        # the average
        # unit vector is smaller than the unit vector threshold
        gs.run_command(
            "g.remove", type="raster", name="slu_r_todo", flags="f", quiet=True
        )
        if options["areamax"]:
            exp = "$out = if($a > $f || ($a > $b && $c > $d), $g, null())"
            gs.mapcalc(
                exp,
                out="slu_r_todo",
                a="count",
                b=aminc,
                c="cvar",
                d=cvarmin,
                g="slu_r",
                f=amaxc,
                quiet=True,
            )
            gs.run_command(
                "g.copy",
                rast=(f"count,count_prova_{counter}"),
                quiet=True,
            )
            rm_rasters.append(f"count_prova_{counter}")
            # exp = "$out = if($a>$b,1,null())"
            # gs.mapcalc(
            #     exp, out = "slu_r_large"+str(counter),
            #     a = "count", b = amaxc , overwrite=True, quiet=True)
        else:
            exp = "$out = if($a > $b && $c > $d, $g, null())"
            gs.mapcalc(
                exp,
                out="slu_r_todo",
                a="count",
                b=aminc,
                c="cvar",
                d=cvarmin,
                g="slu_r",
                quiet=True,
            )

        # checking that there actually are half-basins with area greater than
        # areamin
        # and circular variance greater than cvarmin. otherwise the loop exits
        stats = gs.read_command("r.univar", flags="g", map="slu_r_todo", quiet=True)
        keyval = gs.parse_key_val(stats)
        # ivan
        # if there are any non-NULL cells
        if int(keyval["n"]) > 0:
            # if kv.has_key("n"):
            # increasing counter
            last_counter = counter
            counter = counter + 1
            # patching the current half-basins, cvar and counter that were not
            # selected
            # in the previous steps with those that come from the previous step
            # of the loop
            gs.run_command(
                "g.copy",
                rast=(f"slu_r_todo,slu_r_todo_{counter}"),
                quiet=True,
            )
            rm_rasters.append(f"slu_r_todo_{counter}")
            gs.run_command("r.mask", raster="slu_r_todo", flags="i", quiet=True)
            gs.run_command(
                "r.patch",
                input=("slu_r_" + str(last_counter), "slu_r"),
                output="slu_r_" + str(counter),
                quiet=True,
            )
            rm_rasters.append(f"slu_r_{counter}")
            gs.run_command(
                "g.copy",
                rast=("slu_r_" + str(counter), "slu_r_prova_" + str(counter)),
                quiet=True,
            )
            rm_rasters.append(f"slu_r_prova_{counter}")
            gs.run_command(
                "r.patch",
                input=("cvar_" + str(last_counter), "cvar"),
                output="cvar_" + str(counter),
                quiet=True,
            )
            rm_rasters.append(f"cvar_{counter}")
            gs.run_command(
                "r.patch",
                input=("count_" + str(last_counter), "count"),
                output="count_" + str(counter),
                quiet=True,
            )
            rm_rasters.append(f"count_{counter}")

            gs.run_command("r.mask", flags="r", quiet=True)

            # rejecting partition if average area of new half-basins is less
            # than amin;
            # not effective on large areas, if areamax is present
            if counter > 0:  # counter is always > 0 ?
                if options["areamax"]:
                    # this block does not make sense,
                    # count_prova_<last_counter> has been calculated above
                    if counter == 1:
                        gs.mapcalc("$out = 1", out="count_prova_0", quiet=True)
                    exp = "$out = if($a > $b, 1, null())"
                    # this
                    # a="count_prova_" + str(last_counter - 1)
                    # can not work if counter = 1 and last_counter = 0
                    # because the result would be "count_prova_-1"
                    # changed to
                    # a="count_prova_" + str(last_counter)
                    gs.mapcalc(
                        exp,
                        out="slu_r_large" + str(counter),
                        a="count_prova_" + str(last_counter),
                        b=amaxc,
                        quiet=True,
                    )
                    rm_rasters.append(f"slu_r_large{counter}")
                    exp = "$out = if(isnull($a), $b, null())"
                    gs.mapcalc(
                        exp,
                        out="MASK",
                        a="slu_r_large" + str(counter),
                        b="slu_r_" + str(counter),
                        quiet=True,
                    )
                    gs.run_command(
                        "g.copy",
                        rast="MASK,mask" + str(counter),
                        quiet=True,
                    )
                else:
                    gs.run_command("r.mask", raster="slu_r_" + str(counter), quiet=True)

                stats_lc = gs.read_command(
                    "r.univar",
                    flags="g",
                    map="slu_r_todo_" + str(last_counter),
                    quiet=True,
                )
                kv_lc = gs.parse_key_val(stats_lc)

                #                gs.message(("Univar: %s") % kv_lc )
                # ivan
                # if kv_lc.has_key("n"):
                # if there are any non-NULL cells
                if int(kv_lc["n"]) > 0:
                    en_int = int(kv_lc["n"])
                    gs.message(f"Univar: {en_int}")
                    if en_int > 0:
                        gs.run_command(
                            "r.statistics",
                            base="slu_r_todo_" + str(last_counter),
                            cover="slu_r",
                            method="diversity",
                            output="slu_diversity_" + str(counter),
                            quiet=True,
                        )
                        rm_rasters.append(f"slu_diversity_{counter}")
                        rm_rasters.append(f"slu_r_todo_{last_counter}")
                        # gs.run_command('r.univar', map='slu_r')
                        # gs.run_command(
                        #     'r.univar', map='slu_r_todo_'+str(last_counter))
                        # gs.run_command(
                        #     'r.univar', map='slu_diversity_'+str(counter))
                        gs.run_command(
                            "r.stats.zonal",
                            base="slu_r_todo_" + str(last_counter),
                            cover="coseno",
                            method="count",
                            output="todocount_" + str(counter),
                            quiet=True,
                        )
                        rm_rasters.append(f"todocount_{counter}")
                        exp = "$out = $d / $a"
                        gs.mapcalc(
                            exp,
                            out="slu_r_test_" + str(counter),
                            a="@slu_diversity_" + str(counter),
                            d="todocount_" + str(counter),
                            quiet=True,
                        )
                        rm_rasters.append(f"slu_r_test_{counter}")
                        exp = "$out = if($d < $e, $c, null())"
                        gs.mapcalc(
                            exp,
                            out="slu_r_corr_" + str(counter),
                            b="slu_r_" + str(counter),
                            c="slu_r_todo_" + str(last_counter),
                            d="slu_r_test_" + str(counter),
                            e=aminc,
                            quiet=True,
                        )
                        rm_rasters.append(f"slu_r_corr_{counter}")
                        gs.run_command("r.mask", flags="r", quiet=True)

                        gs.run_command(
                            "g.rename",
                            rast=f"slu_r_{counter},slu_r_tmp_{counter}",
                            quiet=True,
                        )
                        rm_rasters.append(f"slu_r_tmp_{counter}")
                        gs.run_command(
                            "r.patch",
                            input=(
                                "slu_r_corr_" + str(counter),
                                "slu_r_tmp_" + str(counter),
                            ),
                            output="slu_r_" + str(counter),
                            quiet=True,
                        )
                        gs.run_command(
                            "g.remove",
                            type="raster",
                            name=f"slu_r_tmp_{counter}",
                            flags="f",
                            quiet=True,
                        )
                        rm_rasters.append(f"slu_r_{counter}")
                    else:
                        gs.run_command("r.mask", flags="r", quiet=True)
                else:
                    gs.run_command("r.mask", flags="r", quiet=True)

            control = int(keyval["n"])
            thc = int(thc - thc / red)
            thhect = thc * nsres * ewres / 10000
            gs.message((f"Threshold (hectars) is: {thhect}"))
            gs.message(
                (
                    "No. of cells to be still classified as SLU is: "
                    f"{control}. Loop done: {counter}"
                )
            )
        else:
            # exit the loop
            gs.message(("Nothing to do, ready to write the outputs"))
            control = 0

    # depending on how the while loop is exited the slu_r_$counter may have
    # some small holes. Here we fill them.
    exp = "$out = if(isnull($a), $b, $a)"
    gs.mapcalc(
        exp,
        out="slu_r_final",
        a="slu_r_" + str(counter),
        b="slu_r",
        quiet=True,
    )
    exp = "$out = $a"
    gs.mapcalc(
        exp,
        out="cvar_final",
        a="cvar_" + str(counter),
        quiet=True,
    )
    exp = "$out = $a"
    gs.mapcalc(
        exp,
        out="count_final",
        a="count_" + str(counter),
        quiet=True,
    )

    # preparing the outputs
    exp = "$out = $a"
    gs.mapcalc(exp, out="slumap_1", a="slu_r_final", quiet=True)
    # add areas where DEM exists, and SUs do not exist
    if options["plainsmap"]:
        exp = (
            "$out = if(isnull($a), if(isnull($b), if(isnull($c),"
            "null(), 1), null()), $a)"
        )
        gs.mapcalc(
            exp,
            a="slumap_1",
            b=plains,
            c=dem,
            out="slumap_2",
            quiet=True,
        )
    else:
        exp = "$out = if(isnull($a), if(isnull($c), null(), 1), $a)"
        gs.mapcalc(exp, a="slumap_1", c=dem, out="slumap_2", quiet=True)
    gs.run_command("r.clump", input="slumap_2", output=slumap, quiet=True)
    gs.run_command("g.remove", type="raster", name="slumap_1", flags="f", quiet=True)
    gs.run_command("g.remove", type="raster", name="slumap_2", flags="f", quiet=True)

    gs.run_command("r.colors", map="slu_r_final", color="random", quiet=True)

    if circvarmap:
        gs.message(f"Writing out {circvarmap}")
        exp = "$out = $a"
        gs.mapcalc(exp, out=circvarmap, a="cvar_final", quiet=True)
    if areamap:
        gs.message(f"Writing out {areamap}")
        exp = "$out = $a * $b * $c"
        gs.mapcalc(
            exp,
            out=areamap,
            a="count_final",
            b=nsres,
            c=ewres,
            quiet=True,
        )

    # clean up
    if gs.find_file(name="MASK", element="cell")["file"]:
        gs.run_command("r.mask", flags="r", quiet=True)
    gs.run_command("g.remove", type="raster", name="seno,coseno", flags="f", quiet=True)

    gs.run_command("g.remove", type="raster", name="slu_r_todo", flags="f", quiet=True)
    gs.run_command(
        "g.remove",
        type="raster",
        name="slu_r_final,cvar_final,count_final,slu_r_todo_final",
        flags="f",
        quiet=True,
    )

    for i in range(1, counter + 1):
        mapname = "slu_diversity_" + str(i)
        gs.run_command("g.remove", type="raster", name=mapname, flags="f", quiet=True)

    for i in range(counter + 1):
        mapname = "slu_r_" + str(i)
        gs.run_command("g.remove", type="raster", name=mapname, flags="f", quiet=True)
        mapname = "cvar_" + str(i)
        gs.run_command("g.remove", type="raster", name=mapname, flags="f", quiet=True)
        mapname = "count_" + str(i)
        gs.run_command("g.remove", type="raster", name=mapname, flags="f", quiet=True)
        mapname = "slu_r_todo_" + str(i)
        gs.run_command("g.remove", type="raster", name=mapname, flags="f", quiet=True)

    gs.message("Slope units calculated.")


def export_as_vect(slumap, slumapvect):
    """Create vector map from raster map"""
    gs.run_command("r.to.vect", type="area", input=slumap, output=slumapvect)
    threshold = options["generalize_treshold"]
    if flags["g"]:
        gs.run_command(
            "v.generalize",
            input=slumapvect,
            output=f"{slumapvect}_gen",
            method="douglas",
            threshold=threshold,
        )


def main():
    """Main function of r.slopeunits"""
    global rm_rasters, rm_vectors
    global thc

    dem = options["demmap"]
    plains = None
    if options["plainsmap"]:
        plains = options["plainsmap"]
    slumap = options["slumap"]
    circvarmap = options["circvarmap"]
    areamap = options["areamap"]
    thr = float(options["thresh"])
    amin = float(options["areamin"])
    cvarmin = float(options["cvmin"])
    red = int(options["rf"])
    maxiter = int(options["maxiteration"])
    convergence = int(options["convergence"])

    slope_units(
        dem,
        plains,
        slumap,
        circvarmap,
        areamap,
        thr,
        amin,
        cvarmin,
        red,
        maxiter,
        convergence,
    )
    if options["slumapvect"]:
        export_as_vect(slumap, options["slumapvect"])

    gs.message("Slope units finished.")


if __name__ == "__main__":
    options, flags = gs.parser()
    atexit.register(cleanup)
    main()
