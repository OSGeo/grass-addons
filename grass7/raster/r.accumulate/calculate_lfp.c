#include <grass/gis.h>
#include <grass/vector.h>
#include "global.h"

void calculate_lfp(struct Map_info *Map, struct cell_map *dir_buf,
                   struct raster_map *accum_buf, int *id, char *idcol,
                   struct point_list *outlet_pl, char recur)
{
    if (recur)
        calculate_lfp_recursive(Map, dir_buf, accum_buf, id, idcol,
                                outlet_pl);
    else
        calculate_lfp_iterative(Map, dir_buf, accum_buf, id, idcol,
                                outlet_pl);
}
