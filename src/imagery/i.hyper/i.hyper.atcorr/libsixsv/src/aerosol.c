/* Aerosol optical properties — ported from 6SV2.1 AEROSO.f + DUST/WATE/OCEA/SOOT.f */
#include "../include/sixs_ctx.h"
#include "../include/aerosol_tables.h"
#include "../include/gas_tables.h"  /* for wldis */
#include "gauss.h"
#include <math.h>
#include <string.h>

/* Reference wavelengths (same as AEROSO wldisc) */
static const float wldisc[NWL_DISC] = {
    0.350f,0.400f,0.412f,0.443f,0.470f,0.488f,0.515f,0.550f,
    0.590f,0.633f,0.670f,0.694f,0.760f,0.860f,1.240f,1.536f,
    1.650f,1.950f,2.250f,3.750f
};

/* Component pointer arrays */
static const float * const comp_ext[4] = {
    aerosol_dust_ext, aerosol_wate_ext, aerosol_ocea_ext, aerosol_soot_ext
};
static const float * const comp_sca[4] = {
    aerosol_dust_sca, aerosol_wate_sca, aerosol_ocea_sca, aerosol_soot_sca
};
static const float * const comp_asy[4] = {
    aerosol_dust_asy, aerosol_wate_asy, aerosol_ocea_asy, aerosol_soot_asy
};
static const float (* const comp_pha[4])[83] = {
    aerosol_dust_pha, aerosol_wate_pha, aerosol_ocea_pha, aerosol_soot_pha
};

/* Mixing ratios for standard models (from 6SV2.1 main.f) [dust, wate, ocea, soot] */
static const float std_mix[3][4] = {
    { 0.70f, 0.29f, 0.00f, 0.01f },  /* continental (iaer=1) */
    { 0.05f, 0.95f, 0.00f, 0.00f },  /* maritime    (iaer=2) */
    { 0.21f, 0.30f, 0.00f, 0.49f },  /* urban       (iaer=3) */
};

/* Volume fractions (vi in 6SV) for each component — from d'Almeida 1991 */
static const float vi[4] = { 0.09f, 0.25f, 1.00f, 0.01f };

/* Forward declaration: Mie initialisation (src/mie.c) */
void sixs_mie_init(SixsCtx *ctx,
                   double r_mode, double sigma_g,
                   double m_r_550, double m_i_550);

/**
 * \brief Initialise aerosol optical properties in a 6SV context.
 *
 * Populates \c ctx->aer (extinction, single-scattering albedo, asymmetry,
 * and phase function at the 20 reference wavelengths) for the chosen standard
 * aerosol model and total AOD at 550 nm.
 *
 * For \c AEROSOL_CUSTOM (iaer = 9), the caller must have already called
 * sixs_mie_init() to populate \c ctx->aer before calling this function;
 * the function will only verify the no-aerosol path and return immediately
 * if \c taer55 ≤ 0.
 *
 * Ported from 6SV2.1 AEROSO.f.
 *
 * \param[in,out] ctx    6SV context; writes \c ctx->aer and \c ctx->polar.
 * \param[in]     iaer   Aerosol model: 0=none, 1=continental, 2=maritime,
 *                       3=urban, 5=desert (treated as continental), 9=custom Mie.
 * \param[in]     taer55 Total aerosol OD at 550 nm.
 * \param[in]     xmud   Cosine of the scattering angle (for phase-function evaluation).
 */
void sixs_aerosol_init(SixsCtx *ctx, int iaer, float taer55, float xmud) {
    if (iaer == 0 || taer55 <= 0.0f) {
        memset(&ctx->aer, 0, sizeof(ctx->aer));
        /* For pure Rayleigh: ext[8]=1 to avoid divide-by-zero in DISCOM */
        ctx->aer.ext[7] = 1.0f;
        return;
    }

    /* Custom Mie: ctx->aer already populated by sixs_mie_init() */
    if (iaer == 9) {
        /* Only rebuild ctx->polar from ctx->aer (re-use the Legendre expansion
         * that sixs_mie_init already filled).  Nothing more to do here. */
        return;
    }

    /* Map iaer to mixing index */
    int mix_idx;
    switch (iaer) {
        case 2:  mix_idx = 1; break;
        case 3:  mix_idx = 2; break;
        default: mix_idx = 0; break;  /* continental or desert */
    }

    const float *ci = std_mix[mix_idx];

    /* Compute cij (normalized concentration) using vi */
    float sigm = 0.0f;
    for (int j = 0; j < 4; j++) sigm += (ci[j] > 0.0f ? ci[j] / vi[j] : 0.0f);
    if (sigm == 0.0f) sigm = 1.0f;

    double cij[4] = {0}, sumni = 0.0;
    for (int j = 0; j < 4; j++) {
        cij[j] = (ci[j] > 0.0f) ? (ci[j] / vi[j] / sigm) : 0.0;
        sumni += cij[j] * comp_ext[j][7];  /* normalize at index 8 = 550nm */
    }
    double nis = (sumni > 0.0) ? 1.0 / sumni : 1.0;

    /* Build Gauss quadrature grid for phase function interpolation */
    float cgaus_S[NQ_MAX], pdgs_S[NQ_MAX];
    int nquad = ctx->quad.nquad;
    sixs_gauss_setup(nquad, cgaus_S, pdgs_S);

    /* Find Gauss interval for xmud */
    int j1 = 0;
    for (int k = 0; k < nquad - 1; k++) {
        if (xmud >= cgaus_S[k] && xmud < cgaus_S[k + 1]) { j1 = k; break; }
    }
    int j2 = j1 + 1;
    float coef = -(xmud - cgaus_S[j1]) / (cgaus_S[j2] - cgaus_S[j1]);

    /* Mix optical properties at each reference wavelength */
    float ext[NWL_DISC] = {0}, sca[NWL_DISC] = {0}, gasym[NWL_DISC] = {0};
    float phase[NWL_DISC] = {0};

    for (int l = 0; l < NWL_DISC; l++) {
        for (int j = 0; j < 4; j++) {
            if (cij[j] == 0.0) continue;
            float dd = comp_pha[j][l][j1] + coef * (comp_pha[j][l][j1] - comp_pha[j][l][j2]);
            ext[l]   += (float)(comp_ext[j][l] * cij[j]);
            sca[l]   += (float)(comp_sca[j][l] * cij[j]);
            gasym[l] += (float)(comp_sca[j][l] * cij[j] * comp_asy[j][l]);
            phase[l] += (float)(comp_sca[j][l] * cij[j] * dd);
        }
        if (sca[l] > 0.0f) {
            gasym[l] /= sca[l];
            phase[l] /= sca[l];
        }
        ext[l] *= (float)nis;
        sca[l] *= (float)nis;
    }

    for (int l = 0; l < NWL_DISC; l++) {
        ctx->aer.ext[l]   = ext[l];
        ctx->aer.ome[l]   = (ext[l] > 0.0f) ? sca[l] / ext[l] : 0.0f;
        ctx->aer.gasym[l] = gasym[l];
        ctx->aer.phase[l] = phase[l];
    }

    /* Build Legendre expansion in ctx->polar (for TRUNCA equivalent) */
    /* Compute betal coefficients from phase function at Gauss points */
    float pha_full[NQ_MAX];
    /* For simplicity, interpolate from 20-wavelength phase to all nquad points */
    /* Use the mixed phase function: we need to build phasel[nquad] from component data */
    /* Mix phase function at all Gauss points (for reference wavelength 8 = 550nm, l=7) */
    memset(pha_full, 0, nquad * sizeof(float));
    for (int k = 0; k < nquad; k++) {
        for (int j = 0; j < 4; j++) {
            if (cij[j] == 0.0) continue;
            pha_full[k] += (float)(comp_sca[j][7] * cij[j] * comp_pha[j][7][k]);
        }
        if (sca[7] > 0.0f) pha_full[k] /= sca[7];
    }
    memcpy(ctx->polar.pha, pha_full, nquad * sizeof(float));

    /* Compute Legendre coefficients (TRUNCA logic) */
    float pl[NQ_MAX + 2];
    for (int kk = 0; kk <= nquad - 3; kk++) ctx->polar.betal[kk] = 0.0f;
    for (int j = 0; j < nquad; j++) {
        float x   = pha_full[j] * pdgs_S[j];
        float rm  = cgaus_S[j];
        float plm1 = 0.0f, pl0 = 1.0f;
        for (int k = 0; k <= nquad - 3; k++) {
            float plnew = ((2.0f * k + 1.0f) * rm * pl0 - k * plm1) / (k + 1.0f);
            ctx->polar.betal[k] += x * pl0;
            plm1 = pl0; pl0 = plnew;
        }
    }
    for (int k = 0; k <= nquad - 3; k++) {
        ctx->polar.betal[k] *= (2.0f * k + 1.0f) * 0.5f;
        if (ctx->polar.betal[k] < 0.0f) {
            for (int j = k; j <= nquad - 3; j++) ctx->polar.betal[j] = 0.0f;
            break;
        }
    }
}
