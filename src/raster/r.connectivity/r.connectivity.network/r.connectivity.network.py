#!/usr/bin/env python
# -*- coding: UTF-8 -*-

"""
MODULE:       r.connectivity.network
AUTHOR(S):    Stefan Blumentrath <stefan dot blumentrath at nina dot no>
PURPOSE:      Compute connectivity measures for a set of habitat patches
              based on graph-theory (using the igraph-package in R).

              Recently, graph-theory has been characterised as an
              efficient and useful tool for conservation planning
              (e.g. Bunn et al. 2000, Calabrese & Fagan 2004,
              Minor & Urban 2008, Zetterberg et. al. 2010).
              As a part of the r.connectivity.* tool-chain,
              r.connectivity.network is intended to make graph-theory
              more easily available to conservation planning.

              r.connectivity.network is the 2nd tool of the
              r.connectivity.* toolchain and performs the (core) network
              analysis (using the igraph-package in R) on the network
              data prepared with r.connectivity.distance. This network
              data is analysed on graph, edge and vertex level.

              Connectivity measures for the graph level are: number of
              vertices, number of edges, number of clusters, size of the
              largest cluster, average cluster size, diameter, density,
              modularity, number of communities, community size (in
              number of vertices) Network characteristics are visualised
              in a plot showing an  overview over the number of connections,
              number of components and the size of the largest
              network component within the network with regards
              to cost-distance between patches.

              Connectivity measures calculated for the edges are:
              Minimum-spanning-trees, directness, edge-betweenness,
              local edge-betweenness, edge-betweenness-community,
              bridges (biconnected components), tree edges
              (biconnected components), and potential connectors of
              clusters and communities.

              Connectivity measures calculated for the vertices are:
              Degree-centrality, Eigenvector-centrality, closeness
              centrality, vertex-betweenness, local vertex-betweenness,
              cluster-membership, edge betweenness community  structure,
              community-membership, neighbourhood size, local
              neighbourhood size, articulation points, and articulation.

              Most measured can be calculated both on a directed and/or
              an undirected graph.

              Analysis is based on a negative exponential decay kernel
              (as described e.g. in Bunn et al. (2000), which the user
              can modify according to the dispersal characteristics of
              her/his species or habitat type.

              !!!This script is designed to work based on the output of
              r.connectivity.distance!!!

COPYRIGHT:    (C) 2011, 2018 by the Norwegian Institute for Nature
                                    Research (NINA)

              This program is free software under the GNU General Public
              License (>=v2). Read the file COPYING that comes with
              GRASS for details.

########################################################################
REQUIREMENTS:
R with packages igraph (version 1.0) and nlme (for parallel processing
doMC, multicore, iterators, codetools and foreach are required as well),
ghostscript is required for postscript-output

ToDo:
- replace R with Python
- add RGB columns instead of QML
- Fix history assignment
- - grass.parse_command('v.support', map=edges, flags='g')[comments]
- - grass.parse_command('v.support', map=nodes, flags='g')[comments]
"""

# %Module
# % description: Compute connectivity measures for a set of habitat patches based on graph-theory
# % keyword: raster
# % keyword: vector
# % keyword: graph theory
# % keyword: network
# % keyword: network analysis
# %End

# %option G_OPT_V_INPUT
# % required: yes
# % key_desc: Network computed with r.connectivity.distance (input)
# % description: Name of input vector map containing the network produced with r.connectivity.distance
# %end

# %option G_OPT_M_DIR
# % type: string
# % key: qml_style
# % required: no
# % description: Directory for output of QML files for layer styling in QGIS
# %end

# %option
# % type: string
# % key: prefix
# % required: yes
# % description: Prefix for output tables
# %end

# %option
# % key: connectivity_cutoff
# % type: double
# % description: Maximum cost distance for connectivity
# % guisection: Settings
# % required: no
# % answer: 0.0
# %end

# %option
# % key: lnbh_cutoff
# % type: double
# % description: Threshold defining a locale neighborhood (neighborhood = number of times connectivity_cutoff)
# % guisection: Settings
# % required: no
# % answer: 3.0
# %end

# %option
# % key: convergence_threshold
# % type: double
# % description: Convergence threshold for the overview plot over the graph
# % guisection: Settings
# % required: no
# % answer: 0.05
# %end

# %option
# % key: cl_thresh
# % type: integer
# % description: Number of community levels to be traced in edge betweenness community
# % guisection: Settings
# % required: no
# % answer: 0
# %end

# Temporarily disabled
##%flag
##% key: y
##% description: Calculate edge betweenness community (default is do not).
##% guisection: Measures
##%end

# %option
# % key: base
# % type: double
# % description: A factor for defining the shape of the negative exponential decay kernel (e ^ base * exponent)
# % guisection: Kernel
# % required: no
# % answer: -3.0
# %end

# %option
# % key: exponent
# % type: double
# % description: Exponent of the negative exponential decay kernel (e ^ base * exponent)
# % guisection: Kernel
# % required: no
# % answer: -4.5
# %end

# %flag
# % key: x
# % description: Visualise negative exponential decay kernel and exit
# % guisection: Output
# %end

# %option G_OPT_F_OUTPUT
# % key: kernel_plot
# % description: File name for a plot of the negative exponential decay kernel (e ^ base * exponent) used in analysis (requires ghostscript installed)
# % required : no
# % guisection: Output
# %end

# %option G_OPT_F_OUTPUT
# % key: overview_plot
# % description: File name for a plot of an overview over network characteristics (requires ghostscript installed)
# % required : no
# % guisection: Output
# %end

# %option
# % key: cores
# % type: integer
# % description: Number of cores to be used for computation (if <= 1 no parallelisation is applied)
# % guisection: Parallelisation
# % required: no
# % answer: 1
# %end

# %flag
# % key: i
# % description: Install required R packages in an interactive session if they are missing
# %end

# %flag
# % key: r
# % description: Remove indirect connections from network
# %end

import atexit
import os
import sys
import platform
import warnings
import numpy as np
import grass.script as grass
import grass.script.task as task
import grass.script.db as grass_db


# check if GRASS is running or not
if "GISBASE" not in os.environ:
    sys.exit("You must be in GRASS GIS to run this program")


def cleanup():
    """tmp_maps = grass.read_command("g.list",
                                  type=['vector', 'raster'],
                                  pattern='{}*'.format(TMP_prefix),
                                  separator=',')

    if tmp_maps:
        grass.run_command("g.remove", type=['vector', 'raster'],
                          pattern='{}*'.format(TMP_prefix), quiet=True,
                          flags='f')
    #grass.del_temp_region()"""
    pass


def is_number(string):
    """Check if a string can be converted to numeric"""

    try:
        complex(string)  # for int, long, float and complex
    except ValueError:
        return False

    return True


def main():
    """Do the main work"""

    try:
        import rpy2
        import rpy2.rinterface

        rpy2.rinterface.set_initoptions(
            (b"rpy2", b"--no-save", b"--no-restore", b"--quiet")
        )
        import rpy2.robjects as robjects

        # rpy2 throws lots of warnings (that cannot be suppressed)
        # when packages are loaded
        warnings.filterwarnings("ignore")
        import rpy2.robjects.packages as rpackages
        from rpy2.robjects.vectors import StrVector
        import rpy2.robjects.numpy2ri
    except ImportError:
        grass.fatal(
            _(
                "Cannot import rpy2 (https://rpy2.bitbucket.io)"
                " library."
                " Please install it (pip install rpy2)"
                " or ensure that it is on path"
                " (use PYTHONPATH variable)."
            )
        )

    import matplotlib

    matplotlib.use("wxAGG")  # required by windows
    import matplotlib.pyplot as plt

    # Input variables
    network_map = options["input"]
    # network_mapset = network_map.split('@')[0]
    # network = network_map.split('@')[1] if len(network_map.split('@'))
    # > 1 else None
    prefix = options["prefix"]
    cores = options["cores"]
    convergence_treshold = options["convergence_threshold"]
    euler = np.exp(1)
    base = float(options["base"])
    exponent = float(options["exponent"])
    qml_style_dir = options["qml_style"]
    if is_number(options["connectivity_cutoff"]):
        if float(options["connectivity_cutoff"]) > 0:
            connectivity_cutoff = float(options["connectivity_cutoff"])
        else:
            grass.fatal('"connectivity_cutoff" has to be > 0.')
    else:
        grass.fatal('Option "connectivity_cutoff" is not given as a number.')
    lnbh_cutoff = options["lnbh_cutoff"]
    cl_thresh = options["cl_thresh"]

    cd_cutoff = connectivity_cutoff

    kernel_plot = options["kernel_plot"]
    overview_plot = options["overview_plot"]

    verbose = grass.verbosity() == 3
    overwrite = grass.overwrite()

    edge_output = "{}_edge_measures".format(prefix)
    edge_output_tmp = "{}_edge_measures_tmp".format(prefix)
    vertex_output = "{}_vertex_measures".format(prefix)
    vertex_output_tmp = "{}_vertex_measures_tmp".format(prefix)
    network_output = "{}_network_measures".format(prefix)

    # Check if input parameters are correct
    for table in [vertex_output, edge_output, network_output]:
        if grass.db.db_table_exist(table) and not overwrite:
            grass.fatal(
                'Table "{}" already exists. \
                         Use --o flag to overwrite'.format(
                    table
                )
            )

    if qml_style_dir:
        if not os.path.exists(qml_style_dir):
            grass.fatal(
                'QML output requested but directory "{}" \
                        does not exists.'.format(
                    qml_style_dir
                )
            )
        if not os.path.isdir(qml_style_dir):
            grass.fatal(
                'QML output requested but "{}" is not a \
                        directory.'.format(
                    qml_style_dir
                )
            )
        if not os.access(qml_style_dir, os.R_OK):
            grass.fatal(
                'Output directory "{}" for QML files is not \
                        writable.'.format(
                    qml_style_dir
                )
            )

    for plot in [kernel_plot, overview_plot]:
        if plot:
            if not os.path.exists(os.path.dirname(plot)):
                grass.fatal(
                    'Directory for output "{}" does not \
                            exists.'.format(
                        plot
                    )
                )
            if not os.access(os.path.dirname(plot), os.R_OK):
                grass.fatal(
                    'Output directory "{}" is not \
                            writable.'.format(
                        plot
                    )
                )

    # Visualise negative exponential decay kernel and exit
    x_flag = flags["x"]

    # Calculate edge betweenness community (default is do not)
    # y_flag = flags['y']

    # Install missing R packages
    i_flag = flags["i"]

    # Remove indirect connections from network
    r_flag = flags["r"]

    db_connection = grass_db.db_connection()
    # parse_command('db.connect', flags='g')
    db_name = grass.read_command("db.databases").rstrip("\n")

    net_hist_str = grass.parse_command(
        "v.info", map=network_map, flags="h", delimiter=":"
    )["COMMAND"].split("\n")[0]
    # grass.parse_command('v.info', map=network_map, flags='h'
    #                     ).split('\n')[0].split(': ')[1]
    # Parsing goes wrong in some cases (extracting with -tp) as input
    dist_cmd_dict = task.cmdstring_to_tuple(net_hist_str)
    command = os.environ["CMDLINE"]

    dist_prefix = dist_cmd_dict[1]["prefix"]
    pop_proxy = dist_cmd_dict[1]["pop_proxy"]

    in_vertices = "{}_vertices".format(dist_prefix)

    # OS adjustment
    os_type = platform.system()

    robjects.numpy2ri.activate()

    grass.verbose("prefix is {}".format(prefix))
    grass.verbose("cores is {}".format(cores))
    grass.verbose("convergence_treshold is {}".format(convergence_treshold))
    grass.verbose("euler is {}".format(euler))
    grass.verbose("base is {}".format(base))
    grass.verbose("exponent is {}".format(exponent))
    grass.verbose("cd_cutoff is {}".format(cd_cutoff))
    grass.verbose("connectivity_cutoff is {}".format(connectivity_cutoff))
    grass.verbose("lnbh_cutoff is {}".format(lnbh_cutoff))
    grass.verbose("kernel_plot is {}".format(kernel_plot))
    grass.verbose("overview_plot is {}".format(overview_plot))
    grass.verbose("dist_prefix is {}".format(dist_prefix))
    grass.verbose("EDGES is {}_edges".format(prefix))
    grass.verbose("VERTICES is {}_vertices".format(prefix))
    grass.verbose("cl_thresh is {}".format(cl_thresh))

    # Check if R is installed
    if not grass.find_program("R"):
        grass.fatal(
            "R is required, but cannot be found on the system.\n \
                    Please make sure that R is installed and the path \
                    to R is added to the environment variables \
                    (see: http://grass.osgeo.org/wiki/R_statistics#MS_Windows). \
                    After that a restart of GRASS GIS is required."
        )

    # Visualise the negative exponential decay kernel and exit (if requested)
    if x_flag:
        rscript = """euler <- {euler}
        basis <- {base}
        exponent <- {exponent}
        cd_cutoff <- {cd_cutoff}
        matplot((0:cd_cutoff/1000),
                (euler^((basis*(10^exponent))*(0:cd_cutoff))),
                type=\"l\",
                xlab=c(\"Cost distance (in 1000)\"),
                ylab=\"Potential flow between patches\")
        locator(n = 1, type = \"n\")""".format(
            euler=euler, base=base, exponent=exponent, cd_cutoff=cd_cutoff
        )

    if x_flag or kernel_plot:
        if x_flag:
            plt.ion()

        fig = plt.figure()
        # ax = plt.axes()
        x_values = np.linspace(0, cd_cutoff, 1000)

        plt.plot(x_values, np.exp(base * (np.power(10.0, exponent)) * x_values))

        # Simplified version could be
        # plt.plot(x, np.exp(exponent*x))

        if x_flag:
            fig.show()
            plt.waitforbuttonpress()
            sys.exit(0)
        elif kernel_plot:
            fig.savefig(kernel_plot)

    if cores > 1 and os_type == "Windows":
        grass.warning(
            "Parallel processing not yet supported on MS Windows. \
                       Setting number of cores to 1."
        )
        cores = 1

    # Check if ghostscript is installed
    if overview_plot:
        if os_type == "Windows":
            # grass.warning("Ghostscript is required. Assuming
            # ghostscript is installed on MS Windows")
            # Check for ghostscript deactivated on Windows because the
            # path to gswin32 is not defined in the environment settings
            # by ghostscript installation automatically
            if not grass.shutil_which("gswin32") and not grass.shutil_which(
                "gswin32.exe"
            ):
                grass.fatal(
                    "ghostscript is required for postscript \
                            output, cannot find ghostscript \
                            (gswin32.exe), please install ghostscript \
                            first (or check environment path settings)"
                )

        else:
            if not grass.shutil_which("gs") and not grass.shutil_which("ghostscript"):
                grass.fatal(
                    "ghostscript is required for postscript \
                            output, please install ghostscript first"
                )

    req_packages = ["igraph", "nlme", "rgrass7", "DBI"]
    if cores > 1 and os_type != "Windows":
        req_packages = req_packages + ["doMC", "foreach", "iterators", "codetools"]

    rscript = "unique(sort(row.names(installed.packages())))"
    installed_packages = robjects.r(rscript)

    missing_packages = np.setdiff1d(req_packages, installed_packages)

    if i_flag and missing_packages:
        grass.warning(
            "Installing required R-packages {} on \
                      request.".format(
                ",".join(missing_packages)
            )
        )
        utils = rpackages.importr("utils")
        utils.chooseCRANmirror(ind=1)
        utils.install_packages(StrVector(missing_packages))
    elif missing_packages:
        grass.fatal(
            "The following required R-packages {} are issing \
                    on your system. Please install \
                    them.".format(
                ",".join(missing_packages)
            )
        )

    # Check igraph version
    rscript = """if(as.double(substr(
                    packageDescription("igraph",
                                       fields = c("Version")),1,3)
                    )<=0.6) packageDescription("igraph",
                                               fields = c("Version"))"""
    igraph_version = robjects.r(rscript)

    if not isinstance(igraph_version, rpy2.rinterface.RNULLType):
        if i_flag:
            grass.warning(
                "The required igraph version is 0.6-2 or \
                          later, the installed version is {}. \
                          Installing latest version of igraph on \
                          request.".format(
                    igraph_version
                )
            )
            utils.install_packages("igraph")
        else:
            grass.fatal(
                "The required igraph version is 0.6-2 or \
                         later, the installed version is {}. \
                         Please download and install at least igraph \
                         version 0.6-2".format(
                    igraph_version
                )
            )

    rscript = """
########################################################################
###Preparation
########################################################################
verbose <- {}

if (verbose) {{
cat("Loading variables and packages...\n")
}}

library(igraph)
library(nlme)
library(codetools)
library(rgrass7)
library(DBI)
""".format(
        "{}".format(verbose).upper()
    )

    if cores > 1:
        rscript += """
# library(multicore)
library(iterators)
library(foreach)
library(doMC)

registerDoMC()
options(cores = {})
""".format(
            cores
        )

    rscript += """
# Variables
convergence_threshold <- {convergence_treshold}
euler <- {euler}
basis <- {base}
exponent <- {exponent}
remove_indirect <- {r_flag}
cd_cutoff <- {cd_cutoff}
connectivity_cutoff <- {connectivity_cutoff}
lnbh_cutoff <- {lnbh_cutoff}
cl_thresh <- {cl_thresh}
db <- "{database}"
db_driver <- "{driver}"
db_schema <- "{schema}"
qml_directory <- '{qml_style_dir}'
in_edges <- "{network_map}"
in_vertices <- '{in_vertices}'
overwrite <- {overwrite}
command <- '{command}'
pop_proxy <- '{pop_proxy}'

#Output files
#Path to kernel plot file
decay_kernel_ps <- '{kernel_plot}'

#Path to output overview plot file
network_overview_ps <- '{overview_plot}'

# Tables with connectivity measures
network_output <- '{network_output}'
vertex_output <- '{vertex_output}'
edge_output <- '{edge_output}'
""".format(
        convergence_treshold=convergence_treshold,
        euler=euler,
        base=base,
        exponent=exponent,
        pop_proxy=pop_proxy,
        r_flag="{}".format(r_flag).upper(),
        cd_cutoff=cd_cutoff,
        connectivity_cutoff=connectivity_cutoff,
        lnbh_cutoff=lnbh_cutoff,
        cl_thresh=cl_thresh,
        kernel_plot=kernel_plot,
        overview_plot=overview_plot,
        driver=db_connection["driver"],
        database=db_name,
        schema=db_connection["schema"],
        qml_style_dir=qml_style_dir,
        in_vertices=in_vertices,
        edge_output=edge_output_tmp,
        vertex_output=vertex_output_tmp,
        network_output=network_output,
        network_map=network_map,
        overwrite="{}".format(overwrite).upper(),
        command=command,
    )

    rscript += """
#network_measures <- paste(prefix, "network_measures", sep="_")
#edge_output <- paste(prefix, "edge_measures", sep="_")
#vertex_output <- paste(prefix, "vertex_measures", sep="_")
#network_output <- paste(prefix, "network_measures", sep="_")

if (decay_kernel_ps != "") {{
if (verbose) {{
cat("Exporting a plot of the negative exponential decay kernel...\n")
}}

########################################################################
#Plot the negative exponential decay kernel
ps.options(encoding="CP1257.enc", family="Helvetica", horizontal=FALSE, fonts="Helvetica", paper="a4", pointsize=1/96, height=3.5, width=3.5)
postscript(decay_kernel_ps)
matplot((0:cd_cutoff/(10^(nchar(as.integer(cd_cutoff))-2))), (euler^((basis*(10^exponent))*(0:cd_cutoff))), type="l", xlab=paste(c("Cost distance (in ", as.character(10^(nchar(as.integer(cd_cutoff))-2)), ")"), sep="", collapse=""), ylab="Potential flow between patches")
off <- dev.off(dev.cur())
}}

########################################################################
###Construct graph
if (verbose) {{
cat("Reading and preparing input data...\n")
}}

goutput <- execGRASS('v.db.select', map=in_vertices, columns=paste('cat', pop_proxy, sep=','), separator=',', intern=TRUE)
con <- textConnection(goutput)
v <- read.csv(con, header=TRUE)
names(v) <- c('patch_id', 'pop_proxy')

#Read and group edge data
goutput <- execGRASS('v.db.select', map=in_edges, columns='cat,from_p,to_p,dist', separator=',', intern=TRUE)
con <- textConnection(goutput)
e_df <- read.csv(con, header=TRUE)

#e_df <- data.frame(from_p=e_pre[,1], to_p=e_pre[,2], dist=e_pre[,3])
#e_groups <- groupedData(dist ~ from_p | from_p/to_p, data=as.data.frame(e_df), FUN=mean)
#e_grouped <- gsummary(e_groups, mean)
con_id_u_pre <- unlist(mclapply(mc.cores={0}, 1:length(e_df$from_p), function(x) paste(sort(c(e_df$from_p[x], e_df$to_p[x]))[1], sort(c(e_df$from_p[x], e_df$to_p[x]))[2], sep="_")))
con_id_u_pre_df <- data.frame(con_id_u_pre=unique(con_id_u_pre), con_id_u=1:length(unique(con_id_u_pre)))
e_grouped_df_pre <- merge(data.frame(con_id_u_pre=con_id_u_pre, con_id=1:length(e_df$from_p), from_p=e_df$from_p, to_p=e_df$to_p, dist=e_df$dist), con_id_u_pre_df, all.x=TRUE)
e_groups_ud <- groupedData(dist ~ 1 | con_id_u, data=e_grouped_df_pre, FUN=mean)
e_grouped_ud <- gsummary(e_groups_ud, mean)
e_grouped_ud_df <- data.frame(con_id_u=as.vector(e_grouped_ud$con_id_u), dist_ud=as.vector(e_grouped_ud$dist))
e_grouped_df <- merge(data.frame(con_id=as.integer(e_grouped_df_pre$con_id), con_id_u=as.integer(e_grouped_df_pre$con_id_u), from_p=as.integer(e_grouped_df_pre$from_p), to_p=as.integer(e_grouped_df_pre$to_p), dist=as.double(e_grouped_df_pre$dist)), e_grouped_ud_df, all.x=TRUE)

##Remove connections longer than cost distance threshold if requested
#if(remove_longer_cutoff == 1) {{
#con_id_true <-  e_grouped_df$con_id[grep(TRUE, e_grouped_df$dist_ud<cd_cutoff)]
#e_grouped_df_pre <- merge(data.frame(con_id=con_id_true), e_grouped_df)
#con_id_u_df <- data.frame(con_id_u_old=unique(e_grouped_df_pre$con_id_u), con_id_u=1:length(unique(e_grouped_df_pre$con_id_u)))
#e_grouped_df <- merge(data.frame(con_id_old=e_grouped_df_pre$con_id, con_id_u_old=e_grouped_df_pre$con_id_u, con_id=1:length(e_grouped_df_pre$con_id), from_p=e_grouped_df_pre$from_p, to_p=e_grouped_df_pre$to_p, dist=e_grouped_df_pre$dist, dist_ud=e_grouped_df_pre$dist_ud), con_id_u_df, all.x=TRUE)
#}}

#Merge vertex and grouped edge data
from_pop <- merge(data.frame(con_id=e_grouped_df$con_id, from_p=e_grouped_df$from_p), data.frame(from_p=as.integer(v$patch_id), from_pop=as.double(v$pop_proxy)), all.x=TRUE, sort=FALSE)
to_pop <- merge(data.frame(con_id=e_grouped_df$con_id, to_p=e_grouped_df$to_p), data.frame(to_p=as.integer(v$patch_id), to_pop=as.double(v$pop_proxy)), all.x=TRUE, sort=FALSE)
e <- merge(merge(from_pop, to_pop, sort=TRUE), data.frame(con_id=e_grouped_df$con_id, con_id_u=e_grouped_df$con_id_u, cost_distance=e_grouped_df$dist, cd_u=e_grouped_df$dist_ud), by="con_id", sort=TRUE)

#Calculate attributes representing proxies for potential flow between patches
distance_weight_e <- euler^((basis*(10^exponent))*(e$cost_distance))
distance_weight_e_ud <- euler^((basis*(10^exponent))*(e$cd_u))
#out_areal_distance_weight_e <- e$from_pop*distance_weight_e
#in_areal_distance_weight_e <- e$to_pop*distance_weight_e

mf_o <- e$from_pop*distance_weight_e
mf_i <- e$to_pop*distance_weight_e
mf_u <- e$from_pop*distance_weight_e_ud+e$from_pop*distance_weight_e_ud

mf_o_inv <- mf_o^-1
mf_i_inv <- mf_i^-1
mf_inv_u <- ((mf_u*-1)-min(mf_u*-1))*(ifelse(max(mf_u)>10000000000000000,10000000000000000,max(mf_u))-ifelse(min(mf_u)<0.000000000001,0.000000000001,min(mf_u)))/(max(mf_u*-1)-min(mf_u*-1))+ifelse(min(mf_u)<0.000000000001,0.000000000001,min(mf_u))

flow_df <- data.frame(from_p=e$from_p, mf_i=mf_i)
sum_mf_i_groups <- groupedData(mf_i ~ from_p | from_p, data=as.data.frame(flow_df), FUN=sum)
sum_mf_i_pre <- gsummary(sum_mf_i_groups, sum)
sum_mf_i <- data.frame(from_p=as.integer(as.character(sum_mf_i_pre[,1])), sum_mf_i=as.double(sum_mf_i_pre[,2]))

tmp <- merge(merge(e, data.frame(con_id=e$con_id, distance_weight_e_ud=distance_weight_e_ud, distance_weight_e=distance_weight_e, mf_o=mf_o, mf_o_inv=mf_o_inv, mf_i=mf_i, mf_i_inv=mf_i_inv, mf_u=mf_u, mf_inv_u=mf_inv_u)), sum_mf_i)
cf <- tmp$mf_o*(tmp$mf_i/tmp$sum_mf_i)
#cf <- (cf-rep(min(cf),length(cf)))*(1/(rep(max(cf),length(cf))-rep(min(cf),length(cf))))
#cf_inv <- cf^-1
#igraphs limits for weights in edge.betweenness function are aproximately max 12600000000000000 and min 0.000000000001
cf_inv <- ((cf*-1)-min(cf*-1))*(ifelse(max(cf)>10000000000000000,10000000000000000,max(cf))-ifelse(min(cf)<0.000000000001,0.000000000001,min(cf)))/(max(cf*-1)-min(cf*-1))+ifelse(min(cf)<0.000000000001,0.000000000001,min(cf))

e <- merge(tmp, data.frame(con_id=e$con_id, cf=cf, cf_inv=cf_inv), by="con_id", sort=TRUE)

cf_u_df <- data.frame(con_id_u=e$con_id_u, cf=e$cf, cf_inv=e$cf_inv)
cf_u_groups <- groupedData(cf ~ 1 | con_id_u, data=cf_u_df, FUN=sum)
cf_u_grouped <- gsummary(cf_u_groups, sum)

e <- merge(e, data.frame(con_id_u=as.vector(cf_u_grouped$con_id_u), cf_u=as.vector(cf_u_grouped$cf), cf_inv_u=((as.vector(cf_u_grouped$cf)*-1)-min(as.vector(cf_u_grouped$cf)*-1))*(ifelse(max(as.vector(cf_u_grouped$cf))>10000000000000000,10000000000000000,max(as.vector(cf_u_grouped$cf)))-ifelse(min(as.vector(cf_u_grouped$cf))<0.000000000001,0.000000000001,min(as.vector(cf_u_grouped$cf))))/(max(as.vector(cf_u_grouped$cf)*-1)-min(as.vector(cf_u_grouped$cf)*-1))+ifelse(min(as.vector(cf_u_grouped$cf))<0.000000000001,0.000000000001,min(as.vector(cf_u_grouped$cf)))), all.x=TRUE)

#Collapse edge data for undirected graph
con_id_u_unique <- unique(e$con_id_u)
ud_groups <- groupedData(con_id ~ 1 | con_id_u, data=data.frame(con_id_u=e$con_id_u, con_id=e$con_id), FUN=mean)
ud_grouped <- gsummary(ud_groups)
ud_grouped_df <- data.frame(con_id_u=as.vector(ud_grouped$con_id_u), con_id_avg=as.vector(ud_grouped$con_id))
e_ud_pre <- merge(e, ud_grouped_df, all.x=TRUE)
first_con_id <- data.frame(con_id=e_ud_pre$con_id[e_ud_pre$con_id_avg>e_ud_pre$con_id])
e_ud <- merge(first_con_id, e)

#Merge vertices and edges to graph-object
#Build directed graph
if (verbose) {{
cat("Building the graph...\n")
}}

g <- graph.empty()
g <- add.vertices(g, nrow(v), patch_id=as.character(v$patch_id), pop_proxy=as.numeric(v$pop_proxy))
names <- V(g)$patch_id
ids <- 1:length(names)
names(ids) <- names
from <- as.character(e$from_p)
to <- as.character(e$to_p)
edges <- matrix(c(ids[from], ids[to]), nc=2)
g <- add.edges(g, t(edges), con_id=e$con_id, con_id_u=e$con_id_u, from_p=e$from_p, from_pop=e$from_pop, to_p=e$to_p, to_pop=e$to_pop, cost_distance=e$cost_distance, cd_u=e$cd_u, distance_weight_e=e$distance_weight_e, distance_weight_e_ud=e$distance_weight_e_ud, mf_o=e$mf_o, mf_o_inv=e$mf_o_inv, mf_i=e$mf_i, mf_i_inv=e$mf_i_inv, mf_u=e$mf_u, mf_inv_u=e$mf_inv_u, cf=e$cf, cf_inv=e$cf_inv, cf_u=e$cf_u, cf_inv_u=e$cf_inv_u)

#Build undirected graph
g_ud <- as.undirected(graph.empty())
g_ud <- add.vertices(g_ud, nrow(v), patch_id=as.character(v$patch_id), pop_proxy=as.numeric(v$pop_proxy))
names <- V(g_ud)$patch_id
ids <- 1:length(names)
names(ids) <- names
from <- as.character(e_ud$from_p)
to <- as.character(e_ud$to_p)
edges <- matrix(c(ids[from], ids[to]), nc=2)
g_ud <- add.edges(g_ud, t(edges), con_id=e_ud$con_id, con_id_u=e_ud$con_id_u, from_p=e_ud$from_p, from_pop=e_ud$from_pop, to_p=e_ud$to_p, to_pop=e_ud$to_pop, cost_distance=e_ud$cost_distance, cd_u=e_ud$cd_u, distance_weight_e=e_ud$distance_weight_e, mf_o=e_ud$mf_o, mf_o_inv=e_ud$mf_o_inv, mf_i=e_ud$mf_i, mf_i_inv=e_ud$mf_i_inv, mf_u=e_ud$mf_u, mf_inv_u=e_ud$mf_inv_u, cf=e_ud$cf, cf_inv=e_ud$cf_inv, cf_u=e_ud$cf_u, cf_inv_u=e_ud$cf_inv_u)

#Classify connection with regards to shortest paths
#con_id_u <- unlist(lapply(0:(length(E(g))-1), function(x) E(g, path=c(sort(array(c(ends(g, x)[1], ends(g, x)[2])))[1], sort(array(c(ends(g, x)[1], ends(g, x)[2])))[2]))))
#l1 <- unlist(lapply(1:length(V(g_ud)), function(x) rep(x, length(V(g_ud)))))
#l2 <- rep(1:length(V(g_ud)), length(V(g_ud)))
#fa <- function(a) get.shortest.paths(g_ud, l1[a], l2[a], weights=E(g_ud)$cd_u)
#sp <- fa(1:length(l1))
#Set edge attributes
#E(g)$con_id_u <- con_id_u

#E(g)$cd_u <- unlist(mclapply(mc.cores={0}, 0:(length(E(g))-1), function(x) (E(g)[x]$cost_distance+E(g, path=c(ends(g, x)[2], ends(g, x)[1]))$cost_distance)/2))

####################################
###Can the following be vectorised????

E(g_ud)$isshort_cd <- as.integer(unlist(mclapply(mc.cores={0}, 1:(length(E(g_ud))), function(x) length(get.shortest.paths(g_ud, from=ends(g_ud, x)[1], to=ends(g_ud, x)[2], weights=E(g_ud)$cd_u)$vpath[[1]])))==2)
E(g_ud)$isshort_mf <- as.integer(unlist(mclapply(mc.cores={0}, 1:(length(E(g_ud))), function(x) length(get.shortest.paths(g_ud, from=ends(g_ud, x)[1], to=ends(g_ud, x)[2], weights=E(g_ud)$mf_inv_u)$vpath[[1]])))==2)
E(g_ud)$isshort_cf <- as.integer(unlist(mclapply(mc.cores={0}, 1:(length(E(g_ud))), function(x) length(get.shortest.paths(g_ud, from=ends(g_ud, x)[1], to=ends(g_ud, x)[2], weights=E(g_ud)$cf_inv_u)$vpath[[1]])))==2)
E(g_ud)$isshort <- ifelse((E(g_ud)$isshort_cd==0 & E(g_ud)$isshort_mf==0 & E(g_ud)$isshort_cf==0), 0, 1)
####################################

#Add edge attributes to directed graph (for export)
#E(g)$isshort[grep(TRUE, E(g)$con_id_u %in% E(g_ud)$con_id_u[grep(TRUE, E(g_ud)$isshort)])] <- TRUE
#E(g)$isshort[grep(TRUE, E(g)$con_id_u %in% E(g_ud)$con_id_u[grep(FALSE, E(g_ud)$isshort)])] <- FALSE

#Remove indirect connections if requested
#if(remove_indirect == 1) {{
g_ud_d <- delete.edges(g_ud, E(g_ud)[E(g_ud)$isshort==FALSE])
#g_ud <- delete.edges(g_ud, E(g_ud)[E(g_ud)$isshort==FALSE])
#}}

#Remove connections above connectivity threshold if requested
if(connectivity_cutoff >= 0.0) {{
g_ud_cd <- delete.edges(g_ud, E(g_ud)[grep(TRUE, E(g_ud)$cd_u>=connectivity_cutoff)])
g_ud_d_cd <- delete.edges(g_ud_d, E(g_ud_d)[grep(TRUE, E(g_ud_d)$cd_u>=connectivity_cutoff)])
}}

########################################################################
###Analysis on graph level
########################################################################

if (verbose) {{
cat("Starting analysis on graph level...\n")
}}

###graph measures
vertices_n <- length(V(g_ud_d))
edges_n <- length(E(g_ud))
edges_n_d <- length(E(g_ud_d))
edges_n_cd <- length(E(g_ud_cd))
edges_n_d_cd <- length(E(g_ud_d_cd))


########################################################################
######Calculate number of clusters
#On the undirected graph with only direct edges and on the undirected graph with only direct edges shorter cost distance threshold
cl_no_d <- clusters(g_ud_d)$no
cl_no_d_cd <- clusters(g_ud_d_cd)$no

cls_size_d <- as.vector(gsummary(groupedData(pop_size ~ 1 | cl, data.frame(cl=clusters(g_ud_d)$membership, pop_size=V(g_ud_d)$pop_proxy), order.groups=TRUE, FUN=sum), sum)$pop_size)
cls_size_d_cd <- as.vector(gsummary(groupedData(pop_size ~ 1 | cl, data.frame(cl=clusters(g_ud_d_cd)$membership, pop_size=V(g_ud_d_cd)$pop_proxy), order.groups=TRUE, FUN=sum), sum)$pop_size)

cl_max_size_d <- max(cls_size_d)
cl_max_size_d_cd <- max(cls_size_d_cd)

cl_mean_size_d <- mean(cls_size_d)
cl_mean_size_d_cd <- mean(cls_size_d_cd)

diam <- diameter(g_ud, directed=FALSE, unconnected=TRUE, weights=E(g_ud)$cd_u)
diam_d <- diameter(g_ud_d, directed=FALSE, unconnected=TRUE, weights=E(g_ud_d)$cd_u)
diam_d_cd <- diameter(g_ud_d_cd, directed=FALSE, unconnected=TRUE, weights=E(g_ud_d_cd)$cd_u)

density <- graph.density(g, loops=FALSE)
density_u <- graph.density(g_ud, loops=FALSE)
density_ud <- graph.density(g_ud_d, loops=FALSE)
density_udc <- graph.density(g_ud_d_cd, loops=FALSE)

if (network_overview_ps != "") {{
######Edge removal operations
idx <- sort(E(g_ud)$cd_u, decreasing=TRUE, na.last=NA, index.return=TRUE)$ix
cl_del_count <- unlist(mclapply(mc.cores={0}, 1:length(idx), function(x) ifelse((clusters(delete.edges(g_ud, E(g_ud)[idx[1:x]]))$no/vertices_n)>=convergence_threshold||E(g_ud)$cd_u[idx[x]]<=(connectivity_cutoff+(connectivity_cutoff*0.25)),clusters(delete.edges(g_ud, E(g_ud)[idx[1:x]]))$no,NA)))
cl_del_max_size <- unlist(mclapply(mc.cores={0}, 1:length(idx), function(x) ifelse((clusters(delete.edges(g_ud, E(g_ud)[idx[1:x]]))$no/vertices_n)>=convergence_threshold||E(g_ud)$cd_u[idx[x]]<=(connectivity_cutoff+(connectivity_cutoff*0.25)),max(as.vector(gsummary(groupedData(pop_size ~ 1 | cl, data.frame(cl=clusters(delete.edges(g_ud, E(g_ud)[idx[1:x]]))$membership, pop_size=V(g_ud)$pop_proxy), order.groups=TRUE, FUN=sum), sum)$pop_size)),NA)))
cl_del_diam <- unlist(mclapply(mc.cores={0}, 1:length(idx), function(x) ifelse((clusters(delete.edges(g_ud, E(g_ud)[idx[1:x]]))$no/vertices_n)>=convergence_threshold||E(g_ud)$cd_u[idx[x]]<=(connectivity_cutoff+(connectivity_cutoff*0.25)),diameter(delete.edges(g_ud, E(g_ud)[idx[1:x]]), directed=FALSE, unconnected=TRUE, weights=E(delete.edges(g_ud, E(g_ud)[idx[1:x]]))$cd_u),NA)))
extract <- sort(grep(FALSE, is.na(cl_del_count)), decreasing=TRUE)
df_edgeremoval <- data.frame(distance=E(g_ud)$cd_u[((idx[extract]))], cl_del_count=cl_del_count[extract], cl_del_max_size=cl_del_max_size[extract], cl_del_diam=cl_del_diam[extract])
dist_inv_ix <- sort(df_edgeremoval$distance, decreasing=FALSE, na.last=NA, index.return=TRUE)$ix

ps.options(encoding="CP1257.enc", family="Helvetica", horizontal=FALSE, fonts="Helvetica", paper="a4", pointsize=1/96, height=3.5, width=3.5)
postscript(network_overview_ps)

###Check axis labels!!!
matplot(df_edgeremoval$distance/(10^(nchar(as.integer(max(df_edgeremoval$distance)))-2)), df_edgeremoval$cl_del_count*100/vertices_n, type="l", ylab="", xlab=c("Connectivity threshold", paste("(Cost distance between patches in ", as.character(10^(nchar(as.integer(max(df_edgeremoval$distance)))-2)), ")", sep="")), lty=1, yaxt="n", yaxs="r", ylim=c(0, 100), yaxs="i", xaxs="i")
if (connectivity_cutoff>0) abline(v=connectivity_cutoff/10^(nchar(as.integer(max(df_edgeremoval$distance)))-2), col="red", lty=3)
ifelse(connectivity_cutoff>0, legend("topleft",
                                     #inset=c(0,-0.15), bty = "n",
                                     xpd=TRUE,
                                     c("Clusters (in % of maximum possible clusters)", "Size of the largest cluster (in % of total population size)", "Number of edges (in % of maximum possible number of edges)", "Diameter (in % of diameter of the entire graph)", "Connectivity threshold used in analysis"), lty=c(1, 2, 3, 4, 3), col=c("black", "black", "black", "black", "red"), inset=0.005, bty="o", box.lty=0, bg="White"), legend("topleft", c("Clusters (in % of maximum possible clusters)", "Size of the largest cluster (in % of total population size)", "Number of edges (in % of maximum possible number of edges)", "Diameter (in % of diameter of the entire graph)"), lty=c(1, 2, 3, 4), col=c("black", "black", "black", "black"), inset=0.005, bty="o", box.lty=0, bg="White"))
axis(2, seq.int(0, 100, 25), labels=c("0 %", "25 %", "50 %", "75 %", "100 %"), yaxs="r")
matplot(df_edgeremoval$distance/(10^(nchar(as.integer(max(df_edgeremoval$distance)))-2)), df_edgeremoval$cl_del_max_size*100/sum(V(g)$pop_proxy), type="l", lty=2, yaxt="n", yaxs="i", add=TRUE)
lines(df_edgeremoval$distance/(10^(nchar(as.integer(max(df_edgeremoval$distance)))-2)), dist_inv_ix*100/edges_n, type="l", lty=3)
lines(df_edgeremoval$distance/(10^(nchar(as.integer(max(df_edgeremoval$distance)))-2)), df_edgeremoval$cl_del_diam*100/diam_d, type="l", lty=4)
#Label axis 4!!!
#axis(4, seq.int(0, 100, 25), yaxs="i", labels=seq.int(0, ceiling((as.integer(edges_n)/(10^(nchar(as.integer(edges_n))-2))))*(10^(nchar(as.integer(edges_n))-2)), ceiling((as.integer(edges_n)/(10^(nchar(as.integer(edges_n))-2))))*(10^(nchar(as.integer(edges_n))-2))/4))
off <- dev.off(dev.cur())

#idx <- sort(E(g_ud)$cd_u, decreasing=TRUE, na.last=NA, index.return=TRUE)$ix
#cl_del_count <- unlist(mclapply(mc.cores={0}, 1:length(idx), function(x) ifelse((clusters(delete.edges(g_ud, E(g_ud)[idx[1:x]]))$no/vertices_n)>=convergence_threshold,clusters(delete.edges(g_ud, E(g_ud)[idx[1:x]]))$no,NA)))
#cl_del_max_size <- unlist(mclapply(mc.cores={0}, 1:length(idx), function(x) ifelse((clusters(delete.edges(g_ud, E(g_ud)[idx[1:x]]))$no/vertices_n)>=convergence_threshold,max(as.vector(gsummary(groupedData(pop_size ~ 1 | cl, data.frame(cl=clusters(delete.edges(g_ud, E(g_ud)[idx[1:x]]))$membership, pop_size=V(g_ud)$pop_proxy), order.groups=TRUE, FUN=sum), sum)$pop_size)),NA)))
#cl_del_diam <- unlist(mclapply(mc.cores={0}, 1:length(idx), function(x) ifelse((clusters(delete.edges(g_ud, E(g_ud)[idx[1:x]]))$no/vertices_n)>=convergence_threshold,diameter(delete.edges(g_ud, E(g_ud)[idx[1:x]]), directed=FALSE, unconnected=TRUE, weights=E(delete.edges(g_ud, E(g_ud)[idx[1:x]]))$cd_u),NA)))
#extract <- sort(grep(FALSE, is.na(cl_del_count)), decreasing=TRUE)
#df_edgeremoval <- data.frame(distance=E(g_ud)$cd_u[((idx[extract]))], cl_del_count=cl_del_count[extract], cl_del_max_size=cl_del_max_size[extract], cl_del_diam=cl_del_diam[extract])
#dist_inv_ix <- sort(df_edgeremoval$distance, decreasing=FALSE, na.last=NA, index.return=TRUE)$ix

#ps.options(encoding="CP1257.enc", family="Helvetica", horizontal=FALSE, fonts="Helvetica", paper="a4", pointsize=1/96, height=3.5, width=3.5)
#postscript(network_overview_ps)

####Check axis labels!!!
#matplot(df_edgeremoval$distance/(10^(nchar(as.integer(max(df_edgeremoval$distance)))-2)), df_edgeremoval$cl_del_count*100/vertices_n, type="l", xlab=c("Grenseverdi for antatt konnektivitet mellom vernområdene", paste("basert på den funksjonale avstanden mellom dem i ", as.character(10^(nchar(as.integer(max(df_edgeremoval$distance)))-2)), sep="")), ylab="Antall vernområder / nettverkskomponenter", lty=1, yaxt="n", yaxs="r", ylim=c(0, 100), yaxs="i", xaxs="i")
#if (connectivity_cutoff>0) abline(v=connectivity_cutoff, col="red", lty=3)
#ifelse(connectivity_cutoff>0, legend("topleft", c("Andel nettverkskomponenter", "Størrelsen av den største nettverkskomponenten", "(i andel populasjons størrelse)", "Antall forbindelser i nettverket", "Andel av diameter av nettverket", "Antatt grenseverdi for konnektivitet"), lty=c(1, 2, 0, 3, 4, 3), col=c("black", "black", "black", "black", "black", "red"), inset=0.005, bty="o", box.lty=0, bg="White"), legend("topleft", c("Andel nettverkskomponenter", "Størrelsen av den største nettverkskomponenten", "(i andel populasjons størrelse)", "Antall forbindelser i nettverket", "Andel av diameter av nettverket"), lty=c(1, 2, 0, 3, 4), col=c("black", "black", "black", "black", "black"), inset=0.005, bty="o", box.lty=0, bg="White"))
#axis(2, seq.int(0, 100, 25), yaxs="r")
#matplot(df_edgeremoval$distance, df_edgeremoval$cl_del_max_size*100/sum(V(g)$pop_proxy), type="l", lty=2, yaxt="n", yaxs="i", add=TRUE)
#lines(df_edgeremoval$distance, dist_inv_ix*100/edges_n, type="l", lty=3)
#lines(df_edgeremoval$distance, df_edgeremoval$cl_del_diam*100/diam_d, type="l", lty=4)
##Label axis 4!!!
##axis(4, seq.int(0, maks_forbindelser_ud*maks_nodes/maks_forbindelser_ud, 100*maks_nodes/maks_forbindelser_ud), yaxs="i", labels=seq.int(0, maks_forbindelser_ud, 100), ylab="Antall forbindelser")
#off <- dev.off(dev.cur())
}}

########################################################################
###Analysis on edge level
########################################################################

if (verbose) {{
cat("Starting analysis on edge level...\n")
}}

########################################################################
######Calculate minimum spanning trees (MST) on the undirected graph with only direct edges
###Minimum spanning tree weighted by maximum potential flow

E(g_ud_d)$mf_mst_ud <- as.integer(0)
E(g_ud_d)[grep(TRUE, E(g_ud_d)$con_id %in% E(minimum.spanning.tree(g_ud_d, weights=E(g_ud_d)$mf_inv_u))$con_id)]$mf_mst_ud <- 1

###Minimum spanning tree weighted by cost distance
E(g_ud_d)$cd_mst_ud <- as.integer(0)
E(g_ud_d)[grep(TRUE, E(g_ud_d)$con_id %in% E(minimum.spanning.tree(g_ud_d, weights=E(g_ud_d)$cd_u))$con_id)]$cd_mst_ud <- 1

E(g_ud_d)$cf_mst_ud <- as.integer(0)
E(g_ud_d)[grep(TRUE, E(g_ud_d)$con_id %in% E(minimum.spanning.tree(g_ud_d, weights=E(g_ud_d)$cf_inv_u))$con_id)]$cf_mst_ud <- 1

######Calculate minimum spanning trees (MST) on the undirected graph with only direct edges shorter cost distance threshold
###Minimum spanning tree weighted by maximum potential flow
E(g_ud_d_cd)$mf_mst_udc <- as.integer(0)
E(g_ud_d_cd)[grep(TRUE, E(g_ud_d_cd)$con_id %in% E(minimum.spanning.tree(g_ud_d_cd, weights=E(g_ud_d_cd)$mf_inv_u))$con_id)]$mf_mst_udc <- 1


###Minimum spanning tree weighted by cost distance
E(g_ud_d_cd)$cd_mst_udc <- as.integer(0)
E(g_ud_d_cd)[grep(TRUE, E(g_ud_d_cd)$con_id %in% E(minimum.spanning.tree(g_ud_d_cd, weights=E(g_ud_d_cd)$cd_u))$con_id)]$cd_mst_udc <- 1

###Minimum spanning tree weighted by competing potential flow
E(g_ud_d_cd)$cf_mst_udc <- as.integer(0)
E(g_ud_d_cd)[grep(TRUE, E(g_ud_d_cd)$con_id %in% E(minimum.spanning.tree(g_ud_d_cd, weights=E(g_ud_d_cd)$cf_inv_u))$con_id)]$cf_mst_udc <- 1

########################################################################
###Identify bridges for the undirected graph
E(g_ud)$is_br_u <- as.integer(unlist(mclapply(mc.cores={0}, 1:(length(E(g_ud))), function(x) clusters(delete.edges(g_ud, E(g_ud)[as.integer(x)]))$no-cl_no_d)))

#Identify bridges for the undirected graph with only direct edges
E(g_ud_d)$is_br_ud <- as.integer(unlist(mclapply(mc.cores={0}, 1:(length(E(g_ud_d))), function(x) clusters(delete.edges(g_ud_d, E(g_ud_d)[as.integer(x)]))$no-cl_no_d)))

###Identify bridges for the undirected graph with only direct edges shorter cost distance threshold
E(g_ud_d_cd)$is_br_udc <- as.integer(unlist(mclapply(mc.cores={0}, 1:(length(E(g_ud_d_cd))), function(x) clusters(delete.edges(g_ud_d_cd, E(g_ud_d_cd)[as.integer(x)]))$no-cl_no_d_cd)))

########################################################################

biconnected_components_d <- biconnected.components(g_ud)

#Identify component edges (biconnected components) for the undirected graph with only direct edges
E(g_ud)$bc_e_u <- as.integer(0)
for (c in 1:biconnected_components_d$no) {{
E(g_ud)$bc_e_u[unlist(biconnected_components_d$component_edges[c])] <- c
}}
#Identify tree edges (biconnected components) for the undirected graph with only direct edges
E(g_ud)$bc_te_u <- as.integer(0)
for (c in 1:biconnected_components_d$no) {{
E(g_ud)$bc_te_u[unlist(biconnected_components_d$tree_edges[c])] <- c
}}

biconnected_components_d <- biconnected.components(g_ud_d)
#Identify component edges (biconnected components) for the undirected graph with only direct edges
E(g_ud_d)$bc_e_ud <- as.integer(0)
for (c in 1:biconnected_components_d$no) {{
E(g_ud_d)$bc_e_ud[unlist(biconnected_components_d$component_edges[c])] <- c
}}
#Identify tree edges (biconnected components) for the undirected graph with only direct edges
E(g_ud_d)$bc_te_ud <- as.integer(0)
for (c in 1:biconnected_components_d$no) {{
E(g_ud_d)$bc_te_ud[unlist(biconnected_components_d$tree_edges[c])] <- c
}}

biconnected_components_d_cd <- biconnected.components(g_ud_d_cd)
#Identify component edges (biconnected components) for the undirected graph with only direct edges shorter cost distance threshold
E(g_ud_d_cd)$bc_e_udc <- as.integer(0)
for (c in 1:biconnected_components_d_cd$no) {{
E(g_ud_d_cd)$bc_e_udc[unlist(biconnected_components_d_cd$component_edges[c])] <- c
}}
#Identify tree edges (biconnected components) for the undirected graph with only direct edges shorter cost distance threshold
E(g_ud_d_cd)$bc_te_udc <- as.integer(0)
for (c in 1:biconnected_components_d_cd$no) {{
E(g_ud_d_cd)$bc_te_udc[unlist(biconnected_components_d_cd$tree_edges[c])] <- c
}}

########################################################################
###Calculate edge betweenness
##Results of the internal edge.betweenness.estimate function are slightly different from the one used here (always larger values):
##see: E(g_ud_d)$cd_leb_ud <- edge.betweenness.estimate(g_ud_d, e=E(g_ud_d), directed=FALSE, lnbh_cutoff*connectivity_cutoff, weights=E(g_ud_d)$cd_u)
##But since the internal edge.betweenness.estimate function is not reasonable to use with other weights than cost distance, the workarounds are used nevertheless
##Further investigation necessary!!!

###Calculate edge betweenness on the entire undirected graph with only direct edges

path_lengths <- shortest.paths(g_ud_d, v=V(g_ud_d), to=V(g_ud_d), weights=E(g_ud_d)$cd_u)

#weighted by cost distance
E(g_ud_d)$cd_eb_ud <- edge.betweenness(g_ud_d, e=E(g_ud_d), directed=FALSE, weights=E(g_ud_d)$cd_u)
E(g_ud_d)$cd_leb_ud <- hist(unlist(mclapply(mc.cores={0}, 1:length(V(g_ud_d)), function(x) get.shortest.paths(g_ud_d, x,  V(g_ud_d)[grep(TRUE, path_lengths[x,]<(lnbh_cutoff*connectivity_cutoff))], weights=E(g_ud_d)$cd_u, output=c("epath"))$epath)), breaks=0:(length(E(g_ud_d))), plot=FALSE)$counts/2
#E(g_ud_d)$cd_leb_ud <- edge.betweenness.estimate(g_ud_d, e=E(g_ud_d), directed=FALSE, lnbh_cutoff*connectivity_cutoff, weights=E(g_ud_d)$cd_u)

#weighted by maximum potential flow
E(g_ud_d)$mf_eb_ud <- edge.betweenness(g_ud_d, e=E(g_ud_d), directed=FALSE, weights=E(g_ud_d)$mf_inv_u)
E(g_ud_d)$mf_leb_ud <- hist(unlist(mclapply(mc.cores={0}, 1:length(V(g_ud_d)), function(x) get.shortest.paths(g_ud_d, x,  V(g_ud_d)[grep(TRUE, path_lengths[x,]<(lnbh_cutoff*connectivity_cutoff))], weights=E(g_ud_d)$mf_inv_u, output=c("epath"))$epath)), breaks=0:(length(E(g_ud_d))), plot=FALSE)$counts/2

##weighted by competing potential flow
E(g_ud_d)$cf_eb_ud <- edge.betweenness(g_ud_d, e=E(g_ud_d), directed=FALSE, weights=E(g_ud_d)$cf_inv_u)
E(g_ud_d)$cf_leb_ud <- hist(unlist(mclapply(mc.cores={0}, 1:length(V(g_ud_d)), function(x) get.shortest.paths(g_ud_d, x,  V(g_ud_d)[grep(TRUE, path_lengths[x,]<(lnbh_cutoff*connectivity_cutoff))], weights=E(g_ud_d)$cf_inv_u, output=c("epath"))$epath)), breaks=0:(length(E(g_ud_d))), plot=FALSE)$counts/2

########################################################################
###Calculate edge betweenness on the entire undirected graph with only direct edges shorter cost distance threshold

path_lengths_cd <- shortest.paths(g_ud_d_cd, v=V(g_ud_d_cd), to=V(g_ud_d_cd), weights=E(g_ud_d_cd)$cd_u)

#weighted by cost distance
E(g_ud_d_cd)$cd_eb_udc <- edge.betweenness(g_ud_d_cd, e=E(g_ud_d_cd), directed=FALSE, weights=E(g_ud_d_cd)$cd_u)
E(g_ud_d_cd)$cd_leb_udc <- hist(unlist(mclapply(mc.cores={0}, 1:length(V(g_ud_d_cd)), function(x) get.shortest.paths(g_ud_d_cd, x,  V(g_ud_d_cd)[grep(TRUE, path_lengths_cd[x,]<(lnbh_cutoff*connectivity_cutoff))], weights=E(g_ud_d_cd)$cd_u, output=c("epath"))$epath)), breaks=0:(length(E(g_ud_d_cd))), plot=FALSE)$counts/2


#weighted by maximum potential flow
E(g_ud_d_cd)$mf_eb_udc <- edge.betweenness(g_ud_d_cd, e=E(g_ud_d_cd), directed=FALSE, weights=E(g_ud_d_cd)$mf_inv_u)
E(g_ud_d_cd)$mf_leb_udc <- hist(unlist(mclapply(mc.cores={0}, 1:length(V(g_ud_d_cd)), function(x) get.shortest.paths(g_ud_d_cd, x,  V(g_ud_d_cd)[grep(TRUE, path_lengths_cd[x,]<(lnbh_cutoff*connectivity_cutoff))], weights=E(g_ud_d_cd)$mf_inv_u, output=c("epath"))$epath)), breaks=0:(length(E(g_ud_d_cd))), plot=FALSE)$counts/2

##weighted by competing potential flow
E(g_ud_d_cd)$cf_eb_udc <- edge.betweenness(g_ud_d_cd, e=E(g_ud_d_cd), directed=FALSE, weights=E(g_ud_d_cd)$cf_inv_u)
E(g_ud_d_cd)$cf_leb_udc <- hist(unlist(mclapply(mc.cores={0}, 1:length(V(g_ud_d_cd)), function(x) get.shortest.paths(g_ud_d_cd, x,  V(g_ud_d_cd)[grep(TRUE, path_lengths_cd[x,]<(lnbh_cutoff*connectivity_cutoff))], weights=E(g_ud_d_cd)$cf_inv_u, output=c("epath"))$epath)), breaks=0:(length(E(g_ud_d_cd))), plot=FALSE)$counts/2

if (cl_thresh > 0) {{
#########################################################################
#######Calculate edge betweenness community on the undirected graph
##weighted by competing potential flow
ebc <- edge.betweenness.community(g_ud, weights=E(g_ud)$cf_inv_u, directed=FALSE, edge.betweenness=TRUE, merges=TRUE, bridges=TRUE, modularity=TRUE, membership=TRUE)

E(g_ud)$cf_iebc_v <- ebc$edge.betweenness
#cf_iebc_m <- ebc$merges
E(g_ud)$cf_iebc_r <- ebc$removed.edges
E(g_ud)$cf_iebc_b <- unlist(mclapply(mc.cores={0}, 1:length(E(g_ud)), function(x) ifelse(x %in% ebc$bridges, 1, 0)))
E(g_ud)$cf_iebc_c <- crossing(ebc, g_ud)

#V(g)$cf_iebc_mo <- ebc$modularity
V(g)$cf_iebc_me <- ebc$membership

com_struct <- as.character(cutat(ebc, cl_no_d))
for (i in (cl_no_d+1):(cl_no_d+cl_thresh)) {{
com_struct <- paste(com_struct, cutat(ebc, i), sep=';')
}}
V(g)$cf_iebc_cs <- as.character(com_struct)
V(g)$cf_iebc_cl <- cutat(ebc, (cl_no_d+cl_thresh))

cf_iebc_u_mod <- modularity(ebc)
com_no_u <- length(ebc)
com_sizes_u <- sizes(ebc)
com_sizes_u_names <- paste("Size of comumity ", names(sizes(ebc)), " (at maximum modularity score (from iebc))", sep="")

#The following workaround was written when igraph did not support weights when calculating edge.betweenness.community
#The results of this procedure differ significantly from the (new) edge.betweenness.community in igraph 0.6-2 with weights (above)
#In a first visual the results of the following procedure look more reasonable, but further investigation is necessary!!!

n <- as.integer(1)
ebc_con_id_u <- as.integer(0)
ebc_rank <- as.integer(0)
ebc_value <- as.integer(0)
ebc_clust <- as.integer(0)
V(g_ud)$cf_ebc_cs <- as.character(clusters(g_ud)$membership)
del_eb_g <- g_ud

for (edge in 1:length(E(del_eb_g))) {{
##Recalculate edge betweenness for the remaining edges
E(del_eb_g)$cf_eb_ud <- edge.betweenness(del_eb_g, e=E(del_eb_g), directed=FALSE, weights=E(del_eb_g)$cf_inv_u)
##Identify edge with highest edge betweenness value
idx <- sort.int(E(del_eb_g)$cf_eb_ud, decreasing=TRUE, na.last=NA, index.return=TRUE)$ix[1]
##Save edge betweenness value for this edge
ebc_con_id_u[n] <- E(del_eb_g)$con_id_u[idx]
ebc_rank[n] <- n
ebc_clust[n] <- clusters(del_eb_g)$no
if((ebc_clust[n]-cl_no_d)<(cl_no_d+cl_thresh)) {{if(n>1) {{if(ebc_clust[n]>ebc_clust[n-1]) V(g_ud)$cf_ebc_cs <- paste(V(g_ud)$cf_ebc_cs, clusters(del_eb_g)$membership, sep=";")}}}}
ebc_value[n] <- E(del_eb_g)$cf_eb_ud[idx]
##Delete edge with highest edge betweenness value
del_eb_g <- delete.edges(del_eb_g, E(del_eb_g)[idx])
n <- n+1
}}

V(g_ud)$cf_ebc_cl <- unlist(mclapply(mc.cores={0}, 1:length(V(g_ud)), function(x) strsplit(V(g_ud)$cf_ebc_cs, ";")[[x]][(cl_no_d+cl_thresh)]))

#ebc_df <- merge(data.frame(con_id=E(g)$con_id, con_id_u=E(g)$con_id_u), data.frame(con_id_u=ebc_con_id_u, ebc_rank=ebc_rank, ebc_clust=ebc_clust, ebc_value=ebc_value), all.x=TRUE)
idx <- sort.int(ebc_con_id_u, index.return=TRUE)$ix
E(g_ud)$cf_ebc_v <- ebc_value[idx]
E(g_ud)$cf_ebc_r <- ebc_rank[idx]
E(g_ud)$cf_ebc_c <- ebc_clust[idx]

E(g_ud)$cf_ebc_vi <- strftime(Sys.time()+E(g_ud)$cf_ebc_r)

#########################################################################
###Calculate community connectors (based on community structure from ebc)
com_membership <- data.frame(patch_id=V(g_ud_d_cd)$patch_id, com=V(g_ud)$cf_ebc_cl)
com_pc_pre <- merge(merge(data.frame(id=1:length(E(g)), from_p=E(g)$from_p, to_p=E(g)$to_p), com_membership, by.x="from_p", by.y="patch_id"),  com_membership, by.x="to_p", by.y="patch_id")[order(merge(merge(data.frame(id=1:length(E(g)), from_p=E(g)$from_p, to_p=E(g)$to_p), com_membership, by.x="from_p", by.y="patch_id"),  com_membership, by.x="to_p", by.y="patch_id")$id) ,]
E(g)$cf_ebc_cc <- ifelse(com_pc_pre$com.x==com_pc_pre$com.y,0,1)


}} else {{
if (verbose) {{
cat("Skipping community algorithms...\n")
}}
}}
########################################################################
######Calculate cluster membership
V(g_ud_d)$cl_ud <- clusters(g_ud_d)$membership
V(g_ud_d_cd)$cl_udc <- clusters(g_ud_d_cd)$membership

#########################################################################
###Calculate potential cluster connectors (based on cost distance threshold)
cl_membership <- data.frame(patch_id=V(g_ud_d_cd)$patch_id, cl=V(g_ud_d_cd)$cl_udc)
cl_pc_pre <- merge(merge(data.frame(id=1:length(E(g)), from_p=E(g)$from_p, to_p=E(g)$to_p), cl_membership, by.x="from_p", by.y="patch_id"),  cl_membership, by.x="to_p", by.y="patch_id")[order(merge(merge(data.frame(id=1:length(E(g)), from_p=E(g)$from_p, to_p=E(g)$to_p), cl_membership, by.x="from_p", by.y="patch_id"),  cl_membership, by.x="to_p", by.y="patch_id")$id) ,]
E(g)$cl_pc <- ifelse(cl_pc_pre$cl.x==cl_pc_pre$cl.y,0,1)

if (verbose) {{
cat("Starting analysis on vertex level...\n")
}}

########################################################################
###Analysis on vertex level
########################################################################

########################################################################
######Calculate degree centrality
#On the directed graph
#V(g)$deg_dir <- as.integer(degree(g, v=V(g), mode=c("in")))

#On the entire undirected graph
V(g_ud)$deg_u <- as.integer(degree(g_ud, v=V(g_ud)))

#On the undirected graph with edges shorter cost distance threshold
V(g_ud_cd)$deg_uc <- as.integer(degree(g_ud_cd, v=V(g_ud_cd)))

#On the undirected graph with only direct edges
V(g_ud_d)$deg_ud <- as.integer(degree(g_ud_d, v=V(g_ud_d)))

#On the undirected graph with only direct edges shorter cost distance threshold
V(g_ud_d_cd)$deg_udc <- as.integer(degree(g_ud_d_cd, v=V(g_ud_d_cd)))

########################################################################
######Calculate closeness centrality
V(g_ud_d)$cd_cl_ud <- closeness(g_ud_d, vids=V(g_ud_d), weights = E(g_ud_d)$cd_u, normalized = FALSE)
V(g_ud_d)$mf_cl_ud <- closeness(g_ud_d, vids=V(g_ud_d), weights = E(g_ud_d)$mf_inv_u, normalized = FALSE)
V(g_ud_d)$cf_cl_ud <- closeness(g_ud_d, vids=V(g_ud_d), weights = E(g_ud_d)$cf_inv_u, normalized = FALSE)

V(g_ud_d_cd)$cd_cl_udc <- closeness(g_ud_d_cd, vids=V(g_ud_d_cd), weights = E(g_ud_d_cd)$cd_u, normalized = FALSE)
V(g_ud_d_cd)$mf_cl_udc <- closeness(g_ud_d_cd, vids=V(g_ud_d_cd), weights = E(g_ud_d_cd)$mf_inv_u, normalized = FALSE)
V(g_ud_d_cd)$cf_cl_udc <- closeness(g_ud_d_cd, vids=V(g_ud_d_cd), weights = E(g_ud_d_cd)$cf_inv_u, normalized = FALSE)

########################################################################
######Calculate biconnected components

##On the undirected graph with only direct edges
#Number of new clusters when a vertex is deleted
V(g_ud_d)$art_ud <- as.integer(unlist(mclapply(mc.cores={0}, 1:(length(V(g_ud_d))), function(x) ifelse((clusters(delete.vertices(g_ud_d, V(g_ud_d)[x]))$no-cl_no_d)<0,0,clusters(delete.vertices(g_ud_d, V(g_ud_d)[x]))$no-cl_no_d))))
#Vertex is articulation point
V(g_ud_d)$art_p_ud <- as.integer(0)
V(g_ud_d)$art_p_ud[biconnected_components_d$articulation_points] <- as.integer(1)

##On the undirected graph with only direct edges shorter cost distance threshold
#Number of new clusters when a vertex is deleted
V(g_ud_d_cd)$art_udc <- unlist(mclapply(mc.cores={0}, 1:(length(V(g_ud_d_cd))), function(x) ifelse((clusters(delete.vertices(g_ud_d_cd, V(g_ud_d_cd)[x]))$no-cl_no_d_cd)<0,0,clusters(delete.vertices(g_ud_d_cd, V(g_ud_d_cd)[x]))$no-cl_no_d_cd)))
#Vertex is articulation point
V(g_ud_d_cd)$art_p_udc <- as.integer(0)
V(g_ud_d_cd)$art_p_udc[biconnected_components_d_cd$articulation_points] <- as.integer(1)

########################################################################
######Calculate eigenvector centrality
#Calculate eigenvector for the entire directed graph

#Calculate eigenvector centrality weighted by competing potential flow
cf_evc_groups <- groupedData(cf ~ 1 | to_p, data=e, FUN=sum)
cf_evc <- gsummary(cf_evc_groups, sum)
df_cf_evc_d <- data.frame(patch_id=cf_evc$to_p, cf_evc_d=cf_evc$cf)

#Calculate eigenvector centrality weighted by maximum potential flow
mf_o_evc_groups <- groupedData(mf_o ~ 1 | to_p, data=e, FUN=sum)
mf_o_evc <- gsummary(mf_o_evc_groups, sum)
df_mf_i_evc_d <- data.frame(patch_id=mf_o_evc$to_p, mf_evc_d=mf_o_evc$mf_o)

df_evc_d <- merge(df_cf_evc_d, df_mf_i_evc_d)

######Calculate eigenvector centrality on the directed graph with edges shorter cost distance threshold
#Calculate eigenvector centrality weighted by competing potential flow
evc_udc_pre <- data.frame(to_p=e$to_p[grep(TRUE, e$cd_u<connectivity_cutoff)], mf_o=e$mf_o[grep(TRUE, e$cd_u<connectivity_cutoff)], cf=e$cf[grep(TRUE, e$cd_u<connectivity_cutoff)])

cf_evc_udc_groups <- groupedData(cf ~ 1 | to_p, data=evc_udc_pre, FUN=sum)
cf_evc_udc <- gsummary(cf_evc_udc_groups, sum)
df_cf_evc_udc <- data.frame(patch_id=cf_evc_udc$to_p, cf_evc=cf_evc_udc$cf)

#Calculate eigenvector centrality weighted by maximum potential flow
mf_o_evc_udc_groups <- groupedData(mf_o ~ 1 | to_p, data=evc_udc_pre, FUN=sum)
mf_o_evc_udc <- gsummary(mf_o_evc_udc_groups, sum)
df_mf_o_evc_udc <- data.frame(patch_id=mf_o_evc_udc$to_p, mf_evc=mf_o_evc_udc$mf_o)

df_evc_cd <- merge(df_cf_evc_udc, df_mf_o_evc_udc)

###Add eigenvector centrality as a vertex attribute
for (p in 1:length(V(g))) {{
    V(g)$mf_evc_d[p] <- ifelse(length(grep(TRUE, as.integer(as.character(df_evc_d$patch_id))==as.integer(V(g)$patch_id[p])))<1,0,df_evc_d$mf_evc[grep(TRUE, as.integer(as.character(df_evc_d$patch_id))==as.integer(V(g)$patch_id[p]))])
    V(g)$cf_evc_d[p] <- ifelse(length(grep(TRUE, as.integer(as.character(df_evc_d$patch_id))==as.integer(V(g)$patch_id[p])))<1,0,df_evc_d$cf_evc[grep(TRUE, as.integer(as.character(df_evc_d$patch_id))==as.integer(V(g)$patch_id[p]))])
    V(g)$mf_evc_cd[p] <- ifelse(length(grep(TRUE, as.integer(as.character(df_evc_cd$patch_id))==as.integer(V(g)$patch_id[p])))<1,0,df_evc_cd$mf_evc[grep(TRUE, as.integer(as.character(df_evc_cd$patch_id))==as.integer(V(g)$patch_id[p]))])
    V(g)$cf_evc_cd[p] <- ifelse(length(grep(TRUE, as.integer(as.character(df_evc_cd$patch_id))==as.integer(V(g)$patch_id[p])))<1,0,df_evc_cd$cf_evc[grep(TRUE, as.integer(as.character(df_evc_cd$patch_id))==as.integer(V(g)$patch_id[p]))])
}}


########################################################################
###Calculate vertex betweenness
##Results of the internal betweenness.estimate function are slightly different from the one used here (always larger values)
##see: V(g_ud_d)$cd_lvb_ud <- betweenness.estimate(g_ud_d, vids = V(g_ud_d), directed = FALSE, lnbh_cutoff*connectivity_cutoff, weights = E(g_ud_d)$cd_u)
##But since the internal betweenness.estimate function is not reasonable to use with other weights than cost distance, the workarounds are used nevertheless
##Further investigation necessary!!!

###Calculate vertex betweenness on the undirected graph with only direct edges
V(g_ud_d)$cd_vb_ud <- betweenness(g_ud_d, v=V(g_ud_d), directed = FALSE, weights = E(g_ud_d)$cd_u)
vsp_cd_ud <- function(x) unlist(get.shortest.paths(g_ud_d, x,  V(g_ud_d)[grep(TRUE, path_lengths[x,]<(lnbh_cutoff*connectivity_cutoff))], weights=E(g_ud_d)$cd_u, output=c("vpath"))$vpath)
V(g_ud_d)$cd_lvb_ud <- hist(unlist(mclapply(mc.cores={0}, 1:length(V(g_ud_d)), function(x) vsp_cd_ud(x)[grep(FALSE, 1:length(vsp_cd_ud(x)) %in% append(c(1, length(vsp_cd_ud(x))), append(grep(TRUE, vsp_cd_ud(x)[1:length(vsp_cd_ud(x))]==x), grep(TRUE, vsp_cd_ud(x)[1:length(vsp_cd_ud(x))]==x)-1)))])), breaks=0:length(V(g_ud_d)), plot=FALSE)$counts/2

##weighted by maximum potential flow
V(g_ud_d)$mf_vb_ud <- betweenness(g_ud_d, v=V(g_ud_d), directed = TRUE, weights = E(g_ud_d)$mf_inv_u)
vsp_mf_u <- function(x) unlist(get.shortest.paths(g_ud_d, x,  V(g_ud_d)[grep(TRUE, path_lengths[x,]<(lnbh_cutoff*connectivity_cutoff))], weights=E(g_ud_d)$mf_inv_u, output=c("vpath"))$vpath)
V(g_ud_d)$mf_lvb_ud <- hist(unlist(mclapply(mc.cores={0}, 1:length(V(g_ud_d)), function(x) vsp_mf_u(x)[grep(FALSE, 1:length(vsp_mf_u(x)) %in% append(c(1, length(vsp_mf_u(x))), append(grep(TRUE, vsp_mf_u(x)[1:length(vsp_mf_u(x))]==x), grep(TRUE, vsp_mf_u(x)[1:length(vsp_mf_u(x))]==x)-1)))])), breaks=0:length(V(g_ud_d)), plot=FALSE)$counts/2

##weighted by competing potential flow
V(g_ud_d)$cf_vb_ud <- betweenness(g_ud_d, v=V(g_ud_d), directed = TRUE, weights = E(g_ud_d)$cf_inv_u)
vsp_cf_u <- function(x) unlist(get.shortest.paths(g_ud_d, x,  V(g_ud_d)[grep(TRUE, path_lengths[x,]<(lnbh_cutoff*connectivity_cutoff))], weights=E(g_ud_d)$cf_inv_u, output=c("vpath"))$vpath)
V(g_ud_d)$cf_lvb_ud <- hist(unlist(mclapply(mc.cores={0}, 1:length(V(g_ud_d)), function(x) vsp_cf_u(x)[grep(FALSE, 1:length(vsp_cf_u(x)) %in% append(c(1, length(vsp_cf_u(x))), append(grep(TRUE, vsp_cf_u(x)[1:length(vsp_cf_u(x))]==x), grep(TRUE, vsp_cf_u(x)[1:length(vsp_cf_u(x))]==x)-1)))])), breaks=0:length(V(g_ud_d)), plot=FALSE)$counts/2

###Calculate vertex betweenness on the undirected graph with only direct edges shorter connectivity cutoff
V(g_ud_d_cd)$cd_vb_udc <- betweenness(g_ud_d_cd, v=V(g_ud_d_cd), directed = FALSE, weights = E(g_ud_d_cd)$cd_u)
vsp_cd_udc <- function(x) unlist(get.shortest.paths(g_ud_d_cd, x,  V(g_ud_d_cd)[grep(TRUE, path_lengths_cd[x,]<(lnbh_cutoff*connectivity_cutoff))], weights=E(g_ud_d_cd)$cd_u, output=c("vpath"))$vpath)
V(g_ud_d_cd)$cd_lvb_udc <- hist(unlist(mclapply(mc.cores={0}, 1:length(V(g_ud_d_cd)), function(x) vsp_cd_udc(x)[grep(FALSE, 1:length(vsp_cd_udc(x)) %in% append(c(1, length(vsp_cd_udc(x))), append(grep(TRUE, vsp_cd_udc(x)[1:length(vsp_cd_udc(x))]==x), grep(TRUE, vsp_cd_udc(x)[1:length(vsp_cd_udc(x))]==x)-1)))])), breaks=0:length(V(g_ud_d_cd)), plot=FALSE)$counts/2

##weighted by maximum potential flow
V(g_ud_d_cd)$mf_vb_udc <- betweenness(g_ud_d_cd, v=V(g_ud_d_cd), directed = TRUE, weights = E(g_ud_d_cd)$mf_i_inv_ud)
vsp_mf_uc <- function(x) unlist(get.shortest.paths(g_ud_d_cd, x,  V(g_ud_d_cd)[grep(TRUE, path_lengths_cd[x,]<(lnbh_cutoff*connectivity_cutoff))], weights=E(g_ud_d_cd)$mf_inv_u, output=c("vpath"))$vpath)
V(g_ud_d_cd)$mf_lvb_udc <- hist(unlist(mclapply(mc.cores={0}, 1:length(V(g_ud_d_cd)), function(x) vsp_mf_uc(x)[grep(FALSE, 1:length(vsp_mf_uc(x)) %in% append(c(1, length(vsp_mf_uc(x))), append(grep(TRUE, vsp_mf_uc(x)[1:length(vsp_mf_uc(x))]==x), grep(TRUE, vsp_mf_uc(x)[1:length(vsp_mf_uc(x))]==x)-1)))])), breaks=0:length(V(g_ud_d_cd)), plot=FALSE)$counts/2

##weighted by competing potential flow
V(g_ud_d_cd)$cf_vb_udc <- betweenness(g_ud_d_cd, v=V(g_ud_d_cd), directed = TRUE, weights = E(g_ud_d_cd)$cf_inv_u)
vsp_cf_uc <- function(x) unlist(get.shortest.paths(g_ud_d_cd, x,  V(g_ud_d_cd)[grep(TRUE, path_lengths_cd[x,]<(lnbh_cutoff*connectivity_cutoff))], weights=E(g_ud_d_cd)$cf_inv_u, output=c("vpath"))$vpath)
V(g_ud_d_cd)$cf_lvb_udc <- hist(unlist(mclapply(mc.cores={0}, 1:length(V(g_ud_d_cd)), function(x) vsp_cf_uc(x)[grep(FALSE, 1:length(vsp_cf_uc(x)) %in% append(c(1, length(vsp_cf_uc(x))), append(grep(TRUE, vsp_cf_uc(x)[1:length(vsp_cf_uc(x))]==x), grep(TRUE, vsp_cf_uc(x)[1:length(vsp_cf_uc(x))]==x)-1)))])), breaks=0:length(V(g_ud_d_cd)), plot=FALSE)$counts/2

########################################################################
###Calculate neighborhood size
V(g_ud_cd)$nbh_s_uc <- as.integer(neighborhood.size(g_ud_cd, 1, nodes=V(g_ud_cd), mode=c("all")))
###Calculate local neighborhood size
V(g_ud_cd)$nbh_sl_uc <- as.integer(neighborhood.size(g_ud_cd, lnbh_cutoff, nodes=V(g_ud_cd), mode=c("all")))

if (db_driver == "sqlite") {{
con <- dbConnect(RSQLite::SQLite(), dbname = db)
}} else {{
con <- dbConnect(PostgreSQL::PostgreSQL(), dbname = db)
}}

##############################################
#Export network overview measures
grml <- rbind(c("Command", command),
c("Number of vertices", vertices_n),
c("Number of edges (undirected)", edges_n),
c("Number of direct edges (undirected)", edges_n_d),
c("Number of edges shorter than cost distance threshold (undirected)", edges_n_cd),
c("Number of direct edges shorter than cost distance threshold (undirected)", edges_n_d_cd),
c("Number of clusters of the entire graph", cl_no_d),
c("Number of clusters of the graph with only edges shorter cost distance threshold", cl_no_d_cd),
c("Size of the largest cluster of the entire graph", cl_max_size_d),
c("Size of the largest cluster of the graph with only edges shorter cost distance threshold", cl_max_size_d_cd),
c("Average size of the clusters of the entire graph", cl_mean_size_d),
c("Average size of the clusters of the graph with only edges shorter cost distance threshold", cl_mean_size_d_cd),
c("Diameter of the entire graph (undirected)", diam),
c("Diameter of the graph with only direct edges (undirected)", diam_d),
c("Diameter of the graph with only edges shorter cost distance threshold", diam_d_cd),
c("Density of the entire graph (directed)", density),
c("Density of the entire graph (undirected)", density_u),
c("Density of the graph with only direct edges (undirected)", density_ud))

if (cl_thresh > 0) {{
grml <- rbind(grml,
c("Density of the graph with only edges shorter cost distance threshold",  density_udc),
c("Modularity (from iebc) of the entire graph (undirected) weighted by cf", cf_iebc_u_mod),
c("Number of communities (at maximum modularity score (from iebc)) of the entire (undirected) graph weighted by cf", com_no_u),
c("com_sizes_u", toString(com_sizes_u, sep=',')),
c("com_sizes_u_names", toString(com_sizes_u_names, sep=','))
)
}}

network_overview_measures <- data.frame(
    measure=grml[,1],
    value=grml[,2])

# Write dataframe
dbWriteTable(con, network_output, network_overview_measures, overwrite=overwrite, row.names=FALSE)

###############################################################
#####Merge vertexmeasures in a dataframe and save it

###Create initial export data frame

vertex_export_df_ud <- as.data.frame(1:length(V(g_ud)))

####Adjust vertex-attributes first

g_ud <- remove.vertex.attribute(g_ud, "pop_proxy")

vertex_attribute_list <- list.vertex.attributes(g_ud)
if(length(vertex_attribute_list)>0) {{
    for (vl in vertex_attribute_list) {{
        vertex_export_df_ud <- as.data.frame(cbind(vertex_export_df_ud, get.vertex.attribute(g_ud, vl)))
    }}

    vertex_export_df_ud <- vertex_export_df_ud[2:length(vertex_export_df_ud)]
    names(vertex_export_df_ud) <- vertex_attribute_list
}}

###Create initial export data frame

vertex_export_df_ud_d <- as.data.frame(1:length(V(g_ud_d)))

####Adjust vertex-attributes first

g_ud_d <- remove.vertex.attribute(g_ud_d, "pop_proxy")

vertex_attribute_list <- list.vertex.attributes(g_ud_d)
if(length(vertex_attribute_list)>0) {{
    for (vl in vertex_attribute_list) {{
        vertex_export_df_ud_d <- as.data.frame(cbind(vertex_export_df_ud_d, get.vertex.attribute(g_ud_d, vl)))
    }}
    vertex_export_df_ud_d <- vertex_export_df_ud_d[2:length(vertex_export_df_ud_d)]
    names(vertex_export_df_ud_d) <- vertex_attribute_list
}}

###Create initial export data frame

vertex_export_df_ud_d_cd <- as.data.frame(1:length(V(g_ud_d_cd)))

####Adjust vertex-attributes first

g_ud_d_cd <- remove.vertex.attribute(g_ud_d_cd, "pop_proxy")

vertex_attribute_list <- list.vertex.attributes(g_ud_d_cd)

if(length(vertex_attribute_list)>0) {{
    for (vl in vertex_attribute_list) {{
        vertex_export_df_ud_d_cd <- as.data.frame(cbind(vertex_export_df_ud_d_cd, get.vertex.attribute(g_ud_d_cd, vl)))
    }}
    vertex_export_df_ud_d_cd <- vertex_export_df_ud_d_cd[2:length(vertex_export_df_ud_d_cd)]
    names(vertex_export_df_ud_d_cd) <- vertex_attribute_list
}}
###Create initial export data frame

vertex_export_df_d <- as.data.frame(1:length(V(g)))

vertex_attribute_list <- list.vertex.attributes(g)
if(length(vertex_attribute_list)>0) {{

    for (vl in vertex_attribute_list) {{
        vertex_export_df_d <- as.data.frame(cbind(vertex_export_df_d, get.vertex.attribute(g, vl)))
    }}
    vertex_export_df_d <- vertex_export_df_d[2:length(vertex_export_df_d)]
    names(vertex_export_df_d) <- vertex_attribute_list
}}

vertex_export_df <- merge(merge(merge(vertex_export_df_d, vertex_export_df_ud, by="patch_id"), vertex_export_df_ud_d, by="patch_id"), vertex_export_df_ud_d_cd, by="patch_id")

dbWriteTable(con, vertex_output, vertex_export_df, overwrite=overwrite, row.names=FALSE)

#########################################################################


###Create initial export data frame for the undirected graph

edge_export_df_ud <- as.data.frame(E(g_ud)$con_id_u)

####Adjust edge attributes for the undirected graphs first
g_ud <- remove.edge.attribute(g_ud, "con_id")
g_ud <- remove.edge.attribute(g_ud, "con_id_u")
g_ud <- remove.edge.attribute(g_ud, "from_p")
g_ud <- remove.edge.attribute(g_ud, "from_pop")
g_ud <- remove.edge.attribute(g_ud, "to_p")
g_ud <- remove.edge.attribute(g_ud, "to_pop")
g_ud <- remove.edge.attribute(g_ud, "cost_distance")
g_ud <- remove.edge.attribute(g_ud, "cd_u")
g_ud <- remove.edge.attribute(g_ud, "distance_weight_e")
#g_ud <- remove.edge.attribute(g_ud, "distance_weight_e_ud")
g_ud <- remove.edge.attribute(g_ud, "mf_o")
g_ud <- remove.edge.attribute(g_ud, "mf_i")
g_ud <- remove.edge.attribute(g_ud, "mf_o_inv")
g_ud <- remove.edge.attribute(g_ud, "mf_i_inv")
g_ud <- remove.edge.attribute(g_ud, "mf_u")
g_ud <- remove.edge.attribute(g_ud, "mf_inv_u")
g_ud <- remove.edge.attribute(g_ud, "cf")
g_ud <- remove.edge.attribute(g_ud, "cf_inv")
g_ud <- remove.edge.attribute(g_ud, "cf_u")
g_ud <- remove.edge.attribute(g_ud, "cf_inv_u")

edge_attribute_list <- list.edge.attributes(g_ud)

if(length(edge_attribute_list )>0) {{
    for (el in edge_attribute_list) {{
        edge_export_df_ud <- as.data.frame(cbind(edge_export_df_ud, get.edge.attribute(g_ud, el)))
    }}
    names(edge_export_df_ud) <- append("con_id_u", edge_attribute_list)
}}

###Create initial export data frame for the undirected graph with only direct edges

edge_export_df_ud_d <- as.data.frame(E(g_ud_d)$con_id_u)

####Adjust edge attributes for the undirected graph with only direct edges
g_ud_d <- remove.edge.attribute(g_ud_d, "con_id")
g_ud_d <- remove.edge.attribute(g_ud_d, "con_id_u")
g_ud_d <- remove.edge.attribute(g_ud_d, "from_p")
g_ud_d <- remove.edge.attribute(g_ud_d, "from_pop")
g_ud_d <- remove.edge.attribute(g_ud_d, "to_p")
g_ud_d <- remove.edge.attribute(g_ud_d, "to_pop")
g_ud_d <- remove.edge.attribute(g_ud_d, "cost_distance")
g_ud_d <- remove.edge.attribute(g_ud_d, "cd_u")
g_ud_d <- remove.edge.attribute(g_ud_d, "distance_weight_e")
#g_ud_d <- remove.edge.attribute(g_ud_d, "distance_weight_e_ud")
g_ud_d <- remove.edge.attribute(g_ud_d, "mf_o")
g_ud_d <- remove.edge.attribute(g_ud_d, "mf_i")
g_ud_d <- remove.edge.attribute(g_ud_d, "mf_o_inv")
g_ud_d <- remove.edge.attribute(g_ud_d, "mf_i_inv")
g_ud_d <- remove.edge.attribute(g_ud_d, "mf_u")
g_ud_d <- remove.edge.attribute(g_ud_d, "mf_inv_u")
g_ud_d <- remove.edge.attribute(g_ud_d, "cf")
g_ud_d <- remove.edge.attribute(g_ud_d, "cf_inv")
g_ud_d <- remove.edge.attribute(g_ud_d, "cf_u")
g_ud_d <- remove.edge.attribute(g_ud_d, "cf_inv_u")
g_ud_d <- remove.edge.attribute(g_ud_d, "isshort")
g_ud_d <- remove.edge.attribute(g_ud_d, "isshort_cd")
g_ud_d <- remove.edge.attribute(g_ud_d, "isshort_mf")
g_ud_d <- remove.edge.attribute(g_ud_d, "isshort_cf")

edge_attribute_list <- list.edge.attributes(g_ud_d)

if(length(edge_attribute_list )>0) {{
    for (el in edge_attribute_list) {{
        edge_export_df_ud_d <- as.data.frame(cbind(edge_export_df_ud_d, get.edge.attribute(g_ud_d, el)))
    }}
    names(edge_export_df_ud_d) <- append("con_id_u", edge_attribute_list)
}}
###Create initial export data frame for the undirected graph with only direct edges

edge_export_df_ud_d_cd <- as.data.frame(E(g_ud_d_cd)$con_id_u)

####Adjust edge attributes for the undirected graph with only direct edges
g_ud_d_cd <- remove.edge.attribute(g_ud_d_cd, "con_id")
g_ud_d_cd <- remove.edge.attribute(g_ud_d_cd, "con_id_u")
g_ud_d_cd <- remove.edge.attribute(g_ud_d_cd, "from_p")
g_ud_d_cd <- remove.edge.attribute(g_ud_d_cd, "from_pop")
g_ud_d_cd <- remove.edge.attribute(g_ud_d_cd, "to_p")
g_ud_d_cd <- remove.edge.attribute(g_ud_d_cd, "to_pop")
g_ud_d_cd <- remove.edge.attribute(g_ud_d_cd, "cost_distance")
g_ud_d_cd <- remove.edge.attribute(g_ud_d_cd, "cd_u")
g_ud_d_cd <- remove.edge.attribute(g_ud_d_cd, "distance_weight_e")
#g_ud_d_cd <- remove.edge.attribute(g_ud_d_cd, "distance_weight_e_ud")
g_ud_d_cd <- remove.edge.attribute(g_ud_d_cd, "mf_o")
g_ud_d_cd <- remove.edge.attribute(g_ud_d_cd, "mf_i")
g_ud_d_cd <- remove.edge.attribute(g_ud_d_cd, "mf_o_inv")
g_ud_d_cd <- remove.edge.attribute(g_ud_d_cd, "mf_i_inv")
g_ud_d_cd <- remove.edge.attribute(g_ud_d_cd, "mf_u")
g_ud_d_cd <- remove.edge.attribute(g_ud_d_cd, "mf_inv_u")
g_ud_d_cd <- remove.edge.attribute(g_ud_d_cd, "cf")
g_ud_d_cd <- remove.edge.attribute(g_ud_d_cd, "cf_inv")
g_ud_d_cd <- remove.edge.attribute(g_ud_d_cd, "cf_u")
g_ud_d_cd <- remove.edge.attribute(g_ud_d_cd, "cf_inv_u")
g_ud_d_cd <- remove.edge.attribute(g_ud_d_cd, "isshort")
g_ud_d_cd <- remove.edge.attribute(g_ud_d_cd, "isshort_cd")
g_ud_d_cd <- remove.edge.attribute(g_ud_d_cd, "isshort_mf")
g_ud_d_cd <- remove.edge.attribute(g_ud_d_cd, "isshort_cf")


edge_attribute_list <- list.edge.attributes(g_ud_d_cd)

if(length(edge_attribute_list )>0) {{
    for (el in edge_attribute_list) {{
        edge_export_df_ud_d_cd <- as.data.frame(cbind(edge_export_df_ud_d_cd, get.edge.attribute(g_ud_d_cd, el)))
    }}
    names(edge_export_df_ud_d_cd) <- append("con_id_u", edge_attribute_list)
}}


###Create initial export data frame for the directed graph
edge_export_df <- as.data.frame(1:length(E(g)))

####Adjust edge attributes for the directed graph first

E(g)$cd <- E(g)$cost_distance
E(g)$distk <- E(g)$distance_weight_e
E(g)$distk_u <- E(g)$distance_weight_e_ud
g <- remove.edge.attribute(g, "distance_weight_e")
g <- remove.edge.attribute(g, "distance_weight_e_ud")
g <- remove.edge.attribute(g, "cost_distance")

edge_attribute_list <- list.edge.attributes(g)

if(length(edge_attribute_list )>0) {{
    for (el in edge_attribute_list) {{
        edge_export_df <- as.data.frame(cbind(edge_export_df, get.edge.attribute(g, el)))
    }}
    names(edge_export_df) <- append("id", edge_attribute_list)
}}

export_df_list <-c("edge_export_df_ud", "edge_export_df_ud_d", "edge_export_df_ud_d_cd")
for (df in export_df_list) {{
    if(length(names(get(df)))) {{
        edge_export_df_final <- merge(edge_export_df, get(df), all.x=TRUE, by="con_id_u", suffixes=c("_x", "_y"))
        edge_export_df <- edge_export_df_final
    }}
}}

dbWriteTable(con, edge_output, edge_export_df, overwrite=overwrite, row.names=FALSE)

dbDisconnect(con)

if(qml_directory != '') {{
#########################
#CREATE .qml-files for edge measures visualistion in QGIS

no_quantile <- 5
colortable <- c('          <prop k="color" v="215,25,28,255"/>',
                '          <prop k="color" v="253,174,97,255"/>',
                '          <prop k="color" v="255,255,191,255"/>',
                '          <prop k="color" v="166,217,106,255"/>',
                '          <prop k="color" v="26,150,65,255"/>')
colortable_bin <- c('          <prop k="color" v="0,0,0,255"/>')
for (attribute in names(edge_export_df_final)) {{

#Skip id and geom columns
if(attribute %in% c("id", "con_id", "con_id_u", "from_p", "to_p", "WKT", "cf_ebc_vi")) {{ next }}

st_mod <- storage.mode(unlist(edge_export_df_final[grep(1, match(names(edge_export_df_final), attribute))]))
att_val <- unlist(edge_export_df_final[grep(1, match(names(edge_export_df_final), attribute))])

#Write header
qml <- c("<!DOCTYPE qgis PUBLIC 'http://mrcc.com/qgis.dtd' 'SYSTEM'>")
qml <- append(qml, '<qgis version="1.8" minimumScale="0" maximumScale="1e+08" hasScaleBasedVisibilityFlag="0">')
qml <- append(qml, '  <transparencyLevelInt>255</transparencyLevelInt>')

if((max(att_val, na.rm=TRUE)-min(att_val, na.rm=TRUE)==1)) {{

#More header
qml <- append(qml, paste('  <renderer-v2 attr="', attribute, '" symbollevels="0" type="categorizedSymbol">', sep=''))

#Categories
qml <- append(qml, '    <categories>')
qml <- append(qml, '      <category symbol=\"0\" value=\"1\" label=\"\"/>')
qml <- append(qml, '    </categories>')

#Write symbols
qml <- append(qml, '    <symbols>')
qml <- append(qml, '      <symbol outputUnit="MM" alpha="1" type="line" name="0">')
qml <- append(qml, '        <layer pass=\"0\" class=\"SimpleLine\" locked=\"0\">')
qml <- append(qml, '          <prop k=\"capstyle\" v=\"square\"/>')
qml <- append(qml, colortable_bin)
qml <- append(qml, '          <prop k=\"customdash\" v=\"5;2\"/>')
qml <- append(qml, '          <prop k=\"joinstyle\" v=\"bevel\"/>')
qml <- append(qml, '          <prop k=\"offset\" v=\"0\"/>')
qml <- append(qml, '          <prop k=\"penstyle\" v=\"solid\"/>')
qml <- append(qml, '          <prop k=\"use_custom_dash\" v=\"0\"/>')
qml <- append(qml, '          <prop k=\"width\" v=\"0.26\"/>')
qml <- append(qml, '        </layer>')
qml <- append(qml, '      </symbol>')
}}
else {{

attribute_quantile <- quantile(edge_export_df_final[grep(1, match(names(edge_export_df_final), attribute))], probs=seq(0, 1, 1/5), na.rm=TRUE, type=8)

#Write more header
qml <- append(qml, paste('  <renderer-v2 attr="', attribute, '" symbollevels="1" type="graduatedSymbol">', sep=''))

#Write ranges
ranges <- character()
qml <- append(qml, '    <ranges>')
for (quant in 1:no_quantile) {{
ranges <- append(ranges, paste('      <range symbol="', (quant-1),
                               '" lower="', attribute_quantile[quant],
                               '" upper="', attribute_quantile[(quant+1)],
                               '" label="', round(attribute_quantile[quant], 4),
                               ' - ', round(attribute_quantile[(quant+1)], 4),
                               '">', sep=''))
}}
qml <- append(qml, ranges)
qml <- append(qml, '    </ranges>')

#Write symbols
qml <- append(qml, '    <symbols>')

for (quant in 1:no_quantile) {{
qml <- append(qml, paste('      <symbol outputUnit="MM" alpha="1" type="line" name="',
                         (quant-1), '">',
                         sep=''))
qml <- append(qml, paste('        <layer pass=\"',
                         (quant-1),
                         '\" class=\"SimpleLine\" locked=\"0\">',
                         sep=''))
qml <- append(qml, '          <prop k=\"capstyle\" v=\"square\"/>')
qml <- append(qml, colortable[quant])
qml <- append(qml, '          <prop k=\"customdash\" v=\"5;2\"/>')
qml <- append(qml, '          <prop k=\"joinstyle\" v=\"bevel\"/>')
qml <- append(qml, '          <prop k=\"offset\" v=\"0\"/>')
qml <- append(qml, '          <prop k=\"penstyle\" v=\"solid\"/>')
qml <- append(qml, '          <prop k=\"use_custom_dash\" v=\"0\"/>')
qml <- append(qml, '          <prop k=\"width\" v=\"0.26\"/>')
qml <- append(qml, '        </layer>')
qml <- append(qml, '      </symbol>')
}}
}}
#Write Footer
qml <- append(qml, '    </symbols>')


qml <- append(qml, '    <source-symbol>')
qml <- append(qml, '      <symbol outputUnit=\"MM\" alpha=\"1\" type=\"line\" name=\"0\">')
qml <- append(qml, '        <layer pass=\"0\" class=\"SimpleLine\" locked=\"0\">')
qml <- append(qml, '          <prop k=\"capstyle\" v=\"square\"/>')
qml <- append(qml, '          <prop k=\"color\" v=\"161,238,135,255\"/>')
qml <- append(qml, '          <prop k=\"customdash\" v=\"5;2\"/>')
qml <- append(qml, '          <prop k=\"joinstyle\" v=\"bevel\"/>')
qml <- append(qml, '          <prop k=\"offset\" v=\"0\"/>')
qml <- append(qml, '          <prop k=\"penstyle\" v=\"solid\"/>')
qml <- append(qml, '          <prop k=\"use_custom_dash\" v=\"0\"/>')
qml <- append(qml, '          <prop k=\"width\" v=\"0.26\"/>')
qml <- append(qml, '        </layer>')
qml <- append(qml, '      </symbol>')
qml <- append(qml, '    </source-symbol>')
qml <- append(qml, '    <mode name="quantile"/>')
qml <- append(qml, '    <rotation field=""/>')
qml <- append(qml, '    <sizescale field=""/>')
qml <- append(qml, '  </renderer-v2>')
qml <- append(qml, '  <customproperties/>')
qml <- append(qml, paste('  <displayfield>"', attribute, '"</displayfield>', sep=''))
qml <- append(qml, '  <attributeactions/>')
qml <- append(qml, '</qgis>')

#Save qml-file
qml_output <- paste(qml_directory, paste(paste("edge_measures_", attribute, sep=''), "qml", sep='.'), sep="/")
con_qml <- file(qml_output, open="wt")
write.table(qml, con_qml, append = FALSE, quote = FALSE, sep = " ", eol = "\n", na = "NA", dec = ".", row.names = FALSE, col.names = FALSE)
close(con_qml)
}}
}}

########################################################################
#Close R
########################################################################
#q()
""".format(
        cores
    )

    if cores <= 1 or os_type == "Windows":
        rscript.replace("mclapply(mc.cores={}, ".format(cores), "lapply(")

    with open(os.path.join(qml_style_dir, "net_r_script.r"), "w") as rs_file:
        rs_file.write(rscript)

    robjects.r(rscript)

    grass.run_command(
        "g.copy", quiet=True, vector="{},{}".format(network_map, edge_output)
    )
    grass.run_command(
        "g.copy", quiet=True, vector="{},{}".format(in_vertices, vertex_output)
    )

    # Use v.db.connect instead of v.db.join (much faster)

    grass.run_command(
        "v.db.join",
        map=edge_output,
        column="cat",
        other_table=edge_output_tmp,
        other_column="con_id",
        quiet=True,
    )
    grass.run_command(
        "v.db.join",
        map=vertex_output,
        column="cat",
        other_table=vertex_output_tmp,
        other_column="patch_id",
        quiet=True,
    )

    update_history = "{}\n{}".format(net_hist_str, os.environ["CMDLINE"])

    grass.run_command(
        "v.support",
        flags="h",
        map=vertex_output,
        person=os.environ["USER"],
        cmdhist=update_history,
    )

    grass.run_command(
        "v.support",
        flags="h",
        map=edge_output,
        person=os.environ["USER"],
        cmdhist=update_history,
    )


if __name__ == "__main__":
    options, flags = grass.parser()
    atexit.register(cleanup)
    sys.exit(main())
