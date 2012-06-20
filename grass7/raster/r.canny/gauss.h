#ifndef GAUSS_H
#define GAUSS_H

#include <grass/gis.h>

int getKernelWidth(const float sigma, float gaussianCutOff);

void gaussKernel(DCELL * gaussKernel, DCELL * diffKernel,
		 int kernelWidth, float kernelRadius);
void gaussConvolution(DCELL * image, DCELL * kernel, DCELL * xConv,
		      DCELL * yConv, int rows, int cols, int kernelWidth);

#endif /* GAUSS_H */
