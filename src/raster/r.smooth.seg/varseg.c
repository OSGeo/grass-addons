/****************************************************************************
 *
 * LIBRARY:      varseg
 *
 * AUTHOR:       Alfonso Vitti <alfonso.vitti ing.unitn.it>
 *
 * PURPOSE:      Implements the Mumford-Shah (MS) variational model for image
 *               segmentation.
 *               The Mumford-Shah variational model with cirvature term (MSK)
 *               is also implemented.
 *
 *               The models generate a piece-wise smooth approximation of the
 *               input image and an image of the discontinuities (edges)
 *               of the output approximation.
 *               The discontinuities of the output approximation are preserved
 *               from being smoothed.
 *
 * REFERENCE:    http://www.ing.unitn.it/~vittia/phd/vitti_phd.pdf
 *
 * COPYRIGHT:    (C) 2007-2010
 *
 *               This program is free software under the GNU General Public
 *               License (>=v2).
 *
 *****************************************************************************/

#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include "varseg.h"

#define max(a, b) ((a) > (b) ? (a) : (b))

/* ========================================================================== */
/*!
 * \brief MS_N --- MUMFORD-SHAH (Gauss-Seidel method)
 *
 * Implements the Mumford-Shah variational model for image segmentation.
 *
 * A smooth approximation of the input image is produced.
 * The model explicitely detects the discontinuities of the output approximation
 * while preserving the discontinuities from being smoothed.
 *
 * A discontinuity image is also produced.
 * The values of the discontinuity image are close to 1 where the output
 * approximation is "homogeneous", where the output approximation has
 * discontinuities (edges) the values are close to 0.
 *
 *
 * \param[in] *g (double; pointer) - The input image
 *
 * \param[in] *u (double; pointer) - The output approximation
 *
 * \param[in] *z (double; pointer) - The output discontinuity map
 *
 * \param[in] lambda (double) - The scale factor parameter [positive]
 *
 * \param[in] kepsilon (double) - The discontinuities thickness [positive]
 *
 * \param[in] alpha (double) - The elasticity parameter [positive]
 *
 * \param[in] *mxdf (double; pointer) - The max difference in the approximation
 * between two iteration steps
 *
 * \param[in] nr (int) - The number of rows in the input image
 *
 * \param[in] nc (int) - The number of colums in the input image
 *
 * \return void [shold be changed to int for error handling]
 */

/** MS_N --- MUMFORD-SHAH (Gauss-Seidel method) **/
void ms_n(double *g, double *u, double *z, double lambda, double kepsilon,
          double alpha, double *mxdf, int nr, int nc)
{
    int i, j, jnc, nrc;
    double old_u;                          /* ms_n */
    double u_hat, z_star, z_tilde, ux, uy; /* ms */
    double num, den;
    double k2, k, h2, h = 1;

    nrc = nr * nc;
    h2 = h * h;
    k = kepsilon;
    k2 = kepsilon * kepsilon;

    /* Boundary conditions (Neumann) */

    /*** image corners ***/
    *u = *(u + nc + 1);                        /* ul corner */
    *(u + nc - 1) = *(u + 2 * nc - 2);         /* ur corner */
    *(u + nrc - nc) = *(u + nrc - 2 * nc + 1); /* ll corner */
    *(u + nrc - 1) = *(u + nrc - nc - 2);      /* lr corner */
    *z = *(z + nc + 1);                        /* ul corner */
    *(z + nc - 1) = *(z + 2 * nc - 2);         /* ur corner */
    *(z + nrc - nc) = *(z + nrc - 2 * nc + 1); /* ll corner */
    *(z + nrc - 1) = *(z + nrc - nc - 2);      /* lr corner */

    /* this is an alternative for the corners using the mean value of the x and
     * y closest points *u = 0.5 * ( *(u+1) + *(u+nc) );
     * *(u+nc-1) = 0.5 * ( *(u+nc-2) + *(u+2*nc-1) );
     * *(u+nrc-nc) = 0.5 * ( *(u+nrc-nc+1) + *(u+nrc-2*nc) );
     * *(u+nrc-1) = 0.5 * ( *(u+nrc-2) +*(u+nrc-nc-1) );
     * *z = 0.5 * ( *(z+1) + *(z+nc) );
     * *(z+nc-1) = 0.5 * ( *(z+nc-2) + *(z+2*nc-1) );
     * *(z+nrc-nc) = 0.5 * ( *(z+nrc-nc+1) + *(z+nrc-2*nc) );
     * *(z+nrc-1) = 0.5 * ( *(z+nrc-2) +*(z+nrc-nc-1) );
     */

    /*** image edges ***/
    for (i = 1; i < nc - 1; i++) { /* top and bottom edges */
        *(u + i) = *(u + nc + i);  /* t edge */
        *(u + nrc - nc + i) = *(u + nrc - 2 * nc + i); /* b edge */
        *(z + i) = *(z + nc + i);                      /* t edge */
        *(z + nrc - nc + i) = *(z + nrc - 2 * nc + i); /* b edge */
    }
    for (j = 1; j < nr - 1; j++) { /* left and right edges */
        jnc = j * nc;
        *(u + jnc) = *(u + jnc + 1);               /* r edge */
        *(u + jnc + nc - 1) = *(u + jnc + nc - 2); /* l edge */
        *(z + jnc) = *(z + jnc + 1);               /* r edge */
        *(z + jnc + nc - 1) = *(z + jnc + nc - 2); /* l edge */
    }

    for (j = 1; j < nr - 1; j++) {
        jnc = j * nc;
        for (i = 1; i < nc - 1; i++) {
            old_u = *(u + jnc + i);
            /*
             *                      x_i+1,j --> *(x+jnc+i+1)
             *                      x_i-1,j --> *(x+jnc+i-1)
             *                      x_i,j+1 --> *(x+jnc+nc+i)
             *                      x_i,j-1 --> *(x+jnc-nc+i)
             */
            u_hat =
                *(z + jnc + i + 1) * *(z + jnc + i + 1) * *(u + jnc + i + 1) +
                *(z + jnc + i - 1) * *(z + jnc + i - 1) * *(u + jnc + i - 1) +
                *(z + jnc + nc + i) * *(z + jnc + nc + i) *
                    *(u + jnc + nc + i) +
                *(z + jnc - nc + i) * *(z + jnc - nc + i) * *(u + jnc - nc + i);
            z_star = *(z + jnc + i + 1) * *(z + jnc + i + 1) +
                     *(z + jnc + i - 1) * *(z + jnc + i - 1) +
                     *(z + jnc + nc + i) * *(z + jnc + nc + i) +
                     *(z + jnc - nc + i) * *(z + jnc - nc + i);

            num = lambda * u_hat + h2 * *(g + jnc + i);
            den = lambda * z_star + h2;

            *(u + jnc + i) = num / den;

            z_tilde = *(z + jnc + i + 1) + *(z + jnc + i - 1) +
                      *(z + jnc + nc + i) + *(z + jnc - nc + i);
            ux = *(u + jnc + i + 1) - *(u + jnc + i - 1);
            uy = *(u + jnc + nc + i) - *(u + jnc - nc + i);

            num = 4 * z_tilde + h2 * k2;
            den = 16 + h2 * k2 + lambda * k * (ux * ux + uy * uy) / alpha;

            *(z + jnc + i) = num / den;

            *mxdf = max(*mxdf, fabs(old_u - *(u + jnc + i)));
        }
    }
    return;
}

/* ========================================================================== */
/* ========================================================================== */

/* ========================================================================== */
/*!
 * \brief MSK_N --- MUMFORD-SHAH with CURVATURE term (Gauss-Seidel method)
 *
 * Implements the Mumford-Shah variational model with curvature term for image
 * segmentation.
 *
 * A smooth approximation of the input image is produced.
 * The model explicitely detects the discontinuities of the output approximation
 * while preserving the discontinuities from being smoothed.
 *
 * A discontinuity image is also produced.
 * The values of the discontinuity image are close to 1 where the output
 * approximation is "homogeneous", where the output approximation has
 * discontinuities (edges) the values are close to 0.
 *
 * The curvature term prevents the discontinuities from being shortened too much
 * when the parameter alpha is set to very high values.
 *
 *
 * \param[in] *g (double; pointer) - The input image
 *
 * \param[in] *u (double; pointer) - The output approximation
 *
 * \param[in] *z (double; pointer) - The output discontinuity map
 *
 * \param[in] lambda (double) - The scale factor parameter [positive]
 *
 * \param[in] kepsilon (double) - The discontinuities thickness [positive]
 *
 * \param[in] alpha (double) - The elasticity parameter [positive]
 *
 * \param[in] beta (double) - The rigidity parameter [positive]
 *
 * \param[in] *mxdf (double; pointer) - The max difference in the approximation
 * between two iteration steps
 *
 * \param[in] nr (int) - The number of rows in the input image
 *
 * \param[in] nc (int) - The number of colums in the input image
 *
 * \return void [shold be changed to int for error handling]
 */

/** MSK_N --- MUMFORD-SHAH WITH CURVATURE (Gauss-Seidel method) **/
void msk_n(double *g, double *u, double *z, double lambda, double kepsilon,
           double alpha, double beta, double *mxdf, int nr, int nc)
{
    int i, j, jnc, nrc;
    double old_u;                                            /* msk_n */
    double u_tilde, ux, uy, zx, zy, z_tilde, z_hat, z_check; /* msk */
    double a, b, c, d, e;                                    /* msk */
    double num, den;
    double k2, k, h2, h = 1;
    double ta;

    nrc = nr * nc;
    h2 = h * h;
    k = kepsilon;
    k2 = kepsilon * kepsilon;

    /* Remove first image boundary using BC values */
    *u = *(u + nc + 1);                        /* ul corner */
    *(u + nc - 1) = *(u + 2 * nc - 2);         /* ur corner */
    *(u + nrc - nc) = *(u + nrc - 2 * nc + 1); /* ll corner */
    *(u + nrc - 1) = *(u + nrc - nc - 2);      /* lr corner */
    *z = *(z + nc + 1);                        /* ul corner */
    *(z + nc - 1) = *(z + 2 * nc - 2);         /* ur corner */
    *(z + nrc - nc) = *(z + nrc - 2 * nc + 1); /* ll corner */
    *(z + nrc - 1) = *(z + nrc - nc - 2);      /* lr corner */
    for (i = 1; i < nc - 1; i++) {             /* top and bottom edges */
        *(u + i) = *(u + nc + i);              /* t edge */
        *(u + nrc - nc + i) = *(u + nrc - 2 * nc + i); /* b edge */
        *(z + i) = *(z + nc + i);                      /* t edge */
        *(z + nrc - nc + i) = *(z + nrc - 2 * nc + i); /* b edge */
    }
    for (j = 1; j < nr - 1; j++) { /* left and right edges */
        jnc = j * nc;
        *(u + jnc) = *(u + jnc + 1);               /* r edge */
        *(u + jnc + nc - 1) = *(u + jnc + nc - 2); /* l edge */
        *(z + jnc) = *(z + jnc + 1);               /* r edge */
        *(z + jnc + nc - 1) = *(z + jnc + nc - 2); /* l edge */
    }

    /* Boundary conditions (Neumann) */

    /*** image corners ***/
    *(u + nc + 1) = *(u + 2 * nc + 2);                 /* ul corner */
    *(u + 2 * nc - 2) = *(u + 3 * nc - 3);             /* ur corner */
    *(u + nrc - 2 * nc + 1) = *(u + nrc - 3 * nc + 2); /* ll corner */
    *(u + nrc - nc - 2) = *(u + nrc - 2 * nc - 3);     /* lr corner */
    *(z + nc + 1) = *(z + 2 * nc + 2);                 /* ul corner */
    *(z + 2 * nc - 2) = *(z + 3 * nc - 3);             /* ur corner */
    *(z + nrc - 2 * nc + 1) = *(z + nrc - 3 * nc + 2); /* ll corner */
    *(z + nrc - nc - 2) = *(z + nrc - 2 * nc - 3);     /* lr corner */

    /* this is an alternative for the corners using the mean value of the x and
     * y closest points
     * *(u+nc+1) = 0.5 * ( *(u+nc+1) + *(u+2*nc+1) );
     * *(u+2*nc-2) = 0.5 * ( *(u+2*nc-3) + *(u+3*nc-2) );
     * *(u+nrc-2*nc+1) = 0.5 * ( *(u+nrc-2*nc+2) + *(u+nrc-3*nc+1) );
     * *(u+nrc-nc-2) = 0.5 * ( *(u+nrc-nc-3) +*(u+nrc-2*nc-2) );
     * *z = 0.5 * ( *(z+nc+1) + *(z+2*nc+1) );
     * *(z+nc-1) = 0.5 * ( *(z+2*nc-3) + *(z+3*nc-2) );
     * *(z+nrc-nc) = 0.5 * ( *(z+nrc-2*nc+2) + *(z+nrc-3*nc+1) );
     * *(z+nrc-1) = 0.5 * ( *(z+nrc-nc-3) +*(z+nrc-2*nc-2) );
     */

    /*** image edges ***/
    for (i = 2; i < nc - 2; i++) {         /* top and bottom edges */
        *(u + nc + i) = *(u + 2 * nc + i); /* t edge */
        *(u + nrc - 2 * nc + i) = *(u + nrc - 3 * nc + i); /* b edge */
        *(z + nc + i) = *(z + 2 * nc + i);                 /* t edge */
        *(z + nrc - 2 * nc + i) = *(z + nrc - 3 * nc + i); /* b edge */
    }
    for (j = 2; j < nr - 2; j++) { /* left and right edges */
        jnc = j * nc;
        *(u + jnc + 1) = *(u + jnc + 2);           /* r edge */
        *(u + jnc + nc - 2) = *(u + jnc + nc - 3); /* l edge */
        *(z + jnc + 1) = *(z + jnc + 2);           /* r edge */
        *(z + jnc + nc - 2) = *(z + jnc + nc - 3); /* l edge */
    }

    for (j = 2; j < nr - 2; j++) {
        jnc = j * nc;
        for (i = 2; i < nc - 2; i++) {
            old_u = *(u + jnc + i);

            u_tilde = *(u + jnc + i + 1) + *(u + jnc + i - 1) +
                      *(u + jnc + nc + i) + *(u + jnc - nc + i);
            ux = *(u + jnc + i + 1) - *(u + jnc + i - 1);
            uy = *(u + jnc + nc + i) - *(u + jnc - nc + i);
            zx = *(z + jnc + i + 1) - *(z + jnc + i - 1);
            zy = *(z + jnc + nc + i) - *(z + jnc - nc + i);
            num = 0.5 * lambda * *(z + jnc + i) * (zx * ux + zy * uy) +
                  lambda * *(z + jnc + i) * *(z + jnc + i) * u_tilde +
                  h2 * *(g + jnc + i);
            den = 4 * lambda * *(z + jnc + i) * *(z + jnc + i) + h2;

            *(u + jnc + i) = num / den;

            z_tilde = *(z + jnc + i + 1) + *(z + jnc + i - 1) +
                      *(z + jnc + nc + i) + *(z + jnc - nc + i);
            z_hat = *(z + jnc + nc + i + 1) + *(z + jnc - nc + i + 1) +
                    *(z + jnc + nc + i - 1) + *(z + jnc - nc + i - 1);
            z_check = *(z + jnc + i + 2) + *(z + jnc + i - 2) +
                      *(z + jnc + 2 * nc + i) + *(z + jnc - 2 * nc + i);
            a = alpha * z_tilde + 4 * alpha * h2 * k2 * *(z + jnc + i) *
                                      *(z + jnc + i) * *(z + jnc + i);
            b = 4 * beta * (8 * z_tilde - 2 * z_hat - z_check) / h2;
            c = -16 * beta * k2 * (3 * *(z + jnc + i) * *(z + jnc + i) + 1) *
                (z_tilde - 4 * *(z + jnc + i));
            d = 64 * beta * k2 * *(z + jnc + i) *
                (3 * *(z + jnc + i) * *(z + jnc + i) - 1);
            e = 64 * beta * h2 * k2 * k2 * *(z + jnc + i) * *(z + jnc + i) *
                *(z + jnc + i) * (3 * *(z + jnc + i) * *(z + jnc + i) - 2);
            num = a + b + c + d + e;
            ta = a;

            a = 4 * alpha +
                2 * alpha * h2 * k2 *
                    (3 * *(z + jnc + i) * *(z + jnc + i) - 1) +
                0.25 * lambda * k * (ux * ux + uy * uy);
            b = 16 * beta * k2 * (h2 * k2 + 5 / (h2 * k2) - 4);
            c = -12 * beta * k2 * (zx * zx + zy * zy);
            d = -96 * beta * k2 * *(z + jnc + i) *
                (z_tilde - 4 * *(z + jnc + i));
            e = 192 * beta * k2 * *(z + jnc + i) * (1 - h2 * k2) +
                240 * beta * h2 * k2 * k2 * *(z + jnc + i) * *(z + jnc + i) *
                    *(z + jnc + i) * *(z + jnc + i);
            den = a + b + c + d + e;

            *(z + jnc + i) = num / den;

            *mxdf = max(*mxdf, fabs(old_u - *(u + jnc + i)));
        }
    }
    return;
}

/* ========================================================================== */
/* ========================================================================== */

/* ========================================================================== */
/*!
 * \brief MS_O --- MUMFORD-SHAH (Jacobi method)
 *
 * Implements the Mumford-Shah variational model for image segmentation.
 *
 * A smooth approximation of the input image is produced.
 * The model explicitely detects the discontinuities of the output approximation
 * while preserving the discontinuities from being smoothed.
 *
 * A discontinuity image is also produced.
 * The values of the discontinuity image are close to 1 where the output
 * approximation is "homogeneous", where the output approximation has
 * discontinuities (edges) the values are close to 0.
 *
 *
 * \param[in] *g (double; pointer) - The input image
 *
 * \param[in] *u (double; pointer) - The output approximation
 *
 * \param[in] *z (double; pointer) - The output discontinuity map
 *
 * \param[in] lambda (double) - The scale factor parameter [positive]
 *
 * \param[in] kepsilon (double) - The discontinuities thickness [positive]
 *
 * \param[in] alpha (double) - The elasticity parameter [positive]
 *
 * \param[in] *mxdf (double; pointer) - The max difference in the approximation
 * between two iteration steps
 *
 * \param[in] nr (int) - The number of rows in the input image
 *
 * \param[in] nc (int) - The number of colums in the input image
 *
 * \return void [shold be changed to int for error handling]
 */

/** MS_O --- MUMFORD-SHAH (Jacobi method) **/
void ms_o(double *g, double *u, double *z, double lambda, double kepsilon,
          double alpha, double *mxdf, int nr, int nc)
{
    int i, j, jnc, nrc;
    double *old_u, *old_z;                 /* ms_o */
    double u_hat, z_star, z_tilde, ux, uy; /* ms */
    double num, den;
    double k2, k, h2, h = 1;

    nrc = nr * nc;
    h2 = h * h;
    k = kepsilon;
    k2 = kepsilon * kepsilon;

    /* Boundary conditions (Neumann) */

    /*** image corners ***/
    *u = *(u + nc + 1);                        /* ul corner */
    *(u + nc - 1) = *(u + 2 * nc - 2);         /* ur corner */
    *(u + nrc - nc) = *(u + nrc - 2 * nc + 1); /* ll corner */
    *(u + nrc - 1) = *(u + nrc - nc - 2);      /* lr corner */
    *z = *(z + nc + 1);                        /* ul corner */
    *(z + nc - 1) = *(z + 2 * nc - 2);         /* ur corner */
    *(z + nrc - nc) = *(z + nrc - 2 * nc + 1); /* ll corner */
    *(z + nrc - 1) = *(z + nrc - nc - 2);      /* lr corner */

    /* this is an alternative for the corners using the mean value of the x and
     * y closest points *u = 0.5 * ( *(u+1) + *(u+nc) );
     * *(u+nc-1) = 0.5 * ( *(u+nc-2) + *(u+2*nc-1) );
     * *(u+nrc-nc) = 0.5 * ( *(u+nrc-nc+1) + *(u+nrc-2*nc) );
     * *(u+nrc-1) = 0.5 * ( *(u+nrc-2) +*(u+nrc-nc-1) );
     * *z = 0.5 * ( *(z+1) + *(z+nc) );
     * *(z+nc-1) = 0.5 * ( *(z+nc-2) + *(z+2*nc-1) );
     * *(z+nrc-nc) = 0.5 * ( *(z+nrc-nc+1) + *(z+nrc-2*nc) );
     * *(z+nrc-1) = 0.5 * ( *(z+nrc-2) +*(z+nrc-nc-1) );
     */

    /*** image edges ***/
    for (i = 1; i < nc - 1; i++) { /* top and bottom edges */
        *(u + i) = *(u + nc + i);  /* t edge */
        *(u + nrc - nc + i) = *(u + nrc - 2 * nc + i); /* b edge */
        *(z + i) = *(z + nc + i);                      /* t edge */
        *(z + nrc - nc + i) = *(z + nrc - 2 * nc + i); /* b edge */
    }
    for (j = 1; j < nr - 1; j++) { /* left and right edges */
        jnc = j * nc;
        *(u + jnc) = *(u + jnc + 1);               /* r edge */
        *(u + jnc + nc - 1) = *(u + jnc + nc - 2); /* l edge */
        *(z + jnc) = *(z + jnc + 1);               /* r edge */
        *(z + jnc + nc - 1) = *(z + jnc + nc - 2); /* l edge */
    }

    old_u = (double *)malloc(sizeof(double) * nrc);
    old_z = (double *)malloc(sizeof(double) * nrc);

    for (j = 0; j < nr; j++) {
        jnc = j * nc;
        for (i = 0; i < nc; i++) {
            *(old_u + jnc + i) = *(u + jnc + i);
            *(old_z + jnc + i) = *(z + jnc + i);
        }
    }

    for (j = 1; j < nr - 1; j++) {
        jnc = j * nc;
        for (i = 1; i < nc - 1; i++) {
            u_hat = *(old_z + jnc + i + 1) * *(old_z + jnc + i + 1) *
                        *(old_u + jnc + i + 1) +
                    *(old_z + jnc + i - 1) * *(old_z + jnc + i - 1) *
                        *(old_u + jnc + i - 1) +
                    *(old_z + jnc + nc + i) * *(old_z + jnc + nc + i) *
                        *(old_u + jnc + nc + i) +
                    *(old_z + jnc - nc + i) * *(old_z + jnc - nc + i) *
                        *(old_u + jnc - nc + i);
            z_star = *(old_z + jnc + i + 1) * *(old_z + jnc + i + 1) +
                     *(old_z + jnc + i - 1) * *(old_z + jnc + i - 1) +
                     *(old_z + jnc + nc + i) * *(old_z + jnc + nc + i) +
                     *(old_z + jnc - nc + i) * *(old_z + jnc - nc + i);

            num = lambda * u_hat + h2 * *(g + jnc + i);
            den = lambda * z_star + h2;

            *(u + jnc + i) = num / den;

            z_tilde = *(old_z + jnc + i + 1) + *(old_z + jnc + i - 1) +
                      *(old_z + jnc + nc + i) + *(old_z + jnc - nc + i);
            ux = *(old_u + jnc + i + 1) - *(old_u + jnc + i - 1);
            uy = *(old_u + jnc + nc + i) - *(old_u + jnc - nc + i);

            num = 4 * z_tilde + h2 * k2;
            den = 16 + h2 * k2 + lambda * k * (ux * ux + uy * uy) / alpha;

            *(z + jnc + i) = num / den;

            *mxdf = max(*mxdf, fabs(*(old_u + jnc + i) - *(u + jnc + i)));
        }
    }
    free(old_u);
    free(old_z);
    return;
}

/* ========================================================================== */
/* ========================================================================== */

/* ========================================================================== */
/*!
 * \brief MSK_O --- MUMFORD-SHAH with CURVATURE term (Jacobi method)
 *
 * Implements the Mumford-Shah variational model with curvature term for image
 * segmentation.
 *
 * A smooth approximation of the input image is produced.
 * The model explicitely detects the discontinuities of the output approximation
 * while preserving the discontinuities from being smoothed.
 *
 * A discontinuity image is also produced.
 * The values of the discontinuity image are close to 1 where the output
 * approximation is "homogeneous", where the output approximation has
 * discontinuities (edges) the values are close to 0.
 *
 * The curvature term prevents the discontinuities from being shortened too much
 * when the parameter alpha is set to very high values.
 *
 *
 * \param[in] *g (double; pointer) - The input image
 *
 * \param[in] *u (double; pointer) - The output approximation
 *
 * \param[in] *z (double; pointer) - The output discontinuity map
 *
 * \param[in] lambda (double) - The scale factor parameter [positive]
 *
 * \param[in] kepsilon (double) - The discontinuities thickness [positive]
 *
 * \param[in] alpha (double) - The elasticity parameter [positive]
 *
 * \param[in] beta (double) - The rigidity parameter [positive]
 *
 * \param[in] *mxdf (double; pointer) - The max difference in the approximation
 * between two iteration steps
 *
 * \param[in] nr (int) - The number of rows in the input image
 *
 * \param[in] nc (int) - The number of colums in the input image
 *
 * \return void [shold be changed to int for error handling]
 */

/** MSK_O --- MUMFORD-SHAH WITH CURVATURE (Jacobi method) **/
void msk_o(double *g, double *u, double *z, double lambda, double kepsilon,
           double alpha, double beta, double *mxdf, int nr, int nc)
{
    int i, j, jnc, nrc;
    double *old_u, *old_z;                                   /* msk_o */
    double u_tilde, ux, uy, zx, zy, z_tilde, z_hat, z_check; /* msk */
    double a, b, c, d, e;                                    /* msk */
    double num, den;
    double k2, k, h2, h = 1;
    double ta;

    nrc = nr * nc;
    h2 = h * h;
    k = kepsilon;
    k2 = kepsilon * kepsilon;

    /* Remove first image boundary using BC values */
    *u = *(u + nc + 1);                        /* ul corner */
    *(u + nc - 1) = *(u + 2 * nc - 2);         /* ur corner */
    *(u + nrc - nc) = *(u + nrc - 2 * nc + 1); /* ll corner */
    *(u + nrc - 1) = *(u + nrc - nc - 2);      /* lr corner */
    *z = *(z + nc + 1);                        /* ul corner */
    *(z + nc - 1) = *(z + 2 * nc - 2);         /* ur corner */
    *(z + nrc - nc) = *(z + nrc - 2 * nc + 1); /* ll corner */
    *(z + nrc - 1) = *(z + nrc - nc - 2);      /* lr corner */
    for (i = 1; i < nc - 1; i++) {             /* top and bottom edges */
        *(u + i) = *(u + nc + i);              /* t edge */
        *(u + nrc - nc + i) = *(u + nrc - 2 * nc + i); /* b edge */
        *(z + i) = *(z + nc + i);                      /* t edge */
        *(z + nrc - nc + i) = *(z + nrc - 2 * nc + i); /* b edge */
    }
    for (j = 1; j < nr - 1; j++) { /* left and right edges */
        jnc = j * nc;
        *(u + jnc) = *(u + jnc + 1);               /* r edge */
        *(u + jnc + nc - 1) = *(u + jnc + nc - 2); /* l edge */
        *(z + jnc) = *(z + jnc + 1);               /* r edge */
        *(z + jnc + nc - 1) = *(z + jnc + nc - 2); /* l edge */
    }

    /* Boundary conditions (Neumann) */

    /*** image corners ***/
    *(u + nc + 1) = *(u + 2 * nc + 2);                 /* ul corner */
    *(u + 2 * nc - 2) = *(u + 3 * nc - 3);             /* ur corner */
    *(u + nrc - 2 * nc + 1) = *(u + nrc - 3 * nc + 2); /* ll corner */
    *(u + nrc - nc - 2) = *(u + nrc - 2 * nc - 3);     /* lr corner */
    *(z + nc + 1) = *(z + 2 * nc + 2);                 /* ul corner */
    *(z + 2 * nc - 2) = *(z + 3 * nc - 3);             /* ur corner */
    *(z + nrc - 2 * nc + 1) = *(z + nrc - 3 * nc + 2); /* ll corner */
    *(z + nrc - nc - 2) = *(z + nrc - 2 * nc - 3);     /* lr corner */

    /* this is an alternative for the corners using the mean value of the x and
     * y closest points
     * *(u+nc+1) = 0.5 * ( *(u+nc+1) + *(u+2*nc+1) );
     * *(u+2*nc-2) = 0.5 * ( *(u+2*nc-3) + *(u+3*nc-2) );
     * *(u+nrc-2*nc+1) = 0.5 * ( *(u+nrc-2*nc+2) + *(u+nrc-3*nc+1) );
     * *(u+nrc-nc-2) = 0.5 * ( *(u+nrc-nc-3) +*(u+nrc-2*nc-2) );
     * *z = 0.5 * ( *(z+nc+1) + *(z+2*nc+1) );
     * *(z+nc-1) = 0.5 * ( *(z+2*nc-3) + *(z+3*nc-2) );
     * *(z+nrc-nc) = 0.5 * ( *(z+nrc-2*nc+2) + *(z+nrc-3*nc+1) );
     * *(z+nrc-1) = 0.5 * ( *(z+nrc-nc-3) +*(z+nrc-2*nc-2) );
     */

    /*** image edges ***/
    for (i = 2; i < nc - 2; i++) {         /* top and bottom edges */
        *(u + nc + i) = *(u + 2 * nc + i); /* t edge */
        *(u + nrc - 2 * nc + i) = *(u + nrc - 3 * nc + i); /* b edge */
        *(z + nc + i) = *(z + 2 * nc + i);                 /* t edge */
        *(z + nrc - 2 * nc + i) = *(z + nrc - 3 * nc + i); /* b edge */
    }
    for (j = 2; j < nr - 2; j++) { /* left and right edges */
        jnc = j * nc;
        *(u + jnc + 1) = *(u + jnc + 2);           /* r edge */
        *(u + jnc + nc - 2) = *(u + jnc + nc - 3); /* l edge */
        *(z + jnc + 1) = *(z + jnc + 2);           /* r edge */
        *(z + jnc + nc - 2) = *(z + jnc + nc - 3); /* l edge */
    }

    old_u = (double *)malloc(sizeof(double) * nrc);
    old_z = (double *)malloc(sizeof(double) * nrc);

    for (j = 0; j < nr; j++) {
        jnc = j * nc;
        for (i = 0; i < nc; i++) {
            *(old_u + jnc + i) = *(u + jnc + i);
            *(old_z + jnc + i) = *(z + jnc + i);
        }
    }

    for (j = 2; j < nr - 2; j++) {
        jnc = j * nc;
        for (i = 2; i < nc - 2; i++) {

            u_tilde = *(old_u + jnc + i + 1) + *(old_u + jnc + i - 1) +
                      *(old_u + jnc + nc + i) + *(old_u + jnc - nc + i);
            ux = *(old_u + jnc + i + 1) - *(old_u + jnc + i - 1);
            uy = *(old_u + jnc + nc + i) - *(old_u + jnc - nc + i);
            zx = *(old_z + jnc + i + 1) - *(old_z + jnc + i - 1);
            zy = *(old_z + jnc + nc + i) - *(old_z + jnc - nc + i);
            num = 0.5 * lambda * *(old_z + jnc + i) * (zx * ux + zy * uy) +
                  lambda * *(old_z + jnc + i) * *(old_z + jnc + i) * u_tilde +
                  h2 * *(g + jnc + i);
            den = 4 * lambda * *(old_z + jnc + i) * *(old_z + jnc + i) + h2;

            *(u + jnc + i) = num / den;

            z_tilde = *(old_z + jnc + i + 1) + *(old_z + jnc + i - 1) +
                      *(old_z + jnc + nc + i) + *(old_z + jnc - nc + i);
            z_hat = *(old_z + jnc + nc + i + 1) + *(old_z + jnc - nc + i + 1) +
                    *(old_z + jnc + nc + i - 1) + *(old_z + jnc - nc + i - 1);
            z_check = *(old_z + jnc + i + 2) + *(old_z + jnc + i - 2) +
                      *(old_z + jnc + 2 * nc + i) + *(old_z + jnc - 2 * nc + i);
            a = alpha * z_tilde + 4 * alpha * h2 * k2 * *(old_z + jnc + i) *
                                      *(old_z + jnc + i) * *(old_z + jnc + i);
            b = 4 * beta * (8 * z_tilde - 2 * z_hat - z_check) / h2;
            c = -16 * beta * k2 *
                (3 * *(old_z + jnc + i) * *(old_z + jnc + i) + 1) *
                (z_tilde - 4 * *(old_z + jnc + i));
            d = 64 * beta * k2 * *(old_z + jnc + i) *
                (3 * *(old_z + jnc + i) * *(old_z + jnc + i) - 1);
            e = 64 * beta * h2 * k2 * k2 * *(old_z + jnc + i) *
                *(old_z + jnc + i) * *(old_z + jnc + i) *
                (3 * *(old_z + jnc + i) * *(old_z + jnc + i) - 2);
            num = a + b + c + d + e;
            ta = a;

            a = 4 * alpha +
                2 * alpha * h2 * k2 *
                    (3 * *(old_z + jnc + i) * *(old_z + jnc + i) - 1) +
                0.25 * lambda * k * (ux * ux + uy * uy);
            b = 16 * beta * k2 * (h2 * k2 + 5 / (h2 * k2) - 4);
            c = -12 * beta * k2 * (zx * zx + zy * zy);
            d = -96 * beta * k2 * *(old_z + jnc + i) *
                (z_tilde - 4 * *(z + jnc + i));
            e = 192 * beta * k2 * *(old_z + jnc + i) * (1 - h2 * k2) +
                240 * beta * h2 * k2 * k2 * *(old_z + jnc + i) *
                    *(old_z + jnc + i) * *(old_z + jnc + i) *
                    *(old_z + jnc + i);
            den = a + b + c + d + e;

            *(z + jnc + i) = num / den;

            *mxdf = max(*mxdf, fabs(*(old_u + jnc + i) - *(u + jnc + i)));
        }
    }
    free(old_u);
    free(old_z);
    return;
}

/* ========================================================================== */
/* ========================================================================== */

/* ========================================================================== */
/*!
 * \brief MS_T --- MUMFORD-SHAH (Gauss-Seidel method) - (Different approximation
 * of "u" wrt MS_N)
 *
 * Implements the Mumford-Shah variational model for image segmentation.
 *
 * A smooth approximation of the input image is produced.
 * The model explicitely detects the discontinuities of the output approximation
 * while preserving the discontinuities from being smoothed.
 *
 * A discontinuity image is also produced.
 * The values of the discontinuity image are close to 1 where the output
 * approximation is "homogeneous", where the output approximation has
 * discontinuities (edges) the values are close to 0.
 *
 * The approximation of "u" is different wrt the one used in MS_N.
 *
 *
 * \param[in] *g (double; pointer) - The input image
 *
 * \param[in] *u (double; pointer) - The output approximation
 *
 * \param[in] *z (double; pointer) - The output discontinuity map
 *
 * \param[in] lambda (double) - The scale factor parameter [positive]
 *
 * \param[in] kepsilon (double) - The discontinuities thickness [positive]
 *
 * \param[in] alpha (double) - The elasticity parameter [positive]
 *
 * \param[in] *mxdf (double; pointer) - The max difference in the approximation
 * between two iteration steps
 *
 * \param[in] nr (int) - The number of rows in the input image
 *
 * \param[in] nc (int) - The number of colums in the input image
 *
 * \return void [shold be changed to int for error handling]
 */

/** MS_T --- MUMFORD-SHAH (Gauss-Seidel method) - (Different approximation of
 * "u" wrt MS_N) **/
void ms_t(double *g, double *u, double *z, double lambda, double kepsilon,
          double alpha, double *mxdf, int nr, int nc)
{
    int i, j, jnc, nrc;
    double old_u;                          /* ms_n */
    double old_t;                          /* ms_t */
    double u_hat, z_star, z_tilde, ux, uy; /* ms */
    double u_tilde, zx, zy;                /* msk */
    double num, den;
    double k2, k, h2, h = 1;

    nrc = nr * nc;
    h2 = h * h;
    k = kepsilon;
    k2 = kepsilon * kepsilon;

    /* Boundary conditions (Neumann) */
    *u = *(u + nc + 1);                        /* ul corner */
    *(u + nc - 1) = *(u + 2 * nc - 2);         /* ur corner */
    *(u + nrc - nc) = *(u + nrc - 2 * nc + 1); /* ll corner */
    *(u + nrc - 1) = *(u + nrc - nc - 2);      /* lr corner */
    *z = *(z + nc + 1);                        /* ul corner */
    *(z + nc - 1) = *(z + 2 * nc - 2);         /* ur corner */
    *(z + nrc - nc) = *(z + nrc - 2 * nc + 1); /* ll corner */
    *(z + nrc - 1) = *(z + nrc - nc - 2);      /* lr corner */
    for (i = 1; i < nc - 1; i++) {             /* top and bottom edges */
        *(u + i) = *(u + nc + i);              /* t edge */
        *(u + nrc - nc + i) = *(u + nrc - 2 * nc + i); /* b edge */
        *(z + i) = *(z + nc + i);                      /* t edge */
        *(z + nrc - nc + i) = *(z + nrc - 2 * nc + i); /* b edge */
    }
    for (j = 1; j < nr - 1; j++) { /* left and right edges */
        jnc = j * nc;
        *(u + jnc) = *(u + jnc + 1);               /* r edge */
        *(u + jnc + nc - 1) = *(u + jnc + nc - 2); /* l edge */
        *(z + jnc) = *(z + jnc + 1);               /* r edge */
        *(z + jnc + nc - 1) = *(z + jnc + nc - 2); /* l edge */
    }
    for (j = 1; j < nr - 1; j++) {
        jnc = j * nc;
        for (i = 1; i < nc - 1; i++) {
            old_u = *(u + jnc + i);

            /* March version and MS */
            u_hat =
                *(z + jnc + i + 1) * *(z + jnc + i + 1) * *(u + jnc + i + 1) +
                *(z + jnc + i - 1) * *(z + jnc + i - 1) * *(u + jnc + i - 1) +
                *(z + jnc + nc + i) * *(z + jnc + nc + i) *
                    *(u + jnc + nc + i) +
                *(z + jnc - nc + i) * *(z + jnc - nc + i) * *(u + jnc - nc + i);
            z_star = *(z + jnc + i + 1) * *(z + jnc + i + 1) +
                     *(z + jnc + i - 1) * *(z + jnc + i - 1) +
                     *(z + jnc + nc + i) * *(z + jnc + nc + i) +
                     *(z + jnc - nc + i) * *(z + jnc - nc + i);
            num = lambda * u_hat + h2 * *(g + jnc + i);
            den = lambda * z_star + h2;
            *(u + jnc + i) = num / den;

            old_t = *(u + jnc + i);

            /* math thesis version and MSK */
            u_tilde = *(u + jnc + i + 1) + *(u + jnc + i - 1) +
                      *(u + jnc + nc + i) + *(u + jnc - nc + i);
            ux = *(u + jnc + i + 1) - *(u + jnc + i - 1);
            uy = *(u + jnc + nc + i) - *(u + jnc - nc + i);
            zx = *(z + jnc + i + 1) - *(z + jnc + i - 1);
            zy = *(z + jnc + nc + i) - *(z + jnc - nc + i);
            num = 0.5 * lambda * *(z + jnc + i) * (zx * ux + zy * uy) +
                  lambda * *(z + jnc + i) * *(z + jnc + i) * u_tilde +
                  h2 * *(g + jnc + i);
            den = 4 * lambda * *(z + jnc + i) * *(z + jnc + i) + h2;
            *(u + jnc + i) = num / den;

            z_tilde = *(z + jnc + i + 1) + *(z + jnc + i - 1) +
                      *(z + jnc + nc + i) + *(z + jnc - nc + i);
            num = 4 * z_tilde + h2 * k2;
            den = 16 + h2 * k2 + lambda * k * (ux * ux + uy * uy) / alpha;
            *(z + jnc + i) = num / den;

            *mxdf = max(*mxdf, fabs(old_u - *(u + jnc + i)));
        }
    }
    return;
}

/* ========================================================================== */
/* ========================================================================== */

/* ========================================================================== */
/*!
 * \brief MSK_T --- MUMFORD-SHAH with CURVATURE term (Gauss-Seidel method) -
 * (Different approximation of "u" wrt MSK_N)
 *
 * Implements the Mumford-Shah variational model with curvature term for image
 * segmentation.
 *
 * A smooth approximation of the input image is produced.
 * The model explicitely detects the discontinuities of the output approximation
 * while preserving the discontinuities from being smoothed.
 *
 * A discontinuity image is also produced.
 * The values of the discontinuity image are close to 1 where the output
 * approximation is "homogeneous", where the output approximation has
 * discontinuities (edges) the values are close to 0.
 *
 * The curvature term prevents the discontinuities from being shortened too much
 * when the parameter alpha is set to very high values.
 *
 * The approximation of "u" is different wrt the one used in MSK_N.
 *
 *
 * \param[in] *g (double; pointer) - The input image
 *
 * \param[in] *u (double; pointer) - The output approximation
 *
 * \param[in] *z (double; pointer) - The output discontinuity map
 *
 * \param[in] lambda (double) - The scale factor parameter [positive]
 *
 * \param[in] kepsilon (double) - The discontinuities thickness [positive]
 *
 * \param[in] alpha (double) - The elasticity parameter [positive]
 *
 * \param[in] beta (double) - The rigidity parameter [positive]
 *
 * \param[in] *mxdf (double; pointer) - The max difference in the approximation
 * between two iteration steps
 *
 * \param[in] nr (int) - The number of rows in the input image
 *
 * \param[in] nc (int) - The number of colums in the input image
 *
 * \return void [shold be changed to int for error handling]
 */

/** MSK_T --- TEST --- MUMFORD-SHAH with CURVATURE term (Gauss-Seidel method) -
 * (Different approximation of "u" wrt MSK_N) **/
void msk_t(double *g, double *u, double *z, double lambda, double kepsilon,
           double alpha, double beta, double *mxdf, int nr, int nc)
{
    int i, j, jnc, nrc;
    double old_u;                           /* ms_n */
    double u_hat, z_star, z_tilde, ux, uy;  /* ms */
    double u_tilde, zx, zy, z_hat, z_check; /* msk */
    double a, b, c, d, e;                   /* msk */
    double num, den;
    double k2, k, h2, h = 1;
    double ta;

    nrc = nr * nc;
    h2 = h * h;
    k = kepsilon;
    k2 = kepsilon * kepsilon;

    /* Remove first image boundary using BC values */
    *u = *(u + nc + 1);                        /* ul corner */
    *(u + nc - 1) = *(u + 2 * nc - 2);         /* ur corner */
    *(u + nrc - nc) = *(u + nrc - 2 * nc + 1); /* ll corner */
    *(u + nrc - 1) = *(u + nrc - nc - 2);      /* lr corner */
    *z = *(z + nc + 1);                        /* ul corner */
    *(z + nc - 1) = *(z + 2 * nc - 2);         /* ur corner */
    *(z + nrc - nc) = *(z + nrc - 2 * nc + 1); /* ll corner */
    *(z + nrc - 1) = *(z + nrc - nc - 2);      /* lr corner */
    for (i = 1; i < nc - 1; i++) {             /* top and bottom edges */
        *(u + i) = *(u + nc + i);              /* t edge */
        *(u + nrc - nc + i) = *(u + nrc - 2 * nc + i); /* b edge */
        *(z + i) = *(z + nc + i);                      /* t edge */
        *(z + nrc - nc + i) = *(z + nrc - 2 * nc + i); /* b edge */
    }
    for (j = 1; j < nr - 1; j++) { /* left and right edges */
        jnc = j * nc;
        *(u + jnc) = *(u + jnc + 1);               /* r edge */
        *(u + jnc + nc - 1) = *(u + jnc + nc - 2); /* l edge */
        *(z + jnc) = *(z + jnc + 1);               /* r edge */
        *(z + jnc + nc - 1) = *(z + jnc + nc - 2); /* l edge */
    }

    /* Boundary conditions (Neumann) */
    *(u + nc + 1) = *(u + 2 * nc + 2);                 /* ul corner */
    *(u + 2 * nc - 2) = *(u + 3 * nc - 3);             /* ur corner */
    *(u + nrc - 2 * nc + 1) = *(u + nrc - 3 * nc + 2); /* ll corner */
    *(u + nrc - nc - 2) = *(u + nrc - 2 * nc - 3);     /* lr corner */
    *(z + nc + 1) = *(z + 2 * nc + 2);                 /* ul corner */
    *(z + 2 * nc - 2) = *(z + 3 * nc - 3);             /* ur corner */
    *(z + nrc - 2 * nc + 1) = *(z + nrc - 3 * nc + 2); /* ll corner */
    *(z + nrc - nc - 2) = *(z + nrc - 2 * nc - 3);     /* lr corner */
    for (i = 2; i < nc - 2; i++) {         /* top and bottom edges */
        *(u + nc + i) = *(u + 2 * nc + i); /* t edge */
        *(u + nrc - 2 * nc + i) = *(u + nrc - 3 * nc + i); /* b edge */
        *(z + nc + i) = *(z + 2 * nc + i);                 /* t edge */
        *(z + nrc - 2 * nc + i) = *(z + nrc - 3 * nc + i); /* b edge */
    }
    for (j = 2; j < nr - 2; j++) { /* left and right edges */
        jnc = j * nc;
        *(u + jnc + 1) = *(u + jnc + 2);           /* r edge */
        *(u + jnc + nc - 2) = *(u + jnc + nc - 3); /* l edge */
        *(z + jnc + 1) = *(z + jnc + 2);           /* r edge */
        *(z + jnc + nc - 2) = *(z + jnc + nc - 3); /* l edge */
    }

    for (j = 2; j < nr - 2; j++) {
        jnc = j * nc;
        for (i = 2; i < nc - 2; i++) {
            old_u = *(u + jnc + i);

            /* math thesis version and MKK */
            u_tilde = *(u + jnc + i + 1) + *(u + jnc + i - 1) +
                      *(u + jnc + nc + i) + *(u + jnc - nc + i);
            ux = *(u + jnc + i + 1) - *(u + jnc + i - 1);
            uy = *(u + jnc + nc + i) - *(u + jnc - nc + i);
            zx = *(z + jnc + i + 1) - *(z + jnc + i - 1);
            zy = *(z + jnc + nc + i) - *(z + jnc - nc + i);
            num = 0.5 * lambda * *(z + jnc + i) * (zx * ux + zy * uy) +
                  lambda * *(z + jnc + i) * *(z + jnc + i) * u_tilde +
                  h2 * *(g + jnc + i);
            den = 4 * lambda * *(z + jnc + i) * *(z + jnc + i) + h2;
            *(u + jnc + i) = num / den;

            /* March version and MS */
            u_hat =
                *(z + jnc + i + 1) * *(z + jnc + i + 1) * *(u + jnc + i + 1) +
                *(z + jnc + i - 1) * *(z + jnc + i - 1) * *(u + jnc + i - 1) +
                *(z + jnc + nc + i) * *(z + jnc + nc + i) *
                    *(u + jnc + nc + i) +
                *(z + jnc - nc + i) * *(z + jnc - nc + i) * *(u + jnc - nc + i);
            z_star = *(z + jnc + i + 1) * *(z + jnc + i + 1) +
                     *(z + jnc + i - 1) * *(z + jnc + i - 1) +
                     *(z + jnc + nc + i) * *(z + jnc + nc + i) +
                     *(z + jnc - nc + i) * *(z + jnc - nc + i);
            num = lambda * u_hat + h2 * *(g + jnc + i);
            den = lambda * z_star + h2;
            *(u + jnc + i) = num / den;

            z_tilde = *(z + jnc + i + 1) + *(z + jnc + i - 1) +
                      *(z + jnc + nc + i) + *(z + jnc - nc + i);
            z_hat = *(z + jnc + nc + i + 1) + *(z + jnc - nc + i + 1) +
                    *(z + jnc + nc + i - 1) + *(z + jnc - nc + i - 1);
            z_check = *(z + jnc + i + 2) + *(z + jnc + i - 2) +
                      *(z + jnc + 2 * nc + i) + *(z + jnc - 2 * nc + i);
            a = alpha * z_tilde + 4 * alpha * h2 * k2 * *(z + jnc + i) *
                                      *(z + jnc + i) * *(z + jnc + i);
            b = 4 * beta * (8 * z_tilde - 2 * z_hat - z_check) / h2;
            c = -16 * beta * k2 * (3 * *(z + jnc + i) * *(z + jnc + i) + 1) *
                (z_tilde - 4 * *(z + jnc + i));
            d = 64 * beta * k2 * *(z + jnc + i) *
                (3 * *(z + jnc + i) * *(z + jnc + i) - 1);
            e = 64 * beta * h2 * k2 * k2 * *(z + jnc + i) * *(z + jnc + i) *
                *(z + jnc + i) * (3 * *(z + jnc + i) * *(z + jnc + i) - 2);
            num = a + b + c + d + e;
            ta = a;

            a = 4 * alpha +
                2 * alpha * h2 * k2 *
                    (3 * *(z + jnc + i) * *(z + jnc + i) - 1) +
                0.25 * lambda * k * (ux * ux + uy * uy);
            b = 16 * beta * k2 * (h2 * k2 + 5 / (h2 * k2) - 4);
            c = -12 * beta * k2 * (zx * zx + zy * zy);
            d = -96 * beta * k2 * *(z + jnc + i) *
                (z_tilde - 4 * *(z + jnc + i));
            e = 192 * beta * k2 * *(z + jnc + i) * (1 - h2 * k2) +
                240 * beta * h2 * k2 * k2 * *(z + jnc + i) * *(z + jnc + i) *
                    *(z + jnc + i) * *(z + jnc + i);
            den = a + b + c + d + e;
            *(z + jnc + i) = num / den;

            *mxdf = max(*mxdf, fabs(old_u - *(u + jnc + i)));
        }
    }
    return;
}

/* ========================================================================== */
/* ========================================================================== */
