#include "houghtransform.h"

#include "linesegmentsextractor.h"
#include "matrix.h"

extern "C" {
#include <grass/gis.h>
#include <grass/raster.h>
#include <grass/vector.h>
#include <grass/glocale.h>
#include <grass/gmath.h>
}

/** Loads map into memory.

  \param[out] mat map in a matrix (row order), field have to be allocated
  */
template <typename Matrix>
void read_raster_map(const char *name, const char *mapset, int nrows, int ncols,
                     Matrix &mat)
{

    int r, c;

    int map_fd;

    CELL *row_buffer;

    CELL cell_value;

    row_buffer = Rast_allocate_c_buf();

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
        Rast_get_row(map_fd, row_buffer, r, CELL_TYPE);

        for (c = 0; c < ncols; c++) {
            cell_value = row_buffer[c];
            if (!Rast_is_c_null_value(&cell_value))
                mat(r, c) = cell_value;
            else
                mat(r, c) = 0.0;
        }
    }
    G_free(row_buffer);

    Rast_close(map_fd);
}

void apply_hough_colors_to_map(const char *name)
{
    struct Colors colors;
    struct Range range;
    CELL min, max;

    Rast_read_range(name, G_mapset(), &range);
    Rast_get_range_min_max(&range, &min, &max);
    Rast_make_grey_scale_colors(&colors, min, max);
    Rast_write_colors(name, G_mapset(), &colors);
}

template <typename Matrix>
void create_raster_map(const char *name, struct Cell_head *window,
                       const Matrix &mat)
{
    struct Cell_head original_window;
    CELL *cell_real;
    int rows, cols; /* number of rows and columns */
    long totsize;
    /* total number of data points */ // FIXME: make clear the size_t usage
    int mapfd;

    /* get the rows and columns in the current window */
    rows = mat.rows();
    cols = mat.columns();
    totsize = rows * cols;

    G_get_set_window(&original_window);

    window->bottom = 0;
    window->top = rows;
    window->cols = cols;
    window->east = cols;
    window->north = rows;
    window->ns_res = 1;
    window->rows = rows;
    window->south = 0;
    window->west = 0;
    window->ew_res = 1;
    window->tb_res = 1;

    Rast_set_window(window);

    /* allocate the space for one row of cell map data */
    cell_real = Rast_allocate_c_buf();

    /* open the output cell maps */
    mapfd = Rast_open_fp_new(name);

    for (int i = 0; i < rows; i++) {
        for (int j = 0; j < cols; j++) {
            cell_real[j] = mat(i, j);
        }
        Rast_put_c_row(mapfd, cell_real);
    }

    Rast_close(mapfd);
    G_free(cell_real);

    Rast_set_window(&original_window);
}

/**
  \param cellhd raster map header, used for converting rows/cols to
  easting/northing
  */
void create_vector_map(const char *name, const SegmentList &segments,
                       const Cell_head *cellhd)
{
    struct Map_info Map;
    Vect_open_new(&Map, name, 0);

    struct line_cats *Cats;
    struct line_pnts *points;
    Cats = Vect_new_cats_struct();
    points = Vect_new_line_struct();

    for (size_t i = 0; i < segments.size(); ++i) {
        const Segment &seg = segments[i];

        double y1 = Rast_row_to_northing(seg.first.first, cellhd);
        double x1 = Rast_col_to_easting(seg.first.second, cellhd);
        double y2 = Rast_row_to_northing(seg.second.first, cellhd);
        double x2 = Rast_col_to_easting(seg.second.second, cellhd);

        Vect_reset_cats(Cats);
        Vect_cat_set(Cats, 1,
                     i + 1); // cat is segment number (counting from one)

        Vect_reset_line(points);
        Vect_append_point(points, x1, y1, 0);
        Vect_append_point(points, x2, y2, 0);

        Vect_write_line(&Map, GV_LINE, points, Cats);
    }

    Vect_destroy_cats_struct(Cats);
    Vect_destroy_line_struct(points);

    Vect_build(&Map);
    Vect_close(&Map);
}

template <typename Matrix>
void extract_line_segments(const Matrix &I, const HoughTransform::Peaks &peaks,
                           const HoughTransform::TracebackMap &houghMap,
                           ExtractParametres extractParametres,
                           SegmentList &segments)
{
    for (size_t i = 0; i < peaks.size(); ++i) {
        const HoughTransform::Peak &peak = peaks[i];

        double theta = peak.coordinates.second;

        HoughTransform::TracebackMap::const_iterator coordsIt =
            houghMap.find(peak.coordinates);
        if (coordsIt != houghMap.end()) {
            const HoughTransform::CoordinatesList &lineCoordinates =
                coordsIt->second;

            LineSegmentsExtractor extractor(I, extractParametres);

            extractor.extract(lineCoordinates, (theta - 90) / 180 * M_PI,
                              segments);
        }
        else {
            // logic error
        }
    }
}

void hough_peaks(HoughParametres houghParametres,
                 ExtractParametres extractParametres, const char *name,
                 const char *mapset, size_t nrows, size_t ncols,
                 const char *anglesMapName, const char *houghImageName,
                 const char *result)
{
    typedef matrix::Matrix<DCELL> Matrix;
    Matrix I(nrows, ncols);
    read_raster_map(name, mapset, nrows, ncols, I);

    HoughTransform hough(I, houghParametres);

    if (anglesMapName != NULL) {
        Matrix angles(nrows, ncols);
        read_raster_map(anglesMapName, mapset, nrows, ncols, angles);
        hough.compute(angles);
    }
    else {
        hough.compute();
    }

    hough.findPeaks();

    if (houghImageName != NULL) {
        struct Cell_head window;
        Rast_get_cellhd(name, "", &window);
        create_raster_map(houghImageName, &window, hough.getHoughMatrix());
        apply_hough_colors_to_map(houghImageName);
    }

    const HoughTransform::Peaks &peaks = hough.getPeaks();
    const HoughTransform::TracebackMap &houghMap = hough.getHoughMap();
    SegmentList segments;

    extract_line_segments(I, peaks, houghMap, extractParametres, segments);

    Cell_head cellhd;
    Rast_get_window(&cellhd);
    create_vector_map(result, segments, &cellhd);
}
