#!/usr/bin/env python

############################################################################
#
# MODULE:      i.landsat.download
# AUTHOR(S):   Veronica Andreo
# PURPOSE:     Downloads Landsat TM, ETM and OLI data from EarthExplorer
#              using landsatxplore Python library.
# COPYRIGHT:   (C) 2020-2021 by Veronica Andreo, and the GRASS development team
#
#              This program is free software under the GNU General Public
#              License (>=v2). Read the file COPYING that comes with GRASS
#              for details.
#
#############################################################################

# %module
# % description: Downloads Landsat TM, ETM and OLI data from EarthExplorer using landsatxplore library
# % keyword: imagery
# % keyword: satellite
# % keyword: Landsat
# % keyword: download
# %end

# %option G_OPT_M_DIR
# % key: output
# % description: Name for output directory where to store downloaded Landsat data
# % required: no
# % guisection: Output
# %end

# %option G_OPT_V_MAP
# % label: Name of input vector map to define Area of Interest (AOI)
# % description: If not given then current computational extent is used
# % required: no
# % guisection: Region
# %end

# %option
# % key: clouds
# % type: integer
# % answer: 100
# % description: Maximum cloud cover percentage for Landsat scene
# % required: no
# % guisection: Filter
# %end

# %option
# % key: dataset
# % type: string
# % description: Landsat dataset to search for
# % required: no
# % options: landsat_tm_c2_l1, landsat_tm_c2_l2, landsat_etm_c2_l1, landsat_etm_c2_l2, landsat_8_ot_c2_l1, landsat_8_ot_c2_l2, landsat_9_ot_c2_l1, landsat_9_ot_c2_l2
# % answer: landsat_9_ot_c2_l1
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
# % key: id
# % type: string
# % multiple: yes
# % description: List of scenes IDs to download
# % guisection: Filter
# %end

# %option
# % key: tier
# % type: string
# % multiple: yes
# % description: Tiers
# % options: RT, T1, T2
# % guisection: Filter
# %end

# %option
# % key: sort
# % type: string
# % description: Sort by values in given order
# % multiple: yes
# % options: acquisition_date,cloud_cover
# % answer: cloud_cover,acquisition_date
# % guisection: Sort
# %end

# %option
# % key: order
# % type: string
# % description: Sort order (see sort parameter)
# % options: asc,desc
# % answer: asc
# % guisection: Sort
# %end

# %option
# % key: timeout
# % type: integer
# % description: Download timeout in seconds
# % answer: 300
# % guisection: Optional
# %end

# %option
# % key: limit
# % type: integer
# % description: maximum number of Landsat scenes
# % answer: 50
# % guisection: Optional
# %end

# %flag
# % key: l
# % description: List filtered products and exit
# % guisection: Print
# %end

# %rules
# % exclusive: -l, id
# % exclusive: -l, output
# %end

import os
import pytz
import json
from datetime import *
import grass.script as gs
from grass.pygrass.modules import Module
from eodag.api.search_result import SearchResult
from eodag.api.product._product import EOProduct
from subprocess import PIPE


def normalize_time(datetime_str: str):
    """Unifies the different ISO formats into 'YYYY-MM-DDTHH:MM:SS'

    :param datetime_str: Datetime in ISO format
    :type datetime_str: str

    :return: Datetime converted to 'YYYY-MM-DDTHH:MM:SS'
    :rtype: str
    """
    normalized_datetime = datetime.fromisoformat(datetime_str)
    if normalized_datetime.tzinfo is None:
        normalized_datetime = normalized_datetime.replace(tzinfo=timezone.utc)
    # Remove microseconds
    normalized_datetime = normalized_datetime.replace(microsecond=0)
    # Convert time to UTC
    normalized_datetime = normalized_datetime.astimezone(pytz.utc)
    # Remove timezone info
    normalized_datetime = normalized_datetime.replace(tzinfo=None)
    return normalized_datetime.isoformat()


def main():
    start_date = options["start"]
    delta_days = timedelta(60)
    if not options["start"]:
        start_date = date.today() - delta_days
        start_date = start_date.strftime("%Y-%m-%d")

    end_date = options["end"]
    if not options["end"]:
        end_date = date.today().strftime("%Y-%m-%d")

    #    outdir = ""
    if options["output"]:
        outdir = options["output"]
        if os.path.isdir(outdir):
            if not os.access(outdir, os.W_OK):
                gs.fatal(_("Output directory <{}> is not writable").format(outdir))
        else:
            gs.fatal(_("Output directory <{}> is not a directory").format(outdir))
    else:
        outdir = "/tmp"

    # Download by ID
    if options["id"]:
        # Should use other provider other than USGS,
        # as there was a bug in USGS API, fixed here
        # https://github.com/CS-SI/eodag/issues/1252
        # TODO: set provider to USGS when the above changes goes into production
        gs.run_command(
            "i.eodag", id=options["id"], output=outdir, provider="planetary_computer"
        )
    else:
        if "c1" in options["dataset"]:
            gs.fatal(_("Landsat Collection 1 is no longer supported"))
        if "l2" in options["dataset"]:
            eodag_producttype = "LANDSAT_C2L2"
        elif "l1" in options["dataset"]:
            # TODO: Planetery Computer has Level 1 data offered till 2013...
            # USGS is needed to compensate here
            eodag_producttype = "LANDSAT_C2L1"
        else:
            gs.fatal(_("Dataset was not recognized"))
        eodag_sort = ""
        for sort_var in options["sort"].split(","):
            if sort_var == "cloud_cover":
                eodag_sort += "cloudcover,"
            if sort_var == "acquisition_date":
                eodag_sort += "ingestiondate,"
        eodag_sort = eodag_sort[:-1]
        eodag_query = ""
        if options["tier"]:
            eodag_query += "landsat:collection_category={options['tier']},"
        if "tm" in options["dataset"]:
            eodag_query += "platformSerialIdentifier=landsat-5;eq"
        if "etm" in options["dataset"]:
            eodag_query += "platformSerialIdentifier=landsat-7;eq"
        if "8_ot" in options["dataset"]:
            eodag_query += "platformSerialIdentifier=landsat-8;eq"
        if "9_ot" in options["dataset"]:
            eodag_query += "platformSerialIdentifier=landsat-9;eq"

        scenes = json.loads(
            gs.read_command(
                "i.eodag",
                flags="j",
                producttype=eodag_producttype,
                map=options["map"] if options["map"] else None,
                start=start_date,
                end=end_date,
                clouds=options["clouds"] if options["clouds"] else None,
                limit=options["limit"],
                order=options["order"],
                sort=eodag_sort,
                provider="planetary_computer",
                query=eodag_query,
                # Each provider provides data in differet format,
                # so using Microsoft Planetary Computer for consistency
                quiet=True,
            )
        )
        # Output number of scenes found
        gs.message(_("{} scenes found.".format(len(scenes["features"]))))

        if flags["l"]:
            for scene in scenes["features"]:
                product_line = scene["properties"]["landsat:scene_id"]
                product_line += " " + scene["id"]
                # Special formatting for datetime
                try:
                    acquisition_time = normalize_time(
                        scene["properties"]["startTimeFromAscendingNode"]
                    )
                except:
                    acquisition_time = scene["properties"]["startTimeFromAscendingNode"]
                product_line += " " + acquisition_time
                cloud_cover = scene["properties"]["cloudCover"]
                product_line += f" {cloud_cover:2.0f}%"
                print(product_line)

            gs.message(
                _(
                    "To download all scenes found, re-run the previous "
                    "command without -l flag. Note that if no output "
                    "option is provided, files will be downloaded in /tmp"
                )
            )
        else:
            geojson_temp_dir = gs.tempdir()
            geojson_temp_file = os.path.join(geojson_temp_dir, "search_result.geojson")
            print(geojson_temp_file)
            with open(geojson_temp_file, "w") as file:
                file.write(json.dumps(scenes))
            gs.run_command(
                "i.eodag",
                file=geojson_temp_file,
                provider="planetary_computer",
                output=outdir,
            )


if __name__ == "__main__":
    options, flags = gs.parser()

    main()
