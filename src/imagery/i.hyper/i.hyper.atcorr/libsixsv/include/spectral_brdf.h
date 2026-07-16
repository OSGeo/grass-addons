/**
 * \file spectral_brdf.h
 * \brief Hyperspectral BRDF utilities: MCD43 disaggregation + Tikhonov smoothing.
 *
 * Provides tools to disaggregate coarse MODIS MCD43A1 kernel weights (7 bands)
 * to full hyperspectral wavelength grids (200+ bands) using piecewise-linear
 * interpolation followed by optional Tikhonov second-difference spectral
 * smoothing.
 *
 * References:
 *   - Queally, N. et al. (2022) FlexBRDF, JGR Biogeosciences 127, e2021JG006545.
 *   - Garcia-Beltran et al. (2024) HABA, Remote Sens. 16, 1405.
 *   - Schaaf, C.B. et al. (2002) MCD43 BRDF/Albedo. RSE 83:135-148.
 *   - Tikhonov, A.N. & Arsenin, V.Y. (1977) Solutions of Ill-Posed Problems.
 *
 * (C) 2025-2026 Yann. GNU GPL >= 2.
 *
 * \author Yann
 */
#pragma once

#ifdef __cplusplus
extern "C" {
#endif

/* ═══════════════════════════════════════════════════════════════════════════
 * MODIS MCD43 reference wavelengths
 * ═══════════════════════════════════════════════════════════════════════════ */

/** \brief MODIS MCD43 band centre wavelengths [µm], 7 bands.
 *
 *  Bands: B3=0.469, B4=0.555, B1=0.645, B2=0.858,
 *         B5=1.240, B6=1.640, B7=2.130
 */
extern const float MODIS_WL_UM[7];

/* ═══════════════════════════════════════════════════════════════════════════
 * Tikhonov second-difference spectral smoother
 * ═══════════════════════════════════════════════════════════════════════════ */

/**
 * \brief Tikhonov second-difference spectral smoother (in-place).
 *
 * Solves the normal equations:
 * \f[
 *   (I + \alpha^2\, D_2^T D_2)\, \mathbf{x} = \mathbf{f}
 * \f]
 * where \f$D_2\f$ is the second-difference matrix.
 * \f$D_2^T D_2\f$ is a symmetric 5-diagonal banded matrix; the system is
 * solved by Cholesky band factorization in O(5n) operations.
 *
 * \param[in,out] f     Float array of length \p n; overwritten with solution.
 * \param[in]     n     Number of spectral samples.
 * \param[in]     alpha Regularization strength (0.0 = no smoothing; ~0.1 typical).
 */
void spectral_smooth_tikhonov(float *f, int n, float alpha);

/* ═══════════════════════════════════════════════════════════════════════════
 * MCD43 7-band → hyperspectral disaggregation
 * ═══════════════════════════════════════════════════════════════════════════ */

/**
 * \brief Disaggregate 7-band MCD43 kernel weights to \p n_wl target wavelengths.
 *
 * Algorithm:
 *   1. Piecewise-linear interpolation between the 7 MCD43 anchor wavelengths
 *      (clamp-extrapolation outside [0.469, 2.130] µm).
 *   2. Optional Tikhonov second-difference spectral smoothing (alpha > 0).
 *
 * Each of the three kernel arrays (iso/vol/geo) is processed independently.
 *
 * \param[in]  fiso_7   f_iso kernel weights at MODIS_WL_UM[7].
 * \param[in]  fvol_7   f_vol kernel weights at MODIS_WL_UM[7].
 * \param[in]  fgeo_7   f_geo kernel weights at MODIS_WL_UM[7].
 * \param[in]  wl_target Target wavelengths [µm], length \p n_wl.
 * \param[in]  n_wl    Number of target wavelengths.
 * \param[in]  alpha   Tikhonov regularization strength (0 = off; ~0.1 typical).
 * \param[out] fiso_wl Caller-allocated float[n_wl]; disaggregated f_iso.
 * \param[out] fvol_wl Caller-allocated float[n_wl]; disaggregated f_vol.
 * \param[out] fgeo_wl Caller-allocated float[n_wl]; disaggregated f_geo.
 */
void mcd43_disaggregate(const float *fiso_7, const float *fvol_7, const float *fgeo_7,
                         const float *wl_target, int n_wl, float alpha,
                         float *fiso_wl, float *fvol_wl, float *fgeo_wl);

#ifdef __cplusplus
}
#endif
