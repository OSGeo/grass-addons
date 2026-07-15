/**
 * \file adjacency.h
 * \brief Adjacency effect correction following Vermote et al. (1997).
 *
 * In heterogeneous scenes, diffuse transmittance carries signal from
 * neighbouring pixels (the "adjacency effect").  The correction replaces
 * the uniform-surface assumption by computing an environmental
 * (spatially-averaged) reflectance and subtracting its excess contribution:
 * \f[
 *   T_{diff} = \mathrm{clip}(T_{scat} - T_{dir},\; 0,\; T_{scat})
 * \f]
 * \f[
 *   r_{BOA} \leftarrow r_{BOA}
 *     + \frac{T_{diff} \cdot s \cdot (r_{BOA} - r_{env})}{1 - s \cdot r_{env}}
 * \f]
 *
 * The main entry point is adjacency_correct_band(), which calls
 * adjacency_r_env() and adjacency_T_dir() internally.
 *
 * Reference:
 *   Vermote, E.F. et al. (1997). Second simulation of the satellite signal
 *   in the solar spectrum (6S). IEEE TGRS 35:675–686.
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
 * \brief Compute the environmental (spatially-averaged) reflectance map.
 *
 * Applies a separable box filter of half-width \p filter_half pixels to
 * the BOA reflectance map.  NaN pixels are excluded from the average.
 *
 * \param[in]  r_boa       Input BOA reflectance float[nrows × ncols].
 * \param[out] r_env       Output environmental reflectance float[nrows × ncols]
 *                         (must not alias r_boa).
 * \param[in]  nrows       Image height in pixels.
 * \param[in]  ncols       Image width in pixels.
 * \param[in]  filter_half Box-filter half-width in pixels.
 */
void adjacency_r_env(const float *r_boa, float *r_env,
                     int nrows, int ncols, int filter_half);

/**
 * \brief Beer-Lambert two-way direct transmittance (no multiple scattering).
 *
 * \f[
 *   \tau = \tau_R(\lambda, P) + \tau_a(\lambda, \tau_{550})
 *   \quad T_{dir} = \exp(-\tau/\cos\theta_s) \cdot \exp(-\tau/\cos\theta_v)
 * \f]
 * where τ_R is the Rayleigh optical depth and τ_a is the aerosol optical depth.
 *
 * \param[in] wl_um    Wavelength [µm].
 * \param[in] aod550   AOD at 550 nm.
 * \param[in] pressure Atmospheric pressure [hPa].
 * \param[in] sza_deg  Solar zenith angle [degrees].
 * \param[in] vza_deg  View zenith angle [degrees].
 * \return Two-way direct transmittance T_dir ∈ (0, 1].
 */
float adjacency_T_dir(float wl_um, float aod550, float pressure,
                      float sza_deg, float vza_deg);

/**
 * \brief Apply the Vermote 1997 adjacency correction in-place to one band.
 *
 * Computes the environmental reflectance box filter and the direct
 * transmittance, then applies the adjacency correction to every pixel.
 *
 * \param[in,out] r_boa          BOA reflectance float[nrows × ncols], updated in place.
 * \param[in]     nrows          Image height in pixels.
 * \param[in]     ncols          Image width in pixels.
 * \param[in]     psf_radius_km  Environmental PSF radius [km] (must be > 0).
 * \param[in]     pixel_size_m   Pixel size [m] (must be > 0).
 * \param[in]     T_scat         Two-way total scattering transmittance at this wavelength.
 * \param[in]     s_alb          Spherical albedo at this wavelength.
 * \param[in]     wl_um          Wavelength [µm].
 * \param[in]     aod550         AOD at 550 nm.
 * \param[in]     pressure       Atmospheric pressure [hPa].
 * \param[in]     sza_deg        Solar zenith angle [degrees].
 * \param[in]     vza_deg        View zenith angle [degrees].
 */
void adjacency_correct_band(float *r_boa, int nrows, int ncols,
                             float psf_radius_km, float pixel_size_m,
                             float T_scat, float s_alb,
                             float wl_um, float aod550, float pressure,
                             float sza_deg, float vza_deg);

#ifdef __cplusplus
}
#endif
