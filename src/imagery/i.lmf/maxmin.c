/* Maxmin Filter */

#include <stdio.h>
#include <stdlib.h>

#define NMAX 200
int maxmin(int n, int nwin, double *dat)
{
    int i, j, jf, jr;

    double da1[NMAX];

    double vmin0 = 9.9E99;

    double vminf, vminr;

    for (i = 0; i < nwin; i++) {
        da1[i] = dat[0];
    }
    for (i = 0; i < n; i++) {
        da1[i + nwin] = dat[i];
    }
    for (i = 0; i < nwin; i++) {
        da1[i + n + nwin] = dat[n];
    }
    for (i = 0; i < n; i++) {
        vminf = vmin0;
        vminr = vmin0;
        for (j = 0; j < nwin; j++) {
            jf = i + nwin + j;
            jr = i + nwin - j;
            if (da1[jf] < vminf) {
                vminf = da1[jf];
            }
            if (da1[jr] < vminr) {
                vminr = da1[jr];
            }
        }
        if (vminf >= vminr) {
            dat[i] = vminf;
        }
        else {
            dat[i] = vminr;
        }
        if (dat[i] > 1.0E10) {
            dat[i] = 0.0;
        }
    }
    return;
}
