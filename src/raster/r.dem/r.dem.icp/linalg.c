/****************************************************************************
 *
 * MODULE:       r.dem.icp
 * AUTHOR(S):    Corey T. White <smortopahri@gmail.com>
 * PURPOSE:      Small dense linear system solver
 * COPYRIGHT:    (C) 2025-2026 by Corey T. White and the GRASS Development
 *               Team
 *
 * SPDX-License-Identifier: GPL-2.0-or-later
 *
 *****************************************************************************/

#include <math.h>
#include <string.h>

#include "rdemicp.h"

/* Solve A x = b for small dense systems (n<=6) using Gaussian elimination
with partial pivoting. A is overwritten. */
int solve_linear_system(int n, double *A, double *b, double *x)
{
    /* Forward elimination */
    for (int k = 0; k < n; k++) {
        /* pivot */
        int piv = k;
        double amax = fabs(A[k * n + k]);
        for (int i = k + 1; i < n; i++) {
            double v = fabs(A[i * n + k]);
            if (v > amax) {
                amax = v;
                piv = i;
            }
        }
        if (amax < 1e-18)
            return -1; /* singular */
        if (piv != k) {
            for (int j = k; j < n; j++) {
                double tmp = A[k * n + j];
                A[k * n + j] = A[piv * n + j];
                A[piv * n + j] = tmp;
            }
            double tb = b[k];
            b[k] = b[piv];
            b[piv] = tb;
        }
        /* elimination */
        double Akk = A[k * n + k];
        for (int i = k + 1; i < n; i++) {
            double f = A[i * n + k] / Akk;
            A[i * n + k] = 0.0;
            for (int j = k + 1; j < n; j++)
                A[i * n + j] -= f * A[k * n + j];
            b[i] -= f * b[k];
        }
    }
    /* back substitution */
    for (int i = n - 1; i >= 0; i--) {
        double sum = b[i];
        for (int j = i + 1; j < n; j++)
            sum -= A[i * n + j] * x[j];
        x[i] = sum / A[i * n + i];
    }
    return 0;
}
