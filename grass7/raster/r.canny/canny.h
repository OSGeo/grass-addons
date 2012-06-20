#ifndef CANNY_H
#define CANNY_H

#include <grass/gis.h>

void computeXGradients(DCELL * diffKernel, DCELL * yConv, DCELL * xGradient,
		       int rows, int cols, int kernelWidth);

void computeYGradients(DCELL * diffKernel, DCELL * xConv, DCELL * yGradient,
		       int rows, int cols, int kernelWidth);

void nonmaxSuppresion(DCELL * xGradient, DCELL * yGradient, DCELL * magnitude,
		      DCELL *angle, int rows, int cols,
		      int kernelWidth, float magnitudeScale, float magnitudeLimit);

void performHysteresis(DCELL * edges, DCELL * magnitude,
		       int low, int high, int rows, int cols);

void thresholdEdges(DCELL * edges, int rows, int cols);

#endif /* CANNY_H */
