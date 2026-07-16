/**
 * \file spatial.c
 * \brief Separable Gaussian and box filter implementation.
 *
 * Both filters use a two-pass (horizontal then vertical) strategy.  The pixel
 * loops are offloaded to the GPU via OpenMP target when a device is available;
 * the intermediate buffer \c tmp is kept on the device between passes using
 * \c map(alloc:) to avoid a redundant host↔device round-trip.  Without an
 * offload-capable compiler or device the directives fall back transparently to
 * host execution.
 *
 * \see include/spatial.h for the public API.
 */

#include "spatial.h"

#define _USE_MATH_DEFINES
#include <math.h>
#include <stdlib.h>
#include <string.h>

#ifdef _OPENMP
#include <omp.h>
#endif

/**
 * \brief Apply a separable box (mean) filter to a 2-D float array.
 *
 * Filters in two 1-D passes (horizontal then vertical) using a symmetric
 * window of half-width \c filter_half pixels.  Boundary pixels are handled
 * by clamping to the nearest edge value.  NaN inputs are excluded from the
 * running average; if all neighbours are NaN the input value is copied as-is.
 *
 * \param[in]  data         Input raster, row-major, size nrows × ncols.
 * \param[out] out          Output raster (same dimensions); must not alias \c data.
 * \param[in]  nrows        Number of rows.
 * \param[in]  ncols        Number of columns.
 * \param[in]  filter_half  Half-width of the box window in pixels.
 *                          If < 1, \c data is copied to \c out unchanged.
 */
void spatial_box_filter(const float *data, float *out,
                        int nrows, int ncols, int filter_half)
{
    if (filter_half < 1) {
        memcpy(out, data, (size_t)nrows * ncols * sizeof(float));
        return;
    }

    size_t N   = (size_t)nrows * ncols;
    float *tmp = malloc(N * sizeof(float));
    if (!tmp) return;

    /* Two-pass separable filter.
     * With OpenMP target: data and out are mapped once; tmp stays on the
     * device between the two passes (map(alloc:) — no host copy needed). */
#ifdef _OPENMP
#pragma omp target data map(to: data[0:N]) map(from: out[0:N]) map(alloc: tmp[0:N])
#endif
    {
        /* ── Horizontal pass: data → tmp ── */
#ifdef _OPENMP
#pragma omp target teams distribute parallel for collapse(2)
#endif
        for (int r = 0; r < nrows; r++) {
            for (int c = 0; c < ncols; c++) {
                double sum = 0.0;
                int    n   = 0;
                for (int k = -filter_half; k <= filter_half; k++) {
                    int cc = c + k;
                    if (cc < 0)      cc = 0;
                    if (cc >= ncols) cc = ncols - 1;
                    float v = data[r * ncols + cc];
                    if (!isnan(v)) { sum += v; n++; }
                }
                tmp[r * ncols + c] = (n > 0)
                    ? (float)(sum / n)
                    : data[r * ncols + c];
            }
        }

        /* ── Vertical pass: tmp → out ── */
#ifdef _OPENMP
#pragma omp target teams distribute parallel for collapse(2)
#endif
        for (int r = 0; r < nrows; r++) {
            for (int c = 0; c < ncols; c++) {
                double sum = 0.0;
                int    n   = 0;
                for (int k = -filter_half; k <= filter_half; k++) {
                    int rr = r + k;
                    if (rr < 0)      rr = 0;
                    if (rr >= nrows) rr = nrows - 1;
                    float v = tmp[rr * ncols + c];
                    if (!isnan(v)) { sum += v; n++; }
                }
                out[r * ncols + c] = (n > 0)
                    ? (float)(sum / n)
                    : tmp[r * ncols + c];
            }
        }
    }

    free(tmp);
}

/**
 * \brief Apply a separable Gaussian filter to a 2-D float array in-place.
 *
 * Convolves the raster with a 1-D Gaussian kernel of standard deviation
 * \c sigma pixels in two passes (rows then columns).  The kernel radius is
 * clamped at 3σ.  NaN pixels are excluded from each kernel evaluation; if
 * all contributing pixels are NaN the output is set to 0.
 *
 * \param[in,out] data    Raster to filter in-place, row-major, size nrows × ncols.
 * \param[in]     nrows   Number of rows.
 * \param[in]     ncols   Number of columns.
 * \param[in]     sigma   Gaussian standard deviation in pixels.  No-op if ≤ 0.
 */
void spatial_gaussian_filter(float *data, int nrows, int ncols, float sigma)
{
    if (sigma <= 0.0f) return;

    int radius = (int)(3.0f * sigma + 0.5f);
    if (radius < 1) radius = 1;
    int ksize = 2 * radius + 1;

    float *kernel = malloc(ksize * sizeof(float));
    if (!kernel) return;

    /* Build normalised Gaussian kernel */
    float ksum = 0.0f;
    for (int k = -radius; k <= radius; k++) {
        float v = expf(-0.5f * (float)(k * k) / (sigma * sigma));
        kernel[k + radius] = v;
        ksum += v;
    }
    for (int k = 0; k < ksize; k++) kernel[k] /= ksum;

    size_t N   = (size_t)nrows * ncols;
    float *tmp = malloc(N * sizeof(float));
    if (!tmp) { free(kernel); return; }

    /* Two-pass separable filter.
     * data is mapped tofrom (modified in-place); kernel is read-only (to);
     * tmp stays on the device between passes (alloc). */
#ifdef _OPENMP
#pragma omp target data map(tofrom: data[0:N]) map(to: kernel[0:ksize]) map(alloc: tmp[0:N])
#endif
    {
        /* ── Horizontal pass: data → tmp ── */
#ifdef _OPENMP
#pragma omp target teams distribute parallel for collapse(2)
#endif
        for (int r = 0; r < nrows; r++) {
            for (int c = 0; c < ncols; c++) {
                float val = 0.0f, w = 0.0f;
                for (int k = -radius; k <= radius; k++) {
                    int cc = c + k;
                    if (cc < 0)      cc = 0;
                    if (cc >= ncols) cc = ncols - 1;
                    float v = data[r * ncols + cc];
                    if (!isnan(v)) {
                        float kw = kernel[k + radius];
                        val += kw * v;
                        w   += kw;
                    }
                }
                tmp[r * ncols + c] = (w > 1e-6f) ? val / w : data[r * ncols + c];
            }
        }

        /* ── Vertical pass: tmp → data (in-place result) ── */
#ifdef _OPENMP
#pragma omp target teams distribute parallel for collapse(2)
#endif
        for (int r = 0; r < nrows; r++) {
            for (int c = 0; c < ncols; c++) {
                float val = 0.0f, w = 0.0f;
                for (int k = -radius; k <= radius; k++) {
                    int rr = r + k;
                    if (rr < 0)      rr = 0;
                    if (rr >= nrows) rr = nrows - 1;
                    float v = tmp[rr * ncols + c];
                    if (!isnan(v)) {
                        float kw = kernel[k + radius];
                        val += kw * v;
                        w   += kw;
                    }
                }
                data[r * ncols + c] = (w > 1e-6f) ? val / w : tmp[r * ncols + c];
            }
        }
    }

    free(tmp);
    free(kernel);
}
