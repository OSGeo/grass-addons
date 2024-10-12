#!/usr/bin/env python


################################################
#
# MODULE:       t.rast.aggregate.seasons
# AUTHOR(S):    Luca Delucchi
# PURPOSE:      Aggregates an input strds with astronomical seasons granularity.
#
# COPYRIGHT:    (C) 2023 by Luca Delucchi
#
#               This program is free software under the GNU General Public
#               License (>=v2). Read the file COPYING that comes with GRASS
#               for details.
#
################################################

# %module
# % description: Calculates seasonal data according to astronomical seasons.
# % keyword: temporal
# % keyword: raster
# % keyword: aggregation
# % keyword: series
# %end

# %option G_OPT_STRDS_INPUT
# %end

# %option G_OPT_STRDS_OUTPUT
# % label: The name of a singular space time raster dataset
# % description: Using this option all the yearly space time raster datasets will be merged in a singular space time raster dataset
# % required: no
# %end

# %option
# % key: years
# % type: string
# % label: List of years, separator may be comma (list) or minus (range)
# % multiple: yes
# % required: no
# %end

# %option
# % key: basename
# % type: string
# % label: Basename of the new generated output maps and space time raster datasets if output option is not used
# % description: A numerical suffix separated by an underscore will be attached to create a unique identifier
# % required: yes
# % multiple: no
# % gisprompt:
# %end

# %option
# % key: method
# % type: string
# % description: Aggregate operation to be performed on the raster maps
# % required: yes
# % multiple: no
# % options: average,count,median,mode,minimum,min_raster,maximum,max_raster,stddev,range,sum,variance,diversity,slope,offset,detcoeff,quart1,quart3,perc90,quantile,skewness,kurtosis
# % answer: average
# %end

# %option
# % key: nprocs
# % type: integer
# % description: Number of processes to run in parallel
# % required: no
# % multiple: no
# % answer: 1
# %end

# %flag
# % key: n
# % description: Register Null maps
# %end

# %flag
# % key: m
# % description: Use meteorological seasons
# %end


import copy
import atexit
from datetime import datetime

import grass.temporal as tgis
import grass.script as gs
import grass.pygrass.modules as pymod
from grass.pygrass.vector import VectorTopo
from grass.pygrass.vector.geometry import Point

remove_dataset = {"stvds": [], "strds": []}


def cleanup():
    """
    Clean up temporary maps
    """
    # remove space time vector datasets
    for typ, maps in remove_dataset.items():
        for map in maps:
            remod = pymod.Module("t.remove", run_=False)
            remod.inputs.inputs = map
            remod.inputs.type = typ
            remod.flags.f = True
            remod.flags.d = True
            remod.flags.quiet = True
            remod.run()


def leap_year(year):
    """Function to calculate if it is a leap year or not

    Args:
        year (int): the year to check

    Returns:
        bool: True if it is a leap year otherwise Falses
    """
    # divided by 100 means century year (ending with 00)
    # century year divided by 400 is leap year
    if (year % 400 == 0) and (year % 100 == 0):
        return True

    # not divided by 100 means not a century year
    # year divided by 4 is a leap year
    elif (year % 4 == 0) and (year % 100 != 0):
        return True

    # if not divided by both 400 (century year) and 4 (not century year)
    # year is not leap year
    else:
        return False


def main():
    options, flags = gs.parser()
    strds = options["input"]

    output_name = options["output"]

    meteorological = flags["m"]

    tgis.init()
    # We need a database interface
    dbif = tgis.SQLDatabaseInterfaceConnection()
    dbif.connect()
    mapset = tgis.core.get_current_mapset()

    if options["years"] != "":
        try:
            vals = options["years"].split("-")
            years = range(vals)
        except:
            try:
                years = options["years"].split(",")
            except:
                gs.fatal(_("Invalid option years"))
    else:
        if strds.find("@") >= 0:
            id_ = strds
        else:
            id_ = f'{strds}@{gs.gisenv()["MAPSET"]}'
        dataset = tgis.dataset_factory("strds", id_)
        dataset.select(dbif)
        ext = dataset.get_temporal_extent()
        years = range(ext.start_time.year, ext.end_time.year)

    method = options["method"]
    basename = options["basename"]
    nprocs = int(options["nprocs"])
    register_null = flags["n"]

    seasons = ["spring", "summer", "autumn", "winter"]

    # create new space time vector datasets one for each year to be used as sampler
    for year in years:
        season_vect = []
        for seas in seasons:
            name = f"sample_{seas}_{year}"
            vect = VectorTopo(name)
            vect.open("w")
            point = Point(0, 0)
            vect.write(point, cat=1)
            vect.close()
            map_layer = tgis.space_time_datasets.VectorDataset(f"{name}@{mapset}")
            year_int = int(year)
            # check if it is meteorological or astronomic season for each season
            if seas == "spring":
                if meteorological:
                    extent = tgis.AbsoluteTemporalExtent(
                        start_time=datetime(year_int, 3, 1),
                        end_time=datetime(year_int, 5, 31),
                    )
                else:
                    extent = tgis.AbsoluteTemporalExtent(
                        start_time=datetime(year_int, 3, 20),
                        end_time=datetime(year_int, 6, 21),
                    )
            elif seas == "summer":
                if meteorological:
                    extent = tgis.AbsoluteTemporalExtent(
                        start_time=datetime(year_int, 6, 1),
                        end_time=datetime(year_int, 8, 30),
                    )
                else:
                    extent = tgis.AbsoluteTemporalExtent(
                        start_time=datetime(year_int, 6, 21),
                        end_time=datetime(year_int, 9, 20),
                    )
            elif seas == "autumn":
                if meteorological:
                    extent = tgis.AbsoluteTemporalExtent(
                        start_time=datetime(year_int, 9, 1),
                        end_time=datetime(year_int, 11, 30),
                    )
                else:
                    extent = tgis.AbsoluteTemporalExtent(
                        start_time=datetime(year_int, 9, 20),
                        end_time=datetime(year_int, 12, 21),
                    )
            elif seas == "winter":
                if meteorological:
                    if leap_year(year):
                        extent = tgis.AbsoluteTemporalExtent(
                            start_time=datetime(year_int, 12, 1),
                            end_time=datetime(year_int + 1, 2, 29),
                        )
                    else:
                        extent = tgis.AbsoluteTemporalExtent(
                            start_time=datetime(year_int, 12, 1),
                            end_time=datetime(year_int + 1, 2, 28),
                        )
                else:
                    extent = tgis.AbsoluteTemporalExtent(
                        start_time=datetime(year_int, 12, 21),
                        end_time=datetime(year_int + 1, 3, 20),
                    )
            map_layer.set_temporal_extent(extent=extent)
            season_vect.append(map_layer)
        temp_season = f"sample_seasons_{year}"
        outsp = tgis.open_new_stds(
            temp_season,
            "stvds",
            "absolute",
            f"Season vector year {year}",
            f"Season vector for the year {year}",
            "mean",
            dbif,
        )
        tgis.register_map_object_list(
            "vector",
            season_vect,
            outsp,
            False,
            None,
            dbif,
        )
        remove_dataset["stvds"].append(temp_season)

    process_queue = pymod.ParallelModuleQueue(int(nprocs))

    # create t.rast.aggregate.ds module to be copied
    mod = pymod.Module("t.rast.aggregate.ds")
    mod.inputs.input = strds
    mod.inputs.method = method
    mod.inputs.basename = basename
    mod.inputs.type = "stvds"
    mod.flags.quiet = False
    mod.flags.n = register_null

    count = 0

    outputs = []
    # for each year calculate seasonal aggregation
    for year in years:
        print(year)
        mymod = copy.deepcopy(mod)
        mymod.inputs.sample = f"sample_seasons_{year}@{mapset}"
        if output_name:
            myout = f"{output_name}_{year}"
            remove_dataset["strds"].append(myout)
            outputs.append(myout)
            mymod.outputs.output = myout
        else:
            mymod.outputs.output = f"{basename}_{year}"
        print(mymod.get_bash())
        process_queue.put(mymod)

        if count % 10 == 0:
            gs.percent(count, len(years), 1)

    # Wait for unfinished processes
    process_queue.wait()

    if len(outputs) > 1:
        pymod.Module("t.merge", inputs=",".join(outputs), output=output_name)


if __name__ == "__main__":
    atexit.register(cleanup)
    main()
