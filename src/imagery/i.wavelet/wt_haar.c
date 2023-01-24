#include <stdio.h>
#include <math.h>

/*Public Domain*/

/*Descomposition of a signal following the Haar wavelet method for 2 levels*/
int dwt_haar_l2(double *signal, int length, double *LP1, double *HP1,
                double *LP2, double *HP2)
{
    int n, i;
    double summation, difference;
    for (n = 0; n < 2; n++) {
        printf("Decomposition level %d\t", n + 1);
        printf("Data length = %d\t", length);
        printf("& Scaling length = %f\n", length / pow(2, n + 1));
        for (i = 0; i < length / pow(2, n + 1); i++) {
            if (n == 0) {
                summation = signal[i * 2] + signal[i * 2 + 1];
                difference = signal[i * 2] - signal[i * 2 + 1];
                LP1[i] = summation;
                HP1[i] = difference;
            }
            if (n == 1) {
                summation = LP1[i * 2] + LP1[i * 2 + 1];
                difference = LP1[i * 2] - LP1[i * 2 + 1];
                LP2[i] = summation;
                HP2[i] = difference;
            }
        }
    }
    return (1);
}

/*Recomposition of a signal from its three wavelet coefs from Level 1 & 2: HP1
 * available, LP1 made by LP2 & HP2*/
int idwt_haar_l2(double *LP1, double *HP1, double *LP2, double *HP2, int length,
                 double *out)
{
    int n, i;
    double summation, difference;
    for (n = 0; n < 2; n++) {
        printf("Recomposition level %d\t", (2 - n));
        printf("Data length = %d\t", length);
        printf("& Scaling length = %f\n", length / pow(2, (2 - n)));
        for (i = 0; i < length / pow(2, (2 - n)); i++) {
            if ((2 - n - 1) == 1) {
                summation = (LP2[i] + HP2[i]) / 2;
                difference = (LP2[i] - HP2[i]) / 2;
                LP1[i * 2] = summation;
                LP1[i * 2 + 1] = difference;
            }
            if ((2 - n - 1) == 0) {
                summation = (LP1[i] + HP1[i]) / 2;
                difference = (LP1[i] - HP1[i]) / 2;
                out[i * 2] = summation;
                out[i * 2 + 1] = difference;
            }
        }
    }
    return (1);
}
