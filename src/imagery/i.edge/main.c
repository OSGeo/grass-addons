/****************************************************************************
 *
 * MODULE:       i.edge
 * AUTHOR(S):    Anna Kratochvilova - kratochanna gmail.com
 *               Vaclav Petras - wenzeslaus gmail.com
 *
 * PURPOSE:      Edge detection in raster images.
 *
 * COPYRIGHT:    (C) 2012-2021 by the GRASS Development Team
 *
 *               This program is free software under the GNU General Public
 *                        License (>=v2). Read the file COPYING that comes with
 *GRASS for details.
 *
 *****************************************************************************/

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <grass/gis.h>
#include <grass/raster.h>
#include <grass/glocale.h>

#include <grass/gmath.h>

#include <math.h>

#include "canny.h"
#include "gauss.h"

/** Loads map into memory.

  \param[out] mat map in a matrix (row order), field have to be allocated
  */
static int readMap(const char *name, const char *mapset, int nrows, int ncols,
                   DCELL *mat)
{
    int r, c;
    int map_fd;
    int check_reading;
    DCELL *row_buffer;
    DCELL cell_value;

    row_buffer = Rast_allocate_d_input_buf();
    check_reading = 0;

    /* load map */
    map_fd = Rast_open_old(name, mapset);
    if (map_fd < 0) {
        G_fatal_error(_("Error opening first raster map <%s>"), name);
    }

    G_debug(1, "fd %d %s %s", map_fd, name, mapset);

    /*
       if ((first_map_R_type =
       Rast_map_type(templName, mapset)) < 0)
       G_fatal_error(_("Error getting first raster map type"));
     */

    for (r = 0; r < nrows; r++) {
        Rast_get_row(map_fd, row_buffer, r, DCELL_TYPE);

        for (c = 0; c < ncols; c++) {
            cell_value = row_buffer[c];
            size_t index = ((size_t)ncols * r) + c;

            if (!Rast_is_d_null_value(&cell_value))
                mat[index] = cell_value;
            else
                mat[index] = 0.0;

            if (mat[index])
                check_reading = 1;
        }
    }
    G_free(row_buffer);

    Rast_close(map_fd);

    return check_reading;
}

/** Writes map from memory into the file.

  \param[in] map map in a matrix (row order)
  */
static void writeMap(const char *name, int nrows, int ncols, CELL *map)
{
    unsigned char *outrast; /* output buffer */
    int outfd;
    int r, c;

    outfd = Rast_open_new(
        name, CELL_TYPE); /* FIXME: using both open old and open new */

    outrast = Rast_allocate_buf(CELL_TYPE);
    for (r = 0; r < nrows; r++) {
        for (c = 0; c < ncols; c++) {
            size_t index = (size_t)r * ncols + c;

            CELL value = map[index];

            ((CELL *)outrast)[c] = value;
        }
        Rast_put_row(outfd, outrast, CELL_TYPE);
    }
    G_free(outrast);

    Rast_close(outfd);
}

/**

  \todo Floats are used instead of doubles.
  \todo Be able to work with FCELL (and CELL?).
  */
int main(int argc, char *argv[])
{
    struct Cell_head cell_head; /* it stores region information,
                                   and header information of rasters */
    char *name;                 /* input raster name */
    char *mapset;               /* mapset name */
    int kernelWidth;
    double kernelRadius;
    char *result; /* output raster name */
    char *anglesMapName;

    static const double GAUSSIAN_CUT_OFF = 0.005;
    static const int MAGNITUDE_SCALE = 100;
    static const int MAGNITUDE_LIMIT = 1000;

    int lowThreshold, highThreshold, low, high;
    int nrows, ncols, i;
    size_t dim_2;
    DCELL *mat1;

    struct History history; /* holds meta-data (title, comments,..) */
    struct GModule *module; /* GRASS module for parsing arguments */

    /* options */
    struct Option *input, *output, *angleOutput, *lowThresholdOption,
        *highThresholdOption, *sigmaOption;
    struct Flag *nullflag;

    size_t r;

    /* initialize GIS environment */
    G_gisinit(
        argv[0]); /* reads grass env, stores program name to G_program_name() */

    /* initialize module */
    module = G_define_module();
    G_add_keyword(_("raster"));
    G_add_keyword(_("canny"));
    G_add_keyword(_("edge detection"));
    module->description = _("Canny edge detector.");

    /* Define the different options as defined in gis.h */
    input = G_define_standard_option(G_OPT_R_INPUT);

    output = G_define_standard_option(G_OPT_R_OUTPUT);

    angleOutput = G_define_standard_option(G_OPT_R_OUTPUT);
    angleOutput->key = "angles_map";
    angleOutput->required = NO;
    angleOutput->description = _("Map with angles");
    angleOutput->guisection = _("Outputs");

    lowThresholdOption = G_define_option();
    lowThresholdOption->key = "low_threshold";
    lowThresholdOption->type = TYPE_DOUBLE;
    lowThresholdOption->required = NO;
    lowThresholdOption->multiple = NO;
    lowThresholdOption->description = _("Low treshold for edges in Canny");
    lowThresholdOption->answer = "3";
    /*    lowThresholdOption->options = "1-10"; */

    highThresholdOption = G_define_option();
    highThresholdOption->key = "high_threshold";
    highThresholdOption->type = TYPE_DOUBLE;
    highThresholdOption->required = NO;
    highThresholdOption->multiple = NO;
    highThresholdOption->description = _("High treshold for edges in Canny");
    highThresholdOption->answer = "10";
    /*    lowThresholdOption->options = "1-10"; */

    sigmaOption = G_define_option();
    sigmaOption->key = "sigma";
    sigmaOption->type = TYPE_DOUBLE;
    sigmaOption->required = NO;
    sigmaOption->multiple = NO;
    sigmaOption->description = _("Kernel radius");
    sigmaOption->answer = "2";

    nullflag = G_define_flag();
    nullflag->key = 'n';
    nullflag->label = _("Create empty output if input map is empty");
    nullflag->description = _("Default: no output and ERROR");

    /* options and flags parser */
    if (G_parser(argc, argv))
        exit(EXIT_FAILURE);

    lowThreshold = (int)(atof(lowThresholdOption->answer) + 0.5);
    highThreshold = (int)(atof(highThresholdOption->answer) + 0.5);

    low = (int)((lowThreshold * MAGNITUDE_SCALE) + 0.5);
    high = (int)((highThreshold * MAGNITUDE_SCALE) + 0.5);

    kernelRadius = atoi(sigmaOption->answer);

    result = output->answer;

    /* stores options and flags to variables */
    name = input->answer;

    anglesMapName = angleOutput->answer;

    /* returns NULL if the map was not found in any mapset,
     * mapset name otherwise */
    mapset = (char *)G_find_raster2(name, "");
    if (mapset == NULL)
        G_fatal_error(_("Raster map <%s> not found"), name);

    /* determine the inputmap type (CELL/FCELL/DCELL) */
    /* data_type = Rast_map_type(name, mapset); */

    /* Rast_open_old - returns file destriptor (>0) */
    /*    infd = Rast_open_old(name, mapset); */

    /*    struct Cell_head templCellhd; */

    /*    Rast_get_cellhd(name, mapset, &cellhd); */
    /*    Rast_get_cellhd(first_map_R_name, first_map_R_mapset, &cellhd_zoom1);
     */

    /* controlling, if we can open input raster */
    Rast_get_cellhd(name, mapset, &cell_head);
    G_debug(3, "number of rows %d", cell_head.rows);

    nrows = Rast_window_rows();
    ncols = Rast_window_cols();
    dim_2 = (size_t)nrows * ncols;

    /* Memory allocation for map_1: */
    mat1 = (DCELL *)G_calloc((dim_2), sizeof(DCELL));

    /* FIXME: it is necessary? */
    for (r = 0; r < dim_2; r++) {
        mat1[r] = 0.0;
    }

    /*
       if ((first_map_R_type =
       Rast_map_type(templName, mapset)) < 0)
       G_fatal_error(_("Error getting first raster map type"));
     */

    if (!readMap(name, mapset, nrows, ncols, mat1)) {
        if (!nullflag->answer)
            G_fatal_error(_("Input map contains no data"));
        else {
            int outfd;
            CELL *outrast; /* output buffer */

            outfd = Rast_open_new(result, CELL_TYPE);

            outrast = Rast_allocate_buf(CELL_TYPE);
            Rast_set_c_null_value(outrast, ncols);
            for (i = 0; i < nrows; i++) {
                Rast_put_row(outfd, outrast, CELL_TYPE);
            }

            Rast_close(outfd);
            /* add command line incantation to history file */
            Rast_short_history(result, "raster", &history);
            Rast_command_history(&history);
            Rast_write_history(result, &history);

            if (anglesMapName) {
                outfd = Rast_open_new(anglesMapName, CELL_TYPE);

                for (i = 0; i < nrows; i++) {
                    Rast_put_row(outfd, outrast, CELL_TYPE);
                }

                Rast_close(outfd);
                /* add command line incantation to history file */
                Rast_short_history(anglesMapName, "raster", &history);
                Rast_command_history(&history);
                Rast_write_history(anglesMapName, &history);
            }

            G_free(outrast);

            exit(EXIT_SUCCESS);
        }
    }

    /* **** */

    kernelWidth = getKernelWidth(kernelRadius, GAUSSIAN_CUT_OFF);

    DCELL *kernel;
    DCELL *diffKernel;

    kernel = (DCELL *)G_calloc((kernelWidth), sizeof(DCELL));
    diffKernel = (DCELL *)G_calloc((kernelWidth), sizeof(DCELL));
    gaussKernel(kernel, diffKernel, kernelWidth, kernelRadius);

    DCELL *yConv = (DCELL *)G_calloc((dim_2), sizeof(DCELL));
    DCELL *xConv = (DCELL *)G_calloc((dim_2), sizeof(DCELL));

    for (r = 0; r < dim_2; r++) {
        yConv[r] = xConv[r] = 0;
    }
    gaussConvolution(mat1, kernel, xConv, yConv, nrows, ncols, kernelWidth);

    DCELL *yGradient = (DCELL *)G_calloc((dim_2), sizeof(DCELL));
    DCELL *xGradient = (DCELL *)G_calloc((dim_2), sizeof(DCELL));

    for (r = 0; r < dim_2; r++) {
        yGradient[r] = xGradient[r] = 0;
    }

    computeXGradients(diffKernel, yConv, xGradient, nrows, ncols, kernelWidth);
    computeYGradients(diffKernel, xConv, yGradient, nrows, ncols, kernelWidth);

    CELL *magnitude = (CELL *)G_calloc((dim_2), sizeof(CELL));

    CELL *angle = NULL;

    if (anglesMapName != NULL) {
        angle = (CELL *)G_calloc((dim_2), sizeof(CELL));
        Rast_set_null_value(angle, dim_2, CELL_TYPE);
    }

    nonmaxSuppresion(xGradient, yGradient, magnitude, angle, nrows, ncols,
                     kernelWidth, MAGNITUDE_SCALE, MAGNITUDE_LIMIT);

    CELL *edges = (CELL *)G_calloc((dim_2), sizeof(CELL));

    for (r = 0; r < dim_2; r++) {
        edges[r] = 0;
    }

    performHysteresis(edges, magnitude, low, high, nrows, ncols);

    thresholdEdges(edges, nrows, ncols);

    writeMap(result, nrows, ncols, edges);

    if (angle != NULL) {
        writeMap(anglesMapName, nrows, ncols, angle);
    }

    /* **** */

    /* memory cleanup */
    G_free(kernel);
    G_free(diffKernel);
    G_free(name);

    /* add command line incantation to history file */
    Rast_short_history(result, "raster", &history);
    Rast_command_history(&history);
    Rast_write_history(result, &history);

    exit(EXIT_SUCCESS);
}
