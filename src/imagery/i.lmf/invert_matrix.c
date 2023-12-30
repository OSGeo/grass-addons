/****************************************************************
 * Inverse and Determinant of A by the Gauss-Jordan Method.
 * m is the order of the square matrix, A.
 * A-Inverse replaces A.
 * Determinant of A is placed in DET.
 * Cooley and Lohnes (1971:63)
 ****************************************************************/

#include <stdio.h>
#include <stdlib.h>
#include <math.h>

#define IDIM 50
#define MAXF 50
int invert_matrix(double a[][MAXF], int order)
{
    double ipvt[IDIM + 1];

    double pvt[IDIM + 1];

    double ind[IDIM + 1][1];

    int i, j, k, l, l1;

    double amax, swap;

    int irow, icol;

    int m = order;

    for (j = 0; j < m; j++) {
        ipvt[j] = 0.0;
    }
    for (i = 0; i < m; i++) {

        /*SEARCH FOR THE PIVOT ELEMENT */
        double temporary = 0;

        amax = 0.0;
        for (j = 0; j < m; j++) {
            if (ipvt[j] != 1) {
                for (k = 0; k < m; k++) {
                    if (ipvt[k] == 0 && abs(amax) < abs(a[j][k])) {
                        irow = j;
                        icol = k;
                        amax = a[j][k];
                    }
                    else if (ipvt[j] == 1) {
                        temporary = 1;
                        break;
                    }
                    else if (ipvt[j] > 1 || ipvt[j] < 0) {
                        temporary = 5;
                        break;
                    }
                }
                if (temporary == 5 || temporary == 1) {
                    break;
                }
            }
            else {
                break;
            }
            if (temporary == 5) {
                break;
            }
        }
        if (temporary != 5) {

            /*INTERCHANGE ROWS TO PUT PIVOT ELEMENT ON DIAGONAL */
            if (irow != icol) {
                for (l = 0; l < m; l++) {
                    swap = a[irow][l];
                    a[irow][l] = a[icol][l];
                    a[icol][l] = swap;
                }
            }
            ind[i][0] = irow;
            ind[i][1] = icol;
            pvt[i] = a[icol][icol];

            /*DIVIDE THE PIVOT ROW BY THE PIVOT ELEMENT */
            a[icol][icol] = 1.0;
            for (l = 0; l < m; l++) {
                a[icol][l] = a[icol][l] / pvt[i];
            }

            /*REDUCE THE NON-PIVOT ROWS */
            for (l1 = 0; l1 < m; l1++) {
                if (l1 != icol) {
                    swap = a[l1][icol];
                    a[l1][icol] = 0.0;
                    if (swap < pow(0.1, -30) && swap > pow(-0.1, -30)) {
                        swap = 0.0;
                    }
                    for (l = 0; l < m; l++) {
                        a[l1][l] = a[l1][l] - a[icol][l] * swap;
                    }
                }
            }
        }
        else {
            break;
        }
    }

    /*INTERCHANGE THE COLUMNS */
    for (i = 0; i < m; i++) {
        l = m - i - 1;
        if (ind[l][0] != ind[l][1]) {
            irow = ind[l][0];
            icol = ind[l][1];
            for (k = 0; k < m; k++) {
                swap = a[k][irow];
                a[k][irow] = a[k][icol];
                a[k][icol] = swap;
            }
        }
        else if (ind[l][0] == ind[l][1]) {
            break;
        }
    }
    return;
}
