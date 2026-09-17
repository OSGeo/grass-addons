#pragma once
#include "../include/sixs_ctx.h"

/* Compute Rayleigh optical depth at wavelength wl (µm). */
void sixs_odrayl(const SixsCtx *ctx, float wl, float *tray);
