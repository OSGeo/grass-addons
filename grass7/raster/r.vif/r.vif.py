#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
########################################################################
#
# MODULE:       r.vif
# AUTHOR(S):    Paulo van Breugel <p.vanbreugel AT gmail.com>
# PURPOSE:      Calculate the variance inflation factor of set of
#               variables. Alternatively, to speed the calculation up,
#               this can be done for an user defined number of random
#               cells. The user can set a maximum VIF, in wich case the VIF
#               will calculated again after removing the variables with the
#               highest VIF. This will be repeated till the VIF falls below
#               the user defined VIF threshold value.
# TODO          Include the option to force the function to retain one or more
#               variables
# Dependency:    r.regression.multi
#
# COPYRIGHT: (C) 2014 Paulo van Breugel
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
#% description: Calculate the variance inflation factor
#% keyword: raster
#% keyword: variance inflation factor
#%End

#%option
#% key: maps
#% type: string
#% gisprompt: old,cell,raster
#% description: variables
#% key_desc: name
#% required: yes
#% multiple: yes
#%end

#%option
#% key: retain
#% type: string
#% gisprompt: old,cell,raster
#% description: variables to retain
#% key_desc: name
#% required: no
#% multiple: yes
#%end

#%option G_OPT_F_OUTPUT
#% key:file
#% description: Name of output text file
#% key_desc: name
#% required: no
#%end

#%option
#% key: maxvif
#% type: string
#% description: Maximum vif
#% key_desc: string
#%end

#%option
#% key: nsp
#% type: string
#% gisprompt: new
#% description: random sample size
#% key_desc: number or percentage
#% required: no
#%end

# Test purposes
#options = {"maps":"bio1,bio5,bio6", "output":"bb", "nsp":"100", "retain":"bio1,bio2", "maxvif":"100", "file":"aa.txt"}
#flags = {"m":True, "k":True, "n":False, "i":True, "k":True}

#=======================================================================
## General
#=======================================================================

# import libraries
import os
import sys
import uuid
import atexit
import math
import tempfile
import string
import collections
import numpy as np
import grass.script as grass

# Check if running in GRASS
if not os.environ.has_key("GISBASE"):
    grass.message("You must be in GRASS GIS to run this program.")
    sys.exit(1)

# create set to store names of temporary maps to be deleted upon exit
clean_rast = set()

def cleanup():
    for rast in clean_rast:
        grass.run_command("g.remove",
        type="rast", name=rast, quiet=True)

# main function
def main():

    # Variables
    IPF = options['maps']
    IPF = IPF.split(',')
    IPFn = [i.split('@')[0] for i in IPF]
    IPR = options['retain']
    if IPR != '':
        IPR = IPR.split(',')
        IPRn = [i.split('@')[0] for i in IPR]
        iprn = collections.Counter(IPRn)
        ipfn = collections.Counter(IPFn)
        IPFn = list((ipfn-iprn).elements())
        ipr = collections.Counter(IPR)
        ipf = collections.Counter(IPF)
        IPF = list((ipf-ipr).elements())
        if len(IPFn) == 0:
            grass.fatal("No variables to remove")
    OPF = options['file']
    if OPF == '':
        OPF = tempfile.mkstemp()[1]
    NSP = options['nsp']
    MXVIF = float(options['maxvif'])

    # Test if text file exists. If so, append _v1 to file name
    k = 0
    OPFold = OPF[:]
    while os.path.isfile(OPF):
        k = k + 1
        opft = OPF.split('.')
        if len(opft) == 1:
            OPF = opft[0] + "_v" + str(k)
        else:
            OPF = opft[0] + "_v" + str(k) + "." + opft[1]
    if k > 0:
        grass.info("there is already a file " + OPFold + ".")
        grass.info("Using " + OPF + "_v" + str(k) + " instead")

#=======================================================================
## Calculate VIF and write to standard output (& optionally to file)
#=======================================================================

    # Create mask if nsp is set replace existing MASK if exist)
    citiam = grass.find_file('MASK', element='cell',
                             mapset=grass.gisenv()['MAPSET'])
    if NSP != '':
        if citiam['fullname'] != '':
            tmpf0 = "rvif_mask_" + str(uuid.uuid4())
            tmpf0 = string.replace(tmpf0, '-', '_')
            grass.run_command("g.copy", quiet=True, raster=("MASK", tmpf0))
            clean_rast.add(tmpf0)
        tmpf1 = "rvif_" + str(uuid.uuid4())
        tmpf1 = string.replace(tmpf1, '-', '_')
        grass.run_command("r.random", quiet=True, input=IPF[0], n=NSP, raster=tmpf1)
        grass.run_command("r.mask", quiet=True, overwrite=True, raster=tmpf1)
        clean_rast.add(tmpf1)

    # Open text file for writing and write heading
    text_file = open(OPF, "w")

HIER GEBLEVEN... NU NOG UITVOGELEN HOE DE VARIABLES ALTIJD BEWAARD BLIJVEN

    # Calculate VIF and write results to text file
    rvifmx = MXVIF + 1
    IPF2 = IPF[:]
    IPFn2 = IPFn[:]
    while MXVIF < rvifmx:
        rvif = np.zeros(len(IPF2))
        text_file.write("variable\tvif\tsqrtvif\n")
        for k in xrange(len(IPF2)):
            MAPy = IPF2[k]
            nMAPy = IPFn2[k]
            MAPx = IPF2[:]
            del MAPx[k]
            vifstat = grass.read_command("r.regression.multi",
                               flags="g", quiet=True,
                               mapx=MAPx, mapy=MAPy)
            vifstat = vifstat.split('\n')
            vifstat = [i.split('=') for i in vifstat]
            vif = 1 / (1 - float(vifstat[1][1]))
            sqrtvif = math.sqrt(vif)
            text_file.write(nMAPy + "\t" + str(round(vif, 3)) + "\t" + str(round(sqrtvif, 3)) + "\n")
            rvif[k] = vif

        rvifmx = max(rvif)
        if rvifmx >= MXVIF:
            rvifindex = np.argmax(rvif, axis=None)
            varremove = IPF2[rvifindex]
            text_file.write("\n")
            text_file.write("Removing " + varremove)
            text_file.write("\n---------------------------\n")
            text_file.write("\n")
            del IPF2[rvifindex]
            del IPFn2[rvifindex]
        else:
            text_file.write("\n\n")
            text_file.write("Final selection (above) has maximum VIF = " + str(round(rvifmx, 3)))
    text_file.close()

    # Recover original mask
    if NSP != '':
        grass.run_command("r.mask", flags="r", quiet=True)
        if citiam['fullname'] != '':
            grass.mapcalc("MASK = $tmpf0",tmpf0=tmpf0, quiet=True)
            grass.run_command("g.remove", quiet=True, flags="f", type="raster", name=tmpf0)
        grass.run_command("g.remove", quiet=True, flags="f", type="raster", name=tmpf1)

    # Write to std output
    grass.info("selected variables are: ")
    grass.info(', '.join(IPFn2))
    grass.info("with as maximum VIF: " + str(rvifmx))
    grass.info("Full statistics are in " + OPF)

if __name__ == "__main__":
    options, flags = grass.parser()
    atexit.register(cleanup)
    sys.exit(main())






