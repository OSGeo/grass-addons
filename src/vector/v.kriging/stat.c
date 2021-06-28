#include "local_proto.h"

void test_normality(int n, double *data, struct write *report)
{
    int i;
    double *elm;
    double sum_data = 0.;
    double res;
    double sum_res2, sum_res3, sum_res4;
    double tmp;
    double mean, skewness, kurtosis;
    double limit5, limit1;

    // compute mean
    elm = &data[0];
    for (i = 0; i < n; i++) {
        sum_data += *elm;
        elm++;
    }
    mean = sum_data / n;

    // compute skewness and curtosis
    elm = &data[0];
    sum_res2 = sum_res3 = sum_res4 = 0.;
    for (i = 0; i < n; i++) {
        res = *elm - mean;
        sum_res2 += SQUARE(res);
        sum_res3 += POW3(res);
        sum_res4 += POW4(res);
        elm++;
    }

    tmp = sum_res2 / (n - 1);
    skewness = (sum_res3 / (n - 1)) / sqrt(POW3(tmp));
    kurtosis = (sum_res4 / (n - 1)) / SQUARE(tmp) - 3.;

    // expected RMSE
    limit5 = sqrt(6. / n);
    limit1 = sqrt(24. / n);

    fprintf(report->fp, "\n");
    fprintf(report->fp, "Test of normality\n");
    fprintf(report->fp, "-----------------\n");
    fprintf(report->fp, "Test statistics | Value\n");
    fprintf(report->fp, "skewness | %f\n", skewness);
    fprintf(report->fp, "kurtosis | %f\n", kurtosis);
    fprintf(report->fp, "\n");
    fprintf(report->fp, "Level of confidence | Critical value\n");
    fprintf(report->fp, " 0.05 | %f\n", limit5);
    fprintf(report->fp, " 0.01 | %f\n", limit1);
    fprintf(report->fp, "-----------------\n\n");
}
