#include "gauss.h"

#include <math.h>

#include <grass/gis.h>

int getKernelWidth(const double sigma, double gaussianCutOff)
{
    return (int)ceil(sqrt(-2 * sigma * sigma * log(gaussianCutOff)));
}

static double gaussian(double x, double sigma)
{
    return exp(-(x * x) / (2.0 * sigma * sigma));
}

void gaussKernel(DCELL *gaussKernel, DCELL *diffKernel, int kernelWidth,
                 double kernelRadius)
{
    int kwidth;

    for (kwidth = 0; kwidth < kernelWidth; kwidth++) {
        double g1 = gaussian(kwidth, kernelRadius);

        double g2 = gaussian(kwidth - 0.5, kernelRadius);

        double g3 = gaussian(kwidth + 0.5, kernelRadius);

        gaussKernel[kwidth] =
            (g1 + g2 + g3) / 3. /
            (2.0 * (double)M_PI * kernelRadius * kernelRadius);
        diffKernel[kwidth] = g3 - g2;
    }
}

void gaussConvolution(DCELL *image, DCELL *kernel, DCELL *xConv, DCELL *yConv,
                      int rows, int cols, int kernelWidth)
{
    int x;
    size_t y;

    int initX = kernelWidth - 1;

    int maxX = cols - (kernelWidth - 1);

    int initY = cols * (kernelWidth - 1);

    size_t maxY = (size_t)cols * (rows - (kernelWidth - 1));

    /* perform convolution in x and y directions */
    for (x = initX; x < maxX; x++) {
        for (y = initY; y < maxY; y += cols) {
            size_t index = x + y;

            double sumX = image[index] * kernel[0];

            double sumY = sumX;

            int xOffset = 1;

            int yOffset = cols;

            for (; xOffset < kernelWidth;) {
                sumY += kernel[xOffset] *
                        (image[index - yOffset] + image[index + yOffset]);
                sumX += kernel[xOffset] *
                        (image[index - xOffset] + image[index + xOffset]);
                yOffset += cols;
                xOffset++;
            }
            yConv[index] = sumY;
            xConv[index] = sumX;
        }
    }
}
