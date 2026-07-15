/* RT kernel (Legendre polynomials) — ported from 6SV2.1 KERNEL.f */
#include "../include/sixs_ctx.h"
#include <math.h>
#include <string.h>
#include <stdlib.h>

/**
 * \brief Build the Legendre-polynomial RT kernel matrices for scalar radiative transfer.
 *
 * Constructs the associated Legendre polynomial array \c psl and the scattering
 * kernel \c bp used by the successive-orders solver sixs_os().  On entry the
 * Gauss quadrature nodes are read from \c ctx->quad.
 *
 * Ported from 6SV2.1 KERNEL.f.
 *
 * \param[in]  ctx      6SV context (Gauss quadrature nodes in \c ctx->quad).
 * \param[in]  is       Fourier order index (0 = azimuthal mean).
 * \param[in]  mu       Half the number of quadrature angles (mu = nquad/2).
 * \param[in]  rm_off   Quadrature cosines: \c rm_off[j+mu] = rm[j], size 2mu+1.
 * \param[out] xpl_off  Legendre values at quadrature nodes, size 2mu+1 (offset by mu).
 * \param[out] psl      Associated Legendre polynomials, row-major [l+1][j+mu],
 *                      dimensions (NQ_P+2) × (2mu+1).
 * \param[out] bp       Scattering kernel, row-major [j][k+mu],
 *                      dimensions (mu+1) × (2mu+1).
 */
void sixs_kernel(const SixsCtx *ctx, int is, int mu,
                  const float *rm_off,  /* rm_off[j] = rm[j-mu] */
                  double *xpl_off,      /* xpl_off[j+mu] = xpl[j], size 2mu+1 */
                  double *psl,          /* psl[(NQ_P+2)*(2*mu+1)], row-major [l+1][j+mu] */
                  double *bp)           /* bp[(mu+1)*(2*mu+1)], row-major [j][k+mu] */
{
    int nquad  = ctx->quad.nquad;
    int ip1    = nquad - 3;
    double rac3 = sqrt(3.0);
    int dim = 2 * mu + 1;

    /* Access macros */
    #define PSL(l, j)  psl[((l)+1)*dim + ((j)+mu)]
    #define XPL(j)     xpl_off[(j)+mu]
    #define BP(j, k)   bp[(j)*dim + ((k)+mu)]
    #undef RM
    #define RM(j)      rm_off[(j)+mu]

    if (is == 0) {
        for (int j = 0; j <= mu; j++) {
            double c = RM(j);
            PSL(0, -j) = 1.0; PSL(0, j) = 1.0;
            PSL(1,  j) = c;   PSL(1, -j) = -c;
            double xdb = (3.0 * c * c - 1.0) * 0.5;
            if (fabs(xdb) < 1e-30) xdb = 0.0;
            PSL(2, -j) = xdb; PSL(2, j) = xdb;
        }
        PSL(1, 0) = RM(0);
    } else if (is == 1) {
        for (int j = 0; j <= mu; j++) {
            double c = RM(j);
            double x = 1.0 - c * c;
            PSL(0,  j) = 0.0; PSL(0, -j) = 0.0;
            double sq = sqrt(x * 0.5);
            PSL(1, -j) = sq;  PSL(1, j) = sq;
            PSL(2,  j) = c * PSL(1, j) * rac3;
            PSL(2, -j) = -PSL(2, j);
        }
        PSL(2, 0) = -PSL(2, 0);
    } else {
        double a = 1.0;
        for (int i = 1; i <= is; i++) {
            double xi = i;
            a *= sqrt((xi + is) / xi) * 0.5;
        }
        for (int j = 0; j <= mu; j++) {
            double c = RM(j);
            double xx = 1.0 - c * c;
            PSL(is-1, j) = 0.0;
            double xdb = a * pow(xx, is * 0.5);
            if (fabs(xdb) < 1e-30) xdb = 0.0;
            PSL(is, -j) = xdb; PSL(is, j) = xdb;
        }
    }

    /* Recurrence relation for higher orders */
    int k = (is > 2) ? is : 2;
    if (k < ip1) {
        int ig = (is == 1) ? 1 : -1;
        for (int l = k; l <= ip1 - 1; l++) {
            int lp = l + 1, lm = l - 1;
            double aa = (2.0 * l + 1.0) / sqrt((double)((l + is + 1) * (l - is + 1)));
            double bb = sqrt((double)((l + is) * (l - is))) / (2.0 * l + 1.0);
            for (int j = 0; j <= mu; j++) {
                double c = RM(j);
                double xdb = aa * (c * PSL(l, j) - bb * PSL(lm, j));
                if (fabs(xdb) < 1e-30) xdb = 0.0;
                PSL(lp, j) = xdb;
                if (j != 0) PSL(lp, -j) = ig * PSL(lp, j);
            }
            ig = -ig;
        }
    }

    /* xpl = psl[2, :] */
    for (int j = -mu; j <= mu; j++) XPL(j) = PSL(2, j);

    /* Compute bp[j][k] = sum_l betal[l] * psl[l,j] * psl[l,k] */
    for (int j = 0; j <= mu; j++) {
        for (int k2 = -mu; k2 <= mu; k2++) {
            double sbp = 0.0;
            if (is <= ip1) {
                for (int l = is; l <= ip1; l++) {
                    sbp += PSL(l, j) * PSL(l, k2) * ctx->polar.betal[l];
                }
            }
            if (fabs(sbp) < 1e-30) sbp = 0.0;
            BP(j, k2) = sbp;
        }
    }

    #undef PSL
    #undef XPL
    #undef BP
    #undef RM
}
