/*************************************************************
******Triangular Function Fitting********************
*************************************************************/

#include <stdio.h>
#include <stdlib.h>

#define NMAX 200
#define MAXF 50
int invert_matrix(double a[][MAXF], int order);

int fitting(int npoint, int nfunc, double *dat, int *idx1, double f[][MAXF],
            double *c, double *vfit)
{
    int i, j, k, k1, k2, nn;

    double tf[MAXF][MAXF];

    double tinv[MAXF][MAXF];

    double vec[MAXF];

    double tfij;

    double sum;

    nn = nfunc * 2 + 2;

    /*Value Initialization */
    for (i = 0; i < nn; i++) {
        c[i] = 0.0;
    }
    for (i = 0; i < npoint; i++) {
        vfit[i] = 0.0;
    }

    /*Matrix Initialization */
    for (i = 0; i < nn; i++) {
        for (j = 0; j < nn; j++) {
            tf[i][j] = 0.0;
            tf[j][i] = 0.0;
        }
        vec[i] = 0.0;
    }

    /*Making Matrix */
    for (i = 0; i < npoint; i++) {
        if (idx1[i] == 1) {
            for (k1 = 0; k1 < nn; k1++) {
                for (k2 = 0; k2 < nn; k2++) {
                    tf[k1][k2] = tf[k1][k2] + f[i][k2] * f[i][k1];
                }
                vec[k1] = vec[k1] + dat[i] * f[i][k1];
            }
        }
    }

    /*Matrix Copy and Inversion */
    for (i = 0; i < nn; i++) {
        for (j = i; j < nn; j++) {
            tfij = tf[i][j];
            tinv[i][j] = tfij;
            tinv[j][i] = tfij;
        }
    }
    invert_matrix(tinv, nn);

    /*Calculation of Coefficients */
    for (i = 0; i < nn; i++) {
        sum = 0.0;
        for (j = 0; j < nn; j++) {
            sum = sum + tinv[i][j] * vec[j];
        }
        c[i] = sum;
    }

    /*Calculating theoretical value */
    for (i = 0; i < npoint; i++) {
        sum = 0.0;
        for (k = 0; k < nn; k++) {
            sum = sum + c[k] * f[i][k];
        }
        vfit[i] = sum;
    }
    return;
}
