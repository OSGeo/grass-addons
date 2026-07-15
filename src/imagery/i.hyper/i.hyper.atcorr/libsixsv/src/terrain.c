/**
 * \file terrain.c
 * \brief Terrain illumination and transmittance correction for tilted surfaces.
 *
 * Implements the topographic corrections described in:
 *   Richter & Schläpfer (2002), Topographic correction of satellite data using
 *   a modified Minnaert approach; also consistent with Tanre et al. (1992) and
 *   the correction used in ATCOR and PARGE.
 *
 * Reference for diffuse skyview decomposition:
 *   Häberle & Richter (2015), ATCOR Technical Report.
 *
 * Physics:
 *   On a tilted surface the downward solar irradiance is split into:
 *     E_direct  = E0 × T_down_dir × cos_i       [local incidence]
 *     E_diffuse = E0 × T_down_dif × Vd          [skyview-weighted]
 *   where Vd = (1 + cos(slope)) / 2 and T_down_dif = T_down − T_down_dir.
 *
 *   The effective downward transmittance that enters the inversion is:
 *     T_down_eff = T_down_dir × (cos_i / cos_sza) + T_down_dif × Vd
 *   (divided by E0×cos_sza as in the flat-surface formula).
 */
#include "../include/terrain.h"
#include <math.h>

#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif

/**
 * \brief Compute the cosine of the local solar incidence angle on a tilted surface.
 *
 * Uses the Iqbal (1983) standard topographic illumination model:
 * \f[
 *   \cos i = \cos\theta_s \cos s + \sin\theta_s \sin s \cos(\phi_s - \phi_a)
 * \f]
 * where \f$\theta_s\f$ is SZA, \f$s\f$ is slope, \f$\phi_s\f$ is solar azimuth,
 * and \f$\phi_a\f$ is terrain aspect.
 *
 * \param[in] sza_deg    Solar zenith angle (degrees).
 * \param[in] saa_deg    Solar azimuth angle (degrees, CW from North).
 * \param[in] slope_deg  Terrain slope (degrees, 0 = horizontal).
 * \param[in] aspect_deg Terrain aspect (degrees, CW from North).
 * \return Cosine of the local incidence angle; negative values indicate shadow.
 */
float cos_incidence(float sza_deg, float saa_deg,
                    float slope_deg, float aspect_deg)
{
    float sza    = sza_deg    * (float)(M_PI / 180.0);
    float saa    = saa_deg    * (float)(M_PI / 180.0);
    float slope  = slope_deg  * (float)(M_PI / 180.0);
    float aspect = aspect_deg * (float)(M_PI / 180.0);

    /* Standard topographic illumination model (Iqbal 1983) */
    return cosf(sza) * cosf(slope)
         + sinf(sza) * sinf(slope) * cosf(saa - aspect);
}

/**
 * \brief Compute the skyview factor for a tilted surface.
 *
 * Approximates the fraction of the hemisphere visible from a slope as:
 * \f[ V_d = \frac{1 + \cos s}{2} \f]
 * where \f$s\f$ is the slope angle.  For a horizontal surface, \f$V_d = 1\f$.
 *
 * \param[in] slope_deg Terrain slope in degrees.
 * \return Skyview factor in [0, 1].
 */
float skyview_factor(float slope_deg)
{
    float s = slope_deg * (float)(M_PI / 180.0);
    return (1.0f + cosf(s)) * 0.5f;
}

/**
 * \brief Compute the effective downward transmittance for a tilted surface.
 *
 * Replaces the flat-surface \c T_down with the topographically corrected
 * effective value:
 * \f[
 *   T^\text{eff}_\downarrow = T^\text{dir}_\downarrow \frac{\cos i}{\cos\theta_s}
 *                             + (T_\downarrow - T^\text{dir}_\downarrow) V_d
 * \f]
 * On shadowed pixels (\f$\cos i \le 0\f$), only the diffuse term survives.
 *
 * \param[in] T_down     Total downward transmittance from the flat-surface LUT.
 * \param[in] T_down_dir Direct (beam) component of the downward transmittance.
 * \param[in] cos_sza    Cosine of the solar zenith angle.
 * \param[in] cos_i      Cosine of the local incidence angle (from cos_incidence()).
 * \param[in] V_d        Skyview factor (from skyview_factor()).
 * \return Effective downward transmittance for the tilted pixel.
 */
float atcorr_terrain_T_down(float T_down, float T_down_dir,
                             float cos_sza, float cos_i, float V_d)
{
    float T_dif = T_down - T_down_dir;
    if (T_dif < 0.0f) T_dif = 0.0f;

    if (cos_i <= 0.0f)
        /* Topographic shadow: only diffuse sky radiation reaches surface */
        return T_dif * V_d;

    /* Illuminated: direct component scaled by local/scene incidence ratio */
    float cos_sza_safe = (cos_sza > 1e-6f) ? cos_sza : 1e-6f;
    return T_down_dir * (cos_i / cos_sza_safe) + T_dif * V_d;
}

/**
 * \brief Scale the upward transmittance for a per-pixel view zenith angle.
 *
 * The LUT stores \c T_up at the scene-mean VZA.  For pixels with a
 * different VZA (e.g. off-nadir pushbroom sensors, or after terrain correction),
 * Beer-Lambert path scaling gives:
 * \f[
 *   T_\uparrow(\text{px}) = T_\uparrow(\text{ref})^{\cos\theta^\text{ref}_v / \cos\theta^\text{px}_v}
 * \f]
 *
 * \param[in] T_up           Upward transmittance at the reference VZA.
 * \param[in] cos_vza_ref    Cosine of the reference view zenith angle (scene mean).
 * \param[in] vza_pixel_deg  Per-pixel view zenith angle (degrees).
 * \return Scaled upward transmittance for the pixel VZA.
 */
float atcorr_terrain_T_up(float T_up, float cos_vza_ref, float vza_pixel_deg)
{
    if (T_up <= 0.0f || T_up >= 1.0f) return T_up;

    float cos_px = cosf(vza_pixel_deg * (float)(M_PI / 180.0));
    if (cos_px < 1e-4f) cos_px = 1e-4f;
    if (cos_vza_ref < 1e-4f) cos_vza_ref = 1e-4f;

    /* T_up ∝ exp(−τ / cos_vza)  →  T_up(px) = T_up(ref) ^ (cos_ref / cos_px) */
    return powf(T_up, cos_vza_ref / cos_px);
}
