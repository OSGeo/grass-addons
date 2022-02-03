#!/usr/bin/env python
# -*- coding: utf-8 -*-

############################################################################
#
# MODULE:    r.in.usgs
#
# AUTHORS:   Zechariah Krautwurst
#            Anna Petrasova
#            Vaclav Petras
#
# PURPOSE:   Download user-requested products through the USGS TNM API.
#
# COPYRIGHT: (C) 2017-2021 Zechariah Krautwurst and the GRASS Development Team
#
#            This program is free software under the GNU General Public
#            License (>=v2). Read the file COPYING that comes with GRASS
#            for details.
#
############################################################################

# %module
# % description: Download user-requested products through the USGS TNM API
# % keyword: import
# % keyword: raster
# % keyword: USGS
# % keyword: NED
# % keyword: NAIP
# %end

# %flag
# % key: i
# % description: Return USGS data information without downloading files
# %end

# %option
# % key: product
# % required: yes
# % options: ned,naip,lidar
# % label: USGS data product
# % description: Available USGS data products to query
# %end

# %option G_OPT_R_OUTPUT
# % key: output_name
# % required: yes
# %end

# %option
# % key: ned_dataset
# % required: no
# % options: ned1sec, ned13sec, ned19sec
# % answer: ned1sec
# % label: NED dataset
# % description: Available NED datasets to query
# % descriptions: ned1sec;NED 1 arc-second;ned13sec;NED 1/3 arc-second;ned19sec;NED 1/9 arc-second
# % guisection: NED
# %end

# %option
# % key: input_srs
# % type: string
# % required: no
# % multiple: no
# % label: Input lidar dataset projection (WKT or EPSG, e.g. EPSG:4326)
# % description: Override input lidar dataset coordinate system using EPSG code or WKT definition
# % guisection: Lidar
# %end

# %option
# % key: resolution
# % type: double
# % required: no
# % multiple: no
# % description: Resolution of lidar-based DSM
# % guisection: Lidar
# %end

# %option
# % key: title_filter
# % type: string
# % required: no
# % multiple: no
# % label: Filter available lidar tiles by their title (e.g. use "Phase4")
# % description: To avoid combining lidar from multiple years, use first -i flag and filter by tile title.
# % guisection: Lidar
# %end

# %option
# % key: resampling_method
# % type: string
# % required: no
# % multiple: no
# % options: default,nearest,bilinear,bicubic,lanczos,bilinear_f,bicubic_f,lanczos_f
# % description: Resampling method to use
# % descriptions: default;default method based on product;nearest;nearest neighbor;bilinear;bilinear interpolation;bicubic;bicubic interpolation;lanczos;lanczos filter;bilinear_f;bilinear interpolation with fallback;bicubic_f;bicubic interpolation with fallback;lanczos_f;lanczos filter with fallback
# % answer: default
# %end

# %option
# % key: memory
# % type: integer
# % required: no
# % multiple: no
# % label: Maximum memory to be used (in MB)
# % description: Cache size for raster rows during import and reprojection
# % answer: 300
# % guisection: Speed
# %end

# %option
# % key: nprocs
# % type: integer
# % required: no
# % multiple: no
# % description: Number of processes which will be used for parallel import and reprojection
# % answer: 1
# % guisection: Speed
# %end

# %option G_OPT_M_DIR
# % key: output_directory
# % required: no
# % label: Cache directory for download and processing
# % description: Defaults to system user cache directory (e.g., .cache)
# % guisection: Speed
# %end

# %flag
# % key: k
# % description: Keep imported tiles in the mapset after patch
# % guisection: Speed
# %end

# %rules
# % required: output_name, -i
# %end

import sys
import os
import zipfile
import grass.script as gscript
from six.moves.urllib.request import urlopen
from six.moves.urllib.error import URLError, HTTPError
from six.moves.urllib.parse import quote_plus
from multiprocessing import Process, Manager
import json
import atexit
from pathlib import Path

import grass.script as gs
from grass.exceptions import CalledModuleError

cleanup_list = []


def get_cache_dir(name):
    """Get the default user cache directory

    The name parameter is used to distinguish cache data from different
    components, e.g., from different modules.

    The function creates the directory (including all its parent directories)
    if it does not exist.
    """
    app_version = gs.version()["version"]
    if sys.platform.startswith("win"):
        # App name, directory, and the assumption that the directory
        # should be used are derived from the startup script.
        # Major version is part of the directory name.
        app_name = "GRASS{}".format(app_version.split(".", maxsplit=1)[0])
        path = Path(os.getenv("APPDATA")) / app_name / "Cache" / name
    elif sys.platform.startswith("darwin"):
        app_name = "grass"
        path = Path("~/Library/Caches").expanduser() / app_name / app_version / name
    else:
        app_name = "grass"
        # According to XDG Base Directory Specification 0.8:
        # If $XDG_CACHE_HOME is either not set or empty, a default equal
        # to $HOME/.cache should be used.
        env_var = os.getenv("XDG_CACHE_HOME")
        if env_var:
            path = Path(env_var)
        else:
            path = Path("~/.cache").expanduser()
        path = path / app_name / app_version / name
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_current_mapset():
    """Get curret mapset name as a string"""
    return gscript.read_command("g.mapset", flags="p").strip()


def map_exists(element, name, mapset):
    """Check is map is present in the mapset given in the environment

    :param name: name of the map
    :param element: data type ('raster', 'raster_3d', and 'vector')
    """
    # change type to element used by find file
    if element == "raster":
        element = "cell"
    elif element == "raster_3d":
        element = "grid3"
    # g.findfile returns non-zero when file was not found
    # se we ignore return code and just focus on stdout
    process = gscript.start_command(
        "g.findfile",
        flags="n",
        element=element,
        file=name,
        mapset=mapset,
        stdout=gscript.PIPE,
        stderr=gscript.PIPE,
    )
    output, errors = process.communicate()
    info = gscript.parse_key_val(output, sep="=")
    # file is the key questioned in grass.script.core find_file()
    # return code should be equivalent to checking the output
    if info["file"]:
        return True
    else:
        return False


def run_file_import(
    identifier,
    results,
    input,
    output,
    resolution,
    resolution_value,
    extent,
    resample,
    memory,
):
    result = {}
    try:
        gscript.run_command(
            "r.import",
            input=input,
            output=output,
            resolution=resolution,
            resolution_value=resolution_value,
            extent=extent,
            resample=resample,
            memory=memory,
        )
    except CalledModuleError:
        error = ("Unable to import <{0}>").format(output)
        result["errors"] = error
    else:
        result["output"] = output
    results[identifier] = result


def run_lidar_import(identifier, results, input, output, input_srs=None):
    result = {}
    params = {}
    if input_srs:
        params["input_srs"] = input_srs
    try:
        gscript.run_command(
            "v.in.pdal", input=input, output=output, flags="wr", **params
        )
    except CalledModuleError:
        error = ("Unable to import <{0}>").format(output)
        result["errors"] = error
    else:
        result["output"] = output
    results[identifier] = result


def main():
    # Hard-coded parameters needed for USGS datasets
    usgs_product_dict = {
        "ned": {
            "product": "National Elevation Dataset (NED)",
            "dataset": {
                "ned1sec": (1.0 / 3600, 30, 100),
                "ned13sec": (1.0 / 3600 / 3, 10, 30),
                "ned19sec": (1.0 / 3600 / 9, 3, 10),
            },
            "subset": {},
            "extent": ["1 x 1 degree", "15 x 15 minute"],
            "format": "IMG",
            "extension": "img",
            "zip": True,
            "srs": "wgs84",
            "srs_proj4": "+proj=longlat +ellps=GRS80 +datum=NAD83 +nodefs",
            "interpolation": "bilinear",
            "url_split": "/",
        },
        "nlcd": {
            "product": "National Land Cover Database (NLCD)",
            "dataset": {
                "National Land Cover Database (NLCD) - 2001": (1.0 / 3600, 30, 100),
                "National Land Cover Database (NLCD) - 2006": (1.0 / 3600, 30, 100),
                "National Land Cover Database (NLCD) - 2011": (1.0 / 3600, 30, 100),
            },
            "subset": {
                "Percent Developed Imperviousness",
                "Percent Tree Canopy",
                "Land Cover",
            },
            "extent": ["3 x 3 degree"],
            "format": "GeoTIFF",
            "extension": "tif",
            "zip": True,
            "srs": "wgs84",
            "srs_proj4": "+proj=longlat +ellps=GRS80 +datum=NAD83 +nodefs",
            "interpolation": "nearest",
            "url_split": "/",
        },
        "naip": {
            "product": "USDA National Agriculture Imagery Program (NAIP)",
            "dataset": {"Imagery - 1 meter (NAIP)": (1.0 / 3600 / 27, 1, 3)},
            "subset": {},
            "extent": [
                "3.75 x 3.75 minute",
            ],
            "format": "JPEG2000",
            "extension": "jp2",
            "zip": False,
            "srs": "wgs84",
            "srs_proj4": "+proj=longlat +ellps=GRS80 +datum=NAD83 +nodefs",
            "interpolation": "nearest",
            "url_split": "/",
        },
        "lidar": {
            "product": "Lidar Point Cloud (LPC)",
            "dataset": {"Lidar Point Cloud (LPC)": (1.0 / 3600 / 9, 3, 10)},
            "subset": {},
            "extent": [""],
            "format": "LAS,LAZ",
            "extension": "las,laz",
            "zip": True,
            "srs": "",
            "srs_proj4": "+proj=longlat +ellps=GRS80 +datum=NAD83 +nodefs",
            "interpolation": "nearest",
            "url_split": "/",
        },
    }

    # Set GRASS GUI options and flags to python variables
    gui_product = options["product"]

    # Variable assigned from USGS product dictionary
    nav_string = usgs_product_dict[gui_product]
    product = nav_string["product"]
    product_format = nav_string["format"]
    product_extensions = tuple(nav_string["extension"].split(","))
    product_is_zip = nav_string["zip"]
    product_srs = nav_string["srs"]
    product_proj4 = nav_string["srs_proj4"]
    product_interpolation = nav_string["interpolation"]
    product_url_split = nav_string["url_split"]
    product_extent = nav_string["extent"]
    gui_subset = None

    # Parameter assignments for each dataset
    if gui_product == "ned":
        gui_dataset = options["ned_dataset"]
        ned_api_name = ""
        if options["ned_dataset"] == "ned1sec":
            ned_data_abbrv = "ned_1arc_"
            ned_api_name = "1 arc-second"
        if options["ned_dataset"] == "ned13sec":
            ned_data_abbrv = "ned_13arc_"
            ned_api_name = "1/3 arc-second"
        if options["ned_dataset"] == "ned19sec":
            ned_data_abbrv = "ned_19arc_"
            ned_api_name = "1/9 arc-second"
        product_tag = product + " " + ned_api_name

    if gui_product == "nlcd":
        gui_dataset = options["nlcd_dataset"]
        if options["nlcd_dataset"] == "nlcd2001":
            gui_dataset = "National Land Cover Database (NLCD) - 2001"
        if options["nlcd_dataset"] == "nlcd2006":
            gui_dataset = "National Land Cover Database (NLCD) - 2006"
        if options["nlcd_dataset"] == "nlcd2011":
            gui_dataset = "National Land Cover Database (NLCD) - 2011"

        if options["nlcd_subset"] == "landcover":
            gui_subset = "Land Cover"
        if options["nlcd_subset"] == "impervious":
            gui_subset = "Percent Developed Imperviousness"
        if options["nlcd_subset"] == "canopy":
            gui_subset = "Percent Tree Canopy"
        product_tag = gui_dataset

    if gui_product == "naip":
        gui_dataset = "Imagery - 1 meter (NAIP)"
        product_tag = nav_string["product"]

    has_pdal = gscript.find_program(pgm="v.in.pdal")
    if gui_product == "lidar":
        gui_dataset = "Lidar Point Cloud (LPC)"
        product_tag = nav_string["product"]
        if not has_pdal:
            gscript.warning(
                _(
                    "Module v.in.pdal is missing,"
                    " any downloaded data will not be processed."
                )
            )
    # Assigning further parameters from GUI
    gui_output_layer = options["output_name"]
    gui_resampling_method = options["resampling_method"]
    gui_i_flag = flags["i"]
    gui_k_flag = flags["k"]
    work_dir = options["output_directory"]
    memory = options["memory"]
    nprocs = options["nprocs"]

    preserve_extracted_files = True
    use_existing_extracted_files = True
    preserve_imported_tiles = gui_k_flag
    use_existing_imported_tiles = True

    if not work_dir:
        work_dir = get_cache_dir("r_in_usgs")
    elif not os.path.isdir(work_dir):
        gscript.fatal(
            _("Directory <{}> does not exist. Please create it.").format(work_dir)
        )

    # Returns current units
    try:
        proj = gscript.parse_command("g.proj", flags="g")
        if gscript.locn_is_latlong():
            product_resolution = nav_string["dataset"][gui_dataset][0]
        elif float(proj["meters"]) == 1:
            product_resolution = nav_string["dataset"][gui_dataset][1]
        else:
            # we assume feet
            product_resolution = nav_string["dataset"][gui_dataset][2]
    except TypeError:
        product_resolution = False
    if gui_product == "lidar" and options["resolution"]:
        product_resolution = float(options["resolution"])

    if gui_resampling_method == "default":
        gui_resampling_method = nav_string["interpolation"]
        gscript.verbose(
            _("The default resampling method for product {product} is {res}").format(
                product=gui_product, res=product_interpolation
            )
        )

    # Get coordinates for current GRASS computational region and convert to USGS SRS
    gregion = gscript.region()
    wgs84 = "+proj=longlat +ellps=WGS84 +datum=WGS84 +no_defs"
    min_coords = gscript.read_command(
        "m.proj",
        coordinates=(gregion["w"], gregion["s"]),
        proj_out=wgs84,
        separator="comma",
        flags="d",
    )
    max_coords = gscript.read_command(
        "m.proj",
        coordinates=(gregion["e"], gregion["n"]),
        proj_out=wgs84,
        separator="comma",
        flags="d",
    )
    min_list = min_coords.split(",")[:2]
    max_list = max_coords.split(",")[:2]
    list_bbox = min_list + max_list
    str_bbox = ",".join((str(coord) for coord in list_bbox))

    # Format variables for TNM API call
    gui_prod_str = str(product_tag)
    datasets = quote_plus(gui_prod_str)
    prod_format = quote_plus(product_format)
    prod_extent = quote_plus(product_extent[0])

    # Create TNM API URL
    base_TNM = "https://tnmaccess.nationalmap.gov/api/v1/products?"
    datasets_TNM = "datasets={0}".format(datasets)
    bbox_TNM = "&bbox={0}".format(str_bbox)
    prod_format_TNM = "&prodFormats={0}".format(prod_format)
    TNM_API_URL = base_TNM + datasets_TNM + bbox_TNM + prod_format_TNM
    if gui_product == "nlcd":
        TNM_API_URL += "&prodExtents={0}".format(prod_extent)
    gscript.verbose("TNM API Query URL:\t{0}".format(TNM_API_URL))

    # Query TNM API
    try_again_messge = _(
        "Possibly, the query has timed out. Check network configuration and try again."
    )
    try:
        TNM_API_GET = urlopen(TNM_API_URL, timeout=12)
    except HTTPError as error:
        gscript.fatal(
            _(
                "HTTP(S) error from USGS TNM API: {code}: {reason} ({instructions})"
            ).format(
                reason=error.reason, code=error.code, instructions=try_again_messge
            )
        )
    except (URLError, OSError, IOError) as error:
        # Catching also SSLError and potentially others which are
        # subclasses of IOError in Python 2 and of OSError in Python 3.
        gscript.fatal(
            _("Error accessing USGS TNM API: {error} ({instructions})").format(
                error=error, instructions=try_again_messge
            )
        )

    # Parse return JSON object from API query
    try:
        return_JSON = json.load(TNM_API_GET)
        if return_JSON["errors"]:
            TNM_API_error = return_JSON["errors"]
            api_error_msg = "TNM API Error - {0}".format(str(TNM_API_error))
            gscript.fatal(api_error_msg)
        if gui_product == "lidar" and options["title_filter"]:
            return_JSON["items"] = [
                item
                for item in return_JSON["items"]
                if options["title_filter"] in item["title"]
            ]
            return_JSON["total"] = len(return_JSON["items"])

    except:
        gscript.fatal(_("Unable to load USGS JSON object."))

    # Functions down_list() and exist_list() used to determine
    # existing files and those that need to be downloaded.
    def down_list():
        dwnld_url.append(TNM_file_URL)
        dwnld_size.append(TNM_file_size)
        TNM_file_titles.append(TNM_file_title)
        if product_is_zip:
            extract_zip_list.append(local_zip_path)

    def exist_list():
        exist_TNM_titles.append(TNM_file_title)
        exist_dwnld_url.append(TNM_file_URL)
        if product_is_zip:
            exist_zip_list.append(local_zip_path)
            extract_zip_list.append(local_zip_path)
        else:
            exist_tile_list.append(local_tile_path)

    # Assign needed parameters from returned JSON
    tile_API_count = int(return_JSON["total"])
    tiles_needed_count = 0
    # TODO: Make the tolerance configurable.
    # Some combinations produce >10 byte differences.
    size_diff_tolerance = 5
    exist_dwnld_size = 0

    # Fatal error if API query returns no results for GUI input
    if tile_API_count == 0:
        gs.fatal(
            _("USGS TNM API error or no tiles available for given input parameters")
        )

    dwnld_size = []
    dwnld_url = []
    TNM_file_titles = []
    exist_dwnld_url = []
    exist_TNM_titles = []
    exist_zip_list = []
    exist_tile_list = []
    extract_zip_list = []
    # for each file returned, assign variables to needed parameters
    for f in return_JSON["items"]:
        TNM_file_title = f["title"]
        TNM_file_URL = str(f["downloadURL"])
        TNM_file_size = int(f["sizeInBytes"])
        TNM_file_name = TNM_file_URL.split(product_url_split)[-1]
        if gui_product == "ned":
            local_file_path = os.path.join(work_dir, ned_data_abbrv + TNM_file_name)
            local_zip_path = os.path.join(work_dir, ned_data_abbrv + TNM_file_name)
            local_tile_path = os.path.join(work_dir, ned_data_abbrv + TNM_file_name)
        else:
            local_file_path = os.path.join(work_dir, TNM_file_name)
            local_zip_path = os.path.join(work_dir, TNM_file_name)
            local_tile_path = os.path.join(work_dir, TNM_file_name)
        file_exists = os.path.exists(local_file_path)
        file_complete = None
        # If file exists, do not download,
        # but if incomplete (e.g. interupted download), redownload.
        if file_exists:
            existing_local_file_size = os.path.getsize(local_file_path)
            # if local file is incomplete
            if abs(existing_local_file_size - TNM_file_size) > size_diff_tolerance:
                gscript.verbose(
                    _(
                        "Size of local file {filename} ({local_size}) differs"
                        " from a file size specified in the API ({api_size})"
                        " by {difference} bytes"
                        " which is more than tolerance ({tolerance})."
                        " It will be downloaded again."
                    ).format(
                        filename=local_file_path,
                        local_size=existing_local_file_size,
                        api_size=TNM_file_size,
                        difference=abs(existing_local_file_size - TNM_file_size),
                        tolerance=size_diff_tolerance,
                    )
                )
                # NLCD API query returns subsets that cannot be filtered before
                # results are returned. gui_subset is used to filter results.
                if not gui_subset:
                    tiles_needed_count += 1
                    down_list()
                else:
                    if gui_subset in TNM_file_title:
                        tiles_needed_count += 1
                        down_list()
                    else:
                        continue
            else:
                if not gui_subset:
                    tiles_needed_count += 1
                    exist_list()
                    exist_dwnld_size += TNM_file_size
                else:
                    if gui_subset in TNM_file_title:
                        tiles_needed_count += 1
                        exist_list()
                        exist_dwnld_size += TNM_file_size
                    else:
                        continue
        else:
            if not gui_subset:
                tiles_needed_count += 1
                down_list()
            else:
                if gui_subset in TNM_file_title:
                    tiles_needed_count += 1
                    down_list()
                    continue

    # number of files to be downloaded
    file_download_count = len(dwnld_url)

    # remove existing files from download lists
    for t in exist_TNM_titles:
        if t in TNM_file_titles:
            TNM_file_titles.remove(t)
    for url in exist_dwnld_url:
        if url in dwnld_url:
            dwnld_url.remove(url)

    # messages to user about status of files to be kept, removed, or downloaded
    if exist_zip_list:
        exist_msg = _(
            "\n{0} of {1} files/archive(s) exist locally and will be used by module."
        ).format(len(exist_zip_list), tiles_needed_count)
        gscript.message(exist_msg)
    # TODO: fix this way of reporting and merge it with the one in use
    if exist_tile_list:
        exist_msg = _(
            "\n{0} of {1} files/archive(s) exist locally and will be used by module."
        ).format(len(exist_tile_list), tiles_needed_count)
        gscript.message(exist_msg)

    # formats JSON size from bites into needed units for combined file size
    if dwnld_size:
        total_size = sum(dwnld_size)
        len_total_size = len(str(total_size))
        if 6 < len_total_size < 10:
            total_size_float = total_size * 1e-6
            total_size_str = str("{0:.2f}".format(total_size_float) + " MB")
        if len_total_size >= 10:
            total_size_float = total_size * 1e-9
            total_size_str = str("{0:.2f}".format(total_size_float) + " GB")
    else:
        total_size_str = "0"

    # Prints 'none' if all tiles available locally
    if TNM_file_titles:
        TNM_file_titles_info = "\n".join(TNM_file_titles)
    else:
        TNM_file_titles_info = "none"

    # Formatted return for 'i' flag
    if file_download_count <= 0:
        data_info = "USGS file(s) to download: NONE"
        if gui_product == "nlcd":
            if tile_API_count != file_download_count:
                if tiles_needed_count == 0:
                    nlcd_unavailable = (
                        "NLCD {0} data unavailable for input parameters".format(
                            gui_subset
                        )
                    )
                    gscript.fatal(nlcd_unavailable)
    else:
        data_info = (
            "USGS file(s) to download:",
            "-------------------------",
            "Total download size:\t{size}",
            "Tile count:\t{count}",
            "USGS SRS:\t{srs}",
            "USGS tile titles:\n{tile}",
            "-------------------------",
        )
        data_info = "\n".join(data_info).format(
            size=total_size_str,
            count=file_download_count,
            srs=product_srs,
            tile=TNM_file_titles_info,
        )
    print(data_info)

    if gui_i_flag:
        gs.message(_("To download USGS data, remove <i> flag, and rerun r.in.usgs."))
        sys.exit()

    # USGS data download process
    if file_download_count <= 0:
        gscript.message(_("Extracting existing USGS Data..."))
    else:
        gscript.message(_("Downloading USGS Data..."))

    TNM_count = len(dwnld_url)
    download_count = 0
    local_tile_path_list = []
    local_zip_path_list = []
    patch_names = []

    # Download files
    for url in dwnld_url:
        # create file name by splitting name from returned url
        # add file name to local download directory
        if gui_product == "ned":
            file_name = ned_data_abbrv + url.split(product_url_split)[-1]
            local_file_path = os.path.join(work_dir, file_name)
        else:
            file_name = url.split(product_url_split)[-1]
            local_file_path = os.path.join(work_dir, file_name)
        try:
            download_count += 1
            gs.message(
                _("Download {current} of {total}...").format(
                    current=download_count, total=TNM_count
                )
            )
            # download files in chunks rather than write complete files to memory
            dwnld_req = urlopen(url, timeout=12)
            download_bytes = int(dwnld_req.info()["Content-Length"])
            CHUNK = 16 * 1024
            with open(local_file_path, "wb+") as local_file:
                count = 0
                steps = int(download_bytes / CHUNK) + 1
                while True:
                    chunk = dwnld_req.read(CHUNK)
                    gscript.percent(count, steps, 10)
                    count += 1
                    if not chunk:
                        break
                    local_file.write(chunk)
                gscript.percent(1, 1, 1)
            local_file.close()
            # determine if file is a zip archive or another format
            if product_is_zip:
                local_zip_path_list.append(local_file_path)
            else:
                local_tile_path_list.append(local_file_path)
        except URLError as error:
            gs.fatal(
                _(
                    "USGS download request for {url} has timed out. "
                    "Network or formatting error: {err}"
                ).format(url=url, err=error)
            )
        except StandardError as error:
            cleanup_list.append(local_file_path)
            gs.fatal(_("Download of {url} failed: {err}").format(url=url, err=error))

    # sets already downloaded zip files or tiles to be extracted or imported
    # our pre-stats for extraction are broken, collecting stats during
    used_existing_extracted_tiles_num = 0
    removed_extracted_tiles_num = 0
    old_extracted_tiles_num = 0
    extracted_tiles_num = 0
    if exist_zip_list:
        for z in exist_zip_list:
            local_zip_path_list.append(z)
    if exist_tile_list:
        for t in exist_tile_list:
            local_tile_path_list.append(t)
    if product_is_zip:
        if file_download_count == 0:
            pass
        else:
            gscript.message("Extracting data...")
        # for each zip archive, extract needed file
        files_to_process = len(local_zip_path_list)
        for i, z in enumerate(local_zip_path_list):
            # TODO: measure only for the files being unzipped
            gscript.percent(i, files_to_process, 10)
            # Extract tiles from ZIP archives
            try:
                with zipfile.ZipFile(z, "r") as read_zip:
                    for f in read_zip.namelist():
                        if f.lower().endswith(product_extensions):
                            extracted_tile = os.path.join(work_dir, str(f))
                            remove_and_extract = True
                            if os.path.exists(extracted_tile):
                                if use_existing_extracted_files:
                                    # if the downloaded file is newer
                                    # than the extracted on, we extract
                                    if os.path.getmtime(
                                        extracted_tile
                                    ) < os.path.getmtime(z):
                                        remove_and_extract = True
                                        old_extracted_tiles_num += 1
                                    else:
                                        remove_and_extract = False
                                        used_existing_extracted_tiles_num += 1
                                else:
                                    remove_and_extract = True
                                if remove_and_extract:
                                    removed_extracted_tiles_num += 1
                                    os.remove(extracted_tile)
                            if remove_and_extract:
                                extracted_tiles_num += 1
                                read_zip.extract(f, str(work_dir))
                if os.path.exists(extracted_tile):
                    local_tile_path_list.append(extracted_tile)
                    if not preserve_extracted_files:
                        cleanup_list.append(extracted_tile)
            except IOError as error:
                cleanup_list.append(extracted_tile)
                gscript.fatal(
                    _(
                        "Unable to locate or extract IMG file '{filename}'"
                        " from ZIP archive '{zipname}': {error}"
                    ).format(filename=extracted_tile, zipname=z, error=error)
                )
        gscript.percent(1, 1, 1)
        # TODO: do this before the extraction begins
        gscript.verbose(
            _("Extracted {extracted} new tiles and used {used} existing tiles").format(
                used=used_existing_extracted_tiles_num, extracted=extracted_tiles_num
            )
        )
        if old_extracted_tiles_num:
            gscript.verbose(
                _(
                    "Found {removed} existing tiles older"
                    " than the corresponding downloaded archive"
                ).format(removed=old_extracted_tiles_num)
            )
        if removed_extracted_tiles_num:
            gscript.verbose(
                _("Removed {removed} existing tiles").format(
                    removed=removed_extracted_tiles_num
                )
            )

    if gui_product == "lidar" and not has_pdal:
        gs.fatal(_("Module v.in.pdal is missing, cannot process downloaded data."))

    # operations for extracted or complete files available locally
    # We are looking only for the existing maps in the current mapset,
    # but theoretically we could be getting them from other mapsets
    # on search path or from the whole location. User may also want to
    # store the individual tiles in a separate mapset.
    # The big assumption here is naming of the maps (it is a smaller
    # for the files in a dedicated download directory).
    used_existing_imported_tiles_num = 0
    imported_tiles_num = 0
    mapset = get_current_mapset()
    files_to_import = len(local_tile_path_list)

    process_list = []
    process_id_list = []
    process_count = 0
    num_tiles = len(local_tile_path_list)

    with Manager() as manager:
        results = manager.dict()
        for i, t in enumerate(local_tile_path_list):
            # create variables for use in GRASS GIS import process
            LT_file_name = os.path.basename(t)
            LT_layer_name = os.path.splitext(LT_file_name)[0]
            # we are removing the files if requested even if we don't use them
            # do not remove by default with NAIP, there are no zip files
            if gui_product != "naip" and not preserve_extracted_files:
                cleanup_list.append(t)
            # TODO: unlike the files, we don't compare date with input
            if use_existing_imported_tiles and map_exists(
                "raster", LT_layer_name, mapset
            ):
                patch_names.append(LT_layer_name)
                used_existing_imported_tiles_num += 1
            else:
                in_info = _(
                    "Importing and reprojecting {name} ({count} out of {total})..."
                ).format(name=LT_file_name, count=i + 1, total=files_to_import)
                gscript.info(in_info)

                process_count += 1
                if gui_product != "lidar":
                    process = Process(
                        name="Import-{}-{}-{}".format(process_count, i, LT_layer_name),
                        target=run_file_import,
                        kwargs=dict(
                            identifier=i,
                            results=results,
                            input=t,
                            output=LT_layer_name,
                            resolution="value",
                            resolution_value=product_resolution,
                            extent="region",
                            resample=product_interpolation,
                            memory=int(float(memory) // int(nprocs)),
                        ),
                    )
                else:
                    srs = options["input_srs"]
                    process = Process(
                        name="Import-{}-{}-{}".format(process_count, i, LT_layer_name),
                        target=run_lidar_import,
                        kwargs=dict(
                            identifier=i,
                            results=results,
                            input=t,
                            output=LT_layer_name,
                            input_srs=srs if srs else None,
                        ),
                    )
                process.start()
                process_list.append(process)
                process_id_list.append(i)

            # Wait for processes to finish when we reached the max number
            # of processes.
            if process_count == nprocs or i == num_tiles - 1:
                exitcodes = 0
                for process in process_list:
                    process.join()
                    exitcodes += process.exitcode
                if exitcodes != 0:
                    if nprocs > 1:
                        gscript.fatal(
                            _(
                                "Parallel import and reprojection failed."
                                " Try running with nprocs=1."
                            )
                        )
                    else:
                        gscript.fatal(_("Import and reprojection step failed."))
                for identifier in process_id_list:
                    if "errors" in results[identifier]:
                        gscript.warning(results[identifier]["errors"])
                    else:
                        patch_names.append(results[identifier]["output"])
                        imported_tiles_num += 1
                # Empty the process list
                process_list = []
                process_id_list = []
                process_count = 0
        # no process should be left now
        assert not process_list
        assert not process_id_list
        assert not process_count

    gscript.verbose(
        _("Imported {imported} new tiles and used {used} existing tiles").format(
            used=used_existing_imported_tiles_num, imported=imported_tiles_num
        )
    )

    # if control variables match and multiple files need to be patched,
    # check product resolution, run r.patch

    # v.surf.rst lidar params
    rst_params = dict(tension=25, smooth=0.1, npmin=100)

    # Check that downloaded files match expected count
    completed_tiles_count = len(local_tile_path_list)
    if completed_tiles_count == tiles_needed_count:
        if len(patch_names) > 1:
            try:
                gscript.use_temp_region()
                # set the resolution
                if product_resolution:
                    gscript.run_command("g.region", res=product_resolution, flags="a")
                if gui_product == "naip":
                    for i in ("1", "2", "3", "4"):
                        patch_names_i = [name + "." + i for name in patch_names]
                        output = gui_output_layer + "." + i
                        gscript.run_command(
                            "r.patch", input=patch_names_i, output=output
                        )
                        gscript.raster_history(output)
                elif gui_product == "lidar":
                    gscript.run_command(
                        "v.patch",
                        flags="nzb",
                        input=patch_names,
                        output=gui_output_layer,
                    )
                    gscript.run_command(
                        "v.surf.rst",
                        input=gui_output_layer,
                        elevation=gui_output_layer,
                        nprocs=nprocs,
                        **rst_params
                    )
                else:
                    gscript.run_command(
                        "r.patch", input=patch_names, output=gui_output_layer
                    )
                    gscript.raster_history(gui_output_layer)
                gscript.del_temp_region()
                out_info = ("Patched composite layer '{0}' added").format(
                    gui_output_layer
                )
                gscript.verbose(out_info)
                # Remove files if not -k flag
                if not preserve_imported_tiles:
                    if gui_product == "naip":
                        for i in ("1", "2", "3", "4"):
                            patch_names_i = [name + "." + i for name in patch_names]
                            gscript.run_command(
                                "g.remove", type="raster", name=patch_names_i, flags="f"
                            )
                    elif gui_product == "lidar":
                        gscript.run_command(
                            "g.remove",
                            type="vector",
                            name=patch_names + [gui_output_layer],
                            flags="f",
                        )
                    else:
                        gscript.run_command(
                            "g.remove", type="raster", name=patch_names, flags="f"
                        )
            except CalledModuleError:
                gscript.fatal("Unable to patch tiles.")
            temp_down_count = _(
                "{0} of {1} tiles successfully imported and patched"
            ).format(completed_tiles_count, tiles_needed_count)
            gscript.info(temp_down_count)
        elif len(patch_names) == 1:
            if gui_product == "naip":
                for i in ("1", "2", "3", "4"):
                    gscript.run_command(
                        "g.rename",
                        raster=(patch_names[0] + "." + i, gui_output_layer + "." + i),
                    )
            elif gui_product == "lidar":
                if product_resolution:
                    gscript.run_command("g.region", res=product_resolution, flags="a")
                gscript.run_command(
                    "v.surf.rst",
                    input=patch_names[0],
                    elevation=gui_output_layer,
                    nprocs=nprocs,
                    **rst_params
                )
                if not preserve_imported_tiles:
                    gscript.run_command(
                        "g.remove", type="vector", name=patch_names[0], flags="f"
                    )
            else:
                gscript.run_command(
                    "g.rename", raster=(patch_names[0], gui_output_layer)
                )
            temp_down_count = _("Tile successfully imported")
            gscript.info(temp_down_count)
        else:
            gscript.fatal(_("No tiles imported successfully. Nothing to patch."))
    else:
        gscript.fatal(
            _("Error in getting or importing the data (see above). Please retry.")
        )

    # set appropriate color table
    if gui_product == "ned":
        gscript.run_command("r.colors", map=gui_output_layer, color="elevation")

    # composite NAIP
    if gui_product == "naip":
        gscript.use_temp_region()
        gscript.run_command("g.region", raster=gui_output_layer + ".1")
        gscript.run_command(
            "r.composite",
            red=gui_output_layer + ".1",
            green=gui_output_layer + ".2",
            blue=gui_output_layer + ".3",
            output=gui_output_layer,
        )
        gscript.raster_history(gui_output_layer)
        gscript.del_temp_region()


def cleanup():
    # Remove files in cleanup_list
    for f in cleanup_list:
        if os.path.exists(f):
            gscript.try_remove(f)


if __name__ == "__main__":
    options, flags = gscript.parser()
    atexit.register(cleanup)
    sys.exit(main())
