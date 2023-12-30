#!/usr/bin/env python


"""
 MODULE:       i.landsat8.swlst

 AUTHOR(S):    Nikos Alexandris <nik@nikosalexandris.net>
               Created on Wed Mar 18 10:00:53 2015
               First all-through execution: Tue May 12 21:50:42 EEST 2015

 PURPOSE:      A robust and practical Slit-Window (SW) algorithm estimating
               land surface temperature, from the Thermal Infra-Red Sensor
               (TIRS) aboard Landsat 8 with an accuracy of better than 1.0 K.

               The components of the algorithm estimating LST values are
               at-satellite brightness temperature (BT); land surface
               emissivity (LSE); and the coefficients of the main Split-Window
               equation (SWC) linked to the Column Water Vapor.

               The module's input parameters include:

               - the brightness temperatures (Ti and Tj) of the two adjacent
                 TIRS channels,

               - FROM-GLC land cover products and an emissivity look-up table,
                 which are a fraction of the FVC that can be estimated from the
                 red and near-infrared reflectance of the Operational Land
                 Imager (OLI).

               The algorithm's flowchart (Figure 3 in the paper [0]) is:

               +--------+   +--------------------------+
               |Landsat8+--->Cloud screen & calibration|
               +--------+   +---+--------+-------------+
                                |        |
                                |        |
                              +-v-+   +--v-+
                              |OLI|   |TIRS|
                              +-+-+   +--+-+
                                |        |
                                |        |
                             +--v-+   +--v-------------------+  +-------------+
                             |NDVI|   |Brightness temperature+-->MSWCVM method|
              +----------+   +--+-+   +--+-------------------+  +----------+--+
              |Land cover|      |        |                               |
              +----------+      |        |                               |
                      |       +-v-+   +--v-------------------+    +------v--+
                      |       |FVC|   |Split Window Algorithm|    |ColWatVap|
+---------------------v--+    +-+-+   +-------------------+--+    +------+--+
|Emissivity look|up table|      |                         |              |
+---------------------+--+      |                         |              |
                      |      +--v--------------------+    |    +---------v--+
                      +------>Pixel emissivity ei, ej+--> | <--+Coefficients|
                             +-----------------------+    |    +------------+
                                                          |
                                                          |
                                          +---------------v--+
                                          |LST and emissivity|
                                          +------------------+

               Sources:

               [0] Du, Chen; Ren, Huazhong; Qin, Qiming; Meng, Jinjie;
               Zhao, Shaohua. 2015. "A Practical Split-Window Algorithm
               for Estimating Land Surface Temperature from Landsat 8 Data."
               Remote Sens. 7, no. 1: 647-665.
               <http://www.mdpi.com/2072-4292/7/1/647/htm#sthash.ba1pt9hj.dpuf>

               [1] [Look below for the publised paper!] Huazhong Ren, Chen Du,
               Qiming Qin, Rongyuan Liu, Jinjie Meng, and Jing Li. "Atmospheric
               Water Vapor Retrieval from Landsat 8 and Its Validation."
               3045–3048. IEEE, 2014.

               [2] Ren, H., Du, C., Liu, R., Qin, Q., Yan, G., Li, Z. L., &
               Meng, J. (2015). Atmospheric water vapor retrieval from Landsat
               8 thermal infrared images. Journal of Geophysical Research:
               Atmospheres, 120(5), 1723-1738.

 COPYRIGHT:    (C) 2015 by the GRASS Development Team

               This program is free software under the GNU General Public
               License (>=v2). Read the file COPYING that comes with GRASS
               for details.
"""

# %Module
# %  description: Practical split-window algorithm estimating Land Surface Temperature from Landsat 8 OLI/TIRS imagery (Du, Chen; Ren, Huazhong; Qin, Qiming; Meng, Jinjie; Zhao, Shaohua. 2015)
# %  keywords: imagery
# %  keywords: split window
# %  keywords: column water vapor
# %  keywords: land surface temperature
# %  keywords: lst
# %  keywords: landsat8
# %End

# %flag
# %  key: i
# %  description: Print out model equations, citation
# %end

# %flag
# %  key: e
# %  description: Match computational region to extent of thermal bands
# %end

# %flag
# %  key: r
# %  description: Round LST output and keep two digits
# %end

# %flag
# % key: t
# % description: Time-stamp the output LST (and optional CWV) map
# %end

# %flag
# % key: c
# % description: Convert LST output to celsius degrees, apply color table
# %end

# %flag
# % key: n
# % description: Set zero digital numbers in b10, b11 to NULL | ToDo: Perform in copy of input input maps!
# %end

# %option G_OPT_F_INPUT
# % key: mtl
# % key_desc: filename
# % description: Landsat8 metadata file (MTL)
# % required: no
# %end

# %option G_OPT_R_BASENAME_INPUT
# % key: prefix
# % key_desc: basename
# % type: string
# % label: OLI/TIRS band names prefix
# % description: Prefix of Landsat8 OLI/TIRS band names
# % required: no
# %end

##%rules
##% collective: prefix, mtl
##%end

# %option G_OPT_R_INPUT
# % key: b10
# % key_desc: name
# % description: TIRS 10 (10.60 - 11.19 microns)
# % required : no
# %end

# %rules
# % requires_all: b10, mtl
# %end

# %option G_OPT_R_INPUT
# % key: b11
# % key_desc: name
# % description: TIRS 11 (11.50 - 12.51 microns)
# % required : no
# %end

# %rules
# % requires_all: b11, mtl
# %end

# %option G_OPT_R_BASENAME_INPUT
# % key: prefix_bt
# % key_desc: basename
# % type: string
# % label: Prefix for output at-satellite brightness temperature maps (K)
# % description: Prefix for brightness temperature maps (K)
# % required: no
# %end

# %option G_OPT_R_INPUT
# % key: t10
# % key_desc: name
# % description: Brightness temperature (K) from band 10 | Overrides 'b10'
# % required : no
# %end

# %option G_OPT_R_INPUT
# % key: t11
# % key_desc: name
# % description: Brightness temperature (K) from band 11 | Overrides 'b11'
# % required : no
# %end

# %rules
# % requires: b10, b11, t11
# %end

# %rules
# % requires: b11, b10, t10
# %end

# %rules
# % requires: t10, t11, b11
# %end

# %rules
# % requires: t11, t10, b10
# %end

# %rules
# % exclusive: b10, t10
# %end

# %rules
# % exclusive: b11, t11
# %end

# %option G_OPT_R_INPUT
# % key: qab
# % key_desc: name
# % description: Landsat 8 Quality Assessment band
# % required : no
# %end

# %option
# % key: qapixel
# % key_desc: pixelvalue
# % description: Quality assessment pixel value for which to build a mask | Source: <http://landsat.usgs.gov/L8QualityAssessmentBand.php>.
# % answer: 61440
# % required: no
# % multiple: yes
# %end

# %rules
# % excludes: prefix, b10, b11, qab
# %end

# %option G_OPT_R_INPUT
# % key: clouds
# % key_desc: name
# % description: A raster map applied as an inverted MASK | Overrides 'qab'
# % required : no
# %end

# %rules
# % exclusive: qab, clouds
# %end

# %option G_OPT_R_INPUT
# % key: emissivity
# % key_desc: name
# % description: Land surface emissivity map | Expert use, overrides retrieving average emissivity from landcover
# % required : no
# %end

# %option G_OPT_R_OUTPUT
# % key: emissivity_out
# % key_desc: name
# % description: Name for output emissivity map | For re-use as "emissivity=" input in subsequent trials with different spatial window sizes
# % required: no
# %end

# %option G_OPT_R_INPUT
# % key: delta_emissivity
# % key_desc: name
# % description: Emissivity difference map for Landsat8 TIRS channels 10 and 11 | Expert use, overrides retrieving delta emissivity from landcover
# % required : no
# %end

# %option G_OPT_R_OUTPUT
# % key: delta_emissivity_out
# % key_desc: name
# % description: Name for output delta emissivity map | For re-use as "delta_emissivity=" in subsequent trials with different spatial window sizes
# % required: no
# %end

# %option G_OPT_R_INPUT
# % key: landcover
# % key_desc: name
# % description: FROM-GLC products covering the Landsat8 scene under processing. Source <http://data.ess.tsinghua.edu.cn/>.
# % required : no
# %end

# %option
# % key: landcover_class
# % key_desc: string
# % description: Retrieve average emissivities only for a single land cover class (case sensitive) | Expert use
# % options: Cropland, Forest, Grasslands, Shrublands, Wetlands, Waterbodies, Tundra, Impervious, Barren_Land, Snow_and_ice, Random
# % required : no
# %end

# %rules
# % required: landcover, landcover_class
# % exclusive: landcover, landcover_class
# %end

# %option G_OPT_R_OUTPUT
# % key: lst
# % key_desc: name
# % description: Name for output Land Surface Temperature map
# % required: yes
# % answer: lst
# %end

# %option
# % key: window
# % key_desc: integer
# % description: Odd number n sizing an n^2 spatial window for column water vapor retrieval | Increase to reduce spatial discontinuation in the final LST
# % answer: 7
# % required: yes
# %end

# %option G_OPT_R_OUTPUT
# % key: cwv
# % key_desc: name
# % description: Name for output Column Water Vapor map | Optional
# % required: no
# %end

# required librairies
import os
import sys

sys.path.insert(
    1, os.path.join(os.path.dirname(sys.path[0]), "etc", "i.landsat8.swlst")
)

import atexit
import grass.script as grass

# from grass.exceptions import CalledModuleError
from grass.pygrass.modules.shortcuts import general as g
from grass.pygrass.modules.shortcuts import raster as r

# from grass.pygrass.raster.abstract import Info
import functools

from column_water_vapor import estimate_cwv_big_expression
from split_window_lst import *
from landsat8_mtl import Landsat8_MTL
from helpers import cleanup
from helpers import tmp_map_name
from helpers import run
from helpers import save_map
from helpers import extract_number_from_string
from helpers import add_timestamp
from helpers import mask_clouds
from randomness import random_digital_numbers
from randomness import random_column_water_vapor_subrange
from randomness import random_column_water_vapor_value
from constants import DUMMY_MAPCALC_STRING_RADIANCE
from constants import DUMMY_MAPCALC_STRING_DN
from constants import DUMMY_MAPCALC_STRING_T10
from constants import DUMMY_MAPCALC_STRING_T11
from constants import DUMMY_MAPCALC_STRING_AVG_LSE
from constants import DUMMY_MAPCALC_STRING_DELTA_LSE
from constants import DUMMY_MAPCALC_STRING_FROM_GLC
from constants import DUMMY_MAPCALC_STRING_CWV
from constants import DUMMY_Ti_MEAN
from constants import DUMMY_Tj_MEAN
from constants import DUMMY_Rji
from constants import EQUATION as equation
from column_water_vapor import Column_Water_Vapor
from emissivity import determine_average_emissivity
from emissivity import determine_delta_emissivity
from dummy_mapcalc_strings import replace_dummies
from radiance import digital_numbers_to_radiance
from radiance import radiance_to_brightness_temperature
from temperature import tirs_to_at_satellite_temperature
from temperature import estimate_lst

if "GISBASE" not in os.environ:
    print("You must be in GRASS GIS to run this program.")
    sys.exit(1)


def main():
    # Temporary filenames
    tmp_avg_lse = tmp_map_name("avg_lse")
    tmp_delta_lse = tmp_map_name("delta_lse")
    tmp_cwv = tmp_map_name("cwv")
    # tmp_lst = tmp_map_name('lst')

    # user input
    mtl_file = options["mtl"]

    if not options["prefix"]:
        b10 = options["b10"]
        b11 = options["b11"]
        t10 = options["t10"]
        t11 = options["t11"]

        if not options["clouds"]:
            qab = options["qab"]
            cloud_map = False

        else:
            qab = False
            cloud_map = options["clouds"]

    elif options["prefix"]:
        prefix = options["prefix"]
        b10 = prefix + "10"
        b11 = prefix + "11"

        if not options["clouds"]:
            qab = prefix + "QA"
            cloud_map = False

        else:
            cloud_map = options["clouds"]
            qab = False

    qapixel = options["qapixel"]
    lst_output = options["lst"]

    # save Brightness Temperature maps?
    if options["prefix_bt"]:
        brightness_temperature_prefix = options["prefix_bt"]
    else:
        brightness_temperature_prefix = None

    cwv_window_size = int(options["window"])
    assertion_for_cwv_window_size_msg = (
        "A spatial window of size 5^2 or less is not "
        "recommended. Please select a larger window. "
        "Refer to the manual's notes for details."
    )
    assert cwv_window_size >= 7, assertion_for_cwv_window_size_msg
    cwv_output = options["cwv"]

    # optional maps
    average_emissivity_map = options["emissivity"]
    delta_emissivity_map = options["delta_emissivity"]

    # output for in-between maps?
    emissivity_output = options["emissivity_out"]
    delta_emissivity_output = options["delta_emissivity_out"]
    landcover_map = options["landcover"]
    landcover_class = options["landcover_class"]

    # flags
    info = flags["i"]
    scene_extent = flags["e"]
    timestamping = flags["t"]
    null = flags["n"]
    rounding = flags["r"]
    celsius = flags["c"]

    # ToDo:
    # shell = flags['g']

    #
    # Pre-production actions
    #

    # Set Region
    if scene_extent:
        grass.use_temp_region()  # safely modify the region
        msg = "\n|! Matching region extent to map {name}"

        # ToDo: check if extent-B10 == extent-B11? Unnecessary?
        # Improve below!

        if b10:
            run("g.region", rast=b10, align=b10)
            msg = msg.format(name=b10)

        elif t10:
            run("g.region", rast=t10, align=t10)
            msg = msg.format(name=t10)

        g.message(msg)

    elif not scene_extent:
        grass.warning(_("Operating on current region"))

    #
    # 1. Mask clouds
    #

    if cloud_map:
        # user-fed cloud map?
        msg = "\n|i Using {cmap} as a MASK".format(cmap=cloud_map)
        g.message(msg)
        r.mask(raster=cloud_map, flags="i", overwrite=True)

    else:
        # using the quality assessment band and a "QA" pixel value
        mask_clouds(qab, qapixel)

    #
    # 2. TIRS > Brightness Temperatures
    #

    if mtl_file:

        # if MTL and b10 given, use it to compute at-satellite temperature t10
        if b10:
            # convert DNs to at-satellite temperatures
            t10 = tirs_to_at_satellite_temperature(
                b10,
                mtl_file,
                brightness_temperature_prefix,
                null,
                quiet=info,
            )

        # likewise for b11 -> t11
        if b11:
            # convert DNs to at-satellite temperatures
            t11 = tirs_to_at_satellite_temperature(
                b11,
                mtl_file,
                brightness_temperature_prefix,
                null,
                quiet=info,
            )

    #
    # Initialise a SplitWindowLST object
    #

    split_window_lst = SplitWindowLST(landcover_class)
    citation_lst = split_window_lst.citation

    #
    # 3. Land Surface Emissivities
    #

    # use given fixed class?
    if landcover_class:

        if split_window_lst.landcover_class is False:
            # replace with meaningful error
            grass.warning(
                "Unknown land cover class string! Note, this string "
                "input option is case sensitive."
            )

        if landcover_class == "Random":
            msg = (
                "\n|! Random emissivity class selected > "
                + split_window_lst.landcover_class
                + " "
            )

        if landcover_class == "Barren_Land":
            msg = (
                "\n|! For barren land, the last quadratic term of the Split-Window algorithm will be set to 0"
                + split_window_lst.landcover_class
                + " "
            )

        else:
            msg = "\n|! Retrieving average emissivities *only* for {eclass} "

        if info:
            msg += "| Average emissivities (channels 10, 11): "
            msg += (
                str(split_window_lst.emissivity_t10)
                + ", "
                + str(split_window_lst.emissivity_t11)
            )

        msg = msg.format(eclass=split_window_lst.landcover_class)
        g.message(msg)

    # use the FROM-GLC map
    elif landcover_map:

        if average_emissivity_map:
            tmp_avg_lse = average_emissivity_map

        if not average_emissivity_map:
            determine_average_emissivity(
                tmp_avg_lse,
                emissivity_output,
                landcover_map,
                split_window_lst.average_lse_mapcalc,
                quiet=info,
            )
            if options["emissivity_out"]:
                tmp_avg_lse = options["emissivity_out"]

        if delta_emissivity_map:
            tmp_delta_lse = delta_emissivity_map

        if not delta_emissivity_map:
            determine_delta_emissivity(
                tmp_delta_lse,
                delta_emissivity_output,
                landcover_map,
                split_window_lst.delta_lse_mapcalc,
                quiet=info,
            )
            if options["delta_emissivity_out"]:
                tmp_delta_lse = options["delta_emissivity_out"]

    #
    # 4. Modified Split-Window Variance-Covariance Matrix > Column Water Vapor
    #

    if info:
        msg = "\n|i Spatial window of size {n} for Column Water Vapor estimation: "
        msg = msg.format(n=cwv_window_size)
        g.message(msg)

    cwv = Column_Water_Vapor(cwv_window_size, t10, t11)
    citation_cwv = cwv.citation
    estimate_cwv_big_expression(
        tmp_cwv,
        cwv_output,
        t10,
        t11,
        cwv._big_cwv_expression(),
    )
    if cwv_output:
        tmp_cwv = cwv_output

    #
    # 5. Estimate Land Surface Temperature
    #

    if info and landcover_class == "Random":
        msg = "\n|* Will pick a random emissivity class!"
        grass.verbose(msg)

    estimate_lst(
        lst_output,
        t10,
        t11,
        landcover_map,
        landcover_class,
        tmp_avg_lse,
        tmp_delta_lse,
        tmp_cwv,
        split_window_lst.sw_lst_mapcalc,
        rounding,
        celsius,
        quiet=info,
    )

    #
    # Post-production actions
    #

    # remove MASK
    r.mask(flags="r", verbose=True)

    # time-stamping
    if timestamping:
        add_timestamp(mtl_file, lst_output)

        if cwv_output:
            add_timestamp(mtl_file, cwv_output)

    # Apply color table
    if celsius:
        run("r.colors", map=lst_output, color="celsius")
    else:
        # color table for kelvin
        run("r.colors", map=lst_output, color="kelvin")

    # ToDo: helper function for r.support
    # strings for metadata
    history_lst = "\n" + citation_lst
    history_lst += "\n\n" + citation_cwv
    history_lst += "\n\nSplit-Window model: "
    history_lst += split_window_lst._equation  # :wsw_lst_mapcalc
    description_lst = "Land Surface Temperature derived from a split-window algorithm. "

    if celsius:
        title_lst = "Land Surface Temperature (C)"
        units_lst = "Celsius"

    else:
        title_lst = "Land Surface Temperature (K)"
        units_lst = "Kelvin"

    landsat8_metadata = Landsat8_MTL(mtl_file)
    source1_lst = landsat8_metadata.scene_id
    source2_lst = landsat8_metadata.origin

    # history entry
    run(
        "r.support",
        map=lst_output,
        title=title_lst,
        units=units_lst,
        description=description_lst,
        source1=source1_lst,
        source2=source2_lst,
        history=history_lst,
    )

    # (re)name the LST product
    # run("g.rename", rast=(tmp_lst, lst_output))

    # restore region
    if scene_extent:
        grass.del_temp_region()  # restoring previous region settings
        g.message("|! Original Region restored")

    # print citation
    if info:
        g.message("\nSource: " + citation_lst)


if __name__ == "__main__":
    options, flags = grass.parser()
    atexit.register(cleanup)
    sys.exit(main())
