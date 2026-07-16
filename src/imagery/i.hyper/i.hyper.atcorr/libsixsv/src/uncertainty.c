/**
 * \file uncertainty.c
 * \brief Per-band reflectance uncertainty propagation (noise + AOD perturbation).
 *
 * \see include/uncertainty.h for the public API.
 */

#include "uncertainty.h"
#include "../include/atcorr.h"

#define _USE_MATH_DEFINES
#include <math.h>
#include <stdlib.h>
#include <string.h>

#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif

#ifdef _OPENMP
#include <omp.h>
#endif

/* Forward declaration: trilinear LUT point interpolation (src/lut.c) */
void atcorr_lut_interp_pixel(const LutConfig *cfg, const LutArrays *lut,
                               float aod_val, float h2o_val, float wl_um,
                               float *R_atm, float *T_down,
                               float *T_up,  float *s_alb);

/** \cond INTERNAL */
/* qsort comparator */
static int cmp_float_asc(const void *a, const void *b)
{
    float fa = *(const float *)a;
    float fb = *(const float *)b;
    return (fa > fb) - (fa < fb);
}

/** \endcond */

/**
 * \brief Estimate the Noise-Equivalent Radiance Difference (NEDL) from image data.
 *
 * Estimates the instrument noise level from the radiance distribution of the
 * darkest 5% of valid (finite, positive) pixels.  The returned value is the
 * standard deviation of that dark-pixel sample — a proxy for NEDL in the
 * absence of calibration data.
 *
 * \param[in] rad   Radiance array [npix] (W m⁻² sr⁻¹ µm⁻¹).
 * \param[in] npix  Number of pixels.
 * \return NEDL estimate; falls back to 0.01 if fewer than 10 valid pixels.
 */
float uncertainty_estimate_nedl(const float *rad, int npix)
{
    float *buf = malloc((size_t)npix * sizeof(float));
    if (!buf) return 0.01f;

    int n = 0;
    for (int i = 0; i < npix; i++)
        if (isfinite(rad[i]) && rad[i] > 0.0f) buf[n++] = rad[i];

    if (n < 10) { free(buf); return 0.01f; }

    qsort(buf, n, sizeof(float), cmp_float_asc);

    /* Standard deviation of the darkest 5 % */
    int p5 = (int)(0.05f * n);
    if (p5 < 5) p5 = 5;

    double sum = 0.0, sum2 = 0.0;
    for (int i = 0; i < p5; i++) {
        sum  += buf[i];
        sum2 += (double)buf[i] * buf[i];
    }
    double mean = sum / p5;
    double var  = sum2 / p5 - mean * mean;

    free(buf);
    return (var > 0.0) ? (float)sqrt(var) : 0.01f;
}

/**
 * \brief Compute per-pixel reflectance uncertainty for one spectral band.
 *
 * Propagates two independent error sources through the atmospheric correction
 * inversion for every pixel in the band:
 * 1. **Instrument noise** — NEDL converted to TOA reflectance uncertainty via
 *    \f$\sigma_\rho^\text{noise} = \pi \cdot \text{NEDL} \cdot d^2 / (E_0 \cos\theta_s)\f$,
 *    then propagated through the 6SV inversion Jacobian.
 * 2. **AOD uncertainty** — re-runs the inversion at \f$\text{AOD} \pm \sigma_\text{AOD}\f$
 *    and takes half the difference as a one-sigma AOD perturbation error.
 *
 * If \c nedl ≤ 0 it is estimated from \c rad_band via uncertainty_estimate_nedl().
 *
 * \param[in]  rad_band   Radiance array for this band [npix] (W m⁻² sr⁻¹ µm⁻¹); may be NULL.
 * \param[in]  refl_band  Corrected surface reflectance array [npix].
 * \param[in]  npix       Number of pixels.
 * \param[in]  E0         Exo-atmospheric solar irradiance at band centre (W m⁻² µm⁻¹).
 * \param[in]  d2         Earth-Sun distance squared (AU²).
 * \param[in]  cos_sza    Cosine of the solar zenith angle.
 * \param[in]  T_down     Downward transmittance at the scene-mean AOD.
 * \param[in]  T_up       Upward transmittance at the scene-mean AOD.
 * \param[in]  s_alb      Spherical albedo at the scene-mean AOD.
 * \param[in]  R_atm      Atmospheric path reflectance at the scene-mean AOD.
 * \param[in]  nedl       Instrument NEDL (W m⁻² sr⁻¹ µm⁻¹); 0 → estimate from \c rad_band.
 * \param[in]  aod_sigma  One-sigma AOD uncertainty for the perturbation test.
 * \param[in]  cfg        LUT configuration (used for AOD perturbation LUT query).
 * \param[in]  lut        Precomputed LUT arrays.
 * \param[in]  wl_um      Wavelength in µm.
 * \param[in]  aod_val    Scene-mean AOD at 550 nm.
 * \param[in]  h2o_val    Scene-mean column water vapour (g cm⁻²).
 * \param[out] sigma_out  Per-pixel combined uncertainty (1σ reflectance) [npix].
 */
void uncertainty_compute_band(const float *rad_band, const float *refl_band,
                               int npix,
                               float E0, float d2, float cos_sza,
                               float T_down, float T_up,
                               float s_alb,  float R_atm,
                               float nedl,   float aod_sigma,
                               const LutConfig  *cfg,
                               const LutArrays  *lut,
                               float wl_um,
                               float aod_val, float h2o_val,
                               float *sigma_out)
{
    /* ── Instrument noise (scalar for this band) ── */
    if (nedl <= 0.0f && rad_band != NULL)
        nedl = uncertainty_estimate_nedl(rad_band, npix);
    if (nedl <= 0.0f) nedl = 0.01f;

    if (E0 <= 0.0f) E0 = 1.0f;
    if (cos_sza <= 0.0f) cos_sza = 0.01f;

    float sigma_rho_toa = (float)M_PI * nedl * (float)d2 / (E0 * cos_sza);
    float T_total = T_down * T_up;
    float sigma_noise = sigma_rho_toa / (T_total > 1e-6f ? T_total : 1e-6f);

    /* ── AOD perturbation (scalar LUT values at ±aod_sigma) ── */
    float aod_plus  = aod_val + aod_sigma;
    float aod_minus = (aod_val > aod_sigma + 0.001f)
                      ? aod_val - aod_sigma : 0.001f;

    float R1, Td1, Tu1, s1;
    float R0, Td0, Tu0, s0;
    atcorr_lut_interp_pixel(cfg, lut, aod_plus,  h2o_val, wl_um,
                             &R1, &Td1, &Tu1, &s1);
    atcorr_lut_interp_pixel(cfg, lut, aod_minus, h2o_val, wl_um,
                             &R0, &Td0, &Tu0, &s0);

    /* ── Per-pixel uncertainty: offloaded to GPU via OpenMP target ── */
#ifdef _OPENMP
#pragma omp target teams distribute parallel for \
    map(to: refl_band[0:npix]) \
    map(from: sigma_out[0:npix])
#endif
    for (int i = 0; i < npix; i++) {
        float r = refl_band[i];
        if (!isfinite(r)) { sigma_out[i] = NAN; continue; }

        /* Reconstruct rho_toa from inverted result */
        float rho_toa = R_atm + T_total * r / (1.0f - s_alb * r + 1e-10f);

        /* Invert at AOD+sigma */
        float T1 = Td1 * Tu1;
        float y1 = (rho_toa - R1) / (T1 > 1e-6f ? T1 : 1e-6f);
        float r1 = y1 / (1.0f + s1 * y1 + 1e-10f);

        /* Invert at AOD-sigma */
        float T0 = Td0 * Tu0;
        float y0 = (rho_toa - R0) / (T0 > 1e-6f ? T0 : 1e-6f);
        float r0 = y0 / (1.0f + s0 * y0 + 1e-10f);

        float sigma_aod = fabsf(r1 - r0) * 0.5f;
        sigma_out[i] = sqrtf(sigma_noise * sigma_noise + sigma_aod * sigma_aod);
    }
}
