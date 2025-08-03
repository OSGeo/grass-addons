#include "globals.h"

void compute_temp_region(struct Cell_head *temp_region,
                         struct Cell_head *region, double east, double west,
                         double north, double south)
{
    *temp_region = *region;
    temp_region->north = north;
    temp_region->south = south;
    temp_region->east = east;
    temp_region->west = west;
    temp_region->cols =
        (int)(temp_region->east - temp_region->west) / region->ew_res;
    temp_region->rows =
        (int)(temp_region->north - temp_region->south) / region->ns_res;
    temp_region->ns_res = region->ns_res;
    temp_region->ew_res = region->ew_res;
}
