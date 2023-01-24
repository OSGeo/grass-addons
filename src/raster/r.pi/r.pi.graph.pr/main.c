/*****************************************************************************
 *
 * MODULE:       r.pi.graph.pr
 * AUTHOR(S):    Elshad Shirinov, Dr. Martin Wegmann
 *               Markus Metz (update to GRASS 7)
 * PURPOSE:      Graph Theory approach for connectivity analysis on patch
 *               level - iterative patch removal option (patch relevance)
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

int recur_test(int, int, int);

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
    CELL *result;
    DCELL *d_res;
    CELL *clustermap;
    Coords *cells;
    Patch *fragments;
    int *flagbuf;
    int fragcount;
    DCELL *distmatrix;
    int *adjmatrix;
    int *patches;
    Cluster *clusters;
    int clustercount;
    DCELL *values, *ref_values, *temp_values;
    int *splitter_patches;

    struct GModule *module;
    struct {
        struct Option *input, *output;
        struct Option *keyval, *distance;
        struct Option *neighborhood, *index;
    } parm;
    struct {
        struct Flag *adjacent, *percent;
    } flag;

    G_gisinit(argv[0]);

    module = G_define_module();
    G_add_keyword(_("raster"));
    module->description =
        _("Graph Theory - iterative removal (patch relevance analysis).");

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

    flag.percent = G_define_flag();
    flag.percent->key = 'p';
    flag.percent->description = _("Defines, if the output should be a "
                                  "percentual of the cluster index values.");

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

    /*G_message("Distance matrix:");
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
    build_graph(adjmatrix, distmatrix, fragcount, distance);

    /*G_message("Adjacency matrix:");
       for(row = 0; row < fragcount; row++) {
       for(col = 0; col < fragcount; col++) {
       fprintf(stderr, "%d", adjmatrix[row * fragcount + col]);
       }
       fprintf(stderr, "\n");
       } */

    /* find clusters */
    patches = (int *)G_malloc(fragcount * sizeof(int));
    clusters = (Cluster *)G_malloc((fragcount) * sizeof(Cluster));

    clusters[0].first_patch = patches;

    clustercount = find_clusters(clusters, adjmatrix, fragcount);

    /*for(i = 0; i < clustercount; i++) {
       fprintf(stderr, "Cluster_%d:", i);
       for(curpos = clusters[i]; curpos < clusters[i + 1]; curpos++) {
       fprintf(stderr, " %d", *curpos);
       }
       fprintf(stderr, "\n");
       } */

    values = (DCELL *)G_malloc(fragcount * sizeof(DCELL));

    ref_values = (DCELL *)G_malloc(clustercount * sizeof(DCELL));
    temp_values = (DCELL *)G_malloc(clustercount * sizeof(DCELL));

    calc_index = indices[index].method;
    calc_index(ref_values, clusters, clustercount, adjmatrix, fragments,
               fragcount, distmatrix);

    /*fprintf(stderr, "Reference values:");
       for(i = 0; i < clustercount; i++) {
       fprintf(stderr, " %0.2f", ref_values[i]);
       }
       fprintf(stderr, "\n"); */

    /* perform iterative deletion analysis */
    splitter_patches = (int *)G_malloc(fragcount * sizeof(int));

    memset(splitter_patches, 0, fragcount * sizeof(int));

    /* for each patch */
    G_message("Performing iterative deletion...");
    for (i = 0; i < fragcount; i++) {
        DCELL *temp_distm;
        int temp_fragcount = fragcount - 1;
        int p1, p2;
        int tp1 = 0;
        int *temp_adjm;
        int *temp_p;
        Cluster *temp_c;
        int temp_cc;
        int c;
        int focal_cluster;

        /* delete i-th patch... */

        /* from fragment list */
        Patch *temp_frags = (Patch *)G_malloc(temp_fragcount * sizeof(Patch));

        memcpy(temp_frags, fragments, i * sizeof(Patch));
        memcpy(temp_frags + i, fragments + i + 1,
               (fragcount - i - 1) * sizeof(Patch));

        /* from distance matrix */
        temp_distm =
            (DCELL *)G_malloc(temp_fragcount * temp_fragcount * sizeof(DCELL));
        memset(temp_distm, 0, temp_fragcount * temp_fragcount * sizeof(DCELL));

        for (p1 = 0; p1 < fragcount; p1++) {
            if (p1 != i) {
                int tp2 = 0;

                for (p2 = 0; p2 < fragcount; p2++) {
                    if (p2 != i) {
                        DCELL dist = distmatrix[p1 * fragcount + p2];

                        temp_distm[tp1 * temp_fragcount + tp2] = dist;

                        tp2++;
                    }
                    else {
                        continue;
                    }
                }

                tp1++;
            }
            else {
                continue;
            }
        }

        /* build graph and see if the cluster is splitted */
        temp_adjm = (int *)G_malloc(fragcount * fragcount * sizeof(int));

        memset(temp_adjm, 0, fragcount * fragcount * sizeof(int));

        build_graph(temp_adjm, temp_distm, temp_fragcount, distance);

        /*fprintf(stderr, "\nAdjacency matrix with deleted patch %d\n", i);
           for(p1 = 0; p1 < temp_fragcount; p1++) {
           for(p2 = 0; p2 < temp_fragcount; p2++) {
           fprintf(stderr, "%d ", temp_adjm[p1 * temp_fragcount + p2]);
           }
           fprintf(stderr, "\n");
           } */

        temp_p = (int *)G_malloc(fragcount * sizeof(int));
        temp_c = (Cluster *)G_malloc(fragcount * sizeof(Cluster));

        temp_c[0].first_patch = temp_p;

        temp_cc = find_clusters(temp_c, temp_adjm, temp_fragcount);

        /* G_message("Clustercount = %d", temp_cc); */

        /* if cluster count changed mark patch as splitter */
        if (temp_cc > clustercount) {
            splitter_patches[i] = 1;
        }

        /* now compare the cluster index with and without patch i */
        /* delete i-th patch ... */

        /* from adjacency matrix */
        memcpy(temp_adjm, adjmatrix, fragcount * fragcount * sizeof(int));

        for (index = 0; index < fragcount; index++) {
            temp_adjm[index * fragcount + i] = 0;
            temp_adjm[i * fragcount + index] = 0;
        }

        /*fprintf(stderr, "\nAdjacency matrix with deleted patch %d\n", i);
           for(p1 = 0; p1 < fragcount; p1++) {
           for(p2 = 0; p2 < fragcount; p2++) {
           fprintf(stderr, "%d ", temp_adjm[p1 * fragcount + p2]);
           }
           fprintf(stderr, "\n");
           } */

        /* from cluster list */

        /* for each cluster */
        focal_cluster = -1;
        curpos = temp_p;

        for (c = 0; c < clustercount; c++) {
            int *patch;

            temp_c[c].first_patch = curpos;

            /* for each patch in the cluster */

            for (patch = clusters[c].first_patch;
                 patch < clusters[c].first_patch + clusters[c].count; patch++) {
                /* if patch is deleted */
                if (*patch == i) {
                    *curpos = clusters[c].first_patch[clusters[c].count - 1];
                    focal_cluster = c;
                }
                else {
                    *curpos = *patch;
                }
                curpos++;
            }

            temp_c[c].count = clusters[c].count;
            if (focal_cluster == c) {
                temp_c[c].count--;
            }
        }

        calc_index(temp_values, temp_c, clustercount, temp_adjm, fragments,
                   fragcount, distmatrix);

        /*fprintf(stderr, "Values without patch %d:", i);
           for(c = 0; c < clustercount; c++) {
           fprintf(stderr, " %0.2f", temp_values[c]);
           }
           fprintf(stderr, "\n"); */

        values[i] = temp_values[focal_cluster] - ref_values[focal_cluster];

        if (flag.percent->answer) {
            values[i] *= 100.0 / ref_values[focal_cluster];
        }

        G_percent(i + 1, fragcount, 1);

        G_free(temp_frags);
        G_free(temp_distm);
        G_free(temp_adjm);
        G_free(temp_p);
        G_free(temp_c);
    }

    G_free(ref_values);
    G_free(temp_values);

    /* test output */
    /*fprintf(stderr, "Splitter patches:");
       for(i = 0; i < fragcount; i++) {
       fprintf(stderr, " %d", splitter_patches[i]);
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
        int patch_index;

        Rast_set_d_null_value(d_res, ncols);

        for (patch_index = 0; patch_index < fragcount; patch_index++) {
            int cell_index;

            for (cell_index = 0; cell_index < fragments[patch_index].count;
                 cell_index++) {
                Coords *cell = fragments[patch_index].first_cell + cell_index;

                if (cell->y == row) {
                    d_res[cell->x] = values[patch_index];
                }
            }
        }

        Rast_put_d_row(out_fd, d_res);

        G_percent(row + 1, 2 * nrows, 1);
    }

    /* close output file */
    Rast_close(out_fd);

    /* write splitter patch map */
    /* open the new cellfile  */
    sprintf(fullname, "%s_split", newname);
    out_fd = Rast_open_new(fullname, CELL_TYPE);
    if (out_fd < 0)
        G_fatal_error(_("Cannot create raster map <%s>"), fullname);

    /* write values */
    for (row = 0; row < nrows; row++) {
        Rast_set_d_null_value(d_res, ncols);

        for (i = 0; i < clustercount; i++) {
            for (curpos = clusters[i].first_patch;
                 curpos < clusters[i].first_patch + clusters[i].count;
                 curpos++) {
                int cell_index;

                for (cell_index = 0; cell_index < fragments[*curpos].count;
                     cell_index++) {
                    Coords *cell = fragments[*curpos].first_cell + cell_index;

                    if (cell->y == row) {
                        d_res[cell->x] =
                            splitter_patches[*curpos] ? -(i + 1) : i + 1;
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

    /* open the new cellfile */
    sprintf(fullname, "%s_clusters", newname);
    out_fd = Rast_open_new(fullname, CELL_TYPE);
    if (out_fd < 0)
        G_fatal_error(_("Cannot create raster map <%s>"), fullname);

    /* allocate and initialize the clustermap */
    clustermap = (CELL *)G_malloc(nrows * ncols * sizeof(CELL));
    Rast_set_c_null_value(clustermap, nrows * ncols);

    /* for each cluster */
    for (i = 0; i < clustercount; i++) {
        /* for each patch in the cluster */
        int *this;

        for (this = clusters[i].first_patch;
             this < clusters[i].first_patch + clusters[i].count; this ++) {
            /* for each cell in the patch */
            int cell_index;
            int *other;

            for (cell_index = 0; cell_index < fragments[*this].count;
                 cell_index++) {
                Coords *cell = fragments[*this].first_cell + cell_index;

                clustermap[cell->y * ncols + cell->x] = i;
            }

            /* for each patch in the cluster */
            for (other = this + 1;
                 other < clusters[i].first_patch + clusters[i].count; other++) {
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

    G_free(clustermap);

    /* close output file */
    Rast_close(out_fd);

    /* =============================
       =======  free memory  =======
       ============================= */
    G_free(values);
    G_free(patches);
    G_free(clusters);
    G_free(cells);
    G_free(fragments);
    G_free(flagbuf);
    G_free(result);
    G_free(d_res);
    G_free(splitter_patches);

    G_free(distmatrix);
    G_free(adjmatrix);

    exit(EXIT_SUCCESS);
}
