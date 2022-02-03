#!/usr/bin/env python
#
############################################################################
#
# MODULE:       r.viewshed.cva.py
# AUTHOR(S):    Isaac Ullah, additions by Anna Petrasova
# PURPOSE:      Undertakes a "cumulative viewshed analysis" using a vector points map
#               as input "viewing" locations, using r.viewshed to calculate the individual viewsheds.
# COPYRIGHT:    (C) 2015 by Isaac Ullah
# REFERENCES:   r.viewshed
# 		This program is free software under the GNU General Public
# 		License (>=v2). Read the file COPYING that comes with GRASS
# 		for details.
#
#############################################################################


# %module
# % description: Undertakes a "cumulative viewshed analysis" using a vector points map as input "viewing" locations, using r.viewshed to calculate the individual viewsheds.
# % keyword: raster
# % keyword: viewshed
# % keyword: line of sight
# % keyword: LOS
# %end

# %option G_OPT_R_INPUT
# % description: Input elevation map (DEM)
# %END

# %option G_OPT_V_INPUT
# % key: vector
# % description: Name of input vector points map containg the set of points for this analysis.
# %end

# %option G_OPT_R_OUTPUT
# % key: output
# % description: Output cumulative viewshed raster
# %end

# %option
# % key: observer_elevation
# % type: double
# % description: Height of observation points off the ground
# %answer: 1.75
# % required : no
# %end

# %option
# % key: target_elevation
# % type: double
# % description: Height of target areas off the ground
# %answer: 1.75
# % required : no
# %end

# %option
# % key: max_distance
# % type: double
# % description: Maximum visibility radius. By default infinity (-1)
# %answer: -1
# % required : no
# %end

# %option
# % key: memory
# % type: integer
# % description: Amount of memory to use (in MB)
# %answer: 500
# % required : no
# %end

# %option
# % key: refraction_coeff
# % type: double
# % description: Refraction coefficient (with flag -r)
# %answer: 0.14286
# % options: 0.0-1.0
# % required : no
# %end

# %option G_OPT_DB_COLUMN
# % key: name_column
# % description: Database column for point names (with flag -k)
# % required : no
# %end


# %flag
# % key: k
# % description:  Keep all interim viewshed maps produced by the routine (maps will be named "vshed_'name'_uniquenumber", where 'name' is the value in "name_column" for each input point. If no value specified in "name_column", cat value will be used instead)
# %end

# %flag
# % key: c
# % description: Consider the curvature of the earth (current ellipsoid)
# %end

# %flag
# % key: r
# % description: Consider the effect of atmospheric refraction
# %end

# %flag
# % key: b
# % description: Output format is {0 (invisible) 1 (visible)}
# %end

# %flag
# % key: e
# % description:  Output format is invisible = NULL, else current elev - viewpoint_elev
# %end


import sys
import os
import grass.script as grass


# main block of code starts here
def main():
    # bring in input variables
    elev = options["input"]
    vect = options["vector"]
    viewshed_options = {}
    for option in (
        "observer_elevation",
        "target_elevation",
        "max_distance",
        "memory",
        "refraction_coeff",
    ):
        viewshed_options[option] = options[option]
    out = options["output"]
    # assemble flag string
    flagstring = ""
    if flags["r"]:
        flagstring += "r"
    if flags["c"]:
        flagstring += "c"
    if flags["b"]:
        flagstring += "b"
    if flags["e"]:
        flagstring += "e"

    # check if vector map exists
    gfile = grass.find_file(vect, element="vector")
    if not gfile["name"]:
        grass.fatal(_("Vector map <%s> not found") % vect)

    # get the coords from the vector map, and check if we want to name them
    if flags["k"] and options["name_column"] != "":
        # note that the "r" flag will constrain to points in the current geographic region.
        output_points = grass.read_command(
            "v.out.ascii",
            flags="r",
            input=vect,
            type="point",
            format="point",
            separator=",",
            columns=options["name_column"],
        ).strip()
    else:
        # note that the "r" flag will constrain to points in the current geographic region.
        output_points = grass.read_command(
            "v.out.ascii",
            flags="r",
            input=vect,
            type="point",
            format="point",
            separator=",",
        ).strip()
    grass.message(
        _(
            "Note that the routine is constrained to points in the current geographic region."
        )
    )
    # read the coordinates, and parse them up.
    masterlist = []
    for line in output_points.splitlines():
        if line:  # see ticket #3155
            masterlist.append(line.strip().split(","))
    # now, loop through the master list and run r.viewshed for each of the sites,
    # and append the viewsheds to a list (so we can work with them later)
    vshed_list = []
    counter = 0
    for site in masterlist:
        if flags["k"] and options["name_column"] != "":
            ptname = site[3]
        else:
            ptname = site[2]
        grass.verbose(
            _("Calculating viewshed for location %s,%s (point name = %s)")
            % (site[0], site[1], ptname)
        )
        # need additional number for cases when points have the same category (e.g. from v.to.points)
        tempry = "vshed_{ptname}_{c}".format(ptname=ptname, c=counter)
        counter += 1
        vshed_list.append(tempry)
        grass.run_command(
            "r.viewshed",
            quiet=True,
            overwrite=grass.overwrite(),
            flags=flagstring,
            input=elev,
            output=tempry,
            coordinates=site[0] + "," + site[1],
            **viewshed_options
        )
    # now make a mapcalc statement to add all the viewsheds together to make the outout cumulative viewsheds map
    grass.message(_("Calculating cumulative viewshed map <%s>") % out)
    # when binary viewshed, r.series has to use sum instead of count
    rseries_method = "sum" if "b" in flagstring else "count"
    grass.run_command(
        "r.series",
        quiet=True,
        overwrite=grass.overwrite(),
        input=(",").join(vshed_list),
        output=out,
        method=rseries_method,
    )
    if flags["e"]:
        grass.run_command("r.null", quiet=True, map=out, setnull="0")
    # Clean up temporary maps, if requested
    if flags["k"]:
        grass.message(_("Temporary viewshed maps will not removed"))
    else:
        grass.message(_("Removing temporary viewshed maps"))
        grass.run_command(
            "g.remove",
            quiet=True,
            flags="f",
            type="raster",
            name=(",").join(vshed_list),
        )
    return


# here is where the code in "main" actually gets executed. This way of programming is neccessary for the way g.parser needs to run.
if __name__ == "__main__":
    options, flags = grass.parser()
    main()
