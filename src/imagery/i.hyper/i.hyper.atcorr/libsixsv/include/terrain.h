/**
 * \file terrain.h
 * \brief Terrain illumination and transmittance correction for tilted surfaces.
 *
 * Corrects the flat-terrain assumption in the 6SV LUT for topographically
 * complex scenes following Proy et al. (1989) and Richter (1997):
 *   - Direct irradiance scales with the local incidence angle (cos_i / cos_SZA).
 *   - Diffuse irradiance scales with the skyview factor V_d.
 *   - Upward transmittance is rescaled for per-pixel view-zenith variation.
 *
 * All angle arguments are in degrees; azimuth is measured clockwise from North.
 *
 * References:
 *   - Proy, C. et al. (1989), RSE 30:37–52
 *   - Richter, R. (1997), IJRS 18:2877–2883
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
 * \brief Cosine of the local illumination angle on a tilted surface.
 *
 * \f[
 *   \cos i = \cos(\theta_s)\cos(\alpha)
 *           + \sin(\theta_s)\sin(\alpha)\cos(\phi_s - \phi_a)
 * \f]
 * where θ_s is the solar zenith, α is the slope, φ_s is the solar azimuth,
 * and φ_a is the aspect (all in degrees).
 *
 * A return value ≤ 0 indicates topographic shadow (surface faces away from sun).
 *
 * \param[in] sza_deg    Solar zenith angle [degrees].
 * \param[in] saa_deg    Solar azimuth angle [degrees, clockwise from North].
 * \param[in] slope_deg  Surface slope [degrees, 0 = flat].
 * \param[in] aspect_deg Surface aspect [degrees, clockwise from North].
 * \return cos(i); ≤ 0 means topographic shadow.
 */
float cos_incidence(float sza_deg, float saa_deg,
                    float slope_deg, float aspect_deg);

/**
 * \brief Diffuse-sky view factor for a tilted surface.
 *
 * Isotropic sky approximation:
 * \f[ V_d = \frac{1 + \cos(\alpha)}{2} \f]
 *
 * Returns 1.0 for a flat surface (α = 0) and 0.5 for a vertical wall (α = 90°).
 *
 * \param[in] slope_deg Surface slope [degrees].
 * \return Sky view factor V_d ∈ [0, 1].
 */
float skyview_factor(float slope_deg);

/**
 * \brief Effective downward transmittance on a tilted surface.
 *
 * Separates the LUT transmittance into direct-beam and diffuse components,
 * then rescales each for the local illumination geometry:
 *
 * Illuminated surface (cos_i > 0):
 * \f[
 *   T_{down,eff} = T_{dir} \cdot \frac{\cos i}{\cos\theta_s}
 *                + (T_{down} - T_{dir}) \cdot V_d
 * \f]
 *
 * Topographic shadow (cos_i ≤ 0):
 * \f[
 *   T_{down,eff} = (T_{down} - T_{dir}) \cdot V_d
 * \f]
 *
 * \param[in] T_down     Flat-surface total downward transmittance (LUT value).
 * \param[in] T_down_dir Flat-surface direct downward transmittance (LUT value).
 * \param[in] cos_sza    cos(scene SZA) used when building the LUT.
 * \param[in] cos_i      Local illumination cosine from cos_incidence().
 * \param[in] V_d        Sky view factor from skyview_factor().
 * \return Effective downward transmittance T_down_eff ≥ 0.
 */
float atcorr_terrain_T_down(float T_down, float T_down_dir,
                             float cos_sza, float cos_i, float V_d);

/**
 * \brief Per-pixel upward transmittance correction for view-zenith variation.
 *
 * On tilted terrain the effective view zenith varies per pixel.  Using the
 * Beer-Lambert power-law approximation T ∝ exp(−τ/cos_VZA):
 * \f[
 *   T_{up,eff} = T_{up}^{\;\cos(\theta_{v,ref}) / \cos(\theta_{v,pixel})}
 * \f]
 *
 * \param[in] T_up         Flat-surface upward transmittance (LUT reference VZA).
 * \param[in] cos_vza_ref  cos(VZA) used when building the LUT.
 * \param[in] vza_pixel_deg Per-pixel effective view zenith angle [degrees].
 * \return Corrected upward transmittance T_up_eff.
 */
float atcorr_terrain_T_up(float T_up, float cos_vza_ref, float vza_pixel_deg);

#ifdef __cplusplus
}
#endif
