#include <stdlib.h>
#include <math.h>
#include "global.h"

#ifdef USE_FLOAT64_LENGTH
#define RASTER_TYPE float64
#define FLEN_TYPE   double
#else
#define RASTER_TYPE float32
#define FLEN_TYPE   float
#endif

#define INDEX(row, col) (size_t)(row) * ncols + (col)
#define DIR_NULL        (unsigned char)dir_map->null_value

#ifdef USE_LEAST_MEMORY
#define UFLEN uflen_leastmem
#define SET_UP(row, col)                                             \
    do {                                                             \
        FLEN(row, col) = -FLEN(row, col) - FIND_UP(row, col) / 256.; \
    } while (0)
#define GET_DIR(row, col) (unsigned char)abs(FLEN(row, col))
#define FLEN(row, col)    dir_map->cells.RASTER_TYPE[INDEX(row, col)]
#else

#ifdef USE_LESS_MEMORY
#define UFLEN        uflen_lessmem
#define UP(row, col) FIND_UP(row, col)
#else
#define UFLEN        uflen_moremem
#define UP(row, col) up_cells[INDEX(row, col)]
static unsigned char *up_cells;
#endif

#define DIR(row, col)     dir_map->cells.byte[INDEX(row, col)]
#define GET_DIR(row, col) DIR(row, col)
#define FLEN(row, col)    flen_map->cells.RASTER_TYPE[INDEX(row, col)]
#endif

#define FIND_UP(row, col)                                                     \
    ((row > 0                                                                 \
          ? (col > 0 && GET_DIR(row - 1, col - 1) == SE ? NW : 0) |           \
                (GET_DIR(row - 1, col) == S ? N : 0) |                        \
                (col < ncols - 1 && GET_DIR(row - 1, col + 1) == SW ? NE : 0) \
          : 0) |                                                              \
     (col > 0 && GET_DIR(row, col - 1) == E ? W : 0) |                        \
     (col < ncols - 1 && GET_DIR(row, col + 1) == W ? E : 0) |                \
     (row < nrows - 1                                                         \
          ? (col > 0 && GET_DIR(row + 1, col - 1) == NE ? SW : 0) |           \
                (GET_DIR(row + 1, col) == N ? S : 0) |                        \
                (col < ncols - 1 && GET_DIR(row + 1, col + 1) == NW ? SE : 0) \
          : 0))

static int nrows, ncols;

static int ortho_dirs = N | S | W | E;
static FLEN_TYPE ortho_flen, dia_flen, half_ortho_flen, half_dia_flen;

static void trace_down(struct raster_map *
#ifndef USE_LEAST_MEMORY
                       ,
                       struct raster_map *
#endif
                       ,
                       int, int, int, unsigned char);
static FLEN_TYPE max_up(
#if defined USE_LESS_MEMORY || defined USE_LEAST_MEMORY
    struct raster_map *,
#endif
#ifndef USE_LEAST_MEMORY
    struct raster_map *,
#endif
    int, int, int *);

void UFLEN(struct raster_map *dir_map
#ifndef USE_LEAST_MEMORY
           ,
           struct raster_map *flen_map
#endif
           ,
           int from_one)
{
    int row, col;

    nrows = dir_map->nrows;
    ncols = dir_map->ncols;

    ortho_flen = (dir_map->dx + dir_map->dy) / 2;
    dia_flen = sqrt(pow(dir_map->dx, 2) + pow(dir_map->dy, 2));
    half_ortho_flen = ortho_flen / 2;
    half_dia_flen = dia_flen / 2;

#ifdef USE_LEAST_MEMORY
#pragma omp parallel for schedule(dynamic) private(col)
    for (row = 0; row < nrows; row++) {
        for (col = 0; col < ncols; col++)
            if (FLEN(row, col) == DIR_NULL)
                FLEN(row, col) = 0;
            else
                SET_UP(row, col);
    }
    dir_map->null_value = 0;
#elifndef USE_LESS_MEMORY
    up_cells = calloc((size_t)nrows * ncols, sizeof *up_cells);
#pragma omp parallel for schedule(dynamic) private(col)
    for (row = 0; row < nrows; row++) {
        for (col = 0; col < ncols; col++)
            if (GET_DIR(row, col) != DIR_NULL)
                UP(row, col) = FIND_UP(row, col);
    }
#endif

#pragma omp parallel for schedule(dynamic) private(col)
    for (row = 0; row < nrows; row++) {
        for (col = 0; col < ncols; col++) {
            unsigned char dir, up;

#ifdef USE_LEAST_MEMORY
            FLEN_TYPE flen_dir;

#pragma omp atomic read seq_cst
            flen_dir = FLEN(row, col);
            if (flen_dir >= 0)
                continue;
            dir = (unsigned char)abs(flen_dir);
            up = (unsigned char)(((int)flen_dir - flen_dir) * 256);
#else
            if ((dir = GET_DIR(row, col)) == DIR_NULL)
                continue;
            up = UP(row, col);
#endif
            if (up)
                continue;

            /* if the current cell is not null and has no upstream cells, start
             * tracing down */

            /* assign the current cell's flen */
#pragma omp atomic write seq_cst
            FLEN(row, col) =
                from_one ? (dir & ortho_dirs ? half_ortho_flen : half_dia_flen)
                         : 1;

            trace_down(dir_map
#ifndef USE_LEAST_MEMORY
                       ,
                       flen_map
#endif
                       ,
                       from_one, row, col, dir);
        }
    }

#if !defined USE_LESS_MEMORY && !defined USE_LEAST_MEMORY
    free(up_cells);
#endif

    if (!from_one) {
        /* cells >= 1 are visited and cells == 0 are not; subtract 1 from them
         * to make visited cells start from 0 and unvisited cells null (-1); we
         * need to use this technique because the flen_map is initialized to 0
         * and using 0 as a valid cell value is not possible */
#ifdef USE_LEAST_MEMORY
        dir_map->null_value = -1;
#else
        flen_map->null_value--;
#endif
#pragma omp parallel for schedule(dynamic) private(col)
        for (row = 0; row < nrows; row++) {
            for (col = 0; col < ncols; col++)
                FLEN(row, col)--;
        }
    }
    /* else cells > 0 are visited and their values are desired; cells == 0 will
     * become null */
}

static void trace_down(struct raster_map *dir_map
#ifndef USE_LEAST_MEMORY
                       ,
                       struct raster_map *flen_map
#endif
                       ,
                       int from_one, int row, int col, unsigned char dir)
{
    int next_row = row, next_col = col;
    unsigned char next_dir = DIR_NULL;
    FLEN_TYPE flen_up;
    int nup;

#ifdef USE_LEAST_MEMORY
    FLEN_TYPE flen_dir;
#endif

    /* find the downstream cell */
    switch (dir) {
    case NW:
        next_row--;
        next_col--;
        break;
    case N:
        next_row--;
        break;
    case NE:
        next_row--;
        next_col++;
        break;
    case W:
        next_col--;
        break;
    case E:
        next_col++;
        break;
    case SW:
        next_row++;
        next_col--;
        break;
    case S:
        next_row++;
        break;
    case SE:
        next_row++;
        next_col++;
        break;
    }

    if (next_row >= 0 && next_row < nrows && next_col >= 0 &&
        next_col < ncols) {
#ifdef USE_LEAST_MEMORY
#pragma omp atomic read seq_cst
        flen_dir = FLEN(next_row, next_col);
        /* if the downstream cell is done, stop tracing down */
        if (flen_dir > 0)
            return;
        next_dir = (unsigned char)abs(flen_dir);
#else
        next_dir = GET_DIR(next_row, next_col);
#endif
    }

    /* if the downstream cell is null, stop tracing down */
    if (next_dir == DIR_NULL) {
        if (from_one)
            /* updating a terminal cell does not require atomicity because no
             * other threads will check its value */
            FLEN(row, col) +=
                dir & ortho_dirs ? half_ortho_flen : half_dia_flen;
        return;
    }

    /* if any upstream cells of the downstream cell have never been visited,
     * stop tracing down */
    if (!(flen_up = max_up(
#if defined USE_LESS_MEMORY || defined USE_LEAST_MEMORY
              dir_map,
#endif
#ifndef USE_LEAST_MEMORY
              flen_map,
#endif
              next_row, next_col, &nup)))
        return;

    /* only one thread should move to the next cell */
    if (nup == 1) {
#pragma omp atomic write seq_cst
        FLEN(next_row, next_col) = flen_up;
    }
    else {
        FLEN_TYPE expected = 0;

        /* if the next cell is already owned by another thread, stop */
#pragma omp atomic read seq_cst
        expected = FLEN(next_row, next_col);
        if (expected > 0)
            return;

        /* if the next cell is not owned yet by another thread, own it */
#pragma omp atomic compare capture seq_cst
        if (FLEN(next_row, next_col) == expected) {
            FLEN(next_row, next_col) = flen_up;
        }
        else {
            /* otherwise, we need to check this value again because
             * FLEN(next_row, next_col) could change between atomic read and
             * atomic compare capture */
            expected = FLEN(next_row, next_col);
        }

        /* at this point, if the current thread owned the next cell, expected
         * <= 0; otherwise, expected > 0 */
        if (expected > 0)
            return;
    }

    /* use gcc -O2 or -O3 flags for tail-call optimization
     * (-foptimize-sibling-calls) */
    trace_down(dir_map
#ifndef USE_LEAST_MEMORY
               ,
               flen_map
#endif
               ,
               from_one, next_row, next_col, next_dir);
}

/* if any upstream cells have never been visited, 0 is returned; otherwise, the
 * max of the upstream flen and the current flen is returned */
static FLEN_TYPE max_up(
#if defined USE_LESS_MEMORY || defined USE_LEAST_MEMORY
    struct raster_map *dir_map,
#endif
#ifndef USE_LEAST_MEMORY
    struct raster_map *flen_map,
#endif
    int row, int col, int *nup)
{
    unsigned char up;
    FLEN_TYPE max = 0, flen;

#ifdef USE_LEAST_MEMORY
    FLEN_TYPE flen_dir;

#pragma omp atomic read seq_cst
    flen_dir = FLEN(row, col);
    if (flen_dir > 0)
        return 0;
    up = (unsigned char)(((int)flen_dir - flen_dir) * 256);
#else
    up = UP(row, col);
#endif

    *nup = 0;
    if (up & NW) {
#ifdef USE_LEAST_MEMORY
#pragma omp atomic read seq_cst
        flen_dir = FLEN(row - 1, col - 1);
        flen = flen_dir < 0 ? 0 : flen_dir;
#else
#pragma omp atomic read seq_cst
        flen = FLEN(row - 1, col - 1);
#endif
        if (!flen)
            return 0;
        if (flen + dia_flen > max)
            max = flen + dia_flen;
        (*nup)++;
    }
    if (up & N) {
#ifdef USE_LEAST_MEMORY
#pragma omp atomic read seq_cst
        flen_dir = FLEN(row - 1, col);
        flen = flen_dir < 0 ? 0 : flen_dir;
#else
#pragma omp atomic read seq_cst
        flen = FLEN(row - 1, col);
#endif
        if (!flen)
            return 0;
        if (flen + ortho_flen > max)
            max = flen + ortho_flen;
        (*nup)++;
    }
    if (up & NE) {
#ifdef USE_LEAST_MEMORY
#pragma omp atomic read seq_cst
        flen_dir = FLEN(row - 1, col + 1);
        flen = flen_dir < 0 ? 0 : flen_dir;
#else
#pragma omp atomic read seq_cst
        flen = FLEN(row - 1, col + 1);
#endif
        if (!flen)
            return 0;
        if (flen + dia_flen > max)
            max = flen + dia_flen;
        (*nup)++;
    }
    if (up & W) {
#ifdef USE_LEAST_MEMORY
#pragma omp atomic read seq_cst
        flen_dir = FLEN(row, col - 1);
        flen = flen_dir < 0 ? 0 : flen_dir;
#else
#pragma omp atomic read seq_cst
        flen = FLEN(row, col - 1);
#endif
        if (!flen)
            return 0;
        if (flen + ortho_flen > max)
            max = flen + ortho_flen;
        (*nup)++;
    }
    if (up & E) {
#ifdef USE_LEAST_MEMORY
#pragma omp atomic read seq_cst
        flen_dir = FLEN(row, col + 1);
        flen = flen_dir < 0 ? 0 : flen_dir;
#else
#pragma omp atomic read seq_cst
        flen = FLEN(row, col + 1);
#endif
        if (!flen)
            return 0;
        if (flen + ortho_flen > max)
            max = flen + ortho_flen;
        (*nup)++;
    }
    if (up & SW) {
#ifdef USE_LEAST_MEMORY
#pragma omp atomic read seq_cst
        flen_dir = FLEN(row + 1, col - 1);
        flen = flen_dir < 0 ? 0 : flen_dir;
#else
#pragma omp atomic read seq_cst
        flen = FLEN(row + 1, col - 1);
#endif
        if (!flen)
            return 0;
        if (flen + dia_flen > max)
            max = flen + dia_flen;
        (*nup)++;
    }
    if (up & S) {
#ifdef USE_LEAST_MEMORY
#pragma omp atomic read seq_cst
        flen_dir = FLEN(row + 1, col);
        flen = flen_dir < 0 ? 0 : flen_dir;
#else
#pragma omp atomic read seq_cst
        flen = FLEN(row + 1, col);
#endif
        if (!flen)
            return 0;
        if (flen + ortho_flen > max)
            max = flen + ortho_flen;
        (*nup)++;
    }
    if (up & SE) {
#ifdef USE_LEAST_MEMORY
#pragma omp atomic read seq_cst
        flen_dir = FLEN(row + 1, col + 1);
        flen = flen_dir < 0 ? 0 : flen_dir;
#else
#pragma omp atomic read seq_cst
        flen = FLEN(row + 1, col + 1);
#endif
        if (!flen)
            return 0;
        if (flen + dia_flen > max)
            max = flen + dia_flen;
        (*nup)++;
    }

    return max;
}
