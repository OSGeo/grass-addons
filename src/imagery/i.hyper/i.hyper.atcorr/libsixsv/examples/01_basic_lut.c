/**
 * 01_basic_lut.c — LUT computation and single-pixel Lambertian correction.
 *
 * Compile:
 *   gcc -std=c11 -O2 -fopenmp -I../include 01_basic_lut.c \
 *       -L../testsuite -lsixsv -lm -fopenmp -Wl,-rpath,../testsuite -o 01_basic_lut
 * Run:
 *   ./01_basic_lut
 */

#include <stdio.h>
#include <stdlib.h>
#include "atcorr.h"

int main(void)
{
    /* ── 1. LUT grid ────────────────────────────────────────────────────── */
    float wl[]  = {0.45f, 0.55f, 0.65f, 0.87f};   /* µm */
    float aod[] = {0.0f, 0.1f, 0.2f, 0.4f};        /* AOD at 550 nm */
    float h2o[] = {1.0f, 2.0f, 3.0f};              /* g/cm² WVC */

    int n_wl = 4, n_aod = 4, n_h2o = 3;
    int N = n_aod * n_h2o * n_wl;

    /* ── 2. Scene geometry and atmospheric model ─────────────────────────── */
    LutConfig cfg = {
        .wl            = wl,  .n_wl  = n_wl,
        .aod           = aod, .n_aod = n_aod,
        .h2o           = h2o, .n_h2o = n_h2o,
        .sza           = 35.0f,     /* solar zenith [deg] */
        .vza           = 5.0f,      /* view zenith [deg]  */
        .raa           = 90.0f,     /* relative azimuth [deg] */
        .altitude_km   = 1000.0f,    /* Landsat / Sentinel orbit */
        .atmo_model    = ATMO_US62,
        .aerosol_model = AEROSOL_CONTINENTAL,
        .ozone_du      = 300.0f,
    };

    /* ── 3. Allocate and fill LUT (OpenMP-parallel over AOD dimension) ───── */
    float *R_atm  = malloc(N * sizeof(float));
    float *T_down = malloc(N * sizeof(float));
    float *T_up   = malloc(N * sizeof(float));
    float *s_alb  = malloc(N * sizeof(float));

    LutArrays lut = {
        .R_atm = R_atm, .T_down = T_down,
        .T_up  = T_up,  .s_alb  = s_alb,
        /* optional arrays — not needed for Lambertian correction */
        .T_down_dir = NULL, .R_atmQ = NULL, .R_atmU = NULL,
    };

    int rc = atcorr_compute_lut(&cfg, &lut);
    if (rc != 0) { fprintf(stderr, "atcorr_compute_lut failed (%d)\n", rc); return 1; }

    /* ── 4. Bilinear slice at AOD=0.15, H2O=2.0 ─────────────────────────── */
    float Rs[4], Tds[4], Tus[4], ss[4];
    atcorr_lut_slice(&cfg, &lut, /*aod=*/0.15f, /*h2o=*/2.0f,
                     Rs, Tds, Tus, ss, /*T_down_dir=*/NULL);

    /* ── 5. Per-band Lambertian inversion ────────────────────────────────── */
    const char *band_names[] = {"Blue", "Green", "Red", "NIR"};
    float rho_toa[] = {0.18f, 0.20f, 0.15f, 0.35f};

    printf("Band    TOA      BOA      R_atm    T_dn     T_up     s_alb\n");
    printf("------  -------  -------  -------  -------  -------  -------\n");
    for (int b = 0; b < n_wl; b++) {
        float rho_boa = atcorr_invert(rho_toa[b], Rs[b], Tds[b], Tus[b], ss[b]);
        printf("%-6s  %.4f   %.4f   %.4f   %.4f   %.4f   %.4f\n",
               band_names[b], rho_toa[b], rho_boa, Rs[b], Tds[b], Tus[b], ss[b]);
    }

    /* ── 6. Solar irradiance and Earth–Sun distance ──────────────────────── */
    printf("\nSolar irradiance at 550 nm: %.1f W/m²/µm\n", sixs_E0(0.55f));
    printf("Earth-Sun d² at DOY 185 (aphelion): %.6f AU²\n",
           sixs_earth_sun_dist2(185));

    free(R_atm); free(T_down); free(T_up); free(s_alb);
    return 0;
}
