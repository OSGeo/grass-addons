/**
 * \file surface_model.h
 * \brief 3-component surface reflectance prior and MAP regularisation.
 *
 * Implements a Gaussian mixture prior with three components (vegetation,
 * soil, water) whose reference spectra are hardcoded at 29 key wavelengths
 * (0.40–2.50 µm) and linearly interpolated to sensor bands at initialisation.
 *
 * The prior is used for:
 *   - Per-pixel surface classification (surface_model_classify()).
 *   - Diagonal MAP regularisation of the full reflectance cube
 *     (surface_model_regularize()) to suppress retrieval artefacts.
 *   - Per-band RT model discrepancy σ (surface_model_discrepancy()).
 *
 * The implementation supports up to SM_MAX_BANDS sensor bands.
 *
 * (C) 2025-2026 Yann. GNU GPL ≥ 2.
 *
 * \author Yann
 */
#pragma once

/** Maximum number of sensor bands supported by this implementation. */
#define SM_MAX_BANDS 2048

/** Number of surface prior components: vegetation (0), soil (1), water (2). */
#define SM_N_COMPONENTS 3

/**
 * \brief Opaque surface model handle.
 *
 * Create with surface_model_alloc(); free with surface_model_free().
 * Holds interpolated reference spectra and component covariances for each
 * sensor band.
 */
typedef struct SurfaceModelImpl_ SurfaceModelImpl;

#ifdef __cplusplus
extern "C" {
#endif

/**
 * \brief Allocate and initialise the surface model for a given sensor.
 *
 * Interpolates the three hardcoded reference spectra to the supplied band
 * centres.  Allocates internal buffers; free with surface_model_free().
 *
 * \param[in] wl_um   Band-centre wavelengths [µm], length \p n_bands.
 * \param[in] n_bands Number of sensor bands (must be ≤ SM_MAX_BANDS).
 * \return Pointer to initialised model, or NULL on allocation failure.
 */
SurfaceModelImpl *surface_model_alloc(const float *wl_um, int n_bands);

/**
 * \brief Classify a single pixel spectrum to the nearest surface component.
 *
 * Uses only VNIR bands (0.40–1.00 µm) for robustness to atmospheric
 * residuals in SWIR.  Classification is by minimum Euclidean distance to
 * the interpolated reference spectra.
 *
 * NaN values in \p refl are safely skipped.
 *
 * \param[in] mdl     Initialised surface model from surface_model_alloc().
 * \param[in] refl    Reflectance spectrum [n_bands].
 * \param[in] n_bands Number of bands.
 * \return Component index: 0 (vegetation), 1 (soil), or 2 (water).
 */
int surface_model_classify(const SurfaceModelImpl *mdl,
                            const float *refl, int n_bands);

/**
 * \brief Diagonal MAP regularisation of the full reflectance cube in-place.
 *
 * For each pixel, classifies the surface type, then blends the observed
 * reflectance with the corresponding component prior using diagonal MAP:
 * \f[
 *   r_{MAP} = \frac{r_{obs}/\sigma_{obs}^2 + r_{prior}/\sigma_{prior}^2}
 *                  {1/\sigma_{obs}^2 + 1/\sigma_{prior}^2}
 * \f]
 *
 * Array layout: \c refl_cube[b * npix + p] = reflectance of pixel \c p at band \c b.
 *
 * When \p sigma2 is NULL, \p weight controls the blend:
 * \c weight=0.1 means 90 %% observation + 10 %% prior.
 *
 * Row loops are OpenMP-parallelised over pixels.
 *
 * \param[in]     mdl       Initialised surface model.
 * \param[in,out] refl_cube Reflectance cube float[n_bands × npix], updated in place.
 * \param[in]     sigma2    Per-element observation variance float[n_bands × npix],
 *                          or NULL to use \p weight.
 * \param[in]     n_bands   Number of spectral bands.
 * \param[in]     npix      Number of pixels.
 * \param[in]     weight    Prior weight ∈ (0, 1]; used when \p sigma2 is NULL.
 */
void surface_model_regularize(const SurfaceModelImpl *mdl,
                               float *refl_cube,
                               const float *sigma2,
                               int n_bands, int npix,
                               float weight);

/**
 * \brief Per-band RT model discrepancy (added in quadrature to σ).
 *
 * Returns a baseline forward-model error of 0.5 %% reflectance with small
 * bumps at gas-absorption band edges (O₂-A, CO₂, H₂O, CH₄).
 *
 * Add to the instrument-noise σ before MAP regularisation:
 * \f$ \sigma_{total}^2 = \sigma_{noise}^2 + \sigma_{discr}^2 \f$.
 *
 * \param[in]  wl_um     Band-centre wavelengths [µm], length \p n_wl.
 * \param[in]  n_wl      Number of bands.
 * \param[out] sigma_out Pre-allocated float[n_wl]; model discrepancy σ [reflectance].
 */
void surface_model_discrepancy(const float *wl_um, int n_wl, float *sigma_out);

/**
 * \brief Free a surface model handle.
 *
 * \param[in] mdl Handle to free (NULL is a no-op).
 */
void surface_model_free(SurfaceModelImpl *mdl);

#ifdef __cplusplus
}
#endif
