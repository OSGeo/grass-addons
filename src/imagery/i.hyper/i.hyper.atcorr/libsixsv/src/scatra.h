#pragma once
#include "../include/sixs_ctx.h"

/* Compute scattering transmittances and spherical albedo.
 * Ports 6SV2.1 SCATRA.f + ISO.f. */
void sixs_scatra(SixsCtx *ctx,
                  float taer, float taerp, float tray, float trayp,
                  float piza, float palt, int nt, int mu,
                  const float *rm, const float *gb,
                  float xmus, float xmuv,
                  float *ddirtt, float *ddiftt, float *udirtt, float *udiftt, float *sphalbt,
                  float *ddirtr, float *ddiftr, float *udirtr, float *udiftr, float *sphalbr,
                  float *ddirta, float *ddifta, float *udirta, float *udifta, float *sphalba);
