#!/usr/bin/env python

################################################
#
# MODULE:       t.rast.climatologies
# AUTHOR(S):    Luca Delucchi, Fondazione Edmund Mach
# PURPOSE:      t.rast.climatologies calculate climatologies for space time raster dataset
#
# COPYRIGHT:        (C) 2023 by Luca Delucchi
#
#                This program is free software under the GNU General Public
#                License (>=v2). Read the file COPYING that comes with GRASS
#                for details.
#
################################################

# %module
# % description: Calculate climatologies in a space time raster dataset
# % keyword: temporal
# % keyword: raster
# % keyword: aggregation
# % keyword: series
# % keyword: time
# %end

# %option G_OPT_STRDS_INPUT
# % key: strds
# %end

# %option G_OPT_STRDS_OUTPUT
# % required: no
# %end

# %option
# % key: basename
# % type: string
# % label: Basename of the new generated output maps
# % description: Either a numerical suffix or the start time (s-flag) separated by an underscore will be attached to create a unique identifier
# % required: yes
# % multiple: no
# % gisprompt:
# %end

# %option
# % key: method
# % type: string
# % description: Aggregate operation to be performed on the raster maps
# % required: yes
# % multiple: yes
# % options: average,count,median,mode,minimum,min_raster,maximum,max_raster,stddev,range,sum,variance,diversity,slope,offset,detcoeff,quart1,quart3,perc90,quantile,skewness,kurtosis
# % answer: average
# %end

# %option
# % key: quantile
# % type: double
# % description: Quantile to calculate for method=quantile
# % required: no
# % multiple: yes
# % options: 0.0-1.0
# %end

# %option
# % key: granularity
# % type: string
# % label: Aggregate by day or month
# % required: yes
# % multiple: no
# % options: day, month
# % answer: day
# %end

# %option
# % key: nprocs
# % type: integer
# % description: Number of r.null processes to run in parallel
# % required: no
# % multiple: no
# % answer: 1
# %end

#%flag
#% key: s
#% description: Do not create space time raster dataset
#%end

import sys
import copy

import grass.pygrass.modules as pymod
import grass.script as gscript
import grass.temporal as tgis


def main():
    strds = options["strds"]
    output = options["output"]
    method = options["method"]
    gran = options["granularity"]
    basename = options["basename"]
    nprocs = options["nprocs"]
    quantile = options["quantile"]
    space_time = flags["s"]

    # check if quantile value is used correctly
    if "quantile" in method and not quantile:
        gscript.fatal(_("Number requested methods and output maps do not match."))
    elif quantile and "quantile" not in method:
        gscript.warning(
            _("Quantile option set but quantile not selected in method option")
        )

    # Check if number of methods and output maps matches
    if "quantile" in method:
        len_method = len(method.split(",")) - 1
    else:
        len_method = len(method.split(","))

    if not space_time:
        if (len(list(filter(None, quantile.split(",")))) + len_method) != len(
            output.split(",")
        ):
            gscript.fatal(_("Number requested methods and output maps do not match."))

    tgis.init()
    # We need a database interface
    dbif = tgis.SQLDatabaseInterfaceConnection()
    dbif.connect()

    insp = tgis.open_old_stds(strds, "strds", dbif)
    temporal_type, semantic_type, title, description = insp.get_initial_values()
    if temporal_type != "absolute":
        gscript.fatal(
            _(
                "Space time raster dataset is not absolute, this module require an absolute one"
            )
        )
    maps = insp.get_registered_maps_as_objects(None, "start_time", None)
    if maps is None:
        gscript.fatal(
            _(
                "No maps selected in space time raster dataset {};"
                " it could be empty or where option returno none data".format(strds)
            )
        )
        return False
    # start the r.series module to be used in a ParallelModuleQueue
    mod = pymod.Module("r.series")
    mod.inputs.method = method
    mod.flags.quiet = True
    if quantile:
        mod.inputs.quantile = quantile
    process_queue = pymod.ParallelModuleQueue(int(nprocs))
    mapset = tgis.core.get_current_mapset()
    # depending on granularity it calculate by daily or monthly data
    outmaps = []
    if gran == "day":
        outunit = "days"
        # for each day
        for doy in range(1, 367):
            doystr = "{:03d}".format(doy)
            thiswhere = f"strftime('%j', start_time) == '{doy}'"
            selemaps = insp.get_registered_maps_as_objects(
                thiswhere, "start_time", None
            )
            maps_name = [sam.get_id() for sam in selemaps]
            # check if there are maps for that day
            if len(maps_name) > 0:
                outname = f"{basename}_{doystr}"
                runmod = copy.deepcopy(mod)
                runmod.inputs.input = ",".join(maps_name)
                runmod.outputs.output = outname
                process_queue.put(runmod)
                map_layer = tgis.space_time_datasets.RasterDataset(
                    f"{outname}@{mapset}"
                )
                extent = tgis.RelativeTemporalExtent(
                    start_time=doy - 1,
                    end_time=doy,
                    unit=outunit,
                )
                map_layer.set_temporal_extent(extent=extent)
                outmaps.append(map_layer)

            if doy % 10 == 0:
                gscript.percent(doy, 366, 1)
    else:
        outunit = "months"
        for month in range(1, 13):
            monthstr = "{:02d}".format(month)
            thiswhere = f"strftime('%m', start_time) == '{monthstr}'"
            selemaps = insp.get_registered_maps_as_objects(
                thiswhere, "start_time", None
            )
            maps_name = [sam.get_id() for sam in selemaps]
            if len(maps_name) > 0:
                outname = f"{basename}_{monthstr}"
                runmod = copy.deepcopy(mod)
                runmod.inputs.input = ",".join(maps_name)
                runmod.outputs.output = outname
                process_queue.put(runmod)
                map_layer = tgis.space_time_datasets.RasterDataset(
                    f"{outname}@{mapset}"
                )
                extent = tgis.RelativeTemporalExtent(
                    start_time=month - 1,
                    end_time=month,
                    unit=outunit,
                )
                map_layer.set_temporal_extent(extent=extent)
                outmaps.append(map_layer)
            gscript.percent(month, 12, 1)

    if not space_time:
        # create new space time raster dataset
        output_strds = tgis.open_new_stds(
            output,
            "strds",
            "relative",
            f"{gran} {method} climatologies",
            f"Climatologies create from {strds}, {gran} {method} maps",
            semantic_type,
            dbif,
            gscript.overwrite(),
        )
        register_null = False
        # register maps into space time raster dataset
        tgis.register_map_object_list(
            "rast",
            outmaps,
            output_strds,
            register_null,
            outunit,
            dbif,
        )

        # Update the raster metadata table entries
        output_strds.metadata.update(dbif)

    dbif.close()


if __name__ == "__main__":
    options, flags = gscript.parser()
    sys.exit(main())
