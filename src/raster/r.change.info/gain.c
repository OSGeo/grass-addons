#include <math.h>
#include <grass/gis.h>
#include <grass/raster.h>
#include "ncb.h"
#include "window.h"

/* information gain = amount of change
 * gain1: gain for patch type frequencies
 * gain2: gain for clump size class frequencies
 * gain3: gain for patch type x clump size class frequencies
 * pc: proportion of changes =
 *     number of transitions / ( n unmasked cells x n inputs ) */

/* gain for any number of equally sized distributions using log2
 * thus the upper bound is log2(n)
 * dist: array of distributions
 * nd: number of cells in each distribution
 * n: number of distributions
 * dsize: distributions' size
 * h: entropy for each distribution */
DCELL gain(double **dist, int *nd, int n, int dsize, double *h)
{
    int i, d, n_comb;
    double p, pe, p_comb, H_comb, H_avg;

    H_comb = 0;
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
    for (d = 0; d < n; d++) {
        H_avg += entropy(h[d]) * nd[d];
    }
    H_avg /= n_comb;
    H_comb = entropy(H_comb);

    if (H_comb < 0)
        H_comb = 0;
    if (H_avg < 0)
        H_avg = 0;

    if (H_comb < H_avg)
        return 0;

    if (H_comb == 0)
        return 0;

    return (H_comb - H_avg);
}

DCELL pc(void)
{
    /* proportion of changes
     * theoretical max: ncb.n * (ncb.nin - 1) */
    return (double)ci.nchanges / (ncb.n * (ncb.nin - 1));
}

DCELL gain1(void)
{
    return gain(ci.dt, ci.n, ncb.nin, ci.ntypes, ci.ht);
}

DCELL gain2(void)
{
    return gain(ci.ds, ci.n, ncb.nin, ci.nsizebins, ci.hs);
}

DCELL gain3(void)
{
    return gain(ci.dts, ci.n, ncb.nin, ci.dts_size, ci.hts);
}
