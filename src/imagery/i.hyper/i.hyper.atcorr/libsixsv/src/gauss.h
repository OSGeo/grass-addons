#pragma once
#include "../include/sixs_ctx.h"

void sixs_gauss(float x1, float x2, float *x, float *w, int n);
void sixs_gauss_setup(int nquad, float *cgaus_S, float *pdgs_S);
