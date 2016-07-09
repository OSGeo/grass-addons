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
# COPYRIGHT: (C) 2014-2016 by Paulo van Breugel and the GRASS Development Team
#
#        This program is free software under the GNU General Public
#        License (>=v2). Read the file COPYING that comes with GRASS
#        for details.
##############################################################################

#%module
#% description: Quantification of novel uni- and multi-variate environments
#% keyword: similarity
#% keyword: multivariate
#% keyword: raster
#% keyword: modelling
#%end

#%option G_OPT_R_INPUTS
#% key: reference
#% label: Reference conditions
#% description: Reference environmental conditions
#% key_desc: raster
#% required: yes
#% multiple: yes
#% guisection: Input
#%end

#%option G_OPT_R_INPUTS
#% key: projection
#% label: Projected conditions
#% description: Projected conditions to be compared to reference conditions
#% key_desc: raster
#% required: no
#% multiple: yes
#% guisection: Input
#%end

#%option
#% key: region
#% type: string
#% gisprompt: new,region
#% label: Projection region
#% description: Region defining the area to be compared to the reference area
#% key_desc: region
#% required: no
#% multiple: no
#% guisection: Input
#%end

#%rules
#%exclusive: projection,region
#%end

#%option G_OPT_R_BASENAME_OUTPUT
#% key: output
#% label: Suffix name output layers
#% description: Root name of the output layers
#% key_desc: raster
#% required: yes
#% multiple: no
#% guisection: Output
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

# import libraries
import os
import sys
import atexit
import numpy as np
import grass.script as gs
import grass.script.array as garray
import tempfile
import uuid
import string

COLORS_EXDET = """\
0% 255:0:0
0 255:200:200
0.000001 200:255:200
1.000001 200:200:255
100% 0:0:255
"""

# Functions
CLEAN_LAY = []


def cleanup():
    """Remove temporary maps specified in the global list"""
    cleanrast = list(reversed(CLEAN_LAY))
    for rast in cleanrast:
        gs.run_command("g.remove", flags="f", type="all",
                       name=rast, quiet=True)


def checkmask():
    """Check if there is a MASK set"""
    ffile = gs.find_file(name="MASK", element="cell",
                         mapset=gs.gisenv()['MAPSET'])
    mask_presence = ffile['fullname'] != ''
    return mask_presence


def tmpname(prefix):
    """Generate a tmp name which contains prefix
    Store the name in the global list.
    Use only for raster maps.
    """
    tmpf = prefix + str(uuid.uuid4())
    tmpf = string.replace(tmpf, '-', '_')
    CLEAN_LAY.append(tmpf)
    return tmpf


def mahal(v, m, VI):
    """Compute the mahalanobis distance over reference layers"""
    delta = v - m[:, None, None]
    mahdist = np.sum(np.sum(delta[None, :, :, :] *
                     VI[:, :, None, None], axis=1) * delta, axis=0)
    stat_mahal = garray.array()
    stat_mahal[...] = mahdist
    return stat_mahal


def main(options, flags):

    gisbase = os.getenv('GISBASE')
    if not gisbase:
        gs.fatal(_('$GISBASE not defined'))
        return 0

    # Variables
    ref = options['reference']
    REF = ref.split(',')
    pro = options['projection']
    if pro:
        PRO = pro.split(',')
    else:
        PRO = REF
    opn = [z.split('@')[0] for z in PRO]
    opn = [x.lower() for x in opn]
    out = options['output']
    region = options['region']
    flag_d = flags['d']
    flag_o = flags['o']
    #TODO: flag_p = flags['p']

    if region:
        ffile = gs.find_file(region, element="region")
        if not ffile:
            gs.fatal(_("the region {} does not exist").format(region))
    if not pro and not checkmask() and not region:
        gs.fatal(_("You need to provide projected layers, a region, or "
                   "a mask has to be set"))
    if pro and len(REF) != len(PRO):
        gs.fatal(_("The number of reference and projection layers need to "
                   "be the same. Your provided %d reference and %d"
                   "projection variables") % (len(REF), len(PRO)))

    # Text for history in metadata
    opt2 = dict((k, v) for k, v in options.iteritems() if v)
    hist = ' '.join("{!s}={!r}".format(k, v) for (k, v) in opt2.iteritems())
    hist = "r.exdet {}".format(hist)
    unused, tmphist = tempfile.mkstemp()
    text_file = open(tmphist, "w")
    text_file.write(hist)
    text_file.close()

    # Create covariance table
    tmpcov = tempfile.mkstemp()[1]
    text_file = open(tmpcov, "w")
    text_file.write(gs.read_command("r.covar", quiet=True, map=REF))
    text_file.close()
    covar = np.loadtxt(tmpcov, skiprows=1)
    VI = np.linalg.inv(covar)
    os.remove(tmpcov)

    # Import reference data & compute univar stats per reference layer
    s = len(REF)
    dat_ref = stat_mean = stat_min = stat_max = None
    layer = garray.array()

    for i, map in enumerate(REF):
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
        dat_ref[i, :, :] = layer
    del layer

    # Compute mahalanobis over full set of reference layers
    mahal_ref = mahal(v=dat_ref, m=stat_mean, VI=VI)
    mahal_ref_max = max(mahal_ref[np.isfinite(mahal_ref)])
    del mahal_ref

    # Remove mask and set new region based on user-defined region or
    # otherwise based on projection layers
    if checkmask():
        gs.run_command("r.mask", flags="r")
    if region:
        gs.run_command("g.region", region=region)
        gs.info(_("The region has set to the region {}").format(region))
    if pro:
        gs.run_command("g.region", raster=PRO[0])
        # TODO: only set region to PRO[0] when different from current region
        gs.info(_("The region has set to match the proj raster layers"))

    # Import projected layers in numpy array
    s = len(PRO)
    dat_pro = None
    layer = garray.array()
    for i, map in enumerate(PRO):
        layer.read(map, null=np.nan)
        r, c = layer.shape
        if dat_pro is None:
            dat_pro = np.empty((s, r, c), dtype=np.double)
        dat_pro[i, :, :] = layer
    del layer

    # Compute mahalanobis distance
    mahal_pro = mahal(v=dat_pro, m=stat_mean, VI=VI)
    if flag_d:
        mapname = "{}_mahalanobis".format(out)
        mahal_pro.write(mapname=mapname)
        gs.info(_("Mahalanobis distance map saved: {}").format(mapname))
        gs.run_command("r.support", map=mapname,
                       title="Mahalanobis distance map", units="unitless",
                       description="Mahalanobis distance map",
                       loadhistory=tmphist)

    # Compute NT2
    nt2map = garray.array()
    nt2map[...] = mahal_pro / mahal_ref_max
    nt2 = "{}_NT2".format(out)
    nt2map.write(mapname=nt2)
    gs.run_command("r.support", map=nt2, units="unitless",
                   title="Type 2 similarity",
                   description="Type 2 similarity (NT2)",
                   loadhistory=tmphist)

    # Compute NT1
    tmplay = tmpname(out)
    mnames = [None] * len(REF)
    for i in xrange(len(REF)):
        tmpout = tmpname("exdet")
        gs.mapcalc("$Dij = min(($prolay - $refmin), ($refmax - $prolay),"
                   "0) / ($refmax - $refmin)", Dij=tmpout, prolay=PRO[i],
                   refmin=stat_min[i], refmax=stat_max[i], quiet=True)
        mnames[i] = tmpout
    nt1 = "{}_NT1".format(out)
    gs.run_command("r.series", quiet=True, input=mnames, output=nt1,
                   method="sum")
    gs.run_command("r.support", map=nt1, units="unitless",
                   title="Type 1 similarity",
                   description="Type 1 similarity (NT1)",
                   loadhistory=tmphist)

    # Compute exdet novelty map
    novelty = "{}_NT1NT2".format(out)
    gs.mapcalc("$final = if($nt1<0,$nt1,$nt2)", final=novelty,
               nt1=nt1, nt2=nt2, quiet=True, overwrite=True)
    gs.run_command("r.support", map=novelty, units="unitless",
                   title="Type 1 + 2 novelty / similarity",
                   description="Type 1 + 2 similarity (NT1)",
                   loadhistory=tmphist)

    # Color table
    gs.write_command("r.colors", map=novelty, rules='-', stdin=COLORS_EXDET,
                     quiet=True)

    # Compute most influential covariate (MIC) metric for NT1
    # TODO: compute MIC for NT2 as well (see email exchange with authors
    # exdet program about deviating results)
    if flag_o:
        mod = "{}_MICNT1".format(out)
        gs.run_command("r.series", quiet=True, output=mod, input=mnames,
                       method="min_raster")
        tmpcat = tempfile.mkstemp()
        text_file = open(tmpcat[1], "w")
        for cats in xrange(len(opn)):
            text_file.write("{}:{}\n".format(cats, opn[cats]))
        text_file.close()
        gs.run_command("r.category", quiet=True, map=mod, rules=tmpcat[1],
                       separator=":")
        os.remove(tmpcat[1])
        gs.run_command("r.support", map=mod, units="unitless",
                       title="MIC for NT1",
                       description="Most influential covariate for NT1",
                       loadhistory=tmphist)

    # Finalize
    gs.info(_("Done...."))

if __name__ == "__main__":
    atexit.register(cleanup)
    sys.exit(main(*gs.parser()))
