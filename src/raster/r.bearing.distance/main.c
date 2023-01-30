/***********************************************************************/
/*
   r.bearing.distance

   *****

   COPYRIGHT:    (C) 2020 by UCL, and the GRASS Development Team

   This program is free software under the GNU General Public
   License (>=v2). Read the COPYING file that comes with GRASS
   for details.

   REVISIONS

   Written by Mark Lake for GRASS 7.x., 09/12/2020

   *****

   AUTHOR

   Mark Lake <mark.lake@ucl.ac.uk>

   University College London
   Institute of Archaeology
   31-34 Gordon Square
   London.  WC1H 0PY
   United Kingdom

   *****

   ACKNOWLEDGEMENTS

   Draws on code from r.skyline.

   *****

   PURPOSE

   1) Given a point location, specified as a pair of coordinates,
   computes the bearing and/or straight-line distance from that point
   towards every non-null cell.  There are several options for the type
   of bearing returned, as documented in the man page.

   *****

   OPTIONS

   r.bearing.distance
   r.bearing.distance --help
   r.bearing.distance [-rabse] input=name coordinate=x,y
   [reference_bearing=double] [bearing=string] [distance=string]
   [segment=string] [csv_seg=string] [csv_ax=string] [--overwrite] [--help]
   [--verbose] [--quiet] [--ui]

   Flags:
   -r Reverse bearing (i.e. bearing towards point location)
   -a Bearing difference is axial (0 - 90 degrees) rather than clockwise)
   -b Bearing difference is axial and signed (0 - +/-90 degrees) rather than
   clockwise) -s Segments are clockwise from zero rather than centred on zero -e
   Compute eight segments rather than four

   --overwrite Allow output files to overwrite existing files
   --help Print usage summary
   --verbose Verbose module output
   --quiet Quiet module output
   --ui Force launching GUI dialog

   Parameters:
   input=name [required] Raster map containing non-null cells for which bearing
   is to be computed coordinate=x,y [required] Coordinate identifying the point
   location reference_bearing=double Bearing in degrees from N (for calculation
   of bearing difference map) bearing=string Raster map name for storing the
   bearing distance=string Raster map name for storing the distance
   segment=string Raster map name for storing the segment
   csv_seg=string Output plain text CSV file for segment counts
   csv_ax=string Output plain text CSV file for axial difference counts

   *****

   NOTES

   *****

   TO DO

 */

/***********************************************************************/

#define MAIN

#include <stdlib.h>
#include <string.h>
#include <math.h>

#include "global_vars.h"
#include "raster_file.h"
#include "azimuth.h"
#include "file.h"

int main(int argc, char *argv[])
{
    int input_fd = -1, output_fd = -1, segment_fd = -1;
    FILE *csv_seg_str, *csv_ax_str;
    char input_mapset[GMAPSET_MAX];
    char current_mapset[GMAPSET_MAX];
    RASTER_MAP_TYPE input_map_cell_type;
    RASTER_MAP_TYPE output_map_cell_type;
    RASTER_MAP_TYPE segment_map_cell_type;
    char message[GMAPSET_MAX + 64];
    struct Categories cats;
    struct History history;

    /* struct Colors colr; */
    double data, bearing, relative_bearing, distance, reference_bearing;
    void *input_buf, *output_buf, *segment_buf = NULL;
    int nrows, ncols, row, col;
    int segment, n_segments, i;
    long int cell_counts[9];
    double axial_counts[N_AXIAL_COUNT_CATS];
    struct GModule *module;
    struct Option *input, *bearing_map, *ref_bearing;
    struct Option *segment_map;
    struct Option *distance_map, *point;
    struct Option *csv_seg, *csv_ax;
    struct Flag *reverse, *axial, *axial_signed, *square, *eight;
    int overwrite;

    /***********************************************************************
      Options

    ***********************************************************************/

    /* Initialize the GIS calls and sort out error handling */

    G_gisinit(argv[0]);
    G_sleep_on_error(0);

    /* Declare module info. */

    module = G_define_module();
    G_add_keyword(_("raster"));
    G_add_keyword(_("azimuth"));
    G_add_keyword(_("direction"));
    G_add_keyword(_("bearing"));
    module->description = _("Find the bearing and/or straight-line distance "
                            "from all non-null cells to the specified point.");

    /* Define the options */

    input = G_define_option();
    input->key = "input";
    input->type = TYPE_STRING;
    input->required = YES;
    input->gisprompt = "old,cell,raster";
    input->key_desc = "name";
    input->description = _("Raster map containing non-null cells for which "
                           "bearing is to be computed");

    point = G_define_option();
    point->key = "coordinate";
    point->type = TYPE_STRING;
    point->required = YES;
    point->key_desc = "x,y";
    point->description = _("Coordinate identifying the point location");

    ref_bearing = G_define_option();
    ref_bearing->key = "reference_bearing";
    ref_bearing->type = TYPE_DOUBLE;
    ref_bearing->required = NO;
    ref_bearing->key_desc = "double";
    ref_bearing->description = _("Bearing in degrees from N (for calculation "
                                 "of bearing difference map)");

    bearing_map = G_define_option();
    bearing_map->key = "bearing";
    bearing_map->type = TYPE_STRING;
    bearing_map->required = NO;
    bearing_map->gisprompt = "new,cell,raster";
    bearing_map->description = _("Raster map name for storing the bearing");

    distance_map = G_define_option();
    distance_map->key = "distance";
    distance_map->type = TYPE_STRING;
    distance_map->required = NO;
    distance_map->gisprompt = "new,cell,raster";
    distance_map->description = _("Raster map name for storing the distance");

    segment_map = G_define_option();
    segment_map->key = "segment";
    segment_map->type = TYPE_STRING;
    segment_map->required = NO;
    segment_map->gisprompt = "new,cell,raster";
    segment_map->description = _("Raster map name for storing the segment");

    csv_seg = G_define_option();
    csv_seg->key = "csv_seg";
    csv_seg->type = TYPE_STRING;
    csv_seg->required = NO;
    csv_seg->description = _("Output plain text  CSV file for segment counts");

    csv_ax = G_define_option();
    csv_ax->key = "csv_ax";
    csv_ax->type = TYPE_STRING;
    csv_ax->required = NO;
    csv_ax->description =
        _("Output plain text CSV file for axial difference counts");

    reverse = G_define_flag();
    reverse->key = 'r';
    reverse->description =
        _("Reverse bearing (i.e. bearing towards point location) ");

    axial = G_define_flag();
    axial->key = 'a';
    axial->description = _(
        "Bearing difference is axial (0 - 90 degrees) rather than clockwise) ");

    axial_signed = G_define_flag();
    axial_signed->key = 'b';
    axial_signed->description = _("Bearing difference is axial and signed (0 - "
                                  "+/-90 degrees) rather than clockwise) ");

    square = G_define_flag();
    square->key = 's';
    square->description =
        _("Segments are clockwise from zero rather than centred on zero ");

    eight = G_define_flag();
    eight->key = 'e';
    eight->description = _("Compute eight segments rather than four ");

    if (G_parser(argc, argv))
        exit(EXIT_FAILURE);

    /* Make parameters globally available */

    if (bearing_map->answer != NULL)
        do_bearing = 1;
    else
        do_bearing = 0;

    if (distance_map->answer != NULL)
        do_distance = 1;
    else
        do_distance = 0;

    if (segment_map->answer != NULL)
        do_segments = 1;
    else
        do_segments = 0;

    do_eight_segments = eight->answer;
    if (do_eight_segments)
        n_segments = 8;
    else
        n_segments = 4;

    do_square_segments = square->answer;

    if (ref_bearing->answer != NULL) {
        sscanf(ref_bearing->answer, "%lf", &reference_bearing);
        if ((reference_bearing >= 0.0) && (reference_bearing <= 360.0))
            do_relative_bearing = 1;
        else
            G_fatal_error(
                _("Reference bearing must be between 0.0 and 360.0 inclusive"));
    }
    else {
        do_relative_bearing = 0;
        /* do_segments = 0; */
    }

    if ((do_bearing + do_distance + do_segments) < 1)
        G_fatal_error("You have not asked for any output!");

    G_scan_easting(point->answers[0], &east, G_projection());
    G_scan_northing(point->answers[1], &north, G_projection());
    overwrite = module->overwrite;

    /* Specify output raster map cell types.  Input map cell types will
       be retrieved by Open_raster_infile */

    output_map_cell_type = FCELL_TYPE;
    segment_map_cell_type = CELL_TYPE;

    /* Specify buffer cell types */
    input_buf_cell_type = FCELL_TYPE;
    output_buf_cell_type = FCELL_TYPE;
    segment_buf_cell_type = DCELL_TYPE;

    /***********************************************************************
      Check region and find bounding box for analysis

    ***********************************************************************/

    /* Get current region */
    G_get_window(&window);
    nrows = Rast_window_rows();
    n_row = 0; /* Origin is top left */
    s_row = nrows - 1;
    ncols = Rast_window_cols();
    w_col = 0;
    e_col = ncols - 1;

    /* Check for appropriate projection.  Code currently does not
       deal with Lat/Long  */

    if ((G_projection() == PROJECTION_LL))
        G_fatal_error(
            _("Lat/Long support is not (yet) implemented for this module."));

    /* Check for integer resolution.  Algorithm is not robust in
       cases where resolution is non-integer */

    if ((floor(window.ew_res) != window.ew_res) ||
        (floor(window.ns_res) != window.ns_res)) {
        G_fatal_error(_("Please use region with integer resolution "));
    }

    /* Check that point location falls within current region */

    if (east < window.west || east > window.east || north > window.north ||
        north < window.south) {
        G_fatal_error(_("Specified point location outside database region "));
    }

    /* Convert point location coordinates to rows and columns */

    point_col = (int)Rast_easting_to_col(east, &window);
    point_row = (int)Rast_northing_to_row(north, &window);

    /***********************************************************************
      Open input map and set up input and output buffers for processing

    ***********************************************************************/

    input_fd = Open_raster_infile(input->answer, input_mapset, "",
                                  &input_map_cell_type, message);
    if (input_fd < 0)
        G_fatal_error("%s", message);

    G_message(_("\nReading input data from '%s@%s' \n"), input->answer,
              input_mapset);

    input_buf = Allocate_raster_buf_with_null(input_buf_cell_type);
    Read_raster_infile(input_buf, input_fd, input_buf_cell_type,
                       input_map_cell_type);
    Close_raster_file(input_fd);

#ifdef DEBUG
    fprintf(stdout, "\nIn function main: contents of 'input_buf'\n");
    Print_raster_buf_row_col(input_buf, input_buf_cell_type, stderr);
#endif

    /***********************************************************************
      Compute bearings

    ***********************************************************************/

    if (do_bearing || do_segments) {
        if (!do_segments)
            G_message(_("Computing bearings\n"));
        else
            G_message(_("Computing bearings and segments\n"));

        output_buf = Allocate_raster_buf_with_null(output_buf_cell_type);
        if (do_segments)
            segment_buf = Allocate_raster_buf_with_null(segment_buf_cell_type);

        /* Reset counters */
        for (i = 0; i <= 8; i++)
            cell_counts[i] = 0;

        for (i = 0; i < N_AXIAL_COUNT_CATS; i++)
            axial_counts[i] = 0;

        for (row = n_row; row <= s_row; row++) { /* row origin at north */
            for (col = w_col; col <= e_col; col++) {
                data = Get_buffer_value_d_row_col(
                    input_buf, input_buf_cell_type, row, col);

                /* Point location could be NULL in input map, so we test it
                 * first */
                if ((row == point_row) && (col == point_col)) {
                    /* Cell is point location so set appropriate values */
                    bearing = IS_POINT;
                    /* Set_buffer_value_d_row_col (output_buf, bearing,
                       output_buf_cell_type, row, col); */
                    Set_buffer_null_d_row_col(output_buf, output_buf_cell_type,
                                              row, col);
                }
                else {
                    /* Cell is not point location */
                    if (!(Rast_is_null_value(&data, input_buf_cell_type))) {
                        /* Cell is in area of interest */
                        bearing = calc_azimuth(row, col, reverse->answer);
                        relative_bearing = 0;
                        cell_counts[0]++;
                        if (do_relative_bearing) {
                            if (axial->answer)
                                relative_bearing = calc_azimuth_axial_diff(
                                    reference_bearing, bearing);
                            else {
                                if (axial_signed->answer)
                                    relative_bearing =
                                        calc_azimuth_axial_diff_signed(
                                            reference_bearing, bearing);
                                else
                                    relative_bearing =
                                        calc_azimuth_clockwise_diff(
                                            reference_bearing, bearing);
                            }
                            Set_buffer_value_d_row_col(
                                output_buf, relative_bearing,
                                output_buf_cell_type, row, col);
                            if ((axial->answer || axial_signed->answer) &&
                                csv_ax->answer != NULL) {
                                axial_counts[NALL]++;
                                axial_counts[SUMALL] += relative_bearing;
                                axial_counts[RUN_MEAN_ALL_CUR] =
                                    axial_counts[RUN_MEAN_ALL_PREV] +
                                    ((relative_bearing -
                                      axial_counts[RUN_MEAN_ALL_PREV]) /
                                     axial_counts[NALL]);
                                axial_counts[RUN_Q_ALL_CUR] =
                                    axial_counts[RUN_Q_ALL_PREV] +
                                    ((relative_bearing -
                                      axial_counts[RUN_MEAN_ALL_PREV]) *
                                     (relative_bearing -
                                      axial_counts[RUN_MEAN_ALL_CUR]));
                                axial_counts[RUN_MEAN_ALL_PREV] =
                                    axial_counts[RUN_MEAN_ALL_CUR];
                                axial_counts[RUN_Q_ALL_PREV] =
                                    axial_counts[RUN_Q_ALL_CUR];
                                /* Positive relative bearings only */
                                if (relative_bearing > 0) {
                                    axial_counts[NPOS]++;
                                    axial_counts[SUMPOS] += relative_bearing;
                                    axial_counts[RUN_MEAN_POS_CUR] =
                                        axial_counts[RUN_MEAN_POS_PREV] +
                                        ((relative_bearing -
                                          axial_counts[RUN_MEAN_POS_PREV]) /
                                         axial_counts[NPOS]);
                                    axial_counts[RUN_Q_POS_CUR] =
                                        axial_counts[RUN_Q_POS_PREV] +
                                        ((relative_bearing -
                                          axial_counts[RUN_MEAN_POS_PREV]) *
                                         (relative_bearing -
                                          axial_counts[RUN_MEAN_POS_CUR]));
                                    axial_counts[RUN_MEAN_POS_PREV] =
                                        axial_counts[RUN_MEAN_POS_CUR];
                                    axial_counts[RUN_Q_POS_PREV] =
                                        axial_counts[RUN_Q_POS_CUR];
                                    if (relative_bearing <= 22.5)
                                        axial_counts[NPOS22_5]++;
                                    else if (relative_bearing <= 45)
                                        axial_counts[NPOS45]++;
                                    else if (relative_bearing <= 67.5)
                                        axial_counts[NPOS67_5]++;
                                    else
                                        axial_counts[NPOS90]++;
                                }
                                else {
                                    /* Negative relative bearings only */
                                    if (relative_bearing < 0) {
                                        axial_counts[NNEG]++;
                                        axial_counts[SUMNEG] +=
                                            relative_bearing;
                                        axial_counts[RUN_MEAN_NEG_CUR] =
                                            axial_counts[RUN_MEAN_NEG_PREV] +
                                            ((relative_bearing -
                                              axial_counts[RUN_MEAN_NEG_PREV]) /
                                             axial_counts[NNEG]);
                                        axial_counts[RUN_Q_NEG_CUR] =
                                            axial_counts[RUN_Q_NEG_PREV] +
                                            ((relative_bearing -
                                              axial_counts[RUN_MEAN_NEG_PREV]) *
                                             (relative_bearing -
                                              axial_counts[RUN_MEAN_NEG_CUR]));
                                        axial_counts[RUN_MEAN_NEG_PREV] =
                                            axial_counts[RUN_MEAN_NEG_CUR];
                                        axial_counts[RUN_Q_NEG_PREV] =
                                            axial_counts[RUN_Q_NEG_CUR];
                                        if (relative_bearing >= -22.5)
                                            axial_counts[NNEG22_5]++;
                                        else if (relative_bearing >= -45)
                                            axial_counts[NNEG45]++;
                                        else if (relative_bearing >= -67.5)
                                            axial_counts[NNEG67_5]++;
                                        else
                                            axial_counts[NNEG90]++;
                                    }
                                    else {
                                        /* Relative bearings of zero */
                                        axial_counts[NZERO]++;
                                    }
                                }
                            }
                        }
                        else
                            Set_buffer_value_d_row_col(output_buf, bearing,
                                                       output_buf_cell_type,
                                                       row, col);

                        /* Compute which segment the point falls in */
                        if (do_segments) {
                            if (do_relative_bearing && (!axial->answer) &&
                                (!axial_signed->answer))
                                segment = calc_segment(relative_bearing);
                            else
                                segment =
                                    calc_segment(calc_azimuth_clockwise_diff(
                                        reference_bearing, bearing));
                            Set_buffer_value_c_row_col(segment_buf, segment,
                                                       segment_buf_cell_type,
                                                       row, col);
                            cell_counts[segment]++;
                        }
                    }
                    /* Implicit else leaves value in buffer as NULL */
                }
            }
        }

        /* Open raster maps and allocate memory */

        output_fd =
            Open_raster_outfile(bearing_map->answer, current_mapset,
                                output_map_cell_type, overwrite, message);
        if (output_fd < 0)
            G_warning("%s", message);
        else {
            Write_raster_outfile(output_buf, output_fd, output_buf_cell_type,
                                 output_map_cell_type);
            Close_raster_file(output_fd);
        }

        G_free(output_buf);

        if (do_segments) {
            segment_fd =
                Open_raster_outfile(segment_map->answer, current_mapset,
                                    segment_map_cell_type, overwrite, message);
            if (segment_fd < 0)
                G_warning("%s", message);
            else {
                Write_raster_outfile(segment_buf, segment_fd,
                                     segment_buf_cell_type,
                                     segment_map_cell_type);
                Close_raster_file(segment_fd);
            }

            G_free(segment_buf);
        }
    }

    /***********************************************************************
      Compute distance

    ***********************************************************************/

    if (do_distance) {
        G_message(_("Computing distances\n"));

        output_buf = Allocate_raster_buf_with_null(output_buf_cell_type);

        for (row = n_row; row <= s_row; row++) { /* row origin at north */
            for (col = w_col; col <= e_col; col++) {
                data = Get_buffer_value_d_row_col(
                    input_buf, input_buf_cell_type, row, col);

                /* Point location could be NULL in input map, so we test it
                 * first */
                if ((row == point_row) && (col == point_col)) {
                    /* Cell is point location so set appropriate values */
                    distance = 0.0;
                    Set_buffer_value_d_row_col(output_buf, distance,
                                               output_buf_cell_type, row, col);
                }
                else {
                    /* Cell is not point location */
                    if (!(Rast_is_null_value(&data, input_buf_cell_type))) {
                        /* If cell is in area of interest */
                        distance = calc_distance(row, col);
                        Set_buffer_value_d_row_col(output_buf, distance,
                                                   output_buf_cell_type, row,
                                                   col);
                    }
                    /* Implicit else leaves value in buffer as NULL */
                }
            }
        }

        /* Open raster map and allocate memory */

        output_fd =
            Open_raster_outfile(distance_map->answer, current_mapset,
                                output_map_cell_type, overwrite, message);
        if (output_fd < 0)
            G_warning("%s", message);
        else {
            Write_raster_outfile(output_buf, output_fd, output_buf_cell_type,
                                 output_map_cell_type);
            Close_raster_file(output_fd);
        }

        G_free(output_buf);
    }

    /***********************************************************************
      Release input_buf memory

    ***********************************************************************/

    G_free(input_buf);

    /***********************************************************************
      Create support files

    ***********************************************************************/

    G_message(_("Creating support files\n"));

    if (do_bearing) {
        /* Create history support file for bearing map */

        Rast_short_history(bearing_map->answer, "raster", &history);
        Rast_set_history(&history, HIST_DATSRC_1, input->answer);
        Rast_command_history(&history);
        Rast_write_history(bearing_map->answer, &history);

        /* Create category file for bearing map */

        Rast_read_cats(bearing_map->answer, current_mapset, &cats);
        Rast_set_cats_fmt("$1 degree$?s", 1.0, 0.0, 0.0, 0.0, &cats);
        Rast_write_cats(bearing_map->answer, &cats);
        Rast_free_cats(&cats);
    }

    if (do_distance) {
        /* Create history support file for distance map */

        Rast_short_history(distance_map->answer, "raster", &history);
        Rast_set_history(&history, HIST_DATSRC_1, input->answer);
        Rast_command_history(&history);
        Rast_write_history(distance_map->answer, &history);

        /* Create category file for distance map */

        Rast_read_cats(distance_map->answer, current_mapset, &cats);
        Rast_set_cats_fmt("$1", 1.0, 0.0, 0.0, 0.0, &cats);
        Rast_write_cats(distance_map->answer, &cats);
        Rast_free_cats(&cats);
    }

    if (do_segments) {
        /* Create history support file for distance map */

        Rast_short_history(segment_map->answer, "raster", &history);
        Rast_set_history(&history, HIST_DATSRC_1, input->answer);
        Rast_command_history(&history);
        Rast_write_history(segment_map->answer, &history);

        /* Create category file for distance map */

        Rast_read_cats(segment_map->answer, current_mapset, &cats);
        Rast_set_cats_fmt("$1", 1.0, 0.0, 0.0, 0.0, &cats);
        Rast_write_cats(segment_map->answer, &cats);
        Rast_free_cats(&cats);
    }

    /* Output segment data to screen */
    if (do_segments) {
        G_message(_("\nCells in segments (segment 0 is total)\n"));
        G_message(_("| Segment |          Count | Percent |\n"));

        for (i = 0; i <= n_segments; i++) {
            G_message(_("| %7d | %14ld | %7.1f |\n"), i, cell_counts[i],
                      100.0 / cell_counts[0] * cell_counts[i]);
        }
    }

    /* Output segment data to CSV file */
    if (do_segments) {
        if (csv_seg->answer != NULL) {
            csv_seg_str =
                Create_file(csv_seg->answer, ".csv", message, overwrite);
            if (csv_seg_str == NULL)
                G_warning(_("Not writing CSV file: %s"), message);
            else {
                G_message(_("\nSaving results to file '%s' "), csv_seg->answer);

                /* Write header */
                fprintf(csv_seg_str, "Input");
                for (i = 0; i <= n_segments; i++) {
                    fprintf(csv_seg_str, ",Count_%d", i);
                }
                for (i = 0; i <= n_segments; i++) {
                    fprintf(csv_seg_str, ",Percent_%d", i);
                }
                fprintf(csv_seg_str, "\n");
                fflush(csv_seg_str);

                /* Write data */
                fprintf(csv_seg_str, "%s", input->answer);
                for (i = 0; i <= n_segments; i++) {
                    fprintf(csv_seg_str, ",%ld", cell_counts[i]);
                }
                for (i = 0; i <= n_segments; i++) {
                    fprintf(csv_seg_str, ",%f",
                            100.0 / cell_counts[0] * cell_counts[i]);
                }
                fprintf(csv_seg_str, "\n");
                fflush(csv_seg_str);

                fclose(csv_seg_str);
            }
        }
    }

    /* Output axial difference data to CSV file */
    if (axial->answer || axial_signed->answer) {
        if (csv_ax->answer != NULL) {
            csv_ax_str =
                Create_file(csv_ax->answer, ".csv", message, overwrite);
            if (csv_ax_str == NULL)
                G_warning(_("Not writing CSV file: %s"), message);
            else {
                G_message(_("\nSaving results to file '%s' "), csv_ax->answer);

                /* Write header */
                fprintf(csv_ax_str, "Input");
                fprintf(csv_ax_str, ",N_ZERO");
                fprintf(csv_ax_str, ",N_POS_25_5");
                fprintf(csv_ax_str, ",N_POS_45");
                fprintf(csv_ax_str, ",N_POS_67_5");
                fprintf(csv_ax_str, ",N_POS_90");
                fprintf(csv_ax_str, ",N_NEG_25_5");
                fprintf(csv_ax_str, ",N_NEG_45");
                fprintf(csv_ax_str, ",N_NEG_67_5");
                fprintf(csv_ax_str, ",N_NEG_90");
                fprintf(csv_ax_str, ",N_POS");
                fprintf(csv_ax_str, ",N_NEG");
                fprintf(csv_ax_str, ",N_ALL");
                fprintf(csv_ax_str, ",SUM_POS");
                fprintf(csv_ax_str, ",SUM_NEG");
                fprintf(csv_ax_str, ",SUM_ALL");
                fprintf(csv_ax_str, ",MEAN_POS");
                fprintf(csv_ax_str, ",SDEV_POS");
                fprintf(csv_ax_str, ",MEAN_NEG");
                fprintf(csv_ax_str, ",SDEV_NEG");
                fprintf(csv_ax_str, ",MEAN_ALL");
                fprintf(csv_ax_str, ",SDEV_ALL");
                fprintf(csv_ax_str, "\n");
                fflush(csv_ax_str);

                /* Write data */
                /*long int n_all = (long)axial_counts[NPOS] +
                    (long)axial_counts[NNEG] + axial_counts[NZERO];
                double sum_all =
                axial_counts[SUMPOS] + axial_counts[SUMNEG] + 0;*/
                fprintf(csv_ax_str, "%s", input->answer);
                fprintf(csv_ax_str, ",%ld", (long)axial_counts[NZERO]);
                fprintf(csv_ax_str, ",%ld", (long)axial_counts[NPOS22_5]);
                fprintf(csv_ax_str, ",%ld", (long)axial_counts[NPOS45]);
                fprintf(csv_ax_str, ",%ld", (long)axial_counts[NPOS67_5]);
                fprintf(csv_ax_str, ",%ld", (long)axial_counts[NPOS90]);
                fprintf(csv_ax_str, ",%ld", (long)axial_counts[NNEG22_5]);
                fprintf(csv_ax_str, ",%ld", (long)axial_counts[NNEG45]);
                fprintf(csv_ax_str, ",%ld", (long)axial_counts[NNEG67_5]);
                fprintf(csv_ax_str, ",%ld", (long)axial_counts[NNEG90]);
                fprintf(csv_ax_str, ",%ld", (long)axial_counts[NPOS]);
                fprintf(csv_ax_str, ",%ld", (long)axial_counts[NNEG]);
                fprintf(csv_ax_str, ",%ld", (long)axial_counts[NALL]);
                fprintf(csv_ax_str, ",%ld", (long)axial_counts[SUMPOS]);
                fprintf(csv_ax_str, ",%ld", (long)axial_counts[SUMNEG]);
                fprintf(csv_ax_str, ",%ld", (long)axial_counts[SUMALL]);

                /* Mean pos
                if (axial_counts[NPOS] > 0)
                    fprintf(csv_ax_str, ",%lf",
                            axial_counts[SUMPOS] / axial_counts[NPOS]);
                else
                fprintf(csv_ax_str, ",%s", "NA");*/
                /* Running mean pos */
                if (axial_counts[NPOS] > 0)
                    fprintf(csv_ax_str, ",%lf", axial_counts[RUN_MEAN_POS_CUR]);
                else
                    fprintf(csv_ax_str, ",%s", "NA");
                /* Standard deviation pos */
                if (axial_counts[NPOS] > 0)
                    fprintf(
                        csv_ax_str, ",%lf",
                        sqrt(axial_counts[RUN_Q_POS_CUR] / axial_counts[NPOS]));
                else
                    fprintf(csv_ax_str, ",%s", "NA");

                /* Mean neg
                if (axial_counts[NNEG] > 0)
                    fprintf(csv_ax_str, ",%lf",
                            axial_counts[SUMNEG] / axial_counts[NNEG]);
                else
                fprintf(csv_ax_str, ",%s", "NA");*/
                /* Running mean neg */
                if (axial_counts[NNEG] > 0)
                    fprintf(csv_ax_str, ",%lf", axial_counts[RUN_MEAN_NEG_CUR]);
                else
                    fprintf(csv_ax_str, ",%s", "NA");
                /* Standard deviation neg */
                if (axial_counts[NNEG] > 0)
                    fprintf(
                        csv_ax_str, ",%lf",
                        sqrt(axial_counts[RUN_Q_NEG_CUR] / axial_counts[NNEG]));
                else
                    fprintf(csv_ax_str, ",%s", "NA");

                /* Mean all
                if (n_all > 0)
                    fprintf(csv_ax_str, ",%lf", sum_all / n_all);
                else
                fprintf(csv_ax_str, ",%s", "NA");*/
                /* Running mean all */
                if (axial_counts[NALL] > 0)
                    fprintf(csv_ax_str, ",%lf", axial_counts[RUN_MEAN_ALL_CUR]);
                else
                    fprintf(csv_ax_str, ",%s", "NA");
                /* Standard deviation all */
                if (axial_counts[NALL] > 0)
                    fprintf(
                        csv_ax_str, ",%lf",
                        sqrt(axial_counts[RUN_Q_ALL_CUR] / axial_counts[NALL]));
                else
                    fprintf(csv_ax_str, ",%s", "NA");
                fprintf(csv_ax_str, "\n");
                fflush(csv_ax_str);

                fclose(csv_ax_str);
            }
        }
    }

    G_message(_("\nJob finished\n"));

    return (EXIT_SUCCESS);
}
