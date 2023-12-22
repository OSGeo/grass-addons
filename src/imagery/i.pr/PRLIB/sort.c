/*
   The following routines is borrowed from "Numerical Recipes in C"

   for

   sortinf of an array
 */

#include <math.h>
#include <stdlib.h>
#include <grass/gis.h>
#include "global.h"

#define ALN2I 1.442695022
#define TINY  1.0e-5

static void indexx();

void shell(int n, double *arr)

/*
   sort and rearranges an array arr of length n
   into ascending order
 */
{
    int nn, m, j, i, lognb2;
    double t;

    lognb2 = (log((double)n) * ALN2I + TINY);
    m = n;
    for (nn = 1; nn <= lognb2; nn++) {
        m >>= 1;
        for (j = m + 1; j <= n; j++) {
            i = j - m;
            t = arr[j - 1];
            while (i >= 1 && arr[i - 1] > t) {
                arr[i + m - 1] = arr[i - 1];
                i -= m;
            }
            arr[i + m - 1] = t;
        }
    }
}

#undef ALN2I
#undef TINY

void indexx_1(int n, double arrin[], int indx[])

/*
   sort array arrin of length n into ascending order,
   without modify it. The order of the sording will be
   contained into the indx array
 */
{
    int i;
    double *tmparrin;
    int *tmpindx;

    tmpindx = (int *)G_calloc(n + 1, sizeof(int));
    tmparrin = (double *)G_calloc(n + 1, sizeof(double));

    for (i = 0; i < n; i++)
        tmparrin[i + 1] = arrin[i];

    indexx(n, tmparrin, tmpindx);

    for (i = 0; i < n; i++)
        indx[i] = tmpindx[i + 1] - 1;

    G_free(tmpindx);
    G_free(tmparrin);
}

static void indexx(int n, double arrin[], int indx[])
{
    int l, j, ir, indxt, i;
    double q;

    for (j = 1; j <= n; j++)
        indx[j] = j;
    if (n == 1)
        return;
    l = (n >> 1) + 1;
    ir = n;
    for (;;) {
        if (l > 1)
            q = arrin[(indxt = indx[--l])];
        else {
            q = arrin[(indxt = indx[ir])];
            indx[ir] = indx[1];
            if (--ir == 1) {
                indx[1] = indxt;
                return;
            }
        }
        i = l;
        j = l << 1;
        while (j <= ir) {
            if (j < ir && arrin[indx[j]] < arrin[indx[j + 1]])
                j++;
            if (q < arrin[indx[j]]) {
                indx[i] = indx[j];
                j += (i = j);
            }
            else
                j = ir + 1;
        }
        indx[i] = indxt;
    }
}
