#include <math.h>
#include <string.h>
#include <grass/gis.h>
#include <grass/glocale.h>
#include <grass/gmath.h>

/* bandwidth bw
 * each cell within bw (distance from center <= bw)
 * gets a weight > 0 */

static double vf = -0.5;

double (*w_fn)(double, double);

double epanechnikov(double d2, double bw)
{
    double bw2, bw2d, w;

    bw2 = (bw + 1);
    bw2d = bw * bw;

    w = 0;

    if (d2 <= bw2d) {
        w = 1 - d2 / bw2;
    }

    return w;
}

double bisquare(double d2, double bw)
{
    double bw2, bw2d, w, t;

    bw2 = (bw + 1) * (bw + 1);
    bw2d = bw * bw;

    w = 0;

    if (d2 <= bw2d) {
        t = 1 - d2 / bw2;
        w = t * t;
    }

    return w;
}

double tricubic(double d2, double bw)
{
    double bw3, bw3d, w, d3, t;

    bw3 = (bw + 1) * (bw + 1) * (bw + 1);
    bw3d = bw * bw * bw;

    d3 = sqrt(d2);
    d3 = d3 * d3 * d3;
    w = 0;

    if (d3 <= bw3d) {
        t = 1 - d3 / bw3;
        w = t * t * t;
    }

    return w;
}

double gauss(double d2, double bw)
{
    double bw2, w;

    bw2 = bw * bw;

    /* Gaussian function: exp(-x^2 / ( 2 * variance) */

    w = 0;

    if (d2 <= bw2) {
        w = exp(vf * d2 / bw2);
    }

    return w;
}

/* set weighing kernel function and variance factor */
void set_wfn(char *name, int vfu)
{
    vf = vfu / -2.;

    if (*name == 'g')
        w_fn = gauss;
    else if (*name == 'e')
        w_fn = epanechnikov;
    else if (*name == 'b')
        w_fn = bisquare;
    else if (*name == 't')
        w_fn = tricubic;
    else
        G_fatal_error(_("Invalid kernel option '%s'"), name);
}

double **calc_weights(int bw)
{
    int r, c, count;
    double d2, **w;

    w = G_alloc_matrix(bw * 2 + 1, bw * 2 + 1);

    count = 0;
    for (r = -bw; r <= bw; r++) {
        for (c = -bw; c <= bw; c++) {
            d2 = r * r + c * c;
            w[r + bw][c + bw] = w_fn(d2, bw);
            if (w[r + bw][c + bw] > 0)
                count++;
        }
    }
    G_verbose_message(_("%d cells for bandwidth %d"), count, bw);

    return w;
}
