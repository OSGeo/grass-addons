#!/usr/bin/env python3

############################################################################
#
# MODULE:       i.sentinel.parallel.download
# AUTHOR(S):    Guido Riembauer
#
# PURPOSE:      Downloads Sentinel-2 images in parallel using i.sentinel.download.
# COPYRIGHT:    (C) 2020 by mundialis and the GRASS Development Team
#
# 		This program is free software under the GNU General Public
# 		License (>=v2). Read the file COPYING that comes with GRASS
# 		for details.
#
############################################################################

# %module
# % description: Downloads Sentinel-2 images in parallel using i.sentinel.download.
# % keyword: imagery
# % keyword: satellite
# % keyword: Sentinel
# % keyword: download
# % keyword: parallel
# %end

# %option G_OPT_F_INPUT
# % key: settings
# % required: no
# % label: Full path to settings file (user, password)
# %end

# %option
# % key: scene_name
# % required: no
# % multiple: yes
# % label: Names of the scenes to be downloaded
# %end

# %option G_OPT_M_DIR
# % key: output
# % description: Name for output directory where to store downloaded Sentinel data
# % required: no
# % guisection: Output
# %end

# %option
# % key: clouds
# % type: integer
# % description: Maximum cloud cover percentage for Sentinel scene
# % required: no
# % guisection: Filter
# % answer: 20
# %end

# %option
# % key: producttype
# % type: string
# % description: Sentinel product type to filter
# % required: no
# % options: SLC,GRD,OCN,S2MSI1C,S2MSI2A,S2MSI2Ap
# % answer: S2MSI2A
# % guisection: Filter
# %end

# %option
# % key: start
# % type: string
# % description: Start date ('YYYY-MM-DD')
# % guisection: Filter
# %end

# %option
# % key: end
# % type: string
# % description: End date ('YYYY-MM-DD')
# % guisection: Filter
# %end

# %option
# % key: nprocs
# % type: integer
# % required: no
# % multiple: no
# % label: Number of parallel processes
# % description: Number of used CPUs
# % answer: 1
# %end

# %option
# % key: datasource
# % description: Data-Hub to download scenes from
# % label: Default is ESA Copernicus Open Access Hub (ESA_COAH), but Sentinel-2 L1C data can also be acquired from USGS Earth Explorer (USGS_EE) or Google Cloud Storage (GCS)
# % options: ESA_COAH,USGS_EE,GCS
# % answer: ESA_COAH
# % guisection: Filter
# %end

# %option
# % key: limit
# % type: integer
# % description: Maximum number of scenes to filter/download
# % required: no
# % guisection: Filter
# %end

# %flag
# % key: s
# % description: Use scenename/s instead of start/end/producttype to download specific S2 data (specify in the scene_name field)
# %end

# %flag
# % key: f
# % description: Download each Sentinel-2 datasat into an individual folder within the output folder
# %end

# %flag
# % key: e
# % description: Use ESA-style scenename/s to download from USGS
# %end

# %rules
# % collective: -s,scene_name
# % requires_all: -e,-s,scene_name
# %end

import sys
import os
import multiprocessing as mp
import grass.script as grass
from grass.pygrass.modules import Module, ParallelModuleQueue
from datetime import datetime, timedelta


def scenename_split(scenename, datasource, esa_name_for_usgs=False):
    """
    When using the query option in i.sentinel.coverage and defining
    specific filenames, the parameters Producttype, Start-Date, and End-Date
    have to be definied as well. This function extracts these parameters from a
    Sentinel-2 filename and returns the proper string to be passed to the query
    option.
    Args:
        scenename(string): Name of the scene either in ESA or USGS format
        datasource(string): datasource (ESA_COAH or USGS_EE)
        esa_name_for_usgs(bool): use ESA filename to download from USGS
    Returns:
        producttype(string): Sentinel-2 producttype in the required parameter
                             format for i.sentinel.download, e.g. S2MSI2A
        start_day(string): Date in the format YYYY-MM-DD, it is the acquisition
                           date -1 day
        end_day(string): Date in the format YYYY-MM-DD, it is the acquisition
                           date +1 day
        query_string(string): string in the format "identifier=..."

    """
    if datasource == "ESA_COAH" or datasource == "GCS" or esa_name_for_usgs is True:
        # get producttype
        name_split = scenename.split("_")
        type_string = name_split[1]
        level_string = type_string.split("L")[1]
        producttype = "S2MSI" + level_string
        # get dates
        date_string = name_split[2].split("T")[0]
        dt_obj = datetime.strptime(date_string, "%Y%m%d")
        start_day_dt = dt_obj - timedelta(days=1)
        end_day_dt = dt_obj + timedelta(days=1)
        start_day = start_day_dt.strftime("%Y-%m-%d")
        end_day = end_day_dt.strftime("%Y-%m-%d")
        query_string = f"identifier={scenename.replace('.SAFE', '')}"
    else:
        # when usgs downloads via identifier, start/end are ignored
        producttype = "S2MSI1C"
        start_day = "2020-01-01"
        end_day = "2020-02-01"
        query_string = "usgs_identifier={}".format(scenename)
    return producttype, start_day, end_day, query_string


def main():

    settings = options["settings"]
    scene_names = options["scene_name"].split(",")
    output = options["output"]
    nprocs = int(options["nprocs"])
    clouds = int(options["clouds"])
    producttype = options["producttype"]
    start = options["start"]
    end = options["end"]
    datasource = options["datasource"]
    use_scenenames = flags["s"]
    ind_folder = flags["f"]
    if use_scenenames and datasource == "GCS":
        settings_required = False
    else:
        settings_required = True

    if datasource == "USGS_EE" and producttype != "S2MSI1C":
        grass.fatal(
            _(
                "Download from USGS Earth Explorer only supports "
                "Sentinel-2 Level 1C data (S2MSI1C)"
            )
        )
    elif datasource == "GCS" and producttype not in ["S2MSI2A", "S2MSI1C"]:
        grass.fatal(
            _(
                "Download from GCS only supports Sentinel-2 Level"
                "1C (S2MSI1C) or 2A (S2MSI2A)"
            )
        )

    # check if we have the i.sentinel.download + i.sentinel.import addons
    if not grass.find_program("i.sentinel.download", "--help"):
        grass.fatal(
            _(
                "The 'i.sentinel.download' module was not found, "
                "install it first: \n g.extension i.sentinel"
            )
        )

    # Test if all required data are there
    if settings_required is True:
        if not os.path.isfile(settings):
            grass.fatal(_("Settings file <{}> not found").format(settings))

    # set some common environmental variables, like:
    os.environ.update(
        dict(
            GRASS_COMPRESS_NULLS="1",
            GRASS_COMPRESSOR="ZSTD",
            GRASS_MESSAGE_FORMAT="plain",
        )
    )

    # test nprocs Settings
    if nprocs > mp.cpu_count():
        grass.warning(
            _(
                "Using {} parallel processes but only {} CPUs available."
                "Setting nprocs to {}"
            ).format(nprocs, mp.cpu_count(), mp.cpu_count() - 1)
        )
        nprocs = mp.cpu_cound() - 1

    # sentinelsat allows only three parallel downloads
    elif nprocs > 2 and options["datasource"] == "ESA_COAH":
        grass.message(
            _(
                "Maximum number of parallel processes for Downloading"
                " fixed to 2 due to sentinelsat API restrictions"
            )
        )
        nprocs = 2

    # usgs allows maximum 10 parallel downloads
    elif nprocs > 10 and options["dataseource"] == "USGS_EE":
        grass.message(
            _(
                "Maximum number of parallel processes for Downloading"
                " fixed to 10 due to Earth Explorer restrictions"
            )
        )
        nprocs = 10

    if use_scenenames:
        scenenames = scene_names
        # check if the filename is valid
        # usgs scenename format will be checked in i.sentinel.download
        if datasource == "ESA_COAH":
            for scene in scenenames:
                if len(scene) < 10 or not scene.startswith("S2"):
                    grass.fatal(
                        _(
                            "Please provide scenenames in the format"
                            " S2X_LLLLLL_YYYYMMDDTHHMMSS_"
                            "NYYYY_RZZZ_TUUUUU_YYYYMMDDTHHMMSS.SAFE"
                        )
                    )
    else:
        # get a list of scenenames to download
        download_args = {
            "settings": settings,
            "producttype": producttype,
            "start": start,
            "end": end,
            "clouds": clouds,
            "datasource": datasource,
            "flags": "l",
        }
        if options["limit"]:
            download_args["limit"] = options["limit"]
        i_sentinel_download_string = grass.parse_command(
            "i.sentinel.download", **download_args
        )
        i_sentinel_keys = i_sentinel_download_string.keys()
        scenenames = [item.split(" ")[1] for item in i_sentinel_keys]
    # parallelize download
    grass.message(_("Downloading Sentinel-2 data..."))

    # adapt nprocs to number of scenes
    nprocs_final = min(len(scenenames), nprocs)
    queue_download = ParallelModuleQueue(nprocs=nprocs_final)
    for idx, scenename in enumerate(scenenames):
        producttype, start_date, end_date, query_string = scenename_split(
            scenename, datasource, flags["e"]
        )
        # output into separate folders, easier to import in a parallel way:
        if ind_folder:
            outpath = os.path.join(output, "dl_s2_%s" % str(idx + 1))
        else:
            outpath = output
        download_kwargs = {
            "start": start_date,
            "end": end_date,
            "producttype": producttype,
            "query": query_string,
            "output": outpath,
            "datasource": datasource,
        }
        if settings_required is True:
            download_kwargs["settings"] = settings
        i_sentinel_download = Module(
            "i.sentinel.download",
            run_=False,
            **download_kwargs,
        )
        queue_download.put(i_sentinel_download)
    queue_download.wait()


if __name__ == "__main__":
    options, flags = grass.parser()
    sys.exit(main())
