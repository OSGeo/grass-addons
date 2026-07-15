#pragma once
#include "../include/sixs_ctx.h"
void sixs_kernel(const SixsCtx *ctx, int is, int mu,
                  const float *rm_off,
                  double *xpl_off,
                  double *psl,
                  double *bp);
