#!/usr/bin/env python

"""
MODULE:       r.connectivity.network
AUTHOR(S):    Stefan Blumentrath <stefan dot blumentrath at nina dot no>
PURPOSE:      Compute connectivity measures for a set of habitat patches
              based on graph-theory (usig the igraph-package in R).

              Recently, graph-theory has been characterised as an
              efficient and useful tool for conservation planning
              (e.g. Bunn et al. 2000, Calabrese & Fagan 2004,
              Minor & Urban 2008, Zetterberg et. al. 2010).
              As a part of the r.connectivity.* tool-chain,
              r.connectivity.network is intended to make graph-theory
              more easily available to conservation planning.

              r.connectivity.network is the 2nd tool of the
              r.connectivity.* toolchain and performs the (core) network
              analysis (usig the igraph-package in R) on the network
              data prepared with r.connectivity.distance. This network
              data is analysed on graph, edge and vertex level.

              Connectivity measures for the graph level are: number of
              vertices, number of edges, number of clusters, size of the
              largest cluster, average cluster size, diameter, density,
              modularity, number of communities, community size (in
              number of vertices) Network characteristics are visualised
              in a plot showing an  overview over number of connections,
              number of components and and the size of the largest
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
- - gscript.parse_command('v.support', map=edges, flags='g')[comments]
- - gscript.parse_command('v.support', map=nodes, flags='g')[comments]
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
## %flag
## % key: y
## % description: Calculate edge betweenness community (default is do not).
## % guisection: Measures
## %end

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
# % key: r
# % description: Remove indirect connections from network
# %end

import atexit
import os
from io import BytesIO
import sys
import platform
import warnings
import numpy as np
import matplotlib

# Required for Windows
matplotlib.use("wx")
import matplotlib.pyplot as plt
import grass.script as gscript
import grass.script.task as task
import grass.script.db as grass_db


# check if GRASS is running or not
if "GISBASE" not in os.environ:
    sys.exit("You must be in GRASS GIS to run this program")


def cleanup():
    """tmp_maps = gscript.read_command("g.list",
                                  type=['vector', 'raster'],
                                  pattern='{}*'.format(TMP_prefix),
                                  separator=',')

    if tmp_maps:
        gscript.run_command("g.remove", type=['vector', 'raster'],
                          pattern='{}*'.format(TMP_prefix), quiet=True,
                          flags='f')
    #gscript.del_temp_region()"""
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

    # Lazy import
    try:
        import igraph
    except ImportError:
        gscript.fatal(
            "Could not import igraph library! To install it run:",
            "pip install python-igraph",
        )
    # Input variables
    network_map = options["input"]
    # network_mapset = network_map.split('@')[0]
    # network = network_map.split('@')[1] if len(network_map.split('@'))
    # > 1 else None
    prefix = options["prefix"]
    cores = options["cores"]
    convergence_treshold = options["convergence_threshold"]
    base = float(options["base"])
    exponent = float(options["exponent"])
    qml_style_dir = options["qml_style"]
    if is_number(options["connectivity_cutoff"]):
        if float(options["connectivity_cutoff"]) > 0:
            connectivity_cutoff = float(options["connectivity_cutoff"])
        else:
            gscript.fatal('"connectivity_cutoff" has to be > 0.')
    else:
        gscript.fatal('Option "connectivity_cutoff" is not given as a number.')
    lnbh_cutoff = options["lnbh_cutoff"]
    cl_thresh = options["cl_thresh"]

    cd_cutoff = connectivity_cutoff

    kernel_plot = options["kernel_plot"]
    overview_plot = options["overview_plot"]

    verbose = gscript.verbosity() == 3
    overwrite = gscript.overwrite()

    edge_output = f"{prefix}_edge_measures"
    edge_output_tmp = f"{prefix}_edge_measures_tmp"
    vertex_output = f"{prefix}_vertex_measures"
    vertex_output_tmp = f"{prefix}_vertex_measures_tmp"
    network_output = f"{prefix}_network_measures"

    # Check if input parameters are correct
    for table in [vertex_output, edge_output, network_output]:
        if gscript.db.db_table_exist(table) and not overwrite:
            gscript.fatal(
                _(
                    'Table "{}" already exists. \
                         Use --o flag to overwrite'
                ).format(table)
            )

    if qml_style_dir:
        if not os.path.exists(qml_style_dir):
            gscript.fatal(
                _(
                    'QML output requested but directory "{}" \
                        does not exists.'
                ).format(qml_style_dir)
            )
        if not os.path.isdir(qml_style_dir):
            gscript.fatal(
                _(
                    'QML output requested but "{}" is not a \
                        directory.'
                ).format(qml_style_dir)
            )
        if not os.access(qml_style_dir, os.R_OK):
            gscript.fatal(
                _(
                    'Output directory "{}" for QML files is not \
                        writable.'
                ).format(qml_style_dir)
            )

    for plot in [kernel_plot, overview_plot]:
        if plot:
            if not os.path.exists(os.path.dirname(plot)):
                gscript.fatal(
                    _(
                        'Directory for output "{}" does not \
                            exists.'
                    ).format(plot)
                )
            if not os.access(os.path.dirname(plot), os.R_OK):
                gscript.fatal(
                    _(
                        'Output directory "{}" is not \
                            writable.'
                    ).format(plot)
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
    db_name = gscript.read_command("db.databases").rstrip("\n")

    net_hist_str = gscript.parse_command(
        "v.info", map=network_map, flags="h", delimiter=":"
    )["COMMAND"].split("\n")[0]
    # gscript.parse_command('v.info', map=network_map, flags='h'
    #                     ).split('\n')[0].split(': ')[1]
    # Parsing goes wrong in some cases (extractig with -tp) as input
    dist_cmd_dict = task.cmdstring_to_tuple(net_hist_str)
    command = os.environ["CMDLINE"]

    dist_prefix = dist_cmd_dict[1]["prefix"]
    pop_proxy = dist_cmd_dict[1]["pop_proxy"]

    in_vertices = "{}_vertices".format(dist_prefix)

    # OS adjustment
    os_type = platform.system()

    gscript.verbose(_("prefix is {}").format(prefix))
    gscript.verbose(_("cores is {}").format(cores))
    gscript.verbose(_("convergence_treshold is {}").format(convergence_treshold))
    gscript.verbose(_("base is {}").format(base))
    gscript.verbose(_("exponent is {}").format(exponent))
    gscript.verbose(_("cd_cutoff is {}").format(cd_cutoff))
    gscript.verbose(_("connectivity_cutoff is {}").format(connectivity_cutoff))
    gscript.verbose(_("lnbh_cutoff is {}").format(lnbh_cutoff))
    gscript.verbose(_("kernel_plot is {}").format(kernel_plot))
    gscript.verbose(_("overview_plot is {}").format(overview_plot))
    gscript.verbose(_("dist_prefix is {}").format(dist_prefix))
    gscript.verbose(_("EDGES is {}_edges").format(prefix))
    gscript.verbose(_("VERTICES is {}_vertices").format(prefix))
    gscript.verbose(_("cl_thresh is {}").format(cl_thresh))

    # Visualise the negative exponential decay kernel and exit (if requested)
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
        gscript.warning(
            _(
                "Parallel processing not yet supported on MS Windows. \
                       Setting number of cores to 1."
            )
        )
        cores = 1

    # Check igraph version
    if igraph.__version_info__ < (0, 6, 2):
        gscript.fatal(
            _(
                "The required igraph version is 0.6.2 or \
                     later, the installed version is {}. \
                     Please download and install at least igraph \
                     version 0.6.2"
            ).format(".".join(igraph.__version_info__))
        )

    driver = db_connection["driver"]
    database = db_name
    schema = db_connection["schema"]
    command = command

    gscript.verbose(_("Reading and preparing input data...\n"))
    vertices = np.gefromtext(
        BytesIO(
            gscript.read_command(
                "v.db.select",
                flags="c",
                map=in_vertices,
                columns="cat,{}".format(pop_proxy),
                separator=",",
            ).strip("\n")
        ),
        dtype=None,
        names=["patch_id", "pop_proxy"],
        delimiter=",",
    )

    # Read edge data
    edges = np.gefromtext(
        BytesIO(
            gscript.read_command(
                "v.db.select",
                flags="c",
                map=in_edges,
                columns="cat,from_p,to_p,dist",
                separator=",",
            ).strip("\n")
        ),
        dtype=None,
        names=["cat", "from_patch", "to_patch", "distance"],
        delimiter=",",
    )

    # The following can be done in igraph graph.simplify(combine_edges=dict(weight="mean"))
    # https://igraph.org/python/doc/igraph.GraphBase-class.html#simplify
    """con_id_u_pre = np.unique(np.sort(e_df[:,[1,2]]), axis=0)
    con_id_u_pre_df = data.frame(con_id_u_pre=unique(con_id_u_pre), con_id_u=1:length(unique(con_id_u_pre)))
    e_grouped_df_pre = merge(data.frame(con_id_u_pre=con_id_u_pre, con_id=1:length(e_df$from_p), from_p=e_df$from_p, to_p=e_df$to_p, dist=e_df$dist), con_id_u_pre_df, all.x=True)
    e_groups_ud = groupedData(dist ~ 1 | con_id_u, data=e_grouped_df_pre, FUN=mean)
    e_grouped_ud = gsummary(e_groups_ud, mean)
    e_grouped_ud_df = data.frame(con_id_u=as.vector(e_grouped_ud$con_id_u), dist_ud=as.vector(e_grouped_ud$dist))
    e_grouped_df = merge(data.frame(con_id=as.integer(e_grouped_df_pre$con_id), con_id_u=as.integer(e_grouped_df_pre$con_id_u), from_p=as.integer(e_grouped_df_pre$from_p), to_p=as.integer(e_grouped_df_pre$to_p), dist=as.double(e_grouped_df_pre$dist)), e_grouped_ud_df, all.x=True)"""

    # Merge vertices and edges to graph-object
    # Build directed graph
    gscript.verbose(_("Building the graph..."))

    g = Graph().as_directed()
    g.add_vertices(vertices[:, 0].astype("i").astype("S"))
    g.vs["patch_id"] = vertices[:, 0].astype("i")
    g.vs["pop_proxy"] = vertices[:, 1]

    g.add_edges(edges[:, [1, 2]].astype("i").astype("S"))
    g.es["cat"] = edges[:, 0].astype("i")
    g.es["from_patch"] = edges[:, 1].astype("i").astype("S")
    g.es["to_patch"] = edges[:, 2].astype("i").astype("S")
    g.es["cost_distance"] = edges[:, 3]

    # g = add.edges(g, t(edges), con_id=e$con_id, con_id_u=e$con_id_u, from_p=e$from_p, from_pop=e$from_pop, to_p=e$to_p, to_pop=e$to_pop, cost_distance=e$cost_distance, cd_u=e$cd_u, distance_weight_e=e$distance_weight_e, distance_weight_e_ud=e$distance_weight_e_ud, mf_o=e$mf_o, mf_o_inv=e$mf_o_inv, mf_i=e$mf_i, mf_i_inv=e$mf_i_inv, mf_u=e$mf_u, mf_inv_u=e$mf_inv_u, cf=e$cf, cf_inv=e$cf_inv, cf_u=e$cf_u, cf_inv_u=e$cf_inv_u)

    ##Remove connections longer than cost distance threshold if requested
    # if(remove_longer_cutoff == 1) {{
    # con_id_True =  e_grouped_df$con_id[grep(True, e_grouped_df$dist_ud<cd_cutoff)]
    # e_grouped_df_pre = merge(data.frame(con_id=con_id_True), e_grouped_df)
    # con_id_u_df = data.frame(con_id_u_old=unique(e_grouped_df_pre$con_id_u), con_id_u=1:length(unique(e_grouped_df_pre$con_id_u)))
    # e_grouped_df = merge(data.frame(con_id_old=e_grouped_df_pre$con_id, con_id_u_old=e_grouped_df_pre$con_id_u, con_id=1:length(e_grouped_df_pre$con_id), from_p=e_grouped_df_pre$from_p, to_p=e_grouped_df_pre$to_p, dist=e_grouped_df_pre$dist, dist_ud=e_grouped_df_pre$dist_ud), con_id_u_df, all.x=True)
    # }}

    # Merge vertex and grouped edge data
    # Can be done in igraph
    """from_pop = merge(data.frame(con_id=e_grouped_df$con_id, from_p=e_grouped_df$from_p), data.frame(from_p=as.integer(v$patch_id), from_pop=as.double(v$pop_proxy)), all.x=True, sort=False)
    to_pop = merge(data.frame(con_id=e_grouped_df$con_id, to_p=e_grouped_df$to_p), data.frame(to_p=as.integer(v$patch_id), to_pop=as.double(v$pop_proxy)), all.x=True, sort=False)
    e = merge(merge(from_pop, to_pop, sort=True), data.frame(con_id=e_grouped_df$con_id, con_id_u=e_grouped_df$con_id_u, cost_distance=e_grouped_df$dist, cd_u=e_grouped_df$dist_ud), by="con_id", sort=True)"""

    # Calculate attributes representing proxies for potential flow between patches
    g.es["exponential_distance_weight"] = np.exp(
        ((float(base) * (10.0 ** float(exponent))) * np.array(g.es["cost_distance"]))
    )  # distance_weight_e
    # out_areal_distance_weight_e = e$from_pop*distance_weight_e
    # in_areal_distance_weight_e = e$to_pop*distance_weight_e

    g.es["maximum_flow_out"] = g.es["from_pop"] * g.es["exponential_distance_weight"]
    g.es["maximum_flow_in"] = g.es["to_pop"] * g.es["exponential_distance_weight"]
    g.es["maximum_flow_sum"] = np.array(
        g.es["from_pop"] * g.es["exponential_distance_weight"]
    ) + np.array(g.es["to_pop"] * g.es["exponential_distance_weight"])

    g.es["maximum_flow_out_inverse"] = g.es["mf_o"] ** -1
    g.es["maximum_flow_in_inverse"] = g.es["mf_i"] ** -1
    # g.es["maximum_flow_sum_inverse"] = ((g.es["maximum_flow_sum"]*-1)-min(g.es["maximum_flow_sum"]*-1))*(ifelse(max(g.es["maximum_flow_sum"])>10000000000000000,10000000000000000,max(g.es["maximum_flow_sum"]))-ifelse(min(g.es["maximum_flow_sum"])<0.000000000001,0.000000000001,min(g.es["maximum_flow_sum"])))/(max(g.es["maximum_flow_sum"]*-1)-min(g.es["maximum_flow_sum"]*-1))+ifelse(min(g.es["maximum_flow_sum"])<0.000000000001,0.000000000001,min(g.es["maximum_flow_sum"]))

    """
    flow_df = data.frame(from_p=e$from_p, mf_i=mf_i)
    sum_mf_i_groups = groupedData(mf_i ~ from_p | from_p, data=as.data.frame(flow_df), FUN=sum)
    sum_mf_i_pre = gsummary(sum_mf_i_groups, sum)
    sum_mf_i = data.frame(from_p=as.integer(as.character(sum_mf_i_pre[,1])), sum_mf_i=as.double(sum_mf_i_pre[,2]))

    tmp = merge(merge(e, data.frame(con_id=e$con_id, distance_weight_e_ud=distance_weight_e_ud, distance_weight_e=distance_weight_e, mf_o=mf_o, mf_o_inv=mf_o_inv, mf_i=mf_i, mf_i_inv=mf_i_inv, mf_u=mf_u, mf_inv_u=mf_inv_u)), sum_mf_i)
    cf = tmp$mf_o*(tmp$mf_i/tmp$sum_mf_i)
    # cf = (cf-rep(min(cf),length(cf)))*(1/(rep(max(cf),length(cf))-rep(min(cf),length(cf))))
    # cf_inv = cf^-1
    # igraphs limits for weights in edge.betweenness function are aproximately max 12600000000000000 and min 0.000000000001
    cf_inv = ((cf*-1)-min(cf*-1))*(ifelse(max(cf)>10000000000000000,10000000000000000,max(cf))-ifelse(min(cf)<0.000000000001,0.000000000001,min(cf)))/(max(cf*-1)-min(cf*-1))+ifelse(min(cf)<0.000000000001,0.000000000001,min(cf))

    e = merge(tmp, data.frame(con_id=e$con_id, cf=cf, cf_inv=cf_inv), by="con_id", sort=True)

    cf_u_df = data.frame(con_id_u=e$con_id_u, cf=e$cf, cf_inv=e$cf_inv)
    cf_u_groups = groupedData(cf ~ 1 | con_id_u, data=cf_u_df, FUN=sum)
    cf_u_grouped = gsummary(cf_u_groups, sum)

    e = merge(e, data.frame(con_id_u=as.vector(cf_u_grouped$con_id_u), cf_u=as.vector(cf_u_grouped$cf), cf_inv_u=((as.vector(cf_u_grouped$cf)*-1)-min(as.vector(cf_u_grouped$cf)*-1))*(ifelse(max(as.vector(cf_u_grouped$cf))>10000000000000000,10000000000000000,max(as.vector(cf_u_grouped$cf)))-ifelse(min(as.vector(cf_u_grouped$cf))<0.000000000001,0.000000000001,min(as.vector(cf_u_grouped$cf))))/(max(as.vector(cf_u_grouped$cf)*-1)-min(as.vector(cf_u_grouped$cf)*-1))+ifelse(min(as.vector(cf_u_grouped$cf))<0.000000000001,0.000000000001,min(as.vector(cf_u_grouped$cf)))), all.x=True)

    # Collapse edge data for undirected graph
    con_id_u_unique = np.unique(e$con_id_u)
    ud_groups = groupedData(con_id ~ 1 | con_id_u, data=data.frame(con_id_u=e$con_id_u, con_id=e$con_id), FUN=mean)
    ud_grouped = gsummary(ud_groups)
    ud_grouped_df = data.frame(con_id_u=as.vector(ud_grouped$con_id_u), con_id_avg=as.vector(ud_grouped$con_id))
    e_ud_pre = merge(e, ud_grouped_df, all.x=True)
    first_con_id = data.frame(con_id=e_ud_pre$con_id[e_ud_pre$con_id_avg>e_ud_pre$con_id])
    e_ud = merge(first_con_id, e)
    """

    # Build undirected graph
    # graph.simplify(combine_edges=dict(weight="mean"))
    # https://igraph.org/python/doc/igraph.GraphBase-class.html#simplify
    g_ud = deepcopy(g)
    g_ud = g_ud.simplify(
        combine_edges=dict(
            mf_o="mean",
            mf_i="mean",
        )
    )
    g_ud.es["exponential_distance_weight_undirected"] = np.exp(
        (basis * (10 ^ exponent)) * np.array(g_ud.es["cost_distance_undirected"])
    )

    """
    g_ud = add.edges(g_ud, t(edges), con_id=e_ud$con_id,
                                     con_id_u=e_ud$con_id_u,
                                     from_p=e_ud$from_p,
                                     from_pop=e_ud$from_pop,
                                     to_p=e_ud$to_p,
                                     to_pop=e_ud$to_pop,
                                     cost_distance=e_ud$cost_distance,
                                     cd_u=e_ud$cd_u,
                                     distance_weight_e=e_ud$distance_weight_e,
                                     mf_o=e_ud$mf_o,
                                     mf_o_inv=e_ud$mf_o_inv,
                                     mf_i=e_ud$mf_i,
                                     mf_i_inv=e_ud$mf_i_inv,
                                     mf_u=e_ud$mf_u,
                                     mf_inv_u=e_ud$mf_inv_u,
                                     cf=e_ud$cf,
                                     cf_inv=e_ud$cf_inv,
                                     cf_u=e_ud$cf_u,
                                     cf_inv_u=e_ud$cf_inv_u)
    """

    # Classify connection with regards to shortest paths
    # con_id_u = unlist(lapply(0:(length(E(g))-1), function(x) E(g, path=c(sort(array(c(ends(g, x)[1], ends(g, x)[2])))[1], sort(array(c(ends(g, x)[1], ends(g, x)[2])))[2]))))
    # l1 = unlist(lapply(1:length(V(g_ud)), function(x) rep(x, length(V(g_ud)))))
    # l2 = rep(1:length(V(g_ud)), length(V(g_ud)))
    # fa = function(a) get.shortest.paths(g_ud, l1[a], l2[a], weights=g_ud.es["cd_u)
    # sp = fa(1:length(l1))
    # Set edge attributes
    # g.es["con_id_u = con_id_u

    # g.es["cd_u = unlist(mclapply(mc.cores={0}, 0:(length(E(g))-1), function(x) (E(g)[x]$cost_distance+E(g, path=c(ends(g, x)[2], ends(g, x)[1]))$cost_distance)/2))

    """
    ####################################
    ### Can the following be vectorised????

    g_ud.es["is_short_cd"] = as.integer(unlist(mclapply(mc.cores={0}, 1:(length(E(g_ud))), function(x) length(get.shortest.paths(g_ud, from=ends(g_ud, x)[1], to=ends(g_ud, x)[2], weights=g_ud.es["cd_u)$vpath[[1]])))==2)
    g_ud.es["is_short_mf"] = as.integer(unlist(mclapply(mc.cores={0}, 1:(length(E(g_ud))), function(x) length(get.shortest.paths(g_ud, from=ends(g_ud, x)[1], to=ends(g_ud, x)[2], weights=g_ud.es["mf_inv_u)$vpath[[1]])))==2)
    g_ud.es["is_short_cf"] = as.integer(unlist(mclapply(mc.cores={0}, 1:(length(E(g_ud))), function(x) length(get.shortest.paths(g_ud, from=ends(g_ud, x)[1], to=ends(g_ud, x)[2], weights=g_ud.es["cf_inv_u)$vpath[[1]])))==2)
    # g_ud.es["is_short"] = ifelse((g_ud.es["isshort_cd==0 & g_ud.es["isshort_mf==0 & g_ud.es["isshort_cf==0), 0, 1)
    """
    g_ud.es["is_short"] = np.min(
        g_ud.es["is_short_cd"], g_ud.es["is_short_mf"], g_ud.es["is_short_cf"]
    )

    ####################################

    # Add edge attributes to directed graph (for export)
    # g.es["isshort[grep(True, g.es["con_id_u %in% g_ud.es["con_id_u[grep(True, g_ud.es["isshort)])] = True
    # g.es["isshort[grep(True, g.es["con_id_u %in% g_ud.es["con_id_u[grep(False, g_ud.es["isshort)])] = False

    # Remove indirect connections if requested
    if remove_indirect == 1:
        g_ud_d = deepcopy(g_ud)
        g_ud_d.delete.edges(g_ud.es.select(is_short_eq=0))

    # Remove connections above connectivity threshold if requested
    """
    if connectivity_cutoff >= 0.0:
        g_ud_cd = deepcopy(g_ud)
        g_ud_cd = g_ud_cd.delete_edges(E(g_ud)[grep(True, g_ud.es["cd_u>=connectivity_cutoff)])
        g_ud_d_cd = deepcopy(g_ud_d)
        g_ud_d_cd = g_ud_d_cd.delete_edges(E(g_ud_d)[grep(True, g_ud_d.es["cd_u>=connectivity_cutoff)])
    """
    ########################################################################
    ### Analysis on graph level
    ########################################################################

    gscript.verbose(_("Starting analysis on graph level..."))

    ### graph measures
    vertices_n = len(g_ud.vs)
    edges_n = len(g_ud.es)
    edges_n_d = len(g_ud_d.es)
    edges_n_cd = len(g_ud_cd.es)
    edges_n_d_cd = len(g_ud_d_cd.es)

    ########################################################################
    ###### Calculate number of clusters
    # On the undirected graph with only direct edges and on the undirected graph with only direct edges shorter cost distance threshold
    cl_no_d = g_ud_d.clusters()["no"]
    cl_no_d_cd = g_ud_d_cd.clusters()["no"]

    """
    cls_size_d = as.vector(gsummary(groupedData(pop_size ~ 1 | cl, data.frame(cl=clusters(g_ud_d)$membership, pop_size=g_ud_d.vs["pop_proxy), order.groups=True, FUN=sum), sum)$pop_size)
    cls_size_d_cd = as.vector(gsummary(groupedData(pop_size ~ 1 | cl, data.frame(cl=clusters(g_ud_d_cd)$membership, pop_size=g_ud_d_cd.vs["pop_proxy), order.groups=True, FUN=sum), sum)$pop_size)
    """

    cl_max_size_d = max(cls_size_d)
    cl_max_size_d_cd = max(cls_size_d_cd)

    cl_mean_size_d = mean(cls_size_d)
    cl_mean_size_d_cd = mean(cls_size_d_cd)

    diam = g_ud.diameter(directed=False, unconnected=True, weights=g_ud.es["cd_u"])
    diam_d = g_ud_d.diameter(
        directed=False, unconnected=True, weights=g_ud_d.es["cd_u"]
    )
    diam_d_cd = g_ud_d_cd.diameter(
        directed=False, unconnected=True, weights=g_ud_d_cd.es["cd_u"]
    )

    density = g.density(g, loops=False)
    density_u = g_ud.density(g_ud, loops=False)
    density_ud = g_ud_d.density(g_ud_d, loops=False)
    density_udc = g_ud_d_cd.density(g_ud_d_cd, loops=False)

    """
    if network_overview_ps:
        ###### Edge removal operations
        for edge_length in np.sort(g_ud.es["cd_u"], decreasing=True, na.last=NA):
            cl_del_count = unlist(mclapply(mc.cores={0}, 1:length(idx), function(x) ifelse((clusters(delete.edges(g_ud, E(g_ud)[idx[1:x]]))$no/vertices_n)>=convergence_threshold||g_ud.es["cd_u[idx[x]]<=(connectivity_cutoff+(connectivity_cutoff*0.25)),clusters(delete.edges(g_ud, E(g_ud)[idx[1:x]]))$no,NA)))
            cl_del_max_size = unlist(mclapply(mc.cores={0}, 1:length(idx), function(x) ifelse((clusters(delete.edges(g_ud, E(g_ud)[idx[1:x]]))$no/vertices_n)>=convergence_threshold||g_ud.es["cd_u[idx[x]]<=(connectivity_cutoff+(connectivity_cutoff*0.25)),max(as.vector(gsummary(groupedData(pop_size ~ 1 | cl, data.frame(cl=clusters(delete.edges(g_ud, E(g_ud)[idx[1:x]]))$membership, pop_size=g_ud.vs["pop_proxy), order.groups=True, FUN=sum), sum)$pop_size)),NA)))
            cl_del_diam = unlist(mclapply(mc.cores={0}, 1:length(idx), function(x) ifelse((clusters(delete.edges(g_ud, E(g_ud)[idx[1:x]]))$no/vertices_n)>=convergence_threshold||g_ud.es["cd_u[idx[x]]<=(connectivity_cutoff+(connectivity_cutoff*0.25)),diameter(delete.edges(g_ud, E(g_ud)[idx[1:x]]), directed=False, unconnected=True, weights=E(delete.edges(g_ud, E(g_ud)[idx[1:x]]))$cd_u),NA)))
            extract = sort(grep(False, is.na(cl_del_count)), decreasing=True)
            df_edgeremoval = data.frame(distance=g_ud.es["cd_u[((idx[extract]))], cl_del_count=cl_del_count[extract], cl_del_max_size=cl_del_max_size[extract], cl_del_diam=cl_del_diam[extract])
            dist_inv_ix = sort(df_edgeremoval$distance, decreasing=False, na.last=NA, index.return=True)$ix

        ps.options(encoding="CP1257.enc", family="Helvetica", horizontal=False, fonts="Helvetica", paper="a4", pointsize=1/96, height=3.5, width=3.5)
        postscript(network_overview_ps)

        ### Check axis lables!!!
        matplot(df_edgeremoval$distance/(10^(nchar(as.integer(max(df_edgeremoval$distance)))-2)), df_edgeremoval$cl_del_count*100/vertices_n, type="l", ylab="", xlab=c("Connectivity threshold", paste("(Cost distance between patches in ", as.character(10^(nchar(as.integer(max(df_edgeremoval$distance)))-2)), ")", sep="")), lty=1, yaxt="n", yaxs="r", ylim=c(0, 100), yaxs="i", xaxs="i")
        if (connectivity_cutoff>0) abline(v=connectivity_cutoff/10^(nchar(as.integer(max(df_edgeremoval$distance)))-2), col="red", lty=3)
        ifelse(connectivity_cutoff>0, legend("topleft",
                                             #inset=c(0,-0.15), bty = "n",
                                             xpd=True,
                                             c("Clusters (in % of maximum possible clusters)", "Size of the largest cluster (in % of total population size)", "Number of edges (in % of maximum possible number of edges)", "Diameter (in % of diameter of the entire graph)", "Connectivity threshold used in analysis"), lty=c(1, 2, 3, 4, 3), col=c("black", "black", "black", "black", "red"), inset=0.005, bty="o", box.lty=0, bg="White"), legend("topleft", c("Clusters (in % of maximum possible clusters)", "Size of the largest cluster (in % of total population size)", "Number of edges (in % of maximum possible number of edges)", "Diameter (in % of diameter of the entire graph)"), lty=c(1, 2, 3, 4), col=c("black", "black", "black", "black"), inset=0.005, bty="o", box.lty=0, bg="White"))
        axis(2, seq.int(0, 100, 25), labels=c("0 %", "25 %", "50 %", "75 %", "100 %"), yaxs="r")
        matplot(df_edgeremoval$distance/(10^(nchar(as.integer(max(df_edgeremoval$distance)))-2)), df_edgeremoval$cl_del_max_size*100/sum(g.vs["pop_proxy), type="l", lty=2, yaxt="n", yaxs="i", add=True)
        lines(df_edgeremoval$distance/(10^(nchar(as.integer(max(df_edgeremoval$distance)))-2)), dist_inv_ix*100/edges_n, type="l", lty=3)
        lines(df_edgeremoval$distance/(10^(nchar(as.integer(max(df_edgeremoval$distance)))-2)), df_edgeremoval$cl_del_diam*100/diam_d, type="l", lty=4)
        # Lable axis 4!!!
        # axis(4, seq.int(0, 100, 25), yaxs="i", labels=seq.int(0, ceiling((as.integer(edges_n)/(10^(nchar(as.integer(edges_n))-2))))*(10^(nchar(as.integer(edges_n))-2)), ceiling((as.integer(edges_n)/(10^(nchar(as.integer(edges_n))-2))))*(10^(nchar(as.integer(edges_n))-2))/4))
    """
    ########################################################################
    ###Analysis on edge level
    ########################################################################

    gscript.verbose("Starting analysis on edge level...")

    ########################################################################
    ###### Calculate minimum spanning trees (MST) on the undirected graph with only direct edges
    ### Minimum spanning tree weighted by maximum potential flow

    g_ud_d.es["mf_mst_ud"] = 0
    # E(g_ud_d.es["mf_mst_ud"] = [grep(True, g_ud_d.es["con_id %in% E(minimum.spanning.tree(g_ud_d, weights=g_ud_d.es["mf_inv_u))$con_id)]$mf_mst_ud = 1

    ### Minimum spanning tree weighted by cost distance
    g_ud_d.es["cd_mst_ud"] = 0
    # g_ud_d.es["cd_mst_ud"] = [grep(True, g_ud_d.es["con_id %in% E(minimum.spanning.tree(g_ud_d, weights=g_ud_d.es["cd_u))$con_id)]$cd_mst_ud = 1

    g_ud_d.es["cf_mst_ud"] = 0
    # g_ud_d.es["cf_mst_ud"] = [grep(True, g_ud_d.es["con_id %in% E(minimum.spanning.tree(g_ud_d, weights=g_ud_d.es["cf_inv_u))$con_id)]$cf_mst_ud = 1

    ###### Calculate minimum spanning trees (MST) on the undirected graph with only direct edges shorter cost distance threshold
    ### Minimum spanning tree weighted by maximum potential flow
    g_ud_d_cd.es["mf_mst_udc"] = 0
    # g_ud_d_cd.es["mf_mst_udc"] = [grep(True, E(g_ud_d_cd)$con_id %in% E(minimum.spanning.tree(g_ud_d_cd, weights=E(g_ud_d_cd)$mf_inv_u))$con_id)]$mf_mst_udc = 1

    ### Minimum spanning tree weighted by cost distance
    g_ud_d_cd.es["cd_mst_udc"] = 0
    # g_ud_d_cd.es["cd_mst_udc"] = [grep(True, E(g_ud_d_cd)$con_id %in% E(minimum.spanning.tree(g_ud_d_cd, weights=E(g_ud_d_cd)$cd_u))$con_id)]$cd_mst_udc = 1

    ### Minimum spanning tree weighted by competing potential flow
    g_ud_d_cd.es["cf_mst_udc"] = 0
    # g_ud_d_cd.es["cf_mst_udc"] = [grep(True, E(g_ud_d_cd)$con_id %in% E(minimum.spanning.tree(g_ud_d_cd, weights=E(g_ud_d_cd)$cf_inv_u))$con_id)]$cf_mst_udc = 1

    ########################################################################
    ### Identify bridges for the undirected graph
    # E(g_ud.es["is_br_u"] = as.integer(unlist(mclapply(mc.cores={0}, 1:(length(E(g_ud))), function(x) clusters(delete.edges(g_ud, E(g_ud)[as.integer(x)]))$no-cl_no_d)))

    # Identify bridges for the undirected graph with only direct edges
    # E(g_ud_d.es["is_br_ud"] = as.integer(unlist(mclapply(mc.cores={0}, 1:(length(E(g_ud_d))), function(x) clusters(delete.edges(g_ud_d, E(g_ud_d)[as.integer(x)]))$no-cl_no_d)))

    ### Identify bridges for the undirected graph with only direct edges shorter cost distance threshold
    # E(g_ud_d_cd.es["is_br_udc"] = as.integer(unlist(mclapply(mc.cores={0}, 1:(length(E(g_ud_d_cd))), function(x) clusters(delete.edges(g_ud_d_cd, E(g_ud_d_cd)[as.integer(x)]))$no-cl_no_d_cd)))

    ########################################################################

    biconnected_components_d = biconnected.components(g_ud)

    # Identify component edges (biconnected components) for the undirected graph with only direct edges
    g_ud.es["bc_e_u"] = 0
    for c in range(biconnected_components_d["no"]):
        g_ud.es["bc_e_u"][unlist(biconnected_components_d["component_edges"][c])] = c

    # Identify tree edges (biconnected components) for the undirected graph with only direct edges
    g_ud.es["bc_te_u"] = 0
    for c in range(biconnected_components_d["no"]):
        g_ud.es["bc_te_u"][unlist(biconnected_components_d["tree_edges"][c])] = c

    biconnected_components_d = biconnected.components(g_ud_d)
    # Identify component edges (biconnected components) for the undirected graph with only direct edges
    g_ud_d.es["bc_e_ud"] = 0
    for c in range(biconnected_components_d["no"]):
        g_ud_d.es["bc_e_ud"][unlist(biconnected_components_d["component_edges"][c])] = c

    # Identify tree edges (biconnected components) for the undirected graph with only direct edges
    g_ud_d.es["bc_te_ud"] = 0
    for c in range(biconnected_components_d["no"]):
        g_ud_d.es["bc_te_ud"][unlist(biconnected_components_d["tree_edges"][c])] = c

    biconnected_components_d_cd = biconnected.components(g_ud_d_cd)
    # Identify component edges (biconnected components) for the undirected graph with only direct edges shorter cost distance threshold
    g_ud_d_cd.es["bc_e_udc"] = 0
    for c in range(biconnected_components_d_cd["no"]):
        g_ud_d_cd.es["bc_e_udc"][
            unlist(biconnected_components_d_cd["component_edges"][c])
        ] = c

    # Identify tree edges (biconnected components) for the undirected graph with only direct edges shorter cost distance threshold
    g_ud_d_cd.es["bc_te_udc"] = 0
    for c in range(biconnected_components_d_cd["no"]):
        g_ud_d_cd.es["bc_te_udc"][
            unlist(biconnected_components_d_cd["tree_edges"][c])
        ] = c

    ########################################################################
    ### Calculate edge betweenness
    ## Results of the internal edge.betweeness.estimate function are slightly different from the one used here (always larger values):
    ## see: g_ud_d.es["cd_leb_ud = edge.betweenness.estimate(g_ud_d, e=E(g_ud_d), directed=False, lnbh_cutoff*connectivity_cutoff, weights=g_ud_d.es["cd_u)
    ## But since the internal edge.betweeness.estimate function is not reasonable to use with other weights than cost distance, the workarounds are used nevertheless
    ## Further investigation necessary!!!

    ### Calculate edge betweenness on the entire undirected graph with only direct edges

    path_lengths = shortest.paths(
        g_ud_d, v=g_ud_d.vs, to=g_ud_d.vs, weights=g_ud_d.es["cd_u"]
    )

    # weighted by cost distance
    g_ud_d.es["cd_eb_ud"] = edge.betweenness(
        g_ud_d, e=g_ud_d.es, directed=False, weights=g_ud_d.es["cd_u"]
    )
    # g_ud_d.es.["cd_leb_ud"] = hist(unlist(mclapply(mc.cores={0}, 1:length(V(g_ud_d)), function(x) get.shortest.paths(g_ud_d, x,  V(g_ud_d)[grep(True, path_lengths[x,]<(lnbh_cutoff*connectivity_cutoff))], weights=g_ud_d.es["cd_u, output=c("epath"))$epath)), breaks=0:(length(E(g_ud_d))), plot=False)$counts/2
    # g_ud_d.es["cd_leb_ud = edge.betweenness.estimate(g_ud_d, e=E(g_ud_d), directed=False, lnbh_cutoff*connectivity_cutoff, weights=g_ud_d.es["cd_u)

    # weighted by maximum potential flow
    g_ud_d.es["mf_eb_ud"] = edge.betweenness(
        g_ud_d, e=g_ud_d.es, directed=False, weights=g_ud_d.es["mf_inv_u"]
    )
    # g_ud_d.es.["mf_leb_ud"] = hist(unlist(mclapply(mc.cores={0}, 1:length(V(g_ud_d)), function(x) get.shortest.paths(g_ud_d, x,  V(g_ud_d)[grep(True, path_lengths[x,]<(lnbh_cutoff*connectivity_cutoff))], weights=g_ud_d.es["mf_inv_u, output=c("epath"))$epath)), breaks=0:(length(E(g_ud_d))), plot=False)$counts/2

    # weighted by competing potential flow
    g_ud_d.es["cf_eb_ud"] = edge.betweenness(
        g_ud_d, e=g_ud_d.es, directed=False, weights=g_ud_d.es["cf_inv_u"]
    )
    # g_ud_d.es.["cf_leb_ud"] = hist(unlist(mclapply(mc.cores={0}, 1:length(V(g_ud_d)), function(x) get.shortest.paths(g_ud_d, x,  V(g_ud_d)[grep(True, path_lengths[x,]<(lnbh_cutoff*connectivity_cutoff))], weights=g_ud_d.es["cf_inv_u, output=c("epath"))$epath)), breaks=0:(length(E(g_ud_d))), plot=False)$counts/2

    ########################################################################
    ### Calculate edge betweenness on the entire undirected graph with only direct edges shorter cost distance threshold

    path_lengths_cd = shortest.paths(
        g_ud_d_cd, v=g_ud_d_cd.vs, to=g_ud_d_cd.vs, weights=g_ud_d_cd.es["cd_u"]
    )

    # weighted by cost distance
    g_ud_d_cd.es["cd_eb_udc"] = edge.betweenness(
        g_ud_d_cd, e=g_ud_d_cd.es, directed=False, weights=g_ud_d_cd.es["cd_u"]
    )
    # g_ud_d_cd.es["cd_leb_udc"] = hist(unlist(mclapply(mc.cores={0}, 1:length(V(g_ud_d_cd)), function(x) get.shortest.paths(g_ud_d_cd, x,  V(g_ud_d_cd)[grep(True, path_lengths_cd[x,]<(lnbh_cutoff*connectivity_cutoff))], weights=E(g_ud_d_cd)$cd_u, output=c("epath"))$epath)), breaks=0:(length(E(g_ud_d_cd))), plot=False)$counts/2

    # weighted by maximum potential flow
    g_ud_d_cd.es["mf_eb_udc"] = edge.betweenness(
        g_ud_d_cd, e=g_ud_d_cd.es, directed=False, weights=g_ud_d_cd.es["mf_inv_u"]
    )
    # g_ud_d_cd.es["mf_leb_udc"] = hist(unlist(mclapply(mc.cores={0}, 1:length(V(g_ud_d_cd)), function(x) get.shortest.paths(g_ud_d_cd, x,  V(g_ud_d_cd)[grep(True, path_lengths_cd[x,]<(lnbh_cutoff*connectivity_cutoff))], weights=E(g_ud_d_cd)$mf_inv_u, output=c("epath"))$epath)), breaks=0:(length(E(g_ud_d_cd))), plot=False)$counts/2

    # weighted by competing potential flow
    g_ud_d_cd.es["cf_eb_udc"] = edge.betweenness(
        g_ud_d_cd, e=g_ud_d_cd.es, directed=False, weights=g_ud_d_cd.es["cf_inv_u"]
    )
    # g_ud_d_cd.es["cf_leb_udc"] = hist(unlist(mclapply(mc.cores={0}, 1:length(V(g_ud_d_cd)), function(x) get.shortest.paths(g_ud_d_cd, x,  V(g_ud_d_cd)[grep(True, path_lengths_cd[x,]<(lnbh_cutoff*connectivity_cutoff))], weights=E(g_ud_d_cd)$cf_inv_u, output=c("epath"))$epath)), breaks=0:(length(E(g_ud_d_cd))), plot=False)$counts/2

    if cl_thresh > 0:
        #########################################################################
        ####### Calculate edge betweenness community on the undirected graph
        ## weighted by competing potential flow
        ebc = edge.betweenness.community(
            g_ud,
            weights=g_ud.es["cf_inv_u"],
            directed=False,
            edge_betweenness=True,
            merges=True,
            bridges=True,
            modularity=True,
            membership=True,
        )

        g_ud.es["cf_iebc_v"] = ebc["edge.betweenness"]
        # cf_iebc_m = ebc$merges
        g_ud.es["cf_iebc_r"] = ebc["removed.edges"]
        # g_ud.es["cf_iebc_b"] = unlist(mclapply(mc.cores={0}, 1:length(E(g_ud)), function(x) ifelse(x %in% ebc$bridges, 1, 0)))
        g_ud.es["cf_iebc_c"] = crossing(ebc, g_ud)

        # g.vs["cf_iebc_mo = ebc$modularity
        g.vs["cf_iebc_me"] = ebc.es["membership"]

        """
        com_struct = as.character(cutat(ebc, cl_no_d))
        for i in (cl_no_d+1):(cl_no_d+cl_thresh):
            com_struct = paste(com_struct, cutat(ebc, i), sep=';')

        V(g.vs["cf_iebc_cs"] = as.character(com_struct)
        V(g.vs["cf_iebc_cl"] = cutat(ebc, (cl_no_d+cl_thresh))

        cf_iebc_u_mod = modularity(ebc)
        com_no_u = length(ebc)
        com_sizes_u = sizes(ebc)
        com_sizes_u_names = paste("Size of comumity ", names(sizes(ebc)), " (at maximum modularity score (from iebc))", sep="")
        """

        # The following workaround was written when igraph did not support weights when calculating edge.betweenness.community
        # The results of this procedure differ significantly from the (new) edge.betweenness.community in igraph 0.6-2 with weights (above)
        # In a first visual the results of the following procedure look more reasonable, but further investigation is necessary!!!

        n = 1
        ebc_con_id_u = 0
        ebc_rank = 0
        ebc_value = 0
        ebc_clust = 0
        g_ud.vs["cf_ebc_cs"] = str(clusters(g_ud)["membership"])
        del_eb_g = g_ud

        for edge in del_eb_g.es:
            # Recalculate edge betweenness for the remaining edges
            del_eb_g.es["cf_eb_ud"] = edge.betweenness(
                del_eb_g, e=del_eb_g.es, directed=False, weights=del_eb_g.es["cf_inv_u"]
            )
            # Identify edge with highest edge betweenness value
            # idx = sort.int(del_eb_g.es["cf_eb_ud"], decreasing=True, na.last=NA, index.return=True).es["ix"][1]
            # Save edge betweenness value for this edge
            ebc_con_id_u[n] = del_eb_g.es["con_id_u"][idx]
            ebc_rank[n] = n
            ebc_clust[n] = clusters(del_eb_g)["no"]
            # if((ebc_clust[n]-cl_no_d)<(cl_no_d+cl_thresh)) {{if(n>1) {{if(ebc_clust[n]>ebc_clust[n-1]) g_ud.vs["cf_ebc_cs = paste(g_ud.vs["cf_ebc_cs, clusters(del_eb_g)$membership, sep=";")}}}}
            ebc_value[n] = del_eb_g.es["cf_eb_ud"][idx]
            # Delete edge with highest edge betweenness value
            del_eb_g = delete.edges(del_eb_g, del_eb_g.es[idx])
            n += 1

        # g_ud.vs["cf_ebc_cl"] = unlist(mclapply(mc.cores={0}, 1:length(V(g_ud)), function(x) strsplit(g_ud.vs["cf_ebc_cs, ";")[[x]][(cl_no_d+cl_thresh)]))

        # ebc_df = merge(data.frame(con_id=g.es["con_id, con_id_u=g.es["con_id_u), data.frame(con_id_u=ebc_con_id_u, ebc_rank=ebc_rank, ebc_clust=ebc_clust, ebc_value=ebc_value), all.x=True)
        # idx = sort.int(ebc_con_id_u, index.return=True)["ix"]
        g_ud.es["cf_ebc_v"] = ebc_value[idx]
        g_ud.es["cf_ebc_r"] = ebc_rank[idx]
        g_ud.es["cf_ebc_c"] = ebc_clust[idx]

        g_ud.es["cf_ebc_vi"] = strftime(Sys.time() + g_ud.es["cf_ebc_r"])

        #########################################################################
        ### Calculate community connectors (based on community structure from ebc)
        """
        com_membership = data.frame(patch_id=g_ud_d_cd.vs["patch_id"], com=g_ud.vs["cf_ebc_cl"])
        com_pc_pre = merge(merge(data.frame(id=1:length(E(g)), from_p=g.es["from_p, to_p=g.es["to_p), com_membership, by.x="from_p", by.y="patch_id"),  com_membership, by.x="to_p", by.y="patch_id")[order(merge(merge(data.frame(id=1:length(E(g)), from_p=g.es["from_p, to_p=g.es["to_p), com_membership, by.x="from_p", by.y="patch_id"),  com_membership, by.x="to_p", by.y="patch_id")$id) ,]
        g.es["cf_ebc_cc"] = ifelse(com_pc_pre$com.x==com_pc_pre$com.y,0,1)
        """
    else:
        gscript.verbose(_("Skipping comunity algorithms..."))

    ########################################################################
    ###### Calculate cluster membership
    g_ud_d.vs["cl_ud"] = clusters(g_ud_d)["membership"]
    g_ud_d_cd.vs["cl_udc"] = clusters(g_ud_d_cd)["membership"]

    #########################################################################
    ### Calculate potential cluster connectors (based on cost distance threshold)
    """
    cl_membership = data.frame(patch_id=g_ud_d_cd.vs["patch_id, cl=g_ud_d_cd.vs["cl_udc)
    cl_pc_pre = merge(merge(data.frame(id=1:length(E(g)), from_p=g.es["from_p, to_p=g.es["to_p), cl_membership, by.x="from_p", by.y="patch_id"),  cl_membership, by.x="to_p", by.y="patch_id")[order(merge(merge(data.frame(id=1:length(E(g)), from_p=g.es["from_p, to_p=g.es["to_p), cl_membership, by.x="from_p", by.y="patch_id"),  cl_membership, by.x="to_p", by.y="patch_id")$id) ,]
    g.es["cl_pc"] = ifelse(cl_pc_pre$cl.x==cl_pc_pre$cl.y,0,1)
    """
    gscript.verbose(_("Starting analysis on vertex level..."))

    ########################################################################
    ### Analysis on vertex level
    ########################################################################

    ########################################################################
    ###### Calculate degree centrality
    # On the directed graph
    # g.vs["deg_dir = as.integer(degree(g, v=V(g), mode=c("in")))

    # On the entire undirected graph
    g_ud.vs["deg_u"] = degree(g_ud, v=g_ud.vs)

    # On the undirected graph with edges shorter cost distance threshold
    g_ud_cd.vs["deg_uc"] = degree(g_ud_cd, v=g_ud_cd.vs)

    # On the undirected graph with only direct edges
    g_ud_d.vs["deg_ud"] = degree(g_ud_d, v=g_ud_d.vs)

    # On the undirected graph with only direct edges shorter cost distance threshold
    g_ud_d_cd.vs["deg_udc"] = degree(g_ud_d_cd, v=g_ud_d_cd.vs)

    ########################################################################
    ###### Calculate closeness centrality
    g_ud_d.vs["cd_cl_ud"] = closeness(
        g_ud_d, vids=g_ud_d.vs, weights=g_ud_d.es["cd_u"], normalized=False
    )
    g_ud_d.vs["mf_cl_ud"] = closeness(
        g_ud_d, vids=g_ud_d.vs, weights=g_ud_d.es["mf_inv_u"], normalized=False
    )
    g_ud_d.vs["cf_cl_ud"] = closeness(
        g_ud_d, vids=g_ud_d.vs, weights=g_ud_d.es["cf_inv_u"], normalized=False
    )

    g_ud_d_cd.vs["cd_cl_udc"] = closeness(
        g_ud_d_cd, vids=g_ud_d_cd.vs, weights=g_ud_d_cd.es["cd_u"], normalized=False
    )
    g_ud_d_cd.vs["mf_cl_udc"] = closeness(
        g_ud_d_cd, vids=g_ud_d_cd.vs, weights=g_ud_d_cd["mf_inv_u"], normalized=False
    )
    g_ud_d_cd.vs["cf_cl_udc"] = closeness(
        g_ud_d_cd, vids=g_ud_d_cd.vs, weights=g_ud_d_cd["cf_inv_u"], normalized=False
    )

    ########################################################################
    ###### Calculate biconnected components

    # On the undirected graph with only direct edges
    # Number of new clusters when a vertex is deleted
    # g_ud_d.vs["art_ud"] = unlist(mclapply(mc.cores={0}, 1:(length(V(g_ud_d))), function(x) ifelse((clusters(delete.vertices(g_ud_d, V(g_ud_d)[x]))$no-cl_no_d)<0,0,clusters(delete.vertices(g_ud_d, V(g_ud_d)[x]))$no-cl_no_d)))
    # Vertex is articulation point
    g_ud_d.vs["art_p_ud"] = 0
    g_ud_d.vs[art_p_ud[biconnected_components_d["articulation_points"]]] = 1

    # On the undirected graph with only direct edges shorter cost distance threshold
    # Number of new clusters when a vertex is deleted
    # g_ud_d_cd.vs["art_udc"] = unlist(mclapply(mc.cores={0}, 1:(length(V(g_ud_d_cd))), function(x) ifelse((clusters(delete.vertices(g_ud_d_cd, V(g_ud_d_cd)[x]))$no-cl_no_d_cd)<0,0,clusters(delete.vertices(g_ud_d_cd, V(g_ud_d_cd)[x]))$no-cl_no_d_cd)))
    # Vertex is articulation point
    g_ud_d_cd.vs["art_p_udc"] = 0
    g_ud_d_cd.vs["art_p_udc"][biconnected_components_d_cd["articulation_points"]] = 1

    ########################################################################
    ###### Calculate eigenvector centrality
    # Calculate eigenvector for the entire directed graph
    """
    # Calculate eigenvector centrality weighted by competing potential flow
    cf_evc_groups = groupedData(cf ~ 1 | to_p, data=e, FUN=sum)
    cf_evc = gsummary(cf_evc_groups, sum)
    df_cf_evc_d = data.frame(patch_id=cf_evc["to_p"], cf_evc_d=cf_evc["cf"])

    # Calculate eigenvector centrality weighted by maximum potential flow
    mf_o_evc_groups = groupedData(mf_o ~ 1 | to_p, data=e, FUN=sum)
    mf_o_evc = gsummary(mf_o_evc_groups, sum)
    df_mf_i_evc_d = data.frame(patch_id=mf_o_evc$to_p, mf_evc_d=mf_o_evc$mf_o)

    df_evc_d = merge(df_cf_evc_d, df_mf_i_evc_d)

    ###### Calculate eigenvector centrality on the directed graph with edges shorter cost distance threshold
    # Calculate eigenvector centrality weighted by competing potential flow
    evc_udc_pre = data.frame(to_p=e$to_p[grep(True, e$cd_u<connectivity_cutoff)], mf_o=e$mf_o[grep(True, e$cd_u<connectivity_cutoff)], cf=e$cf[grep(True, e$cd_u<connectivity_cutoff)])

    cf_evc_udc_groups = groupedData(cf ~ 1 | to_p, data=evc_udc_pre, FUN=sum)
    cf_evc_udc = gsummary(cf_evc_udc_groups, sum)
    df_cf_evc_udc = data.frame(patch_id=cf_evc_udc$to_p, cf_evc=cf_evc_udc$cf)

    # Calculate eigenvector centrality weighted by maximum potential flow
    mf_o_evc_udc_groups = groupedData(mf_o ~ 1 | to_p, data=evc_udc_pre, FUN=sum)
    mf_o_evc_udc = gsummary(mf_o_evc_udc_groups, sum)
    df_mf_o_evc_udc = data.frame(patch_id=mf_o_evc_udc$to_p, mf_evc=mf_o_evc_udc$mf_o)

    df_evc_cd = merge(df_cf_evc_udc, df_mf_o_evc_udc)

    ### Add eigenvector centrality as a vertex attribute
    for p in 1:length(V(g)):
        g.vs["mf_evc_d[p] = ifelse(length(grep(True, as.integer(as.character(df_evc_d$patch_id))==as.integer(g.vs["patch_id[p])))<1,0,df_evc_d$mf_evc[grep(True, as.integer(as.character(df_evc_d$patch_id))==as.integer(g.vs["patch_id[p]))])
        g.vs["cf_evc_d[p] = ifelse(length(grep(True, as.integer(as.character(df_evc_d$patch_id))==as.integer(g.vs["patch_id[p])))<1,0,df_evc_d$cf_evc[grep(True, as.integer(as.character(df_evc_d$patch_id))==as.integer(g.vs["patch_id[p]))])
        g.vs["mf_evc_cd[p] = ifelse(length(grep(True, as.integer(as.character(df_evc_cd$patch_id))==as.integer(g.vs["patch_id[p])))<1,0,df_evc_cd$mf_evc[grep(True, as.integer(as.character(df_evc_cd$patch_id))==as.integer(g.vs["patch_id[p]))])
        g.vs["cf_evc_cd[p] = ifelse(length(grep(True, as.integer(as.character(df_evc_cd$patch_id))==as.integer(g.vs["patch_id[p])))<1,0,df_evc_cd$cf_evc[grep(True, as.integer(as.character(df_evc_cd$patch_id))==as.integer(g.vs["patch_id[p]))])

    ########################################################################
    ### Calculate vertex betweenness
    ## Results of the internal betweeness.estimate function are slightly different from the one used here (always larger values)
    ## see: g_ud_d.vs["cd_lvb_ud = betweenness.estimate(g_ud_d, vids = V(g_ud_d), directed = False, lnbh_cutoff*connectivity_cutoff, weights = g_ud_d.es["cd_u)
    ## But since the internal betweeness.estimate function is not reasonable to use with other weights than cost distance, the workarounds are used nevertheless
    ## Further investigation necessary!!!

    ### Calculate vertex betweenness on the undirected graph with only direct edges
    g_ud_d.vs["cd_vb_ud = betweenness(g_ud_d, v=V(g_ud_d), directed = False, weights = g_ud_d.es["cd_u)
    vsp_cd_ud = function(x) unlist(get.shortest.paths(g_ud_d, x,  V(g_ud_d)[grep(True, path_lengths[x,]<(lnbh_cutoff*connectivity_cutoff))], weights=g_ud_d.es["cd_u, output=c("vpath"))$vpath)
    g_ud_d.vs["cd_lvb_ud = hist(unlist(mclapply(mc.cores={0}, 1:length(V(g_ud_d)), function(x) vsp_cd_ud(x)[grep(False, 1:length(vsp_cd_ud(x)) %in% append(c(1, length(vsp_cd_ud(x))), append(grep(True, vsp_cd_ud(x)[1:length(vsp_cd_ud(x))]==x), grep(True, vsp_cd_ud(x)[1:length(vsp_cd_ud(x))]==x)-1)))])), breaks=0:length(V(g_ud_d)), plot=False)$counts/2

    # weighted by maximum potential flow
    g_ud_d.vs["mf_vb_ud = betweenness(g_ud_d, v=V(g_ud_d), directed = True, weights = g_ud_d.es["mf_inv_u)
    vsp_mf_u = function(x) unlist(get.shortest.paths(g_ud_d, x,  V(g_ud_d)[grep(True, path_lengths[x,]<(lnbh_cutoff*connectivity_cutoff))], weights=g_ud_d.es["mf_inv_u, output=c("vpath"))$vpath)
    g_ud_d.vs["mf_lvb_ud = hist(unlist(mclapply(mc.cores={0}, 1:length(V(g_ud_d)), function(x) vsp_mf_u(x)[grep(False, 1:length(vsp_mf_u(x)) %in% append(c(1, length(vsp_mf_u(x))), append(grep(True, vsp_mf_u(x)[1:length(vsp_mf_u(x))]==x), grep(True, vsp_mf_u(x)[1:length(vsp_mf_u(x))]==x)-1)))])), breaks=0:length(V(g_ud_d)), plot=False)$counts/2

    # weighted by competing potential flow
    g_ud_d.vs["cf_vb_ud = betweenness(g_ud_d, v=V(g_ud_d), directed = True, weights = g_ud_d.es["cf_inv_u)
    vsp_cf_u = function(x) unlist(get.shortest.paths(g_ud_d, x,  V(g_ud_d)[grep(True, path_lengths[x,]<(lnbh_cutoff*connectivity_cutoff))], weights=g_ud_d.es["cf_inv_u, output=c("vpath"))$vpath)
    g_ud_d.vs["cf_lvb_ud = hist(unlist(mclapply(mc.cores={0}, 1:length(V(g_ud_d)), function(x) vsp_cf_u(x)[grep(False, 1:length(vsp_cf_u(x)) %in% append(c(1, length(vsp_cf_u(x))), append(grep(True, vsp_cf_u(x)[1:length(vsp_cf_u(x))]==x), grep(True, vsp_cf_u(x)[1:length(vsp_cf_u(x))]==x)-1)))])), breaks=0:length(V(g_ud_d)), plot=False)$counts/2

    ### Calculate vertex betweenness on the undirected graph with only direct edges shorter connectivity cutoff
    g_ud_d_cd.vs["cd_vb_udc = betweenness(g_ud_d_cd, v=V(g_ud_d_cd), directed = False, weights = E(g_ud_d_cd)$cd_u)
    vsp_cd_udc = function(x) unlist(get.shortest.paths(g_ud_d_cd, x,  V(g_ud_d_cd)[grep(True, path_lengths_cd[x,]<(lnbh_cutoff*connectivity_cutoff))], weights=E(g_ud_d_cd)$cd_u, output=c("vpath"))$vpath)
    g_ud_d_cd.vs["cd_lvb_udc = hist(unlist(mclapply(mc.cores={0}, 1:length(V(g_ud_d_cd)), function(x) vsp_cd_udc(x)[grep(False, 1:length(vsp_cd_udc(x)) %in% append(c(1, length(vsp_cd_udc(x))), append(grep(True, vsp_cd_udc(x)[1:length(vsp_cd_udc(x))]==x), grep(True, vsp_cd_udc(x)[1:length(vsp_cd_udc(x))]==x)-1)))])), breaks=0:length(V(g_ud_d_cd)), plot=False)$counts/2

    # weighted by maximum potential flow
    g_ud_d_cd.vs["mf_vb_udc = betweenness(g_ud_d_cd, v=V(g_ud_d_cd), directed = True, weights = E(g_ud_d_cd)$mf_i_inv_ud)
    vsp_mf_uc = function(x) unlist(get.shortest.paths(g_ud_d_cd, x,  V(g_ud_d_cd)[grep(True, path_lengths_cd[x,]<(lnbh_cutoff*connectivity_cutoff))], weights=E(g_ud_d_cd)$mf_inv_u, output=c("vpath"))$vpath)
    g_ud_d_cd.vs["mf_lvb_udc = hist(unlist(mclapply(mc.cores={0}, 1:length(V(g_ud_d_cd)), function(x) vsp_mf_uc(x)[grep(False, 1:length(vsp_mf_uc(x)) %in% append(c(1, length(vsp_mf_uc(x))), append(grep(True, vsp_mf_uc(x)[1:length(vsp_mf_uc(x))]==x), grep(True, vsp_mf_uc(x)[1:length(vsp_mf_uc(x))]==x)-1)))])), breaks=0:length(V(g_ud_d_cd)), plot=False)$counts/2

    # weighted by competing potential flow
    g_ud_d_cd.vs["cf_vb_udc = betweenness(g_ud_d_cd, v=V(g_ud_d_cd), directed = True, weights = E(g_ud_d_cd)$cf_inv_u)
    vsp_cf_uc = function(x) unlist(get.shortest.paths(g_ud_d_cd, x,  V(g_ud_d_cd)[grep(True, path_lengths_cd[x,]<(lnbh_cutoff*connectivity_cutoff))], weights=E(g_ud_d_cd)$cf_inv_u, output=c("vpath"))$vpath)
    g_ud_d_cd.vs["cf_lvb_udc = hist(unlist(mclapply(mc.cores={0}, 1:length(V(g_ud_d_cd)), function(x) vsp_cf_uc(x)[grep(False, 1:length(vsp_cf_uc(x)) %in% append(c(1, length(vsp_cf_uc(x))), append(grep(True, vsp_cf_uc(x)[1:length(vsp_cf_uc(x))]==x), grep(True, vsp_cf_uc(x)[1:length(vsp_cf_uc(x))]==x)-1)))])), breaks=0:length(V(g_ud_d_cd)), plot=False)$counts/2

    ########################################################################
    ### Calculate neighborhood size
    g_ud_cd.vs["nbh_s_uc = as.integer(neighborhood.size(g_ud_cd, 1, nodes=V(g_ud_cd), mode=c("all")))
    ### Calculate local neighborhood size
    g_ud_cd.vs["nbh_sl_uc = as.integer(neighborhood.size(g_ud_cd, lnbh_cutoff, nodes=V(g_ud_cd), mode=c("all")))

    if (db_driver == "sqlite") {{
    con = dbConnect(RSQLite::SQLite(), dbname = db)
    }} else {{
    con = dbConnect(PostgreSQL::PostgreSQL(), dbname = db)
    }}

    ##############################################
    # Export network overview measures
    grml = rbind(c("Command", command),
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

    if cl_thresh > 0:
        grml = rbind(grml,
    c("Density of the graph with only edges shorter cost distance threshold",  density_udc),
    c("Modularity (from iebc) of the entire graph (undirected) weighted by cf", cf_iebc_u_mod),
    c("Number of communities (at maximum modularity score (from iebc)) of the entire (undirected) graph weighted by cf", com_no_u),
    c("com_sizes_u", toString(com_sizes_u, sep=',')),
    c("com_sizes_u_names", toString(com_sizes_u_names, sep=','))
    )

        network_overview_measures = data.frame(
            measure=grml[,1],
            value=grml[,2])

    # Write dataframe
    dbWriteTable(con, network_output, network_overview_measures, overwrite=overwrite, row.names=False)
    """

    ###############################################################
    ##### Merge vertexmeasures in a dataframe and save it

    ### Create initial export data frame
    # vertex_export_df_ud = as.data.frame(1:length(V(g_ud)))

    #### Adjust vertex-attributes first

    g_ud = remove.vertex.attribute(g_ud, "pop_proxy")

    vertex_attribute_list = list.vertex.attributes(g_ud)
    if len(vertex_attribute_list) > 0:
        for vl in vertex_attribute_list:
            # vertex_export_df_ud = as.data.frame(cbind(vertex_export_df_ud, get.vertex.attribute(g_ud, vl)))
            continue

        vertex_export_df_ud = vertex_export_df_ud[2 : length(vertex_export_df_ud)]
        vertex_export_df_ud["names"] = vertex_attribute_list

    ### Create initial export data frame

    # vertex_export_df_ud_d = as.data.frame(1:length(V(g_ud_d)))

    #### Adjust vertex-attributes first
    g_ud_d = remove.vertex.attribute(g_ud_d, "pop_proxy")

    vertex_attribute_list = list.vertex.attributes(g_ud_d)
    if length(vertex_attribute_list) > 0:
        for vl in vertex_attribute_list:
            # vertex_export_df_ud_d = as.data.frame(cbind(vertex_export_df_ud_d, get.vertex.attribute(g_ud_d, vl)))
            continue

        # vertex_export_df_ud_d = vertex_export_df_ud_d[2:length(vertex_export_df_ud_d)]
        vertex_export_df_ud_d["names"] = vertex_attribute_list

    ###Create initial export data frame
    # vertex_export_df_ud_d_cd = as.data.frame(1:length(V(g_ud_d_cd)))

    ####Adjust vertex-attributes first
    g_ud_d_cd = remove.vertex.attribute(g_ud_d_cd, "pop_proxy")
    vertex_attribute_list = list.vertex.attributes(g_ud_d_cd)

    if len(vertex_attribute_list) > 0:
        for vl in vertex_attribute_list:
            # vertex_export_df_ud_d_cd = as.data.frame(cbind(vertex_export_df_ud_d_cd, get.vertex.attribute(g_ud_d_cd, vl)))
            continue

        # vertex_export_df_ud_d_cd = vertex_export_df_ud_d_cd[2:length(vertex_export_df_ud_d_cd)]
        vertex_export_df_ud_d_cd["names"] = vertex_attribute_list

    ###Create initial export data frame
    # vertex_export_df_d = as.data.frame(1:length(V(g)))
    vertex_attribute_list = list.vertex.attributes(g)
    if len(vertex_attribute_list) > 0:
        for vl in vertex_attribute_list:
            # vertex_export_df_d = as.data.frame(cbind(vertex_export_df_d, get.vertex.attribute(g, vl)))
            continue

        # vertex_export_df_d = vertex_export_df_d[2:length(vertex_export_df_d)]
        vertex_export_df_d["names"] = vertex_attribute_list

    # vertex_export_df = merge(merge(merge(vertex_export_df_d, vertex_export_df_ud, by="patch_id"), vertex_export_df_ud_d, by="patch_id"), vertex_export_df_ud_d_cd, by="patch_id")
    # dbWriteTable(con, vertex_output, vertex_export_df, overwrite=overwrite, row.names=False)

    #########################################################################
    ###Create initial export data frame for the undirected graph
    # edge_export_df_ud = as.data.frame(g_ud.es["con_id_u)

    ####Adjust edge attributes for the undirected graphs first
    g_ud = remove.edge.attribute(g_ud, "con_id")
    g_ud = remove.edge.attribute(g_ud, "con_id_u")
    g_ud = remove.edge.attribute(g_ud, "from_p")
    g_ud = remove.edge.attribute(g_ud, "from_pop")
    g_ud = remove.edge.attribute(g_ud, "to_p")
    g_ud = remove.edge.attribute(g_ud, "to_pop")
    g_ud = remove.edge.attribute(g_ud, "cost_distance")
    g_ud = remove.edge.attribute(g_ud, "cd_u")
    g_ud = remove.edge.attribute(g_ud, "distance_weight_e")
    # g_ud = remove.edge.attribute(g_ud, "distance_weight_e_ud")
    g_ud = remove.edge.attribute(g_ud, "mf_o")
    g_ud = remove.edge.attribute(g_ud, "mf_i")
    g_ud = remove.edge.attribute(g_ud, "mf_o_inv")
    g_ud = remove.edge.attribute(g_ud, "mf_i_inv")
    g_ud = remove.edge.attribute(g_ud, "mf_u")
    g_ud = remove.edge.attribute(g_ud, "mf_inv_u")
    g_ud = remove.edge.attribute(g_ud, "cf")
    g_ud = remove.edge.attribute(g_ud, "cf_inv")
    g_ud = remove.edge.attribute(g_ud, "cf_u")
    g_ud = remove.edge.attribute(g_ud, "cf_inv_u")

    edge_attribute_list = list.edge.attributes(g_ud)

    if length(edge_attribute_list) > 0:
        for el in edge_attribute_list:
            # edge_export_df_ud = as.data.frame(cbind(edge_export_df_ud, get.edge.attribute(g_ud, el)))
            continue
        edge_export_df_ud["names"] = append("con_id_u", edge_attribute_list)

    ###Create initial export data frame for the undirected graph with only direct edges
    # edge_export_df_ud_d = as.data.frame(g_ud_d.es["con_id_u)

    ####Adjust edge attributes for the undirected graph with only direct edges
    g_ud_d = remove.edge.attribute(g_ud_d, "con_id")
    g_ud_d = remove.edge.attribute(g_ud_d, "con_id_u")
    g_ud_d = remove.edge.attribute(g_ud_d, "from_p")
    g_ud_d = remove.edge.attribute(g_ud_d, "from_pop")
    g_ud_d = remove.edge.attribute(g_ud_d, "to_p")
    g_ud_d = remove.edge.attribute(g_ud_d, "to_pop")
    g_ud_d = remove.edge.attribute(g_ud_d, "cost_distance")
    g_ud_d = remove.edge.attribute(g_ud_d, "cd_u")
    g_ud_d = remove.edge.attribute(g_ud_d, "distance_weight_e")
    # g_ud_d = remove.edge.attribute(g_ud_d, "distance_weight_e_ud")
    g_ud_d = remove.edge.attribute(g_ud_d, "mf_o")
    g_ud_d = remove.edge.attribute(g_ud_d, "mf_i")
    g_ud_d = remove.edge.attribute(g_ud_d, "mf_o_inv")
    g_ud_d = remove.edge.attribute(g_ud_d, "mf_i_inv")
    g_ud_d = remove.edge.attribute(g_ud_d, "mf_u")
    g_ud_d = remove.edge.attribute(g_ud_d, "mf_inv_u")
    g_ud_d = remove.edge.attribute(g_ud_d, "cf")
    g_ud_d = remove.edge.attribute(g_ud_d, "cf_inv")
    g_ud_d = remove.edge.attribute(g_ud_d, "cf_u")
    g_ud_d = remove.edge.attribute(g_ud_d, "cf_inv_u")
    g_ud_d = remove.edge.attribute(g_ud_d, "isshort")
    g_ud_d = remove.edge.attribute(g_ud_d, "isshort_cd")
    g_ud_d = remove.edge.attribute(g_ud_d, "isshort_mf")
    g_ud_d = remove.edge.attribute(g_ud_d, "isshort_cf")

    edge_attribute_list = list.edge.attributes(g_ud_d)

    if len(edge_attribute_list) > 0:
        for el in edge_attribute_list:
            # edge_export_df_ud_d = as.data.frame(cbind(edge_export_df_ud_d, get.edge.attribute(g_ud_d, el)))
            pass

        edge_export_df_ud_d["names"] = append("con_id_u", edge_attribute_list)

    ###Create initial export data frame for the undirected graph with only direct edges
    # edge_export_df_ud_d_cd = as.data.frame(E(g_ud_d_cd)$con_id_u)

    ####Adjust edge attributes for the undirected graph with only direct edges
    g_ud_d_cd = remove.edge.attribute(g_ud_d_cd, "con_id")
    g_ud_d_cd = remove.edge.attribute(g_ud_d_cd, "con_id_u")
    g_ud_d_cd = remove.edge.attribute(g_ud_d_cd, "from_p")
    g_ud_d_cd = remove.edge.attribute(g_ud_d_cd, "from_pop")
    g_ud_d_cd = remove.edge.attribute(g_ud_d_cd, "to_p")
    g_ud_d_cd = remove.edge.attribute(g_ud_d_cd, "to_pop")
    g_ud_d_cd = remove.edge.attribute(g_ud_d_cd, "cost_distance")
    g_ud_d_cd = remove.edge.attribute(g_ud_d_cd, "cd_u")
    g_ud_d_cd = remove.edge.attribute(g_ud_d_cd, "distance_weight_e")
    # g_ud_d_cd = remove.edge.attribute(g_ud_d_cd, "distance_weight_e_ud")
    g_ud_d_cd = remove.edge.attribute(g_ud_d_cd, "mf_o")
    g_ud_d_cd = remove.edge.attribute(g_ud_d_cd, "mf_i")
    g_ud_d_cd = remove.edge.attribute(g_ud_d_cd, "mf_o_inv")
    g_ud_d_cd = remove.edge.attribute(g_ud_d_cd, "mf_i_inv")
    g_ud_d_cd = remove.edge.attribute(g_ud_d_cd, "mf_u")
    g_ud_d_cd = remove.edge.attribute(g_ud_d_cd, "mf_inv_u")
    g_ud_d_cd = remove.edge.attribute(g_ud_d_cd, "cf")
    g_ud_d_cd = remove.edge.attribute(g_ud_d_cd, "cf_inv")
    g_ud_d_cd = remove.edge.attribute(g_ud_d_cd, "cf_u")
    g_ud_d_cd = remove.edge.attribute(g_ud_d_cd, "cf_inv_u")
    g_ud_d_cd = remove.edge.attribute(g_ud_d_cd, "isshort")
    g_ud_d_cd = remove.edge.attribute(g_ud_d_cd, "isshort_cd")
    g_ud_d_cd = remove.edge.attribute(g_ud_d_cd, "isshort_mf")
    g_ud_d_cd = remove.edge.attribute(g_ud_d_cd, "isshort_cf")

    edge_attribute_list = list.edge.attributes(g_ud_d_cd)

    if len(edge_attribute_list) > 0:
        for el in edge_attribute_list:
            # edge_export_df_ud_d_cd = as.data.frame(cbind(edge_export_df_ud_d_cd, get.edge.attribute(g_ud_d_cd, el)))
            pass
        edge_export_df_ud_d_cd["names"] = append("con_id_u", edge_attribute_list)

    ###Create initial export data frame for the directed graph
    # edge_export_df = as.data.frame(1:length(E(g)))

    ####Adjust edge attributes for the directed graph first
    g.es["cd"] = g.es["cost_distance"]
    g.es["distk"] = g.es["distance_weight_e"]
    g.es["distk_u"] = g.es["distance_weight_e_ud"]
    g = remove.edge.attribute(g, "distance_weight_e")
    g = remove.edge.attribute(g, "distance_weight_e_ud")
    g = remove.edge.attribute(g, "cost_distance")

    edge_attribute_list = list.edge.attributes(g)

    if len(edge_attribute_list) > 0:
        for el in edge_attribute_list:
            # edge_export_df = as.data.frame(cbind(edge_export_df, get.edge.attribute(g, el)))
            pass

        edge_export_df["names"] = append("id", edge_attribute_list)

    export_df_list = (
        "edge_export_df_ud",
        "edge_export_df_ud_d",
        "edge_export_df_ud_d_cd",
    )
    for df in export_df_list:
        if len(names(get(df))):
            edge_export_df_final = merge(
                edge_export_df,
                get(df),
                all_x=True,
                by="con_id_u",
                suffixes=("_x", "_y"),
            )
            edge_export_df = edge_export_df_final

    dbWriteTable(con, edge_output, edge_export_df, overwrite=overwrite, row_names=False)
    dbDisconnect(con)

    if qml_directory != "":
        #########################
        # CREATE .qml-files for edge measures visualistion in QGIS

        no_quantile = 5
        colortable = (
            '          <prop k="color" v="215,25,28,255"/>',
            '          <prop k="color" v="253,174,97,255"/>',
            '          <prop k="color" v="255,255,191,255"/>',
            '          <prop k="color" v="166,217,106,255"/>',
            '          <prop k="color" v="26,150,65,255"/>',
        )
        colortable_bin = '          <prop k="color" v="0,0,0,255"/>'
        for attribute in edge_export_df_final:

            # Skip id and geom columns
            if attribute in (
                "id",
                "con_id",
                "con_id_u",
                "from_p",
                "to_p",
                "WKT",
                "cf_ebc_vi",
            ):
                continue

            st_mod = storage.mode(
                unlist(
                    edge_export_df_final[
                        grep(1, match(names(edge_export_df_final), attribute))
                    ]
                )
            )
            att_val = unlist(
                edge_export_df_final[
                    grep(1, match(names(edge_export_df_final), attribute))
                ]
            )

        # Write header
        qml = "<!DOCTYPE qgis PUBLIC 'http://mrcc.com/qgis.dtd' 'SYSTEM'>"
        qml += '<qgis version="1.8" minimumScale="0" maximumScale="1e+08" hasScaleBasedVisibilityFlag="0">'
        qml += "  <transparencyLevelInt>255</transparencyLevelInt>"

        if max(att_val, na_rm=True) - min(att_val, na_rm=True) == 1:

            # More header
            qml += paste(
                '  <renderer-v2 attr="',
                attribute,
                '" symbollevels="0" type="categorizedSymbol">',
                sep="",
            )

            # Categories
            qml += "    <categories>"
            qml += '      <category symbol="0" value="1" label=""/>'
            qml += "    </categories>"

            # Write symbols
            qml += "    <symbols>"
            qml += '      <symbol outputUnit="MM" alpha="1" type="line" name="0">'
            qml += '        <layer pass="0" class="SimpleLine" locked="0">'
            qml += '          <prop k="capstyle" v="square"/>'
            qml += colortable_bin
            qml += '          <prop k="customdash" v="5;2"/>'
            qml += '          <prop k="joinstyle" v="bevel"/>'
            qml += '          <prop k="offset" v="0"/>'
            qml += '          <prop k="penstyle" v="solid"/>'
            qml += '          <prop k="use_custom_dash" v="0"/>'
            qml += '          <prop k="width" v="0.26"/>'
            qml += "        </layer>"
            qml += "      </symbol>"
        else:

            # attribute_quantile = quantile(edge_export_df_final[grep(1, match(names(edge_export_df_final), attribute))], probs=seq(0, 1, 1/5), na.rm=True, type=8)

            # Write more header
            qml += paste(
                '  <renderer-v2 attr="',
                attribute,
                '" symbollevels="1" type="graduatedSymbol">',
                sep="",
            )

            # Write ranges
            ranges = str()
            qml += "    <ranges>"
            for quant in range(no_quantile):
                ranges = append(
                    ranges,
                    paste(
                        '      <range symbol="',
                        (quant - 1),
                        '" lower="',
                        attribute_quantile[quant],
                        '" upper="',
                        attribute_quantile[(quant + 1)],
                        '" label="',
                        round(attribute_quantile[quant], 4),
                        " - ",
                        round(attribute_quantile[(quant + 1)], 4),
                        '">',
                        sep="",
                    ),
                )

        qml += ranges
        qml += "    </ranges>"

        # Write symbols
        qml += "    <symbols>"

        for quant in range(no_quantile):
            qml += paste(
                '      <symbol outputUnit="MM" alpha="1" type="line" name="',
                (quant - 1),
                '">',
                sep="",
            )
            qml += paste(
                '        <layer pass="',
                (quant - 1),
                '" class="SimpleLine" locked="0">',
                sep="",
            )
            qml += '          <prop k="capstyle" v="square"/>'
            qml += colortable[quant]
            qml += '          <prop k="customdash" v="5;2"/>'
            qml += '          <prop k="joinstyle" v="bevel"/>'
            qml += '          <prop k="offset" v="0"/>'
            qml += '          <prop k="penstyle" v="solid"/>'
            qml += '          <prop k="use_custom_dash" v="0"/>'
            qml += '          <prop k="width" v="0.26"/>'
            qml += "        </layer>"
            qml += "      </symbol>"

        # Write Footer
        qml += "    </symbols>"
        qml += "    <source-symbol>"
        qml += '      <symbol outputUnit="MM" alpha="1" type="line" name="0">'
        qml += '        <layer pass="0" class="SimpleLine" locked="0">'
        qml += '          <prop k="capstyle" v="square"/>'
        qml += '          <prop k="color" v="161,238,135,255"/>'
        qml += '          <prop k="customdash" v="5;2"/>'
        qml += '          <prop k="joinstyle" v="bevel"/>'
        qml += '          <prop k="offset" v="0"/>'
        qml += '          <prop k="penstyle" v="solid"/>'
        qml += '          <prop k="use_custom_dash" v="0"/>'
        qml += '          <prop k="width" v="0.26"/>'
        qml += "        </layer>"
        qml += "      </symbol>"
        qml += "    </source-symbol>"
        qml += '    <mode name="quantile"/>'
        qml += '    <rotation field=""/>'
        qml += '    <sizescale field=""/>'
        qml += "  </renderer-v2>"
        qml += "  <customproperties/>"
        qml += '  <displayfield>"' + attribute + '"</displayfield>'
        qml += "  <attributeactions/>"
        qml += "</qgis>"

        # Save qml-file
        qml_output = paste(
            qml_directory,
            paste(paste("edge_measures_", attribute, sep=""), "qml", sep="."),
            sep="/",
        )
        con_qml = file(qml_output, open="wt")
        write.table(
            qml,
            con_qml,
            append=False,
            quote=False,
            sep=" ",
            eol="\n",
            na="NA",
            dec=".",
            row_names=False,
            col_names=False,
        )
        close(con_qml)

    gscript.run_command(
        "g.copy", quiet=True, vector="{},{}".format(network_map, edge_output)
    )
    gscript.run_command(
        "g.copy", quiet=True, vector="{},{}".format(in_vertices, vertex_output)
    )

    # Use v.db.connect instead of v.db.join (much faster)

    gscript.run_command(
        "v.db.join",
        map=edge_output,
        column="cat",
        other_table=edge_output_tmp,
        other_column="con_id",
        quiet=True,
    )
    gscript.run_command(
        "v.db.join",
        map=vertex_output,
        column="cat",
        other_table=vertex_output_tmp,
        other_column="patch_id",
        quiet=True,
    )

    update_history = "{}\n{}".format(net_hist_str, os.environ["CMDLINE"])

    gscript.run_command(
        "v.support",
        flags="h",
        map=vertex_output,
        person=os.environ["USER"],
        cmdhist=update_history,
    )

    gscript.run_command(
        "v.support",
        flags="h",
        map=edge_output,
        person=os.environ["USER"],
        cmdhist=update_history,
    )


if __name__ == "__main__":
    options, flags = gscript.parser()
    atexit.register(cleanup)
    sys.exit(main())
