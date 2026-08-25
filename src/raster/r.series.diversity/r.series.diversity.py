#!/usr/bin/env python


########################################################################
#
# MODULE:       r.series.diversity
# AUTHOR(S):    Paulo van Breugel <paulo ecodiv earth>
# PURPOSE:      Compute biodiversity indices over input layers
#
# COPYRIGHT: (C) 2016-2026 Paulo van Breugel and the GRASS DEVELOPMENT TEAM
#            https://ecodiv.earth
#
#            This program is free software under the GNU General Public
#            License (>=v2). Read the file COPYING that comes with GRASS
#            for details.
#
########################################################################
#
# %Module
# % description: Compute diversity indici over input layers
# % keyword: raster
# % keyword: diversity index
# % keyword: renyi entrophy
# % keyword: shannon
# % keyword: simpson
# % keyword: richness
# % keyword: biodiversity
# % keyword: eveness
# %End

# %option
# % key: input
# % type: string
# % gisprompt: old,cell,raster
# % description: input layers
# % label: input layers
# % key_desc: name
# % required: yes
# % multiple: yes
# %end

# %option
# % key: output
# % type: string
# % gisprompt: new,cell,raster
# % description: prefix name output layer
# % key_desc: name
# % required: yes
# % multiple: no
# %end

# %flag
# % key: r
# % description: Renyi enthropy index
# % guisection: Indices
# %end

# %option
# % key: alpha
# % type: double
# % description: Order of generalized entropy
# % key_desc: number(s)
# % multiple: yes
# % options: 0.0-*
# % guisection: Indices
# %end

# %rules
# % collective: -r,alpha
# %end

# %flag
# % key: s
# % description: Richness index
# % guisection: Indices
# %end

# %flag
# % key: h
# % description: Shannon index
# % guisection: Indices
# %end

# %flag
# % key: p
# % description: Reversed Simpson index
# % guisection: Indices
# %end

# %flag
# % key: g
# % description: Gini-Simpson index
# % guisection: Indices
# %end

# %flag
# % key: e
# % description: Pielou's evenness index
# % guisection: Indices
# %end

# %flag
# % key: n
# % description: Shannon effective number of species
# % guisection: Indices
# %end

# %flag
# % key: t
# % description: Total counts
# % guisection: Indices
# %end

# %rules
# % required: -r,-s,-h,-e,-p,-g,-n
# %end

# %option G_OPT_M_NPROCS
# %end

# %option G_OPT_MEMORYMB
# %end

# ----------------------------------------------------------------------------
# Standard
# ----------------------------------------------------------------------------

# import libraries
import sys
import atexit
import inspect
import grass.script as gs

# ----------------------------------------------------------------------------
# Functions
# ----------------------------------------------------------------------------

# create set to store names of temporary maps to be deleted upon exit
clean_rast = []

# Detect support for paralelization (8.5+).
MAPCALC_HAS_NPROCS = "nprocs" in inspect.signature(gs.mapcalc).parameters


def mapcalc(expression, nprocs=1, **kwargs):
    """Wrapper around gs.mapcalc that passes nprocs only where supported.

    On GRASS 8.4 r.mapcalc has no nprocs parameter, so the argument is
    dropped; on 8.5+ it is forwarded to run the calculation in parallel.
    """
    if MAPCALC_HAS_NPROCS:
        kwargs["nprocs"] = nprocs
    gs.mapcalc(expression, **kwargs)


def cleanup():
    """Remove temporary maps specified in the global list"""
    cleanrast = list(reversed(clean_rast))
    for rast in cleanrast:
        if gs.find_file(rast, element="cell")["name"] != "":
            gs.run_command("g.remove", flags="f", type="rast", name=rast, quiet=True)


def CheckLayer(envlay):
    """Check if layers exist"""
    for chl in range(len(envlay)):
        ffile = gs.find_file(envlay[chl], element="cell")
        if ffile["fullname"] == "":
            gs.fatal("The layer " + envlay[chl] + " does not exist.")


def tmpname(name):
    """Create temporary file name"""
    tmpf = gs.append_uuid(name)
    clean_rast.append(tmpf)
    return tmpf


# ----------------------------------------------------------------------------
# main function
# ----------------------------------------------------------------------------
def main():
    # --------------------------------------------------------------------------
    # Variables
    # --------------------------------------------------------------------------

    # nprocs and memory
    nprocs = int(options["nprocs"])
    memory = int(options["memory"])

    # Layers
    gs.info("Preparing...")
    OUT = options["output"]
    IN = options["input"]
    IN = IN.split(",")
    CheckLayer(IN)

    # Diversity indici
    flag_r = flags["r"]
    flag_s = flags["s"]
    flag_h = flags["h"]
    flag_e = flags["e"]
    flag_p = flags["p"]
    flag_g = flags["g"]
    flag_n = flags["n"]
    flag_t = flags["t"]
    if options["alpha"]:
        Qtmp = map(float, options["alpha"].split(","))
    else:
        Qtmp = map(float, [])
    Q = list(Qtmp)
    Qoriginal = Q

    # --------------------------------------------------------------------------
    # Create list of what need to be computed
    # --------------------------------------------------------------------------
    if not flag_r:
        flag_r = []
    if flag_s and 0.0 not in Q:
        Q.append(0.0)
    if flag_h and 1.0 not in Q:
        Q.append(1.0)
    if flag_e and 0.0 not in Q:
        Q.append(0.0)
    if flag_e and 1.0 not in Q:
        Q.append(1.0)
    if flag_p and 2.0 not in Q:
        Q.append(2.0)
    if flag_g and 2.0 not in Q:
        Q.append(2.0)
    if flag_n and 1.0 not in Q:
        Q.append(1.0)

    # Check that none of the output layers already exist (unless overwriting)
    output_layers = [f"{OUT}_Renyi_" + str(q).replace(".", "_") for q in Q]
    if flag_s:
        output_layers.append(OUT + "_richness")
    if flag_h:
        output_layers.append(OUT + "_shannon")
    if flag_n:
        output_layers.append(OUT + "_ens")
    if flag_e:
        output_layers.append(OUT + "_eveness")
    if flag_p:
        output_layers.append(OUT + "_invsimpson")
    if flag_g:
        output_layers.append(OUT + "_ginisimpson")
    if flag_t:
        output_layers.append(OUT + "_count")

    if not gs.overwrite():
        mapset = gs.gisenv()["MAPSET"]
        existing = [
            lay
            for lay in output_layers
            if gs.find_file(name=lay, element="cell", mapset=mapset)["name"]
        ]
        if existing:
            gs.fatal(
                _(
                    "The following output raster map(s) already exist: {maps}. "
                    "Use the --overwrite flag to allow them to be overwritten, "
                    "or choose a different output prefix."
                ).format(maps=", ".join(sorted(existing)))
            )

    # --------------------------------------------------------------------------
    # Renyi entropy
    # --------------------------------------------------------------------------
    # The sum across all input layers.
    tmp_series = tmpname("tmp02")
    gs.info("Computing the sum across all input layers (this may take a while)")
    gs.run_command(
        "r.series",
        quiet=True,
        output=tmp_series,
        input=IN,
        method="sum",
        nprocs=nprocs,
        memory=memory,
    )

    # Layer marking the cells to keep: 1 where the sum > 0, null where the sum
    # is 0 (no observations). Multiplying a result by this layer sets the
    # zero-sum cells to null.
    zeromask = tmpname("tmp_zeromask")
    mapcalc(f"{zeromask} = if({tmp_series}==0, null(), 1)", nprocs=nprocs, quiet=True)

    # Calculate renyi
    for n in range(len(Q)):
        gs.info(_("Computing alpha = {}").format(Q[n]))
        Qn = str(Q[n])
        Qn = Qn.replace(".", "_")
        renyi = OUT + "_Renyi_" + Qn
        if Q[n] == 1:
            # If alpha = 1
            # TODO See email 14-01-16 about avoiding loop below
            mapcalc(f"{renyi} = 0", nprocs=nprocs, quiet=True)
            for i in range(len(IN)):
                gs.info(_("Computing map {j} from {n} maps").format(j=i + 1, n=len(IN)))
                tmp_2 = tmpname("tmp04")
                mapcalc(
                    (
                        f"{tmp_2} = if({IN[i]} == 0, {renyi}, "
                        f"{renyi} - (({IN[i]}/{tmp_series}) * log(({IN[i]}/{tmp_series}))))"
                    ),
                    nprocs=nprocs,
                    quiet=True,
                )
                gs.run_command(
                    "g.rename",
                    raster="{0},{1}".format(tmp_2, renyi),
                    overwrite=True,
                    quiet=True,
                )
            # Set zero-sum cells to null
            tmp_z = tmpname("tmp07")
            mapcalc(f"{tmp_z} = {renyi} * {zeromask}", nprocs=nprocs, quiet=True)
            gs.run_command(
                "g.rename",
                raster="{0},{1}".format(tmp_z, renyi),
                overwrite=True,
                quiet=True,
            )
        else:
            # If alpha != 1
            tmp_3 = tmpname("tmp05")
            tmp_4 = tmpname("tmp06")
            mapcalc(f"{tmp_3} = 0", nprocs=nprocs, quiet=True)
            for i in range(len(IN)):
                gs.info(_("Computing map {j} from {n} maps").format(j=i + 1, n=len(IN)))
                mapcalc(
                    (
                        f"{tmp_4} = if({IN[i]} == 0, "
                        f"{tmp_3}, {tmp_3} + (pow({IN[i]}/{tmp_series},{Q[n]})))"
                    ),
                    nprocs=nprocs,
                    quiet=True,
                )
                gs.run_command(
                    "g.rename",
                    raster="{0},{1}".format(tmp_4, tmp_3),
                    overwrite=True,
                    quiet=True,
                )
            # Multiply by zeromask to set zero-sum cells to null (log(0) above
            # would otherwise leave them non-null
            mapcalc(
                f"{renyi} = ((1/(1-{Q[n]})) * log({tmp_3})) * {zeromask}",
                nprocs=nprocs,
                quiet=True,
            )

    # --------------------------------------------------------------------------
    # Species richness, add 0 for areas with no observations
    # --------------------------------------------------------------------------
    if flag_s:
        gs.info("Computing species richness map")
        out_div = OUT + "_richness"
        in_div = OUT + "_Renyi_0_0"
        mapcalc(
            f"{out_div} = if({tmp_series}==0,0,exp({in_div}))",
            nprocs=nprocs,
            quiet=True,
        )
        if 0.0 not in Qoriginal and not flag_e:
            gs.run_command(
                "g.remove", flags="f", type="raster", name=in_div, quiet=True
            )

    # --------------------------------------------------------------------------
    # Shannon index
    # --------------------------------------------------------------------------
    if flag_h:
        gs.info("Computing Shannon index map")
        out_div = OUT + "_shannon"
        in_div = OUT + "_Renyi_1_0"
        if 1.0 in Qoriginal or flag_e or flag_n:
            gs.run_command("g.copy", raster=(in_div, out_div), quiet=True)
        else:
            gs.run_command("g.rename", raster=(in_div, out_div), quiet=True)

    # --------------------------------------------------------------------------
    # Shannon Effective Number of Species (ENS)
    # --------------------------------------------------------------------------
    if flag_n:
        gs.info("Computing ENS map")
        out_div = OUT + "_ens"
        in_div = OUT + "_Renyi_1_0"
        mapcalc(f"{out_div} = exp({in_div})", nprocs=nprocs, quiet=True)
        if 1.0 not in Qoriginal and not flag_e:
            gs.run_command(
                "g.remove", flags="f", type="raster", name=in_div, quiet=True
            )

    # --------------------------------------------------------------------------
    # Eveness
    # --------------------------------------------------------------------------
    if flag_e:
        gs.info("Computing Eveness map")
        out_div = OUT + "_eveness"
        in_div1 = OUT + "_Renyi_0_0"
        in_div2 = OUT + "_Renyi_1_0"
        mapcalc(f"{out_div} = {in_div2} / {in_div1}", nprocs=nprocs, quiet=True)
        if 0.0 not in Qoriginal:
            gs.run_command(
                "g.remove", flags="f", type="raster", name=in_div1, quiet=True
            )
        if 1.0 not in Qoriginal:
            gs.run_command(
                "g.remove", flags="f", type="raster", name=in_div2, quiet=True
            )
    # --------------------------------------------------------------------------
    # Inversed Simpson index
    # --------------------------------------------------------------------------
    if flag_p:
        gs.info("Computing inverse simpson map")
        out_div = OUT + "_invsimpson"
        in_div = OUT + "_Renyi_2_0"
        mapcalc(f"{out_div} = exp({in_div})", nprocs=nprocs, quiet=True)
        if 2.0 not in Qoriginal and not flag_g:
            gs.run_command(
                "g.remove", flags="f", type="raster", name=in_div, quiet=True
            )

    # --------------------------------------------------------------------------
    # Gini Simpson index
    # --------------------------------------------------------------------------
    if flag_g:
        gs.info("Computing Gini simpson map")
        out_div = OUT + "_ginisimpson"
        in_div = OUT + "_Renyi_2_0"
        mapcalc(f"{out_div} = 1.0 - (1.0 / exp({in_div}))", nprocs=nprocs, quiet=True)
        if 2.0 not in Qoriginal:
            gs.run_command(
                "g.remove", flags="f", type="raster", name=in_div, quiet=True
            )

    # --------------------------------------------------------------------------
    # Total count (base unit, like individuals)
    # --------------------------------------------------------------------------
    if flag_t:
        rast = OUT + "_count"
        gs.run_command("g.rename", raster=(tmp_series, rast), quiet=True)
    else:
        gs.run_command(
            "g.remove", type="raster", name=tmp_series, flags="f", quiet=True
        )


if __name__ == "__main__":
    options, flags = gs.parser()
    atexit.register(cleanup)
    sys.exit(main())
