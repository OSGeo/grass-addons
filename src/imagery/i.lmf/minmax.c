/* Minmax Filter */

#include <stdio.h>
#include <stdlib.h>

#define NMAX 200
int minmax(int n, int nwin, double *dat)
{
    int i, j, jf, jr;

    double da1[NMAX];

    double vmax0 = -9.9E99;

    double vmaxf, vmaxr;

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
        vmaxf = vmax0;
        vmaxr = vmax0;
        for (j = 0; j < nwin; j++) {
            jf = i + nwin + j;
            jr = i + nwin - j;
            if (da1[jf] > vmaxf) {
                vmaxf = da1[jf];
            }
            if (da1[jr] > vmaxr) {
                vmaxr = da1[jr];
            }
        }
        if (vmaxf <= vmaxr) {
            dat[i] = vmaxf;
        }
        else {
            dat[i] = vmaxr;
        }
        if (dat[i] <= -1.0E10) {
            dat[i] = 0.0;
        }
    }
    return;
}
