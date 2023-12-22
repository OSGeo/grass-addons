/*****************************************************************************
 *
 * MODULE:       r.pi.graph.dec
 * AUTHOR(S):    Elshad Shirinov, Dr. Martin Wegmann
 *               Markus Metz (update to GRASS 7)
 * PURPOSE:      Graph Theory approach for connectivity analysis on patch
 *               level - successive removal of patches based on defined criteria
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

struct choice {
    f_choice *method; /* routine to determine the next patch to delete */
    char *name;       /* method name */
    char *text;       /* menu display - full description */
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

static struct choice choices[] = {
    {f_smallest_first, "smallest_first", "smallest patch is deleted first"},
    {f_biggest_first, "biggest_first", "biggest patch is deleted first"},
    {f_random, "random", "a random patch is deleted"},
    {f_link_min, "link_min", "the patch with the least links is deleted first"},
    {f_link_max, "link_max", "the patch with the most links is deleted first"},
    {0, 0, 0}};

int main(int argc, char *argv[])
{
    /* input */
    char *oldname, *newname, *idname;
    const char *oldmapset;
    char fullname[GNAME_MAX];

    /* in and out file pointers */
    int in_fd;
    int out_fd;
    FILE *out_fp; /* ASCII - output */

    /* parameters */
    int keyval;
    int nbr_count;
    int index;
    int neighborhood;
    int choice;
    DCELL distance;

    /* helpers */
    char *p;
    int nrows, ncols;
    int row, col, i;
    int n;
    f_neighborhood *build_graph;
    f_index *calc_index;
    f_choice *choose_patch;
    CELL *result;
    DCELL *d_res;
    CELL *clustermap;
    int seed;
    int *flagbuf;
    int fragcount;
    DCELL *distmatrix;
    int *adjmatrix;
    int *patches;
    int clustercount;
    DCELL *values, *cur_values;
    int *patch_notes;
    int *cluster_notes;
    int cur_pos;
    Cluster *clusters;
    Coords *cells;
    Patch *fragments;

    struct GModule *module;
    struct {
        struct Option *input, *output, *id;
        struct Option *keyval, *distance;
        struct Option *neighborhood, *index;
        struct Option *choice, *seed;
    } parm;
    struct {
        struct Flag *adjacent, *landscape;
    } flag;

    G_gisinit(argv[0]);

    module = G_define_module();
    G_add_keyword(_("raster"));
    G_add_keyword(_("landscape structure analysis"));
    G_add_keyword(_("connectivity analysis"));
    module->description =
        _("Graph Theory - successive criteria-based deletion of patches.");

    parm.input = G_define_standard_option(G_OPT_R_INPUT);

    parm.id = G_define_option();
    parm.id->key = "id";
    parm.id->type = TYPE_STRING;
    parm.id->required = NO;
    parm.id->gisprompt = "new,cell,raster";
    parm.id->description = _("Base name for the ID raster files");

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

    parm.choice = G_define_option();
    parm.choice->key = "choice";
    parm.choice->type = TYPE_STRING;
    parm.choice->required = YES;
    p = G_malloc(1024);
    for (n = 0; choices[n].name; n++) {
        if (n)
            strcat(p, ",");
        else
            *p = 0;
        strcat(p, choices[n].name);
    }
    parm.choice->options = p;
    parm.choice->description = _("Cluster index");

    parm.seed = G_define_option();
    parm.seed->key = "seed";
    parm.seed->type = TYPE_INTEGER;
    parm.seed->required = NO;
    parm.seed->description = _("Seed for the random number generation");

    flag.adjacent = G_define_flag();
    flag.adjacent->key = 'a';
    flag.adjacent->description =
        _("Set for 8 cell-neighbors. 4 cell-neighbors are default");

    flag.landscape = G_define_flag();
    flag.landscape->key = 'l';
    flag.landscape->description = _("Set to perform deletion for the whole "
                                    "landscape rather than cluster-wise");

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

    /* check if the id raster file name is correct */
    idname = parm.id->answer;
    if (G_legal_filename(idname) < 0)
        G_fatal_error(_("<%s> is an illegal file name"), idname);

    nrows = Rast_window_rows();
    ncols = Rast_window_cols();

    G_debug(1, "rows = %d, cols = %d", nrows, ncols);

    /* open cell files */
    in_fd = Rast_open_old(oldname, oldmapset);
    if (in_fd < 0)
        G_fatal_error(_("Unable to open raster map <%s>"), oldname);

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

    /* get the choice method */
    for (choice = 0; (p = choices[choice].name); choice++)
        if ((strcmp(p, parm.choice->answer) == 0))
            break;
    if (!p) {
        G_fatal_error("<%s=%s> unknown %s", parm.choice->key,
                      parm.choice->answer, parm.choice->key);
    }

    /* get number of cell-neighbors */
    nbr_count = flag.adjacent->answer ? 8 : 4;

    /* set random seed */
    seed = time(NULL);

    if (parm.seed->answer) {
        sscanf(parm.seed->answer, "%d", &seed);
    }
    srand(seed);

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

    /* values: Before Deletion(cluster1, cluster2, ...), After First
     * Deletion(...), After Second Deletion(...), ... */
    values = (DCELL *)G_malloc((fragcount + 1) * clustercount * sizeof(DCELL));
    patch_notes = (int *)G_malloc(fragcount * sizeof(int));
    cluster_notes = (int *)G_malloc(fragcount * sizeof(int));

    calc_index = indices[index].method;
    choose_patch = choices[choice].method;

    /* write id raster maps */

    if (parm.id->answer) {
        /* ==================================
           ==========  cluster map  =========
           ================================== */

        /* open the new cellfile */
        sprintf(fullname, "%s_clusters", idname);
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
                     other < clusters[i].first_patch + clusters[i].count;
                     other++) {
                    if (*other != *this &&
                        adjmatrix[*this * fragcount + *other]) {
                        Coords np1, np2;

                        nearest_points(fragments, *this, *other, &np1, &np2);

                        draw_line(clustermap, -1, np1.x, np1.y, np2.x, np2.y,
                                  ncols, nrows, 1);
                    }
                }
            }
        }

        /* write output */
        for (row = 0; row < nrows; row++) {
            Rast_put_c_row(out_fd, clustermap + row * ncols);
        }

        G_free(clustermap);

        /* close output file */
        Rast_close(out_fd);

        /* ==================================
           ============  id raster  ============
           ================================== */

        /* allocate result row variable */
        d_res = Rast_allocate_d_buf();

        /* open new cellfile  */
        sprintf(fullname, "%s_id", idname);
        out_fd = Rast_open_new(fullname, CELL_TYPE);
        if (out_fd < 0)
            G_fatal_error(_("Cannot create raster map <%s>"), fullname);

        /* write the output file */
        for (row = 0; row < nrows; row++) {
            int patch_index;

            Rast_set_d_null_value(d_res, ncols);

            for (patch_index = 0; patch_index < fragcount; patch_index++) {
                int cell_index;

                for (cell_index = 0; cell_index < fragments[patch_index].count;
                     cell_index++) {
                    Coords *cell =
                        fragments[patch_index].first_cell + cell_index;
                    if (cell->y == row) {
                        d_res[cell->x] = patch_index;
                    }
                }
            }

            Rast_put_d_row(out_fd, d_res);
        }

        /* free result row */
        G_free(d_res);

        /* close output */
        Rast_close(out_fd);
    }

    /* calculate indices once before deletion */
    calc_index(values, clusters, clustercount, adjmatrix, fragments, fragcount,
               distmatrix);

    /*fprintf(stderr, "Values:");
       for(i = 0; i < clustercount; i++) {
       fprintf(stderr, " %0.2f", values[i]);
       }
       fprintf(stderr, "\n"); */

    G_message("Performing iterative deletion...");

    cur_values = values + clustercount;
    cur_pos = 0;

    if (flag.landscape->answer) { /* landscape wide deletion */
        /* for each patch */
        for (i = 0; i < fragcount; i++) {
            /* find next patch to delete */
            int patch = choose_patch(-1, clusters, clustercount, adjmatrix,
                                     fragments, fragcount, distmatrix);

            /* find the appropriate cluster */
            int j, k;
            int cluster = -1;
            int rel_patch;

            for (j = 0; j < clustercount; j++) {
                int m;

                for (m = 0; m < clusters[j].count; m++) {
                    if (clusters[j].first_patch[m] == patch) {
                        cluster = j;
                        rel_patch = m;
                        break;
                    }
                }
            }

            if (cluster == -1) {
                G_fatal_error("A clusterless patch nr.%d encountered!", patch);
            }

            /* save which patch from which cluster has been deleted */
            cluster_notes[cur_pos] = cluster;
            patch_notes[cur_pos] = patch;
            cur_pos++;

            /* delete this patch from the cluster */
            clusters[cluster].first_patch[rel_patch] =
                clusters[cluster].first_patch[clusters[cluster].count - 1];
            clusters[cluster].count--;

            /* and from the adjacency matrix */

            for (k = 0; k < fragcount; k++) {
                adjmatrix[k * fragcount + patch] = 0;
                adjmatrix[patch * fragcount + k] = 0;
            }

            /* calculate index */
            calc_index(cur_values, clusters, clustercount, adjmatrix, fragments,
                       fragcount, distmatrix);
            cur_values += clustercount;
        }
    }
    else {
        /* for each cluster */
        for (i = 0; i < clustercount; i++) {
            int j, k;

            /* patch count times do */
            int count = clusters[i].count;

            for (j = 0; j < count; j++) {
                /* find next patch to delete */
                int patch = choose_patch(i, clusters, clustercount, adjmatrix,
                                         fragments, fragcount, distmatrix);
                int real_patch = clusters[i].first_patch[patch];

                /* save which patch from which cluster has been deleted */
                cluster_notes[cur_pos] = i;
                patch_notes[cur_pos] = real_patch;
                cur_pos++;

                /*int c;
                   fprintf(stderr, "Patch notes:");
                   for(c = 0; c < save_fc; c++) {
                   fprintf(stderr, " %d", patch_notes[c]);
                   }
                   fprintf(stderr, "\n"); */

                /* delete this patch from the cluster */
                clusters[i].first_patch[patch] =
                    clusters[i].first_patch[clusters[i].count - 1];
                clusters[i].count--;

                /* and from the adjacency matrix */

                for (k = 0; k < fragcount; k++) {
                    adjmatrix[k * fragcount + real_patch] = 0;
                    adjmatrix[real_patch * fragcount + k] = 0;
                }

                /* calculate index */
                calc_index(cur_values, clusters, clustercount, adjmatrix,
                           fragments, fragcount, distmatrix);
                cur_values += clustercount;
            }
        }
    }

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
    fprintf(out_fp, "cluster patch");
    for (i = 0; i < clustercount; i++) {
        fprintf(out_fp, " cluster_index_%d", i);
    }
    fprintf(out_fp, " change change_percent change_from_initial");
    fprintf(out_fp, "\n");

    /* write values */
    for (i = 0; i < fragcount + 1; i++) {
        int cluster = i > 0 ? cluster_notes[i - 1] : -1;
        int patch = i > 0 ? patch_notes[i - 1] : -1;
        int j;

        fprintf(out_fp, "%d %d", cluster, patch);

        for (j = 0; j < clustercount; j++) {
            fprintf(out_fp, " %f", values[i * clustercount + j]);
        }

        if (i > 0 && cluster >= 0) {
            /* print changes */
            DCELL initval = values[cluster];
            DCELL oldval = values[(i - 1) * clustercount + cluster];
            DCELL newval = values[i * clustercount + cluster];
            DCELL change = newval - oldval;
            DCELL change_pr = change / oldval * 100.0;
            DCELL change_from_init = change / initval * 100.0;

            fprintf(out_fp, " %f %f %f", change, change_pr, change_from_init);
        }
        else {
            fprintf(out_fp, " 0 0 0");
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
    G_free(values);
    G_free(patches);
    G_free(clusters);
    G_free(cells);
    G_free(fragments);
    G_free(flagbuf);
    G_free(result);

    G_free(distmatrix);
    G_free(adjmatrix);

    G_free(cluster_notes);
    G_free(patch_notes);

    exit(EXIT_SUCCESS);
}
