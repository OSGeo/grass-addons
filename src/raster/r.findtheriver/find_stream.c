#include <math.h>
#include <grass/raster.h>
#include <grass/glocale.h>
#include "global.h"

/**
\brief Find stream pixels in a given window of the UAA raster

\param[in] fd UAA raster file descriptor
\param[in] name Name of UAA raster map
\param[in] mapset Name of the GRASS mapset from which UAA raster should be read
\param[in] dataType Data type of UAA raster
\param[in] windowSize Size of the search window, must be an odd integer >= 3
\param[in] threshold to use for distinguishing stream pixels by comparing
log(UAA) values \param[in] nrows_less_one Number of rows in the current window,
minus 1 \param[in] ncols_less_one Number of columns in the current window, minus
1 \param[in] currRow, Row of pixel that will be compared to pixels in the window
\param[in] currCol, Column of pixel that will be compared to pixels in the
window

\return Pointer to PointList_t representing a list of stream pixels found in the
window
*/
PointList_t *
find_stream_pixels_in_window(int fd, char *name, const char *mapset,
                             RASTER_MAP_TYPE dataType, int windowSize,
                             double threshold, int nrows_less_one,
                             int ncols_less_one, int currRow, int currCol)
{
    PointList_t *streamPixels = NULL;
    DCELL centralValue;
    double logCentralValue;
    void *tmpRow;
    int windowOffset, minCol, maxCol, minRow, maxRow, row, col;

    /* Get value of central cell */
    tmpRow = Rast_allocate_buf(dataType);
    Rast_get_row(fd, tmpRow, currRow, dataType);

    switch (dataType) {
    case FCELL_TYPE:
        centralValue = (double)((FCELL *)tmpRow)[currCol];
        break;
    case DCELL_TYPE:
        centralValue = (double)((DCELL *)tmpRow)[currCol];
        break;
    default:
        centralValue = (double)((CELL *)tmpRow)[currCol];
        break;
    }
    if (centralValue <= 0)
        centralValue = 1;
    logCentralValue = log10(centralValue);

    G_debug(1, "logCentralValue: %f", logCentralValue);

    /* Determine threshold if need be */
    if (-1.0 == threshold) {
        struct FPRange *range;
        double max, logMax;

        range = (struct FPRange *)G_malloc(sizeof(struct FPRange));
        if (Rast_read_fp_range(name, mapset, range) < 0) {
            G_fatal_error(_("Unable to determine range of raster map <%s>"),
                          name);
        }
        max = range->max;

        G_free(range); // eggs or is it chicken?
        if (max == centralValue)
            return streamPixels;

        logMax = log10(max);

        threshold = floor(logMax - logCentralValue);
        if (threshold <= 0.0) {
            threshold = 1.0;
        }
        else if (threshold > 2.0) {
            threshold = 2.0;
        }

        G_debug(1, "logMax: %f", logMax);
    }

    G_verbose_message(_("Threshold: %f\n"), threshold);

    /* Define window bounds */
    windowOffset = (windowSize - 1) / 2;

    minCol = currCol - windowOffset;
    if (minCol < 0)
        minCol = 0;

    maxCol = currCol + windowOffset;
    if (maxCol > ncols_less_one)
        maxCol = ncols_less_one;

    minRow = currRow - windowOffset;
    if (minRow < 0)
        minRow = 0;

    maxRow = currRow + windowOffset;
    if (maxRow > nrows_less_one)
        maxRow = nrows_less_one;

    G_debug(1, "currCol: %d, currRow: %d", currCol, currRow);
    G_debug(1, "min. col: %d, max. col: %d", minCol, maxCol);
    G_debug(1, "min. row: %d, max. row: %d", minRow, maxRow);

    /* Search for stream pixels within the window */
    for (row = minRow; row <= maxRow; row++) {
        G_debug(1, "row: %d", row);
        /* Get the current row */
        Rast_get_row(fd, tmpRow, row, dataType);

        for (col = minCol; col <= maxCol; col++) {
            DCELL tmpValue;
            double logTmpValue;

            G_debug(1, "  col: %d", col);

            switch (dataType) {
            case FCELL_TYPE:
                tmpValue = (double)((FCELL *)tmpRow)[col];
                break;
            case DCELL_TYPE:
                tmpValue = (double)((DCELL *)tmpRow)[col];
                break;
            default:
                tmpValue = (double)((CELL *)tmpRow)[col];
                break;
            }
            logTmpValue = log10(tmpValue);
            /* Test for nearby pixels that are stream pixels when compared to
             * the central pixel */
            G_debug(1, "    tmpValue: %f, centralValue: %f", tmpValue,
                    centralValue);
            G_debug(1, "    logTmpValue: %f, logCentralValue: %f", logTmpValue,
                    logCentralValue);

            if (logTmpValue - logCentralValue > threshold) {
                /* Add to list of stream pixels if the nearby pixel is a stream
                 * pixel */
                if (NULL == streamPixels)
                    streamPixels = create_list(col, row);
                else
                    append_point(streamPixels, col, row);
            }
            else if (logCentralValue - logTmpValue > threshold) {
                /* Add to list of stream pixels if the given pixel itself is a
                 * stream pixel; don't try to find streams somewhere else */
                if (NULL == streamPixels)
                    streamPixels = create_list(currCol, currRow);
                else
                    append_point(streamPixels, currCol, currRow);
            }
        }
    }
    G_free(tmpRow);

    return streamPixels;
}
