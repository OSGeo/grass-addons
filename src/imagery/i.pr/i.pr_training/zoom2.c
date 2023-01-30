#include "globals.h"

void compute_temp_region2(struct Cell_head *temp_region,
                          struct Cell_head *region, double east, double north,
                          int window_rows, int window_cols)
{
    *temp_region = *region;
    temp_region->north = north + (double)window_rows / 2 * temp_region->ns_res;
    temp_region->south = north - (double)window_rows / 2 * temp_region->ns_res;
    temp_region->east = east + (double)window_cols / 2 * temp_region->ew_res;
    temp_region->west = east - (double)window_cols / 2 * temp_region->ew_res;
    temp_region->rows = window_rows;
    temp_region->cols = window_cols;
}
