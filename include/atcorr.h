/**
 * \file atcorr.h
 * \brief Public API for the i.hyper.atcorr atmospheric correction library.
 *
 * Declares the LUT grid specification (::LutConfig), output arrays
 * (::LutArrays), and all functions exported by \c libatcorr.so:
 *   - atcorr_compute_lut()  — build the 3-D [AOD × H₂O × λ] LUT via DISCOM
 *   - atcorr_lut_slice()    — bilinear interpolation at a fixed (AOD, H₂O)
 *   - atcorr_lut_interp_pixel() — trilinear point lookup for per-pixel paths
 *   - atcorr_invert()       — Lambertian BOA reflectance inversion
 *   - atcorr_invert_brdf()  — BRDF-coupled inversion (white-sky albedo term)
 *   - sixs_E0()             — Thuillier solar irradiance spectrum
 *   - sixs_earth_sun_dist2()— seasonal Earth–Sun distance
 *   - SRF gas-transmittance correction (::SrfConfig, atcorr_srf_compute(), …)
 *
 * (C) 2025-2026 Yann. GNU GPL ≥ 2.
 *
 * \author Yann
 */
#pragma once
#include <stddef.h>
#include <stdint.h>
#include "brdf.h"

#ifdef __cplusplus
extern "C" {
#endif

/** \defgroup aerosol_models Aerosol model identifiers
 *  Matching 6SV \c iaer codes passed to ::LutConfig::aerosol_model.
 *  @{ */
#define AEROSOL_NONE         0  /*!< No aerosol (Rayleigh only) */
#define AEROSOL_CONTINENTAL  1  /*!< Continental aerosol mixture */
#define AEROSOL_MARITIME     2  /*!< Maritime aerosol mixture */
#define AEROSOL_URBAN        3  /*!< Urban aerosol mixture */
#define AEROSOL_DESERT       5  /*!< Desert dust aerosol */
#define AEROSOL_CUSTOM       9  /*!< Custom Mie log-normal (mie.c) */
/** @} */

/** \defgroup atmo_models Atmosphere model identifiers
 *  Passed to ::LutConfig::atmo_model.
 *  @{ */
#define ATMO_US62            1  /*!< US Standard Atmosphere 1962 */
#define ATMO_MIDSUM          2  /*!< Mid-latitude summer */
#define ATMO_MIDWIN          3  /*!< Mid-latitude winter */
#define ATMO_TROPICAL        4  /*!< Tropical */
#define ATMO_SUBSUM          5  /*!< Sub-arctic summer */
#define ATMO_SUBWIN          6  /*!< Sub-arctic winter */
/** @} */

/* ═══════════════════════════════════════════════════════════════════════════
 * LUT API
 * ═══════════════════════════════════════════════════════════════════════════ */

/**
 * \brief 6SV LUT grid specification.
 *
 * Describes the geometry, atmospheric state grid, and surface/polarization
 * options for atcorr_compute_lut().  All pointer fields must remain valid
 * for the lifetime of the LUT computation.
 */
typedef struct {
    /* ── Wavelength grid ─────────────────────────────────────────────────── */
    const float *wl;        /*!< Band-centre wavelengths [µm], length \c n_wl */
    int          n_wl;      /*!< Number of wavelength bands */

    /* ── AOD grid ────────────────────────────────────────────────────────── */
    const float *aod;       /*!< AOD at 550 nm, length \c n_aod (must be ≥ 0, sorted) */
    int          n_aod;     /*!< Number of AOD grid points */

    /* ── Column water-vapour grid ────────────────────────────────────────── */
    const float *h2o;       /*!< WVC [g/cm²], length \c n_h2o (sorted) */
    int          n_h2o;     /*!< Number of H₂O grid points */

    /* ── Scene geometry ──────────────────────────────────────────────────── */
    float sza;              /*!< Solar zenith angle [degrees] */
    float vza;              /*!< View zenith angle [degrees] */
    float raa;              /*!< Relative azimuth angle [degrees] */

    float altitude_km;      /*!< Surface/sensor altitude [km] */

    /* ── Atmosphere / aerosol ────────────────────────────────────────────── */
    int atmo_model;         /*!< \ref atmo_models constant (default: \c ATMO_US62) */
    int aerosol_model;      /*!< \ref aerosol_models constant */

    float surface_pressure; /*!< Surface pressure [hPa]; 0 = standard atmosphere */
    float ozone_du;         /*!< Ozone column [Dobson units]; 0 = standard atmosphere */

    /* ── Custom Mie aerosol (aerosol_model == AEROSOL_CUSTOM) ───────────── */
    float mie_r_mode;       /*!< Log-normal mode radius [µm], e.g. 0.12 */
    float mie_sigma_g;      /*!< Geometric standard deviation, e.g. 1.8 */
    float mie_m_real;       /*!< Real refractive index at 550 nm */
    float mie_m_imag;       /*!< Imaginary refractive index at 550 nm */

    /* ── BRDF surface model ──────────────────────────────────────────────── */
    BrdfType   brdf_type;   /*!< Surface reflectance model (default: \c BRDF_LAMBERTIAN) */
    BrdfParams brdf_params; /*!< Per-model parameter union; see ::BrdfParams */

    /* ── Polarized RT ────────────────────────────────────────────────────── */
    int enable_polar;       /*!< 0 = scalar RT (default); 1 = vector Stokes (I,Q,U)
                             *   via sixs_ospol().  Improves R_atm by 1–5 %% in the
                             *   blue (Rayleigh polarisation feedback).  ~3× slower. */
} LutConfig;

/**
 * \brief LUT output arrays — shape [n_aod × n_h₂o × n_wl] (C row-major).
 *
 * Element access: \c idx = \c iaod*n_h2o*n_wl + \c ih2o*n_wl + \c iwl
 *
 * All mandatory arrays (\c R_atm … \c s_alb) must be pre-allocated by the
 * caller.  Optional pointers (\c T_down_dir, \c R_atmQ, \c R_atmU) are
 * populated only when non-NULL on input; pass NULL to skip.
 */
typedef struct {
    float *R_atm;      /*!< Atmospheric path reflectance — Stokes I [0, 1) */
    float *T_down;     /*!< Total downward transmittance (direct + diffuse) [0, 1] */
    float *T_up;       /*!< Total upward transmittance (direct + diffuse) [0, 1] */
    float *s_alb;      /*!< Spherical albedo of the atmosphere [0, 1) */
    float *T_down_dir; /*!< Direct (beam-only) component of \c T_down.
                        *   NULL → not computed (saves RAM and time).
                        *   Required by atcorr_terrain_T_down(). */
    float *R_atmQ;     /*!< Q Stokes component of path reflectance.
                        *   NULL unless \c enable_polar=1 in ::LutConfig.
                        *   Linearly interpolated from 20 reference wavelengths. */
    float *R_atmU;     /*!< U Stokes component; same layout as \c R_atmQ. */
} LutArrays;

/**
 * \brief Compute a full 3-D atmospheric correction LUT.
 *
 * Runs DISCOM once per AOD grid point (OpenMP-parallel over AOD dimension).
 * Gas transmittance is applied at each (H₂O, λ) combination via the reptran
 * parameterisation inside the AOD loop.
 *
 * \param[in]  cfg  LUT grid specification and scene geometry.
 * \param[out] out  Pre-allocated output arrays (R_atm … s_alb must be
 *                  \c n_aod×n_h2o×n_wl floats each; optional pointers
 *                  T_down_dir, R_atmQ, R_atmU populated when non-NULL).
 * \return 0 on success; negative error code on failure.
 */
int atcorr_compute_lut(const LutConfig *cfg, LutArrays *out);

/* ═══════════════════════════════════════════════════════════════════════════
 * Single-point atmospheric correction
 * ═══════════════════════════════════════════════════════════════════════════ */

/**
 * \brief Lambertian BOA reflectance inversion.
 *
 * Inverts the 6SV scalar radiative-transfer forward model:
 * \f[
 *   \rho_{BOA} = \frac{y}{1 + s \cdot y}, \quad
 *   y = \frac{\rho_{TOA} - R_{atm}}{T_\downarrow \cdot T_\uparrow}
 * \f]
 *
 * \param[in] rho_toa TOA reflectance at the band wavelength.
 * \param[in] R_atm   Atmospheric path reflectance (LUT value).
 * \param[in] T_down  Downward transmittance (LUT value).
 * \param[in] T_up    Upward transmittance (LUT value).
 * \param[in] s_alb   Spherical albedo (LUT value).
 * \return Surface BOA reflectance ρ_BOA.
 */
static inline float atcorr_invert(float rho_toa, float R_atm,
                                   float T_down, float T_up, float s_alb)
{
    float y = (rho_toa - R_atm) / (T_down * T_up + 1e-10f);
    return y / (1.0f + s_alb * y + 1e-10f);
}

/**
 * \brief BRDF-coupled BOA reflectance inversion (6SV idirec=1 equivalent).
 *
 * When the surface is non-Lambertian, the multiple-scattering feedback
 * (spherical-albedo denominator) uses the bihemispherical (white-sky) albedo
 * ρ̄ of the BRDF model rather than the directional ρ_BOA:
 * \f[
 *   \rho_{BRDF} = y \cdot (1 - s \cdot \bar{\rho}), \quad
 *   y = \frac{\rho_{TOA} - R_{atm}}{T_\downarrow \cdot T_\uparrow}
 * \f]
 *
 * \param[in] rho_toa  TOA reflectance at the band wavelength.
 * \param[in] R_atm    Atmospheric path reflectance (LUT value).
 * \param[in] T_down   Downward transmittance (LUT value).
 * \param[in] T_up     Upward transmittance (LUT value).
 * \param[in] s_alb    Spherical albedo (LUT value).
 * \param[in] rho_albe Bihemispherical (white-sky) albedo ρ̄ of the BRDF
 *                     surface, from sixs_brdf_albe().
 * \return Bidirectional reflectance factor ρ_BRDF(θs, θv, φ).
 */
static inline float atcorr_invert_brdf(float rho_toa, float R_atm,
                                        float T_down,  float T_up,
                                        float s_alb,   float rho_albe)
{
    float y = (rho_toa - R_atm) / (T_down * T_up + 1e-10f);
    return y * (1.0f - s_alb * rho_albe);
}

/* ═══════════════════════════════════════════════════════════════════════════
 * Solar irradiance and Earth–Sun distance
 * ═══════════════════════════════════════════════════════════════════════════ */

/**
 * \brief Thuillier solar irradiance spectrum.
 *
 * Returns E₀ in W/(m² µm) at wavelength \p wl_um, linearly interpolated
 * from the 6SV2.1 Thuillier (2003) reference spectrum.  Clamped to zero
 * outside [0.25, 4.0] µm.
 *
 * \param[in] wl_um Wavelength [µm].
 * \return E₀ [W m⁻² µm⁻¹] ≥ 0.
 */
float sixs_E0(float wl_um);

/**
 * \brief Squared Earth–Sun distance for a given day of year.
 *
 * Uses the approximation \f$ d = 1 - 0.01670963 \cos(2\pi(DOY-3)/365) \f$
 * (Liou 2002), so perihelion (DOY≈3) gives d²<1 and aphelion (DOY≈185)
 * gives d²>1.
 *
 * \param[in] doy Day of year [1, 365].
 * \return d² [AU²].
 */
double sixs_earth_sun_dist2(int doy);

/* ═══════════════════════════════════════════════════════════════════════════
 * LUT spectral slice and per-pixel interpolation
 * ═══════════════════════════════════════════════════════════════════════════ */

/**
 * \brief Bilinear LUT interpolation at a fixed (AOD, H₂O) point.
 *
 * Fills per-wavelength correction arrays [n_wl] by bilinear interpolation of
 * the 3-D LUT along the AOD and H₂O axes.  Useful for pre-computing
 * scene-average atmospheric parameters before the pixel-level inversion loop.
 *
 * \param[in]  cfg      LUT grid specification.
 * \param[in]  lut      Pre-computed LUT arrays.
 * \param[in]  aod_val  AOD at 550 nm (clamped to LUT range).
 * \param[in]  h2o_val  Water-vapour column [g/cm²] (clamped to LUT range).
 * \param[out] Rs       Path reflectance [n_wl].
 * \param[out] Tds      Downward transmittance [n_wl].
 * \param[out] Tus      Upward transmittance [n_wl].
 * \param[out] ss       Spherical albedo [n_wl].
 * \param[out] Tdds     Direct downward transmittance [n_wl]; pass NULL to skip
 *                      (requires \c lut->T_down_dir to be non-NULL).
 */
void atcorr_lut_slice(const LutConfig *cfg, const LutArrays *lut,
                      float aod_val, float h2o_val,
                      float *Rs, float *Tds, float *Tus, float *ss,
                      float *Tdds);

/**
 * \brief Trilinear LUT interpolation at a single (AOD, H₂O, λ) point.
 *
 * Performs binary-search bracketing + 8-corner trilinear interpolation to
 * return a single set of atmospheric correction parameters.  All values are
 * clamped to the LUT grid boundaries; no extrapolation.
 *
 * Used for per-pixel correction with spatially varying AOD/H₂O maps and
 * for AOD-perturbation uncertainty estimation in uncertainty_compute_band().
 *
 * \param[in]  cfg     LUT grid specification.
 * \param[in]  lut     Pre-computed LUT arrays.
 * \param[in]  aod_val AOD at 550 nm.
 * \param[in]  h2o_val WVC [g/cm²].
 * \param[in]  wl_um   Wavelength [µm].
 * \param[out] R_atm   Path reflectance.
 * \param[out] T_down  Downward transmittance.
 * \param[out] T_up    Upward transmittance.
 * \param[out] s_alb   Spherical albedo.
 */
void atcorr_lut_interp_pixel(const LutConfig *cfg, const LutArrays *lut,
                               float aod_val, float h2o_val, float wl_um,
                               float *R_atm, float *T_down,
                               float *T_up,  float *s_alb);

/* ═══════════════════════════════════════════════════════════════════════════
 * SRF gas-transmittance correction
 * ═══════════════════════════════════════════════════════════════════════════ */

/**
 * \brief Configuration for Gaussian SRF gas-transmittance correction.
 *
 * Drives atcorr_srf_compute() to replace the coarse 6SV Curtis-Godson gas
 * parameterisation with libRadtran reptran fine-resolution (~0.05 nm) gas
 * transmittance convolved with the sensor spectral response function.
 */
typedef struct {
    const float *fwhm_um;   /*!< Per-band FWHM [µm], length \c n_wl (aligned with
                             *   ::LutConfig::wl).  NULL → correct all bands. */
    float threshold_um;     /*!< Only correct bands with FWHM < threshold [µm].
                             *   ≤ 0 → use default of 0.005 µm (5 nm). */
} SrfConfig;

/**
 * \brief Opaque per-band SRF correction table.  Created by atcorr_srf_compute().
 */
typedef struct SrfCorrection_ SrfCorrection;

/**
 * \brief Compute per-band, per-H₂O SRF gas-transmittance correction factors.
 *
 * Runs 4 × n_h2o \c uvspec subprocesses (fine/coarse × down/up × each H₂O)
 * parallelised with OpenMP.  The \c uvspec binary is located via PATH,
 * \c $LIBRADTRAN_DIR/bin, or \c $GISBASE/bin.
 *
 * \param[in] srf_cfg SRF configuration (FWHM array and threshold).
 * \param[in] lut_cfg LUT grid specification (wavelengths, H₂O grid, geometry).
 * \return Pointer to correction table, or NULL if \c uvspec is not found
 *         or no bands fall below the FWHM threshold.
 */
SrfCorrection *atcorr_srf_compute(const SrfConfig *srf_cfg,
                                   const LutConfig *lut_cfg);

/**
 * \brief Apply SRF correction factors to a LUT in place.
 *
 * Must be called after atcorr_compute_lut() and before pixel inversion.
 * Multiplies \c T_down and \c T_up by the H₂O-matched correction factor
 * for each wavelength band.
 *
 * \param[in]     srf  Correction table from atcorr_srf_compute().
 * \param[in]     cfg  LUT grid specification.
 * \param[in,out] lut  LUT arrays (T_down and T_up modified in place).
 */
void atcorr_srf_apply(const SrfCorrection *srf,
                       const LutConfig     *cfg,
                       LutArrays           *lut);

/**
 * \brief Free memory allocated by atcorr_srf_compute().
 *
 * \param[in] srf Correction table to free (NULL is a no-op).
 */
void atcorr_srf_free(SrfCorrection *srf);

/* ═══════════════════════════════════════════════════════════════════════════
 * Solar position
 * ═══════════════════════════════════════════════════════════════════════════ */

/**
 * \brief Compute solar zenith and azimuth angles.
 *
 * C port of the 6SV \c POSSOL Fortran subroutine.
 *
 * \param[in]  month Calendar month [1, 12].
 * \param[in]  jday  Julian day of month [1, 31].
 * \param[in]  tu    UTC decimal hours.
 * \param[in]  xlon  Longitude [degrees East].
 * \param[in]  xlat  Latitude [degrees North].
 * \param[out] asol  Solar zenith angle [degrees].
 * \param[out] phi0  Solar azimuth angle [degrees, clockwise from North].
 * \param[in]  ia    Year (non-zero enables leap-year correction).
 */
void sixs_possol(int month, int jday, float tu, float xlon, float xlat,
                 float *asol, float *phi0, int ia);

/* ═══════════════════════════════════════════════════════════════════════════
 * Rayleigh analytical reflectance
 * ═══════════════════════════════════════════════════════════════════════════ */

/**
 * \brief Chandrasekhar analytical Rayleigh reflectance.
 *
 * C port of the 6SV \c CHAND Fortran function.
 *
 * \param[in] xphi Relative azimuth [degrees, 0 = backscatter].
 * \param[in] xmuv cos(view zenith angle).
 * \param[in] xmus cos(solar zenith angle).
 * \param[in] xtau Rayleigh optical depth.
 * \return Molecular path reflectance [0, 1].
 */
float sixs_chand(float xphi, float xmuv, float xmus, float xtau);

/* ═══════════════════════════════════════════════════════════════════════════
 * Environmental (adjacency) factors
 * ═══════════════════════════════════════════════════════════════════════════ */

/**
 * \brief Compute adjacency-effect correction factors.
 *
 * C port of the 6SV \c ENVIRO Fortran subroutine.
 *
 * \param[in]  difr  Diffuse Rayleigh optical depth.
 * \param[in]  difa  Diffuse aerosol optical depth.
 * \param[in]  r     Total aerosol OD at 550 nm.
 * \param[in]  palt  Sensor altitude [km].
 * \param[in]  xmuv  cos(view zenith angle).
 * \param[out] fra   Rayleigh adjacency factor.
 * \param[out] fae   Aerosol adjacency factor.
 * \param[out] fr    Combined adjacency factor.
 */
void sixs_enviro(float difr, float difa, float r, float palt, float xmuv,
                 float *fra, float *fae, float *fr);

/* ═══════════════════════════════════════════════════════════════════════════
 * Version
 * ═══════════════════════════════════════════════════════════════════════════ */

/**
 * \brief Library version string.
 * \return Pointer to a static null-terminated string, e.g. \c "1.0.0".
 */
const char *atcorr_version(void);

#ifdef __cplusplus
}
#endif
