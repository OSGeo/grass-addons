/* Atmospheric path reflectance — ported from 6SV2.1 OS.f
 * Successive Orders of Scattering with Fourier decomposition. */
#include "../include/sixs_ctx.h"
#include "discre.h"
#include "kernel.h"
#include <math.h>
#include <string.h>
#include <stdlib.h>

/**
 * \brief Compute atmospheric path reflectance via scalar successive orders of scattering.
 *
 * Solves the scalar (intensity-only) vector radiative transfer equation by
 * Fourier decomposition over azimuth and iterative successive orders, with
 * geometric-series acceleration when convergence is detected.
 *
 * The result is stored in \c xl[0] = R_atm × xmus (path reflectance × cos SZA).
 *
 * Ported from 6SV2.1 OS.f.
 *
 * \param[in,out] ctx       6SV context (reads polar.betal, del.delta, quad.nquad,
 *                          multi.igmax; writes ctx->err on error).
 * \param[in]     iaer_prof Aerosol profile type (0 = exponential; only value supported).
 * \param[in]     tamoy     Aerosol OD above the target (truncated).
 * \param[in]     trmoy     Rayleigh OD above the target.
 * \param[in]     pizmoy    Truncated single-scattering albedo.
 * \param[in]     tamoyp    Aerosol OD above the observer plane.
 * \param[in]     trmoyp    Rayleigh OD above the observer plane.
 * \param[in]     palt      Observer altitude in km (> 900 = satellite).
 * \param[in]     phirad    Relative azimuth angle in radians.
 * \param[in]     nt        Number of atmospheric integration levels.
 * \param[in]     mu        Gauss quadrature points per hemisphere.
 * \param[in]     np        Number of azimuth planes in \c xl.
 * \param[in]     nfi       Number of azimuth samples in \c xlphim.
 * \param[in]     rm_off    Gauss cosines, size 2mu+1 (offset by mu).
 * \param[in]     gb_off    Gauss weights, size 2mu+1 (offset by mu).
 * \param[in]     rp        Azimuth angles for the \c xl planes [np].
 * \param[out]    xl        Radiance array [(2mu+1)*np]; \c xl[0] = R_atm × xmus.
 * \param[out]    xlphim    Path reflectance as a function of azimuth [nfi].
 * \param[out]    rolut     Angular LUT reflectance [mu × 61]; may be NULL to skip.
 */
void sixs_os(SixsCtx *ctx, int iaer_prof,
             float tamoy, float trmoy, float pizmoy,
             float tamoyp, float trmoyp, float palt,
             float phirad, int nt, int mu, int np, int nfi,
             const float *rm_off, const float *gb_off, const float *rp,
             float *xl, float *xlphim, float *rolut)
{
    /* Local offset macros using function parameters */
    #undef RM
    #undef GB
    #define RM(j)   rm_off[(j)+mu]
    #define GB(j)   gb_off[(j)+mu]

    int snt = nt;   /* save to restore at end */

    double ta  = tamoy,  tr  = trmoy;
    double tap = tamoy - tamoyp, trp = trmoy - trmoyp;
    double piz = pizmoy;
    double hr  = 8.0, ha  = 2.0;
    int ntp    = nt, iplane = 0;
    double accu = 1e-20, accu2 = 1e-3;
    int mum1 = mu - 1;

    /* Plane observation: compute aerosol scale height */
    if (palt <= 900.0 && palt > 0.0) {
        ha  = (tap > 1e-3) ? -palt / log(tap / ta) : 2.0;
        ntp = nt - 1;
    }

    /* Allocate working arrays */
    int sz  = nt + 1;
    int dim = 2 * mu + 1;

    double *h    = (double*)calloc(sz, sizeof(double));
    double *ch   = (double*)calloc(sz, sizeof(double));
    double *xdel = (double*)calloc(sz, sizeof(double));
    double *ydel = (double*)calloc(sz, sizeof(double));
    double *altc = (double*)calloc(sz, sizeof(double));
    double *i1   = (double*)calloc((size_t)sz  * dim, sizeof(double));
    double *i2   = (double*)calloc((size_t)sz  * dim, sizeof(double));
    double *i3   = (double*)calloc(dim, sizeof(double));
    double *i4   = (double*)calloc(dim, sizeof(double));
    double *in_  = (double*)calloc(dim, sizeof(double));
    double *inm1 = (double*)calloc(dim, sizeof(double));
    double *inm2 = (double*)calloc(dim, sizeof(double));
    double *xpl  = (double*)calloc(dim, sizeof(double));
    int psl_rows = NQ_MAX + 2;
    double *psl  = (double*)calloc((size_t)psl_rows * dim, sizeof(double));
    double *bp   = (double*)calloc((size_t)(mu + 1) * dim, sizeof(double));

    /* LUT azimuth arrays (optional) */
    float  *filut  = rolut ? (float*)calloc((size_t)mu * 61, sizeof(float))  : NULL;
    int    *nfilut = rolut ? (int*)  calloc(mu, sizeof(int))                 : NULL;

    if (!h || !ch || !xdel || !ydel || !altc || !i1 || !i2 || !i3 || !i4 ||
        !in_ || !inm1 || !inm2 || !xpl || !psl || !bp)
        goto cleanup;

    /* Array accessors (negative-indexed via offset) */
    #define I1(k,j)    i1 [(size_t)(k)*dim + (j)+mu]
    #define I2(k,j)    i2 [(size_t)(k)*dim + (j)+mu]
    #define I3(j)      i3 [(j)+mu]
    #define I4(j)      i4 [(j)+mu]
    #define IN(j)      in_[(j)+mu]
    #define INM1(j)    inm1[(j)+mu]
    #define INM2(j)    inm2[(j)+mu]
    #define XPL(j)     xpl [(j)+mu]
    #define BP(j,k)    bp  [(j)*dim + (k)+mu]
    #define XL(m,l)    xl  [((m)+mu)*np + (l)]
    #define FILUT(i,j) filut [(i)*61 + (j)]
    #define ROLUT(i,j) rolut [(i)*61 + (j)]

    double xmus = -(double)RM(0);   /* solar cosine (rm(0) = -xmus) */

    /* ===== Layer grid setup ===== */
    if (ta <= accu2 && tr > ta) {
        /* Pure Rayleigh */
        for (int j = 0; j <= ntp; j++) {
            h[j]    = (double)j * tr / ntp;
            ch[j]   = exp(-h[j] / xmus) * 0.5;
            ydel[j] = 1.0; xdel[j] = 0.0;
            altc[j] = (j == 0) ? 300.0 : -log(h[j] / tr) * hr;
        }
    } else if (tr <= accu2 && ta > tr) {
        /* Pure aerosol */
        for (int j = 0; j <= ntp; j++) {
            h[j]    = (double)j * ta / ntp;
            ch[j]   = exp(-h[j] / xmus) * 0.5;
            ydel[j] = 0.0; xdel[j] = piz;
            altc[j] = (j == 0) ? 300.0 : -log(h[j] / ta) * ha;
        }
    } else {
        /* Mixed Rayleigh + aerosol: use discre bisection */
        ydel[0] = 1.0; xdel[0] = 0.0; h[0] = 0.0; ch[0] = 0.5; altc[0] = 300.0;
        double zx = 300.0;
        for (int it = 0; it <= ntp; it++) {
            double yy = (it > 0) ? h[it-1]    : 0.0;
            double dd = (it > 0) ? ydel[it-1] : 0.0;
            int itp   = it;
            sixs_discre(ctx, ta, ha, tr, hr, itp, ntp, yy, dd, 300.0, 0.0, &zx);
            if (ctx->err.ier) goto cleanup;
            double xxx = -zx / ha;
            double ca  = (xxx < -18.0) ? 0.0 : ta * exp(xxx);
            double cr  = tr * exp(-zx / hr);
            h[it]    = ca + cr;
            altc[it] = zx;
            ch[it]   = exp(-h[it] / xmus) * 0.5;
            cr /= hr; ca /= ha;
            double ratio = (cr + ca > 0.0) ? cr / (cr + ca) : 0.5;
            xdel[it] = (1.0 - ratio) * piz;
            ydel[it] = ratio;
        }
    }

    /* ===== Plane layer update ===== */
    if (ntp == nt - 1) {
        double taup = tap + trp;
        iplane = -1;
        for (int i = 0; i <= ntp; i++) if (taup >= h[i]) iplane = i;
        double th  = 0.0005;
        double xt1 = fabs(h[iplane]   - taup);
        double xt2 = fabs(h[iplane+1] - taup);
        if (xt1 > th && xt2 > th) {
            for (int i = nt; i >= iplane + 1; i--) {
                xdel[i] = xdel[i-1]; ydel[i] = ydel[i-1];
                h[i]    = h[i-1];    altc[i] = altc[i-1]; ch[i] = ch[i-1];
            }
        } else {
            nt = ntp;
            if (xt2 < xt1) iplane++;
        }
        h[iplane] = taup;
        if (tr > accu2 && ta > accu2) {
            double ca = ta * exp(-palt / ha), cr = tr * exp(-palt / hr);
            double hi = ca + cr;
            h[iplane]    = hi;
            ch[iplane]   = exp(-hi / xmus) * 0.5;
            cr /= hr; ca /= ha;
            double ratio  = cr / (cr + ca);
            xdel[iplane] = (1.0 - ratio) * piz;
            ydel[iplane] = ratio;
            altc[iplane] = palt;
        } else if (tr > accu2) {
            ydel[iplane] = 1.0; xdel[iplane] = 0.0; altc[iplane] = palt;
        } else {
            ydel[iplane] = 0.0; xdel[iplane] = piz; altc[iplane] = palt;
        }
    }

    /* ===== Initialize output arrays ===== */
    double pi  = acos(-1.0);
    for (int l = 0; l < np; l++)
        for (int m = -mu; m <= mu; m++) XL(m, l) = 0.0f;
    for (int ifi = 0; ifi < nfi; ifi++) xlphim[ifi] = 0.0f;

    /* LUT azimuth angle table */
    if (rolut && filut && nfilut) {
        double its_deg = acos(xmus) * 180.0 / pi;
        double sin_sza = sqrt(fmax(0.0, 1.0 - xmus * xmus));
        for (int m2 = 0; m2 < mu; m2++) {
            nfilut[m2] = 0;
            for (int j = 0; j < 61; j++) { FILUT(m2,j)=0.f; ROLUT(m2,j)=0.f; }
            double lutmuv = (double)RM(m2 + 1);
            double luttv  = acos(lutmuv) * 180.0 / pi;
            double iscama = 180.0 - fabs(luttv - its_deg);
            double iscami = 180.0 - (luttv + its_deg);
            int nbisca = (int)((iscama - iscami) / 4.0) + 1;
            if (nbisca > 61) nbisca = 61;
            if (nbisca < 1)  nbisca = 1;
            nfilut[m2] = nbisca;
            FILUT(m2, 0) = 0.0f;
            FILUT(m2, nbisca - 1) = 180.0f;
            double scaa    = iscama;
            double sin_vza = sqrt(fmax(0.0, 1.0 - lutmuv * lutmuv));
            for (int j = 1; j < nbisca - 1; j++) {
                scaa -= 4.0;
                double cscaa = cos(scaa * pi / 180.0);
                if (sin_sza < 1e-9 || sin_vza < 1e-9) { FILUT(m2,j)=0.f; continue; }
                double cfi = -(cscaa + xmus * lutmuv) / (sin_sza * sin_vza);
                cfi = fmax(-1.0, fmin(1.0, cfi));
                FILUT(m2, j) = (float)(acos(cfi) * 180.0 / pi);
            }
        }
    }

    /* ===== Rayleigh depolarization parameters ===== */
    double aaaa  = (double)ctx->del.delta / (2.0 - (double)ctx->del.delta);
    double ron   = (1.0 - aaaa) / (1.0 + 2.0 * aaaa);
    double beta0 = 1.0, beta2 = 0.5 * ron;

    /* i4 accumulates Fourier sum across all orders */
    for (int j = -mu; j <= mu; j++) I4(j) = 0.0;

    int iborm = ctx->quad.nquad - 3;
    if (fabs(xmus - 1.0) < 1e-6) iborm = 0;

    /* ===== Fourier decomposition loop: is = 0 .. iborm ===== */
    for (int is = 0; is <= iborm; is++) {
        int ig = 1;
        double roavion = 0.0, roavion0 = 0.0, roavion1 = 0.0, roavion2 = 0.0;
        for (int j = -mu; j <= mu; j++) I3(j) = 0.0;

        /* Reset beta0 for is > 0 (Rayleigh has no azimuthal component) */
        if (is > 0) beta0 = 0.0;

        /* Kernel for this Fourier order */
        sixs_kernel(ctx, is, mu, rm_off, xpl, psl, bp);

        /* Primary scattering source: i2(k,j) = ch[k]*(sa2*xdel[k]+sa1*ydel[k]) */
        for (int j = -mu; j <= mu; j++) {
            double spl = XPL(0);
            double sa1, sa2;
            if (is <= 2) {
                sa1 = beta0 + beta2 * XPL(j) * spl;
                sa2 = BP(0, j);
            } else {
                sa1 = 0.0;
                sa2 = BP(0, j);
            }
            for (int k = 0; k <= nt; k++)
                I2(k, j) = ch[k] * (sa2 * xdel[k] + sa1 * ydel[k]);
        }

        /* Vertical integration, primary upward (k = 1..mu) */
        for (int k = 1; k <= mu; k++) {
            I1(nt, k) = 0.0;
            double zi1 = 0.0, yy = (double)RM(k);
            for (int i = nt - 1; i >= 0; i--) {
                int jj = i + 1;
                double f  = h[jj] - h[i];
                double a  = (I2(jj,k) - I2(i,k)) / f;
                double b  = I2(i,k) - a * h[i];
                double c  = exp(-f / yy);
                double d  = 1.0 - c;
                double xx = h[i] - h[jj] * c;
                zi1 = c * zi1 + (d * (b + a * yy) + a * xx) * 0.5;
                I1(i, k) = zi1;
            }
        }

        /* Vertical integration, primary downward (k = -mu..-1) */
        for (int k = -mu; k <= -1; k++) {
            I1(0, k) = 0.0;
            double zi1 = 0.0, yy = (double)RM(k);
            for (int i = 1; i <= nt; i++) {
                int jj = i - 1;
                double f  = h[i] - h[jj];
                double c  = exp(f / yy);
                double d  = 1.0 - c;
                double a  = (I2(i,k) - I2(jj,k)) / f;
                double b  = I2(i,k) - a * h[i];
                double xx = h[i] - h[jj] * c;
                zi1 = c * zi1 + (d * (b + a * yy) + a * xx) * 0.5;
                I1(i, k) = zi1;
            }
        }

        /* Collect primary scattering: inm2 = inm1 = i3 = i1 at boundaries */
        for (int k = -mu; k <= mu; k++) {
            if (k == 0) continue;
            int idx = (k < 0) ? nt : 0;
            INM1(k) = I1(idx, k);
            INM2(k) = I1(idx, k);
            I3(k)   = I1(idx, k);
        }
        roavion2 = I1(iplane, mu);
        roavion  = I1(iplane, mu);

        /* ---- Successive Orders of Scattering ---- */
        for (;;) {
            ig++;

            /* Build source function from previous i1 */
            if (is <= 2) {
                /* Mixed Rayleigh + aerosol kernel */
                for (int k = 1; k <= mu; k++) {
                    double xpk = XPL(k), ypk = XPL(-k);
                    for (int i = 0; i <= nt; i++) {
                        double ii1 = 0.0, ii2 = 0.0;
                        double x = xdel[i], y = ydel[i];
                        for (int j = 1; j <= mu; j++) {
                            double xpj  = XPL(j), z = (double)GB(j);
                            double xi1  = I1(i,  j), xi2 = I1(i, -j);
                            double bpjk  = BP(j,  k) * x + y * (beta0 + beta2 * xpj * xpk);
                            double bpjmk = BP(j, -k) * x + y * (beta0 + beta2 * xpj * ypk);
                            ii2 += z * (xi1 * bpjk  + xi2 * bpjmk);
                            ii1 += z * (xi1 * bpjmk + xi2 * bpjk);
                        }
                        if (fabs(ii2) < 1e-30) ii2 = 0.0;
                        if (fabs(ii1) < 1e-30) ii1 = 0.0;
                        I2(i,  k) = ii2;
                        I2(i, -k) = ii1;
                    }
                }
            } else {
                /* Aerosol-only kernel (is > 2, no Rayleigh term) */
                for (int k = 1; k <= mu; k++) {
                    for (int i = 0; i <= nt; i++) {
                        double ii1 = 0.0, ii2 = 0.0;
                        double x = xdel[i];
                        for (int j = 1; j <= mu; j++) {
                            double z    = (double)GB(j);
                            double xi1  = I1(i,  j), xi2 = I1(i, -j);
                            double bpjk  = BP(j,  k) * x;
                            double bpjmk = BP(j, -k) * x;
                            ii2 += z * (xi1 * bpjk  + xi2 * bpjmk);
                            ii1 += z * (xi1 * bpjmk + xi2 * bpjk);
                        }
                        if (fabs(ii2) < 1e-30) ii2 = 0.0;
                        if (fabs(ii1) < 1e-30) ii1 = 0.0;
                        I2(i,  k) = ii2;
                        I2(i, -k) = ii1;
                    }
                }
            }

            /* Vertical integration upward */
            for (int k = 1; k <= mu; k++) {
                I1(nt, k) = 0.0;
                double zi1 = 0.0, yy = (double)RM(k);
                for (int i = nt - 1; i >= 0; i--) {
                    int jj = i + 1;
                    double f  = h[jj] - h[i];
                    double a  = (I2(jj,k) - I2(i,k)) / f;
                    double b  = I2(i,k) - a * h[i];
                    double c  = exp(-f / yy);
                    double d  = 1.0 - c;
                    double xx = h[i] - h[jj] * c;
                    zi1 = c * zi1 + (d * (b + a * yy) + a * xx) * 0.5;
                    if (fabs(zi1) < 1e-20) zi1 = 0.0;
                    I1(i, k) = zi1;
                }
            }

            /* Vertical integration downward */
            for (int k = -mu; k <= -1; k++) {
                I1(0, k) = 0.0;
                double zi1 = 0.0, yy = (double)RM(k);
                for (int i = 1; i <= nt; i++) {
                    int jj = i - 1;
                    double f  = h[i] - h[jj];
                    double c  = exp(f / yy);
                    double d  = 1.0 - c;
                    double a  = (I2(i,k) - I2(jj,k)) / f;
                    double b  = I2(i,k) - a * h[i];
                    double xx = h[i] - h[jj] * c;
                    zi1 = c * zi1 + (d * (b + a * yy) + a * xx) * 0.5;
                    if (fabs(zi1) < 1e-20) zi1 = 0.0;
                    I1(i, k) = zi1;
                }
            }

            /* Collect scattering order n */
            for (int k = -mu; k <= mu; k++) {
                if (k == 0) continue;
                IN(k) = I1((k < 0) ? nt : 0, k);
            }
            roavion0 = I1(iplane, mu);

            /* Geometric series convergence test */
            if (ig > 2) {
                double z = 0.0;
                if (roavion2 >= accu && roavion1 >= accu && roavion >= accu) {
                    double r = roavion0 / roavion1;
                    double y = fabs(((r - roavion1/roavion2) /
                                     ((1.0 - r) * (1.0 - r))) *
                                    (roavion0 / roavion));
                    z = fmax(y, z);
                }
                for (int l = -mu; l <= mu; l++) {
                    if (l == 0) continue;
                    if (INM2(l) <= accu || INM1(l) <= accu || I3(l) <= accu) continue;
                    double r = IN(l) / INM1(l);
                    double y = fabs(((r - INM1(l)/INM2(l)) /
                                     ((1.0 - r) * (1.0 - r))) *
                                    (IN(l) / I3(l)));
                    z = fmax(y, z);
                }
                if (z < 0.0001) {
                    /* Apply geometric series acceleration */
                    for (int l = -mu; l <= mu; l++) {
                        if (l == 0) continue;
                        double d1 = INM1(l), g1 = IN(l);
                        if (d1 <= accu || fabs(g1 - d1) <= accu) continue;
                        I3(l) += g1 / (1.0 - g1 / d1);
                    }
                    if (roavion1 >= accu && fabs(roavion0 - roavion1) >= accu)
                        roavion += roavion0 / (1.0 - roavion0 / roavion1);
                    goto done_sos;
                }
                for (int k = -mu; k <= mu; k++) INM2(k) = INM1(k);
                roavion2 = roavion1;
            }

            for (int k = -mu; k <= mu; k++) INM1(k) = IN(k);
            roavion1 = roavion0;
            for (int l = -mu; l <= mu; l++) I3(l) += IN(l);
            roavion += roavion0;

            /* Relative convergence: stop if last order < 1e-5 of sum */
            {
                double z = 0.0;
                for (int l = -mu; l <= mu; l++) {
                    if (l == 0 || fabs(I3(l)) < accu) continue;
                    z = fmax(z, fabs(IN(l) / I3(l)));
                }
                if (z < 1e-5) goto done_sos;
            }
            if (ig >= ctx->multi.igmax) goto done_sos;
        } /* end SOS loop */
    done_sos:;

        /* ---- Accumulate this Fourier component ---- */
        double delta0s = (is == 0) ? 1.0 : 2.0;
        for (int l = -mu; l <= mu; l++) I4(l) += delta0s * I3(l);

        /* xl: radiance field at each azimuth plane */
        for (int l_idx = 0; l_idx < np; l_idx++) {
            double phi_l = (double)rp[l_idx];
            for (int m = -mum1; m <= mum1; m++) {
                double cosfac = (m > 0) ? cos(is * (phi_l + pi)) : cos(is * phi_l);
                XL(m, l_idx) += (float)(delta0s * I3(m) * cosfac);
            }
        }

        /* xl(mu, 1): upward at specific view direction */
        XL(mu, 0) += (float)(delta0s * I3(mu) * cos(is * (phirad + pi)));

        /* xl(-mu, 1): atmospheric path reflectance (×xmus) */
        XL(-mu, 0) += (float)(delta0s * roavion * cos(is * (phirad + pi)));

        /* xl(0, 1): downward flux at surface (is=0 only) */
        if (is == 0) {
            for (int k = 1; k <= mum1; k++)
                XL(0, 0) += (float)((double)RM(k) * (double)GB(k) * I3(-k));
        }

        /* xlphim: path reflectance vs azimuth angle */
        for (int ifi = 0; ifi < nfi; ifi++) {
            double phimul = (double)ifi * pi / (double)(nfi - 1);
            xlphim[ifi] += (float)(delta0s * roavion * cos(is * (phimul + pi)));
        }

        /* LUT angular table */
        if (rolut && filut && nfilut) {
            for (int m2 = 0; m2 < mu; m2++) {
                for (int l2 = 0; l2 < nfilut[m2]; l2++) {
                    double phimul = (double)FILUT(m2, l2) * pi / 180.0;
                    ROLUT(m2, l2) += (float)(delta0s * I3(m2 + 1) *
                                             cos(is * (phimul + pi)));
                }
            }
        }

        /* Fourier convergence: exit early if last term < 0.1% of sum */
        {
            double z = 0.0;
            for (int l = -mu; l <= mu; l++) {
                if (fabs(I4(l)) < accu) continue;
                z = fmax(z, fabs(I3(l) / I4(l)));
            }
            if (z <= 0.001) break;
        }
    } /* end Fourier loop */

    nt = snt;  /* restore nt */

cleanup:
    #undef RM
    #undef GB
    #undef I1
    #undef I2
    #undef I3
    #undef I4
    #undef IN
    #undef INM1
    #undef INM2
    #undef XPL
    #undef BP
    #undef XL
    #undef FILUT
    #undef ROLUT
    free(h); free(ch); free(xdel); free(ydel); free(altc);
    free(i1); free(i2); free(i3); free(i4); free(in_); free(inm1); free(inm2);
    free(xpl); free(psl); free(bp);
    free(filut); free(nfilut);
}
