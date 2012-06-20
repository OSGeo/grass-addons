#ifndef HOUGH_H
#define HOUGH_H

extern "C" {
#include <grass/gis.h>
#include <grass/raster.h>
}

void hough_peaks(int maxPeaks, int threshold, int sizeOfNeighbourhood, int gap, int minSegmentLength, const char * name, const char* mapset, size_t nrows, size_t ncols, const char * angleMapName, int angleWidth, const char * result);

#endif // HOUGH_H
