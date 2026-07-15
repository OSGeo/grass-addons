/* Basic sanity test: compute Rayleigh reflectance at 550nm */
#include <stdio.h>
#include <math.h>
#include <string.h>
#include <stdlib.h>
#include "../include/sixs_ctx.h"
#include "../src/rayleigh.h"
#include "../src/rt.h"
#include "../src/scatra.h"
#include "../src/gauss.h"

/* Forward declarations */
void sixs_init_atmosphere(SixsCtx *ctx, int atmo_model);
void sixs_aerosol_init(SixsCtx *ctx, int iaer, float taer55, float xmud);
void sixs_discom(SixsCtx *ctx, int idatmp, int iaer,
                  float xmus, float xmuv, float phi,
                  float taer55, float taer55p, float palt, float phirad,
                  int nt, int mu, int np, float ftray, int ipol);
void sixs_interp(const SixsCtx *ctx, int iaer, float wl,
                  float taer55, float taer55p,
                  float *roatm, float *T_down, float *T_up, float *s_alb,
                  float *tray_out, float *taer_out);
void sixs_trunca(SixsCtx *ctx, int ipol, float *coeff);

#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif

int main(void)
{
    SixsCtx ctx = {0};
    ctx.quad.nquad  = NQ_P;
    ctx.multi.igmax = 20;

    sixs_init_atmosphere(&ctx, 1);  /* US62 */

    /* Test 1: Rayleigh OD at 550nm */
    float tray;
    sixs_odrayl(&ctx, 0.55f, &tray);
    printf("Rayleigh OD at 550nm: %.4f (expect ~0.11)\n", tray);

    /* Test 2: full RT via sixs_os for Rayleigh only at 550nm */
    float sza = 30.0f, vza = 10.0f, raa = 90.0f;
    float xmus = cosf(sza * (float)M_PI / 180.0f);
    float xmuv = cosf(vza * (float)M_PI / 180.0f);
    float phirad = raa * (float)M_PI / 180.0f;
    float xmud = -xmus * xmuv - sqrtf(1.0f-xmus*xmus) * sqrtf(1.0f-xmuv*xmuv) * cosf(phirad);

    int mu = MU_P, nt = NT_P, np = 1;

    /* Set up rm/gb */
    float rm_full[2*MU_P+1], gb_full[2*MU_P+1];
    memset(rm_full, 0, sizeof(rm_full)); memset(gb_full, 0, sizeof(gb_full));
    float cgaus[MU_P], wgaus[MU_P];
    sixs_gauss(0.0f, 1.0f, cgaus, wgaus, mu-1);
    for (int k = 1; k <= mu-1; k++) {
        rm_full[k+mu] = cgaus[k-1];
        rm_full[-k+mu] = -cgaus[k-1];
        gb_full[k+mu] = wgaus[k-1];
        gb_full[-k+mu] = wgaus[k-1];
    }
    rm_full[0+mu] = -xmus;
    rm_full[mu+mu] = xmuv;
    rm_full[-mu+mu] = -xmuv;

    /* Minimal Rayleigh betal: betal[0]=1, betal[2]=0.5 */
    for (int k = 0; k <= NQ_P; k++) ctx.polar.betal[k] = 0.0f;
    ctx.polar.betal[0] = 1.0f;
    ctx.polar.betal[2] = 0.5f;

    float xl[(2*MU_P+1)*1] = {0};
    float xlphim[1] = {0};
    float rp[1] = {phirad};

    printf("Calling sixs_os: tray=%.4f, xmus=%.4f, xmuv=%.4f\n", tray, xmus, xmuv);
    sixs_os(&ctx, 0, 0.0f, tray, 1.0f, 0.0f, 0.0f, 1000.0f,
            phirad, nt, mu, np, 1,
            rm_full, gb_full, rp, xl, xlphim, NULL);

    float rorayl = xl[0] / xmus;   /* xl(-mu, 1) / xmus */
    printf("Rayleigh reflectance at 550nm: %.4f (expect ~0.08-0.12)\n", rorayl);
    printf("xl[-mu,0] = %.6f\n", xl[0]);
    printf("xl[0,0] (surface flux) = %.6f\n", xl[(0+mu)*np + 0]);

    /* Test 3: via discom + interp */
    sixs_aerosol_init(&ctx, 1, 0.2f, xmud);  /* continental, AOD=0.2 */
    sixs_discom(&ctx, 99, 1, xmus, xmuv, raa, 0.2f, 0.0f, 1000.0f, phirad,
                nt, mu, np, 0.0f, 0);
    if (ctx.err.ier) { printf("DISCOM error!\n"); return 1; }

    float R_atm, T_dn, T_up, s_alb;
    sixs_interp(&ctx, 1, 0.55f, 0.2f, 0.0f, &R_atm, &T_dn, &T_up, &s_alb, NULL, NULL);
    printf("\nFull RT at 550nm (AOD=0.2, continental):\n");
    printf("  R_atm  = %.4f (expect ~0.06-0.12)\n", R_atm);
    printf("  T_down = %.4f (expect ~0.60-0.80)\n", T_dn);
    printf("  T_up   = %.4f (expect ~0.70-0.90)\n", T_up);
    printf("  s_alb  = %.4f (expect ~0.05-0.15)\n", s_alb);

    return 0;
}
