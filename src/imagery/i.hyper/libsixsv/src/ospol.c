/**
 * \file ospol.c
 * \brief Vector (Stokes I,Q,U) successive-orders radiative transfer.
 *
 * Extends the scalar solver sixs_os() to propagate the full Stokes vector
 * \f$(I, Q, U)\f$ through the atmosphere.
 *
 * The dominant physical improvement over the scalar version is Rayleigh
 * polarisation feedback: solar intensity generates \f$Q\f$ and \f$U\f$ via
 * the anisotropy factor \f$\gamma^2\f$, and multiply-scattered \f$Q/U\f$
 * feed back into \f$I\f$, improving R_atm accuracy by 1–5% in blue bands.
 *
 * \par Aerosol simplification:
 * \f$\gamma_l = \zeta_l = 0\f$, \f$\alpha_l = \beta_l\f$ (spherical particles).
 * The off-diagonal Müller matrix blocks \f$g_r, g_t\f$ vanish for aerosol.
 *
 * Memory: six \f$(n_t+1)\times(2\mu+1)\f$ double arrays (3 Stokes × 2 sweeps)
 * — roughly 3× the scalar memory footprint. All temporary arrays are
 * heap-allocated and freed on return.
 *
 * Ported from 6SV2.1 OSPOL.f.
 */

#include "ospol.h"
#include "kernelpol.h"
#include "discre.h"
#include <math.h>
#include <string.h>
#include <stdlib.h>

/**
 * \brief Compute atmospheric path reflectance and polarisation via vector successive orders.
 *
 * Propagates the three Stokes components \f$(I, Q, U)\f$ simultaneously using
 * Fourier decomposition over azimuth and iterative successive orders with
 * geometric-series convergence acceleration.
 *
 * On return:
 * - \c xl[0] contains \f$I \cdot \cos\theta_s\f$ (total path reflectance × cos SZA),
 * - \c xlq[0] and \c xlu[0] contain the corresponding \f$Q\f$ and \f$U\f$ components.
 *
 * Ported from 6SV2.1 OSPOL.f.
 *
 * \param[in,out] ctx       6SV context (reads polar.betal, del.delta; writes err).
 * \param[in]     iaer_prof Aerosol profile type (0 = exponential; only value supported).
 * \param[in]     tamoy     Aerosol OD above the target.
 * \param[in]     trmoy     Rayleigh OD above the target.
 * \param[in]     pizmoy    Single-scattering albedo.
 * \param[in]     tamoyp    Aerosol OD above the observer plane.
 * \param[in]     trmoyp    Rayleigh OD above the observer plane.
 * \param[in]     palt      Observer altitude in km (> 900 = satellite).
 * \param[in]     phirad    Relative azimuth angle in radians.
 * \param[in]     nt        Number of atmospheric integration levels.
 * \param[in]     mu        Gauss quadrature points per hemisphere.
 * \param[in]     np        Number of azimuth planes in the output arrays.
 * \param[in]     nfi       Number of azimuth samples in \c xlphim.
 * \param[in]     rm_off    Gauss cosines, size 2mu+1 (offset by mu).
 * \param[in]     gb_off    Gauss weights, size 2mu+1 (offset by mu).
 * \param[in]     rp        Azimuth angles for the output planes [np].
 * \param[out]    xl        Stokes-I radiance [(2mu+1)*np]; \c xl[0] = I × cos SZA.
 * \param[out]    xlq       Stokes-Q radiance [(2mu+1)*np].
 * \param[out]    xlu       Stokes-U radiance [(2mu+1)*np].
 * \param[out]    xlphim    Total intensity path reflectance vs. azimuth [nfi].
 */
void sixs_ospol(SixsCtx *ctx, int iaer_prof,
                float tamoy, float trmoy, float pizmoy,
                float tamoyp, float trmoyp, float palt,
                float phirad, int nt, int mu, int np, int nfi,
                const float *rm_off, const float *gb_off, const float *rp,
                float *xl, float *xlq, float *xlu, float *xlphim)
{
    (void)iaer_prof;   /* exponential profile only */

    #undef RM
    #undef GB
    #define RM(j)    rm_off[(j)+mu]
    #define GB(j)    gb_off[(j)+mu]

    int snt = nt;

    double ta  = tamoy,  tr  = trmoy;
    double tap = tamoy - tamoyp, trp = trmoy - trmoyp;
    double piz = pizmoy;
    double hr  = 8.0,  ha  = 2.0;
    int ntp    = nt, iplane = 0;
    double accu  = 1e-20, accu2 = 1e-3;
    int mum1 = mu - 1;

    if (palt <= 900.0 && palt > 0.0) {
        ha  = (tap > 1e-3) ? -palt / log(tap / ta) : 2.0;
        ntp = nt - 1;
    }

    int sz  = nt + 1;
    int dim = 2 * mu + 1;

    /* Layer-profile arrays */
    double *h    = (double*)calloc(sz, sizeof(double));
    double *ch   = (double*)calloc(sz, sizeof(double));
    double *xdel = (double*)calloc(sz, sizeof(double));
    double *ydel = (double*)calloc(sz, sizeof(double));
    double *altc = (double*)calloc(sz, sizeof(double));

    /* Stokes I working arrays */
    double *i1   = (double*)calloc((size_t)sz  * dim, sizeof(double));
    double *i2   = (double*)calloc((size_t)sz  * dim, sizeof(double));
    double *i3   = (double*)calloc(dim, sizeof(double));
    double *i4   = (double*)calloc(dim, sizeof(double));
    double *in_  = (double*)calloc(dim, sizeof(double));
    double *inm1 = (double*)calloc(dim, sizeof(double));
    double *inm2 = (double*)calloc(dim, sizeof(double));

    /* Stokes Q working arrays */
    double *q1   = (double*)calloc((size_t)sz  * dim, sizeof(double));
    double *q2   = (double*)calloc((size_t)sz  * dim, sizeof(double));
    double *q3   = (double*)calloc(dim, sizeof(double));
    double *q4   = (double*)calloc(dim, sizeof(double));
    double *qn   = (double*)calloc(dim, sizeof(double));
    double *qnm1 = (double*)calloc(dim, sizeof(double));
    double *qnm2 = (double*)calloc(dim, sizeof(double));

    /* Stokes U working arrays */
    double *u1   = (double*)calloc((size_t)sz  * dim, sizeof(double));
    double *u2   = (double*)calloc((size_t)sz  * dim, sizeof(double));
    double *u3   = (double*)calloc(dim, sizeof(double));
    double *u4   = (double*)calloc(dim, sizeof(double));
    double *un   = (double*)calloc(dim, sizeof(double));
    double *unm1 = (double*)calloc(dim, sizeof(double));
    double *unm2 = (double*)calloc(dim, sizeof(double));

    /* Kernel matrices */
    int psl_rows = NQ_MAX + 2;
    double *xpl  = (double*)calloc(dim, sizeof(double));
    double *xrl  = (double*)calloc(dim, sizeof(double));
    double *xtl  = (double*)calloc(dim, sizeof(double));
    double *psl  = (double*)calloc((size_t)psl_rows * dim, sizeof(double));
    double *rsl  = (double*)calloc((size_t)psl_rows * dim, sizeof(double));
    double *tsl  = (double*)calloc((size_t)psl_rows * dim, sizeof(double));
    double *bp   = (double*)calloc((size_t)(mu + 1) * dim, sizeof(double));
    double *arr  = (double*)calloc((size_t)(mu + 1) * dim, sizeof(double));
    double *art  = (double*)calloc((size_t)(mu + 1) * dim, sizeof(double));
    double *att  = (double*)calloc((size_t)(mu + 1) * dim, sizeof(double));

    if (!h || !ch || !xdel || !ydel || !altc ||
        !i1 || !i2 || !i3 || !i4 || !in_  || !inm1 || !inm2 ||
        !q1 || !q2 || !q3 || !q4 || !qn   || !qnm1 || !qnm2 ||
        !u1 || !u2 || !u3 || !u4 || !un   || !unm1 || !unm2 ||
        !xpl || !xrl || !xtl || !psl || !rsl || !tsl ||
        !bp  || !arr || !art || !att)
        goto cleanup;

    /* Array accessors (negative-indexed via offset) */
    #define I1(k,j)  i1[(size_t)(k)*dim + (j)+mu]
    #define I2(k,j)  i2[(size_t)(k)*dim + (j)+mu]
    #define I3(j)    i3[(j)+mu]
    #define I4(j)    i4[(j)+mu]
    #define IN(j)    in_[(j)+mu]
    #define INM1(j)  inm1[(j)+mu]
    #define INM2(j)  inm2[(j)+mu]
    #define Q1(k,j)  q1[(size_t)(k)*dim + (j)+mu]
    #define Q2(k,j)  q2[(size_t)(k)*dim + (j)+mu]
    #define Q3(j)    q3[(j)+mu]
    #define Q4(j)    q4[(j)+mu]
    #define QN(j)    qn[(j)+mu]
    #define QNM1(j)  qnm1[(j)+mu]
    #define QNM2(j)  qnm2[(j)+mu]
    #define U1(k,j)  u1[(size_t)(k)*dim + (j)+mu]
    #define U2(k,j)  u2[(size_t)(k)*dim + (j)+mu]
    #define U3(j)    u3[(j)+mu]
    #define U4(j)    u4[(j)+mu]
    #define UN(j)    un[(j)+mu]
    #define UNM1(j)  unm1[(j)+mu]
    #define UNM2(j)  unm2[(j)+mu]
    #define XPL(j)   xpl[(j)+mu]
    #define XRL(j)   xrl[(j)+mu]
    #define XTL(j)   xtl[(j)+mu]
    #define BP(j,k)  bp [(j)*dim + (k)+mu]
    #define ARR(j,k) arr[(j)*dim + (k)+mu]
    #define ART(j,k) art[(j)*dim + (k)+mu]
    #define ATT(j,k) att[(j)*dim + (k)+mu]
    #define XL(m,l)  xl [((m)+mu)*np + (l)]

    double xmus = -(double)RM(0);

    /* ── Layer grid setup (identical to sixs_os) ── */
    if (ta <= accu2 && tr > ta) {
        for (int j = 0; j <= ntp; j++) {
            h[j]    = (double)j * tr / ntp;
            ch[j]   = exp(-h[j] / xmus) * 0.5;
            ydel[j] = 1.0;  xdel[j] = 0.0;
            altc[j] = (j == 0) ? 300.0 : -log(h[j] / tr) * hr;
        }
    } else if (tr <= accu2 && ta > tr) {
        for (int j = 0; j <= ntp; j++) {
            h[j]    = (double)j * ta / ntp;
            ch[j]   = exp(-h[j] / xmus) * 0.5;
            ydel[j] = 0.0;  xdel[j] = piz;
            altc[j] = (j == 0) ? 300.0 : -log(h[j] / ta) * ha;
        }
    } else {
        ydel[0] = 1.0;  xdel[0] = 0.0;  h[0] = 0.0;
        ch[0]   = 0.5;  altc[0] = 300.0;
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
            cr /= hr;  ca /= ha;
            double ratio = (cr + ca > 0.0) ? cr / (cr + ca) : 0.5;
            xdel[it] = (1.0 - ratio) * piz;
            ydel[it] = ratio;
        }
    }

    /* ── Plane layer update ── */
    if (ntp == nt - 1) {
        double taup = tap + trp;
        iplane = -1;
        for (int i = 0; i <= ntp; i++) if (taup >= h[i]) iplane = i;
        double th  = 0.0005;
        double xt1 = fabs(h[iplane]   - taup);
        double xt2 = fabs(h[iplane+1] - taup);
        if (xt1 > th && xt2 > th) {
            for (int i = nt; i >= iplane + 1; i--) {
                xdel[i] = xdel[i-1];  ydel[i] = ydel[i-1];
                h[i]    = h[i-1];     altc[i] = altc[i-1];  ch[i] = ch[i-1];
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
            cr /= hr;  ca /= ha;
            double ratio  = cr / (cr + ca);
            xdel[iplane] = (1.0 - ratio) * piz;
            ydel[iplane] = ratio;
            altc[iplane] = palt;
        } else if (tr > accu2) {
            ydel[iplane] = 1.0;  xdel[iplane] = 0.0;  altc[iplane] = palt;
        } else {
            ydel[iplane] = 0.0;  xdel[iplane] = piz;   altc[iplane] = palt;
        }
    }

    /* ── Initialise output arrays ── */
    double pi = acos(-1.0);
    for (int l = 0; l < np; l++)
        for (int m = -mu; m <= mu; m++) {
            XL(m, l) = 0.0f;
            if (xlq) xlq[((m)+mu)*np + l] = 0.0f;
            if (xlu) xlu[((m)+mu)*np + l] = 0.0f;
        }
    for (int ifi = 0; ifi < nfi; ifi++) xlphim[ifi] = 0.0f;

    /* ── Rayleigh depolarisation parameters ── */
    double aaaa   = (double)ctx->del.delta / (2.0 - (double)ctx->del.delta);
    double ron    = (1.0 - aaaa) / (1.0 + 2.0 * aaaa);
    double beta0  = 1.0;
    double beta2  = 0.5 * ron;
    double gamma2 = -ron * sqrt(1.5);   /* Rayleigh I→Q coupling */
    double alpha2 = 3.0 * ron;          /* Rayleigh Q→Q strength */

    for (int j = -mu; j <= mu; j++) {
        I4(j) = 0.0;  Q4(j) = 0.0;  U4(j) = 0.0;
    }

    int iborm = ctx->quad.nquad - 3;
    if (fabs(xmus - 1.0) < 1e-6) iborm = 0;

    /* ══ Fourier decomposition loop ══════════════════════════════════════ */
    for (int is = 0; is <= iborm; is++) {

        int ig = 1;
        /* roIavion etc.: path reflectance × xmus at observer plane */
        double roI = 0.0, roI0 = 0.0, roI1 = 0.0, roI2 = 0.0;
        double roQ = 0.0, roQ0 = 0.0, roQ1 = 0.0, roQ2 = 0.0;
        double roU = 0.0, roU0 = 0.0, roU1 = 0.0, roU2 = 0.0;

        for (int j = -mu; j <= mu; j++) {
            I3(j) = 0.0;  Q3(j) = 0.0;  U3(j) = 0.0;
        }

        double beta0_is = (is > 0) ? 0.0 : beta0;

        /* Polarised kernel for this Fourier order */
        sixs_kernelpol(ctx, is, mu, rm_off,
                       xpl, xrl, xtl, psl, rsl, tsl,
                       bp, arr, art, att);

        /* ── Primary scattering source functions ── */
        double spl = XPL(0);   /* xpl[0] = psl[2][0] */
        double srl = XRL(0);   /* xrl[0] = rsl[2][0] */
        double stl = XTL(0);   /* xtl[0] = tsl[2][0] */
        (void)srl; (void)stl;  /* Only spl enters the primary term */

        for (int j = -mu; j <= mu; j++) {
            double sa1, sa2, sb1, sb2, sc1, sc2;
            if (is <= 2) {
                sa1 = beta0_is + beta2 * XPL(j) * spl;  /* Rayleigh I from I */
                sa2 = BP(0, j);                           /* aerosol I from I */
                sb1 = gamma2 * XRL(j) * spl;             /* Rayleigh Q from I */
                sb2 = 0.0;                                /* gr(0,j) = 0 */
                sc1 = gamma2 * XTL(j) * spl;             /* Rayleigh U from I */
                sc2 = 0.0;                                /* gt(0,j) = 0 */
            } else {
                sa1 = 0.0;  sa2 = BP(0, j);
                sb1 = 0.0;  sb2 = 0.0;
                sc1 = 0.0;  sc2 = 0.0;
            }
            for (int k = 0; k <= nt; k++) {
                double c = ch[k];
                double a = ydel[k];
                double b = xdel[k];
                I2(k, j) =  c * (sa2 * b + sa1 * a);
                Q2(k, j) =  c * (sb2 * b + sb1 * a);
                U2(k, j) = -c * (sc2 * b + sc1 * a);   /* minus sign per OSPOL.f */
            }
        }

        /* ── Vertical integration, primary upward (k = 1..mu) ── */
        for (int k = 1; k <= mu; k++) {
            I1(nt,k) = Q1(nt,k) = U1(nt,k) = 0.0;
            double zi1 = 0.0, zq1 = 0.0, zu1 = 0.0;
            double yy = (double)RM(k);
            for (int i = nt - 1; i >= 0; i--) {
                int jj = i + 1;
                double f = h[jj] - h[i];
                double c = exp(-f / yy), d = 1.0 - c, xx = h[i] - h[jj]*c;
                #define VERT_INT_UP(Z, v2, v1, k_idx) \
                    { double _a = (v2(jj,k_idx) - v2(i,k_idx)) / f; \
                      double _b = v2(i,k_idx) - _a * h[i]; \
                      Z = c*Z + (d*(_b + _a*yy) + _a*xx) * 0.5; \
                      v1(i,k_idx) = Z; }
                VERT_INT_UP(zi1, I2, I1, k)
                VERT_INT_UP(zq1, Q2, Q1, k)
                VERT_INT_UP(zu1, U2, U1, k)
                #undef VERT_INT_UP
            }
        }

        /* ── Vertical integration, primary downward (k = -mu..-1) ── */
        for (int k = -mu; k <= -1; k++) {
            I1(0,k) = Q1(0,k) = U1(0,k) = 0.0;
            double zi1 = 0.0, zq1 = 0.0, zu1 = 0.0;
            double yy = (double)RM(k);
            for (int i = 1; i <= nt; i++) {
                int jj = i - 1;
                double f = h[i] - h[jj];
                double c = exp(f / yy), d = 1.0 - c, xx = h[i] - h[jj]*c;
                #define VERT_INT_DN(Z, v2, v1, k_idx) \
                    { double _a = (v2(i,k_idx) - v2(jj,k_idx)) / f; \
                      double _b = v2(i,k_idx) - _a * h[i]; \
                      Z = c*Z + (d*(_b + _a*yy) + _a*xx) * 0.5; \
                      v1(i,k_idx) = Z; }
                VERT_INT_DN(zi1, I2, I1, k)
                VERT_INT_DN(zq1, Q2, Q1, k)
                VERT_INT_DN(zu1, U2, U1, k)
                #undef VERT_INT_DN
            }
        }

        /* ── Collect primary scattering ── */
        for (int k = -mu; k <= mu; k++) {
            if (k == 0) continue;
            int idx = (k < 0) ? nt : 0;
            INM1(k) = INM2(k) = I3(k) = I1(idx, k);
            QNM1(k) = QNM2(k) = Q3(k) = Q1(idx, k);
            UNM1(k) = UNM2(k) = U3(k) = U1(idx, k);
        }
        roI2 = roI = I1(iplane, mu);
        roQ2 = roQ = Q1(iplane, mu);
        roU2 = roU = U1(iplane, mu);

        /* ════ Successive Orders of Scattering ════════════════════════════ */
        for (;;) {
            ig++;

            /* ── Build source functions for next order ── */
            if (is <= 2) {
                /* Mixed Rayleigh + aerosol */
                for (int k = 1; k <= mu; k++) {
                    double xpk = XPL( k), ypk = XPL(-k);
                    double xrk = XRL( k), yrk = XRL(-k);
                    double xtk = XTL( k), ytk = XTL(-k);
                    for (int i = 0; i <= nt; i++) {
                        double ii1 = 0.0, ii2 = 0.0;
                        double qq1 = 0.0, qq2 = 0.0;
                        double uu1 = 0.0, uu2 = 0.0;
                        double x = xdel[i], y = ydel[i];
                        for (int j = 1; j <= mu; j++) {
                            double z   = (double)GB(j);
                            double xpj = XPL( j);
                            double xrj = XRL( j), yrj = XRL(-j);
                            double xtj = XTL( j), ytj = XTL(-j);
                            double xi1 = I1(i, j), xi2 = I1(i, -j);
                            double xq1 = Q1(i, j), xq2 = Q1(i, -j);
                            double xu1 = U1(i, j), xu2 = U1(i, -j);

                            /* Combined (aerosol×x + Rayleigh×y) kernels */
                            double bpjk   = BP(j, k)*x  + y*(beta0_is + beta2*xpj*xpk);
                            double bpjmk  = BP(j,-k)*x  + y*(beta0_is + beta2*xpj*ypk);
                            /* I→Q and Q→I Rayleigh coupling (gr=0 for aerosol) */
                            double grjk   = y * gamma2 * xpj * xrk;
                            double grjmk  = y * gamma2 * xpj * yrk;
                            double grkj   = y * gamma2 * xpk * xrj;
                            double grkmj  = y * gamma2 * xpk * yrj;
                            /* I→U and U→I Rayleigh coupling (gt=0 for aerosol) */
                            double gtjk   = y * gamma2 * xpj * xtk;
                            double gtjmk  = y * gamma2 * xpj * ytk;
                            double gtkj   = y * gamma2 * xpk * xtj;
                            double gtkmj  = y * gamma2 * xpk * ytj;
                            /* Q↔Q and U↔U (aerosol arr/att + Rayleigh alpha2) */
                            double arrjk  = ARR(j, k)*x + y * alpha2 * xrj * xrk;
                            double arrjmk = ARR(j,-k)*x + y * alpha2 * xrj * yrk;
                            double artjk  = ART(j, k)*x + y * alpha2 * xtj * xrk;
                            double artjmk = ART(j,-k)*x + y * alpha2 * xtj * yrk;
                            double artkj  = ART(k, j)*x + y * alpha2 * xtk * xrj;
                            double artkmj = ART(k,-j)*x + y * alpha2 * xtk * yrj;
                            double attjk  = ATT(j, k)*x + y * alpha2 * xtj * xtk;
                            double attjmk = ATT(j,-k)*x + y * alpha2 * xtj * ytk;

                            /* I source */
                            double xdb;
                            xdb = xi1*bpjk + xi2*bpjmk + xq1*grkj  + xq2*grkmj
                                - xu1*gtkj - xu2*gtkmj;
                            ii2 += xdb * z;
                            xdb = xi1*bpjmk + xi2*bpjk + xq1*grkmj + xq2*grkj
                                + xu1*gtkmj + xu2*gtkj;
                            ii1 += xdb * z;

                            /* Q source */
                            xdb = xi1*grjk  + xi2*grjmk  + xq1*arrjk  + xq2*arrjmk
                                - xu1*artjk + xu2*artjmk;
                            qq2 += xdb * z;
                            xdb = xi1*grjmk + xi2*grjk   + xq1*arrjmk + xq2*arrjk
                                - xu1*artjmk + xu2*artjk;
                            qq1 += xdb * z;

                            /* U source  (minus sign per OSPOL.f) */
                            xdb = xi1*gtjk  - xi2*gtjmk  + xq1*artkj  + xq2*artkmj
                                - xu1*attjk - xu2*attjmk;
                            uu2 -= xdb * z;
                            xdb = xi1*gtjmk - xi2*gtjk   - xq1*artkmj - xq2*artkj
                                - xu1*attjmk - xu2*attjk;
                            uu1 -= xdb * z;
                        }
                        if (fabs(ii2) < 1e-30) ii2 = 0.0;
                        if (fabs(ii1) < 1e-30) ii1 = 0.0;
                        if (fabs(qq2) < 1e-30) qq2 = 0.0;
                        if (fabs(qq1) < 1e-30) qq1 = 0.0;
                        if (fabs(uu2) < 1e-30) uu2 = 0.0;
                        if (fabs(uu1) < 1e-30) uu1 = 0.0;
                        I2(i,  k) = ii2;  I2(i, -k) = ii1;
                        Q2(i,  k) = qq2;  Q2(i, -k) = qq1;
                        U2(i,  k) = uu2;  U2(i, -k) = uu1;
                    }
                }
            } else {
                /* Aerosol-only: no Rayleigh coupling, arr/att/art only */
                for (int k = 1; k <= mu; k++) {
                    for (int i = 0; i <= nt; i++) {
                        double ii1 = 0.0, ii2 = 0.0;
                        double qq1 = 0.0, qq2 = 0.0;
                        double uu1 = 0.0, uu2 = 0.0;
                        double x = xdel[i];
                        for (int j = 1; j <= mu; j++) {
                            double z  = (double)GB(j);
                            double xi1 = I1(i, j), xi2 = I1(i, -j);
                            double xq1 = Q1(i, j), xq2 = Q1(i, -j);
                            double xu1 = U1(i, j), xu2 = U1(i, -j);
                            double bpjk   = BP (j,  k) * x;
                            double bpjmk  = BP (j, -k) * x;
                            double arrjk  = ARR(j,  k) * x;
                            double arrjmk = ARR(j, -k) * x;
                            double artjk  = ART(j,  k) * x;
                            double artjmk = ART(j, -k) * x;
                            double artkj  = ART(k,  j) * x;
                            double artkmj = ART(k, -j) * x;
                            double attjk  = ATT(j,  k) * x;
                            double attjmk = ATT(j, -k) * x;

                            double xdb;
                            xdb = xi1*bpjk + xi2*bpjmk;
                            ii2 += xdb * z;
                            xdb = xi1*bpjmk + xi2*bpjk;
                            ii1 += xdb * z;
                            xdb = xq1*arrjk + xq2*arrjmk - xu1*artjk + xu2*artjmk;
                            qq2 += xdb * z;
                            xdb = xq1*arrjmk + xq2*arrjk - xu1*artjmk + xu2*artjk;
                            qq1 += xdb * z;
                            xdb = xq1*artkj + xq2*artkmj - xu1*attjk - xu2*attjmk;
                            uu2 -= xdb * z;
                            xdb = -xq1*artkmj - xq2*artkj - xu1*attjmk - xu2*attjk;
                            uu1 -= xdb * z;
                        }
                        if (fabs(ii2) < 1e-30) ii2 = 0.0;
                        if (fabs(ii1) < 1e-30) ii1 = 0.0;
                        if (fabs(qq2) < 1e-30) qq2 = 0.0;
                        if (fabs(qq1) < 1e-30) qq1 = 0.0;
                        if (fabs(uu2) < 1e-30) uu2 = 0.0;
                        if (fabs(uu1) < 1e-30) uu1 = 0.0;
                        I2(i,  k) = ii2;  I2(i, -k) = ii1;
                        Q2(i,  k) = qq2;  Q2(i, -k) = qq1;
                        U2(i,  k) = uu2;  U2(i, -k) = uu1;
                    }
                }
            }

            /* ── Vertical integration upward ── */
            for (int k = 1; k <= mu; k++) {
                I1(nt,k) = Q1(nt,k) = U1(nt,k) = 0.0;
                double zi1 = 0.0, zq1 = 0.0, zu1 = 0.0;
                double yy = (double)RM(k);
                for (int i = nt - 1; i >= 0; i--) {
                    int jj = i + 1;
                    double f = h[jj] - h[i];
                    double c = exp(-f / yy), d = 1.0 - c, xx = h[i] - h[jj]*c;
                    #define VI_UP(Z, v2, v1, k_idx) \
                        { double _a = (v2(jj,k_idx) - v2(i,k_idx)) / f; \
                          double _b = v2(i,k_idx) - _a * h[i]; \
                          Z = c*Z + (d*(_b + _a*yy) + _a*xx) * 0.5; \
                          if (fabs(Z) < 1e-20) Z = 0.0; \
                          v1(i,k_idx) = Z; }
                    VI_UP(zi1, I2, I1, k)
                    VI_UP(zq1, Q2, Q1, k)
                    VI_UP(zu1, U2, U1, k)
                    #undef VI_UP
                }
            }

            /* ── Vertical integration downward ── */
            for (int k = -mu; k <= -1; k++) {
                I1(0,k) = Q1(0,k) = U1(0,k) = 0.0;
                double zi1 = 0.0, zq1 = 0.0, zu1 = 0.0;
                double yy = (double)RM(k);
                for (int i = 1; i <= nt; i++) {
                    int jj = i - 1;
                    double f = h[i] - h[jj];
                    double c = exp(f / yy), d = 1.0 - c, xx = h[i] - h[jj]*c;
                    #define VI_DN(Z, v2, v1, k_idx) \
                        { double _a = (v2(i,k_idx) - v2(jj,k_idx)) / f; \
                          double _b = v2(i,k_idx) - _a * h[i]; \
                          Z = c*Z + (d*(_b + _a*yy) + _a*xx) * 0.5; \
                          if (fabs(Z) < 1e-20) Z = 0.0; \
                          v1(i,k_idx) = Z; }
                    VI_DN(zi1, I2, I1, k)
                    VI_DN(zq1, Q2, Q1, k)
                    VI_DN(zu1, U2, U1, k)
                    #undef VI_DN
                }
            }

            /* ── Collect scattering order n ── */
            for (int k = -mu; k <= mu; k++) {
                if (k == 0) continue;
                int idx = (k < 0) ? nt : 0;
                IN(k)  = I1(idx, k);
                QN(k)  = Q1(idx, k);
                UN(k)  = U1(idx, k);
            }
            roI0 = I1(iplane, mu);
            roQ0 = Q1(iplane, mu);
            roU0 = U1(iplane, mu);

            /* ── Convergence test (geometric series) ── */
            if (ig > 2) {
                double z = 0.0;
                /* Check roI */
                if (roI2 >= accu && roI1 >= accu && roI >= accu) {
                    double r = roI0 / roI1;
                    double y = fabs(((r - roI1/roI2) / ((1.0-r)*(1.0-r)))
                                    * (roI0 / roI));
                    z = fmax(y, z);
                }
                /* Check roQ, roU similarly */
                #define CHECK_CONV(a2, a1, a0, asum) \
                    if (fabs(a2) >= accu && fabs(a1) >= accu && fabs(asum) >= accu) { \
                        double _r = (a0) / (a1); \
                        double _y = fabs(((_r - (a1)/(a2)) / ((1.0-_r)*(1.0-_r))) \
                                         * ((a0) / (asum))); \
                        z = fmax(_y, z); \
                    }
                CHECK_CONV(roQ2, roQ1, roQ0, roQ)
                CHECK_CONV(roU2, roU1, roU0, roU)
                #undef CHECK_CONV
                /* Check all quadrature points */
                for (int l = -mu; l <= mu; l++) {
                    if (l == 0) continue;
                    #define CK3(n2,n1,n0,s3) \
                        if (fabs(n2(l)) >= accu && fabs(n1(l)) >= accu && fabs(s3(l)) >= accu) { \
                            double _r = (n0(l)) / (n1(l)); \
                            double _y = fabs(((_r - (n1(l))/(n2(l))) / ((1.0-_r)*(1.0-_r))) \
                                             * ((n0(l)) / (s3(l)))); \
                            z = fmax(_y, z); \
                        }
                    CK3(INM2, INM1, IN, I3)
                    CK3(QNM2, QNM1, QN, Q3)
                    CK3(UNM2, UNM1, UN, U3)
                    #undef CK3
                }

                if (z < 0.01) {
                    /* Geometric series acceleration */
                    for (int l = -mu; l <= mu; l++) {
                        if (l == 0) continue;
                        #define ACCEL(n1,n0,s3) \
                            { double _d1 = n1(l), _g1 = n0(l); \
                              if (fabs(_d1) > accu && fabs(_g1 - _d1) > accu) \
                                  s3(l) += _g1 / (1.0 - _g1 / _d1); }
                        ACCEL(INM1, IN, I3)
                        ACCEL(QNM1, QN, Q3)
                        ACCEL(UNM1, UN, U3)
                        #undef ACCEL
                    }
                    #define ACCEL_RO(ro1, ro0, ro) \
                        { if (fabs(ro1) >= accu && fabs(ro0 - ro1) >= accu) \
                              ro += ro0 / (1.0 - ro0 / ro1); }
                    ACCEL_RO(roI1, roI0, roI)
                    ACCEL_RO(roQ1, roQ0, roQ)
                    ACCEL_RO(roU1, roU0, roU)
                    #undef ACCEL_RO
                    goto done_sos;
                }
                /* Shift n-2 ← n-1 */
                for (int k = -mu; k <= mu; k++) {
                    INM2(k) = INM1(k);  QNM2(k) = QNM1(k);  UNM2(k) = UNM1(k);
                }
                roI2 = roI1;  roQ2 = roQ1;  roU2 = roU1;
            }
            /* Shift n-1 ← n */
            for (int k = -mu; k <= mu; k++) {
                INM1(k) = IN(k);  QNM1(k) = QN(k);  UNM1(k) = UN(k);
            }
            roI1 = roI0;  roQ1 = roQ0;  roU1 = roU0;

            /* Accumulate order n */
            for (int l = -mu; l <= mu; l++) {
                I3(l) += IN(l);  Q3(l) += QN(l);  U3(l) += UN(l);
            }
            roI += roI0;  roQ += roQ0;  roU += roU0;

            /* Relative convergence: stop if last order < 1e-5 of sum */
            {
                double z = 0.0;
                for (int l = -mu; l <= mu; l++) {
                    if (l == 0) continue;
                    if (fabs(I3(l)) >= accu) z = fmax(z, fabs(IN(l)/I3(l)));
                    if (fabs(Q3(l)) >= accu) z = fmax(z, fabs(QN(l)/Q3(l)));
                    if (fabs(U3(l)) >= accu) z = fmax(z, fabs(UN(l)/U3(l)));
                }
                if (z < 1e-5) goto done_sos;
            }
            if (ig >= ctx->multi.igmax) goto done_sos;
        } /* end SOS loop */
    done_sos:;

        /* ── Accumulate Fourier component ── */
        double delta0s = (is == 0) ? 1.0 : 2.0;
        for (int l = -mu; l <= mu; l++) {
            I4(l) += delta0s * I3(l);
            Q4(l) += delta0s * Q3(l);
            U4(l) += delta0s * U3(l);
        }

        /* xl: radiance field at each azimuth plane */
        for (int l_idx = 0; l_idx < np; l_idx++) {
            double phi_l = (double)rp[l_idx];
            for (int m = -mum1; m <= mum1; m++) {
                double cosfac = (m > 0) ? cos(is * (phi_l + pi)) : cos(is * phi_l);
                double sinfac = (m > 0) ? sin(is * (phi_l + pi)) : sin(is * phi_l);
                XL(m, l_idx) += (float)(delta0s * I3(m) * cosfac);
                if (xlq) xlq[((m)+mu)*np + l_idx] += (float)(delta0s * Q3(m) * cosfac);
                if (xlu) xlu[((m)+mu)*np + l_idx] += (float)(delta0s * U3(m) * sinfac);
            }
        }

        /* xl(mu, 1): upward at specific view direction */
        XL(mu, 0) += (float)(delta0s * I3(mu) * cos(is * (phirad + pi)));
        if (xlq) xlq[(mu+mu)*np] += (float)(delta0s * Q3(mu) * cos(is * (phirad + pi)));
        if (xlu) xlu[(mu+mu)*np] += (float)(delta0s * U3(mu) * sin(is * (phirad + pi)));

        /* xl(-mu, 1): atmospheric path reflectance (×xmus) */
        XL(-mu, 0) += (float)(delta0s * roI * cos(is * (phirad + pi)));
        if (xlq) xlq[(0)*np]     += (float)(delta0s * roQ * cos(is * (phirad + pi)));
        if (xlu) xlu[(0)*np]     += (float)(delta0s * roU * sin(is * (phirad + pi)));

        /* xl(0, 1): downward flux (is=0 only) */
        if (is == 0) {
            for (int k = 1; k <= mum1; k++)
                XL(0, 0) += (float)((double)RM(k) * (double)GB(k) * I3(-k));
        }

        /* xlphim: path reflectance vs azimuth */
        for (int ifi = 0; ifi < nfi; ifi++) {
            double phimul = (double)ifi * pi / (double)(nfi - 1);
            xlphim[ifi] += (float)(delta0s * roI * cos(is * (phimul + pi)));
        }

        /* Fourier convergence */
        {
            double z = 0.0;
            for (int l = -mu; l <= mu; l++) {
                if (fabs(I4(l)) >= accu) z = fmax(z, fabs(I3(l)/I4(l)));
                if (fabs(Q4(l)) >= accu) z = fmax(z, fabs(Q3(l)/Q4(l)));
                if (fabs(U4(l)) >= accu) z = fmax(z, fabs(U3(l)/U4(l)));
            }
            if (z <= 0.0005) break;
        }
    } /* end Fourier loop */

    nt = snt;

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
    #undef Q1
    #undef Q2
    #undef Q3
    #undef Q4
    #undef QN
    #undef QNM1
    #undef QNM2
    #undef U1
    #undef U2
    #undef U3
    #undef U4
    #undef UN
    #undef UNM1
    #undef UNM2
    #undef XPL
    #undef XRL
    #undef XTL
    #undef BP
    #undef ARR
    #undef ART
    #undef ATT
    #undef XL

    free(h);    free(ch);   free(xdel); free(ydel); free(altc);
    free(i1);   free(i2);   free(i3);   free(i4);
    free(in_);  free(inm1); free(inm2);
    free(q1);   free(q2);   free(q3);   free(q4);
    free(qn);   free(qnm1); free(qnm2);
    free(u1);   free(u2);   free(u3);   free(u4);
    free(un);   free(unm1); free(unm2);
    free(xpl);  free(xrl);  free(xtl);
    free(psl);  free(rsl);  free(tsl);
    free(bp);   free(arr);  free(art);  free(att);
}
