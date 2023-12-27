#!/usr/bin/env python3

############################################################################
#
# MODULE:       r.model.eval
# AUTHOR(S):    Paulo van Breugel <paulo AT ecodiv.earth>
# PURPOSE:      To evaluate a binary classification predictions.
#
# NOTES:        The observed distribution of e.g., a species, land
#               cover unit or vegetation unit should be a binary map
#               with 1 (present) and 0 (absent). The values of the
#               modeled distribution can be any map that represents a
#               probability distribution in space. This could be based
#               on X, but it doesn't need to be. You can also, for example,
#               evaluate how well the modeled distribution of a species X
#               predicts the distribution of species Y or of land cover
#               type Y.
#
# COPYRIGHT: (C) 2014-2023 Paulo van Breugel
#            http://ecodiv.earth
#
#            This program is free software under the GNU General Public
#            License (>=v2). Read the file COPYING that comes with GRASS
#            for details.
#
########################################################################
#
# %Module
# % description: Computes evaluation statistics for a given prediction layer
# %End

# %option
# % key: reference
# % type: string
# % gisprompt: old,cell,raster
# % description: Name of raster layer containing references classes
# % key_desc: Raster name
# % required: yes
# % multiple: no
# % guisection: Input
# %end

# %option
# % key: prediction
# % type: string
# % gisprompt: old,cell,raster
# % description: Name of raster layer with predictions
# % key_desc: Raster name
# % required: yes
# % multiple: no
# % guisection: Input
# %end

# %option G_OPT_F_OUTPUT
# % key: csv
# % type: string
# % description: Name csv file with evaluation statistics
# % required: no
# % guisection: Output
# %end

# %option G_OPT_F_OUTPUT
# % key: figure
# % label: Name of the output file (extension decides format)
# % description: Name of the output file. The format is determined by the file extension.
# % required: no
# % guisection: Output
# %end

# %flag
# % key: p
# % description: Print plot to screen
# % guisection: Output
# %end

# %flag
# % key: b
# % description: Add presence to background
# % guisection: Evaluation area
# %end

# %option
# % key: buffer
# % type: double
# % description: Restrict absence area
# % key_desc: meter
# % required: no
# % guisection: Evaluation area
# %end

# %option
# % key: preval
# % type: double
# % description: Prevalence of presence points
# % key_desc: <0-1>
# % options: 0-1
# % required: no
# % guisection: Evaluation area
# %end

# %option
# % key: plot_dimensions
# % type: string
# % label: Plot dimensions (width,height)
# % description: Dimensions (width,height) of the figure in inches
# % required: no
# % answer: 6.4,4.8
# % guisection: Plot options
# %end

# %option
# % key: dpi
# % type: integer
# % label: DPI
# % description: Resolution of plot in dpi's
# % required: no
# % answer: 100
# % guisection: Plot options
# %end

# %option
# % key: fontsize
# % type: double
# % label: Font size
# % answer: 10
# % description: The basis font size (default = 10)
# % guisection: Plot options
# % required: no
# %end

# %option
# % key: n_bins
# % type: integer
# % description: Number of bins in which to divide the modeled distribution scores
# % key_desc: integer
# % answer: 200
# % required: no
# %end

# %option
# % key: presence
# % type: integer
# % description: Score that represent presence/true
# % key_desc: integer
# % answer: 1
# % required: no
# %end

# %option
# % key: absence
# % type: integer
# % description: Score that represent absence/false
# % key_desc: integer
# % answer: 0
# % required: no
# %end

import atexit
import sys
import uuid
import numpy as np
from subprocess import PIPE
import grass.script as gs
from grass.pygrass.modules import Module
import pandas as pd

clean_layers = []


def cleanup():
    """Remove temporary maps specified in the global list"""
    cleanrast = list(reversed(clean_layers))
    for rast in cleanrast:
        Module("g.remove", flags="f", type="all", name=rast, quiet=True)


def lazy_import_matplotlib():
    """Lazy import matplotlib modules"""
    global matplotlib
    global plt
    try:
        import matplotlib

        matplotlib.use("WXAgg")
        from matplotlib import pyplot as plt
    except ModuleNotFoundError:
        gs.fatal(_("Matplotlib is not installed. Please, install it."))


def lazy_import_pandas():
    """Lazy import pandas"""
    global pd
    try:
        import pandas as pd
    except ModuleNotFoundError:
        gs.fatal(_("Pandas is not installed. Please, install it."))


def create_unique_name(name):
    """Generate a temporary name which contains prefix
    Store the name in the global list.
    """
    return name + str(uuid.uuid4().hex)


def create_temporary_name(prefix):
    """Create temporary file name"""
    tmpf = create_unique_name(prefix)
    clean_layers.append(tmpf)
    return tmpf


def subsample_points(input, id, required_number):
    """Select random subset of map from rastercells with value 'id'

    :param str input: input raster layer (with 0 and 1)
    :param int id: raster value from which to select random subset
    :param int required_absence: number of raster cells to select

    :return str name output layer
    """
    reclass_rules = f"{id} = {id}\n* = NULL"
    tmp_prev1 = create_temporary_name("eval1_")
    Module(
        "r.reclass",
        input=input,
        output=tmp_prev1,
        rules="-",
        stdin_=reclass_rules,
    )
    tmp_prev2 = create_temporary_name("eval2_")
    Module(
        "r.random",
        input=tmp_prev1,
        npoints=int(required_number),
        raster=tmp_prev2,
        flags="s",
        quiet=True,
    )
    tmp_prev3 = create_temporary_name("eval3_")
    id2 = int(abs(np.round(id - 1 + 0.1)))
    Module(
        "r.mapcalc",
        expression=f"{tmp_prev3} = if({input}=={id2}, {input}, {tmp_prev2})",
    )
    return tmp_prev3


def compute_stats(modelled, reference, n_bins, background):
    """Create map with probability scores grouped in n.bins bins

    :param str modelled: name of prediction map
    :param str reference: name of binary map
    :param int n_bins: number of bins in which the prediction map is to be divided

    :return DataFrame classbounds_df Pandas dataframe
    :return DataFrame stats Pandas dataframe
    """

    stats = gs.parse_command("r.univar", map=modelled, flags="g")
    roc_steps = np.linspace(float(stats["min"]), float(stats["max"]), n_bins)[::-1]
    classbounds = list(
        zip(list(roc_steps)[:-1], list(roc_steps)[1:], list(range(1, n_bins, 1)))
    )
    classbounds_df = pd.DataFrame(classbounds, columns=["LB", "UB", "ID"])
    file_name = gs.tempfile()
    with open(file_name, "w") as file:
        for row in classbounds:
            file.write(f"{row[0]}:{row[1]}:{row[2]}\n")
    tmp_rocsteps = create_temporary_name("eval4_")
    Module("r.recode", input=modelled, output=tmp_rocsteps, rules=file_name)

    stat_presabs = Module(
        "r.stats",
        flags="cn",
        input=f"{reference},{tmp_rocsteps}",
        separator="pipe",
        stdout_=PIPE,
    ).outputs.stdout
    stats_outlines = stat_presabs.replace("\r", "").strip().split("\n")
    v1 = [float(z.split("|")[0]) for z in stats_outlines]
    v2 = [float(z.split("|")[1]) for z in stats_outlines]
    v3 = [float(z.split("|")[2]) for z in stats_outlines]
    df = pd.DataFrame(zip(v1, v2, v3), columns=["v1", "v2", "v3"])

    # Calculate evaluation stats per threshold
    dfw = pd.pivot_table(
        df, values="v3", index="v2", columns="v1", aggfunc="sum"
    ).fillna(0)
    dfw_sum = dfw.sum()
    dfw["FP"] = dfw.iloc[:, 0].cumsum()
    dfw["TP"] = dfw.iloc[:, 1].cumsum()
    dfw["TN"] = dfw_sum[0] - dfw["FP"]
    dfw["FN"] = (dfw_sum[0] + dfw_sum[1]) - (dfw["TP"] + dfw["FP"] + dfw["TN"])
    dfw = dfw.iloc[:, 2:6]
    dfw["TPR"] = dfw["TP"] / (dfw["TP"] + dfw["FN"])
    if background:
        dfw["FPR"] = dfw["FP"] / (dfw_sum[0] + dfw_sum[1])
    else:
        dfw["FPR"] = dfw["FP"] / (dfw["FP"] + dfw["TN"])
    dfw["TNR"] = dfw["TN"] / (dfw["TN"] + dfw["FP"])
    dfw["TSS"] = dfw["TPR"] - dfw["FPR"]
    dfw["kappa"] = (
        2
        * (dfw["TP"] * dfw["TN"] - dfw["FN"] * dfw["FP"])
        / (
            (dfw["TP"] + dfw["FP"]) * (dfw["FP"] + dfw["TN"])
            + (dfw["TP"] + dfw["FN"]) * (dfw["FN"] + dfw["TN"])
        )
    )
    dfw["distance"] = ((dfw["FPR"] - 0) ** 2 + (dfw["TPR"] - 1) ** 2) ** 0.5

    # Calculate stats
    dfw_stats = {}
    dfw_stats["auc"] = np.trapz(y=dfw["TPR"], x=dfw["FPR"])
    dfw_stats["tss_max"] = max(dfw["TSS"])
    dfw_stats["tss_threshold"] = classbounds_df["LB"][int(dfw["TSS"].idxmax())]
    dfw_stats["kappa_max"] = max(dfw["kappa"])
    dfw_stats["kappa_threshold"] = classbounds_df["LB"][int(dfw["kappa"].idxmax())]
    dfw_stats["min_dist_threshold"] = classbounds_df["LB"][
        int(dfw["distance"].idxmin())
    ]

    dfw["ID"] = dfw.index
    dfexport = pd.merge(classbounds_df, dfw, on="ID", how="left")

    return dfexport, dfw_stats


def roc_plot(X, Y, dimensions, fontsize, background):
    """
    Create roc plot

    :param list X: X values
    :param list Y: Y values
    :param list dimensions: plot dimensions (width, height)
    :param float fontsize: fontsize of all text (tic labes are 1pnt smaller)

    :return print ax, fig
    """

    fig, ax = plt.subplots(figsize=dimensions)
    plt.rcParams["font.size"] = fontsize
    for label in ax.get_xticklabels() + ax.get_yticklabels():
        label.set_fontsize(fontsize - 1)
    ax.plot([0, 1], [0, 1], color="grey", ls="-", linewidth=1)
    ax.plot(X, Y, color="blue", linewidth=1.5)
    plt.ylabel("True positive rate", fontsize=fontsize)
    if background:
        plt.xlabel("Fraction predicted of all points", fontsize=fontsize)
    else:
        plt.xlabel("False negative rate", fontsize=fontsize)
    ax.set_xticks(np.arange(0, 1.1, 0.1))
    ax.set_yticks(np.arange(0, 1.1, 0.1))
    plt.grid(True, color="lightgrey", lw=0.5)
    return ax, fig


def is_integer(input):
    """
    Check if a layer is an integer

    :param string input: name input layer

    :return bool true false
    """
    info = gs.parse_command("r.info", map=input, flags="g")
    data_type = info["datatype"]
    return data_type == "CELL"


def main(options, flags):
    """
    Computes evaluation statistics of an environmental distribution
    model, based on a layer with observed and a layer with predicted
    values.
    """

    # Check if reference layer is integer
    reference = options["reference"]
    if not is_integer(input=reference):
        gs.fatal("The 'reference' layer is not an integer map")

    # Check if reference map is binary
    vals = gs.read_command(
        "r.stats", flags="n", input=reference, separator="comma"
    ).splitlines()
    vals = [int(i) for i in vals]
    if len(vals) > 2:
        gs.fatal("The 'reference' layer is not binary")

    # Check presence/absence values
    abs_val = int(options["absence"])
    pres_val = int(options["presence"])
    if pres_val != 1 or abs_val != 0:
        tmp_ch = create_temporary_name("ch_5")
        recode_rules = f"{abs_val}:{abs_val}:0\n{pres_val}:{pres_val}:1"
        Module(
            "r.recode",
            input=reference,
            output=tmp_ch,
            rules="-",
            stdin_=recode_rules,
        )
        reference = tmp_ch
    else:
        if min(vals) != 0 or max(vals) != 1:
            gs.fatal(
                "The values of the 'reference' map are not 0 and 1.\n"
                "Give  the values for the 'absence' and 'presence'"
            )

    # Limit absence area to buffer around presence locations
    if options["buffer"]:
        buffer_absence = float(options["buffer"])
        tmp_a = create_temporary_name("eval5_")
        tmp_b = create_temporary_name("eval6_")
        tmp_c = create_temporary_name("eval7_")
        Module(
            "r.mapcalc",
            expression=f"{tmp_a} = if({reference} == 0, null(), {reference})",
            quiet=True,
        )
        Module(
            "r.buffer",
            input=tmp_a,
            output=tmp_b,
            distances=buffer_absence,
            units="meters",
            quiet=True,
        )
        Module(
            "r.mapcalc",
            expression=f"{tmp_c} = if({tmp_b} > 0, {reference}, null())",
        )
        reference = tmp_c

    # Prevalence
    if options["preval"]:
        prevalence = float(options["preval"])
        stats = gs.parse_command("r.univar", map=reference, flags="g")
        actual_presence = int(stats["sum"])
        actual_absence = int(stats["n"]) - actual_presence
        required_presence = np.ceil(float(stats["n"]) * prevalence)
        required_absence = int(stats["n"]) - required_presence
        if required_presence > actual_presence:
            required_presence = int(actual_presence)
            required_absence = np.ceil(
                (required_presence / prevalence) - required_presence
            )
            reference = subsample_points(
                input=reference, id=0, required_number=required_absence
            )
        if required_absence > actual_absence:
            required_presence = np.ceil(
                actual_absence / required_absence * required_presence
            )
            required_absence = actual_absence
            reference = subsample_points(
                input=reference, id=1, required_number=required_presence
            )

    # recode steps
    lazy_import_pandas()
    dfw, dfw_stats = compute_stats(
        modelled=options["prediction"],
        reference=reference,
        n_bins=int(options["n_bins"]) + 1,
        background=flags["b"],
    )
    gs.message(_("AUC = {}".format(round(dfw_stats["auc"], 4))))
    gs.message(_("maximum TSS =  {}".format(round(dfw_stats["tss_max"], 4))))
    gs.message(_("maximum kappa =  {}".format(round(dfw_stats["kappa_max"], 4))))
    gs.message(
        _("treshold maximum TSS = {}".format(round(dfw_stats["tss_threshold"], 4)))
    )
    gs.message(
        _("treshold maximum kappa = {}".format(round(dfw_stats["kappa_threshold"], 4)))
    )
    gs.message(
        _(
            "treshold minimum distance to (0,1) = {}".format(
                round(dfw_stats["min_dist_threshold"], 4)
            )
        )
    )
    if options["csv"]:
        dfw.drop(columns=["ID", "distance"])
        dfw.to_csv(options["csv"], index=False)

    # Show ROC plot
    if flags["p"] or bool(options["figure"]):
        lazy_import_matplotlib()
        plot_dimensions = [float(x) for x in options["plot_dimensions"].split(",")]
        fontsize = float(options["fontsize"])
        ax, p = roc_plot(
            X=dfw["FPR"],
            Y=dfw["TPR"],
            dimensions=plot_dimensions,
            fontsize=fontsize,
            background=flags["b"],
        )
    if bool(options["figure"]):
        p.savefig(options["figure"], bbox_inches="tight", dpi=float(options["dpi"]))
    if flags["p"]:
        p.tight_layout()
        plt.show(block=False)
        plt.show()


if __name__ == "__main__":
    atexit.register(cleanup)
    sys.exit(main(*gs.parser()))
