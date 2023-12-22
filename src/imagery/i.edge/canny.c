/*
   Canny Edge Detector Implementation
   http://www.tomgibara.com/computer-vision/canny-edge-detector
   Public Domain.

   NOTE from Java source code: The elements of the method below (specifically
   the technique for non-maximal suppression and the technique for gradient
   computation) are derived from an implementation posted in the following forum
   (with the clear intent of others using the code):
   http://forum.java.sun.com/thread.jspa?threadID=546211&start=45&tstart=0
   My code effectively mimics the algorithm exhibited above.
   Since I don't know the providence of the code that was posted it is a
   possibility (though I think a very remote one) that this code violates
   someone's intellectual property rights. If this concerns you feel free to
   contact me for an alternative, though less efficient, implementation.

   NOTE - Citation of forum Terms of Use accoding to http://archive.org/:
   Java Technology Forums
   Sun.com Terms of Use
   http://www.sun.com/termsofuse.html

   4. CONTENT SUBMITTED TO SUN

   4.1 Sun does not claim ownership of the Content You place on the Website and
   shall have no obligation of any kind with respect to such Content.
   Unless otherwise stated herein, or in Sun's Privacy Policy,
   any Content You provide in connection with this Website shall be deemed
   to be provided on a nonconfidential basis. Sun shall be free to use
   or disseminate such Content on an unrestricted basis for any purpose,
   and You grant Sun and all other users of the Website an irrevocable,
   worldwide, royalty-free, nonexclusive license to use, reproduce, modify,
   distribute, transmit, display, perform, adapt,
   resell and publish such Content (including in digital form).
   You represent and warrant that you have proper authorization
   for the worldwide transfer and processing among Sun, its affiliates,
   and third-party providers of any information
   that You may provide on the Website.
 */

#include "canny.h"

#include <math.h>

void computeXGradients(DCELL *diffKernel, DCELL *yConv, DCELL *xGradient,
                       int rows, int cols, int kernelWidth)
{
    int initX = kernelWidth - 1;

    int maxX = cols - (kernelWidth - 1);

    int initY = cols * (kernelWidth - 1);

    size_t maxY = (size_t)cols * (rows - (kernelWidth - 1));

    int x;

    size_t y;

    int i;

    for (x = initX; x < maxX; x++) {
        for (y = initY; y < maxY; y += cols) {
            double sum = 0.;

            size_t index = x + y;

            for (i = 1; i < kernelWidth; i++) {
                sum += diffKernel[i] * (yConv[index - i] - yConv[index + i]);
            }
            xGradient[index] = sum;
        }
    }
}

void computeYGradients(DCELL *diffKernel, DCELL *xConv, DCELL *yGradient,
                       int rows, int cols, int kernelWidth)
{
    int initY = cols * (kernelWidth - 1);

    size_t maxY = (size_t)cols * (rows - (kernelWidth - 1));

    int x;

    size_t y;

    int i;

    for (x = kernelWidth; x < cols - kernelWidth; x++) {
        for (y = initY; y < maxY; y += cols) {
            double sum = 0.0;

            size_t index = x + y;

            int yOffset = cols;

            for (i = 1; i < kernelWidth; i++) {
                sum += diffKernel[i] *
                       (xConv[index - yOffset] - xConv[index + yOffset]);
                yOffset += cols;
            }
            yGradient[index] = sum;
        }
    }
}

static double custom_hypot(double x, double y)
{
    double t;

    x = fabs(x);
    y = fabs(y);

    if (x < y) {
        t = x;
        x = y;
        y = t;
    }

    if (x == 0.0)
        return 0.0;
    if (y == 0.0)
        return x;
    return x * sqrt(1 + (y / x) * (y / x));
}

/*
 * An explanation of what's happening here, for those who want
 * to understand the source: This performs the "non-maximal
 * supression" phase of the Canny edge detection in which we
 * need to compare the gradient magnitude to that in the
 * direction of the gradient; only if the value is a local
 * maximum do we consider the point as an edge candidate.
 *
 * We need to break the comparison into a number of different
 * cases depending on the gradient direction so that the
 * appropriate values can be used. To avoid computing the
 * gradient direction, we use two simple comparisons: first we
 * check that the partial derivatives have the same sign (1)
 * and then we check which is larger (2). As a consequence, we
 * have reduced the problem to one of four identical cases that
 * each test the central gradient magnitude against the values at
 * two points with 'identical support'; what this means is that
 * the geometry required to accurately interpolate the magnitude
 * of gradient function at those points has an identical
 * geometry (upto right-angled-rotation/reflection).
 *
 * When comparing the central gradient to the two interpolated
 * values, we avoid performing any divisions by multiplying both
 * sides of each inequality by the greater of the two partial
 * derivatives. The common comparand is stored in a temporary
 * variable (3) and reused in the mirror case (4).
 *
 */
static int isLocalMax(double xGrad, double yGrad, double gradMag, double neMag,
                      double seMag, double swMag, double nwMag, double nMag,
                      double eMag, double sMag, double wMag)
{
    double tmp, tmp1, tmp2;

    if (xGrad * yGrad <= 0.0f) {
        if (fabs(xGrad) >= fabs(yGrad)) {
            tmp = fabs(xGrad * gradMag);
            tmp1 = fabs(yGrad * neMag - (xGrad + yGrad) * eMag) /*(3) */;
            tmp2 = fabs(yGrad * swMag - (xGrad + yGrad) * wMag) /*(4) */;
        }
        else {
            tmp = fabs(yGrad * gradMag);
            tmp1 = fabs(xGrad * neMag - (yGrad + xGrad) * nMag) /*(3) */;
            tmp2 = fabs(xGrad * swMag - (yGrad + xGrad) * sMag) /*(4) */;
        }
    }
    else {
        if (fabs(xGrad) >= fabs(yGrad) /*(2) */) {
            tmp = fabs(xGrad * gradMag);
            tmp1 = fabs(yGrad * seMag + (xGrad - yGrad) * eMag) /*(3) */;
            tmp2 = fabs(yGrad * nwMag + (xGrad - yGrad) * wMag) /*(4) */;
        }
        else {
            tmp = fabs(yGrad * gradMag);
            tmp1 = fabs(xGrad * seMag + (yGrad - xGrad) * sMag) /*(3) */;
            tmp2 = fabs(xGrad * nwMag + (yGrad - xGrad) * nMag) /*(4) */;
        }
    }
    if (tmp >= tmp1 && tmp > tmp2) {
        return 1;
    }
    return 0;
}

void nonmaxSuppresion(DCELL *xGradient, DCELL *yGradient, CELL *magnitude,
                      CELL *angle, int rows, int cols, int kernelWidth,
                      int magnitudeScale, int magnitudeLimit)
{
    int initX = kernelWidth;

    int maxX = cols - kernelWidth;

    int initY = cols * kernelWidth;

    size_t maxY = cols * (rows - kernelWidth);

    int x;

    size_t y;

    int MAGNITUDE_MAX = magnitudeScale * magnitudeLimit;

    for (x = initX; x < maxX; x++) {
        for (y = initY; y < maxY; y += cols) {
            size_t index = x + y;

            int indexN = index - cols;

            int indexS = index + cols;

            int indexW = index - 1;

            int indexE = index + 1;

            int indexNW = indexN - 1;

            int indexNE = indexN + 1;

            int indexSW = indexS - 1;

            int indexSE = indexS + 1;

            double xGrad = xGradient[index];

            double yGrad = yGradient[index];

            double gradMag = custom_hypot(xGrad, yGrad);

            /* perform non-maximal supression */
            double nMag = custom_hypot(xGradient[indexN], yGradient[indexN]);

            double sMag = custom_hypot(xGradient[indexS], yGradient[indexS]);

            double wMag = custom_hypot(xGradient[indexW], yGradient[indexW]);

            double eMag = custom_hypot(xGradient[indexE], yGradient[indexE]);

            double neMag = custom_hypot(xGradient[indexNE], yGradient[indexNE]);

            double seMag = custom_hypot(xGradient[indexSE], yGradient[indexSE]);

            double swMag = custom_hypot(xGradient[indexSW], yGradient[indexSW]);

            double nwMag = custom_hypot(xGradient[indexNW], yGradient[indexNW]);

            if (isLocalMax(xGrad, yGrad, gradMag, neMag, seMag, swMag, nwMag,
                           nMag, eMag, sMag, wMag)) {
                magnitude[index] = gradMag >= magnitudeLimit
                                       ? MAGNITUDE_MAX
                                       : (int)(magnitudeScale * gradMag + 0.5);
                /*
                   NOTE: The orientation of the edge is not employed by this
                   implementation. It is a simple matter to compute it at
                   this point as: Math.atan2(yGrad, xGrad);
                 */
                if (angle != NULL) {
                    /* angle of gradient (mathematical axes) */
                    angle[index] =
                        (int)(-atan2(yGrad, xGrad) * 180 / M_PI + 0.5);
                }
            }
            else {
                magnitude[index] = 0;
            }
        }
    }
}

static void follow(CELL *edges, CELL *magnitude, int x1, int y1, int i1,
                   int threshold, int rows, int cols)
{
    int x0 = x1 == 0 ? x1 : x1 - 1;

    int x2 = x1 == cols - 1 ? x1 : x1 + 1;

    int y0 = y1 == 0 ? y1 : y1 - 1;

    int y2 = y1 == rows - 1 ? y1 : y1 + 1;

    int x;

    int y;

    edges[i1] = magnitude[i1];
    for (x = x0; x <= x2; x++) {
        for (y = y0; y <= y2; y++) {
            int i2 = x + y * cols;

            if ((y != y1 || x != x1) && edges[i2] == 0 &&
                magnitude[i2] >= threshold) {
                follow(edges, magnitude, x, y, i2, threshold, rows, cols);
                return;
            }
        }
    }
}

/* edges.fill(0) */
void performHysteresis(CELL *edges, CELL *magnitude, int low, int high,
                       int rows, int cols)
{
    /*
       NOTE: this implementation reuses the data array to store both
       luminance data from the image, and edge intensity from the processing.
       This is done for memory efficiency, other implementations may wish
       to separate these functions.
     */

    int x;

    int y;

    int offset = 0;

    for (y = 0; y < rows; y++) {
        for (x = 0; x < cols; x++) {
            if (edges[offset] == 0 && magnitude[offset] >= high) {
                follow(edges, magnitude, x, y, offset, low, rows, cols);
            }
            offset++;
        }
    }
}

void thresholdEdges(CELL *edges, int rows, int cols)
{
    size_t i;
    size_t max = (size_t)rows * cols;

    for (i = 0; i < max; i++) {
        edges[i] = edges[i] > 0 ? 1 : 0;
    }
}
