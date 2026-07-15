/* Spectral interpolation — ported from 6SV2.1 INTERP.f
 * Interpolates ctx->disc quantities from 20 reference wavelengths
 * to any specific wavelength using log-log interpolation. */
#include "../include/sixs_ctx.h"
#include <math.h>
#include <string.h>

/**
 * \brief Power-law (log-log) spectral interpolation.
 *
 * Interpolates between two spectral values assuming a power-law dependence
 * \f$ y = \beta \lambda^\alpha \f$, where \f$\alpha\f$ is fitted from the
 * two bracketing points.  Falls back to linear interpolation in log-wavelength
 * space if either endpoint is non-positive.
 *
 * \param[in]  y_inf   Value at the lower wavelength bracket \c wl_inf.
 * \param[in]  y_sup   Value at the upper wavelength bracket.
 * \param[in]  wl_inf  Lower wavelength (µm).
 * \param[in]  coef    \f$\ln(wl\_sup / wl\_inf)\f$, pre-computed by the caller.
 * \param[in]  wl      Target wavelength (µm).
 * \return Interpolated value at \c wl.
 */
static float log_interp(float y_inf, float y_sup,
                          float wl_inf, float coef, float wl)
{
    if (y_inf <= 1e-30f || y_sup <= 1e-30f) {
        /* Linear fallback */
        float t = logf(wl / wl_inf) / coef;
        return y_inf + t * (y_sup - y_inf);
    }
    float alpha = logf(y_sup / y_inf) / coef;
    float beta  = y_inf / powf(wl_inf, alpha);
    return beta * powf(wl, alpha);
}

/**
 * \brief Interpolate 6SV discrete-wavelength RT outputs to any wavelength.
 *
 * Performs log-log power-law spectral interpolation of the atmospheric
 * correction parameters precomputed by sixs_discom() at the 20 reference
 * wavelengths to an arbitrary target wavelength.  Outputs path reflectance,
 * downward/upward transmittances, spherical albedo, and optional optical depths.
 *
 * The direct downward transmittance \c T_down_dir is also interpolated if the
 * output pointer is non-NULL; this enables the diffuse/direct split required
 * for terrain illumination correction.
 *
 * Ported from 6SV2.1 INTERP.f.
 *
 * \param[in]  ctx          6SV context with \c disc and \c aer populated by sixs_discom().
 * \param[in]  iaer         Aerosol model index (0 = no aerosol).
 * \param[in]  wl           Target wavelength (µm).
 * \param[in]  taer55       Total aerosol optical depth at 550 nm.
 * \param[in]  taer55p      AOD above sensor altitude (reserved, currently unused).
 * \param[out] roatm        Atmospheric path reflectance (Rayleigh + aerosol).
 * \param[out] T_down       Total downward transmittance (direct + diffuse).
 * \param[out] T_up         Total upward transmittance (direct + diffuse).
 * \param[out] s_alb        Atmospheric spherical albedo.
 * \param[out] tray_out     Rayleigh optical depth at \c wl (may be NULL).
 * \param[out] taer_out     Aerosol optical depth at \c wl (may be NULL).
 * \param[out] T_down_dir_out  Direct (beam-only) downward transmittance (may be NULL).
 */
void sixs_interp(const SixsCtx *ctx, int iaer, float wl,
                  float taer55, float taer55p,
                  float *roatm, float *T_down, float *T_up, float *s_alb,
                  float *tray_out, float *taer_out,
                  float *T_down_dir_out)
{
    const SixsDisc *d = &ctx->disc;

    /* Defaults */
    *roatm = 0.0f; *T_down = 1.0f; *T_up = 1.0f; *s_alb = 0.0f;
    if (tray_out) *tray_out = 0.0f;
    if (taer_out) *taer_out = 0.0f;

    /* Find bracketing wavelength indices (0-based) */
    int linf = 0;
    for (int ll = 0; ll < NWL_DISC - 1; ll++) {
        if (wl > d->wldis[ll] && wl <= d->wldis[ll+1]) { linf = ll; break; }
    }
    if (wl > d->wldis[NWL_DISC - 1]) linf = NWL_DISC - 2;
    int lsup = linf + 1;

    float wl_inf = d->wldis[linf];
    float wl_sup = d->wldis[lsup];
    float coef   = logf(wl_sup / wl_inf);   /* log(wl ratio) */

    /* ---- Atmospheric reflectance: romix = roatm[1] ---- */
    float roatm_inf = d->roatm[1][linf];
    float roatm_sup = d->roatm[1][lsup];
    *roatm = log_interp(roatm_inf, roatm_sup, wl_inf, coef, wl);

    /* ---- Rayleigh optical depth ---- */
    float tray = log_interp(d->trayl[linf], d->trayl[lsup], wl_inf, coef, wl);
    if (tray_out) *tray_out = tray;

    /* ---- Aerosol optical depth ---- */
    float taer = 0.0f;
    if (iaer != 0 && ctx->aer.ext[7] > 0.0f) {
        float ext_inf = ctx->aer.ext[linf], ext_sup = ctx->aer.ext[lsup];
        float alpha = logf(ext_sup / ext_inf) / coef;
        float beta  = ext_inf / powf(wl_inf, alpha);
        float ext_wl = beta * powf(wl, alpha);
        taer = taer55 * ext_wl / ctx->aer.ext[7];
        if (taer_out) *taer_out = taer;
    }

    /* ---- Downward transmittance: dtott = dtotc * dtotr ---- */
    /* dtotr = Rayleigh (dir + dif), dtotr at wl */
    float drinf = d->dtdif[0][linf] + d->dtdir[0][linf];
    float drsup = d->dtdif[0][lsup] + d->dtdir[0][lsup];
    float dtotr = log_interp(drinf, drsup, wl_inf, coef, wl);

    /* dtotc = ratio total / Rayleigh, interpolated */
    float dtinf = d->dtdif[1][linf] + d->dtdir[1][linf];
    float dtsup = d->dtdif[1][lsup] + d->dtdir[1][lsup];
    float dtotc;
    if (drinf > 1e-10f && drsup > 1e-10f) {
        float alpha = logf((dtsup * drinf) / (dtinf * drsup)) / coef;
        float beta  = (dtinf / drinf) / powf(wl_inf, alpha);
        dtotc = beta * powf(wl, alpha);
    } else {
        dtotc = (drinf > 0.0f) ? dtinf / drinf : 1.0f;
    }
    *T_down = dtotc * dtotr;

    /* ---- Upward transmittance: utott = utotc * utotr ---- */
    float urinf = d->utdif[0][linf] + d->utdir[0][linf];
    float ursup = d->utdif[0][lsup] + d->utdir[0][lsup];
    float utotr = log_interp(urinf, ursup, wl_inf, coef, wl);

    float utinf = d->utdif[1][linf] + d->utdir[1][linf];
    float utsup = d->utdif[1][lsup] + d->utdir[1][lsup];
    float utotc;
    if (urinf > 1e-10f && ursup > 1e-10f) {
        float alpha = logf((utsup * urinf) / (utinf * ursup)) / coef;
        float beta  = (utinf / urinf) / powf(wl_inf, alpha);
        utotc = beta * powf(wl, alpha);
    } else {
        utotc = (urinf > 0.0f) ? utinf / urinf : 1.0f;
    }
    *T_up = utotc * utotr;

    /* ---- Spherical albedo: astot ---- */
    *s_alb = log_interp(d->sphal[1][linf], d->sphal[1][lsup], wl_inf, coef, wl);

    /* ---- Direct (beam) downward transmittance (scattering only) ---- *
     * d->dtdir[1] = combined (Rayleigh + aerosol) direct transmittance at 20 wl.
     * Log-log interpolated then scaled by the same ratio as T_down so that
     * T_down_dir / T_down is consistent with the DISCOM ratio at the 20 bands. */
    if (T_down_dir_out) {
        float ddinf = d->dtdir[1][linf];
        float ddsup = d->dtdir[1][lsup];
        *T_down_dir_out = log_interp(ddinf, ddsup, wl_inf, coef, wl);
    }

    (void)taer55p;  /* used by 6SV for taerp; not needed for our inversion */
}

/**
 * \brief Interpolate Stokes Q and U path reflectance components to any wavelength.
 *
 * Linearly interpolates (in log-wavelength space) the Q and U Stokes components
 * of the atmospheric path reflectance from the 20 reference wavelengths
 * precomputed by sixs_discom().  Linear rather than log-log interpolation is
 * used because Q and U can be negative.
 *
 * \param[in]  ctx          6SV context with \c disc populated by sixs_discom().
 * \param[in]  wl           Target wavelength (µm).
 * \param[out] roatmq_out   Stokes Q path reflectance at \c wl (may be NULL).
 * \param[out] roatmu_out   Stokes U path reflectance at \c wl (may be NULL).
 */
void sixs_interp_polar(const SixsCtx *ctx, float wl,
                        float *roatmq_out, float *roatmu_out)
{
    const SixsDisc *d = &ctx->disc;

    /* Find bracketing wavelength pair */
    int linf = 0;
    for (int ll = 0; ll < NWL_DISC - 1; ll++) {
        if (wl > d->wldis[ll] && wl <= d->wldis[ll + 1]) { linf = ll; break; }
    }
    if (wl > d->wldis[NWL_DISC - 1]) linf = NWL_DISC - 2;
    int lsup = linf + 1;

    float wl_inf = d->wldis[linf];
    float wl_sup = d->wldis[lsup];
    float dw     = wl_sup - wl_inf;

    /* Linear fraction (log-space for consistency with the wavelength axis) */
    float t = (dw > 1e-10f) ? logf(wl / wl_inf) / logf(wl_sup / wl_inf) : 0.0f;

    /* Linear interpolation (Q/U can be negative, so log-log is not applicable) */
    if (roatmq_out)
        *roatmq_out = d->roatmq[1][linf] + t * (d->roatmq[1][lsup] - d->roatmq[1][linf]);
    if (roatmu_out)
        *roatmu_out = d->roatmu[1][linf] + t * (d->roatmu[1][lsup] - d->roatmu[1][linf]);
}
