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

#%flag
#% key: s
#% description: Only print selected variables
#%end

#%rules
#%requires_all: -s,maxvif
#%end

#==============================================================================
## General
#==============================================================================

# import libraries
import os
import sys
import math
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
    flag_s = flags['s']

    #==========================================================================
    ## Calculate VIF and write to standard output (& optionally to file)
    #==========================================================================

    # Determine maximum width of the columns to be printed to std output
    name_lengths = []
    for i in IPF:
        name_lengths.append(len(i))
    nlength = max(name_lengths)

    # Create arrays to hold results (which will be written to file at end)
    out_vif = []
    out_sqrt = []
    out_variable = []
    out_round = []

    # VIF is computed for each variable
    #--------------------------------------------------------------------------
    if MXVIF =='':
        # Print header of table to std output
        print('{0[0]:{1}s} {0[1]:8s} {0[2]:8s}'.format(
            ['variable', 'vif', 'sqrtvif'], nlength))

        # Compute the VIF
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

            # Write results to array (this will be printed to file at end
            # of script)
            out_vif.append(vif)
            out_sqrt.append(sqrtvif)
            out_variable.append(MAPy)
            print('{0[0]:{1}s} {0[1]:8.2f} {0[2]:8.2f}'.format([MAPy, vif,
                  sqrtvif], nlength))
        print
        if len(OPF) > 0:
            print("Statistics are written to " + OPF + "\n")

    # The stepwise variable selection procedure is run
    #--------------------------------------------------------------------------
    else:
        rvifmx = MXVIF + 1
        m = 0
        remove_variable = 'none'
        out_removed = []
        txt_message = "Working"

        # The VIF will be computed across all variables. Next, the variable
        # with highest vif is removed and the procedure is repeated. This
        # continuous till the maximum vif across the variables > maxvif
        while MXVIF < rvifmx:
            m += 1
            rvif = np.zeros(len(IPF))

            # print the header of the output table to the console
            if not flag_s:
                print
                print("VIF round " + str(m))
                print("--------------------------------------")
                print('{0[0]:{1}s} {0[1]:>8s} {0[2]:>8s}'.format(
                    ['variable', 'vif', 'sqrtvif'], nlength))
            else:
                txt_message = txt_message + "."
                grass.message(txt_message)

            # Compute the VIF and sqrt(vif) for all variables in this round
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

                # Write results to arrays (which will be written to csv file
                # at end of script)
                out_vif.append(vif)
                out_sqrt.append(sqrtvif)
                out_variable.append(MAPy)
                out_round.append(m)
                out_removed.append(remove_variable)

                # print result to console
                if not flag_s:
                    print('{0[0]:{1}s} {0[1]:8.2f} {0[2]:8.2f}'.format([MAPy,
                          vif, sqrtvif], nlength))

                # If variable is set to be retained by the user, the VIF
                # is set to -9999 to ensure it will not have highest VIF
                if IPFn[k] in IPRn:
                    rvif[k] = -9999
                else:
                    rvif[k] = vif

            # Compute the maximum vif across the variables for this round and
            # remove the variable with the highest VIF
            rvifmx = max(rvif)
            if rvifmx >= MXVIF:
                rvifindex = np.argmax(rvif, axis=None)
                remove_variable = IPFn[rvifindex]
                del IPF[rvifindex]
                del IPFn[rvifindex]


        # Write final selected variables to std output
        if not flag_s:
            print
            print("selected variables are: ")
            print("--------------------------------------")
            print(', '.join(IPFn))
            print
            if len(OPF) > 0:
                print("Statistics are written to " + OPF + "\n")
            print
        else:
            print(','.join(IPFn))

    if len(OPF) > 0:
        try:
            text_file = open(OPF, "w")
            if MXVIF =='':
                text_file.write("variable,vif,sqrtvif\n")
                for i in xrange(len(out_vif)):
                    text_file.write('{0:s},{1:.6f},{2:.6f}\n'.format(
                        out_variable[i], out_vif[i], out_sqrt[i]))
            else:
                text_file.write("round,removed,variable,vif,sqrtvif\n")
                for i in xrange(len(out_vif)):
                    text_file.write('{0:d},{1:s},{2:s},{3:.6f},{4:.6f}\n'.format(
                        out_round[i], out_removed[i],out_variable[i],
                         out_vif[i], out_sqrt[i]))
        finally:
            text_file.close()

if __name__ == "__main__":
    options, flags = grass.parser()
    sys.exit(main())




