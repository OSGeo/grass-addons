#pragma once
#include "../include/sixs_ctx.h"

/* Interpolate disc quantities from 20 reference wavelengths to wl (µm).
 * ctx->disc must be filled by sixs_discom() first.
 *
 * T_down_dir_out: optional; if non-NULL receives the direct (beam) component
 *                 of T_down (scattering only, before gas multiplication).
 *                 Pass NULL to skip. */
void sixs_interp(const SixsCtx *ctx, int iaer, float wl,
                  float taer55, float taer55p,
                  float *roatm, float *T_down, float *T_up, float *s_alb,
                  float *tray_out, float *taer_out,
                  float *T_down_dir_out);

/* Interpolate the Q and U Stokes components of the atmospheric path reflectance
 * (roatmq[1], roatmu[1]) from 20 reference wavelengths to wl (µm).
 * Only meaningful after sixs_discom() with ipol=1; returns 0 otherwise.
 * Uses linear (not log-log) interpolation because Q/U can be negative. */
void sixs_interp_polar(const SixsCtx *ctx, float wl,
                        float *roatmq_out, float *roatmu_out);
