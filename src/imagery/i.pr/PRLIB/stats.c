/*
   The following routing are written and tested by Stefano Merler

   for

   statistical description of data

   Supported function for:
   - mean computation
   - standard deviation and variance computation
   - autocovariance computation
   - covariance matrix computation
   -min-max of an array
 */

#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <grass/gis.h>

double mean_of_double_array(double *x, int n)

/*
   compute the mean of an array x of lenth n
 */
{
    int i;
    double mean = .0;

    for (i = 0; i < n; i++)
        mean += x[i];

    mean /= n;

    return mean;
}

double var_of_double_array(double *x, int n)

/*
   compute the var of an array x of length n
 */
{
    int i;
    double deviation;
    double mean = .0;
    double var = .0;

    for (i = 0; i < n; i++)
        mean += x[i];

    mean /= n;

    for (i = 0; i < n; i++) {
        deviation = x[i] - mean;
        var += deviation * deviation;
    }

    var /= (n - 1.0);

    return var;
}

double sd_of_double_array(double *x, int n)

/*
   compute the sd of an array x of length n
 */
{
    int i;
    double deviation;
    double mean = .0;
    double var = .0;

    for (i = 0; i < n; i++)
        mean += x[i];

    mean /= n;

    for (i = 0; i < n; i++) {
        deviation = x[i] - mean;
        var += deviation * deviation;
    }

    var /= (n - 1.0);

    return sqrt(var);
}

double var_of_double_array_given_mean(double *x, int n, double mean)

/*
   compute the var of an array x of length n
   without computation of the mean mean,
   given in input
 */
{
    int i;
    double deviation;
    double var = .0;

    for (i = 0; i < n; i++) {
        deviation = x[i] - mean;
        var += deviation * deviation;
    }

    var /= (n - 1.0);

    return var;
}

double sd_of_double_array_given_mean(double *x, int n, double mean)

/*
   compute the sd of an array x of length n
   without computation of the mean,
   given in input
 */
{
    int i;
    double deviation;
    double var = .0;

    for (i = 0; i < n; i++) {
        deviation = x[i] - mean;
        var += deviation * deviation;
    }

    var /= (n - 1.0);

    return sqrt(var);
}

void mean_and_var_of_double_matrix_by_row(double **x, int n, int m,
                                          double *mean, double *var)

/*
   each row of the input matrix x (dimension n x m)
   is considered an independent array of data.
   The function compute mean and var of each row,
   stored within the array mean and var.
 */
{
    int i, j;
    double deviation;

    for (j = 0; j < n; j++)
        for (i = 0; i < m; i++) {
            mean[j] += x[j][i];
        }
    for (i = 0; i < n; i++)
        mean[i] /= m;
    for (j = 0; j < n; j++) {
        for (i = 0; i < m; i++) {
            deviation = x[j][i] - mean[j];
            var[j] += deviation * deviation;
        }
    }
    for (i = 0; i < n; i++)
        var[i] = var[i] / (m - 1.);
}

void mean_and_sd_of_double_matrix_by_row(double **x, int n, int m, double *mean,
                                         double *sd)

/*
   each row of the input matrix x (dimension n x m)
   is considered an independent array of data.
   The function compute mean and sd of each row,
   stored within the array mean and sd.
 */
{
    int i, j;
    double deviation;

    for (j = 0; j < n; j++)
        for (i = 0; i < m; i++) {
            mean[j] += x[j][i];
        }
    for (i = 0; i < n; i++)
        mean[i] /= m;
    for (j = 0; j < n; j++) {
        for (i = 0; i < m; i++) {
            deviation = x[j][i] - mean[j];
            sd[j] += deviation * deviation;
        }
    }
    for (i = 0; i < n; i++)
        sd[i] = sqrt(sd[i] / (m - 1.));
}

void mean_and_var_of_double_matrix_by_col(double **x, int n, int m,
                                          double *mean, double *var)

/*
   each col of the input matrix x (dimension n x m)
   is considered an independent array of data.
   The function compute mean and var of each col,
   stored within the array mean and sd.
 */
{
    int i, j;
    double deviation;

    for (i = 0; i < m; i++) {
        for (j = 0; j < n; j++)
            mean[i] += x[j][i];
    }
    for (i = 0; i < m; i++)
        mean[i] /= n;

    for (i = 0; i < m; i++) {
        for (j = 0; j < n; j++) {
            deviation = x[j][i] - mean[i];
            var[i] += deviation * deviation;
        }
    }
    for (i = 0; i < m; i++)
        var[i] = var[i] / (n - 1.);
}

void mean_and_sd_of_double_matrix_by_col(double **x, int n, int m, double *mean,
                                         double *sd)

/*
   each col of the input matrix x (dimension n x m)
   is considered an independent array of data.
   The function compute mean and sd of each col,
   stored within the array mean and sd.
 */
{
    int i, j;
    double deviation;

    for (i = 0; i < m; i++) {
        for (j = 0; j < n; j++)
            mean[i] += x[j][i];
    }
    for (i = 0; i < m; i++)
        mean[i] /= n;

    for (i = 0; i < m; i++) {
        for (j = 0; j < n; j++) {
            deviation = x[j][i] - mean[i];
            sd[i] += deviation * deviation;
        }
    }
    for (i = 0; i < m; i++)
        sd[i] = sqrt(sd[i] / (n - 1.));
}

double auto_covariance_of_2_double_array(double *x, double *y, int n)

/*
   compute the auto covariance of 2 array x and y of length n
 */
{
    int i;
    double mx = .0;
    double my = .0;
    double cc = .0;

    for (i = 0; i < n; i++) {
        mx += x[i];
        my += y[i];
    }
    mx /= n;
    my /= n;

    for (i = 0; i < n; i++)
        cc += (x[i] - mx) * (y[i] - my);
    cc /= n;
    return (cc);
}

void covariance_of_double_matrix(double **x, int n, int m, double **cov)

/*
   compute covariance matrix of a matrix x of dimension n x m.
   Output to matrix cov.
 */
{
    int i, j, k;
    double *mean;

    mean = (double *)G_calloc(m, sizeof(double));

    for (i = 0; i < m; i++) {
        for (j = 0; j < n; j++)
            mean[i] += x[j][i];
        mean[i] /= n;
    }

    for (i = 0; i < m; i++)
        for (j = i; j < m; j++) {
            for (k = 0; k < n; k++)
                cov[i][j] += (x[k][i] - mean[i]) * (x[k][j] - mean[j]);
            cov[i][j] /= n;
            cov[j][i] = cov[i][j];
        }

    G_free(mean);
}

double entropy(double *p, int n)

/*
   compute and return entropy of an array p (his components to be intended
   as proportions) of length n
 */
{
    int i;
    double entropy = .0;

    for (i = 0; i < n; i++)
        if (p[i] > 0)
            entropy += p[i] * log(p[i]);

    return -1.0 * entropy;
}

double gaussian_kernel(double *x, double *y, int n, double kp)

/*
   compute e return gaussian kernel exp(-sqrt(||x-y||)/kp),
   x and y array of length n
 */
{
    int j;
    double out = 0.0;
    double tmp;

    for (j = 0; j < n; j++) {
        tmp = x[j] - y[j];
        out += tmp * tmp;
    }

    return exp(-1.0 * sqrt(out) / kp);
}

double squared_gaussian_kernel(double *x, double *y, int n, double kp)

/*
   compute e return gaussian kernel exp(-||x-y||/kp),
   x and y array of length n
 */
{
    int j;
    double out = 0.0;
    double tmp;

    for (j = 0; j < n; j++) {
        tmp = x[j] - y[j];
        out += tmp * tmp;
    }

    return exp(-1.0 * out / kp);
}

double min(double *x, int n)
{
    int j;
    double out;

    out = x[0];

    for (j = 1; j < n; j++) {
        if (out > x[j]) {
            out = x[j];
        }
    }
    return out;
}

double max(double *x, int n)
{
    int j;
    double out;

    out = x[0];

    for (j = 1; j < n; j++) {
        if (out < x[j]) {
            out = x[j];
        }
    }
    return out;
}
