#!/usr/bin/env python

#
############################################################################
#
# MODULE:       r.lake.series
# AUTHOR(S):    Vaclav Petras
# PURPOSE:      Fills lake at given point(s) to given levels.
#
# SPDX-FileCopyrightText: 2013 Other GRASS authors
# SPDX-License-Identifier: GPL-2.0-or-later
#############################################################################


# %module
# % description: Fills lake at given point(s) to given levels.
# % keyword: raster
# % keyword: hydrology
# % keyword: hazard
# % keyword: flood
# %end
# %option G_OPT_R_ELEV
# %end
# %option G_OPT_STRDS_OUTPUT
# % label: Name of the output space time raster dataset
# % description: The name of the dataset is used as a base name for created output maps. Map names will consist of a base name, underscore and water level value or number depending on -c flag.
# %end
# %option
# % key: start_water_level
# % type: double
# % label: Start water level
# % description: Units should be meters?
# % required: yes
# % guisection: Water
# %end
# %option
# % key: end_water_level
# % type: double
# % label: Final (maximal) water level
# % description: Units should be meters?
# % required: yes
# % guisection: Water
# %end
# %option
# % key: water_level_step
# % type: double
# % label: Water level step
# % description: Units should be meters?
# % guisection: Water
# % required: yes
# %end
# %option G_OPT_M_COORDS
# % label: Seed point coordinates
# % description: Either this coordinates pair or a seed map name have to be specified.
# % required: no
# % guisection: Water
# %end
# %option G_OPT_R_INPUT
# % key: seed_raster
# % label: Name of input raster map with given starting point(s) (at least 1 cell > 0)
# % description: Either this parameter or a coordinates pair have to be specified.
# % required: no
# % guisection: Water
# %end
# %option
# % key: time_step
# % type: integer
# % label: Time increment
# % description: Time increment between two states (maps) used to register output maps in space-time raster dataset. Used together with time_units parameter.
# % required: no
# % answer: 30
# % options: 0-
# % guisection: Time
# %end
# %option
# % key: time_unit
# % type: string
# % label: Time units
# % description: Time units used to register output maps in space-time raster dataset. Used together with time_step parameter.
# % required: no
# % options: years,months,days,hours,minutes,seconds
# % answer: minutes
# % guisection: Time
# %end
# %option G_OPT_M_NPROCS
# %end
# %flag
# % key: n
# % label: Use negative depth values for lake raster map
# % description: This flag is passed to r.lake module.
# %end
# %flag
# % key: c
# % label: Use map number instead of the water level in map name (currently ignored)
# % description: This names are always in the right alphabetical order and are also valid vector map names.
# %end

"""
Created on Tue Oct 15 21:18:00 2013

@author: Vaclav Petras <wenzeslaus gmail.com>
"""

# TODO: generate SQL valid map names (replace decimal dot by underscore)
# TODO: use numbers instead of water levels flag
# TODO: remove unused functions

import sys
import decimal
import os

from grass.script import core as gcore
import grass.temporal as tgis
from grass.exceptions import CalledModuleError
from concurrent.futures import ThreadPoolExecutor


def format_time(time):
    return "%05.2f" % time


def format_order(number, zeros):
    return str(number).zfill(zeros)


def frange(x, y, step, precision):
    scale = 10**precision
    array = [
        val / scale
        for val in range(int(x * scale), int((y + step) * scale), int(step * scale))
        if val / scale <= y
    ]
    return array


def check_maps_exist(maps, mapset):
    for map_ in maps:
        if gcore.find_file(map_, element="cell", mapset=mapset)["file"]:
            gcore.fatal(
                _(
                    "Raster map <%s> already exists. Change the base name or allow overwrite."
                )
                % map_
            )


def remove_raster_maps(maps, quiet=False):
    for map_ in maps:
        gcore.run_command("g.remove", flags="f", type="raster", name=map_, quiet=quiet)


def run_lake_task(args):
    elevation, output, water_level, kwargs, flags, overwrite = args

    try:
        gcore.run_command(
            "r.lake",
            flags=flags,
            elevation=elevation,
            lake=output,
            water_level=water_level,
            overwrite=overwrite,
            **kwargs,
        )

    except CalledModuleError as e:
        # Show the error message
        gcore.error(f"r.lake failed for output <{output}>: {e}")
        return None
    return output


def _resolve_nprocs(nprocs):
    """Resolve G_OPT_M_NPROCS into a worker count for ThreadPoolExecutor.

    Mirrors the semantics of G_set_omp_num_threads() in
    lib/gis/omp_threads.c: 0 means use all available cores, a positive
    number is used as-is, a negative number means cpu_count + nprocs
    (clamped to at least 1). Belongs in a library helper eventually.
    """
    nprocs = int(nprocs)
    if nprocs > 0:
        return nprocs
    available = os.cpu_count()
    if nprocs == 0:
        return available
    return max(1, available + nprocs)


def main():
    options, flags = gcore.parser()

    elevation = options["elevation"]
    strds = options["output"]
    basename = strds
    start_water_level = float(options["start_water_level"])
    end_water_level = float(options["end_water_level"])
    water_level_step = options["water_level_step"]
    # if options['coordinates']:
    #    options['coordinates'].split(',')
    # passing coordinates parameter as is
    coordinates = options["coordinates"]
    seed_raster = options["seed_raster"]
    if seed_raster and coordinates:
        gcore.fatal(
            _(
                "Both seed raster and coordinates cannot be specified"
                " together, please specify only one of them."
            )
        )

    time_unit = options["time_unit"]
    time_step = options["time_step"]  # temporal fucntions accepts only string now
    if int(time_step) <= 0:
        gcore.fatal(
            _("Time step must be greater than zero. Please specify number > 0.")
        )

    nprocs = options["nprocs"]

    mapset = gcore.gisenv()["MAPSET"]
    title = _("r.lake series")
    desctiption = _("r.lake series")

    precision = abs(decimal.Decimal(water_level_step).as_tuple().exponent)
    water_levels = frange(
        start_water_level, end_water_level, float(water_level_step), precision
    )
    outputs = [
        f"{basename}_{water_level:.{precision}f}" for water_level in water_levels
    ]

    if not gcore.overwrite():
        check_maps_exist(outputs, mapset)

    kwargs = {}
    if seed_raster:
        kwargs["seed"] = seed_raster
    elif coordinates:
        # Convert coordinates to a tuple for the module
        try:
            east, north = coordinates.split(",")
            kwargs["coordinates"] = (float(east), float(north))
        except Exception:
            gcore.fatal(_("Coordinates must be 'east,north'"))

    if flags["n"]:
        pass_flags = "n"
    else:
        pass_flags = ""

    tasks = [
        (
            elevation,
            outputs[i],
            water_level,
            kwargs,
            pass_flags,
            gcore.overwrite(),
        )
        for i, water_level in enumerate(water_levels)
    ]

    use_cores = _resolve_nprocs(nprocs)

    # Run tasks
    with ThreadPoolExecutor(max_workers=use_cores) as executor:
        outputs = [out for out in executor.map(run_lake_task, tasks) if out is not None]

    gcore.info(_("Registering created maps into temporal dataset..."))

    # Make sure the temporal database exists
    tgis.init()

    tgis.open_new_stds(
        strds,
        type="strds",
        temporaltype="relative",
        title=title,
        descr=desctiption,
        semantic="sum",
        dbif=None,
        overwrite=gcore.overwrite(),
    )
    # TODO: we must start from 1 because there is a bug in register_maps_in_space_time_dataset
    tgis.register_maps_in_space_time_dataset(
        type="raster",
        name=basename,
        maps=",".join(outputs),
        start=str(1),
        end=None,
        unit=time_unit,
        increment=time_step,
        interval=False,
        dbif=None,
    )


if __name__ == "__main__":
    sys.exit(main())

