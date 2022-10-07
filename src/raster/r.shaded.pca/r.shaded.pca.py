#!/usr/bin/env python

############################################################################
#
# MODULE:    r.shaded.pca
# AUTHOR(S): Vaclav Petras
# PURPOSE:   Creates RGB composition from PCA of hill shades
# COPYRIGHT: (C) 2013-2014 by Vaclav Petras and the GRASS Development Team
#
#                This program is free software under the GNU General Public
#                License (>=v2). Read the file COPYING that comes with GRASS
#                for details.
#
#############################################################################

# %module
# % label: Creates relief shades from various directions and combines them into RGB composition.
# % description: The combined shades highlight terrain features which wouldn't be visible using standard shading technique.
# % keyword: raster
# % keyword: elevation
# % keyword: terrain
# % keyword: visualization
# % keyword: parallel
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
# % description: Name for output PCA shaded relief map
# % required: yes
# %end
# %option
# % key: altitude
# % type: double
# % description: Altitude of the sun in degrees above the horizon
# % options: 0-90
# % answer: 30
# %end
# %option
# % key: nazimuths
# % type: integer
# % description: The number of azimuths (suggested values are 4, 8, 16, 32)
# % answer: 8
# %end
# %option
# % key: zscale
# % type: double
# % description: Factor for exaggerating relief
# % answer: 1
# %end
# %option
# % key: scale
# % type: double
# % description: Azimuth of the sun in degrees to the east of north
# % answer: 1
# %end
# %option
# % key: units
# % type: string
# % description: Elevation units (overrides scale factor)
# % options: intl,survey
# % descriptions: intl;international feet;survey;survey feet
# %end
# %option
# % key: shades_basename
# % type: string
# % label: Base name for output shades map
# % description: A base of the name of shades maps for all azimuths. An underscore ('_') and a azimuth will be added to the base name. When empty, no maps will be outputted (although they need to be generated).
# %end
# %option
# % key: pca_shades_basename
# % type: string
# % label: Base name for output PCA shades map
# % description: A base of the name of PCA shades maps. An underscore ('_') and a azimuth will be added to the base name. When empty, no maps will be outputted (although they need to be generated).
# %end
# %option
# % key: nprocs
# % type: integer
# % description: Number of r.shade.relief processes to run in parallel
# % options: 1-
# % answer: 1
# %end


import os
import atexit
from multiprocessing import Process

import grass.script as grass
import grass.script.core as core

REMOVE = []
MREMOVE = []


def cleanup():
    if REMOVE or MREMOVE:
        core.info(_("Cleaning temporary maps..."))
    for rast in REMOVE:
        grass.run_command("g.remove", flags="f", type="raster", name=rast, quiet=True)
    for pattern in MREMOVE:
        grass.run_command(
            "g.remove", flags="f", type="raster", pattern="%s*" % pattern, quiet=True
        )


def is_grass_7():
    if core.version()["version"].split(".")[0] == "7":
        return True
    return False


def create_tmp_map_name(name):
    return "{mod}_{pid}_{map_}_tmp".format(
        mod="r_shaded_pca", pid=os.getpid(), map_=name
    )


# add latitude map
def run_r_shaded_relief(
    elevation_input,
    shades_basename,
    altitude,
    azimuth,
    z_exaggeration,
    scale,
    units,
    suffix,
):
    params = {}
    if units:
        params.update({"units": units})
    grass.run_command(
        "r.relief",
        input=elevation_input,
        output=shades_basename + suffix,
        azimuth=azimuth,
        zscale=z_exaggeration,
        scale=scale,
        altitude=altitude,
        overwrite=core.overwrite(),
        quiet=True,
        **params,
    )


def set_color_table(rasters, map_):
    if is_grass_7():
        grass.run_command("r.colors", map=rasters, raster=map_, quiet=True)
    else:
        for rast in rasters:
            grass.run_command("r.colors", map=rast, raster=map_, quiet=True)


def check_map_names(basename, mapset, suffixes):
    for suffix in suffixes:
        map_ = "%s%s%s" % (basename, "_", suffix)
        if grass.find_file(map_, element="cell", mapset=mapset)["file"]:
            grass.fatal(
                _(
                    "Raster map <%s> already exists. "
                    "Change the base name or allow overwrite."
                )
                % map_
            )


def frange(x, y, step):
    # we want to be close to range behaviour, so no <=
    while x < y:
        yield x
        x += step


def main():
    options, flags = grass.parser()

    elevation_input = options["input"]
    pca_shade_output = options["output"]
    altitude = float(options["altitude"])
    number_of_azimuths = int(options["nazimuths"])
    z_exaggeration = float(options["zscale"])
    scale = float(options["scale"])
    units = options["units"]
    shades_basename = options["shades_basename"]
    pca_basename = pca_basename_user = options["pca_shades_basename"]
    nprocs = int(options["nprocs"])

    full_circle = 360
    # let's use floats here and leave the consequences to the user
    smallest_angle = float(full_circle) / number_of_azimuths
    azimuths = list(frange(0, full_circle, smallest_angle))

    if not shades_basename:
        shades_basename = create_tmp_map_name("shade")
        MREMOVE.append(shades_basename)

    if not pca_basename:
        pca_basename = pca_shade_output + "_pca"
    pca_maps = [pca_basename + "." + str(i) for i in range(1, number_of_azimuths + 1)]
    if not pca_basename_user:
        REMOVE.extend(pca_maps)

    # here we check all the posible
    if not grass.overwrite():
        check_map_names(shades_basename, grass.gisenv()["MAPSET"], suffixes=azimuths)
        check_map_names(
            pca_basename,
            grass.gisenv()["MAPSET"],
            suffixes=range(1, number_of_azimuths),
        )

    grass.info(_("Running r.relief in a loop..."))
    count = 0
    # Parallel processing
    proc_list = []
    proc_count = 0
    suffixes = []
    all_suffixes = []
    core.percent(0, number_of_azimuths, 1)
    for azimuth in azimuths:
        count += 1
        core.percent(count, number_of_azimuths, 10)

        suffix = "_" + str(azimuth)
        proc_list.append(
            Process(
                target=run_r_shaded_relief,
                args=(
                    elevation_input,
                    shades_basename,
                    altitude,
                    azimuth,
                    z_exaggeration,
                    scale,
                    units,
                    suffix,
                ),
            )
        )

        proc_list[proc_count].start()
        proc_count += 1
        suffixes.append(suffix)
        all_suffixes.append(suffix)

        if (
            proc_count == nprocs
            or proc_count == number_of_azimuths
            or count == number_of_azimuths
        ):
            proc_count = 0
            exitcodes = 0
            for proc in proc_list:
                proc.join()
                exitcodes += proc.exitcode

            if exitcodes != 0:
                core.fatal(_("Error during r.relief computation"))

            # Empty process list
            proc_list = []
            suffixes = []
    # FIXME: how percent really works?
    # core.percent(1, 1, 1)

    shade_maps = [shades_basename + suf for suf in all_suffixes]

    grass.info(_("Running r.pca..."))

    # not quiet=True to get percents
    grass.run_command(
        "i.pca", input=shade_maps, output=pca_basename, overwrite=core.overwrite()
    )

    grass.info(
        _("Creating RGB composite from " "PC1 (red), PC2 (green), PC3 (blue) ...")
    )
    grass.run_command(
        "r.composite",
        red=pca_maps[0],
        green=pca_maps[1],
        blue=pca_maps[2],
        output=pca_shade_output,
        overwrite=core.overwrite(),
        quiet=True,
    )
    grass.raster_history(pca_shade_output)

    if pca_basename_user:
        set_color_table(pca_maps, map_=shade_maps[0])


if __name__ == "__main__":
    atexit.register(cleanup)
    main()
