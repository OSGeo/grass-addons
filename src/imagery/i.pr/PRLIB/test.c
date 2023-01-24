/*
   The following routines are borrowed from "Numerical Recipes in C"
   and rearranged by Stefano Merler

   for

   statistical test computation

   Supported functions for:
   - KS test the normal distribution of data
   - KS test for equality of 2 distribution
   - t-test for mean
 */

#include <math.h>
#include <grass/gis.h>
#include "global.h"

#define EPS1 0.001
#define EPS2 1.0e-8
#ifndef MAX
#define MAX(a, b) ((a) > (b) ? (a) : (b))
#endif

double probks();
double probks2();
double betai();
double gammln();
double betacf();

void ksone_normal(double *data, int n, double p1, double p2, double *d,
                  double *prob)

/*
   KS test for normal distribution. data is the array of data
   of length n. p1 and p2 mean and sd of the normal distribution
   tested. On output d is the value of the test and prob
   the p-value
 */
{
    int j;
    double fo = 0.0, fn, ff, en, dt;

    shell(n, data);
    en = (double)n;

    *d = 0.0;

    for (j = 1; j <= n; j++) {
        fn = j / en;
        ff = cumulative_normal_distribution(p1, p2, data[j - 1]);
        dt = MAX(fabs(fo - ff), fabs(fn - ff));
        if (dt > *d)
            *d = dt;
        fo = fn;
    }
    *prob = probks2(*d, n);
}

void kstwo(double *data1, int n1, double *data2, int n2, double *d,
           double *prob)

/*
   KS test for testing 2 distribution. data1 is the first
   array of data of length n1. data2 is the second array
   of data of length n2. On output d is the value of the
   test and prob the p-value
 */
{
    int j1 = 1, j2 = 1;
    double en1, en2, fn1 = 0.0, fn2 = 0.0, dt, d1, d2;

    en1 = n1;
    en2 = n2;
    *d = 0.0;
    shell(n1, data1);
    shell(n2, data2);
    while (j1 <= n1 && j2 <= n2) {
        if ((d1 = data1[j1 - 1]) <= (d2 = data2[j2 - 1])) {
            fn1 = (j1++) / en1;
        }
        if (d2 <= d1) {
            fn2 = (j2++) / en2;
        }
        if ((dt = fabs(fn2 - fn1)) > *d)
            *d = dt;
    }
    *prob = probks(sqrt(en1 * en2 / (en1 + en2)) * (*d));
}

double probks(double alam)

/*
   evaluate Q(KS) function i.e significance
 */
{
    int j;
    double a2, fac = 2.0, sum = 0.0, term, termbf = 0.0;

    a2 = -2.0 * alam * alam;
    for (j = 1; j <= 100; j++) {
        term = fac * exp(a2 * j * j);
        sum += term;
        if (fabs(term) <= EPS1 * termbf || fabs(term) <= EPS2 * sum)
            return sum;
        fac = -fac;
        termbf = fabs(term);
    }
    return 1.0;
}

double probks2(double alam, int ndata)

/*
   evaluate Q(KS) function (Dallal-Wilkinson approx.)
   i.e significance depending from the number of
   data ndata
 */
{
    double ks, p, n;

    n = (double)ndata;
    ks = alam;

    if (ndata > 100) {
        ks = ks * pow(n / 100., 0.49);
        n = 100.;
    }
    p = exp(-7.01256 * ks * ks * (n + 2.78019) +
            2.99587 * ks * sqrt(n + 2.78019) - 0.122119 + 0.974598 / sqrt(n) +
            1.67997 / n);
    return (p);
}

double normal_distribution(x, mu, sigma)
/*
   normal distribution with mean mu and
   standard deviation sigma computed at point x

   1/(sigma*sqrt(PIG) exp(-(x-mu)^2/2sigma^2)
 */
double x, mu, sigma;
{
    return exp(-1 * (x - mu) * (x - mu) / (2.0 * sigma * sigma)) /
           (sigma * sqrt(2 * PIG));
}

double cumulative_normal_distribution(double mu, double sigma, double x)

/*
   cumulative probability of the normal
   distribution with mean mu and
   standard deviation sigma, i.e.
   integral from -Inf to x

 */
{
    return trapzd2(normal_distribution, mu, sigma, -10., x, 1000);
}

#undef EPS1
#undef EPS2

double gammln(double xx)
{
    double x, tmp, ser;

    static double cof[6] = {76.18009173,  -86.50532033,   24.01409822,
                            -1.231739516, 0.120858003e-2, -0.536382e-5};
    int j;

    x = xx - 1.0;
    tmp = x + 5.5;
    tmp -= (x + 0.5) * log(tmp);
    ser = 1.0;
    for (j = 0; j <= 5; j++) {
        x += 1.0;
        ser += cof[j] / x;
    }
    return -tmp + log(2.50662827465 * ser);
}

#define ITMAX 1000000
#define EPS   3.0e-7

double betacf(double a, double b, double x)
{
    double qap, qam, qab, em, tem, d;
    double bz, bm = 1.0, bp, bpp;
    double az = 1.0, am = 1.0, ap, app, aold;
    int m;

    qab = a + b;
    qap = a + 1.0;
    qam = a - 1.0;

    bz = 1.0 - qab * x / qap;

    for (m = 1; m <= ITMAX; m++) {
        em = (double)m;
        tem = em + em;
        d = em * (b - em) * x / ((qam + tem) * (a + tem));
        ap = az + d * am;
        bp = bz + d * bm;
        d = -(a + em) * (qab + em) * x / ((qap + tem) * (a + tem));
        app = ap + d * az;
        bpp = bp + d * bz;
        aold = az;
        am = ap / bpp;
        bm = bp / bpp;
        az = app / bpp;
        bz = 1.0;
        if (fabs(az - aold) < (EPS * fabs(az)))
            return az;
    }
    G_warning("a or b too big, or ITMAX too small in BETACF\n");
    return az;
}

#undef ITMAX
#undef EPS

double betai(double a, double b, double x)
{
    double bt;

    if (x < 0.0 || x > 1.0) {
        G_warning("bad x in BETAI\n");
    }
    if (x == 0.0 || x == 1.0) {
        bt = 0.0;
    }
    else {
        bt = exp(gammln(a + b) - gammln(a) - gammln(b) + a * log(x) +
                 b * log(1.0 - x));
    }
    if (x < (a + 1.0) / (a + b + 2.0)) {
        return bt * betacf(a, b, x) / a;
    }
    else {
        return 1.0 - bt * betacf(b, a, 1.0 - x) / b;
    }
}

double sqrarg;

#define SQR(a) (sqrarg = (a), sqrarg * sqrarg)

void tutest(double *data1, int n1, double *data2, int n2, double *t,
            double *prob)

/*
 */
{
    double var1, var2, df, ave1, ave2;

    ave1 = mean_of_double_array(data1, n1);
    var1 = var_of_double_array_given_mean(data1, n1, ave1);

    ave2 = mean_of_double_array(data2, n2);
    var2 = var_of_double_array_given_mean(data2, n2, ave2);

    *t = (ave1 - ave2) / sqrt(var1 / n1 + var2 / n2);
    df = SQR(var1 / n1 + var2 / n2) /
         (SQR(var1 / n1) / (n1 - 1) + SQR(var2 / n2) / (n2 - 1));
    *prob = betai(0.5 * df, 0.5, df / (df + SQR(*t)));
}
