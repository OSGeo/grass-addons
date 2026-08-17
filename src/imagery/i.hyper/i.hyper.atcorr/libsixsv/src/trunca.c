/* Phase-matrix Legendre expansion — ported from 6SV2.1 TRUNCA.f. */
#include "../include/sixs_ctx.h"
#include <math.h>
#include <string.h>
#include <stdlib.h>

#include "gauss.h"

/**
 * \brief Expand the aerosol phase function into Legendre polynomial
 * coefficients.
 *
 * Decomposes \c ctx->polar.pha[] (evaluated at the Gauss quadrature nodes) into
 * coefficients \c ctx->polar.betal[] using Gauss-Legendre quadrature:
 * \f[
 *   \beta_k = \frac{2k+1}{2} \sum_j w_j \, P(\mu_j) \, P_k(\mu_j)
 * \f]
 * Negative coefficients and all higher-order terms beyond the first negative
 * coefficient are zeroed (delta-M truncation).
 *
 * Ported from 6SV2.1 TRUNCA.f.
 *
 * \param[in,out] ctx    6SV context; reads \c ctx->polar.pha[], writes \c
 * ctx->polar.betal[].
 * \param[in]     ipol   0 = scalar only; non-zero = include polarization.
 * \param[out]    coeff  Truncation coefficient; always set to 0 (no truncation
 * applied).
 */
void sixs_trunca(SixsCtx *ctx, int ipol, float *coeff)
{
    int nbmu = ctx->quad.nquad; /* e.g. 83 */

    /* Set up Gauss quadrature with special endpoints at -1, 0, +1 */
    float cgaus_S[NQ_MAX];
    float pdgs_S[NQ_MAX];
    sixs_gauss_setup(nbmu, cgaus_S, pdgs_S);

    int ncoeff = nbmu - 2; /* 0 .. nbmu-3 */
    float deltal[NQ_P + 1] = {0.0f};
    for (int k = 0; k < ncoeff; k++) {
        ctx->polar.alphal[k] = 0.0f;
        ctx->polar.betal[k] = 0.0f;
        ctx->polar.gammal[k] = 0.0f;
        ctx->polar.zetal[k] = 0.0f;
    }

    /* Compute betal[k] = (2k+1)/2 * sum_j pha[j] * w[j] * P_k(cos_j) */
    /* Use double precision to accumulate; pl uses offset pointer trick */
    double pl_arr[NQ_MAX + 2]; /* pl_arr[k+1] = P_k */
    double *pl = pl_arr + 1;   /* so pl[-1], pl[0], pl[k] work */

    for (int j = 0; j < nbmu; j++) {
        double x = (double)ctx->polar.pha[j] * (double)pdgs_S[j];
        double rm = (double)cgaus_S[j];
        pl[-1] = 0.0;
        pl[0] = 1.0;
        for (int k = 0; k < ncoeff; k++) {
            pl[k + 1] =
                ((2 * k + 1.0) * rm * pl[k] - k * pl[k - 1]) / (k + 1.0);
            ctx->polar.betal[k] += (float)(x * pl[k]);
        }
    }

    /* Normalise and zero out negative coefficients */
    for (int k = 0; k < ncoeff; k++) {
        ctx->polar.betal[k] =
            (float)((2 * k + 1.0) * 0.5 * ctx->polar.betal[k]);
        if (ctx->polar.betal[k] < 0.0f) {
            for (int j = k; j < ncoeff; j++)
                ctx->polar.betal[j] = 0.0f;
            break;
        }
    }

    if (ipol) {
        double pol[NQ_P + 1];
        for (int j = 0; j < nbmu; j++) {
            double rm = (double)cgaus_S[j];
            double q = (double)ctx->polar.qha[j] * (double)pdgs_S[j];
            double u = (double)ctx->polar.uha[j] * (double)pdgs_S[j];

            memset(pol, 0, sizeof(pol));
            pol[2] = 3.0 * (1.0 - rm * rm) / (2.0 * sqrt(6.0));
            for (int k = 2; k < ncoeff; k++) {
                double d = (2.0 * k + 1.0) / sqrt((k + 3.0) * (k - 1.0));
                double e = sqrt((k + 2.0) * (k - 2.0)) / (2.0 * k + 1.0);
                pol[k + 1] = d * (rm * pol[k] - e * pol[k - 1]);
                ctx->polar.gammal[k] += (float)(q * pol[k]);
            }

            pl[-1] = 0.0;
            pl[0] = 1.0;
            for (int k = 0; k < ncoeff; k++) {
                pl[k + 1] =
                    ((2 * k + 1.0) * rm * pl[k] - k * pl[k - 1]) / (k + 1.0);
                deltal[k] += (float)(u * pl[k]);
            }
        }

        for (int k = 0; k < ncoeff; k++) {
            float scale = (2.0f * k + 1.0f) * 0.5f;
            deltal[k] *= scale;
            ctx->polar.gammal[k] *= scale;
        }

        for (int i = 2; i < ncoeff; i++) {
            double co1 =
                4.0 * (2.0 * i + 1.0) / (i * (i - 1.0) * (i + 1.0) * (i + 2.0));
            double co2 = i * (i - 1.0) / ((i + 1.0) * (i + 2.0));
            double som1 = 0.0, som2 = 0.0, som3 = 0.0, som4 = 0.0;
            for (int j = 1; j <= i / 2; j++) {
                double c2 =
                    (i - 1.0) * (i - 1.0) - 3.0 * (2.0 * j - 1.0) * (i - j);
                som1 += c2 * ctx->polar.betal[i - 2 * j];
                som2 += c2 * deltal[i - 2 * j];
            }
            for (int j = 0; j <= (i - 1) / 2; j++) {
                double c2 =
                    (i - 1.0) * (i - 1.0) - 3.0 * j * (2.0 * i - 2.0 * j - 1.0);
                som3 += c2 * ctx->polar.betal[i - 2 * j - 1];
                som4 += c2 * deltal[i - 2 * j - 1];
            }
            ctx->polar.zetal[i] =
                (float)(co2 * deltal[i] - co1 * (som2 - som3));
            ctx->polar.alphal[i] =
                (float)(co2 * ctx->polar.betal[i] - co1 * (som1 - som4));
        }

        float beta0 = ctx->polar.betal[0];
        if (fabsf(beta0) > 1e-20f) {
            for (int k = 0; k < ncoeff; k++) {
                ctx->polar.alphal[k] /= beta0;
                ctx->polar.betal[k] /= beta0;
                ctx->polar.gammal[k] /= beta0;
                ctx->polar.zetal[k] /= beta0;
            }
        }
    }

    *coeff = 0.0f; /* no truncation applied in 6SV2.1 */
}
