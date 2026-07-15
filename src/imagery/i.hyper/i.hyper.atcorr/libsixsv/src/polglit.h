#pragma once

/* Polarized surface reflectance models — ported from 6SV2.1 POLGLIT.f and POLNAD.f.
 *
 * Both functions compute the Q and U Stokes parameters of the polarized surface
 * reflectance for use as boundary conditions in sixs_ospol().
 *
 * ropq: Q component of polarized surface reflectance (0 for Lambertian)
 * ropu: U component of polarized surface reflectance (0 for Lambertian) */

/* Ocean glint surface polarization (Cox-Munk anisotropic wave-facet model).
 *   xts:  solar zenith angle (degrees)
 *   xtv:  view zenith angle (degrees)
 *   phi:  relative azimuth sun→view (degrees)
 *   wspd: wind speed (m/s)
 *   azw:  sun azimuth − wind direction (degrees) */
void sixs_polglit(float xts, float xtv, float phi, float wspd, float azw,
                   float *ropq, float *ropu);

/* Nadal-Breon vegetation/soil polarization model (leaf/soil Fresnel, N=1.5).
 *   xts:  solar zenith angle (degrees)
 *   xtv:  view zenith angle (degrees)
 *   phi:  relative azimuth (degrees)
 *   pveg: vegetation fraction (0 = bare soil, 1 = full canopy) */
void sixs_polnad(float xts, float xtv, float phi, float pveg,
                  float *ropq, float *ropu);
