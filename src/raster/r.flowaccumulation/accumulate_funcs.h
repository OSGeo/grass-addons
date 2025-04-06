#include <stdlib.h>
#include <grass/raster.h>
#include "global.h"
#ifdef CHECK_OVERFLOW
#include <grass/glocale.h>
#endif
#if ACCUM_RAST_TYPE != CELL_TYPE
#include <math.h>
#endif

#if ACCUM_RAST_TYPE == CELL_TYPE
#define ACCUMULATE(o, m, z, w) accumulate_c##o##m##z##w
#define NULLIFY_ZERO           nullify_zero_c
#define ACCUM_MAP_CELLS        accum_map->cells.c
#define ACCUM_TYPE             int
#define SET_ACCUM_NULL(cell)   Rast_set_c_null_value(cell, 1)
#define IS_ACCUM_NULL(cell)    Rast_is_c_null_value(cell)
#elif ACCUM_RAST_TYPE == FCELL_TYPE
#define ACCUMULATE(o, m, z, w) accumulate_f##o##m##z##w
#define NULLIFY_ZERO           nullify_zero_f
#define ACCUM_MAP_CELLS        accum_map->cells.f
#define ACCUM_TYPE             float
#define SET_ACCUM_NULL(cell)   Rast_set_f_null_value(cell, 1)
#define IS_ACCUM_NULL(cell)    Rast_is_f_null_value(cell)
#else
#define ACCUMULATE(o, m, z, w) accumulate_d##o##m##z##w
#define NULLIFY_ZERO           nullify_zero_d
#define ACCUM_MAP_CELLS        accum_map->cells.d
#define ACCUM_TYPE             double
#define SET_ACCUM_NULL(cell)   Rast_set_d_null_value(cell, 1)
#define IS_ACCUM_NULL(cell)    Rast_is_d_null_value(cell)
#endif

#define ACCUM(row, col) ACCUM_MAP_CELLS[INDEX(row, col)]

#ifdef USE_WEIGHT
#define WEIGHT(row, col)                                            \
    ((ACCUM_TYPE)(weight_map->type == CELL_TYPE                     \
                      ? weight_map->cells.c[INDEX(row, col)]        \
                      : (weight_map->type == FCELL_TYPE             \
                             ? weight_map->cells.f[INDEX(row, col)] \
                             : weight_map->cells.d[INDEX(row, col)])))
#define IS_WEIGHT_NULL(row, col)                                              \
    (weight_map->type == CELL_TYPE                                            \
         ? Rast_is_c_null_value(&weight_map->cells.c[INDEX(row, col)])        \
         : (weight_map->type == FCELL_TYPE                                    \
                ? Rast_is_f_null_value(&weight_map->cells.f[INDEX(row, col)]) \
                : Rast_is_d_null_value(                                       \
                      &weight_map->cells.d[INDEX(row, col)])))
#define FIND_UP(row, col)                                                    \
    ((row > 0 ? (col > 0 && DIR(row - 1, col - 1) == SE &&                   \
                         !IS_WEIGHT_NULL(row - 1, col - 1)                   \
                     ? NW                                                    \
                     : 0) |                                                  \
                    (DIR(row - 1, col) == S && !IS_WEIGHT_NULL(row - 1, col) \
                         ? N                                                 \
                         : 0) |                                              \
                    (col < ncols - 1 && DIR(row - 1, col + 1) == SW &&       \
                             !IS_WEIGHT_NULL(row - 1, col + 1)               \
                         ? NE                                                \
                         : 0)                                                \
              : 0) |                                                         \
     (col > 0 && DIR(row, col - 1) == E && !IS_WEIGHT_NULL(row, col - 1)     \
          ? W                                                                \
          : 0) |                                                             \
     (col < ncols - 1 && DIR(row, col + 1) == W &&                           \
              !IS_WEIGHT_NULL(row, col + 1)                                  \
          ? E                                                                \
          : 0) |                                                             \
     (row < nrows - 1                                                        \
          ? (col > 0 && DIR(row + 1, col - 1) == NE &&                       \
                     !IS_WEIGHT_NULL(row + 1, col - 1)                       \
                 ? SW                                                        \
                 : 0) |                                                      \
                (DIR(row + 1, col) == N && !IS_WEIGHT_NULL(row + 1, col)     \
                     ? S                                                     \
                     : 0) |                                                  \
                (col < ncols - 1 && DIR(row + 1, col + 1) == NW &&           \
                         !IS_WEIGHT_NULL(row + 1, col + 1)                   \
                     ? SE                                                    \
                     : 0)                                                    \
          : 0))
#else
#define WEIGHT(row, col) 1
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
#endif

#ifdef USE_LESS_MEMORY
#define UP(row, col) FIND_UP(row, col)
#else
#define UP(row, col) up_cells[INDEX(row, col)]
static unsigned char *up_cells;
#endif

static int nrows, ncols;
static ACCUM_TYPE accum_not_ready;

static void trace_down(struct raster_map *,
#ifdef USE_WEIGHT
                       struct raster_map *,
#endif
                       struct raster_map *, int, int, ACCUM_TYPE);
static ACCUM_TYPE sum_up(struct raster_map *, int, int, int);

void ACCUMULATE(
#ifdef CHECK_OVERFLOW
    o
#endif
    ,
#ifdef USE_LESS_MEMORY
    m
#endif
    ,
#ifdef USE_ZERO
    z
#endif
    ,
#ifdef USE_WEIGHT
    w
#endif
    )(struct raster_map *dir_map,
#ifdef USE_WEIGHT
      struct raster_map *weight_map,
#endif
      struct raster_map *accum_map)
{
    int row, col;

    nrows = dir_map->nrows;
    ncols = dir_map->ncols;

#ifdef USE_WEIGHT
    SET_ACCUM_NULL(&accum_not_ready);
#else
    accum_not_ready = 0;
#endif

#ifndef USE_ZERO
#pragma omp parallel for schedule(dynamic)
    for (row = 0; row < nrows; row++)
        Rast_set_null_value((char *)accum_map->cells.v +
                                accum_map->cell_size * ncols * row,
                            ncols, accum_map->type);
#endif

#ifndef USE_LESS_MEMORY
    up_cells = calloc((size_t)nrows * ncols, sizeof *up_cells);

#pragma omp parallel for schedule(dynamic) private(col)
    for (row = 0; row < nrows; row++) {
        for (col = 0; col < ncols; col++)
            if (DIR(row, col))
                UP(row, col) = FIND_UP(row, col);
    }
#endif

#pragma omp parallel for schedule(dynamic) private(col)
    for (row = 0; row < nrows; row++) {
        for (col = 0; col < ncols; col++)
            /* if the current cell is not null and has no upstream cells, start
             * tracing down */
            if (DIR(row, col) && !UP(row, col)
#ifdef USE_WEIGHT
                && !IS_WEIGHT_NULL(row, col)
#endif
            )
                trace_down(dir_map,
#ifdef USE_WEIGHT
                           weight_map,
#endif
                           accum_map, row, col, WEIGHT(row, col));
    }

#ifndef USE_LESS_MEMORY
    free(up_cells);
#endif
}

#if !defined CHECK_OVERFLOW && !defined USE_LESS_MEMORY && \
    !defined USE_ZERO && !defined USE_WEIGHT
void NULLIFY_ZERO(struct raster_map *accum_map)
{
    int row, col;

    nrows = accum_map->nrows;
    ncols = accum_map->ncols;

#pragma omp parallel for schedule(dynamic) private(col)
    for (row = 0; row < nrows; row++)
        for (col = 0; col < ncols; col++)
            if (!ACCUM(row, col))
                SET_ACCUM_NULL(&ACCUM(row, col));
}
#endif

static void trace_down(struct raster_map *dir_map,
#ifdef USE_WEIGHT
                       struct raster_map *weight_map,
#endif
                       struct raster_map *accum_map, int row, int col,
                       ACCUM_TYPE accum)
{
    int up;
    ACCUM_TYPE accum_up = 0;

#ifdef CHECK_OVERFLOW
    if (
#if ACCUM_RAST_TYPE == CELL_TYPE
        Rast_is_c_null_value(&accum) || accum <= 0
#else
        isinf(accum)
#endif
    )
        G_fatal_error(
#if ACCUM_RAST_TYPE == CELL_TYPE
            _("Flow accumulation is too large. Try FCELL or DCELL type.")
#elif ACCUM_RAST_TYPE == FCELL_TYPE
            _("Flow accumulation is too large. Try DCELL type.")
#else
            _("Flow accumulation is too large.")
#endif
        );
#endif

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
    if (row < 0 || row >= nrows || col < 0 || col >= ncols || !DIR(row, col) ||
        !(up = UP(row, col))
#ifndef USE_WEIGHT
        || (accum_up = sum_up(accum_map, row, col, up)) == accum_not_ready
#endif
    )
        return;

#ifdef USE_WEIGHT
    accum_up = sum_up(accum_map, row, col, up);
    if (IS_ACCUM_NULL(&accum_up) || IS_WEIGHT_NULL(row, col))
        return;
#endif

    /* use gcc -O2 or -O3 flags for tail-call optimization
     * (-foptimize-sibling-calls) */
    trace_down(dir_map,
#ifdef USE_WEIGHT
               weight_map,
#endif
               accum_map, row, col, accum_up + WEIGHT(row, col));
}

/* if any upstream cells have never been visited, 0 is returned; otherwise, the
 * sum of upstream accumulation is returned */
static ACCUM_TYPE sum_up(struct raster_map *accum_map, int row, int col, int up)
{
    ACCUM_TYPE sum = 0, accum;

#pragma omp flush(accum_map)
    if (up & NW) {
#ifdef USE_ZERO
        if (!(accum = ACCUM(row - 1, col - 1)))
#else
        accum = ACCUM(row - 1, col - 1);
        if (IS_ACCUM_NULL(&accum))
#endif
            return accum_not_ready;
        sum += accum;
    }
    if (up & N) {
#ifdef USE_ZERO
        if (!(accum = ACCUM(row - 1, col)))
#else
        accum = ACCUM(row - 1, col);
        if (IS_ACCUM_NULL(&accum))
#endif
            return accum_not_ready;
        sum += accum;
    }
    if (up & NE) {
#ifdef USE_ZERO
        if (!(accum = ACCUM(row - 1, col + 1)))
#else
        accum = ACCUM(row - 1, col + 1);
        if (IS_ACCUM_NULL(&accum))
#endif
            return accum_not_ready;
        sum += accum;
    }
    if (up & W) {
#ifdef USE_ZERO
        if (!(accum = ACCUM(row, col - 1)))
#else
        accum = ACCUM(row, col - 1);
        if (IS_ACCUM_NULL(&accum))
#endif
            return accum_not_ready;
        sum += accum;
    }
    if (up & E) {
#ifdef USE_ZERO
        if (!(accum = ACCUM(row, col + 1)))
#else
        accum = ACCUM(row, col + 1);
        if (IS_ACCUM_NULL(&accum))
#endif
            return accum_not_ready;
        sum += accum;
    }
    if (up & SW) {
#ifdef USE_ZERO
        if (!(accum = ACCUM(row + 1, col - 1)))
#else
        accum = ACCUM(row + 1, col - 1);
        if (IS_ACCUM_NULL(&accum))
#endif
            return accum_not_ready;
        sum += accum;
    }
    if (up & S) {
#ifdef USE_ZERO
        if (!(accum = ACCUM(row + 1, col)))
#else
        accum = ACCUM(row + 1, col);
        if (IS_ACCUM_NULL(&accum))
#endif
            return accum_not_ready;
        sum += accum;
    }
    if (up & SE) {
#ifdef USE_ZERO
        if (!(accum = ACCUM(row + 1, col + 1)))
#else
        accum = ACCUM(row + 1, col + 1);
        if (IS_ACCUM_NULL(&accum))
#endif
            return accum_not_ready;
        sum += accum;
    }

    return sum;
}
