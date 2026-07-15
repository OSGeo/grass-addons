/**
 * \file retrieve.h
 * \brief Image-based atmospheric state retrievals for i.hyper.atcorr.
 *
 * All functions are pure computation with no GRASS dependencies.
 * The caller is responsible for allocating output buffers and supplying
 * pre-loaded per-pixel band arrays.
 *
 * Implemented algorithms:
 *   - H₂O from 940 nm band depth (Kaufman & Gao 1992)
 *   - AOD from MODIS dark-target DDV (Kaufman et al. 1997)
 *   - O₃ from Chappuis band depth at 600 nm
 *   - Surface pressure from ISA barometric formula or O₂-A band depth
 *   - Cloud / shadow / water / snow quality bitmask
 *   - MAIAC-inspired patch-median AOD spatial regularisation
 *
 * \note All radiance inputs are in W m⁻² sr⁻¹ µm⁻¹ (= mW m⁻² sr⁻¹ nm⁻¹).
 *
 * References:
 *   - Kaufman, Y.J. & Gao, B.C. (1992), IEEE TGRS 30:871–884 (H₂O)
 *   - Kaufman, Y.J. et al. (1997), IEEE TGRS 35:1286–1298 (AOD DDV)
 *   - Bogumil, K. et al. (2003), J. Photochem. Photobiol. A 157:167–184 (O₃)
 *   - ICAO (1993), International Standard Atmosphere (ISA pressure)
 *   - Schläpfer, D. et al. (1998), SPIE 3502 (O₂-A pressure)
 *   - Lyapustin, A. et al. (2011), JGR 116:D05203 (MAIAC)
 *
 * (C) 2025-2026 Yann. GNU GPL ≥ 2.
 *
 * \author Yann
 */
#pragma once
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

/* ═══════════════════════════════════════════════════════════════════════════
 * H₂O column from 940 nm band depth
 * ═══════════════════════════════════════════════════════════════════════════ */

/**
 * \brief Per-pixel water-vapour column retrieval from 940 nm band depth.
 *
 * Continuum interpolation method (Kaufman & Gao 1992):
 * \f[
 *   L_{cont} = \mathrm{interp}(L_{865}, L_{1040})\big|_{940\,\mathrm{nm}}
 *   \quad D = \max(0,\; 1 - L_{940}/L_{cont})
 *   \quad WVC = D \;/\; (K_{940} \cdot m)
 * \f]
 * with m = 1/cos(SZA) + 1/cos(VZA), and K₉₄₀ scaled by sensor FWHM:
 * \f[
 *   K_{940}(\Delta\lambda) = 0.036 \left(\frac{50\,\mathrm{nm}}{\Delta\lambda}\right)^{0.90}
 * \f]
 * Calibrated against MODIS (50 nm, K=0.036) and Tanager (6.8 nm, K≈0.217;
 * empirical: D=0.718, WVC=1.54 g/cm², Kanpur 2025-03-21).  Exponent α=0.90
 * corrects for spectral line saturation in the 5–8 nm FWHM regime.
 * Pass fwhm_um = 0 to use the broadband default K=0.036 (MODIS-equivalent).
 *
 * NaN or non-positive radiance pixels default to 2.0 g/cm².
 * Output is clamped to [0.1, 8.0] g/cm².
 *
 * \param[in]  L_865    Per-pixel TOA radiance near 865 nm [npix].
 * \param[in]  L_940    Per-pixel TOA radiance near 940 nm [npix].
 * \param[in]  L_1040   Per-pixel TOA radiance near 1040 nm [npix].
 * \param[in]  fwhm_um  FWHM of the 940 nm band in µm (0 = use default K).
 * \param[in]  npix     Number of pixels.
 * \param[in]  sza_deg  Solar zenith angle [degrees].
 * \param[in]  vza_deg  View zenith angle [degrees].
 * \param[out] out_wvc  Pre-allocated float[npix]; WVC [g/cm²] per pixel.
 */
void retrieve_h2o_940(const float *L_865,  const float *L_940,
                       const float *L_1040, float fwhm_um,
                       int npix,
                       float sza_deg, float vza_deg,
                       float *out_wvc);

/* ═══════════════════════════════════════════════════════════════════════════
 * AOD from MODIS Dark Dense Vegetation (DDV)
 * ═══════════════════════════════════════════════════════════════════════════ */

/**
 * \brief Scene-mean and per-pixel AOD from the MODIS dark-target DDV algorithm.
 *
 * DDV mask: 0.01 < ρ_2130 < 0.25 AND NDVI(860, 660) > 0.1.
 * Surface reflectance:  ρ_surf(470) = 0.25 ρ_2130, ρ_surf(660) = 0.50 ρ_2130.
 * Path reflectance:     ρ_path = max(0, ρ_TOA − ρ_surf).
 * AOD inversion:        τ = ρ_path × 4μs / (ω₀ P_HG),  g=0.65, ω₀=0.89.
 * Ångström interpolation to 550 nm: τ_550 = τ_470 × (550/470)^(−α).
 * Non-DDV pixels are filled with the scene-mean AOD.
 *
 * \param[in]  L_470   Per-pixel TOA radiance near 470 nm [npix].
 * \param[in]  L_660   Per-pixel TOA radiance near 660 nm [npix].
 * \param[in]  L_860   Per-pixel TOA radiance near 860 nm [npix].
 * \param[in]  L_2130  Per-pixel TOA radiance near 2130 nm [npix].
 * \param[in]  npix    Number of pixels.
 * \param[in]  doy     Day of year [1, 365].
 * \param[in]  sza_deg Solar zenith angle [degrees].
 * \param[out] out_aod Pre-allocated float[npix]; AOD at 550 nm per pixel.
 * \return Scene-mean AOD at 550 nm (0.15 fallback when no DDV pixels found).
 */
float retrieve_aod_ddv(const float *L_470,  const float *L_660,
                        const float *L_860,  const float *L_2130,
                        int npix, int doy, float sza_deg,
                        float *out_aod);

/* ═══════════════════════════════════════════════════════════════════════════
 * O₃ column from Chappuis band depth
 * ═══════════════════════════════════════════════════════════════════════════ */

/**
 * \brief Scene-mean ozone column from the Chappuis 600 nm band depth.
 *
 * Continuum between 540 nm and 680 nm; feature at 600 nm:
 * \f[
 *   D = \max(0,\; 1 - L_{600}/L_{cont})
 *   \quad O_3 = D \;/\; (\sigma_{600} \cdot m)
 * \f]
 * with σ₆₀₀ ≈ 1.0×10⁻⁴ DU⁻¹ (Bogumil 2003) and m = 1/cos(SZA) + 1/cos(VZA).
 *
 * \param[in] L_540   Per-pixel TOA radiance near 540 nm [npix].
 * \param[in] L_600   Per-pixel TOA radiance near 600 nm [npix].
 * \param[in] L_680   Per-pixel TOA radiance near 680 nm [npix].
 * \param[in] npix    Number of pixels.
 * \param[in] sza_deg Solar zenith angle [degrees].
 * \param[in] vza_deg View zenith angle [degrees].
 * \return Scene-mean O₃ column [Dobson units] ∈ [50, 800]; fallback 300 DU.
 */
float retrieve_o3_chappuis(const float *L_540, const float *L_600,
                            const float *L_680, int npix,
                            float sza_deg, float vza_deg);

/* ═══════════════════════════════════════════════════════════════════════════
 * Surface pressure from mean terrain elevation (ISA)
 * ═══════════════════════════════════════════════════════════════════════════ */

/**
 * \brief Surface pressure from mean terrain elevation (ISA barometric formula).
 *
 * \f[
 *   P = 1013.25 \times (1 - 2.2558 \times 10^{-5}\, h)^{5.2559} \quad [\mathrm{hPa}]
 * \f]
 * Valid for h ∈ [0, 11 000] m; clamped at boundaries.
 *
 * \param[in] elev_m Mean scene elevation [m].
 * \return Surface pressure [hPa].
 */
float retrieve_pressure_isa(float elev_m);

/* ═══════════════════════════════════════════════════════════════════════════
 * Surface pressure from O₂-A band depth
 * ═══════════════════════════════════════════════════════════════════════════ */

/**
 * \brief Per-pixel surface pressure from the O₂-A 760 nm absorption band.
 *
 * Continuum between 740 nm and 780 nm; feature at 760 nm:
 * \f[
 *   D_{760} = \max(0,\; 1 - L_{760}/L_{cont})
 *   \quad P = P_0 \cdot D_{760} \;/\; (K_{O_2} \cdot m)
 * \f]
 * with K_O₂ = 0.25 (calibrated for ~10 nm FWHM; Schläpfer 1998) and
 * m = 1/cos(SZA) + 1/cos(VZA).
 *
 * NaN or non-positive radiance pixels default to P₀ = 1013.25 hPa.
 * Output clamped to [200, 1100] hPa.
 *
 * \param[in]  L_740         Per-pixel TOA radiance near 740 nm [npix].
 * \param[in]  L_760         Per-pixel TOA radiance near 760 nm [npix].
 * \param[in]  L_780         Per-pixel TOA radiance near 780 nm [npix].
 * \param[in]  npix          Number of pixels.
 * \param[in]  sza_deg       Solar zenith angle [degrees].
 * \param[in]  vza_deg       View zenith angle [degrees].
 * \param[out] out_pressure  Pre-allocated float[npix]; pressure [hPa] per pixel.
 */
void retrieve_pressure_o2a(const float *L_740, const float *L_760,
                             const float *L_780, int npix,
                             float sza_deg, float vza_deg,
                             float *out_pressure);

/* ═══════════════════════════════════════════════════════════════════════════
 * Quality bitmask constants and per-pixel classifier
 * ═══════════════════════════════════════════════════════════════════════════ */

/** \defgroup quality_mask Quality bitmask bit definitions
 *  Bits set in the output of retrieve_quality_mask().
 *  @{ */
#define RETRIEVE_MASK_CLOUD  0x01u  /*!< High blue TOA, or very bright NIR */
#define RETRIEVE_MASK_SHADOW 0x02u  /*!< Uniformly dark in VIS + NIR */
#define RETRIEVE_MASK_WATER  0x04u  /*!< Low NIR + negative NDVI */
#define RETRIEVE_MASK_SNOW   0x08u  /*!< NDSI > 0.4 and NIR > 0.1 */
/** @} */

/**
 * \brief Per-pixel cloud / shadow / water / snow quality bitmask.
 *
 * Classifies each pixel using TOA reflectance thresholds (converted from
 * radiance using sixs_E0() and the Earth–Sun distance at \p doy):
 *   - **Cloud**: TOA_blue > 0.25 AND NDVI < 0.2, OR TOA_nir > 0.60
 *   - **Shadow**: TOA_blue < 0.04 AND TOA_red < 0.04 AND TOA_nir < 0.04
 *   - **Water**: TOA_nir < 0.05 AND NDVI < 0.0
 *   - **Snow**: NDSI > 0.4 AND TOA_nir > 0.1 (only when \p L_swir ≠ NULL)
 *
 * \param[in]  L_blue    Per-pixel TOA radiance near 470 nm [npix].
 * \param[in]  L_red     Per-pixel TOA radiance near 660 nm [npix].
 * \param[in]  L_nir     Per-pixel TOA radiance near 860 nm [npix].
 * \param[in]  L_swir    Per-pixel TOA radiance near 1600 nm [npix]; NULL → skip snow.
 * \param[in]  npix      Number of pixels.
 * \param[in]  doy       Day of year [1, 365] (for Earth–Sun distance).
 * \param[in]  sza_deg   Solar zenith angle [degrees].
 * \param[out] out_mask  Pre-allocated uint8_t[npix]; bitmask per pixel.
 *
 * \see RETRIEVE_MASK_CLOUD, RETRIEVE_MASK_SHADOW, RETRIEVE_MASK_WATER, RETRIEVE_MASK_SNOW
 */
void retrieve_quality_mask(const float *L_blue, const float *L_red,
                            const float *L_nir,  const float *L_swir,
                            int npix, int doy, float sza_deg,
                            uint8_t *out_mask);

/* ═══════════════════════════════════════════════════════════════════════════
 * MAIAC-inspired patch AOD spatial regularisation
 * ═══════════════════════════════════════════════════════════════════════════ */

/**
 * \brief Patch-median AOD spatial regularisation (MAIAC-inspired).
 *
 * Divides the image into non-overlapping \p patch_sz × \p patch_sz blocks.
 * Each block's AOD is replaced by its per-block median (robust to DDV outliers).
 * Blocks with no valid AOD are filled by inverse-distance weighting from
 * neighbouring block centroids.
 *
 * \param[in,out] aod_data  float[nrows × ncols], updated in place.
 * \param[in]     nrows     Image height in pixels.
 * \param[in]     ncols     Image width in pixels.
 * \param[in]     patch_sz  Block side in pixels (typical: 32 for 30 m, 16 for 5 m).
 *
 * \see Lyapustin, A. et al. (2011), MAIAC. JGR 116, D05203.
 */
void retrieve_aod_maiac(float *aod_data, int nrows, int ncols, int patch_sz);

/* ═══════════════════════════════════════════════════════════════════════════
 * DASF retrieval — Directional Area Scattering Factor
 * ═══════════════════════════════════════════════════════════════════════════ */

/**
 * \brief PROSPECT-D leaf single-scattering albedo (R+T) via linear interpolation.
 *
 * Table covers 705–795 nm at 5 nm steps (Féret et al. 2017, Cab=40).
 *
 * \param[in] wl_um  Wavelength in µm.
 * \return Leaf albedo ω_L ∈ [0.74, 0.912]; -1 if outside table range.
 */
float leaf_albedo_nir(float wl_um);

/**
 * \brief Per-pixel DASF retrieval from corrected BRF in the 710–790 nm NIR plateau.
 *
 * Directional Area Scattering Factor (Knyazikhin et al. 2013 PNAS):
 * \f[
 *   \rho(\lambda) \approx \mathrm{DASF} \cdot \omega_L(\lambda)
 * \f]
 * Solved as linear least squares: \f$\mathrm{DASF} = \Sigma(\rho\,\omega_L) / \Sigma(\omega_L^2)\f$.
 *
 * Output is NaN for pixels with fewer than 3 valid bands or near-zero denominator.
 * Values are clipped to [0.01, 1.0].
 *
 * \param[in]  refl      Pre-corrected BRF, band-major order [n_dasf × npix].
 * \param[in]  wl_dasf   Wavelengths of the DASF bands [µm], length \p n_dasf.
 * \param[in]  n_dasf    Number of DASF bands (those within 710–790 nm).
 * \param[in]  npix      Number of pixels.
 * \param[out] out_dasf  Caller-allocated float[npix]; DASF per pixel.
 *
 * \see Knyazikhin, Y. et al. (2013) PNAS 110, E185–E192.
 */
void retrieve_dasf(const float *refl, const float *wl_dasf, int n_dasf,
                   int npix, float *out_dasf);

/* ═══════════════════════════════════════════════════════════════════════════
 * Generic H₂O triplet retrieval (any absorption feature)
 * ═══════════════════════════════════════════════════════════════════════════ */

/**
 * \brief Per-pixel H₂O retrieval from any (lo, feat, hi) wavelength triplet.
 *
 * Continuum interpolation:
 * \f[
 *   L_{cont} = L_{lo}(1-f) + L_{hi}\,f,\quad
 *   f = \frac{\lambda_{feat}-\lambda_{lo}}{\lambda_{hi}-\lambda_{lo}}
 * \f]
 * \f[
 *   D = \max(0,\; 1 - L_{feat}/L_{cont}), \quad
 *   WVC = D \;/\; (K \cdot m)
 * \f]
 * K is scaled from K_ref using the same power law as retrieve_h2o_940():
 * K = K_ref × (fwhm_ref / fwhm)^0.90 when fwhm < fwhm_ref; otherwise K = K_ref.
 *
 * Pixels with D ∉ [D_min, D_max] or non-positive radiance are marked invalid
 * and assigned WVC = 2.0 g/cm² (fallback).
 *
 * \param[in]  L_lo, L_feat, L_hi  Per-pixel TOA radiance at the triplet bands [npix].
 * \param[in]  wl_lo_um, wl_feat_um, wl_hi_um  Band centre wavelengths [µm].
 * \param[in]  K_ref       Broadband reference absorption coefficient [cm²/g].
 * \param[in]  fwhm_ref_um FWHM of the reference sensor [µm].
 * \param[in]  fwhm_um     Actual sensor FWHM [µm]; 0 = use K_ref directly.
 * \param[in]  D_min       Minimum valid band depth (below = too noisy).
 * \param[in]  D_max       Maximum valid band depth (above = saturation).
 * \param[in]  npix        Number of pixels.
 * \param[in]  sza_deg     Solar zenith angle [degrees].
 * \param[in]  vza_deg     View zenith angle [degrees].
 * \param[out] out_wvc     Pre-allocated float[npix]; WVC [g/cm²] per pixel.
 * \param[out] out_valid   Pre-allocated uint8_t[npix]; 1=valid, 0=excluded (may be NULL).
 */
void retrieve_h2o_triplet(const float *L_lo,   const float *L_feat,
                           const float *L_hi,
                           float wl_lo_um,  float wl_feat_um, float wl_hi_um,
                           float K_ref, float fwhm_ref_um, float fwhm_um,
                           float D_min, float D_max,
                           int npix, float sza_deg, float vza_deg,
                           float *out_wvc, uint8_t *out_valid);

/* ═══════════════════════════════════════════════════════════════════════════
 * Multi-band H₂O consensus
 * ═══════════════════════════════════════════════════════════════════════════ */

/**
 * \brief Per-pixel median consensus across multiple H₂O retrieval estimates.
 *
 * For each pixel, collects valid estimates (where valid_arrays[m][i] != 0),
 * computes the median (exact for 2–3 values), and writes it to out_wvc.
 * Falls back to WVC = 2.0 g/cm² where no estimate is valid.
 *
 * \param[in]  n_methods     Number of retrieval methods (max 3 used for median).
 * \param[in]  wvc_arrays    Array of n_methods pointers to float[npix] WVC arrays.
 * \param[in]  valid_arrays  Array of n_methods pointers to uint8_t[npix] validity flags.
 * \param[in]  npix          Number of pixels.
 * \param[out] out_wvc       Pre-allocated float[npix]; consensus WVC [g/cm²].
 * \return Number of pixels where at least 2 estimates agreed (n_valid ≥ 2).
 */
int retrieve_h2o_consensus(int n_methods,
                            float * const *wvc_arrays,
                            uint8_t * const *valid_arrays,
                            int npix,
                            float *out_wvc);

#ifdef __cplusplus
}
#endif
