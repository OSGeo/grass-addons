#include <grass/glocale.h>
#include "global.h"

struct neighbor {
    int row;
    int col;
    char done;
    char parent;
};

struct neighbor_stack {
    struct neighbor *up;
    int n;
    int nalloc;
};

static int nrows, ncols;

static void trace_up(struct cell_map *, struct raster_map *,
                     struct raster_map *, char **, char, int, int);
static void find_up(struct cell_map *, struct raster_map *, struct raster_map *,
                    char **, char, int, int, struct neighbor *, int *);
static char is_incomplete(struct cell_map *, int, int);
static void init_up_stack(struct neighbor_stack *);
static void free_up_stack(struct neighbor_stack *);
static void push_up(struct neighbor_stack *, struct neighbor *);
static struct neighbor pop_up(struct neighbor_stack *);
static struct neighbor *get_up(struct neighbor_stack *, int);

void accumulate_iterative(struct cell_map *dir_buf,
                          struct raster_map *weight_buf,
                          struct raster_map *accum_buf, char **done, char neg,
                          char zero)
{
    int row, col;

    nrows = dir_buf->nrows;
    ncols = dir_buf->ncols;

    G_message(_("Accumulating flows iteratively..."));
#pragma omp parallel for schedule(dynamic) private(col)
    for (row = 0; row < nrows; row++) {
        G_percent(row, nrows, 1);
        for (col = 0; col < ncols; col++)
            if (dir_buf->c[row][col])
                trace_up(dir_buf, weight_buf, accum_buf, done, neg, row, col);
            else if (!zero)
                set_null(accum_buf, row, col);
    }
    G_percent(1, 1, 1);
}

static void trace_up(struct cell_map *dir_buf, struct raster_map *weight_buf,
                     struct raster_map *accum_buf, char **done, char neg,
                     int row, int col)
{
    int i, nup;
    struct neighbor cur, up[8];
    struct neighbor_stack up_stack;

    /* if the current cell is outside the computational region or already
     * processed, stop tracing */
    if (row < 0 || row >= nrows || col < 0 || col >= ncols || done[row][col])
        return;

    find_up(dir_buf, weight_buf, accum_buf, done, neg, row, col, up, &nup);

    /* if no upstream neighbors are found, stop tracing */
    if (!nup)
        return;

    init_up_stack(&up_stack);

    cur.row = row;
    cur.col = col;
    cur.done = cur.parent = 0;
    push_up(&up_stack, &cur);

    /* push upstream cells */
#pragma omp parallel for schedule(dynamic) private(i)
    for (i = 0; i < nup; i++)
        push_up(&up_stack, &up[i]);

    do {
        /* pop one upstream cell */
        struct neighbor *cur_up = get_up(&up_stack, 0);

        /* only if the current cell is not processed */
        if (!cur_up->done) {
            /* find its upstream cells */
            find_up(dir_buf, weight_buf, accum_buf, done, neg, cur_up->row,
                    cur_up->col, up, &nup);

            /* if there are upstream cells */
            if (nup) {
                /* push them */
                for (i = 0; i < nup; i++)
                    push_up(&up_stack, &up[i]);
                /* move to the next cell in the stack without tracing down */
                continue;
            }
        }

        /* trace down */
        if (cur_up->parent) {
            char incomplete = cur_up->done == 2;
            char last_child = cur_up->parent == 1;
            double accum = get(accum_buf, cur_up->row, cur_up->col);

            /* for negative accumulation */
            if (neg) {
                /* always return its absolute value */
                if (accum < 0)
                    accum = -accum;

                /* set the incomplete flag if the cell is on edges */
                if (!incomplete)
                    incomplete =
                        is_incomplete(dir_buf, cur_up->row, cur_up->col);
            }

            /* retrieve the parent cell */
            cur_up = get_up(&up_stack, cur_up->parent);

            /* set the incomplete flag if negative accumulation is requested
             * and the cell is on edges */
            if (neg && !incomplete)
                incomplete = cur_up->done == 2 ||
                             is_incomplete(dir_buf, cur_up->row, cur_up->col);

            if (cur_up->done) {
                double a = get(accum_buf, cur_up->row, cur_up->col);

                accum += neg && a < 0 ? -a : a;
            }
            else
                /* if a weight map is specified (no negative accumulation is
                 * implied), use the weight value at the current cell;
                 * otherwise use 1 */
                accum += weight_buf->cells.v
                             ? get(weight_buf, cur_up->row, cur_up->col)
                             : 1.0;

            /* if negative accumulation is desired and the current cell is
             * incomplete, use a negative cell count without weighting;
             * otherwise use accumulation as is (cell count or weighted
             * accumulation, which can be negative) */
            set(accum_buf, cur_up->row, cur_up->col,
                incomplete ? -accum : accum);

            /* the current cell is done; 1 for no likely underestimates and 2
             * for likely underestimates */
            if (cur_up->done != 2)
                cur_up->done = 1 + incomplete;

            if (last_child)
                done[cur_up->row][cur_up->col] = cur_up->done;
        }

        /* discard the top cell from the stack */
        pop_up(&up_stack);
    } while (up_stack.n);

    free_up_stack(&up_stack);
}

static void find_up(struct cell_map *dir_buf, struct raster_map *weight_buf,
                    struct raster_map *accum_buf, char **done, char neg,
                    int row, int col, struct neighbor *up, int *nup)
{
    int i, j;
    char incomplete = 0;

    *nup = 0;
    for (i = -1; i <= 1; i++) {
        /* if a neighbor cell is outside the computational region, its
         * downstream accumulation is incomplete */
        if (row + i < 0 || row + i >= nrows) {
            incomplete = neg;
            continue;
        }

        for (j = -1; j <= 1; j++) {
            /* skip the current cell */
            if (i == 0 && j == 0)
                continue;

            /* if a neighbor cell is outside the computational region or null,
             * its downstream accumulation is incomplete */
            if (col + j < 0 || col + j >= ncols ||
                !dir_buf->c[row + i][col + j]) {
                incomplete = neg;
                continue;
            }

            /* if a neighbor cell flows into the current cell with no flow
             * loop, store its row and col in the up array */
            if (dir_buf->c[row + i][col + j] == dir_checks[i + 1][j + 1][0] &&
                dir_buf->c[row][col] != dir_checks[i + 1][j + 1][1]) {
                up[*nup].row = row + i;
                up[*nup].col = col + j;
                up[*nup].done = done[row + i][col + j];
                /* XXX: tempted to merge these two lines into
                 * up[*nup].parent = ++(*nup);
                 * ? don't because its behavior is undefined (-Wsequence-point
                 * GCC(1)); you don't want to have on both sides of an
                 * assignment the same variable that pre-/post-increments */
                up[*nup].parent = *nup + 1;
                (*nup)++;
            }
        }
    }

    /* if no upstream cells are found */
    if (!*nup) {
        /* if a weight map is specified (no negative accumulation is implied),
         * use the weight value at the current cell; otherwise use 1 */
        double accum = weight_buf->cells.v ? get(weight_buf, row, col) : 1.0;

        /* if negative accumulation is desired and the current cell is
         * incomplete, use a negative cell count without weighting; otherwise
         * use accumulation as is (cell count or weighted accumulation, which
         * can be negative) */
        set(accum_buf, row, col, incomplete ? -accum : accum);

        /* the current cell is done; 1 for no likely underestimates and 2 for
         * likely underestimates (only when requested) */
        done[row][col] = 1 + incomplete;
    }
}

static char is_incomplete(struct cell_map *dir_buf, int row, int col)
{
    char incomplete = 0;

    if (row == 0 || row == nrows - 1 || col == 0 || col == ncols - 1)
        incomplete = 1;
    else {
        int i, j;
        for (i = -1; i <= 1 && !incomplete; i++) {
            if (row + i < 0 || row + i >= nrows)
                continue;
            for (j = -1; j <= 1 && !incomplete; j++) {
                if ((i == 0 && j == 0) || col + j < 0 || col + j >= ncols)
                    continue;
                if (!dir_buf->c[row + i][col + j])
                    incomplete = 1;
            }
        }
    }

    return incomplete;
}

static void init_up_stack(struct neighbor_stack *up_stack)
{
    up_stack->nalloc = up_stack->n = 0;
    up_stack->up = NULL;
}

static void free_up_stack(struct neighbor_stack *up_stack)
{
    if (up_stack->up)
        G_free(up_stack->up);
    init_up_stack(up_stack);
}

static void push_up(struct neighbor_stack *up_stack, struct neighbor *up)
{
    if (up_stack->n == up_stack->nalloc) {
        up_stack->nalloc += REALLOC_INCREMENT;
        up_stack->up = (struct neighbor *)G_realloc(
            up_stack->up, up_stack->nalloc * sizeof(struct neighbor));
    }
    up_stack->up[up_stack->n++] = *up;
}

static struct neighbor pop_up(struct neighbor_stack *up_stack)
{
    struct neighbor up;

    if (up_stack->n > 0) {
        up = up_stack->up[--up_stack->n];
        if (up_stack->n == up_stack->nalloc - REALLOC_INCREMENT) {
            up_stack->nalloc -= REALLOC_INCREMENT;
            up_stack->up = (struct neighbor *)G_realloc(
                up_stack->up, up_stack->nalloc * sizeof(struct neighbor));
        }
    }

    return up;
}

static struct neighbor *get_up(struct neighbor_stack *up_stack, int back)
{
    struct neighbor *up = NULL;

    if (up_stack->n > back)
        up = &up_stack->up[up_stack->n - 1 - back];

    return up;
}
