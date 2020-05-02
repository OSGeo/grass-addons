#include <grass/gis.h>
#include <grass/vector.h>
#include <grass/glocale.h>
#include "global.h"

static void trace_down(struct cell_map *, struct raster_map *, double, char,
		       struct Cell_head *, int, int, struct point_list *);

void delineate_streams(struct Map_info *Map, struct cell_map *dir_buf,
                       struct raster_map *accum_buf, double thresh, char conf)
{
    struct Cell_head window;
    int rows = accum_buf->rows, cols = accum_buf->cols;
    int row, col;
    struct point_list pl;
    struct line_pnts *Points;
    struct line_cats *Cats;
    int stream_cat = 0;

    G_get_set_window(&window);

    init_point_list(&pl);

    Points = Vect_new_line_struct();
    Cats = Vect_new_cats_struct();

    /* loop through all cells to find headwater cells */
    G_message(_("Delineating streams..."));
    for (row = 0; row < rows; row++) {
        G_percent(row, rows, 1);
        for (col = 0; col < cols; col++) {
            int i, j;
            int nup = 0;

            /* if the current cell is less than the threshold, skip */
            if (get(accum_buf, row, col) < thresh)
                continue;

            /* the current cell is greater than the threshold; check if it is
             * a headwater (no upstream cells greater than the threshold) */
            for (i = -1; i <= 1; i++) {
                /* skip edge cells */
                if (row + i < 0 || row + i >= rows)
                    continue;

                for (j = -1; j <= 1; j++) {
                    /* skip the current and edge cells */
                    if ((i == 0 && j == 0) || col + j < 0 || col + j >= cols)
                        continue;

                    /* if a neighbor cell flows into the current cell and has a
                     * flow higher than the threshold, the current cell is not
                     * a headwater */
                    if (dir_buf->c[row + i][col + j] ==
                        dir_checks[i + 1][j + 1][0] &&
                        get(accum_buf, row + i, col + j) >= thresh)
                        nup++;
                }
            }

            /* if a headwater is found or a confluence is found and requested,
             * trace down flow directions */
            if (!nup || (!conf && nup > 1)) {
                reset_point_list(&pl);
                trace_down(dir_buf, accum_buf, thresh, conf, &window, row,
                           col, &pl);

                /* if tracing is successful, write out the stream */
                if (pl.n > 0) {
                    Vect_reset_line(Points);
                    Vect_reset_cats(Cats);

                    Vect_copy_xyz_to_pnts(Points, pl.x, pl.y, NULL, pl.n);
                    Vect_cat_set(Cats, 1, ++stream_cat);
                    Vect_write_line(Map, GV_LINE, Points, Cats);
                }
            }
        }
    }
    G_percent(1, 1, 1);

    free_point_list(&pl);

    Vect_destroy_line_struct(Points);
    Vect_destroy_cats_struct(Cats);
}

static void trace_down(struct cell_map *dir_buf, struct raster_map *accum_buf,
                       double thresh, char conf, struct Cell_head *window,
                       int row, int col, struct point_list *pl)
{
    static int next_cells[8][2] = {
        {-1, 1}, {-1, 0}, {-1, -1}, {0, -1}, {1, -1}, {1, 0}, {1, 1}, {0, 1}
    };
    int rows = dir_buf->rows, cols = dir_buf->cols;
    int dir;

    /* if the current cell is outside the computational region, stop tracing */
    if (row < 0 || row >= rows || col < 0 || col >= cols)
        return;

    /* add the current cell */
    add_point(pl, Rast_col_to_easting(col + 0.5, window),
              Rast_row_to_northing(row + 0.5, window));

    /* conf = 1 for continuous streams across a confluence;
     * conf = 0 for split streams at a confluence */
    if (!conf) {
        int nup = 0;
	int i, j;

        for (i = -1; i <= 1; i++) {
            /* skip edge cells */
            if (row + i < 0 || row + i >= rows)
                continue;

            for (j = -1; j <= 1; j++) {
                /* skip the current and edge cells */
                if ((i == 0 && j == 0) || col + j < 0 || col + j >= cols)
                    continue;

                /* if multiple neighbor cells flow into the current cell and
                 * have a flow higher than the threshold, the current cell is a
                 * confluence; stop tracing in this case only if this cell is
                 * not starting a new stream at this confluence */
                if (dir_buf->c[row + i][col + j] ==
                    dir_checks[i + 1][j + 1][0] &&
                    get(accum_buf, row + i, col + j) >= thresh && pl->n > 1 &&
                    ++nup > 1)
                    return;
            }
        }
    }

    /* if the current cell doesn't flow out of the computational region
     * (negative direction from r.watershed flows out), keep tracing */
    dir = dir_buf->c[row][col] - 1;
    if (dir >= 0 && dir < 8)
        trace_down(dir_buf, accum_buf, thresh, conf, window,
                   row + next_cells[dir][0], col + next_cells[dir][1], pl);
}
