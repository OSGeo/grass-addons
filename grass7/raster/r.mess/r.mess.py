#!/usr/bin/env python
# -*- coding: utf-8 -*-

########################################################################
#
# MODULE:       r.mess
# AUTHOR(S):    Paulo van Breugel <p.vanbreugel AT gmail.com>
# PURPOSE:      Calculate the multivariate environmental similarity
#               surface (MESS) as proposed by Elith et al., 2010,
#               Methods in Ecology & Evolution, 1(330–342).
#
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
#% description: Computes multivariate environmental similarity surface
#% keyword: raster
#% keyword: modelling
#%End

#%option
#% key: ref_rast
#% type: string
#% gisprompt: old,cell,raster
#% description: Reference distribution as raster (1 = presence, 0 = absence)
#% label: Reference layer (raster)
#% key_desc: name
#% required: no
#% multiple: no
#% guisection: reference distribution
#%end

#%option
#% key: ref_vect
#% type: string
#% gisprompt: old,vector
#% description: Reference distribution as point vector layer
#% key_desc: name
#% required: no
#% multiple: no
#% guisection: reference distribution
#%end

#%rules
#%exclusive: ref_rast,ref_vect
#%end

#%option
#% key: env_old
#% type: string
#% gisprompt: old,cell,raster
#% description: Input (predictor) raster map(s)
#% key_desc: names
#% required: yes
#% multiple: yes
#% guisection: predictors
#%end

#%option
#% key: env_new
#% type: string
#% gisprompt: old,cell,raster
#% description: Input (predictor) raster map(s)
#% key_desc: names
#% required: no
#% multiple: yes
#% guisection: predictors
#%end

#%option
#% key: output
#% type: string
#% gisprompt: new,cell,raster
#% description: Root name of the output MESS data layers
#% key_desc: name
#% required: yes
#% guisection: Output
#%end

#%option
#% key: digits
#% type: integer
#% description: Precision of your input layers values
#% key_desc: string
#% answer: 3
#%end

#%flag
#% key: m
#% description: Calculate Most dissimilar variable (MoD)
#% guisection: Output
#%end

#%flag
#% key: n
#% description: Area with negative MESS
#% guisection: Output
#%end

#%flag
#% key: k
#% description: sum(IES), where IES < 0
#% guisection: Output
#%end

#%flag
#% key: c
#% description: Number of IES layers with values < 0
#% guisection: Output
#%end

##%flag
##% key: b
##% description: Only compute MESS for areas with novel conditions (faster)
##% guisection: Output
##%end

#%flag:  IES
#% key: i
#% description: Remove individual environmental similarity layers (IES)
#% guisection: Output
#%end

#%flag
#% key: r
#% description: Keep current region (otherwise set to match env_new)
#%end

#----------------------------------------------------------------------------
# Standard
#----------------------------------------------------------------------------

# import libraries
import os
import sys
import numpy as np
import uuid
import atexit
import tempfile
import operator
import string
import grass.script as grass
from grass.script import db as db

if not os.environ.has_key("GISBASE"):
    grass.message( "You must be in GRASS GIS to run this program." )
    sys.exit(1)

#----------------------------------------------------------------------------
# Functions
#----------------------------------------------------------------------------

# create set to store names of temporary maps to be deleted upon exit
clean_rast = set()
def cleanup():
    for rast in clean_rast:
        grass.run_command("g.remove", type=["rast", "region"], name = rast,
                          quiet = True, flags="f")

def CheckLayer(envlay):
    for chl in xrange(len(envlay)):
        ffile = grass.find_file(envlay[chl], element = 'cell')
        if ffile['fullname'] == '':
            grass.fatal("The layer " + envlay[chl] + " does not exist.")

# Create temporary name
def tmpname(name):
    tmpf = name + "_" + str(uuid.uuid4())
    tmpf = string.replace(tmpf, '-', '_')
    clean_rast.add(tmpf)
    return tmpf

#----------------------------------------------------------------------------
# main function
#----------------------------------------------------------------------------

def main():

    #----------------------------------------------------------------------------
    # Variables
    #----------------------------------------------------------------------------

    # reference layer
    REF_VECT = options['ref_vect']
    REF_RAST = options['ref_rast']
    if len(REF_VECT) == 0 and len(REF_RAST) == 0:
        grass.fatal("You did not provide the reference distribution layer")
    if len(REF_RAST) > 0:
        vtl = REF_RAST
        rtl = 'R'
    else:
        vtl = REF_VECT
        rtl = 'V'

    # old environmental layers & variable names
    ipl = options['env_old']
    ipl = ipl.split(',')
    CheckLayer(ipl)
    ipn = [z.split('@')[0] for z in ipl]
    ipn = [x.lower() for x in ipn]

    # new environmental variables
    ipl2 = options['env_new']
    if ipl2 == '':
        ipl_dif = False
        ipl2 = ipl
    else:
        ipl_dif = True
        ipl2 = ipl2.split(',')
        CheckLayer(ipl2)
        if len(ipl2) != len(ipl) and len(ipl2) != 0:
            msg = 'number of old and new environmental variables is not the same'
            grass.fatal(msg)

    # output layers
    opl = options['output']
    opc = opl + '_MESS'
    ipi = [opl + '_' + i for i in ipn]

    # flags
    flm = flags['m']
    flk = flags['k']
    fln = flags['n']
    fli = flags['i']
    flr = flags['r']
    fll = flags['c']
    #flb = flags['b']

    # digits / precision
    digits = int(options['digits'])
    digits2 = pow(10, digits)

    # Color table
    fd1, tmpcol = tempfile.mkstemp()
    text_file = open(tmpcol, "w")
    text_file.write("0% 244:109:67\n")
    text_file.write("0 255:255:210\n")
    text_file.write("100% 50:136:189\n")
    text_file.close()

    # Copy current region
    regionbackup = tmpname("mess_region_backup")
    grass.run_command("g.region", save=regionbackup)

    #----------------------------------------------------------------------------
    # Create the recode table - Reference distribution is raster
    #----------------------------------------------------------------------------

    if rtl=="R":

        # Copy mask (if there is one) to temporary layer
        citiam = grass.find_file(name='MASK', element = 'cell',
                                 mapset=grass.gisenv()['MAPSET'])
        if citiam['fullname'] != '':
            rname = tmpname('MASK')
            grass.mapcalc('$rname = MASK', rname=rname, quiet=True)

        # Create temporary layer based on reference layer
        tmpf0 = tmpname('rmess_tmp')
        grass.mapcalc("$tmpf0 = $vtl * 1", vtl = vtl, tmpf0=tmpf0, quiet=True)
        grass.run_command("r.null", map=tmpf0, setnull=0, quiet=True)

        # Remove mask
        if citiam['fullname'] != '':
            grass.run_command("r.mask", quiet=True, flags="r")

        for i in xrange(len(ipl)):

            # Create mask based on combined MASK/reference layer
            grass.run_command("r.mask", quiet=True, overwrite=True, raster=tmpf0)

            # Calculate the frequency distribution
            tmpf1 = tmpname('rmess_tmp1')
            grass.mapcalc("$tmpf1 = int($dignum * $inplay)", tmpf1=tmpf1,
                          inplay=ipl[i],
                          dignum=digits2,
                          quiet=True)
            p = grass.pipe_command('r.stats', quiet=True, flags = 'cn', input = tmpf1, sort = 'asc', sep=';')
            stval = {}
            for line in p.stdout:
                [val,count] = line.strip(os.linesep).split(';')
                stval[float(val)] = float(count)
            p.wait()
            sstval = sorted(stval.items(), key=operator.itemgetter(0))
            sstval = np.matrix(sstval)
            a = np.cumsum(np.array(sstval), axis=0)
            b = np.sum(np.array(sstval), axis=0)
            c = a[:,1] / b[1] * 100

            # Restore mask and set region to new env_new
            # Note: if region env_new is different from region env_old, setting
            # the mask will not do anything. If there is partial overlap, the mask
            # may affect the area where the two overlap
            if citiam['fullname'] != '':
                grass.run_command("r.mask", flags="r", quiet=True)
                grass.run_command("r.mask", raster=rname, quiet=True)
            else:
                grass.run_command("r.mask", quiet=True, flags="r")
            if ipl_dif and not flr:
                grass.run_command("g.region", quiet=True, raster=ipl2[0])

            # Get min and max values for recode table (based on full map)
            tmpf2 = tmpname('rmess_tmp2')
            grass.mapcalc("$tmpf2 = int($dignum * $inplay)",
                          tmpf2 = tmpf2,
                          inplay = ipl2[i],
                          dignum = digits2,
                          quiet=True)
            d = grass.parse_command("r.univar",quiet=True, flags="g", map=tmpf2)

            # Create recode rules
            Dmin = int(d['min'])
            Dmax = int(d['max'])
            envmin = np.min(np.array(sstval), axis=0)[0]
            envmax = np.max(np.array(sstval), axis=0)[0]

            if Dmin < envmin: e1 = Dmin - 1
            else: e1 = envmin -1
            if Dmax > envmax: e2 = Dmax + 1
            else: e2 = envmax + 1

            a1 = np.hstack([(e1), np.array(sstval.T[0])[0,:] ])
            a2 = np.hstack([np.array(sstval.T[0])[0,:] -1, (e2)])
            b1 = np.hstack([(0), c])

            fd2, tmprule = tempfile.mkstemp(suffix=ipn[i])
            text_file = open(tmprule, "w")
            for k in np.arange(0,len(b1.T)):
                rtmp = str(int(a1[k])) + ":" + str(int(a2[k])) + ":" + str(b1[k])
                text_file.write(rtmp + "\n")
            text_file.close()

            # Create the recode layer and calculate the IES
            tmpf3 = tmpname('rmess_tmp3')
            grass.run_command("r.recode", input=tmpf2, output=tmpf3, rules=tmprule)
            z1 = ipi[i] + " = if(" + tmpf3 + "==0, (float(" + tmpf2 + ")-" + str(float(envmin)) + ")/(" + str(float(envmax)) + "-" + str(float(envmin)) + ") * 100"
            z2 = ", if(" + tmpf3 + "<=50, 2*float(" + tmpf3 + ")"
            z3 = ", if(" + tmpf3 + "<100, 2*(100-float(" + tmpf3 + "))"
            z4 = ", (" + str(float(envmax)) + "- float(" + tmpf2 + "))/(" + str(float(envmax)) + "-" + str(float(envmin)) +  ") * 100.0)))"
            calcc = z1 + z2 + z3 + z4
            grass.mapcalc(calcc, quiet=True)
            grass.run_command("r.colors", quiet=True, map=ipi[i], rules=tmpcol)
            os.close(fd2)
            os.remove(tmprule)
            grass.run_command("g.region", quiet=True, region=regionbackup)

        if citiam['fullname'] != '':
            grass.mapcalc("MASK1 = 1 * MASK", overwrite=True)
            grass.run_command("r.mask", quiet=True, flags="r")
            grass.run_command("g.rename", raster=("MASK1","MASK"))

    #----------------------------------------------------------------------------
    # Create the recode table - Reference distribution is vector
    #----------------------------------------------------------------------------

    if rtl=="V":

        # Copy point layer and add columns for variables
        tmpf0 = tmpname('rmess_tmp0')
        grass.run_command("v.extract", quiet=True, flags="t", input=vtl, type="point", output=tmpf0)
        grass.run_command("v.db.addtable", quiet=True, map=tmpf0)

        # Upload raster values and get value in python as frequency table
        check_n = len(np.hstack(db.db_select(sql = "SELECT cat FROM " + tmpf0)))
        for m in xrange(len(ipl)):
            mid = str(m)
            laytype = grass.raster_info(ipl[m])['datatype']
            if laytype =='CELL':
                columns = "envvar" + mid + " integer"
            else:
                columns = "envvar" + mid + " double precision"
            grass.run_command("v.db.addcolumn", quiet=True, map=tmpf0, columns=columns)
            grass.run_command("db.execute" , quiet=True, sql = "UPDATE " + tmpf0 + " SET envvar" + mid + " = NULL")
            grass.run_command("v.what.rast", quiet=True, map=tmpf0, layer=1, raster=ipl[m], column="envvar" + mid)
            volval = np.vstack(db.db_select(sql = "SELECT envvar" + mid + ",count(envvar" + mid +") from " + tmpf0 +
                " WHERE envvar" + mid + " IS NOT NULL GROUP BY envvar" + mid + " ORDER BY envvar" + mid))
            volval = volval.astype(np.float, copy=False)
            a = np.cumsum(volval[:,1], axis=0)
            b = np.sum(volval[:,1], axis=0)
            c = a / b * 100

            # Check for point without values
            if b < check_n:
                 grass.info("Please note that there were " + str(check_n - b) + " points without value")
                 grass.info("This is probably because they lies outside the current region or input rasters")

            # Set region to env_new layers (if different from env_old)
            if ipl_dif and not flr:
                grass.run_command("g.region", quiet=True, raster=ipl2[0])

            # Multiply env layer with dignum
            tmpf2 = tmpname('rmess_tmp2')
            grass.mapcalc("$tmpf2 = int($dignum * $inplay)", tmpf2=tmpf2,
                          inplay=ipl[m],
                          dignum=digits2,
                          quiet=True)

            # Calculate min and max values of sample points and raster layer
            envmin = int(min(volval[:,0]) * digits2)
            envmax = int(max(volval[:,0]) * digits2)
            Drange = grass.read_command("r.info", flags="r", map=tmpf2)
            Drange = str.splitlines(Drange)
            Drange = np.hstack([i.split('=') for i in Drange])
            Dmin = int(Drange[1])
            Dmax = int(Drange[3])

            if Dmin < envmin: e1 = Dmin - 1
            else: e1 = envmin -1
            if Dmax > envmax: e2 = Dmax + 1
            else: e2 = envmax + 1

            a0 = volval[:,0] * digits2
            a0 = a0.astype(np.int, copy=False)
            a1 = np.hstack([(e1) , a0 ])
            a2 = np.hstack([a0 -1, (e2) ])
            b1 = np.hstack([(0), c])

            fd3, tmprule = tempfile.mkstemp(suffix=ipn[m])
            text_file = open(tmprule, "w")
            for k in np.arange(0,len(b1)):
                rtmp = str(int(a1[k])) + ":" + str(int(a2[k])) + ":" + str(b1[k])
                text_file.write(rtmp + "\n")
            text_file.close()

            # Create the recode layer and calculate the IES
            tmpf3 = tmpname('rmess_tmp3')
            grass.run_command("r.recode", quiet=True, input=tmpf2, output=tmpf3, rules=tmprule)

            z1 = ipi[m] + " = if(" + tmpf3 + "==0, (float(" + tmpf2 + ")-" + str(float(envmin)) + ")/(" + str(float(envmax)) + "-" + str(float(envmin)) + ") * 100"
            z2 = ", if(" + tmpf3 + "<=50, 2*float(" + tmpf3 + ")"
            z3 = ", if(" + tmpf3 + "<100, 2*(100-float(" + tmpf3 + "))"
            z4 = ", (" + str(float(envmax)) + "- float(" + tmpf2 + "))/(" + str(float(envmax)) + "-" + str(float(envmin)) +  ") * 100.0)))"
            calcc = z1 + z2 + z3 + z4
            grass.mapcalc(calcc, quiet=True)
            grass.run_command("r.colors", quiet=True, map=ipi[m], rules=tmpcol)

            # Clean up
            os.close(fd3)
            os.remove(tmprule)
            grass.run_command("g.region", quiet=True, region=regionbackup)

    #-----------------------------------------------------------------------
    # Calculate MESS statistics
    #-----------------------------------------------------------------------

    # MESS
    grass.run_command("r.series", quiet=True, output=opc, input=ipi, method="minimum")
    grass.run_command("r.colors", quiet=True, map=opc, rules=tmpcol)
    grass.message("\n")
    grass.message("The following layers were created:")
    grass.message("\n")
    grass.message("MES layer:       " + opc)

    # Area with negative MESS
    if fln:
        grass.mapcalc(opc + "_neg = if(" + opc + "<0,1,0)", quiet=True)

    # Most dissimilar variable (MoD)
    if flm:
        mod = opc + "_MoD"
        grass.run_command("r.series", quiet=True, output=mod, input=ipi, method="min_raster")
        fd4, tmpcat = tempfile.mkstemp()
        text_file = open(tmpcat, "w")
        for cats in xrange(len(ipi)):
            text_file.write(str(cats) + ":" + ipi[cats] + "\n")
        text_file.close()
        grass.run_command("r.category", quiet=True, map=mod, rules=tmpcat, separator=":")
        os.close(fd4)
        os.remove(tmpcat)
        grass.message("MoD layer:       " + mod)

    # sum(IES), where IES < 0
    if flk:
        mod = opc + "SumNeg"
        c0 = -0.01/digits2
        grass.run_command("r.series", quiet=True, input=ipi, output=mod, method="sum", range=('-inf',c0))
        grass.run_command("r.colors", quiet=True, map=mod, col="ryg")
        grass.message("Sum(IES):        " + mod)

    # Number of layers with negative values
    if fll:
        MinMes = grass.read_command("r.info", quiet=True, flags="r", map=opc)
        MinMes = str.splitlines(MinMes)
        MinMes = float(np.hstack([i.split('=') for i in MinMes])[1])
        mod = opc + "CountNeg"
        c0 = -0.0001/digits2
        grass.run_command("r.series", quiet=True, input=ipi, output=mod, method="count", range=(MinMes,c0))
        grass.run_command("r.colors", quiet=True, map=mod, col="ryg")
        grass.message("Count(layers<0): " + mod)
        grass.message("\n")

    # Remove IES layers
    if fli:
        grass.run_command("g.remove", quiet=True, flags="f", type="raster", name=ipi)

if __name__ == "__main__":
    options, flags = grass.parser()
    atexit.register(cleanup)
    sys.exit(main())
