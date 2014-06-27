#include <math.h>
#include <string.h>
#include <grass/gis.h>
#include <grass/glocale.h>
#include <grass/gmath.h>

/* bandwidth bw
 * each cell within bw (distance from center <= bw)
 * gets a weight > 0 */

static double vf = 2;

double ** (*w_fn) (int);

double **epanechnikov(int bw)
{
    int r, c;
    double bw2, bw2d, d, **w;

    w = G_alloc_matrix(bw * 2 + 1, bw * 2 + 1);
    bw2 = (bw + 1) * (bw + 1);
    bw2d = bw * bw;
    
    for (r = -bw; r <= bw; r++) {
	for (c = -bw; c <= bw; c++) {
	    d = r * r + c * c;
	    w[r + bw][c + bw] = 0;

	    if (d <= bw2d) {
		w[r + bw][c + bw] = 1 - d / bw2;
	    }
	}
    }
    
    return w;
}

double **quartic(int bw)
{
    int r, c;
    double bw2, bw2d, d, **w, t;

    w = G_alloc_matrix(bw * 2 + 1, bw * 2 + 1);
    bw2 = (bw + 1) * (bw + 1);
    bw2d = bw * bw;
    
    for (r = -bw; r <= bw; r++) {
	for (c = -bw; c <= bw; c++) {
	    d = r * r + c * c;
	    w[r + bw][c + bw] = 0;

	    if (d <= bw2d) {
		t = 1 - d / bw2;
		w[r + bw][c + bw] = t * t;
	    }
	}
    }
    
    return w;
}

double **tricubic(int bw)
{
    int r, c;
    double bw3, bw3d, d, **w, t;

    w = G_alloc_matrix(bw * 2 + 1, bw * 2 + 1);
    bw3 = (bw + 1) * (bw + 1) * (bw + 1);
    bw3d = bw * bw * bw;
    
    for (r = -bw; r <= bw; r++) {
	for (c = -bw; c <= bw; c++) {
	    d = sqrt(r * r + c * c);
	    d = d * d * d;
	    w[r + bw][c + bw] = 0;

	    if (d <= bw3d) {
		t = 1 - d / bw3;
		w[r + bw][c + bw] = t * t * t;
	    }
	}
    }
    
    return w;
}

double **gauss(int bw)
{
    int r, c;
    double bw2, d, **w;

    w = G_alloc_matrix(bw * 2 + 1, bw * 2 + 1);
    bw2 = bw * bw;

    /* Gaussian function: exp(-x^2 / ( 2 * variance) */

    for (r = -bw; r <= bw; r++) {
	for (c = -bw; c <= bw; c++) {
	    d = r * r + c * c;
	    w[r + bw][c + bw] = 0;

	    if (d <= bw2) {
		w[r + bw][c + bw] = exp(vf * d / bw2);
		w[r + bw][c + bw] = 1;
	    }
	}
    }
    
    return w;
}

/* set weighing kernel function and variance factor */
void set_wfn(char *name, int vfu)
{
    vf = vfu / 2.;

    if (*name == 'g')
	w_fn = gauss;
    else if (*name == 'e')
	w_fn = epanechnikov;
    else if (*name == 'q')
	w_fn = quartic;
    else if (*name == 't')
	w_fn = tricubic;
    else
	G_fatal_error(_("Invalid kernel option '%s'"), name);
}
