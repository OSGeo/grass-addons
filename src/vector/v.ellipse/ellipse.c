#include <math.h>

#include <grass/vector.h>
#include <grass/gmath.h>
#include <grass/glocale.h>

#include "proto.h"

void create_ellipse(struct Parameters *par, struct line_pnts *Ellipse,
                    struct line_cats *Cats, double stepsize)
{
    Vect_reset_line(Ellipse);

    /* angle */
    double t = 0;

    /* number of points */
    if (stepsize < 0.01) /* too small step */
        stepsize = 0.01;
    int n = 360.0 / stepsize;

    /* compute n points on ellipse */
    double *x;
    double *y;

    x = (double *)G_malloc((n + 1) * sizeof(double));
    y = (double *)G_malloc((n + 1) * sizeof(double));

    int i;

    for (i = 0; i < n; i++) {
        x[i] = par->a * cos(t) * cos(par->angle) -
               par->b * sin(t) * sin(par->angle) +
               par->xc; /* parametric equations of an ellipse (non-tilted) */
        y[i] = par->a * cos(t) * sin(par->angle) +
               par->b * sin(t) * cos(par->angle) + par->yc;
        Vect_cat_set(Cats, 1, i);
        t += 2 * M_PI / n;
    }

    x[n] = x[0];
    y[n] = y[0];
    Vect_cat_set(Cats, 1, n);

    Vect_copy_xyz_to_pnts(Ellipse, x, y, 0, n + 1);

    G_free(x);
    G_free(y);
}

int fitting_ellipse(struct line_pnts *Points, struct Parameters *pars)
{
    /* variables */
    int i, j, k, n;
    double meanx, meany;
    double *x, *y, *nn;
    double **AA, **NN;
    int singular;

    /* LSM for conic representation of an ellipse */
    /* a*x^2 + b*x*y + c*y^2 + d*x + e*y = f */

    /* allocate memory */
    n = Points->n_points;
    x = G_alloc_vector(n); /* x-coordinates */
    y = G_alloc_vector(n); /* y-coordinates */
    AA =
        G_alloc_matrix(n, 5); /* design matrix [x.^2, y.^2, x.*y, y.^2, x, y] */
    NN = G_alloc_matrix(5, 5); /* N = A'*A */
    nn = G_alloc_vector(5);    /* n = A'*l, vector of unknown
                                * parameters of conic representation of
                                * ellipse [a, b, c, d, e] */

    /* remove bias of the ellipse (to be more accurate for inversion) */
    /* compute mean */
    meanx = 0;
    meany = 0;
    /* TODO: do this more effective */
    for (i = 0; i < n; i++) {
        meanx += Points->x[i] / n;
        meany += Points->y[i] / n;
    }
    /* change coordinates */
    for (i = 0; i < n; i++) {
        x[i] = Points->x[i] - meanx;
        y[i] = Points->y[i] - meany;
    }

    /* compute design matrix */
    for (i = 0; i < n; i++) {
        AA[i][0] = x[i] * x[i];
        AA[i][1] = x[i] * y[i];
        AA[i][2] = y[i] * y[i];
        AA[i][3] = x[i];
        AA[i][4] = y[i];
    }

    /* compute N=A'*A */
    /* TODO: use fn - mat_struct *G_matrix_product (mat_struct *mt1, mat_struct
     * *mt2) */
    for (i = 0; i < 5; i++) {
        for (j = 0; j < 5; j++) {
            NN[i][j] = 0;

            if (i > j) {
                NN[i][j] = NN[j][i]; // matrix is symmetric
            }
            else {
                for (k = 0; k < n; k++) {
                    NN[i][j] += AA[k][i] * AA[k][j];
                }
            }
        }
    }

    /* compute n = A'*l (as column sum) */
    for (i = 0; i < 5; i++) {
        nn[i] = 0;
        for (k = 0; k < n; k++) {
            nn[i] += AA[k][i];
        }
    }

    /* solve x = N^(-1)*n */
    singular = G_math_solv(NN, nn, 5); /* TODO: ensure use of the most effective
                                          method from G_math_sol... */

    /* free memory */
    G_free_vector(x);
    G_free_vector(y);
    G_free_matrix(AA);
    G_free_matrix(NN);

    if (singular == -1) {
        G_free_vector(nn);
        G_warning(_("Singular matrix failure"));
        return 0;
    }

    /* extract parameters of ellipse from conic representation */

    double a, b, c, d, e, f;
    double test, tol, cos_phi, sin_phi, x0, y0, sqrta,
        sqrtb; /*, sqrta, sqrtb; */

    tol = 1e-3;

    /* parameters of conic representation */
    a = nn[0];
    b = nn[1];
    c = nn[2];
    d = nn[3];
    e = nn[4];
    /* f = -1; */

    G_free_vector(nn);

    /* check if it is an ellipse */
    test = a * c;
    if (test == 0) {
        G_warning(_("Parabola found. Exiting."));
        return 0;
    }
    else if (test < 0) {
        G_warning(_("Hyperbola found. Exiting."));
        return 0;
    }

    /* orientation (and its removing for further computing) */
    if ((abs(b / a) > tol) && (abs(b / c) > tol)) {
        pars->angle = 0.5 * atan2(b, (c - a));
        cos_phi = cos(pars->angle);
        sin_phi = sin(pars->angle);
        a = a * cos_phi * cos_phi - b * cos_phi * sin_phi +
            c * sin_phi * sin_phi;
        b = 0;
        c = a * sin_phi * sin_phi - b * cos_phi * sin_phi +
            c * cos_phi * cos_phi;
        d = d * cos_phi - e * sin_phi;
        e = d * sin_phi + e * cos_phi;
    }
    else {
        pars->angle = 0;
        cos_phi = 1;
        sin_phi = 0;
    }

    /* make sure coefficients are positive */
    if (a < 0) {
        a *= -1;
        b *= -1;
        c *= -1;
        d *= -1;
        e *= -1;
    }

    /* center of non-tilted ellipse */
    x0 = meanx - d / 2 / a;
    y0 = meany - e / 2 / c;
    /* center of tilted ellipse */
    pars->xc = cos_phi * x0 + sin_phi * y0;
    pars->yc = cos_phi * y0 - sin_phi * x0;

    /* semi-axis */
    f = 1 + d * d / 4 / a + e * e / 4 / c;
    sqrta = sqrt(f / a);
    sqrtb = sqrt(f / c);
    if (sqrta > sqrtb) {
        pars->a = sqrta;
        pars->b = sqrtb;
    }
    else {
        pars->b = sqrta;
        pars->a = sqrtb;
    }

    G_verbose_message("%s: %f*x^2+%f*x*y+%f*y^2+%f*x+%f*y-1=0",
                      _("conic representation"), a, b, c, d, e);
    G_verbose_message("parameters of ellipse:\na = %f \nb = %f \nangle = %f \n"
                      "xc = %f \nyc = %f",
                      pars->a, pars->b, pars->angle, pars->xc, pars->yc);

    return 1;
}
