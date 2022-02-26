#include <math.h>
#include <grass/gis.h>
#include <grass/raster.h>
#include "ncb.h"
#include "window.h"

/* Gini index = 1 - Simpson
 * 
 * dist: array of distributions
 * nd: number of cells in each distribution
 * n: number of distributions
 * dsize: distributions' size */

DCELL gini(double **dist, int *nd, int n, int dsize)
{
    int i, d, n_comb;
    double p, p_avg, gini, gini_avg, *gini_d;

    gini_d = G_malloc(n * sizeof(double));
    gini = 0;
    gini_avg = 0;
    n_comb = 0;
    for (d = 0; d < n; d++) {
	n_comb += nd[d];
	gini_d[d] = 1;
    }
    for (i = 0; i < dsize; i++) {

	/* combined distribution */
	p_avg = 0;
	for (d = 0; d < n; d++) {
	    if (dist[d][i] > 0 && nd[d] > 0) {
		p_avg += dist[d][i];
		p = dist[d][i] / nd[d];
		gini_d[d] -= p * p;
	    }
	}
	
	/* gini of combined distribution */
	if (p_avg > 0) {
	    p_avg /= n_comb;
	    gini -= p_avg * p_avg;

	}
    }
    /* average gini of single distributions */
    gini_avg = 0;
    for (d = 0; d < n; d++) {
	gini_avg += ((double) nd[d] / n_comb) * gini_d[d];
    }
    G_free(gini_d);

    if (gini == 0)
	return 0;

    return gini - gini_avg;

    /* Gini ratio: the max decrease is (n - 1) / n */
    return gini_avg * n / (n - 1);
}

DCELL gini1(void)
{
    return gini(ci.dt, ci.n, ncb.nin, ci.ntypes);
}

DCELL gini2(void)
{
    return gini(ci.ds, ci.n, ncb.nin, ci.nsizebins);
}

DCELL gini3(void)
{
    return gini(ci.dts, ci.n, ncb.nin, ci.dts_size);
}
