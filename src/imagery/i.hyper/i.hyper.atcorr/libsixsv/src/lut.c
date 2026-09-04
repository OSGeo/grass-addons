/**
 * \file lut.c
 * \brief 3-D LUT engine: [AOD × H₂O × λ] grid computation and interpolation.
 *
 * Calls sixs_discom() once per AOD grid point (H₂O only affects gas
 * absorption, not scattering, so DISCOM only needs to run n_aod times).
 * Gas transmittance is applied per (H₂O, λ) inside the AOD loop.
 * The outer loop is OpenMP-parallelised over AOD; each thread owns a
 * private ::SixsCtx.
 *
 * Public functions (declared in include/atcorr.h):
 *   - atcorr_compute_lut()       — full LUT build
 *   - atcorr_lut_slice()         — bilinear (AOD, H₂O) interpolation → n_wl
 * arrays
 *   - atcorr_lut_interp_pixel()  — trilinear (AOD, H₂O, λ) → single pixel
 */
#include "../include/sixs_ctx.h"
#include "../include/atcorr.h"
#include "interp.h"
#define _USE_MATH_DEFINES
#include <math.h>
#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif
#include <string.h>
#include <stdlib.h>
#include "../include/brdf.h"

/* Forward declarations for functions implemented elsewhere */
void sixs_init_atmosphere(SixsCtx *ctx, int atmo_model);
int sixs_pressure_checked(SixsCtx *ctx, float sp);
int sixs_presplane(SixsCtx *ctx, float height_km);
void sixs_aerosol_init(SixsCtx *ctx, int iaer, float taer55, float xmud);
void sixs_mie_init(SixsCtx *ctx, double r_mode, double sigma_g, double m_r_550,
                   double m_i_550);
void sixs_discom(SixsCtx *ctx, int idatmp, int iaer, float xmus, float xmuv,
                 float phi, float taer55, float taer55p, float palt,
                 float phirad, int nt, int mu, int np, float ftray, int ipol);
void sixs_interp_polar_components(const SixsCtx *ctx, float wl,
                                  float *roatmq_out, float *roatmu_out,
                                  float *roraylq_out, float *roraylu_out);
float sixs_gas_transmittance(const SixsCtx *ctx, float wl, float xmus,
                             float xmuv, float uw, float uo3);
void sixs_gas_profile_columns(const SixsCtx *ctx, float *h2o, float *ozone_du);
float sixs_gas_transmittance_total(const SixsCtx *ctx, int observer_mode,
                                   float wl, float xmus, float xmuv, float uw,
                                   float uo3);

/**
 * \brief Compute the 3-D atmospheric correction LUT.
 *
 * Runs the 6SV2.1 radiative transfer solver for each AOD grid point in
 * \c cfg->aod[], then applies gas transmittance for each H₂O grid point
 * and each wavelength in \c cfg->wl[], filling \c out with:
 *
 * | Array       | Index order (C, last varies fastest)       |
 * |-------------|---------------------------------------------|
 * | R_atm       | [n_aod][n_h2o][n_wl]                       |
 * | T_down      | [n_aod][n_h2o][n_wl]                       |
 * | T_up        | [n_aod][n_h2o][n_wl]                       |
 * | s_alb       | [n_aod][n_h2o][n_wl]                       |
 * | T_down_dir  | [n_aod][n_h2o][n_wl] (optional, may be NULL) |
 *
 * The outer AOD loop is parallelised with OpenMP; each thread owns a
 * private ::SixsCtx to avoid races.
 *
 * \param[in]  cfg  LUT configuration (geometry, atmosphere, aerosol, grid
 * dimensions).
 * \param[out] out  LUT arrays; allocates all sub-arrays internally.
 * \return  0 on success, a negative status on invalid input or computation
 * failure.
 */
int atcorr_compute_lut(const LutConfig *cfg, LutArrays *out)
{
    if (!cfg || !out || !cfg->wl || !cfg->aod || !cfg->h2o || cfg->n_wl <= 0 ||
        cfg->n_aod <= 0 || cfg->n_h2o <= 0)
        return -1;
    if (cfg->atmo_model < ATMO_US62 || cfg->atmo_model > ATMO_SUBWIN)
        return -5;
    if (!isfinite(cfg->surface_pressure) || cfg->surface_pressure < 0.0f)
        return -5;
    if (cfg->aerosol_model == AEROSOL_CUSTOM) {
        if (cfg->enable_polar)
            return -4;
        if (cfg->mie_r_mode <= 0.0f || cfg->mie_sigma_g <= 1.0f)
            return -3;
    }

    int n_wl = cfg->n_wl;
    int n_aod = cfg->n_aod;
    int n_h2o = cfg->n_h2o;
    size_t n = (size_t)n_aod * n_h2o * n_wl;

    if (!out->R_atm || !out->T_down || !out->T_up || !out->s_alb)
        return -1;

    /* Initialize output arrays */
    memset(out->R_atm, 0, n * sizeof(float));
    memset(out->s_alb, 0, n * sizeof(float));
    for (size_t i = 0; i < n; i++) {
        out->T_down[i] = 1.0f;
        out->T_up[i] = 1.0f;
    }
    if (out->T_down_dir)
        for (size_t i = 0; i < n; i++)
            out->T_down_dir[i] = 1.0f;
    if (out->R_atmQ)
        memset(out->R_atmQ, 0, n * sizeof(float));
    if (out->R_atmU)
        memset(out->R_atmU, 0, n * sizeof(float));

    /* Geometry */
    float xmus = cosf(cfg->sza * (float)M_PI / 180.0f);
    float xmuv = cosf(cfg->vza * (float)M_PI / 180.0f);
    float phirad = cfg->raa * (float)M_PI / 180.0f;
    float phi = cfg->raa;
    float xmud = -xmus * xmuv - sqrtf(1.0f - xmus * xmus) *
                                    sqrtf(1.0f - xmuv * xmuv) *
                                    cosf(phirad); /* cos(scattering angle) */

    /* 6SV internal parameters */
    int nt = NT_P;                        /* 30 atmospheric layers */
    int mu = MU_P;                        /* 25 Gauss points per hemisphere */
    int np = 1;                           /* one azimuth plane */
    int ipol = cfg->enable_polar ? 1 : 0; /* 0=scalar, 1=Stokes(I,Q,U) */
    int idatmp = (cfg->altitude_km >= 100.0f) ? 4 : /* satellite */
                     (cfg->altitude_km > 0.0f) ? 2
                                               : 0; /* plane or ground */
    float palt = (cfg->altitude_km >= 100.0f) ? 1000.0f : cfg->altitude_km;
    int failed = 0;

    /* ===== Outer loop: AOD ===== */
#ifdef _OPENMP
#pragma omp parallel for schedule(dynamic, 1)
#endif
    for (int ia = 0; ia < n_aod; ia++) {
        /* Each thread needs its own context for thread safety */
        SixsCtx *ctx = (SixsCtx *)calloc(1, sizeof(SixsCtx));
        if (!ctx) {
#ifdef _OPENMP
#pragma omp atomic write
#endif
            failed = 1;
            continue;
        }

        float aod = cfg->aod[ia];

        /* Initialize atmosphere and aerosol */
        ctx->quad.nquad = NQ_P; /* 83 Gauss points */
        ctx->multi.igmax = 20;
        ctx->err.ier = false;
        sixs_init_atmosphere(ctx, cfg->atmo_model);
        if (cfg->surface_pressure > 0.0f &&
            sixs_pressure_checked(ctx, cfg->surface_pressure) != 0) {
#ifdef _OPENMP
#pragma omp atomic write
#endif
            failed = 1;
            free(ctx);
            continue;
        }
        if (idatmp == 2 && sixs_presplane(ctx, palt) != 0) {
#ifdef _OPENMP
#pragma omp atomic write
#endif
            failed = 1;
            free(ctx);
            continue;
        }
        float default_h2o, default_ozone;
        sixs_gas_profile_columns(ctx, &default_h2o, &default_ozone);
        if (ctx->fixed_us62_column_reference) {
            default_h2o = 1.424f;
            default_ozone = 344.0f;
        }

        /* Custom Mie: populate ctx->aer before aerosol_init */
        if (cfg->aerosol_model == AEROSOL_CUSTOM && cfg->mie_r_mode > 0.0f &&
            cfg->mie_sigma_g > 1.0f) {
            sixs_mie_init(ctx, (double)cfg->mie_r_mode,
                          (double)cfg->mie_sigma_g, (double)cfg->mie_m_real,
                          (double)cfg->mie_m_imag);
        }

        sixs_aerosol_init(ctx, cfg->aerosol_model, aod, xmud);

        /* Call DISCOM once per AOD: fills ctx->disc at 20 reference wavelengths
         */
        /* Optical depth between target and sensor: the full column for a
         * satellite and zero for the current ground/aircraft approximation. */
        float ftray =
            idatmp == 4 ? 1.0f : (idatmp == 2 ? ctx->plane_ftray : 0.0f);
        float taer55p =
            idatmp == 4
                ? aod
                : (idatmp == 2 ? aod * (1.0f - expf(-palt / 2.0f)) : 0.0f);
        sixs_discom(ctx, idatmp, cfg->aerosol_model, xmus, xmuv, phi, aod,
                    taer55p, palt, phirad, nt, mu, np, ftray, ipol);

        if (ctx->err.ier) {
#ifdef _OPENMP
#pragma omp atomic write
#endif
            failed = 1;
            free(ctx);
            continue;
        }

        /* ===== Inner loop: H2O ===== */
        for (int ih = 0; ih < n_h2o; ih++) {
            float h2o = cfg->h2o[ih];
            float h2o_column = h2o > 0.0f ? h2o : default_h2o;
            float ozone_column =
                cfg->ozone_du > 0.0f ? cfg->ozone_du : default_ozone;

            /* ===== Innermost loop: wavelength ===== */
            for (int iw = 0; iw < n_wl; iw++) {
                float wl = cfg->wl[iw];
                size_t idx = ((size_t)ia * n_h2o + ih) * n_wl + iw;

                /* Scattering quantities (no H2O dependence) via interpolation
                 */
                float roatm, rorayl, T_down_sca, T_up_sca, s_alb;
                float T_down_dir_sca = 1.0f;
                sixs_interp_components(
                    ctx, cfg->aerosol_model, wl, aod, taer55p, &roatm, &rorayl,
                    &T_down_sca, &T_up_sca, &s_alb, NULL, NULL,
                    out->T_down_dir ? &T_down_dir_sca : NULL);

                /* Gas transmittance (H2O-dependent): separate solar/view paths
                 */
                float T_gas_down = sixs_gas_transmittance(
                    ctx, wl, xmus, xmuv, h2o_column, ozone_column);
                float T_gas_total = sixs_gas_transmittance_total(
                    ctx, idatmp, wl, xmus, xmuv, h2o_column, ozone_column);
                float tgp1 = sixs_gas_transmittance_total(
                    ctx, idatmp, wl, xmus, xmuv, 0.0f, ozone_column);
                float tgp2 = sixs_gas_transmittance_total(
                    ctx, idatmp, wl, xmus, xmuv, 0.5f * h2o_column,
                    ozone_column);

                /* Combined transmittances */
                out->R_atm[idx] = (roatm - rorayl) * tgp2 + rorayl * tgp1;
                out->T_down[idx] = T_down_sca * T_gas_down;
                out->T_up[idx] =
                    T_up_sca * T_gas_total / fmaxf(T_gas_down, 1e-20f);
                out->s_alb[idx] = s_alb;
                if (out->T_down_dir)
                    out->T_down_dir[idx] = T_down_dir_sca * T_gas_down;

                /* Polarized atmospheric path, with the same gas weighting as I.
                 */
                if (cfg->enable_polar) {
                    float roatmq = 0.0f, roatmu = 0.0f;
                    float roraylq = 0.0f, roraylu = 0.0f;
                    sixs_interp_polar_components(ctx, wl, &roatmq, &roatmu,
                                                 &roraylq, &roraylu);
                    if (out->R_atmQ)
                        out->R_atmQ[idx] =
                            (roatmq - roraylq) * tgp2 + roraylq * tgp1;
                    if (out->R_atmU)
                        out->R_atmU[idx] =
                            (roatmu - roraylu) * tgp2 + roraylu * tgp1;
                }
            }
        }

        free(ctx);
    }

    return failed ? -2 : 0;
}

/* ── Per-pixel trilinear LUT interpolation ───────────────────────────────────
 *
 * Returns R_atm, T_down, T_up, s_alb for a single (aod, h2o, wl) point via
 * trilinear interpolation in the 3-D LUT.  Values are clamped to the grid
 * boundaries; no extrapolation.
 *
 * Used by uncertainty.c (AOD perturbation) and main.c (per-pixel correction
 * with per-pixel AOD/H2O raster maps).
 * ────────────────────────────────────────────────────────────────────────────
 */

/**
 * \brief Binary search: find the largest index \c i such that arr[i] <= val.
 *
 * Returns 0 if val < arr[0], and n-2 if val >= arr[n-1] (so the caller
 * can safely interpolate between arr[i] and arr[i+1]).
 *
 * \param[in] arr Sorted ascending array.
 * \param[in] n   Array length (must be >= 2).
 * \param[in] val Query value.
 * \return Lower bracket index in [0, n-2].
 */
static int find_bracket(const float *arr, int n, float val)
{
    if (val <= arr[0])
        return 0;
    if (val >= arr[n - 1])
        return n - 2;
    int lo = 0, hi = n - 1;
    while (hi - lo > 1) {
        int mid = (lo + hi) / 2;
        if (arr[mid] <= val)
            lo = mid;
        else
            hi = mid;
    }
    return lo;
}

/**
 * \brief Trilinearly interpolate the LUT at a single (AOD, H₂O, λ) point.
 *
 * Performs tri-linear interpolation in the [AOD × H₂O × λ] LUT grid and
 * returns the four correction parameters for one pixel.
 *
 * \param[in]  cfg        LUT configuration (grid axes).
 * \param[in]  lut        Precomputed LUT arrays.
 * \param[in]  aod_val    AOD at 550 nm for this pixel.
 * \param[in]  h2o_val    Column water vapour (g cm⁻²) for this pixel.
 * \param[in]  wl_um      Wavelength in µm.
 * \param[out] R_atm_out  Atmospheric path reflectance.
 * \param[out] T_down_out Downward transmittance (direct + diffuse).
 * \param[out] T_up_out   Upward transmittance (direct + diffuse).
 * \param[out] s_alb_out  Spherical albedo of the atmosphere.
 */
void atcorr_lut_interp_pixel(const LutConfig *cfg, const LutArrays *lut,
                             float aod_val, float h2o_val, float wl_um,
                             float *R_atm_out, float *T_down_out,
                             float *T_up_out, float *s_alb_out)
{
    int n_aod = cfg->n_aod;
    int n_h2o = cfg->n_h2o;
    int n_wl = cfg->n_wl;

    /* Clamp to grid */
    if (aod_val < cfg->aod[0])
        aod_val = cfg->aod[0];
    if (aod_val > cfg->aod[n_aod - 1])
        aod_val = cfg->aod[n_aod - 1];
    if (h2o_val < cfg->h2o[0])
        h2o_val = cfg->h2o[0];
    if (h2o_val > cfg->h2o[n_h2o - 1])
        h2o_val = cfg->h2o[n_h2o - 1];
    if (wl_um < cfg->wl[0])
        wl_um = cfg->wl[0];
    if (wl_um > cfg->wl[n_wl - 1])
        wl_um = cfg->wl[n_wl - 1];

    int ia = find_bracket(cfg->aod, n_aod, aod_val);
    int ih = find_bracket(cfg->h2o, n_h2o, h2o_val);
    int iw = find_bracket(cfg->wl, n_wl, wl_um);

    /* Fractional weights — guard against zero-width intervals */
    float dA = cfg->aod[ia + 1] - cfg->aod[ia];
    float dH = cfg->h2o[ih + 1] - cfg->h2o[ih];
    float dW = cfg->wl[iw + 1] - cfg->wl[iw];

    float wa1 = (dA > 0.0f) ? (aod_val - cfg->aod[ia]) / dA : 0.0f;
    float wh1 = (dH > 0.0f) ? (h2o_val - cfg->h2o[ih]) / dH : 0.0f;
    float ww1 = (dW > 0.0f) ? (wl_um - cfg->wl[iw]) / dW : 0.0f;
    float wa0 = 1.0f - wa1;
    float wh0 = 1.0f - wh1;
    float ww0 = 1.0f - ww1;

/* Flat index into the [n_aod × n_h2o × n_wl] C-order array */
#define IDX(a, h, w) (((size_t)(a) * n_h2o + (h)) * n_wl + (w))

/* Trilinear interpolation of an array at the 8 surrounding grid corners */
#define TRILIN(arr)                                         \
    (wa0 * (wh0 * (ww0 * (arr)[IDX(ia, ih, iw)] +           \
                   ww1 * (arr)[IDX(ia, ih, iw + 1)]) +      \
            wh1 * (ww0 * (arr)[IDX(ia, ih + 1, iw)] +       \
                   ww1 * (arr)[IDX(ia, ih + 1, iw + 1)])) + \
     wa1 * (wh0 * (ww0 * (arr)[IDX(ia + 1, ih, iw)] +       \
                   ww1 * (arr)[IDX(ia + 1, ih, iw + 1)]) +  \
            wh1 * (ww0 * (arr)[IDX(ia + 1, ih + 1, iw)] +   \
                   ww1 * (arr)[IDX(ia + 1, ih + 1, iw + 1)])))

    *R_atm_out = TRILIN(lut->R_atm);
    *T_down_out = TRILIN(lut->T_down);
    *T_up_out = TRILIN(lut->T_up);
    *s_alb_out = TRILIN(lut->s_alb);

#undef IDX
#undef TRILIN
}
