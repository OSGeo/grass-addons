/*
   The following routines are written and tested by Stefano Merler

   for

   Distance between arrays computation
 */

#include <math.h>
#include "global.h"

double squared_distance(double *x, double *y, int n)

/*
   squared euclidean distance between vectors x and y of length n
 */
{
    int j;
    double out = 0.0;
    double tmp;

    for (j = 0; j < n; j++) {
        tmp = x[j] - y[j];
        out += tmp * tmp;
    }

    return out;
}

double euclidean_distance(double *x, double *y, int n)

/*
   euclidean distance between vectors x and y of length n
 */
{
    int j;
    double out = 0.0;
    double tmp;

    for (j = 0; j < n; j++) {
        tmp = x[j] - y[j];
        out += tmp * tmp;
    }

    return sqrt(out);
}

double scalar_product(double *x, double *y, int n)

/*
   scalar product between vector x and y of length n
 */
{
    double out;
    int i;

    out = 0.0;
    for (i = 0; i < n; i++)
        out += x[i] * y[i];

    return out;
}

double euclidean_norm(double *x, int n)

/*
   euclidean norm of a  vector x of length n
 */
{
    return sqrt(scalar_product(x, x, n));
}
