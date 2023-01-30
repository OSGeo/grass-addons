#include <stdlib.h>
#include <string.h>
#include <grass/gis.h>
#include <grass/vector.h>
#include <grass/glocale.h>
#include "local_proto.h"

void add_city(int city, int after, int *tncyc, int *tcycle, int *tcused)
{
    int i, j;

    /* after: index !!! to cycle, after which to put it */
    if (after == -1) {
        tcycle[0] = city;
    }
    else {
        /* for a large number of cities this will become slow */
        for (j = *tncyc - 1; j > after; j--)
            tcycle[j + 1] = tcycle[j];

        tcycle[after + 1] = city;
    }
    (*tncyc)++;
    tcused[city] = 1;

    if (debug_level >= 2) {
        G_debug(2, "Cycle:");
        for (i = 0; i < *tncyc; i++) {
            G_debug(2, "%d: %d: %d", i, tcycle[i], cities[tcycle[i]]);
        }
    }
}

int build_tour(int *cycle, int *cused, int *tncyc, int optimize, int opt_high)
{
    int j, k;
    int city, city1;
    int ncyc = *tncyc;
    double cost, tmpcost, tcost;

    /* complete the tour */

    /* In each step, find not used city with biggest cost to any used city,
     * and insert into cycle between 2 nearest nodes */
    /* for a large number of cities this will become very slow, can be fixed */

    while (ncyc < ncities) {
        if (opt_high)
            cost = -1;
        else
            cost = PORT_DOUBLE_MAX;
        city = -1;
        for (j = 0; j < ncities; j++) {
            if (cused[j])
                continue;
            tmpcost = 0;
            for (k = 0; k < ncities - 1; k++) {
                G_debug(2, "forward? %d (%d) - %d (%d)", j, cities[j],
                        costs[j][k].city, cities[costs[j][k].city]);
                if (!cused[costs[j][k].city])
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
                    if (!cused[bcosts[j][k].city])
                        continue; /* only used */
                    /* directional costs k -> j */
                    tmpcost += bcosts[j][k].cost;
                    break; /* first nearest */
                }
            }

            G_debug(2, "    cost = %f x %f", tmpcost, cost);
            if (opt_high) {
                if (tmpcost > cost) {
                    cost = tmpcost;
                    city = j;
                }
            }
            else {
                if (tmpcost < cost) {
                    cost = tmpcost;
                    city = j;
                }
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

        if (optimize && ncyc > 3)
            optimize_nbrs(city1, ncyc, cycle);
    }

    *tncyc = ncyc;

    return 1;
}
