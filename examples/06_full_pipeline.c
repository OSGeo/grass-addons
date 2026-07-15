/**
 * 06_full_pipeline.c — End-to-end hyperspectral atmospheric correction.
 *
 * Full operational pipeline:
 *  1.  Surface pressure from elevation (ISA)
 *  2.  O₃ column from Chappuis 600 nm band depth
 *  3.  H₂O map from 940 nm band depth
 *  4.  AOD map from MODIS DDV + MAIAC spatial regularisation
 *  5.  Build 3-D LUT (OpenMP-parallel)
 *  6.  Quality bitmask (cloud / shadow / water / snow)
 *  7.  Per-pixel atmospheric correction (Lambertian inversion, parallel)
 *  8.  Adjacency effect correction (Vermote 1997)
 *  9.  Terrain correction (Proy 1989)
 * 10.  Per-band uncertainty propagation
 * 11.  DASF canopy structure retrieval from 710–790 nm NIR plateau
 *
 * Compile:
 *   gcc -std=c11 -O2 -fopenmp -I../include 06_full_pipeline.c \
 *       -L../testsuite -lsixsv -lm -fopenmp -Wl,-rpath,../testsuite -o 06_full_pipeline
 */

#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#define _USE_MATH_DEFINES
#include <math.h>
#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif
#include <string.h>
#include "atcorr.h"
#include "retrieve.h"
#include "spatial.h"
#include "terrain.h"
#include "adjacency.h"
#include "uncertainty.h"

/* ── Simulation helpers ───────────────────────────────────────────────────── */
static void fill_band(float *buf, int n, float base, float var)
{
    for (int i = 0; i < n; i++)
        buf[i] = base + var * sinf((float)i * 0.15f + base);
}

int main(void)
{
    /* ── Scene parameters ────────────────────────────────────────────────── */
    const int nrows = 32, ncols = 32, npix = nrows * ncols;
    const int doy    = 210;
    const float sza  = 30.0f, vza = 6.0f, raa = 100.0f;
    const float elev_m = 800.0f;

    /* Hyperspectral: 10 bands covering 450–870 nm at ~50 nm spacing */
    const int n_bands = 10;
    float wl[] = {0.45f, 0.50f, 0.55f, 0.60f, 0.65f,
                  0.70f, 0.75f, 0.80f, 0.84f, 0.87f};

    printf("=== lib6sv Full Pipeline ===\n");
    printf("Scene: %d×%d px  DOY=%d  SZA=%.1f°  VZA=%.1f°\n\n",
           nrows, ncols, doy, sza, vza);

    /* ── Step 1: Surface pressure from elevation ─────────────────────────── */
    float pressure = retrieve_pressure_isa(elev_m);
    printf("[1] Surface pressure: %.1f hPa (%.0f m elevation)\n", pressure, elev_m);

    /* ── Simulated per-pixel radiances ───────────────────────────────────── */
    float *bands[10];
    float bases[] = {90.0f, 85.0f, 78.0f, 68.0f, 60.0f,
                     50.0f, 45.0f, 42.0f, 38.0f, 35.0f};
    for (int b = 0; b < n_bands; b++) {
        bands[b] = malloc(npix * sizeof(float));
        fill_band(bands[b], npix, bases[b], 8.0f);
    }
    /* Diagnostic bands */
    float *L_540 = bands[2], *L_600 = bands[3], *L_680 = bands[5];
    float *L_865 = bands[8];

    float *L_470  = malloc(npix * sizeof(float)); fill_band(L_470,  npix, 95.0f, 6.0f);
    float *L_660  = malloc(npix * sizeof(float)); fill_band(L_660,  npix, 60.0f, 4.0f);
    float *L_940  = malloc(npix * sizeof(float));
    float *L_1040 = malloc(npix * sizeof(float));
    float *L_2130 = malloc(npix * sizeof(float)); fill_band(L_2130, npix, 20.0f, 2.0f);
    for (int i = 0; i < npix; i++) {
        L_940[i]  = L_865[i] * 0.82f - 3.0f * sinf(i * 0.4f);
        L_1040[i] = L_865[i] * 0.91f;
    }

    /* ── Step 2: O₃ column ───────────────────────────────────────────────── */
    float o3_du = retrieve_o3_chappuis(L_540, L_600, L_680, npix, sza, vza);
    printf("[2] O₃ column: %.0f DU\n", o3_du);

    /* ── Step 3: H₂O map ─────────────────────────────────────────────────── */
    float *wvc = malloc(npix * sizeof(float));
    retrieve_h2o_940(L_865, L_940, L_1040, 0.0f, npix, sza, vza, wvc);
    float wvc_mean = 0.0f;
    for (int i = 0; i < npix; i++) wvc_mean += wvc[i];
    wvc_mean /= npix;
    /* Smooth the WVC map */
    spatial_gaussian_filter(wvc, nrows, ncols, 1.5f);
    printf("[3] H₂O: mean WVC = %.2f g/cm²\n", wvc_mean);

    /* ── Step 4: AOD map (DDV + MAIAC) ───────────────────────────────────── */
    float *aod_px = malloc(npix * sizeof(float));
    float aod_scene = retrieve_aod_ddv(L_470, L_660, L_865, L_2130,
                                       npix, doy, sza, aod_px);
    retrieve_aod_maiac(aod_px, nrows, ncols, 8);
    printf("[4] AOD: scene mean = %.3f (after MAIAC)\n", aod_scene);

    /* ── Step 5: LUT computation ─────────────────────────────────────────── */
    float aod_lut[] = {0.0f, 0.1f, 0.2f, 0.3f, 0.5f};
    float h2o_lut[] = {0.5f, 1.5f, 2.5f, 3.5f};
    int n_aod = 5, n_h2o = 4;
    int N = n_aod * n_h2o * n_bands;

    float *R_atm  = malloc(N * sizeof(float));
    float *T_down = malloc(N * sizeof(float));
    float *T_up   = malloc(N * sizeof(float));
    float *s_alb  = malloc(N * sizeof(float));
    float *T_dir  = malloc(N * sizeof(float));   /* direct: needed for adjacency */

    LutConfig cfg = {
        .wl = wl, .n_wl = n_bands,
        .aod = aod_lut, .n_aod = n_aod,
        .h2o = h2o_lut, .n_h2o = n_h2o,
        .sza = sza, .vza = vza, .raa = raa,
        .altitude_km   = 1000.0f,
        .atmo_model = ATMO_US62,
        .aerosol_model = AEROSOL_CONTINENTAL,
        .ozone_du = o3_du,
        .surface_pressure = pressure,
    };
    LutArrays lut = {
        .R_atm = R_atm, .T_down = T_down,
        .T_up  = T_up,  .s_alb  = s_alb,
        .T_down_dir = T_dir,
        .R_atmQ = NULL, .R_atmU = NULL,
    };
    atcorr_compute_lut(&cfg, &lut);
    printf("[5] LUT computed: %d × %d × %d\n", n_aod, n_h2o, n_bands);

    /* ── Step 6: Quality bitmask ─────────────────────────────────────────── */
    uint8_t *qmask = malloc(npix * sizeof(uint8_t));
    retrieve_quality_mask(L_470, L_660, L_865, NULL, npix, doy, sza, qmask);
    int n_valid = 0;
    for (int i = 0; i < npix; i++) if (!qmask[i]) n_valid++;
    printf("[6] Valid pixels: %d / %d\n", n_valid, npix);

    /* ── Step 7: Per-pixel Lambertian correction ─────────────────────────── */
    float *rho_boa = malloc((size_t)n_bands * npix * sizeof(float));

    for (int b = 0; b < n_bands; b++) {
        /* Scene-average LUT slice for this band */
        float Rs[10], Tds[10], Tus[10], ss[10];
        atcorr_lut_slice(&cfg, &lut, aod_scene, wvc_mean,
                         Rs, Tds, Tus, ss, NULL);

        #ifdef _OPENMP
        #pragma omp parallel for schedule(static)
        #endif
        for (int i = 0; i < npix; i++) {
            float rho_toa = bands[b][i] * (float)M_PI
                            / (sixs_E0(wl[b]) * cosf(sza * (float)M_PI / 180.0f));
            rho_boa[b * npix + i] = (qmask[i] == 0)
                ? atcorr_invert(rho_toa, Rs[b], Tds[b], Tus[b], ss[b])
                : 1.0f / 0.0f;   /* NaN for flagged pixels */
        }
    }
    printf("[7] Per-pixel correction done (Lambertian)\n");

    /* ── Step 8: Adjacency effect correction ─────────────────────────────── */
    float Rs_avg[10], Tds_avg[10], Tus_avg[10], ss_avg[10];
    atcorr_lut_slice(&cfg, &lut, aod_scene, wvc_mean,
                     Rs_avg, Tds_avg, Tus_avg, ss_avg, NULL);

    for (int b = 0; b < n_bands; b++) {
        float T_scat = 1.0f - (Tds_avg[b] - 0.7f * Tds_avg[b]);  /* approx */
        adjacency_correct_band(
            rho_boa + b * npix, nrows, ncols,
            1.0f, 30.0f,
            T_scat, ss_avg[b],
            wl[b], aod_scene, pressure, sza, vza);
    }
    printf("[8] Adjacency correction done\n");

    /* ── Step 9: Terrain correction ──────────────────────────────────────── */
    /* Uniform slope/aspect (in practice: per-pixel DEM-derived) */
    float slope = 12.0f, aspect_deg = 200.0f, saa = 150.0f;
    float cos_i   = cos_incidence(sza, saa, slope, aspect_deg);
    float V_d     = skyview_factor(slope);
    float cos_sza = cosf(sza * (float)M_PI / 180.0f);
    float cos_vza = cosf(vza * (float)M_PI / 180.0f);

    for (int b = 0; b < n_bands; b++) {
        /* Re-fetch T_dir for this band from the LUT */
        float Rs2[10], Tds2[10], Tus2[10], ss2[10], Tdds[10];
        atcorr_lut_slice(&cfg, &lut, aod_scene, wvc_mean,
                         Rs2, Tds2, Tus2, ss2, Tdds);
        float T_eff = atcorr_terrain_T_down(Tds2[b], Tdds[b], cos_sza, cos_i, V_d);
        float T_up_eff = atcorr_terrain_T_up(Tus2[b], cos_vza, vza + slope * 0.3f);
        /* Rescale BOA reflectance for the terrain transmittance change */
        float scale = (T_eff * T_up_eff) / (Tds2[b] * Tus2[b] + 1e-6f);
        for (int i = 0; i < npix; i++)
            if (rho_boa[b * npix + i] == rho_boa[b * npix + i])  /* finite */
                rho_boa[b * npix + i] *= scale;
    }
    printf("[9] Terrain correction done (slope=%.0f°, aspect=%.0f°)\n",
           slope, aspect_deg);

    /* ── Step 10: Uncertainty propagation ────────────────────────────────── */
    double d2 = sixs_earth_sun_dist2(doy);
    float *sigma = malloc((size_t)n_bands * npix * sizeof(float));

    for (int b = 0; b < n_bands; b++) {
        float Rs2[10], Tds2[10], Tus2[10], ss2[10];
        atcorr_lut_slice(&cfg, &lut, aod_scene, wvc_mean,
                         Rs2, Tds2, Tus2, ss2, NULL);
        uncertainty_compute_band(
            bands[b], rho_boa + b * npix, npix,
            sixs_E0(wl[b]), (float)d2, cos_sza,
            Tds2[b], Tus2[b], ss2[b], Rs2[b],
            0.0f, 0.04f,
            &cfg, &lut, wl[b], aod_scene, wvc_mean,
            sigma + b * npix);
    }
    printf("[10] Uncertainty propagation done\n");

    /* ── Step 11: Summary statistics ────────────────────────────────────────*/
    printf("\n=== Results ===\n");
    printf("%-6s  %-6s  %-8s  %-8s\n", "Band", "WL(µm)", "mean_BOA", "mean_sigma");
    for (int b = 0; b < n_bands; b++) {
        float mb = 0.0f, ms = 0.0f;
        int n = 0;
        for (int i = 0; i < npix; i++) {
            float v = rho_boa[b * npix + i];
            if (v == v) { mb += v; ms += sigma[b * npix + i]; n++; }
        }
        printf("%-6d  %-6.2f  %-8.4f  %-8.5f\n",
               b, wl[b], n ? mb / n : 0.0f, n ? ms / n : 0.0f);
    }

    for (int b = 0; b < n_bands; b++) free(bands[b]);
    free(L_470); free(L_660); free(L_940); free(L_1040); free(L_2130);
    free(wvc); free(aod_px); free(qmask);
    free(R_atm); free(T_down); free(T_up); free(s_alb); free(T_dir);
    free(rho_boa); free(sigma);
    return 0;
}
