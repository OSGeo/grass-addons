#include <stdlib.h>
#ifdef _MSC_VER
/* MSVC requires this definition to expose common math constants because they
 * are not part of the C standards */
#define _USE_MATH_DEFINES
#endif
#include <math.h>
#include <grass/gis.h>
#include <grass/raster.h>
#include "global.h"

#define INDEX(row, col)       ((size_t)(row) * ncols + (col))
#define DIR(row, col)         dir_map->cells.byte[INDEX(row, col)]
#define IS_DIR_NULL(row, col) Rast_is_c_null_value(&DIR(row, col))

#ifdef USE_LESS_MEMORY
#define LFP lfp_lessmem
#define SET_OUTLET(row, col) \
    do {                     \
        DIR(row, col) = 0;   \
    } while (0)
#define IS_OUTLET(row, col) !DIR(row, col)

/* to flag a cell as done, add 5 to its direction value; 5 is the smallest
 * number that won't change the direction to another; for example, adding 3 to
 * E (1) would change E to S (4) */
#define SET_DONE(row, col)  \
    do {                    \
        DIR(row, col) += 5; \
    } while (0)

/* if a direction value was not altered by adding 5, subtracting 1 from it will
 * clear the bit position for the original value and the bitwise AND between
 * the original and 1-subtracted values will yield 0; if a direction value was
 * altered by adding 5, the bitwise AND value will have some bits uncleared,
 * indicating which cells are done */
#define IS_RECOVERABLE(row, col) \
    (!IS_DIR_NULL(row, col) && DIR(row, col) & (DIR(row, col) - 1))

/* recover the original direction value by subtracting 5 */
#define RECOVER(row, col)   \
    do {                    \
        DIR(row, col) -= 5; \
    } while (0)

static unsigned char *outlet_dirs;
#else
#define LFP lfp_moremem
#ifdef USE_BITS_FOR_MORE_MEMORY

/*******************************************************************************
 * this more-memory version allocates one byte per four cells
 *
 * XXX: the idea was great, but data races can occur because multiple threads
 * can try to update the same byte in the done array for four different cells;
 * I've tried omp critical statements for SET_OUTLET and SET_DONE, but they
 * turn out to be too slow; with data races, multiple identical longest flow
 * paths can be generated; that's not too bad, but just don't use this mode;
 * why would you want to save memory when you use a more-memory version anyway?
 * either use the less-memory version or the byte-mode more-memory version.
 */

/* store outlet and done bit flags for four cells in a byte; the total number
 * of cells divided by 4 (>> 2) plus one byte for remaining three cells if any
 */
#define SIZE \
    ((((size_t)nrows * ncols) >> 2) + ((((size_t)nrows * ncols) & 3) != 0))

/* divide the cell index by 4 (>> 2) to find the location in the done array
 * where information for four cells is stored in a byte */
#define DONE(row, col) done[INDEX(row, col) >> 2]

/* in each byte in the done array, odd bits are for done flags; however, BIT0
 * does not return a bit location, but it indicates the actual flagged value
 * for the indexed cell */
#define BIT0(row, col) (1 << ((INDEX(row, col) & 3) << 1))

/* even bits are for outlet flags; similarly, BIT1 returns the actual flagged
 * value for the indexed cell */
#define BIT1(row, col) (BIT0(row, col) << 1)

/* tests for bit flags */
#define SET_OUTLET(row, col)              \
    do {                                  \
        DONE(row, col) |= BIT1(row, col); \
    } while (0)
#define IS_OUTLET(row, col) (DONE(row, col) & BIT1(row, col))
#define SET_DONE(row, col)                \
    do {                                  \
        DONE(row, col) |= BIT0(row, col); \
    } while (0)
#define IS_NOTDONE(row, col) \
    !(DONE(row, col) & (BIT0(row, col) | BIT1(row, col)))
#else

/*******************************************************************************
 * this more-memory version allocates one byte per cell
 */
#define SIZE           ((size_t)nrows * ncols)
#define DONE(row, col) done[INDEX(row, col)]

/* bit 0 for outlet */
#define SET_OUTLET(row, col) \
    do {                     \
        DONE(row, col) |= 1; \
    } while (0)
#define IS_OUTLET(row, col) (DONE(row, col) & 1)

/* bit 1 for done */
#define SET_DONE(row, col)   \
    do {                     \
        DONE(row, col) |= 2; \
    } while (0)
#define IS_NOTDONE(row, col) !(DONE(row, col) & 3)
#endif
static char *done;
#endif

/* relative row, col, and direction to the center in order of
 * E S W N SE SW NW NE */
static int nbr_rcd[8][3] = {{0, 1, W},  {1, 0, N},   {0, -1, E},   {-1, 0, S},
                            {1, 1, NW}, {1, -1, NE}, {-1, -1, SE}, {-1, 1, SW}};

struct cell {
    int row;
    int col;
    int northo;
    int ndia;
};

struct cell_stack {
    struct cell *cells;
    int n;
    int nalloc;
};

static int nrows, ncols;

#ifdef LOOP_THEN_TASK
#define TRACE_UP_RETURN int
#else
#define TRACE_UP_RETURN void
#endif

static TRACE_UP_RETURN trace_up(struct raster_map *, int, int, int, int, int *,
                                int *, double *, struct point_list *,
                                struct cell_stack *);
static void find_full_lfp(struct raster_map *, struct outlet_list *);
static void init_up_stack(struct cell_stack *);
static void free_up_stack(struct cell_stack *);
static void push_up(struct cell_stack *, struct cell *);
static void pop_up(struct cell_stack *, struct cell *);

void LFP(struct raster_map *dir_map, struct outlet_list *outlet_l, int find_full
#ifdef USE_LESS_MEMORY
         ,
         int preserve_dir
#endif
)
{
    int i;

    nrows = dir_map->nrows;
    ncols = dir_map->ncols;

#ifdef USE_LESS_MEMORY
    outlet_dirs = G_calloc(outlet_l->n, sizeof *outlet_dirs);
#else
    done = G_calloc(SIZE, sizeof *done);
#endif

#pragma omp parallel for schedule(dynamic)
    for (i = 0; i < outlet_l->n; i++) {
        int j;
        int nup = 0;

#ifdef USE_LESS_MEMORY
        outlet_dirs[i] = DIR(outlet_l->row[i], outlet_l->col[i]);
#endif
        for (j = 0; j < 8; j++) {
            int nbr_row = outlet_l->row[i] + nbr_rcd[j][0];
            int nbr_col = outlet_l->col[i] + nbr_rcd[j][1];

            /* skip edge cells */
            if (nbr_row < 0 || nbr_row >= nrows || nbr_col < 0 ||
                nbr_col >= ncols)
                continue;

            if (DIR(nbr_row, nbr_col) == nbr_rcd[j][2])
                nup++;
        }

        /* only if the outlet has any upstream neighbor cells, flag it as an
         * outlet to avoid cross-tracing it because subwatershed-level longest
         * flow paths should not pass through any outlets; however, if it is a
         * headwater cell without any upstream cells, it can start a longest
         * flow path for its downstream outlets, if any, so leave them */
        if (nup)
            SET_OUTLET(outlet_l->row[i], outlet_l->col[i]);
    }

    /* loop through all outlets and find longest flow paths for subwatersheds
     */
#ifdef _MSC_VER
    /* XXX: MSVC requires private(i) so that a thread creating tasks can share
     * its private i with threads who will execute generated tasks later
     * (undocumented?); otherwise, i should be private by default */
#pragma omp parallel for schedule(dynamic) private(i)
#else
#pragma omp parallel for schedule(dynamic)
#endif
    for (i = 0; i < outlet_l->n; i++) {
        struct cell_stack *up_stack = G_malloc(sizeof *up_stack);

        init_up_stack(up_stack);

        /* trace up flow directions */
#ifdef LOOP_THEN_TASK
        /* if this outlet is the last one, use tasking for better load
         * balancing */
        if (
#endif
            trace_up(dir_map, outlet_l->row[i], outlet_l->col[i], 0, 0,
                     &outlet_l->northo[i], &outlet_l->ndia[i],
                     &outlet_l->lflen[i], &outlet_l->head_pl[i], up_stack)
#ifdef LOOP_THEN_TASK
        ) {
#ifdef _MSC_VER
            /* XXX: MSVC needs it! even with the above private(i), i inside
             * tasks is not the same as i from the creator thread
             * (undocumented?); GCC works without this line */
            int I = i;
#else
#define I i
#endif

            do {
                /* calculate upstream longest flow paths at branching cells,
                 * compare their lengths, and add them if necessary */
                while (up_stack->n) {
                    struct cell up;

#pragma omp critical
                    pop_up(up_stack, &up);

#pragma omp task
                    {
                        int row = up.row, col = up.col;
                        int down_northo = up.northo, down_ndia = up.ndia;
                        int northo, ndia;
                        double lflen = 0;
                        struct point_list head_pl;
                        struct cell_stack *task_up_stack =
                            G_malloc(sizeof *task_up_stack);

                        init_point_list(&head_pl);
                        init_up_stack(task_up_stack);

                        /* calculate upstream longest flow paths from a
                         * branching node */
                        if (trace_up(dir_map, row, col, down_northo, down_ndia,
                                     &northo, &ndia, &lflen, &head_pl,
                                     task_up_stack)) {
                            while (task_up_stack->n) {
                                struct cell task_up;

                                pop_up(task_up_stack, &task_up);

#pragma omp critical
                                push_up(up_stack, &task_up);
                            }
                        }

                        free_up_stack(task_up_stack);

                        /* this block is critical to avoid race conditions when
                         * updating outlet_l->*[i] values */
#pragma omp critical
                        {
                            /* if its longest flow length is longer than or
                             * equal to the previously found one, add new
                             * longest flow paths */
                            if (lflen >= outlet_l->lflen[I]) {
                                int j;

                                /* if it is longer, reomve all previous longest
                                 * flow paths first */
                                if (lflen > outlet_l->lflen[I]) {
                                    outlet_l->northo[I] = northo;
                                    outlet_l->ndia[I] = ndia;
                                    outlet_l->lflen[I] = lflen;
                                    reset_point_list(&outlet_l->head_pl[I]);
                                }

                                /* add all new longest flow paths */
                                for (j = 0; j < head_pl.n; j++)
                                    add_point(&outlet_l->head_pl[I],
                                              head_pl.row[j], head_pl.col[j]);
                            }
                        }

                        free_point_list(&head_pl);
                    }
                }
#pragma omp taskwait
            } while (up_stack->n);
        }
#endif
        /* XXX: work around an indent bug
         * #else
         *     ;
         * #endif
         * doesn't work */
        ;

        free_up_stack(up_stack);
    }

#ifdef USE_LESS_MEMORY
    /* if 5 was added previously (multiple bits), recover directions */
    if (find_full || preserve_dir) {
        int r, c;

#pragma omp parallel for schedule(dynamic)
        for (r = 0; r < nrows; r++)
            for (c = 0; c < ncols; c++) {
                if (IS_RECOVERABLE(r, c))
                    RECOVER(r, c);
            }
    }
#endif

    if (find_full)
        find_full_lfp(dir_map, outlet_l);

#ifdef USE_LESS_MEMORY
    /* recover outlet directions */
    if (preserve_dir) {
#pragma omp parallel for schedule(dynamic)
        for (i = 0; i < outlet_l->n; i++)
            DIR(outlet_l->row[i], outlet_l->col[i]) = outlet_dirs[i];
    }
    G_free(outlet_dirs);
#else
    G_free(done);
#endif
}

static TRACE_UP_RETURN trace_up(struct raster_map *dir_map, int row, int col,
                                int down_northo, int down_ndia, int *northo,
                                int *ndia, double *lflen,
                                struct point_list *head_pl,
                                struct cell_stack *up_stack)
{
#ifdef DONT_USE_TCO
    do {
#endif
        int i;
        int nup = 0;
        int next_row = -1, next_col = -1;
        int ortho = 0, dia = 0;
        struct cell up;

        for (i = 0; i < 8; i++) {
            int nbr_row = row + nbr_rcd[i][0];
            int nbr_col = col + nbr_rcd[i][1];

            /* skip edge cells */
            if (nbr_row < 0 || nbr_row >= nrows || nbr_col < 0 ||
                nbr_col >= ncols)
                continue;

            /* if a neighbor cell flows into the current cell, trace up further
             */
            if (DIR(nbr_row, nbr_col) == nbr_rcd[i][2]
#ifndef USE_LESS_MEMORY
                && IS_NOTDONE(nbr_row, nbr_col)
#endif
                && ++nup == 1) {
                /* climb up only to this cell at this time */
                next_row = nbr_row;
                next_col = nbr_col;
                ortho = i < 4;
                dia = !ortho;
                SET_DONE(next_row, next_col);
            }
        }

        if (!nup) {
            /* reached a ridge cell; if there were any up cells to visit, let's
             * go back or simply complete tracing */
            double flen = down_northo + down_ndia * M_SQRT2;

            if (flen >= *lflen) {
                if (flen > *lflen) {
                    *northo = down_northo;
                    *ndia = down_ndia;
                    *lflen = flen;
                    reset_point_list(head_pl);
                }
                add_point(head_pl, row, col);
            }

            if (!up_stack->n)
                return
#ifdef LOOP_THEN_TASK
                    0
#endif
                    ;

#ifdef LOOP_THEN_TASK
            /* next cell is not popped yet;
             * if current stack size >= tracing stack size */
            if (up_stack->n >= tracing_stack_size)
                return 1;
#endif

            pop_up(up_stack, &up);
            next_row = up.row;
            next_col = up.col;
            down_northo = up.northo;
            down_ndia = up.ndia;
        }
        else if (nup > 1) {
            /* if there are more up cells to visit, let's come back later */
            up.row = row;
            up.col = col;
            up.northo = down_northo;
            up.ndia = down_ndia;
            push_up(up_stack, &up);
        }

#ifdef LOOP_THEN_TASK
        /* next cell is not in the stack;
         * if current stack size + next cell >= tracing stack size */
        if (up_stack->n + 1 >= tracing_stack_size) {
            up.row = next_row;
            up.col = next_col;
            up.northo = down_northo + ortho;
            up.ndia = down_ndia + dia;
            push_up(up_stack, &up);

            return 1;
        }
#endif

#ifdef DONT_USE_TCO
        row = next_row;
        col = next_col;
        down_northo += ortho;
        down_ndia += dia;
    } while (1);
    /* XXX: work around an indent bug
     * #else
     * doesn't work */
#endif
#ifndef DONT_USE_TCO
    /* use gcc -O2 or -O3 flags for tail-call optimization
     * (-foptimize-sibling-calls) */
#ifdef LOOP_THEN_TASK
    return
#endif
        trace_up(dir_map, next_row, next_col, down_northo + ortho,
                 down_ndia + dia, northo, ndia, lflen, head_pl, up_stack);
#endif
}

static void find_full_lfp(struct raster_map *dir_map,
                          struct outlet_list *outlet_l)
{
    int i, j;
    int found_down = 0;

    if (outlet_l->n == 1)
        return;

#pragma omp parallel for schedule(dynamic)
    for (i = 0; i < outlet_l->n; i++) {
        int r = outlet_l->row[i], c = outlet_l->col[i];
        unsigned char dir;
        int northo = 0, ndia = 0;

#ifdef USE_LESS_MEMORY
        dir = outlet_dirs[i];
#else
        dir = DIR(r, c);
#endif

        do {
            switch (dir) {
            case NE:
                r--;
                c++;
                ndia++;
                break;
            case N:
                r--;
                northo++;
                break;
            case NW:
                r--;
                c--;
                ndia++;
                break;
            case W:
                c--;
                northo++;
                break;
            case SW:
                r++;
                c--;
                ndia++;
                break;
            case S:
                r++;
                northo++;
                break;
            case SE:
                r++;
                c++;
                ndia++;
                break;
            case E:
                c++;
                northo++;
                break;
            }
            dir = DIR(r, c);
        } while (r >= 0 && r < nrows && c >= 0 && c < ncols &&
                 !IS_DIR_NULL(r, c) && !IS_OUTLET(r, c));

        outlet_l->flen[i] = northo + ndia * M_SQRT2;

        if (IS_OUTLET(r, c)) {
            for (j = 0; j < outlet_l->n; j++) {
                if (j != i && outlet_l->row[j] == r && outlet_l->col[j] == c) {
                    outlet_l->has_up[j] = 1;
                    outlet_l->down[i] = j;
                    if (!found_down)
                        found_down = 1;
                    break;
                }
            }
        }
    }

    if (!found_down)
        return;

    /* cannot be parallelized because multiple threads could try to update a
     * common downstream outlet's head_pl, possibly causing a race condition */
    for (i = 0; i < outlet_l->n; i++) {
        int idx = i, down_idx = outlet_l->down[i];

        if (!outlet_l->has_up[idx] && down_idx >= 0) {
            do {
                double lflen_new = outlet_l->lflen[idx] + outlet_l->flen[idx];

                if (lflen_new >= outlet_l->lflen[down_idx]) {
                    if (lflen_new > outlet_l->lflen[down_idx]) {
                        reset_point_list(&outlet_l->head_pl[down_idx]);
                        outlet_l->lflen[down_idx] = lflen_new;
                    }
                    for (j = 0; j < outlet_l->head_pl[idx].n; j++)
                        add_point(&outlet_l->head_pl[down_idx],
                                  outlet_l->head_pl[idx].row[j],
                                  outlet_l->head_pl[idx].col[j]);
                }
                /* avoid duplicate tracing */
                outlet_l->down[idx] = -1;
                idx = down_idx;
                down_idx = outlet_l->down[idx];
            } while (down_idx >= 0);
        }
    }
}

static void init_up_stack(struct cell_stack *up_stack)
{
    up_stack->nalloc = up_stack->n = 0;
    up_stack->cells = NULL;
}

static void free_up_stack(struct cell_stack *up_stack)
{
    if (up_stack->cells)
        G_free(up_stack->cells);
    init_up_stack(up_stack);
}

static void push_up(struct cell_stack *up_stack, struct cell *up)
{
    if (up_stack->n == up_stack->nalloc) {
        up_stack->nalloc += REALLOC_INCREMENT;
        up_stack->cells = G_realloc(up_stack->cells,
                                    sizeof *up_stack->cells * up_stack->nalloc);
    }
    up_stack->cells[up_stack->n++] = *up;
}

static void pop_up(struct cell_stack *up_stack, struct cell *up)
{
    if (up_stack->n > 0) {
        *up = up_stack->cells[--up_stack->n];
        if (up_stack->n == 0)
            free_up_stack(up_stack);
        else if (up_stack->n == up_stack->nalloc - REALLOC_INCREMENT) {
            up_stack->nalloc -= REALLOC_INCREMENT;
            up_stack->cells = G_realloc(
                up_stack->cells, sizeof *up_stack->cells * up_stack->nalloc);
        }
    }
}
