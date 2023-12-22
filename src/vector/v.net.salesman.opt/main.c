/****************************************************************
 *
 *  MODULE:       v.net.salesman
 *
 *  AUTHOR(S):    Radim Blazek, Markus Metz
 *
 *  PURPOSE:      Create a cycle connecting given nodes.
 *
 *  COPYRIGHT:    (C) 2001-2011 by the GRASS Development Team
 *
 *                This program is free software under the
 *                GNU General Public License (>=v2).
 *                Read the file COPYING that comes with GRASS
 *                for details.
 *
 **************************************************************/
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <grass/gis.h>
#include <grass/vector.h>
#include <grass/dbmi.h>
#include <grass/glocale.h>
#include "local_proto.h"

/* use EUC_2D distances for TSPLIB test data */
#define TSP_TEST 0

/* TODO: Use some better algorithm */

int ncities; /* number of cities */
int nnodes;  /* number of nodes */
int *cities; /* array of cities */
int *cused;  /* city is in cycle */
COST *
    *costs; /* pointer to array of pointers to arrays of sorted forward costs */
COST **bcosts; /* pointer to array of pointers to arrays of sorted backward
                  costs */
double *
    *cost_cache; /* pointer to array of pointers to arrays of cached costs */
int *cycle;      /* path */
int ncyc = 0;    /* number of cities in cycle */
int debug_level;

int cmp(const void *, const void *);

int cnode(int city)
{
    return (cities[city]);
}

/* like Vect_list_append(), but allows duplicates */
int tsp_list_append(struct ilist *list, int val)
{
    size_t size;

    if (list == NULL)
        return 1;

    if (list->n_values == list->alloc_values) {
        size = (list->n_values + 1000) * sizeof(int);
        list->value = (int *)G_realloc((void *)list->value, size);
        list->alloc_values = list->n_values + 1000;
    }

    list->value[list->n_values] = val;
    list->n_values++;

    return 0;
}

int main(int argc, char **argv)
{
    int i, j, k, ret, city, city1;
    int nlines, type, ltype, afield, tfield, geo, cat;
    int node, node1, node2, line;
    int last_opt = 0, ostep, optimize;
    struct Option *map, *output, *afield_opt, *tfield_opt, *afcol, *abcol, *seq,
        *type_opt, *term_opt, *opt_opt;
    struct Flag *geo_f;
    struct GModule *module;
    struct Map_info Map, Out;
    struct ilist *TList; /* list of terminal nodes */
    struct ilist *List;
    struct ilist *StArcs;  /* list of arcs on tour */
    struct ilist *StNodes; /* list of nodes on tour */
    double cost, tmpcost, tcost;
    struct cat_list *Clist;
    struct line_cats *Cats;
    struct line_pnts *Points;
    const char *dstr;
    const char *seqname;
    int seq2stdout;
    char *desc;
    FILE *fp;

    /* Initialize the GIS calls */
    G_gisinit(argv[0]);

    module = G_define_module();
    G_add_keyword(_("vector"));
    G_add_keyword(_("network"));
    G_add_keyword(_("salesman"));
    module->label = _(
        "Creates a cycle connecting given nodes (Traveling salesman problem).");
    module->description =
        _("Note that TSP is NP-hard, heuristic algorithm is used by "
          "this module and created cycle may be suboptimal");

    map = G_define_standard_option(G_OPT_V_INPUT);
    output = G_define_standard_option(G_OPT_V_OUTPUT);

    type_opt = G_define_standard_option(G_OPT_V_TYPE);
    type_opt->options = "line,boundary";
    type_opt->answer = "line,boundary";
    type_opt->description = _("Arc type");

    afield_opt = G_define_standard_option(G_OPT_V_FIELD);
    afield_opt->key = "alayer";
    afield_opt->description = _("Arc layer");

    tfield_opt = G_define_standard_option(G_OPT_V_FIELD);
    tfield_opt->key = "nlayer";
    tfield_opt->answer = "2";
    tfield_opt->description = _("Node layer (used for cities)");

    afcol = G_define_option();
    afcol->key = "afcolumn";
    afcol->type = TYPE_STRING;
    afcol->required = NO;
    afcol->description =
        _("Arc forward/both direction(s) cost column (number)");

    abcol = G_define_option();
    abcol->key = "abcolumn";
    abcol->type = TYPE_STRING;
    abcol->required = NO;
    abcol->description =
        _("EXPERIMENTAL: Arc backward direction cost column (number)");

    seq = G_define_standard_option(G_OPT_F_OUTPUT);
    seq->key = "sequence";
    seq->type = TYPE_STRING;
    seq->required = NO;
    seq->description =
        _("Name for output file holding node sequence (\"-\" for stdout)");

    term_opt = G_define_standard_option(G_OPT_V_CATS);
    term_opt->key = "ccats";
    term_opt->required = YES;
    term_opt->description = _("Categories of points ('cities') on nodes "
                              "(layer is specified by nlayer)");

    opt_opt = G_define_option();
    opt_opt->type = TYPE_STRING;
    opt_opt->key = "method";
    opt_opt->required = NO;
    opt_opt->options = "bs,ga";
    opt_opt->description = _("Optimization method");
    desc = NULL;
    G_asprintf(&desc,
               "bs;%s;"
               "ga;%s;",
               _("bootstrapping"), _("genetic algorithm"));
    opt_opt->descriptions = desc;

    geo_f = G_define_flag();
    geo_f->key = 'g';
    geo_f->description =
        _("Use geodesic calculation for longitude-latitude locations");

    if (G_parser(argc, argv))
        exit(EXIT_FAILURE);

    Cats = Vect_new_cats_struct();
    Points = Vect_new_line_struct();

    type = Vect_option_to_types(type_opt);
    afield = atoi(afield_opt->answer);

    TList = Vect_new_list();
    List = Vect_new_list();
    StArcs = Vect_new_list();
    StNodes = Vect_new_list();

    Clist = Vect_new_cat_list();
    tfield = atoi(tfield_opt->answer);
    Vect_str_to_cat_list(term_opt->answer, Clist);

    dstr = G_getenv_nofatal("DEBUG");

    if (dstr != NULL)
        debug_level = atoi(dstr);
    else
        debug_level = 0;

    if (debug_level >= 1) {
        G_debug(1, "Input categories:");
        for (i = 0; i < Clist->n_ranges; i++) {
            G_debug(1, "%d - %d", Clist->min[i], Clist->max[i]);
        }
    }

    geo = geo_f->answer;

    if (opt_opt->answer) {
        if (opt_opt->answer[0] == 'b')
            optimize = 1;
        else if (opt_opt->answer[0] == 'g')
            optimize = 2;
        else
            G_fatal_error(_("Unknown method '%s'"), opt_opt->answer);
    }
    else
        optimize = 0;

    Vect_check_input_output_name(map->answer, output->answer, G_FATAL_EXIT);

    Vect_set_open_level(2);
    Vect_open_old(&Map, map->answer, "");
    nnodes = Vect_get_num_nodes(&Map);
    nlines = Vect_get_num_lines(&Map);

    /* Create list of terminals based on list of categories */
    for (i = 1; i <= nlines; i++) {

        ltype = Vect_get_line_type(&Map, i);
        if (!(ltype & GV_POINT))
            continue;

        Vect_read_line(&Map, Points, Cats, i);
        node = Vect_find_node(&Map, Points->x[0], Points->y[0], Points->z[0], 0,
                              0);
        if (!node) {
            G_warning(_("Point is not connected to the network"));
            continue;
        }
        if (!(Vect_cat_get(Cats, tfield, &cat)))
            continue;
        if (Vect_cat_in_cat_list(cat, Clist)) {
            tsp_list_append(TList, node);
        }
    }

    ncities = TList->n_values;
    G_message(_("Number of cities: [%d]"), ncities);
    if (ncities < 2)
        G_fatal_error(_("Not enough cities (< 2)"));

    /* Alloc memory */
    cities = (int *)G_malloc(ncities * sizeof(int));
    cused = (int *)G_malloc(ncities * sizeof(int));
    for (i = 0; i < ncities; i++) {
        G_debug(1, "%d", TList->value[i]);
        cities[i] = TList->value[i];
        cused[i] = 0; /* not in cycle */
    }

    costs = (COST **)G_malloc(ncities * sizeof(COST *));
    for (i = 0; i < ncities; i++) {
        costs[i] = (COST *)G_malloc(ncities * sizeof(COST));
    }
    cost_cache = (double **)G_malloc(ncities * sizeof(double *));
    for (i = 0; i < ncities; i++) {
        cost_cache[i] = (double *)G_malloc(ncities * sizeof(double));
    }
    if (abcol->answer) {
        bcosts = (COST **)G_malloc(ncities * sizeof(COST *));
        for (i = 0; i < ncities; i++) {
            bcosts[i] = (COST *)G_malloc(ncities * sizeof(COST));
        }
    }
    else
        bcosts = NULL;

    cycle = (int *)G_malloc((ncities + 1) *
                            sizeof(int)); /* + 1 is for output cycle */

    /* Build graph */
    Vect_net_build_graph(&Map, type, afield, 0, afcol->answer, abcol->answer,
                         NULL, geo, 0);

    /* Create sorted lists of costs */
    /* for a large number of cities this will become very slow, can not be fixed
     */
    G_message(_("Creating cost cache..."));
    G_begin_distance_calculations();
    for (i = 0; i < ncities; i++) {
        G_percent(i, ncities, 2);
        k = 0;
        for (j = 0; j < ncities; j++) {
            cost_cache[i][j] = 0.0;
            if (i == j)
                continue;

            if (!TSP_TEST) {
                ret = Vect_net_shortest_path(&Map, cities[i], cities[j], NULL,
                                             &cost);

                if (ret == -1)
                    G_fatal_error(_("Destination node [%d] is unreachable "
                                    "from node [%d]"),
                                  cities[i], cities[j]);
            }
            else {
                double x1, y1, z1, x2, y2, z2, dx, dy;

                Vect_get_node_coor(&Map, cities[i], &x1, &y1, &z1);
                Vect_get_node_coor(&Map, cities[j], &x2, &y2, &z2);

                if (geo) {
                    cost = G_distance(x1, y1, x2, y2);
                }
                else {
                    dx = x1 - x2;
                    dy = y1 - y2;
                    cost = sqrt(dx * dx + dy * dy);
                }
            }

            /* add to directional cost cache: from, to, cost */
            costs[i][k].city = j;
            costs[i][k].cost = cost;
            cost_cache[i][j] = cost;

            k++;
        }
        qsort((void *)costs[i], k, sizeof(COST), cmp);
    }
    G_percent(1, 1, 2);

    if (bcosts) {
        for (i = 0; i < ncities; i++) {
            /* this should be fast, no need for G_percent() */
            k = 0;
            for (j = 0; j < ncities; j++) {
                if (i == j)
                    continue;

                bcosts[i][k].city = j;
                bcosts[i][k].cost = cost_cache[j][i];

                k++;
            }
            qsort((void *)bcosts[i], k, sizeof(COST), cmp);
        }
    }

    if (debug_level >= 2) {
        /* debug: print sorted */
        for (i = 0; i < ncities; i++) {
            for (j = 0; j < ncities - 1; j++) {
                city = costs[i][j].city;
                G_debug(2, "%d -> %d = %f", cities[i], cities[city],
                        costs[i][j].cost);
            }
        }
    }

    if (ncities < 5 && optimize) {
        G_message(_("Optimization is not necessary for less than 5 cities"));
        optimize = 0;
    }

    if (optimize < 2) {
        G_message(_("Searching for the shortest tour..."));
        /* find 2 cities with largest distance */
        cost = city = -1;
        for (i = 0; i < ncities; i++) {
            tmpcost = costs[i][ncities - 2].cost;
            if (tmpcost > cost) {
                cost = tmpcost;
                city = i;
            }
        }

        G_debug(2, "biggest costs %d - %d", city,
                costs[city][ncities - 2].city);

        /* add these 2 cities to array */
        add_city(city, -1, &ncyc, cycle, cused);
        add_city(costs[city][ncities - 2].city, 0, &ncyc, cycle, cused);

        /* In each step, find not used city with biggest cost to any used city,
         * and insert into cycle between 2 nearest nodes */
        /* for a large number of cities this will become very slow, can be fixed
         */

        /* for (i = 0; i < ncities - 2; i++) { */
        while (ncyc < ncities) {
            G_percent(ncyc, ncities, 1);
            cost = -1;
            G_debug(2, "---- city %d ----", i);
            for (j = 0; j < ncities; j++) {
                if (cused[j])
                    continue;
                tmpcost = 0;
                for (k = 0; k < ncities - 1; k++) {
                    G_debug(2, "forward? %d (%d) - %d (%d)", j, cnode(j),
                            costs[j][k].city, cnode(costs[j][k].city));
                    if (!cused[costs[j][k].city])
                        continue; /* only used */
                    /* directional costs j -> k */
                    tmpcost += costs[j][k].cost;
                    break; /* first nearest */
                }
                /* forward/backward: tmpcost = min(fcost) + min(bcost) */
                if (bcosts) {
                    for (k = 0; k < ncities - 1; k++) {
                        G_debug(2, "backward? %d (%d) - %d (%d)", j, cnode(j),
                                bcosts[j][k].city, cnode(bcosts[j][k].city));
                        if (!cused[bcosts[j][k].city])
                            continue; /* only used */
                        /* directional costs k -> j */
                        tmpcost += bcosts[j][k].cost;
                        break; /* first nearest */
                    }
                }

                G_debug(2, "    cost = %f x %f", tmpcost, cost);
                if (tmpcost > cost) {
                    cost = tmpcost;
                    city = j;
                }
            }
            G_debug(2, "add city %d", city);

            /* add to cycle on lowest costs */
            cycle[ncyc] = cycle[0]; /* temporarily close the cycle */
            cost = PORT_DOUBLE_MAX;
            city1 = 0;
            for (j = 0; j < ncyc; j++) {
                /* cost from j to j + 1 (directional) */
                /* get cost from directional cost cache */
                tcost = cost_cache[cycle[j]][cycle[j + 1]];
                tmpcost = -tcost;

                /* check insertion of city between j and j + 1 */

                /* cost from j to city (directional) */
                /* get cost from directional cost cache */
                tcost = cost_cache[cycle[j]][city];
                tmpcost += tcost;
                /* cost from city to j + 1 (directional) */
                /* get cost from directional cost cache */
                tcost = cost_cache[city][cycle[j + 1]];
                tmpcost += tcost;

                /* tmpcost must always be > 0 */

                /* always true for j = 0 */
                if (tmpcost < cost) {
                    city1 = j;
                    cost = tmpcost;
                }
            }
            add_city(city, city1, &ncyc, cycle, cused);

            if (optimize && ncyc > 4) {
                int chain_length;
                int success;

                success = optimize_nbrs(city1, ncyc, cycle);
                if (success)
                    G_debug(3, "Neighbours optimized? %s",
                            success ? "Yes" : "No");

                /* keep ostep sufficiently large */
                ostep = sqrt(ncyc) * 2 / 3;

                if (ostep < 2)
                    ostep = 2;
                if (ostep > MAX_CHAIN_LENGTH && ncities < 3000) /* max 3000 */
                    ostep = MAX_CHAIN_LENGTH;

                if (last_opt < ncyc - ostep) {

                    /* use brute force optimization
                     * don't overdo it here, it's costly in terms of time
                     * and the benefits are small */

                    chain_length = ostep;
                    if (chain_length > ncyc / 2)
                        chain_length = ncyc / 2;
                    if (chain_length > MAX_CHAIN_LENGTH)
                        chain_length = MAX_CHAIN_LENGTH;
                    if (chain_length == 0)
                        chain_length = 1;

                    success =
                        optimize_tour_chains(chain_length, chain_length, ostep,
                                             cycle, cused, ncyc, 0, 0, 1);
                    if (success)
                        G_debug(3, "Preliminary tour optimized? %s",
                                success ? "Yes" : "No");

                    last_opt = ncyc;
                }
            } /* optimize done */
        }

        /* tour is complete */

        if (optimize && ncyc > 3) {
            double ocost, ocost1;
            int max_chain_length, chain_length;
            int success = 0;
            int optiter = 1;

            /* brute force bootstrapping */
            ocost = 0.;
            cycle[ncyc] = cycle[0];
            for (j = 0; j < ncyc; j++) {
                ocost += cost_cache[cycle[j]][cycle[j + 1]];
            }
            G_verbose_message(_("Current total cost: %.3f"), ocost);

            max_chain_length =
                MAX_CHAIN_LENGTH < ncyc / 2 ? MAX_CHAIN_LENGTH : ncyc / 2;

            G_message(_("Optimizing..."));

            for (chain_length = max_chain_length; chain_length > 0;
                 chain_length--) {
                success = 0;

                G_message("%d. iteration...", optiter++);

                if (max_chain_length >= 5)
                    optimize_tour_chains(max_chain_length, max_chain_length, 1,
                                         cycle, cused, ncyc, 1, 1, 0);
                else
                    optimize_tour_chains(max_chain_length, max_chain_length, 1,
                                         cycle, cused, ncyc, 1, 1, 0);

                success = optimize_tour_chains(max_chain_length, 1, 1, cycle,
                                               cused, ncyc, 1, 1, 1);

                if (!success)
                    break;
            }
            success = 1;
            while (success) {
                success = 0;
                G_message("%d. iteration...", optiter++);
                for (i = 0; i < ncyc; i++) {
                    if (optimize_nbrs(i, ncyc, cycle))
                        success = 1;
                }
            }

            ocost1 = 0.;
            cycle[ncyc] = cycle[0];
            for (j = 0; j < ncyc; j++) {
                ocost1 += cost_cache[cycle[j]][cycle[j + 1]];
            }
            G_verbose_message(_("Optimized total cost: %.3f, gain %.3f%%"),
                              ocost1, ocost / ocost1 * 100 - 100);
        } /* optimize done */
    }
    else {
        int ntours, nelim, nopt, ngen;

        /* number of tours to work with */
        if (ncities > 20)
            ntours = 20;
        else
            ntours = ncities - 1;

        /* number of tours to eliminate (< ntours / 2) */
        nelim = ntours * 0.4;
        /* number of tours to optimize (<= ntours) */
        nopt = ntours * 1;
        /* max number of generations */
        ngen = 200;

        ga_opt(ntours, nelim, nopt, ngen, cycle);
    }

    if (debug_level >= 2) {
        /* debug print */
        G_debug(2, "Tour:");
        for (i = 0; i < ncities; i++) {
            G_debug(2, "%d: %d: %d", i, cycle[i], cities[cycle[i]]);
        }
    }

    /* Create list of arcs */
    cycle[ncities] = cycle[0]; /* close the cycle */
    cost = 0.0;
    for (i = 0; i < ncities; i++) {
        node1 = cities[cycle[i]];
        node2 = cities[cycle[i + 1]];
        G_debug(2, " %d -> %d", node1, node2);
        ret = Vect_net_shortest_path(&Map, node1, node2, List, NULL);
        cost += cost_cache[cycle[i]][cycle[i + 1]];
        for (j = 0; j < List->n_values; j++) {
            line = abs(List->value[j]);
            /* Vect_list_append() appends only if value not yet present !!!
             * this breaks the correct sequence */
            tsp_list_append(StArcs, line);
            Vect_get_line_nodes(&Map, line, &node1, &node2);
            tsp_list_append(StNodes, node1);
            tsp_list_append(StNodes, node2);
        }
    }

    /* Write arcs to new map */
    Vect_open_new(&Out, output->answer, Vect_is_3d(&Map));
    Vect_hist_command(&Out);

    G_debug(2, "Arcs' categories (layer %d, %d arcs):", afield,
            StArcs->n_values);

    for (i = 0; i < StArcs->n_values; i++) {
        line = StArcs->value[i];
        ltype = Vect_read_line(&Map, Points, Cats, line);
        Vect_write_line(&Out, ltype, Points, Cats);
        Vect_cat_get(Cats, afield, &cat);
        G_debug(2, "%d. arc: cat %d", i + 1, cat);
    }

    seq2stdout = 0;
    seqname = NULL;
    if (seq->answer) {
        if (strcmp(seq->answer, "-")) {
            seqname = seq->answer;
        }
        else {
            seqname = G_tempfile();
            seq2stdout = 1;
        }

        fp = fopen(seqname, "w");
        if (!fp)
            G_fatal_error(_("Unable to open file '%s' for writing"), seqname);

        fprintf(fp, "sequence;category;cost_to_next\n");
    }
    else
        fp = NULL;

    k = 0;
    /* this writes out only user-selected nodes, not all visited nodes */
    G_debug(2, "Nodes' categories (layer %d, %d nodes):", tfield, ncities);
    for (i = 0; i < ncities; i++) {
        double coor_x, coor_y, coor_z;

        node = cities[cycle[i]];
        Vect_get_node_coor(&Map, node, &coor_x, &coor_y, &coor_z);
        line = Vect_find_line(&Map, coor_x, coor_y, coor_z, GV_POINT, 0, 0, 0);

        if (!line)
            continue;

        ltype = Vect_read_line(&Map, Points, Cats, line);
        if (!(ltype & GV_POINT))
            continue;
        if (!(Vect_cat_get(Cats, tfield, &cat)))
            continue;
        Vect_write_line(&Out, ltype, Points, Cats);
        k++;
        if (fp) {
            fprintf(fp, "%d;%d;%.3f\n", k, cat,
                    cost_cache[cycle[i]][cycle[i + 1]]);
        }

        G_debug(2, "%d. node: cat %d", k, cat);
    }

    Vect_build(&Out);

    /* Free, ... */
    Vect_destroy_list(StArcs);
    Vect_destroy_list(StNodes);
    Vect_close(&Map);
    Vect_close(&Out);

    G_message(_("Tour with total cost %.3f"), cost);

    if (fp) {
        fclose(fp);
        if (seq2stdout) {
            char buf[2000];

            /* spacer to previous output to stderr */
            G_message(" ");

            fp = fopen(seqname, "r");
            while (G_getl2(buf, 2000, fp) != 0)
                fprintf(stdout, "%s\n", buf);

            fclose(fp);
            remove(seqname);
        }
    }

    exit(EXIT_SUCCESS);
}

int cmp(const void *pa, const void *pb)
{
    COST *p1 = (COST *)pa;
    COST *p2 = (COST *)pb;

    if (p1->cost < p2->cost)
        return -1;

    if (p1->cost > p2->cost)
        return 1;

    return 0;
}
