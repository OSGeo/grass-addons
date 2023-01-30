/****************************************************************************
 *
 * MODULE:       r.findtheriver
 *
 * AUTHOR(S):    Brian Miles <brian_miles unc.edu> (May 20, 2013)
 *               Update to GRASS 7 and returning the input cell as needed
 *               by Huidae Cho <grass4u gmail.com>
 *
 * PURPOSE:      Finds the nearest stream pixel to a coordinate pair using an
 *               upstream accumulating area map.
 *
 * COPYRIGHT:    (C) 2013 by the University of North Carolina at Chapel Hill
 *
 *               This program is free software under the GNU General Public
 *               License (>=v2). Read the file COPYING that comes with GRASS
 *               for details.
 *
 *****************************************************************************/

#include <stdlib.h>
#include <string.h>
#include <grass/raster.h>
#include <grass/glocale.h>
#include "global.h"

int main(int argc, char *argv[])
{
    struct GModule *module; /* GRASS module for parsing arguments */
    struct {
        struct Option *input;
        struct Option *window;
        struct Option *threshold;
        struct Option *coords;
        struct Option *separator;
    } opt;
    struct Cell_head cellhd; /* it stores region information,
                                and header information of rasters */
    char name[GNAME_MAX];    /* input raster name */
    const char *mapset;      /* mapset name */
    int nrows, ncols;
    int rowIdx, colIdx, nrows_less_one, ncols_less_one;
    int infd;                  /* file descriptor */
    RASTER_MAP_TYPE data_type; /* type of the map (CELL/DCELL/...) */
    double E, N;
    struct Cell_head window;
    int windowSize;
    double threshold;
    char *sep;
    int debug;

    /* initialize GIS environment */
    G_gisinit(
        argv[0]); /* reads grass env, stores program name to G_program_name() */

    /* initialize module */
    module = G_define_module();
    G_add_keyword(_("raster"));
    G_add_keyword(_("hydrology"));
    module->description =
        _("Find the stream pixel nearest the input coordinate");

    /* Define command options */
    opt.input = G_define_standard_option(G_OPT_R_MAP);
    opt.input->description =
        _("Name of input upstream accumulation area raster map");

    opt.window = G_define_option();
    opt.window->key = "window";
    opt.window->type = TYPE_INTEGER;
    opt.window->key_desc = "x";
    opt.window->multiple = NO;
    opt.window->required = NO;
    opt.window->description =
        _("The size of the window in pixels to search in for stream pixels. "
          "Must be an odd integer. If not supplied, window will be inferred "
          "based on raster resolution.");

    opt.threshold = G_define_option();
    opt.threshold->key = "threshold";
    opt.threshold->type = TYPE_DOUBLE;
    opt.threshold->key_desc = "x";
    opt.threshold->multiple = NO;
    opt.threshold->required = NO;
    opt.threshold->description =
        _("The threshold for distinguishing log(UAA) values of stream and "
          "non-stream pixels. If not supplied, threshold will be inferred from "
          "minimum and maximum raster values.");

    opt.coords = G_define_standard_option(G_OPT_M_COORDS);
    opt.coords->description = _("Coordinates of outlet point");
    opt.coords->required = YES;

    opt.separator = G_define_standard_option(G_OPT_F_SEP);
    opt.separator->answer = "space";

    /* options and flags parser */
    if (G_parser(argc, argv))
        exit(EXIT_FAILURE);

    if (G_getenv_nofatal("DEBUG"))
        debug = atoi(G_getenv_nofatal("DEBUG"));
    else
        debug = 0;

    G_get_window(&window);

    /* stores options and flags to variables */
    strncpy(name, opt.input->answer, GNAME_MAX);

    /* returns NULL if the map was not found in any mapset,
     * mapset name otherwise */
    if ((mapset = G_find_raster(name, "")) == NULL)
        G_fatal_error(_("Raster map <%s> not found"), name);

    /* Determine the inputmap type (CELL/FCELL/DCELL) */
    if ((data_type = Rast_map_type(name, mapset)) < 0)
        G_fatal_error(_("Unable to determine the type of raster map <%s>"),
                      name);

    /* Get raster metadata */
    Rast_get_cellhd(name, mapset, &cellhd);

    if (NULL != opt.window->answer) {
        windowSize = atoi(opt.window->answer);

        if (windowSize < 2 || !(windowSize & 1))
            G_fatal_error(_("Invalid window size %s. Window size must be an "
                            "odd integer >= 3"),
                          opt.window->answer);
    }
    else {
        /* Determine window size */
        double cellRes = (cellhd.ew_res + cellhd.ns_res) / 2;

        windowSize = THRESHOLD_DISTANCE / cellRes;
        if (!(windowSize & 1))
            windowSize++;
    }
    G_verbose_message(_("Stream search window size %d\n"), windowSize);

    if (NULL != opt.threshold->answer) {
        threshold = atof(opt.threshold->answer);

        if (threshold <= 0.0)
            G_fatal_error(_("Invalid threshold %f. Threshold must be > 0.0."),
                          threshold);
    }
    else
        /* Automatically determine the threshold */
        threshold = -1.0;

    if (!G_scan_easting(opt.coords->answers[0], &E, G_projection()))
        G_fatal_error(_("Illegal east coordinate '%s'"),
                      opt.coords->answers[0]);

    if (!G_scan_northing(opt.coords->answers[1], &N, G_projection()))
        G_fatal_error(_("Illegal north coordinate '%s'"),
                      opt.coords->answers[1]);

    G_verbose_message(_("Input coordinates, easting %f, northing %f\n"), E, N);

    sep = G_option_to_separator(opt.separator);

    /* Open the raster - returns file descriptor (>0) */
    if ((infd = Rast_open_old(name, mapset)) < 0)
        G_fatal_error(_("Unable to open raster map <%s>"), name);

    G_get_set_window(&window);
    nrows = Rast_window_rows();
    ncols = Rast_window_cols();
    nrows_less_one = nrows - 1;
    ncols_less_one = ncols - 1;

    rowIdx = (int)Rast_northing_to_row(N, &window);
    colIdx = (int)Rast_easting_to_col(E, &window);

    PointList_t *streamPixels = find_stream_pixels_in_window(
        infd, name, mapset, data_type, windowSize, threshold, nrows_less_one,
        ncols_less_one, rowIdx, colIdx);

    if (debug)
        print_list(streamPixels, " ");

    PointList_t *nearestStreamPixel =
        find_nearest_point(streamPixels, colIdx, rowIdx);

    if (NULL != nearestStreamPixel) {
        double nearestEasting, nearestNorthing;

        if (debug) {
            double nearestValue;
            void *tmpRow = Rast_allocate_buf(data_type);
            int currCol = nearestStreamPixel->col;
            int currRow = nearestStreamPixel->row;

            G_debug(1, "Nearest pixel col: %d, row: %d", currCol, currRow);

            /* Get value of central cell */
            Rast_get_row(infd, tmpRow, currRow, data_type);

            switch (data_type) {
            case FCELL_TYPE:
                nearestValue = (double)((FCELL *)tmpRow)[currCol];
                break;
            case DCELL_TYPE:
                nearestValue = (double)((DCELL *)tmpRow)[currCol];
                break;
            default:
                nearestValue = (double)((CELL *)tmpRow)[currCol];
                break;
            }

            G_debug(1, "Nearest stream pixel UAA value: %f", nearestValue);
            G_free(tmpRow);
        }

        /* Get center of each column */
        nearestEasting =
            Rast_col_to_easting(nearestStreamPixel->col + 0.5, &window);
        nearestNorthing =
            Rast_row_to_northing(nearestStreamPixel->row + 0.5, &window);

        /* Print snapped coordinates */
        fprintf(stdout, "%f%s%f\n", nearestEasting, sep, nearestNorthing);
        fflush(stdout);
    }

    /* closing raster maps */
    Rast_close(infd);

    /* Clean up */
    destroy_list(streamPixels);

    exit(EXIT_SUCCESS);
}
