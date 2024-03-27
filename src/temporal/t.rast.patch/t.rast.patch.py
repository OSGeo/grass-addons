#!/usr/bin/env python

############################################################################
#
# MODULE:    t.rast.patch
# AUTHOR(S):    Anika Bettge
#
# PURPOSE:    Patches rasters that have gaps with subsequent maps in time within a space time raster dataset using r.patch
# COPYRIGHT:    (C) 2019 by by mundialis and the GRASS Development Team
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#############################################################################

# %module
# % description: Patches multiple space time raster maps into a single raster map using r.patch.
# % keyword: temporal
# % keyword: aggregation
# % keyword: series
# % keyword: raster
# % keyword: merge
# % keyword: patching
# % keyword: time
# %end

# %option G_OPT_STRDS_INPUT
# %end

# %option G_OPT_T_WHERE
# %end

# %option G_OPT_R_OUTPUT
# %end

# %flag
# % key: t
# % description: Do not assign the space time raster dataset start and end time to the output map
# %end

# %flag
# % key: z
# % description: Use zero (0) for transparency instead of NULL
# %end

# %flag
# % key: s
# % description: Do not create color and category files
# %end

# %flag
# % key: v
# % description: Patch to virtual raster map (r.buildvrt)
# %end

# %option
# % key: sort
# % description: Sort order (see sort parameter)
# % options: asc,desc
# % answer: desc
# %end

# %rules
# % excludes: -v,-s,-z
# %end

import grass.script as grass
from grass.exceptions import CalledModuleError


def main():
    # lazy imports
    import grass.temporal as tgis

    # Get the options
    input = options["input"]
    output = options["output"]
    where = options["where"]
    sort = options["sort"]
    add_time = flags["t"]
    patch_s = flags["s"]
    patch_z = flags["z"]
    patch_module = "r.buildvrt" if flags["v"] else "r.patch"

    # Make sure the temporal database exists
    tgis.init()

    sp = tgis.open_old_stds(input, "strds")

    rows = sp.get_registered_maps("id", where, "start_time", None)

    if rows:

        ordered_rasts = []
        # newest images are first
        if sort == "desc":
            rows_sorted = rows[::-1]
        # older images are first
        elif sort == "asc":
            rows_sorted = rows

        for row in rows_sorted:
            string = "%s" % (row["id"])
            ordered_rasts.append(string)

        patch_flags = ""
        if patch_z:
            patch_flags += "z"
        if patch_s:
            patch_flags += "s"

        try:
            grass.run_command(
                patch_module,
                overwrite=grass.overwrite(),
                input=(",").join(ordered_rasts),
                output=output,
                flags=patch_flags,
            )
        except CalledModuleError:
            grass.fatal(_("%s failed. Check above error messages.") % "r.patch")

        if not add_time:

            # We need to set the temporal extent from the subset of selected maps
            maps = sp.get_registered_maps_as_objects(
                where=where, order="start_time", dbif=None
            )
            first_map = maps[0]
            last_map = maps[-1]
            start_a, end_a = first_map.get_temporal_extent_as_tuple()
            start_b, end_b = last_map.get_temporal_extent_as_tuple()

            if end_b is None:
                end_b = start_b

            if first_map.is_time_absolute():
                extent = tgis.AbsoluteTemporalExtent(start_time=start_a, end_time=end_b)
            else:
                extent = tgis.RelativeTemporalExtent(
                    start_time=start_a,
                    end_time=end_b,
                    unit=first_map.get_relative_time_unit(),
                )

            # Create the time range for the output map
            if output.find("@") >= 0:
                id = output
            else:
                mapset = grass.gisenv()["MAPSET"]
                id = output + "@" + mapset

            map = sp.get_new_map_instance(id)
            map.load()

            map.set_temporal_extent(extent=extent)

            # Register the map in the temporal database
            if map.is_in_db():
                map.update_all()
            else:
                map.insert()


if __name__ == "__main__":
    options, flags = grass.parser()
    main()
