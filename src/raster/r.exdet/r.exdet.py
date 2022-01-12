#!/usr/bin/env python


##############################################################################
#
# MODULE:       r.exdet
# AUTHOR(S):    paulo van Breugel <paulo at ecodiv.earth>
# PURPOSE:      Detection and quantification of novel environments, with
#               points / locations being novel because they are outside
#               the range of individual covariates (NT1) and points/locations
#               that are within the univariate range but constitute novel
#               combinations between covariates (NT2).
#               Based on Mesgaran et al.2014 [1]
#
# COPYRIGHT: (C) 2014-2017 by Paulo van Breugel and the GRASS Development Team
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
#% key: p
#% description: Most influential covariates (MIC)
#% guisection: Output
#%end

#%flag
#% key: d
#% label: Mahalanobis distance in projection domain?
#% description: Keep layer Mahalanobis distance in projection domain?
#%end

#%flag
#% key: e
#% label: Mahalanobis distance in reference domain
#% description: Keep layer Mahalanobis distance in reference domain?
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
from grass.pygrass.modules import Module
from subprocess import PIPE

# for Python 3 compatibility
try:
    xrange
except NameError:
    xrange = range

COLORS_EXDET = """\
0% 255:0:0
0 255:240:240
0.000001 240:255:240
1 0:128:0
1.000001 255:221:160
100% 219:65:0
"""

# Functions
CLEAN_LAY = []


def cleanup():
    """Remove temporary maps specified in the global list"""
    cleanrast = list(reversed(CLEAN_LAY))
    for rast in cleanrast:
        gs.run_command("g.remove", flags="f", type="all", name=rast, quiet=True)


def checkmask():
    """Check if there is a MASK set"""
    ffile = gs.find_file(name="MASK", element="cell", mapset=gs.gisenv()["MAPSET"])
    mask_presence = ffile["fullname"] != ""
    return mask_presence


def tmpname(prefix):
    """Generate a tmp name which contains prefix
    Store the name in the global list.
    Use only for raster maps.
    """
    tmpf = prefix + str(uuid.uuid4())
    tmpf = tmpf.replace("-", "_")
    CLEAN_LAY.append(tmpf)
    return tmpf


def CoVar(maps):
    """Compute the covariance matrix over reference layers"""
    tmpcov = tempfile.mkstemp()[1]
    with open(tmpcov, "w") as text_file:
        text_file.write(gs.read_command("r.covar", quiet=True, map=maps))
    covar = np.loadtxt(tmpcov, skiprows=1)
    os.remove(tmpcov)
    VI = np.linalg.inv(covar)
    return VI


def mahal(v, m, VI):
    """Compute the Mahalanobis distance over reference layers"""
    delta = v - m[:, None, None]
    mahdist = np.sum(
        np.sum(delta[None, :, :, :] * VI[:, :, None, None], axis=1) * delta, axis=0
    )
    stat_mahal = garray.array()
    stat_mahal[...] = mahdist
    return stat_mahal


def main(options, flags):

    gisbase = os.getenv("GISBASE")
    if not gisbase:
        gs.fatal(_("$GISBASE not defined"))
        return 0

    # Variables
    ref = options["reference"]
    REF = ref.split(",")
    pro = options["projection"]
    if pro:
        PRO = pro.split(",")
    else:
        PRO = REF
    opn = [z.split("@")[0] for z in PRO]
    out = options["output"]
    region = options["region"]
    flag_d = flags["d"]
    flag_e = flags["e"]
    flag_p = flags["p"]

    # get current region settings, to compare to new ones later
    regbu1 = tmpname("region")
    gs.parse_command("g.region", save=regbu1)

    # Check if region, projected layers or mask is given
    if region:
        ffile = gs.find_file(region, element="region")
        if not ffile:
            gs.fatal(_("the region {} does not exist").format(region))
    if not pro and not checkmask() and not region:
        gs.fatal(
            _(
                "You need to provide projected layers, a region, or "
                "a mask has to be set"
            )
        )
    if pro and len(REF) != len(PRO):
        gs.fatal(
            _(
                "The number of reference and projection layers need to "
                "be the same. Your provided %d reference and %d"
                "projection variables"
            )
            % (len(REF), len(PRO))
        )

    # Text for history in metadata
    opt2 = dict((k, v) for k, v in options.items() if v)
    hist = " ".join("{!s}={!r}".format(k, v) for (k, v) in opt2.items())
    hist = "r.exdet {}".format(hist)
    unused, tmphist = tempfile.mkstemp()
    with open(tmphist, "w") as text_file:
        text_file.write(hist)

    # Create covariance table
    VI = CoVar(maps=REF)

    # Import reference data & compute univar stats per reference layer
    s = len(REF)
    dat_ref = stat_mean = stat_min = stat_max = None

    for i, map in enumerate(REF):
        layer = garray.array(map, null=np.nan)
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

    # Compute Mahalanobis over full set of reference layers
    mahal_ref = mahal(v=dat_ref, m=stat_mean, VI=VI)
    mahal_ref_max = max(mahal_ref[np.isfinite(mahal_ref)])
    if flag_e:
        mahalref = "{}_mahalref".format(out)
        mahal_ref.write(mapname=mahalref)
        gs.info(_("Mahalanobis distance map saved: {}").format(mahalref))
        gs.run_command(
            "r.support",
            map=mahalref,
            title="Mahalanobis distance map",
            units="unitless",
            description="Mahalanobis distance map in reference " "domain",
            loadhistory=tmphist,
        )
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
    for i, map in enumerate(PRO):
        layer = garray.array(map, null=np.nan)
        r, c = layer.shape
        if dat_pro is None:
            dat_pro = np.empty((s, r, c), dtype=np.double)
        dat_pro[i, :, :] = layer
        del layer

    # Compute mahalanobis distance
    mahal_pro = mahal(v=dat_pro, m=stat_mean, VI=VI)
    if flag_d:
        mahalpro = "{}_mahalpro".format(out)
        mahal_pro.write(mapname=mahalpro)
        gs.info(_("Mahalanobis distance map saved: {}").format(mahalpro))
        gs.run_command(
            "r.support",
            map=mahalpro,
            title="Mahalanobis distance map projection domain",
            units="unitless",
            loadhistory=tmphist,
            description="Mahalanobis distance map in projection "
            "domain estimated using covariance of reference data",
        )

    # Compute NT1
    tmplay = tmpname(out)
    mnames = [None] * len(REF)
    for i in range(len(REF)):
        tmpout = tmpname("exdet")
        # TODO: computations below sometimes result in very small negative
        # numbers, which are not 'real', but rather due to some differences
        # in handling digits in grass and Python, hence second mapcalc
        # statement. Need to figure out how to handle this better.
        gs.mapcalc(
            "eval("
            "tmp = min(($prolay - $refmin), ($refmax - $prolay),0) / "
            "($refmax - $refmin))\n"
            "$Dij = if(tmp > -0.00000000001, 0, tmp)",
            Dij=tmpout,
            prolay=PRO[i],
            refmin=stat_min[i],
            refmax=stat_max[i],
            quiet=True,
        )
        mnames[i] = tmpout
    gs.run_command("r.series", quiet=True, input=mnames, output=tmplay, method="sum")

    # Compute most influential covariate (MIC) metric for NT1
    if flag_p:
        tmpla1 = tmpname(out)
        gs.run_command(
            "r.series", quiet=True, output=tmpla1, input=mnames, method="min_raster"
        )

    # Compute NT2
    tmpla2 = tmpname(out)
    nt2map = garray.array()
    nt2map[...] = mahal_pro / mahal_ref_max
    nt2map.write(mapname=tmpla2)

    # Compute  most influential covariate (MIC) metric for NT2
    if flag_p:
        tmpla3 = tmpname(out)
        laylist = []
        layer = garray.array()
        for i, map in enumerate(opn):
            gs.use_temp_region()
            gs.run_command("g.region", quiet=True, region=regbu1)
            REFtmp = [x for num, x in enumerate(REF) if not num == i]
            stattmp = np.delete(stat_mean, i, axis=0)
            VItmp = CoVar(maps=REFtmp)
            gs.del_temp_region()
            dat_protmp = np.delete(dat_pro, i, axis=0)
            ymap = mahal(v=dat_protmp, m=stattmp, VI=VItmp)
            # in Mesgaran et al, the MIC2 is the max icp, but that is the
            # same as the minimum Mahalanobis distance (ymap)
            # icp = (mahal_pro - ymap) / mahal_pro * 100
            layer[:, :] = ymap
            tmpmahal = tmpname(out)
            layer.write(tmpmahal)
            laylist.append(tmpmahal)
        gs.run_command(
            "r.series",
            quiet=True,
            output=tmpla3,
            input=laylist,
            method="min_raster",
            overwrite=True,
        )

    # Compute nt1, nt2, and nt1and2 novelty maps
    nt1 = "{}_NT1".format(out)
    nt2 = "{}_NT2".format(out)
    nt12 = "{}_NT1NT2".format(out)
    expr = ";".join(
        [
            "$nt12 = if($tmplay < 0, $tmplay, $tmpla2)",
            "$nt2 = if($tmplay >= 0, $tmpla2, null())",
            "$nt1 = if($tmplay < 0, $tmplay, null())",
        ]
    )
    gs.mapcalc(
        expr, nt12=nt12, nt1=nt1, nt2=nt2, tmplay=tmplay, tmpla2=tmpla2, quiet=True
    )

    # Write metadata nt1, nt2, nt1and2  maps
    gs.run_command(
        "r.support",
        map=nt1,
        units="unitless",
        title="Type 1 similarity",
        description="Type 1 similarity (NT1)",
        loadhistory=tmphist,
    )
    gs.run_command(
        "r.support",
        map=nt2,
        units="unitless",
        title="Type 2 similarity",
        description="Type 2 similarity (NT2)",
        loadhistory=tmphist,
    )
    gs.run_command(
        "r.support",
        map=nt12,
        units="unitless",
        title="Type 1 + 2 novelty / similarity",
        description="Type 1 + 2 similarity (NT1)",
        loadhistory=tmphist,
    )

    # Compute MIC maps
    if flag_p:
        mic12 = "{}_MICNT1and2".format(out)
        expr = "$mic12 = if($tmplay < 0, $tmpla1, " "if($tmpla2>1, $tmpla3, -1))"
        gs.mapcalc(
            expr,
            tmplay=tmplay,
            tmpla1=tmpla1,
            tmpla2=tmpla2,
            tmpla3=tmpla3,
            mic12=mic12,
            quiet=True,
        )

        # Write category labels to MIC maps
        tmpcat = tempfile.mkstemp()
        with open(tmpcat[1], "w") as text_file:
            text_file.write("-1:None\n")
            for cats in range(len(opn)):
                text_file.write("{}:{}\n".format(cats, opn[cats]))
        gs.run_command(
            "r.category", quiet=True, map=mic12, rules=tmpcat[1], separator=":"
        )
        os.remove(tmpcat[1])
        CATV = Module("r.category", map=mic12, stdout_=PIPE).outputs.stdout
        Module("r.category", map=mic12, rules="-", stdin_=CATV, quiet=True)
        gs.run_command(
            "r.support",
            map=mic12,
            units="unitless",
            title="Most influential covariate",
            description="Most influential covariate (MIC) for NT1" "and NT2",
            loadhistory=tmphist,
        )

    # Write color table
    gs.write_command("r.colors", map=nt12, rules="-", stdin=COLORS_EXDET, quiet=True)

    # Finalize
    gs.info(_("Done...."))


if __name__ == "__main__":
    atexit.register(cleanup)
    sys.exit(main(*gs.parser()))
