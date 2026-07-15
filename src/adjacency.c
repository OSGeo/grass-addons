/**
 * \file adjacency.c
 * \brief Adjacency effect correction (Vermote et al. 1997).
 *
 * \see include/adjacency.h for the public API and algorithm description.
 */

#include "adjacency.h"
#include "spatial.h"

#define _USE_MATH_DEFINES
#include <math.h>
#include <stdlib.h>

#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif

#ifdef _OPENMP
#include <omp.h>
#endif

/**
 * \brief Compute the environmental (neighbourhood-average) reflectance.
 *
 * Applies a box filter of half-width \c filter_half pixels to \c r_boa to
 * produce the spatially averaged reflectance seen by adjacent pixels.
 *
 * \param[in]  r_boa        Surface reflectance array [nrows × ncols].
 * \param[out] r_env        Environmental reflectance output [nrows × ncols].
 * \param[in]  nrows        Number of rows.
 * \param[in]  ncols        Number of columns.
 * \param[in]  filter_half  Half-width of the averaging window in pixels.
 */
void adjacency_r_env(const float *r_boa, float *r_env,
                     int nrows, int ncols, int filter_half)
{
    spatial_box_filter(r_boa, r_env, nrows, ncols, filter_half);
}

/**
 * \brief Compute the Beer-Lambert direct (beam) transmittance for adjacency correction.
 *
 * Calculates the combined direct transmittance through Rayleigh + aerosol
 * along the two-way path (solar down + view up):
 * \f[T_\text{dir} = \exp(-\tau / \cos\theta_s) \cdot \exp(-\tau / \cos\theta_v)\f]
 *
 * The Rayleigh OD follows Hansen & Travis (1974); aerosol OD is scaled from
 * 550 nm by an Angström exponent of 1.3.
 *
 * \param[in] wl_um    Wavelength in µm.
 * \param[in] aod550   AOD at 550 nm.
 * \param[in] pressure Surface pressure in hPa.
 * \param[in] sza_deg  Solar zenith angle (degrees).
 * \param[in] vza_deg  View zenith angle (degrees).
 * \return Combined direct transmittance in [0, 1].
 */
float adjacency_T_dir(float wl_um, float aod550, float pressure,
                      float sza_deg, float vza_deg)
{
    /* Rayleigh optical depth (Hansen & Travis 1974) */
    float wl2   = wl_um * wl_um;
    float wl4   = wl2 * wl2;
    float tau_r = 0.008569f / wl4 * (1.0f + 0.0113f / wl2)
                  * (pressure / 1013.25f);

    /* Aerosol optical depth (power-law with alpha = 1.3) */
    float tau_a = aod550 * powf(wl_um / 0.55f, -1.3f);

    float tau = tau_r + tau_a;
    float us  = cosf(sza_deg * (float)(M_PI / 180.0));
    float uv  = cosf(vza_deg * (float)(M_PI / 180.0));

    return expf(-tau / us) * expf(-tau / uv);
}

/**
 * \brief Apply the Vermote (1997) adjacency effect correction in-place.
 *
 * Corrects each pixel's surface reflectance for the contribution of scattered
 * light from neighbouring surfaces:
 * \f[
 *   \rho^\text{adj}_i = \rho_i - T_\text{dir} \cdot s_\text{alb}
 *                       \cdot (\bar\rho_\text{env} - \rho_i)
 * \f]
 * where \f$\bar\rho_\text{env}\f$ is the spatially averaged reflectance over
 * a box filter with half-width determined by \c psf_radius_km and
 * \c pixel_size_m.
 *
 * \param[in,out] r_boa          Surface reflectance array [nrows × ncols]; corrected in place.
 * \param[in]     nrows          Number of rows.
 * \param[in]     ncols          Number of columns.
 * \param[in]     psf_radius_km  Environmental PSF radius (km; half-width of the averaging window).
 * \param[in]     pixel_size_m   Pixel size in metres (used to convert km → pixels).
 * \param[in]     T_scat         Combined scattering transmittance \f$T_\downarrow T_\uparrow\f$.
 * \param[in]     s_alb          Spherical albedo of the atmosphere.
 * \param[in]     wl_um          Wavelength in µm.
 * \param[in]     aod550         AOD at 550 nm (for direct transmittance calculation).
 * \param[in]     pressure       Surface pressure in hPa.
 * \param[in]     sza_deg        Solar zenith angle (degrees).
 * \param[in]     vza_deg        View zenith angle (degrees).
 */
void adjacency_correct_band(float *r_boa, int nrows, int ncols,
                             float psf_radius_km, float pixel_size_m,
                             float T_scat, float s_alb,
                             float wl_um, float aod550, float pressure,
                             float sza_deg, float vza_deg)
{
    int npix = nrows * ncols;

    /* Filter half-width: PSF radius in pixels (minimum 1) */
    int filter_half = (int)(psf_radius_km * 1000.0f / pixel_size_m + 0.5f);
    if (filter_half < 1) filter_half = 1;

    float *r_env = malloc((size_t)npix * sizeof(float));
    if (!r_env) return;

    adjacency_r_env(r_boa, r_env, nrows, ncols, filter_half);

    float T_dir  = adjacency_T_dir(wl_um, aod550, pressure, sza_deg, vza_deg);
    float T_diff = T_scat - T_dir;
    if (T_diff < 0.0f) T_diff = 0.0f;

#ifdef _OPENMP
#pragma omp parallel for schedule(static)
#endif
    for (int i = 0; i < npix; i++) {
        float r  = r_boa[i];
        float re = r_env[i];
        if (!isfinite(r) || !isfinite(re)) continue;
        float denom = 1.0f - s_alb * re;
        if (fabsf(denom) < 1e-10f) continue;
        float corr = T_diff * s_alb * (r - re) / denom;
        r_boa[i] = r + corr;
    }

    free(r_env);
}
