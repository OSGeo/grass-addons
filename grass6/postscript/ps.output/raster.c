/* File: raster.c
 *
 *  AUTHOR:    E. Jorge Tizado, Spain 2009
 *
 *  COPYRIGHT: (c) 2009 E. Jorge Tizado, and the GRASS Development Team
 *             This program is free software under the GNU General Public
 *             License (>=v2). Read the file COPYING that comes with GRASS
 *             for details.
 */

#include <string.h>
#include "raster.h"
#include "ps_info.h"
#include "local_proto.h"

int raster_close(void)
{
    int i;

    for (i = 0; i < 3; i++) {
	if (PS.rst.fd[i] >= 0) {
	    G_close_cell(PS.rst.fd[i]);
	    G_free(PS.rst.name[i]);
	    G_free(PS.rst.mapset[i]);
	    G_free_colors(&(PS.rst.colors[i]));
	    PS.rst.fd[i] = -1;
	}
    }

    return 1;
}
