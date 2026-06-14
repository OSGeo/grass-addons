/*
   The following routines are written and tested by Stefano Merler

   for

   open new raster maps
 */

#include <grass/gis.h>
#include <grass/raster.h>
#include <stdlib.h>

int open_new_CELL(char *name)
/*
   open a new raster map of name name in CELL format
 */
{
    int fd;

    if (G_legal_filename(name) < 0) {
        G_fatal_error("open_new_CELL-> %s - ** illegal name **", name);
    }

    fd = Rast_open_new(name, CELL_TYPE);
    if (fd < 0) {
        G_fatal_error("open_new_CELL-> failed in attempt to open %s\n", name);
    }

    return fd;
}

int open_new_DCELL(char *name)
/*
   open a new raster map of name name in DELL format
 */
{
    int fd;

    if (G_legal_filename(name) < 0) {
        G_fatal_error("open_new_DCELL-> %s - ** illegal name **", name);
    }

    fd = Rast_open_new(name, DCELL_TYPE);
    if (fd < 0) {
        G_fatal_error("open_new_DCELL-> failed in attempt to open %s\n", name);
    }

    return fd;
}
