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
#            https://ecodiv.earth
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

# %option G_OPT_R_INPUTS
# %key:maps
# % description: Input maps
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

# %flag
# % key: m
# % description: remove NA cells
# % guisection: Statistics
# %end

# %rules
# %required: -i,-d,-c
# %end

# %option G_OPT_M_NPROCS
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


def create_unique_name(name):
    """Generate a tmp name which contains prefix
    Store the name in the global list.
    Use only for raster maps.
    """
    return name + str(uuid.uuid4().hex)


def create_temporary_name(prefix):
    tmpf = create_unique_name(prefix)
    CLEAN_LAY.append(tmpf)
    return tmpf


def D_index(n1, n2, v1, v2, txtf, nprocs):
    """Calculate D (Schoener's 1968)"""
    tmpf0 = create_temporary_name("rniche")
    gs.mapcalc(
        "$tmpf0 = abs(double($n1)/$v1 - double($n2)/$v2)",
        tmpf0=tmpf0,
        n1=n1,
        v1=v1,
        n2=n2,
        v2=v2,
        quiet=True,
    )
    NO = float(
        gs.parse_command("r.univar", quiet=True, flags="g", map=tmpf0, nprocs=nprocs)[
            "sum"
        ]
    )
    NOV = 1 - (0.5 * NO)
    return NOV


def I_index(n1, v1, n2, v2, txtf, nprocs):
    """Calculate I (Warren et al. 2008). Note that the sqrt in the
    H formulation and the ^2 in the I formation  cancel each other out,
    hence the formulation below"""
    tmpf1 = create_temporary_name("rniche")
    gs.mapcalc(
        "$tmpf1 = (sqrt(double($n1)/$v1) - sqrt(double($n2)/$v2))^2",
        tmpf1=tmpf1,
        n1=n1,
        v1=v1,
        n2=n2,
        v2=v2,
        quiet=True,
    )
    NE = float(
        gs.parse_command("r.univar", quiet=True, flags="g", map=tmpf1, nprocs=nprocs)[
            "sum"
        ]
    )
    NEQ = 1 - (0.5 * NE)
    return NEQ


def C_index(n1, n2, txtf):
    """Calculate correlation"""
    corl = gs.read_command("r.covar", quiet=True, flags="r", map=(n1, n2))
    corl = corl.split("N = ")[1]
    corl = float(corl.split(" ")[1])
    return corl


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
    nprocs = int(options["nprocs"])
    flag_i = flags["i"]
    flag_d = flags["d"]
    flag_c = flags["c"]
    flag_m = flags["m"]

    # Check if there are more than 1 input maps
    NLAY = len(INMAPS)
    if NLAY < 2:
        gs.fatal(_("You need to provide 2 or more raster maps"))

    # Write D and I values to standard output and optionally to text file
    Dind = []
    Iind = []
    Cind = []

    i = 0

    if flag_m:
        while i < NLAY:
            nlay1 = INMAPS[i]
            nvar1 = VARI[i]
            j = i + 1
            while j < NLAY:
                nlay2 = INMAPS[j]
                nvar2 = VARI[j]

                # Set temp region to overlapping area
                gs.use_temp_region()
                gs.run_command("g.region", zoom=nlay1)
                gs.run_command("g.region", zoom=nlay2)

                # Stats
                vsta1 = gs.parse_command(
                    "r.univar", quiet=True, flags="g", map=nlay1, nprocs=nprocs
                )
                vsum1 = float(vsta1["sum"])
                vsta2 = gs.parse_command(
                    "r.univar", quiet=True, flags="g", map=nlay2, nprocs=nprocs
                )
                vsum2 = float(vsta2["sum"])

                # Remove remaining nodata
                chnodat = int(vsta1["null_cells"]) + int(vsta2["null_cells"])
                if chnodat > 0:
                    tmpl1 = create_temporary_name("tmp")
                    gs.run_command(
                        "r.mapcalc",
                        expression=f"{tmpl1} = if(isnull({nlay1}) || isnull({nlay2}), null(), {nlay1})",
                    )
                    tmpl2 = create_temporary_name("tmp")
                    gs.run_command(
                        "r.mapcalc",
                        expression=f"{tmpl2} = if(isnull({nlay1}) || isnull({nlay2}), null(), {nlay2})",
                    )
                    vsum1 = float(
                        gs.parse_command(
                            "r.univar", quiet=True, flags="g", map=tmpl1, nprocs=nprocs
                        )["sum"]
                    )
                    vsum2 = float(
                        gs.parse_command(
                            "r.univar", quiet=True, flags="g", map=tmpl2, nprocs=nprocs
                        )["sum"]
                    )
                else:
                    tmpl1 = nlay1
                    tmpl2 = nlay2

                # Calculate D (Schoener's 1968)
                if flag_d:
                    di = D_index(
                        n1=tmpl1, n2=tmpl2, v1=vsum1, v2=vsum2, txtf=OPF, nprocs=nprocs
                    )
                    Dind.append(di)
                    gs.info(
                        _("Niche overlap (D) of {} and {} {}").format(
                            nvar1, nvar2, round(di, 5)
                        )
                    )

                # Calculate I (Warren et al. 2008)
                if flag_i:
                    ii = I_index(
                        n1=tmpl1, n2=tmpl2, v1=vsum1, v2=vsum2, txtf=OPF, nprocs=nprocs
                    )
                    Iind.append(ii)
                    gs.info(
                        _("Niche overlap (I) of {} and {} {}").format(
                            nvar1, nvar2, round(ii, 5)
                        )
                    )

                # Calculate correlation
                if flag_c:
                    ci = C_index(n1=tmpl1, n2=tmpl2, txtf=OPF)
                    Cind.append(ci)
                    gs.info(
                        _("Correlation coeff of {} and {} {}").format(
                            nvar1, nvar2, round(ci, 5)
                        )
                    )
                gs.del_temp_region()

                # Set counter
                gs.info("--------------------------------------")
                j = j + 1

            # Set counter i
            i = i + 1
    else:
        while i < NLAY:
            nlay1 = INMAPS[i]
            nvar1 = VARI[i]
            j = i + 1

            # Stats
            vsta1 = gs.parse_command(
                "r.univar", quiet=True, flags="g", map=nlay1, nprocs=nprocs
            )
            vsum1 = float(vsta1["sum"])

            while j < NLAY:
                nlay2 = INMAPS[j]
                nvar2 = VARI[j]

                # Stats
                vsta2 = gs.parse_command(
                    "r.univar", quiet=True, flags="g", map=nlay2, nprocs=nprocs
                )
                vsum2 = float(vsta2["sum"])

                # Calculate D (Schoener's 1968)
                if flag_d:
                    di = D_index(
                        n1=nlay1, n2=nlay2, v1=vsum1, v2=vsum2, txtf=OPF, nprocs=nprocs
                    )
                    Dind.append(di)
                    gs.info(
                        _("Niche overlap (D) of {} and {} {}").format(
                            nvar1, nvar2, round(di, 5)
                        )
                    )

                # Calculate I (Warren et al. 2008)
                if flag_i:
                    ii = I_index(
                        n1=nlay1, n2=nlay2, v1=vsum1, v2=vsum2, txtf=OPF, nprocs=nprocs
                    )
                    Iind.append(ii)
                    gs.info(
                        _("Niche overlap (I) of {} and {} {}").format(
                            nvar1, nvar2, round(ii, 5)
                        )
                    )

                # Calculate correlation
                if flag_c:
                    ci = C_index(n1=nlay1, n2=nlay2, txtf=OPF)
                    Cind.append(ci)
                    gs.info(
                        _("Correlation coeff of {} and {} {}").format(
                            nvar1, nvar2, round(ci, 5)
                        )
                    )

                # Set counter
                gs.info("--------------------------------------")
                j = j + 1

                # Warn if there is NODATA in one of the input raster layers
                chnodat = int(vsta1["null_cells"]) + int(vsta2["null_cells"])
                if chnodat > 0:
                    gs.warning(
                        _(
                            "Note that {} or {} contain NODATA cells.\n"
                            "This may result in unexpected outcomes. \n"
                            "Use the -m flag or check the manual page\n"
                            "for alternatives."
                        ).format(nvar1, nvar2)
                    )

            # Set counter i
            i = i + 1

    # Write results to csv file
    if OPF:
        IND = [["Statistic", "Layer 1", "Layer 2", "value"]] + Dind + Iind + Cind
        import csv

        with open(OPF, "w") as f:
            writer = csv.writer(f)
            writer.writerows(IND)
        gs.info(_("Results written to {}").format(OPF))


if __name__ == "__main__":
    atexit.register(cleanup)
    sys.exit(main(*gs.parser()))
