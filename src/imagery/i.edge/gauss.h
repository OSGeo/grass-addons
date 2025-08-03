#ifndef GAUSS_H
#define GAUSS_H

#include <grass/gis.h>

int getKernelWidth(const double sigma, double gaussianCutOff);

void gaussKernel(DCELL *gaussKernel, DCELL *diffKernel, int kernelWidth,
                 double kernelRadius);
void gaussConvolution(DCELL *image, DCELL *kernel, DCELL *xConv, DCELL *yConv,
                      int rows, int cols, int kernelWidth);

#endif /* GAUSS_H */
