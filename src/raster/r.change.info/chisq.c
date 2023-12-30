#include <math.h>
#include <grass/gis.h>
#include <grass/raster.h>
#include "ncb.h"
#include "window.h"

/* CHI-square statistics to assess the relevance of an attribute
 * from Quinlain 1986
 * expected frequency for each dist bin and year:
 *   pexp[i] = p * (ncells[i] / ncellstot)
 *   then
 *   sum of all (p[i] - pexp[i])^2 / pexp[i]
 *
 * dist: array of distributions
 * nd: number of cells in each distribution
 * n: number of distributions
 * dsize: distributions' size */

DCELL chisq(double **dist, int *nd, int n, int dsize)
{
    int i, d, n_comb;
    double p_sum, p_exp, result;

    result = 0;
    n_comb = 0;
    for (d = 0; d < n; d++) {
        n_comb += nd[d];
    }
    for (i = 0; i < dsize; i++) {

        /* create combined distribution */
        p_sum = 0;
        for (d = 0; d < n; d++) {
            if (dist[d][i] > 0 && nd[d] > 0) {
                p_sum += dist[d][i];
            }
        }
        /* squared and normalized difference to combined distribution */
        if (p_sum > 0) {
            for (d = 0; d < n; d++) {
                if (nd[d] > 0) {
                    p_exp = p_sum * nd[d] / n_comb;
                    result +=
                        (dist[d][i] - p_exp) * (dist[d][i] - p_exp) / p_exp;
                }
            }
        }
    }

    return result;
}

DCELL chisq1(void)
{
    return chisq(ci.dt, ci.n, ncb.nin, ci.ntypes);
}

DCELL chisq2(void)
{
    return chisq(ci.ds, ci.n, ncb.nin, ci.nsizebins);
}

DCELL chisq3(void)
{
    return chisq(ci.dts, ci.n, ncb.nin, ci.dts_size);
}
