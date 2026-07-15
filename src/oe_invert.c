/**
 * \file oe_invert.c
 * \brief Joint per-pixel AOD + H₂O MAP retrieval via LUT grid-search.
 *
 * \see include/oe_invert.h for the algorithm description and public API.
 */

#include "../include/oe_invert.h"
#include "../include/atcorr.h"     /* atcorr_invert, atcorr_lut_interp_pixel */

#define _USE_MATH_DEFINES
#include <math.h>
#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif
#include <float.h>

/**
 * \brief 1-D least-squares linear fit.
 *
 * Fits \f$y = a + b \cdot \lambda\f$ to \c n data points by ordinary least squares.
 * Used by oe_invert_aod_h2o() to assess spectral smoothness of the VIS residuals.
 *
 * \param[in]  wl     Wavelength values (predictor) [n].
 * \param[in]  y      Observed values (response) [n].
 * \param[in]  n      Number of points (must be ≥ 2).
 * \param[out] a_out  OLS intercept.
 * \param[out] b_out  OLS slope.
 */
static void _linfit(const float *wl, const float *y, int n,
                    float *a_out, float *b_out)
{
    double sw = 0, swl = 0, sy = 0, swl2 = 0, swly = 0;
    for (int i = 0; i < n; i++) {
        sw   += 1.0;
        swl  += wl[i];
        sy   += y[i];
        swl2 += (double)wl[i] * wl[i];
        swly += (double)wl[i] * y[i];
    }
    double det = sw * swl2 - swl * swl;
    if (det == 0.0) { *a_out = (float)(sy / sw); *b_out = 0.0f; return; }
    *a_out = (float)((sy * swl2 - swl * swly) / det);
    *b_out = (float)((sw * swly - swl * sy)   / det);
}

/**
 * \brief Compute the 940 nm water vapour band depth via continuum interpolation.
 *
 * Uses the continuum interpolation fraction
 * \f[\text{FRAC} = (940 - 865) / (1040 - 865) \approx 0.4286\f]
 * and returns \f$D = 1 - L_{940} / L_\text{cont}\f$, clamped to 0.
 *
 * \param[in] l865   Radiance at 865 nm.
 * \param[in] l940   Radiance at 940 nm.
 * \param[in] l1040  Radiance at 1040 nm.
 * \return Band depth D ≥ 0; −1 if any input radiance is non-positive.
 */
static float _h2o_depth(float l865, float l940, float l1040)
{
    static const float FRAC = (0.940f - 0.865f) / (1.040f - 0.865f);
    if (!(l865 > 0.0f) || !(l940 > 0.0f) || !(l1040 > 0.0f)) return -1.0f;
    float L_cont = l865 * (1.0f - FRAC) + l1040 * FRAC;
    if (L_cont <= 0.0f) return -1.0f;
    float D = 1.0f - l940 / L_cont;
    return (D < 0.0f) ? 0.0f : D;
}

/**
 * \brief Joint per-pixel MAP retrieval of AOD and column water vapour.
 *
 * For each pixel, performs a 2-D grid-search over the (AOD, H₂O) LUT axes
 * and minimises the total cost:
 * \f[
 *   J = \frac{\sum_b (\rho^\text{boa} - \hat\rho^\text{boa}_b)^2}{\sigma_\text{spec}^2}
 *     + \frac{D_{940}^2}{\sigma_\text{h2o}^2}
 *     + \frac{(\ln\text{AOD} - \ln\text{AOD}_\text{prior})^2}{\sigma_\text{aod}^2}
 * \f]
 * where the first term penalises non-smooth VIS spectra, the second anchors H₂O
 * to the 940 nm band depth, and the third is the Gaussian AOD prior.
 *
 * A parabolic sub-grid refinement step is applied around the minimum.
 *
 * \param[in]  cfg          LUT configuration.
 * \param[in]  lut          Precomputed LUT arrays.
 * \param[in]  rho_toa_vis  TOA reflectance in VIS bands [n_vis × npix], band-major.
 * \param[in]  npix         Number of pixels.
 * \param[in]  n_vis        Number of VIS bands used for spectral smoothness.
 * \param[in]  vis_wl       Wavelengths of the VIS bands in µm [n_vis].
 * \param[in]  L_865        Radiance at 865 nm [npix].
 * \param[in]  L_940        Radiance at 940 nm [npix].
 * \param[in]  L_1040       Radiance at 1040 nm [npix].
 * \param[in]  sza_deg      Solar zenith angle (degrees).
 * \param[in]  vza_deg      View zenith angle (degrees).
 * \param[in]  aod_prior    Prior AOD at 550 nm (Gaussian mean in log space).
 * \param[in]  h2o_prior    Prior column WVC in g cm⁻² (Gaussian mean).
 * \param[in]  sigma_aod    Prior uncertainty on log(AOD).
 * \param[in]  sigma_h2o    Prior uncertainty on H₂O (g cm⁻²).
 * \param[in]  sigma_spec   Expected spectral residual (dimensionless reflectance).
 * \param[in]  fwhm_940_um  Sensor FWHM at 940 nm in µm (0 = broadband default).
 * \param[out] out_aod      Retrieved per-pixel AOD [npix].
 * \param[out] out_h2o      Retrieved per-pixel WVC in g cm⁻² [npix].
 */
void oe_invert_aod_h2o(
        const LutConfig  *cfg,
        const LutArrays  *lut,
        const float      *rho_toa_vis,
        int               npix,
        int               n_vis,
        const float      *vis_wl,
        const float      *L_865,
        const float      *L_940,
        const float      *L_1040,
        float             sza_deg,
        float             vza_deg,
        float             aod_prior,
        float             h2o_prior,
        float             sigma_aod,
        float             sigma_h2o,
        float             sigma_spec,
        float             fwhm_940_um,
        float            *out_aod,
        float            *out_h2o)
{
    /* K₉₄₀ scaled by sensor FWHM (same power law as retrieve_h2o_triplet, α=0.90).
     * Tanager 6.8 nm → K≈0.217; MODIS 50 nm → K=0.036. */
    float K_940 = (fwhm_940_um > 0.0f && fwhm_940_um < 0.050f)
                  ? 0.036f * powf(0.050f / fwhm_940_um, 0.90f)
                  : 0.036f;
    float cos_sza = cosf(sza_deg * (float)(M_PI / 180.0));
    float cos_vza = cosf(vza_deg * (float)(M_PI / 180.0));
    float mu_s = (cos_sza > 0.05f) ? cos_sza : 0.05f;
    float mu_v = (cos_vza > 0.05f) ? cos_vza : 0.05f;
    float km   = K_940 * (1.0f / mu_s + 1.0f / mu_v);

    int na = cfg->n_aod;
    int nh = cfg->n_h2o;

    /* Safety: need at least 2 VIS bands for linear fit */
    int do_spec = (n_vis >= 2);

    /* Pre-allocate per-band BOA work buffer (stack is fine for n_vis ≤ 64) */
    float rho_boa_buf[64];
    if (n_vis > 64) n_vis = 64;

    float sigma_spec2 = sigma_spec  * sigma_spec;
    float sigma_aod2  = sigma_aod   * sigma_aod;
    float sigma_h2o2  = sigma_h2o   * sigma_h2o;

#ifdef _OPENMP
#pragma omp parallel for schedule(static) private(rho_boa_buf)
#endif
    for (int i = 0; i < npix; i++) {

        /* ── Check that all VIS bands are valid ── */
        int valid = 1;
        for (int b = 0; b < n_vis; b++) {
            float rt = rho_toa_vis[i * n_vis + b];
            if (!isfinite(rt) || rt <= 0.0f) { valid = 0; break; }
        }
        if (!valid) {
            out_aod[i] = aod_prior;
            out_h2o[i] = h2o_prior;
            continue;
        }

        /* ── H₂O measurement constraint ── */
        float D_940_meas = -1.0f;
        if (L_865 && L_940 && L_1040)
            D_940_meas = _h2o_depth(L_865[i], L_940[i], L_1040[i]);

        float best_cost = FLT_MAX;
        float best_aod  = aod_prior;
        float best_h2o  = h2o_prior;
        int   best_ia   = 0;
        int   best_ih   = 0;

        /* ── Grid search over (AOD, H₂O) LUT points ── */
        for (int ia = 0; ia < na; ia++) {
            float aod = cfg->aod[ia];

            for (int ih = 0; ih < nh; ih++) {
                float h2o = cfg->h2o[ih];

                /* ── J_spec: invert all VIS bands and measure smoothness ── */
                float J_spec = 0.0f;
                if (do_spec) {
                    int ok = 1;
                    for (int b = 0; b < n_vis; b++) {
                        float R, Td, Tu, s;
                        atcorr_lut_interp_pixel(cfg, lut, aod, h2o, vis_wl[b],
                                                 &R, &Td, &Tu, &s);
                        float rt = rho_toa_vis[i * n_vis + b];
                        float y = (rt - R) / (Td * Tu + 1e-10f);
                        float rboa = y / (1.0f + s * y + 1e-10f);
                        if (!isfinite(rboa) || rboa < -0.05f || rboa > 1.5f) {
                            ok = 0; break;
                        }
                        rho_boa_buf[b] = rboa;
                    }
                    if (!ok) continue;

                    /* Linear fit residuals (spectral smoothness) */
                    float a_fit, b_fit;
                    _linfit(vis_wl, rho_boa_buf, n_vis, &a_fit, &b_fit);
                    for (int b = 0; b < n_vis; b++) {
                        float fit  = a_fit + b_fit * vis_wl[b];
                        float dr   = rho_boa_buf[b] - fit;
                        J_spec    += dr * dr;
                    }
                    J_spec /= sigma_spec2;
                }

                /* ── J_h2o: H₂O band-depth consistency ── */
                float J_h2o = 0.0f;
                if (D_940_meas >= 0.0f) {
                    /* Expected D_940 for this H₂O value:
                     * D_expected = km × h2o  (Beer-Lambert linear approx) */
                    float D_expected = km * h2o;
                    if (D_expected > 0.95f) D_expected = 0.95f;
                    float dD = D_940_meas - D_expected;
                    /* Normalise by a typical D uncertainty ~0.05 */
                    J_h2o = (dD * dD) / (0.05f * 0.05f);
                }

                /* ── J_prior: MAP regularisation ── */
                float da = (logf(aod + 1e-4f) - logf(aod_prior + 1e-4f));
                float dh = h2o - h2o_prior;
                float J_prior = (da * da) / sigma_aod2 + (dh * dh) / sigma_h2o2;

                float cost = J_spec + J_h2o + J_prior;

                if (cost < best_cost) {
                    best_cost = cost;
                    best_aod  = aod;
                    best_h2o  = h2o;
                    best_ia   = ia;
                    best_ih   = ih;
                }
            }
        }

        /* ── Parabolic sub-grid refinement in AOD dimension ── */
        if (best_ia > 0 && best_ia < na - 1) {
            /* Evaluate cost at ia-1, ia, ia+1 with best_ih fixed */
            float aod_m = cfg->aod[best_ia - 1];
            float aod_p = cfg->aod[best_ia + 1];
            float h2o   = best_h2o;

            /* Cost at the three points (recompute J terms at ia±1) */
            float c[3];
            for (int k = -1; k <= 1; k++) {
                int ia2 = best_ia + k;
                float aod2 = cfg->aod[ia2];
                float J_s = 0.0f;
                if (do_spec) {
                    int ok = 1;
                    for (int b = 0; b < n_vis; b++) {
                        float R, Td, Tu, s;
                        atcorr_lut_interp_pixel(cfg, lut, aod2, h2o, vis_wl[b],
                                                 &R, &Td, &Tu, &s);
                        float rt = rho_toa_vis[i * n_vis + b];
                        float y  = (rt - R) / (Td * Tu + 1e-10f);
                        float rb = y / (1.0f + s * y + 1e-10f);
                        if (!isfinite(rb) || rb < -0.05f || rb > 1.5f) {
                            ok = 0; break;
                        }
                        rho_boa_buf[b] = rb;
                    }
                    if (ok) {
                        float a_fit, b_fit;
                        _linfit(vis_wl, rho_boa_buf, n_vis, &a_fit, &b_fit);
                        for (int b = 0; b < n_vis; b++) {
                            float dr = rho_boa_buf[b] - (a_fit + b_fit * vis_wl[b]);
                            J_s += dr * dr;
                        }
                        J_s /= sigma_spec2;
                    } else {
                        J_s = FLT_MAX;
                    }
                }
                float da2 = (logf(aod2 + 1e-4f) - logf(aod_prior + 1e-4f));
                float dh2 = h2o - h2o_prior;
                float J_p = (da2 * da2) / sigma_aod2 + (dh2 * dh2) / sigma_h2o2;
                c[k + 1] = (J_s < FLT_MAX) ? J_s + J_p : FLT_MAX;
            }

            /* Fit parabola c(Δ) = c0 + c1×Δ + c2×Δ²; minimum at Δ* = -c1/(2×c2) */
            float c0 = c[1], cm = c[0], cp = c[2];
            if (cm < FLT_MAX && cp < FLT_MAX) {
                float c2 = 0.5f * (cm - 2.0f * c0 + cp);
                float c1 = 0.5f * (cp - cm);
                if (c2 > 1e-10f) {
                    float delta = -c1 / (2.0f * c2);
                    if (delta > -1.0f && delta < 1.0f) {
                        /* Linearly interpolate AOD */
                        float ref = best_aod;
                        if (delta < 0.0f)
                            ref = aod_m + (best_aod - aod_m) * (1.0f + delta);
                        else
                            ref = best_aod + (aod_p - best_aod) * delta;
                        best_aod = ref;
                        if (best_aod < cfg->aod[0])
                            best_aod = cfg->aod[0];
                        if (best_aod > cfg->aod[na - 1])
                            best_aod = cfg->aod[na - 1];
                    }
                }
            }
        }

        /* ── Parabolic sub-grid refinement in H₂O dimension ── */
        if (best_ih > 0 && best_ih < nh - 1) {
            float h2o_m = cfg->h2o[best_ih - 1];
            float h2o_p = cfg->h2o[best_ih + 1];
            float aod   = best_aod;

            float c[3];
            for (int k = -1; k <= 1; k++) {
                int ih2   = best_ih + k;
                float h2o2 = cfg->h2o[ih2];
                float J_h = 0.0f;
                if (D_940_meas >= 0.0f) {
                    float D_exp = km * h2o2;
                    if (D_exp > 0.95f) D_exp = 0.95f;
                    float dD = D_940_meas - D_exp;
                    J_h = (dD * dD) / (0.05f * 0.05f);
                }
                float da2 = (logf(aod + 1e-4f) - logf(aod_prior + 1e-4f));
                float dh2 = h2o2 - h2o_prior;
                float J_p = (da2 * da2) / sigma_aod2 + (dh2 * dh2) / sigma_h2o2;
                c[k + 1] = J_h + J_p;
            }

            float c2 = 0.5f * (c[0] - 2.0f * c[1] + c[2]);
            float c1 = 0.5f * (c[2] - c[0]);
            if (c2 > 1e-10f) {
                float delta = -c1 / (2.0f * c2);
                if (delta > -1.0f && delta < 1.0f) {
                    float ref;
                    if (delta < 0.0f)
                        ref = h2o_m + (best_h2o - h2o_m) * (1.0f + delta);
                    else
                        ref = best_h2o + (h2o_p - best_h2o) * delta;
                    best_h2o = ref;
                    if (best_h2o < cfg->h2o[0])
                        best_h2o = cfg->h2o[0];
                    if (best_h2o > cfg->h2o[nh - 1])
                        best_h2o = cfg->h2o[nh - 1];
                }
            }
        }

        out_aod[i] = best_aod;
        out_h2o[i] = best_h2o;
    }
}
