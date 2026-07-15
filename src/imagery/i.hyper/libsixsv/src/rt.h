#pragma once
#include "../include/sixs_ctx.h"

/* Compute atmospheric path reflectance via SOS with Fourier decomposition.
 * Ports 6SV2.1 OS.f.
 *
 * Key output: xl[0] / xmus = xl(-mu,1) / xmus = roatm (path reflectance)
 * where xl[0] = XL(-mu, 0) in row-major [(2mu+1)*np] layout.
 *
 * rolut may be NULL to skip LUT azimuth table computation. */
void sixs_os(SixsCtx *ctx, int iaer_prof,
             float tamoy, float trmoy, float pizmoy,
             float tamoyp, float trmoyp, float palt,
             float phirad, int nt, int mu, int np, int nfi,
             const float *rm_off, const float *gb_off, const float *rp,
             float *xl, float *xlphim, float *rolut);
