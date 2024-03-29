#include <grass/glocale.h>
#include "global.h"

static int nrows, ncols;

static double trace_up(struct cell_map *, struct raster_map *,
                       struct raster_map *, char **, char, int, int);

void accumulate_recursive(struct cell_map *dir_buf,
                          struct raster_map *weight_buf,
                          struct raster_map *accum_buf, char **done, char neg,
                          char zero)
{
    int row, col;

    nrows = dir_buf->nrows;
    ncols = dir_buf->ncols;

    G_message(_("Accumulating flows recursively..."));
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

static double trace_up(struct cell_map *dir_buf, struct raster_map *weight_buf,
                       struct raster_map *accum_buf, char **done, char neg,
                       int row, int col)
{
    int i, j;
    char incomplete = 0;
    double accum;

    /* if the current cell has been calculated, just return its accumulation so
     * that downstream cells can simply propagate and add it to themselves */
    if (done[row][col]) {
        accum = get(accum_buf, row, col);

        /* for negative accumulation, always return its absolute value;
         * otherwise return it as is */
        return neg && accum < 0 ? -accum : accum;
    }

    /* if a weight map is specified (no negative accumulation is implied), use
     * the weight value at the current cell; otherwise use 1 */
    accum = weight_buf->cells.v ? get(weight_buf, row, col) : 1.0;

    /* loop through all neighbor cells and see if any of them drains into the
     * current cell (are there upstream cells?) */
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

            /* if a neighbor cell drains into the current cell and the current
             * cell doesn't flow back into the same neighbor cell (no flow
             * loop), trace and recursively accumulate upstream cells */
            if (dir_buf->c[row + i][col + j] == dir_checks[i + 1][j + 1][0] &&
                dir_buf->c[row][col] != dir_checks[i + 1][j + 1][1]) {
                /* for negative accumulation, trace_up() always returns a
                 * positive value, so accum is always positive (cell count);
                 * otherwise, accum is weighted accumulation */
                accum += trace_up(dir_buf, weight_buf, accum_buf, done, neg,
                                  row + i, col + j);

                /* if the neighbor cell is incomplete, the current cell also
                 * becomes incomplete */
                if (done[row + i][col + j] == 2)
                    incomplete = neg;
            }
        }
    }

    /* if negative accumulation is desired and the current cell is incomplete,
     * use a negative cell count without weighting; otherwise use accumulation
     * as is (cell count or weighted accumulation, which can be negative) */
    set(accum_buf, row, col, incomplete ? -accum : accum);

    /* the current cell is done; 1 for no likely underestimates and 2 for
     * likely underestimates (only when requested) */
    done[row][col] = 1 + incomplete;

    /* for negative accumulation, accum is already positive */
    return accum;
}
