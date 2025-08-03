#include <grass/gis.h>
#include <grass/raster.h>
#include <grass/glocale.h>
#include "local_proto.h"

int close_map(char *ele_rast, int ele_map_type)
{
    int ele_fd, r, c;
    void *ele_buf, *ele_ptr;
    struct History history;
    size_t ele_size;
    CELL ele_val;

    G_message(_("Write conditioned DEM"));

    ele_fd = Rast_open_new(ele_rast, ele_map_type);
    ele_size = Rast_cell_size(ele_map_type);
    ele_buf = Rast_allocate_buf(ele_map_type);

    for (r = 0; r < nrows; r++) {
        G_percent(r, nrows, 2);

        Rast_set_null_value(ele_buf, ncols,
                            ele_map_type); /* reset row to all NULL */

        ele_ptr = ele_buf;

        for (c = 0; c < ncols; c++) {
            cseg_get(&ele, &ele_val, r, c);

            if (!Rast_is_c_null_value(&ele_val)) {

                switch (ele_map_type) {
                case CELL_TYPE:
                    *((CELL *)ele_ptr) = ele_val;
                    break;
                case FCELL_TYPE:
                    *((FCELL *)ele_ptr) = (FCELL)ele_val / ele_scale;
                    break;
                case DCELL_TYPE:
                    *((DCELL *)ele_ptr) = (DCELL)ele_val / ele_scale;
                    break;
                }
            }
            ele_ptr = G_incr_void_ptr(ele_ptr, ele_size);
        }
        Rast_put_row(ele_fd, ele_buf, ele_map_type);
    }
    G_percent(nrows, nrows, 2); /* finish it */

    Rast_close(ele_fd);
    G_free(ele_buf);
    Rast_short_history(ele_rast, "raster", &history);
    Rast_command_history(&history);
    Rast_write_history(ele_rast, &history);

    return 1;
}
