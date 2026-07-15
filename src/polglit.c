/**
 * \file polglit.c
 * \brief Polarized surface reflectance — C port of 6SV2.1 POLGLIT.f and POLNAD.f.
 *
 * POLGLIT: ocean glint using Cox-Munk anisotropic wave-facet distribution and
 *          Fresnel reflection.  Refractive index m = 1.33 (sea water).
 *
 * POLNAD:  Nadal-Breon vegetation/soil model.  Leaf Fresnel N = 1.5.
 *          r_pveg = Γ / [4(cos_SZA + cos_VZA)],
 *          r_psoil = Γ / [4 cos_SZA cos_VZA],
 *          r_psur = p_veg · r_pveg + (1 − p_veg) · r_psoil.
 *
 * Both models rotate the polarisation state from the scattering plane to the
 * sensor meridional plane using the rotation cosine cksi.
 */

#include "polglit.h"
#include <math.h>

/**
 * \brief Compute polarised ocean-glint Stokes Q and U components.
 *
 * Models the Q and U Stokes parameters of ocean surface glint reflectance
 * using the Cox-Munk anisotropic wave-facet slope distribution and Fresnel
 * reflection for sea water (n = 1.33).  The result is rotated from the
 * scattering plane into the sensor meridional plane.
 *
 * Ported from 6SV2.1 POLGLIT.f.
 *
 * \param[in]  xts   Solar zenith angle (degrees).
 * \param[in]  xtv   View zenith angle (degrees).
 * \param[in]  phi   Relative azimuth angle (degrees).
 * \param[in]  wspd  Wind speed at 10 m (m s⁻¹).
 * \param[in]  azw   Wind direction (degrees from North, clockwise).
 * \param[out] ropq  Polarised Q component of ocean glint reflectance.
 * \param[out] ropu  Polarised U component of ocean glint reflectance.
 */
void sixs_polglit(float xts, float xtv, float phi, float wspd, float azw,
                   float *ropq, float *ropu)
{
    *ropq = 0.0f;
    *ropu = 0.0f;

    double pi  = acos(-1.0);
    double dtr = pi / 180.0;
    double m   = 1.33;

    double cxts = cos(xts * dtr), sxts = sin(xts * dtr);
    double cxtv = cos(xtv * dtr), sxtv = sin(xtv * dtr);
    double cphi = cos(phi * dtr), sphi = sin(phi * dtr);

    double csca = -cxts * cxtv - sxts * sxtv * cphi;
    if (csca >  1.0) csca =  1.0;
    if (csca < -1.0) csca = -1.0;

    double sca   = acos(csca);
    double alpha = (pi - sca) * 0.5;
    double sinA  = sin(alpha), cosA = cos(alpha);
    double sqrtM = sqrt(m * m - sinA * sinA);

    /* Fresnel coefficients (parallel and perpendicular polarisation) */
    double rl = (sqrtM - m * m * cosA) / (sqrtM + m * m * cosA);
    double rr = (cosA  - sqrtM)        / (cosA  + sqrtM);
    double r2 = 0.5 * (rl * rl - rr * rr);   /* polarizing term; r3=rl*rr set to 0 */

    /* Cox-Munk anisotropic wave-facet slope distribution */
    double phw    = azw * dtr;
    double cs = cxts, cv = cxtv, ss = sxts, sv = sxtv;
    double Zx = -sv * sphi / (cs + cv);
    double Zy = (ss + sv * cphi) / (cs + cv);

    double tantilt = sqrt(Zx * Zx + Zy * Zy);
    double tilt    = atan(tantilt);

    double sigmaC = 0.003 + 0.00192 * wspd;
    double sigmaU = 0.00316 * wspd;
    double C21    =  0.01  - 0.0086 * wspd;
    double C03    =  0.04  - 0.033  * wspd;
    double C40    =  0.40;
    double C22    =  0.12;
    double C04    =  0.23;

    double xe  = (cos(phw) * Zx + sin(phw) * Zy) / sqrt(sigmaC);
    double xn  = (-sin(phw) * Zx + cos(phw) * Zy) / sqrt(sigmaU);
    double xe2 = xe * xe, xn2 = xn * xn;

    double coef = 1.0
                - C21 / 2.0 * (xe2 - 1.0) * xn
                - C03 / 6.0 * (xn2 - 3.0) * xn
                + C40 / 24.0 * (xe2 * xe2 - 6.0 * xe2 + 3.0)
                + C04 / 24.0 * (xn2 * xn2 - 6.0 * xn2 + 3.0)
                + C22 / 4.0  * (xe2 - 1.0) * (xn2 - 1.0);

    double proba = coef / (2.0 * pi * sqrt(sigmaU * sigmaC))
                 * exp(-(xe2 + xn2) * 0.5);

    double ct = cos(tilt);
    double ct4 = ct * ct * ct * ct;
    if (ct4 < 1e-12) return;   /* surface near-horizontal; avoid ÷0 */

    double factor = pi * proba / (4.0 * cs * cv * ct4);

    /* Rotation angle cksi (cosine of rotation from scattering to meridional plane) */
    double cksi;
    if (xtv > 0.5f) {
        double denom = sqrt(1.0 - csca * csca) * sxtv;
        if (denom < 1e-12) denom = 1e-12;
        cksi = (sphi < 0.0)
             ?  (cxtv * csca + cxts) / denom
             : -(cxtv * csca + cxts) / denom;
    } else {
        cksi = 1.0;   /* near-nadir: Q = r2*factor, U = 0 */
    }
    if (cksi >  1.0) cksi =  1.0;
    if (cksi < -1.0) cksi = -1.0;

    *ropq = (float)( r2 * (2.0 * cksi * cksi - 1.0) * factor);
    *ropu = (float)(-r2 * 2.0 * cksi * sqrt(1.0 - cksi * cksi) * factor);
}

/**
 * \brief Compute polarised Stokes Q and U for vegetation/soil (Nadal-Breon model).
 *
 * Implements the Nadal-Breon surface polarisation model, which linearly
 * mixes a leaf Fresnel term (\f$N = 1.5\f$) and a soil Fresnel term,
 * weighted by the vegetation fraction \c pveg.  The result is rotated into
 * the sensor meridional plane.
 *
 * Ported from 6SV2.1 POLNAD.f.
 *
 * \param[in]  xts   Solar zenith angle (degrees).
 * \param[in]  xtv   View zenith angle (degrees).
 * \param[in]  phi   Relative azimuth angle (degrees).
 * \param[in]  pveg  Vegetation fraction [0, 1].
 * \param[out] ropq  Polarised Q component of surface reflectance.
 * \param[out] ropu  Polarised U component of surface reflectance.
 */
void sixs_polnad(float xts, float xtv, float phi, float pveg,
                  float *ropq, float *ropu)
{
    *ropq = 0.0f;
    *ropu = 0.0f;

    double pi  = acos(-1.0);
    double dtr = pi / 180.0;
    double N   = 1.5;

    double cxts = cos(xts * dtr), sxts = sin(xts * dtr);
    double cxtv = cos(xtv * dtr), sxtv = sin(xtv * dtr);
    double cphi = cos(phi * dtr), sphi = sin(phi * dtr);

    double csca = -cxts * cxtv - sxts * sxtv * cphi;
    if (csca >  1.0) csca =  1.0;
    if (csca < -1.0) csca = -1.0;

    double sca    = acos(csca);
    double alpha  = (pi - sca) * 0.5;
    double alphap = asin(sin(alpha) / N);
    double mui    = cos(alpha);
    double mut    = cos(alphap);

    double xf1     = (N * mut - mui) / (N * mut + mui);
    double xf2     = (N * mui - mut) / (N * mui + mut);
    double fpalpha = 0.5 * (xf1 * xf1 - xf2 * xf2);

    double dveg  = 4.0 * (cxts + cxtv);
    double dsoil = 4.0 * cxts * cxtv;
    if (fabs(dveg)  < 1e-12) dveg  = 1e-12;
    if (fabs(dsoil) < 1e-12) dsoil = 1e-12;

    double rpveg  = fpalpha / dveg;
    double rpsoil = fpalpha / dsoil;
    double rpsur  = (double)pveg * rpveg + (1.0 - (double)pveg) * rpsoil;

    /* Rotation angle cksi */
    double cksi;
    if (xtv > 0.5f) {
        double denom = sqrt(1.0 - csca * csca) * sxtv;
        if (denom < 1e-12) denom = 1e-12;
        cksi = (sphi < 0.0)
             ?  (cxtv * csca + cxts) / denom
             : -(cxtv * csca + cxts) / denom;
    } else {
        cksi = 0.0;   /* near-nadir: Q = U = 0 per POLNAD.f */
    }
    if (cksi >  1.0) cksi =  1.0;
    if (cksi < -1.0) cksi = -1.0;

    *ropq = (float)( rpsur * (2.0 * cksi * cksi - 1.0));
    *ropu = (float)(-rpsur * 2.0 * cksi * sqrt(1.0 - cksi * cksi));
}
