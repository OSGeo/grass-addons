/* Mie scattering for custom aerosols — ported from 6SV2.1 MIE.f + EXSCPHASE.f.
 *
 * Implements Bohren-Huffman Mie theory for spherical particles over a
 * log-normal size distribution, computing extinction, single-scatter albedo,
 * asymmetry parameter, and phase function at the 20 reference wavelengths
 * used by the 6SV2.1 RT solver.
 *
 * Usage:
 *   sixs_mie_init(ctx, r_mode, sigma_g, m_r, m_i)  — fills ctx->aer
 *   sixs_aerosol_init then builds ctx->polar from ctx->aer as usual.
 */
#include "../include/sixs_ctx.h"
#include "gauss.h"
#include <math.h>
#include <stdlib.h>
#include <string.h>

#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif

/* Reference wavelengths (µm) — same as aerosol.c wldisc */
static const float wldisc_mie[NWL_DISC] = {
    0.350f,0.400f,0.412f,0.443f,0.470f,0.488f,0.515f,0.550f,
    0.590f,0.633f,0.670f,0.694f,0.760f,0.860f,1.240f,1.536f,
    1.650f,1.950f,2.250f,3.750f
};

/**
 * \brief Compute Mie extinction/scattering efficiencies and phase function for a sphere.
 *
 * Implements Bohren-Huffman Mie theory for a homogeneous sphere of size
 * parameter \f$X = 2\pi r / \lambda\f$ and complex refractive index
 * \f$m = n_r - i n_i\f$.  Series length follows the Wiscombe criterion
 * based on \f$|m| \cdot X\f$.
 *
 * \param[in]  X         Size parameter \f$2\pi r / \lambda\f$ (dimensionless).
 * \param[in]  nr        Real part of the refractive index.
 * \param[in]  ni        Imaginary part (absorption; positive value means absorbing).
 * \param[out] Qext_out  Extinction efficiency \f$Q_\text{ext}\f$.
 * \param[out] Qsca_out  Scattering efficiency \f$Q_\text{sca}\f$.
 * \param[out] p11       Scattering phase function at \c nbmu Gauss quadrature angles.
 * \param[in]  nbmu      Number of Gauss quadrature angles.
 * \param[in]  cgaus_S   Gauss quadrature cosines [nbmu].
 * \param[in]  pdgs_S    Gauss quadrature weights [nbmu] (unused, reserved).
 */
static void exscphase(double X, double nr, double ni,
                      double *Qext_out, double *Qsca_out,
                      double *p11, int nbmu,
                      const float *cgaus_S, const float *pdgs_S)
{
    (void)pdgs_S;   /* used only when asymmetry is needed externally */

    /* Maximum series order — Wiscombe criterion on |m|*X */
    double Y = X * sqrt(nr*nr + ni*ni);
    int N = (int)(0.5 * (-1.0 + sqrt(1.0 + 4.0*Y*Y))) + 1;
    if (N < 2) N = 2;

    /* Upper bound for series truncation (Deirmendjian) */
    double Up = 2.0*Y / (2.0*N + 1.0);
    int mu1 = (int)(N + 30.0*(0.10 + 0.35*Up*(2 - Up*Up)/2.0/(1 - Up + 1e-30)));
    int Np  = (int)(Y - 0.5 + sqrt(30.0*0.35*Y));
    int mu2 = mu1;
    if (Np > N) {
        Up  = 2.0*Y / (2.0*Np + 1.0);
        mu2 = (int)(Np + 30.0*(0.10 + 0.35*Up*(2 - Up*Up)/2.0/(1 - Up + 1e-30)));
    }
    int mu = (mu1 < mu2) ? mu1 : mu2;
    if (mu < 2) mu = 2;
    if (mu > 50000) mu = 50000;   /* hard safety cap */

    /* Dynamic allocation for Mie recursion arrays (0..mu) */
    double *xj   = (double*)calloc(mu + 2, sizeof(double));
    double *xy   = (double*)calloc(mu + 2, sizeof(double));   /* shifted: index 0=xy[-1], 1=xy[0], ... */
    double *Rn   = (double*)calloc(mu + 2, sizeof(double));
    double *RDnX = (double*)calloc(mu + 2, sizeof(double));
    double *RDnY = (double*)calloc(mu + 2, sizeof(double));
    double *IDnY = (double*)calloc(mu + 2, sizeof(double));
    double *RGnX = (double*)calloc(mu + 2, sizeof(double));
    double *IGnX = (double*)calloc(mu + 2, sizeof(double));
    double *RAn  = (double*)calloc(mu + 2, sizeof(double));
    double *IAn  = (double*)calloc(mu + 2, sizeof(double));
    double *RBn  = (double*)calloc(mu + 2, sizeof(double));
    double *IBn  = (double*)calloc(mu + 2, sizeof(double));
    double *TAUn = (double*)calloc(mu + 2, sizeof(double));
    double *PIn  = (double*)calloc(mu + 2, sizeof(double));

    if (!xj || !xy || !Rn || !RDnX || !RDnY || !IDnY ||
        !RGnX || !IGnX || !RAn || !IAn || !RBn || !IBn || !TAUn || !PIn) {
        free(xj); free(xy); free(Rn); free(RDnX); free(RDnY); free(IDnY);
        free(RGnX); free(IGnX); free(RAn); free(IAn); free(RBn); free(IBn);
        free(TAUn); free(PIn);
        *Qext_out = 2.0; *Qsca_out = 2.0;
        for (int j = 0; j < nbmu; j++) p11[j] = 1.0;
        return;
    }

    /* Inverse relative refractive index (for Dn recursion) */
    double denom = nr*nr + ni*ni;
    double Ren   = nr / denom;
    double Imn   = ni / denom;

    /* Downward recursion for Dn(X) and Dn(Y) */
    RDnY[mu] = 0.0; IDnY[mu] = 0.0; RDnX[mu] = 0.0;
    for (int k = mu; k >= 1; k--) {
        RDnX[k-1] = (double)k/X - 1.0 / (RDnX[k] + (double)k/X);
        double XnumR = RDnY[k] + Ren*(double)k/X;
        double XnumI = IDnY[k] + Imn*(double)k/X;
        double Xden  = XnumR*XnumR + XnumI*XnumI;
        RDnY[k-1] = (double)k*Ren/X - XnumR/Xden;
        IDnY[k-1] = (double)k*Imn/X + XnumI/Xden;
    }

    /* Downward pass for Rn ratios + xj normalization seed */
    Rn[mu] = 0.0;
    int mub = mu;
    for (int k = mu; k >= 2; k--) {
        Rn[k-1] = X / (2.0*k + 1.0 - X*Rn[k]);
        if (Rn[k-1] > 1.0) {
            mub = k - 1;
            xj[mub+1] = Rn[mub];
            xj[mub]   = 1.0;
            goto seed_found;
        }
    }
    /* Fell through: start from mu */
    xj[mub+1] = 0.0;
    xj[mub]   = 1.0;

seed_found:;
    /* Upward recursion for xj (spherical Bessel j) */
    for (int k = mub; k >= 1; k--)
        xj[k-1] = (2.0*k + 1.0)*xj[k]/X - xj[k+1];

    /* Normalize xj by the Wronskian coxj */
    double coxj = (xj[0] - X*xj[1])*cos(X) + X*xj[0]*sin(X);

    /* Initialise Bessel y (-1 and 0 indices stored offset by 1) */
    /* xy_arr[k] = y(k-1): xy_arr[0]=y(-1)=sin(X)/X, xy_arr[1]=y(0)=-cos(X)/X */
    xy[0] = sin(X)/X;    /* y_{-1} */
    xy[1] = -cos(X)/X;   /* y_0    */

    /* Upward recursion for Gn, An, Bn, Qsca, Qext */
    RGnX[0] = 0.0;
    IGnX[0] = -1.0;
    double Qsca = 0.0, Qext = 0.0;

    int mu_final = mu;
    for (int k = 1; k <= mu; k++) {
        /* Normalise xj */
        double xjk;
        if (k <= mub) {
            xjk = xj[k] / coxj;
        } else {
            xjk = Rn[k-1] * xj[k-1] / coxj;
        }
        xj[k] = xjk;

        /* Bessel y upward */
        xy[k+1] = (2.0*k - 1.0)*xy[k]/X - xy[k-1];   /* y_k */

        double yk    = xy[k+1];   /* y_{k} */
        double h2    = xjk*xjk + yk*yk;
        double xJonH = (h2 > 0.0) ? xjk/h2 : 0.0;

        /* Gn */
        double den_G = (RGnX[k-1] - (double)k/X)*(RGnX[k-1] - (double)k/X)
                     + IGnX[k-1]*IGnX[k-1];
        if (den_G > 0.0) {
            RGnX[k] = ((double)k/X - RGnX[k-1])/den_G - (double)k/X;
            IGnX[k] = IGnX[k-1]/den_G;
        }

        /* An */
        double n1a = RDnY[k] - nr*RDnX[k];
        double n2a = IDnY[k] + ni*RDnX[k];
        double d1a = RDnY[k] - nr*RGnX[k] - ni*IGnX[k];
        double d2a = IDnY[k] + ni*RGnX[k] - nr*IGnX[k];
        double da  = d1a*d1a + d2a*d2a;
        double RAb = (da > 0.0) ? (n1a*d1a + n2a*d2a)/da : 0.0;
        double IAb = (da > 0.0) ? (-n1a*d2a + n2a*d1a)/da : 0.0;
        RAn[k] = xJonH*(xjk*RAb - yk*IAb);
        IAn[k] = xJonH*(yk*RAb  + xjk*IAb);

        /* Bn */
        double n1b = nr*RDnY[k] + ni*IDnY[k] - RDnX[k];
        double n2b = nr*IDnY[k] - ni*RDnY[k];
        double d1b = nr*RDnY[k] + ni*IDnY[k] - RGnX[k];
        double d2b = nr*IDnY[k] - ni*RDnY[k] - IGnX[k];
        double db  = d1b*d1b + d2b*d2b;
        double RBb = (db > 0.0) ? (n1b*d1b + n2b*d2b)/db : 0.0;
        double IBb = (db > 0.0) ? (-n1b*d2b + n2b*d1b)/db : 0.0;
        RBn[k] = xJonH*(xjk*RBb - yk*IBb);
        IBn[k] = xJonH*(yk*RBb  + xjk*IBb);

        /* Convergence test */
        double test = (RAn[k]*RAn[k] + IAn[k]*IAn[k]
                     + RBn[k]*RBn[k] + IBn[k]*IBn[k]) / (double)k;
        if (test < 1.0e-14) {
            mu_final = k;
            break;
        }

        double xpond = 2.0/X/X * (2.0*k + 1.0);
        Qsca += xpond * (RAn[k]*RAn[k] + IAn[k]*IAn[k]
                       + RBn[k]*RBn[k] + IBn[k]*IBn[k]);
        Qext += xpond * (RAn[k] + RBn[k]);
    }

    /* Phase function at nbmu Gauss angles */
    for (int j = 0; j < nbmu; j++) {
        double xmud = (double)cgaus_S[j];
        double RS1 = 0.0, RS2 = 0.0, IS1 = 0.0, IS2 = 0.0;
        PIn[0] = 0.0;
        PIn[1] = 1.0;
        TAUn[1] = xmud;
        for (int k = 1; k <= mu_final; k++) {
            double co_n = (2.0*k + 1.0) / ((double)k * (k + 1.0));
            RS1 += co_n * (RAn[k]*PIn[k]  + RBn[k]*TAUn[k]);
            RS2 += co_n * (RAn[k]*TAUn[k] + RBn[k]*PIn[k]);
            IS1 += co_n * (IAn[k]*PIn[k]  + IBn[k]*TAUn[k]);
            IS2 += co_n * (IAn[k]*TAUn[k] + IBn[k]*PIn[k]);
            PIn[k+1]  = ((2.0*k+1)*xmud*PIn[k]  - (k+1.0)*PIn[k-1]) / (double)k;
            TAUn[k+1] = (k+1.0)*xmud*PIn[k+1] - (k+2.0)*PIn[k];
        }
        p11[j] = (RS1*RS1 + IS1*IS1 + RS2*RS2 + IS2*IS2) / (X*X*2.0);
    }

    *Qext_out = Qext;
    *Qsca_out = Qsca;

    free(xj); free(xy); free(Rn); free(RDnX); free(RDnY); free(IDnY);
    free(RGnX); free(IGnX); free(RAn); free(IAn); free(RBn); free(IBn);
    free(TAUn); free(PIn);
}

/**
 * \brief Initialise a custom log-normal aerosol by computing Mie scattering properties.
 *
 * Populates \c ctx->aer with extinction coefficient, single-scattering albedo,
 * asymmetry parameter, and phase function at the 20 reference wavelengths
 * used by sixs_discom(), by integrating Mie theory over a log-normal size
 * distribution.
 *
 * \note A spectrally constant refractive index (at 550 nm) is assumed across
 *       all 20 wavelengths.  For a spectrally varying index, call aerosol_init()
 *       with a pre-built mixture table instead.
 *
 * \param[in,out] ctx      6SV context; writes \c ctx->aer on return.
 * \param[in]     r_mode   Mode radius of the log-normal distribution (µm).
 * \param[in]     sigma_g  Geometric standard deviation (dimensionless; must be > 1).
 * \param[in]     m_r_550  Real part of the refractive index at 550 nm.
 * \param[in]     m_i_550  Imaginary part of the refractive index at 550 nm (> 0 = absorbing).
 */
void sixs_mie_init(SixsCtx *ctx,
                   double r_mode, double sigma_g,
                   double m_r_550, double m_i_550)
{
    const double pi      = M_PI;
    const double rlogpas = 0.011;   /* log10 step = 6SV default */
    const double rmin    = 0.001;   /* minimum radius (µm) */
    const double rmax    = 25.0;    /* maximum radius (µm) */

    /* Build quadrature grid (same as aerosol.c / DISCOM) */
    int nbmu = ctx->quad.nquad;
    float *cgaus_S = (float*)malloc((size_t)nbmu * sizeof(float));
    float *pdgs_S  = (float*)malloc((size_t)nbmu * sizeof(float));
    if (!cgaus_S || !pdgs_S) { free(cgaus_S); free(pdgs_S); return; }
    sixs_gauss_setup(nbmu, cgaus_S, pdgs_S);

    double *p11    = (double*)malloc((size_t)nbmu * sizeof(double));
    double *ph_wl  = (double*)calloc((size_t)(NWL_DISC * nbmu), sizeof(double));
    if (!p11 || !ph_wl) {
        free(cgaus_S); free(pdgs_S); free(p11); free(ph_wl);
        return;
    }

    /* Accumulators for each reference wavelength */
    double ext_acc[NWL_DISC] = {0};
    double sca_acc[NWL_DISC] = {0};
    double np_acc  = 0.0;
    double vol_acc = 0.0;

    double log10_sigma = log10(sigma_g);

    /* Integrate over particle radius */
    double r  = rmin;
    double dr = r * (pow(10.0, rlogpas) - 1.0);

    while (r < rmax) {
        /* Log-normal dn/dr */
        double logr_ratio = log10(r / r_mode) / log10_sigma;
        double nr_dist = exp(-0.5 * logr_ratio * logr_ratio)
                       / (sqrt(2.0*pi) * log(10.0) * r * log10_sigma);
        /* Projected area element */
        double xndpr2 = nr_dist * dr * pi * r * r;
        np_acc  += nr_dist * dr;
        vol_acc += r*r*r * nr_dist * dr;

        for (int l = 0; l < NWL_DISC; l++) {
            double wl  = (double)wldisc_mie[l];
            double X   = 2.0 * pi * r / wl;
            double Qext, Qsca;
            exscphase(X, m_r_550, m_i_550, &Qext, &Qsca, p11, nbmu,
                      cgaus_S, pdgs_S);
            ext_acc[l] += xndpr2 * Qext;
            sca_acc[l] += xndpr2 * Qsca;
            for (int k = 0; k < nbmu; k++)
                ph_wl[l*nbmu + k] += 4.0 * p11[k] * xndpr2;
        }

        r  += dr;
        dr  = r * (pow(10.0, rlogpas) - 1.0);
    }

    /* Normalise per-particle and store into ctx->aer */
    /* 6SV normalises at 550 nm (index 7 in wldisc) */
    double norm = (ext_acc[7] > 0.0) ? 1.0 / ext_acc[7] : 1.0;

    for (int l = 0; l < NWL_DISC; l++) {
        if (np_acc > 0.0) {
            ext_acc[l] /= np_acc;
            sca_acc[l] /= np_acc;
            for (int k = 0; k < nbmu; k++)
                ph_wl[l*nbmu + k] /= np_acc;
        }
        ctx->aer.ext[l]   = (float)(ext_acc[l] * norm);
        ctx->aer.ome[l]   = (ext_acc[l] > 0.0) ? (float)(sca_acc[l] / ext_acc[l]) : 0.0f;

        /* Asymmetry parameter from phase function */
        double asy_n = 0.0, asy_d = 0.0;
        for (int k = 0; k < nbmu; k++) {
            double ph_k = (sca_acc[l] > 0.0) ? ph_wl[l*nbmu+k] / sca_acc[l] : 0.0;
            asy_n += (double)cgaus_S[k] * ph_k * (double)pdgs_S[k];
            asy_d += ph_k * (double)pdgs_S[k];
        }
        ctx->aer.gasym[l] = (float)((asy_d > 0.0) ? asy_n / asy_d : 0.0);

        /* Phase function at the scattering angle (from ctx->polar.pha[0..nbmu-1]) */
        /* Store at index 0 (forward scatter) for now; aerosol.c rebuilds polar */
        ctx->aer.phase[l] = (sca_acc[l] > 0.0 && nbmu > 0)
            ? (float)(ph_wl[l*nbmu + 0] / sca_acc[l])
            : 0.0f;
    }

    /* Build phase function in ctx->polar (Legendre expansion at 550 nm) */
    if (sca_acc[7] > 0.0) {
        for (int k = 0; k < nbmu; k++) {
            ctx->polar.pha[k] = (float)(ph_wl[7*nbmu + k] / sca_acc[7]);
        }
        /* Legendre coefficients */
        float *betal = ctx->polar.betal;
        for (int kk = 0; kk <= nbmu - 3; kk++) betal[kk] = 0.0f;
        for (int j = 0; j < nbmu; j++) {
            float x   = ctx->polar.pha[j] * pdgs_S[j];
            float rm_ = cgaus_S[j];
            float plm1 = 0.0f, pl0 = 1.0f;
            for (int k = 0; k <= nbmu - 3; k++) {
                float plnew = ((2.0f*k + 1.0f)*rm_*pl0 - (float)k*plm1) / (float)(k+1);
                betal[k] += x * pl0;
                plm1 = pl0; pl0 = plnew;
            }
        }
        for (int k = 0; k <= nbmu - 3; k++) {
            betal[k] *= (2.0f*k + 1.0f) * 0.5f;
            if (betal[k] < 0.0f) {
                for (int j = k; j <= nbmu - 3; j++) betal[j] = 0.0f;
                break;
            }
        }
    }

    free(cgaus_S); free(pdgs_S); free(p11); free(ph_wl);
}
