/**
 * \file spectral_brdf.c
 * \brief MCD43 disaggregation and Tikhonov spectral smoothing.
 *
 * Implements:
 *   - spectral_interp_linear(): piecewise-linear interpolation with
 *     clamp-extrapolation outside the anchor range.
 *   - spectral_smooth_tikhonov(): O(5n) Cholesky-band solver for the
 *     second-difference Tikhonov regularization system.
 *   - mcd43_disaggregate(): full 7→n_wl disaggregation pipeline.
 *
 * \see include/spectral_brdf.h for the public API.
 */

#include "../include/spectral_brdf.h"

#include <math.h>
#include <string.h>
#include <stdlib.h>

/* ── MODIS MCD43 band centres [µm] ────────────────────────────────────────── */

const float MODIS_WL_UM[7] = {
    0.469f,   /* B3 blue  */
    0.555f,   /* B4 green */
    0.645f,   /* B1 red   */
    0.858f,   /* B2 NIR   */
    1.240f,   /* B5 SWIR  */
    1.640f,   /* B6 SWIR  */
    2.130f    /* B7 SWIR  */
};

/* ── Piecewise-linear interpolation ──────────────────────────────────────── */

/**
 * \brief Piecewise-linear interpolation with clamp extrapolation.
 *
 * Evaluates the piecewise-linear function defined by \c (x_anchor, y_anchor)
 * at each query point in \c x_out.  Points outside the anchor range are
 * clamped to the nearest endpoint value (no extrapolation).
 *
 * \param[in]  x_anchor  Sorted ascending anchor x-values (length \c n_anchor).
 * \param[in]  y_anchor  Anchor y-values (length \c n_anchor).
 * \param[in]  n_anchor  Number of anchor points.
 * \param[in]  x_out     Query x-values (length \c n_out).
 * \param[in]  n_out     Number of query points.
 * \param[out] y_out     Interpolated output values (caller-allocated, length \c n_out).
 */
static void spectral_interp_linear(const float *x_anchor, const float *y_anchor,
                                    int n_anchor,
                                    const float *x_out, int n_out,
                                    float *y_out)
{
    for (int j = 0; j < n_out; j++) {
        float x = x_out[j];

        /* Clamp-extrapolate below / above */
        if (x <= x_anchor[0]) {
            y_out[j] = y_anchor[0];
            continue;
        }
        if (x >= x_anchor[n_anchor - 1]) {
            y_out[j] = y_anchor[n_anchor - 1];
            continue;
        }

        /* Binary search for bracket */
        int lo = 0, hi = n_anchor - 2;
        while (lo < hi) {
            int mid = (lo + hi) / 2;
            if (x_anchor[mid + 1] <= x) lo = mid + 1;
            else                         hi = mid;
        }

        float dx = x_anchor[lo + 1] - x_anchor[lo];
        float t  = (dx > 1e-12f) ? (x - x_anchor[lo]) / dx : 0.0f;
        y_out[j] = y_anchor[lo] * (1.0f - t) + y_anchor[lo + 1] * t;
    }
}

/**
 * \brief Smooth a spectral array in-place using second-difference Tikhonov regularisation.
 *
 * Solves the system \f$(I + \alpha^2 D_2^\top D_2)\,x = f\f$ in-place,
 * where \f$D_2\f$ is the second-difference matrix.
 *
 * \f$D_2^\top D_2\f$ is symmetric positive semi-definite and 5-diagonal;
 * the augmented matrix \f$A = I + \alpha^2 D_2^\top D_2\f$ is symmetric
 * positive-definite with bandwidth 2.  The system is solved via Cholesky
 * band factorisation (\f$A = LL^\top\f$) + forward/back substitution in
 * \f$O(5n)\f$ operations.
 *
 * \param[in,out] f      Spectral array to smooth in-place (length \c n).
 * \param[in]     n      Number of elements.  No-op if \c n < 3.
 * \param[in]     alpha  Regularisation strength.  No-op if ≤ 0.
 *                       Larger values increase spectral smoothness.
 */
void spectral_smooth_tikhonov(float *f, int n, float alpha)
{
    if (n < 3 || alpha <= 0.0f) return;

    float a2 = alpha * alpha;

    /* ── Assemble band A = I + alpha^2 * D2^T D2 ── *
     * Store lower-triangle band: A_main[i], A_sub1[i], A_sub2[i].
     * Use VLAs — maximum n_wl is ~10000, so stack is fine.            */
    float *A0 = (float *)malloc((size_t)n * sizeof(float));
    float *A1 = (float *)malloc((size_t)n * sizeof(float));
    float *A2 = (float *)malloc((size_t)n * sizeof(float));
    if (!A0 || !A1 || !A2) {
        free(A0); free(A1); free(A2);
        return; /* OOM: return unchanged */
    }

    /* Main diagonal of D2^T D2 */
    static const float d2_main_edge0 = 1.0f;
    static const float d2_main_edge1 = 5.0f;
    static const float d2_main_inner = 6.0f;

    for (int i = 0; i < n; i++) {
        float d2_main = (i == 0 || i == n - 1) ? d2_main_edge0
                      : (i == 1 || i == n - 2) ? d2_main_edge1
                      :                           d2_main_inner;
        A0[i] = 1.0f + a2 * d2_main;
    }

    /* ±1 sub-diagonal of D2^T D2 */
    for (int i = 0; i < n - 1; i++) {
        float d2_sub1 = (i == 0 || i == n - 2) ? -2.0f : -4.0f;
        A1[i] = a2 * d2_sub1;   /* A1[i] = A[i+1,i] */
    }
    A1[n - 1] = 0.0f;

    /* ±2 sub-diagonal of D2^T D2 = 1 everywhere */
    for (int i = 0; i < n - 2; i++)
        A2[i] = a2 * 1.0f;
    A2[n - 2] = A2[n - 1] = 0.0f;

    /* ── Cholesky band factorization ── *
     * Overwrites A0,A1,A2 with lower-banded Cholesky factor L. */
    for (int i = 0; i < n; i++) {
        /* Subtract contributions from previous columns */
        if (i >= 1) A0[i] -= A1[i-1] * A1[i-1];
        if (i >= 2) A0[i] -= A2[i-2] * A2[i-2];

        if (A0[i] <= 0.0f) A0[i] = 1e-12f;  /* guard (shouldn't happen for SPD) */
        float inv_d = 1.0f / sqrtf(A0[i]);
        A0[i] = sqrtf(A0[i]);

        if (i + 1 < n) {
            A1[i] -= (i >= 1) ? A2[i-1] * A1[i-1] : 0.0f;
            A1[i] *= inv_d;
        }
        if (i + 2 < n) {
            A2[i] *= inv_d;
        }
    }

    /* ── Forward substitution: L y = f ── */
    for (int i = 0; i < n; i++) {
        if (i >= 1) f[i] -= A1[i-1] * f[i-1];
        if (i >= 2) f[i] -= A2[i-2] * f[i-2];
        f[i] /= A0[i];
    }

    /* ── Back substitution: L^T x = y ── */
    for (int i = n - 1; i >= 0; i--) {
        if (i + 1 < n) f[i] -= A1[i] * f[i+1];
        if (i + 2 < n) f[i] -= A2[i] * f[i+2];
        f[i] /= A0[i];
    }

    free(A0); free(A1); free(A2);
}

/**
 * \brief Disaggregate MCD43 7-band Ross-Li kernel weights to an arbitrary wavelength grid.
 *
 * Interpolates the three Ross-Li BRDF kernel weights (f_iso, f_vol, f_geo)
 * from the seven MODIS MCD43A1 bands to a target wavelength grid using
 * piecewise-linear interpolation followed by optional Tikhonov spectral
 * smoothing.
 *
 * The 7 MODIS band centres are stored in \c MODIS_WL_UM[].
 *
 * \param[in]  fiso_7    f_iso kernel weights at 7 MODIS bands.
 * \param[in]  fvol_7    f_vol kernel weights at 7 MODIS bands.
 * \param[in]  fgeo_7    f_geo kernel weights at 7 MODIS bands.
 * \param[in]  wl_target Target wavelength grid in µm (length \c n_wl).
 * \param[in]  n_wl      Number of target wavelengths.
 * \param[in]  alpha     Tikhonov smoothing strength (0 = no smoothing).
 * \param[out] fiso_wl   Disaggregated f_iso at \c wl_target (caller-allocated, length \c n_wl).
 * \param[out] fvol_wl   Disaggregated f_vol at \c wl_target.
 * \param[out] fgeo_wl   Disaggregated f_geo at \c wl_target.
 */
void mcd43_disaggregate(const float *fiso_7, const float *fvol_7, const float *fgeo_7,
                         const float *wl_target, int n_wl, float alpha,
                         float *fiso_wl, float *fvol_wl, float *fgeo_wl)
{
    /* Interpolate each kernel array from 7 MODIS anchors to n_wl targets */
    spectral_interp_linear(MODIS_WL_UM, fiso_7, 7, wl_target, n_wl, fiso_wl);
    spectral_interp_linear(MODIS_WL_UM, fvol_7, 7, wl_target, n_wl, fvol_wl);
    spectral_interp_linear(MODIS_WL_UM, fgeo_7, 7, wl_target, n_wl, fgeo_wl);

    /* Optional Tikhonov smoothing — applied independently to each kernel */
    if (alpha > 0.0f) {
        spectral_smooth_tikhonov(fiso_wl, n_wl, alpha);
        spectral_smooth_tikhonov(fvol_wl, n_wl, alpha);
        spectral_smooth_tikhonov(fgeo_wl, n_wl, alpha);
    }
}
