#!/usr/bin/env python
#-*- coding: utf-8 -*-

#MODULE:     r.in.usgs
#
#AUTHORS:    Zechariah Krautwurst
#            Anna Petrasova
#            Vaclav Petras
#
#MENTORS:    Anna Petrasova
#            Vaclav Petras
#
#PURPOSE:    Download user-requested products through the USGS TNM API.
#
#COPYRIGHT:  (C) 2017 Zechariah Krautwurst and the GRASS Development Team
#
#            This program is free software under the GNU General Public
#            License (>=v2). Read the file COPYING that comes with GRASS
#            for details.

#%module
#% description: Download user-requested products through the USGS TNM API
#% keyword: import
#% keyword: raster
#% keyword: USGS
#% keyword: NED
#% keyword: NLCD
#% keyword: NAIP
#%end

#%flag
#% key: i
#% description: Return USGS data information without downloading files
#%end

#%option
#% key: product
#% required: yes
#% options: ned,nlcd,naip
#% label: USGS data product
#% description: Available USGS data products to query
#%end

#%option G_OPT_R_OUTPUT
#% key: output_name
#% required: yes
#%end

#%option G_OPT_M_DIR
#% key: output_directory
#% required: yes
#% description: Directory for USGS data download and processing
#%end

#%option
#% key: ned_dataset
#% required: no
#% options: ned1sec, ned13sec, ned19sec
#% answer: ned1sec
#% label: NED dataset
#% description: Available NED datasets to query
#% descriptions: ned1sec;NED 1 arc-second;ned13sec;NED 1/3 arc-second;ned19sec;NED 1/9 arc-second
#% guisection: NED
#%end

#%option
#% key: nlcd_dataset
#% required: no
#% options: nlcd2001, nlcd2006, nlcd2011
#% answer: nlcd2011
#% label: NLCD dataset
#% description: Available NLCD datasets to query
#% descriptions: nlcd2001;National Land Cover Dataset - 2001;nlcd2006;National Land Cover Dataset - 2006;nlcd2011;National Land Cover Dataset - 2011
#% guisection: NLCD
#%end

#%option
#% key: nlcd_subset
#% required: no
#% options: landcover, impervious, canopy
#% answer: landcover
#% label: NLCD subset
#% description: Available NLCD subsets to query
#% descriptions: impervious;Percent Developed Imperviousness;canopy;Percent Tree Canopy;landcover;Land Cover
#% guisection: NLCD
#%end

#%option
#% key: resampling_method
#% type: string
#% required: no
#% multiple: no
#% options: default,nearest,bilinear,bicubic,lanczos,bilinear_f,bicubic_f,lanczos_f
#% description: Resampling method to use
#% descriptions: default;default method based on product;nearest;nearest neighbor;bilinear;bilinear interpolation;bicubic;bicubic interpolation;lanczos;lanczos filter;bilinear_f;bilinear interpolation with fallback;bicubic_f;bicubic interpolation with fallback;lanczos_f;lanczos filter with fallback
#% answer: default
#%end

#%flag
#% key: k
#% description: Keep extracted files after GRASS import and patch
#%end

#%rules
#% required: output_name, -i
#%end

import sys
import os
import zipfile
import grass.script as gscript
from six.moves.urllib.request import urlopen
from six.moves.urllib.error import URLError
from six.moves.urllib.parse import quote_plus
import json
import atexit

from grass.exceptions import CalledModuleError

cleanup_list = []


def get_current_mapset():
    """Get curret mapset name as a string"""
    return gscript.read_command('g.mapset', flags='p').strip()


def map_exists(element, name, mapset):
    """Check is map is present in the mapset given in the environment

    :param name: name of the map
    :param element: data type ('raster', 'raster_3d', and 'vector')
    """
    # change type to element used by find file
    if element == 'raster':
        element = 'cell'
    elif element == 'raster_3d':
        element = 'grid3'
    # g.findfile returns non-zero when file was not found
    # se we ignore return code and just focus on stdout
    process = gscript.start_command(
        'g.findfile',
        flags='n',
        element=element,
        file=name,
        mapset=mapset,
        stdout=gscript.PIPE,
        stderr=gscript.PIPE)
    output, errors = process.communicate()
    info = gscript.parse_key_val(output, sep='=')
    # file is the key questioned in grass.script.core find_file()
    # return code should be equivalent to checking the output
    if info['file']:
        return True
    else:
        return False


def main():
    # Hard-coded parameters needed for USGS datasets
    usgs_product_dict = {
        "ned": {
                'product': 'National Elevation Dataset (NED)',
                'dataset': {
                        'ned1sec': (1. / 3600, 30, 100),
                        'ned13sec': (1. / 3600 / 3, 10, 30),
                        'ned19sec': (1. / 3600 / 9, 3, 10)
                        },
                'subset': {},
                'extent': [
                        '1 x 1 degree',
                        '15 x 15 minute'
                         ],
                'format': 'IMG',
                'extension': 'img',
                'zip': True,
                'srs': 'wgs84',
                'srs_proj4': "+proj=longlat +ellps=GRS80 +datum=NAD83 +nodefs",
                'interpolation': 'bilinear',
                'url_split': '/'
                },
        "nlcd": {
                'product': 'National Land Cover Database (NLCD)',
                'dataset': {
                        'National Land Cover Database (NLCD) - 2001': (1. / 3600, 30, 100),
                        'National Land Cover Database (NLCD) - 2006': (1. / 3600, 30, 100),
                        'National Land Cover Database (NLCD) - 2011': (1. / 3600, 30, 100)
                        },
                'subset': {
                        'Percent Developed Imperviousness',
                        'Percent Tree Canopy',
                        'Land Cover'
                        },
                'extent': ['3 x 3 degree'],
                'format': 'GeoTIFF',
                'extension': 'tif',
                'zip': True,
                'srs': 'wgs84',
                'srs_proj4': "+proj=longlat +ellps=GRS80 +datum=NAD83 +nodefs",
                'interpolation': 'nearest',
                'url_split': '/'
                },
        "naip": {
                'product': 'USDA National Agriculture Imagery Program (NAIP)',
                'dataset': {
                        'Imagery - 1 meter (NAIP)': (1. / 3600 / 27, 1, 3)},
                'subset': {},
                'extent': [
                        '3.75 x 3.75 minute',
                         ],
                'format': 'JPEG2000',
                'extension': 'jp2',
                'zip': False,
                'srs': 'wgs84',
                'srs_proj4': "+proj=longlat +ellps=GRS80 +datum=NAD83 +nodefs",
                'interpolation': 'nearest',
                'url_split': '/'
                }
            }

    # Set GRASS GUI options and flags to python variables
    gui_product = options['product']

    # Variable assigned from USGS product dictionary
    nav_string = usgs_product_dict[gui_product]
    product = nav_string['product']
    product_format = nav_string['format']
    product_extension = nav_string['extension']
    product_is_zip = nav_string['zip']
    product_srs = nav_string['srs']
    product_proj4 = nav_string['srs_proj4']
    product_interpolation = nav_string['interpolation']
    product_url_split = nav_string['url_split']
    product_extent = nav_string['extent']
    gui_subset = None

    # Parameter assignments for each dataset
    if gui_product == 'ned':
        gui_dataset = options['ned_dataset']
        ned_api_name = ''
        if options['ned_dataset'] == 'ned1sec':
            ned_data_abbrv = 'ned_1arc_'
            ned_api_name = '1 arc-second'
        if options['ned_dataset'] == 'ned13sec':
            ned_data_abbrv = 'ned_13arc_'
            ned_api_name = '1/3 arc-second'
        if options['ned_dataset'] == 'ned19sec':
            ned_data_abbrv = 'ned_19arc_'
            ned_api_name = '1/9 arc-second'
        product_tag = product + " " + ned_api_name

    if gui_product == 'nlcd':
        gui_dataset = options['nlcd_dataset']
        if options['nlcd_dataset'] == 'nlcd2001':
            gui_dataset = 'National Land Cover Database (NLCD) - 2001'
        if options['nlcd_dataset'] == 'nlcd2006':
            gui_dataset = 'National Land Cover Database (NLCD) - 2006'
        if options['nlcd_dataset'] == 'nlcd2011':
            gui_dataset = 'National Land Cover Database (NLCD) - 2011'

        if options['nlcd_subset'] == 'landcover':
            gui_subset = 'Land Cover'
        if options['nlcd_subset'] == 'impervious':
            gui_subset = 'Percent Developed Imperviousness'
        if options['nlcd_subset'] == 'canopy':
            gui_subset = 'Percent Tree Canopy'
        product_tag = gui_dataset

    if gui_product == 'naip':
        gui_dataset = 'Imagery - 1 meter (NAIP)'
        product_tag = nav_string['product']

    # Assigning further parameters from GUI
    gui_output_layer = options['output_name']
    gui_resampling_method = options['resampling_method']
    gui_i_flag = flags['i']
    gui_k_flag = flags['k']
    work_dir = options['output_directory']

    preserve_extracted_files = gui_k_flag
    use_existing_extracted_files = True
    preserve_imported_tiles = gui_k_flag
    use_existing_imported_tiles = True

    # Returns current units
    try:
        proj = gscript.parse_command('g.proj', flags='g')
        if gscript.locn_is_latlong():
            product_resolution = nav_string['dataset'][gui_dataset][0]
        elif float(proj['meters']) == 1:
            product_resolution = nav_string['dataset'][gui_dataset][1]
        else:
            # we assume feet
            product_resolution = nav_string['dataset'][gui_dataset][2]
    except TypeError:
        product_resolution = False

    if gui_resampling_method == 'default':
        gui_resampling_method = nav_string['interpolation']
        gscript.verbose(_("The default resampling method for product {product} is {res}").format(product=gui_product,
                        res=product_interpolation))

    # Get coordinates for current GRASS computational region and convert to USGS SRS
    gregion = gscript.region()
    min_coords = gscript.read_command('m.proj', coordinates=(gregion['w'], gregion['s']),
                                      proj_out=product_proj4, separator='comma',
                                      flags='d')
    max_coords = gscript.read_command('m.proj', coordinates=(gregion['e'], gregion['n']),
                                      proj_out=product_proj4, separator='comma',
                                      flags='d')
    min_list = min_coords.split(',')[:2]
    max_list = max_coords.split(',')[:2]
    list_bbox = min_list + max_list
    str_bbox = ",".join((str(coord) for coord in list_bbox))

    # Format variables for TNM API call
    gui_prod_str = str(product_tag)
    datasets = quote_plus(gui_prod_str)
    prod_format = quote_plus(product_format)
    prod_extent = quote_plus(product_extent[0])

    # Create TNM API URL
    base_TNM = "https://viewer.nationalmap.gov/tnmaccess/api/products?"
    datasets_TNM = "datasets={0}".format(datasets)
    bbox_TNM = "&bbox={0}".format(str_bbox)
    prod_format_TNM = "&prodFormats={0}".format(prod_format)
    TNM_API_URL = base_TNM + datasets_TNM + bbox_TNM + prod_format_TNM
    if gui_product == 'nlcd':
        TNM_API_URL += "&prodExtents={0}".format(prod_extent)
    gscript.verbose("TNM API Query URL:\t{0}".format(TNM_API_URL))

    # Query TNM API
    try:
        TNM_API_GET = urlopen(TNM_API_URL, timeout=12)
    except URLError:
        gscript.fatal(_("USGS TNM API query has timed out. Check network configuration. Please try again."))
    except:
        gscript.fatal(_("USGS TNM API query has timed out. Check network configuration. Please try again."))

    # Parse return JSON object from API query
    try:
        return_JSON = json.load(TNM_API_GET)
        if return_JSON['errors']:
            TNM_API_error = return_JSON['errors']
            api_error_msg = "TNM API Error - {0}".format(str(TNM_API_error))
            gscript.fatal(api_error_msg)

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
        if f['datasets'][0] not in dataset_name:
            if len(dataset_name) <= 1:
                dataset_name.append(str(f['datasets'][0]))

    def exist_list():
        exist_TNM_titles.append(TNM_file_title)
        exist_dwnld_url.append(TNM_file_URL)
        if product_is_zip:
            exist_zip_list.append(local_zip_path)
            extract_zip_list.append(local_zip_path)
        else:
            exist_tile_list.append(local_tile_path)

    # Assign needed parameters from returned JSON
    tile_API_count = int(return_JSON['total'])
    tiles_needed_count = 0
    size_diff_tolerance = 5
    exist_dwnld_size = 0
    if tile_API_count > 0:
        dwnld_size = []
        dwnld_url = []
        dataset_name = []
        TNM_file_titles = []
        exist_dwnld_url = []
        exist_TNM_titles = []
        exist_zip_list = []
        exist_tile_list = []
        extract_zip_list = []
        # for each file returned, assign variables to needed parameters
        for f in return_JSON['items']:
            TNM_file_title = f['title']
            TNM_file_URL = str(f['downloadURL'])
            TNM_file_size = int(f['sizeInBytes'])
            TNM_file_name = TNM_file_URL.split(product_url_split)[-1]
            if gui_product == 'ned':
                local_file_path = os.path.join(work_dir, ned_data_abbrv + TNM_file_name)
                local_zip_path = os.path.join(work_dir, ned_data_abbrv + TNM_file_name)
                local_tile_path = os.path.join(work_dir, ned_data_abbrv + TNM_file_name)
            else:
                local_file_path = os.path.join(work_dir, TNM_file_name)
                local_zip_path = os.path.join(work_dir, TNM_file_name)
                local_tile_path = os.path.join(work_dir, TNM_file_name)
            file_exists = os.path.exists(local_file_path)
            file_complete = None
            # if file exists, but is incomplete, remove file and redownload
            if file_exists:
                existing_local_file_size = os.path.getsize(local_file_path)
                # if local file is incomplete
                if abs(existing_local_file_size - TNM_file_size) > size_diff_tolerance:
                    # add file to cleanup list
                    cleanup_list.append(local_file_path)
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

    # return fatal error if API query returns no results for GUI input
    elif tile_API_count == 0:
        gscript.fatal(_("TNM API ERROR or Zero tiles available for given input parameters."))

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
        exist_msg = _("\n{0} of {1} files/archive(s) exist locally and will be used by module.").format(len(exist_zip_list), tiles_needed_count)
        gscript.message(exist_msg)
    # TODO: fix this way of reporting and merge it with the one in use
    if exist_tile_list:
        exist_msg = _("\n{0} of {1} files/archive(s) exist locally and will be used by module.").format(len(exist_tile_list), tiles_needed_count)
        gscript.message(exist_msg)
    # TODO: simply continue with whatever is needed to be done in this case
    if cleanup_list:
        cleanup_msg = _("\n{0} existing incomplete file(s) detected and removed. Run module again.").format(len(cleanup_list))
        gscript.fatal(cleanup_msg)

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
        total_size_str = '0'

    # Prints 'none' if all tiles available locally
    if TNM_file_titles:
        TNM_file_titles_info = "\n".join(TNM_file_titles)
    else:
        TNM_file_titles_info = 'none'

    # Formatted return for 'i' flag
    if file_download_count <= 0:
        data_info = "USGS file(s) to download: NONE"
        if gui_product == 'nlcd':
            if tile_API_count != file_download_count:
                if tiles_needed_count == 0:
                    nlcd_unavailable = "NLCD {0} data unavailable for input parameters".format(gui_subset)
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
        data_info = '\n'.join(data_info).format(size=total_size_str,
                                                count=file_download_count,
                                                srs=product_srs,
                                                tile=TNM_file_titles_info)
    print(data_info)

    if gui_i_flag:
        gscript.info(_("To download USGS data, remove <i> flag, and rerun r.in.usgs."))
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
        if gui_product == 'ned':
            file_name = ned_data_abbrv + url.split(product_url_split)[-1]
            local_file_path = os.path.join(work_dir, file_name)
        else:
            file_name = url.split(product_url_split)[-1]
            local_file_path = os.path.join(work_dir, file_name)
        try:
            # download files in chunks rather than write complete files to memory
            dwnld_req = urlopen(url, timeout=12)
            download_bytes = int(dwnld_req.info()['Content-Length'])
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
            local_file.close()
            download_count += 1
            # determine if file is a zip archive or another format
            if product_is_zip:
                local_zip_path_list.append(local_file_path)
            else:
                local_tile_path_list.append(local_file_path)
            file_complete = "Download {0} of {1}: COMPLETE".format(
                    download_count, TNM_count)
            gscript.info(file_complete)
        except URLError:
            gscript.fatal(_("USGS download request has timed out. Network or formatting error."))
        except StandardError:
            cleanup_list.append(local_file_path)
            if download_count:
                file_failed = "Download {0} of {1}: FAILED".format(
                            download_count, TNM_count)
                gscript.fatal(file_failed)

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
        for z in local_zip_path_list:
            # Extract tiles from ZIP archives
            try:
                with zipfile.ZipFile(z, "r") as read_zip:
                    for f in read_zip.namelist():
                        if f.endswith(product_extension):
                            extracted_tile = os.path.join(work_dir, str(f))
                            remove_and_extract = True
                            if os.path.exists(extracted_tile):
                                if use_existing_extracted_files:
                                    # if the downloaded file is newer
                                    # than the extracted on, we extract
                                    if os.path.getmtime(extracted_tile) < os.path.getmtime(z):
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
                                read_zip.extract(f, work_dir)
                if os.path.exists(extracted_tile):
                    local_tile_path_list.append(extracted_tile)
                    if not preserve_extracted_files:
                        cleanup_list.append(extracted_tile)
            except IOError as error:
                cleanup_list.append(extracted_tile)
                gscript.fatal(_(
                    "Unable to locate or extract IMG file '{filename}'"
                    " from ZIP archive '{zipname}': {error}").format(
                        filename=extracted_tile, zipname=z, error=error))
        # TODO: do this before the extraction begins
        gscript.verbose(_("Extracted {extracted} new tiles and"
                          " used {used} existing tiles").format(
                            used=used_existing_extracted_tiles_num,
                            extracted=extracted_tiles_num
                            ))
        if old_extracted_tiles_num:
            gscript.verbose(_("Found {removed} existing tiles older"
                              " than the corresponding downloaded archive").format(
                            removed=old_extracted_tiles_num
                            ))
        if removed_extracted_tiles_num:
            gscript.verbose(_("Removed {removed} existing tiles").format(
                            removed=removed_extracted_tiles_num
                            ))

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
    for t in local_tile_path_list:
        # create variables for use in GRASS GIS import process
        LT_file_name = os.path.basename(t)
        LT_layer_name = os.path.splitext(LT_file_name)[0]
        # TODO: unlike the files, we don't compare date with input
        if use_existing_imported_tiles and map_exists("raster", LT_layer_name, mapset):
            patch_names.append(LT_layer_name)
            used_existing_imported_tiles_num += 1
            continue
        in_info = ("Importing and reprojecting {0}...").format(LT_file_name)
        gscript.info(in_info)
        # import to GRASS GIS
        try:
            gscript.run_command('r.import', input=t, output=LT_layer_name,
                                resolution='value', resolution_value=product_resolution,
                                extent="region", resample=product_interpolation)
        except CalledModuleError:
            in_error = ("Unable to import '{0}'").format(LT_file_name)
            gscript.warning(in_error)
        else:
            patch_names.append(LT_layer_name)
            imported_tiles_num += 1
        # do not remove by default with NAIP, there are no zip files
        if gui_product != 'naip' and not preserve_extracted_files:
            cleanup_list.append(t)
    gscript.verbose(_("Imported {imported} new tiles and"
                      " used {used} existing tiles").format(
                        used=used_existing_imported_tiles_num,
                        imported=imported_tiles_num
                        ))

    # if control variables match and multiple files need to be patched,
    # check product resolution, run r.patch

    # Check that downloaded files match expected count
    completed_tiles_count = len(local_tile_path_list)
    if completed_tiles_count == tiles_needed_count:
        if len(patch_names) > 1:
            try:
                gscript.use_temp_region()
                # set the resolution
                if product_resolution:
                    gscript.run_command('g.region', res=product_resolution, flags='a')
                if gui_product == 'naip':
                    for i in ('1', '2', '3', '4'):
                        patch_names_i = [name + '.' + i for name in patch_names]
                        output = gui_output_layer + '.' + i
                        gscript.run_command('r.patch', input=patch_names_i,
                                            output=output)
                        gscript.raster_history(output)
                else:
                    gscript.run_command('r.patch', input=patch_names,
                                        output=gui_output_layer)
                    gscript.raster_history(gui_output_layer)
                gscript.del_temp_region()
                out_info = ("Patched composite layer '{0}' added").format(gui_output_layer)
                gscript.verbose(out_info)
                # Remove files if not -k flag
                if not preserve_imported_tiles:
                    if gui_product == 'naip':
                        for i in ('1', '2', '3', '4'):
                            patch_names_i = [name + '.' + i for name in patch_names]
                            gscript.run_command('g.remove', type='raster',
                                                name=patch_names_i, flags='f')
                    else:
                        gscript.run_command('g.remove', type='raster',
                                            name=patch_names, flags='f')
            except CalledModuleError:
                gscript.fatal("Unable to patch tiles.")
            temp_down_count = _(
                "{0} of {1} tiles successfully imported and patched").format(
                    completed_tiles_count, tiles_needed_count)
            gscript.info(temp_down_count)
        elif len(patch_names) == 1:
            if gui_product == 'naip':
                for i in ('1', '2', '3', '4'):
                    gscript.run_command('g.rename', raster=(patch_names[0] + '.' + i, gui_output_layer + '.' + i))
            else:
                gscript.run_command('g.rename', raster=(patch_names[0], gui_output_layer))
            temp_down_count = _("Tile successfully imported")
            gscript.info(temp_down_count)
        else:
            gscript.fatal(_("No tiles imported successfully. Nothing to patch."))
    else:
        gscript.fatal(_(
            "Error in getting or importing the data (see above). Please retry."))

    # Keep source files if 'k' flag active
    if gui_k_flag:
        src_msg = ("<k> flag selected: Source tiles remain in '{0}'").format(work_dir)
        gscript.info(src_msg)

    # set appropriate color table
    if gui_product == 'ned':
        gscript.run_command('r.colors', map=gui_output_layer, color='elevation')

    # composite NAIP
    if gui_product == 'naip':
        gscript.use_temp_region()
        gscript.run_command('g.region', raster=gui_output_layer + '.1')
        gscript.run_command('r.composite', red=gui_output_layer + '.1',
                            green=gui_output_layer + '.2', blue=gui_output_layer + '.3',
                            output=gui_output_layer)
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
