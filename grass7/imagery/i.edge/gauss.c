#include "gauss.h"

#include <math.h>

#include <grass/gis.h>

int getKernelWidth(const float sigma, float gaussianCutOff)
{
    return ceil(sqrt(-2 * sigma * sigma * log(gaussianCutOff)));
}

static float gaussian(float x, float sigma)
{
    return exp(-(x * x) / (2.0 * sigma * sigma));
}

void gaussKernel(DCELL * gaussKernel, DCELL * diffKernel,
		 int kernelWidth, float kernelRadius)
{
    int kwidth;

    for (kwidth = 0; kwidth < kernelWidth; kwidth++) {
	float g1 = gaussian(kwidth, kernelRadius);

	float g2 = gaussian(kwidth - 0.5, kernelRadius);

	float g3 = gaussian(kwidth + 0.5, kernelRadius);

	gaussKernel[kwidth] =
	    (g1 + g2 +
	     g3) / 3. / (2.0 * (float)M_PI * kernelRadius * kernelRadius);
	diffKernel[kwidth] = g3 - g2;
    }
}

void gaussConvolution(DCELL * image, DCELL * kernel, DCELL * xConv,
		      DCELL * yConv, int rows, int cols, int kernelWidth)
{
    int x, y;

    int initX = kernelWidth - 1;

    int maxX = cols - (kernelWidth - 1);

    int initY = cols * (kernelWidth - 1);

    int maxY = cols * (rows - (kernelWidth - 1));

    //perform convolution in x and y directions
    for (x = initX; x < maxX; x++) {
	for (y = initY; y < maxY; y += cols) {
	    int index = x + y;

	    float sumX = image[index] * kernel[0];

	    float sumY = sumX;

	    int xOffset = 1;

	    int yOffset = cols;

	    for (; xOffset < kernelWidth;) {
		sumY +=
		    kernel[xOffset] * (image[index - yOffset] +
				       image[index + yOffset]);
		sumX +=
		    kernel[xOffset] * (image[index - xOffset] +
				       image[index + xOffset]);
		yOffset += cols;
		xOffset++;
	    }
	    yConv[index] = sumY;
	    xConv[index] = sumX;
	}
    }
}
