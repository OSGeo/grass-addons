/*
   The following routines are written and tested by Stefano Merler

   for

   open new raster maps
 */

#include <grass/gis.h>
#include <grass/raster.h>
#include <stdlib.h>

int open_new_CELL(name)
/*
   open a new raster map of name name in CELL format
 */
char *name;
{
    int fd;
    char err[400];

    if (G_legal_filename(name) < 0) {
        sprintf(err, "open_new_CELL-> %s - ** illegal name **", name);
        G_fatal_error(err);
        exit(1);
    }

    fd = Rast_open_new(name, CELL_TYPE);
    if (fd < 0) {
        sprintf(err, "open_new_CELL-> failed in attempt to open %s\n", name);
        G_fatal_error(err);
        exit(1);
    }

    return fd;
}

int open_new_DCELL(char *name)

/*
   open a new raster map of name name in DELL format
 */
{
    int fd;
    char err[400];

    if (G_legal_filename(name) < 0) {
        sprintf(err, "open_new_DCELL-> %s - ** illegal name **", name);
        G_fatal_error(err);
        exit(1);
    }

    fd = Rast_open_new(name, DCELL_TYPE);
    if (fd < 0) {
        sprintf(err, "open_new_DCELL-> failed in attempt to open %s\n", name);
        G_fatal_error(err);
        exit(1);
    }

    return fd;
}
