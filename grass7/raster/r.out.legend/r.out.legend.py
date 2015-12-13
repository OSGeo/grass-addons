#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
########################################################################
#
# MODULE:       r.legend.out
# AUTHOR(S):    Paulo van Breugel
# DESCRIPTION:  Export the legend of a raster as image, which can be used
#               in e.g., the map composer in QGIS.
#
# COPYRIGHT: (C) 2015 Paulo van Breugel
#            http://ecodiv.org
#            http://pvanb.wordpress.com/
#
#            This program is free software under the GNU General Public
#            License (>=v2). Read the file COPYING that comes with GRASS
#            for details.
#
########################################################################
#
#%Module
#% description: Create and export image file with legend of a raster map
#% keyword: raster
#% keyword: color
#% keyword: color table
#% keyword: image
#%End

#%option G_OPT_R_MAP
#% key: raster
#%end

#%option G_OPT_F_OUTPUT
#% key:file
#% description: Name of the output file
#% key_desc: name
#%end

#%option
#% key: filetype
#% type: string
#% description: File type
#% key_desc: extension
#% options: png,ps,cairo
#% required: yes
#% multiple: no
#%end

#------------------------------------------------------------------------------

#%option
#% key: dimensions
#% type: string
#% description: width and height of the color legend
#% key_desc: width,height
#% required: yes
#% guisection: Image settings
#%end

#%option
#% key: unit
#% type: string
#% description: unit of the image dimensions
#% key_desc: unit
#% required: no
#% options: cm,mm,inch
#% answer: cm
#% guisection: Image settings
#%end

#%option
#% key: resolution
#% type: integer
#% description: resolution (dots/inch)
#% key_desc: value
#% required: yes
#% answer:300
#% guisection: Image settings
#%end

#%option G_OPT_CN
#% key: bgcolor
#% description: background colour
#% key_desc: name
#% required: no
#% answer: none
#% guisection: Image settings
#%end

#------------------------------------------------------------------------------

#%option
#% key: labelnum
#% type: integer
#% description: Number of text labels
#% key_desc: integer
#% required: no
#% answer: 5
#% guisection: Extra options
#%end

#%option
#% key: range
#% type: string
#% description: Use a subset of the map range for the legend
#% key_desc: min,max
#% required: no
#% guisection: Extra options
#%end

#%option
#% key: digits
#% type: integer
#% description: Maximum number of digits for raster value display
#% key_desc: integer
#% required: no
#% answer: 1
#%end

#%flag:
#% key: f
#% description: Flip legend
#% guisection: Extra options
#%end


#------------------------------------------------------------------------------

#%option
#% key: font
#% type: string
#% description: Font name
#% key_desc: string
#% required: no
#% answer: Arial
#% guisection: Font settings
#%end

#%option
#% key: fontsize
#% type: string
#% description: Font size
#% key_desc: float
#% required: no
#% answer: 10
#% guisection: Font settings
#%end

#=======================================================================
## General
#=======================================================================

# import libraries
import os
import sys
import math
import grass.script as grass

# Check if running in GRASS
if not os.environ.has_key("GISBASE"):
    grass.message("You must be in GRASS GIS to run this program.")
    sys.exit(1)

# Check if layers exist
def CheckLayer(raster):
    ffile = grass.find_file(raster, element = 'cell')
    if ffile['fullname'] == '':
        grass.fatal("The layer " + raster + " does not exist.")

# main function
def main():

    # Variables / parameters
    outputfile    = options['file']
    filetype      = options['filetype']
    dimensions    = options['dimensions']
    width, height = dimensions.split(",")
    resol         = options['resolution']
    unit          = options['unit']
    bgcolor       = options['bgcolor']
    inmap         = options['raster']
    labelnum      = options['labelnum']
    val_range     = options['range']
    font          = options['font']
    fontsize      = options['fontsize']
    digits          = int(options['digits'])
    flag_f        = flags['f']

    # Check if input layer exists
    CheckLayer(inmap)

    # Compute output size
    if unit=='cm':
        w = math.ceil(float(width)/2.54*float(resol))
        h = math.ceil(float(height)/2.54*float(resol))
    elif unit=='mm':
        w = math.ceil(float(width)/25.4*float(resol))
        h = math.ceil(float(height)/25.4*float(resol))
    elif unit=='inch':
        w = math.ceil(height*resol)
        h = math.ceil(height*resol)
    else:
        grass.error('Unit must be inch, cm or mm')

    # Compute fontsize
    fz = round(float(fontsize) * (float(resol)/72.272))

    # Compute image position
    maprange = grass.raster_info(inmap)
    maxval = round(maprange['max'],digits)
    if maxval<1:
        maxl=len(str(maxval)) -1
    else:
        maxl=len(str(maxval)) - 2

    if float(height)>float(width):
        iw = w + fz * maxl
        ih = h
        at = "1,99,1," + str((100*w/iw)-1)
    else:
        margin_left = 0.5 * (len(str(maprange['min'])) - 1)
        margin_right = 0.5 * maxl
        iw = w + fz * (margin_left + margin_right)
        ih = h + fz
        at = str(100 - (100*h/ih)+5) + ",99," + \
        str((100 * fz * margin_left / iw)) + "," + \
        str(100 - (100 * fz * margin_right / iw))

    # Open file connection, set font, write legend and close file
    grass.run_command("d.mon", start=filetype, output=outputfile, width=iw, height=ih,
                      resolution=1, bgcolor=bgcolor)
    if flag_f:
        flag='vsf'
    else:
        flag="vs"
    if val_range=='':
        grass.run_command("d.legend", flags=flag, raster=inmap, font=font,
                      at=at, fontsize=fz, labelnum=labelnum)
    else:
        grass.run_command("d.legend", flags=flag, raster=inmap, font=font,
                      at=at, fontsize=fz, labelnum=labelnum, range=val_range)

    grass.run_command("d.mon", stop=filetype)
    grass.info("File saved as " + outputfile)

if __name__ == "__main__":
    options, flags = grass.parser()
    sys.exit(main())










