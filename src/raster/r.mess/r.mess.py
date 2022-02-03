#!/usr/bin/env python


########################################################################
#
# MODULE:       r.mess
# AUTHOR(S):    Paulo van Breugel <paulo ecodiv earth>
# PURPOSE:      Calculate the multivariate environmental similarity
#               surface (MESS) as proposed by Elith et al., 2010,
#               Methods in Ecology & Evolution, 1(330–342).
#
# COPYRIGHT: (C) 2014-2017 by Paulo van Breugel and the GRASS Development Team
#
#            This program is free software under the GNU General Public
#            License (>=v2). Read the file COPYING that comes with GRASS
#            for details.
#
########################################################################
#
# %Module
# % description: Computes multivariate environmental similarity surface (MES)
# % keyword: similarity
# % keyword: raster
# % keyword: modelling
# %End

# %option G_OPT_R_INPUTS
# % key: env
# % description: Reference conditions
# % key_desc: names
# % required: yes
# % guisection: Input
# %end

# %option G_OPT_R_INPUTS
# % key: env_proj
# % description: Projected conditions
# % key_desc: names
# % required: no
# % guisection: Input
# %end

# %option G_OPT_R_INPUT
# % key: ref_rast
# % label: Reference area (raster)
# % description: Reference areas (1 = presence, 0 or null = absence)
# % key_desc: name
# % required: no
# % guisection: Input
# %end

# %option G_OPT_V_MAP
# % key: ref_vect
# % label: Reference points (vector)
# % description: Point vector layer with presence locations
# % key_desc: name
# % required: no
# % guisection: Input
# %end

# %rules
# %exclusive: ref_rast,ref_vect
# %end

# %option G_OPT_R_BASENAME_OUTPUT
# % description: Root name of the output MESS data layers
# % key_desc: name
# % required: yes
# % guisection: Output
# %end

# %option
# % key: digits
# % type: integer
# % description: Precision of your input layers values
# % key_desc: string
# % answer: 3
# %end

# %flag
# % key: m
# % description: Calculate Most dissimilar variable (MoD)
# % guisection: Output
# %end

# %flag
# % key: n
# % description: Area with negative MESS
# % guisection: Output
# %end

# %flag
# % key: k
# % description: sum(IES), where IES < 0
# % guisection: Output
# %end

# %flag
# % key: c
# % description: Number of IES layers with values < 0
# % guisection: Output
# %end

# %flag:  IES
# % key: i
# % description: Remove individual environmental similarity layers (IES)
# % guisection: Output
# %end

# import libraries
import os
import sys
import numpy as np
import uuid
import atexit
import tempfile
import operator
import string
import grass.script as gs
from grass.script import db as db

# for Python 3 compatibility
try:
    xrange
except NameError:
    xrange = range

COLORS_MES = """\
0% 244:109:67
0 255:255:210
100% 50:136:189
"""

RECL_MESNEG = """\
0\twithin range
1\tnovel conditions
"""

# ----------------------------------------------------------------------------
# Functions
# ----------------------------------------------------------------------------

# create set to store names of temporary maps to be deleted upon exit
CLEAN_RAST = []


def cleanup():
    """Remove temporary maps specified in the global list"""
    cleanrast = list(reversed(CLEAN_RAST))
    for rast in cleanrast:
        gs.run_command("g.remove", flags="f", type="all", name=rast, quiet=True)


def raster_exists(envlay):
    """Check if the raster map exists, call GRASS fatal otherwise"""
    for chl in xrange(len(envlay)):
        ffile = gs.find_file(envlay[chl], element="cell")
        if not ffile["fullname"]:
            gs.fatal(_("The layer {} does not exist".format(envlay[chl])))


# Create temporary name
def tmpname(prefix):
    """Generate a tmp name which contains prefix
    Store the name in the global list.
    Use only for raster maps.
    """
    tmpf = prefix + str(uuid.uuid4())
    tmpf = string.replace(tmpf, "-", "_")
    CLEAN_RAST.append(tmpf)
    return tmpf


def compute_ies(INtmprule, INipi, INtmpf2, INenvmin, INenvmax):
    """
    Compute the environmental similarity layer for the individual variables
    """
    tmpf3 = tmpname("tmp6")
    gs.run_command("r.recode", input=INtmpf2, output=tmpf3, rules=INtmprule)

    calcc = (
        "{0} = if({1} == 0, (float({2}) - {3}) / ({4} - {3}) "
        "* 100.0, if({1} <= 50, 2 * float({1}), "
        "if({1} < 100, 2*(100-float({1})), "
        "({4} - float({2})) / ({4} - {3}) * 100.0)))".format(
            INipi, tmpf3, INtmpf2, float(INenvmin), float(INenvmax)
        )
    )
    gs.mapcalc(calcc, quiet=True)
    gs.write_command("r.colors", map=INipi, rules="-", stdin=COLORS_MES, quiet=True)


def main(options, flags):

    gisbase = os.getenv("GISBASE")
    if not gisbase:
        gs.fatal(_("$GISBASE not defined"))
        return 0

    # Reference / sample area or points
    ref_rast = options["ref_rast"]
    ref_vect = options["ref_vect"]
    if ref_rast:
        reftype = gs.raster_info(ref_rast)
        if reftype["datatype"] != "CELL":
            gs.fatal(_("The ref_rast map must have type CELL (integer)"))
        if (reftype["min"] != 0 and reftype["min"] != 1) or reftype["max"] != 1:
            gs.fatal(
                _(
                    "The ref_rast map must be a binary raster,"
                    " i.e. it should contain only values 0 and 1 or 1 only"
                    " (now the minimum is {} and maximum is {})".format(
                        reftype["min"], reftype["max"]
                    )
                )
            )

    # old environmental layers & variable names
    REF = options["env"]
    REF = REF.split(",")
    raster_exists(REF)
    ipn = [z.split("@")[0] for z in REF]
    ipn = [x.lower() for x in ipn]

    # new environmental variables
    PROJ = options["env_proj"]
    if not PROJ:
        RP = False
        PROJ = REF
    else:
        RP = True
        PROJ = PROJ.split(",")
        raster_exists(PROJ)
        if len(PROJ) != len(REF) and len(PROJ) != 0:
            gs.fatal(
                _(
                    "The number of reference and predictor variables"
                    " should be the same. You provided {} reference and {}"
                    " projection variables".format(len(REF), len(PROJ))
                )
            )

    # output layers
    opl = options["output"]
    opc = opl + "_MES"
    ipi = [opl + "_" + i for i in ipn]

    # flags
    flm = flags["m"]
    flk = flags["k"]
    fln = flags["n"]
    fli = flags["i"]
    flc = flags["c"]

    # digits / precision
    digits = int(options["digits"])
    digits2 = pow(10, digits)

    # get current region settings, to compare to new ones later
    region_1 = gs.parse_command("g.region", flags="g")

    # Text for history in metadata
    opt2 = dict((k, v) for k, v in options.iteritems() if v)
    hist = " ".join("{!s}={!r}".format(k, v) for (k, v) in opt2.iteritems())
    hist = "r.mess {}".format(hist)
    unused, tmphist = tempfile.mkstemp()
    with open(tmphist, "w") as text_file:
        text_file.write(hist)

    # Create reference layer if not defined
    if not ref_rast and not ref_vect:
        ref_rast = tmpname("tmp0")
        gs.mapcalc("$i = if(isnull($r),null(),1)", i=ref_rast, r=REF[0], quiet=True)

    # Create the recode table - Reference distribution is raster
    citiam = gs.find_file(name="MASK", element="cell", mapset=gs.gisenv()["MAPSET"])
    if citiam["fullname"]:
        rname = tmpname("tmp3")
        gs.mapcalc("$rname = MASK", rname=rname, quiet=True)

    if ref_rast:
        vtl = ref_rast

        # Create temporary layer based on reference layer
        tmpf0 = tmpname("tmp2")
        gs.mapcalc("$tmpf0 = int($vtl * 1)", vtl=vtl, tmpf0=tmpf0, quiet=True)
        gs.run_command("r.null", map=tmpf0, setnull=0, quiet=True)
        if citiam["fullname"]:
            gs.run_command("r.mask", flags="r", quiet=True)
        for i in xrange(len(REF)):

            # Create mask based on combined MASK/reference layer
            gs.run_command("r.mask", raster=tmpf0, quiet=True)

            # Calculate the frequency distribution
            tmpf1 = tmpname("tmp4")
            gs.mapcalc(
                "$tmpf1 = int($dignum * $inplay)",
                tmpf1=tmpf1,
                inplay=REF[i],
                dignum=digits2,
                quiet=True,
            )
            p = gs.pipe_command(
                "r.stats", quiet=True, flags="cn", input=tmpf1, sort="asc", sep=";"
            )
            stval = {}
            for line in p.stdout:
                [val, count] = line.strip(os.linesep).split(";")
                stval[float(val)] = float(count)
            p.wait()
            sstval = sorted(stval.items(), key=operator.itemgetter(0))
            sstval = np.matrix(sstval)
            a = np.cumsum(np.array(sstval), axis=0)
            b = np.sum(np.array(sstval), axis=0)
            c = a[:, 1] / b[1] * 100

            # Remove tmp mask and set region to env_proj if needed
            gs.run_command("r.mask", quiet=True, flags="r")
            if RP:
                gs.use_temp_region()
                gs.run_command("g.region", quiet=True, raster=PROJ[0])

            # get new region settings, to compare to original ones later
            region_2 = gs.parse_command("g.region", flags="g")

            # Get min and max values for recode table (based on full map)
            tmpf2 = tmpname("tmp5")
            gs.mapcalc(
                "$tmpf2 = int($dignum * $inplay)",
                tmpf2=tmpf2,
                inplay=PROJ[i],
                dignum=digits2,
                quiet=True,
            )
            d = gs.parse_command("r.univar", flags="g", map=tmpf2, quiet=True)

            # Create recode rules
            Dmin = int(d["min"])
            Dmax = int(d["max"])
            envmin = np.min(np.array(sstval), axis=0)[0]
            envmax = np.max(np.array(sstval), axis=0)[0]

            if Dmin < envmin:
                e1 = Dmin - 1
            else:
                e1 = envmin - 1
            if Dmax > envmax:
                e2 = Dmax + 1
            else:
                e2 = envmax + 1

            a1 = np.hstack([(e1), np.array(sstval.T[0])[0, :]])
            a2 = np.hstack([np.array(sstval.T[0])[0, :] - 1, (e2)])
            b1 = np.hstack([(0), c])

            fd2, tmprule = tempfile.mkstemp(suffix=ipn[i])
            with open(tmprule, "w") as text_file:
                for k in np.arange(0, len(b1.T)):
                    text_file.write(
                        "%s:%s:%s\n" % (str(int(a1[k])), str(int(a2[k])), str(b1[k]))
                    )

            # Create the recode layer and calculate the IES
            compute_ies(tmprule, ipi[i], tmpf2, envmin, envmax)
            gs.run_command(
                "r.support",
                map=ipi[i],
                title="IES {}".format(REF[i]),
                units="0-100 (relative score",
                description="Environmental similarity {}".format(REF[i]),
                loadhistory=tmphist,
            )

            # Clean up
            os.close(fd2)
            os.remove(tmprule)

            # Change region back to original
            gs.del_temp_region()

    # Create the recode table - Reference distribution is vector
    else:
        vtl = ref_vect

        # Copy point layer and add columns for variables
        tmpf0 = tmpname("tmp7")
        gs.run_command(
            "v.extract", quiet=True, flags="t", input=vtl, type="point", output=tmpf0
        )
        gs.run_command("v.db.addtable", quiet=True, map=tmpf0)

        # TODO: see if there is a more efficient way to handle the mask
        if citiam["fullname"]:
            gs.run_command("r.mask", quiet=True, flags="r")

        # Upload raster values and get value in python as frequency table
        sql1 = "SELECT cat FROM {}".format(str(tmpf0))
        cn = len(np.hstack(db.db_select(sql=sql1)))
        for m in xrange(len(REF)):

            # Set mask back (this means that points outside the mask will
            # be ignored in the computation of the frequency distribution
            # of the reference variabele env(m))
            if citiam["fullname"]:
                gs.run_command("g.copy", raster=[rname, "MASK"], quiet=True)

            # Compute frequency distribution of variable(m)
            mid = str(m)
            laytype = gs.raster_info(REF[m])["datatype"]
            if laytype == "CELL":
                columns = "envvar_{} integer".format(str(mid))
            else:
                columns = "envvar_%s double precision" % mid
            gs.run_command("v.db.addcolumn", map=tmpf0, columns=columns, quiet=True)
            sql2 = "UPDATE {} SET envvar_{} = NULL".format(str(tmpf0), str(mid))
            gs.run_command("db.execute", sql=sql2, quiet=True)
            coln = "envvar_%s" % mid
            gs.run_command(
                "v.what.rast",
                quiet=True,
                map=tmpf0,
                layer=1,
                raster=REF[m],
                column=coln,
            )
            sql3 = (
                "SELECT {0}, count({0}) from {1} WHERE {0} IS NOT NULL "
                "GROUP BY {0} ORDER BY {0}"
            ).format(coln, tmpf0)
            volval = np.vstack(db.db_select(sql=sql3))
            volval = volval.astype(np.float, copy=False)
            a = np.cumsum(volval[:, 1], axis=0)
            b = np.sum(volval[:, 1], axis=0)
            c = a / b * 100

            # Check for point without values
            if b < cn:
                gs.info(
                    _(
                        "Please note that there were {} points without "
                        "value. This is probably because they are outside "
                        "the computational region or mask".format((cn - b))
                    )
                )

            # Set region to env_proj layers (if different from env) and remove
            # mask (if set above)
            if citiam["fullname"]:
                gs.run_command("r.mask", quiet=True, flags="r")
            if RP:
                gs.use_temp_region()
                gs.run_command("g.region", quiet=True, raster=PROJ[0])
            region_2 = gs.parse_command("g.region", flags="g")

            # Multiply env_proj layer with dignum
            tmpf2 = tmpname("tmp8")
            gs.mapcalc(
                "$tmpf2 = int($dignum * $inplay)",
                tmpf2=tmpf2,
                inplay=PROJ[m],
                dignum=digits2,
                quiet=True,
            )

            # Calculate min and max values of sample points and raster layer
            envmin = int(min(volval[:, 0]) * digits2)
            envmax = int(max(volval[:, 0]) * digits2)
            Drange = gs.read_command("r.info", flags="r", map=tmpf2)
            Drange = str.splitlines(Drange)
            Drange = np.hstack([i.split("=") for i in Drange])
            Dmin = int(Drange[1])
            Dmax = int(Drange[3])

            if Dmin < envmin:
                e1 = Dmin - 1
            else:
                e1 = envmin - 1
            if Dmax > envmax:
                e2 = Dmax + 1
            else:
                e2 = envmax + 1

            a0 = volval[:, 0] * digits2
            a0 = a0.astype(np.int, copy=False)
            a1 = np.hstack([(e1), a0])
            a2 = np.hstack([a0 - 1, (e2)])
            b1 = np.hstack([(0), c])

            fd3, tmprule = tempfile.mkstemp(suffix=ipn[m])
            with open(tmprule, "w") as text_file:
                for k in np.arange(0, len(b1)):
                    rtmp = "{}:{}:{}\n".format(
                        str(int(a1[k])), str(int(a2[k])), str(b1[k])
                    )
                    text_file.write(rtmp)

            # Create the recode layer and calculate the IES
            compute_ies(tmprule, ipi[m], tmpf2, envmin, envmax)
            gs.run_command(
                "r.support",
                map=ipi[m],
                title="IES {}".format(REF[m]),
                units="0-100 (relative score",
                description="Environmental similarity {}".format(REF[m]),
                loadhistory=tmphist,
            )

            # Clean up
            os.close(fd3)
            os.remove(tmprule)

            # Change region back to original
            gs.del_temp_region()

    # Calculate MESS statistics
    # Set region to env_proj layers (if different from env)
    # Note: this changes the region, to ensure the newly created layers
    # are actually visible to the user. This goes against normal practise
    # There will be a warning.
    if RP:
        gs.run_command("g.region", quiet=True, raster=PROJ[0])

    # MES
    gs.run_command("r.series", quiet=True, output=opc, input=ipi, method="minimum")
    gs.write_command("r.colors", map=opc, rules="-", stdin=COLORS_MES, quiet=True)

    # Write layer metadata
    gs.run_command(
        "r.support",
        map=opc,
        title="Areas with novel conditions",
        units="0-100 (relative score",
        description="The multivariate environmental similarity" "(MES)",
        loadhistory=tmphist,
    )

    # Area with negative MES
    if fln:
        mod1 = "{}_novel".format(opl)
        gs.mapcalc("$mod1 = int(if( $opc < 0, 1, 0))", mod1=mod1, opc=opc, quiet=True)

        # Write category labels
        gs.write_command(
            "r.category", map=mod1, rules="-", stdin=RECL_MESNEG, quiet=True
        )

        # Write layer metadata
        gs.run_command(
            "r.support",
            map=mod1,
            title="Areas with novel conditions",
            units="-",
            source1="Based on {}".format(opc),
            description="1 = novel conditions, 0 = within range",
            loadhistory=tmphist,
        )

    # Most dissimilar variable (MoD)
    if flm:
        tmpf4 = tmpname("tmp9")
        mod2 = "{}_MoD".format(opl)
        gs.run_command(
            "r.series", quiet=True, output=tmpf4, input=ipi, method="min_raster"
        )
        gs.mapcalc("$mod2 = int($tmpf4)", mod2=mod2, tmpf4=tmpf4, quiet=True)

        fd4, tmpcat = tempfile.mkstemp()
        with open(tmpcat, "w") as text_file:
            for cats in xrange(len(ipi)):
                text_file.write("{}:{}\n".format(str(cats), REF[cats]))
        gs.run_command("r.category", quiet=True, map=mod2, rules=tmpcat, separator=":")
        os.close(fd4)
        os.remove(tmpcat)

        # Write layer metadata
        gs.run_command(
            "r.support",
            map=mod2,
            title="Most dissimilar variable (MoD)",
            units="-",
            source1="Based on {}".format(opc),
            description="Name of most dissimilar variable",
            loadhistory=tmphist,
        )

    # sum(IES), where IES < 0
    if flk:
        mod3 = "{}_SumNeg".format(opl)
        c0 = -0.01 / digits2
        gs.run_command(
            "r.series",
            quiet=True,
            input=ipi,
            method="sum",
            range=("-inf", c0),
            output=mod3,
        )
        gs.write_command("r.colors", map=mod3, rules="-", stdin=COLORS_MES, quiet=True)

        # Write layer metadata
        gs.run_command(
            "r.support",
            map=mod3,
            title="Sum of negative IES values",
            units="-",
            source1="Based on {}".format(opc),
            description="Sum of negative IES values",
            loadhistory=tmphist,
        )

    # Number of layers with negative values
    if flc:
        tmpf5 = tmpname("tmp10")
        mod4 = "{}_CountNeg".format(opl)
        MinMes = gs.read_command("r.info", quiet=True, flags="r", map=opc)
        MinMes = str.splitlines(MinMes)
        MinMes = float(np.hstack([i.split("=") for i in MinMes])[1])
        c0 = -0.0001 / digits2
        gs.run_command(
            "r.series",
            quiet=True,
            input=ipi,
            output=tmpf5,
            method="count",
            range=(MinMes, c0),
        )
        gs.mapcalc("$mod4 = int($tmpf5)", mod4=mod4, tmpf5=tmpf5, quiet=True)

        # Write layer metadata
        gs.run_command(
            "r.support",
            map=mod4,
            title="Number of layers with negative values",
            units="-",
            source1="Based on {}".format(opc),
            description="Number of layers with negative values",
            loadhistory=tmphist,
        )

    # Remove IES layers
    if fli:
        gs.run_command("g.remove", quiet=True, flags="f", type="raster", name=ipi)
    # Clean up tmp file
    os.remove(tmphist)

    gs.message(_("Finished ...\n"))
    if region_1 != region_2:
        gs.message(
            _(
                "\nPlease note that the region has been changes to match"
                " the set of projection (env_proj) variables.\n"
            )
        )


if __name__ == "__main__":
    atexit.register(cleanup)
    sys.exit(main(*gs.parser()))
