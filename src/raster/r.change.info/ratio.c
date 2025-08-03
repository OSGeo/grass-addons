#include <math.h>
#include <grass/gis.h>
#include <grass/raster.h>
#include "ncb.h"
#include "window.h"

/* information gain ratio = proportion of change
 * dist: array of distributions
 * nd: number of cells in each distribution
 * n: number of distributions
 * dsize: distributions' size
 * h: entropy for each distribution */

DCELL ratio(double **dist, int *nd, int n, int dsize, double *h)
{
    int i, d, n_comb;
    double p, pe, p_comb, H_comb, H_avg, IV, igr;

    /* entropy of combined distribution */
    /* average entropy of all distributions */

    H_comb = 0;
    H_avg = 0;
    IV = 0;
    n_comb = 0;
    for (d = 0; d < n; d++) {
        h[d] = 0;
        n_comb += nd[d];
    }
    for (i = 0; i < dsize; i++) {
        p_comb = 0;
        for (d = 0; d < n; d++) {
            if (dist[d][i] > 0 && nd[d] > 0) {
                p = dist[d][i] / nd[d];
                p_comb += dist[d][i];
                pe = entropy_p(p);
                h[d] += pe;
            }
        }
        if (p_comb > 0) {
            H_comb += entropy_p(p_comb / n_comb);
        }
    }
    H_avg = 0;
    IV = 0;
    for (d = 0; d < n; d++) {
        H_avg += entropy(h[d]) * nd[d] / n_comb;
        /* intrinsic value in decision tree modelling
         * here a constant if there are no NULL cells */
        IV += entropy_p((double)nd[d] / n_comb);
    }
    H_comb = entropy(H_comb);
    IV = entropy(IV);

    if (H_comb < 0)
        H_comb = 0;
    if (H_avg < 0)
        H_avg = 0;
    if (IV < 0)
        IV = 0;

    if (H_comb == 0)
        return 0;

    if (H_comb < H_avg)
        return 0;

    /* information gain rate:
     * actual change divided by maximum possible change
     * (H_comb - H_avg) / H_comb */
    igr = 1 - H_avg / H_comb;

    return igr;
}

DCELL ratio1(void)
{
    return ratio(ci.dt, ci.n, ncb.nin, ci.ntypes, ci.ht);
}

DCELL ratio2(void)
{
    return ratio(ci.ds, ci.n, ncb.nin, ci.nsizebins, ci.hs);
}

DCELL ratio3(void)
{
    return ratio(ci.dts, ci.n, ncb.nin, ci.dts_size, ci.hts);
}
