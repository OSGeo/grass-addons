#include <grass/raster.h>
#include "globals.h"
#include "local_proto.h"

int overlap(void)
{
    double e, n;

    G_debug(1, "overlap()");

    if (tgt_window.north > cellhd2.north)
        tgt_window.north = cellhd2.north;
    if (tgt_window.south < cellhd2.south)
        tgt_window.south = cellhd2.south;
    if (tgt_window.east > cellhd2.east)
        tgt_window.east = cellhd2.east;
    if (tgt_window.west < cellhd2.west)
        tgt_window.west = cellhd2.west;

    /* NW corner */
    CRS_georef(tgt_window.west, tgt_window.north, &e, &n, group.E21, group.N21,
               transform_order);

    curr_window.north = curr_window.south = n;
    curr_window.east = curr_window.west = e;

    /* NE corner */
    CRS_georef(tgt_window.east, tgt_window.north, &e, &n, group.E21, group.N21,
               transform_order);

    if (curr_window.north < n)
        curr_window.north = n;
    if (curr_window.south > n)
        curr_window.south = n;
    if (curr_window.east < e)
        curr_window.east = e;
    if (curr_window.west > e)
        curr_window.west = e;

    /* SE corner */
    CRS_georef(tgt_window.east, tgt_window.south, &e, &n, group.E21, group.N21,
               transform_order);

    if (curr_window.north < n)
        curr_window.north = n;
    if (curr_window.south > n)
        curr_window.south = n;
    if (curr_window.east < e)
        curr_window.east = e;
    if (curr_window.west > e)
        curr_window.west = e;

    /* SW corner */
    CRS_georef(tgt_window.west, tgt_window.south, &e, &n, group.E21, group.N21,
               transform_order);

    if (curr_window.north < n)
        curr_window.north = n;
    if (curr_window.south > n)
        curr_window.south = n;
    if (curr_window.east < e)
        curr_window.east = e;
    if (curr_window.west > e)
        curr_window.west = e;

    G_adjust_Cell_head(&curr_window, 1, 1);
    tgt_window.ew_res = (tgt_window.east - tgt_window.west) / curr_window.cols;
    tgt_window.ns_res =
        (tgt_window.north - tgt_window.south) / curr_window.rows;
    tgt_window.cols = curr_window.cols;
    tgt_window.rows = curr_window.rows;
    select_env(TGT_ENV);
    G_adjust_Cell_head(&tgt_window, 0, 0);
    select_env(SRC_ENV);

    return 1;
}
