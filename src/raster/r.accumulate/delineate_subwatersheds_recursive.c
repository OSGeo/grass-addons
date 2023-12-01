#include <grass/gis.h>
#include <grass/glocale.h>
#include "global.h"

static int nrows, ncols;

static void trace_up(struct cell_map *, char **, int, int, int);

void delineate_subwatersheds_recursive(struct cell_map *dir_buf, char **done,
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
    G_message(_("Delineating subwatersheds recursively..."));
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

        /* unflag the current outlet for now */
        done[row][col] = 0;

        /* trace up flow directions */
        trace_up(dir_buf, done, row, col, subwshed_id);

        /* flag the current outlet again */
        done[row][col] = 1;
    }
    G_percent(1, 1, 1);

    G_message(_("Nullifying cells outside subwatersheds..."));
#pragma omp parallel for schedule(dynamic) private(col)
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
    int i, j;

    /* if the current cell is outside the computational region or already
     * processed, stop tracing */
    if (row < 0 || row >= nrows || col < 0 || col >= ncols || done[row][col])
        return;

    dir_buf->c[row][col] = id;
    done[row][col] = 1;

    for (i = -1; i <= 1; i++) {
        /* skip edge cells */
        if (row + i < 0 || row + i >= nrows)
            continue;

        for (j = -1; j <= 1; j++) {
            /* skip the current and edge cells */
            if ((i == 0 && j == 0) || col + j < 0 || col + j >= ncols)
                continue;

            /* if a neighbor cell flows into the current cell, add it to the
             * map and trace up further; no check for flow loop is needed
             * because dir_buf is being overwritten */
            if (dir_buf->c[row + i][col + j] == dir_checks[i + 1][j + 1][0] &&
                !done[row + i][col + j])
                trace_up(dir_buf, done, row + i, col + j, id);
        }
    }
}
