#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
########################################################################
#
# MODULE:       r.category.clean
# AUTHOR(S):    Paulo van Breugel
# DESCRIPTION:  Trim a cut out raster layer by removing non-existing categories
#               and their color defintions. Optionally, a new map can be
#               created to ensure consecutive categories values, but retaining
#               the category labels and colors. The user als has the option to
#               export the categories, category labels and color codes (RGB) as
#               csv file or as a QGIS color map file.
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
#% description: Trim redundant category labels and colors and export as QGIS colour file.
#% keyword: raster
#% keyword: color
#% keyword: color table
#% keyword: category
#%End

#%option
#% key: input
#% type: string
#% gisprompt: old,cell,raster
#% description: input map
#% key_desc: name
#% required: yes
#% multiple: no
#% guisection: Raster
#%end

#%option
#% key: output
#% type: string
#% gisprompt: new,cell,raster
#% description: output map
#% key_desc: name
#% required: no
#% multiple: no
#% guisection: Raster
#%end

#%option G_OPT_F_OUTPUT
#% key:csv
#% description: Attribute table (csv format)
#% key_desc: name
#% required: no
#% guisection: Export
#%end

#%option G_OPT_F_OUTPUT
#% key:qgis
#% description: QGIS color file (txt format)
#% key_desc: name
#% required: no
#% guisection: Export
#%end

#%flag:
#% key: n
#% description: Recode layer to get consecutive category values
#%end

#%rules
#% requires_all: -n, output
#%end

#=======================================================================
## General
#=======================================================================

# import libraries
import os
import sys
from subprocess import PIPE
from grass.pygrass.modules import Module
import grass.script as grass

# Check if running in GRASS
if not os.environ.has_key("GISBASE"):
    grass.message("You must be in GRASS GIS to run this program.")
    sys.exit(1)

# main function
def main():

    # Input
    IP = options['input']
    OP = options['output']
    CSV = options['csv']
    QGIS = options['qgis']
    flags_n = flags['n']

    # Check if raster is integer
    iscell = grass.raster.raster_info(IP)["datatype"]
    if iscell != u'CELL':
        grass.error('Input should be an integer raster layer')

    # Get map category values and their labels
    CATV = Module('r.category', map=IP, stdout_=PIPE).outputs.stdout
    RCAT = CATV.split('\n')
    RCAT = filter(None,RCAT)
    RID = [z.split('\t')[0] for z in RCAT]
    RIDI = map(int, RID)

    # Get full color table
    RCOL = grass.read_command("r.colors.out", map=IP).split('\n')
    RCOL = [ x for x in RCOL if "nv" not in x and 'default' not in x]
    RCOL = filter(None, RCOL)
    CCAT = [z.split(' ')[0] for z in RCOL]
    CCAT = map(int, CCAT)

    # Set strings / list to be used in loop
    CR = ""; RECO = ""; CL = ""; CV = []

    # recode to consecutive category values
    if flags_n:
        RIDN = range(1, len(RID) + 1)
        RLAB = [z.split('\t')[1] for z in RCAT]
        for j in xrange(len(RID)):
            RECO = RECO + RID[j] + ":" + RID[j] + ":" + str(RIDN[j]) + "\n"
            A = map(int, [i for i, x in enumerate(CCAT) if x == RIDI[j]])
            CV.append(RCOL[A[0]].split(' ')[1])
            CR = CR + str(RIDN[j]) + " " + CV[j] + "\n"
            CL = CL + str(RIDN[j]) + "|" + RLAB[j] + "\n"

        CR = CR + 'nv 255:255:255\ndefault 255:255:255\n'
        Module("r.recode", flags="a", input=IP, output=OP, rules="-", stdin_=RECO, quiet=True)
        Module("r.colors", map=OP, rules="-", stdin_=CR, quiet=True)
        Module("r.category", map=OP, rules="-", stdin_=CL, quiet=True, separator="pipe")
    else:
        # Check if new layer should be created
        if len(OP) > 0:
            k = IP + "," + OP
            grass.run_command("g.copy", raster=k)
        else:
            OP = IP

        # Remove redundant categories
        Module('r.category', map=OP, rules="-", stdin_=CATV, quiet=True)

        # Write color rules and assign colors
        for j in xrange(len(RIDI)):
            A = map(int, [i for i, x in enumerate(CCAT) if x == RIDI[j]])
            CV.append(RCOL[A[0]].split(' ')[1])
            CR = CR + str(RIDI[j]) + " " + CV[j] + "\n"
        CR = CR + 'nv 255:255:255\ndefault 255:255:255\n'
        Module("r.colors", map=OP, rules="-", stdin_=CR, quiet=True)

    # If attribute table (csv format) should be written
    if len(CSV) > 0:
        if flags_n:
            RCAT1 = CL.split('\n'); RCAT1 = filter(None,RCAT1)
            RCAT1 = [w.replace('|', ',') for w in RCAT1]
        else:
            RCAT1 = [w.replace('\t', ',') for w in RCAT]
        RCAT1.insert(0, "CATEGORY,CATEGORY LABEL")
        CV1 = list(CV); CV1.insert(0,"RGB")
        text_file = open(CSV, "w")
        for k in xrange(len(RCAT1)):
            text_file.write(RCAT1[k] + "," + CV1[k] + "\n")
        text_file.close()

    # If QGIS Color Map text files should be written
    if len(QGIS) > 0:
        RGB = [w.replace(':', ',') for w in CV]
        if flags_n:
            RCAT = CL.split('\n'); RCAT = filter(None,RCAT)
            RCAT = [w.replace('|', ',') for w in RCAT]
        else:
            RCAT = [w.replace('\t', ',') for w in RCAT]
        text_file = open(QGIS, "w")
        text_file.write("# QGIS color map for " + OP + "\n")
        text_file.write("INTERPOLATION:EXACT\n")
        for k in xrange(len(RCAT)):
            RC2 = RCAT[k].split(',')
            text_file.write(RC2[0] + "," + RGB[k] + ",255," + RC2[1] + "\n")
        text_file.close()

if __name__ == "__main__":
    options, flags = grass.parser()
    sys.exit(main())
























