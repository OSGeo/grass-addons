#!/usr/bin/env python3

"""
 MODULE:      i.sentinel.download
 AUTHOR(S):   Martin Landa
 PURPOSE:     Downloads Sentinel data from Copernicus Open Access Hub,
              USGS Earth Explorer or Google Cloud Storage.
 COPYRIGHT:   (C) 2018-2024 by Martin Landa, and the GRASS development team

              This program is free software under the GNU General Public
              License (>=v2). Read the file COPYING that comes with GRASS
              for details.
"""

# %module
# % description: Downloads Sentinel satellite data from Copernicus Open Access Hub, USGS Earth Explorer, or Google Cloud Storage.
# % keyword: imagery
# % keyword: satellite
# % keyword: Sentinel
# % keyword: download
# %end
# %option G_OPT_F_INPUT
# % key: settings
# % label: Full path to settings file (user, password)
# % required: no
# % description: '-' for standard input
# %end
# %option G_OPT_M_DIR
# % key: output
# % description: Name for output directory where to store downloaded Sentinel data
# % required: no
# % guisection: Output
# %end
# %option G_OPT_V_OUTPUT
# % key: footprints
# % description: Name for output vector map with footprints
# % label: Only supported for download from ESA_Copernicus Open Access Hub
# % required: no
# % guisection: Output
# %end
# %option G_OPT_V_MAP
# % description: If not given then current computational extent is used
# % label: Name of input vector map to define Area of Interest (AOI)
# % required: no
# % guisection: Region
# %end
# %option
# % key: area_relation
# % type: string
# % description: Spatial relation of footprint to AOI
# % label: ESA Copernicus Open Access Hub allows all three, USGS Earth Explorer only 'Intersects' option
# % options: Intersects,Contains,IsWithin
# % answer: Intersects
# % required: no
# % guisection: Region
# %end
# %option
# % key: clouds
# % type: integer
# % description: Maximum cloud cover percentage for Sentinel scene
# % required: no
# % guisection: Filter
# %end
# %option
# % key: producttype
# % type: string
# % description: Sentinel product type to filter
# % label: USGS Earth Explorer only supports S2MSI1C
# % required: no
# % options: SLC,GRD,OCN,S2MSI1C,S2MSI2A,S2MSI2Ap,S3OL1EFR,S3OL1ERR,S3OL1SPC,S3OL1RAC,S3SL1RBT,S3OL2WFR,S3OL2WRR,S3OL2LFR,S3OL2LRR,S3SL2LST,S3SL2FRP,S3SY2SYN,S3SY2VGP,S3SY2VG1,S3SY2V10,S3SY2AOD,S3SR2LAN
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
# % key: limit
# % type: integer
# % answer: 50
# % description: Limit number of Sentinel products
# % guisection: Filter
# %end
# %option
# % key: query
# % type: string
# % description: Extra search keywords to use in the query
# % label: USGS Earth Explorer only supports query options "identifier", "filename" (in ESA name format) or "usgs_identifier" (in USGS name format)
# % guisection: Filter
# %end
# %option
# % key: id
# % type: string
# % multiple: yes
# % description: List of ID to download
# % guisection: Filter
# %end
# %option
# % key: relativeorbitnumber
# % type: integer
# % multiple: yes
# % description: Relative orbit number to download (Sentinel-1: from 1 to 175; Sentinel-2: from 1 to 143; Sentinel-3: from 1 to 385)
# % label:_Only supported by ESA Copernicus Open Access Hub.
# % guisection: Filter
# %end
# %option
# % key: sleep
# % description: Sleep time in minutes before retrying to download data from ESA LTA
# % guisection: Filter
# %end
# %option
# % key: retry
# % description: Maximum number of retries before skipping to the next scene at ESA LTA
# % answer: 5
# % guisection: Filter
# %end
# %option
# % key: datasource
# % description: Data-Hub to download scenes from.
# % label: The currently supported provider is ESA Copernicus Data Space Ecosystem (ESA_CDSE)
# % options: ESA_CDSE
# % answer: ESA_CDSE
# % guisection: Filter
# %end
# %option
# % key: sort
# % description: Sort by values in given order
# % multiple: yes
# % options: ingestiondate,cloudcoverpercentage,footprint
# % answer: cloudcoverpercentage,ingestiondate,footprint
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
# %flag
# % key: p
# % description: Print compiled query string and exit (only supported for ESA_COAH)
# % guisection: Print
# %end
# %flag
# % key: l
# % description: List filtered products and exit
# % guisection: Print
# %end
# %flag
# % key: s
# % description: Skip scenes that have already been downloaded after ingestiondate
# % guisection: Filter
# %end
# %flag
# % key: b
# % description: Use the borders of the AOI polygon and not the region of the AOI
# %end
# %rules
# % requires: -b,map
# % required: output,-l,-p
# % excludes: id,map,area_relation,clouds,producttype,start,end,limit,query,sort,order
# % excludes: -p,-l
# % exclusive: -l, id
# %end

import fnmatch
import hashlib
import os
import re
import xml.etree.ElementTree as ET
import shutil
import sys
import logging
import time
from collections import OrderedDict
from datetime import datetime
from subprocess import PIPE
import json


from datetime import datetime, timezone, timedelta, date
import grass.script as gs
from grass.pygrass.modules import Module
from grass.exceptions import CalledModuleError


def create_dir(directory):
    """Try to create a directory"""
    if not os.path.isdir(directory):
        try:
            os.makedirs(directory)
            return 0
        except OSError as e:
            gs.warning(_("Could not create directory {}").format(directory))
            return 1
    else:
        gs.verbose(_("Directory {} already exists").format(directory))
        return 0


def normalize_time(datetime_str: str):
    """Unifies the different ISO formats into 'YYYY-MM-DDTHH:MM:SS'

    :param datetime_str: Datetime in ISO format
    :type datetime_str: str

    :return: Datetime converted to 'YYYY-MM-DDTHH:MM:SS'
    :rtype: str
    """
    normalized_datetime = datetime.fromisoformat(datetime_str)
    if normalized_datetime.tzinfo is None:
        return normalized_datetime.strftime("%Y-%m-%dT%H:%M:%S")
    return normalized_datetime.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")


PRODUCTTYPE_MAP = {
    "S2MSI1C": "S2_MSI_L1C",
    "S2MSI2A": "S2_MSI_L2A",
    "OCN": "S1_SAR_OCN",
    "GRD": "S1_SAR_GRD",
    "SLC": "S1_SAR_SLC",
    "S3OL1EFR": "S3_EFR",
    "S3OL1ERR": "S3_ERR",
    "S3SL1RBT": "S3_SLSTR_L1RBT",
    "S3OL2WFR": "S3_OLCI_L2WFR",
    "S3OL2WRR": "S3_OLCI_L2WRR",
    "S3OL2LFR": "S3_OLCI_L2LFR",
    "S3OL2LRR": "S3_OLCI_L2LRR",
    "S3SL2LST": "S3_SLSTR_L2LST",
    "S3SL2FRP": "S3_SLSTR_L2FRP",
    "S3SR2LAN": "S3_LAN",
    "S3SY2SYN": "S3_SY_SYN",
    "S3SY2VGP": "S3_SY_VGP",
    "S3SY2VG1": "S3_SY_VG1",
    "S3SY2V10": "S3_SY_V10",
    "S3SY2AOD": "S3_SY_AOD",
    "S3OL1RAC": "S3_RAC - SARA/WEKEO",
    "S3OL1SAC": "DEPRECATED",  # Can not be found anywhere within EODAG
}

REVERSE_PRODUCTTYPE_MAP = {
    "S2_MSI_L1C": "S2MSI1C",
    "S2_MSI_L2A": "S2MSI2A",
    "S1_SAR_OCN": "OCN",
    "S1_SAR_GRD": "GRD",
    "S1_SAR_SLC": "SLC",
    "S3_EFR": "S3OL1EFR",
    "S3_ERR": "S3OL1ERR",
    "S3_SLSTR_L1RBT": "S3SL1RBT",
    "S3_OLCI_L2WFR": "S3OL2WFR",
    "S3_OLCI_L2WRR": "S3OL2WRR",
    "S3_OLCI_L2LFR": "S3OL2LFR",
    "S3_OLCI_L2LRR": "S3OL2LRR",
    "S3_SLSTR_L2LST": "S3SL2LST",
    "S3_SLSTR_L2FRP": "S3SL2FRP",
    "S3_LAN": "S3SR2LAN",
    "S3_SY_SYN": "S3SY2SYN",
    "S3_SY_VGP": "S3SY2VGP",
    "S3_SY_VG1": "S3SY2VG1",
    "S3_SY_V10": "S3SY2V10",
    "S3_SY_AOD": "S3SY2AOD",
    "S3_RAC - SARA/WEKEO": "S3OL1RAC",
    "S3OL1SAC": "DEPRECATED",  # Can not be found anywhere within EODAG
}

CLOUDCOVER_PRODUCTS = [
    "S2MSI1C",
    "S2MSI2A",
    "S3SY2SYN",
    "S3SY2VGP",
    "S3SY2VG1",
    "S3SY2V10",
    "S3SY2AOD",
]

DATASOURCE_MAP = {
    "ESA_CDSE": "cop_dataspace",
    "GCS": "DEPRECATED",
    "SARA": "sara",  # TODO: Can be used as a source for S3OL1RAC
    "ESA_COAH": "DEPRECATED",  # Transferred to ESA_CDSE
    "USGS_EE": "DEPRECATED",  # No longer provides Sentinel products
}


def main():
    global CLOUDCOVER_PRODUCTS

    if not options["datasource"] in DATASOURCE_MAP:
        gs.fatal(_("{} is unrecognized".format(options["datasource"])))
    if DATASOURCE_MAP[options["datasource"]] == "DEPRECATED":
        gs.fatal(_("{} is no longer supported".format(options["datasource"])))

    if options["output"]:
        outdir = options["output"]
        if os.path.isdir(outdir):
            if not os.access(outdir, os.W_OK):
                gs.fatal(_("Output directory <{}> is not writable").format(outdir))
        else:
            create_dir(outdir)
    else:
        outdir = os.getcwd()

    start_date = options["start"]
    delta_days = timedelta(60)
    if not options["start"]:
        start_date = date.today() - delta_days
        start_date = start_date.strftime("%Y-%m-%d")

    end_date = options["end"]
    if not options["end"]:
        end_date = date.today().strftime("%Y-%m-%d")

    sortby = options["sort"].split(",")
    if not options["producttype"] in CLOUDCOVER_PRODUCTS:
        if options["clouds"]:
            gs.info(
                _(
                    "Option <{}> ignored: cloud cover percentage "
                    "is not defined for product type {}"
                ).format("clouds", options["producttype"])
            )
            options["clouds"] = None
        try:
            sortby.remove("cloudcoverpercentage")
        except ValueError:
            pass

    eodag_producttype = PRODUCTTYPE_MAP[options["producttype"]]
    eodag_provider = DATASOURCE_MAP[options["datasource"]]
    eodag_flags = ""
    eodag_sort = ""
    # TODO: Leave a note in the manual that in most cases values should be upper-case
    # TODO: Add a method to list available queryables
    eodag_query = options["query"]
    eodag_pattern = ""

    for sort_var in options["sort"].split(","):
        if sort_var == "cloudcoverpercentage":
            eodag_sort += "cloudcover,"
        if sort_var == "ingestiondate":
            eodag_sort += "ingestiondate,"
        if sort_var == "footprint":
            eodag_sort += "footprint,"

    if flags["b"]:
        eodag_flags += "b"
    if flags["s"]:
        eodag_flags += "s"
    if options["relativeorbitnumber"]:
        eodag_query += f",relativeOrbitNumber={options['relativeorbitnumber']}"

    # Credentials needed
    if not flags["l"]:
        if options["settings"] == "-":
            # stdin
            import getpass

            user = input(_("Insert username: "))
            password = getpass.getpass(_("Insert password: "))
        else:
            try:
                with open(options["settings"], "r") as fd:
                    lines = list(
                        filter(None, (line.rstrip() for line in fd))
                    )  # non-blank lines only
                    if len(lines) < 2:
                        gs.fatal(_("Invalid settings file"))
                    user = lines[0].strip()
                    password = lines[1].strip()
                    if len(lines) > 2:
                        api_url = lines[2].strip()
            except IOError as e:
                gs.fatal(_("Unable to open settings file: {}").format(e))
            if user is None or password is None:
                gs.fatal(_("No user or password given"))

        os.environ[f"EODAG__{eodag_provider.upper()}__AUTH__CREDENTIALS__USERNAME"] = (
            user
        )
        os.environ[f"EODAG__{eodag_provider.upper()}__AUTH__CREDENTIALS__PASSWORD"] = (
            password
        )

        # Checking credentials early
        dag = EODataAccessGateway()
        try:
            dag._plugins_manager.get_auth_plugin("cop_dataspace").authenticate()
        except AuthenticationError:
            gs.fatal(
                _("Authentication failed, please check your credentials and try again.")
            )

    if options["id"]:
        gs.run_command(
            "i.eodag",
            id=options["id"],
            output=outdir,
            provider=options["datasource"],
        )
    else:
        try:
            # TODO: Implement -p flag
            scenes = json.loads(
                gs.read_command(
                    "i.eodag",
                    flags="j" + eodag_flags,
                    producttype=eodag_producttype,
                    map=options["map"] if options["map"] else None,
                    start=start_date,
                    end=end_date,
                    clouds=options["clouds"] if options["clouds"] else None,
                    limit=options["limit"],
                    order=options["order"],
                    area_relation=(
                        options["area_relation"] if options["area_relation"] else None
                    ),
                    sort=eodag_sort,
                    provider=eodag_provider,
                    pattern=eodag_pattern,
                    query=eodag_query,
                    footprints=options["footprints"] if options["footprints"] else None,
                    output=outdir,
                    quiet=True,
                )
            )
        except CalledModuleError:
            gs.fatal(_("Connection to {} faild.\n".format(options["datasource"])))
    headers_mapping = {
        "cop_dataspace": {
            "cloud_cover": "cloudCover",
            "datetime": "startTimeFromAscendingNode",
        },
    }

    # Output number of scenes found
    gs.message(_("{} Sentinel product(s) found.".format(len(scenes["features"]))))

    if flags["l"]:
        for scene in scenes["features"]:
            product_line = scene["id"]
            # Special formatting for datetime
            try:
                acquisition_time = normalize_time(
                    scene["properties"][headers_mapping[eodag_provider]["datetime"]]
                )
            except:
                acquisition_time = scene["properties"][
                    headers_mapping[eodag_provider]["datetime"]
                ]
            product_line += " " + acquisition_time
            if (
                REVERSE_PRODUCTTYPE_MAP[scene["properties"]["eodag_product_type"]]
                in CLOUDCOVER_PRODUCTS
                and headers_mapping[eodag_provider]["cloud_cover"]
                in scene["properties"]
            ):
                cloud_cover = scene["properties"][
                    headers_mapping[eodag_provider]["cloud_cover"]
                ]
                product_line += f" {cloud_cover:2.0f}%"
            else:
                product_line += " cloudcover_NA"
            product_line += f" {options['producttype']}"
            print(product_line)
    else:

        if len(scenes["features"]) == 0:
            gs.warning(_("Nothing to download.\nExiting..."))
            return

        geojson_temp_dir = gs.tempdir()
        geojson_temp_file = os.path.join(geojson_temp_dir, "search_result.geojson")
        with open(geojson_temp_file, "w") as file:
            file.write(json.dumps(scenes))
        gs.run_command(
            "i.eodag",
            file=geojson_temp_file,
            provider=eodag_provider,
            output=outdir,
            quiet=True,
        )
    return 0


if __name__ == "__main__":
    options, flags = gs.parser()

    try:
        import eodag
        from eodag import EODataAccessGateway
        from eodag.utils.exceptions import AuthenticationError

        gs.find_program("i.eodag", "--help")
    except ImportError:
        gs.fatal(_("Addon i.eodag not found. Please intall it with g.extension."))

    sys.exit(main())
