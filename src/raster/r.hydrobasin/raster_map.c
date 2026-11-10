#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <grass/glocale.h>
#include "global.h"

#define DIR_UNKNOWN 0
#define DIR_DEG     1
#define DIR_DEG45   2
#define DIR_POW2    3

struct raster_map *read_direction(char *dir_name, char *format)
{
    int dir_fd, dir_format;
    struct Range dir_range;
    CELL dir_min, dir_max, *dir_buf;
    struct raster_map *dir_map;
    int nrows, ncols, row, col;

    dir_fd = Rast_open_old(dir_name, "");
    if (Rast_get_map_type(dir_fd) != CELL_TYPE)
        G_fatal_error(_("Invalid direction map <%s>"), dir_name);

    /* adapted from r.path */
    if (Rast_read_range(dir_name, "", &dir_range) < 0)
        G_fatal_error(_("Unable to read range file"));
    Rast_get_range_min_max(&dir_range, &dir_min, &dir_max);
    if (dir_max <= 0)
        G_fatal_error(_("Invalid direction map <%s>"), dir_name);

    dir_format = DIR_UNKNOWN;
    if (strcmp(format, "degree") == 0) {
        if (dir_max > 360)
            G_fatal_error(_("Directional degrees cannot be > 360"));
        dir_format = DIR_DEG;
    }
    else if (strcmp(format, "45degree") == 0) {
        if (dir_max > 8)
            G_fatal_error(_("Directional degrees divided by 45 cannot be > 8"));
        dir_format = DIR_DEG45;
    }
    else if (strcmp(format, "power2") == 0) {
        if (dir_max > 128)
            G_fatal_error(_("Powers of 2 cannot be > 128"));
        dir_format = DIR_POW2;
    }
    else if (strcmp(format, "auto") == 0) {
        if (dir_max <= 8) {
            dir_format = DIR_DEG45;
            G_important_message(_("Flow direction format assumed to be "
                                  "degrees CCW from East divided by 45"));
        }
        else if (dir_max <= 128) {
            dir_format = DIR_POW2;
            G_important_message(_("Flow direction format assumed to be "
                                  "powers of 2 CW from East"));
        }
        else if (dir_max <= 360) {
            dir_format = DIR_DEG;
            G_important_message(
                _("Flow direction format assumed to be degrees CCW from East"));
        }
        else
            G_fatal_error(
                _("Unable to detect format of input direction map <%s>"),
                dir_name);
    }
    if (dir_format == DIR_UNKNOWN)
        G_fatal_error(_("Invalid direction format '%s'"), format);
    /* end of r.path */

    nrows = Rast_window_rows();
    ncols = Rast_window_cols();

    dir_map = G_malloc(sizeof *dir_map);
    dir_map->type = CELL_TYPE;
    dir_map->cell_size = Rast_cell_size(dir_map->type);
    dir_map->nrows = nrows;
    dir_map->ncols = ncols;
    dir_map->cells.v = G_malloc(dir_map->cell_size * nrows * ncols);
    dir_buf = G_malloc(dir_map->cell_size * ncols);

    for (row = 0; row < nrows; row++) {
        G_percent(row, nrows, 1);
        Rast_get_c_row(dir_fd, dir_buf, row);
        switch (dir_format) {
        case DIR_DEG:
            for (col = 0; col < ncols; col++)
                if (!Rast_is_c_null_value(&dir_buf[col]))
                    DIR(row, col) = pow(2, abs(dir_buf[col] / 45.));
            break;
        case DIR_DEG45:
            for (col = 0; col < ncols; col++)
                if (!Rast_is_c_null_value(&dir_buf[col]))
                    DIR(row, col) = pow(2, 8 - abs(dir_buf[col]));
            break;
        default:
            for (col = 0; col < ncols; col++)
                if (!Rast_is_c_null_value(&dir_buf[col]))
                    DIR(row, col) = abs(dir_buf[col]);
            break;
        }
    }
    G_percent(1, 1, 1);
    G_free(dir_buf);
    Rast_close(dir_fd);

    return dir_map;
}

void write_watersheds(char *wsheds_name, struct raster_map *wsheds_map)
{
    int wsheds_fd = Rast_open_new(wsheds_name, wsheds_map->type);
    int row;
    struct History hist;

    for (row = 0; row < wsheds_map->nrows; row++) {
        G_percent(row, wsheds_map->nrows, 1);
        Rast_put_row(wsheds_fd,
                     (char *)wsheds_map->cells.v +
                         wsheds_map->cell_size * wsheds_map->ncols * row,
                     wsheds_map->type);
    }
    G_percent(1, 1, 1);
    Rast_close(wsheds_fd);

    /* write history */
    Rast_put_cell_title(wsheds_name, _("Watersheds"));
    Rast_short_history(wsheds_name, "raster", &hist);
    Rast_command_history(&hist);
    Rast_write_history(wsheds_name, &hist);
}

void free_raster_map(struct raster_map *rast_map)
{
    G_free(rast_map->cells.v);
    G_free(rast_map);
}
