#include <stdlib.h>
#include <string.h>
#include <grass/gis.h>
#include <grass/vector.h>
#include <grass/glocale.h>
#include "local_proto.h"

struct tsp_tour {
    int *cycle;  /* order of cities */
    double cost; /* total cost */
    int used;
    int opt_done;
};

struct tour_cost {
    int t;
    double cost;
};

/* common variables */
int *tcused, *tmpcycle;

/* helper functions */

int init_tour(struct tsp_tour *tour);
int init_ga_1(struct tsp_tour *tour, int ntours);
int init_ga_2(struct tsp_tour *tour, int ntours);
int ga_rem_dupl_tours(struct tsp_tour *tour, int ntours);
int ga_recombine(struct tsp_tour *tour, int p1, int p2, int c);
int ga_recombine2(struct tsp_tour *tour, int p1, int p2, int c);
int cmp_tour_cost(const void *pa, const void *pb);

/* genetic algorithm:
 * initialization
 * loop over
 * 1. natural selection
 * 2. recombination
 * 3. mutation
 * until there is no better solution */

int ga_opt(int ntours, int nelim, int nopt, int ngen, int *best_cycle)
{
    int i, j, k, t;
    double best_cost, worst_cost;
    int no_better, gen, best_tour, new_child, ncidx;
    int ntours_left, nparents;
    int nunused, *tunused;
    struct tsp_tour *tour, *tp;
    struct tour_cost *tc, *td;
    int init_method = 2;

    int max_chain_length, chain_length;
    int optiter, success;

    tour = G_malloc(ntours * sizeof(struct tsp_tour));
    tc = G_malloc(ntours * sizeof(struct tour_cost));
    td = G_malloc(ntours * sizeof(struct tour_cost));
    tunused = G_malloc(ntours * sizeof(int));
    tcused = G_malloc(ncities * sizeof(int));
    tmpcycle = G_malloc(ncities * sizeof(int));

    /* initialize */
    G_verbose_message(_("Generating %d tours"), ntours);
    for (i = 0; i < ntours; i++) {
        tp = &(tour[i]);
        init_tour(tp);
        tunused[i] = -1;
    }
    if (init_method == 1) {
        if (init_ga_1(tour, ntours) < ntours)
            G_fatal_error(_("Method 1 failed to create %d tours"), ntours);
    }
    else if (init_method == 2) {
        if (init_ga_2(tour, ntours) < ntours)
            G_fatal_error(_("Method 2 failed to create %d tours"), ntours);
    }
    else {
        G_fatal_error(_("Method %d is not implemented"), init_method);
    }

    /* tour costs */
    best_cost = -1;
    best_tour = -1;
    for (i = 0; i < ntours; i++) {
        tp = &(tour[i]);
        tp->cycle[ncities] = tp->cycle[0];
        tp->cost = 0;
        for (j = 0; j < ncities; j++)
            tp->cost += cost_cache[tp->cycle[j]][tp->cycle[j + 1]];

        tc[i].cost = tp->cost;
        tc[i].t = i;

        if (best_cost < 0) {
            best_cost = tp->cost;
            best_tour = i;
        }
        else if (best_cost > tp->cost) {
            best_cost = tp->cost;
            best_tour = i;
        }
    }

    no_better = gen = 0;

    while (!no_better && gen < ngen) {

        G_message(_("%d. Generation"), gen + 1);

        /* 1. natural selection */
        G_verbose_message(_("Natural Selection"));

        /* remove duplicate tours */
        ga_rem_dupl_tours(tour, ntours);

        ntours_left = nunused = 0;
        for (i = 0; i < ntours; i++) {
            if (!tour[i].used) {
                tour[i].opt_done = 0;
                tunused[nunused++] = i;
                continue;
            }

            tc[ntours_left].cost = tour[i].cost;
            tc[ntours_left].t = i;
            ntours_left++;
        }
        if (nunused)
            G_debug(1, "%d tours: %d duplicates removed", ntours, nunused);

        /* sort tours ascending by cost */
        qsort((void *)tc, ntours_left, sizeof(struct tour_cost), cmp_tour_cost);

        /* sort by cost difference to previous tour */
        for (t = 1; t < ntours_left; t++) {
            td[t - 1].cost = tour[tc[t].t].cost - tour[tc[t - 1].t].cost;
            td[t - 1].t = tc[t].t;
        }
        qsort((void *)td, ntours_left - 1, sizeof(struct tour_cost),
              cmp_tour_cost);
        G_debug(3, "Smallest difference: %.3f", td[0].cost);

        /* remove nelim tours */
        k = 0;
        while (ntours_left > ntours - nelim || td[k].cost < 0.0001) {
            tour[td[k].t].used = 0;
            tour[td[k].t].opt_done = 0;
            tunused[nunused++] = td[k].t;
            ntours_left--;
            k++;
        }
        G_debug(1, "%d tours: %d unused, %d left", ntours, nunused,
                ntours_left);
        if (ntours_left < 2)
            G_fatal_error(_("Diversity loss"));

        nunused = 0;
        for (i = 0, j = 0; i < ntours; i++) {
            if (!tour[i].used) {
                tunused[nunused++] = i;
                continue;
            }
            tc[j].cost = tour[i].cost;
            tc[j++].t = i;
        }
        if (j != ntours_left)
            G_fatal_error(_("Wrong number of remaining tours"));

        /* sort tours ascending by cost */
        qsort((void *)tc, ntours_left, sizeof(struct tour_cost), cmp_tour_cost);

        /* 2. recombination */
        G_verbose_message(_("Recombination"));
        nparents = ntours_left;

        new_child = -1;
        ncidx = nunused - 1;
        for (i = 0; i < nparents; i++) {
            for (j = i + 1; j < nparents; j++) {

                if (ntours_left < ntours) {
                    if (ncidx < 0)
                        G_fatal_error(_("1 ncidx too small"));

                    if (tunused[ncidx] < 0)
                        G_fatal_error(_("1 tunused too small"));

                    if (tunused[ncidx] >= ntours)
                        G_fatal_error(_("1 tunused too large"));

                    new_child = tunused[ncidx];
                }
                else {
                    worst_cost = -1;
                    for (k = 0; k < nunused; k++) {
                        if (worst_cost < tour[tunused[k]].cost) {
                            worst_cost = tour[tunused[k]].cost;
                            new_child = tunused[k];
                        }
                    }
                }

                if (ga_recombine(tour, tc[i].t, tc[j].t, new_child)) {
                    if (ntours_left < ntours) {
                        ncidx--;
                        ntours_left++;
                    }
                }

                if (ntours_left < ntours) {
                    if (ncidx < 0)
                        G_fatal_error(_("2 ncidx too small"));

                    if (tunused[ncidx] < 0)
                        G_fatal_error(_("2 tunused too small"));

                    if (tunused[ncidx] >= ntours)
                        G_fatal_error(_("2 tunused too large"));

                    new_child = tunused[ncidx];
                }
                else {
                    worst_cost = -1;
                    for (k = 0; k < nunused; k++) {
                        if (worst_cost < tour[tunused[k]].cost) {
                            worst_cost = tour[tunused[k]].cost;
                            new_child = tunused[k];
                        }
                    }
                }

                if (ga_recombine(tour, tc[j].t, tc[i].t, new_child)) {
                    if (ntours_left < ntours) {
                        ncidx--;
                        ntours_left++;
                    }
                }
            }
        }
        if (ntours_left < ntours) {
            G_debug(1, "Failed to generate enough new tours (old: %d, new: %d)",
                    nparents, ntours_left);
        }

        /* 3. optimization */
        G_verbose_message(_("Mutation"));
        for (i = 0; i < ntours; i++) {
            success = 1;

            if (!tour[i].used)
                continue;

            /*
            if (tour[i].opt_done)
                continue;
            */

            /* this can break out of the current local minimum */
            optimize_tour_chains(4, 2, 2, tour[i].cycle, tcused, ncities, 0, 0,
                                 1);

            for (j = 0; j < ncities; j++) {
                optimize_nbrs(j, ncities, tour[i].cycle);
                tcused[j] = 1;
            }

            /* this would approximate a local minimum,
             * but is slow and will be done later on with the best tour anyway
             * disabled */
#if 0
            while (success)
                success = optimize_tour_chains(4, 4, 1, tour[i].cycle, tcused, ncities, 0, 1, 1);
#endif

            tp = &(tour[i]);
            tp->cycle[ncities] = tp->cycle[0];
            tp->cost = 0;
            for (j = 0; j < ncities; j++)
                tp->cost += cost_cache[tp->cycle[j]][tp->cycle[j + 1]];

            tour[i].opt_done = 1;
        }
        /* debug */
        for (t = 0; t < ntours; t++) {
            if (!tour[i].used)
                continue;

            for (i = 0; i < ncities; i++)
                tcused[i] = 0;
            for (i = 0; i < ncities; i++) {
                if (tcused[tour[t].cycle[i]])
                    G_fatal_error(_("Duplicate city"));
                tcused[tour[t].cycle[i]] = 1;
            }
        }

        /* tour costs */
        ntours_left = 0;
        for (i = 0; i < ntours; i++) {
            if (!tour[i].used)
                continue;

            tp = &(tour[i]);

            tc[ntours_left].cost = tp->cost;
            tc[ntours_left].t = i;
            ntours_left++;
        }

        /* sort tours ascending by cost */
        qsort((void *)tc, ntours_left, sizeof(struct tour_cost), cmp_tour_cost);

        for (i = 0; i < ntours_left; i++) {
            if (!tour[tc[i].t].used)
                continue;
            G_debug(3, "%d. tour, cost %.3f", i + 1, tc[i].cost);
        }

        if (best_cost > tour[tc[0].t].cost + 0.0001) {
            no_better = 0;
        }
        else
            no_better++;

        best_cost = tour[tc[0].t].cost;
        best_tour = tc[0].t;

        G_verbose_message(_("Best tour: %d, best cost: %.3f"), best_tour,
                          best_cost);

        if (ntours_left == nparents)
            break;

        gen++;
    }

    for (i = 0; i < ncities; i++)
        best_cycle[i] = tour[best_tour].cycle[i];
    best_cycle[ncities] = best_cycle[0];

    /* brute force optimization of the best tour */
    G_message(_("Optimizing the best tour"));

    for (j = 0; j < ncities; j++) {
        optimize_nbrs(j, ncities, best_cycle);
    }

    optiter = 1;
    max_chain_length =
        MAX_CHAIN_LENGTH < ncities / 2 ? MAX_CHAIN_LENGTH : ncities / 2;
    for (chain_length = max_chain_length; chain_length > 0; chain_length--) {
        success = 0;

        G_message(_("%d. iteration..."), optiter++);

        if (max_chain_length >= 5)
            optimize_tour_chains(5, 5, 1, best_cycle, tcused, ncities, 1, 1, 0);
        else
            optimize_tour_chains(max_chain_length, max_chain_length, 1,
                                 best_cycle, tcused, ncities, 1, 1, 0);

        success = optimize_tour_chains(max_chain_length, 1, 1, best_cycle,
                                       tcused, ncities, 1, 1, 1);

        if (!success)
            break;
    }

    return gen;
}

int init_tour(struct tsp_tour *tour)
{
    tour->cycle = (int *)G_malloc((ncities + 1) * sizeof(int));

    if (tour->cycle == NULL)
        G_fatal_error(_("Out of memory"));

    tour->cost = -1;
    tour->used = 0;
    tour->opt_done = 0;

    return 1;
}

int init_ga_1(struct tsp_tour *tour, int ntours)
{
    int t, i;
    struct tsp_tour *tp;
    double cost, tmpcost;
    int start1, start2;
    int nxt1, nxt2;
    int tnc;

    start1 = start2 = -1;
    nxt1 = nxt2 = 0;
    t = 0;

    while (t < ntours) {
        tp = &(tour[t]);

        tnc = 0;
        for (i = 0; i < ncities; i++)
            tcused[i] = 0;

        if (t == 0) {
            /* the first tour is the standard tour */

            cost = start1 = -1;
            for (i = 0; i < ncities; i++) {
                tmpcost = costs[i][ncities - 2].cost;
                if (tmpcost > cost) {
                    cost = tmpcost;
                    start1 = i;
                }
            }
            start2 = costs[start1][ncities - 2].city;

            /* add these 2 cities to array */
            add_city(start1, -1, &tnc, tp->cycle, tcused);
            add_city(start2, 0, &tnc, tp->cycle, tcused);
        }
        else {
            if (nxt2 <= nxt1)
                nxt2 = nxt1 + 1;
            if (nxt2 >= ncities) {
                nxt1++;
                nxt2 = nxt1 + 1;
            }
            if (nxt1 == ncities - 1)
                return t;
            if (nxt2 >= ncities)
                return t;
            if ((nxt1 == start1 && nxt2 == start2) ||
                (nxt1 == start2 && nxt2 == start1)) {
                nxt2++;
                if (nxt2 >= ncities) {
                    nxt1++;
                    nxt2 = nxt1 + 1;
                }
                if (nxt1 == ncities - 1)
                    return t;
                if (nxt2 >= ncities)
                    return t;
            }
            /* add these 2 cities to array */
            tnc = 0;
            add_city(nxt1, -1, &tnc, tp->cycle, tcused);
            add_city(nxt2, 0, &tnc, tp->cycle, tcused);
        }

        build_tour(tp->cycle, tcused, &tnc, 2, 1);

        /* debug */
        for (i = 0; i < ncities; i++)
            tcused[i] = 0;
        for (i = 0; i < ncities; i++) {
            if (tcused[tp->cycle[i]])
                G_fatal_error(_("Duplicate city"));
            tcused[tp->cycle[i]] = 1;
        }

        tp->used = 1;
        t++;
    }

    return t;
}

int init_ga_2(struct tsp_tour *tour, int ntours)
{
    int t, i;
    int city, city1;
    int tnc;
    struct tsp_tour *tp;

    /* ntours must be <= ncities */
    if (ntours > ncities)
        G_fatal_error(_("The number of tours (%d) must not be larger than the "
                        "number of cities (%d)"),
                      ntours, ncities);

    /* use each city as start
     * go to nearest unused city
     * from this city
     * go to nearest unused city
     * etc until all cities are in the cycle */
    for (t = 0; t < ntours; t++) {
        tp = &(tour[t]);

        tnc = 0;
        for (i = 0; i < ncities; i++)
            tcused[i] = 0;

        city = t;
        tp->cycle[0] = city;
        tcused[city] = 1;
        tnc++;

        while (tnc < ncities) {
            /* get nearest unused city */
            city1 = -1;
            for (i = 0; i < ncities - 1; i++) {
                if (tcused[costs[city][i].city])
                    continue;
                city1 = costs[city][i].city;
                break;
            }
            if (city1 == -1)
                G_fatal_error(_("No unused city left"));
            tp->cycle[tnc] = city1;
            city = city1;
            tcused[city] = 1;
            tnc++;
        }
        tp->used = 1;

        /* debug */
        for (i = 0; i < ncities; i++)
            tcused[i] = 0;
        for (i = 0; i < ncities; i++) {
            if (tcused[tp->cycle[i]])
                G_fatal_error(_("Duplicate city"));
            tcused[tp->cycle[i]] = 1;
        }
    }

    return ntours;
}

int ga_rem_dupl_tours(struct tsp_tour *tour, int ntours)
{
    int i, j, k;
    int n_left, start1, start2, nxt1, nxt2;
    int tequal;

    /* remove duplicate tours */
    n_left = ntours;

    for (i = 0; i < ntours; i++) {

        if (!tour[i].used)
            continue;

        start1 = 0;
        for (j = i + 1; j < ntours; j++) {
            tequal = 1;

            if (!tour[j].used)
                continue;

            start2 = -1;
            for (k = 0; k < ncities; k++) {
                if (tour[j].cycle[k] == tour[i].cycle[start1]) {
                    start2 = k;
                    break;
                }
            }
            if (start2 == -1)
                G_fatal_error(_("start2 not found"));

            if (tour[i].cycle[start1] != tour[j].cycle[start2])
                G_fatal_error(_("No common start city"));

            /* move this up */
            if (fabs(tour[i].cost - tour[j].cost) > 0.01)
                continue;

            for (k = 0; k < ncities; k++) {
                nxt1 = wrap_into(start1 + k, ncities);
                nxt2 = wrap_into(start2 + k, ncities);
                if (tour[i].cycle[nxt1] != tour[j].cycle[nxt2])
                    tequal = 0;
                break;
            }
            if (tequal) {
                /* remove the tour */
                G_debug(1, "Tours %d and %d are identical", i, j);
                tour[j].used = 0;
                n_left--;
            }
        }
    }

    return n_left;
}

/* recombination similar to
 * http://www.gcd.org/sengoku/docs/arob98.pdf
 * here: not the longest (most nodes) subtour, but the shortest (costs) total
 * tour */
int ga_subtour(struct tsp_tour *tour, int p1, int p2, int c, int next_i,
               int *start_i)
{
    int i, j;
    int prev1, prev2, nxt1, nxt2, startsub, endsub;
    int cncyc;
    int have_p1, have_p2;
    int st_max, st_length, st_i, st_j;
    struct tsp_tour *parent1, *parent2, *child;

    G_debug(1, "ga_subtour()");

    parent1 = &(tour[p1]);
    parent2 = &(tour[p2]);
    child = &(tour[c]);
    cncyc = 0;

    child->used = 0;

    /* find subtour */
    st_max = st_length = st_i = st_j = -1;

    for (i = next_i; i < ncities; i++) {
        for (j = 0; j < ncities; j++)
            tcused[j] = 0;

        prev1 = wrap_into(i - 1, ncities);
        nxt1 = wrap_into(i + 1, ncities);

        st_length = -1;
        j = 0;

        while (parent2->cycle[j] != parent1->cycle[i]) {
            j++;
            if (j >= ncities)
                G_fatal_error(_("Missing city"));
        }

        if (parent2->cycle[j] != parent1->cycle[i])
            G_fatal_error(_("City mismatch"));

        prev2 = wrap_into(j - 1, ncities);
        nxt2 = wrap_into(j + 1, ncities);

        /* makes only sense if prev[1,2] are not equal or nxt[1,2] are not equal
         */
        if (parent2->cycle[prev2] != parent1->cycle[nxt1] &&
            (parent2->cycle[prev2] != parent1->cycle[prev1] &&
             parent2->cycle[nxt2] != parent1->cycle[nxt1])) {

            /* fake recombination */
            have_p1 = have_p2 = 1;
            tmpcycle[0] = parent1->cycle[i];
            tcused[parent1->cycle[i]] = 1;
            startsub = endsub = 0;
            st_length = 1;

            while (have_p1 || have_p2) {

                if (have_p1 && tcused[parent1->cycle[nxt1]])
                    have_p1 = 0;

                if (have_p1) {
                    endsub = wrap_into(endsub + 1, ncities);
                    tmpcycle[endsub] = parent1->cycle[nxt1];
                    tcused[parent1->cycle[nxt1]] = 1;
                    st_length++;

                    nxt1 = wrap_into(nxt1 + 1, ncities);
                    if (tcused[parent1->cycle[nxt1]])
                        have_p1 = 0;
                }

                if (have_p2 && tcused[parent2->cycle[prev2]])
                    have_p2 = 0;

                if (have_p2) {
                    startsub = wrap_into(startsub - 1, ncities);
                    tmpcycle[startsub] = parent2->cycle[prev2];
                    tcused[parent2->cycle[prev2]] = 1;
                    st_length++;

                    prev2 = wrap_into(prev2 - 1, ncities);
                    if (tcused[parent2->cycle[prev2]])
                        have_p2 = 0;
                }
            }
        }
        if (st_max <= st_length) {
            st_max = st_length;
            st_i = i;
            st_j = j;
        }
        if (st_max > 4)
            break;
    }
    *start_i = i;

    if (st_max <= 0)
        return 0;

    G_debug(3, "longest subtour %d at %d", st_max, st_i);

    for (i = 0; i < ncities; i++)
        tcused[i] = 0;

    /* recombination for selected subtour */
    i = st_i;
    j = st_j;
    nxt1 = wrap_into(i + 1, ncities);
    prev2 = wrap_into(j - 1, ncities);
    have_p1 = have_p2 = 1;
    tmpcycle[0] = parent1->cycle[i];
    tcused[parent1->cycle[i]] = 1;
    startsub = endsub = 0;

    while (have_p1 || have_p2) {

        if (have_p1 && tcused[parent1->cycle[nxt1]])
            have_p1 = 0;

        if (have_p1) {
            endsub = wrap_into(endsub + 1, ncities);
            tmpcycle[endsub] = parent1->cycle[nxt1];
            tcused[parent1->cycle[nxt1]] = 1;

            nxt1 = wrap_into(nxt1 + 1, ncities);
            if (tcused[parent1->cycle[nxt1]])
                have_p1 = 0;
        }

        if (have_p2 && tcused[parent2->cycle[prev2]])
            have_p2 = 0;

        if (have_p2) {
            startsub = wrap_into(startsub - 1, ncities);
            tmpcycle[startsub] = parent2->cycle[prev2];
            tcused[parent2->cycle[prev2]] = 1;

            prev2 = wrap_into(prev2 - 1, ncities);
            if (tcused[parent2->cycle[prev2]])
                have_p2 = 0;
        }
    }
    while (startsub != endsub) {
        if (cncyc >= ncities)
            G_fatal_error(_("Too many cities"));

        child->cycle[cncyc++] = tmpcycle[startsub];
        startsub = wrap_into(startsub + 1, ncities);
    }
    if (cncyc >= ncities)
        G_fatal_error(_("Too many cities"));

    if (startsub != endsub)
        G_fatal_error(_("startsub != endsub"));

    child->cycle[cncyc++] = tmpcycle[startsub];

#if 0
    /* this method is better, but the standard method */

    build_tour(child->cycle, tcused, &cncyc, 2, 0);

#else
    /* this method is faster and true recombination */

    /* add unused cities */
    i = nxt1;
    while (cncyc < ncities) {
        int found = 0;

        i = wrap_into(i + 1, ncities);

        if (tcused[parent1->cycle[i]]) {
            continue;
        }
        G_debug(3, "cncyc: %d", cncyc);

        if (tcused[parent1->cycle[nxt1]]) {
            child->cycle[cncyc++] = parent1->cycle[i];
            tcused[parent1->cycle[i]] = 1;
            continue;
        }

        prev1 = wrap_into(i - 1, ncities);
        nxt1 = wrap_into(i + 1, ncities);

        found = 0;
        j = 0;

        while (parent2->cycle[j] != parent1->cycle[i]) {
            j++;
            if (j >= ncities)
                G_fatal_error(_("Missing city"));
        }

        if (parent2->cycle[j] != parent1->cycle[i])
            G_fatal_error(_("City mismatch"));

        prev2 = wrap_into(j - 1, ncities);
        nxt2 = wrap_into(j + 1, ncities);

        if (tcused[parent2->cycle[prev2]]) {
            child->cycle[cncyc++] = parent1->cycle[i];
            tcused[parent1->cycle[i]] = 1;
            continue;
        }

        /* makes only sense if prev[1,2] are not equal or nxt[1,2] are not equal
         */
        if (parent2->cycle[prev2] != parent1->cycle[nxt1] &&
            (parent2->cycle[prev2] != parent1->cycle[prev1] &&
             parent2->cycle[nxt2] != parent1->cycle[nxt1])) {

            found = 1;

            /* actual recombination */
            have_p1 = have_p2 = 1;
            tmpcycle[0] = parent1->cycle[i];
            tcused[parent1->cycle[i]] = 1;
            startsub = endsub = 0;

            while (have_p1 || have_p2) {

                if (have_p1 && tcused[parent1->cycle[nxt1]])
                    have_p1 = 0;

                if (have_p1) {
                    endsub = wrap_into(endsub + 1, ncities);
                    tmpcycle[endsub] = parent1->cycle[nxt1];
                    tcused[parent1->cycle[nxt1]] = 1;

                    nxt1 = wrap_into(nxt1 + 1, ncities);
                    if (tcused[parent1->cycle[nxt1]])
                        have_p1 = 0;
                }

                if (have_p2 && tcused[parent2->cycle[prev2]])
                    have_p2 = 0;

                if (have_p2) {
                    startsub = wrap_into(startsub - 1, ncities);
                    tmpcycle[startsub] = parent2->cycle[prev2];
                    tcused[parent2->cycle[prev2]] = 1;

                    prev2 = wrap_into(prev2 - 1, ncities);
                    if (tcused[parent2->cycle[prev2]])
                        have_p2 = 0;
                }
            }
        }

        if (found) {
            /* add tmpcycle to child cycle */
            G_debug(3, "add subtour, startsub %d, endsub %d", startsub, endsub);

            while (startsub != endsub) {
                if (cncyc >= ncities)
                    G_fatal_error(_("Too many cities"));

                child->cycle[cncyc++] = tmpcycle[startsub];
                startsub = wrap_into(startsub + 1, ncities);
            }
            if (cncyc >= ncities)
                G_fatal_error(_("Too many cities"));

            if (startsub != endsub)
                G_fatal_error(_("startsub != endsub"));

            child->cycle[cncyc++] = tmpcycle[startsub];
            G_debug(3, "cncyc: %d", cncyc);
        }
        else {
            if (cncyc >= ncities)
                G_fatal_error(_("No subtour, too many cities"));

            child->cycle[cncyc++] = parent1->cycle[i];
            tcused[parent1->cycle[i]] = 1;
            G_debug(3, "cncyc: %d", cncyc);
        }
    }
#endif

    child->cost = 0;
    child->cycle[ncities] = child->cycle[0];
    for (i = 0; i < ncities; i++)
        child->cost += cost_cache[child->cycle[i]][child->cycle[i + 1]];

    child->used = 1;

    return child->used;
}

/* Greedy Crossover as in java-tsp
 * http://http://code.google.com/p/java-traveling-salesman/
 * children are too expensive */
int ga_recombine2(struct tsp_tour *tour, int p1, int p2, int c)
{
    int i;
    int nxt1, nxt2, picked, last;
    int cncyc;
    struct tsp_tour *parent1, *parent2, *child;

    parent1 = &(tour[p1]);
    parent2 = &(tour[p2]);
    child = &(tour[c]);

    cncyc = 0;
    nxt1 = 0;
    nxt2 = 0;

    for (i = 0; i < ncities; i++)
        tcused[i] = 0;

    picked = parent1->cycle[nxt1];
    child->cycle[cncyc] = picked;
    tcused[picked] = 1;
    last = picked;
    cncyc++;

    while (cncyc < ncities) {

        while (parent1->cycle[nxt1] != last)
            nxt1 = wrap_into(nxt1 + 1, ncities);
        nxt1 = wrap_into(nxt1 + 1, ncities);

        while (parent2->cycle[nxt2] != last)
            nxt2 = wrap_into(nxt2 + 1, ncities);
        nxt2 = wrap_into(nxt2 + 1, ncities);

        if (tcused[parent1->cycle[nxt1]] && tcused[parent2->cycle[nxt2]]) {
            while (tcused[parent1->cycle[nxt1]])
                nxt1 = wrap_into(nxt1 + 1, ncities);

            picked = parent1->cycle[nxt1];
        }
        else if (tcused[parent1->cycle[nxt1]]) {
            picked = parent2->cycle[nxt2];
        }
        else if (tcused[parent2->cycle[nxt2]]) {
            picked = parent1->cycle[nxt1];
        }
        else {
            if (cost_cache[last][parent1->cycle[nxt1]] <
                cost_cache[last][parent2->cycle[nxt2]]) {

                picked = parent1->cycle[nxt1];
            }
            else {
                picked = parent2->cycle[nxt2];
            }
        }
        child->cycle[cncyc] = picked;
        tcused[picked] = 1;
        last = picked;
        cncyc++;
    }

    child->cycle[ncities] = child->cycle[0];
    child->cost = 0;
    for (i = 0; i < ncities; i++)
        child->cost += cost_cache[child->cycle[i]][child->cycle[i + 1]];

    if (child->cost < parent1->cost && child->cost < parent2->cost)
        child->used = 1;
    else
        child->used = 1;

    child->opt_done = 0;

    return child->used;
}

int ga_recombine(struct tsp_tour *tour, int p1, int p2, int c)
{
    int i, start_i, best_i;
    double best_cost;

    G_debug(1, "ga_recombine()");

    /* select subtour resulting in shortest total tour:
     * genetic engineering */

    best_cost = best_i = start_i = -1;

    i = start_i + 1;
    while (i < ncities) {
        ga_subtour(tour, p1, p2, c, i, &start_i);
        if (tour[c].used) {
            if (best_cost < 0 || best_cost > tour[c].cost) {
                best_cost = tour[c].cost;
                best_i = start_i;
            }
        }
        i = start_i + 1;
    }

    if (best_cost < 0 || (best_cost > tour[p1].cost - 0.0001 &&
                          best_cost > tour[p2].cost - 0.0001)) {
        tour[c].used = 0;
    }
    else {
        ga_subtour(tour, p1, p2, c, best_i, &start_i);
        tour[c].used = 1;
    }

    return tour[c].used;
}

int cmp_tour_cost(const void *pa, const void *pb)
{
    struct tour_cost *p1 = (struct tour_cost *)pa;
    struct tour_cost *p2 = (struct tour_cost *)pb;

    if (p1->cost < p2->cost)
        return -1;

    if (p1->cost > p2->cost)
        return 1;

    return 0;
}
