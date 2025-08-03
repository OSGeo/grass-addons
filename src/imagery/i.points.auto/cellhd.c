#include "globals.h"
#include "local_proto.h"

int set_target_window(void)
{
    double e, n;

    G_debug(1, "set_target_window()");

    /* NW corner */
    CRS_georef(curr_window.west, curr_window.north, &e, &n, group.E12,
               group.N12, transform_order);

    tgt_window.north = tgt_window.south = n;
    tgt_window.east = tgt_window.west = e;

    /* NE corner */
    CRS_georef(curr_window.east, curr_window.north, &e, &n, group.E12,
               group.N12, transform_order);

    if (tgt_window.north < n)
        tgt_window.north = n;
    if (tgt_window.south > n)
        tgt_window.south = n;
    if (tgt_window.east < e)
        tgt_window.east = e;
    if (tgt_window.west > e)
        tgt_window.west = e;

    /* SE corner */
    CRS_georef(curr_window.east, curr_window.south, &e, &n, group.E12,
               group.N12, transform_order);

    if (tgt_window.north < n)
        tgt_window.north = n;
    if (tgt_window.south > n)
        tgt_window.south = n;
    if (tgt_window.east < e)
        tgt_window.east = e;
    if (tgt_window.west > e)
        tgt_window.west = e;

    /* SW corner */
    CRS_georef(curr_window.west, curr_window.south, &e, &n, group.E12,
               group.N12, transform_order);

    if (tgt_window.north < n)
        tgt_window.north = n;
    if (tgt_window.south > n)
        tgt_window.south = n;
    if (tgt_window.east < e)
        tgt_window.east = e;
    if (tgt_window.west > e)
        tgt_window.west = e;

    tgt_window.ew_res = (tgt_window.east - tgt_window.west) / curr_window.cols;
    tgt_window.ns_res =
        (tgt_window.north - tgt_window.south) / curr_window.rows;
    tgt_window.cols = curr_window.cols;
    tgt_window.rows = curr_window.rows;
    G_adjust_Cell_head(&tgt_window, 0, 0);

    return 1;
}
