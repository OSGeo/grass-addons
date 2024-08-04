#!/usr/bin/env python3

############################################################################
#
# MODULE:      i.landsat.download
# AUTHOR(S):   Veronica Andreo (original contributor)
#              Hamed Elgizery <hamedashraf2004 gmail.com>
#
# PURPOSE:     Downloads Landsat TM, ETM and OLI data from EarthExplorer
#              and Planetary Computer using EODAG Python library.
#
# COPYRIGHT:   (C) 2020-2024 by Veronica Andreo, and the GRASS development team
#
#              This program is free software under the GNU General Public
#              License (>=v2). Read the file COPYING that comes with GRASS
#              for details.
#
# CHANGELOG:   Switch API from landsatxplore to EODAG - Hamed Elgizery
#############################################################################

# %module
# % description: Downloads Landsat TM, ETM and OLI data from EarthExplorer using landsatxplore library
# % keyword: imagery
# % keyword: satellite
# % keyword: Landsat
# % keyword: download
# %end

# %option G_OPT_F_INPUT
# % key: settings
# % label: Full path to settings file (user, password)
# % description: '-' for standard input
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
# % key: datasource
# % type: string
# % answer: planetary_computer
# % description: Data source to use for searching and downloading landsat scenes
# % options: planetary_computer,usgs
# % required: no
# % guisection: Filter
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
# % answer: landsat_9_ot_c2_l2
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
import json
import sys
import yaml
from datetime import datetime, timezone, timedelta, date
import grass.script as gs
from grass.exceptions import CalledModuleError


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


def get_custom_eodag_config(datasource, settings):
    username = None
    password = None
    apikey = None
    if settings == "-":
        # stdin
        import getpass

        if datasource == "usgs":
            username = input(_("Insert username: "))
            password = getpass.getpass(_("Insert password: "))
        elif datasource == "planetary_computer":
            apikey = getpass.getpass(_("Insert API key: "))
    else:
        try:
            with open(settings, "r") as fd:
                lines = list(
                    filter(None, (line.rstrip() for line in fd))
                )  # non-blank lines only
                if datasource == "usgs":
                    if len(lines) < 2:
                        gs.fatal(_("Invalid settings file"))
                    username = lines[0].strip()
                    password = lines[1].strip()
                elif datasource == "planetary_computer":
                    if len(lines) < 1:
                        gs.fatal(_("Invalid settings file"))
                    apikey = lines[0].strip()
        except IOError as e:
            gs.fatal(_("Unable to open settings file: {}").format(e))

    geojson_temp_dir = gs.tempdir()
    custom_eodag_config_path = os.path.join(
        geojson_temp_dir, f"{datasource}_config.yml"
    )

    eodag_config = None
    try:
        with open(os.path.expanduser("~/.config/eodag/eodag.yml")) as def_config:
            eodag_config = yaml.safe_load(def_config)
    except FileNotFoundError:
        pass

    def build_default_usgs_config(username, password):
        usgs_config = {"priority": None, "api": {}}
        usgs_config["api"]["extract"] = None
        usgs_config["api"]["outputs_prefix"] = None
        usgs_config["api"]["dl_url_params"] = None
        usgs_config["api"]["product_location_scheme"] = None
        usgs_config["api"]["credentials"] = {}
        usgs_config["api"]["credentials"]["username"] = username
        usgs_config["api"]["credentials"]["password"] = password
        return usgs_config

    def build_default_planetary_computer_config(apikey):
        planetary_computer_config = {
            "priority": None,
            "search": None,
            "auth": {},
            "download": {},
        }
        planetary_computer_config["auth"]["credentials"] = {"apikey": apikey}
        planetary_computer_config["download"]["outputs_prefix"] = None
        return planetary_computer_config

    if datasource == "usgs":
        if username is None or password is None:
            gs.warnign(_("No user or password given for USGS"))
        else:
            if eodag_config is None:
                # Shall we always just ignore any configuration in the eodag config file
                # to eliminate confusion between i.eodag and i.landsat.download?
                eodag_config = {"usgs": build_default_usgs_config(username, password)}
            else:
                try:
                    eodag_config["usgs"]["api"]["credentials"]["username"] = username
                    eodag_config["usgs"]["api"]["credentials"]["password"] = password
                except KeyError:
                    # In case the user messes up
                    # usgs in eodag config file
                    gs.warning(_("USGS EODAG configuration could not be parsed."))
                    eodag_config["usgs"] = build_default_usgs_config(username, password)
    elif datasource == "planetary_computer":
        if apikey is None:
            gs.warning(_("No API key given for Planetary Computer"))
        else:
            if eodag_config is None:
                eodag_config = {
                    "planetary_computer": build_default_planetary_computer_config(
                        apikey
                    )
                }
            else:
                try:
                    eodag_config["planetary_computer"]["auth"]["credentials"][
                        "apikey"
                    ] = apikey
                except KeyError:
                    # In case the user messes up
                    # planetary computer in eodag config file
                    gs.warning(
                        _("Planetary Computer EODAG configuration could not be parsed.")
                    )
                    eodag_config["planetary_computer"] = (
                        build_default_planetary_computer_config(apikey)
                    )

    with open(custom_eodag_config_path, "w") as file:
        yaml.dump(eodag_config, file)

    return custom_eodag_config_path


def main():
    start_date = options["start"]
    delta_days = timedelta(60)
    if not options["start"]:
        start_date = date.today() - delta_days
        start_date = start_date.strftime("%Y-%m-%d")

    end_date = options["end"]
    if not options["end"]:
        end_date = date.today().strftime("%Y-%m-%d")

    if options["output"]:
        outdir = options["output"]
        if os.path.isdir(outdir):
            if not os.access(outdir, os.W_OK):
                gs.fatal(_("Output directory <{}> is not writable").format(outdir))
        else:
            gs.fatal(_("Output directory <{}> is not a directory").format(outdir))
    else:
        outdir = os.getcwd()

    custom_eodag_config_path = get_custom_eodag_config(
        options["datasource"], options["settings"]
    )

    # Download by ID
    if options["id"]:
        # Should use other provider other than USGS,
        # as there was a bug in USGS API, fixed here
        # https://github.com/CS-SI/eodag/issues/1252
        # TODO: set provider to USGS when the above changes goes into production
        if options["datasource"] == "usgs" and int(eodag.__version__.split(".")[0]) < 3:
            gs.fatal(
                _(
                    "EODAG 3.0.0 or later is needed to search by IDs with USGS".format(
                        eodag.__version__
                    )
                )
            )
        gs.run_command(
            "i.eodag",
            id=options["id"],
            output=outdir,
            provider=options["datasource"],
            config=custom_eodag_config_path,
        )
    else:
        if "c1" in options["dataset"]:
            gs.fatal(_("Landsat Collection 1 is no longer supported"))
        if "l2" in options["dataset"]:
            eodag_producttype = "LANDSAT_C2L2"
        elif "l1" in options["dataset"]:
            if options["datasource"] != "usgs":
                # USGS is prefered here to compensate here
                gs.warning(
                    _(
                        "Planetary Computer only offers Level 1 scenes till 2013...\nIt is recommended to use USGS instead."
                    )
                )
            eodag_producttype = "LANDSAT_C2L1"
        else:
            gs.fatal(_("Dataset was not recognized"))

        eodag_sort = ""
        eodag_pattern = ""
        for sort_var in options["sort"].split(","):
            if sort_var == "cloud_cover":
                eodag_sort += "cloudcover,"
            if sort_var == "acquisition_date":
                eodag_sort += "ingestiondate,"

        if "tm" in options["dataset"]:
            eodag_pattern += "LM05.+"
        if "etm" in options["dataset"]:
            eodag_pattern += "LE07.+"
        if "8_ot" in options["dataset"]:
            eodag_pattern += "LC08.+"
        if "9_ot" in options["dataset"]:
            eodag_pattern += "LC09.+"
        if options["tier"]:
            eodag_pattern += options["tier"]

        try:
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
                    provider=options["datasource"],
                    pattern=eodag_pattern,
                    config=custom_eodag_config_path,
                    quiet=True,
                )
            )
        except CalledModuleError:
            gs.fatal(
                _(
                    "Could not connect to {}.\nPlease check your credentials or try again later.".format(
                        "Planetary Computer"
                        if options["datasource"] == "planetary_computer"
                        else "USGS"
                    )
                )
            )

        headers_mapping = {
            "planetary_computer": {
                "entity_id": "landsat:scene_id",
                "cloud_cover": "cloudCover",
                "datetime": "startTimeFromAscendingNode",
            },
            "usgs": {
                "entity_id": "entityId",
                "cloud_cover": "cloudCover",
                "datetime": "startTimeFromAscendingNode",
            },
        }

        # Output number of scenes found
        gs.message(_("{} scene(s) found.".format(len(scenes["features"]))))

        if flags["l"]:
            for scene in scenes["features"]:
                product_line = scene["properties"][
                    headers_mapping[options["datasource"]]["entity_id"]
                ]
                product_line += " " + scene["id"]
                # Special formatting for datetime
                try:
                    acquisition_time = normalize_time(
                        scene["properties"][
                            headers_mapping[options["datasource"]]["datetime"]
                        ]
                    )
                except:
                    acquisition_time = scene["properties"][
                        headers_mapping[options["datasource"]]["datetime"]
                    ]
                product_line += " " + acquisition_time
                cloud_cover = scene["properties"][
                    headers_mapping[options["datasource"]]["cloud_cover"]
                ]
                product_line += f" {cloud_cover:2.0f}%"
                print(product_line)
        else:
            if len(scenes) == 0:
                return
            gs.run_command(
                "i.eodag",
                producttype=eodag_producttype,
                output=outdir,
                map=options["map"] if options["map"] else None,
                start=start_date,
                end=end_date,
                clouds=options["clouds"] if options["clouds"] else None,
                limit=options["limit"],
                order=options["order"],
                sort=eodag_sort,
                provider=options["datasource"],
                pattern=eodag_pattern,
                config=custom_eodag_config_path,
                quiet=True,
            )


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
