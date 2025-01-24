#include "global.h"

void delineate(struct raster_map *dir_map, struct outlet_list *outlet_l,
               int use_lessmem)
{
    if (use_lessmem)
        delineate_lessmem(dir_map, outlet_l);
    else
        delineate_moremem(dir_map, outlet_l);
}
