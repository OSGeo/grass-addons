#!/usr/bin/env python
# -*- coding: utf-8 -*-

########################################################################
#
# MODULE:       r.niche.similarity
# AUTHOR(S):    Paulo van Breugel <paulo AT ecodiv.org>
# PURPOSE:      Compute  degree of niche overlap using the statistics D
#               and I (as proposed by Warren et al., 2008) based on
#               Schoeners D (Schoener, 1968) and Hellinger Distances
#               (van der Vaart, 1998)
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
#% description: Computes niche overlap or similarity
#%End

#%option
#% key: maps
#% type: string
#% gisprompt: old,cell,raster
#% description: Input maps
#% key_desc: name
#% required: yes
#% multiple: yes
#% guisection: Suitability distribution maps
#%end

#%option
#% key: output
#% type: string
#% gisprompt: new
#% description: Name of output text file
#% key_desc: name
#% required: no
#%end

#%flag
#% key: i
#% description: Calculate I niche similarity
#% guisection: Statistics
#%end

#%flag
#% key: d
#% description: Calculate D niche similarity
#% guisection: Statistics
#%end

##----------------------------------------------------------------------------
# Test purposes
##----------------------------------------------------------------------------
#options = {"maps":"bio1,bio5,bio6", "output":""}
#flags = {"i":True, "d":True}

##----------------------------------------------------------------------------
## STANDARD ##
##----------------------------------------------------------------------------

# import libraries
import os
import sys
import atexit
import uuid
import string
import tempfile
import grass.script as grass

# Check if running in GRASS
if not os.environ.has_key("GISBASE"):
    grass.message( "You must be in GRASS GIS to run this program." )
    sys.exit(1)

# Cleanup
clean_rast = set()

def cleanup():
    for rast in clean_rast:
        grass.run_command("g.remove",
        type="rast", name = rast, quiet = True)

##----------------------------------------------------------------------------
## main function
##----------------------------------------------------------------------------

def main():

    ## input
    #--------------------------------------------------------------------------
    INMAPS = options['maps']
    INMAPS = INMAPS.split(',')
    VARI = [i.split('@')[0] for i in INMAPS]
    OPF = options['output']
    if OPF == '':
        OPF = tempfile.mkstemp()[1]
    flag_i = flags['i']
    flag_d = flags['d']

    ## Checks
    #--------------------------------------------------------------------------

    # Check if there are more than 1 input maps
    NLAY = len(INMAPS)
    if NLAY < 2:
        grass.fatal("You need to provide 2 or more raster maps")

    # Check that at least one statistic is selected
    if flag_i == '' and flag_d == '':
        grass.fatal("You need to select at least one statistic")

    # Test if text file exists. If so, append _v1 to file name
    #--------------------------------------------------------------------------
    k = 0
    OPFold = OPF[:]
    OPFold = OPFold.split('.')
    while os.path.isfile(OPF):
        k = k + 1
        opft = OPF.split('.')
        if len(opft) == 1:
            OPF = opft[0] + "_" + str(k)
        else:
            OPF = OPFold[0] + "_v" + str(k) + "." + OPFold[1]
    if k > 0:
        grass.info("there is already a file " + OPFold[0] + ".")
        grass.info("Using " + OPF + " instead")

    #=======================================================================
    ## Calculate D and I and write to standard output (& optionally to file)
    #=======================================================================

    # Open text file for writing and write heading
    text_file = open(OPF, "w")
    text_file.write("raster1,raster2,statistic,value" + "\n")

    # Write D and I values to standard output and optionally to text file
    i=0
    while i < NLAY:
        nlay1 = INMAPS[i]
        nvar1 = VARI[i]
        vsum1 = float(grass.parse_command("r.univar", quiet=True, flags="g", map=nlay1)['sum'])

        j = i + 1
        while j < NLAY:
            nlay2 = INMAPS[j]
            nvar2 = VARI[j]
            vsum2 = float(grass.parse_command("r.univar", quiet=True, flags="g", map=nlay2)['sum'])

            ## Calculate D (Schoener's 1968)
            #=======================================================================

            if flag_d:
                tmpf0 = "rniche_" + str(uuid.uuid4())
                tmpf0 = string.replace(tmpf0, '-', '_')
                clean_rast.add(tmpf0)
                grass.mapcalc("$tmpf0 = abs(double($nlay1)/$vsum1 - double($nlay2)/$vsum2)",
                             tmpf0 = tmpf0,
                             nlay1 = nlay1,
                             vsum1 = vsum1,
                             nlay2 = nlay2,
                             vsum2 = vsum2,
                             quiet=True)
                NO = float(grass.parse_command("r.univar", quiet=True, flags="g", map=tmpf0)['sum'])
                NOV = 1 - ( 0.5 * NO )
                grass.run_command("g.remove", quiet=True, flags="f", type="raster", name=tmpf0)
                text_file.write("D, " + nvar1 + "," + nvar2 + "," + str(NOV) + "\n")
                grass.message("niche overlap (D) of " + nvar1 + " and " + nvar2 + ": " + str(round(NOV,3)))

                ## Calculate I (Warren et al. 2008), but note that the original formulation
                ## was corrected in erratum by Warren et al, using I = 1 - H^2 * 0.5
                ## The sqrt in the H formulation and this new ^2 cancel each other out,
                ## leading to the formulation used below.
                #=======================================================================

            if flag_i:
                tmpf1 = "rniche_" + str(uuid.uuid4())
                tmpf1 = string.replace(tmpf1, '-', '_')
                clean_rast.add(tmpf1)
                grass.mapcalc("$tmpf1 = (sqrt(double($nlay1)/$vsum1) - sqrt(double($nlay2)/$vsum2))^2",
                             tmpf1 = tmpf1,
                             nlay1 = nlay1,
                             vsum1 = vsum1,
                             nlay2 = nlay2,
                             vsum2 = vsum2,
                             quiet=True)
                NE = float(grass.parse_command("r.univar", quiet=True, flags="g", map=tmpf1)['sum'])
                NEQ = 1 - (0.5 * NE)
                grass.run_command("g.remove", quiet=True, flags="f", type="raster", name=tmpf1)
                text_file.write("I, " + nvar1 + "," + nvar2 + "," + str(NEQ) + "\n")
                grass.message("niche overlap (I) of " + nvar1 + " and " + nvar2 + ": " + str(round(NEQ, 3)))

            j = j + 1
        i = i + 1

    text_file.close()

if __name__ == "__main__":
    options, flags = grass.parser()
    atexit.register(cleanup)
    sys.exit(main())












