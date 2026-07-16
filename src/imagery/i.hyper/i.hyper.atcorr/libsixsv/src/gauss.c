/* Gauss-Legendre quadrature — ported from 6SV2.1 GAUSS.f */
#include "../include/sixs_ctx.h"
#include <math.h>
#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif

/**
 * \brief Compute Gauss-Legendre quadrature nodes and weights.
 *
 * Returns the \c n abscissae and weights for numerical integration over
 * \f$[x_1, x_2]\f$ using the Newton-Raphson iteration on the Legendre
 * polynomial \f$P_n\f$.  Accurate to machine precision (~3×10⁻¹⁴).
 *
 * Ported from 6SV2.1 GAUSS.f.
 *
 * \param[in]  x1  Lower bound of the integration interval.
 * \param[in]  x2  Upper bound of the integration interval.
 * \param[out] x   Array of \c n quadrature nodes (abscissae).
 * \param[out] w   Array of \c n quadrature weights.
 * \param[in]  n   Number of quadrature points.
 */
void sixs_gauss(float x1, float x2, float *x, float *w, int n) {
    const double eps = 3.0e-14;
    int m = (n + 1) / 2;
    double xm = 0.5 * (x2 + x1);
    double xl = 0.5 * (x2 - x1);

    for (int i = 1; i <= m; i++) {
        double z = cos(M_PI * (i - 0.25) / (n + 0.5));
        double z1, p1, p2, p3, pp;
        do {
            p1 = 1.0; p2 = 0.0;
            for (int j = 1; j <= n; j++) {
                p3 = p2; p2 = p1;
                p1 = ((2.0 * j - 1.0) * z * p2 - (j - 1.0) * p3) / j;
            }
            pp = n * (z * p1 - p2) / (z * z - 1.0);
            z1 = z;
            z = z1 - p1 / pp;
        } while (fabs(z - z1) > eps);
        if (fabs(z) < eps) z = 0.0;
        x[i - 1]     = (float)(xm - xl * z);
        x[n - i]     = (float)(xm + xl * z);
        w[i - 1]     = (float)(2.0 * xl / ((1.0 - z * z) * pp * pp));
        w[n - i]     = w[i - 1];
    }
}

/**
 * \brief Build the full 6SV Gauss quadrature grid including sentinel points.
 *
 * Constructs the \c nquad-point angular quadrature grid used by the 6SV
 * successive-orders-of-scattering solver.  The grid is composed of
 * \c nquad−3 interior Gauss-Legendre points over (−1, 1), plus the three
 * special sentinel values −1, 0, and +1 inserted at fixed positions.
 *
 * The weights for the sentinel points are set to zero (they are used for
 * boundary evaluation only, not integration).
 *
 * \param[in]  nquad    Total number of quadrature points (must be ≥ 4 and odd).
 * \param[out] cgaus_S  Cosine nodes: \c cgaus_S[0]=−1, interior nodes, \c cgaus_S[nquad−1]=+1.
 * \param[out] pdgs_S   Quadrature weights (zero at sentinel positions).
 */
void sixs_gauss_setup(int nquad, float *cgaus_S, float *pdgs_S) {
    int nbmu_2 = (nquad - 3) / 2;
    float cosang[NQ_MAX], weight[NQ_MAX];
    sixs_gauss(-1.0f, 1.0f, cosang, weight, nquad - 3);

    cgaus_S[0] = -1.0f; pdgs_S[0] = 0.0f;
    for (int j = 0; j < nbmu_2; j++) {
        cgaus_S[j + 1] = cosang[j];
        pdgs_S[j + 1]  = weight[j];
    }
    cgaus_S[nbmu_2 + 1] = 0.0f; pdgs_S[nbmu_2 + 1] = 0.0f;
    for (int j = nbmu_2; j < nquad - 3; j++) {
        cgaus_S[j + 2] = cosang[j];
        pdgs_S[j + 2]  = weight[j];
    }
    cgaus_S[nquad - 1] = 1.0f; pdgs_S[nquad - 1] = 0.0f;
}
