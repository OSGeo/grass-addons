/**
 * 02_scene_correction.c — Per-pixel scene-scale Lambertian correction.
 *
 * Demonstrates:
 *  - Per-pixel trilinear LUT interpolation from a spatially varying AOD map
 *  - OpenMP parallel pixel loop
 *  - Polarized RT (enable_polar=1) for improved blue-band accuracy
 *  - BRDF-coupled inversion (atcorr_invert_brdf + sixs_brdf_albe)
 *
 * Compile:
 *   gcc -std=c11 -O2 -fopenmp -I../include 02_scene_correction.c \
 *       -L../testsuite -lsixsv -lm -fopenmp -Wl,-rpath,../testsuite -o 02_scene_correction
 */

#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include "atcorr.h"
#include "brdf.h"

int main(void)
{
    /* ── Simulate a small 64×64 scene ───────────────────────────────────── */
    const int nrows = 64, ncols = 64, npix = nrows * ncols;
    const int n_bands = 4;
    float wl[]  = {0.45f, 0.55f, 0.65f, 0.87f};
    float aod[] = {0.0f, 0.1f, 0.2f, 0.3f, 0.5f};
    float h2o[] = {0.5f, 1.5f, 2.5f, 3.5f};

    LutConfig cfg = {
        .wl  = wl,  .n_wl  = n_bands,
        .aod = aod, .n_aod = 5,
        .h2o = h2o, .n_h2o = 4,
        .sza = 32.0f, .vza = 8.0f, .raa = 120.0f,
        .altitude_km   = 1000.0f,
        .atmo_model    = ATMO_US62,
        .aerosol_model = AEROSOL_CONTINENTAL,
        .ozone_du      = 310.0f,
        /* ── Polarized RT: better R_atm in the blue at ~1-5% cost ── */
        .enable_polar  = 1,
    };

    int N = cfg.n_aod * cfg.n_h2o * n_bands;
    float *R_atm  = malloc(N * sizeof(float));
    float *T_down = malloc(N * sizeof(float));
    float *T_up   = malloc(N * sizeof(float));
    float *s_alb  = malloc(N * sizeof(float));
    float *R_atmQ = malloc(N * sizeof(float));   /* Q Stokes */
    float *R_atmU = malloc(N * sizeof(float));   /* U Stokes */

    LutArrays lut = {
        .R_atm  = R_atm,  .T_down = T_down,
        .T_up   = T_up,   .s_alb  = s_alb,
        .T_down_dir = NULL,
        .R_atmQ = R_atmQ, .R_atmU = R_atmU,
    };
    atcorr_compute_lut(&cfg, &lut);

    /* ── Spatially varying AOD and H₂O maps (simulated) ─────────────────── */
    float *aod_map = malloc(npix * sizeof(float));
    float *h2o_map = malloc(npix * sizeof(float));
    for (int i = 0; i < npix; i++) {
        aod_map[i] = 0.05f + 0.3f * (float)(i % ncols) / ncols;
        h2o_map[i] = 1.0f + 2.0f * (float)(i / ncols) / nrows;
    }

    /* ── Per-band multi-pixel correction ─────────────────────────────────── */
    /* Input TOA reflectance: band-major layout [n_bands × npix] */
    float *rho_toa = malloc((size_t)n_bands * npix * sizeof(float));
    float *rho_boa = malloc((size_t)n_bands * npix * sizeof(float));
    for (int b = 0; b < n_bands; b++)
        for (int i = 0; i < npix; i++)
            rho_toa[b * npix + i] = 0.05f + 0.25f * b / n_bands
                                    + 0.02f * sinf(i * 0.1f);

    /* OpenMP parallel over pixels — trilinear lookup per pixel */
    for (int b = 0; b < n_bands; b++) {
        #ifdef _OPENMP
        #pragma omp parallel for schedule(static)
        #endif
        for (int i = 0; i < npix; i++) {
            float Ra, Td, Tu, sa;
            atcorr_lut_interp_pixel(&cfg, &lut,
                                    aod_map[i], h2o_map[i], wl[b],
                                    &Ra, &Td, &Tu, &sa);
            rho_boa[b * npix + i] = atcorr_invert(rho_toa[b * npix + i],
                                                   Ra, Td, Tu, sa);
        }
        float mean_boa = 0.0f;
        for (int i = 0; i < npix; i++) mean_boa += rho_boa[b * npix + i];
        printf("Band %d (%.2f µm): mean BOA = %.4f\n",
               b, wl[b], mean_boa / npix);
    }

    /* ── BRDF-coupled inversion (RPV model, green band example) ─────────── */
    BrdfParams rpv = { .rahman = { .rho0 = 0.12f, .af = -0.15f, .k = 0.75f } };
    float cos_sza = cosf(cfg.sza * 3.14159265f / 180.0f);
    float rho_albe = sixs_brdf_albe(BRDF_RAHMAN, &rpv, cos_sza, 48, 24);

    float Rs[4], Tds[4], Tus[4], ss[4];
    atcorr_lut_slice(&cfg, &lut, 0.15f, 2.0f, Rs, Tds, Tus, ss, NULL);
    /* Green band (index 1) for the BRDF-coupled inversion */
    float rho_brdf = atcorr_invert_brdf(0.18f, Rs[1], Tds[1], Tus[1], ss[1], rho_albe);
    printf("\nRPV BRDF correction: rho_BRDF = %.4f  (white-sky albedo = %.4f)\n",
           rho_brdf, rho_albe);

    free(R_atm); free(T_down); free(T_up); free(s_alb);
    free(R_atmQ); free(R_atmU);
    free(aod_map); free(h2o_map);
    free(rho_toa); free(rho_boa);
    return 0;
}
