/* Scattering transmittances — ported from 6SV2.1 SCATRA.f + ISO.f */
#include "../include/sixs_ctx.h"
#include "discre.h"
#include "kernel.h"
#include <math.h>
#include <string.h>
#include <stdlib.h>

void sixs_csalbr(float xtau, float *xalb);

/* Forward declarations */
static void compute_iso(SixsCtx *ctx, float taer, float tray, float pizmoy,
                         float taerp, float trayp, float palt,
                         int nt, int mu, const float *rm, const float *gb,
                         float *xtrans_m1, float *xtrans_0, float *xtrans_1);

/**
 * \brief Compute direction/diffuse transmittances and spherical albedo.
 *
 * Provides the six transmittance/albedo triplets (total, Rayleigh-only,
 * aerosol-only) that feed into the surface-reflectance inversion:
 * - \c ddirtt / \c ddiftt — downward direct / diffuse (total)
 * - \c udirtt / \c udiftt — upward direct / diffuse (total)
 * - \c sphalbt — total spherical albedo
 * - analogous \c *r and \c *a suffixes for Rayleigh-only and aerosol-only.
 *
 * At satellite altitude (palt > 900 km) a closed-form Rayleigh solution is
 * used; otherwise the successive-orders solver (compute_iso()) is called.
 *
 * Ported from 6SV2.1 SCATRA.f.
 *
 * \param[in,out] ctx      6SV context with initialised atmosphere, aerosol and quadrature.
 * \param[in]     taer     Total aerosol OD above target.
 * \param[in]     taerp    Aerosol OD above sensor plane.
 * \param[in]     tray     Total Rayleigh OD above target.
 * \param[in]     trayp    Rayleigh OD above sensor plane.
 * \param[in]     piza     Single-scattering albedo of the aerosol.
 * \param[in]     palt     Sensor altitude in km (> 900 = satellite).
 * \param[in]     nt       Number of atmospheric integration levels.
 * \param[in]     mu       Number of Gauss quadrature angles per hemisphere.
 * \param[in]     rm       Quadrature cosines (offset array, size 2mu+1).
 * \param[in]     gb       Gauss weights (offset array, size 2mu+1).
 * \param[in]     xmus     Cosine of solar zenith angle.
 * \param[in]     xmuv     Cosine of view zenith angle.
 * \param[out]    ddirtt   Downward direct transmittance (total).
 * \param[out]    ddiftt   Downward diffuse transmittance (total).
 * \param[out]    udirtt   Upward direct transmittance (total).
 * \param[out]    udiftt   Upward diffuse transmittance (total).
 * \param[out]    sphalbt  Spherical albedo (total).
 * \param[out]    ddirtr   Downward direct transmittance (Rayleigh only).
 * \param[out]    ddiftr   Downward diffuse transmittance (Rayleigh only).
 * \param[out]    udirtr   Upward direct transmittance (Rayleigh only).
 * \param[out]    udiftr   Upward diffuse transmittance (Rayleigh only).
 * \param[out]    sphalbr  Spherical albedo (Rayleigh only).
 * \param[out]    ddirta   Downward direct transmittance (aerosol only).
 * \param[out]    ddifta   Downward diffuse transmittance (aerosol only).
 * \param[out]    udirta   Upward direct transmittance (aerosol only).
 * \param[out]    udifta   Upward diffuse transmittance (aerosol only).
 * \param[out]    sphalba  Spherical albedo (aerosol only).
 */
void sixs_scatra(SixsCtx *ctx,
                  float taer, float taerp, float tray, float trayp,
                  float piza, float palt, int nt, int mu,
                  const float *rm, const float *gb,
                  float xmus, float xmuv,
                  float *ddirtt, float *ddiftt, float *udirtt, float *udiftt, float *sphalbt,
                  float *ddirtr, float *ddiftr, float *udirtr, float *udiftr, float *sphalbr,
                  float *ddirta, float *ddifta, float *udirta, float *udifta, float *sphalba)
{
    /* Initialize */
    *ddirtt=1.f; *ddiftt=0.f; *udirtt=1.f; *udiftt=0.f; *sphalbt=0.f;
    *ddirtr=1.f; *ddiftr=0.f; *udirtr=1.f; *udiftr=0.f; *sphalbr=0.f;
    *ddirta=1.f; *ddifta=0.f; *udirta=1.f; *udifta=0.f; *sphalba=0.f;

    for (int it = 1; it <= 3; it++) {
        if (it == 2 && taer <= 0.0f) continue;

        if (it == 1) {
            if (palt > 900.0f) {
                /* Simple analytical Rayleigh */
                *udiftt = (2.f/3.f + xmuv) + (2.f/3.f - xmuv) * expf(-tray / xmuv);
                *udiftt = *udiftt / (4.f/3.f + tray) - expf(-tray / xmuv);
                *ddiftt = (2.f/3.f + xmus) + (2.f/3.f - xmus) * expf(-tray / xmus);
                *ddiftt = *ddiftt / (4.f/3.f + tray) - expf(-tray / xmus);
                *ddirtt = expf(-tray / xmus);
                *udirtt = expf(-tray / xmuv);
                sixs_csalbr(tray, sphalbt);
            } else if (palt > 0.0f) {
                float xt_m1, xt_0, xt_1;
                /* Upward: view direction */
                float tamol = 0.0f, tamolp = 0.0f;
                compute_iso(ctx, tamol, tray, piza, tamolp, trayp, palt,
                            nt, mu, rm, gb, &xt_m1, &xt_0, &xt_1);
                *udiftt = xt_m1 - expf(-trayp / xmuv);
                *udirtt = expf(-trayp / xmuv);
                /* Downward: simple formula */
                *ddiftt = (2.f/3.f + xmus) + (2.f/3.f - xmus) * expf(-tray / xmus);
                *ddiftt = *ddiftt / (4.f/3.f + tray) - expf(-tray / xmus);
                *ddirtt = expf(-tray / xmus);
                *udirtt = expf(-tray / xmuv);
                sixs_csalbr(tray, sphalbt);
            } else {
                *udiftt = 0.f; *udirtt = 1.f;
            }
        }

        if (it == 2) {
            float xt_m1, xt_0, xt_1;
            float tamol = 0.0f, tamolp = 0.0f;
            /* Upward */
            compute_iso(ctx, taer, tamol, piza, taerp, tamolp, palt,
                        nt, mu, rm, gb, &xt_m1, &xt_0, &xt_1);
            *udiftt = xt_m1 - expf(-taerp / xmuv);
            *udirtt = expf(-taerp / xmuv);
            /* Downward + spherical albedo */
            compute_iso(ctx, taer, tamol, piza, taerp, tamolp, 999.0f,
                        nt, mu, rm, gb, &xt_m1, &xt_0, &xt_1);
            *ddirtt = expf(-taer / xmus);
            *ddiftt = xt_1 - expf(-taer / xmus);
            *sphalbt = xt_0 * 2.0f;
            if (palt <= 0.0f) { *udiftt = 0.f; *udirtt = 1.f; }
        }

        if (it == 3) {
            float xt_m1, xt_0, xt_1;
            /* Upward */
            compute_iso(ctx, taer, tray, piza, taerp, trayp, palt,
                        nt, mu, rm, gb, &xt_m1, &xt_0, &xt_1);
            *udirtt = expf(-(taerp + trayp) / xmuv);
            *udiftt = xt_m1 - expf(-(taerp + trayp) / xmuv);
            /* Downward + spherical albedo */
            compute_iso(ctx, taer, tray, piza, taerp, trayp, 999.0f,
                        nt, mu, rm, gb, &xt_m1, &xt_0, &xt_1);
            *ddiftt = xt_1 - expf(-(taer + tray) / xmus);
            *ddirtt = expf(-(taer + tray) / xmus);
            *sphalbt = xt_0 * 2.0f;
            if (palt <= 0.0f) { *udiftt = 0.f; *udirtt = 1.f; }
        }

        /* Copy Rayleigh (it==1) and aerosol (it==2) results */
        if (it == 1) {
            *ddirtr=*ddirtt; *ddiftr=*ddiftt;
            *udirtr=*udirtt; *udiftr=*udiftt;
            *sphalbr=*sphalbt;
        }
        if (it == 2) {
            *ddirta=*ddirtt; *ddifta=*ddiftt;
            *udirta=*udirtt; *udifta=*udiftt;
            *sphalba=*sphalbt;
        }
    }
}

/**
 * \brief Compute diffuse transmittances via successive orders of scattering.
 *
 * Internal helper (ported from 6SV2.1 ISO.f) that calls sixs_os() in isotropic
 * illumination mode to obtain three transmittance integrals:
 *
 * - \c *xtrans_m1 — upward diffuse transmittance at the sensor plane.
 * - \c *xtrans_0  — 0.5 × spherical albedo.
 * - \c *xtrans_1  — downward diffuse transmittance through the total atmosphere.
 *
 * \param[in,out] ctx       6SV context.
 * \param[in]     tamoy     Aerosol OD above target.
 * \param[in]     trmoy     Rayleigh OD above target.
 * \param[in]     pizmoy    Single-scattering albedo.
 * \param[in]     tamoyp    Aerosol OD above sensor plane.
 * \param[in]     trmoyp    Rayleigh OD above sensor plane.
 * \param[in]     palt      Sensor altitude in km.
 * \param[in]     nt        Number of atmospheric levels.
 * \param[in]     mu        Number of quadrature angles per hemisphere.
 * \param[in]     rm        Quadrature cosines (offset array).
 * \param[in]     gb        Gauss weights (offset array).
 * \param[out]    xtrans_m1 Upward diffuse transmittance at the sensor plane.
 * \param[out]    xtrans_0  0.5 × spherical albedo.
 * \param[out]    xtrans_1  Downward diffuse transmittance (total atmosphere).
 */
static void compute_iso(SixsCtx *ctx, float tamoy, float trmoy, float pizmoy,
                          float tamoyp, float trmoyp, float palt,
                          int nt, int mu, const float *rm, const float *gb,
                          float *xtrans_m1, float *xtrans_0, float *xtrans_1)
{
    *xtrans_m1 = 0.f; *xtrans_0 = 0.f; *xtrans_1 = 0.f;

    /* Allocate working arrays */
    int sz = nt + 1;
    double *h    = (double*)calloc(sz, sizeof(double));
    double *xdel = (double*)calloc(sz, sizeof(double));
    double *ydel = (double*)calloc(sz, sizeof(double));
    double *altc = (double*)calloc(sz, sizeof(double));
    int dim = 2 * mu + 1;
    double *i1 = (double*)calloc(sz * dim, sizeof(double));
    double *i2 = (double*)calloc(sz * dim, sizeof(double));
    double *i3 = (double*)calloc(dim, sizeof(double));
    double *in_ = (double*)calloc(dim, sizeof(double));
    double *inm1= (double*)calloc(dim, sizeof(double));
    double *inm2= (double*)calloc(dim, sizeof(double));
    /* Kernel arrays */
    int psl_dim = (NQ_P + 2) * dim;
    double *xpl = (double*)calloc(dim, sizeof(double));
    double *psl = (double*)calloc(psl_dim, sizeof(double));
    double *bp  = (double*)calloc((mu + 1) * dim, sizeof(double));

    if (!h || !xdel || !ydel || !altc || !i1 || !i2 || !i3 || !in_ || !inm1 || !inm2 || !xpl || !psl || !bp)
        goto cleanup;

    /* Access helpers */
    #define I1(k,j) i1[(k)*dim + (j)+mu]
    #define I2(k,j) i2[(k)*dim + (j)+mu]
    #define I3(j)   i3[(j)+mu]
    #define IN(j)   in_[(j)+mu]
    #define INM1(j) inm1[(j)+mu]
    #define INM2(j) inm2[(j)+mu]
    #undef RM
    #undef GB
    #define RM(j)   rm[(j)+mu]
    #define GB(j)   gb[(j)+mu]
    #define XPL(j)  xpl[(j)+mu]
    #define BP(j,k) bp[(j)*dim + (k)+mu]

    double accu = 1e-20, acu2 = 1e-3;
    double ta = tamoy, tr = trmoy, piz = pizmoy;
    double trp = trmoy - trmoyp, tap = tamoy - tamoyp;
    double hr = 8.0, ha = 2.0;
    int ntp = nt, iplane = 0;

    if (palt <= 900.0 && palt > 0.0) {
        ha = (tap > 1e-3) ? -palt / log(tap / ta) : 2.0;
        ntp = nt - 1;
    }

    /* Set up layer grid */
    if (ta <= acu2 && tr > ta) {
        for (int j = 0; j <= ntp; j++) {
            h[j] = (double)j * tr / ntp;
            ydel[j] = 1.0; xdel[j] = 0.0;
        }
    } else if (tr <= acu2 && ta > tr) {
        for (int j = 0; j <= ntp; j++) {
            h[j] = (double)j * ta / ntp;
            ydel[j] = 0.0; xdel[j] = piz;
        }
    } else {
        ydel[0] = 1.0; xdel[0] = 0.0; h[0] = 0.0; altc[0] = 300.0;
        double zx = 300.0;
        for (int it = 0; it <= ntp; it++) {
            double yy = (it > 0) ? h[it-1] : 0.0;
            double dd = (it > 0) ? ydel[it-1] : 0.0;
            int itp = it;
            sixs_discre(ctx, ta, ha, tr, hr, itp, ntp, yy, dd, 300.0, 0.0, &zx);
            if (ctx->err.ier) goto cleanup;
            double xxx = -zx / ha;
            double ca = (xxx < -18.0) ? 0.0 : ta * exp(xxx);
            double cr = tr * exp(-zx / hr);
            h[it] = cr + ca;
            altc[it] = zx;
            cr /= hr; ca /= ha;
            double ratio = (cr + ca > 0.0) ? cr / (cr + ca) : 0.5;
            xdel[it] = (1.0 - ratio) * piz;
            ydel[it] = ratio;
        }
    }

    /* Plane layer update */
    if (ntp == nt - 1) {
        double taup = tap + trp;
        iplane = -1;
        for (int i = 0; i <= ntp; i++) if (taup >= h[i]) iplane = i;
        double th = 0.005;
        double xt1 = fabs(h[iplane] - taup);
        double xt2 = fabs(h[iplane+1] - taup);
        if (xt1 > th && xt2 > th) {
            for (int i = nt; i >= iplane+1; i--) {
                xdel[i]=xdel[i-1]; ydel[i]=ydel[i-1]; h[i]=h[i-1]; altc[i]=altc[i-1];
            }
        } else {
            nt = ntp;
            if (xt2 < xt1) iplane++;
        }
        if (tr > acu2 && ta > acu2) {
            double ca = ta * exp(-palt / ha), cr = tr * exp(-palt / hr);
            cr /= hr; ca /= ha;
            double ratio = cr / (cr + ca);
            xdel[iplane] = (1.0 - ratio) * piz;
            ydel[iplane] = ratio;
            altc[iplane] = palt;
        }
    }

    /* Kernel for is=0 */
    sixs_kernel(ctx, 0, mu, rm, xpl, psl, bp);

    /* Rayleigh depolarization */
    double aaaa = ctx->del.delta / (2.0 - ctx->del.delta);
    double ron  = (1.0 - aaaa) / (1.0 + 2.0 * aaaa);
    double beta0 = 1.0, beta2 = 0.5 * ron;

    /* Primary scattering: initialize i1 for upward direction */
    for (int k = 1; k <= mu; k++) {
        I1(nt, k) = 1.0;
        double yy = RM(k);
        for (int i = nt - 1; i >= 0; i--) {
            I1(i, k) = exp(-(ta + tr - h[i]) / yy);
        }
    }
    for (int k = -mu; k <= -1; k++) {
        for (int i = 0; i <= nt; i++) I1(i, k) = 0.0;
    }

    int igmax = ctx->multi.igmax;
    double tavion = I1(iplane, mu), tavion0 = tavion, tavion1 = 0.0, tavion2 = tavion;

    for (int k = -mu; k <= mu; k++) {
        if (k == 0) continue;
        int idx = (k < 0) ? nt : 0;
        INM1(k) = I1(idx, k); INM2(k) = I1(idx, k); I3(k) = I1(idx, k);
    }

    /* Successive orders */
    int ig = 1;
    for (;;) {
        ig++;
        /* Build source function i2 from i1 */
        for (int k = 1; k <= mu; k++) {
            double xpk = XPL(k), ypk = XPL(-k);
            for (int i = 0; i <= nt; i++) {
                double ii1 = 0.0, ii2 = 0.0;
                double x = xdel[i], y = ydel[i];
                for (int j = 1; j <= mu; j++) {
                    double xpj = XPL(j), z = GB(j);
                    double xi1 = I1(i, j), xi2 = I1(i, -j);
                    double bpjk  = BP(j, k) * x + y * (beta0 + beta2 * xpj * xpk);
                    double bpjmk = BP(j, -k)* x + y * (beta0 + beta2 * xpj * ypk);
                    ii2 += z * (xi1 * bpjk  + xi2 * bpjmk);
                    ii1 += z * (xi1 * bpjmk + xi2 * bpjk);
                }
                I2(i,  k) = ii2;
                I2(i, -k) = ii1;
            }
        }

        /* Vertical integration upward */
        for (int k = 1; k <= mu; k++) {
            I1(nt, k) = 0.0;
            double zi1 = 0.0, yy = RM(k);
            for (int i = nt - 1; i >= 0; i--) {
                int jj = i + 1;
                double f = h[jj] - h[i];
                double a = (I2(jj,k) - I2(i,k)) / f;
                double b = I2(i,k) - a * h[i];
                double c = exp(-f / yy);
                double d = 1.0 - c;
                double xx = h[i] - h[jj] * c;
                zi1 = c * zi1 + (d * (b + a * yy) + a * xx) * 0.5;
                I1(i, k) = zi1;
            }
        }

        /* Vertical integration downward */
        for (int k = -mu; k <= -1; k++) {
            I1(0, k) = 0.0;
            double zi1 = 0.0, yy = RM(k);
            for (int i = 1; i <= nt; i++) {
                int jj = i - 1;
                double f = h[i] - h[jj];
                double c = exp(f / yy);
                double d = 1.0 - c;
                double a = (I2(i,k) - I2(jj,k)) / f;
                double b = I2(i,k) - a * h[i];
                double xx = h[i] - h[jj] * c;
                zi1 = c * zi1 + (d * (b + a * yy) + a * xx) * 0.5;
                I1(i, k) = zi1;
            }
        }

        /* Collect order n */
        for (int k = -mu; k <= mu; k++) {
            if (k == 0) continue;
            int idx = (k < 0) ? nt : 0;
            IN(k) = I1(idx, k);
        }
        tavion0 = I1(iplane, mu);

        /* Convergence test */
        if (ig > 2) {
            double z = 0.0;
            if (tavion2 >= accu && tavion1 >= accu && tavion >= accu) {
                double y = fabs(((tavion0/tavion1 - tavion1/tavion2) /
                                  ((1.0 - tavion0/tavion1) * (1.0 - tavion0/tavion1))) *
                                 (tavion0 / tavion));
                z = fmax(y, z);
            }
            for (int l = -mu; l <= mu; l++) {
                if (l == 0) continue;
                if (INM2(l) <= accu || INM1(l) <= accu || I3(l) <= accu) continue;
                double y = fabs(((IN(l)/INM1(l) - INM1(l)/INM2(l)) /
                                  ((1.0 - IN(l)/INM1(l)) * (1.0 - IN(l)/INM1(l)))) *
                                 (IN(l) / I3(l)));
                z = fmax(y, z);
            }
            if (z < 0.0001) {
                /* Geometric series acceleration */
                for (int l = -mu; l <= mu; l++) {
                    if (l == 0) continue;
                    if (INM1(l) == 0.0) continue;
                    double y1 = 1.0 - IN(l)/INM1(l);
                    double g1 = IN(l) / y1;
                    I3(l) += g1;
                }
                if (tavion1 >= accu && fabs(tavion0 - tavion1) >= accu) {
                    double y1 = 1.0 - tavion0/tavion1;
                    tavion += tavion0 / y1;
                }
                break;
            }
            for (int k = -mu; k <= mu; k++) INM2(k) = INM1(k);
            tavion2 = tavion1;
        }
        for (int k = -mu; k <= mu; k++) INM1(k) = IN(k);
        tavion1 = tavion0;
        for (int l = -mu; l <= mu; l++) I3(l) += IN(l);
        tavion += tavion0;

        /* Stop if order < 1e-5 of total */
        double z = 0.0;
        for (int l = -mu; l <= mu; l++) {
            if (l == 0) continue;
            if (I3(l) != 0.0) z = fmax(z, fabs(IN(l) / I3(l)));
        }
        if (z < 0.00001) break;
        if (ig >= igmax) break;
    }

    *xtrans_1  = (float)I3(mu);     /* downward diffuse (total atm) */
    *xtrans_m1 = (float)tavion;     /* upward at plane level */
    *xtrans_0  = 0.0f;
    for (int k = 1; k <= mu; k++) {
        *xtrans_0 += (float)(RM(k) * GB(k) * I3(-k));
    }

cleanup:
    #undef I1
    #undef I2
    #undef I3
    #undef IN
    #undef INM1
    #undef INM2
    #undef RM
    #undef GB
    #undef XPL
    #undef BP
    free(h); free(xdel); free(ydel); free(altc);
    free(i1); free(i2); free(i3); free(in_); free(inm1); free(inm2);
    free(xpl); free(psl); free(bp);
}
