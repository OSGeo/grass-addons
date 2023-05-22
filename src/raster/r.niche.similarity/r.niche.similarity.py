#!/usr/bin/env python


########################################################################
#
# MODULE:       r.niche.similarity
# AUTHOR(S):    Paulo van Breugel <paulo ecodiv earth>
# PURPOSE:      Compute  degree of niche overlap using the statistics D
#               and I (as proposed by Warren et al., 2008) based on
#               Schoeners D (Schoener, 1968) and Hellinger Distances
#               (van der Vaart, 1998)
#
# COPYRIGHT: (c) 2015-2019 Paulo van Breugel and GRASS Development Team
#            http://ecodiv.earth
#
#            This program is free software under the GNU General Public
#            License (>=v2). Read the file COPYING that comes with GRASS
#            for details.
#
########################################################################
#
# %Module
# % description: Computes niche overlap or similarity
# % keyword: raster
# % keyword: niche modelling
# %End

# %option
# % key: maps
# % type: string
# % gisprompt: old,cell,raster
# % description: Input maps
# % key_desc: name
# % required: yes
# % multiple: yes
# % guisection: Suitability distribution maps
# %end

# %option G_OPT_F_OUTPUT
# % key:output
# % description: Name of output text file
# % key_desc: name
# % required: no
# %end

# %flag
# % key: i
# % description: I niche similarity
# % guisection: Statistics
# %end

# %flag
# % key: d
# % description: D niche similarity
# % guisection: Statistics
# %end

# %flag
# % key: c
# % description: Correlation
# % guisection: Statistics
# %end

# %rules
# %required: -i,-d,-c
# %end

# import libraries
import os
import sys
import atexit
import uuid
import grass.script as gs

# Cleanup
CLEAN_LAY = []


def cleanup():
    """Remove temporary maps specified in the global list"""
    cleanrast = list(reversed(CLEAN_LAY))
    for rast in cleanrast:
        gs.run_command("g.remove", type="raster", name=rast, quiet=True, flags="f")


def tmpname(prefix):
    """Generate a tmp name which contains prefix, store the name in the
    global list.
    """
    tmpf = 'prefix{}'.format(uuid.uuid4())
    tmpf = tmpf.replace("-", "_")
    CLEAN_LAY.append(tmpf)
    return tmpf


def D_index(n1, n2, v1, v2, txtf):
    """Calculate D (Schoener's 1968)"""
    tmpf0 = tmpname("rniche")
    gs.mapcalc(
        "$tmpf0 = abs(double($n1)/$v1 - double($n2)/$v2)",
        tmpf0=tmpf0,
        n1=n1,
        v1=v1,
        n2=n2,
        v2=v2,
        quiet=True,
    )
    NO = float(gs.parse_command("r.univar", quiet=True, flags="g", map=tmpf0)["sum"])
    NOV = 1 - (0.5 * NO)
    gs.info(
        _("Niche overlap (D) of {} and {} {}").format(
            n1.split("@")[0], n2.split("@")[0], round(NOV, 3)
        )
    )
    return ["Niche overlap (D)", n1, n2, NOV]


def I_index(n1, v1, n2, v2, txtf):
    """Calculate I (Warren et al. 2008). Note that the sqrt in the
    H formulation and the ^2 in the I formation  cancel each other out,
    hence the formulation below"""
    tmpf1 = tmpname("rniche")
    gs.mapcalc(
        "$tmpf1 = (sqrt(double($n1)/$v1) - sqrt(double($n2)/$v2))^2",
        tmpf1=tmpf1,
        n1=n1,
        v1=v1,
        n2=n2,
        v2=v2,
        quiet=True,
    )
    NE = float(gs.parse_command("r.univar", quiet=True, flags="g", map=tmpf1)["sum"])
    NEQ = 1 - (0.5 * NE)
    gs.info(
        _("Niche overlap (I) of {} and {} {}").format(
            n1.split("@")[0], n2.split("@")[0], round(NEQ, 3)
        )
    )
    return ["Niche overlap (I)", n1, n2, NEQ]


def C_index(n1, n2, txtf):
    """Calculate correlation"""
    corl = gs.read_command("r.covar", quiet=True, flags="r", map=(n1, n2))
    corl = corl.split("N = ")[1]
    corl = float(corl.split(" ")[1])
    gs.info(
        _("Correlation coeff of {} and {} {}").format(
            n1.split("@")[0], n2.split("@")[0], round(corl, 3)
        )
    )
    return ["Correlation coeff", n1, n2, corl]


def main(options, flags):

    # Check if running in GRASS
    gisbase = os.getenv("GISBASE")
    if not gisbase:
        gs.fatal(_("$GISBASE not defined"))
        return 0

    # input
    INMAPS = options["maps"]
    INMAPS = INMAPS.split(",")
    VARI = [i.split("@")[0] for i in INMAPS]
    OPF = options["output"]
    flag_i = flags["i"]
    flag_d = flags["d"]
    flag_c = flags["c"]

    # Check if there are more than 1 input maps
    NLAY = len(INMAPS)
    if NLAY < 2:
        gs.fatal("You need to provide 2 or more raster maps")

    # Write D and I values to standard output and optionally to text file
    Dind = []
    Iind = []
    Cind = []

    i = 0
    while i < NLAY:
        nlay1 = INMAPS[i]
        nvar1 = VARI[i]
        vsum1 = float(
            gs.parse_command("r.univar", quiet=True, flags="g", map=nlay1)["sum"]
        )
        j = i + 1
        while j < NLAY:
            nlay2 = INMAPS[j]
            nvar2 = VARI[j]
            vsum2 = float(
                gs.parse_command("r.univar", quiet=True, flags="g", map=nlay2)["sum"]
            )

            # Calculate D (Schoener's 1968)
            if flag_d:
                di = D_index(n1=nlay1, n2=nlay2, v1=vsum1, v2=vsum2, txtf=OPF)
                Dind.append(di)

            # Calculate I (Warren et al. 2008)
            if flag_i:
                ii = I_index(n1=nlay1, v1=vsum1, n2=nlay2, v2=vsum2, txtf=OPF)
                Iind.append(ii)

            # Calculate correlation
            if flag_c:
                ci = C_index(n1=nlay1, n2=nlay2, txtf=OPF)
                Cind.append(ci)

            # Set counter
            gs.info("--------------------------------------")
            j = j + 1

        # Set counter i
        i = i + 1

    # Write results to csv file
    if OPF:
        IND = [["Statistic", "Layer 1", "Layer 2", "value"], Dind, Iind, Cind]
        import csv

        with open(OPF, "w") as f:
            writer = csv.writer(f)
            writer.writerows(IND)
        gs.info(_("Results written to {}").format(OPF))


if __name__ == "__main__":
    atexit.register(cleanup)
    sys.exit(main(*gs.parser()))
