#!/usr/bin/env python

############################################################################
#
# MODULE:    r.local.relief
# AUTHOR(S): Vaclav Petras <wenzeslaus gmail.com>,
#            Eric Goddard <egoddard memphis.edu>
# PURPOSE:   Create a local relief model from elevation map
# COPYRIGHT: (C) 2013 by the GRASS Development Team
#
#            This program is free software under the GNU General Public
#            License (>=v2). Read the file COPYING that comes with GRASS
#            for details.
#
#############################################################################

# %module
# % description: Creates a local relief model from elevation map.
# % keyword: raster
# % keyword: elevation
# % keyword: terrain
# % keyword: relief
# % keyword: LRM
# % keyword: visualization
# %end
# %option
# % type: string
# % gisprompt: old,cell,raster
# % key: input
# % description: Name of the input elevation raster map
# % required: yes
# %end
# %option
# % type: string
# % gisprompt: new,cell,raster
# % key: output
# % description: Name for output local relief map
# % required: yes
# %end
# %option
# % key: neighborhood_size
# % type: integer
# % label: Smoothing neighborhood size
# % description: Neighborhood size used when smoothing the elevation model
# % options: 0-
# % answer: 11
# %end
# %option
# % key: color_table
# % type: string
# % label: Color table for the local relief model raster map
# % description: If not provided, grey is used for output and differences is used for the shaded_output
# % required: no
# % options: grey, differences
# % guisection: Color
# %end
# %option G_OPT_R_OUTPUT
# % key: shaded_output
# % required: no
# % label: Local relief combined with shaded relief
# % description: Local relief model combined with shaded relief of the original elevation
# % guisection: Color
# %end
# %flag
# % key: i
# % description: Save intermediate maps
# %end
# %flag
# % key: v
# % label: Use bspline interpolation to construct the surface
# % description: Uses v.surf.bspline cubic interpolation instead of r.fillnulls cubic interpolation.
# %end
# %flag
# % key: n
# % description: Invert colors in the color table
# % guisection: Color
# %end
# %flag
# % key: g
# % description: Logarithmic scaling of the color table
# % guisection: Color
# %end
# %flag
# % key: f
# % description: Do not perform histogram equalization on the color table
# % guisection: Color
# %end


import os
import atexit

import grass.script as gscript
import grass.script.core as gcore


RREMOVE = []
VREMOVE = []


def cleanup():
    if RREMOVE or VREMOVE:
        gcore.info(_("Cleaning temporary maps..."))
    for rast in RREMOVE:
        gscript.run_command("g.remove", flags="f", type="raster", name=rast, quiet=True)
    for vect in VREMOVE:
        gscript.run_command("g.remove", flags="f", type="vector", name=vect, quiet=True)


def create_tmp_map_name(name):
    return "{mod}_{pid}_{map_}_tmp".format(
        mod="r_local_relief", pid=os.getpid(), map_=name
    )


def create_persistent_map_name(basename, name):
    return "{basename}_{name}".format(basename=basename, name=name)


def check_map_name(name, mapset, element_type):
    if gscript.find_file(name, element=element_type, mapset=mapset)["file"]:
        gscript.fatal(
            _(
                "Raster map <%s> already exists. "
                "Change the base name or allow overwrite."
            )
            % name
        )


def main():
    atexit.register(cleanup)
    options, flags = gscript.parser()

    elevation_input = options["input"]
    local_relief_output = options["output"]
    neighborhood_size = int(options["neighborhood_size"])
    save_intermediates = flags["i"]
    bspline = flags["v"]  # when bspline == False, r.fillnulls is used

    shaded_local_relief_output = options["shaded_output"]

    # constants
    fill_method = "bicubic"
    # color table changed from difference to grey to histogram equalized-grey
    # It does make more sense to use that since many archaeologists use the same
    # color scheme for magnetometry and gpr data.
    color_table = options["color_table"]
    if color_table:
        user_color_table = True
    else:
        user_color_table = False
    rcolors_flags = "e"
    if flags["f"]:
        rcolors_flags = ""
    if flags["g"]:
        rcolors_flags += "g"
    if flags["n"]:
        rcolors_flags += "n"

    if save_intermediates:

        def local_create(name):
            """create_persistent_map_name with hard-coded first argument"""
            basename = local_relief_output.split("@")[0]
            return create_persistent_map_name(basename=basename, name=name)

        create_map_name = local_create
    else:
        create_map_name = create_tmp_map_name

    smooth_elevation = create_map_name("smooth_elevation")
    subtracted_smooth_elevation = create_map_name("subtracted_smooth_elevation")
    vector_contours = create_map_name("vector_contours")
    raster_contours_with_values = create_map_name("raster_contours_with_values")
    purged_elevation = create_map_name("purged_elevation")

    if bspline:
        contour_points = create_map_name("contour_points")
    else:
        raster_contours = create_map_name("raster_contours")

    if shaded_local_relief_output:
        relief_shade = create_map_name("relief_shade")

    # if saving intermediates, keep only 1 contour layer
    if save_intermediates:
        if not bspline:
            RREMOVE.append(raster_contours)
            VREMOVE.append(vector_contours)
    else:
        RREMOVE.append(smooth_elevation)
        RREMOVE.append(subtracted_smooth_elevation)
        VREMOVE.append(vector_contours)
        RREMOVE.append(purged_elevation)
        if bspline:
            VREMOVE.append(contour_points)
        else:
            RREMOVE.append(raster_contours)
            RREMOVE.append(raster_contours_with_values)

    # check even for the temporary maps
    # (although, in ideal world, we should always fail if some of them exists)
    if not gcore.overwrite():
        check_map_name(smooth_elevation, gscript.gisenv()["MAPSET"], "cell")
        check_map_name(subtracted_smooth_elevation, gscript.gisenv()["MAPSET"], "cell")
        check_map_name(vector_contours, gscript.gisenv()["MAPSET"], "vect")
        check_map_name(raster_contours_with_values, gscript.gisenv()["MAPSET"], "cell")
        check_map_name(purged_elevation, gscript.gisenv()["MAPSET"], "cell")
        if bspline:
            check_map_name(contour_points, gscript.gisenv()["MAPSET"], "vect")
        else:
            check_map_name(raster_contours, gscript.gisenv()["MAPSET"], "cell")

    # algorithm according to Hesse 2010 (LiDAR-derived Local Relief Models)
    # step 1 (point cloud to digital elevation model) omitted

    # step 2
    gscript.info(_("Smoothing using r.neighbors..."))
    gscript.run_command(
        "r.neighbors",
        input=elevation_input,
        output=smooth_elevation,
        size=neighborhood_size,
        overwrite=gcore.overwrite(),
    )

    # step 3
    gscript.info(_("Subtracting smoothed from original elevation..."))
    gscript.mapcalc(
        "{c} = {a} - {b}".format(
            c=subtracted_smooth_elevation,
            a=elevation_input,
            b=smooth_elevation,
            overwrite=gcore.overwrite(),
        )
    )

    # step 4
    gscript.info(_("Finding zero contours in elevation difference map..."))
    gscript.run_command(
        "r.contour",
        input=subtracted_smooth_elevation,
        output=vector_contours,
        levels=[0],
        overwrite=gcore.overwrite(),
    )

    # Diverge here if using bspline interpolation
    # step 5
    gscript.info(
        _("Extracting z value from the elevation" " for difference zero contours...")
    )
    if bspline:
        # Extract points from vector contours
        gscript.run_command(
            "v.to.points",
            _input=vector_contours,
            llayer="1",
            _type="line",
            output=contour_points,
            dmax="10",
            overwrite=gcore.overwrite(),
        )

        # Extract original dem elevations at point locations
        gscript.run_command(
            "v.what.rast",
            _map=contour_points,
            raster=elevation_input,
            layer="2",
            column="along",
        )

        # Get mean distance between points to optimize spline interpolation
        mean_dist = gscript.parse_command(
            "v.surf.bspline",
            flags="e",
            _input=contour_points,
            raster_output=purged_elevation,
            layer="2",
            column="along",
            method=fill_method,
        )
        spline_step = round(float(mean_dist.keys()[0].split(" ")[-1])) * 2

        gscript.info(
            _(
                "Interpolating purged surface using a spline step value"
                " of {s}".format(s=spline_step)
            )
        )
        gscript.run_command(
            "v.surf.bspline",
            _input=contour_points,
            raster_output=purged_elevation,
            layer="2",
            column="along",
            method=fill_method,
            overwrite=gcore.overwrite(),
        )
    else:
        gscript.run_command(
            "v.to.rast",
            input=vector_contours,
            output=raster_contours,
            type="line",
            use="val",
            value=1,
            overwrite=gcore.overwrite(),
        )
        gscript.mapcalc(
            "{c} = {a} * {b}".format(
                c=raster_contours_with_values,
                a=raster_contours,
                b=elevation_input,
                overwrite=gcore.overwrite(),
            )
        )

        gscript.info(
            _("Interpolating elevation between" " difference zero contours...")
        )
        gscript.run_command(
            "r.fillnulls",
            input=raster_contours_with_values,
            output=purged_elevation,
            method=fill_method,
            overwrite=gcore.overwrite(),
        )

    # step 6
    gscript.info(_("Subtracting purged from original elevation..."))
    gscript.mapcalc(
        "{c} = {a} - {b}".format(
            c=local_relief_output,
            a=elevation_input,
            b=purged_elevation,
            overwrite=gcore.overwrite(),
        )
    )

    gscript.raster_history(local_relief_output)

    # set color tables
    if save_intermediates:
        # same color table as input
        gscript.run_command(
            "r.colors", map=smooth_elevation, raster=elevation_input, quiet=True
        )
        gscript.run_command(
            "r.colors", map=purged_elevation, raster=elevation_input, quiet=True
        )

        # has only one color
        if not bspline:
            gscript.run_command(
                "r.colors",
                map=raster_contours_with_values,
                raster=elevation_input,
                quiet=True,
            )

        # same color table as output
        gscript.run_command(
            "r.colors", map=subtracted_smooth_elevation, color=color_table, quiet=True
        )

    if shaded_local_relief_output:
        if not user_color_table:
            color_table = "difference"
        gscript.run_command(
            "r.colors",
            flags=rcolors_flags,
            map=local_relief_output,
            color=color_table,
            quiet=True,
        )
        # r.relief could run in parallel to the main computation,
        # but it is probably fast in comparison to the rest.
        # In theory, r.skyview and first component from r.shaded.pca
        # can be added as well, but let's leave this to the user.
        gscript.run_command("r.relief", input=elevation_input, output=relief_shade)
        gscript.run_command(
            "r.shade",
            shade=relief_shade,
            color=local_relief_output,
            output=shaded_local_relief_output,
        )
        if not user_color_table:
            color_table = "grey"
            gscript.run_command(
                "r.colors",
                flags=rcolors_flags,
                map=local_relief_output,
                color=color_table,
                quiet=True,
            )
        gscript.raster_history(shaded_local_relief_output)
    else:
        if not user_color_table:
            color_table = "grey"
        gscript.run_command(
            "r.colors",
            flags=rcolors_flags,
            map=local_relief_output,
            color=color_table,
            quiet=True,
        )


if __name__ == "__main__":
    main()
