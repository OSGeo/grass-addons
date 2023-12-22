#include <grass/raster.h>
#include "global.h"

void set(struct raster_map *buf, int row, int col, double value)
{
    switch (buf->type) {
    case CELL_TYPE:
        buf->cells.c[row][col] = (CELL)value;
        break;
    case FCELL_TYPE:
        buf->cells.f[row][col] = (FCELL)value;
        break;
    case DCELL_TYPE:
        buf->cells.d[row][col] = (DCELL)value;
        break;
    }
}

double get(struct raster_map *buf, int row, int col)
{
    double value = 0;

    switch (buf->type) {
    case CELL_TYPE:
        value = (double)buf->cells.c[row][col];
        break;
    case FCELL_TYPE:
        value = (double)buf->cells.f[row][col];
        break;
    case DCELL_TYPE:
        value = buf->cells.d[row][col];
        break;
    }

    return value;
}

int is_null(struct raster_map *buf, int row, int col)
{
    int is_null_value = 0;

    switch (buf->type) {
    case CELL_TYPE:
        is_null_value = Rast_is_c_null_value(&buf->cells.c[row][col]);
        break;
    case FCELL_TYPE:
        is_null_value = Rast_is_f_null_value(&buf->cells.f[row][col]);
        break;
    case DCELL_TYPE:
        is_null_value = Rast_is_d_null_value(&buf->cells.d[row][col]);
        break;
    }

    return is_null_value;
}

void set_null(struct raster_map *buf, int row, int col)
{
    switch (buf->type) {
    case CELL_TYPE:
        Rast_set_c_null_value(&buf->cells.c[row][col], 1);
        break;
    case FCELL_TYPE:
        Rast_set_f_null_value(&buf->cells.f[row][col], 1);
        break;
    case DCELL_TYPE:
        Rast_set_d_null_value(&buf->cells.d[row][col], 1);
        break;
    }
}
