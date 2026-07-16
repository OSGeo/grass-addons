/**
 * \file retrieve.c
 * \brief Image-based atmospheric state retrievals (H₂O, AOD, O₃, pressure, quality).
 *
 * Pure computation: no GRASS dependencies; compiles into both the GRASS
 * module and libatcorr.so without modification.
 * Uses sixs_E0() and sixs_earth_sun_dist2() from solar_table.c.
 *
 * \see include/retrieve.h for the public API and algorithm descriptions.
 */

#include "../include/retrieve.h"
#include "../include/atcorr.h"   /* sixs_E0, sixs_earth_sun_dist2 */

#define _USE_MATH_DEFINES
#include <math.h>
#include <stdint.h>
#include <stdlib.h>
#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif

/**
 * \brief Retrieve per-pixel column water vapour from the 940 nm absorption band.
 *
 * Applies the continuum-interpolated band ratio (CIBR) method using bands at
 * 865, 940, and 1040 nm.  The effective absorption coefficient K_940 is
 * scaled with sensor FWHM to account for spectral line resolution
 * (power law calibrated against MODIS and Tanager AVIRIS-NG data):
 * \f[K(\text{FWHM}) = 0.036 \times (50\,\text{nm} / \text{FWHM})^{0.90}\f]
 *
 * \param[in]  L_865    Radiance at 865 nm [npix].
 * \param[in]  L_940    Radiance at 940 nm [npix].
 * \param[in]  L_1040   Radiance at 1040 nm [npix].
 * \param[in]  fwhm_um  Sensor FWHM at 940 nm in µm (0 = use broadband K=0.036).
 * \param[in]  npix     Number of pixels.
 * \param[in]  sza_deg  Solar zenith angle (degrees).
 * \param[in]  vza_deg  View zenith angle (degrees).
 * \param[out] out_wvc  Per-pixel WVC in g cm⁻² [npix]; clamped to [0.1, 8.0].
 */
void retrieve_h2o_940(const float *L_865,  const float *L_940,
                       const float *L_1040, float fwhm_um,
                       int npix,
                       float sza_deg, float vza_deg,
                       float *out_wvc)
{
    /* Fraction of the 865→1040 range occupied by 940-865 = 75/175 ≈ 0.4286 */
    static const float FRAC    = (0.940f - 0.865f) / (1.040f - 0.865f);
    static const float WVC_DEF = 2.0f;     /* fallback for invalid pixels */
    static const float WVC_MIN = 0.1f;
    static const float WVC_MAX = 8.0f;

    /* K_940 scales with sensor FWHM: narrow sensors resolve individual H2O
     * lines in the 940 nm cluster, raising the effective absorption coefficient
     * above the MODIS broadband value (K=0.036 at 50 nm FWHM).
     * Power law K(FWHM) = 0.036 × (50 nm / FWHM_nm)^0.90, calibrated against:
     *   MODIS (50 nm) → K=0.036;  Tanager (6.8 nm) → K≈0.217
     *   (empirical: D=0.718 at WVC=1.54 g/cm², SZA=29.3°, VZA=3.1°).
     *   Exponent α=0.90 = log(0.217/0.036)/log(50/6.8) corrects for
     *   spectral line saturation: H₂O lines are narrower than 5–8 nm FWHM,
     *   so K changes faster with FWHM than α=0.78 predicts in this range. */
    float K_940;
    if (fwhm_um > 0.0f && fwhm_um < 0.050f)
        K_940 = 0.036f * powf(0.050f / fwhm_um, 0.90f);
    else
        K_940 = 0.036f;   /* broadband default (MODIS-equivalent) */

    float cos_sza = cosf(sza_deg * (float)(M_PI / 180.0));
    float cos_vza = cosf(vza_deg * (float)(M_PI / 180.0));
    float mu_s = (cos_sza > 0.05f) ? cos_sza : 0.05f;
    float mu_v = (cos_vza > 0.05f) ? cos_vza : 0.05f;
    float km   = K_940 * (1.0f / mu_s + 1.0f / mu_v);

    for (int i = 0; i < npix; i++) {
        float l8 = L_865[i], l9 = L_940[i], l10 = L_1040[i];
        if (!(l8 > 0.0f) || !(l9 > 0.0f) || !(l10 > 0.0f)) {
            out_wvc[i] = WVC_DEF;
            continue;
        }
        float L_cont = l8 * (1.0f - FRAC) + l10 * FRAC;
        if (L_cont <= 0.0f) { out_wvc[i] = WVC_DEF; continue; }

        float D = 1.0f - l9 / L_cont;
        if (D < 0.0f) D = 0.0f;

        float wvc = D / km;
        out_wvc[i] = (wvc < WVC_MIN) ? WVC_MIN : (wvc > WVC_MAX) ? WVC_MAX : wvc;
    }
}

/**
 * \brief Retrieve per-pixel AOD at 550 nm from Dark Dense Vegetation (DDV).
 *
 * Implements a simplified MODIS dark-target algorithm.  Dark vegetated pixels
 * (NDVI > 0.5 and 2130 nm reflectance < 0.15) are selected; surface reflectance
 * at 470 and 660 nm is estimated from the 2130 nm band via empirical ratios, and
 * the difference from TOA reflectance yields the AOD.  Non-DDV pixels receive the
 * scene-mean AOD.
 *
 * \param[in]  L_470    Radiance at 470 nm [npix] (W m⁻² sr⁻¹ µm⁻¹).
 * \param[in]  L_660    Radiance at 660 nm [npix].
 * \param[in]  L_860    Radiance at 860 nm [npix].
 * \param[in]  L_2130   Radiance at 2130 nm [npix].
 * \param[in]  npix     Number of pixels.
 * \param[in]  doy      Day of year (for Earth-Sun distance correction).
 * \param[in]  sza_deg  Solar zenith angle (degrees).
 * \param[out] aod_out  Per-pixel AOD at 550 nm [npix]; NaN for invalid pixels.
 * \return Scene-mean AOD over DDV pixels (fallback to 0.1 if no DDV found).
 */
float retrieve_aod_ddv(const float *L_470,  const float *L_660,
                        const float *L_860,  const float *L_2130,
                        int npix, int doy, float sza_deg,
                        float *out_aod)
{
    static const float G      = 0.65f;   /* HG asymmetry parameter */
    static const float OMEGA0 = 0.89f;   /* single-scattering albedo */
    static const float AOD_FALLBACK = 0.15f;
    static const float AOD_MAX      = 3.0f;

    float E0_470  = sixs_E0(0.470f);
    float E0_660  = sixs_E0(0.660f);
    float E0_2130 = sixs_E0(2.130f);
    float d2f     = (float)sixs_earth_sun_dist2(doy);

    float cos_sza = cosf(sza_deg * (float)(M_PI / 180.0));
    float mu_s = (cos_sza > 0.05f) ? cos_sza : 0.05f;

    /* Henyey-Greenstein phase function for nadir view (cos Θ = −μs):
     * P_HG = (1 − g²) / (1 + g² − 2g cos Θ)^1.5  with cos Θ = −μs */
    float cos_theta = -mu_s;
    float denom_hg  = 1.0f + G*G - 2.0f*G*cos_theta;
    float P_HG = (1.0f - G*G) / (denom_hg * sqrtf(denom_hg));
    if (P_HG < 1e-4f) P_HG = 1e-4f;

    /* ρ_toa = π × L × d² / (E0 × μs)  →  scale = π × d² / μs */
    float pi_d2_over_mus = (float)M_PI * d2f / mu_s;

    /* τ = ρ_path × 4 μs / (ω₀ P_HG)  with μv = 1 (nadir) */
    float tau_factor = 4.0f * mu_s / (OMEGA0 * P_HG);

    double sum_aod = 0.0;
    int    n_ddv   = 0;

    for (int i = 0; i < npix; i++) {
        float l4 = L_470[i], l6 = L_660[i], l8 = L_860[i], l21 = L_2130[i];
        if (!(l4 > 0.0f) || !(l6 > 0.0f) || !(l8 > 0.0f) || !(l21 > 0.0f)) {
            out_aod[i] = -1.0f;   /* invalid → fill with mean later */
            continue;
        }

        /* TOA reflectance at 2130 nm for DDV mask */
        float rho_2130 = pi_d2_over_mus * l21 / E0_2130;
        if (rho_2130 < 0.01f || rho_2130 > 0.25f) {
            out_aod[i] = -1.0f;
            continue;
        }

        /* NDVI from 860/660 radiance (E0 factor cancels in ratio) */
        float ndvi = (l8 - l6) / (l8 + l6 + 1e-10f);
        if (ndvi <= 0.1f) { out_aod[i] = -1.0f; continue; }

        /* TOA reflectance at 470/660 nm */
        float rho_470 = pi_d2_over_mus * l4 / E0_470;
        float rho_660 = pi_d2_over_mus * l6 / E0_660;

        /* DDV surface reflectance prediction */
        float rho_surf_470 = 0.25f * rho_2130;
        float rho_surf_660 = 0.50f * rho_2130;

        /* Path reflectance (ensure positive) */
        float rho_path_470 = rho_470 - rho_surf_470;
        float rho_path_660 = rho_660 - rho_surf_660;
        if (rho_path_470 < 1e-5f) rho_path_470 = 1e-5f;
        if (rho_path_660 < 1e-5f) rho_path_660 = 1e-5f;

        /* Single-scattering aerosol optical depth at 470/660 nm */
        float tau_470 = rho_path_470 * tau_factor;
        float tau_660 = rho_path_660 * tau_factor;

        /* Ångström exponent and scale to 550 nm */
        float alpha = 0.0f;
        if (tau_470 > 1e-4f && tau_660 > 1e-4f) {
            alpha = -logf(tau_470 / tau_660) / logf(0.470f / 0.660f);
            if (alpha < -1.0f) alpha = -1.0f;
            if (alpha >  3.0f) alpha =  3.0f;
        }
        float tau_550 = tau_470 * powf(0.550f / 0.470f, -alpha);
        if (tau_550 < 0.0f)   tau_550 = 0.0f;
        if (tau_550 > AOD_MAX) tau_550 = AOD_MAX;

        out_aod[i] = tau_550;
        sum_aod   += tau_550;
        n_ddv++;
    }

    float aod_mean = (n_ddv > 0) ? (float)(sum_aod / n_ddv) : AOD_FALLBACK;

    /* Fill invalid pixels (marked -1) with scene mean */
    for (int i = 0; i < npix; i++)
        if (out_aod[i] < 0.0f) out_aod[i] = aod_mean;

    return aod_mean;
}

/**
 * \brief Retrieve scene-mean ozone column from the Chappuis absorption band.
 *
 * Uses the continuum-interpolated band ratio at 540, 600, and 680 nm.  The
 * 600 nm band falls within the Chappuis band; 540 and 680 nm bracket the
 * continuum.  The ozone absorption cross-section at 600 nm is
 * σ = 4.9 × 10⁻²¹ cm² molecule⁻¹.
 *
 * \param[in] L_540     Radiance at 540 nm [npix].
 * \param[in] L_600     Radiance at 600 nm [npix].
 * \param[in] L_680     Radiance at 680 nm [npix].
 * \param[in] npix      Number of pixels.
 * \param[in] sza_deg   Solar zenith angle (degrees).
 * \param[in] vza_deg   View zenith angle (degrees).
 * \return Scene-mean ozone column in Dobson units; fallback to 300 DU on failure.
 */
float retrieve_o3_chappuis(const float *L_540, const float *L_600,
                            const float *L_680, int npix,
                            float sza_deg, float vza_deg)
{
    /* Fraction of 540→680 range at 600 nm: (600-540)/(680-540) = 3/7 */
    static const float FRAC       = (0.600f - 0.540f) / (0.680f - 0.540f);
    /* Chappuis cross section at 600 nm; effective DU⁻¹ absorption coefficient.
     * Derived from Bogumil et al. (2003): σ ≈ 3.8e-21 cm²/mol;
     * 1 DU = 2.687e16 mol/cm²  →  σ_DU = 3.8e-21 × 2.687e16 ≈ 1.02e-4 DU⁻¹ */
    static const float SIGMA_O3   = 1.0e-4f;
    static const float O3_FALLBACK = 300.0f;
    static const float O3_MIN      = 50.0f;
    static const float O3_MAX      = 800.0f;

    float cos_sza = cosf(sza_deg * (float)(M_PI / 180.0));
    float cos_vza = cosf(vza_deg * (float)(M_PI / 180.0));
    float mu_s = (cos_sza > 0.05f) ? cos_sza : 0.05f;
    float mu_v = (cos_vza > 0.05f) ? cos_vza : 0.05f;
    float sigma_m = SIGMA_O3 * (1.0f / mu_s + 1.0f / mu_v);

    double sum_o3  = 0.0;
    int    n_valid = 0;

    for (int i = 0; i < npix; i++) {
        float l5 = L_540[i], l6 = L_600[i], l7 = L_680[i];
        if (!(l5 > 0.0f) || !(l6 > 0.0f) || !(l7 > 0.0f)) continue;

        float L_cont = l5 * (1.0f - FRAC) + l7 * FRAC;
        if (L_cont <= 0.0f || l6 >= L_cont) continue;

        float D  = 1.0f - l6 / L_cont;
        float o3 = D / sigma_m;

        if (o3 >= O3_MIN && o3 <= O3_MAX) {
            sum_o3 += o3;
            n_valid++;
        }
    }

    if (n_valid == 0) return O3_FALLBACK;

    float result = (float)(sum_o3 / n_valid);
    return (result < O3_MIN) ? O3_MIN : (result > O3_MAX) ? O3_MAX : result;
}

/**
 * \brief Compute surface pressure from elevation using the ISA model.
 *
 * Applies the ICAO International Standard Atmosphere (1993) barometric formula:
 * \f[P = 1013.25 \left(1 - 2.2558 \times 10^{-5} \, z\right)^{5.2559}\f]
 * for elevation \f$z\f$ in metres.
 *
 * \param[in] elev_m  Elevation above sea level (metres).
 * \return Surface pressure in hPa; clamped to [1.0, 1100.0].
 */
float retrieve_pressure_isa(float elev_m)
{
    /* ICAO International Standard Atmosphere (1993)
     * P = 1013.25 × (1 − 2.2558×10⁻⁵ × h)^5.2559  [hPa] */
    if (elev_m < 0.0f)       elev_m = 0.0f;
    if (elev_m > 11000.0f)   elev_m = 11000.0f;
    return 1013.25f * powf(1.0f - 2.2558e-5f * elev_m, 5.2559f);
}

/**
 * \brief Retrieve per-pixel surface pressure from the O₂-A absorption band.
 *
 * Applies the continuum-interpolated band ratio at 740, 760, and 780 nm.
 * The effective absorption coefficient is
 * K_O2 = 0.25 calibrated to ~10 nm FWHM sensors.
 * The band depth \f$D = \ln(L_c / L_{760})\f$ yields surface pressure via
 * Beer-Lambert: \f$P = P_0 \times D / (K_{O2}(1/\cos\theta_s + 1/\cos\theta_v))\f$.
 *
 * \param[in]  L_740       Radiance at 740 nm [npix].
 * \param[in]  L_760       Radiance at 760 nm (O₂-A band centre) [npix].
 * \param[in]  L_780       Radiance at 780 nm [npix].
 * \param[in]  npix        Number of pixels.
 * \param[in]  sza_deg     Solar zenith angle (degrees).
 * \param[in]  vza_deg     View zenith angle (degrees).
 * \param[out] pressure_out Per-pixel surface pressure in hPa [npix];
 *                          clamped to [600, 1100] hPa; NaN for invalid pixels.
 */
void retrieve_pressure_o2a(const float *L_740, const float *L_760,
                             const float *L_780, int npix,
                             float sza_deg, float vza_deg,
                             float *out_pressure)
{
    /* Continuum interpolation between 740 nm and 780 nm; feature at 760 nm.
     *
     * Physical model (Beer-Lambert, linearised):
     *   τ_O2(P) = K_O2 × (P / P0)
     *   D_760   = max(0, 1 − L_760 / L_cont) ≈ τ_O2 × m  (first-order)
     *   P       = P0 × D_760 / (K_O2 × m)
     *
     * K_O2 = 0.25: calibrated to ~10 nm FWHM sensors; derived from
     * Schläpfer et al. (1998): at P=P0, SZA=0 (m=2), band-depth D ≈ 0.50.
     * For a 5 nm sensor set K_O2 ≈ 0.40; for 20 nm use K_O2 ≈ 0.15.
     *
     * Reference:
     *   Schläpfer, D., Borel, C.C., Keller, J., Itten, K.I. (1998).
     *   Atmospheric pre-processing of DAIS airborne data. SPIE 3502.
     */
    static const float FRAC   = 0.5f;      /* (760−740)/(780−740) = 0.5 */
    static const float K_O2   = 0.25f;     /* effective OD per unit air mass at P0 */
    static const float P0     = 1013.25f;  /* sea-level pressure [hPa] */
    static const float P_MIN  = 200.0f;    /* ~11 km altitude */
    static const float P_MAX  = 1100.0f;
    static const float P_DEF  = P0;

    float cos_sza = cosf(sza_deg * (float)(M_PI / 180.0));
    float cos_vza = cosf(vza_deg * (float)(M_PI / 180.0));
    float mu_s = (cos_sza > 0.05f) ? cos_sza : 0.05f;
    float mu_v = (cos_vza > 0.05f) ? cos_vza : 0.05f;
    float m    = 1.0f / mu_s + 1.0f / mu_v;   /* two-way air mass */

    for (int i = 0; i < npix; i++) {
        float l74 = L_740[i], l76 = L_760[i], l78 = L_780[i];
        if (!(l74 > 0.0f) || !(l76 > 0.0f) || !(l78 > 0.0f)) {
            out_pressure[i] = P_DEF;
            continue;
        }
        float L_cont = l74 * (1.0f - FRAC) + l78 * FRAC;
        if (L_cont <= 0.0f || l76 >= L_cont) {
            out_pressure[i] = P_DEF;
            continue;
        }
        float D = 1.0f - l76 / L_cont;
        if (D < 0.0f) D = 0.0f;
        if (D > 0.95f) D = 0.95f;  /* cap: near-zero pressure is unphysical */

        float P = P0 * D / (K_O2 * m);
        out_pressure[i] = (P < P_MIN) ? P_MIN : (P > P_MAX) ? P_MAX : P;
    }
}

/* ─── Cloud / shadow / water / snow quality bitmask ───────────────────────── */

#include <stdint.h>

/**
 * \brief Compute a pre-correction cloud/shadow/water/snow quality bitmask.
 *
 * Classifies each pixel using TOA reflectance thresholds:
 * - **Cloud** (bit 0): blue reflectance > 0.25 AND NDVI < 0.2.
 * - **Shadow** (bit 1): sum of visible + NIR reflectance < 0.04.
 * - **Water** (bit 2): NIR reflectance < 0.05.
 * - **Snow/Ice** (bit 3): NDSI = (green − SWIR) / (green + SWIR) > 0.4.
 *
 * \param[in]  L_blue   Radiance at ~470 nm [npix].
 * \param[in]  L_red    Radiance at ~660 nm [npix].
 * \param[in]  L_nir    Radiance at ~860 nm [npix].
 * \param[in]  L_swir   Radiance at ~1600 nm [npix], or NULL to skip snow/ice detection.
 * \param[in]  npix     Number of pixels.
 * \param[in]  doy      Day of year (for Earth-Sun distance).
 * \param[in]  sza_deg  Solar zenith angle (degrees).
 * \param[out] mask_out Per-pixel quality bitmask (RETRIEVE_MASK_* bits) [npix].
 */
void retrieve_quality_mask(const float *L_blue, const float *L_red,
                            const float *L_nir,  const float *L_swir,
                            int npix, int doy, float sza_deg,
                            uint8_t *out_mask)
{
    /* Thresholds are applied to TOA reflectance (from TOA radiance).
     *
     * Bitmask:  MASK_CLOUD=0x01  MASK_SHADOW=0x02  MASK_WATER=0x04  MASK_SNOW=0x08
     *
     * Cloud:    TOA_blue > 0.25 AND NDVI < 0.2, OR TOA_nir > 0.60
     * Shadow:   TOA_blue < 0.04 AND TOA_red < 0.04 AND TOA_nir < 0.04
     * Water:    TOA_nir < 0.05 AND NDVI < 0.0
     * Snow/ice: NDSI > 0.40 AND TOA_nir > 0.10   (requires L_swir)
     *
     * References:
     *   Cloud / shadow: Braaten et al. (2015), Remote Sens. 7:15745
     *   Water:          McFeeters (1996), Int. J. Remote Sens. 17:1425
     *   Snow:           Hall et al. (1995), Remote Sens. Environ. 54:127
     */
    float E0_blue = sixs_E0(0.470f);
    float E0_red  = sixs_E0(0.660f);
    float E0_nir  = sixs_E0(0.860f);
    float E0_swir = sixs_E0(1.600f);
    float d2f     = (float)sixs_earth_sun_dist2(doy);

    float cos_sza = cosf(sza_deg * (float)(M_PI / 180.0));
    float mu_s    = (cos_sza > 0.05f) ? cos_sza : 0.05f;
    float scale   = (float)M_PI * d2f / mu_s;

    for (int i = 0; i < npix; i++) {
        out_mask[i] = 0;
        float lb = L_blue[i], lr = L_red[i], ln = L_nir[i];
        if (!(lb > 0.0f) || !(lr > 0.0f) || !(ln > 0.0f)) continue;

        float rb = scale * lb / E0_blue;
        float rr = scale * lr / E0_red;
        float rn = scale * ln / E0_nir;

        float ndvi = (rn - rr) / (rn + rr + 1e-10f);

        /* NDSI requires SWIR */
        float ndsi = -2.0f;
        if (L_swir && L_swir[i] > 0.0f) {
            float rs = scale * L_swir[i] / E0_swir;
            ndsi = (rb - rs) / (rb + rs + 1e-10f);
        }

        if ((rb > 0.25f && ndvi < 0.2f) || rn > 0.60f)
            out_mask[i] |= RETRIEVE_MASK_CLOUD;

        if (rb < 0.04f && rr < 0.04f && rn < 0.04f)
            out_mask[i] |= RETRIEVE_MASK_SHADOW;

        if (rn < 0.05f && ndvi < 0.0f)
            out_mask[i] |= RETRIEVE_MASK_WATER;

        if (ndsi > 0.40f && rn > 0.10f)
            out_mask[i] |= RETRIEVE_MASK_SNOW;
    }
}

/** \cond INTERNAL */
static int _float_cmp(const void *a, const void *b)
{
    float fa = *(const float *)a, fb = *(const float *)b;
    return (fa > fb) - (fa < fb);
}

/** \endcond */

/**
 * \brief Apply MAIAC-inspired patch-based AOD spatial regularisation.
 *
 * Divides the image into non-overlapping square patches of size \c patch_sz,
 * replaces each patch with its median DDV AOD, and fills patches with no DDV
 * pixels by inverse-distance weighting from neighbouring patches.
 *
 * \param[in,out] aod_data  Per-pixel AOD map [nrows × ncols] (modified in place).
 * \param[in]     nrows     Number of rows.
 * \param[in]     ncols     Number of columns.
 * \param[in]     patch_sz  Patch side length in pixels (must be ≥ 2).
 */
void retrieve_aod_maiac(float *aod_data, int nrows, int ncols, int patch_sz)
{
    /* Segment image into non-overlapping patch_sz × patch_sz blocks.
     * Each patch with ≥1 valid pixel uses the patch-median AOD (robust to
     * DDV outliers).  Invalid patches are filled by inverse-distance
     * weighting from the nearest valid patch centroids.
     *
     * Reference:
     *   Lyapustin, A. et al. (2011). Multiangle implementation of atmospheric
     *   correction (MAIAC) — Part 1. JGR 116, D05203.  This implementation
     *   uses only the spatial regularization concept (patch-median + IDW fill),
     *   not the full MAIAC surface model or multi-angle retrieval.
     */
    if (patch_sz < 2) patch_sz = 2;

    int np_rows  = (nrows + patch_sz - 1) / patch_sz;
    int np_cols  = (ncols + patch_sz - 1) / patch_sz;
    int np_total = np_rows * np_cols;
    int buf_max  = patch_sz * patch_sz;

    float *patch_aod   = malloc((size_t)np_total * sizeof(float));
    float *patch_row   = malloc((size_t)np_total * sizeof(float));
    float *patch_col   = malloc((size_t)np_total * sizeof(float));
    int   *patch_valid = malloc((size_t)np_total * sizeof(int));
    float *patch_buf   = malloc((size_t)buf_max   * sizeof(float));
    if (!patch_aod || !patch_row || !patch_col || !patch_valid || !patch_buf) {
        free(patch_aod); free(patch_row); free(patch_col);
        free(patch_valid); free(patch_buf);
        return;   /* silently skip on OOM */
    }

    /* ── Step 1: per-patch median ── */
    for (int pr = 0; pr < np_rows; pr++) {
        for (int pc = 0; pc < np_cols; pc++) {
            int pi = pr * np_cols + pc;
            int r0 = pr * patch_sz, r1 = r0 + patch_sz; if (r1 > nrows) r1 = nrows;
            int c0 = pc * patch_sz, c1 = c0 + patch_sz; if (c1 > ncols) c1 = ncols;

            patch_row[pi] = 0.5f * (float)(r0 + r1);
            patch_col[pi] = 0.5f * (float)(c0 + c1);

            int n = 0;
            for (int r = r0; r < r1; r++)
                for (int c = c0; c < c1; c++) {
                    float v = aod_data[r * ncols + c];
                    if (isfinite(v) && v >= 0.0f)
                        patch_buf[n++] = v;
                }

            if (n == 0) {
                patch_valid[pi] = 0;
                patch_aod[pi]   = -1.0f;
            } else {
                qsort(patch_buf, (size_t)n, sizeof(float), _float_cmp);
                patch_aod[pi]   = patch_buf[n / 2];
                patch_valid[pi] = 1;
            }
        }
    }

    /* ── Step 2: IDW fill for invalid patches ── */
    for (int pi = 0; pi < np_total; pi++) {
        if (patch_valid[pi]) continue;
        double sum_w = 0.0, sum_wa = 0.0;
        for (int pj = 0; pj < np_total; pj++) {
            if (!patch_valid[pj]) continue;
            float dr = patch_row[pi] - patch_row[pj];
            float dc = patch_col[pi] - patch_col[pj];
            double d2 = (double)(dr * dr + dc * dc);
            if (d2 < 1.0) d2 = 1.0;
            double w = 1.0 / d2;
            sum_w  += w;
            sum_wa += w * (double)patch_aod[pj];
        }
        patch_aod[pi] = (sum_w > 0.0) ? (float)(sum_wa / sum_w) : 0.1f;
    }

    /* ── Step 3: write patch medians back to all pixels in each patch ── */
    for (int pr = 0; pr < np_rows; pr++) {
        for (int pc = 0; pc < np_cols; pc++) {
            int pi = pr * np_cols + pc;
            float aod_p = patch_aod[pi];
            int r0 = pr * patch_sz, r1 = r0 + patch_sz; if (r1 > nrows) r1 = nrows;
            int c0 = pc * patch_sz, c1 = c0 + patch_sz; if (c1 > ncols) c1 = ncols;
            for (int r = r0; r < r1; r++)
                for (int c = c0; c < c1; c++)
                    aod_data[r * ncols + c] = aod_p;
        }
    }

    free(patch_aod); free(patch_row); free(patch_col);
    free(patch_valid); free(patch_buf);
}

/**
 * \brief Retrieve per-pixel column water vapour from a generic absorption triplet.
 *
 * Generic CIBR retrieval using three bands (lo, feature, hi) bracketing a
 * water vapour absorption feature.  Supports the 720, 940, and 1135 nm features.
 * The FWHM-dependent absorption coefficient follows the same power law as
 * retrieve_h2o_940() with exponent α = 0.90.
 *
 * \param[in]  L_lo          Radiance at the lower continuum band [npix].
 * \param[in]  L_feat        Radiance at the absorption feature band [npix].
 * \param[in]  L_hi          Radiance at the upper continuum band [npix].
 * \param[in]  wl_lo_um      Wavelength of the lower continuum band (µm).
 * \param[in]  wl_feat_um    Wavelength of the absorption feature (µm).
 * \param[in]  wl_hi_um      Wavelength of the upper continuum band (µm).
 * \param[in]  K_ref         Reference absorption coefficient (cm² g⁻¹) at \c fwhm_ref_um.
 * \param[in]  fwhm_ref_um   Reference FWHM for \c K_ref calibration (µm).
 * \param[in]  fwhm_um       Sensor FWHM at the feature band (µm; 0 = use \c K_ref unchanged).
 * \param[in]  D_min         Minimum valid band depth (below → invalid).
 * \param[in]  D_max         Maximum valid band depth (above → invalid).
 * \param[in]  npix          Number of pixels.
 * \param[in]  sza_deg       Solar zenith angle (degrees).
 * \param[in]  vza_deg       View zenith angle (degrees).
 * \param[out] out_wvc       Per-pixel WVC in g cm⁻² [npix]; fallback to 2.0 for invalid.
 * \param[out] out_valid     Per-pixel validity flag (1=valid, 0=invalid) [npix]; may be NULL.
 */
void retrieve_h2o_triplet(const float *L_lo,   const float *L_feat,
                           const float *L_hi,
                           float wl_lo_um,  float wl_feat_um, float wl_hi_um,
                           float K_ref, float fwhm_ref_um, float fwhm_um,
                           float D_min, float D_max,
                           int npix, float sza_deg, float vza_deg,
                           float *out_wvc, uint8_t *out_valid)
{
    static const float WVC_DEF = 2.0f;

    float FRAC = (wl_feat_um - wl_lo_um) / (wl_hi_um - wl_lo_um);

    /* FWHM-dependent K scaling (same power law as retrieve_h2o_940, α=0.90) */
    float K = K_ref;
    if (fwhm_um > 0.0f && fwhm_um < fwhm_ref_um)
        K = K_ref * powf(fwhm_ref_um / fwhm_um, 0.90f);

    float cos_sza = cosf(sza_deg * (float)(M_PI / 180.0));
    float cos_vza = cosf(vza_deg * (float)(M_PI / 180.0));
    float mu_s = (cos_sza > 0.05f) ? cos_sza : 0.05f;
    float mu_v = (cos_vza > 0.05f) ? cos_vza : 0.05f;
    float km   = K * (1.0f / mu_s + 1.0f / mu_v);

    for (int i = 0; i < npix; i++) {
        float ll = L_lo[i], lf = L_feat[i], lh = L_hi[i];
        if (!(ll > 0.0f) || !(lf > 0.0f) || !(lh > 0.0f)) {
            out_wvc[i] = WVC_DEF;
            if (out_valid) out_valid[i] = 0;
            continue;
        }
        float L_cont = ll * (1.0f - FRAC) + lh * FRAC;
        if (L_cont <= 0.0f) {
            out_wvc[i] = WVC_DEF;
            if (out_valid) out_valid[i] = 0;
            continue;
        }
        float D = 1.0f - lf / L_cont;
        if (D < 0.0f) D = 0.0f;

        if (D < D_min || D > D_max) {
            out_wvc[i] = WVC_DEF;
            if (out_valid) out_valid[i] = 0;
            continue;
        }

        float wvc = D / km;
        if (wvc < 0.1f) wvc = 0.1f;
        if (wvc > 8.0f) wvc = 8.0f;
        out_wvc[i] = wvc;
        if (out_valid) out_valid[i] = 1;
    }
}

/**
 * \brief Compute a per-pixel consensus WVC from multiple retrieval methods.
 *
 * For each pixel, combines valid WVC estimates from \c n_methods independent
 * retrievals:
 * - 1 valid → use it directly.
 * - 2 valid → arithmetic mean.
 * - 3 valid → median.
 *
 * Pixels with no valid estimate receive the mean of all available values.
 *
 * \param[in]  n_methods    Number of retrieval methods (typically 3: 720, 940, 1135 nm).
 * \param[in]  wvc_arrays   Array of \c n_methods per-pixel WVC arrays [npix each].
 * \param[in]  valid_arrays Array of \c n_methods per-pixel validity flags [npix each].
 * \param[in]  npix         Number of pixels.
 * \param[out] out_wvc      Per-pixel consensus WVC in g cm⁻² [npix].
 * \return Number of pixels where ≥ 2 methods agreed.
 */
int retrieve_h2o_consensus(int n_methods,
                            float * const *wvc_arrays,
                            uint8_t * const *valid_arrays,
                            int npix,
                            float *out_wvc)
{
    static const float WVC_DEF = 2.0f;
    int n_agreed = 0;

    for (int i = 0; i < npix; i++) {
        /* Collect valid estimates into a small stack (max 3) */
        float vals[3];
        int n_valid = 0;
        for (int m = 0; m < n_methods && m < 3; m++) {
            if (valid_arrays[m][i])
                vals[n_valid++] = wvc_arrays[m][i];
        }

        if (n_valid == 0) {
            out_wvc[i] = WVC_DEF;
            continue;
        }
        if (n_valid == 1) {
            out_wvc[i] = vals[0];
            continue;
        }

        /* Sort 2–3 values and take median */
        if (n_valid == 2) {
            out_wvc[i] = 0.5f * (vals[0] + vals[1]);
        } else {
            /* n_valid == 3: sort then take middle element */
            float a = vals[0], b = vals[1], c = vals[2], t;
            if (a > b) { t = a; a = b; b = t; }
            if (b > c) { t = b; b = c; c = t; }
            if (a > b) { t = a; a = b; b = t; }
            (void)a; (void)c;
            out_wvc[i] = b;
        }
        if (n_valid >= 2) n_agreed++;
    }

    return n_agreed;
}

/* ═══════════════════════════════════════════════════════════════════════════
 * DASF retrieval — Directional Area Scattering Factor (Knyazikhin 2013)
 * ═══════════════════════════════════════════════════════════════════════════ */

/*
 * PROSPECT-D leaf albedo (R_leaf + T_leaf) at 5 nm steps, 705–795 nm.
 * Source: PROSPECT-D (Féret et al. 2017), Cab=40 µg/cm², Car=8,
 *         Cw=0.013, Cm=0.010, N=1.5.
 * These represent the combined reflectance + transmittance of a single leaf
 * in the NIR plateau where the canopy radiative transfer is nearly conservative
 * (ω_L ≈ 0.90), making the spectral invariant approach well-conditioned.
 */
static const float LEAF_ALB_WL_NM[] = {
    705.0f, 710.0f, 715.0f, 720.0f, 725.0f, 730.0f, 735.0f,
    740.0f, 745.0f, 750.0f, 755.0f, 760.0f, 765.0f, 770.0f,
    775.0f, 780.0f, 785.0f, 790.0f, 795.0f
};
static const float LEAF_ALB_VAL[] = {
    0.740f, 0.770f, 0.808f, 0.840f, 0.865f, 0.881f, 0.892f,
    0.900f, 0.906f, 0.910f, 0.912f, 0.912f, 0.911f, 0.911f,
    0.910f, 0.909f, 0.908f, 0.907f, 0.906f
};
#define N_LEAF_ALB 19

/**
 * \brief Look up PROSPECT-D leaf single-scattering albedo in the NIR plateau.
 *
 * Returns the combined reflectance + transmittance of a single leaf at the
 * given wavelength, interpolated from the 19-entry PROSPECT-D table at 5 nm
 * steps over 705–795 nm.  Parameters: Cab=40, Car=8, Cw=0.013, Cm=0.010, N=1.5.
 *
 * \param[in] wl_um Wavelength in µm.
 * \return Leaf single-scattering albedo in [0, 1]; −1 if outside the 705–795 nm range.
 */
float leaf_albedo_nir(float wl_um)
{
    float wl_nm = wl_um * 1000.0f;
    if (wl_nm < LEAF_ALB_WL_NM[0] || wl_nm > LEAF_ALB_WL_NM[N_LEAF_ALB - 1])
        return -1.0f;   /* outside table: signal to caller */

    /* Linear interpolation */
    int lo = 0;
    while (lo < N_LEAF_ALB - 2 && LEAF_ALB_WL_NM[lo + 1] <= wl_nm)
        lo++;
    float dx = LEAF_ALB_WL_NM[lo + 1] - LEAF_ALB_WL_NM[lo];
    float t  = (dx > 0.0f) ? (wl_nm - LEAF_ALB_WL_NM[lo]) / dx : 0.0f;
    return LEAF_ALB_VAL[lo] * (1.0f - t) + LEAF_ALB_VAL[lo + 1] * t;
}

/**
 * \brief Retrieve per-pixel Directional Area Scattering Factor (DASF).
 *
 * Regresses per-pixel surface BRF against PROSPECT-D leaf single-scattering
 * albedo over the 710–790 nm NIR plateau using linear least-squares:
 * \f[\text{DASF}_i = \frac{\sum_b \rho_{b,i} \, \omega_b}{\sum_b \omega_b^2}\f]
 * (Knyazikhin et al. 2013, PNAS 110, E185–E192).
 *
 * \param[in]  refl      Surface reflectance cube [n_dasf × npix], band-major order.
 * \param[in]  wl_dasf   Wavelengths of the DASF bands in µm [n_dasf].
 * \param[in]  n_dasf    Number of bands in the NIR plateau.
 * \param[in]  npix      Number of pixels.
 * \param[out] out_dasf  Per-pixel DASF [npix]; NaN for pixels with no valid bands.
 */
void retrieve_dasf(const float *refl, const float *wl_dasf, int n_dasf,
                   int npix, float *out_dasf)
{
    /* DASF = Σ(ρ · ω_L) / Σ(ω_L²)  [linear least-squares, ω_L as predictor]
     * Knyazikhin et al. (2013) PNAS: ρ(λ) = DASF · ω_L(λ) in the NIR plateau.
     * We accumulate per band; refl is band-major [n_dasf × npix]. */

#ifdef _OPENMP
#pragma omp parallel for schedule(static)
#endif
    for (int i = 0; i < npix; i++) {
        float sum_xy = 0.0f;   /* Σ ρ · ω_L */
        float sum_yy = 0.0f;   /* Σ ω_L²    */
        int   n_valid = 0;

        for (int b = 0; b < n_dasf; b++) {
            float omega = leaf_albedo_nir(wl_dasf[b]);
            if (omega <= 0.0f) continue;
            float rho = refl[(size_t)b * npix + i];
            if (!isfinite(rho)) continue;
            sum_xy += rho   * omega;
            sum_yy += omega * omega;
            n_valid++;
        }

        if (n_valid < 3 || sum_yy < 1e-6f)
            out_dasf[i] = NAN;
        else {
            float d = sum_xy / sum_yy;
            out_dasf[i] = (d < 0.01f) ? 0.01f : (d > 1.0f) ? 1.0f : d;
        }
    }
}
