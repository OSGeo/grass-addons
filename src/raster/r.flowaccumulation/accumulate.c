#include <stdlib.h>
#include <grass/raster.h>
#include "global.h"

#define ACCUM(row, col) accum_map->cells[(size_t)(row)*ncols + (col)]
#define FIND_UP(row, col)                                                     \
    ((row > 0 ? (col > 0 && DIR(row - 1, col - 1) == SE ? NW : 0) |           \
                    (DIR(row - 1, col) == S ? N : 0) |                        \
                    (col < ncols - 1 && DIR(row - 1, col + 1) == SW ? NE : 0) \
              : 0) |                                                          \
     (col > 0 && DIR(row, col - 1) == E ? W : 0) |                            \
     (col < ncols - 1 && DIR(row, col + 1) == W ? E : 0) |                    \
     (row < nrows - 1                                                         \
          ? (col > 0 && DIR(row + 1, col - 1) == NE ? SW : 0) |               \
                (DIR(row + 1, col) == N ? S : 0) |                            \
                (col < ncols - 1 && DIR(row + 1, col + 1) == NW ? SE : 0)     \
          : 0))

#ifdef USE_LESS_MEMORY
#define UP(row, col) FIND_UP(row, col)
#else
#define UP(row, col) up_cells[(size_t)(row)*ncols + (col)]
static unsigned char *up_cells;
#endif

static int nrows, ncols;

static void trace_down(struct raster_map *, struct raster_map *, int, int, int);
static int sum_up(struct raster_map *, int, int, int);

void accumulate(struct raster_map *dir_map, struct raster_map *accum_map)
{
    int row, col;

    nrows = dir_map->nrows;
    ncols = dir_map->ncols;

#ifndef USE_LESS_MEMORY
    up_cells = calloc((size_t)nrows * ncols, sizeof *up_cells);

#pragma omp parallel for schedule(dynamic) private(col)
    for (row = 0; row < nrows; row++) {
        for (col = 0; col < ncols; col++)
            if (!Rast_is_c_null_value(&DIR(row, col)))
                UP(row, col) = FIND_UP(row, col);
    }
#endif

#pragma omp parallel for schedule(dynamic) private(col)
    for (row = 0; row < nrows; row++) {
        for (col = 0; col < ncols; col++)
            /* if the current cell is not null and has no upstream cells, start
             * tracing down */
            if (!Rast_is_c_null_value(&DIR(row, col)) && !UP(row, col))
                trace_down(dir_map, accum_map, row, col, 1);
    }

#ifndef USE_LESS_MEMORY
    free(up_cells);
#endif
}

static void trace_down(struct raster_map *dir_map, struct raster_map *accum_map,
                       int row, int col, int accum)
{
    int up, accum_up = 0;

    /* accumulate the current cell itself */
    ACCUM(row, col) = accum;

    /* find the downstream cell */
    switch (DIR(row, col)) {
    case NW:
        row--;
        col--;
        break;
    case N:
        row--;
        break;
    case NE:
        row--;
        col++;
        break;
    case W:
        col--;
        break;
    case E:
        col++;
        break;
    case SW:
        row++;
        col--;
        break;
    case S:
        row++;
        break;
    case SE:
        row++;
        col++;
        break;
    }

    /* if the downstream cell is null or any upstream cells of the downstream
     * cell have never been visited, stop tracing down */
    if (row < 0 || row >= nrows || col < 0 || col >= ncols ||
        Rast_is_c_null_value(&DIR(row, col)) || !(up = UP(row, col)) ||
        !(accum_up = sum_up(accum_map, row, col, up)))
        return;

    /* use gcc -O2 or -O3 flags for tail-call optimization
     * (-foptimize-sibling-calls) */
    trace_down(dir_map, accum_map, row, col, accum_up + 1);
}

/* if any upstream cells have never been visited, 0 is returned; otherwise, the
 * sum of upstream accumulation is returned */
static int sum_up(struct raster_map *accum_map, int row, int col, int up)
{
    int sum = 0, accum;

#pragma omp flush(accum_map)
    if (up & NW) {
        if (!(accum = ACCUM(row - 1, col - 1)))
            return 0;
        sum += accum;
    }
    if (up & N) {
        if (!(accum = ACCUM(row - 1, col)))
            return 0;
        sum += accum;
    }
    if (up & NE) {
        if (!(accum = ACCUM(row - 1, col + 1)))
            return 0;
        sum += accum;
    }
    if (up & W) {
        if (!(accum = ACCUM(row, col - 1)))
            return 0;
        sum += accum;
    }
    if (up & E) {
        if (!(accum = ACCUM(row, col + 1)))
            return 0;
        sum += accum;
    }
    if (up & SW) {
        if (!(accum = ACCUM(row + 1, col - 1)))
            return 0;
        sum += accum;
    }
    if (up & S) {
        if (!(accum = ACCUM(row + 1, col)))
            return 0;
        sum += accum;
    }
    if (up & SE) {
        if (!(accum = ACCUM(row + 1, col + 1)))
            return 0;
        sum += accum;
    }

    return sum;
}
