/*
   The following routines are written and tested by Stefano Merler

   for

   Soft Boosting implementation (quadratic programming)
 */

#include <grass/gis.h>
#include "global.h"
#include <stdlib.h>
#include <string.h>
#include <math.h>

void maximize(double *alpha, int N, double *beta, int T, double **M)
{
    int i, l, t, s;
    int convergence = FALSE;
    double detetaalpha, detetabeta;
    double *alpha_old;
    double *beta_old;
    double eps = 0.00001;
    double *eta;
    double tmp;

    alpha_old = (double *)G_calloc(N, sizeof(double));
    beta_old = (double *)G_calloc(T, sizeof(double));
    eta = (double *)G_calloc(N, sizeof(double));

    for (l = 0; l < N; l++) {
        tmp = .0;
        for (t = 0; t < T; t++)
            tmp += M[l][t] * M[l][t];
        eta[l] = 1.0 / tmp;
    }

    for (l = 0; l < N; l++)
        alpha[l] = .0;

    for (t = 0; t < T; t++)
        beta[t] = .0;

    while (!convergence) {
        for (l = 0; l < N; l++)
            alpha_old[l] = alpha[l];
        for (s = 0; s < T; s++)
            beta_old[s] = beta[s];

        for (l = 0; l < N; l++) {
            detetaalpha = .0;
            for (t = 0; t < T; t++)
                for (i = 0; i < N; i++)
                    detetaalpha -= alpha[i] * M[l][t] * M[i][t];

            for (t = 0; t < T; t++)
                detetaalpha -= beta[t] * M[l][t];

            detetaalpha += 1.0;

            alpha[l] += eta[l] * detetaalpha;

            if (alpha[l] < 0)
                alpha[l] = .0;

            if (alpha[l] > 100. / N)
                alpha[l] = 100. / N;
        }

        for (s = 0; s < T; s++) {
            detetabeta = -1.0 * beta[s];

            for (i = 0; i < N; i++)
                detetabeta -= alpha[i] * M[i][s];

            beta[s] += detetabeta;

            if (beta[s] < 0)
                beta[s] = .0;
        }

        /*
           for(l=0;l<N;l++){
           fprintf(stderr,"%f\t",alpha[l]);
           }
           fprintf(stderr,"\n");
         */

        convergence = TRUE;
        for (l = 0; l < N; l++) {
            if (fabs(alpha[l] - alpha_old[l]) > eps) {
                fprintf(stderr, "ALPHA %d %f %f\n", l, alpha_old[l], alpha[l]);
                convergence = FALSE;
                break;
            }
        }
        if (convergence)
            for (s = 0; s < T; s++) {
                if (fabs(beta[s] - beta_old[s]) > eps) {
                    fprintf(stderr, "BETA %d %f %f\n", s, beta_old[s], beta[s]);
                    convergence = FALSE;
                    break;
                }
            }
    }
    G_free(alpha_old);
    G_free(beta_old);
    G_free(eta);
}
