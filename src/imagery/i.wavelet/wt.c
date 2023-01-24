#include <stdio.h>
#include <math.h>

int dwt_l2(double *signal, int length, double *LP1, double *HP1, double *HP2,
           double *LP2, double *h, double *g, int l)
{
    int n, i, j, k;
    double Hilbert_lp, Hilbert_hp;
    for (n = 0; n < 2; n++) {
        printf("Decomposition level %d\tData length = %d\t", n + 1, length);
        printf("& Scaling length = %f\n", length / pow(2, n + 1));
        for (i = 0; i < length / pow(2, n + 1); i++) {
            if (n == 0) {
                for (j = 0; j < l; j++) {
                    k = i * 2 + j;
                    while (k >= length / pow(2, n)) {
                        k -= length / pow(2, n);
                    }
                    Hilbert_lp = signal[k] * h[j];
                    Hilbert_hp = signal[k] * g[j];
                    LP1[i] += Hilbert_lp;
                    HP1[i] += Hilbert_hp;
                }
            }
            if (n == 1) {
                for (j = 0; j < l; j++) {
                    k = i * 2 + j;
                    while (k >= length / pow(2, n)) {
                        k -= length / pow(2, n);
                    }
                    Hilbert_lp = LP1[k] * h[j];
                    Hilbert_hp = LP1[k] * g[j];
                    LP2[i] += Hilbert_lp;
                    HP2[i] += Hilbert_hp;
                }
            }
        }
    }
    return (1);
}

/** REVERSE MODE FUNCTION **/
int idwt_l2(double *LP1, double *HP1, double *LP2, double *HP2, int length,
            double *out, double *h, double *g, int l)
{
    double Hilbert_lp, Hilbert_hp;
    int n, i, j, k;
    for (n = 0; n < 2; n++) {
        printf("Recomposition level %d\tData length = %d\t", n + 1, length);
        printf("& Scaling length = %f\n", length * pow(2, n));
        for (i = 0; i < length * pow(2, n); i++) {
            if (n == 0) {
                for (j = 0; j < l; j++) {
                    k = i * 2 + j;
                    while (k >= length * pow(2, n + 1)) {
                        k -= length * pow(2, n + 1);
                    }
                    Hilbert_lp = LP2[i] * h[j];
                    Hilbert_hp = HP2[i] * g[j];
                    LP1[k] += Hilbert_lp + Hilbert_hp;
                }
            }
            if (n == 1) {
                for (j = 0; j < l; j++) {
                    k = i * 2 + j;
                    while (k >= length * pow(2, n + 1)) {
                        k -= length * pow(2, n + 1);
                    }
                    Hilbert_lp = LP1[i] * h[j];
                    Hilbert_hp = HP1[i] * g[j];
                    out[k] += Hilbert_lp + Hilbert_hp;
                }
            }
        }
    }
    return (1);
}
