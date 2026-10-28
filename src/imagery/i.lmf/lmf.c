/********************************************************************
 * LMF SUBROUTINE: Trying to process one pixel at a time         ****
 *                       in a single function                    ****
 ********************************************************************
 ********************************************************************
 * NBANDS = how many dates in this time-series                   ****
 * NPOINT = how many dates of this time-series cover one year    ****
 *               (NPOINT=46 for MODIS 8-days product)            ****
 ********************************************************************/

#include <stdio.h>
#include <stdlib.h>

#define MAXB  200
/* NMAX=MAXB */
#define NMAX  200
#define MAXF  50

#define TRUE  1
#define FALSE 0

#define PI    3.1415926535897932385
void make_matrix(int n, int npoint, int nfunc, int *numk, double f[][MAXF]);

void fitting(int npoint, int nfunc, double *dat, int *idx1, double f[][MAXF],
             double *c, double *vfit);
void minmax(int n, int nwin, double *dat);

void maxmin(int n, int nwin, double *dat);

int lmf(int nbands, int npoint, double *inpix, double *outpix)
{
    int i, j, k, nfunc;

    int nwin, mmsw, nds;

    int fitmd;

    int idx1[NMAX];

    /*for fitting */
    double dat[NMAX];

    double f[NMAX][MAXF], c[MAXF];

    double vfit[NMAX];

    /*for iteration */
    double dat0[NMAX];

    /*for Matrix Inversion */
    int numk[MAXF] = {1, 2, 3, 4, 6, 12, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                      0, 0, 0, 0, 0, 0,  0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                      0, 0, 0, 0, 0, 0,  0, 0, 0, 0, 0, 0, 0, 0, 0, 0};

    /*Set Defaults */
    nfunc = 6;
    for (i = 0; i < NMAX; i++) {
        for (j = 0; j < MAXF; j++) {
            f[i][j] = 0.0;
        }
    }
    make_matrix(nbands, npoint, nfunc, numk, f);
    nwin = 3;
    mmsw = 1;

    /*nds=npoint; */
    nds = 2 * nfunc + 2;

    /*fitting method */
    fitmd = 2;

    /*initialize arrays */
    for (k = 0; k < nbands; k++) {
        dat0[k] = 0.0;
        outpix[k] = 0.0;
        idx1[k] = TRUE;
    }
    for (k = 0; k < nds; k++) {
        c[k] = 0.0;
    }
    for (k = 0; k < nbands; k++) {
        dat0[k] = inpix[k];
        dat[k] = dat0[k];
    }

    /*Minimax Filter */
    if (mmsw >= 1 && fitmd == 0) {
        minmax(nbands, nwin, dat);
    }
    else if (mmsw >= 1 && fitmd == 1) {
        maxmin(nbands, nwin, dat);
    }

    /*Fitting */
    fitting(nbands, 3, dat, idx1, f, c, vfit);
    for (k = 0; k < nbands; k++) {
        outpix[k] = vfit[k];
    }
    return 0;
}
