/**
 * \file spatial.h
 * \brief Spatial filtering utilities for atmospheric parameter maps.
 *
 * Provides NaN-safe Gaussian and box filters for 2-D float rasters:
 *   - spatial_gaussian_filter() — separable Gaussian smoothing (in-place)
 *   - spatial_box_filter()      — separable uniform-mean filter
 *
 * Both functions handle NaN pixels by excluding them from neighbourhood
 * averages; NaN output pixels are restored where all neighbours were NaN.
 * Boundary pixels use edge-replication (nearest-pixel) padding.
 * Row loops are OpenMP-parallelised.
 *
 * Typical uses:
 *   - Smooth per-pixel AOD/H₂O raster maps before correction.
 *   - Compute the environmental reflectance box filter needed by
 *     adjacency_correct_band() (via adjacency_r_env()).
 *
 * (C) 2025-2026 Yann. GNU GPL ≥ 2.
 *
 * \author Yann
 */
#pragma once

#ifdef __cplusplus
extern "C" {
#endif

/**
 * \brief Separable Gaussian filter applied in-place to a 2-D float array.
 *
 * Applies a Gaussian blur with standard deviation \p sigma pixels.
 * Kernel half-width is ceil(3·σ); edge-replication padding.
 * NaN pixels are excluded from the weighted average.
 *
 * A σ of 0 or negative is a no-op.
 *
 * \param[in,out] data   float[nrows × ncols] array, modified in place.
 * \param[in]     nrows  Image height in pixels.
 * \param[in]     ncols  Image width in pixels.
 * \param[in]     sigma  Gaussian standard deviation [pixels].
 */
void spatial_gaussian_filter(float *data, int nrows, int ncols, float sigma);

/**
 * \brief Separable box (uniform mean) filter.
 *
 * Applies a (2·half+1) × (2·half+1) uniform averaging filter.
 * NaN pixels are excluded; output is NaN only where all neighbours are NaN.
 *
 * \p out must not alias \p data.
 *
 * \param[in]  data        Input float[nrows × ncols].
 * \param[out] out         Output float[nrows × ncols] (must not alias data).
 * \param[in]  nrows       Image height in pixels.
 * \param[in]  ncols       Image width in pixels.
 * \param[in]  filter_half Half-width of the box filter in pixels.
 */
void spatial_box_filter(const float *data, float *out,
                        int nrows, int ncols, int filter_half);

#ifdef __cplusplus
}
#endif
