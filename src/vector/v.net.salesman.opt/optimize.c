#include <stdlib.h>
#include <string.h>
#include <grass/gis.h>
#include <grass/vector.h>
#include <grass/glocale.h>
#include "local_proto.h"

int wrap_into(int i, int n)
{
    /* wrap to range 0, n - 1 */
    while (i >= n)
        i -= n;
    while (i < 0)
        i += n;

    return i;
}

int wrap_towards(int i, int n)
{
    /* wrap to range -n, 2n - 1 */
    while (i - n >= n)
        i -= n;
    while (i + n < 0)
        i += n;

    return i;
}

/* swap nodes if result is better */
int optimize_nbrs(int city1, int tncyc, int *tcycle)
{
    int j, k, city, city2;
    int prev, nxt, prevk, nxtk;
    double ocost1, ocost2, tmpcost, gain;
    int success = 0;

    /* check alternatives for city1 and city1 + 2 */
    for (j = city1; j < city1 + 3; j += 2) {

        /* city += j; */
        city = wrap_into(j, tncyc);
        prev = wrap_into(city - 1, tncyc);
        nxt = wrap_into(city + 1, tncyc);
        ocost1 = cost_cache[tcycle[prev]][tcycle[city]] +
                 cost_cache[tcycle[city]][tcycle[nxt]];
        gain = 0;
        tmpcost = 0;
        city2 = tcycle[city];
        for (k = 0; k < tncyc; k++) {

            prevk = wrap_into(k - 1, tncyc);
            nxtk = wrap_into(k + 1, tncyc);

            /* original costs */
            ocost2 = cost_cache[tcycle[prevk]][tcycle[k]] +
                     cost_cache[tcycle[k]][tcycle[nxtk]];

            /* new costs:
             * (city1 - 1) -> k -> (city1 + 1)
             * (k - 1) -> city1 -> (k + 1) */
            tmpcost = cost_cache[tcycle[prev]][tcycle[k]] +
                      cost_cache[tcycle[k]][tcycle[nxt]] +
                      cost_cache[tcycle[prevk]][tcycle[city]] +
                      cost_cache[tcycle[city]][tcycle[nxtk]];

            if (ocost1 + ocost2 - tmpcost > gain) {
                gain = ocost1 + ocost2 - tmpcost;
                city2 = k;
            }
        }
        if (gain > 0 && tcycle[city2] != tcycle[city] &&
            tcycle[city2] != tcycle[prev] && tcycle[city2] != tcycle[nxt]) {
            /* swap cities */
            G_debug(3, "swap cities");
            tcycle[tncyc] = tcycle[city2];
            tcycle[city2] = tcycle[city];
            tcycle[city] = tcycle[tncyc];
            tcycle[tncyc] = tcycle[0];
            success = 1;
        }
    } /* neighbor check done */

    return success;
}

/* standard 2opt method
 * disadvantage: requires reversing a subtour, not good for
 * asymmetric problems, therefore not used */
int opt_2opt(int *tcycle, int *tcused, int tncyc)
{
    int i, j, k, nxt1, nxt2;
    int pivot1;
    double cost, new_cost;
    static int *tmpcycle = NULL;

    if (tmpcycle == NULL)
        tmpcycle = G_malloc((ncities + 1) * sizeof(int));

    tcycle[tncyc] = tcycle[0];

    for (i = 0; i < tncyc; i++) {
        for (j = 0; j < tncyc; j++) {
            if (j == i || j == i + 1)
                continue;

            nxt2 = wrap_into(j + 1, tncyc);
            if (nxt2 == i)
                continue;

            cost = cost_cache[tcycle[i]][tcycle[i + 1]] +
                   cost_cache[tcycle[j]][tcycle[j + 1]];

            new_cost = cost_cache[tcycle[i]][tcycle[j + 1]] +
                       cost_cache[tcycle[j]][tcycle[i + 1]];

            if (new_cost > cost)
                continue;

            /* go from i to j,
             * backwards until we meet i + 1, go from i + 1 to j + 1,
             * forwards until we meet i again */
            nxt1 = i;
            tmpcycle[nxt1] = tcycle[i];
            nxt1 = wrap_into(nxt1 + 1, tncyc);
            tmpcycle[nxt1] = tcycle[j];

            nxt2 = j;
            nxt1 = wrap_into(nxt1 + 1, tncyc);
            nxt2 = wrap_into(nxt2 - 1, tncyc);

            pivot1 = wrap_into(i + 1, tncyc);
            while (nxt2 != pivot1) {
                tmpcycle[nxt1] = tcycle[nxt2];
                nxt1 = wrap_into(nxt1 + 1, tncyc);
                nxt2 = wrap_into(nxt2 - 1, tncyc);
            }
            /* nxt2 = i + 1 */
            tmpcycle[nxt1] = tcycle[nxt2];
            nxt1 = wrap_into(nxt1 + 1, tncyc);
            nxt2 = wrap_into(j + 1, tncyc);
            tmpcycle[nxt1] = tcycle[nxt2];

            nxt1 = wrap_into(nxt1 + 1, tncyc);
            nxt2 = wrap_into(nxt2 + 1, tncyc);
            while (nxt2 != i) {
                tmpcycle[nxt1] = tcycle[nxt2];
                nxt1 = wrap_into(nxt1 + 1, tncyc);
                nxt2 = wrap_into(nxt2 + 1, tncyc);
            }
            for (k = 0; k < tncyc; k++)
                tcycle[k] = tmpcycle[k];

            tcycle[tncyc] = tcycle[0];
        }
    }

    return 1;
}

/* bootstrapping:
 * cut out subtour of length chain_length
 * reinsert the removed nodes */

int optimize_tour(int *tcycle, int *tcused, int tncyc, int chain_length,
                  int show_perc, int opt_high, int subtour)
{
    int i, j, k;
    int city, city1;
    int cl1, cl2, cl3, cstep;
    double cost, tcost, tmpcost, ocost1, ocost2;
    int nl[MAX_CHAIN_LENGTH];
    static int *ccycle = NULL;
    int success = 0, found;
    int ncyc_noopt, n_removed;

    if (!ccycle)
        ccycle = (int *)G_malloc((ncities + 1) *
                                 sizeof(int)); /* + 1 is for output cycle */

    cl1 = chain_length;
    cstep = cl1 * 2 / 3; /* adjust */

    if (cstep == 0)
        cstep = 1;

    ncyc_noopt = tncyc;

    if (show_perc)
        G_message("Chain length %d", cl1);

    for (i = 0; i < ncyc_noopt; i += cstep) {
        if (show_perc)
            G_percent(i, ncyc_noopt, 2);

        /* copy of current cycle */
        for (j = 0; j < tncyc; j++)
            ccycle[j] = tcycle[j];

        /* remove <cl1> nodes */
        n_removed = 0;

        if (subtour) {
            /* cut out subtour */
            for (cl2 = 0; cl2 < tncyc; cl2++) {
                j = wrap_into(i, tncyc);
                nl[n_removed] = tcycle[j];

                if (!tcused[tcycle[j]])
                    continue;

                G_debug(3, "removing city %d, cycle %d", nl[n_removed], j);
                tcused[tcycle[j]] = 0;
                for (k = j; k < tncyc; k++)
                    tcycle[k] = tcycle[k + 1];
                tncyc--;
                n_removed++;
                if (n_removed == cl1)
                    break;
            }
        }
        else {
            /* cut our nearest */
            j = wrap_into(i, tncyc);
            city = tcycle[j];
            nl[n_removed] = city;
            tcused[city] = 0;
            found = 0;
            for (k = 0; k < tncyc; k++) {
                if (tcycle[k] == city)
                    found = 1;
                if (found)
                    tcycle[k] = tcycle[k + 1];
            }
            tncyc--;

            n_removed++;

            for (cl2 = 0; cl2 < tncyc - 1; cl2++) {

                if (n_removed == cl1)
                    break;

                city = costs[tcycle[j]][cl2].city;

                if (!tcused[city])
                    continue;

                nl[n_removed] = city;
                G_debug(3, "removing city %d", nl[n_removed]);
                tcused[city] = 0;
                found = 0;
                for (k = 0; k < tncyc; k++) {
                    if (tcycle[k] == city)
                        found = 1;
                    if (found)
                        tcycle[k] = tcycle[k + 1];
                }
                tncyc--;

                n_removed++;
                if (n_removed == cl1)
                    break;
            }
        }

        if (!n_removed)
            return 1;

        /* reinsert <cl1> nodes */
        for (cl2 = 0; cl2 < n_removed; cl2++) {
            if (opt_high)
                cost = -1;
            else
                cost = PORT_DOUBLE_MAX;
            city = -1;
            G_debug(3, "---- city %d ----", i);
            for (cl3 = 0; cl3 < n_removed; cl3++) {
                j = nl[cl3];
                if (tcused[j])
                    continue;
                tmpcost = 0;
                for (k = 0; k < ncities - 1; k++) {
                    G_debug(2, "forward? %d (%d) - %d (%d)", j, cities[j],
                            costs[j][k].city, cities[costs[j][k].city]);
                    if (!tcused[costs[j][k].city])
                        continue; /* only used */
                    /* directional costs j -> k */
                    tmpcost += costs[j][k].cost;
                    break; /* first nearest */
                }
                /* forward/backward: tmpcost = min(fcost) + min(bcost) */
                if (bcosts) {
                    for (k = 0; k < ncities - 1; k++) {
                        G_debug(2, "backward? %d (%d) - %d (%d)", j, cities[j],
                                bcosts[j][k].city, cities[bcosts[j][k].city]);
                        if (!tcused[bcosts[j][k].city])
                            continue; /* only used */
                        /* directional costs k -> j */
                        tmpcost += bcosts[j][k].cost;
                        break; /* first nearest */
                    }
                }

                G_debug(2, "    cost = %f x %f", tmpcost, cost);
                if (opt_high) {
                    /* pick farthest */
                    if (tmpcost > cost) {
                        cost = tmpcost;
                        city = j;
                    }
                }
                else {
                    /* pick nearest */
                    if (tmpcost < cost) {
                        cost = tmpcost;
                        city = j;
                    }
                }
            }
            G_debug(3, "add city %d", city);

            /* add to cycle on lowest costs */
            tcycle[tncyc] = tcycle[0]; /* temporarily close the cycle */
            cost = PORT_DOUBLE_MAX;
            city1 = 0;
            for (j = 0; j < tncyc; j++) {
                /* cost from j to j + 1 (directional) */
                /* get cost from directional cost cache */
                tcost = cost_cache[tcycle[j]][tcycle[j + 1]];
                tmpcost = -tcost;

                /* check insertion of city between j and j + 1 */

                /* cost from j to city (directional) */
                /* get cost from directional cost cache */
                tcost = cost_cache[tcycle[j]][city];
                tmpcost += tcost;
                /* cost from city to j + 1 (directional) */
                /* get cost from directional cost cache */
                tcost = cost_cache[city][tcycle[j + 1]];
                tmpcost += tcost;

                /* tmpcost must always be > 0 */

                G_debug(2, "? %d - %d cost = %f x %f", j, city1, tmpcost, cost);
                /* always true for j = 0 */
                if (tmpcost < cost) {
                    city1 = j;
                    cost = tmpcost;
                }
            }
            add_city(city, city1, &tncyc, tcycle, tcused);

            tcycle[tncyc] = tcycle[0];

            if (tncyc > 3)
                optimize_nbrs(city1, tncyc, tcycle);

        } /* all nodes reinserted */

        /* compare cycles */
        ocost1 = ocost2 = 0.;
        tcycle[tncyc] = tcycle[0];
        ccycle[tncyc] = ccycle[0];
        for (j = 0; j < tncyc; j++) {
            ocost1 += cost_cache[ccycle[j]][ccycle[j + 1]];
            ocost2 += cost_cache[tcycle[j]][tcycle[j + 1]];
        }
        if (ocost1 - ocost2 > 0.001) {
            success = 1;
            G_debug(3, "success for chain length %d, gain %.4f", cl1,
                    ocost1 - ocost2);
        }
        else {
            for (j = 0; j < tncyc; j++)
                tcycle[j] = ccycle[j];
        }
    } /* chain length for all cities removed */

    return success;
}

int optimize_tour_chains(int hi, int lo, int cstep, int *tcycle, int *tused,
                         int tncyc, int show_perc, int opt_high, int subtour)
{
    int cl1, success = 0;

    if (lo <= 0)
        lo = 1;

    if (hi > tncyc / 2)
        hi = tncyc / 2;
    if (hi > MAX_CHAIN_LENGTH)
        hi = MAX_CHAIN_LENGTH;
    if (hi <= 0)
        hi = 1;
    if (hi < lo)
        lo = hi;

    for (cl1 = hi; cl1 >= lo; cl1 -= cstep) {

        if (!optimize_tour(tcycle, tused, tncyc, cl1, show_perc, opt_high,
                           subtour))
            break;
        success = 1;
    }

    return success;
}
