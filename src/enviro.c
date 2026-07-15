/* Environmental reflectance correction — ported from 6SV2.1 ENVIRO.f.
 *
 * Computes the fraction of diffuse irradiance originating from the
 * neighbourhood of the target pixel (adjacency effect correction factors)
 * as a function of sensor altitude and aerosol+Rayleigh optical depths. */
#include <math.h>

/* Altitude grid (16 levels, km) and polynomial coefficients.
 * cfr1,cfr2  : Rayleigh contribution coefficients
 * cfa1,cfa2,cfa3: aerosol contribution coefficients
 * (nadir-view look-up table, corrected for view-angle effect below). */
static const float alt_lut[16] = {
    0.5f,1.0f,2.0f,3.0f,4.0f,5.0f,6.0f,7.0f,8.0f,
    10.0f,12.0f,14.0f,16.0f,18.0f,20.0f,60.0f
};
static const float cfr1[16] = {
    0.730f,0.710f,0.656f,0.606f,0.560f,0.516f,0.473f,
    0.433f,0.395f,0.323f,0.258f,0.209f,0.171f,0.142f,0.122f,0.070f
};
static const float cfr2[16] = {
    2.8f,1.51f,0.845f,0.634f,0.524f,0.465f,0.429f,
    0.405f,0.390f,0.386f,0.409f,0.445f,0.488f,0.545f,0.608f,0.868f
};
static const float cfa1[16] = {
    0.239f,0.396f,0.588f,0.626f,0.612f,0.505f,0.454f,
    0.448f,0.444f,0.445f,0.444f,0.448f,0.448f,0.448f,0.448f,0.448f
};
static const float cfa2[16] = {
    1.40f,1.20f,1.02f,0.86f,0.74f,0.56f,0.46f,0.42f,
    0.38f,0.34f,0.3f,0.28f,0.27f,0.27f,0.27f,0.27f
};
static const float cfa3[16] = {
    9.17f,6.26f,5.48f,5.16f,4.74f,3.65f,3.24f,3.15f,
    3.07f,2.97f,2.88f,2.83f,2.83f,2.83f,2.83f,2.83f
};

/**
 * \brief Compute environmental reflectance correction factors (adjacency effect).
 *
 * Calculates the Rayleigh (\c fra) and aerosol (\c fae) environmental
 * correction functions and their weighted combination (\c fr) using the
 * polynomial look-up table from 6SV2.1 ENVIRO.f.
 *
 * Ported from 6SV2.1 ENVIRO.f.
 *
 * \param[in]  difr  Diffuse Rayleigh OD at the target wavelength.
 * \param[in]  difa  Diffuse aerosol OD at the target wavelength.
 * \param[in]  r     Total aerosol OD at 550 nm (for the nadir-view LUT lookup).
 * \param[in]  palt  Sensor altitude in km.
 * \param[in]  xmuv  Cosine of the view zenith angle.
 * \param[out] fra   Rayleigh environmental correction fraction.
 * \param[out] fae   Aerosol environmental correction fraction.
 * \param[out] fr    Combined fraction (weighted average of fra and fae).
 */
void sixs_enviro(float difr, float difa, float r, float palt, float xmuv,
                 float *fra, float *fae, float *fr)
{
    const float a0 =  1.3347f,  b0 = 0.57757f;
    const float a1 = -1.479f,   b1 = -1.5275f;

    float fae0, fra0;

    if (palt >= 60.0f) {
        /* Above 60 km: use asymptotic coefficients */
        fae0 = 1.0f - 0.448f * expf(-r * 0.27f)  - 0.552f * expf(-r * 2.83f);
        fra0 = 1.0f - 0.930f * expf(-r * 0.080f) - 0.070f * expf(-r * 1.100f);
    } else {
        /* Find bracketing altitude levels */
        int idx = 0;
        while (idx < 15 && palt >= alt_lut[idx]) idx++;
        /* idx points to first level with alt_lut[idx] > palt */

        float xcfr1_v, xcfr2_v, xcfa1_v, xcfa2_v, xcfa3_v;
        if (idx == 0) {
            /* Below lowest level */
            xcfr1_v = cfr1[0]; xcfr2_v = cfr2[0];
            xcfa1_v = cfa1[0]; xcfa2_v = cfa2[0]; xcfa3_v = cfa3[0];
        } else {
            /* Linear interpolation between idx-1 and idx */
            float zmin = alt_lut[idx - 1];
            float zmax = alt_lut[idx];
            float t    = (palt - zmin) / (zmax - zmin);
            xcfr1_v = cfr1[idx-1] + (cfr1[idx] - cfr1[idx-1]) * t;
            xcfr2_v = cfr2[idx-1] + (cfr2[idx] - cfr2[idx-1]) * t;
            xcfa1_v = cfa1[idx-1] + (cfa1[idx] - cfa1[idx-1]) * t;
            xcfa2_v = cfa2[idx-1] + (cfa2[idx] - cfa2[idx-1]) * t;
            xcfa3_v = cfa3[idx-1] + (cfa3[idx] - cfa3[idx-1]) * t;
        }
        fra0 = 1.0f - xcfr1_v * expf(-r * xcfr2_v)
                    - (1.0f - xcfr1_v) * expf(-r * 0.08f);
        fae0 = 1.0f - xcfa1_v * expf(-r * xcfa2_v)
                    - (1.0f - xcfa1_v) * expf(-r * xcfa3_v);
    }

    /* View-angle correction */
    float xlnv = logf(xmuv);
    *fra = fra0 * (xlnv * (1.0f - fra0) + 1.0f);
    *fae = fae0 * ((1.0f + a0*xlnv + b0*xlnv*xlnv)
                 + fae0 * (a1*xlnv + b1*xlnv*xlnv)
                 + fae0*fae0 * ((-a1 - a0)*xlnv + (-b1 - b0)*xlnv*xlnv));

    /* Combined factor weighted by diffuse OD contributions */
    if ((difa + difr) > 1.0e-3f) {
        *fr = (*fae * difa + *fra * difr) / (difa + difr);
    } else {
        *fr = 1.0f;
    }
}
