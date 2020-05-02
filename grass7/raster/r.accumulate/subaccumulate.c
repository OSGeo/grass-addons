#include <grass/glocale.h>
#include "global.h"

static void trace_down(struct cell_map *, struct raster_map *, double,
                       struct Cell_head *, int, int);

void subaccumulate(struct Map_info *Map, struct cell_map *dir_buf,
		   struct raster_map *accum_buf, struct point_list *outlet_pl)
{
    struct Cell_head window;
    int rows = accum_buf->rows, cols = accum_buf->cols;
    int i;

    G_get_set_window(&window);

    /* loop through all outlets and calculate subaccumulation for each */
    G_message(_("Subaccumulating flows..."));
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

        /* trace down flow accumulation and calculate subaccumulation */
        trace_down(dir_buf, accum_buf, OUTLET, &window, row, col);
    }
    G_percent(1, 1, 1);
}

static void trace_down(struct cell_map *dir_buf, struct raster_map *accum_buf,
		       double up_accum, struct Cell_head *window,
		       int row, int col)
{
    static int next_cells[8][2] = {
        {-1, 1}, {-1, 0}, {-1, -1}, {0, -1}, {1, -1}, {1, 0}, {1, 1}, {0, 1}
    };
    int rows = dir_buf->rows, cols = dir_buf->cols;
    int dir;

    /* if the current cell is outside the computational region, stop tracing */
    if (row < 0 || row >= rows || col < 0 || col >= cols)
        return;

    if (up_accum == OUTLET)
	/* accumulation at the outlet will need to be subtracted from all
	 * downstream accumulation cells */
	up_accum = get(accum_buf, row, col);
    else
	/* calculate subaccumulation */
	set(accum_buf, row, col, get(accum_buf, row, col) - up_accum);

    /* if the current cell doesn't flow out of the computational region
     * (negative direction from r.watershed flows out), keep tracing */
    dir = dir_buf->c[row][col] - 1;
    if (dir >= 0 && dir < 8)
        trace_down(dir_buf, accum_buf, up_accum, window,
                   row + next_cells[dir][0], col + next_cells[dir][1]);
}
