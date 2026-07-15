/**
 * \file surface_model.c
 * \brief 3-component surface reflectance prior and MAP regularisation.
 *
 * \see include/surface_model.h for the public API.
 */

#include "surface_model.h"

#define _USE_MATH_DEFINES
#include <math.h>
#include <stdlib.h>
#include <string.h>

#ifdef _OPENMP
#include <omp.h>
#endif

/* ── Reference spectra at 29 key wavelengths (µm) ───────────────────────────── */
/* Values match the Python lib/surface_model.py reference tables. */

#define SM_N_REF 29

static const float REF_WL[SM_N_REF] = {
    0.400f, 0.450f, 0.500f, 0.550f, 0.600f,
    0.650f, 0.680f, 0.700f, 0.720f, 0.750f,
    0.800f, 0.850f, 0.900f, 1.000f, 1.100f,
    1.200f, 1.300f, 1.400f, 1.500f, 1.600f,
    1.700f, 1.800f, 1.900f, 2.000f, 2.100f,
    2.200f, 2.300f, 2.400f, 2.500f
};

/* Component 0: Typical green vegetation */
static const float VEG_REFL[SM_N_REF] = {
    0.030f, 0.040f, 0.050f, 0.080f, 0.050f,
    0.040f, 0.030f, 0.080f, 0.200f, 0.400f,
    0.430f, 0.450f, 0.440f, 0.420f, 0.400f,
    0.380f, 0.350f, 0.100f, 0.300f, 0.280f,
    0.250f, 0.100f, 0.050f, 0.200f, 0.220f,
    0.180f, 0.120f, 0.080f, 0.050f
};

/* Component 1: Bare soil / mixed bare surfaces */
static const float SOIL_REFL[SM_N_REF] = {
    0.040f, 0.050f, 0.070f, 0.100f, 0.130f,
    0.160f, 0.180f, 0.190f, 0.200f, 0.210f,
    0.220f, 0.240f, 0.250f, 0.270f, 0.280f,
    0.300f, 0.310f, 0.150f, 0.300f, 0.320f,
    0.330f, 0.150f, 0.100f, 0.300f, 0.310f,
    0.280f, 0.220f, 0.180f, 0.150f
};

/* Component 2: Water / wet surfaces */
static const float WATER_REFL[SM_N_REF] = {
    0.050f, 0.060f, 0.060f, 0.050f, 0.040f,
    0.030f, 0.030f, 0.020f, 0.020f, 0.020f,
    0.010f, 0.010f, 0.010f, 0.010f, 0.005f,
    0.005f, 0.003f, 0.002f, 0.002f, 0.001f,
    0.001f, 0.001f, 0.001f, 0.001f, 0.001f,
    0.001f, 0.001f, 0.001f, 0.001f
};

/* Per-component variance scale: σ = scale × mean (floor 1e-3).
 * Larger scale = weaker prior constraint. */
static const float VAR_SCALE[SM_N_COMPONENTS] = { 0.15f, 0.20f, 0.03f };

static const float *REFL_TABLE[SM_N_COMPONENTS] = {
    VEG_REFL, SOIL_REFL, WATER_REFL
};

/* ── Internal struct ─────────────────────────────────────────────────────────── */

struct SurfaceModelImpl_ {
    int    n_bands;
    float *means;       /* [SM_N_COMPONENTS × n_bands], row-major */
    float *variances;   /* [SM_N_COMPONENTS × n_bands], row-major */
    int   *vnir_mask;   /* [n_bands]: 1 if 0.40 ≤ wl ≤ 1.00 µm */
};

/* ── Helpers ─────────────────────────────────────────────────────────────────── */

/**
 * \brief Linear interpolation of a 1-D tabulated function with clamp extrapolation.
 * \param[in] xp Sorted ascending x-values (length \c n).
 * \param[in] yp Corresponding y-values.
 * \param[in] n  Table length.
 * \param[in] x  Query x value.
 * \return Interpolated (or clamped) y value.
 */
static float interp1(const float *xp, const float *yp, int n, float x)
{
    if (x <= xp[0])      return yp[0];
    if (x >= xp[n - 1])  return yp[n - 1];
    for (int i = 0; i < n - 1; i++) {
        if (xp[i + 1] >= x) {
            float t = (x - xp[i]) / (xp[i + 1] - xp[i]);
            return yp[i] + t * (yp[i + 1] - yp[i]);
        }
    }
    return yp[n - 1];
}

/**
 * \brief Allocate and initialise a surface model for a given wavelength grid.
 *
 * Interpolates the three built-in reference spectra (vegetation, soil, water)
 * to the caller's wavelength grid and stores them inside the returned object.
 *
 * \param[in] wl_um   Target wavelength grid in µm (length \c n_bands).
 * \param[in] n_bands Number of bands.
 * \return Pointer to the new \c SurfaceModelImpl, or NULL on allocation failure.
 *         Free with surface_model_free().
 */
SurfaceModelImpl *surface_model_alloc(const float *wl_um, int n_bands)
{
    SurfaceModelImpl *mdl = calloc(1, sizeof(*mdl));
    if (!mdl) return NULL;

    mdl->n_bands   = n_bands;
    mdl->means     = malloc((size_t)SM_N_COMPONENTS * n_bands * sizeof(float));
    mdl->variances = malloc((size_t)SM_N_COMPONENTS * n_bands * sizeof(float));
    mdl->vnir_mask = malloc((size_t)n_bands * sizeof(int));

    if (!mdl->means || !mdl->variances || !mdl->vnir_mask) {
        surface_model_free(mdl);
        return NULL;
    }

    for (int c = 0; c < SM_N_COMPONENTS; c++) {
        for (int b = 0; b < n_bands; b++) {
            float mean = interp1(REF_WL, REFL_TABLE[c], SM_N_REF, wl_um[b]);
            float sd   = VAR_SCALE[c] * mean;
            if (sd < 1e-3f) sd = 1e-3f;
            mdl->means    [c * n_bands + b] = mean;
            mdl->variances[c * n_bands + b] = sd * sd;   /* store σ² */
        }
    }

    for (int b = 0; b < n_bands; b++)
        mdl->vnir_mask[b] = (wl_um[b] >= 0.400f && wl_um[b] <= 1.000f);

    return mdl;
}

/**
 * \brief Classify a reflectance spectrum into one of three surface types.
 *
 * Returns the index (0=vegetation, 1=soil, 2=water) of the built-in
 * reference spectrum closest in least-squares sense to \c refl.
 *
 * \param[in] mdl     Surface model allocated by surface_model_alloc().
 * \param[in] refl    Reflectance spectrum [n_bands].
 * \param[in] n_bands Number of bands (must match the model).
 * \return 0, 1, or 2 (vegetation / soil / water).
 */
int surface_model_classify(const SurfaceModelImpl *mdl,
                            const float *refl, int n_bands)
{
    int   best_comp = 1;    /* default: soil */
    float best_dist = 1e30f;

    for (int c = 0; c < SM_N_COMPONENTS; c++) {
        const float *ref = mdl->means + c * n_bands;
        float dist = 0.0f;
        int   n    = 0;
        for (int b = 0; b < n_bands; b++) {
            if (!mdl->vnir_mask[b]) continue;
            if (!isfinite(refl[b]))  continue;
            float d = refl[b] - ref[b];
            dist += d * d;
            n++;
        }
        if (n > 0 && dist < best_dist) {
            best_dist = dist;
            best_comp = c;
        }
    }
    return best_comp;
}

/**
 * \brief Apply diagonal MAP regularisation using the surface spectral prior.
 *
 * For each pixel, blends the retrieved reflectance spectrum toward the
 * nearest reference spectrum (vegetation / soil / water) using a diagonal
 * maximum a posteriori update:
 * \f[
 *   \rho_b^\text{MAP} = \frac{\sigma_\text{prior}^2 \rho_b + \sigma_b^2 \mu_b}
 *                            {\sigma_\text{prior}^2 + \sigma_b^2}
 * \f]
 * where \f$\sigma_b^2\f$ is the per-pixel per-band measurement variance from
 * \c sigma2, and \f$\mu_b\f$ is the prior mean from the classified reference.
 *
 * \param[in]     mdl        Surface model with reference spectra.
 * \param[in,out] refl_cube  Reflectance cube [n_bands × npix] (modified in place).
 * \param[in]     sigma2     Measurement variance cube [n_bands × npix], or NULL
 *                           (uses \c weight as a uniform variance scale).
 * \param[in]     n_bands    Number of spectral bands.
 * \param[in]     npix       Number of pixels.
 * \param[in]     weight     Prior weight relative to measurement uncertainty.
 */
void surface_model_regularize(const SurfaceModelImpl *mdl,
                               float *refl_cube,
                               const float *sigma2,
                               int n_bands, int npix,
                               float weight)
{
    /* Stack buffer limit — sufficient for Tanager (426 bands) and beyond. */
#define SM_MAX_BANDS 2048
    if (n_bands > SM_MAX_BANDS) n_bands = SM_MAX_BANDS;

#ifdef _OPENMP
#pragma omp parallel for schedule(dynamic, 64)
#endif
    for (int p = 0; p < npix; p++) {
        /* Copy pixel spectrum into a contiguous local buffer. */
        float tmp[SM_MAX_BANDS];
        for (int b = 0; b < n_bands; b++)
            tmp[b] = refl_cube[(size_t)b * npix + p];

        /* Classify to nearest component using VNIR bands. */
        int comp = surface_model_classify(mdl, tmp, n_bands);

        const float *xa = mdl->means     + comp * mdl->n_bands;
        const float *sa = mdl->variances + comp * mdl->n_bands;

        /* MAP blend per band (diagonal covariance). */
        for (int b = 0; b < n_bands; b++) {
            float r = tmp[b];
            if (!isfinite(r)) continue;

            float inv_so;
            if (sigma2 != NULL) {
                float s2 = sigma2[(size_t)b * npix + p];
                inv_so = (isfinite(s2) && s2 > 1e-20f) ? 1.0f / s2 : 1e20f;
            } else {
                /* Effective obs variance from weight parameter */
                float sa_b   = sa[b] > 1e-20f ? sa[b] : 1e-20f;
                float s2_obs = sa_b * (1.0f - weight)
                               / (weight > 1e-10f ? weight : 1e-10f);
                inv_so = 1.0f / (s2_obs > 1e-20f ? s2_obs : 1e-20f);
            }
            float inv_sa = 1.0f / (sa[b] > 1e-20f ? sa[b] : 1e-20f);

            refl_cube[(size_t)b * npix + p] =
                (r * inv_so + xa[b] * inv_sa) / (inv_so + inv_sa);
        }
    }
#undef SM_MAX_BANDS
}

/* ── Model discrepancy ──────────────────────────────────────────────────────── */

/**
 * \brief Compute the per-band surface model discrepancy (empirical RT error floor).
 *
 * Returns a per-band uncertainty floor derived from the expected mismatch
 * between the simplified 3-component prior and actual surface spectra.
 * The values are calibrated to match the Python \c lib/uncertainty.py reference.
 *
 * \param[in]  wl_um     Wavelength grid in µm (length \c n_wl).
 * \param[in]  n_wl      Number of bands.
 * \param[out] sigma_out Per-band standard deviation of model discrepancy [n_wl].
 */
void surface_model_discrepancy(const float *wl_um, int n_wl, float *sigma_out)
{
    /* Empirical RT error floor — matches Python lib/uncertainty.py */
    static const float centers[6] = {
        0.720f, 0.760f, 0.940f, 1.135f, 1.380f, 1.850f
    };

    for (int i = 0; i < n_wl; i++) {
        float s = 0.005f;   /* baseline 0.5 % */
        for (int k = 0; k < 6; k++) {
            float dw = (wl_um[i] - centers[k]) / 0.030f;
            s += 0.02f * expf(-0.5f * dw * dw);
        }
        if (wl_um[i] > 1.5f) s += 0.01f;
        sigma_out[i] = s;
    }
}

/**
 * \brief Free a surface model allocated by surface_model_alloc().
 * \param[in] mdl Surface model to free.  No-op if NULL.
 */
void surface_model_free(SurfaceModelImpl *mdl)
{
    if (!mdl) return;
    free(mdl->means);
    free(mdl->variances);
    free(mdl->vnir_mask);
    free(mdl);
}
