/*
   Same of the following routines are borrowed from "Numerical Recipes in C"
   other are written and tested by Stefano Merler

   for

   integration of function using the trapezoidal rule

   Supported function for
   - non-parametric functions
   - functions depending from 1 parameter
   - functions depending from 2 parameters
 */

#include <math.h>
#include <stdio.h>

#define FUNC(x) ((*func)(x))
#define EPS     1.0e-5
#define JMAX    1000

double trapzd(func, a, b, n)
/*
   trapezoidal rule for func=func(x) on interval [a,b]
   n = steps number
 */
double a, b;
double (*func)();
int n;
{
    double x, tnm, sum, del;
    double s;
    int j;

    if (n == 1) {
        return (s = 0.5 * (b - a) * (FUNC(a) + FUNC(b)));
    }
    else {
        tnm = n;
        del = (b - a) / tnm;
        x = a + 0.5 * del;
        for (sum = 0.0, j = 1; j <= n; j++, x += del)
            sum += FUNC(x);
        s = (b - a) * sum / tnm;
        return s;
    }
}

double trapzd1(func, p1, a, b, n)
/*
   trapezoidal rule for func=func(x; p1) on interval [a,b]
   p1 free parameter
   n = steps number
 */
double a, b;
double p1;
double (*func)();
int n;
{
    double x, tnm, sum, del;
    double s;
    int j;

    if (n == 1) {
        return (s = 0.5 * (b - a) * (func(a, p1) + func(b, p1)));
    }
    else {
        tnm = n;
        del = (b - a) / tnm;
        x = a + 0.5 * del;
        for (sum = 0.0, j = 1; j <= n; j++, x += del)
            sum += func(x, p1);
        s = (b - a) * sum / tnm;
        return s;
    }
}

double trapzd2(func, p1, p2, a, b, n)
/*
   trapezoidal rule for func=func(x; p1,p2) on interval [a,b]
   p1 and p2 free parameters
   n = steps number
 */
double a, b;
double p1, p2;
double (*func)();
int n;
{
    double x, tnm, sum, del;
    double s;
    int j;

    if (n == 1) {
        return (s = 0.5 * (b - a) * (func(a, p1, p2) + func(b, p1, p2)));
    }
    else {
        tnm = n;
        del = (b - a) / tnm;
        x = a + 0.5 * del;
        for (sum = 0.0, j = 1; j <= n; j++, x += del)
            sum += func(x, p1, p2);
        s = (b - a) * sum / tnm;
        return s;
    }
}

double qtrap(func, a, b)
/*
   trapezoidal rule for func=func(x) with stopping rule
 */
double a, b;
double (*func)();
{
    int j;
    double s, olds;

    olds = -1.0e-30;

    for (j = 1; j <= JMAX; j++) {
        s = trapzd(func, a, b, j);
        if (fabs(s - olds) < EPS * fabs(olds))
            return s;
        olds = s;
    }

    fprintf(stderr, "Too many steps in routine qtrap\n");
    return s;
}

double qtrap1(func, p1, a, b)
/*
   trapezoidal rule for func=func(x) on interval [a,b]
   with internal stopping rule
   p1  free parameter
 */
double a, b;
double p1;
double (*func)();
{
    int j;
    double s, olds;

    olds = -1.0e-30;

    for (j = 1; j <= JMAX; j++) {
        s = trapzd(func, p1, a, b, j);
        if (fabs(s - olds) < EPS * fabs(olds))
            return s;
        olds = s;
    }

    fprintf(stderr, "Too many steps in routine qtrap\n");
    return s;
}

double qtrap2(func, p1, p2, a, b)
/*
   trapezoidal rule for func=func(x) on interval [a,b]
   with internal stopping rule
   p1 and p2 free parameters
 */
double a, b;
double p1, p2;
double (*func)();
{
    int j;
    double s, olds;

    olds = -1.0e-30;

    for (j = 1; j <= JMAX; j++) {
        s = trapzd(func, p1, p2, a, b, j);
        if (fabs(s - olds) < EPS * fabs(olds))
            return s;
        olds = s;
    }

    fprintf(stderr, "Too many steps in routine qtrap\n");
    return s;
}

#undef EPS
#undef JMAX
