/**
 * \file oe_invert.h
 * \brief Per-pixel joint AOD + H₂O retrieval via optimal estimation.
 *
 * Implements a grid-search MAP inversion over the pre-computed LUT following
 * the ISOFIT spectral-smoothness cost formulation (Thompson et al. 2019).
 *
 * **Cost function** (minimised per pixel over the LUT grid):
 * \f[
 *   J = J_{spec} + J_{H_2O} + J_{prior}
 * \f]
 *
 * - \f$J_{spec}\f$ — VIS spectral smoothness: residuals from a linear fit to
 *   the retrieved BOA reflectance at 470–870 nm, normalised by σ_spec.
 *   Over- or under-correction by aerosol produces a spectral step at 470 nm.
 *
 * - \f$J_{H_2O}\f$ — 940 nm band-depth consistency between the retrieved
 *   LUT H₂O and the measured 865/940/1040 nm radiances.
 *
 * - \f$J_{prior}\f$ — MAP regularisation:
 *   \f$ (\ln AOD - \ln AOD_{prior})^2/\sigma_a^2
 *       + (H_2O - H_2O_{prior})^2/\sigma_h^2 \f$
 *
 * After the grid search, a parabolic refinement is applied in both
 * dimensions to recover sub-grid accuracy.
 *
 * Pure computation: no GRASS dependencies.
 *
 * References:
 *   - Rodgers, C.D. (2000). Inverse Methods for Atmospheric Sounding. World Sci.
 *   - Thompson, D.R. et al. (2019). ISOFIT. RSE 224:260–271.
 *   - Guanter, L. et al. (2009). Spectral-smoothness OE. RSE 113:2192–2201.
 *
 * (C) 2025-2026 Yann. GNU GPL ≥ 2.
 *
 * \author Yann
 */
#pragma once

#include "atcorr.h"   /* LutConfig, LutArrays, atcorr_lut_interp_pixel */

#ifdef __cplusplus
extern "C" {
#endif

/**
 * \brief Joint per-pixel AOD + H₂O retrieval by grid-search MAP inversion.
 *
 * For each pixel, tests every (AOD_i, H₂O_j) LUT grid point, selects the
 * minimum-cost point, and refines with parabolic interpolation.  Pixels with
 * all-NaN VIS measurements are filled with the prior values.
 *
 * Computation is OpenMP-parallelised over pixels; each thread uses a
 * stack-allocated 64-band work buffer.
 *
 * \param[in]  cfg          LUT grid specification (wavelengths, AOD/H₂O grid, geometry).
 * \param[in]  lut          Pre-computed LUT arrays.
 * \param[in]  rho_toa_vis  TOA reflectance at VIS diagnostic bands,
 *                          band-interleaved: \c [npix × n_vis].
 *                          Pixel \c i at band \c b: \c rho_toa_vis[i*n_vis + b].
 * \param[in]  npix         Number of pixels.
 * \param[in]  n_vis        Number of VIS diagnostic bands (e.g. 4 for 470/550/660/870 nm).
 * \param[in]  vis_wl       Central wavelengths of the VIS bands [µm], length \p n_vis.
 * \param[in]  L_865        TOA radiance near 865 nm [npix]; NULL → disable J_H₂O.
 * \param[in]  L_940        TOA radiance near 940 nm [npix]; NULL → disable J_H₂O.
 * \param[in]  L_1040       TOA radiance near 1040 nm [npix]; NULL → disable J_H₂O.
 * \param[in]  sza_deg      Solar zenith angle [degrees].
 * \param[in]  vza_deg      View zenith angle [degrees].
 * \param[in]  aod_prior    Scene-mean AOD prior (e.g. from retrieve_aod_ddv()).
 * \param[in]  h2o_prior    Scene-mean H₂O prior [g/cm²] (e.g. from retrieve_h2o_940()).
 * \param[in]  sigma_aod    Prior uncertainty in log-AOD space (typical: 0.5).
 * \param[in]  sigma_h2o    Prior uncertainty in H₂O [g/cm²] (typical: 1.0).
 * \param[in]  sigma_spec   Observation σ for spectral smoothness cost
 *                          [reflectance units] (typical: 0.01).
 * \param[in]  fwhm_940_um  FWHM of the 940 nm band [µm]; used to scale K₉₄₀
 *                          via K = 0.036 × (50 nm / FWHM)^0.90.  Pass 0 to use
 *                          the MODIS broadband value K=0.036 (no scaling).
 * \param[out] out_aod      Pre-allocated float[npix]; retrieved AOD at 550 nm.
 * \param[out] out_h2o      Pre-allocated float[npix]; retrieved WVC [g/cm²].
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
        float            *out_h2o);

#ifdef __cplusplus
}
#endif
