/**
 * 05_spatial_filters.c — Spatial filtering, terrain, and adjacency corrections.
 *
 * Demonstrates:
 *  - Gaussian and box spatial filters (NaN-safe, OpenMP + GPU-offload)
 *  - Terrain illumination and transmittance correction (Proy 1989)
 *  - Adjacency effect correction (Vermote 1997)
 *  - Uncertainty propagation (noise + AOD perturbation in quadrature)
 *
 * Compile:
 *   gcc -std=c11 -O2 -fopenmp -I../include 05_spatial_filters.c \
 *       -L../testsuite -lsixsv -lm -fopenmp -Wl,-rpath,../testsuite -o 05_spatial_filters
 */

#include <stdio.h>
#include <stdlib.h>
#define _USE_MATH_DEFINES
#include <math.h>
#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif
#include "atcorr.h"
#include "spatial.h"
#include "terrain.h"
#include "adjacency.h"
#include "uncertainty.h"

int main(void)
{
    const int nrows = 64, ncols = 64, npix = nrows * ncols;

    /* ── Synthetic AOD map with a few NaN outliers ───────────────────────── */
    float *aod_map = malloc(npix * sizeof(float));
    for (int r = 0; r < nrows; r++)
        for (int c = 0; c < ncols; c++) {
            int i = r * ncols + c;
            aod_map[i] = 0.10f + 0.15f * sinf(r * 0.3f) * cosf(c * 0.3f);
        }
    /* Inject NaN outliers (e.g. cloud-masked pixels) */
    for (int i = 10; i < npix; i += 100)
        aod_map[i] = (float)NAN;   /* cloud-masked outlier */

    /* ── 1. Gaussian filter (in-place, NaN excluded from neighbourhood) ──── */
    float *aod_gauss = malloc(npix * sizeof(float));
    for (int i = 0; i < npix; i++) aod_gauss[i] = aod_map[i];
    spatial_gaussian_filter(aod_gauss, nrows, ncols, /*sigma=*/2.5f);
    /* Count NaN pixels that were healed */
    int n_nan_before = 0, n_nan_after = 0;
    for (int i = 0; i < npix; i++) {
        if (aod_map[i] != aod_map[i]) n_nan_before++;
        if (aod_gauss[i] != aod_gauss[i]) n_nan_after++;
    }
    printf("Gaussian filter: NaN before=%d  after=%d\n",
           n_nan_before, n_nan_after);

    /* ── 2. Box filter (separable, allocates separate output buffer) ─────── */
    float *aod_box = malloc(npix * sizeof(float));
    spatial_box_filter(aod_map, aod_box, nrows, ncols, /*filter_half=*/3);
    float box_mean = 0.0f; int box_n = 0;
    for (int i = 0; i < npix; i++)
        if (aod_box[i] == aod_box[i]) { box_mean += aod_box[i]; box_n++; }
    printf("Box filter (half=3): output mean=%.4f\n",
           box_n ? box_mean / box_n : 0.0f);

    /* ── 3. Terrain illumination correction ──────────────────────────────── */
    float sza_deg = 35.0f, saa_deg = 150.0f;   /* solar position */
    float slope_deg = 20.0f, aspect_deg = 180.0f;  /* south-facing slope */

    float cos_i = cos_incidence(sza_deg, saa_deg, slope_deg, aspect_deg);
    float V_d   = skyview_factor(slope_deg);
    printf("\nTerrain:  cos_i = %.4f  skyview = %.4f  %s\n",
           cos_i, V_d, cos_i <= 0.0f ? "(topographic shadow)" : "");

    /* Adjust T_down for the tilted surface (example values from LUT) */
    float T_down     = 0.85f;  /* total downward transmittance */
    float T_down_dir = 0.70f;  /* direct component */
    float cos_sza    = cosf(sza_deg * M_PI / 180.0f);

    float T_down_eff = atcorr_terrain_T_down(T_down, T_down_dir, cos_sza, cos_i, V_d);
    printf("T_down flat=%.4f  T_down_eff (slope)=%.4f\n", T_down, T_down_eff);

    /* Per-pixel T_up correction for view-zenith variation (tilted surface) */
    float T_up       = 0.90f;
    float cos_vza    = cosf(8.0f * M_PI / 180.0f);
    float T_up_eff   = atcorr_terrain_T_up(T_up, cos_vza, /*vza_pixel_deg=*/15.0f);
    printf("T_up flat=%.4f   T_up_eff (off-nadir view)=%.4f\n", T_up, T_up_eff);

    /* ── 4. Adjacency effect correction ──────────────────────────────────── */
    /* Simulate BOA reflectance map for one band */
    float *r_boa = malloc(npix * sizeof(float));
    for (int i = 0; i < npix; i++)
        r_boa[i] = 0.10f + 0.25f * (float)(i % ncols) / ncols;

    /* Apply Vermote 1997 in-place (computes r_env and T_dir internally) */
    adjacency_correct_band(
        r_boa, nrows, ncols,
        /*psf_radius_km=*/1.0f,       /* adjacency PSF radius */
        /*pixel_size_m=*/30.0f,       /* Landsat 30 m pixels */
        /*T_scat=*/1.0f - T_down_dir, /* scattering transmittance */
        /*s_alb=*/0.10f,
        /*wl_um=*/0.65f,
        /*aod550=*/0.15f,
        /*pressure=*/1013.25f,
        /*sza_deg=*/sza_deg,
        /*vza_deg=*/8.0f);

    float r_mean = 0.0f;
    for (int i = 0; i < npix; i++) r_mean += r_boa[i];
    printf("\nAdjacency correction: mean BOA = %.4f\n", r_mean / npix);

    /* ── 5. Uncertainty propagation ──────────────────────────────────────── */
    float wl_um  = 0.65f;
    float aod_val = 0.15f, h2o_val = 2.0f;
    float d2 = (float)sixs_earth_sun_dist2(185);
    float E0 = sixs_E0(wl_um);

    /* Build a minimal LUT for the uncertainty call */
    float wl_u[]  = {0.65f};
    float aod_u[] = {0.0f, 0.1f, 0.2f, 0.4f};
    float h2o_u[] = {1.0f, 3.0f};
    int Nu = 4 * 2 * 1;
    float *Ra = calloc(Nu, sizeof(float));
    float *Td = calloc(Nu, sizeof(float));
    float *Tu = calloc(Nu, sizeof(float));
    float *sa = calloc(Nu, sizeof(float));
    LutConfig cfg_u = {
        .wl=wl_u, .n_wl=1, .aod=aod_u, .n_aod=4, .h2o=h2o_u, .n_h2o=2,
        .sza=35.0f, .vza=8.0f, .raa=90.0f, .altitude_km   = 1000.0f,
        .atmo_model=ATMO_US62, .aerosol_model=AEROSOL_CONTINENTAL, .ozone_du=300.0f,
    };
    LutArrays lut_u = { .R_atm=Ra, .T_down=Td, .T_up=Tu, .s_alb=sa };
    atcorr_compute_lut(&cfg_u, &lut_u);

    float *sigma_out = malloc(npix * sizeof(float));
    uncertainty_compute_band(
        /*rad_band=*/NULL, r_boa, npix,
        E0, d2, cosf(35.0f * M_PI / 180.0f),
        /*T_down=*/0.85f, /*T_up=*/0.90f, /*s_alb=*/0.08f, /*R_atm=*/0.05f,
        /*nedl=*/0.0f,   /* estimate from rad_band — NULL → use 0.01 fallback */
        /*aod_sigma=*/0.04f,
        &cfg_u, &lut_u, wl_um, aod_val, h2o_val,
        sigma_out);

    float sig_mean = 0.0f;
    for (int i = 0; i < npix; i++) sig_mean += sigma_out[i];
    printf("Uncertainty (σ_rfl) at 650 nm: mean = %.5f\n", sig_mean / npix);

    free(aod_map); free(aod_gauss); free(aod_box);
    free(r_boa); free(sigma_out);
    free(Ra); free(Td); free(Tu); free(sa);
    return 0;
}
