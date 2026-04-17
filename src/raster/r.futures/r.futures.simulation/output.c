/*!
   \file outputs.c

   \brief Functions to output rasters

   (C) 2016-2019 by Anna Petrasova, Vaclav Petras and the GRASS Development Team

   This program is free software under the GNU General Public License
   (>=v2).  Read the file COPYING that comes with GRASS for details.

   \author Anna Petrasova
   \author Vaclav Petras
 */

#include <stdlib.h>
#include <stdbool.h>
#include <math.h>

#include <grass/gis.h>
#include <grass/raster.h>
#include <grass/glocale.h>
#include <grass/segment.h>

#include "output.h"
#include "inputs.h"

static void create_timestamp(int year, struct TimeStamp *timestamp)
{
    struct DateTime date_time;
    datetime_set_type(&date_time, DATETIME_ABSOLUTE, DATETIME_YEAR,
                      DATETIME_YEAR, 0);
    datetime_set_year(&date_time, year);
    G_init_timestamp(timestamp);
    G_set_timestamp(timestamp, &date_time);
}
static void create_timestamp_range(int year_from, int year_to,
                                   struct TimeStamp *timestamp)
{
    struct DateTime date_time1;
    struct DateTime date_time2;
    datetime_set_type(&date_time1, DATETIME_ABSOLUTE, DATETIME_YEAR,
                      DATETIME_YEAR, 0);
    datetime_set_type(&date_time2, DATETIME_ABSOLUTE, DATETIME_YEAR,
                      DATETIME_YEAR, 0);
    datetime_set_year(&date_time1, year_from);
    datetime_set_year(&date_time2, year_to);
    G_init_timestamp(timestamp);
    G_set_timestamp_range(timestamp, &date_time1, &date_time2);
}

/*!
 * \brief Create an output name from basename and step
 *
 * \param basename basename specified by user
 * \param step step of simulation (0 is first step)
 * \param nsteps total number of steps to add zero padding
 * \return output name
 */
char *name_for_step(const char *basename, const int step, const int nsteps)
{
    int digits;
    digits = log10(nsteps) + 1;

    return G_generate_basename(basename, step + 1, digits, 0);
}

/*!
 * \brief Write current state of developed areas.
 * \param developed_segment segment of developed cells
 * \param name name for output map
 * \param year_from year to put as timestamp
 * \param year_to if > 0 it is end year of timestamp interval
 * \param nsteps total number of steps (needed for color table)
 * \param contains_abandoned If true, represent undeveloped areas as NULLS, and
 *        shift values <= -2 (abandoned) by +1 to represent in absolute value
 *        step when they were abandoned.
 */
void output_developed_step(SEGMENT *developed_segment, const char *name,
                           int year_from, int year_to, int nsteps,
                           bool contains_abandoned)
{
    int out_fd;
    int row, col, rows, cols;
    CELL *out_row;
    CELL developed;
    CELL val1, val2;
    struct Colors colors;
    const char *mapset;
    struct History hist;

    rows = Rast_window_rows();
    cols = Rast_window_cols();

    Segment_flush(developed_segment);
    out_fd = Rast_open_new(name, CELL_TYPE);
    out_row = Rast_allocate_c_buf();

    for (row = 0; row < rows; row++) {
        Rast_set_c_null_value(out_row, cols);
        for (col = 0; col < cols; col++) {
            Segment_get(developed_segment, (void *)&developed, row, col);
            if (Rast_is_c_null_value(&developed)) {
                continue;
            }
            if (contains_abandoned) {
                if (developed < DEV_TYPE_UNDEVELOPED) {
                    developed += 1;
                }
                else if (developed == DEV_TYPE_UNDEVELOPED) {
                    continue;
                }
            }
            out_row[col] = developed;
        }
        Rast_put_c_row(out_fd, out_row);
    }
    G_free(out_row);
    Rast_close(out_fd);

    Rast_init_colors(&colors);
    // TODO: the map max is 36 for 36 steps, it is correct?

    if (contains_abandoned) {
        val1 = -nsteps;
        val2 = -1;
        Rast_add_c_color_rule(&val1, 230, 163, 255, &val2, 60, 0, 80, &colors);
    }
    else {
        val1 = DEV_TYPE_UNDEVELOPED;
        val2 = DEV_TYPE_UNDEVELOPED;
        Rast_add_c_color_rule(&val1, 180, 255, 160, &val2, 180, 255, 160,
                              &colors);
    }
    val1 = 0;
    val2 = 0;
    Rast_add_c_color_rule(&val1, 200, 200, 200, &val2, 200, 200, 200, &colors);
    val1 = 1;
    val2 = nsteps;
    Rast_add_c_color_rule(&val1, 255, 100, 50, &val2, 255, 255, 0, &colors);

    mapset = G_find_file2("cell", name, "");

    if (mapset == NULL)
        G_fatal_error(_("Raster map <%s> not found"), name);

    Rast_write_colors(name, mapset, &colors);
    Rast_free_colors(&colors);

    Rast_short_history(name, "raster", &hist);
    Rast_command_history(&hist);
    // TODO: store also random seed value (need to get it here, global? in
    // Params?)
    Rast_write_history(name, &hist);
    struct TimeStamp timestamp;
    if (year_to < 0)
        create_timestamp(year_from, &timestamp);
    else
        create_timestamp_range(year_from, year_to, &timestamp);
    G_write_raster_timestamp(name, &timestamp);

    G_message(_("Raster map <%s> created"), name);
}

/*!
 * \brief Write out current state of a segment.
 * \param segment segment for output
 * \param developed_segment segment of developed cells (serves as mask)
 * \param name name for output map
 * \param data_type data type (CELL_TYPE, FCELL_TYPE, DCELL_TYPE)
 */
void output_step(SEGMENT *output_segment, SEGMENT *developed_segment,
                 const char *name, RASTER_MAP_TYPE data_type)
{
    int out_fd;
    int row, col, rows, cols;
    void *out_row;
    void *cell;
    CELL developed;

    rows = Rast_window_rows();
    cols = Rast_window_cols();

    Segment_flush(output_segment);
    out_fd = Rast_open_new(name, data_type);
    out_row = Rast_allocate_buf(data_type);

    for (row = 0; row < rows; row++) {
        cell = out_row;
        /* set row to null, so we need to just set non-nulls */
        Rast_set_null_value(out_row, cols, data_type);
        for (col = 0; col < cols; col++) {
            Segment_get(developed_segment, (void *)&developed, row, col);
            if (!Rast_is_c_null_value(&developed)) {
                Segment_get(output_segment, cell, row, col);
            }
            cell = G_incr_void_ptr(cell, Rast_cell_size(data_type));
        }
        Rast_put_row(out_fd, out_row, data_type);
    }
    G_free(out_row);
    Rast_close(out_fd);

    G_message(_("Raster map <%s> created"), name);
}
