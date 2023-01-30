#include <grass/raster.h>
#include <grass/glocale.h>
#include "local_proto.h"

int init_search(int depr_fd)
{
    int r, c, r_nbr, c_nbr, ct_dir;
    void *depr_buf, *depr_ptr;
    CELL ele_value;
    int nextdr[8] = {1, -1, 0, 0, -1, 1, 1, -1};
    int nextdc[8] = {0, 0, -1, 1, 1, -1, 1, -1};
    char asp_value, is_null;
    struct dir_flag df, df_nbr;
    GW_LARGE_INT n_depr_cells = 0;
    GW_LARGE_INT n_null_cells = (GW_LARGE_INT)nrows * ncols - n_points;
    int depr_map_type, depr_size;

    nxt_avail_pt = heap_size = 0;

    /* load edge cells and real depressions to A* heap */
    G_message(_("Set edge points"));

    if (depr_fd > -1) {
        depr_map_type = Rast_get_map_type(depr_fd);
        depr_size = Rast_cell_size(depr_map_type);
        depr_buf = Rast_allocate_buf(depr_map_type);
    }
    else {
        depr_buf = NULL;
        depr_map_type = 0;
        depr_size = 0;
    }
    depr_ptr = NULL;

    for (r = 0; r < nrows; r++) {
        G_percent(r, nrows, 2);

        if (depr_fd >= 0) {
            Rast_get_row(depr_fd, depr_buf, r, depr_map_type);
            depr_ptr = depr_buf;
        }

        for (c = 0; c < ncols; c++) {

            seg_get(&dirflag, (char *)&df, r, c);
            is_null = FLAG_GET(df.flag, NULLFLAG);

            if (is_null) {
                if (depr_fd > -1)
                    depr_ptr = G_incr_void_ptr(depr_ptr, depr_size);

                continue;
            }

            asp_value = 0;

            if (r == 0 || r == nrows - 1 || c == 0 || c == ncols - 1) {

                if (r == 0 && c == 0)
                    asp_value = -7;
                else if (r == 0 && c == ncols - 1)
                    asp_value = -5;
                else if (r == nrows - 1 && c == 0)
                    asp_value = -1;
                else if (r == nrows - 1 && c == ncols - 1)
                    asp_value = -3;
                else if (r == 0)
                    asp_value = -2;
                else if (c == 0)
                    asp_value = -4;
                else if (r == nrows - 1)
                    asp_value = -6;
                else if (c == ncols - 1)
                    asp_value = -8;

                cseg_get(&ele, &ele_value, r, c);
                FLAG_SET(df.flag, EDGEFLAG);
                FLAG_SET(df.flag, INLISTFLAG);
                df.dir = asp_value;
                seg_put(&dirflag, (char *)&df, r, c);
                heap_add(r, c, ele_value);

                if (depr_fd > -1)
                    depr_ptr = G_incr_void_ptr(depr_ptr, depr_size);

                continue;
            }

            if (n_null_cells > 0) {
                /* any neighbour NULL ? */
                for (ct_dir = 0; ct_dir < sides; ct_dir++) {
                    /* get r, c (r_nbr, c_nbr) for neighbours */
                    r_nbr = r + nextdr[ct_dir];
                    c_nbr = c + nextdc[ct_dir];

                    seg_get(&dirflag, (char *)&df_nbr, r_nbr, c_nbr);
                    is_null = FLAG_GET(df_nbr.flag, NULLFLAG);

                    if (is_null) {
                        asp_value = -1 * drain[r - r_nbr + 1][c - c_nbr + 1];
                        cseg_get(&ele, &ele_value, r, c);
                        FLAG_SET(df.flag, EDGEFLAG);
                        FLAG_SET(df.flag, INLISTFLAG);
                        df.dir = asp_value;
                        seg_put(&dirflag, (char *)&df, r, c);
                        heap_add(r, c, ele_value);

                        break;
                    }
                }
            }

            if (asp_value) { /* some neighbour was NULL, point added to list */

                if (depr_fd > -1)
                    depr_ptr = G_incr_void_ptr(depr_ptr, depr_size);

                continue;
            }

            /* real depression ? */
            if (depr_fd > -1) {
                DCELL depr_val = Rast_get_d_value(depr_ptr, depr_map_type);

                if (!Rast_is_null_value(depr_ptr, depr_map_type) &&
                    depr_val != 0) {
                    cseg_get(&ele, &ele_value, r, c);
                    FLAG_SET(df.flag, INLISTFLAG);
                    FLAG_SET(df.flag, DEPRFLAG);
                    df.dir = asp_value;
                    seg_put(&dirflag, (char *)&df, r, c);
                    heap_add(r, c, ele_value);
                    n_depr_cells++;
                }
                depr_ptr = G_incr_void_ptr(depr_ptr, depr_size);
            }
        }
    }
    G_percent(nrows, nrows, 2); /* finish it */

    if (depr_fd > -1) {
        G_free(depr_buf);
    }

    G_debug(1, "%lld edge cells", (long long int)(heap_size - n_depr_cells));
    if (n_depr_cells)
        G_debug(1, "%lld cells in depressions", (long long int)n_depr_cells);

    return 1;
}
