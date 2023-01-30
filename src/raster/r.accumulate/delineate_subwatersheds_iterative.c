#include <grass/gis.h>
#include <grass/glocale.h>
#include "global.h"

struct neighbor {
    int row;
    int col;
};

struct neighbor_stack {
    struct neighbor *up;
    int n;
    int nalloc;
};

static int nrows, ncols;

static void trace_up(struct cell_map *, char **, int, int, int);
static void find_up(struct cell_map *, char **, int, int, int,
                    struct neighbor *, int *);
static void init_up_stack(struct neighbor_stack *);
static void free_up_stack(struct neighbor_stack *);
static void push_up(struct neighbor_stack *, struct neighbor *);
static struct neighbor pop_up(struct neighbor_stack *);

void delineate_subwatersheds_iterative(struct cell_map *dir_buf, char **done,
                                       int *id, struct point_list *outlet_pl)
{
    struct Cell_head window;
    int i, j;
    int subwshed_id;

    G_get_set_window(&window);

    nrows = dir_buf->nrows;
    ncols = dir_buf->ncols;

    G_message(_("Flagging outlets..."));
    for (i = 0; i < outlet_pl->n; i++) {
        int row = (int)Rast_northing_to_row(outlet_pl->y[i], &window);
        int col = (int)Rast_easting_to_col(outlet_pl->x[i], &window);

        G_percent(i, outlet_pl->n, 1);

        /* if the outlet is outside the computational region, skip */
        if (row < 0 || row >= nrows || col < 0 || col >= ncols) {
            G_warning(_("Skip outlet (%f, %f) outside the current region"),
                      outlet_pl->x[i], outlet_pl->y[i]);
            continue;
        }

        done[row][col] = 1;
    }
    G_percent(1, 1, 1);

    /* loop through all outlets and delineate the subwatershed for each */
    subwshed_id = 0;
    G_message(_("Delineating subwatersheds iteratively..."));
    for (i = 0; i < outlet_pl->n; i++) {
        int row = (int)Rast_northing_to_row(outlet_pl->y[i], &window);
        int col = (int)Rast_easting_to_col(outlet_pl->x[i], &window);

        G_percent(i, outlet_pl->n, 1);

        /* if the outlet is outside the computational region, skip */
        if (row < 0 || row >= nrows || col < 0 || col >= ncols) {
            G_warning(_("Skip outlet (%f, %f) outside the current region"),
                      outlet_pl->x[i], outlet_pl->y[i]);
            continue;
        }

        subwshed_id = id ? id[i] : subwshed_id + 1;

        /* trace up flow directions */
        trace_up(dir_buf, done, row, col, subwshed_id);
    }
    G_percent(1, 1, 1);

    G_message(_("Nullifying cells outside subwatersheds..."));
    for (i = 0; i < nrows; i++) {
        G_percent(i, nrows, 1);
        for (j = 0; j < ncols; j++)
            if (!done[i][j])
                Rast_set_c_null_value(&dir_buf->c[i][j], 1);
    }
    G_percent(1, 1, 1);
}

static void trace_up(struct cell_map *dir_buf, char **done, int row, int col,
                     int id)
{
    int nup, i;
    struct neighbor up[8];
    struct neighbor_stack up_stack;

    /* if the current cell is outside the computational region, stop tracing */
    if (row < 0 || row >= nrows || col < 0 || col >= ncols)
        return;

    find_up(dir_buf, done, row, col, id, up, &nup);

    /* if no upstream neighbors are found, stop tracing */
    if (!nup)
        return;

    init_up_stack(&up_stack);

    /* push upstream cells */
    for (i = nup - 1; i >= 0; i--)
        push_up(&up_stack, &up[i]);

    do {
        /* pop one upstream cell */
        struct neighbor cur_up = pop_up(&up_stack);

        /* find its upstream cells */
        find_up(dir_buf, done, cur_up.row, cur_up.col, id, up, &nup);

        /* push its upstream cells */
        for (i = nup - 1; i >= 0; i--)
            push_up(&up_stack, &up[i]);
    } while (up_stack.n);

    free_up_stack(&up_stack);
}

static void find_up(struct cell_map *dir_buf, char **done, int row, int col,
                    int id, struct neighbor *up, int *nup)
{
    int i, j;

    dir_buf->c[row][col] = id;
    done[row][col] = 1;

    *nup = 0;
    for (i = -1; i <= 1; i++) {
        /* skip edge cells */
        if (row + i < 0 || row + i >= nrows)
            continue;

        for (j = -1; j <= 1; j++) {
            /* skip the current and edge cells */
            if ((i == 0 && j == 0) || col + j < 0 || col + j >= ncols)
                continue;

            /* if a neighbor cell flows into the current cell, store its row
             * and col in the up array; no check for flow loop is needed
             * because dir_buf is being overwritten */
            if (dir_buf->c[row + i][col + j] == dir_checks[i + 1][j + 1][0] &&
                !done[row + i][col + j]) {
                up[*nup].row = row + i;
                up[*nup].col = col + j;
                (*nup)++;
            }
        }
    }
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
