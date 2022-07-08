#!/usr/bin/env python
# coding=utf-8
#
############################################################################
#
# MODULE:   i.sentinel.preproc
# AUTHOR(S):    Roberta Fagandini, Moritz Lennert, Roberto Marzocchi
# PURPOSE:  Import and perform atmospheric correction for Sentinel-2 images
#
# COPYRIGHT:    (C) 2018 by Roberta Fagandini, and the GRASS Development Team
#
#        This program is free software under the GNU General Public
#        License (>=v2). Read the file COPYING that comes with GRASS
#        for details.
#
############################################################################

# %Module
# % description: Imports and performs atmospheric correction of Sentinel-2 images.
# % keyword: imagery
# % keyword: satellite
# % keyword: Sentinel
# % keyword: download
# % keyword: import
# % keyword: atmospheric correction
# %End
# %option G_OPT_M_DIR
# % key: input_dir
# % description: Name of the directory where the image and metadata file are stored (*.SAFE)
# % required : yes
# %end
# %option G_OPT_R_ELEV
# % required : yes
# %end
# %option G_OPT_R_INPUT
# % key: visibility
# % description: Name of input visibility raster map (in m)
# % required : no
# % guisection: Input
# %end
# %option
# % key: atmospheric_model
# % type: string
# % description: Select the proper Atmospheric model
# % options: Automatic,No gaseous absorption,Tropical,Midlatitude summer,Midlatitude winter,Subarctic summer,Subarctic winter,Us standard 62
# % answer: Automatic
# % required : yes
# % multiple: no
# % guisection: 6S Parameters
# %end
# %option
# % key: aerosol_model
# % type: string
# % description: Select the proper Aerosol model
# % options: No aerosols,Continental model,Maritime model,Urban model,Shettle model for background desert aerosol,Biomass burning,Stratospheric model
# % answer: Continental model
# % required : yes
# % multiple: no
# % guisection: 6S Parameters
# %end
# %option
# % key: aod_value
# % type: string
# % description: AOD value at 550nm
# % required : no
# % guisection: 6S Parameters
# %end
# %option G_OPT_F_INPUT
# % key: aeronet_file
# % description: Name of the AERONET file for computing AOD at 550nm
# % required : no
# % guisection: 6S Parameters
# %end
# %option
# % key: suffix
# % type: string
# % description: Suffix for output raster maps
# % required : yes
# %end
# %option
# % key: rescale
# % key_desc: min,max
# % type: string
# % description: Rescale output raster map
# % answer: 0,1
# % required : no
# % guisection: Output
# %end
# %option G_OPT_F_OUTPUT
# % key: text_file
# % description: Name for output text file to be used as input in i.sentinel.mask
# % required : no
# % guisection: Output
# %end
# %option
# % key: topo_method
# % description: Topographic correction method
# % options: cosine, minnaert, c-factor, percent
# % required : no
# % guisection: Input
# %end
# %option
# % key: topo_prefix
# % description: Prefix for topographic corrected images
# % required : no
# % answer: tcor
# % guisection: Output
# %end
# %option
# % key: memory
# % type: integer
# % required: no
# % multiple: no
# % label: Maximum memory to be used (in MB)
# % description: Cache size for raster rows
# % answer: 300
# %end
# %flag
# % key: a
# % description: Use AOD instead visibility
# % guisection: 6S Parameters
# %end
# %flag
# % key: t
# % description: Create the input text file for i.sentinel.mask
# % guisection: Output
# %end
# %flag
# % key: r
# % description: Reproject raster data using r.import if needed
# % guisection: Input
# %end
# %flag
# % key: i
# % description: Skip import of Sentinel bands
# % guisection: Input
# %end
# %flag
# % key: c
# % description: Computes topographic correction of reflectance
# % guisection: Input
# %end
# %flag
# % key: l
# % description: Link raster data instead of importing
# % guisection: Settings
# %end
# %flag
# % key: o
# % description: Override projection check (use current location's projection)
# % guisection: Settings
# %end
# %rules
# % requires: -t,text_file
# % requires: text_file,-t
# % required: aod_value,aeronet_file,visibility
# % requires: aod_value,-a
# % requires: aeronet_file,-a
# % requires: -a,aod_value,aeronet_file
# % exclusive: -a,visibility
# % exclusive: -l,-r
# % exclusive: -o,-r
# %end

import grass.script as gscript
import xml.etree.ElementTree as et
from datetime import datetime
import os
import math
import sys
import shutil
import re
import glob
import atexit


def main():

    bands = {}
    cor_bands = {}
    dem = options["elevation"]
    vis = options["visibility"]
    input_dir = options["input_dir"]
    memory = options["memory"]
    check_ndir = 0
    check_odir = 0
    # Check if the input folder has old or new name
    # Check if the input folder belongs to a L1C image
    level_dir = os.path.basename(input_dir).split("_")
    # Check if the input directory is a .SAFE folder
    if not input_dir.endswith(".SAFE"):
        gscript.fatal(
            "The input directory is not a .SAFE folder. Please check the input directory"
        )
    if level_dir[1] == "OPER" and level_dir[3] == "MSIL1C":
        check_odir = 1
        filename = [i for i in os.listdir(input_dir) if i.startswith("S")]
        string = str(filename).strip("['']")
        mtd_file = os.path.join(input_dir, string)
    elif level_dir[1] == "MSIL1C":
        check_ndir = 1
        mtd_file = os.path.join(input_dir, "MTD_MSIL1C.xml")
    else:
        gscript.fatal(
            "The input directory does not belong to a L1C Sentinel image. Please check the input directory"
        )
    # Check if Metadata file exists
    if not os.path.isfile(mtd_file):
        gscript.fatal("Metadata file not found. Please check the input directory")
    atmo_mod = options["atmospheric_model"]
    aerosol_mod = options["aerosol_model"]
    aeronet_file = options["aeronet_file"]
    check_file = 0
    check_value = 0
    mapset = gscript.gisenv()["MAPSET"]
    suffix = options["suffix"]
    rescale = options["rescale"]
    processid = os.getpid()
    txt_file = options["text_file"]
    tmp_file = gscript.tempfile()
    topo_method = options["topo_method"]

    if topo_method and not flags["c"]:
        gscript.warning(
            _(
                "To computes topographic correction of reflectance "
                "please select also 'c' flag"
            )
        )
    elif flags["c"] and not topo_method:
        gscript.warning(
            _(
                "Topographic correction of reflectance will use "
                "default method 'c-factor'"
            )
        )

    if not gscript.find_program("i.sentinel.import", "--help"):
        gscript.fatal(
            "Module requires i.sentinel.import. Please install it using g.extension."
        )

    # Import bands
    if not flags["i"]:
        imp_flags = "o" if flags["o"] else ""
        imp_flags += "l" if flags["l"] else ""
        imp_flags += "r" if flags["r"] else ""
        imp_flags = None if imp_flags == "" else imp_flags
        i_s_imp_dir = os.path.dirname(input_dir)
        pattern_file = os.path.basename(input_dir).split(".")[0]

        # import
        gscript.run_command(
            "i.sentinel.import",
            input=i_s_imp_dir,
            pattern_file=pattern_file,
            flags=imp_flags,
            memory=memory,
        )

    # Create xml "tree" for reading parameters from metadata
    tree = et.parse(mtd_file)
    root = tree.getroot()

    # Start reading the xml file
    if check_ndir == 1:
        for elem in root[0].findall("Product_Info"):
            datatake = elem.find("Datatake")
            # Geometrical conditions = sensor
            sensor = datatake.find("SPACECRAFT_NAME")
            # Acquisition date and time
            time_str = elem.find("GENERATION_TIME")
            # Date and time conversion
            time_py = datetime.strptime(time_str.text, "%Y-%m-%dT%H:%M:%S.%fZ")
            # Compute decimal hour
            dec_hour = (
                float(time_py.hour)
                + float(time_py.minute) / 60
                + float(time_py.second) / 3600
            )
            # Read input bands from metadata
            product = elem.find("Product_Organisation")
            g_list = product.find("Granule_List")
            granule = g_list.find("Granule")
            images = granule.find("IMAGE_FILE")
            img_name = images.text.split("/")
            # Check if input exist and if the mtd file corresponds with the input image
            for img in root.iter("IMAGE_FILE"):
                a = img.text.split(".jp2")[0].split("/")
                b = a[3].split("_")
                if (
                    gscript.find_file(a[3], element="cell", mapset=mapset)["file"]
                    or gscript.find_file(a[3], element="cell")["file"]
                    or b[2] == "TCI"
                ):
                    if b[2] == "B01":
                        bands["costal"] = a[3]
                    elif b[2] == "B02":
                        bands["blue"] = a[3]
                    elif b[2] == "B03":
                        bands["green"] = a[3]
                    elif b[2] == "B04":
                        bands["red"] = a[3]
                    elif b[2] == "B05":
                        bands["re5"] = a[3]
                    elif b[2] == "B06":
                        bands["re6"] = a[3]
                    elif b[2] == "B07":
                        bands["re7"] = a[3]
                    elif b[2] == "B08":
                        bands["nir"] = a[3]
                    elif b[2] == "B8A":
                        bands["nir8a"] = a[3]
                    elif b[2] == "B09":
                        bands["vapour"] = a[3]
                    elif b[2] == "B10":
                        bands["cirrus"] = a[3]
                    elif b[2] == "B11":
                        bands["swir11"] = a[3]
                    elif b[2] == "B12":
                        bands["swir12"] = a[3]
                else:
                    gscript.fatal(
                        (
                            "One or more input bands are missing or \n the metadata file belongs to another image ({})."
                        ).format(img_name[3].replace("_B01", ""))
                    )

    if check_odir == 1:
        for elem in root[0].findall("Product_Info"):
            datatake = elem.find("Datatake")
            # Geometrical conditions = sensor
            sensor = datatake.find("SPACECRAFT_NAME")
            # Acquisition date and time
            time_str = elem.find("GENERATION_TIME")
            # Date and time conversion
            time_py = datetime.strptime(time_str.text, "%Y-%m-%dT%H:%M:%S.%fZ")
            # Compute decimal hour
            dec_hour = (
                float(time_py.hour)
                + float(time_py.minute) / 60
                + float(time_py.second) / 3600
            )
            # Read input bands from metadata
            product = elem.find("Product_Organisation")
            g_list = product.find("Granule_List")
            granule = g_list.find("Granules")
            images = granule.find("IMAGE_ID")
            # Check if input exist and if the mtd file corresponds with the input image
            for img in root.iter("IMAGE_ID"):
                b = img.text.split("_")
                if gscript.find_file(img.text, element="cell", mapset=mapset)["file"]:
                    if b[10] == "B01":
                        bands["costal"] = img.text
                    elif b[10] == "B02":
                        bands["blue"] = img.text
                    elif b[10] == "B03":
                        bands["green"] = img.text
                    elif b[10] == "B04":
                        bands["red"] = img.text
                    elif b[10] == "B05":
                        bands["re5"] = img.text
                    elif b[10] == "B06":
                        bands["re6"] = img.text
                    elif b[10] == "B07":
                        bands["re7"] = img.text
                    elif b[10] == "B08":
                        bands["nir"] = img.text
                    elif b[10] == "B8A":
                        bands["nir8a"] = img.text
                    elif b[10] == "B09":
                        bands["vapour"] = img.text
                    elif b[10] == "B10":
                        bands["cirrus"] = img.text
                    elif b[10] == "B11":
                        bands["swir11"] = img.text
                    elif b[10] == "B12":
                        bands["swir12"] = img.text
                else:
                    gscript.fatal(
                        (
                            "One or more input bands are missing or \n the metadata file belongs to another image ({})."
                        ).format(images.text.replace("_B09", ""))
                    )

    # Check if input exist
    for key, value in bands.items():
        if (
            not gscript.find_file(value, element="cell", mapset=mapset)["file"]
            and not gscript.find_file(value, element="cell")["file"]
        ):
            gscript.fatal(("Raster map <{}> not found.").format(value))

    # Check if output already exist
    for key, value in bands.items():
        if not os.getenv("GRASS_OVERWRITE"):
            if gscript.find_file(value + "_" + suffix, element="cell", mapset=mapset)[
                "file"
            ]:
                gscript.fatal(
                    ("Raster map {} already exists.").format(value + "_" + suffix)
                )

    # Check if output name for the text file has been specified
    if flags["t"]:
        if options["text_file"] == "":
            gscript.fatal(
                "Output name is required for the text file. Please specified it"
            )
        if not os.access(os.path.dirname(options["text_file"]), os.W_OK):
            gscript.fatal("Output directory for the text file is not writable")

    # Set temp region to image max extent
    gscript.use_temp_region()
    gscript.run_command("g.region", rast=bands.values(), flags="a")
    gscript.message(
        _(
            "--- The computational region has been temporarily set to image max extent ---"
        )
    )

    if flags["a"]:
        if vis != "":
            if options["aod_value"] != "" and aeronet_file != "":
                gscript.warning(_("--- Visibility map will be ignored ---"))
                gscript.fatal(
                    "Only one parameter must be provided, AOD value or AERONET file"
                )
            elif options["aod_value"] == "" and aeronet_file == "":
                gscript.warning(_("--- Visibility map will be ignored ---"))
                gscript.fatal(
                    "If -a flag is checked an AOD value or AERONET file must be provided"
                )
            elif options["aod_value"] != "":
                gscript.warning(_("--- Visibility map will be ignored ---"))
                check_value = 1
                aot550 = options["aod_value"]
            elif aeronet_file != "":
                gscript.warning(_("--- Visibility map will be ignored ---"))
        elif options["aod_value"] != "" and aeronet_file != "":
            gscript.fatal(
                "Only one parameter must be provided, AOD value or AERONET file"
            )
        elif options["aod_value"] != "":
            check_value = 1
            aot550 = options["aod_value"]
        elif aeronet_file != "":
            gscript.message(_("--- Computing AOD from input AERONET file ---"))
        elif options["aod_value"] == "" and aeronet_file == "":
            gscript.fatal(
                "If -a flag is checked an AOD value or AERONET file must be provided"
            )
    else:
        if vis != "":
            if options["aod_value"] != "" or aeronet_file != "":
                gscript.warning(_("--- AOD will be ignored ---"))
            check_file = 1
            stats_v = gscript.parse_command("r.univar", flags="g", map=vis)
            try:
                vis_mean = int(float(stats_v["mean"]))
                gscript.message(
                    "--- Computed visibility mean value: {} Km ---".format(vis_mean)
                )
            except:
                gscript.fatal(
                    "The input visibility maps is not valid. It could be out of the computational region."
                )
        elif vis == "" and (options["aod_value"] != "" or aeronet_file != ""):
            gscript.fatal("Check the -a flag to use AOD instead of visibility")
        else:
            gscript.fatal("No visibility map has been provided")

    # Retrieve longitude and latitude of the centre of the computational region
    c_region = gscript.parse_command("g.region", flags="bg")
    lon = float(c_region["ll_clon"])
    lat = float(c_region["ll_clat"])

    # Read and compute AOD from AERONET file
    if check_value == 0 and check_file == 0:
        i = 0
        cc = 0
        count = 0
        columns = []
        m_time = []
        dates_list = []
        t_columns = []
        i_col = []
        coll = []
        wl = []

        with open(aeronet_file, "r") as aeronet:
            for row in aeronet:
                count += 1
                if count == 4:
                    columns = row.split(",")
        # Search for the closest date and time to the acquisition one
        count = 0
        with open(aeronet_file, "r") as aeronet:
            for row in aeronet:
                count += 1
                if count >= 5:
                    columns = row.split(",")
                    m_time.append(columns[0] + " " + columns[1])

        dates = [datetime.strptime(row, "%d:%m:%Y %H:%M:%S") for row in m_time]
        dates_list.append(dates)
        format_bd = time_py.strftime("%d/%m/%Y %H:%M:%S")
        base_date = str(format_bd)
        b_d = datetime.strptime(base_date, "%d/%m/%Y %H:%M:%S")

        for line in dates_list:
            closest = min(line, key=lambda x: abs(x - b_d))
            timedelta = abs(closest - b_d)
        # Search for the closest wavelengths (upper and lower) to 550
        count = 0
        with open(aeronet_file, "r") as aeronet:
            for row in aeronet:
                count += 1
                if count == 4:
                    t_columns = row.split(",")
                    for i, col in enumerate(t_columns):
                        if "AOT_" in col:
                            i_col.append(i)
                            coll.append(col)
        for line in coll:
            l = line.split("_")
            wl.append(int(l[1]))

        aot_req = 550
        upper = min([i for i in wl if i >= aot_req], key=lambda x: abs(x - aot_req))
        lower = min([i for i in wl if i < aot_req], key=lambda x: abs(x - aot_req))

        count = 0
        with open(aeronet_file, "r") as aeronet:
            for row in aeronet:
                count += 1
                if count == dates.index(closest) + 5:
                    t_columns = row.split(",")
                    count2 = 0
                    check_up = 0
                    check_lo = 0
                    while count2 < len(i_col) and check_up < 1:
                        # Search for the not null value for the upper wavelength
                        if t_columns[wl.index(upper) + i_col[0]] == "N/A":
                            aot_req_tmp = upper
                            upper = min(
                                [i for i in wl if i > aot_req_tmp],
                                key=lambda x: abs(x - aot_req_tmp),
                            )
                        else:
                            wl_upper = float(upper)
                            aot_upper = float(t_columns[wl.index(upper) + i_col[0]])
                            check_up = 1
                        count2 += 1
                    count2 = 0
                    while count2 < len(i_col) and check_lo < 1:
                        # Search for the not null value for the lower wavelength
                        if t_columns[wl.index(lower) + i_col[0]] == "N/A":
                            aot_req_tmp = lower
                            lower = min(
                                [i for i in wl if i < aot_req_tmp],
                                key=lambda x: abs(x - aot_req_tmp),
                            )
                        else:
                            wl_lower = float(lower)
                            aot_lower = float(t_columns[wl.index(lower) + i_col[0]])
                            check_lo = 1
                        count2 += 1
        # Compute AOD at 550 nm
        alpha = math.log(aot_lower / aot_upper) / math.log(wl_upper / wl_lower)
        aot550 = math.exp(math.log(aot_lower) - math.log(550.0 / wl_lower) * alpha)
        gscript.message("--- Computed AOD at 550 nm: {} ---".format(aot550))

    # Compute mean target elevation in km
    stats_d = gscript.parse_command("r.univar", flags="g", map=dem)
    try:
        mean = float(stats_d["mean"])
        conv_fac = -0.001
        dem_mean = mean * conv_fac
        gscript.message(
            "--- Computed mean target elevation above sea level: {:.3f} m ---".format(
                mean
            )
        )
    except:
        gscript.fatal(
            "The input elevation maps is not valid. It could be out of the computational region."
        )

    # Start compiling the control file
    for key, bb in bands.items():
        gscript.message(_("--- Compiling the control file.. ---"))
        text = open(tmp_file, "w")
        # Geometrical conditions
        if sensor.text == "Sentinel-2A":
            text.write(str(25) + "\n")
        elif sensor.text == "Sentinel-2B":
            text.write(str(26) + "\n")
        else:
            gscript.fatal("The input image does not seem to be a Sentinel image")
        text.write(
            "{} {} {:.2f} {:.3f} {:.3f}".format(
                time_py.month, time_py.day, dec_hour, lon, lat
            )
            + "\n"
        )
        # Atmospheric model
        # See also: https:/harrisgeospatial.com/docs/FLAASH.html
        # for a more fine tuned way of selecting the atmospheric model
        winter = [1, 2, 3, 4, 10, 11, 12]
        summer = [5, 6, 7, 8, 9]
        if atmo_mod == "Automatic":
            if lat > -15.00 and lat <= 15.00:  # Tropical
                text.write("1" + "\n")
            elif lat > 15.00 and lat <= 45.00:
                if time_py.month in winter:  # Midlatitude winter
                    text.write("3" + "\n")
                else:  # Midlatitude summer
                    text.write("2" + "\n")
            elif lat < -15.00 and lat >= -45.00:
                if time_py.month in winter:  # Midlatitude summer
                    text.write("2" + "\n")
                else:  # Midlatitude winter
                    text.write("3" + "\n")
            elif lat > 45.00:  # and lat <= 60.00:
                if time_py.month in winter:  # Subarctic winter
                    text.write("5" + "\n")
                else:  # Subartic summer
                    text.write("4" + "\n")
            elif lat < -45.00:  # and lat >= -60.00:
                if time_py.month in winter:  # Subarctic summer
                    text.write("4" + "\n")
                else:  # Subartic winter
                    text.write("5" + "\n")
            else:
                gscript.fatal("Latitude {} is out of range".format(lat))
        elif atmo_mod == "No gaseous absorption":
            text.write("0" + "\n")  # No gas abs model
        elif atmo_mod == "Tropical":
            text.write("1" + "\n")  # Tropical model
        elif atmo_mod == "Midlatitude summer":
            text.write("2" + "\n")  # Mid sum model
        elif atmo_mod == "Midlatitude winter":
            text.write("3" + "\n")  # Mid win model
        elif atmo_mod == "Subarctic summer":
            text.write("4" + "\n")  # Sub sum model
        elif atmo_mod == "Subarctic winter":
            text.write("5" + "\n")  # Sub win model
        elif atmo_mod == "Us standard 62":
            text.write("6" + "\n")  # Us 62 model
        # Aerosol model
        if aerosol_mod == "No aerosols":
            text.write("0" + "\n")  # No aerosol model
        elif aerosol_mod == "Continental model":
            text.write("1" + "\n")  # Continental aerosol model
        elif aerosol_mod == "Maritime model":
            text.write("2" + "\n")  # Maritimw aerosol model
        elif aerosol_mod == "Urban model":
            text.write("3" + "\n")  # Urban aerosol model
        elif aerosol_mod == "Shettle model for background desert aerosol":
            text.write("4" + "\n")  # Shettle aerosol model
        elif aerosol_mod == "Biomass burning":
            text.write("5" + "\n")  # Biomass aerosol model
        elif aerosol_mod == "Stratospheric model":
            text.write("6" + "\n")  # Stratospheric aerosol model
        # Visibility and/or AOD
        if not flags["a"] and vis != "":
            text.write("{}".format(vis_mean) + "\n")
        elif flags["a"] and vis != "":
            if aot550 != 0:
                text.write("0" + "\n")  # Visibility
                text.write("{}".format(aot550) + "\n")
            elif aot550 == 0:
                text.write("-1" + "\n")  # Visibility
                text.write("{}".format(aot550) + "\n")
        elif vis == "" and aot550 != 0:
            text.write("0" + "\n")  # Visibility
            text.write("{}".format(aot550) + "\n")
        elif vis == "" and aot550 == 0:
            text.write("-1" + "\n")  # Visibility
            text.write("{}".format(aot550) + "\n")
        else:
            gscript.fatal("Unable to retrieve visibility or AOD value, check the input")
        text.write("{:.3f}".format(dem_mean) + "\n")  # Mean elevation
        text.write("-1000" + "\n")  # Sensor height
        # Band number
        b = bb.split("_")
        if check_ndir == 1:
            band_n = b[2]
        else:
            band_n = b[10]
        if band_n == "B01" and sensor.text == "Sentinel-2A":
            gscript.message(band_n)
            text.write("166")
        elif band_n == "B02" and sensor.text == "Sentinel-2A":
            gscript.message(band_n)
            text.write("167")
        elif band_n == "B03" and sensor.text == "Sentinel-2A":
            gscript.message(band_n)
            text.write("168")
        elif band_n == "B04" and sensor.text == "Sentinel-2A":
            gscript.message(band_n)
            text.write("169")
        elif band_n == "B05" and sensor.text == "Sentinel-2A":
            gscript.message(band_n)
            text.write("170")
        elif band_n == "B06" and sensor.text == "Sentinel-2A":
            gscript.message(band_n)
            text.write("171")
        elif band_n == "B07" and sensor.text == "Sentinel-2A":
            gscript.message(band_n)
            text.write("172")
        elif band_n == "B08" and sensor.text == "Sentinel-2A":
            gscript.message(band_n)
            text.write("173")
        elif band_n == "B8A" and sensor.text == "Sentinel-2A":
            gscript.message(band_n)
            text.write("174")
        elif band_n == "B09" and sensor.text == "Sentinel-2A":
            gscript.message(band_n)
            text.write("175")
        elif band_n == "B10" and sensor.text == "Sentinel-2A":
            gscript.message(band_n)
            text.write("176")
        elif band_n == "B11" and sensor.text == "Sentinel-2A":
            gscript.message(band_n)
            text.write("177")
        elif band_n == "B12" and sensor.text == "Sentinel-2A":
            gscript.message(band_n)
            text.write("178")
        elif band_n == "B01" and sensor.text == "Sentinel-2B":
            gscript.message(band_n)
            text.write("179")
        elif band_n == "B02" and sensor.text == "Sentinel-2B":
            gscript.message(band_n)
            text.write("180")
        elif band_n == "B03" and sensor.text == "Sentinel-2B":
            gscript.message(band_n)
            text.write("181")
        elif band_n == "B04" and sensor.text == "Sentinel-2B":
            gscript.message(band_n)
            text.write("182")
        elif band_n == "B05" and sensor.text == "Sentinel-2B":
            gscript.message(band_n)
            text.write("183")
        elif band_n == "B06" and sensor.text == "Sentinel-2B":
            gscript.message(band_n)
            text.write("184")
        elif band_n == "B07" and sensor.text == "Sentinel-2B":
            gscript.message(band_n)
            text.write("185")
        elif band_n == "B08" and sensor.text == "Sentinel-2B":
            gscript.message(band_n)
            text.write("186")
        elif band_n == "B8A" and sensor.text == "Sentinel-2B":
            gscript.message(band_n)
            text.write("187")
        elif band_n == "B09" and sensor.text == "Sentinel-2B":
            gscript.message(band_n)
            text.write("188")
        elif band_n == "B10" and sensor.text == "Sentinel-2B":
            gscript.message(band_n)
            text.write("189")
        elif band_n == "B11" and sensor.text == "Sentinel-2B":
            gscript.message(band_n)
            text.write("190")
        elif band_n == "B12" and sensor.text == "Sentinel-2B":
            gscript.message(band_n)
            text.write("191")
        else:
            gscript.fatal("Bands do not seem to belong to a Sentinel image")
        text.close()

        if flags["a"]:
            gscript.run_command(
                "i.atcorr",
                input=bb,
                parameters=tmp_file,
                output="{}_{}".format(bb, suffix),
                range="1,10000",
                elevation=dem,
                rescale=rescale,
                flags="r",
            )
            cor_bands[key] = "{}_{}".format(bb, suffix)
        else:
            gscript.run_command(
                "i.atcorr",
                input=bb,
                parameters=tmp_file,
                output="{}_{}".format(bb, suffix),
                range="1,10000",
                elevation=dem,
                visibility=vis,
                rescale=rescale,
                flags="r",
            )
            cor_bands[key] = "{}_{}".format(bb, suffix)

    gscript.message(_("--- All bands have been processed ---"))

    if flags["t"]:
        prefix = options["topo_prefix"] + "." if options["topo_prefix"] else ""
        with open(txt_file, "w") as txt:
            for key, value in cor_bands.items():
                if str(key) in [
                    "blue",
                    "green",
                    "red",
                    "nir",
                    "nir8a",
                    "swir11",
                    "swir12",
                ]:
                    txt.write(str(key) + "=" + prefix + str(value) + "\n")
            mtd_tl_xml = glob.glob(os.path.join(input_dir, "GRANULE/*/MTD_TL.xml"))[0]
            txt.write("MTD_TL.xml=" + mtd_tl_xml + "\n")

    for key, cb in cor_bands.items():
        gscript.message(cb)
        gscript.run_command("r.colors", map=cb, color="grey", flags="e", quiet=True)

    if flags["c"]:
        gscript.message(_("--- Computes topographic correction of reflectance ---"))
        dat = bb.split("_")[1]
        # TODO understand better the timezone
        sunmask = gscript.parse_command(
            "r.sunmask",
            flags="sg",
            elevation=dem,
            year=dat[0:4],
            month=int(dat[4:6]),
            day=int(dat[6:8]),
            hour=int(dat[9:11]),
            minute=int(dat[11:13]),
            second=int(dat[13:15]),
            timezone=0,
        )
        z = 90.0 - float(sunmask["sunangleabovehorizon"])
        if not topo_method:
            topo_method = "c-factor"
        illu = "{}_{}_{}".format(bb, "illu", processid)
        gscript.run_command(
            "i.topo.corr",
            flags="i",
            basemap=dem,
            zenit=z,
            azimuth=sunmask["sunazimuth"],
            output=illu,
        )
        tcor = []
        for ma in cor_bands.values():
            out = "{}_double_{}".format(ma, processid)
            tcor.append(out)
            gscript.raster.mapcalc("{}=double({})".format(out, ma))

        gscript.run_command(
            "i.topo.corr",
            basemap=illu,
            zenith=z,
            input=",".join(tcor),
            method=topo_method,
            output=options["topo_prefix"],
        )
        for ma in tcor:
            inp = "{}.{}".format(options["topo_prefix"], ma)
            gscript.run_command(
                "g.rename",
                quiet=True,
                raster="{},{}".format(
                    inp, inp.replace("_double_{}".format(processid), "")
                ),
            )
        gscript.run_command("g.remove", flags="f", type="raster", name=illu, quiet=True)
        gscript.run_command(
            "g.remove", flags="f", type="raster", name=",".join(tcor), quiet=True
        )

    gscript.del_temp_region()
    gscript.message(
        _("--- The computational region has been reset to the previous one ---")
    )


if __name__ == "__main__":
    options, flags = gscript.parser()
    main()
