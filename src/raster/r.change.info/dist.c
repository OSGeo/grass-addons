#include <math.h>
#include <grass/gis.h>
#include <grass/raster.h>
#include "ncb.h"
#include "window.h"

/* Average statistical distance between average distribution and
 * observed distributions:
 * sum of the absolute differences divided by the number of distributions
 *
 * dist: array of distributions
 * nd: number of cells in each distribution
 * n: number of distributions
 * dsize: distributions' size */

DCELL dist(double **dist, int *nd, int n, int dsize)
{
    int i, d, n_comb;
    double dp;
    double p_avg, d_dist;

    d_dist = 0;
    n_comb = 0;
    for (d = 0; d < n; d++) {
        n_comb += nd[d];
    }
    for (i = 0; i < dsize; i++) {

        /* Create combined distribution */
        p_avg = 0;
        for (d = 0; d < n; d++) {
            if (dist[d][i] > 0 && nd[d] > 0) {
                p_avg += dist[d][i];
            }
        }
        /* Difference to combined distribution */
        if (p_avg > 0) {
            p_avg /= n_comb;
            for (d = 0; d < n; d++) {
                if (nd[d] > 0) {
                    dp = p_avg - dist[d][i] / nd[d];
                    d_dist += fabs(dp);
                }
            }
        }
    }

    if (d_dist == 0)
        return 0;

    return d_dist / (2 * (n - 1));
}

DCELL dist1(void)
{
    return dist(ci.dt, ci.n, ncb.nin, ci.ntypes);
}

DCELL dist2(void)
{
    return dist(ci.ds, ci.n, ncb.nin, ci.nsizebins);
}

DCELL dist3(void)
{
    return dist(ci.dts, ci.n, ncb.nin, ci.dts_size);
}
