/****************************************************************************
 *
 * MODULE:       r.houghtransform
 * AUTHOR(S):    Anna Kratochvilova - kratochanna gmail.com
 *               Vaclav Petras - wenzeslaus gmail.com
 *
 * PURPOSE:      Line segment extraction using Hough transformation.
 *
 * COPYRIGHT:    (C) 2012 by the GRASS Development Team
 *
 *               This program is free software under the GNU General Public
 *               License (>=v2). Read the file COPYING that comes with
 *               GRASS for details.
 *
 *****************************************************************************/

#include "hough.h"

extern "C" {
#include <grass/gis.h>
#include <grass/raster.h>
#include <grass/glocale.h>
#include <grass/gmath.h>
}

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>

/**

  \todo Floats are used instead of doubles.
  \todo Be able to work with FCELL (and CELL?).
  */
int main(int argc, char *argv[])
{
    struct Cell_head cell_head; /* it stores region information,
                                   and header information of rasters */
    char *name;                 /* input raster name */

    char *mapset; /* mapset name */

    char *result; /* output raster name */

    int nrows, ncols;

    struct GModule *module; /* GRASS module for parsing arguments */

    /* options */
    struct Option *input, *output, *anglesOption, *houghImageNameOption,
        *angleWidthOption, *minGapOption, *maxNumberOfGapsOption,
        *maxLinesOption, *maxGapOption, *minSegmentLengthOption,
        *lineWidthOption;

    /* initialize GIS environment */
    G_gisinit(
        argv[0]); /* reads grass env, stores program name to G_program_name() */

    /* initialize module */
    module = G_define_module();
    G_add_keyword(_("raster"));
    G_add_keyword(_("Hough"));
    G_add_keyword(_("imagery"));
    module->description =
        _("Performs Hough transformation and extracts line segments from image."
          " Region shall be set to input map."
          " Can work only on small images since map is loaded into memory.");

    /* Define the different options as defined in gis.h */
    input = G_define_standard_option(G_OPT_R_INPUT);

    output = G_define_standard_option(G_OPT_V_OUTPUT);

    anglesOption = G_define_standard_option(G_OPT_R_INPUT);
    anglesOption->key = "angles";
    anglesOption->required = NO;
    anglesOption->description =
        _("Name of input image with angles from i.edge.");

    houghImageNameOption = G_define_standard_option(G_OPT_R_OUTPUT);
    houghImageNameOption->key = "hough_image";
    houghImageNameOption->required = NO;
    houghImageNameOption->description =
        _("Name of output image containing Hough transform");

    angleWidthOption = G_define_option();
    angleWidthOption->key = "angle_width";
    angleWidthOption->type = TYPE_INTEGER;
    angleWidthOption->required = NO;
    angleWidthOption->multiple = NO;
    angleWidthOption->description =
        _("Width of circle sector (only when you provide angle map)");
    angleWidthOption->answer = const_cast<char *>("5");

    // this option will become max peaks number to find in HT
    maxLinesOption = G_define_option();
    maxLinesOption->key = "lines_number";
    maxLinesOption->type = TYPE_INTEGER;
    maxLinesOption->required = NO;
    maxLinesOption->multiple = NO;
    maxLinesOption->label = _("Approximate number of line segments");
    maxLinesOption->description = _("This number represents"
                                    " maximal number of line candidates"
                                    " detected in Hough transform image."
                                    " Final number of line segments can be"
                                    " smaller or greater.");
    maxLinesOption->answer = const_cast<char *>("20");

    minGapOption = G_define_option();
    minGapOption->key = "gap_size";
    minGapOption->type = TYPE_INTEGER;
    minGapOption->required = NO;
    minGapOption->multiple = NO;
    minGapOption->description = _("Minimal cell count considered as a gap");
    minGapOption->answer = const_cast<char *>("5");

    maxNumberOfGapsOption = G_define_option();
    maxNumberOfGapsOption->key = "max_gap_count";
    maxNumberOfGapsOption->type = TYPE_INTEGER;
    maxNumberOfGapsOption->required = NO;
    maxNumberOfGapsOption->multiple = NO;
    maxNumberOfGapsOption->description =
        _("Maximal number of gaps in line segment");
    maxNumberOfGapsOption->answer = const_cast<char *>("5");

    maxGapOption = G_define_option();
    maxGapOption->key = "max_gap";
    maxGapOption->type = TYPE_INTEGER;
    maxGapOption->required = NO;
    maxGapOption->multiple = NO;
    maxGapOption->description = _("Maximum gap in pixels");
    maxGapOption->answer = const_cast<char *>("5");

    minSegmentLengthOption = G_define_option();
    minSegmentLengthOption->key = "min_segment_length";
    minSegmentLengthOption->type = TYPE_INTEGER;
    minSegmentLengthOption->required = NO;
    minSegmentLengthOption->multiple = NO;
    minSegmentLengthOption->description = _("Minimal length of line segment");
    minSegmentLengthOption->answer = const_cast<char *>("50");

    lineWidthOption = G_define_option();
    lineWidthOption->key = "line_width";
    lineWidthOption->type = TYPE_INTEGER;
    lineWidthOption->required = NO;
    lineWidthOption->multiple = NO;
    lineWidthOption->description =
        _("Expected width of line (used for searching segments)");
    lineWidthOption->answer = const_cast<char *>("3");

    /* options and flags parser */
    if (G_parser(argc, argv))
        exit(EXIT_FAILURE);

    /* stores options and flags to variables */
    result = output->answer;
    name = input->answer;

    HoughParametres houghParametres;
    houghParametres.maxPeaksNum = atoi(maxLinesOption->answer);
    houghParametres.threshold = 10; // TODO: consider option
    houghParametres.angleWidth = atoi(angleWidthOption->answer);
    houghParametres.sizeOfNeighbourhood = 1; // TODO: consider option

    ExtractParametres extractParametres;
    extractParametres.gapSize = atoi(minGapOption->answer);
    extractParametres.maxGap = atoi(maxGapOption->answer);
    extractParametres.maxNumOfGaps = atoi(maxNumberOfGapsOption->answer);
    extractParametres.lineLength = atoi(minSegmentLengthOption->answer);
    extractParametres.lineWidth = atoi(lineWidthOption->answer);

    /* returns NULL if the map was not found in any mapset,
     * mapset name otherwise */
    mapset = (char *)G_find_raster2(name, "");
    if (mapset == NULL)
        G_fatal_error(_("Raster map <%s> not found"), name);

    /* determine the inputmap type (CELL/FCELL/DCELL) */
    // data_type = Rast_map_type(name, mapset);

    //    struct Cell_head templCellhd;

    //    Rast_get_cellhd(name, mapset, &cellhd);
    //    Rast_get_cellhd(first_map_R_name, first_map_R_mapset, &cellhd_zoom1);

    /* controlling, if we can open input raster */
    Rast_get_cellhd(name, mapset, &cell_head);

    G_debug(3, "number of rows %d", cell_head.rows);

    nrows = Rast_window_rows();

    ncols = Rast_window_cols();

    /* **** */

    hough_peaks(houghParametres, extractParametres, name, mapset, nrows, ncols,
                anglesOption->answer, houghImageNameOption->answer, result);

    /* **** */

    /* memory cleanup */
    G_free(name);

    /* add command line incantation to history file */
    //    Rast_short_history(templName, "raster", &history);
    //    Rast_command_history(&history);
    //    Rast_write_history(templName, &history);

    exit(EXIT_SUCCESS);
}
