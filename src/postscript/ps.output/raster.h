#ifndef _RASTER_H_
#define _RASTER_H_

/* Header file: raster.h
 *
 *  AUTHOR:    E. Jorge Tizado, Spain 2009
 *
 *  COPYRIGHT: (c) 2009 E. Jorge Tizado, and the GRASS Development Team
 *             This program is free software under the GNU General Public
 *             License (>=v2). Read the file COPYING that comes with GRASS
 *             for details.
 */

#include "lines.h"
#include "colors.h"
#include <grass/imagery.h>

typedef struct
{
    int files;
    char *title;

    struct Categories cats;
    struct Colors colors[3];
    CELL min, max;		/* to get color table, in gradient */

    int fd[3];
    char *name[3], *mapset[3];

    int do_rgb;
    int do_grey;
    int do_mask;
    PSCOLOR mask_color;

    PSLINE outline;

} RASTER;

#endif
