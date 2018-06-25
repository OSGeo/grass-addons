#include <grass/gis.h>
#include <grass/vector.h>
#include "global.h"

static void trace_down(struct cell_map *, struct Cell_head *, int, int,
                       struct point_list *);

void delineate_streams(struct Map_info *Map, double thresh,
                       struct cell_map *dir_buf, struct raster_map *accum_buf)
{
    struct Cell_head window;
    int rows = accum_buf->rows, cols = accum_buf->cols;
    int row, col;
    int i, j;
    char has_thresh_inflow;
    struct point_list pl;
    struct line_pnts *Points;
    struct line_cats *Cats;
    int stream_id = 0;

    G_get_set_window(&window);

    init_point_list(&pl);
    Points = Vect_new_line_struct();
    Cats = Vect_new_cats_struct();

    /* loop through all cells to find headwater cells */
    for (row = 0; row < rows; row++) {
        for (col = 0; col < cols; col++) {
            /* if the current cell is less than the threshold, skip */
            if (get(accum_buf, row, col) < thresh)
                continue;

            /* the current cell is greater than the threshold; check if it is
             * headwater (no upstream cells greater than the threshold) */
            has_thresh_inflow = 0;

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
                     * headwater */
                    if (dir_buf->c[row + i][col + j] ==
                        dir_checks[i + 1][j + 1][0] &&
                        get(accum_buf, row + i, col + j) >= thresh)
                        has_thresh_inflow = 1;
                }
            }

            /* if headwater is found, trace down flow directions */
            if (!has_thresh_inflow) {
                reset_point_list(&pl);
                trace_down(dir_buf, &window, row, col, &pl);

                /* if tracing is successful, write out the stream */
                if (pl.n > 0) {
                    Vect_reset_line(Points);
                    Vect_reset_cats(Cats);

                    Vect_copy_xyz_to_pnts(Points, pl.x, pl.y, NULL, pl.n);
                    Vect_cat_set(Cats, 1, ++stream_id);
                    Vect_write_line(Map, GV_LINE, Points, Cats);
                }
            }
        }
    }

    free_point_list(&pl);
    Vect_destroy_line_struct(Points);
    Vect_destroy_cats_struct(Cats);
}

static void trace_down(struct cell_map *dir_buf, struct Cell_head *window,
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

    /* if the current cell doesn't flow out of the computational region
     * (negative direction from r.watershed flows out), keep tracing */
    dir = dir_buf->c[row][col] - 1;
    if (dir >= 0 && dir < 8)
        trace_down(dir_buf, window, row + next_cells[dir][0],
                   col + next_cells[dir][1], pl);
}
