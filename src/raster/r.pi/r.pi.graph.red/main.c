/*****************************************************************************
 *
 * MODULE:       r.pi.graph.red
 * AUTHOR(S):    Elshad Shirinov, Dr. Martin Wegmann
 *               Markus Metz (update to GRASS 7)
 * PURPOSE:      Graph Theory approach for connectivity analysis on patch
 *               level - decreasing distance threshold option
 *
 * COPYRIGHT:    (C) 2009-2011,2017 by the GRASS Development Team
 *
 *               This program is free software under the GNU General Public
 *               License (>=v2). Read the file COPYING that comes with GRASS
 *               for details.
 *
 *****************************************************************************/

#define MAIN

#include "local_proto.h"

struct neighborhood {
    f_neighborhood *method; /* routine to build adjacency matrix */
    char *name;             /* method name */
    char *text;             /* menu display - full description */
};

struct index {
    f_index *method; /* routine to calculate cluster index */
    char *name;      /* method name */
    char *text;      /* menu display - full description */
};

struct statmethod {
    f_statmethod *method; /* routine to compute statistical value */
    char *name;           /* method name */
    char *suffix;         /* abbreviation to be displayed in the output */
    char *text;           /* menu display - full description */
};

static struct neighborhood neighborhoods[] = {
    {f_nearest_neighbor, "nearest_neighbor",
     "patches are connected with their nearest neighbors"},
    {f_relative_neighbor, "relative_neighbor",
     "two patches are connected, if no other patch lies in the central lens "
     "between them"},
    {f_gabriel, "gabriel",
     "two patches are connected, if no other patch lies in the circle on them"},
    {f_spanning_tree, "spanning_tree",
     "two patches are connected, if they are neighbors in the minimum spanning "
     "tree"},
    {0, 0, 0}};

static struct index indices[] = {
    {f_connectance_index, "connectance_index", "connectance index"},
    {f_gyration_radius, "gyration_radius", "radius of gyration"},
    {f_cohesion_index, "cohesion_index", "cohesion index"},
    {f_percent_patches, "percent_patches",
     "percentage of the patches in the cluster"},
    {f_percent_area, "percent_area",
     "percentage of the patch area in the cluster"},
    {f_number_patches, "number_patches", "number of patches in the cluster"},
    {f_number_links, "number_links", "number of links in the cluster"},
    {f_mean_patch_size, "mean_patch_size", "mean patch size in the cluster"},
    {f_largest_patch_size, "largest_patch_size",
     "largest patch size in the cluster"},
    {f_largest_patch_diameter, "largest_patch_diameter",
     "largest patch diameter in the cluster"},
    {f_graph_diameter_max, "graph_diameter",
     "longest minimal path in the cluster"},
    {0, 0, 0}};

static struct statmethod statmethods[] = {
    {average, "average", "avg", "average of the values"},
    {median, "median", "med", "median of the values"},
    {variance, "variance", "var", "variance of the values"},
    {std_deviat, "std_deviat", "std", "standard deviation of the values"},
    {min, "min", "min", "minimum of the values"},
    {max, "max", "max", "maximum of the values"},
    {0, 0, 0, 0}};

int main(int argc, char *argv[])
{
    /* input */
    char *newname, *oldname;
    const char *oldmapset;

    /* in and out file pointers */
    int in_fd;
    FILE *out_fp; /* ASCII - output */

    /* parameters */
    int keyval;
    int nbr_count;
    int index[GNAME_MAX];
    int index_count;
    int neighborhood;
    int statmethod;
    DCELL distance;
    DCELL step;

    /* helpers */
    char *p;
    int nrows, ncols;
    int row, col, i;
    int n;
    f_neighborhood *build_graph;
    f_index *calc_index;
    f_statmethod *calc_stat;
    CELL *result;
    Coords *cells;
    Patch *fragments;
    int *flagbuf;
    int fragcount;
    DCELL *distmatrix;
    int *adjmatrix;
    int *patches;
    Cluster *clusters;
    int val_rows;
    DCELL *values;
    int *cluster_counts;
    DCELL temp_d;

    struct GModule *module;
    struct {
        struct Option *input, *output;
        struct Option *keyval, *distance, *step;
        struct Option *neighborhood, *index, *stats;
    } parm;
    struct {
        struct Flag *adjacent;
    } flag;

    G_gisinit(argv[0]);

    module = G_define_module();
    G_add_keyword(_("raster"));
    G_add_keyword(_("landscape structure analysis"));
    G_add_keyword(_("connectivity analysis"));
    module->description =
        _("Graph Theory - decreasing distance threshold option.");

    parm.input = G_define_standard_option(G_OPT_R_INPUT);

    parm.output = G_define_option();
    parm.output->key = "output";
    parm.output->type = TYPE_STRING;
    parm.output->required = YES;
    parm.output->gisprompt = "new_file,file,output";
    parm.output->description = _("Name of the output ASCII file");

    parm.keyval = G_define_option();
    parm.keyval->key = "keyval";
    parm.keyval->type = TYPE_INTEGER;
    parm.keyval->required = YES;
    parm.keyval->description = _("Key value");

    parm.distance = G_define_option();
    parm.distance->key = "distance";
    parm.distance->type = TYPE_DOUBLE;
    parm.distance->required = YES;
    parm.distance->description = _("Distance at which to begin decreasing");

    parm.step = G_define_option();
    parm.step->key = "step";
    parm.step->type = TYPE_DOUBLE;
    parm.step->required = YES;
    parm.step->description = _("Step to decrease the distance");

    parm.neighborhood = G_define_option();
    parm.neighborhood->key = "neighborhood";
    parm.neighborhood->type = TYPE_STRING;
    parm.neighborhood->required = YES;
    p = G_malloc(1024);
    for (n = 0; neighborhoods[n].name; n++) {
        if (n)
            strcat(p, ",");
        else
            *p = 0;
        strcat(p, neighborhoods[n].name);
    }
    parm.neighborhood->options = p;
    parm.neighborhood->description = _("Neighborhood definition");

    parm.index = G_define_option();
    parm.index->key = "index";
    parm.index->type = TYPE_STRING;
    parm.index->required = YES;
    parm.index->multiple = YES;
    p = G_malloc(1024);
    for (n = 0; indices[n].name; n++) {
        if (n)
            strcat(p, ",");
        else
            *p = 0;
        strcat(p, indices[n].name);
    }
    parm.index->options = p;
    parm.index->description = _("Cluster index");

    parm.stats = G_define_option();
    parm.stats->key = "stats";
    parm.stats->type = TYPE_STRING;
    parm.stats->required = YES;
    p = G_malloc(1024);
    for (n = 0; statmethods[n].name; n++) {
        if (n)
            strcat(p, ",");
        else
            *p = 0;
        strcat(p, statmethods[n].name);
    }
    parm.stats->options = p;
    parm.stats->description = _("Statistical method to perform on the values");

    flag.adjacent = G_define_flag();
    flag.adjacent->key = 'a';
    flag.adjacent->description =
        _("Set for 8 cell-neighbors. 4 cell-neighbors are default");

    if (G_parser(argc, argv))
        exit(EXIT_FAILURE);

    /* get names of input files */
    oldname = parm.input->answer;

    /* test input files existance */
    oldmapset = G_find_raster2(oldname, "");
    if (oldmapset == NULL)
        G_fatal_error(_("Raster map <%s> not found"), oldname);

    /* check if the new file name is correct */
    newname = parm.output->answer;
    if (G_legal_filename(newname) < 0)
        G_fatal_error(_("<%s> is an illegal file name"), newname);

    nrows = Rast_window_rows();
    ncols = Rast_window_cols();

    G_message("rows = %d, cols = %d", nrows, ncols);

    /* open cell files */
    in_fd = Rast_open_old(oldname, oldmapset);
    if (in_fd < 0)
        G_fatal_error(_("Unable to open raster map <%s>"), oldname);

    /* get key value */
    sscanf(parm.keyval->answer, "%d", &keyval);

    /* get distance */
    sscanf(parm.distance->answer, "%lf", &distance);

    /* get step */
    sscanf(parm.step->answer, "%lf", &step);

    /* get neighborhood definition */
    for (neighborhood = 0; (p = neighborhoods[neighborhood].name);
         neighborhood++) {
        if ((strcmp(p, parm.neighborhood->answer) == 0))
            break;
    }
    if (!p) {
        G_fatal_error("<%s=%s> unknown %s", parm.neighborhood->key,
                      parm.neighborhood->answer, parm.neighborhood->key);
        exit(EXIT_FAILURE);
    }

    /* get the cluster indices */
    for (index_count = 0; parm.index->answers[index_count]; index_count++) {
        int idx;

        for (idx = 0; (p = indices[idx].name); idx++) {
            if ((strcmp(p, parm.index->answers[index_count]) == 0)) {
                break;
            }
        }

        if (!p) {
            G_fatal_error("<%s=%s> unknown %s", parm.index->key,
                          parm.index->answers[index_count], parm.index->key);
            exit(EXIT_FAILURE);
        }

        index[index_count] = idx;
    }

    /* get the statmethod */
    for (statmethod = 0; (p = statmethods[statmethod].name); statmethod++)
        if ((strcmp(p, parm.stats->answer) == 0))
            break;
    if (!p) {
        G_fatal_error("<%s=%s> unknown %s", parm.stats->key, parm.stats->answer,
                      parm.stats->key);
    }
    calc_stat = statmethods[statmethod].method;

    /* get number of cell-neighbors */
    nbr_count = flag.adjacent->answer ? 8 : 4;

    /* allocate the cell buffers */
    cells = (Coords *)G_malloc(nrows * ncols * sizeof(Coords));
    fragments = (Patch *)G_malloc(nrows * ncols * sizeof(Patch));

    fragments[0].first_cell = cells;
    flagbuf = (int *)G_malloc(nrows * ncols * sizeof(int));

    result = Rast_allocate_c_buf();

    G_message("Loading patches...");

    /* read map */
    for (row = 0; row < nrows; row++) {
        Rast_get_c_row(in_fd, result, row);
        for (col = 0; col < ncols; col++) {
            if (result[col] == keyval)
                flagbuf[row * ncols + col] = 1;
        }

        G_percent(row + 1, nrows, 1);
    }

    /* close cell file */
    Rast_close(in_fd);

    /*G_message("map");
       for(row = 0; row < nrows; row++) {
       for(col = 0; col< ncols; col++) {
       fprintf(stderr, "%d", flagbuf[row * ncols + col]);
       }
       fprintf(stderr, "\n");
       } */

    /* find fragments */
    fragcount =
        writeFragments_local(fragments, flagbuf, nrows, ncols, nbr_count);

    /* allocate distance matrix */
    distmatrix = (DCELL *)G_malloc(fragcount * fragcount * sizeof(DCELL));
    memset(distmatrix, 0, fragcount * fragcount * sizeof(DCELL));

    /* generate the distance matrix */
    get_dist_matrix(distmatrix, fragments, fragcount);

    /* allocate adjacency matrix */
    adjmatrix = (int *)G_malloc(fragcount * fragcount * sizeof(int));

    /* allocate clusters */
    patches = (int *)G_malloc(fragcount * sizeof(int));
    clusters = (Cluster *)G_malloc((fragcount) * sizeof(Cluster));

    clusters[0].first_patch = patches;

    /* set build_graph routine */
    build_graph = neighborhoods[neighborhood].method;

    /*G_message("Distance matrix:");
       for(row = 0; row < fragcount; row++) {
       for(col = 0; col < fragcount; col++) {
       fprintf(stderr, "%0.2f ", distmatrix[row * fragcount + col]);
       }
       fprintf(stderr, "\n");
       } */

    val_rows = (int)(distance / step) + 1;

    /* values = (clustercount, cluster1_index1, cluster2_index1, ...), () */
    values =
        (DCELL *)G_malloc(val_rows * index_count * fragcount * sizeof(DCELL));

    cluster_counts = (int *)G_malloc(val_rows * sizeof(int));

    /*      calc_index = indices[index].method;
       calc_index(ref_values, clusters, clustercount, adjmatrix, fragments,
       fragcount, distmatrix);

       fprintf(stderr, "Reference values:");
       for(i = 0; i < clustercount; i++) {
       fprintf(stderr, " %0.2f", ref_values[i]);
       }
       fprintf(stderr, "\n"); */

    /* perform distance reduction analysis */
    /* for each patch */
    G_message("Performing distance reduction...");
    temp_d = distance;

    for (i = 0; i < val_rows; i++, temp_d -= step) {
        int idx;
        DCELL *vals;

        /* build graph with current distance */
        memset(adjmatrix, 0, fragcount * fragcount * sizeof(int));
        build_graph(adjmatrix, distmatrix, fragcount, temp_d);

        /*fprintf(stderr, "\nAdjacency matrix with deleted patch %d\n", i);
           for(p1 = 0; p1 < temp_fragcount; p1++) {
           for(p2 = 0; p2 < temp_fragcount; p2++) {
           fprintf(stderr, "%d ", temp_adjm[p1 * temp_fragcount + p2]);
           }
           fprintf(stderr, "\n");
           } */

        /* find clusters */
        cluster_counts[i] = find_clusters(clusters, adjmatrix, fragcount);

        /* calculate and save indices */
        vals = &(values[i * index_count * fragcount]);

        for (idx = 0; idx < index_count; idx++, vals += fragcount) {
            int cur_index = index[idx];

            calc_index = indices[cur_index].method;
            calc_index(vals, clusters, cluster_counts[i], adjmatrix, fragments,
                       fragcount, distmatrix);
        }

        G_percent(i + 1, fragcount, 1);
    }

    /* test output */
    /*fprintf(stderr, "Values:");
    for (row = 0; row < val_rows; row++) {
        fprintf(stderr, "\n");
        fprintf(stderr, "Clusters: %d --- ", cluster_counts[row]);
        for (i = 0; i < index_count * fragcount; i++) {
            fprintf(stderr, "%0.2f ",
                    values[row * index_count * fragcount + i]);
        }
    }
    fprintf(stderr, "\n"); */

    /* write output */
    G_message("Writing output...");

    /* ==================================
       ============  output  ============
       ================================== */

    /* open ASCII-file or use stdout */
    if (strcmp(parm.output->answer, "-") != 0) {
        if (!(out_fp = fopen(parm.output->answer, "w"))) {
            G_fatal_error(_("Error creating file <%s>"), parm.output->answer);
        }
    }
    else {
        out_fp = stdout;
    }

    /* write header */
    fprintf(out_fp, "distance cluster_count");
    for (i = 0; i < index_count; i++) {
        fprintf(out_fp, " %s", indices[index[i]].name);
    }
    fprintf(out_fp, "\n");

    /* write values */
    temp_d = distance;
    for (i = 0; i < val_rows; i++, temp_d -= step) {
        int idx;
        DCELL *vals;

        fprintf(out_fp, "%f %d", temp_d, cluster_counts[i]);

        vals = &(values[i * index_count * fragcount]);

        for (idx = 0; idx < index_count; idx++, vals += fragcount) {
            DCELL val = calc_stat(vals, cluster_counts[i]);

            fprintf(out_fp, " %f", val);
        }

        fprintf(out_fp, "\n");
    }

    /* close output file */
    if (strcmp(parm.output->answer, "-") != 0) {
        fclose(out_fp);
    }

    /* =============================
       =======  free memory  =======
       ============================= */
    G_free(cluster_counts);
    G_free(values);
    G_free(patches);
    G_free(clusters);
    G_free(cells);
    G_free(fragments);
    G_free(flagbuf);
    G_free(result);

    G_free(distmatrix);
    G_free(adjmatrix);

    exit(EXIT_SUCCESS);
}
