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
# Dependency:    r.regression.multi
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
#% description: To calculate the stepwise variance inflation factor.
#% keyword: raster
#% keyword: variance inflation factor
#% keyword: VIF
#%End

#%option
#% key: maps
#% type: string
#% gisprompt: old,cell,raster
#% description: variables
#% required: yes
#% multiple: yes
#% guisection: Input
#%end

#%option
#% key: retain
#% type: string
#% gisprompt: old,cell,raster
#% description: variables to retain
#% required: no
#% multiple: yes
#% guisection: Input
#%end

#%option G_OPT_F_OUTPUT
#% key:file
#% description: Name of output text file
#% required: no
#% guisection: Input
#%end

#%option
#% key: maxvif
#% type: string
#% description: Maximum vif
#% key_desc: number
#% guisection: Input
#%end

#=======================================================================
## General
#=======================================================================

# import libraries
import os
import sys
import math
import tempfile
import numpy as np
import grass.script as grass

# Check if running in GRASS
if not os.environ.has_key("GISBASE"):
    grass.message("You must be in GRASS GIS to run this program.")
    sys.exit(1)

# Check if layers exist
def CheckLayer(envlay):
    for chl in xrange(len(envlay)):
        ffile = grass.find_file(envlay[chl], element = 'cell')
        if ffile['fullname'] == '':
            grass.fatal("The layer " + envlay[chl] + " does not exist.")

# main function
def main():

    # Variables
    IPF = options['maps']
    IPF = IPF.split(',')
    CheckLayer(IPF)
    IPR = options['retain']
    if IPR != '':
        IPR = IPR.split(',')
        CheckLayer(IPR)

        for k in xrange(len(IPR)):
            if IPR[k] not in IPF:
                IPF.extend([IPR[k]])
    IPFn = [i.split('@')[0] for i in IPF]
    IPRn = [i.split('@')[0] for i in IPR]

    MXVIF = options['maxvif']
    if MXVIF != '':
        MXVIF = float(MXVIF)
    OPF = options['file']
    if OPF == '':
        idf, OPF = tempfile.mkstemp()

    #=======================================================================
    ## Calculate VIF and write to standard output (& optionally to file)
    #=======================================================================

    # Calculate VIF and write results to text file
    name_lengths = []
    for i in IPF:
        name_lengths.append(len(i))
    nlength = max(name_lengths)
    if MXVIF =='':
        text_file = open(OPF, "w")
        text_file.write("variable,vif,sqrtvif\n")
        grass.info('{0[0]:{1}s} {0[1]:8s} {0[2]:8s}'.format(['variable', 'vif', 'sqrtvif'], nlength))
        for k in xrange(len(IPF)):
            MAPy = IPF[k]
            MAPx = IPF[:]
            del MAPx[k]
            vifstat = grass.read_command("r.regression.multi",
                               flags="g", quiet=True,
                               mapx=MAPx, mapy=MAPy)
            vifstat = vifstat.split('\n')
            vifstat = [i.split('=') for i in vifstat]
            if float(vifstat[1][1]) > 0.9999999999:
                vif = float("inf")
                sqrtvif = float("inf")
            else:
                rsqr = float(vifstat[1][1])
                vif = 1 / (1 - rsqr)
                sqrtvif = math.sqrt(vif)
            RES = [MAPy, vif, sqrtvif]
            text_file.write('{0[0]}, {0[1]}, {0[2]}\n'.format(RES))
            grass.info('{0[0]:{1}s} {0[1]:8.2f} {0[2]:8.2f}'.format(RES, nlength))
        text_file.close()
    else:
        text_file = open(OPF, "w")
        rvifmx = MXVIF + 1
        m = 0
        while MXVIF < rvifmx:
            m += 1
            grass.info("\n")
            grass.info("VIF round " + str(m))
            grass.info("----------------------------------------")
            rvif = np.zeros(len(IPF))
            text_file.write("variable\tvif\tsqrtvif\n")
            grass.info('{0[0]:{1}s} {0[1]:8s} {0[2]:8s}'.format(['variable', 'vif', 'sqrtvif'], nlength))
            for k in xrange(len(IPF)):
                MAPy = IPF[k]
                MAPx = IPF[:]
                del MAPx[k]
                vifstat = grass.read_command("r.regression.multi",
                                   flags="g", quiet=True,
                                   mapx=MAPx, mapy=MAPy)
                vifstat = vifstat.split('\n')
                vifstat = [i.split('=') for i in vifstat]
                if float(vifstat[1][1]) > 0.9999999999:
                    vif = float("inf")
                    sqrtvif = float("inf")
                else:
                    rsqr = float(vifstat[1][1])
                    vif = 1 / (1 - rsqr)
                    sqrtvif = math.sqrt(vif)
                RES = [MAPy, vif, sqrtvif]
                text_file.write('{0[0]}, {0[1]}, {0[2]}\n'.format(RES))
                grass.info('{0[0]:{1}s} {0[1]:8.2f} {0[2]:8.2f}'.format(RES, nlength))
                if IPFn[k] in IPRn:
                    rvif[k] = -9999
                else:
                    rvif[k] = vif

            rvifmx = max(rvif)
            if rvifmx >= MXVIF:
                rvifindex = np.argmax(rvif, axis=None)
                varremove = IPF[rvifindex]
                text_file.write("\n")
                text_file.write("Removing " + varremove)
                text_file.write("\n---------------------------\n")
                text_file.write("\n")
                del IPF[rvifindex]
                del IPFn[rvifindex]
            else:
                text_file.write("\n\n")
                text_file.write("Final selection (above) has maximum VIF = " + str(round(rvifmx, 3)))
        text_file.close()

        # Write to std output
        grass.info("")
        grass.info("selected variables are: ")
        grass.info("----------------------------------------")
        grass.info(', '.join(IPFn))
        grass.info("with as maximum VIF: " + str(rvifmx))
    grass.info("")
    if options['file'] != '':
        grass.info("Statistics are written to " + OPF + "\n")
    grass.info("")

if __name__ == "__main__":
    options, flags = grass.parser()
    sys.exit(main())






