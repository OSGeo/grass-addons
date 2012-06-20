#ifndef HOUGH_H
#define HOUGH_H

extern "C" {
#include <grass/gis.h>
#include <grass/raster.h>
}

void hough_peaks(int maxPeaks, int threshold, double angleWith, int sizeOfNeighbourhood, int gapSize, int maxNumOfGaps, int gap, int minSegmentLength, const char *name, const char *mapset, size_t nrows, size_t ncols, const char *angleMapName, const char *houghImageName, const char *result);

#endif // HOUGH_H
