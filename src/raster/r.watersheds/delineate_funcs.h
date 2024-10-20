#include <stdlib.h>
#include "global.h"

#define SHED(row, col) DIR(row, col)

#ifdef USE_LESS_MEMORY
#define DELINEATE         delineate_lessmem
#define GET_DIR(row, col) (DIR(row, col) & 0x7fffffff)
#define SET_NOTDONE(row, col)        \
    do {                             \
        DIR(row, col) |= 0x80000000; \
    } while (0)
#define SET_DONE(row, col)           \
    do {                             \
        DIR(row, col) &= 0x7fffffff; \
    } while (0)
#define IS_NOTDONE(row, col) (DIR(row, col) & 0x80000000)
#define IS_DONE(row, col)    !IS_NOTDONE(row, col)
#else
#define DELINEATE         delineate_moremem
#define GET_DIR(row, col) DIR(row, col)
#define DONE(row, col)    done[INDEX(row, col)]
#define SET_DONE(row, col)  \
    do {                    \
        DONE(row, col) = 1; \
    } while (0)
#define IS_NOTDONE(row, col) !DONE(row, col)
#define IS_DONE(row, col)    DONE(row, col)
static char *done;
#endif

#define E  1
#define SE 2
#define S  4
#define SW 8
#define W  16
#define NW 32
#define N  64
#define NE 128

static int dir_checks[3][3] = {{SE, S, SW}, {E, 0, W}, {NE, N, NW}};

struct cell {
    int row;
    int col;
};

struct cell_stack {
    struct cell *cells;
    int n;
    int nalloc;
};

static int nrows, ncols;

static void trace_up(struct raster_map *, int, int, int, struct cell_stack *);
static void init_up_stack(struct cell_stack *);
static void free_up_stack(struct cell_stack *);
static void push_up(struct cell_stack *, struct cell *);
static struct cell pop_up(struct cell_stack *);

void DELINEATE(struct raster_map *dir_map, struct outlet_list *outlet_l)
{
    int i, j;

    nrows = dir_map->nrows;
    ncols = dir_map->ncols;

#ifdef USE_LESS_MEMORY
#pragma omp parallel for schedule(dynamic) private(j)
    for (i = 0; i < nrows; i++) {
        for (j = 0; j < ncols; j++)
            SET_NOTDONE(i, j);
    }
#else
    done = calloc((size_t)nrows * ncols, sizeof *done);
#endif

#pragma omp parallel for schedule(dynamic)
    for (i = 0; i < outlet_l->n; i++) {
#ifndef USE_LESS_MEMORY
        SET_DONE(outlet_l->row[i], outlet_l->col[i]);
#endif
        SHED(outlet_l->row[i], outlet_l->col[i]) = outlet_l->id[i];
    }

    /* loop through all outlets and delineate the subwatershed for each */
#pragma omp parallel for schedule(dynamic)
    for (i = 0; i < outlet_l->n; i++) {
        struct cell_stack up_stack;

        init_up_stack(&up_stack);

        /* trace up flow directions */
        trace_up(dir_map, outlet_l->row[i], outlet_l->col[i], outlet_l->id[i],
                 &up_stack);

        free_up_stack(&up_stack);
    }

#pragma omp parallel for schedule(dynamic) private(j)
    for (i = 0; i < nrows; i++) {
        for (j = 0; j < ncols; j++)
            if (IS_NOTDONE(i, j))
                Rast_set_c_null_value(&SHED(i, j), 1);
    }

#ifndef USE_LESS_MEMORY
    free(done);
#endif
}

static void trace_up(struct raster_map *dir_map, int row, int col, int id,
                     struct cell_stack *up_stack)
{
    int i, j;
    int nup = 0;
    int next_row = -1, next_col = -1;

    for (i = -1; i <= 1; i++) {
        /* skip edge cells */
        if (row + i < 0 || row + i >= nrows)
            continue;

        for (j = -1; j <= 1; j++) {
            /* skip the current and edge cells */
            if ((i == 0 && j == 0) || col + j < 0 || col + j >= ncols)
                continue;

            /* if a neighbor cell flows into the current cell, trace up
             * further; we need to check if that neighbor cell has already been
             * processed because we don't want to misinterpret a subwatershed
             * ID as a direction; remember we're overwriting dir_map so it can
             * have both directions and subwatershed IDs */
            if (GET_DIR(row + i, col + j) == dir_checks[i + 1][j + 1] &&
                IS_NOTDONE(row + i, col + j)) {
                if (++nup == 1) {
                    /* climb up only to this cell at this time */
                    next_row = row + i;
                    next_col = col + j;
#ifndef USE_LESS_MEMORY
                    SET_DONE(next_row, next_col);
#endif
                    SHED(next_row, next_col) = id;
                }
                else
                    /* if we found more than one upstream cell, we don't need
                     * to find more at this point */
                    break;
            }
        }
        /* if we found more than one upstream cell, we don't need to find more
         * at this point */
        if (nup > 1)
            break;
    }

    if (!nup) {
        /* reached a ridge cell; if there were any up cells to visit, let's go
         * back or simply complete tracing */
        struct cell up;

        if (!up_stack->n)
            return;

        up = pop_up(up_stack);
        next_row = up.row;
        next_col = up.col;
    }
    else if (nup > 1) {
        /* if there are more up cells to visit, let's come back later */
        struct cell up;

        up.row = row;
        up.col = col;
        push_up(up_stack, &up);
    }

    /* use gcc -O2 or -O3 flags for tail-call optimization
     * (-foptimize-sibling-calls) */
    trace_up(dir_map, next_row, next_col, id, up_stack);
}

static void init_up_stack(struct cell_stack *up_stack)
{
    up_stack->nalloc = up_stack->n = 0;
    up_stack->cells = NULL;
}

static void free_up_stack(struct cell_stack *up_stack)
{
    if (up_stack->cells)
        free(up_stack->cells);
    init_up_stack(up_stack);
}

static void push_up(struct cell_stack *up_stack, struct cell *up)
{
    if (up_stack->n == up_stack->nalloc) {
        up_stack->nalloc += REALLOC_INCREMENT;
        up_stack->cells = realloc(up_stack->cells,
                                  sizeof *up_stack->cells * up_stack->nalloc);
    }
    up_stack->cells[up_stack->n++] = *up;
}

static struct cell pop_up(struct cell_stack *up_stack)
{
    struct cell up;

    if (up_stack->n > 0) {
        up = up_stack->cells[--up_stack->n];
        if (up_stack->n == 0)
            free_up_stack(up_stack);
        else if (up_stack->n == up_stack->nalloc - REALLOC_INCREMENT) {
            up_stack->nalloc -= REALLOC_INCREMENT;
            up_stack->cells = realloc(up_stack->cells, sizeof *up_stack->cells *
                                                           up_stack->nalloc);
        }
    }

    return up;
}
