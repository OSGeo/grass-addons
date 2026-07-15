/**
 * \file uncertainty.h
 * \brief Per-band reflectance uncertainty propagation.
 *
 * Propagates two uncertainty sources through the algebraic Lambertian inversion:
 *
 *   1. **Instrument noise** — noise-equivalent delta radiance (NEDL) is
 *      estimated from the darkest 5 %% of pixels (or supplied externally) and
 *      propagated as σ_ρ_toa → σ_rfl = σ_ρ_toa / (T_down × T_up).
 *
 *   2. **AOD uncertainty** — the LUT is evaluated at ±aod_sigma; the
 *      half-difference of the corrected reflectances gives σ_AOD.
 *
 * The two sources are combined in quadrature:
 * \f[
 *   \sigma_{rfl} = \sqrt{\sigma_{noise}^2 + \sigma_{AOD}^2}
 * \f]
 *
 * The resulting σ_rfl can be added in quadrature to the RT model discrepancy
 * from surface_model_discrepancy() before MAP regularisation.
 *
 * (C) 2025-2026 Yann. GNU GPL ≥ 2.
 *
 * \author Yann
 */
#pragma once

#include "atcorr.h"   /* LutConfig, LutArrays */

#ifdef __cplusplus
extern "C" {
#endif

/**
 * \brief Estimate the noise-equivalent delta radiance (NEDL) from a radiance array.
 *
 * Computes the standard deviation of the darkest 5 %% of finite, positive
 * radiance values as a proxy for instrument noise.
 *
 * \param[in] rad   TOA radiance array [npix].
 * \param[in] npix  Number of pixels.
 * \return NEDL estimate; returns 0.01 when fewer than 10 valid pixels exist.
 */
float uncertainty_estimate_nedl(const float *rad, int npix);

/**
 * \brief Per-pixel reflectance uncertainty for a single spectral band.
 *
 * Outputs \c sigma_out[npix] = sqrt(σ_noise² + σ_AOD²) via:
 *   - σ_noise = NEDL × (π d²) / (E₀ cos_SZA) / (T_down × T_up)
 *   - σ_AOD   = |ρ(AOD + Δ) − ρ(AOD − Δ)| / 2,  Δ = \p aod_sigma
 *
 * NaN pixels in \p refl_band propagate as NaN in \p sigma_out.
 *
 * \param[in]  rad_band  TOA radiance [npix]; may be NULL (NEDL used as-is).
 * \param[in]  refl_band BOA reflectance from atcorr_invert() [npix].
 * \param[in]  npix      Number of pixels.
 * \param[in]  E0        Exo-atmospheric solar irradiance [W m⁻² µm⁻¹].
 * \param[in]  d2        Squared Earth–Sun distance [AU²] from sixs_earth_sun_dist2().
 * \param[in]  cos_sza   cos(solar zenith angle).
 * \param[in]  T_down    Scene-average downward transmittance at this wavelength.
 * \param[in]  T_up      Scene-average upward transmittance at this wavelength.
 * \param[in]  s_alb     Scene-average spherical albedo at this wavelength.
 * \param[in]  R_atm     Scene-average path reflectance at this wavelength.
 * \param[in]  nedl      Noise-equivalent ΔL [W m⁻² sr⁻¹ µm⁻¹];
 *                       pass 0 to estimate from \p rad_band.
 * \param[in]  aod_sigma AOD perturbation half-width for σ_AOD (default: 0.04).
 * \param[in]  cfg       LUT grid specification (for AOD perturbation).
 * \param[in]  lut       Pre-computed LUT arrays.
 * \param[in]  wl_um     Wavelength [µm].
 * \param[in]  aod_val   Scene-average AOD at 550 nm.
 * \param[in]  h2o_val   Scene-average WVC [g/cm²].
 * \param[out] sigma_out Pre-allocated float[npix]; total reflectance σ per pixel.
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
                               float *sigma_out);

#ifdef __cplusplus
}
#endif
