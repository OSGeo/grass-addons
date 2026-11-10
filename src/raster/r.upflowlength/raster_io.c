#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <grass/gis.h>
#include <grass/raster.h>
#include <grass/glocale.h>
#include "global.h"

#ifdef USE_FLOAT64_LENGTH
#define RASTER_TYPE          float64
#define FLEN_TYPE            double
#define FLEN_RASTER_MAP_TYPE DCELL_TYPE
#else
#define RASTER_TYPE          float32
#define FLEN_TYPE            float
#define FLEN_RASTER_MAP_TYPE FCELL_TYPE
#endif

#define INDEX(row, col) (size_t)(row) * ncols + (col)
#define DIR(row, col)   rast_map->cells.RASTER_TYPE[INDEX(row, col)]
#define FLEN(row, col)  DIR(row, col)

#define DIR_RECODE      0
#define DIR_DEG         1
#define DIR_45DEG       2
#define DIR_POW2        3

static double recode_encoding(double, void *);

struct raster_map *read_direction(char *dir_name, char *format, char *encoding)
{
    int dir_fd, dir_format = DIR_RECODE;
    struct Range dir_range;
    int dir_encoding[8];
    CELL dir_min, dir_max, *dir_buf, dir_null;
    int detect = strcmp(format, "auto") == 0;
    struct Cell_head window;
    struct raster_map *rast_map;
    int nrows, ncols, row, col;

    dir_fd = Rast_open_old(dir_name, "");
    if (Rast_get_map_type(dir_fd) != CELL_TYPE)
        G_fatal_error(_("Type of flow direction raster <%s> must be CELL"),
                      dir_name);

    if (Rast_read_range(dir_name, "", &dir_range) < 0)
        G_fatal_error(
            _("Unable to read range file of flow direction raster <%s>"),
            dir_name);
    Rast_get_range_min_max(&dir_range, &dir_min, &dir_max);

    if (strcmp(format, "45degree") == 0 || (detect && dir_max <= 8)) {
        dir_format = DIR_45DEG;
        if (detect)
            G_important_message(_("Flow direction format assumed to be "
                                  "degrees CCW from East divided by 45"));
    }
    else if (strcmp(format, "power2") == 0 || (detect && dir_max <= 128)) {
        dir_format = DIR_POW2;
        G_important_message(_("Flow direction format assumed to be "
                              "powers of 2 CW from East"));
    }
    else if (strcmp(format, "degree") == 0 || (detect && dir_max <= 360)) {
        dir_format = DIR_DEG;
        if (detect)
            G_important_message(_("Flow direction format assumed to be "
                                  "degrees CCW from East"));
    }
    else if (detect)
        G_fatal_error(_("Unable to detect format of input direction map <%s>"),
                      dir_name);
    else if (strcmp(format, "taudem") == 0) {
        int i;

        for (i = 1; i < 9; i++)
            dir_encoding[i % 8] = 9 - i;
    }
    else if (sscanf(encoding, "%d,%d,%d,%d,%d,%d,%d,%d", &dir_encoding[0],
                    &dir_encoding[1], &dir_encoding[2], &dir_encoding[3],
                    &dir_encoding[4], &dir_encoding[5], &dir_encoding[6],
                    &dir_encoding[7]) != 8)
        G_fatal_error(_("%s: Invalid direction encoding"), encoding);

    nrows = Rast_window_rows();
    ncols = Rast_window_cols();

    Rast_set_c_null_value(&dir_null, 1);
    Rast_get_window(&window);

    rast_map = G_malloc(sizeof *rast_map);
    rast_map->type = FLEN_RASTER_MAP_TYPE;
    rast_map->cell_size = sizeof(FLEN_TYPE);
    rast_map->nrows = nrows;
    rast_map->ncols = ncols;
    rast_map->cells.v = G_calloc(rast_map->cell_size * nrows * ncols, 1);
    rast_map->null_value = dir_null;
    rast_map->dx = window.ew_res;
    rast_map->dy = window.ns_res;

    dir_buf = G_malloc(sizeof(CELL) * ncols);

    for (row = 0; row < nrows; row++) {
        G_percent(row, nrows, 1);
        Rast_get_c_row(dir_fd, dir_buf, row);
        switch (dir_format) {
        case DIR_DEG:
            for (col = 0; col < ncols; col++)
                if (!Rast_is_c_null_value(&dir_buf[col]))
                    DIR(row, col) = pow(2, abs(dir_buf[col]) / 45.);
            break;
        case DIR_45DEG:
            for (col = 0; col < ncols; col++)
                if (!Rast_is_c_null_value(&dir_buf[col]))
                    DIR(row, col) = pow(2, 8 - abs(dir_buf[col]));
            break;
        case DIR_POW2:
            for (col = 0; col < ncols; col++)
                if (!Rast_is_c_null_value(&dir_buf[col]))
                    DIR(row, col) = abs(dir_buf[col]);
            break;
        default:
            for (col = 0; col < ncols; col++)
                if (!Rast_is_c_null_value(&dir_buf[col]))
                    DIR(row, col) = recode_encoding(dir_buf[col], dir_encoding);
            break;
        }
    }
    G_percent(1, 1, 1);
    G_free(dir_buf);
    Rast_close(dir_fd);

    return rast_map;
}

static double recode_encoding(double value, void *data)
{
    int *encoding = data;
    int internal_encoding[8] = {E, SE, S, SW, W, NW, N, NE};
    int i;

    for (i = 0; i < 8 && abs(value) != encoding[i]; i++)
        ;
    if (i < 8)
        value = internal_encoding[i];

    return value;
}

void nullify_raster_map(struct raster_map *rast_map)
{
    int nrows = rast_map->nrows, ncols = rast_map->ncols, row, col;

#pragma omp parallel for schedule(dynamic) private(col)
    for (row = 0; row < nrows; row++) {
        for (col = 0; col < ncols; col++)
            if (FLEN(row, col) == rast_map->null_value)
                Rast_set_null_value(&FLEN(row, col), 1, rast_map->type);
    }
}

void write_raster_map(struct raster_map *rast_map, char *name)
{
    int fd, row;

    fd = Rast_open_new(name, rast_map->type);
    for (row = 0; row < rast_map->nrows; row++) {
        G_percent(row, rast_map->nrows, 1);
        Rast_put_row(fd,
                     (char *)rast_map->cells.v +
                         rast_map->cell_size * rast_map->ncols * row,
                     rast_map->type);
    }
    G_percent(1, 1, 1);
    Rast_close(fd);
}

void free_raster_map(struct raster_map *rast_map)
{
    G_free(rast_map->cells.v);
    G_free(rast_map);
}
