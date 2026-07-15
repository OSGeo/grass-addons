/**
 * 03_retrievals.c — Atmospheric state retrievals.
 *
 * Demonstrates:
 *  - Solar position (sixs_possol)
 *  - Surface pressure from elevation (ISA)
 *  - H₂O column from 940 nm band depth (Kaufman & Gao 1992)
 *  - AOD from MODIS DDV + MAIAC patch-median smoothing
 *  - O₃ from Chappuis 600 nm band depth
 *  - Cloud/shadow/water/snow quality bitmask
 *  - Joint AOD + H₂O optimal estimation (ISOFIT-inspired)
 *
 * Compile:
 *   gcc -std=c11 -O2 -fopenmp -I../include 03_retrievals.c \
 *       -L../testsuite -lsixsv -lm -fopenmp -Wl,-rpath,../testsuite -o 03_retrievals
 */

#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <math.h>
#include <string.h>
#include "atcorr.h"
#include "retrieve.h"
#include "oe_invert.h"

/* Synthetic band data helpers */
static void fill_band(float *b, int n, float base, float noise) {
    for (int i = 0; i < n; i++)
        b[i] = base + noise * sinf(i * 0.37f);
}

int main(void)
{
    const int nrows = 32, ncols = 32, npix = nrows * ncols;
    const int doy = 185;   /* summer aphelion */
    const float sza = 32.0f, vza = 5.0f;

    /* ── 1. Solar position ───────────────────────────────────────────────── */
    float sol_zen, sol_az;
    sixs_possol(/*month=*/7, /*day=*/4, /*UTC=*/10.5f,
                /*lon=*/-122.0f, /*lat=*/37.5f,
                &sol_zen, &sol_az, /*year=*/2024);
    printf("Solar position: zenith = %.2f°  azimuth = %.2f°\n", sol_zen, sol_az);

    /* ── 2. Surface pressure from elevation ──────────────────────────────── */
    float p_surface = retrieve_pressure_isa(1500.0f);  /* 1500 m elevation */
    printf("Surface pressure at 1500 m: %.1f hPa\n", p_surface);

    /* ── 3. Synthetic per-pixel radiances ────────────────────────────────── */
    float *L_470  = malloc(npix * sizeof(float));
    float *L_540  = malloc(npix * sizeof(float));
    float *L_600  = malloc(npix * sizeof(float));
    float *L_660  = malloc(npix * sizeof(float));
    float *L_680  = malloc(npix * sizeof(float));
    float *L_860  = malloc(npix * sizeof(float));
    float *L_865  = malloc(npix * sizeof(float));
    float *L_940  = malloc(npix * sizeof(float));
    float *L_1040 = malloc(npix * sizeof(float));
    float *L_2130 = malloc(npix * sizeof(float));

    fill_band(L_470,  npix, 80.0f,  5.0f);
    fill_band(L_540,  npix, 70.0f,  3.0f);
    fill_band(L_600,  npix, 62.0f,  3.0f);
    fill_band(L_660,  npix, 55.0f,  4.0f);
    fill_band(L_680,  npix, 50.0f,  3.0f);
    fill_band(L_860,  npix, 120.0f, 8.0f);
    fill_band(L_865,  npix, 118.0f, 8.0f);
    fill_band(L_2130, npix, 25.0f,  2.0f);
    /* 940 nm: attenuated by water vapour (simulated ~15% depth) */
    for (int i = 0; i < npix; i++)
        L_940[i]  = L_865[i] * 0.85f - 2.0f * sinf(i * 0.5f);
    for (int i = 0; i < npix; i++)
        L_1040[i] = L_865[i] * 0.92f;

    /* ── 4. H₂O retrieval from 940 nm band depth ─────────────────────────── */
    float *wvc = malloc(npix * sizeof(float));
    retrieve_h2o_940(L_865, L_940, L_1040,
                     /*fwhm_um=*/0.0f,   /* broadband — use default K */
                     npix, sza, vza, wvc);
    float wvc_mean = 0.0f;
    for (int i = 0; i < npix; i++) wvc_mean += wvc[i];
    printf("\nH₂O retrieval (940 nm): mean WVC = %.2f g/cm²\n", wvc_mean / npix);

    /* ── 5. AOD retrieval (DDV) ───────────────────────────────────────────── */
    float *aod_px = malloc(npix * sizeof(float));
    float aod_scene = retrieve_aod_ddv(L_470, L_660, L_860, L_2130,
                                       npix, doy, sza, aod_px);
    printf("AOD retrieval (DDV): scene mean = %.3f\n", aod_scene);

    /* MAIAC patch-median spatial regularisation (32×32 patch) */
    retrieve_aod_maiac(aod_px, nrows, ncols, /*patch_sz=*/8);
    float aod_mean = 0.0f;
    for (int i = 0; i < npix; i++) aod_mean += aod_px[i];
    printf("AOD after MAIAC smoothing: mean = %.3f\n", aod_mean / npix);

    /* ── 6. O₃ retrieval from Chappuis band ──────────────────────────────── */
    float o3_du = retrieve_o3_chappuis(L_540, L_600, L_680, npix, sza, vza);
    printf("O₃ column (Chappuis 600 nm): %.0f DU\n", o3_du);

    /* ── 7. Quality bitmask ───────────────────────────────────────────────── */
    uint8_t *mask = malloc(npix * sizeof(uint8_t));
    retrieve_quality_mask(L_470, L_660, L_860,
                          /*L_swir=*/NULL,     /* skip snow detection */
                          npix, doy, sza, mask);
    int n_cloud = 0, n_water = 0;
    for (int i = 0; i < npix; i++) {
        if (mask[i] & RETRIEVE_MASK_CLOUD) n_cloud++;
        if (mask[i] & RETRIEVE_MASK_WATER) n_water++;
    }
    printf("Quality mask: cloud=%d  water=%d  (of %d pixels)\n",
           n_cloud, n_water, npix);

    /* ── 8. Joint AOD + H₂O optimal estimation ────────────────────────────── */
    float wl_vis[] = {0.47f, 0.55f, 0.66f, 0.87f};
    int   n_vis    = 4;
    float aod_lut[] = {0.0f, 0.1f, 0.2f, 0.4f};
    float h2o_lut[] = {1.0f, 2.0f, 3.0f};
    int   N = 4 * 3 * n_vis;

    float *Ra = calloc(N, sizeof(float));
    float *Td = calloc(N, sizeof(float));
    float *Tu = calloc(N, sizeof(float));
    float *sa = calloc(N, sizeof(float));
    LutConfig cfg_oe = {
        .wl = wl_vis, .n_wl = n_vis,
        .aod = aod_lut, .n_aod = 4,
        .h2o = h2o_lut, .n_h2o = 3,
        .sza = sza, .vza = vza, .raa = 90.0f,
        .altitude_km   = 1000.0f, .atmo_model = ATMO_US62,
        .aerosol_model = AEROSOL_CONTINENTAL, .ozone_du = 300.0f,
    };
    LutArrays lut_oe = { .R_atm=Ra, .T_down=Td, .T_up=Tu, .s_alb=sa };
    atcorr_compute_lut(&cfg_oe, &lut_oe);

    /* Simulated TOA reflectances [npix × n_vis] interleaved */
    float *rho_vis = malloc((size_t)npix * n_vis * sizeof(float));
    for (int i = 0; i < npix; i++)
        for (int b = 0; b < n_vis; b++)
            rho_vis[i * n_vis + b] = 0.10f + 0.05f * b + 0.02f * sinf(i * 0.2f);

    float *out_aod = malloc(npix * sizeof(float));
    float *out_h2o = malloc(npix * sizeof(float));
    oe_invert_aod_h2o(&cfg_oe, &lut_oe,
                      rho_vis, npix, n_vis, wl_vis,
                      L_865, L_940, L_1040,
                      sza, vza,
                      /*aod_prior=*/aod_scene,
                      /*h2o_prior=*/wvc_mean / npix,
                      /*sigma_aod=*/0.5f, /*sigma_h2o=*/1.0f,
                      /*sigma_spec=*/0.01f, /*fwhm_940_um=*/0.0f,
                      out_aod, out_h2o);

    float mean_aod = 0.0f, mean_h2o = 0.0f;
    for (int i = 0; i < npix; i++) {
        mean_aod += out_aod[i];
        mean_h2o += out_h2o[i];
    }
    printf("OE retrieval: mean AOD = %.3f  mean H₂O = %.2f g/cm²\n",
           mean_aod / npix, mean_h2o / npix);

    free(L_470); free(L_540); free(L_600); free(L_660); free(L_680);
    free(L_860); free(L_865); free(L_940); free(L_1040); free(L_2130);
    free(wvc); free(aod_px); free(mask);
    free(Ra); free(Td); free(Tu); free(sa);
    free(rho_vis); free(out_aod); free(out_h2o);
    return 0;
}
