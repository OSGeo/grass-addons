/* Solar irradiance (E0) and Earth-Sun distance from 6SV2.1 data.
 * These functions are part of the public library so Python ctypes bindings
 * can call them independently. */
#define _GNU_SOURCE
#include "solar_table.h"
#include <math.h>

/**
 * \brief Return top-of-atmosphere solar irradiance at 1 AU.
 *
 * Linearly interpolates the Thuillier 2003 solar spectrum (as tabulated in
 * 6SV2.1) to the requested wavelength.  The table covers 0.25–4.0 µm at a
 * 0.0025 µm step (1501 points).  Values outside the range are clamped to the
 * nearest table boundary.
 *
 * \param[in]  wl_um  Wavelength in µm.
 * \return Solar irradiance \f$E_0\f$ in W m⁻² µm⁻¹ at 1 AU.
 */
float sixs_E0(float wl_um)
{
    float t = (wl_um - (float)SOLAR_TABLE_WL_START) / (float)SOLAR_TABLE_STEP;
    int   i = (int)t;
    float f = t - (float)i;

    if (i < 0)                  return solar_si[0];
    if (i >= SOLAR_TABLE_N - 1) return solar_si[SOLAR_TABLE_N - 1];
    return solar_si[i] * (1.0f - f) + solar_si[i + 1] * f;
}

/**
 * \brief Compute the squared Earth-Sun distance for a given day of year.
 *
 * Uses the first-order eccentricity approximation:
 * \f[
 *   d = 1 - 0.01670963 \cos\!\left(\frac{2\pi(\text{doy}-3)}{365}\right)
 * \f]
 * The return value is \f$d^2\f$ (in AU²), which is the factor by which
 * top-of-atmosphere irradiance is divided relative to the mean Earth-Sun
 * distance (i.e. \f$E = E_0 / d^2\f$).
 *
 * \param[in]  doy  Day of year (1–365).
 * \return \f$d^2\f$ in AU² (~0.967 in January, ~1.034 in July).
 */
double sixs_earth_sun_dist2(int doy)
{
    double beta = 2.0 * M_PI * (doy - 3) / 365.0;
    double d    = 1.0 - 0.01670963 * cos(beta);
    return d * d;
}
