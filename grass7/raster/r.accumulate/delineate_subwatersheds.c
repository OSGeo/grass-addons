#include <grass/gis.h>
#include <grass/glocale.h>
#include "global.h"

static struct Cell_head window;
static int rows, cols;

static void trace_up(struct cell_map *, struct raster_map *, char **, int,
                     int, int);

void delineate_subwatersheds(struct Map_info *Map, struct cell_map *dir_buf,
                             struct raster_map *accum_buf, char **done,
                             int *id, struct point_list *outlet_pl)
{
    int i, j;
    int subwshed_id;

    G_get_set_window(&window);

    rows = accum_buf->rows;
    cols = accum_buf->cols;

    G_message(_("Flagging outlets..."));
    for (i = 0; i < outlet_pl->n; i++) {
        int row = (int)Rast_northing_to_row(outlet_pl->y[i], &window);
        int col = (int)Rast_easting_to_col(outlet_pl->x[i], &window);

        G_percent(i, outlet_pl->n, 1);

        /* if the outlet is outside the computational region, skip */
        if (row < 0 || row >= rows || col < 0 || col >= cols) {
            G_warning(_("Skip outlet (%f, %f) outside the current region"),
                      outlet_pl->x[i], outlet_pl->y[i]);
            continue;
        }

        done[row][col] = 1;
    }
    G_percent(1, 1, 1);

    /* loop through all outlets and delineate the subwatershed for each */
    subwshed_id = 0;
    G_message(_("Delineating subwatersheds..."));
    for (i = 0; i < outlet_pl->n; i++) {
        int row = (int)Rast_northing_to_row(outlet_pl->y[i], &window);
        int col = (int)Rast_easting_to_col(outlet_pl->x[i], &window);

        G_percent(i, outlet_pl->n, 1);

        /* if the outlet is outside the computational region, skip */
        if (row < 0 || row >= rows || col < 0 || col >= cols) {
            G_warning(_("Skip outlet (%f, %f) outside the current region"),
                      outlet_pl->x[i], outlet_pl->y[i]);
            continue;
        }

        subwshed_id = id ? id[i] : subwshed_id + 1;

        /* unflag the current outlet for now */
        done[row][col] = 0;

        /* trace up flow directions */
        trace_up(dir_buf, accum_buf, done, row, col, subwshed_id);

        /* flag the current outlet again */
        done[row][col] = 1;
    }
    G_percent(1, 1, 1);

    G_message(_("Nullifying cells outside subwatersheds..."));
    for (i = 0; i < rows; i++) {
        G_percent(i, rows, 1);
        for (j = 0; j < cols; j++)
            if (!done[i][j])
                Rast_set_c_null_value(&dir_buf->c[i][j], 1);
    }
    G_percent(1, 1, 1);
}

static void trace_up(struct cell_map *dir_buf, struct raster_map *accum_buf,
                     char **done, int row, int col, int id)
{
    double cur_acc;
    int i, j;

    /* if the current cell is outside the computational region or already
     * processed, stop tracing */
    if (row < 0 || row >= rows || col < 0 || col >= cols || done[row][col])
        return;

    /* if the current accumulation is 1 (headwater), stop tracing */
    cur_acc = get(accum_buf, row, col);
    if (cur_acc == 1) {
        dir_buf->c[row][col] = id;
        done[row][col] = 1;
        return;
    }

    for (i = -1; i <= 1; i++) {
        /* skip edge cells */
        if (row + i < 0 || row + i >= rows)
            continue;

        for (j = -1; j <= 1; j++) {
            /* skip the current and edge cells */
            if ((i == 0 && j == 0) || col + j < 0 || col + j >= cols)
                continue;

            /* if a neighbor cell flows into the current cell, store its
             * accumulation in the accum array; upstream accumulation must
             * always be less than the current accumulation; upstream
             * accumulation can be greater than the current accumulation in a
             * subaccumulation raster */
            if (dir_buf->c[row + i][col + j] == dir_checks[i + 1][j + 1][0] &&
                get(accum_buf, row + i, col + j) < cur_acc) {
                dir_buf->c[row][col] = id;
                done[row][col] = 1;
                trace_up(dir_buf, accum_buf, done, row + i, col + j, id);
            }
        }
    }
}
