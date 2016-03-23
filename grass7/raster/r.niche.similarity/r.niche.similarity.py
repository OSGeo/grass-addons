#!/usr/bin/env python
# -*- coding: utf-8 -*-

########################################################################
#
# MODULE:       r.niche.similarity
# AUTHOR(S):    Paulo van Breugel <p.vanbreugel AT gmail.com>
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
#% keyword: raster
#% keyword: niche modelling
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

#%option G_OPT_F_OUTPUT
#% key:output
#% description: Name of output text file
#% key_desc: name
#% required: no
#%end

#%flag
#% key: i
#% description: I niche similarity
#% guisection: Statistics
#%end

#%flag
#% key: d
#% description: D niche similarity
#% guisection: Statistics
#%end

#%flag
#% key: c
#% description: Correlation
#% guisection: Statistics
#%end

#%rules
#%required: -i,-d,-c
#%end

##----------------------------------------------------------------------------
# Test purposes
##----------------------------------------------------------------------------
#options = {"maps":"bio_1,bio_2,bio_3,bio_4,bio_5,bio_6,bio_7,bio_8, bio_9", "output":""}
#flags = {"i":True, "d":True, "c":True}

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
    grass.message("You must be in GRASS GIS to run this program.")
    sys.exit(1)

# Cleanup
clean_rast = set()

def cleanup():
    for rast in clean_rast:
        grass.run_command("g.remove", flags="f",
        type="rast", name=rast, quiet=True)

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
    flag_c = flags['c']

    ## Checks
    #--------------------------------------------------------------------------

    # Check if there are more than 1 input maps
    NLAY = len(INMAPS)
    if NLAY < 2:
        grass.fatal("You need to provide 2 or more raster maps")

    #=======================================================================
    ## Calculate D and I and write to standard output (& optionally to file)
    #=======================================================================

    # Open text file for writing and write heading
    text_file = open(OPF, "w")
    text_file.write("statistic,raster1,raster2,value" + "\n")

    # Write D and I values to standard output and optionally to text file
    i = 0
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
                             tmpf0=tmpf0,
                             nlay1=nlay1,
                             vsum1=vsum1,
                             nlay2=nlay2,
                             vsum2=vsum2,
                             quiet=True)
                NO = float(grass.parse_command("r.univar", quiet=True, flags="g", map=tmpf0)['sum'])
                NOV = 1 - (0.5 * NO)
                text_file.write("D," + nvar1 + "," + nvar2 + "," + str(NOV) + "\n")
                grass.message("Niche overlap (D) of " + nvar1 + " and " + nvar2 + ": " + str(round(NOV, 3)))

            ## Calculate I (Warren et al. 2008). Note that the sqrt in the
            # H formulation and the ^2 in the I formation  cancel each other out,
            # hence the formulation below.
            #=======================================================================

            if flag_i:
                tmpf1 = "rniche_" + str(uuid.uuid4())
                tmpf1 = string.replace(tmpf1, '-', '_')
                clean_rast.add(tmpf1)
                grass.mapcalc("$tmpf1 = (sqrt(double($nlay1)/$vsum1) - sqrt(double($nlay2)/$vsum2))^2",
                             tmpf1=tmpf1,
                             nlay1=nlay1,
                             vsum1=vsum1,
                             nlay2=nlay2,
                             vsum2=vsum2,
                             quiet=True)
                NE = float(grass.parse_command("r.univar", quiet=True, flags="g", map=tmpf1)['sum'])
                NEQ = 1 - (0.5 * NE)
                text_file.write("I," + nvar1 + "," + nvar2 + "," + str(NEQ) + "\n")
                grass.message("Niche overlap (I) of " + nvar1 + " and " + nvar2 + ": " + str(round(NEQ, 3)))

            ## Calculate correlation
            #=======================================================================

            if flag_c:
                corl = grass.read_command("r.covar", quiet=True, flags="r", map=(nlay1,nlay2))
                corl = corl.split('N = ')[1]
                corl = float(corl.split(' ')[1])
                text_file.write("corr," + nvar1 + "," + nvar2 + "," + str(corl) + "\n")
                grass.message("Correlation of " + nvar1 + " and " + nvar2 + ": " + str(round(corl, 3)))

            grass.message("--------------------------------------")
            j = j + 1
        i = i + 1

    text_file.close()

if __name__ == "__main__":
    options, flags = grass.parser()
    atexit.register(cleanup)
    sys.exit(main())












