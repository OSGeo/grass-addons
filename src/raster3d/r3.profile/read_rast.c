/*
 * Reading raster and writing output during profiling
 *
 * Authors:
 *   Bob Covill <bcovill tekmap.ns.ca>
 *   Vaclav Petras <wenzeslaus gmail com>
 *
 * Copyright 2000-2016 by Bob Covill, and the GRASS Development Team
 *
 * This program is free software licensed under the GPL (>=v2).
 * Read the COPYING file that comes with GRASS for details.
 *
 */

#include <grass/gis.h>
#include <grass/raster.h>
#include <grass/glocale.h>
#include "local_proto.h"
#include "double_list.h"
int read_rast(double east, double north, double dist, RASTER3D_Map *fd,
              int coords, RASTER_MAP_TYPE data_type, FILE *fp,
              char *null_string, RASTER3D_Region *region, int depth,
              struct DoubleList *values)
{
    static DCELL *dcell;
    static CELL nullcell;
    static int nrows, ncols;
    static struct Cell_head window;
    int row, col;
    int outofbounds = FALSE;

    if (!dcell) {
        Rast_set_c_null_value(&nullcell, 1);
        dcell = Rast_allocate_d_buf();
        G_get_window(&window);
        nrows = window.rows;
        ncols = window.cols;
    }

    int unused;

    Rast3d_location2coord(region, north, east, 0, &col, &row, &unused);
    G_debug(4, "row=%d:%d  col=%d:%d", row, nrows, col, ncols);

    /* TODO: use 3D region */
    if ((row < 0) || (row >= nrows) || (col < 0) || (col >= ncols))
        outofbounds = TRUE;

    double val;

    if (!outofbounds) {
        Rast3d_get_value(fd, col, row, depth, &val, DCELL_TYPE);
    }

    if (values)
        double_list_add_item(values, val);

    /* TODO: handle textual outputs systematically */
    /* TODO: enable colors */
    /* TODO: enable xyz coordinates output */
    /*
       if (coords)
       fprintf(fp, "%f %f", east, north);
     */

    if (coords)
        fprintf(fp, "%f %d", dist, depth);

    /*fprintf(fp, " %f", dist); */

    if (outofbounds || Rast_is_d_null_value(&val))
        fprintf(fp, " %s", null_string);
    else {
        if (data_type == CELL_TYPE)
            fprintf(fp, " %d", (int)val);
        else
            fprintf(fp, " %f", val);
    }

    fprintf(fp, "\n");

    return 0;
}
