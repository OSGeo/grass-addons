/*
   The following routines are written and tested by Stefano Merler

   for

   quadratic programming
 */

#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <grass/gis.h>
#include "func.h"

void mqc(double **M, double *m, int n, double **H, double *h, int mH,
         double **K, double *k, int mK, double eps, double *x, double *minvalue)
{
    int i, j, l;

    double **invM;
    double **HM, **HMH, *tnH, **HMK, **KM, **KMK, *tnK, **tH, **tK;
    double mMm;
    double gap;
    double *alpha, *beta;
    double L, f;
    double tmpalpha, tmpbeta, tmpL, tmpf;

    /*alloc memory */
    invM = (double **)G_calloc(n, sizeof(double *));
    for (i = 0; i < n; i++)
        invM[i] = (double *)G_calloc(n, sizeof(double));

    if (mH > 0) {
        HM = (double **)G_calloc(mH, sizeof(double *));
        for (i = 0; i < mH; i++)
            HM[i] = (double *)G_calloc(n, sizeof(double));

        HMH = (double **)G_calloc(mH, sizeof(double *));
        for (i = 0; i < mH; i++)
            HMH[i] = (double *)G_calloc(mH, sizeof(double));

        tnH = (double *)G_calloc(mH, sizeof(double));

        tH = (double **)G_calloc(n, sizeof(double *));
        for (i = 0; i < n; i++)
            tH[i] = (double *)G_calloc(mH, sizeof(double));

        for (i = 0; i < mH; i++)
            for (j = 0; j < n; j++)
                tH[j][i] = H[i][j];
    }

    if (mH > 0 && mK > 0) {
        HMK = (double **)G_calloc(mH, sizeof(double *));
        for (i = 0; i < mH; i++)
            HMK[i] = (double *)G_calloc(mK, sizeof(double));
    }

    if (mK > 0) {
        KM = (double **)G_calloc(mK, sizeof(double *));
        for (i = 0; i < mK; i++)
            KM[i] = (double *)G_calloc(n, sizeof(double));

        KMK = (double **)G_calloc(mK, sizeof(double *));
        for (i = 0; i < mK; i++)
            KMK[i] = (double *)G_calloc(mK, sizeof(double));

        tnK = (double *)G_calloc(mK, sizeof(double));

        tK = (double **)G_calloc(n, sizeof(double *));
        for (i = 0; i < n; i++)
            tK[i] = (double *)G_calloc(mK, sizeof(double));

        for (i = 0; i < mK; i++)
            for (j = 0; j < n; j++)
                tK[j][i] = K[i][j];
    }

    /*compute inverse of M */
    inverse_of_double_matrix(M, invM, n);

    /*compute matrices products */
    if (mH > 0) {
        product_double_matrix_double_matrix(H, invM, mH, n, n, HM);
        product_double_matrix_double_matrix(HM, tH, mH, n, mH, HMH);
        product_double_matrix_double_vector(HM, m, mH, n, tnH);
        for (i = 0; i < mH; i++)
            tnH[i] += 2. * h[i];
    }

    if (mH > 0 && mK > 0)
        product_double_matrix_double_matrix(HM, tK, mH, n, mK, HMK);

    if (mK > 0) {
        product_double_matrix_double_matrix(K, invM, mK, n, n, KM);
        product_double_matrix_double_matrix(KM, tK, mK, n, mK, KMK);
        product_double_matrix_double_vector(KM, m, mK, n, tnK);
        for (i = 0; i < mK; i++)
            tnK[i] += 2. * k[i];
    }

    mMm = 0.0;
    for (i = 0; i < n; i++)
        for (j = 0; j < n; j++)
            mMm += m[i] * m[j] * invM[i][j];
    mMm *= -.5;

    if (mH > 0)
        alpha = (double *)G_calloc(mH, sizeof(double));
    if (mK > 0)
        beta = (double *)G_calloc(mK, sizeof(double));

    gap = eps + 1;
    /*gradient ascendent on the dual Lagrangian */
    while (gap > eps) {
        if (mH > 0 && mK > 0) {
            for (l = 0; l < mH; l++) {

                tmpalpha = .0;
                for (i = 0; i < mH; i++)
                    if (alpha[i] > 0)
                        tmpalpha += HMH[i][l] * alpha[i];

                tmpalpha += tnH[l];

                for (i = 0; i < mK; i++)
                    tmpalpha += HMK[l][i] * beta[i];

                alpha[l] -= tmpalpha / HMH[l][l];

                if (alpha[l] < .0)
                    alpha[l] = .0;
            }

            for (l = 0; l < mK; l++) {
                tmpbeta = .0;
                for (i = 0; i < mK; i++)
                    tmpbeta += KMK[i][l] * beta[i];

                tmpbeta += tnK[l];

                for (i = 0; i < mH; i++)
                    if (alpha[i] > 0)
                        tmpbeta += HMK[i][l] * alpha[i];

                beta[l] -= tmpbeta / KMK[l][l];
            }
        }
        else if (mH > 0 && mK == 0) {
            for (l = 0; l < mH; l++) {

                tmpalpha = .0;
                for (i = 0; i < mH; i++)
                    if (alpha[i] > 0)
                        tmpalpha += HMH[i][l] * alpha[i];

                tmpalpha += tnH[l];

                alpha[l] -= tmpalpha / HMH[l][l];
                if (alpha[l] < .0)
                    alpha[l] = .0;
            }
        }
        else if (mH == 0 && mK > 0) {
            for (l = 0; l < mK; l++) {
                tmpbeta = .0;
                for (i = 0; i < mK; i++)
                    tmpbeta += KMK[i][l] * beta[i];

                tmpbeta += tnK[l];

                beta[l] -= tmpbeta / KMK[l][l];
            }
        }

        /*value of the dual Lagrangian */
        L = mMm;

        tmpL = .0;
        for (i = 0; i < mH; i++)
            if (alpha[i] > 0)
                for (j = 0; j < mH; j++)
                    if (alpha[j] > 0)
                        tmpL += alpha[i] * alpha[j] * HMH[i][j];
        L -= .5 * tmpL;

        tmpL = .0;
        for (i = 0; i < mH; i++)
            if (alpha[i] > 0)
                tmpL += alpha[i] * tnH[i];
        L -= tmpL;

        tmpL = .0;
        for (i = 0; i < mK; i++)
            for (j = 0; j < mK; j++)
                tmpL += beta[i] * beta[j] * KMK[i][j];
        L -= .5 * tmpL;

        tmpL = .0;
        for (i = 0; i < mK; i++)
            tmpL += beta[i] * tnK[i];
        L -= tmpL;

        tmpL = .0;
        for (i = 0; i < mH; i++)
            if (alpha[i] > 0)
                for (j = 0; j < mK; j++)
                    tmpL += alpha[i] * beta[j] * HMK[i][j];
        L -= tmpL;

        L *= .5;

        /*value of the objective function */
        f = mMm - L;

        tmpf = .0;
        for (i = 0; i < mH; i++)
            if (alpha[i] > 0)
                tmpf += alpha[i] * tnH[i];
        f -= .5 * tmpf;

        tmpf = .0;
        for (i = 0; i < mK; i++)
            tmpf += beta[i] * tnK[i];
        f -= .5 * tmpf;

        /* gap between dual Lagrangian and objective function (stopping
         * criteria) */
        gap = fabs((f - L) / (f + 1.));
        printf("%f\n", gap);
    }

    /*minimum */

    for (l = 0; l < n; l++) {
        x[l] = .0;

        for (i = 0; i < mH; i++)
            if (alpha[i] > 0)
                x[l] += HM[i][l] * alpha[i];

        for (i = 0; i < mK; i++)
            x[l] += KM[i][l] * beta[i];

        for (i = 0; i < n; i++)
            x[l] += invM[l][i] * m[i];

        x[l] *= -.5;
    }
    for (i = 0; i < mH; i++)
        printf("a[%d]=%f\n", i, alpha[i]);
    for (i = 0; i < mK; i++)
        printf("b[%d]=%f\n", i, beta[i]);

    /*value of the function */
    *minvalue = f;

    /*free memory */
    for (i = 0; i < n; i++)
        G_free(invM[i]);
    G_free(invM);

    if (mH > 0) {
        G_free(alpha);
        G_free(tnH);
        for (i = 0; i < mH; i++) {
            G_free(HM[i]);
            G_free(HMH[i]);
        }
        G_free(HM);
        G_free(HMH);
        for (i = 0; i < n; i++)
            G_free(tH[i]);
        G_free(tH);
    }

    if (mK > 0) {
        G_free(beta);
        G_free(tnK);
        for (i = 0; i < mK; i++) {
            G_free(KM[i]);
            G_free(KMK[i]);
        }
        G_free(KM);
        G_free(KMK);
        for (i = 0; i < n; i++)
            G_free(tK[i]);
        G_free(tK);
    }

    if (mK > 0 && mH > 0) {
        for (i = 0; i < mH; i++)
            G_free(HMK[i]);
        G_free(HMK);
    }
}
