/* File: r_maparea.c
 *
 *  AUTHOR:    E. Jorge Tizado, Spain 2009
 *
 *  COPYRIGHT: (c) 2009 E. Jorge Tizado, and the GRASS Development Team
 *             This program is free software under the GNU General Public
 *             License (>=v2). Read the file COPYING that comes with GRASS
 *             for details.
 */

#include <stdlib.h>
#include <string.h>
#include "lines.h"
#include "colors.h"
#include "ps_info.h"
#include "local_proto.h"

#define KEY(x) (strcmp(key,x)==0)


int read_maparea(void)
{
    char buf[1024];
    char *key, *data;
    double point;

    G_debug(1, "Reading maparea settings ..");

    /* default values */
    default_psline(&(PS.brd));

    /* process options */
    while (input(2, buf)) {
	if (!key_data(buf, &key, &data)) {
	    continue;
	}
	if (KEY("border")) {
	    if (scan_dimen(data, &(point)) != 1) {
		error(key, data, "illegal border width request (maparea)");
	    }
	    PS.brd.width = point;
	    PS.do_border = 1;
	    continue;
	}
	if (KEY("color")) {
	    if (!scan_color(data, &(PS.brd.color))) {
		error(key, data, "illegal border color request (maparea)");
	    }
	    continue;
	}
	if (KEY("fcolor")) {
	    if (!scan_color(data, &(PS.fcolor))) {
		error(key, data, "illegal fcolor request (maparea)");
	    }
	    continue;
	}
	if (KEY("width")) {
	    if (scan_dimen(data, &(point)) != 1) {
		error(key, data, "illegal map width request (maparea)");
	    }
	    PS.map_w = point;
	    continue;
	}
	if (KEY("height")) {
	    if (scan_dimen(data, &(point)) != 1) {
		error(key, data, "illegal map height request (maparea)");
	    }
	    PS.map_h = point;
	    continue;
	}
	if (KEY("top")) {
	    if (scan_dimen(data, &(point)) != 1) {
		error(key, data, "illegal map top request (maparea)");
	    }
	    PS.map_top = point;
	    continue;
	    continue;
	}
	if (KEY("left")) {
	    if (scan_dimen(data, &(point)) != 1) {
		error(key, data, "illegal map left request (maparea)");
	    }
	    PS.map_x = point;
	    continue;
	}
	error(key, data, "illegal maparea sub-request");
    }

    return 0;
}
