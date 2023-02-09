#!/usr/bin/env python
#
############################################################################
#
# MODULE:      i.sentinel.download
# AUTHOR(S):   Martin Landa
# PURPOSE:     Downloads Sentinel data from Copernicus Open Access Hub,
#              USGS Earth Explorer or Google Cloud Storage.
# COPYRIGHT:   (C) 2018-2021 by Martin Landa, and the GRASS development team
#
#              This program is free software under the GNU General Public
#              License (>=v2). Read the file COPYING that comes with GRASS
#              for details.
#
#############################################################################

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
# % options: SLC,GRD,OCN,S2MSI1C,S2MSI2A,S2MSI2Ap,S3OL1EFR,S3OL1ERR,S3OL1SPC,S3OL1RAC,S3OL2WFR,S3OL2WRR,S3OL2LFR,S3OL2LRR,S3SL2LST,S3SL2FRP,S3SY2SYN,S3SY2VGP,S3SY2VG1,S3SY2V10,S3SY2AOD,S3SR2LAN
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
# % key: uuid
# % type: string
# % multiple: yes
# % description: List of UUID to download
# % guisection: Filter
# %end
# %option
# % key: relativeorbitnumber
# % type: integer
# % multiple: no
# % description: Relative orbit number to download (Sentinel-1: from 1 to 175; Sentinel-2: from 1 to 143)
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
# % label: Default is ESA Copernicus Open Access Hub (ESA_COAH), but Sentinel-2 L1C data can also be acquired from USGS Earth Explorer (USGS_EE) or Google Cloud Storage (GCS)
# % options: ESA_COAH,USGS_EE,GCS
# % answer: ESA_COAH
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
# % description: Sort order (see sort parameter)
# % options: asc,desc
# % answer: asc
# % guisection: Sort
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
# % required: output,-l
# % excludes: uuid,map,area_relation,clouds,producttype,start,end,limit,query,sort,order
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
from glob import glob
from datetime import datetime

import grass.script as gs

cloudcover_products = ["S2MSI1C", "S2MSI2A", "S2MSI2Ap"]


def create_dir(dir):
    if not os.path.isdir(dir):
        try:
            os.makedirs(dir)
            return 0
        except Exception as e:
            gs.warning(_("Could not create directory {}").format(dir))
            return 1
    else:
        gs.verbose(_("Directory {} already exists").format(dir))
        return 0


def get_aoi_box(vector=None):
    args = {}
    if vector:
        args["vector"] = vector

    # are we in LatLong location?
    s = gs.read_command("g.proj", flags="j")
    kv = gs.parse_key_val(s)
    if "+proj" not in kv:
        gs.fatal(
            _("Unable to get AOI bounding box: unprojected location not supported")
        )
    if kv["+proj"] != "longlat":
        info = gs.parse_command("g.region", flags="uplg", **args)
        return "POLYGON(({nw_lon} {nw_lat}, {ne_lon} {ne_lat}, {se_lon} {se_lat}, {sw_lon} {sw_lat}, {nw_lon} {nw_lat}))".format(
            nw_lat=info["nw_lat"],
            nw_lon=info["nw_long"],
            ne_lat=info["ne_lat"],
            ne_lon=info["ne_long"],
            sw_lat=info["sw_lat"],
            sw_lon=info["sw_long"],
            se_lat=info["se_lat"],
            se_lon=info["se_long"],
        )
    else:
        info = gs.parse_command("g.region", flags="upg", **args)
        return "POLYGON(({nw_lon} {nw_lat}, {ne_lon} {ne_lat}, {se_lon} {se_lat}, {sw_lon} {sw_lat}, {nw_lon} {nw_lat}))".format(
            nw_lat=info["n"],
            nw_lon=info["w"],
            ne_lat=info["n"],
            ne_lon=info["e"],
            sw_lat=info["s"],
            sw_lon=info["w"],
            se_lat=info["s"],
            se_lon=info["e"],
        )


def get_aoi(vector=None):
    args = {}
    if vector:
        args["input"] = vector

    if gs.vector_info_topo(vector)["areas"] <= 0:
        gs.fatal(_("No areas found in AOI map <{}>...").format(vector))
    elif gs.vector_info_topo(vector)["areas"] > 1:
        gs.warning(
            _(
                "More than one area found in AOI map <{}>. \
                      Using only the first area..."
            ).format(vector)
        )

    # are we in LatLong location?
    s = gs.read_command("g.proj", flags="j")
    kv = gs.parse_key_val(s)
    if "+proj" not in kv:
        gs.fatal(_("Unable to get AOI: unprojected location not supported"))
    geom_dict = gs.parse_command("v.out.ascii", format="wkt", **args)
    num_vertices = len(str(geom_dict.keys()).split(","))
    geom = [key for key in geom_dict][0]
    if kv["+proj"] != "longlat":
        gs.message(
            _("Generating WKT from AOI map ({} vertices)...").format(num_vertices)
        )
        if num_vertices > 500:
            gs.fatal(
                _(
                    "AOI map has too many vertices to be sent via HTTP GET (sentinelsat). \
                        Use 'v.generalize' to simplify the boundaries"
                )
            )
        coords = geom.replace("POLYGON((", "").replace("))", "").split(", ")
        poly = "POLYGON(("
        poly_coords = []
        for coord in coords:
            coord_latlon = gs.parse_command(
                "m.proj", coordinates=coord.replace(" ", ","), flags="od"
            )
            for key in coord_latlon:
                poly_coords.append((" ").join(key.split("|")[0:2]))
        poly += (", ").join(poly_coords) + "))"
        # Note: poly must be < 2000 chars incl. sentinelsat request (see RFC 2616 HTTP/1.1)
        if len(poly) > 1850:
            gs.fatal(
                _(
                    "AOI map has too many vertices to be sent via HTTP GET (sentinelsat). \
                        Use 'v.generalize' to simplify the boundaries"
                )
            )
        else:
            gs.message(_("Sending WKT from AOI map to ESA..."))
        return poly
    else:
        return geom


def get_bbox_from_S2_UTMtile(tile):
    # download and parse S2-UTM tilegrid kml
    tile_kml_url = (
        "https://sentinel.esa.int/documents/247904/1955685/"
        "S2A_OPER_GIP_TILPAR_MPC__20151209T095117_"
        "V20150622T000000_21000101T000000_B00.kml/"
        "ec05e22c-a2bc-4a13-9e84-02d5257b09a8"
    )
    r = requests.get(tile_kml_url, allow_redirects=True)
    root = ET.fromstring(r.content)
    r = None
    # get center coordinates from tile
    nsmap = {"kml": "http://www.opengis.net/kml/2.2"}
    search_string = ".//*[kml:name='{}']//kml:Point//kml:coordinates".format(tile)
    kml_search = root.findall(search_string, nsmap)
    coord_str = kml_search[0].text
    lon = float(coord_str.split(",")[0])
    lat = float(coord_str.split(",")[1])
    # create a mini bbox around the center
    bbox = (lon - 0.001, lat - 0.001, lon + 0.001, lat + 0.001)
    return bbox


def check_s2l1c_identifier(identifier, source="esa"):
    # checks beginning of identifier string for correct pattern
    if source == "esa":
        expression = "^(S2[A-B]_MSIL1C_20[0-9][0-9][0-9][0-9])"
        test = re.match(expression, identifier)
        if bool(test) is False:
            gs.fatal(
                _(
                    "Query parameter 'identifier'/'filename' has"
                    " to be in format S2X_MSIL1C_YYYYMMDDTHHMMSS"
                    "_NXXXX_RYYY_TUUUUU_YYYYMMDDTHHMMSS for "
                    "usage with USGS Earth Explorer"
                )
            )
    elif source == "usgs":
        # usgs can have two formats, depending on age
        expression1 = "^(L1C_T[0-9][0-9][A-Z][A-Z][A-Z]_A[0-9])"
        expression2 = "^(S2[A-B]_OPER_MSI_L1C_TL_EPA__2[0-9][0-9][0-9])"
        test1 = re.match(expression1, identifier)
        test2 = re.match(expression2, identifier)
        if bool(test1) is False and bool(test2) is False:
            gs.fatal(
                _(
                    "Query parameter 'usgs_identifier' has to be either in"
                    " format L1C_TUUUUU_AXXXXXX_YYYYMMDDTHHMMSS or "
                    "S2X_OPER_MSI_L1C_TL_EPA__YYYYMMDDTHHMMSS_"
                    "YYYYMMDDTHHMMSS_AOOOOOO_TUUUUU_NXX_YY_ZZ"
                )
            )
    return


def parse_manifest_gcs(root):
    """Parses the GCS manifest.safe for files to download and corrects urls
    if necessary.
    Returns: List of dictionaries with file information
    """
    files_list = []
    for elem in root.findall(".//dataObjectSection/dataObject"):
        elem_dict = elem.attrib
        for subelem in elem:
            for subsubelem in subelem:
                subsubelem_dict = subsubelem.attrib
                if subsubelem.tag == "fileLocation":
                    # some scenes (L2A summer 2018) have an inconsistent,
                    # very long url with "PHOEBUS" in it...
                    if "PHOEBUS" in subsubelem_dict["href"]:
                        for subfolder in ["DATASTRIP", "GRANULE"]:
                            if subfolder in subsubelem_dict["href"]:
                                path_end = subsubelem_dict["href"].split(subfolder)[-1]
                                href_corrected = "{}{}".format(subfolder, path_end)
                                subsubelem_dict["href"] = href_corrected
                elem_dict.update(subsubelem_dict)
                if subsubelem.tag == "checksum":
                    elem_dict.update({"checksum": subsubelem.text})
        files_list.append(elem_dict)
    return files_list


def get_checksum(filename, hash_function="md5"):
    """Generate checksum for file based on hash function (MD5 or SHA256).
    Source: https://onestopdataanalysis.com/checksum/
    """
    hash_function = hash_function.lower()

    with open(filename, "rb") as f:
        bytes = f.read()  # read file as bytes
        if hash_function == "md5":
            readable_hash = hashlib.md5(bytes).hexdigest()
        elif hash_function == "sha256":
            readable_hash = hashlib.sha256(bytes).hexdigest()
        elif hash_function == "sha3-256":
            readable_hash = hashlib.sha3_256(bytes).hexdigest()
        else:
            raise Exception(
                (
                    "{} is an invalid hash function. " "Please Enter MD5 or SHA256"
                ).format(hash_function)
            )

    return readable_hash


def download_gcs_file(url, destination, checksum_function, checksum):
    """Downloads a single file from GCS and performs checksumming."""
    # if file exists, check if checksum is ok, download again otherwise
    if os.path.isfile(destination):
        sum_existing = get_checksum(destination, checksum_function)
        if sum_existing == checksum:
            return 0
    try:
        r_file = requests.get(url, allow_redirects=True)
        open(destination, "wb").write(r_file.content)
        sum_dl = get_checksum(destination, checksum_function)
        if sum_dl.lower() != checksum.lower():
            gs.verbose(_("Checksumming not successful for {}").format(destination))
            return 2
        else:
            return 0

    except Exception as e:
        gs.verbose(_("There was a problem downloading {}").format(url))
        return 1


def download_gcs(scene, output):
    """Downloads a single S2 scene from Google Cloud Storage."""
    final_scene_dir = os.path.join(output, "{}.SAFE".format(scene))
    create_dir(final_scene_dir)
    level = scene.split("_")[1]
    if level == "MSIL1C":
        baseurl = "https://storage.googleapis.com/" "gcp-public-data-sentinel-2/tiles"
    elif level == "MSIL2A":
        baseurl = (
            "https://storage.googleapis.com/" "gcp-public-data-sentinel-2/L2/tiles"
        )
    tile_block = scene.split("_")[-2]
    tile_no = tile_block[1:3]
    tile_first_letter = tile_block[3]
    tile_last_letters = tile_block[4:]

    url_scene = os.path.join(
        baseurl, tile_no, tile_first_letter, tile_last_letters, "{}.SAFE".format(scene)
    )
    # download the manifest.safe file
    safe_file = "manifest.safe"
    safe_url = os.path.join(url_scene, safe_file)
    output_path_safe = os.path.join(final_scene_dir, safe_file)
    r_safe = requests.get(safe_url, allow_redirects=True)
    if r_safe.status_code != 200:
        gs.warning(_("Scene <{}> was not found on Google Cloud").format(scene))
        return 1
    root_manifest = ET.fromstring(r_safe.content)
    open(output_path_safe, "wb").write(r_safe.content)
    # parse manifest.safe for the rest of the data
    files_list = parse_manifest_gcs(root_manifest)
    # get all required folders
    hrefs = [file["href"] for file in files_list]
    hrefs_heads = [os.path.split(path)[0] for path in hrefs]
    required_rel_folders = list(set(hrefs_heads))
    # some paths inconsistently start with "." and some don't
    if any([not folder.startswith(".") for folder in required_rel_folders]):
        required_abs_folders = [
            os.path.join(final_scene_dir, item)
            for item in required_rel_folders
            if item != "."
        ]

    else:
        required_abs_folders = [
            item.replace(".", final_scene_dir)
            for item in required_rel_folders
            if item != "."
        ]

    # some scenes don't have additional metadata (GRANULE/.../AUX_DATA or
    # DATASTRIP/.../QI_DATA) but sen2cor seems to require at least the empty folder
    rest_folders = []
    check_folders = [("GRANULE", "AUX_DATA"), ("DATASTRIP", "QI_DATA")]
    for check_folder in check_folders:
        if (
            len(
                fnmatch.filter(
                    required_abs_folders,
                    "*{}*/{}*".format(check_folder[0], check_folder[1]),
                )
            )
            == 0
        ):
            # get required path
            basepath = min(
                [fol for fol in required_abs_folders if check_folder[0] in fol], key=len
            )
            rest_folders.append(os.path.join(basepath, check_folder[1]))

    # two folders are not in the manifest.safe, but the empty folders may
    # be required for other software (e.g. sen2cor)
    rest_folders.extend(
        [
            os.path.join(final_scene_dir, "rep_info"),
            os.path.join(final_scene_dir, "AUX_DATA"),
        ]
    )
    required_abs_folders.extend(rest_folders)

    # create folders
    for folder in required_abs_folders:
        req_folder_code = create_dir(folder)
    if req_folder_code != 0:
        return 1
    failed_downloads = []
    failed_checksums = []
    # no .html files are available on GCS but the folder might be required
    files_list_dl = [file for file in files_list if "HTML" not in file["href"]]
    for dl_file in tqdm(files_list_dl):
        # remove the '.' for relative path in the URLS
        if dl_file["href"].startswith("."):
            href_url = dl_file["href"][1:]
        else:
            href_url = "/{}".format(dl_file["href"])
        # neither os.path.join nor urljoin join these properly...
        dl_url = "{}{}".format(url_scene, href_url)
        output_path_file = "{}{}".format(final_scene_dir, href_url)
        checksum_function = dl_file["checksumName"].lower()
        dl_code = download_gcs_file(
            url=dl_url,
            destination=output_path_file,
            checksum_function=checksum_function,
            checksum=dl_file["checksum"],
        )
        if dl_code == 1:
            failed_downloads.append(dl_url)
        elif dl_code == 2:
            failed_checksums.append(dl_url)

    if len(failed_downloads) > 0:
        gs.verbose(
            _("Downloading was not successful for urls \n{}").format(
                "\n".join(failed_downloads)
            )
        )
        gs.warning(_("Downloading was not successful for scene <{}>").format(scene))
        return 1
    else:
        if len(failed_checksums) > 0:
            gs.warning(
                _(
                    "Scene {} was downloaded but checksumming was not "
                    "successful for one or more files."
                ).format(scene)
            )
            gs.verbose(
                _("Checksumming was not successful for urls \n{}").format(
                    "\n".join(failed_checksums)
                )
            )
        return 0


class SentinelDownloader(object):
    def __init__(
        self,
        user,
        password,
        api_url="https://apihub.copernicus.eu/apihub",
        cred_req=True,
    ):
        self._apiname = api_url
        self._user = user
        self._password = password
        self._cred_req = cred_req

        # init logger
        root = logging.getLogger()
        root.addHandler(logging.StreamHandler(sys.stderr))
        if self._apiname not in ["USGS_EE", "GCS"]:
            try:
                from sentinelsat import SentinelAPI
            except ImportError as e:
                gs.fatal(_("Module requires sentinelsat library: {}").format(e))
            # connect SciHub via API
            self._api = SentinelAPI(self._user, self._password, api_url=self._apiname)
        elif self._apiname == "USGS_EE":
            api_login = False
            while api_login is False:
                # avoid login conflict in possible parallel execution
                try:
                    self._api = landsatxplore.api.API(self._user, self._password)
                    api_login = True
                except EarthExplorerError as e:
                    time.sleep(1)
        self._products_df_sorted = None

    def filter(
        self,
        area,
        area_relation,
        clouds=None,
        producttype=None,
        limit=None,
        query={},
        start=None,
        end=None,
        sortby=[],
        asc=True,
        relativeorbitnumber=None,
    ):
        # Dict to identify plaforms from requested product
        platforms = {
            "SL": "Sentinel-1",
            "GR": "Sentinel-1",
            "OC": "Sentinel-1",
            "S2": "Sentinel-2",
            "S3": "Sentinel-3",
        }
        args = {}
        if clouds:
            args["cloudcoverpercentage"] = (0, int(clouds))
        if relativeorbitnumber:
            args["relativeorbitnumber"] = relativeorbitnumber
            if producttype.startswith("S2") and int(relativeorbitnumber) > 143:
                gs.warning("This relative orbit number is out of range")
            elif int(relativeorbitnumber) > 175:
                gs.warning(_("This relative orbit number is out of range"))
        if producttype:
            if producttype.startswith("S3"):
                # Using custom product names for Sentinel-3 products that look less cryptic
                split = [0, 2, 4, 5, 8]
                args["producttype"] = "_".join(
                    [producttype[i:j] for i, j in zip(split, split[1:] + [None])][1:]
                ).ljust(11, "_")
            else:
                args["producttype"] = producttype
            args["platformname"] = platforms[producttype[0:2]]
        if not start:
            start = "NOW-60DAYS"
        else:
            start = start.replace("-", "")
        if not end:
            end = "NOW"
        else:
            end = end.replace("-", "")
        if query:
            redefined = [value for value in args.keys() if value in query.keys()]
            if redefined:
                gs.warning(
                    _("Query overrides already defined options ({})").format(
                        ",".join(redefined)
                    )
                )
            args.update(query)
        gs.verbose(
            _("Query: area={} area_relation={} date=({}, {}) args={}").format(
                area, area_relation, start, end, args
            )
        )
        if self._cred_req is False:
            # in the main function it is ensured that there is an "identifier" query
            self._products_df_sorted = pandas.DataFrame(
                {"identifier": [query["identifier"]]}
            )
            return

        products = self._api.query(
            area=area, area_relation=area_relation, date=(start, end), **args
        )
        products_df = self._api.to_dataframe(products)
        if len(products_df) < 1:
            gs.message(_("No product found"))
            return

        # sort and limit to first sorted product
        if sortby:
            self._products_df_sorted = products_df.sort_values(
                sortby, ascending=[asc] * len(sortby)
            )
        else:
            self._products_df_sorted = products_df

        if limit:
            self._products_df_sorted = self._products_df_sorted.head(int(limit))

        gs.message(
            _("{} Sentinel product(s) found").format(len(self._products_df_sorted))
        )

    def list(self):
        if self._products_df_sorted is None:
            return
        id_kw = ("uuid", "entity_id")
        identifier_kw = ("identifier", "display_id")
        cloud_kw = ("cloudcoverpercentage", "cloud_cover")
        time_kw = ("beginposition", "acquisition_date")
        kw_idx = 1 if self._apiname == "USGS_EE" else 0
        for idx in range(len(self._products_df_sorted[id_kw[kw_idx]])):
            if cloud_kw[kw_idx] in self._products_df_sorted:
                ccp = "{0:2.0f}%".format(
                    float(self._products_df_sorted[cloud_kw[kw_idx]][idx])
                )
            else:
                ccp = "cloudcover_NA"

            print_str = "{0} {1}".format(
                self._products_df_sorted[id_kw[kw_idx]][idx],
                self._products_df_sorted[identifier_kw[kw_idx]][idx],
            )
            if kw_idx == 1:
                time_string = self._products_df_sorted[time_kw[kw_idx]][idx]
            else:
                time_string = self._products_df_sorted[time_kw[kw_idx]][idx].strftime(
                    "%Y-%m-%dT%H:%M:%SZ"
                )
            print_str += " {0} {1}".format(time_string, ccp)
            if kw_idx == 0:
                print_str += " {0}".format(self._products_df_sorted["producttype"][idx])
                print_str += " {0}".format(self._products_df_sorted["size"][idx])

            print(print_str)

    def skip_existing(self, output, pattern_file):
        prod_df_type = type(self._products_df_sorted)
        # Check i skipping is possible/required
        if prod_df_type != dict:
            if self._products_df_sorted.empty:
                return
        elif not self._products_df_sorted or os.path.exists(output) == False:
            return
        # Check if ingestion date is returned by API
        if "ingestiondate" not in self._products_df_sorted:
            gs.warning(
                _(
                    "Ingestiondate not returned. Cannot filter previously downloaded scenes"
                )
            )
            return
        # Check for previously downloaded scenes
        existing_files = [
            os.path.join(output, f)
            for f in os.listdir(output)
            if re.search(r".zip$|.safe$|.ZIP$|.SAFE$", f)
        ]
        if len(existing_files) <= 1:
            return
        # Filter by ingestion date
        skiprows = []
        for idx, display_id in enumerate(self._products_df_sorted["identifier"]):
            existing_file = [sfile for sfile in existing_files if display_id in sfile]
            if existing_file:
                creation_time = datetime.fromtimestamp(
                    os.path.getctime(existing_file[0])
                )
                if self._products_df_sorted["ingestiondate"][idx] <= creation_time:
                    gs.message(
                        _(
                            "Skipping scene: {} which is already downloaded.".format(
                                self._products_df_sorted["identifier"][idx]
                            )
                        )
                    )
                    skiprows.append(display_id)
        if prod_df_type == dict:
            for scene in skiprows:
                idx = self._products_df_sorted["identifier"].index(scene)
                for key in self._products_df_sorted:
                    self._products_df_sorted[key].pop(idx)
        else:
            self._products_df_sorted = self._products_df_sorted[
                ~self._products_df_sorted["identifier"].isin(skiprows)
            ]

    def download(self, output, sleep=False, maxretry=False, datasource="ESA_COAH"):
        if self._products_df_sorted is None:
            return

        create_dir(output)
        gs.message(_("Downloading data into <{}>...").format(output))
        if datasource == "USGS_EE":
            from landsatxplore.earthexplorer import EarthExplorer
            from landsatxplore.errors import EarthExplorerError
            from zipfile import ZipFile

            ee_login = False
            while ee_login is False:
                # avoid login conflict in possible parallel execution
                try:
                    ee = EarthExplorer(self._user, self._password)
                    ee_login = True
                except EarthExplorerError as e:
                    time.sleep(1)
            for idx in range(len(self._products_df_sorted["entity_id"])):
                scene = self._products_df_sorted["entity_id"][idx]
                identifier = self._products_df_sorted["display_id"][idx]
                zip_file = os.path.join(output, "{}.zip".format(identifier))
                gs.message(_("Downloading {}...").format(identifier))
                try:
                    ee.download(identifier=identifier, output_dir=output, timeout=600)
                except EarthExplorerError as e:
                    gs.fatal(_(e))
                ee.logout()
                # extract .zip to get "usual" .SAFE
                with ZipFile(zip_file, "r") as zip:
                    safe_name = zip.namelist()[0].split("/")[0]
                    outpath = os.path.join(output, safe_name)
                    zip.extractall(path=output)
                gs.message(_("Downloaded to <{}>").format(outpath))
                try:
                    os.remove(zip_file)
                except Exception as e:
                    gs.warning(_("Unable to remove {0}:{1}").format(zip_file, e))

        elif datasource == "ESA_COAH":
            for idx in range(len(self._products_df_sorted["uuid"])):
                gs.message(
                    "{} -> {}.SAFE".format(
                        self._products_df_sorted["uuid"][idx],
                        os.path.join(
                            output, self._products_df_sorted["identifier"][idx]
                        ),
                    )
                )
                # download
                out = self._api.download(self._products_df_sorted["uuid"][idx], output)
                if sleep:
                    x = 1
                    online = out["Online"]
                    while not online:
                        # sleep is in minutes so multiply by 60
                        time.sleep(int(sleep) * 60)
                        out = self._api.download(
                            self._products_df_sorted["uuid"][idx], output
                        )
                        x += 1
                        if x > maxretry:
                            online = True
        elif datasource == "GCS":
            for scene_id in self._products_df_sorted["identifier"]:
                gs.message(_("Downloading {}...").format(scene_id))
                dl_code = download_gcs(scene_id, output)
                if dl_code == 0:
                    gs.message(
                        _("Downloaded to {}").format(
                            os.path.join(output, "{}.SAFE".format(scene_id))
                        )
                    )
                else:
                    # remove incomplete file
                    del_folder = os.path.join(output, "{}.SAFE".format(scene_id))
                    try:
                        shutil.rmtree(del_folder)
                    except Exception as e:
                        gs.warning(
                            _(
                                "Unable to removed unfinished "
                                "download {}".format(del_folder)
                            )
                        )

    def save_footprints(self, map_name):
        if self._products_df_sorted is None:
            return
        if self._apiname == "USGS_EE":
            gs.fatal(_("USGS Earth Explorer does not support footprint download."))
        try:
            from osgeo import ogr, osr
        except ImportError as e:
            gs.fatal(_("Option <footprints> requires GDAL library: {}").format(e))

        gs.message(_("Writing footprints into <{}>...").format(map_name))
        driver = ogr.GetDriverByName("GPKG")
        tmp_name = gs.tempfile() + ".gpkg"
        data_source = driver.CreateDataSource(tmp_name)

        srs = osr.SpatialReference()
        srs.ImportFromEPSG(4326)

        # features can be polygons or multi-polygons
        layer = data_source.CreateLayer(str(map_name), srs, ogr.wkbMultiPolygon)

        # attributes
        attrs = OrderedDict(
            [
                ("uuid", ogr.OFTString),
                ("ingestiondate", ogr.OFTString),
                ("cloudcoverpercentage", ogr.OFTInteger),
                ("producttype", ogr.OFTString),
                ("identifier", ogr.OFTString),
            ]
        )

        # Sentinel-1 data does not have cloudcoverpercentage
        prod_types = [type for type in self._products_df_sorted["producttype"]]
        if not any(type in prod_types for type in cloudcover_products):
            del attrs["cloudcoverpercentage"]

        for key in attrs.keys():
            field = ogr.FieldDefn(key, attrs[key])
            layer.CreateField(field)

        # features
        for idx in range(len(self._products_df_sorted["uuid"])):
            wkt = self._products_df_sorted["footprint"][idx]
            feature = ogr.Feature(layer.GetLayerDefn())
            newgeom = ogr.CreateGeometryFromWkt(wkt)
            # convert polygons to multi-polygons
            newgeomtype = ogr.GT_Flatten(newgeom.GetGeometryType())
            if newgeomtype == ogr.wkbPolygon:
                multigeom = ogr.Geometry(ogr.wkbMultiPolygon)
                multigeom.AddGeometryDirectly(newgeom)
                feature.SetGeometry(multigeom)
            else:
                feature.SetGeometry(newgeom)
            for key in attrs.keys():
                if key == "ingestiondate":
                    value = self._products_df_sorted[key][idx].strftime(
                        "%Y-%m-%dT%H:%M:%SZ"
                    )
                else:
                    value = self._products_df_sorted[key][idx]
                feature.SetField(key, value)
            layer.CreateFeature(feature)
            feature = None

        data_source = None

        # coordinates of footprints are in WKT -> fp precision issues
        # -> snap
        gs.run_command(
            "v.import",
            input=tmp_name,
            output=map_name,
            layer=map_name,
            snap=1e-10,
            quiet=True,
        )

    def get_products_from_uuid_usgs(self, uuid_list):
        scenes = []
        for uuid in uuid_list:
            metadata = self._api.metadata(uuid, "SENTINEL_2A")
            scenes.append(metadata)
        scenes_df = pandas.DataFrame.from_dict(scenes)
        self._products_df_sorted = scenes_df
        gs.message(
            _("{} Sentinel product(s) found").format(len(self._products_df_sorted))
        )

    def set_uuid(self, uuid_list):
        """Set products by uuid.

        TODO: Find better implementation

        :param uuid: uuid to download
        """
        if self._apiname == "USGS_EE":
            self.get_products_from_uuid_usgs(uuid_list)
        else:
            from sentinelsat.sentinel import SentinelAPIError

            self._products_df_sorted = {"uuid": []}
            for uuid in uuid_list:
                try:
                    odata = self._api.get_product_odata(uuid, full=True)
                except SentinelAPIError as e:
                    gs.error(_("{0}. UUID {1} skipped".format(e, uuid)))
                    continue

                for k, v in odata.items():
                    if k == "id":
                        k = "uuid"
                    elif k == "Sensing start":
                        k = "beginposition"
                    elif k == "Product type":
                        k = "producttype"
                    elif k == "Cloud cover percentage":
                        k = "cloudcoverpercentage"
                    elif k == "Identifier":
                        k = "identifier"
                    elif k == "Ingestion Date":
                        k = "ingestiondate"
                    elif k == "footprint":
                        pass
                    else:
                        continue
                    if k not in self._products_df_sorted:
                        self._products_df_sorted[k] = []
                    self._products_df_sorted[k].append(v)

    def filter_USGS(
        self,
        area,
        area_relation,
        clouds=None,
        producttype=None,
        limit=None,
        query={},
        start=None,
        end=None,
        sortby=[],
        asc=True,
        relativeorbitnumber=None,
    ):
        if area_relation != "Intersects":
            gs.fatal(
                _("USGS Earth Explorer only supports area_relation" " 'Intersects'")
            )
        if relativeorbitnumber:
            gs.fatal(
                _(
                    "USGS Earth Explorer does not support 'relativeorbitnumber'"
                    " option."
                )
            )
        if producttype and producttype != "S2MSI1C":
            gs.fatal(_("USGS Earth Explorer only supports producttype S2MSI1C"))
        if query:
            if not any(
                key in query for key in ["identifier", "filename", "usgs_identifier"]
            ):
                gs.fatal(
                    _(
                        "USGS Earth Explorer only supports query options"
                        " 'filename', 'identifier' or 'usgs_identifier'."
                    )
                )
            if "usgs_identifier" in query:
                # get entityId from usgs identifier and directly save results
                usgs_id = query["usgs_identifier"]
                check_s2l1c_identifier(usgs_id, source="usgs")
                # entity_id = self._api.lookup('SENTINEL_2A', [usgs_id],
                #                              inverse=True)
                entity_id = self._api.get_entity_id([usgs_id], "SENTINEL_2A")
                self.get_products_from_uuid_usgs(entity_id)
                return
            else:
                if "filename" in query:
                    esa_id = query["filename"].replace(".SAFE", "")
                else:
                    esa_id = query["identifier"]
                check_s2l1c_identifier(esa_id, source="esa")
                esa_prod_id = esa_id.split("_")[-1]
                utm_tile = esa_id.split("_")[-2]
                acq_date = esa_id.split("_")[2].split("T")[0]
                acq_date_string = "{0}-{1}-{2}".format(
                    acq_date[:4], acq_date[4:6], acq_date[6:]
                )
                start_date = end_date = acq_date_string
                # build the USGS style S2-identifier
                if utm_tile.startswith("T"):
                    utm_tile_base = utm_tile[1:]
                bbox = get_bbox_from_S2_UTMtile(utm_tile_base)
        else:
            # get coordinate pairs from wkt string
            str_1 = "POLYGON(("
            str_2 = "))"
            coords = area[area.find(str_1) + len(str_1) : area.rfind(str_2)].split(",")
            # add one space to first pair for consistency
            coords[0] = " " + coords[0]
            lons = [float(pair.split(" ")[1]) for pair in coords]
            lats = [float(pair.split(" ")[2]) for pair in coords]
            bbox = (min(lons), min(lats), max(lons), max(lats))
            start_date = start
            end_date = end
        usgs_args = {
            "dataset": "SENTINEL_2A",
            "bbox": bbox,
            "start_date": start_date,
            "end_date": end_date,
        }
        if clouds:
            usgs_args["max_cloud_cover"] = clouds
        if limit:
            usgs_args["max_results"] = limit
        scenes = self._api.search(**usgs_args)
        self._api.logout()
        if query:
            # check if the UTM-Tile is correct, remove otherwise
            for scene in scenes:
                if scene["display_id"].split("_")[1] != utm_tile:
                    scenes.remove(scene)
            # remove redundant scene
            if len(scenes) == 2:
                for scene in scenes:
                    prod_id = scene["display_id"].split("_")[-1]
                    if prod_id != esa_prod_id:
                        scenes.remove(scene)
        if len(scenes) < 1:
            gs.message(_("No product found"))
            return
        scenes_df = pandas.DataFrame.from_dict(scenes)
        if sortby:
            # replace sortby keywords with USGS keywords
            for idx, keyword in enumerate(sortby):
                if keyword == "cloudcoverpercentage":
                    sortby[idx] = "cloud_cover"
                    # turn cloudcover to float to make it sortable
                    scenes_df["cloud_cover"] = pandas.to_numeric(
                        scenes_df["cloud_cover"]
                    )
                elif keyword == "ingestiondate":
                    sortby[idx] = "acquisition_date"
                # what does sorting by footprint mean
                elif keyword == "footprint":
                    sortby[idx] = "display_id"
            self._products_df_sorted = scenes_df.sort_values(
                sortby, ascending=[asc] * len(sortby), ignore_index=True
            )
        else:
            self._products_df_sorted = scenes_df
        gs.message(
            _("{} Sentinel product(s) found").format(len(self._products_df_sorted))
        )


def main():
    global cloudcover_products

    cred_req = True
    api_url = "https://apihub.copernicus.eu/apihub"
    if options["datasource"] == "GCS":
        if options["producttype"] not in ["S2MSI2A", "S2MSI1C"]:
            gs.fatal(
                _("Download from GCS only supports producttypes S2MSI2A " "or S2MSI1C")
            )
        if options["query"]:
            queries = options["query"].split(",")
            query_names = [query.split("=")[0] for query in queries]
            if "identifier" in query_names and not flags["l"]:
                cred_req = False
    elif options["datasource"] == "USGS_EE":
        api_url = "USGS_EE"

    if not options["settings"] and cred_req is True:
        gs.fatal(
            _(
                "Unless using the options datasource=GCS and "
                "query='identifier=...', credentials are required via "
                "the settings parameter. "
            )
        )
    user = password = None
    if cred_req is True:
        if options["settings"] == "-":
            # stdin
            import getpass

            user = input(_("Insert username: "))
            password = getpass.getpass(_("Insert password: "))
            url = input(_("Insert API URL (leave empty for {}): ").format(api_url))
            if url:
                api_url = url
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

    if flags["b"]:
        map_box = get_aoi(options["map"])
    else:
        map_box = get_aoi_box(options["map"])

    sortby = options["sort"].split(",")
    if not options["producttype"] in cloudcover_products:
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
    try:
        downloader = SentinelDownloader(user, password, api_url, cred_req)

        if options["uuid"]:
            downloader.set_uuid(options["uuid"].split(","))
        else:
            query = {}
            if options["query"]:
                for item in options["query"].split(","):
                    k, v = item.split("=")
                    query[k] = v
            filter_args = {
                "area": map_box,
                "area_relation": options["area_relation"],
                "clouds": options["clouds"],
                "producttype": options["producttype"],
                "limit": options["limit"],
                "query": query,
                "start": options["start"],
                "end": options["end"],
                "sortby": sortby,
                "asc": True if options["order"] == "asc" else False,
                "relativeorbitnumber": options["relativeorbitnumber"],
            }

            if options["datasource"] == "ESA_COAH" or options["datasource"] == "GCS":
                downloader.filter(**filter_args)
            elif options["datasource"] == "USGS_EE":
                downloader.filter_USGS(**filter_args)
    except Exception as e:
        gs.fatal(_("Unable to connect to {0}: {1}").format(options["datasource"], e))

    if options["footprints"]:
        downloader.save_footprints(options["footprints"])

    if flags["s"]:
        downloader.skip_existing(options["output"], "*.zip")

    if flags["l"]:
        downloader.list()
        return

    downloader.download(
        options["output"],
        options["sleep"],
        int(options["retry"]),
        options["datasource"],
    )

    return 0


if __name__ == "__main__":
    options, flags = gs.parser()

    if options["datasource"] == "GCS":
        # Lazy import nonstandard modules
        try:
            import pandas
        except ImportError as e:
            gs.fatal(_("Module requires pandas library: {}").format(e))

        try:
            import requests
        except ImportError as e:
            gs.fatal(_("Module requires requests library: {}").format(e))

        try:
            from tqdm import tqdm
        except ImportError as e:
            gs.fatal(_("Module requires tqdm library: {}").format(e))
    elif options["datasource"] == "USGS_EE":
        try:
            import landsatxplore.api
            from landsatxplore.errors import EarthExplorerError
        except ImportError as e:
            gs.fatal(_("Module requires landsatxplore library: {}").format(e))

    sys.exit(main())
