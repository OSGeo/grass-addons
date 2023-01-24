#include "local_proto.h"

void linear_regression(DCELL *x, DCELL *y, int count, DCELL *res_offset,
                       DCELL *res_slope, DCELL *res_residuals,
                       DCELL *res_correlation)
{
    int i;
    DCELL sum_x = 0;
    DCELL sum_y = 0;
    DCELL sum_xy = 0;
    DCELL sum_xx = 0;
    DCELL sum_yy = 0;

    DCELL r_n;
    DCELL var_x;
    DCELL var_y;
    DCELL covar;
    DCELL beta;
    DCELL alpha;
    DCELL corr;

    if (count <= 0)
        return;

    for (i = 0; i < count; i++) {
        DCELL xi = x[i];
        DCELL yi = y[i];

        sum_x += xi;
        sum_y += yi;
        sum_xy += xi * yi;
        sum_xx += xi * xi;
        sum_yy += yi * yi;
    }

    r_n = 1.0 / (DCELL)count;
    var_x = (sum_xx - sum_x * sum_x * r_n) * r_n;
    var_y = (sum_yy - sum_y * sum_y * r_n) * r_n;
    covar = (sum_xy - sum_x * sum_y * r_n) * r_n;
    beta = covar / var_x;
    alpha = (sum_y - beta * sum_x) * r_n;
    corr = beta * sqrt(var_x) / sqrt(var_y);

    *res_slope = beta;
    *res_offset = alpha;
    *res_correlation = corr;

    for (i = 0; i < count; i++) {
        res_residuals[i] = y[i] - (alpha + beta * x[i]);
    }
}
