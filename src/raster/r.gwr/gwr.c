#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>
#include <grass/gis.h>
#include <grass/glocale.h>
#include <grass/raster.h>
#include "local_proto.h"
#include "gwr.h"

/* geographically weighted regression:
 * estimate coefficients for given cell */

int solvemat(struct MATRIX *m, double a[], double B[])
{
    int i, j, i2, j2, imark;
    double factor, temp, *tempp;
    double pivot; /* ACTUAL VALUE OF THE LARGEST PIVOT CANDIDATE */

    for (i = 0; i < m->n; i++) {
        j = i;

        /* find row with largest magnitude value for pivot value */

        pivot = M(m, i, j);
        imark = i;
        for (i2 = i + 1; i2 < m->n; i2++) {
            temp = fabs(M(m, i2, j));
            if (temp > fabs(pivot)) {
                pivot = M(m, i2, j);
                imark = i2;
            }
        }

        /* if the pivot is very small then the points are nearly co-linear */
        /* co-linear points result in an undefined matrix, and nearly */
        /* co-linear points results in a solution with rounding error */

        if (fabs(pivot) < GRASS_EPSILON) {
            G_debug(1, "Matrix is unsolvable");
            return 0;
        }

        /* if row with highest pivot is not the current row, switch them */

        if (imark != i) {
            /*
            for (j2 = 0; j2 < m->n; j2++) {
                temp = M(m, imark, j2);
                M(m, imark, j2) = M(m, i, j2);
                M(m, i, j2) = temp;
            }
            */
            tempp = m->v[imark];
            m->v[imark] = m->v[i];
            m->v[i] = tempp;

            temp = a[imark];
            a[imark] = a[i];
            a[i] = temp;
        }

        /* compute zeros above and below the pivot, and compute
           values for the rest of the row as well */

        for (i2 = 0; i2 < m->n; i2++) {
            if (i2 != i) {
                factor = M(m, i2, j) / pivot;
                for (j2 = j; j2 < m->n; j2++)
                    M(m, i2, j2) -= factor * M(m, i, j2);
                a[i2] -= factor * a[i];
            }
        }
    }

    /* SINCE ALL OTHER VALUES IN THE MATRIX ARE ZERO NOW, CALCULATE THE
       COEFFICIENTS BY DIVIDING THE COLUMN VECTORS BY THE DIAGONAL VALUES. */

    for (i = 0; i < m->n; i++) {
        B[i] = a[i] / M(m, i, i);
    }

    return 1;
}

int gwr(struct rb *xbuf, int ninx, struct rb *ybuf, int cc, int bw, double **w,
        DCELL *est, double **B0)
{
    int r, c;
    int i, j, k;
    int nsize;
    static DCELL *xval = NULL;
    DCELL yval;
    int count, isnull, solved;
    /* OLS */
    static double **a = NULL;
    static double **B = NULL;
    static struct MATRIX *m_all = NULL;
    struct MATRIX *m;

    if (!xval) {
        xval = G_malloc((ninx + 1) * sizeof(DCELL));
        xval[0] = 1.;
    }

    if (!m_all) {
        m_all = (struct MATRIX *)G_malloc((ninx + 1) * sizeof(struct MATRIX));
        a = (double **)G_malloc((ninx + 1) * sizeof(double *));
        B = (double **)G_malloc((ninx + 1) * sizeof(double *));

        m = &(m_all[0]);
        m->n = ninx + 1;
        m->v = (double **)G_malloc(m->n * sizeof(double));
        m->v[0] = (double *)G_malloc(m->n * m->n * sizeof(double));
        for (i = 1; i < m->n; i++) {
            m->v[i] = m->v[i - 1] + m->n;
        }

        a[0] = (double *)G_malloc(m->n * sizeof(double));
        B[0] = (double *)G_malloc(m->n * sizeof(double));

        for (k = 1; k <= ninx; k++) {
            m = &(m_all[k]);
            m->n = ninx;
            m->v = (double **)G_malloc(m->n * sizeof(double *));
            m->v[0] = (double *)G_malloc(m->n * m->n * sizeof(double));
            for (i = 1; i < m->n; i++) {
                m->v[i] = m->v[i - 1] + m->n;
            }
            a[k] = (double *)G_malloc(m->n * sizeof(double));
            B[k] = (double *)G_malloc(m->n * sizeof(double));
        }
    }

    for (k = 0; k <= ninx; k++) {
        m = &(m_all[k]);
        for (i = 0; i < m->n; i++) {
            for (j = i; j < m->n; j++)
                M(m, i, j) = 0.0;
            a[k][i] = 0.0;
            B[k][i] = 0.0;
        }
    }

    Rast_set_d_null_value(est, ninx + 1);
    if (B0)
        *B0 = NULL;

    nsize = bw * 2 + 1;

    /* first pass: collect values */
    count = 0;
    for (r = 0; r < nsize; r++) {

        for (c = 0; c < nsize; c++) {

            if (w[r][c] == 0)
                continue;

            isnull = 0;
            for (i = 0; i < ninx; i++) {
                xval[i + 1] = xbuf[i].buf[r][c + cc];
                if (Rast_is_d_null_value(&(xval[i + 1]))) {
                    isnull = 1;
                    break;
                }
            }
            if (isnull)
                continue;

            yval = ybuf->buf[r][c + cc];
            if (Rast_is_d_null_value(&yval))
                continue;

            for (i = 0; i <= ninx; i++) {
                double val1 = xval[i];

                for (j = i; j <= ninx; j++) {
                    double val2 = xval[j];

                    m = &(m_all[0]);
                    M(m, i, j) += val1 * val2 * w[r][c];

                    /* linear model without predictor k */
                    for (k = 1; k <= ninx; k++) {
                        if (k != i && k != j) {
                            int i2 = k > i ? i : i - 1;
                            int j2 = k > j ? j : j - 1;

                            m = &(m_all[k]);
                            M(m, i2, j2) += val1 * val2 * w[r][c];
                        }
                    }
                }

                a[0][i] += yval * val1 * w[r][c];
                for (k = 1; k <= ninx; k++) {
                    if (k != i) {
                        int i2 = k > i ? i : i - 1;

                        a[k][i2] += yval * val1 * w[r][c];
                    }
                }
            }
            count++;
        }
    }

    if (count < ninx + 1) {
        G_verbose_message(_("Unable to determine coefficients. Consider "
                            "increasing the bandwidth."));
        return 0;
    }

    /* estimate coefficients */
    solved = ninx + 1;
    for (k = 0; k <= ninx; k++) {
        m = &(m_all[k]);

        /* TRANSPOSE VALUES IN UPPER HALF OF M TO OTHER HALF */
        for (i = 1; i < m->n; i++)
            for (j = 0; j < i; j++)
                M(m, i, j) = M(m, j, i);

        if (!solvemat(m, a[k], B[k])) {
            /*
            for (i = 0; i <= ninx; i++) {
                fprintf(stdout, "b%d=0.0\n", i);
            }
            */
            G_debug(1, "Solving matrix %d failed", k);
            solved--;
        }
    }
    if (solved < ninx + 1) {
        G_debug(3, "%d of %d equation systems could not be solved",
                ninx + 1 - solved, ninx + 1);
        return 0;
    }

    /* second pass: calculate estimates */
    isnull = 0;
    for (i = 0; i < ninx; i++) {

        xval[i + 1] = xbuf[i].buf[bw][cc + bw];
        if (Rast_is_d_null_value(&(xval[i + 1]))) {
            isnull = 1;
            break;
        }
    }
    if (isnull)
        return 0;

    est[0] = 0.0;
    for (k = 0; k <= ninx; k++) {
        est[0] += B[0][k] * xval[k];

        if (k > 0) {
            est[k] = 0.0;

            /* linear model without predictor k */
            for (i = 0; i <= ninx; i++) {
                if (i != k) {
                    j = k > i ? i : i - 1;
                    est[k] += B[k][j] * xval[i];
                }
            }
        }
    }
    if (B0)
        *B0 = B[0];

    return count;
}
