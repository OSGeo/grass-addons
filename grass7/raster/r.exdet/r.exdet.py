#!/usr/bin/env python
# -*- coding: utf-8 -*-

##############################################################################
#
# MODULE:       r.exdet
# AUTHOR(S):    paulo van Breugel <paulo at ecodiv.org>
# PURPOSE:      Detection and quantification of novel environments, with
#               points / locations being novel because they are outside
#               the range of individual covariates (NT1) and points/locations
#               that are within the univariate range but constitute novel
#               combinations between covariates (NT2).
#               Based on Mesgaran et al.2014 [1]
#
# COPYRIGHT:    (C) 2015 Paulo van Breugel
#               http://ecodiv.org
#               http://pvanb.wordpress.com/
# NOTE:         Requires Numpy >= 1.8, GRASS >=7.0
#
#        This program is free software under the GNU General Public
#        License (>=v2). Read the file COPYING that comes with GRASS
#        for details.
##############################################################################

# [1] Mesgaran, M.B., Cousens, R.D. & Webber, B.L. (2014) Here be dragons: a
# tool for quantifying novelty due to covariate range and correlation change
# when projecting species distribution models. Diversity & Distributions,
# 20: 1147–1159, DOI: 10.1111/ddi.12209.

#%module
#% description: Detection and quantification of novel uni- and multi-variate environments
#% keywords: mahalanobis distance
#% keywords: novel environment
#% keywords: dissimilarity
#% keywords: similarity,
#%end

#%option
#% key: reference
#% type: string
#% gisprompt: old,cell,raster
#% description: Reference environmental raster layers
#% key_desc: raster
#% required: yes
#% multiple: yes
#% guisection: Input
#%end

#%option
#% key: projection
#% type: string
#% gisprompt: old,cell,raster
#% description: Projected environmental raster layers
#% key_desc: raster
#% required: yes
#% multiple: yes
#% guisection: Input
#%end

#%option
#% key: output
#% type: string
#% gisprompt: new,cell,raster
#% description: Output layer
#% key_desc: raster
#% required: yes
#% multiple: no
#% guisection: Output
#%end

#%option
#% key: region
#% type: string
#% gisprompt: new,region
#% description: Region defining the projected area
#% key_desc: region
#% required: no
#% multiple: no
#% guisection: Input
#%end

#%flag
#% key: o
#% description: Most influential covariate (MIC) for NT1
#% guisection: Output
#%end

## Not implemented yet
##%flag
##% key: p
##% description: Most influential covariate (MIC) for NT2
##% guisection: Output
##%end

#%flag
#% key: d
#% description: Keep layer mahalanobis distance?
#%end

#%flag
#% key: m
#% description: Restore mask?
#%end

#%flag
#% key: r
#% description: Restore region?
#%end

# Dependencies
# Numpy >= 1.8, Scipy, grass >= 7.0

#----------------------------------------------------------------------------
# Standard
#----------------------------------------------------------------------------

# import libraries
import os
import sys
import atexit
import numpy as np
import grass.script as grass
import grass.script.array as garray
import tempfile
import uuid
import string

if not os.environ.has_key("GISBASE"):
    grass.message("You must be in GRASS GIS to run this program.")
    sys.exit(1)

# create set to store names of temporary maps to be deleted upon exit
clean_rast = set()

def cleanup():
    for rast in clean_rast:
        grass.run_command("g.remove", type="rast", name=rast, quiet=True)

#----------------------------------------------------------------------------
# Functions
#----------------------------------------------------------------------------

def tmpname(name):
    tmpf = name + "_" + str(uuid.uuid4())
    tmpf = string.replace(tmpf, '-', '_')
    clean_rast.add(tmpf)
    return tmpf

def tmpregion():
    regionname = tmpname("mahal")
    k = 0
    ffile = grass.find_file(regionname, element = 'region',
                            mapset=grass.gisenv()['MAPSET'])
    while ffile['fullname'] != '':
        regionname = regionname + k
        k = k + 1
        ffile = grass.find_file(regionname, element = 'region',
                                mapset=grass.gisenv()['MAPSET'])
    grass.region(save=regionname)
    grass.run_command("g.region", save=regionname)
    return regionname

def tmpmask():
    maskname = tmpname("mask")
    k = 0
    ffile = grass.find_file(maskname, element = 'cell',
                            mapset=grass.gisenv()['MAPSET'])
    while ffile['fullname'] != '':
        maskname = maskname + k
        k = k + 1
        ffile = grass.find_file(maskname, element = 'cell',
                                mapset=grass.gisenv()['MAPSET'])
    return maskname

def checkmask():
    ffile = grass.find_file("MASK", element = 'cell',
                            mapset=grass.gisenv()['MAPSET'])
    mask_presence = ffile['fullname'] != ''
    return mask_presence

def icovar(input):
    tmpcov = tempfile.mkstemp()[1]
    text_file = open(tmpcov, "w")
    text_file.write(grass.read_command("r.covar", quiet=True, map=input))
    text_file.close()
    covar = np.loadtxt(tmpcov, skiprows=1)
    VI = np.linalg.inv(covar)
    os.remove(tmpcov)
    return VI

def mahal(v, m, VI):
    delta = v - m[:,None,None]
    mahdist = np.sum(np.sum(delta[None,:,:,:] * VI[:,:,None,None],axis=1) * delta, axis=0)
    stat_mahal = garray.array()
    stat_mahal[...] = mahdist
    return stat_mahal

def main():

    #----------------------------------------------------------------------------
    # Variables
    #----------------------------------------------------------------------------

    ref = options['reference']
    ref = ref.split(',')
    pro = options['projection']
    pro = pro.split(',')
    opn = [z.split('@')[0] for z in pro]
    opn = [x.lower() for x in opn]
    out = options['output']
    region = options['region']
    flag_r = flags['r']
    flag_m = flags['m']
    flag_d = flags['d']
    flag_o = flags['o']
    # flag_p = flags['p'] # not implemented yet

    if ref == pro and checkmask() == False and region == '':
        grass.warning("1) reference and projected layers are the same, 2) you \
        did not define a mask, 3) and you did not define a region to delimit \
        the region for projection. Was that intentional?")

    if len(ref) != len(pro):
        grass.fatal("the number of reference and test layers should be the same")

    # Create covariance table
    VI = icovar(input=ref)

    #----------------------------------------------------------------------------
    # Import reference data & compute univar stats per reference layer
    #----------------------------------------------------------------------------
    s = len(ref)
    dat_ref = stat_mean = stat_min = stat_max = None
    layer = garray.array()

    for i, map in enumerate(ref):
        layer.read(map, null=np.nan)
        r, c = layer.shape
        if dat_ref is None:
            dat_ref = np.empty((s, r, c), dtype=np.double)
        if stat_mean is None:
            stat_mean = np.empty((s), dtype=np.double)
        if stat_min is None:
            stat_min = np.empty((s), dtype=np.double)
        if stat_max is None:
            stat_max = np.empty((s), dtype=np.double)
        stat_min[i] = np.nanmin(layer)
        stat_mean[i] = np.nanmean(layer)
        stat_max[i] = np.nanmax(layer)
        dat_ref[i,:,:] = layer
    del layer

    #----------------------------------------------------------------------------
    # Compute mahalanobis over reference layers
    #----------------------------------------------------------------------------

    # Compute mahalanobis over full set of layers
    mahal_ref = mahal(v=dat_ref, m=stat_mean, VI=VI)
    mahal_ref_max = max(mahal_ref[np.isfinite(mahal_ref)])
    del mahal_ref

    #----------------------------------------------------------------------------
    # Compute mahalanobis over projected layers
    #----------------------------------------------------------------------------

    # Remove mask (and optionally backup the MASK)
    if checkmask():
        if flag_m:
            mask_backup = tmpmask()
            grass.mapcalc("$mask = MASK", mask=mask_backup, quiet=True)
        grass.run_command("r.mask", flags="r")

    # Make backup of region if required
    if flag_r:
        region_backup = tmpregion()

    # Set new region based on user-defined region or otherwise based on
    # projected layers
    if region != '':
        ffile = grass.find_file(region, element = 'region',
                                mapset=grass.gisenv()['MAPSET'])
        if ffile != '':
            grass.run_command("g.region", region=region)
            grass.info("Region is set to the region. Please note that the function" + region)
            grass.info("does not check if projected layers fall within this region")
        else:
            grass.fatal("the region you selected does not exist")
    else:
        grass.run_command("g.region", raster=pro[0])
    if flag_r:
        grass.info("The original region was saved as " + region_backup)

    # Import projected layers
    s = len(pro)
    dat_pro = None
    layer = garray.array()
    for i, map in enumerate(pro):
        layer.read(map, null=np.nan)
        s = len(pro)
        r, c = layer.shape
        if dat_pro is None:
            dat_pro = np.empty((s, r, c), dtype=np.double)
        dat_pro[i,:,:] = layer
    del layer

    # Compute mahalanobis distance
    mahal_pro = mahal(v=dat_pro, m=stat_mean, VI=VI)
    if flag_d:
        mapname = out + "_mahalanobis"
        mahal_pro.write(mapname=mapname)
        grass.info("Mahalanobis distance map saved: " + mapname)

    #----------------------------------------------------------------------------
    # Compute NT2
    #----------------------------------------------------------------------------
    nt2map = garray.array()
    nt2map[...] = mahal_pro / mahal_ref_max
    nt2 = out + "_NT2"
    clean_rast.add(nt2)
    nt2map.write(mapname=nt2)

    #----------------------------------------------------------------------------
    # Compute NT1
    #----------------------------------------------------------------------------

    tmplay = tmpname(out)
    mnames = [None] * len(ref)
    for i in xrange(len(ref)):
        tmpout = out + "_" + opn[i]
        clean_rast.add(tmpout)
        grass.mapcalc("$Dij = min(($prolay - $refmin), ($refmax - $prolay), 0) / ($refmax - $refmin)",
                      Dij=tmpout,
                      prolay=pro[i],
                      refmin=stat_min[i],
                      refmax=stat_max[i],
                      quiet=True)
        mnames[i] = tmpout
    nt1 = out + "_NT1"
    grass.run_command("r.series", quiet=True, input=mnames, output=nt1, method="sum")

    #----------------------------------------------------------------------------
    # Compute exdet novelty map
    #----------------------------------------------------------------------------

    grass.mapcalc("$final = if($nt1<0,$nt1,$nt2)",
                      final=out,
                      nt1=nt1,
                      nt2=nt2,
                      quiet=True, overwrite=True)

    # Color table
    tmpcol = tempfile.mkstemp()
    text_file = open(tmpcol[1], "w")
    text_file.write("0% 255:0:0\n")
    text_file.write("0 255:200:200\n")
    text_file.write("0.000001 200:255:200\n")
    text_file.write("1 50:210:150\n")
    text_file.write("1.000001 200:200:255\n")
    text_file.write("100% 0:0:255\n")
    text_file.close()
    grass.run_command("r.colors", quiet=True, map=out, rules=tmpcol[1])
    os.remove(tmpcol[1])

#----------------------------------------------------------------------------
    # Compute  most influential covariate (MIC) metric for NT1
    #----------------------------------------------------------------------------

    if flag_o:
        mod = out + "_MIC1"
        grass.run_command("r.series", quiet=True, output=mod, input=mnames, method="min_raster")
        tmpcat = tempfile.mkstemp()
        text_file = open(tmpcat[1], "w")
        for cats in xrange(len(opn)):
            text_file.write(str(cats) + ":" + opn[cats] + "\n")
        text_file.close()
        grass.run_command("r.category", quiet=True, map=mod, rules=tmpcat[1], separator=":")
        os.remove(tmpcat[1])

    #----------------------------------------------------------------------------
    # Compute  most influential covariate (MIC) metric for NT2
    # Not implemented yet
    #----------------------------------------------------------------------------

#    if flag_p:
#        laylist = []
#        layer = garray.array()
#        # compute ICp values
#        for i, map in enumerate(pro):
#            VItmp = array(VI)
#            VItmp[:,i] = 0
#            VItmp[i,:] = 0
#            ymap = mahal(v=dat_pro, m=stat_mean, VI=VItmp)
#            icp = (mahal_pro - ymap) / mahal_pro * 100
#            layer[:,:] = icp
#            layer.write(mapname=out + "_icp_" + opn[i])
#            laylist.append(out + "_icp_" + opn[i])
#        # Combine ICp layers
#        icpname = out + "_MIC2"
#        icptemp = tmpname(name="icp")
#        grass.run_command("r.series", quiet=True, output=icptemp,
#                          input=laylist, method="max_raster")
#        # ICp values apply only to parts where NT2 > 1 and NT1 = 0
#        grass.mapcalc("$icpname = if($nt1<0,-888,if($nt2>1,$icptemp,-999))",
#                      nt1=nt1, nt2=nt2, icpname=icpname, icptemp=icptemp,
#                      quiet=True)
#        # Write categories
#        tmpcat = tempfile.mkstemp()
#        text_file = open(tmpcat[1], "w")
#        text_file.write(str(-999) + ":None\n")
#        text_file.write(str(-888) + ":NT1 range\n")
#        for cats in xrange(len(opn)):
#           text_file.write(str(cats) + ":" + opn[cats] + "\n")
#        text_file.close()
#        grass.run_command("r.category", quiet=True, map=icpname,
#                          rules=tmpcat[1], separator=":")
#        os.remove(tmpcat[1])
#        grass.run_command("g.remove", quiet=True, type="raster", name=icptemp, flags="f")

    #=======================================================================
    ## Clean up
    #=======================================================================

    grass.run_command("g.remove", type="raster", flags="f",
                      quiet=True, pattern=tmplay + "*")
    grass.run_command("g.remove", quiet=True, type="raster",
                      name=mnames, flags="f")
    if flag_m:
        grass.run_command("g.rename", raster=[mask_backup,"MASK"])
        grass.info("Note, the original mask was restored")

    grass.info("Done....")
    if flag_r:
        grass.info("Original region is restored")
    else:
        grass.info("Region is set to match the projected/test layers")


if __name__ == "__main__":
    options, flags = grass.parser()
    atexit.register(cleanup)
    sys.exit(main())




















