#pragma once
#include "../include/sixs_ctx.h"

/* Vector (Stokes I,Q,U) successive orders RT — ported from 6SV2.1 OSPOL.f.
 *
 * Like sixs_os() but propagates all three Stokes components simultaneously,
 * giving a more accurate atmospheric path reflectance xl[-mu,1]/xmus for
 * the I component (the scalar version ignores Rayleigh polarisation feedback).
 *
 * The Q and U components are returned in xlq and xlu, which have the same
 * layout as xl: [(2mu+1)*np] row-major, with xl[0] = xl(-mu,1).
 *
 * xlq and xlu may be NULL if only the I component is needed. */
void sixs_ospol(SixsCtx *ctx, int iaer_prof,
                float tamoy, float trmoy, float pizmoy,
                float tamoyp, float trmoyp, float palt,
                float phirad, int nt, int mu, int np, int nfi,
                const float *rm_off, const float *gb_off, const float *rp,
                float *xl,      /* I component: [(2mu+1)*np] */
                float *xlq,     /* Q component: [(2mu+1)*np], may be NULL */
                float *xlu,     /* U component: [(2mu+1)*np], may be NULL */
                float *xlphim); /* I vs azimuth [nfi] */
