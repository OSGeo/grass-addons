#include <grass/raster.h>
#include "global.h"

void set(struct raster_map *buf, int row, int col, double value)
{
    switch (buf->type) {
    case CELL_TYPE:
        buf->map.c[row][col] = (CELL) value;
        break;
    case FCELL_TYPE:
        buf->map.f[row][col] = (FCELL) value;
        break;
    case DCELL_TYPE:
        buf->map.d[row][col] = (DCELL) value;
        break;
    }

    return;
}

double get(struct raster_map *buf, int row, int col)
{
    double value = 0;

    switch (buf->type) {
    case CELL_TYPE:
        value = (double)buf->map.c[row][col];
        break;
    case FCELL_TYPE:
        value = (double)buf->map.f[row][col];
        break;
    case DCELL_TYPE:
        value = buf->map.d[row][col];
        break;
    }

    return value;
}
