#!/usr/bin/env python
# -*- coding: utf-8 -*-
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

#%module
#% description: Downloads Landsat TM, ETM and OLI data from EarthExplorer using landsatxplore library
#% keyword: imagery
#% keyword: satellite
#% keyword: Landsat
#% keyword: download
#%end
#%option G_OPT_F_INPUT
#% key: settings
#% label: Full path to settings file (user, password)
#% description: '-' for standard input
#%end
#%option G_OPT_M_DIR
#% key: output
#% description: Name for output directory where to store downloaded Landsat data
#% required: no
#% guisection: Output
#%end
#%option G_OPT_V_MAP
#% label: Name of input vector map to define Area of Interest (AOI)
#% description: If not given then current computational extent is used
#% required: no
#% guisection: Region
#%end
#%option
#% key: clouds
#% type: integer
#% description: Maximum cloud cover percentage for Landsat scene
#% required: no
#% guisection: Filter
#%end
#%option
#% key: dataset
#% type: string
#% description: Landsat dataset to search for
#% required: no
#% options: LANDSAT_TM_C1, LANDSAT_ETM_C1, LANDSAT_8_C1
#% answer: LANDSAT_8_C1
#% guisection: Filter
#%end
#%option
#% key: start
#% type: string
#% description: Start date ('YYYY-MM-DD')
#% guisection: Filter
#%end
#%option
#% key: end
#% type: string
#% description: End date ('YYYY-MM-DD')
#% guisection: Filter
#%end
#%option
#% key: id
#% type: string
#% multiple: yes
#% description: List of scenes IDs to download
#% guisection: Filter
#%end
#%option
#% key: tier
#% type: string
#% multiple: yes
#% description: Tiers
#% options: RT, T1, T2
#% guisection: Filter
#%end
#%option
#% key: sort
#% description: Sort by values in given order
#% multiple: yes
#% options: acquisitionDate,cloudCover
#% answer: cloudCover,acquisitionDate
#% guisection: Sort
#%end
#%option
#% key: order
#% description: Sort order (see sort parameter)
#% options: asc,desc
#% answer: asc
#% guisection: Sort
#%end
#%flag
#% key: l
#% description: List filtered products and exit
#% guisection: Print
#%end
#%rules
#% exclusive: -l, id, output
#%end

import os
from datetime import *
import grass.script as gs

# bbox - get region in ll
def get_bb(vector=None):
    args = {}
    if vector:
        args["vector"] = vector
    # are we in LatLong location?
    kv = gs.parse_command("g.proj", flags="j")
    if "+proj" not in kv:
        gs.fatal("Unable to get bounding box: unprojected location not supported")
    if kv["+proj"] != "longlat":
        info = gs.parse_command("g.region", flags="uplg", **args)
        return (info["sw_lat"], info["nw_long"], info["nw_lat"], info["ne_long"])
    else:
        info = gs.parse_command("g.region", flags="upg", **args)
        return (info["s"], info["w"], info["n"], info["e"])


def main():

    user = password = None

    if options["settings"] == "-":
        # stdin
        import getpass

        user = raw_input(_("Insert username: "))
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

        except IOError as e:
            gs.fatal(_("Unable to open settings file: {}").format(e))

    landsat_api = landsatxplore.api.API(user, password)

    if user is None or password is None:
        gs.fatal(_("No user or password given"))

    start_date = ""
    delta_days = timedelta(60)
    if not options["start"]:
        start_date = date.today() - delta_days
        start_date = start_date.strftime("%Y-%m-%d")

    end_date = ""
    if not options["end"]:
        end_date = date.today().strftime("%Y-%m-%d")

    outdir = ""
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

        ids = options["id"].split(",")

        ee = EarthExplorer(user, password)

        for i in ids:

            try:

                ee.download(scene_id=i, output_dir=outdir)

            except OSError:

                gs.fatal(_("Scene ID <{}> not valid or not found").format(i))

        ee.logout()

    else:

        bb = get_bb(options["map"])

        # List available scenes
        scenes = landsat_api.search(
            dataset=options["dataset"],
            bbox=bb,
            start_date=start_date,
            end_date=end_date,
            max_cloud_cover=options["clouds"],
        )

        if options["tier"]:
            scenes = list(filter(lambda s: options["tier"] in s["displayId"], scenes))

        # Output number of scenes found
        gs.message(_("{} scenes found.".format(len(scenes))))

        sort_vars = options["sort"].split(",")

        reverse = False
        if options["order"] == "desc":
            reverse = True

        # Sort scenes
        sorted_scenes = sorted(
            scenes, key=lambda i: (i[sort_vars[0]], i[sort_vars[1]]), reverse=reverse
        )

        landsat_api.logout()

        if flags["l"]:

            # Output sorted list of scenes found
            # print('ID', 'DisplayID', 'Date', 'Clouds')
            for scene in sorted_scenes:
                print(
                    scene["entityId"],
                    scene["displayId"],
                    scene["acquisitionDate"],
                    scene["cloudCover"],
                )

            gs.message(
                _(
                    "To download all scenes found, re-run the previous "
                    "command without -l flag. Note that if no output "
                    "option is provided, files will be downloaded in /tmp"
                )
            )

        else:

            ee = EarthExplorer(user, password)

            for scene in sorted_scenes:

                gs.message(_("Downloading scene <{}> ...").format(scene["entityId"]))

                ee.download(scene_id=scene["entityId"], output_dir=outdir)

            ee.logout()


if __name__ == "__main__":
    options, flags = gs.parser()

    # lazy import
    try:
        import landsatxplore.api
        from landsatxplore.earthexplorer import EarthExplorer

    except ImportError:

        gs.fatal(_("Cannot import landsatxplore. Please install the library first."))

    main()
