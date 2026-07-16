#pragma once
#include "../include/sixs_ctx.h"

/* Decompose ctx->polar.pha[] into Legendre coefficients ctx->polar.betal[].
 * ipol: 0 = scalar only. Sets *coeff = 0 (no truncation). */
void sixs_trunca(SixsCtx *ctx, int ipol, float *coeff);
