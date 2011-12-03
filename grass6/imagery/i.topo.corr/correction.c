/* File: correction.c
 *
 *  AUTHOR:    E. Jorge Tizado, Spain 2010
 *
 *  COPYRIGHT: (c) 2007-10 E. Jorge Tizado
 *             This program is free software under the GNU General Public
 *             License (>=v2). Read the file COPYING that comes with GRASS
 *             for details.
 */

#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <unistd.h>
#include <grass/gis.h>
#include <grass/glocale.h>

#include "local_proto.h"

void eval_tcor(int method, Gfile * out, Gfile * cosi, Gfile * band,
	       double zenith)
{
    int row, col, nrows, ncols;
    void *pref, *pcos;

    double cos_z, cos_i, ref_i;
    double n, sx, sxx, sy, sxy, tx, ty;
    double a, m, cka, ckb, kk;


    nrows = G_window_rows();
    ncols = G_window_cols();

    cos_z = cos(D2R * zenith);

    /* Calculating regression */
    if (method > NON_LAMBERTIAN) {
	n = sx = sxx = sy = sxy = 0.;
	for (row = 0; row < nrows; row++) {
	    G_percent(row, nrows, 2);

	    G_get_raster_row(band->fd, band->rast, row, DCELL_TYPE);
	    G_get_raster_row(cosi->fd, cosi->rast, row, cosi->type);

	    for (col = 0; col < ncols; col++) {
		switch (cosi->type) {
		case FCELL_TYPE:
		    pcos = (void *)((FCELL *) cosi->rast + col);
		    cos_i = (double)((FCELL *) cosi->rast)[col];
		    break;
		case DCELL_TYPE:
		    pcos = (void *)((DCELL *) cosi->rast + col);
		    cos_i = (double)((DCELL *) cosi->rast)[col];
		    break;
		default:
		    pcos = NULL;
		    cos_i = 0.;
		    break;
		}
		pref = (void *)((DCELL *) band->rast + col);

		if (!G_is_null_value(pref, DCELL_TYPE) &&
		    !G_is_null_value(pcos, cosi->type)) {
		    ref_i = (double)*((DCELL *) pref);
		    switch (method) {
		    case MINNAERT:
			if (cos_i > 0. && cos_z > 0. && ref_i > 0.) {
			    n++;
                            /* tx = log(cos_i / cos_z) */
                            /* cos_z is constant then m not changes */
                            tx = log(cos_i);
			    ty = log(ref_i);
			    sx += tx;
			    sxx += tx * tx;
			    sy += ty;
			    sxy += tx * ty;
			}
			break;
		    case C_CORRECT:
			{
			    n++;
			    sx += cos_i;
			    sxx += cos_i * cos_i;
			    sy += ref_i;
			    sxy += cos_i * ref_i;
			}
			break;
		    }
		}
	    }
	}
	m = (n == 0.) ? 1. : (n * sxy - sx * sy) / (n * sxx - sx * sx);
	a = (n == 0.) ? 0. : (sy - m * sx) / n;
    }
    /* Calculating Constants */
    switch (method) {
    case MINNAERT:
	cka = ckb = 0.;
	kk = m;
	G_message("Minnaert constant = %lf", kk);
	break;
    case C_CORRECT:
	cka = ckb = a / m; /* Richter changes to m/a */
	kk = 1.;
	G_message("C-factor constant = %lf (a=%.4f; m=%.4f)", cka, a, m);
	break;
    case PERCENT:
	cka = 2. - cos_z;
	ckb = 1.;
	kk = 1.;
	break;
    default:			/* COSINE */
	cka = ckb = 0.;
	kk = 1.;
    }
    /* Topographic correction */
    for (row = 0; row < nrows; row++) {
	G_percent(row, nrows, 2);

	G_get_raster_row(band->fd, band->rast, row, band->type);
	G_get_raster_row(cosi->fd, cosi->rast, row, cosi->type);

	for (col = 0; col < ncols; col++) {
	    switch (cosi->type) {
	    case FCELL_TYPE:
		pcos = (void *)((FCELL *) cosi->rast + col);
		cos_i = (double)*((FCELL *) pcos);
		break;
	    case DCELL_TYPE:
		pcos = (void *)((DCELL *) cosi->rast + col);
		cos_i = (double)*((DCELL *) pcos);
		break;
	    default:
		pcos = NULL;
		cos_i = 0.;
		break;
	    }
	    pref = (void *)((DCELL *) band->rast + col);

	    if (pcos == NULL ||
		G_is_null_value(pref, DCELL_TYPE) ||
		G_is_null_value(pcos, cosi->type)) {
		G_set_null_value((DCELL *) out->rast + col, 1, DCELL_TYPE);
	    }
	    else {
		ref_i = (double)*((DCELL *) pref);
		((DCELL *) out->rast)[col] =
		    (DCELL) (ref_i * pow((cos_z + cka) / (cos_i + ckb), kk));
		G_debug(3,
			"Old val: %f, cka: %f, cos_i: %f, ckb: %f, kk: %f, New val: %f",
			ref_i, cka, cos_i, ckb, kk,
			((DCELL *) out->rast)[col]);
	    }
	}
	G_put_raster_row(out->fd, out->rast, out->type);
    }
}
