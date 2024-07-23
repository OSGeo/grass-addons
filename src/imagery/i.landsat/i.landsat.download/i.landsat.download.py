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
# COPYRIGHT:   (C) 2020-2025 by Veronica Andreo, and the GRASS development team
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
import pytz
import json
import sys
from datetime import *
import grass.script as gs
from grass.pygrass.modules import Module


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


class LandsatDownloader:
    """Interface for searching, downloading and lising LANDSAT products through EODAG"""

    def __init__(self):
        self.search_result = {"type": "FeatureCollection", "features": []}

    def set_scenes_ids(self, scenes_ids):
        """Should search for scenes and save them in self.search_result"""
        raise NotImplementedError

    def search(
        self,
        dataset,
        start,
        end,
        clouds,
        vector_map,
        limit,
        eodag_sort,
        eodag_order,
        tier,
    ):
        """Should search for scenes and save them in self.search_result"""
        raise NotImplementedError

    def list(self):
        """Should list scenes saved in self.search_result"""
        raise NotImplementedError

    def download(self, output_directory):
        """Should download scenes saved in self.search_result"""
        raise NotImplementedError


class PlanetaryComputerLandsat(LandsatDownloader):
    """Planteray Computer EODAG interface for Landsat products"""

    def __init__(self):
        super().__init__()

    def search(
        self,
        dataset,
        start,
        end,
        clouds=100,
        vector_map=None,
        limit=None,
        eodag_sort=None,
        eodag_order=None,
        tier=None,
    ):
        """Search for Landsat products through USGS"""
        if "c1" in options["dataset"]:
            gs.fatal(_("Landsat Collection 1 is no longer supported"))
        if "l2" in options["dataset"]:
            self.eodag_product_type = "LANDSAT_C2L2"
        elif "l1" in options["dataset"]:
            gs.warning(
                _(
                    "Planetary Computer only offers Level 1 scenes till 2013...\nIt is recommended to use USGS instead."
                )
            )
            self.eodag_product_type = "LANDSAT_C2L1"
        else:
            gs.fatal(_("Dataset was not recognized"))

        gs.message(_("Searching for scenes through Planetary Computer..."))
        eodag_query = ""
        if tier:
            eodag_query += f"landsat:collection_category={options['tier']},"
        if "tm" in options["dataset"]:
            eodag_query += "platformSerialIdentifier=landsat-5"
        if "etm" in options["dataset"]:
            eodag_query += "platformSerialIdentifier=landsat-7"
        if "8_ot" in options["dataset"]:
            eodag_query += "platformSerialIdentifier=landsat-8"
        if "9_ot" in options["dataset"]:
            eodag_query += "platformSerialIdentifier=landsat-9"

        self.search_result = json.loads(
            gs.read_command(
                "i.eodag",
                flags="j",
                producttype=self.eodag_product_type,
                map=vector_map,
                start=start,
                end=end,
                clouds=clouds,
                limit=limit,
                order=eodag_order,
                sort=eodag_sort,
                provider="planetary_computer",
                query=eodag_query,
                quiet=True,
            )
        )

    def set_scenes_ids(self, scenes_ids):
        """Search for Landsat scenes through USGS using their IDs."""
        for scene_id in scenes_ids:
            self.scene = json.loads(
                gs.read_command(
                    "i.eodag",
                    flags="j",
                    id=scene_id,
                    provider="planetary_computer",
                    quiet=True,
                )
            )
            if len(self.scene["features"]) == 0:
                continue
            else:
                self.search_result["features"].extend(self.scene["features"])

    def list(self):
        """List products found in the last search."""
        # Output number of scenes found
        gs.message(_("{} scenes found.".format(len(self.search_result["features"]))))

        for scene in self.search_result["features"]:
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

    def download(self, output_directory):
        """Download products found in the last search."""
        geojson_temp_dir = gs.tempdir()
        geojson_temp_file = os.path.join(geojson_temp_dir, "search_result.geojson")
        with open(geojson_temp_file, "w") as file:
            file.write(json.dumps(self.search_result))
        gs.run_command(
            "i.eodag",
            file=geojson_temp_file,
            provider="planetary_computer",
            output=output_directory,
        )


class USGSLandsat:

    def __init__(self):
        super().__init__()
        self.search_done = False

    def search(
        self,
        dataset,
        start,
        end,
        clouds=100,
        vector_map=None,
        limit=None,
        eodag_sort=None,
        eodag_order=None,
        tier=None,
    ):
        """Search for Landsat products through USGS"""
        if "c1" in options["dataset"]:
            gs.fatal(_("Landsat Collection 1 is no longer supported"))
        if "l2" in options["dataset"]:
            self.eodag_product_type = "LANDSAT_C2L2"
        elif "l1" in options["dataset"]:
            self.eodag_product_type = "LANDSAT_C2L1"
        else:
            gs.fatal(_("Dataset was not recognized"))

        # TODO: This class attributes can be removed when USGS download method
        #       is implemented similar to Planetary Computer

        # These are saved in the class to use them later when downloading
        # because there is no way to store the search result
        # so researching is necessary when downloading
        self.start = start
        self.end = end
        self.eodag_sort = eodag_sort
        self.eodag_order = eodag_order
        self.vector_map = vector_map
        self.limit = limit
        self.clouds = clouds
        self.eodag_pattern = ""
        if "tm" in options["dataset"]:
            # Landsat 5
            self.eodag_pattern += "LM05.+"
        if "etm" in options["dataset"]:
            # Landsat 7
            self.eodag_pattern += "LE07.+"
        if "8_ot" in options["dataset"]:
            # Landsat 8
            self.eodag_pattern += "LC08.+"
        if "9_ot" in options["dataset"]:
            # Landsat 9
            self.eodag_pattern += "LC09.+"
        if options["tier"]:
            # Landsat products has their tiers as the suffix of their title
            self.eodag_pattern += options["tier"]

        self.search_result = json.loads(
            gs.read_command(
                "i.eodag",
                flags="j",
                producttype=self.eodag_product_type,
                map=self.vector_map,
                start=self.start,
                end=self.end,
                clouds=self.clouds,
                limit=self.limit,
                order=self.eodag_order,
                sort=self.eodag_sort,
                provider="usgs",
                pattern=self.eodag_pattern,
                quiet=True,
            )
        )

        self.search_done = True

    def set_scenes_ids(self, scenes_ids):
        """Search for Landsat scenes through USGS using their IDs."""
        if not (eodag.__version__ == "3.0.0b3" or eodag.__version__ >= "3.0.0"):
            gs.fatal(
                _(
                    "EODAG 3.0.0 or later is needed to search by IDs with USGS".format(
                        eodag.__version__
                    )
                )
            )
        for scene_id in scenes_ids:
            self.scene = json.loads(
                gs.read_command(
                    "i.eodag",
                    # flags="j" TODO: uncomment when deserialize_and_register bug is fixed
                    id=scene_id,
                    provider="usgs",
                    quiet=True,
                )
            )
            if len(self.scene["featurs"]) == 0:
                # No need to give a warning as i.eodag already does that
                continue
            else:
                self.search_result["features"].extend(self.scene["features"])

    def list(self):
        """List products found in the last search."""
        # Output number of scenes found
        gs.message(_("{} scenes found.".format(len(self.search_result["features"]))))

        if flags["l"]:
            for scene in self.search_result["features"]:
                product_line = scene["properties"]["entityId"]
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

    def download(self, output_directory):
        """Download products found in the last search."""
        # TODO: Use a simlar implementation to Planetary Computer
        #       when USGS, deserialize_and_register bug is fixed
        gs.read_command(
            "i.eodag",
            producttype=self.eodag_product_type,
            output=output_directory,
            map=self.vector_map,
            start=self.start,
            end=self.end,
            clouds=self.clouds,
            limit=self.limit,
            order=self.eodag_order,
            sort=self.eodag_sort,
            provider="usgs",
            pattern=self.eodag_pattern,
            quiet=True,
        )


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
        outdir = "/tmp"

    if options["datasource"] == "planetary_computer":
        downloader = PlanetaryComputerLandsat()
    elif options["datasource"] == "usgs":
        downloader = USGSLandsat()

    # Download by ID
    if options["id"]:
        # Should use other provider other than USGS,
        # as there was a bug in USGS API, fixed here
        # https://github.com/CS-SI/eodag/issues/1252
        # Currently availble in EODAG 3.0.0b3 (not yet released)
        downloader.set_scenes_ids(options["id"].split(","))
        # TODO: Remove when deserialize_and_register bug is fix
        if options["datasource"] != "usgs":
            downloader.download(outdir)
        return 0

    # Translate sort option to the i.eodag sort options
    eodag_sort = ""
    for sort_var in options["sort"].split(","):
        if sort_var == "cloud_cover":
            eodag_sort += "cloudcover,"
        if sort_var == "acquisition_date":
            eodag_sort += "ingestiondate,"

    # Searching is necessary before listing or downloading
    downloader.search(
        dataset=options["dataset"],
        start=start_date,
        end=end_date,
        clouds=options["clouds"] if options["clouds"] else None,
        vector_map=options["map"] if options["map"] else None,
        limit=options["limit"],
        eodag_sort=eodag_sort,
        eodag_order=options["order"],
    )

    if flags["l"]:
        downloader.list()
        gs.message(
            _(
                "To download all scenes found, re-run the previous "
                "command without -l flag. Note that if no output "
                "option is provided, files will be downloaded in /tmp"
            )
        )
    else:
        downloader.download(outdir)


if __name__ == "__main__":
    options, flags = gs.parser()
    try:
        import eodag
        from eodag import EODataAccessGateway
    except:
        gs.fatal(_("Cannot import eodag. Please intall the library first."))

    # Check if eodag config file is created
    file_path = os.path.join(os.path.expanduser("~"), ".config/eodag/eodag.yml")
    if not os.path.isfile(file_path):
        dag = EODataAccessGateway()
        gs.info(
            _(
                "EODAG Config file is created, you can rerun the module after filling the necessary credentials in {}".format(
                    file_path
                )
            )
        )
        sys.exit(0)
    sys.exit(main())
