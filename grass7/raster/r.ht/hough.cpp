#include "houghtransform.h"

#include"extract_line.h"
#include "matrix.h"

extern "C" {
namespace grass {
#include <grass/gis.h>
#include <grass/raster.h>
#include <grass/vector.h>
#include <grass/glocale.h>
#include <grass/gmath.h>
}
}

using grass::DCELL;
using grass::CELL;
using grass::G__calloc;
using grass::Cell_head;
using grass::Map_info;

using grass::Vect_new_cats_struct;
using grass::Vect_new_line_struct;

using grass::Rast_allocate_d_input_buf;
using grass::Rast_open_old;
using grass::Rast_get_row;
using grass::Rast_close;

using grass::G_gettext;
using grass::G_fatal_error;
using grass::G_debug;
using grass::G_free;

/** Loads map into memory.

  \param[out] mat map in a matrix (row order), field have to be allocated
  */
void read_raster_map(const char *name, const char *mapset, int nrows,
                            int ncols, Matrix& mat)
{

    int r, c;

    int map_fd;

    DCELL *row_buffer;

    DCELL cell_value;

    row_buffer = Rast_allocate_d_input_buf();

    /* load map */
    map_fd = Rast_open_old(name, mapset);
    if (map_fd < 0) {
        G_fatal_error(_("Error opening first raster map <%s>"), name);
    }

    G_debug(1, "fd %d %s %s", map_fd, name, mapset);

    //    if ((first_map_R_type =
    //         Rast_map_type(templName, mapset)) < 0)
    //        G_fatal_error(_("Error getting first raster map type"));

    for (r = 0; r < nrows; r++) {
        Rast_get_row(map_fd, row_buffer, r, DCELL_TYPE);

        for (c = 0; c < ncols; c++) {
            cell_value = row_buffer[c];
            if (!Rast_is_d_null_value(&cell_value))
                mat(r, c) = cell_value;
            else
                mat(r, c) = 0.0;
        }
    }
    G_free(row_buffer);

    Rast_close(map_fd);
}

/**
  \param cellhd raster map header, used for converting rows/cols to easting/northing
  */
void create_vector_map(const char * name, const SegmentList& segments,
                       const Cell_head* cellhd)
{
    struct Map_info Map;
    Vect_open_new(&Map, name, 0);

    struct grass::line_cats *Cats;
    Cats = Vect_new_cats_struct();

    for (size_t i = 0; i < segments.size(); ++i)
    {
        const Segment& seg = segments[i];

        struct grass::line_pnts *points = Vect_new_line_struct();

        double y1 = Rast_row_to_northing(seg.first.first, cellhd);
        double x1 = Rast_col_to_easting(seg.first.second, cellhd);
        double y2 = Rast_row_to_northing(seg.second.first, cellhd);
        double x2 = Rast_col_to_easting(seg.second.second, cellhd);


        Vect_cat_set(Cats, 1, i+1); // cat is segment number (counting from one)

        Vect_append_point(points, x1, y1, 0);
        Vect_append_point(points, x2, y2, 0);

        Vect_write_line(&Map, GV_LINE, points, Cats);

    }

    Vect_build(&Map);
    Vect_close(&Map);
}

void extract_line_segments(const Matrix &I,
                           const HoughTransform::Peaks& peaks,
                           const HoughTransform::TracebackMap& houghMap,
                           int gap,
                           int minSegmentLength,
                           SegmentList& segments)
{
    for (size_t i = 0; i < peaks.size(); ++i)
    {
        const HoughTransform::Peak& peak = peaks[i];

        double theta = peak.coordinates.second;

        HoughTransform::TracebackMap::const_iterator coordsIt =
                houghMap.find(peak.coordinates);
        if (coordsIt != houghMap.end())
        {
            const HoughTransform::CoordinatesList& lineCoordinates = coordsIt->second;

            extract(I, (theta-90)/180*M_PI, gap, minSegmentLength, lineCoordinates, segments);
        }
        else
        {
            // logic error
        }
    }
}

void hough_peaks(int maxPeaks, int threshold, int sizeOfNeighbourhood,
                 int gap, int minSegmentLength,
                 const char *name, const char *mapset, size_t nrows, size_t ncols,
                 const char *anglesMapName, int angleWidth,
                 const char *result)
{
    Matrix I(nrows, ncols);
    read_raster_map(name, mapset, nrows, ncols, I);

    HoughTransform hough(I);

    if (anglesMapName != NULL)
    {
        Matrix angles(nrows, ncols);
        read_raster_map(anglesMapName, mapset, nrows, ncols, angles);
        hough.compute(angles, angleWidth);
    }
    else
    {
        hough.compute();
    }

    hough.findPeaks(maxPeaks, threshold, sizeOfNeighbourhood);

    const HoughTransform::Peaks& peaks = hough.getPeaks();
    const HoughTransform::TracebackMap& houghMap = hough.getHoughMap();
    SegmentList segments;

    extract_line_segments(I, peaks, houghMap, gap, minSegmentLength, segments);

    Cell_head cellhd;
    Rast_get_window(&cellhd);
    create_vector_map(result, segments, &cellhd);
}
