#!/usr/bin/env python

########################################################################
#
# MODULE:       r.mess
# AUTHOR(S):    Paulo van Breugel <paulo ecodiv earth>
# PURPOSE:      Calculate the multivariate environmental similarity
#               surface (MESS) as proposed by Elith et al., 2010,
#               Methods in Ecology & Evolution, 1(330–342).
#
# COPYRIGHT: (C) 2014-2024 by Paulo van Breugel and the GRASS Development
#            Team
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
# % key: ref_env
# % description: Reference conditions
# % key_desc: names
# % required: yes
# % guisection: reference
# %end

# %option G_OPT_R_INPUT
# % key: ref_rast
# % label: Reference area (raster)
# % description: Reference areas (1 = presence, 0 or null = absence)
# % key_desc: name
# % required: no
# % guisection: reference
# %end

# %option G_OPT_V_MAP
# % key: ref_vect
# % label: Reference points (vector)
# % description: Point vector layer with reference locations
# % key_desc: name
# % required: no
# % guisection: reference
# %end

# %option G_OPT_M_REGION
# % key: ref_region
# % label: Reference region
# % description: Region with reference conditions
# % required: no
# % guisection: reference
# %end

# %option G_OPT_R_INPUTS
# % key: proj_env
# % description: Projected conditions
# % key_desc: names
# % required: no
# % guisection: projected
# %end

# %option G_OPT_M_REGION
# % key: proj_region
# % label: Projection region
# % description: Region with projected conditions
# % required: no
# % guisection: projected
# %end

# %rules
# %exclusive: ref_rast,ref_vect,ref_region
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
# % options: 0-6
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

# %option G_OPT_M_NPROCS
# %end

# %option G_OPT_MEMORYMB
# %end

# import libraries
import os
import sys
import atexit
import uuid
import tempfile
import operator
import numpy as np
import subprocess
import grass.script as gs

COLORS_MES = """\
0% 244:109:67
0 255:255:255
100% 50:136:189
"""

RECL_MESNEG = """\
0|within range
1|novel conditions
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
    for chl in range(len(envlay)):
        ffile = gs.find_file(envlay[chl], element="cell")
        if not ffile["fullname"]:
            gs.fatal(_("The layer {} does not exist".format(envlay[chl])))


def create_unique_name(name):
    """Generate a temporary name which contains prefix
    Store the name in the global list.

    :param str name: prefix to be used for unique string

    :return str: Unique string with user defined prefix
    """
    unique_string = f"{name}{uuid.uuid4().hex}"
    return unique_string


def create_temporary_name(prefix):
    """Create temporary file name and add this to clean_maps

    :param str name: prefix to be used for unique string

    :return str: Unique string with user defined prefix
    """
    tmpf = create_unique_name(prefix)
    CLEAN_RAST.append(tmpf)
    return tmpf


def compute_ies(INtmprule, INipi, INtmpf2, INenvmin, INenvmax):
    """
    Compute the environmental similarity layer for the individual variables
    """
    tmpf3 = create_temporary_name("tmp6")
    gs.run_command("r.recode", input=INtmpf2, output=tmpf3, rules=INtmprule)
    if not gs.find_file(tmpf3, element="cell")["fullname"]:
        gs.fatal(_("Failed to recode raster layer"))

    calcc = (
        "{0} = if({1} == 0, (float({2}) - {3}) / ({4} - {3}) "
        "* 100.0, if({1} <= 50, 2 * float({1}), "
        "if({1} < 100, 2*(100-float({1})), "
        "({4} - float({2})) / ({4} - {3}) * 100.0)))".format(
            INipi, tmpf3, INtmpf2, float(INenvmin), float(INenvmax)
        )
    )
    gs.run_command("r.mapcalc", expression=calcc, quiet=True)
    gs.write_command(
        "r.colors",
        map=INipi,
        rules="-",
        stdin=COLORS_MES,
        quiet=True,
        stderr=subprocess.DEVNULL,
    )


def check_layer_type(ref_layer, type):
    """
    Checks if layers are of right type
    """
    # Reference / sample area or points
    if type == "point":
        topology_check = gs.vector_info_topo(ref_layer)
        if topology_check["points"] == 0:
            gs.fatal(
                _(
                    "the reference vector layer {} does not contain points".format(
                        ref_layer
                    )
                )
            )
    elif type == "raster":
        reftype = gs.raster_info(ref_layer)
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
    else:
        gs.message(_("Check format: correct"))


def create_reference_layer(ref_rast, reference_layer):
    """
    Create reference layer
    """
    gs.run_command(
        "r.mapcalc",
        expression=f"{ref_rast} = if(isnull({reference_layer}),null(),1)",
        quiet=True,
    )


def recode_reference_vector(
    ref_vect,
    ref_env_lay,
    proj_region,
    digits2,
    projection_layers,
    variable_name,
    ipi,
    tmphist,
):
    """
    Recode table based on reference vector
    """

    # Copy point layer and add columns for variables
    tmpf0 = create_temporary_name("tmp7")
    gs.run_command(
        "v.extract", flags="t", input=ref_vect, type="point", output=tmpf0, quiet=True
    )
    gs.run_command("v.db.addtable", quiet=True, map=tmpf0, stderr=subprocess.DEVNULL)

    # Upload raster values and get value in python as frequency table
    sql1 = "SELECT cat FROM {}".format(str(tmpf0))
    cn = len(np.hstack(gs.db.db_select(sql=sql1)))
    if not cn:
        gs.fatal(_("Database query failed or returned no results"))
    for m, reflay in enumerate(ref_env_lay):
        gs.message(_("Computing frequency distribution for {} ... ".format(reflay)))

        # Compute frequency distribution of variable(m)
        mid = str(m)
        laytype = gs.raster_info(reflay)["datatype"]
        if laytype == "CELL":
            columns = "envvar_{} integer".format(str(mid))
        else:
            columns = "envvar_{} double precision".format(str(mid))
        gs.run_command("v.db.addcolumn", map=tmpf0, columns=columns, quiet=True)
        sql2 = "UPDATE {} SET envvar_{} = NULL".format(str(tmpf0), str(mid))
        gs.run_command("db.execute", sql=sql2, quiet=True)
        coln = "envvar_{}".format(str(mid))
        gs.run_command(
            "v.what.rast",
            quiet=True,
            map=tmpf0,
            layer=1,
            raster=reflay,
            column=coln,
        )
        sql3 = (
            "SELECT {0}, count({0}) from {1} WHERE {0} IS NOT NULL "
            "GROUP BY {0} ORDER BY {0}"
        ).format(coln, tmpf0)
        volval = np.vstack(gs.db.db_select(sql=sql3))
        volval = volval.astype(float, copy=False)
        a = np.cumsum(volval[:, 1], axis=0)
        b = np.sum(volval[:, 1], axis=0)
        c = a / b * 100

        # Check for point without values
        if b < cn:
            gs.info(
                _(
                    "Please note that there were {} points without "
                    "value. This is probably because they are outside "
                    "the computational region or {} had no value "
                    "(nodata) for that point locations".format((cn - b), reflay)
                )
            )

        # Set region proj_region
        gs.use_temp_region()
        gs.run_command("g.region", region=proj_region)

        # Multiply env_proj layer with dignum
        tmpf2 = create_temporary_name("tmp8")
        gs.run_command(
            "r.mapcalc",
            expression="{0} = int({1} * {2})".format(
                tmpf2, digits2, projection_layers[m]
            ),
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
        a0 = a0.astype(int, copy=False)
        a1 = np.hstack([(e1), a0])
        a2 = np.hstack([a0 - 1, (e2)])
        b1 = np.hstack([(0), c])

        fd3, tmprule = tempfile.mkstemp(suffix=variable_name[m])
        with open(tmprule, "w") as text_file:
            for k in np.arange(0, len(b1)):
                rtmp = "{}:{}:{}\n".format(str(int(a1[k])), str(int(a2[k])), str(b1[k]))
                text_file.write(rtmp)

        # Create the recode layer and calculate the IES
        compute_ies(tmprule, ipi[m], tmpf2, envmin, envmax)
        gs.run_command(
            "r.support",
            map=ipi[m],
            title="IES {}".format(reflay),
            units="0-100 (relative score)",
            description="Environmental similarity {}".format(reflay),
            loadhistory=tmphist,
        )

        # Clean up
        os.close(fd3)
        os.remove(tmprule)

        # Change region back to original
        gs.del_temp_region()


def recode_reference_rasters(
    ref_env_lay,
    ref_rast,
    digits2,
    projection_layers,
    nprocs,
    variable_name,
    ipi,
    tmphist,
    ref_region,
    proj_region,
):
    """
    Recode table based on reference raster (and region)
    """
    if ref_rast:
        gs.run_command("r.mask", raster=ref_rast, quiet=True)
        tmpfmask = create_temporary_name("tmpmsk1")
        gs.run_command("g.rename", raster=f"MASK,{tmpfmask}", quiet=True)
    for i, envlay in enumerate(ref_env_lay):

        gs.message(_("Preparing the input data ..."))

        # set reference region
        gs.use_temp_region()
        gs.run_command("g.region", region=ref_region)

        # Create mask based on reference layer or environmental layers
        if ref_rast:
            gs.run_command("g.rename", raster=f"{tmpfmask},MASK", quiet=True)

        # Calculate the frequency distribution
        tmpf1 = create_temporary_name("tmp4")
        gs.run_command("r.mapcalc", expression=f"{tmpf1} = int({digits2} * {envlay})")
        stats_out = gs.read_command(
            "r.stats", flags="cn", input=tmpf1, sort="asc", separator=";"
        )
        stval = {}
        stats_outlines = stats_out.replace("\r", "").split("\n")
        stats_outlines = [_f for _f in stats_outlines if _f]
        for z in stats_outlines:
            [val, count] = z.split(";")
            stval[float(val)] = float(count)
        sstval = sorted(stval.items(), key=operator.itemgetter(0))
        sstval = np.matrix(sstval)
        a = np.cumsum(np.array(sstval), axis=0)
        b = np.sum(np.array(sstval), axis=0)
        c = a[:, 1] / b[1] * 100

        # Remove tmp mask and set region to proj_env or proj_region if needed
        if ref_rast:
            gs.run_command("g.rename", raster=f"MASK,{tmpfmask}", quiet=True)
        gs.del_temp_region()
        gs.use_temp_region()
        gs.run_command("g.region", region=proj_region)

        # Get min and max values for recode table
        tmpf2 = create_temporary_name("tmp5")
        gs.run_command(
            "r.mapcalc",
            expression=f"{tmpf2} = int({digits2} * {projection_layers[i]})",
        )
        d = gs.parse_command("r.univar", flags="g", map=tmpf2, nprocs=nprocs)
        if not d or "min" not in d or "max" not in d:
            gs.fatal(
                _("Failed to parse statistics from {}".format(projection_layers[i]))
            )

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

        fd2, tmprule = tempfile.mkstemp(suffix=variable_name[i])
        with open(tmprule, "w") as text_file:
            for k in np.arange(0, len(b1.T)):
                text_file.write(
                    "%s:%s:%s\n" % (str(int(a1[k])), str(int(a2[k])), str(b1[k]))
                )

        # Create the recode layer and calculate the IES
        gs.message(_("Calculating IES for {} ...".format(envlay)))
        compute_ies(tmprule, ipi[i], tmpf2, envmin, envmax)
        gs.run_command(
            "r.support",
            map=ipi[i],
            title="IES {}".format(envlay),
            units="0-100 (relative score)",
            description="Environmental similarity {}".format(envlay),
            loadhistory=tmphist,
        )

        # Clean up
        os.close(fd2)
        os.remove(tmprule)

        # Change region back to original
        gs.del_temp_region()


def main(options, flags):

    # Check if there is a MASK
    mask_present = gs.find_file(
        name="MASK", element="cell", mapset=gs.gisenv()["MAPSET"]
    )
    if mask_present and mask_present["fullname"]:
        gs.fatal(_("Please remove the MASK before using r.mess."))

    # Check if reference layers are of right type
    ref_vect = options["ref_vect"]
    if ref_vect:
        check_layer_type(ref_vect, "point")
    ref_rast = options["ref_rast"]
    if ref_rast:
        check_layer_type(ref_rast, "raster")

    # Settings
    nprocs = int(options["nprocs"])
    memory = int(options["memory"])

    # old environmental layers & variable names
    ref_env_lay = options["ref_env"]
    ref_env_lay = ref_env_lay.split(",")
    raster_exists(ref_env_lay)
    variable_name = [z.split("@")[0] for z in ref_env_lay]
    variable_name = [x.lower() for x in variable_name]

    # new environmental variables
    projection_layers = options["proj_env"]
    if not projection_layers:
        projection_layers = ref_env_lay
    else:
        projection_layers = projection_layers.split(",")
        raster_exists(projection_layers)
        if len(projection_layers) != len(ref_env_lay) and len(projection_layers) != 0:
            gs.fatal(
                _(
                    "The number of reference and predictor variables"
                    " should be the same. You provided {} reference and {}"
                    " projection variables".format(
                        len(ref_env_lay), len(projection_layers)
                    )
                )
            )

    # output layers
    opl = options["output"]
    opc = opl + "_MES"
    ipi = [opl + "_" + i for i in variable_name]

    # digits / precision
    digits = int(options["digits"])
    digits2 = pow(10, digits)

    # Text for history in metadata
    opt2 = dict((k, v) for k, v in options.items() if v)
    hist = " ".join("{!s}={!r}".format(k, v) for (k, v) in opt2.items())
    hist = "r.mess {}".format(hist)
    unused, tmphist = tempfile.mkstemp()
    with open(tmphist, "w") as text_file:
        text_file.write(hist)

    # Create reference region
    ref_region = options["ref_region"]
    tmprefreg = create_temporary_name("tmpreg1")
    if ref_region:
        gs.run_command("g.region", region=ref_region)
        tmprefreg = ref_region
    elif ref_rast:
        gs.run_command("g.region", raster=ref_rast)
        gs.run_command("g.region", save=tmprefreg)
    else:
        gs.run_command("g.region", save=tmprefreg)

    # Create projection region
    proj_region = options["proj_region"]
    tmpprojreg = create_temporary_name("tmpreg2")
    if proj_region:
        gs.run_command("g.region", region=proj_region)
        tmpprojreg = proj_region
    else:
        gs.run_command("g.region", raster=projection_layers[0])
        gs.run_command("g.region", save=tmpprojreg)

    # Create recode table
    gs.run_command("g.region", region=tmprefreg)
    if ref_vect:
        # Recode table based on reference vector
        recode_reference_vector(
            ref_vect,
            ref_env_lay,
            tmpprojreg,
            digits2,
            projection_layers,
            variable_name,
            ipi,
            tmphist,
        )
    else:
        # Recode table based on reference raster (and region)
        recode_reference_rasters(
            ref_env_lay,
            ref_rast,
            digits2,
            projection_layers,
            nprocs,
            variable_name,
            ipi,
            tmphist,
            tmprefreg,
            tmpprojreg,
        )
    # Set temporary region to projected region
    gs.use_temp_region()
    gs.run_command("g.region", region=tmpprojreg)

    # Calculate MESS statistics
    gs.message(_("Calculating MESS statistics ..."))
    gs.run_command(
        "r.series",
        quiet=True,
        output=opc,
        input=ipi,
        method="minimum",
        nprocs=nprocs,
        memory=memory,
    )
    gs.write_command(
        "r.colors",
        map=opc,
        rules="-",
        stdin=COLORS_MES,
        quiet=True,
        stderr=subprocess.DEVNULL,
    )

    # Write layer metadata
    gs.run_command(
        "r.support",
        map=opc,
        title="Areas with novel conditions",
        units="0-100 (relative score)",
        description="The multivariate environmental similarity" "(MES)",
        loadhistory=tmphist,
    )

    # Area with negative MES
    if flags["n"]:
        gs.message(_("Calculate Area with negative MES"))
        mod1 = f"{opl}_novel"
        gs.run_command("r.mapcalc", expression=f"{mod1} = if( {opc} < 0, 1, 0)")

        # Write category labels
        gs.write_command(
            "r.category",
            map=mod1,
            rules="-",
            stdin=RECL_MESNEG,
            separator="|",
            quiet=True,
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
    if flags["m"]:
        gs.message(_("Calculate Most dissimilar variable (MoD)"))
        tmpf4 = create_temporary_name("tmp9")
        mod2 = "{}_MoD".format(opl)
        gs.run_command(
            "r.series",
            quiet=True,
            output=tmpf4,
            input=ipi,
            method="min_raster",
            nprocs=nprocs,
            memory=memory,
        )
        gs.run_command("r.mapcalc", expression=f"{mod2} = int({tmpf4})", quiet=True)

        fd4, tmpcat = tempfile.mkstemp()
        with open(tmpcat, "w") as text_file:
            for cats in range(len(ipi)):
                text_file.write(f"{str(cats)}:{ref_env_lay[cats]}\n")
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
    if flags["k"]:
        gs.message(_("Calculate sum(IES), where IES < 0 ..."))
        mod3 = "{}_SumNeg".format(opl)
        c0 = -0.01 / digits2
        gs.run_command(
            "r.series",
            quiet=True,
            input=ipi,
            method="sum",
            range=("-inf", c0),
            output=mod3,
            nprocs=nprocs,
            memory=memory,
        )
        gs.write_command(
            "r.colors",
            map=mod3,
            rules="-",
            stdin=COLORS_MES,
            quiet=True,
            stderr=subprocess.DEVNULL,
        )

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
    if flags["c"]:
        gs.message(_("Calculate number of layers with negative values ..."))
        tmpf5 = create_temporary_name("tmp10")
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
            nprocs=nprocs,
            memory=memory,
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
    if flags["i"]:
        gs.run_command("g.remove", quiet=True, flags="f", type="raster", name=ipi)
    # Clean up tmp file
    # os.remove(tmphist)

    gs.message(_("Finished ...\n"))
    gs.del_temp_region()


if __name__ == "__main__":
    atexit.register(cleanup)
    sys.exit(main(*gs.parser()))
