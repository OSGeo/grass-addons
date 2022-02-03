#!/usr/bin/env python


########################################################################
#
# MODULE:       r.meb
# AUTHOR(S):    Paulo van Breugel <paulo AT ecodiv.earth>
# PURPOSE:      Compute the multivariate envirionmental bias (MEB) as
#               described in van Breugel et al. 2015
#               (doi: 10.1371/journal.pone.0121444). If A s an areas
#               within a larger region B, the EB represents how much
#               envirionmental conditions in A deviate from median
#               conditions in B. The first step is to compute the
#               multi-envirionmental similarity (MES) for B, using all
#               raster cells in B as reference points. The MES of a
#               raster cell thus represent how much conditions deviate
#               from median conditions in B. The EB is then computed as the
#               absolute difference of the median of MES values in A (MESa)
#               and median of MES values in B (MESb), divided by the median of
#               the absolute deviations of MESb from the median of MESb (MAD)
#
# COPYRIGHT: (C) 2014-2019 by Paulo van Breugel and the GRASS Development Team
#
#            This program is free software under the GNU General Public
#            License (>=v2). Read the file COPYING that comes with GRASS
#            for details.
#
########################################################################
#
# %Module
# % description: Compute the multivariate environmental bias (MEB)
# % keyword: similarity
# % keyword: raster
# % keyword: modelling
# %End

# %option G_OPT_R_INPUTS
# % key: env
# % label: Environmental layers
# % description: Raster map(s) of environmental conditions
# % key_desc: names
# % guisection: Input
# %end

# %option G_OPT_R_INPUTS
# % key: ref
# % label: Reference area
# % description: Sub-area (1) within region (1+0) for which to compute the EB
# % key_desc: names
# % multiple: no
# % guisection: Input
# %end

# %option G_OPT_R_OUTPUT
# % key: output
# % label: Root of name output layers
# % description: Output MES layer (and root for IES layers if kept)
# % key_desc: names
# % required: no
# % multiple: no
# % guisection: Output
# %end

# %option G_OPT_F_OUTPUT
# % key:file
# % label: Name of output text file
# % description: Name of output text file (csv format)
# % key_desc: name
# % required: no
# % guisection: Output
# %end

# %flag
# % key: i
# % description: Compute EB for individual variables
# % guisection: Output
# %end

# %flag
# % key: m
# % description: Use mean values of IES layers to compute MES
# % guisection: Output
# %end

# %flag
# % key: n
# % description: Use median values of IES layers to compute MES
# % guisection: Output
# %end

# %flag
# % key: o
# % description: Use minimum values of IES layers to compute MES
# % guisection: Output
# %end

# %rules
# % required: -m,-n,-o
# %end

# %option
# % key: digits
# % type: integer
# % description: Precision of your input layers values
# % key_desc: string
# % answer: 5
# %end

# ----------------------------------------------------------------------------
# Standard
# ----------------------------------------------------------------------------

# import libraries
import os
import sys
import csv
import numpy as np
import uuid
import operator
import atexit
import tempfile
import string
import grass.script as gs

# for Python 3 compatibility
try:
    xrange
except NameError:
    xrange = range

# Rules
COLORS_MES = """\
0% 244:109:67
0 255:255:210
100% 50:136:189
"""

# ---------------------------------------------------------------------------
# Functions
# ---------------------------------------------------------------------------

# create set to store names of temporary maps to be deleted upon exit
CLEAN_RAST = []


def cleanup():
    """Remove temporary maps specified in the global list"""
    for rast in CLEAN_RAST:
        cf = gs.find_file(name=rast, element="cell", mapset=gs.gisenv()["MAPSET"])
        if cf["fullname"] != "":
            gs.run_command("g.remove", type="raster", name=rast, quiet=True, flags="f")


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


def raster_exists(envlay):
    """Check if the raster map exists, call GRASS fatal otherwise"""
    for chl in xrange(len(envlay)):
        ffile = gs.find_file(envlay[chl], element="cell")
        if not ffile["fullname"]:
            gs.fatal(_("The layer {} does not exist").format(envlay[chl]))


# Compute EB for input file (simlay = similarity, reflay = reference layer)
def EB(simlay, reflay):
    """Computation of the envirionmental bias and print to stdout"""
    # Median and mad for whole region (within current mask)
    tmpf4 = tmpname("reb4")
    CLEAN_RAST.append(tmpf4)
    d = gs.read_command("r.quantile", quiet=True, input=simlay, percentiles="50")
    d = d.split(":")
    d = float(string.replace(d[2], "\n", ""))
    gs.mapcalc("$tmpf4 = abs($map - $d)", map=simlay, tmpf4=tmpf4, d=d, quiet=True)
    mad = gs.read_command("r.quantile", quiet=True, input=tmpf4, percentiles="50")
    mad = mad.split(":")
    mad = float(string.replace(mad[2], "\n", ""))
    gs.run_command("g.remove", quiet=True, flags="f", type="raster", name=tmpf4)

    # Median and mad for reference layer
    tmpf5 = tmpname("reb5")
    CLEAN_RAST.append(tmpf5)
    gs.mapcalc(
        "$tmpf5 = if($reflay==1, $simlay, null())",
        simlay=simlay,
        tmpf5=tmpf5,
        reflay=reflay,
        quiet=True,
    )
    e = gs.read_command("r.quantile", quiet=True, input=tmpf5, percentiles="50")
    e = e.split(":")
    e = float(string.replace(e[2], "\n", ""))
    EBstat = abs(d - e) / mad

    # Print results to screen and return results
    gs.info(_("Median (all region) = {:.3f}").format(d))
    gs.info(_("Median (ref. area) = {:.3f}").format(e))
    gs.info(_("MAD = {:.3f}").format(mad))
    gs.info(_("EB = {:.3f}").format(EBstat))

    # Clean up and return data
    gs.run_command("g.remove", flags="f", type="raster", name=tmpf5, quiet=True)
    return (mad, d, e, EBstat)


def main(options, flags):

    # Check if running in GRASS
    gisbase = os.getenv("GISBASE")
    if not gisbase:
        gs.fatal(_("$GISBASE not defined"))
        return 0

    # variables
    ipl = options["env"]
    ipl = ipl.split(",")
    raster_exists(ipl)
    ipn = [z.split("@")[0] for z in ipl]
    ipn = [x.lower() for x in ipn]
    out = options["output"]
    if out:
        tmpf0 = out
    else:
        tmpf0 = tmpname("reb0")
    filename = options["file"]
    ref = options["ref"]
    flag_m = flags["m"]
    flag_n = flags["n"]
    flag_o = flags["o"]
    flag_i = flags["i"]
    digits = int(options["digits"])
    digits2 = pow(10, digits)

    # Check if ref map is of type cell and values are limited to 1 and 0
    reftype = gs.raster_info(ref)
    if reftype["datatype"] != "CELL":
        gs.fatal(_("Your reference map must have type CELL (integer)"))
    if reftype["min"] != 0 or reftype["max"] != 1:
        gs.fatal(
            _(
                "The input raster map must be a binary raster,"
                " i.e. it should contain only values 0 and 1 "
                " (now the minimum is %d and maximum is %d)"
            )
            % (reftype["min"], reftype["max"])
        )

    # Text for history in metadata
    opt2 = dict((k, v) for k, v in options.iteritems() if v)
    hist = " ".join("{!s}={!r}".format(k, v) for (k, v) in opt2.iteritems())
    hist = "r.meb {}".format(hist)
    unused, tmphist = tempfile.mkstemp()
    text_file = open(tmphist, "w")
    text_file.write(hist)
    text_file.close()

    # ------------------------------------------------------------------------
    # Compute MES
    # ------------------------------------------------------------------------

    # Create temporary copy of ref layer
    tmpref0 = tmpname("reb1")
    CLEAN_RAST.append(tmpref0)
    gs.run_command("g.copy", quiet=True, raster=(ref, tmpref0))

    ipi = []
    for j in xrange(len(ipl)):
        # Calculate the frequency distribution
        tmpf1 = tmpname("reb1")
        CLEAN_RAST.append(tmpf1)
        laytype = gs.raster_info(ipl[j])["datatype"]
        if laytype == "CELL":
            gs.run_command("g.copy", quiet=True, raster=(ipl[j], tmpf1))
        else:
            gs.mapcalc(
                "$tmpf1 = int($dignum * $inplay)",
                tmpf1=tmpf1,
                inplay=ipl[j],
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

        # Create recode rules
        e1 = np.min(np.array(sstval), axis=0)[0] - 99999
        e2 = np.max(np.array(sstval), axis=0)[0] + 99999
        a1 = np.hstack([(e1), np.array(sstval.T[0])[0, :]])
        a2 = np.hstack([np.array(sstval.T[0])[0, :] - 1, (e2)])
        b1 = np.hstack([(0), c])

        fd2, tmprule = tempfile.mkstemp()
        text_file = open(tmprule, "w")
        for k in np.arange(0, len(b1.T)):
            text_file.write("{}:{}:{}\n".format(int(a1[k]), int(a2[k]), b1[k]))
        text_file.close()

        # Create the recode layer and calculate the IES
        tmpf2 = tmpname("reb2")
        CLEAN_RAST.append(tmpf2)
        gs.run_command("r.recode", input=tmpf1, output=tmpf2, rules=tmprule)

        tmpf3 = tmpname("reb3")
        CLEAN_RAST.append(tmpf3)

        calcc = (
            "{1} = if({0} <= 50, 2 * float({0}), if({0} < 100, "
            "2 * (100 - float({0}))))".format(tmpf2, tmpf3)
        )
        gs.mapcalc(calcc, quiet=True)
        gs.run_command(
            "g.remove", quiet=True, flags="f", type="raster", name=(tmpf2, tmpf1)
        )
        os.close(fd2)
        os.remove(tmprule)
        ipi.append(tmpf3)

    # ----------------------------------------------------------------------
    # Calculate EB statistics
    # ----------------------------------------------------------------------

    # EB MES
    if flag_m:
        gs.info(_("\nThe EB based on mean ES values:\n"))
        nmn = "{}_MES_mean".format(tmpf0)
        gs.run_command(
            "r.series", quiet=True, output=nmn, input=tuple(ipi), method="average"
        )
        gs.write_command("r.colors", map=nmn, rules="-", stdin=COLORS_MES, quiet=True)
        ebm = EB(simlay=nmn, reflay=tmpref0)
        if not out:
            # Add to list of layers to be removed at completion
            CLEAN_RAST.append(nmn)
        else:
            # Write layer metadata
            gs.run_command(
                "r.support",
                map=nmn,
                title="Multivariate environmental similarity (MES)",
                units="0-100 (relative score",
                description="MES (compuated as the average of "
                "the individual similarity layers",
                loadhistory=tmphist,
            )

    if flag_n:
        gs.info(_("\nThe EB based on median ES values:\n"))
        nmn = "{}_MES_median".format(tmpf0)
        gs.run_command(
            "r.series", quiet=True, output=nmn, input=tuple(ipi), method="median"
        )
        gs.write_command("r.colors", map=nmn, rules="-", stdin=COLORS_MES, quiet=True)
        ebn = EB(simlay=nmn, reflay=tmpref0)
        if not out:
            CLEAN_RAST.append(nmn)
        else:
            # Write layer metadata
            gs.run_command(
                "r.support",
                map=nmn,
                title="Multivariate environmental similarity (MES)",
                units="0-100 (relative score",
                description="MES (compuated as the median of "
                "the individual similarity layers",
                loadhistory=tmphist,
            )

    if flag_o:
        gs.info(_("\nThe EB based on minimum ES values:\n"))
        nmn = "{}_MES_minimum".format(tmpf0)
        gs.run_command(
            "r.series", quiet=True, output=nmn, input=tuple(ipi), method="minimum"
        )
        gs.write_command("r.colors", map=nmn, rules="-", stdin=COLORS_MES, quiet=True)
        ebo = EB(simlay=nmn, reflay=tmpref0)
        if not out:
            CLEAN_RAST.append(nmn)
        else:
            # Write layer metadata
            gs.run_command(
                "r.support",
                map=nmn,
                title="Multivariate environmental similarity (MES)",
                units="0-100 (relative score",
                description="MES (compuated as the minimum of "
                "the individual similarity layers",
                loadhistory=tmphist,
            )

    # EB individual layers
    if flag_i:
        ebi = {}
        for mm in xrange(len(ipi)):
            nmn = "{}_{}".format(tmpf0, ipn[mm])
            if not out:
                CLEAN_RAST.append(nmn)
            gs.run_command("g.rename", quiet=True, raster=(ipi[mm], nmn))
            gs.write_command(
                "r.colors", map=nmn, rules="-", stdin=COLORS_MES, quiet=True
            )
            gs.info(_("\nThe EB for {}:\n").format(ipn[mm]))
            value = EB(simlay=nmn, reflay=tmpref0)
            ebi[ipn[mm]] = value
            gs.run_command(
                "r.support",
                map=nmn,
                title="Environmental similarity (ES) for " "{}".format(ipn[mm]),
                units="0-100 (relative score",
                description="Environmental similarity (ES) for " "{}".format(ipn[mm]),
                loadhistory=tmphist,
            )
    else:
        gs.run_command("g.remove", quiet=True, flags="f", type="raster", name=ipi)

    if filename:
        with open(filename, "wb") as csvfile:
            fieldnames = ["variable", "median_region", "median_reference", "mad", "eb"]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            if flag_m:
                writer.writerow(
                    {
                        "variable": "MES_mean",
                        "median_region": ebm[1],
                        "median_reference": ebm[2],
                        "mad": ebm[0],
                        "eb": ebm[3],
                    }
                )
            if flag_n:
                writer.writerow(
                    {
                        "variable": "MES_median",
                        "median_region": ebn[1],
                        "median_reference": ebn[2],
                        "mad": ebn[0],
                        "eb": ebn[3],
                    }
                )
            if flag_o:
                writer.writerow(
                    {
                        "variable": "MES_minimum",
                        "median_region": ebo[1],
                        "median_reference": ebo[2],
                        "mad": ebo[0],
                        "eb": ebo[3],
                    }
                )
            if flag_i:
                mykeys = ebi.keys()
                for vari in mykeys:
                    ebj = ebi[vari]
                    writer.writerow(
                        {
                            "variable": vari,
                            "median_region": ebj[1],
                            "median_reference": ebj[2],
                            "mad": ebj[0],
                            "eb": ebj[3],
                        }
                    )
        gs.info(_("\nThe results are written to {}\n").format(filename))
        gs.info("\n")


if __name__ == "__main__":
    atexit.register(cleanup)
    sys.exit(main(*gs.parser()))
