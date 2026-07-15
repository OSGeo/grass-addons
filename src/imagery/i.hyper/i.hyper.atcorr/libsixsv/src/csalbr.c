/**
 * \file csalbr.c
 * \brief Rayleigh spherical albedo — ported from 6SV2.1 CSALBR.f.
 */
#include <math.h>

/**
 * \brief Approximation of the first exponential integral E1(τ).
 *
 * Polynomial approximation accurate to 2×10⁻⁷ for 0 < τ < 1.
 *
 * \param[in] xtau  Optical depth τ > 0.
 * \return E1(τ).
 */
static float fintexp1(float xtau) {
    /* E1 integral approximation, accuracy 2e-7 for 0 < xtau < 1 */
    static const float a[6] = {
        -0.57721566f, 0.99999193f, -0.24991055f,
         0.05519968f, -0.00976004f, 0.00107857f
    };
    float xx = a[0];
    float xf = 1.0f;
    for (int i = 1; i <= 5; i++) {
        xf *= xtau;
        xx += a[i] * xf;
    }
    return xx - logf(xtau);
}

/**
 * \brief Approximation of the third exponential integral E3(τ).
 * \param[in] xtau  Optical depth τ.
 * \return E3(τ).
 */
static float fintexp3(float xtau) {
    return (expf(-xtau) * (1.0f - xtau) + xtau * xtau * fintexp1(xtau)) / 2.0f;
}

/**
 * \brief Compute the Rayleigh spherical albedo.
 *
 * Uses the analytical formula (ported from 6SV2.1 CSALBR.f):
 * \f[
 *   s_R(\tau) = \frac{3\tau - E_3(\tau)(4 + 2\tau) + 2 e^{-\tau}}{4 + 3\tau}
 * \f]
 *
 * \param[in]  xtau  Rayleigh optical depth.
 * \param[out] xalb  Rayleigh spherical albedo.
 */
void sixs_csalbr(float xtau, float *xalb) {
    *xalb = (3.0f * xtau - fintexp3(xtau) * (4.0f + 2.0f * xtau) + 2.0f * expf(-xtau))
            / (4.0f + 3.0f * xtau);
}
