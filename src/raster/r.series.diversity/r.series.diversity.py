#!/usr/bin/env python


########################################################################
#
# MODULE:       r.series.diversity
# AUTHOR(S):    Paulo van Breugel <paulo ecodiv earth>
# PURPOSE:      Compute biodiversity indices over input layers
#
# COPYRIGHT: (C) 2014-2019 Paulo van Breugel and the GRASS DEVELOPMENT TEAM
#            http://ecodiv.earth
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

# ----------------------------------------------------------------------------
# Standard
# ----------------------------------------------------------------------------

# import libraries
import os
import sys
import uuid
import atexit
import string
import grass.script as grass

# ----------------------------------------------------------------------------
# Functions
# ----------------------------------------------------------------------------

# create set to store names of temporary maps to be deleted upon exit
clean_rast = set()


def cleanup():
    for rast in clean_rast:
        grass.run_command("g.remove", flags="f", type="rast", name=rast, quiet=True)


def CheckLayer(envlay):
    for chl in range(len(envlay)):
        ffile = grass.find_file(envlay[chl], element="cell")
        if ffile["fullname"] == "":
            grass.fatal("The layer " + envlay[chl] + " does not exist.")


# Create temporary name
def tmpname(name):
    tmpf1 = name + "_" + str(uuid.uuid4())
    tmpf = tmpf1.replace("-", "_")
    clean_rast.add(tmpf)
    return tmpf


# Create mask for all areas with sum=0, incorporate existing mask
def replacemask(inmap):
    msk = grass.find_file(name="MASK", element="cell", mapset=grass.gisenv()["MAPSET"])
    minval = float(
        grass.parse_command("r.info", flags="gr", map=inmap, quiet=True)["min"]
    )
    if msk["fullname"] != "":
        if minval > 0:
            return "samemask"
        else:
            rname = tmpname("MASK")
            grass.mapcalc("$rname = MASK", rname=rname, quiet=True)
            grass.run_command("r.mask", flags="r", quiet=True)
            grass.mapcalc(
                "MASK = if($tmp_1==0, null(),$msk)", tmp_1=inmap, msk=rname, quiet=True
            )
            return rname
    else:
        grass.mapcalc("MASK = if($inmap==0, null(),1)", inmap=inmap, quiet=True)
        return "nomask"


# ----------------------------------------------------------------------------
# main function
# ----------------------------------------------------------------------------

# testset
# MAPS = ','.join(grass.list_strings(type='raster', pattern='s*', mapset='trees'))
# flags = {'r':False, 's':True, 'h':True, 'e':True, 'p':True,'g':True,'n':True, 't':False}
# options={'output':'Test01', 'input':MAPS, 'alpha':''}


def main():

    # --------------------------------------------------------------------------
    # Variables
    # --------------------------------------------------------------------------

    # Layers
    grass.info("Preparing...")
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

    # --------------------------------------------------------------------------
    # Renyi entropy
    # --------------------------------------------------------------------------
    tmp_1 = tmpname("sht")
    clean_rast.add(tmp_1)
    grass.info("Computing the sum across all input layers (this may take a while)")
    grass.run_command("r.series", quiet=True, output=tmp_1, input=IN, method="sum")

    # Create mask for all areas with sum=0, incorporate existing mask
    replmask = replacemask(inmap=tmp_1)

    for n in range(len(Q)):
        grass.info(_("Computing alpha = {n}").format(n=Q[n]))
        Qn = str(Q[n])
        Qn = Qn.replace(".", "_")
        renyi = OUT + "_Renyi_" + Qn
        if Q[n] == 1:
            # If alpha = 1
            # TODO See email 14-01-16 about avoiding loop below
            grass.mapcalc("$renyi = 0", renyi=renyi, quiet=True)
            for i in range(len(IN)):
                grass.info(
                    _("Computing map {j} from {n} maps").format(j=i + 1, n=len(IN))
                )
                tmp_2 = tmpname("sht")
                clean_rast.add(tmp_2)
                grass.mapcalc(
                    "$tmp_2 = if($inl == 0, $renyi, $renyi - (($inl/$tmp_1) * log(($inl/$tmp_1))))",
                    renyi=renyi,
                    tmp_2=tmp_2,
                    inl=IN[i],
                    tmp_1=tmp_1,
                    quiet=True,
                )
                grass.run_command(
                    "g.rename",
                    raster="{0},{1}".format(tmp_2, renyi),
                    overwrite=True,
                    quiet=True,
                )
        else:
            # If alpha != 1
            tmp_3 = tmpname("sht")
            clean_rast.add(tmp_3)
            tmp_4 = tmpname("sht")
            clean_rast.add(tmp_4)
            grass.mapcalc("$tmp_3 = 0", tmp_3=tmp_3, quiet=True)
            for i in range(len(IN)):
                grass.info(
                    _("Computing map {j} from {n} maps").format(j=i + 1, n=len(IN))
                )
                grass.mapcalc(
                    "$tmp_4 = if($inl == 0, $tmp_3, $tmp_3 + (pow($inl/$tmp_1,$alpha)))",
                    tmp_3=tmp_3,
                    tmp_4=tmp_4,
                    tmp_1=tmp_1,
                    inl=IN[i],
                    alpha=Q[n],
                    quiet=True,
                )
                grass.run_command(
                    "g.rename",
                    raster="{0},{1}".format(tmp_4, tmp_3),
                    overwrite=True,
                    quiet=True,
                )
            grass.mapcalc(
                "$outl = (1/(1-$alpha)) * log($tmp_3)",
                outl=renyi,
                tmp_3=tmp_3,
                alpha=Q[n],
                quiet=True,
            )
            grass.run_command(
                "g.remove", type="raster", name=tmp_3, flags="f", quiet=True
            )

    # --------------------------------------------------------------------------
    # Species richness, add 0 for areas with no observations
    # --------------------------------------------------------------------------

    # Remove mask  (or restore if there was one)
    if replmask == "nomask":
        grass.run_command("r.mask", flags="r", quiet=True)
    elif replmask is not "samemask":
        grass.run_command("g.rename", raster=(replmask, "MASK1"), quiet=True)
    if flag_s:
        grass.info("Computing species richness map")
        out_div = OUT + "_richness"
        in_div = OUT + "_Renyi_0_0"
        grass.mapcalc(
            "$out_div = if($tmp_1==0,0,exp($in_div))",
            out_div=out_div,
            in_div=in_div,
            tmp_1=tmp_1,
            quiet=True,
        )
        if 0.0 not in Qoriginal and not flag_e:
            grass.run_command(
                "g.remove", flags="f", type="raster", name=in_div, quiet=True
            )

    # Create mask for all areas with sum=0, incorporate existing mask
    replmask = replacemask(inmap=tmp_1)

    # --------------------------------------------------------------------------
    # Shannon index
    # --------------------------------------------------------------------------
    if flag_h:
        grass.info("Computing Shannon index map")
        out_div = OUT + "_shannon"
        in_div = OUT + "_Renyi_1_0"
        if 1.0 in Qoriginal or flag_e or flag_n:
            grass.run_command("g.copy", raster=(in_div, out_div), quiet=True)
        else:
            grass.run_command("g.rename", raster=(in_div, out_div), quiet=True)

    # --------------------------------------------------------------------------
    # Shannon Effective Number of Species (ENS)
    # --------------------------------------------------------------------------
    if flag_n:
        grass.info("Computing ENS map")
        out_div = OUT + "_ens"
        in_div = OUT + "_Renyi_1_0"
        grass.mapcalc(
            "$out_div = exp($in_div)", out_div=out_div, in_div=in_div, quiet=True
        )
        if 1.0 not in Qoriginal and not flag_e:
            grass.run_command(
                "g.remove", flags="f", type="raster", name=in_div, quiet=True
            )

    # --------------------------------------------------------------------------
    # Eveness
    # --------------------------------------------------------------------------
    if flag_e:
        grass.info("Computing Eveness map")
        out_div = OUT + "_eveness"
        in_div1 = OUT + "_Renyi_0_0"
        in_div2 = OUT + "_Renyi_1_0"
        grass.mapcalc(
            "$out_div = $in_div2 / $in_div1",
            out_div=out_div,
            in_div1=in_div1,
            in_div2=in_div2,
            quiet=True,
        )
        if 0.0 not in Qoriginal:
            grass.run_command(
                "g.remove", flags="f", type="raster", name=in_div1, quiet=True
            )
        if 1.0 not in Qoriginal:
            grass.run_command(
                "g.remove", flags="f", type="raster", name=in_div2, quiet=True
            )
    # --------------------------------------------------------------------------
    # Inversed Simpson index
    # --------------------------------------------------------------------------
    if flag_p:
        grass.info("Computing inverse simpson map")
        out_div = OUT + "_invsimpson"
        in_div = OUT + "_Renyi_2_0"
        grass.mapcalc(
            "$out_div = exp($in_div)", out_div=out_div, in_div=in_div, quiet=True
        )
        if 2.0 not in Qoriginal and not flag_g:
            grass.run_command(
                "g.remove", flags="f", type="raster", name=in_div, quiet=True
            )

    # --------------------------------------------------------------------------
    # Gini Simpson index
    # --------------------------------------------------------------------------
    if flag_g:
        grass.info("Computing Gini simpson map")
        out_div = OUT + "_ginisimpson"
        in_div = OUT + "_Renyi_2_0"
        grass.mapcalc(
            "$out_div = 1.0 - (1.0 / exp($in_div))",
            out_div=out_div,
            in_div=in_div,
            quiet=True,
        )
        if 2.0 not in Qoriginal:
            grass.run_command(
                "g.remove", flags="f", type="raster", name=in_div, quiet=True
            )

    # --------------------------------------------------------------------------
    # Remove mask  (or restore if there was one)
    # --------------------------------------------------------------------------
    if replmask == "nomask":
        grass.run_command("r.mask", flags="r", quiet=True)
    elif replmask is not "samemask":
        grass.run_command("g.rename", raster=(replmask, "MASK1"), quiet=True)

    # --------------------------------------------------------------------------
    # Total count (base unit, like individuals)
    # --------------------------------------------------------------------------
    if flag_t:
        rast = OUT + "_count"
        grass.run_command("g.rename", raster=(tmp_1, rast), quiet=True)
    else:
        grass.run_command("g.remove", type="raster", name=tmp_1, flags="f", quiet=True)


if __name__ == "__main__":
    options, flags = grass.parser()
    atexit.register(cleanup)
    sys.exit(main())
