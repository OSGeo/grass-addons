#!/usr/bin/env python
# -*- coding: utf-8 -*-

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

#%Module
#%  description: Practical split-window algorithm estimating Land Surface Temperature from Landsat 8 OLI/TIRS imagery (Du, Chen; Ren, Huazhong; Qin, Qiming; Meng, Jinjie; Zhao, Shaohua. 2015)
#%  keywords: imagery
#%  keywords: split window
#%  keywords: column water vapor
#%  keywords: land surface temperature
#%  keywords: lst
#%  keywords: landsat8
#%End

#%flag
#%  key: i
#%  description: Print out model equations, citation
#%end

#%flag
#%  key: e
#%  description: Match computational region to extent of thermal bands
#%end

#%flag
#% key: t
#% description: Time-stamping the output LST (and optional CWV) map
#%end

#%flag
#% key: c
#% description: Convert LST output to celsius degrees, apply color table
#%end

#%flag
#% key: n
#% description: Set zero digital numbers in b10, b11 to NULL | ToDo: Perform in copy of input input maps!
#%end

#%option G_OPT_F_INPUT
#% key: mtl
#% key_desc: filename
#% description: Landsat8 metadata file (MTL)
#% required: no
#%end

#%option G_OPT_R_BASENAME_INPUT
#% key: prefix
#% key_desc: basename
#% type: string
#% label: OLI/TIRS band names prefix
#% description: Prefix of Landsat8 OLI/TIRS band names
#% required: no
#%end

##%rules
##% collective: prefix, mtl
##%end

#%option G_OPT_R_INPUT
#% key: b10
#% key_desc: name
#% description: TIRS 10 (10.60 - 11.19 microns)
#% required : no
#%end

#%rules
#% requires_all: b10, mtl
#%end

#%option G_OPT_R_INPUT
#% key: b11
#% key_desc: name
#% description: TIRS 11 (11.50 - 12.51 microns)
#% required : no
#%end

#%rules
#% requires_all: b11, mtl
#%end

#%option G_OPT_R_BASENAME_INPUT
#% key: prefix_bt
#% key_desc: basename
#% type: string
#% label: Prefix for output at-satellite brightness temperature maps (K)
#% description: Prefix for brightness temperature maps (K)
#% required: no
#%end

#%option G_OPT_R_INPUT
#% key: t10
#% key_desc: name
#% description: Brightness temperature (K) from band 10 | Overrides 'b10'
#% required : no
#%end

#%option G_OPT_R_INPUT
#% key: t11
#% key_desc: name
#% description: Brightness temperature (K) from band 11 | Overrides 'b11'
#% required : no
#%end

#%rules
#% requires: b10, b11, t11
#%end

#%rules
#% requires: b11, b10, t10
#%end

#%rules
#% requires: t10, t11, b11
#%end

#%rules
#% requires: t11, t10, b10
#%end

#%rules
#% exclusive: b10, t10
#%end

#%rules
#% exclusive: b11, t11
#%end

#%option G_OPT_R_INPUT
#% key: qab
#% key_desc: name
#% description: Landsat 8 Quality Assessment band
#% required : no
#%end

#%option
#% key: qapixel
#% key_desc: pixelvalue
#% description: Quality assessment pixel value for which to build a mask | Source: <http://landsat.usgs.gov/L8QualityAssessmentBand.php>.
#% answer: 61440
#% required: no
#% multiple: yes
#%end

#%rules
#% excludes: prefix, b10, b11, qab
#%end

#%option G_OPT_R_INPUT
#% key: clouds
#% key_desc: name
#% description: A raster map applied as an inverted MASK | Overrides 'qab'
#% required : no
#%end

#%rules
#% exclusive: qab, clouds
#%end

#%option G_OPT_R_INPUT
#% key: emissivity
#% key_desc: name
#% description: Land surface emissivity map | Expert use, overrides retrieving average emissivity from landcover
#% required : no
#%end

#%option G_OPT_R_OUTPUT
#% key: emissivity_out
#% key_desc: name
#% description: Name for output emissivity map | For re-use as "emissivity=" input in subsequent trials with different spatial window sizes
#% required: no
#%end

#%option G_OPT_R_INPUT
#% key: delta_emissivity
#% key_desc: name
#% description: Emissivity difference map for Landsat8 TIRS channels 10 and 11 | Expert use, overrides retrieving delta emissivity from landcover
#% required : no
#%end

#%option G_OPT_R_OUTPUT
#% key: delta_emissivity_out
#% key_desc: name
#% description: Name for output delta emissivity map | For re-use as "delta_emissivity=" in subsequent trials with different spatial window sizes
#% required: no
#%end

#%option G_OPT_R_INPUT
#% key: landcover
#% key_desc: name
#% description: FROM-GLC products covering the Landsat8 scene under processing. Source <http://data.ess.tsinghua.edu.cn/>.
#% required : no
#%end

#%option
#% key: emissivity_class
#% key_desc: string
#% description: Retrieve average emissivities only for a single land cover class (case sensitive) | Expert use
#% options: Cropland, Forest, Grasslands, Shrublands, Wetlands, Waterbodies, Tundra, Impervious, Barren, Snow, Random
#% required : no
#%end

#%rules
#% required: landcover, emissivity_class
#% exclusive: landcover, emissivity_class
#%end

#%option G_OPT_R_OUTPUT
#% key: lst
#% key_desc: name
#% description: Name for output Land Surface Temperature map
#% required: yes
#% answer: lst
#%end

#%option
#% key: window
#% key_desc: integer
#% description: Odd number n sizing an n^2 spatial window for column water vapor retrieval | Increase to reduce spatial discontinuation in the final LST
#% answer: 7
#% required: yes
#%end

#%option G_OPT_R_OUTPUT
#% key: cwv
#% key_desc: name
#% description: Name for output Column Water Vapor map | Optional
#% required: no
#%end

# required librairies
import os
import sys
from functools import reduce
sys.path.insert(1, os.path.join(os.path.dirname(sys.path[0]),
                                'etc', 'i.landsat8.swlst'))

import atexit
import grass.script as grass
# from grass.exceptions import CalledModuleError
from grass.pygrass.modules.shortcuts import general as g
from grass.pygrass.modules.shortcuts import raster as r
# from grass.pygrass.raster.abstract import Info

from split_window_lst import *
from landsat8_mtl import Landsat8_MTL

if "GISBASE" not in os.environ:
    print("You must be in GRASS GIS to run this program.")
    sys.exit(1)

# globals
DUMMY_MAPCALC_STRING_RADIANCE = 'Radiance'
DUMMY_MAPCALC_STRING_DN = 'DigitalNumber'
DUMMY_MAPCALC_STRING_T10 = 'Input_T10'
DUMMY_MAPCALC_STRING_T11 = 'Input_T11'
DUMMY_MAPCALC_STRING_AVG_LSE = 'Input_AVG_LSE'
DUMMY_MAPCALC_STRING_DELTA_LSE = 'Input_DELTA_LSE'
DUMMY_MAPCALC_STRING_FROM_GLC = 'Input_FROMGLC'
DUMMY_MAPCALC_STRING_CWV = 'Input_CWV'
DUMMY_Ti_MEAN = 'Mean_Ti'
DUMMY_Tj_MEAN = 'Mean_Tj'
DUMMY_Rji = 'Ratio_ji'


# helper functions
def cleanup():
    """
    Clean up temporary maps
    """
    grass.run_command('g.remove', flags='f', type="rast",
                      pattern='tmp.{pid}*'.format(pid=os.getpid()), quiet=True)

    if grass.find_file(name='MASK', element='cell')['file']:
        r.mask(flags='r', verbose=True)


def tmp_map_name(name):
    """
    Return a temporary map name, for example:

    tmp_avg_lse = tmp + '.avg_lse'
    """
    temporary_file = grass.tempfile()
    tmp = "tmp." + grass.basename(temporary_file)  # use its basename
    return tmp + '.' + str(name)


def run(cmd, **kwargs):
    """
    Pass required arguments to grass commands (?)
    """
    grass.run_command(cmd, quiet=True, **kwargs)


def save_map(mapname):
    """
    Helper function to save some in-between maps, assisting in debugging
    """
    # run('r.info', map=mapname, flags='r')
    run('g.copy', raster=(mapname, 'DebuggingMap'))


def random_digital_numbers(count=2):
    """
    Return a user-requested amount of random Digital Number values for testing
    purposes ranging in 12-bit
    """
    digital_numbers = []

    for dn in range(0, count):
        digital_numbers.append(random.randint(1, 2**12))

    if count == 1:
        return digital_numbers[0]

    return digital_numbers


def random_column_water_vapor_subrange():
    """
    Helper function, while coding and testing, returning a random column water
    vapor key to assist in testing the module.
    """
    cwvkey = random.choice(COLUMN_WATER_VAPOUR.keys())
    # COLUMN_WATER_VAPOUR[cwvkey].subrange
    # COLUMN_WATER_VAPOUR[cwvkey].rmse
    return cwvkey


def random_column_water_vapor_value():
    """
    Helper function, while coding and testing, returning a random value for
    column water vapor.
    """
    return random.uniform(0.0, 6.3)


def extract_number_from_string(string):
    """
    Extract the (integer) number from a string. Meand to be used with band
    names. For example:

    print extract_number_from_string('B10')

    will return

    10
    """
    import re
    return str(re.findall(r"[+-]? *(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?",
               string)[-1])


def add_timestamp(mtl_filename, outname):
    """
    Retrieve metadata from MTL file.
    """
    import datetime
    metadata = Landsat8_MTL(mtl_filename)

    # required format is: day=integer month=string year=integer time=hh:mm:ss.dd
    acquisition_date = str(metadata.date_acquired)  ### FixMe ###
    acquisition_date = datetime.datetime.strptime(acquisition_date, '%Y-%m-%d').strftime('%d %b %Y')
    acquisition_time = str(metadata.scene_center_time)[0:8]
    date_time_string = acquisition_date + ' ' + acquisition_time

    #msg = "Date and time of acquisition: " + date_time_string
    #grass.verbose(msg)

    run('r.timestamp', map=outname, date=date_time_string)

    del(date_time_string)


def digital_numbers_to_radiance(outname, band, radiance_expression):
    """
    Convert Digital Number values to TOA Radiance. For details, see in Landsat8
    class.  Zero (0) DNs set to NULL here (not via the class' function).
    """
    if null:
        msg = "\n|i Setting zero (0) Digital Numbers in {band} to NULL"
        msg = msg.format(band=band)
        g.message(msg)
        run('r.null', map=band, setnull=0)

    msg = "\n|i Rescaling {band} digital numbers to spectral radiance "
    msg = msg.format(band=band)

    if info:
        msg += '| Expression: '
        msg += radiance_expression
    g.message(msg)
    radiance_expression = replace_dummies(radiance_expression,
                                          instring=DUMMY_MAPCALC_STRING_DN,
                                          outstring=band)
    radiance_equation = equation.format(result=outname,
                                        expression=radiance_expression)

    grass.mapcalc(radiance_equation, overwrite=True)

    if info:
        run('r.info', map=outname, flags='r')
        #run('r.univar', map=outname)

    del(radiance_expression)
    del(radiance_equation)


def radiance_to_brightness_temperature(outname, radiance, temperature_expression):
    """
    Convert Spectral Radiance to At-Satellite Brightness Temperature. For
    details see Landsat8 class.
    """
    temperature_expression = replace_dummies(temperature_expression,
                                             instring=DUMMY_MAPCALC_STRING_RADIANCE,
                                             outstring=radiance)

    msg = "\n|i Converting spectral radiance to at-Satellite Temperature "
    if info:
        msg += "| Expression: " + str(temperature_expression)
    g.message(msg)

    temperature_equation = equation.format(result=outname,
                                           expression=temperature_expression)

    grass.mapcalc(temperature_equation, overwrite=True)

    if info:
        run('r.info', map=outname, flags='r')
        #run('r.univar', map=outname)

    del(temperature_expression)
    del(temperature_equation)


def tirs_to_at_satellite_temperature(tirs_1x, mtl_file):
    """
    Helper function to convert TIRS bands 10 or 11 in to at-satellite
    temperatures.

    This function uses the pre-defined functions:

    - extract_number_from_string()
    - digital_numbers_to_radiance()
    - radiance_to_brightness_temperature()

    The inputs are:

    - a name for the input tirs band (10 or 11)
    - a Landsat8 MTL file

    The output is a temporary at-Satellite Temperature map.
    """
    # which band number and MTL file
    band_number = extract_number_from_string(tirs_1x)
    tmp_radiance = tmp_map_name('radiance') + '.' + band_number
    tmp_brightness_temperature = tmp_map_name('brightness_temperature') + '.' + \
        band_number
    landsat8 = Landsat8_MTL(mtl_file)

    # rescale DNs to spectral radiance
    radiance_expression = landsat8.toar_radiance(band_number)
    digital_numbers_to_radiance(tmp_radiance, tirs_1x, radiance_expression)

    # convert spectral radiance to at-satellite temperature
    temperature_expression = landsat8.radiance_to_temperature(band_number)
    radiance_to_brightness_temperature(tmp_brightness_temperature,
                                       tmp_radiance,
                                       temperature_expression)

    del(radiance_expression)
    del(temperature_expression)

    # save Brightness Temperature map?
    if brightness_temperature_prefix:
        bt_output = brightness_temperature_prefix + band_number
        run('g.rename', raster=(tmp_brightness_temperature, bt_output))
        tmp_brightness_temperature = bt_output
        del(bt_output)

    return tmp_brightness_temperature


def mask_clouds(qa_band, qa_pixel):
    """
    ToDo:

    - a better, independent mechanism for QA. --> see also Landsat8 class.
    - support for multiple qa_pixel values (eg. input as a list of values)

    Create and apply a cloud mask based on the Quality Assessment Band
    (BQA.) Source: <http://landsat.usgs.gov/L8QualityAssessmentBand.php

    See also:
    http://courses.neteler.org/processing-landsat8-data-in-grass-gis-7/#Applying_the_Landsat_8_Quality_Assessment_%28QA%29_Band
    """
    msg = ('\n|i Masking for pixel values <{qap}> '
           'in the Quality Assessment band.'.format(qap=qa_pixel))
    g.message(msg)

    #tmp_cloudmask = tmp_map_name('cloudmask')
    #qabits_expression = 'if({band} == {pixel}, 1, null())'.format(band=qa_band,
    #                                                              pixel=qa_pixel)

    #cloud_masking_equation = equation.format(result=tmp_cloudmask,
    #                                         expression=qabits_expression)
    #grass.mapcalc(cloud_masking_equation)

    r.mask(raster=qa_band, maskcats=qa_pixel, flags='i', overwrite=True)

    # save for debuging
    #save_map(tmp_cloudmask)

    #del(qabits_expression)
    #del(cloud_masking_equation)


def replace_dummies(string, *args, **kwargs):
    """
    Replace DUMMY_MAPCALC_STRINGS (see SplitWindowLST class for it)
    with input maps ti, tj (here: t10, t11).

    - in_ti and in_tj are the "input" strings, for example:
    in_ti = 'Input_T10'  and  in_tj = 'Input_T11'

    - out_ti and out_tj are the output strings which correspond to map
    names, user-fed or in-between temporary maps, for example:
    out_ti = t10  and  out_tj = t11

    or

    out_ti = tmp_ti_mean  and  out_tj = tmp_ti_mean

    (Idea sourced from: <http://stackoverflow.com/a/9479972/1172302>)
    """
    inout = set(['instring', 'outstring'])
    # if inout.issubset(set(kwargs)):  # alternative
    if inout == set(kwargs):
        instring = kwargs.get('instring', 'None')
        outstring = kwargs.get('outstring', 'None')

        # end comma important!
        replacements = (str(instring), str(outstring)),

    in_tij_out = set(['in_ti', 'out_ti', 'in_tj', 'out_tj'])

    if in_tij_out == set(kwargs):
        in_ti = kwargs.get('in_ti', 'None')
        out_ti = kwargs.get('out_ti', 'None')
        in_tj = kwargs.get('in_tj', 'None')
        out_tj = kwargs.get('out_tj', 'None')

        replacements = (in_ti, str(out_ti)), (in_tj, str(out_tj))

    in_tijm_out = set(['in_ti', 'out_ti', 'in_tj', 'out_tj',
                       'in_tim', 'out_tim', 'in_tjm', 'out_tjm'])

    if in_tijm_out == set(kwargs):
        in_ti = kwargs.get('in_ti', 'None')
        out_ti = kwargs.get('out_ti', 'None')
        in_tj = kwargs.get('in_tj', 'None')
        out_tj = kwargs.get('out_tj', 'None')
        in_tim = kwargs.get('in_tim', 'None')
        out_tim = kwargs.get('out_tim', 'None')
        in_tjm = kwargs.get('in_tjm', 'None')
        out_tjm = kwargs.get('out_tjm', 'None')

        replacements = (in_ti, str(out_ti)), (in_tj, str(out_tj)), \
                       (in_tim, str(out_tim)), (in_tjm, str(out_tjm))

    in_cwv_out = set(['in_ti', 'out_ti', 'in_tj', 'out_tj', 'in_cwv',
                      'out_cwv'])

    if in_cwv_out == set(kwargs):
        in_cwv = kwargs.get('in_cwv', 'None')
        out_cwv = kwargs.get('out_cwv', 'None')
        in_ti = kwargs.get('in_ti', 'None')
        out_ti = kwargs.get('out_ti', 'None')
        in_tj = kwargs.get('in_tj', 'None')
        out_tj = kwargs.get('out_tj', 'None')

        replacements = (in_ti, str(out_ti)), (in_tj, str(out_tj)), \
                       (in_cwv, str(out_cwv))

    in_lst_out = set(['in_ti', 'out_ti', 'in_tj', 'out_tj', 'in_cwv',
                      'out_cwv', 'in_avg_lse', 'out_avg_lse', 'in_delta_lse',
                      'out_delta_lse'])

    if in_lst_out == set(kwargs):
        in_cwv = kwargs.get('in_cwv', 'None')
        out_cwv = kwargs.get('out_cwv', 'None')
        in_ti = kwargs.get('in_ti', 'None')
        out_ti = kwargs.get('out_ti', 'None')
        in_tj = kwargs.get('in_tj', 'None')
        out_tj = kwargs.get('out_tj', 'None')
        in_avg_lse = kwargs.get('in_avg_lse', 'None')
        out_avg_lse = kwargs.get('out_avg_lse', 'None')
        in_delta_lse = kwargs.get('in_delta_lse', 'None')
        out_delta_lse = kwargs.get('out_delta_lse', 'None')

        replacements = (in_ti, str(out_ti)), \
                       (in_tj, str(out_tj)), \
                       (in_cwv, str(out_cwv)), \
                       (in_avg_lse, str(out_avg_lse)), \
                       (in_delta_lse, str(out_delta_lse))

    return reduce(lambda alpha, omega: alpha.replace(*omega),
                  replacements, string)


def determine_average_emissivity(outname, landcover_map, avg_lse_expression):
    """
    Produce an average emissivity map based on FROM-GLC map covering the region
    of interest.
    """
    msg = ('\n|i Determining average land surface emissivity based on a '
           'look-up table ')
    if info:
        msg += ('| Expression:\n\n {exp}')
        msg = msg.format(exp=avg_lse_expression)
    g.message(msg)

    avg_lse_expression = replace_dummies(avg_lse_expression,
                                         instring=DUMMY_MAPCALC_STRING_FROM_GLC,
                                         outstring=landcover_map)

    avg_lse_equation = equation.format(result=outname,
                                       expression=avg_lse_expression)

    grass.mapcalc(avg_lse_equation, overwrite=True)

    if info:
        run('r.info', map=outname, flags='r')

    del(avg_lse_expression)
    del(avg_lse_equation)
    
    # save land surface emissivity map?
    if emissivity_output:
        run('g.rename', raster=(outname, emissivity_output))


def determine_delta_emissivity(outname, landcover_map, delta_lse_expression):
    """
    Produce a delta emissivity map based on the FROM-GLC map covering the
    region of interest.
    """
    msg = ('\n|i Determining delta land surface emissivity based on a '
           'look-up table ')
    if info:
        msg += ('| Expression:\n\n {exp}')
        msg = msg.format(exp=delta_lse_expression)
    g.message(msg)

    delta_lse_expression = replace_dummies(delta_lse_expression,
                                           instring=DUMMY_MAPCALC_STRING_FROM_GLC,
                                           outstring=landcover_map)

    delta_lse_equation = equation.format(result=outname,
                                         expression=delta_lse_expression)

    grass.mapcalc(delta_lse_equation, overwrite=True)

    if info:
        run('r.info', map=outname, flags='r')

    del(delta_lse_expression)
    del(delta_lse_equation)

    # save delta land surface emissivity map?
    if delta_emissivity_output:
        run('g.rename', raster=(outname, delta_emissivity_output))


def get_cwv_window_means(outname, t1x, t1x_mean_expression):
    """

    ***
    This function is NOT used.  It was part of an initial step-by-step approach,
    while coding and testing.  Kept for future plans!?
    ***

    Get window means for T1x
    """
    msg = ('\n |i Deriving window means from {Tx} ')
    msg += ('using the expression:\n {exp}')
    msg = msg.format(Tx=t1x, exp=t1x_mean_expression)
    g.message(msg)

    tx_mean_equation = equation.format(result=outname,
                                       expression=t1x_mean_expression)
    grass.mapcalc(tx_mean_equation, overwrite=True)

    if info:
        run('r.info', map=outname, flags='r')

    del(t1x_mean_expression)
    del(tx_mean_equation)
    
    # save for debuging
    #save_map(outname)


def estimate_ratio_ji(outname, tmp_ti_mean, tmp_tj_mean, ratio_expression):
    """

    ***
    This function is NOT used.  It was part of an initial step-by-step approach,
    while coding and testing.  Kept for future plans!?
    ***

    Estimate Ratio ji for the Column Water Vapor retrieval equation.
    """
    msg = '\n |i Estimating ratio Rji...'
    msg += '\n' + ratio_expression
    g.message(msg)

    ratio_expression = replace_dummies(ratio_expression,
                                       in_ti=DUMMY_Ti_MEAN, out_ti=tmp_ti_mean,
                                       in_tj=DUMMY_Tj_MEAN, out_tj=tmp_tj_mean)

    ratio_equation = equation.format(result=outname,
                                     expression=ratio_expression)

    grass.mapcalc(ratio_equation, overwrite=True)

    if info:
        run('r.info', map=outname, flags='r')

    # save for debuging
    #save_map(outname)


def estimate_column_water_vapor(outname, ratio, cwv_expression):
    """

    ***
    This function is NOT used.  It was part of an initial step-by-step approach,
    while coding and testing.  Kept for future plans!?
    ***

    """
    msg = "\n|i Estimating atmospheric column water vapor "
    msg += '| Mapcalc expression: '
    msg += cwv_expression
    g.message(msg)

    cwv_expression = replace_dummies(cwv_expression,
                                     instring=DUMMY_Rji,
                                     outstring=ratio)

    cwv_equation = equation.format(result=outname, expression=cwv_expression)

    grass.mapcalc(cwv_equation, overwrite=True)

    if info:
        run('r.info', map=outname, flags='r')

    # save Column Water Vapor map?
    if cwv_output:
        run('g.rename', raster=(outname, cwv_output))

    # save for debuging
    #save_map(outname)


def estimate_cwv_big_expression(outname, t10, t11, cwv_expression):
    """
    Derive a column water vapor map using a single mapcalc expression based on
    eval.

            *** To Do: evaluate -- does it work correctly? *** !
    """
    msg = "\n|i Estimating atmospheric column water vapor "
    if info:
        msg += '| Expression:\n'
    g.message(msg)

    if info:
        msg = replace_dummies(cwv_expression,
                              in_ti=t10, out_ti='T10',
                              in_tj=t11, out_tj='T11')
        msg += '\n'
        print(msg)

    cwv_equation = equation.format(result=outname, expression=cwv_expression)
    grass.mapcalc(cwv_equation, overwrite=True)

    if info:
        run('r.info', map=outname, flags='r')

    # save Column Water Vapor map?
    if cwv_output:

        # strings for metadata
        history_cwv = 'FixMe -- Column Water Vapor model: '
        history_cwv += 'FixMe -- Add equation?'
        title_cwv = 'Column Water Vapor'
        description_cwv = 'Column Water Vapor'
        units_cwv = 'g/cm^2'
        source1_cwv = 'FixMe'
        source2_cwv = 'FixMe'

        # history entry
        run("r.support", map=outname, title=title_cwv,
            units=units_cwv, description=description_cwv,
            source1=source1_cwv, source2=source2_cwv,
            history=history_cwv)

        run('g.rename', raster=(outname, cwv_output))

    del(cwv_expression)
    del(cwv_equation)


def estimate_lst(outname, t10, t11, avg_lse_map, delta_lse_map, cwv_map, lst_expression):
    """
    Produce a Land Surface Temperature map based on a mapcalc expression
    returned from a SplitWindowLST object.

    Inputs are:

    - brightness temperature maps t10, t11
    - column water vapor map
    - a temporary filename
    - a valid mapcalc expression
    """
    msg = '\n|i Estimating land surface temperature '
    if info:
        msg += "| Expression:\n"
    g.message(msg)

    if info:
        msg = lst_expression
        msg += '\n'
        print(msg)

    # replace the "dummy" string...
    if landcover_map:
        split_window_expression = replace_dummies(lst_expression,
                                                  in_avg_lse=DUMMY_MAPCALC_STRING_AVG_LSE,
                                                  out_avg_lse=avg_lse_map,
                                                  in_delta_lse=DUMMY_MAPCALC_STRING_DELTA_LSE,
                                                  out_delta_lse=delta_lse_map,
                                                  in_cwv=DUMMY_MAPCALC_STRING_CWV,
                                                  out_cwv=cwv_map,
                                                  in_ti=DUMMY_MAPCALC_STRING_T10,
                                                  out_ti=t10,
                                                  in_tj=DUMMY_MAPCALC_STRING_T11,
                                                  out_tj=t11)
    elif emissivity_class:
        split_window_expression = replace_dummies(lst_expression,
                                                  in_cwv=DUMMY_MAPCALC_STRING_CWV,
                                                  out_cwv=cwv_map,
                                                  in_ti=DUMMY_MAPCALC_STRING_T10,
                                                  out_ti=t10,
                                                  in_tj=DUMMY_MAPCALC_STRING_T11,
                                                  out_tj=t11)
    # Convert to Celsius?
    if celsius:
        split_window_expression = '({swe}) - 273.15'.format(swe=split_window_expression)
        split_window_equation = equation.format(result=outname,
                                            expression=split_window_expression)
    else:
        split_window_equation = equation.format(result=outname,
                                            expression=split_window_expression)

    grass.mapcalc(split_window_equation, overwrite=True)

    if info:
        run('r.info', map=outname, flags='r')

    del(split_window_expression)
    del(split_window_equation)

def main():
    """
    Main program
    """

    # Temporary filenames

    # The following three are meant for a test step-by-step cwv estimation, see
    # unused functions!

    # tmp_ti_mean = tmp_map_name('ti_mean')  # for cwv
    # tmp_tj_mean = tmp_map_name('tj_mean')  # for cwv
    # tmp_ratio = tmp_map_name('ratio')  # for cwv

    tmp_avg_lse = tmp_map_name('avg_lse')
    tmp_delta_lse = tmp_map_name('delta_lse')
    tmp_cwv = tmp_map_name('cwv')
    #tmp_lst = tmp_map_name('lst')

    # basic equation for mapcalc
    global equation, citation_lst
    equation = "{result} = {expression}"

    # user input
    mtl_file = options['mtl']

    if not options['prefix']:
        b10 = options['b10']
        b11 = options['b11']
        t10 = options['t10']
        t11 = options['t11']

        if not options['clouds']:
            qab = options['qab']
            cloud_map = False

        else:
            qab = False
            cloud_map = options['clouds']

    elif options['prefix']:
        prefix = options['prefix']
        b10 = prefix + '10'
        b11 = prefix + '11'

        if not options['clouds']:
            qab = prefix + 'QA'
            cloud_map = False

        else:
            cloud_map = options['clouds']
            qab = False

    qapixel = options['qapixel']
    lst_output = options['lst']

    # save Brightness Temperature maps?
    global brightness_temperature_prefix
    if options['prefix_bt']:
        brightness_temperature_prefix = options['prefix_bt']
    else:
        brightness_temperature_prefix = None

    global cwv_output
    cwv_window_size = int(options['window'])
    assertion_for_cwv_window_size_msg = ('A spatial window of size 5^2 or less is not '
                                         'recommended. Please select a larger window. '
                                         'Refer to the manual\'s notes for details.')
    assert cwv_window_size >= 7, assertion_for_cwv_window_size_msg
    cwv_output = options['cwv']

    # optional maps
    average_emissivity_map = options['emissivity']
    delta_emissivity_map = options['delta_emissivity']

    # output for in-between maps?
    global emissivity_output, delta_emissivity_output
    emissivity_output = options['emissivity_out']
    delta_emissivity_output = options['delta_emissivity_out']

    global landcover_map, emissivity_class
    landcover_map = options['landcover']
    emissivity_class = options['emissivity_class']

    # flags
    global info, null
    info = flags['i']
    scene_extent = flags['e']
    timestamping = flags['t']
    null = flags['n']

    global celsius
    celsius = flags['c']

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
            run('g.region', rast=b10, align=b10)
            msg = msg.format(name=b10)

        elif t10:
            run('g.region', rast=t10, align=t10)
            msg = msg.format(name=t10)

        g.message(msg)

    elif scene_extent:
        grass.warning(_('Operating on current region'))

    #
    # 1. Mask clouds
    #

    if cloud_map:
        # user-fed cloud map?
        msg = '\n|i Using {cmap} as a MASK'.format(cmap=cloud_map)
        g.message(msg)
        r.mask(raster=cloud_map, flags='i', overwrite=True)

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
            t10 = tirs_to_at_satellite_temperature(b10, mtl_file)

        # likewise for b11 -> t11
        if b11:
            # convert DNs to at-satellite temperatures
            t11 = tirs_to_at_satellite_temperature(b11, mtl_file)

    #
    # Initialise a SplitWindowLST object
    #

    split_window_lst = SplitWindowLST(emissivity_class)
    citation_lst = split_window_lst.citation

    #
    # 3. Land Surface Emissivities
    #

    # use given fixed class?
    if emissivity_class:

        if split_window_lst.landcover_class is False:
            # replace with meaningful error
            g.warning('Unknown land cover class string! Note, this string '
                      'input option is case sensitive.')

        if emissivity_class == 'Random':
            msg = "\n|! Random emissivity class selected > " + \
                split_window_lst.landcover_class + ' '

        else:
            msg = '\n|! Retrieving average emissivities *only* for {eclass} '

        if info:
            msg += '| Average emissivities (channels 10, 11): '
            msg += str(split_window_lst.emissivity_t10) + ', ' + \
                str(split_window_lst.emissivity_t11)

        msg = msg.format(eclass=split_window_lst.landcover_class)
        g.message(msg)

    # use the FROM-GLC map
    elif landcover_map:

        if average_emissivity_map:
            tmp_avg_lse = average_emissivity_map

        if not average_emissivity_map:
            determine_average_emissivity(tmp_avg_lse, landcover_map,
                                         split_window_lst.average_lse_mapcalc)
            if options['emissivity_out']:
                tmp_avg_lse = options['emissivity_out']

        if delta_emissivity_map:
            tmp_delta_lse = delta_emissivity_map

        if not delta_emissivity_map:
            determine_delta_emissivity(tmp_delta_lse, landcover_map,
                                       split_window_lst.delta_lse_mapcalc)
            if options['delta_emissivity_out']:
                tmp_delta_lse = options['delta_emissivity_out']

    #
    # 4. Modified Split-Window Variance-Covariance Matrix > Column Water Vapor
    #
    

    if info:
        msg = '\n|i Spatial window of size {n} for Column Water Vapor estimation: '
        msg = msg.format(n=cwv_window_size)
        g.message(msg)

    cwv = Column_Water_Vapor(cwv_window_size, t10, t11)
    citation_cwv = cwv.citation
    estimate_cwv_big_expression(tmp_cwv, t10, t11, cwv._big_cwv_expression())
    if cwv_output:
        tmp_cwv = cwv_output

    #
    # 5. Estimate Land Surface Temperature
    #

    if info and emissivity_class == 'Random':
        msg = '\n|* Will pick a random emissivity class!'
        grass.verbose(msg)

    estimate_lst(lst_output, t10, t11,
                 tmp_avg_lse, tmp_delta_lse, tmp_cwv,
                 split_window_lst.sw_lst_mapcalc)

    #
    # Post-production actions
    #

    # remove MASK
    r.mask(flags='r', verbose=True)

    # time-stamping
    if timestamping:
        add_timestamp(mtl_file, lst_output)

        if cwv_output:
            add_timestamp(mtl_file, cwv_output)

    # Apply color table
    if celsius:
        run('r.colors', map=lst_output, color='celsius')
    else:
        # color table for kelvin
        run('r.colors', map=lst_output, color='kelvin')

    # ToDo: helper function for r.support
    # strings for metadata
    history_lst = '\n' + citation_lst
    history_lst += '\n\n' + citation_cwv
    history_lst += '\n\nSplit-Window model: '
    history_lst += split_window_lst._equation  # :wsw_lst_mapcalc
    description_lst = ('Land Surface Temperature derived from a split-window algorithm. ')

    if celsius:
        title_lst = 'Land Surface Temperature (C)'
        units_lst = 'Celsius'

    else:
        title_lst = 'Land Surface Temperature (K)'
        units_lst = 'Kelvin'

    landsat8_metadata = Landsat8_MTL(mtl_file)
    source1_lst = landsat8_metadata.scene_id
    source2_lst = landsat8_metadata.origin

    # history entry
    run("r.support", map=lst_output, title=title_lst,
        units=units_lst, description=description_lst,
        source1=source1_lst, source2=source2_lst,
        history=history_lst)

    # (re)name the LST product
    #run("g.rename", rast=(tmp_lst, lst_output))

    # restore region
    if scene_extent:
        grass.del_temp_region()  # restoring previous region settings
        g.message("|! Original Region restored")

    # print citation
    if info:
        print('\nSource: ' + citation_lst)


if __name__ == "__main__":
    options, flags = grass.parser()
    atexit.register(cleanup)
    sys.exit(main())
