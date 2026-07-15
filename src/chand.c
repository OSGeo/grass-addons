/* Chandrasekhar Rayleigh reflectance — ported from 6SV2.1 CHAND.f.
 * Analytical polynomial approximation, valid for small optical depths. */
#include <math.h>

#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif

/**
 * \brief Compute molecular (Rayleigh) reflectance via Chandrasekhar's analytical approximation.
 *
 * Implements the polynomial approximation from 6SV2.1 CHAND.f, which is valid
 * for small Rayleigh optical depths and covers typical clear-sky conditions.
 *
 * Ported from 6SV2.1 CHAND.f.
 *
 * \param[in] xphi  Relative azimuth angle between Sun and observer (degrees; 0 = backscattering).
 * \param[in] xmuv  Cosine of the view zenith angle.
 * \param[in] xmus  Cosine of the solar zenith angle.
 * \param[in] xtau  Rayleigh optical depth.
 * \return Molecular (Rayleigh) reflectance in [0, 1].
 */
float sixs_chand(float xphi, float xmuv, float xmus, float xtau)
{
    static const float as0[10] = {
         0.33243832f, -6.777104e-02f,  0.16285370f,
         1.577425e-03f, -0.30924818f, -1.240906e-02f,
        -0.10324388f,   3.241678e-02f,  0.11493334f, -3.503695e-02f
    };
    static const float as1[2] = { 0.19666292f, -5.439061e-02f };
    static const float as2[2] = { 0.14545937f, -2.910845e-02f };

    const float pi  = (float)M_PI;
    const float fac = pi / 180.0f;

    float phios  = 180.0f - xphi;
    float xcosf1 = 1.0f;
    float xcosf2 = cosf(phios * fac);
    float xcosf3 = cosf(2.0f * phios * fac);

    const float xdep   = 0.0279f;
    float xfd = xdep / (2.0f - xdep);
    xfd = (1.0f - xfd) / (1.0f + 2.0f * xfd);

    float xph1 = 1.0f + (3.0f * xmus*xmus - 1.0f) * (3.0f * xmuv*xmuv - 1.0f) * xfd / 8.0f;
    float xph2 = -xmus * xmuv * sqrtf(1.0f - xmus*xmus) * sqrtf(1.0f - xmuv*xmuv)
                 * xfd * 0.5f * 1.5f;
    float xph3 = (1.0f - xmus*xmus) * (1.0f - xmuv*xmuv) * xfd * 0.5f * 0.375f;

    /* Single-scatter term (1-exp) / (mu_s + mu_v) */
    float xitm = (1.0f - expf(-xtau * (1.0f/xmus + 1.0f/xmuv))) * xmus
                 / (4.0f * (xmus + xmuv));
    float xp1 = xph1 * xitm;
    float xp2 = xph2 * xitm;
    float xp3 = xph3 * xitm;

    /* Multiple-scatter correction term */
    xitm = (1.0f - expf(-xtau / xmus)) * (1.0f - expf(-xtau / xmuv));
    float cfonc1 = xph1 * xitm;
    float cfonc2 = xph2 * xitm;
    float cfonc3 = xph3 * xitm;

    /* Legendre polynomial predictors in tau */
    float xlntau = logf(xtau);
    float pl[10];
    pl[0] = 1.0f;
    pl[1] = xlntau;
    pl[2] = xmus + xmuv;
    pl[3] = xlntau * pl[2];
    pl[4] = xmus * xmuv;
    pl[5] = xlntau * pl[4];
    pl[6] = xmus*xmus + xmuv*xmuv;
    pl[7] = xlntau * pl[6];
    pl[8] = xmus*xmus * xmuv*xmuv;
    pl[9] = xlntau * pl[8];

    float fs0 = 0.0f;
    for (int i = 0; i < 10; i++) fs0 += pl[i] * as0[i];
    float fs1 = pl[0] * as1[0] + pl[1] * as1[1];
    float fs2 = pl[0] * as2[0] + pl[1] * as2[1];

    float xitot1 = xp1 + cfonc1 * fs0 * xmus;
    float xitot2 = xp2 + cfonc2 * fs1 * xmus;
    float xitot3 = xp3 + cfonc3 * fs2 * xmus;

    float xrray = xitot1 * xcosf1
                + xitot2 * xcosf2 * 2.0f
                + xitot3 * xcosf3 * 2.0f;
    xrray /= xmus;

    return xrray;
}
