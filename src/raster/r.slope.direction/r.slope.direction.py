#!/usr/bin/env python

"""
MODULE:       r.slope.direction
AUTHOR(S):    Stefan Blumentrath
PURPOSE:      Calculates slope following a dirction raster
COPYRIGHT:    (C) 2019 by the GRASS Development Team

              This program is free software under the GNU General Public
              License (>=v2). Read the file COPYING that comes with GRASS
              for details.
"""

# %module
# % description: Calculates slope following a direction raster.
# % keyword: raster
# % keyword: slope
# % keyword: direction
# % keyword: neighborhood
# % keyword: stream
# % keyword: trail
# % keyword: trac
# % keyword: path
# % keyword: road
# % keyword: street

# %end
# %option G_OPT_R_ELEV
# % required: YES
# %end
# %option G_OPT_R_INPUT
# % key: direction
# % label: Input Direction raster map
# % required: YES
# %end
# %option
# % key: dir_type
# % label: Direction type
# % description: Type of diretion encoding in diections input raster map (default: auto)
# % options: 45degree,degree,bitmask,bitmask_k,auto
# % type: string
# % required: YES
# % answer: auto
# %end
# %option
# % key: steps
# % label: Number of steps
# % description: Comma separated list of steps in direction for which slope is computed
# % type: string
# % required: YES
# % answer: 1
# %end
# %option
# % key: slope_measure
# % label: Slope measure
# % description: Format for reporting the slope (default: degree)
# % options: difference,percent,percent_int,degree,degree_int
# % type: string
# % required: YES
# % answer: degree
# %end
# %option G_OPT_R_OUTPUTS
# % required: YES
# %end
# %flag
# % key: a
# % label: Compute slope as absolute values
# % description: Compute slope as absolute values (default allows negative slopes)
# %end

# toDo:
# - write tests
# - implement ranges instead of single direction values

import os
import atexit

import grass.script as gscript


def cleanup():
    """Remove temporary maps"""
    nuldev = open(os.devnull, "w")
    gscript.run_command(
        "g.remove",
        flags="f",
        quiet=True,
        type=["raster", "vector"],
        stderr=nuldev,
        pattern="{}*".format(tmpname),
    )


def check_directions(dir_type, dmax):
    """
    Mostly copied from r.path
    Checks if values in directions map are consistent with given
    directions type and guesses directions

    Parameters:
    dir_type (str): Type of encoding for directions in input direction raster map
    dmax (int): Maximum value of input direction raster map

    Returns:
    str: Validated name of encoding for directions in input direction raster map
    """
    if dir_type == "degree":
        if dmax > 360:
            gscript.fatal(_("Directional degrees can not be > 360"))
    elif dir_type == "45degree":
        if dmax > 8:
            gscript.fatal(_("Directional degrees divided by 45 can not be > 8"))
    elif dir_type == "bitmask":
        if dmax > ((1 << 16) - 1):
            gscript.fatal(
                _("Bitmask encoded directions can not be > %d"), (1 << 16) - 1
            )
    elif dir_type == "auto":
        if dmax <= 8:
            gscript.message(
                _(
                    "Input direction format assumed to be degrees CCW from East divided by 45"
                )
            )
            dir_type = "degree_45"
        elif dmax <= ((1 << 8) - 1):
            gscript.message(
                _(
                    "Input direction format assumed to be bitmask encoded without Knight's move"
                )
            )
            dir_type = "bitmask"
        elif dmax <= 360:
            gscript.message(
                _("Input direction format assumed to be degrees CCW from East")
            )
            dir_type = "degree"
        elif dmax <= ((1 << 16) - 1):
            gscript.message(
                _(
                    "Input direction format assumed to be bitmask encoded with Knight's move"
                )
            )
            dir_type = "bitmask_k"
            gscript.fatal(
                _(
                    "Sorry, bitmask direction with Knight's move encoding is not (yet) supported"
                )
            )
        else:
            gscript.fatal(
                _(
                    "Unable to detect format of input direction map <{}>".format(
                        direction
                    )
                )
            )
    else:
        gscript.fatal(_("Invalid directions format '{}'".format(direction)))

    return dir_type


def main():
    """Do the main work"""
    # Define static variables
    global tmpname
    tmpname = gscript.tempname(12)

    # Define user input variables
    a_flag = flags["a"]
    elevation = options["elevation"]
    direction = options["direction"]
    slope_measure = options["slope_measure"]
    outputs = options["output"].split(",")
    dir_format = options["dir_type"]

    try:
        steps = list(map(int, options["steps"].split(",")))
    except:
        gscript.fatal(_("Not all steps given as integer."))

    n_steps = max(steps)

    abs = "abs" if a_flag else ""

    dir_values = gscript.parse_command("r.info", map=direction, flags="r")

    dir_type = check_directions(dir_format, float(dir_values["max"]))

    # Ceck if number of requested steps and outputs match
    if len(outputs) != len(steps):
        gscript.fatal(_("Number of steps and number of output maps differ"))

    # Define static variables
    kwargs_even = {
        "dir": direction,
        "elev_in": "{}_elev_even".format(tmpname),
        "elev_out": "{}_elev_odd".format(tmpname),
    }
    kwargs_odd = {
        "dir": direction,
        "elev_in": "{}_elev_odd".format(tmpname),
        "elev_out": "{}_elev_even".format(tmpname),
    }

    if slope_measure != "difference":
        kwargs_even["dist_in"] = "{}_dist_even".format(tmpname)
        kwargs_even["dist_out"] = "{}_dist_odd".format(tmpname)
        kwargs_even["dist_sum_in"] = "{}_dist_sum_even".format(tmpname)
        kwargs_even["dist_sum_out"] = "{}_dist_sum_odd".format(tmpname)
        kwargs_odd["dist_in"] = "{}_dist_odd".format(tmpname)
        kwargs_odd["dist_out"] = "{}_dist_even".format(tmpname)
        kwargs_odd["dist_sum_in"] = "{}_dist_sum_odd".format(tmpname)
        kwargs_odd["dist_sum_out"] = "{}_dist_sum_even".format(tmpname)

    dir_format_dict = {
        "degree_45": [1, 2, 3, 4, 5, 6, 7],
        "degree": [45, 90, 135, 180, 225, 270, 315],
        "bitmask": [1, 8, 7, 6, 5, 4, 3],
    }

    slope_measure_dict = {
        "difference": """\n{gradient}={abs}({elev}-{elev_in})""",
        "percent": """\n{gradient}={abs}({elev}-{elev_in})/{dist}""",
        "percent_int": """\n{gradient}=round(({abs}(({elev}-{elev_in}))/{dist})*10000.0)""",
        "degree": """\n{gradient}=atan({abs}({elev}-{elev_in})/{dist})""",
        "degree_int": """\n{gradient}=round(atan({abs}({elev}-{elev_in})/{dist})*100.0)""",
    }

    dirs = dir_format_dict[dir_type]

    expression_template = """{{elev_out}}=\
if({{dir}} == {0}, if(isnull({{elev_in}}[-1,1]),{{elev_in}},{{elev_in}}[-1,1]), \
if({{dir}} == {1}, if(isnull({{elev_in}}[-1,0]),{{elev_in}},{{elev_in}}[-1,0]), \
if({{dir}} == {2}, if(isnull({{elev_in}}[-1,-1]),{{elev_in}},{{elev_in}}[-1,-1]), \
if({{dir}} == {3}, if(isnull({{elev_in}}[0,-1]),{{elev_in}},{{elev_in}}[0,-1]), \
if({{dir}} == {4}, if(isnull({{elev_in}}[1,-1]),{{elev_in}},{{elev_in}}[1,-1]), \
if({{dir}} == {5}, if(isnull({{elev_in}}[1,0]),{{elev_in}},{{elev_in}}[1,0]), \
if({{dir}} == {6}, if(isnull({{elev_in}}[1,1]),{{elev_in}},{{elev_in}}[1,1]), \
if(isnull({{elev_in}}[0,1]),{{elev_in}},{{elev_in}}[0,1]))))))))""".format(
        *dirs
    )

    kwargs = {
        "dir": direction,
        "elev_in": elevation,
        "elev_out": "{}_elev_even".format(tmpname),
    }

    if slope_measure != "difference":
        expression_template += """\n{{dist_out}}=\
if({{dir}} == {0}, if(isnull({{dist_in}}[-1,1]),{{dist_in}},{{dist_in}}[-1,1]), \
if({{dir}} == {1}, if(isnull({{dist_in}}[-1,0]),{{dist_in}},{{dist_in}}[-1,0]), \
if({{dir}} == {2}, if(isnull({{dist_in}}[-1,-1]),{{dist_in}},{{dist_in}}[-1,-1]), \
if({{dir}} == {3}, if(isnull({{dist_in}}[0,-1]),{{dist_in}},{{dist_in}}[0,-1]), \
if({{dir}} == {4}, if(isnull({{dist_in}}[1,-1]),{{dist_in}},{{dist_in}}[1,-1]), \
if({{dir}} == {5}, if(isnull({{dist_in}}[1,0]),{{dist_in}},{{dist_in}}[1,0]), \
if({{dir}} == {6}, if(isnull({{dist_in}}[1,1]),{{dist_in}},{{dist_in}}[1,1]), \
if(isnull({{dist_in}}[0,1]),{{dist_in}},{{dist_in}}[0,1]))))))))
{{dist_sum_out}}={{dist_sum_in}}+{{dist_in}}""".format(
            *dirs
        )

        kwargs["dist_in"] = "{}_dist_odd".format(tmpname)
        kwargs["dist_out"] = "{}_dist_even".format(tmpname)
        kwargs["dist_sum_in"] = "{}_dist_sum_odd".format(tmpname)
        kwargs["dist_sum_out"] = "{}_dist_sum_even".format(tmpname)

        # Start processing
        curent_region = gscript.region()

        gscript.run_command(
            "r.mapcalc",
            overwrite=True,
            quiet=True,
            expression="""{dist_in}=\
if({dir} == {NE} || {dir} == {NW} || {dir} == {SW}\
|| {dir} == {SE}, sqrt({ewres}^2+{nsres}^2), \
if({dir} == {N} || {dir} == {S},{nsres},{ewres}))
{dist_sum_in}=0""".format(
                NE=dirs[0],
                NW=dirs[2],
                SW=dirs[4],
                SE=dirs[6],
                N=dirs[1],
                S=dirs[5],
                nsres=curent_region["nsres"],
                ewres=curent_region["ewres"],
                dir=direction,
                dist_in=kwargs["dist_in"],
                dist_sum_in=kwargs["dist_sum_in"],
            ),
        )

    for x in range(max(steps) + 1):
        mc_expression = expression_template.format(**kwargs)

        if x in steps:
            idx = steps.index(x)
            # Compile expression for r.mapcalc
            result_expression = slope_measure_dict[slope_measure]
            # Results are computed for output from previous step
            if slope_measure != "difference":
                result_kwargs = {
                    "elev_in": kwargs["elev_in"],
                    "elev": elevation,
                    "dist": kwargs["dist_sum_in"],
                    "abs": abs,
                    "gradient": outputs[idx],
                }
            else:
                result_kwargs = {
                    "elev_in": kwargs["elev_in"],
                    "elev": elevation,
                    "abs": abs,
                    "gradient": outputs[idx],
                }

            result_expression = result_expression.format(**result_kwargs)

            if x == max(steps):
                mc_expression = result_expression.lstrip("\n")
            else:
                mc_expression += result_expression

        gscript.run_command(
            "r.mapcalc", overwrite=True, quiet=True, expression=mc_expression
        )

        if x in steps:
            gscript.raster.raster_history(outputs[idx])

        # Set variables for next iteration
        # Use even and odd numbers for iterative re-naming
        if x % 2 == 0:
            # Even
            kwargs = kwargs_even
        else:
            # Odd
            kwargs = kwargs_odd

        gscript.percent(x, max(steps), 1)


if __name__ == "__main__":
    options, flags = gscript.parser()
    atexit.register(cleanup)
    main()
