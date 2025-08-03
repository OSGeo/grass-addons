/* Making Triangular Function Matrix/Vector */

#include <stdio.h>
#include <stdlib.h>
#include <math.h>

#define NMAX 200
#define MAXF 50

#define PI   3.1415926535897932385
int make_matrix(int n, int npoint, int nfunc, int *numk, double f[][MAXF])
{
    int nn;

    double eps, vn, angle, theta;

    int i, j, j1, j2;

    double di, dk;

    nn = 2 * nfunc + 2;
    eps = 1.0;

    /*Set Constants */
    vn = (double)npoint;
    angle = 2.0 * PI / vn;

    /*Matrix Clear */
    for (i = 0; i < n; i++) {
        for (j = 0; j < nn; j++) {
            f[i][j] = 0.0;
        }
    }

    /*Making Matrix */
    for (i = 0; i < n; i++) {
        di = (double)(i + 1);
        for (j = 0; j < nfunc; j++) {
            j1 = (j + 1) * 2;
            j2 = j1 + 1;
            dk = (double)numk[j];
            theta = angle * di * dk;
            f[i][j1] = sin(theta);
            f[i][j2] = cos(theta);
        }
        f[i][0] = 1.0;
        f[i][1] = 1.0E-1 * (double)(i + 1);
    }
    return;
}
