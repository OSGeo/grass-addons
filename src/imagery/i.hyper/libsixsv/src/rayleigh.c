/* Rayleigh optical depth — ported from 6SV2.1 ODRAYL.f */
#include "../include/sixs_ctx.h"
#include <math.h>
#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif

/**
 * \brief Compute the Rayleigh optical depth at a given wavelength.
 *
 * Uses the Edlén (1966) refractive-index formula for air and integrates the
 * differential Rayleigh cross-section over the standard atmosphere pressure
 * and temperature profiles stored in \c ctx->atm.
 *
 * \f[
 *   n(\lambda) - 1 = \left(8342.13 + \frac{2406030}{130 - \lambda^{-2}}
 *                     + \frac{15997}{38.9 - \lambda^{-2}}\right) \times 10^{-8}
 * \f]
 *
 * Ported from 6SV2.1 ODRAYL.f.
 *
 * \param[in]  ctx   6SV context with initialised atmosphere (\c sixs_init_atmosphere()).
 * \param[in]  wl    Wavelength in µm.
 * \param[out] tray  Rayleigh optical depth (dimensionless, > 0).
 */
void sixs_odrayl(const SixsCtx *ctx, float wl, float *tray) {
    double awl = wl;
    double ak  = 1.0 / awl;
    double a1  = 130.0 - ak * ak;
    double a2  = 38.9  - ak * ak;
    double a3  = 2406030.0 / a1;
    double a4  = 15997.0   / a2;
    double an  = (8342.13 + a3 + a4) * 1.0e-8 + 1.0;

    double delta = ctx->del.delta;
    double a = (24.0 * M_PI * M_PI * M_PI) * ((an * an - 1.0) * (an * an - 1.0)) *
               (6.0 + 3.0 * delta) / (6.0 - 7.0 * delta) /
               ((an * an + 2.0) * (an * an + 2.0));

    double tr = 0.0;
    const float *z  = ctx->atm.z;
    const float *p  = ctx->atm.p;
    const float *t  = ctx->atm.t;
    float ns = 2.54743e19f;
    for (int k = 0; k < NATM - 1; k++) {
        double dppt = (288.15 / 1013.25) * ((double)(p[k] / t[k]) + (double)(p[k+1] / t[k+1])) / 2.0;
        double sr = (a * dppt / (awl * awl * awl * awl) / ns * 1.0e16) * 1.0e5;
        tr += (double)(z[k+1] - z[k]) * sr;
    }
    *tray = (float)tr;
}
