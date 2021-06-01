/* File: r_frame.c
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
#include "frames.h"
#include "ps_info.h"
#include "local_proto.h"

#define KEY(x) (strcmp(key,x)==0)


int default_frame(PSFRAME * box, int refx, int refy)
{
    box->x = (refx == RIGHT ? -100. : 0.0);
    box->y = 0.0;
    box->xset = box->yset = 0.;
    box->xref = refx;
    box->yref = refy;
    box->border = 1.;
    set_color_rgb(&(box->color), 0, 0, 0);
    set_color_rgb(&(box->fcolor), 255, 255, 255);
    box->margin = -1.;
    box->rotate = 0.;

    return 0;
}

int read_frame(PSFRAME * box)
{
    char buf[1024];
    char *key, *data;

    G_debug(1, "Reading frame settings ..");

    /* init values */
    default_frame(box, RIGHT, LOWER);


    /* process options */
    while (input(3, buf)) {
	if (!key_data(buf, &key, &data)) {
	    continue;
	}
	if (KEY("where")) {
	    char xx[50], yy[50];

	    if (sscanf(data, "%s %s", xx, yy) != 2) {
		error(key, data, "illegal box where request");
	    }
	    else {
		if (scan_dimen(xx, &(box->x)) == 2)
		    box->x *= -1;
		if (scan_dimen(yy, &(box->y)) == 2)
		    box->y *= -1;
		continue;
	    }
	}
	if (KEY("offset")) {
	    if (sscanf(data, "%lf %lf", &(box->xset), &(box->yset)) != 2) {
		error(key, data, "illegal box offset request");
	    }
	    continue;
	}
	if (KEY("ref")) {
	    if (!scan_ref(data, &(box->xref), &(box->yref))) {
		error(key, data, "illegal box ref request");
	    }
	    continue;
	}
	if (KEY("border")) {
	    if (scan_dimen(data, &(box->border)) != 1) {
		box->border = -1;
	    }
	    continue;
	}
	if (KEY("color")) {
	    if (!scan_color(data, &(box->color))) {
		error(key, data, "illegal box color request");
	    }
	    continue;
	}
	if (KEY("fcolor")) {
	    if (!scan_color(data, &(box->fcolor))) {
		error(key, data, "illegal box fcolor request");
	    }
	    continue;
	}
	if (KEY("margin")) {
	    if (scan_dimen(data, &(box->margin)) != 1) {
		error(key, data, "illegal box margin request");
	    }
	    continue;
	}
	if (KEY("rotate")) {
	    if (scan_dimen(data, &(box->rotate)) != 1) {
		error(key, data, "illegal box rotate request");
	    }
	    continue;
	}
	error(key, data, "illegal box sub-request");
    }

    return 0;
}
