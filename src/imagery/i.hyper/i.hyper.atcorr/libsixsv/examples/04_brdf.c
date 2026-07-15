/**
 * 04_brdf.c — BRDF surface models, NBAR normalisation, MCD43 disaggregation.
 *
 * Demonstrates:
 *  - BRDF evaluation (RPV, Ross-Li, Hapke)
 *  - Hemispherical (white-sky) albedo integration
 *  - NBAR normalisation from acquisition to nadir geometry
 *  - MCD43 7-band → hyperspectral kernel weight disaggregation
 *  - Tikhonov spectral smoothing
 *
 * Compile:
 *   gcc -std=c11 -O2 -fopenmp -I../include 04_brdf.c \
 *       -L../testsuite -lsixsv -lm -fopenmp -Wl,-rpath,../testsuite -o 04_brdf
 */

#include <stdio.h>
#include <stdlib.h>
#define _USE_MATH_DEFINES
#include <math.h>
#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif
#include "brdf.h"
#include "spectral_brdf.h"

int main(void)
{
    const float cos_sza = cosf(35.0f * M_PI / 180.0f);
    const float cos_vza = cosf(8.0f  * M_PI / 180.0f);
    const float raa_deg = 90.0f;

    /* ── 1. RPV (Rahman-Pinty-Verstraete) model ──────────────────────────── */
    BrdfParams rpv;
    rpv.rahman.rho0 = 0.12f;   /* intensity */
    rpv.rahman.af   = -0.15f;  /* asymmetry (negative = backscatter dominant) */
    rpv.rahman.k    = 0.75f;   /* bowl/bell shape */

    float rho_rpv = sixs_brdf_eval(BRDF_RAHMAN, &rpv, cos_sza, cos_vza, raa_deg);
    float albe_rpv = sixs_brdf_albe(BRDF_RAHMAN, &rpv, cos_sza, 48, 24);
    printf("RPV:       rho = %.4f   white-sky albedo = %.4f\n", rho_rpv, albe_rpv);

    /* ── 2. Ross-Thick + Li-Sparse (Ross-Li / MCD43-equivalent) ─────────── */
    BrdfParams rl;
    rl.rosslimaignan.f_iso = 0.0774f;   /* from MCD43A1 band 4 */
    rl.rosslimaignan.f_vol = 0.0372f;
    rl.rosslimaignan.f_geo = 0.0079f;

    float rho_rl  = sixs_brdf_eval(BRDF_ROSSLIMAIGNAN, &rl, cos_sza, cos_vza, raa_deg);
    float albe_rl = sixs_brdf_albe(BRDF_ROSSLIMAIGNAN, &rl, cos_sza, 48, 24);
    printf("Ross-Li:   rho = %.4f   white-sky albedo = %.4f\n", rho_rl, albe_rl);

    /* ── 3. Hapke canopy model ───────────────────────────────────────────── */
    BrdfParams hapke;
    hapke.hapke.om = 0.85f;   /* single-scatter albedo */
    hapke.hapke.af = 0.10f;   /* asymmetry */
    hapke.hapke.s0 = 0.06f;   /* hotspot amplitude */
    hapke.hapke.h  = 0.20f;   /* hotspot width */

    float rho_hapke = sixs_brdf_eval(BRDF_HAPKE, &hapke, cos_sza, cos_vza, raa_deg);
    printf("Hapke:     rho = %.4f\n", rho_hapke);

    /* ── 4. NBAR normalisation (view-angle to nadir) ─────────────────────── */
    float rho_boa  = 0.22f;           /* corrected at acquisition geometry */
    float sza_obs  = 35.0f;
    float vza_obs  = 8.0f;
    float raa_obs  = 90.0f;
    float sza_nbar = 35.0f;           /* normalise view only; keep solar angle */

    float rho_nbar = atcorr_brdf_normalize(
        rho_boa,
        rl.rosslimaignan.f_iso,
        rl.rosslimaignan.f_vol,
        rl.rosslimaignan.f_geo,
        sza_obs, vza_obs, raa_obs, sza_nbar);
    printf("\nNBAR:  rho_boa = %.4f  →  rho_NBAR = %.4f  (VZA %g° → nadir)\n",
           rho_boa, rho_nbar, vza_obs);

    /* ── 5. MCD43 7-band kernel weights → hyperspectral disaggregation ───── */
    /* MODIS MCD43A1 band 1–7 kernel weights (illustrative values) */
    float fiso_7[] = {0.0774f, 0.1306f, 0.0688f, 0.2972f,
                      0.1218f, 0.1030f, 0.0747f};
    float fvol_7[] = {0.0372f, 0.0580f, 0.0261f, 0.1177f,
                      0.0412f, 0.0324f, 0.0203f};
    float fgeo_7[] = {0.0079f, 0.0178f, 0.0066f, 0.0598f,
                      0.0094f, 0.0068f, 0.0040f};

    /* Hyperspectral target wavelengths (200 nm spacing, 0.4 – 2.5 µm) */
    const int n_tgt = 22;
    float wl_tgt[22];
    for (int i = 0; i < n_tgt; i++) wl_tgt[i] = 0.40f + 0.10f * i;

    float *fiso_hs = malloc(n_tgt * sizeof(float));
    float *fvol_hs = malloc(n_tgt * sizeof(float));
    float *fgeo_hs = malloc(n_tgt * sizeof(float));

    mcd43_disaggregate(fiso_7, fvol_7, fgeo_7,
                       wl_tgt, n_tgt,
                       /*alpha=*/0.10f,          /* Tikhonov smoothing weight */
                       fiso_hs, fvol_hs, fgeo_hs);

    printf("\nMCD43 disaggregation: f_iso at selected wavelengths:\n");
    for (int i = 0; i < n_tgt; i += 4)
        printf("  %.2f µm: fiso=%.4f  fvol=%.4f  fgeo=%.4f\n",
               wl_tgt[i], fiso_hs[i], fvol_hs[i], fgeo_hs[i]);

    /* ── 6. Tikhonov spectral smoothing ──────────────────────────────────── */
    float spectrum[] = {0.05f, 0.07f, 0.09f, 0.11f, 0.12f, 0.20f, 0.22f, 0.23f};
    int   n_spec = 8;
    spectral_smooth_tikhonov(spectrum, n_spec, /*alpha=*/0.5f);
    printf("\nSmoothed spectrum:");
    for (int i = 0; i < n_spec; i++) printf(" %.4f", spectrum[i]);
    printf("\n");

    free(fiso_hs); free(fvol_hs); free(fgeo_hs);
    return 0;
}
