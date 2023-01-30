#ifndef HOUGH_H
#define HOUGH_H

#include "houghparameters.h"

#include <cstddef>

using std::size_t;

void hough_peaks(HoughParametres houghParametres,
                 ExtractParametres extractParametres, const char *name,
                 const char *mapset, size_t nrows, size_t ncols,
                 const char *angleMapName, const char *houghImageName,
                 const char *result);

#endif // HOUGH_H
