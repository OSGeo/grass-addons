#ifndef CANNY_H
#define CANNY_H

#include <grass/gis.h>

void computeXGradients(DCELL *diffKernel, DCELL *yConv, DCELL *xGradient,
                       int rows, int cols, int kernelWidth);

void computeYGradients(DCELL *diffKernel, DCELL *xConv, DCELL *yGradient,
                       int rows, int cols, int kernelWidth);

void nonmaxSuppresion(DCELL *xGradient, DCELL *yGradient, CELL *magnitude,
                      CELL *angle, int rows, int cols, int kernelWidth,
                      int magnitudeScale, int magnitudeLimit);

void performHysteresis(CELL *edges, CELL *magnitude, int low, int high,
                       int rows, int cols);

void thresholdEdges(CELL *edges, int rows, int cols);

#endif /* CANNY_H */
