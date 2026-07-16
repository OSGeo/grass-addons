/**
 * \file brdf.h
 * \brief BRDF surface reflectance models — C port of 6SV2.1 BRDF Fortran subroutines.
 *
 * Provides a single-point evaluation API (sixs_brdf_eval()) and a
 * hemispherical integration helper (sixs_brdf_albe()) dispatched through
 * the ::BrdfType enum.  Also declares atcorr_brdf_normalize() for NBAR
 * normalisation using the MODIS MCD43 Ross-Thick + Li-Sparse kernel model.
 *
 * (C) 2025-2026 Yann. GNU GPL ≥ 2.
 *
 * \author Yann
 */
#pragma once

/* ═══════════════════════════════════════════════════════════════════════════
 * BRDF model identifiers
 * ═══════════════════════════════════════════════════════════════════════════ */

/**
 * \brief Surface BRDF model selector.
 *
 * Passed to sixs_brdf_eval() and sixs_brdf_albe() and stored in
 * ::LutConfig::brdf_type.  Models marked "stub" require external
 * routines not yet ported.
 */
typedef enum {
    BRDF_LAMBERTIAN    = 0,  /*!< Lambertian (constant reflectance; analytically handled) */
    BRDF_RAHMAN        = 1,  /*!< Rahman-Pinty-Verstraete (RPV) */
    BRDF_ROUJEAN       = 2,  /*!< Roujean volumetric kernel */
    BRDF_HAPKE         = 3,  /*!< Hapke canopy model */
    BRDF_OCEAN         = 4,  /*!< Ocean: Cox-Munk sun glint + water body */
    BRDF_WALTHALL      = 5,  /*!< Walthall polynomial */
    BRDF_MINNAERT      = 6,  /*!< Minnaert */
    BRDF_VERSFELD      = 7,  /*!< Verstraete-Pinty (requires mvbp1 — stub) */
    BRDF_IAPI          = 8,  /*!< Iaquinta-Pinty 3-layer canopy (stub) */
    BRDF_ROSSLIMAIGNAN = 9,  /*!< Ross-Thick + Li-Sparse + Maignan hot-spot */
} BrdfType;

/* ═══════════════════════════════════════════════════════════════════════════
 * Per-model parameter union
 * ═══════════════════════════════════════════════════════════════════════════ */

/**
 * \brief Per-model BRDF parameters.
 *
 * Only the member matching the chosen ::BrdfType is used.
 * Initialise with \c memset(&p, 0, sizeof(p)) before setting the active member.
 */
typedef union {
    struct { float rho0; } lambertian;              /*!< Constant surface reflectance ρ₀ */
    struct { float rho0, af, k; } rahman;           /*!< RPV: ρ₀ intensity, af asymmetry, k structure */
    struct { float k0, k1, k2; } roujean;           /*!< k₀ isotropic, k₁ geometric, k₂ volumetric */
    struct { float om, af, s0, h; } hapke;          /*!< ω single-scatter albedo, af asymmetry, s₀ hotspot amp, h width */
    struct { float wspd, azw, sal, pcl, wl; } ocean;/*!< Wind speed [m/s], azimuth offset [deg], salinity [ppt], chlorophyll [mg/m³], wavelength [µm] */
    struct { float a, ap, b, c; } walthall;         /*!< Polynomial coefficients a, a', b, c */
    struct { float k, b; } minnaert;                /*!< k Minnaert exponent, b albedo normalisation */
    struct { float f_iso, f_vol, f_geo; } rosslimaignan; /*!< Ross-Li kernel weights */
} BrdfParams;

/* ═══════════════════════════════════════════════════════════════════════════
 * Public API
 * ═══════════════════════════════════════════════════════════════════════════ */

#ifdef __cplusplus
extern "C" {
#endif

/**
 * \brief Evaluate BRDF at a single geometry point.
 *
 * Returns the bidirectional reflectance factor ρ_s (dimensionless) for the
 * specified model and geometry.  Returns 0.0 for \c BRDF_LAMBERTIAN (the
 * Lambertian coupling is handled analytically by atcorr_invert()).
 *
 * \param[in] type    BRDF model selector (::BrdfType).
 * \param[in] params  Model-specific parameters (use the matching union member).
 * \param[in] cos_sza cos(solar zenith angle).
 * \param[in] cos_vza cos(view zenith angle).
 * \param[in] raa_deg Relative azimuth angle [degrees, 0 = forward scatter].
 * \return Directional reflectance ρ_s ≥ 0.
 */
float sixs_brdf_eval(BrdfType type, const BrdfParams *params,
                     float cos_sza, float cos_vza, float raa_deg);

/**
 * \brief Bihemispherical (white-sky) albedo by numerical integration.
 *
 * Integrates sixs_brdf_eval() over the outgoing hemisphere using a
 * midpoint quadrature grid of size \p n_phi × \p n_theta.
 *
 * Used by the BRDF-coupled inversion formula in atcorr_invert_brdf().
 *
 * \param[in] type    BRDF model selector.
 * \param[in] params  Model parameters.
 * \param[in] cos_sza cos(solar zenith angle).
 * \param[in] n_phi   Azimuth quadrature points (suggested: 48).
 * \param[in] n_theta Zenith quadrature points (suggested: 24).
 * \return White-sky albedo ρ̄ ∈ [0, 1].
 */
float sixs_brdf_albe(BrdfType type, const BrdfParams *params,
                     float cos_sza, int n_phi, int n_theta);

/**
 * \brief NBAR normalisation using the MODIS MCD43 linear kernel model.
 *
 * Normalises ρ_BOA from the observation geometry to nadir view (vza=0, raa=0)
 * using the Ross-Thick + Li-Sparse (standard MODIS MCD43) kernels:
 * \f[
 *   \rho_{NBAR} = \rho_{BOA} \cdot \frac{f_{obs}(SZA_{NBAR}, 0, 0)}
 *                                       {f_{obs}(SZA_{obs}, VZA_{obs}, RAA_{obs})}
 * \f]
 * where \f$ f = f_{iso} + f_{vol} K_{RT} + f_{geo} K_{LS} \f$.
 *
 * Returns \p rho_boa unchanged when f_obs ≈ 0 (division-by-zero guard) or
 * when \c f_vol == 0 and \c f_geo == 0 (Lambertian surface, no correction needed).
 *
 * \param[in] rho_boa  BOA reflectance to normalise.
 * \param[in] f_iso    Ross-Li isotropic kernel weight (from MCD43A1).
 * \param[in] f_vol    Ross-Thick volumetric kernel weight.
 * \param[in] f_geo    Li-Sparse geometric kernel weight.
 * \param[in] sza_obs  Solar zenith [degrees] at acquisition.
 * \param[in] vza_obs  View zenith [degrees] at acquisition.
 * \param[in] raa_obs  Relative azimuth [degrees] at acquisition.
 * \param[in] sza_nbar Reference solar zenith [degrees] for NBAR output
 *                     (typically equal to \p sza_obs — normalises view only).
 * \return ρ_NBAR.
 */
float atcorr_brdf_normalize(float rho_boa,
                             float f_iso, float f_vol, float f_geo,
                             float sza_obs, float vza_obs, float raa_obs,
                             float sza_nbar);

#ifdef __cplusplus
}
#endif
