/*****************************************************************************
 *
 * MODULE:       r.pi.graph
 * AUTHOR(S):    Elshad Shirinov, Dr. Martin Wegmann
 *               Markus Metz (update to GRASS 7)
 * PURPOSE:      Graph Theory approach for connectivity analysis on patch level
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

int main(int argc, char *argv[])
{
    /* input */
    char *newname, *oldname;
    const char *oldmapset;
    char fullname[GNAME_MAX];

    /* in and out file pointers */
    int in_fd;
    int out_fd;

    /* parameters */
    int keyval;
    int nbr_count;
    int index;
    int neighborhood;
    DCELL distance;

    /* map_type and categories */
    RASTER_MAP_TYPE map_type;

    /* helpers */
    char *p;
    int nrows, ncols;
    int row, col, i;
    int n;
    f_neighborhood *build_graph;
    f_index *calc_index;
    int *curpos;
    DCELL *values;
    CELL *result;
    DCELL *d_res;
    CELL *clustermap;
    int *flagbuf;
    int fragcount;

    struct GModule *module;
    struct {
        struct Option *input, *output;
        struct Option *keyval, *distance;
        struct Option *neighborhood, *index;
    } parm;
    struct {
        struct Flag *adjacent, *quiet;
    } flag;

    G_gisinit(argv[0]);

    module = G_define_module();
    G_add_keyword(_("raster"));
    G_add_keyword(_("landscape structure analysis"));
    G_add_keyword(_("connectivity analysis"));
    module->description = _("Graph Theory for connectivity analysis.");

    parm.input = G_define_standard_option(G_OPT_R_INPUT);

    parm.output = G_define_option();
    parm.output->key = "output";
    parm.output->type = TYPE_STRING;
    parm.output->required = YES;
    parm.output->gisprompt = "new,cell,raster";
    parm.output->description = _("Name of the new raster file");

    parm.keyval = G_define_option();
    parm.keyval->key = "keyval";
    parm.keyval->type = TYPE_INTEGER;
    parm.keyval->required = YES;
    parm.keyval->description = _("Key value");

    parm.distance = G_define_option();
    parm.distance->key = "distance";
    parm.distance->type = TYPE_DOUBLE;
    parm.distance->required = YES;
    parm.distance->description =
        _("Bounding distance [0 for maximum distance]");

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

    /* get size */
    nrows = Rast_window_rows();
    ncols = Rast_window_cols();

    /* open cell files */
    in_fd = Rast_open_old(oldname, oldmapset);
    if (in_fd < 0)
        G_fatal_error(_("Unable to open raster map <%s>"), oldname);

    /* get map type */
    map_type = DCELL_TYPE; /* G_raster_map_type(oldname, oldmapset); */

    /* get key value */
    sscanf(parm.keyval->answer, "%d", &keyval);

    /* get distance */
    sscanf(parm.distance->answer, "%lf", &distance);
    if (distance == 0.0) {
        distance = MAX_DOUBLE;
    }

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

    /* get the cluster index */
    for (index = 0; (p = indices[index].name); index++)
        if ((strcmp(p, parm.index->answer) == 0))
            break;
    if (!p) {
        G_fatal_error("<%s=%s> unknown %s", parm.index->key, parm.index->answer,
                      parm.index->key);
    }

    /* get number of cell-neighbors */
    nbr_count = flag.adjacent->answer ? 8 : 4;

    /* allocate the cell buffers */
    cells = (Coords *)G_malloc(nrows * ncols * sizeof(Coords));
    fragments = (Coords **)G_malloc(nrows * ncols * sizeof(Coords *));
    fragments[0] = cells;
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
    fragcount = writeFragments(fragments, flagbuf, nrows, ncols, nbr_count);

    /* allocate distance matrix */
    distmatrix = (DCELL *)G_malloc(fragcount * fragcount * sizeof(DCELL));
    memset(distmatrix, 0, fragcount * fragcount * sizeof(DCELL));

    /* generate the distance matrix */
    get_dist_matrix(fragcount);

    /* G_message("Distance matrix:");
       for(row = 0; row < fragcount; row++) {
       for(col = 0; col < fragcount; col++) {
       fprintf(stderr, "%0.2f ", distmatrix[row * fragcount + col]);
       }
       fprintf(stderr, "\n");
       } */

    /* build adjacency matrix */
    adjmatrix = (int *)G_malloc(fragcount * fragcount * sizeof(int));
    memset(adjmatrix, 0, fragcount * fragcount * sizeof(int));

    build_graph = neighborhoods[neighborhood].method;
    build_graph(distance, fragcount);

    /* G_message("Adjacency matrix:");
       for(row = 0; row < fragcount; row++) {
       for(col = 0; col < fragcount; col++) {
       fprintf(stderr, "%d", adjmatrix[row * fragcount + col]);
       }
       fprintf(stderr, "\n");
       } */

    /* find clusters */
    patches = (int *)G_malloc(fragcount * sizeof(int));
    clusters = (int **)G_malloc((fragcount + 1) * sizeof(int *));

    FindClusters(fragcount);

    /*for(i = 0; i < clustercount; i++) {
       fprintf(stderr, "Cluster_%d:", i);
       for(curpos = clusters[i]; curpos < clusters[i + 1]; curpos++) {
       fprintf(stderr, " %d", *curpos);
       }
       fprintf(stderr, "\n");
       } */

    values = (DCELL *)G_malloc(clustercount * sizeof(DCELL));

    calc_index = indices[index].method;
    calc_index(values, fragcount);

    /*      fprintf(stderr, "Results:");
       for(i = 0; i < clustercount; i++) {
       fprintf(stderr, " %0.2f", values[i]);
       }
       fprintf(stderr, "\n"); */

    /* write output */
    G_message("Writing output...");

    /* ==================================
       ============  output  ============
       ================================== */

    /* open the new cellfile  */
    out_fd = Rast_open_new(newname, map_type);
    if (out_fd < 0)
        G_fatal_error(_("Cannot create raster map <%s>"), newname);

    /* allocate result row variable */
    d_res = Rast_allocate_d_buf();

    /* write values */
    for (row = 0; row < nrows; row++) {
        Rast_set_d_null_value(d_res, ncols);

        for (i = 0; i < clustercount; i++) {
            for (curpos = clusters[i]; curpos < clusters[i + 1]; curpos++) {
                Coords *cell;

                for (cell = fragments[*curpos]; cell < fragments[*curpos + 1];
                     cell++) {
                    if (cell->y == row) {
                        d_res[cell->x] = values[i];
                    }
                }
            }
        }

        Rast_put_d_row(out_fd, d_res);

        G_percent(row + 1, 2 * nrows, 1);
    }

    /* close output file */
    Rast_close(out_fd);

    /* ==================================
       ==========  cluster map  =========
       ================================== */

    /* open the new cellfile  */
    sprintf(fullname, "%s_clusters", newname);
    out_fd = Rast_open_new(fullname, CELL_TYPE);
    if (out_fd < 0)
        G_fatal_error(_("Cannot create raster map <%s>"), newname);

    /* allocate and initialize the clustermap */
    clustermap = (CELL *)G_malloc(nrows * ncols * sizeof(CELL));
    Rast_set_c_null_value(clustermap, nrows * ncols);

    /* for each cluster */
    for (i = 0; i < clustercount; i++) {
        /* for each patch in the cluster */
        int *this;

        for (this = clusters[i]; this < clusters[i + 1]; this ++) {
            /* for each cell in the patch */
            Coords *cell;
            int *other;

            for (cell = fragments[*this]; cell < fragments[*this + 1]; cell++) {
                clustermap[cell->y * ncols + cell->x] = i;
            }

            /* for each patch in the cluster */

            for (other = clusters[i]; other < clusters[i + 1]; other++) {
                if (*other != *this && adjmatrix[*this * fragcount + *other]) {
                    Coords np1, np2;

                    nearest_points(fragments, *this, *other, &np1, &np2);

                    draw_line(clustermap, -1, np1.x, np1.y, np2.x, np2.y, ncols,
                              nrows, 1);
                }
            }
        }
    }

    /* write output */
    for (row = 0; row < nrows; row++) {
        Rast_put_c_row(out_fd, clustermap + row * ncols);

        G_percent(nrows + row + 1, 2 * nrows, 1);
    }

    /* G_free(clustermap); */

    /* close output file */
    Rast_close(out_fd);

    /* ==================================
       ==========  convex hull  =========
       ================================== */

    /* open the new cellfile  */
    sprintf(fullname, "%s_hull", newname);
    out_fd = Rast_open_new(fullname, CELL_TYPE);
    if (out_fd < 0)
        G_fatal_error(_("Cannot create raster map <%s>"), newname);

    /* clear the clustermap */
    Rast_set_c_null_value(clustermap, nrows * ncols);

    /* calculate the convex hull */
    convex_hull(clustermap, nrows, ncols);

    /* write output */
    for (row = 0; row < nrows; row++) {
        Rast_put_c_row(out_fd, clustermap + row * ncols);

        G_percent(nrows + row + 1, 2 * nrows, 1);
    }

    G_free(clustermap);

    /* close output file */
    Rast_close(out_fd);

    /* =====================
       ==== free memory ====
       ===================== */
    G_free(values);
    G_free(patches);
    G_free(clusters);
    G_free(cells);
    G_free(fragments);
    G_free(flagbuf);
    G_free(result);
    G_free(d_res);

    G_free(distmatrix);
    G_free(adjmatrix);

    exit(EXIT_SUCCESS);
}
