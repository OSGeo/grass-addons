#include <stdio.h>
#include <math.h>

#define ISNEG(X) (!((X) > 0) && ((X) != 0))

/* sign() returns -1 (negative) or +1 (positive) or 0 (zero)*/
int sign(double signedvalue)
{
    if (signedvalue == 0.0)
        return 0;
    else if (ISNEG(signedvalue) == 1)
        return -1;
    else
        return 1;
}

/*normalized cumulative distribution function*/
double normcdf(double x, double mu, double sigma)
{
    double y;
    double l[10] = {-1.26551223, 1.00002368, 0.37409196,  0.09678418,
                    -0.18628806, 0.27886807, -1.13520398, 1.48851587,
                    -0.82215223, 0.17087277};
    double val = -(x - mu) / (sigma * sqrt(2.0));
    double t = 1.0 / (1.0 + fabs(val) / 2.0);
    double r =
        t *
        exp(-fabs(val) * fabs(val) + l[0] +
            t * (l[1] +
                 t * (l[2] +
                      t * (l[3] +
                           t * (l[4] +
                                t * (l[5] +
                                     t * (l[6] +
                                          t * (l[7] +
                                               t * (l[8] + t * l[9])))))))));
    if (x >= 0.)
        y = r / 2.0;
    else
        y = (2.0 - r) / 2.0;
    if (y > 1.0)
        y = 1.0;
    return (y);
}

/*Mann-Kendall test input signal and its length (t)*/
double mk_test(double *signal, int t)
{
    double value = 0.0, z = 0.0;
    int i, j;
    for (i = 1; i < t - 1; i++)
        for (j = i + 1; j < t; j++)
            value += sign(signal[j] - signal[i]);
    double variance = (t * (t - 1) * (2 * t + 5)) / 18.0;
    double stddev = sqrt(variance);
    if (value > 0)
        z = ((value - 1) / stddev) * (value);
    else
        z = (value + 1) / stddev;
    return (2 * (1 - normcdf(fabs(z), 0, 1)));
}
