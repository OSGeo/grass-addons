/* File: r_rlegend.c
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
#include "ps_info.h"
#include "local_proto.h"
#include "raster.h"
#include "rlegend.h"

#define KEY(x) (strcmp(key,x)==0)

int read_rlegend(char *arg)
{
    char buf[1024];
    char *key, *data, *mapset;
    double dimen;

    G_debug(1, "Reading rlegend settings ..");

    /* default values */
    PS.rl.name[0] = 0;
    PS.rl.height = 0.;
    PS.rl.do_gradient = FALSE;
    PS.rl.do_nodata = FALSE;
    PS.rl.tickbar = 3;
    PS.rl.whiteframe = 1;
    PS.rl.custom_range = FALSE;
    PS.rl.cat_order[0] = 0;
    default_font(&(PS.rl.legend.font));
    default_frame(&(PS.rl.legend.box), LEFT, LOWER);
    PS.rl.legend.width = -1.0;
    PS.rl.legend.cols = 1;
    PS.rl.legend.xspan = 4.;
    default_font(&(PS.rl.legend.title_font));

    G_strip(arg);
    strncpy(PS.rl.legend.title, arg, TITLE_LEN);

    /* process options */
    while (input(2, buf)) {
	if (!key_data(buf, &key, &data)) {
	    continue;
	}
	if (KEY("title")) {
	    G_strip(data);
	    read_font(data, &(PS.rl.legend.title_font));
	    continue;
	}
	if (KEY("font")) {
	    G_strip(data);
	    read_font(data, &(PS.rl.legend.font));
	    continue;
	}
	if (KEY("frame")) {
	    read_frame(&(PS.rl.legend.box));
	    continue;
	}
	if (KEY("swidth")) {
	    if (scan_dimen(data, &(PS.rl.legend.width)) != 1) {
		PS.rl.legend.width = -1.;
		error(key, data, "illegal width request (rlegend)");
	    }
	    continue;
	}
	if (KEY("cols")) {
	    int n;

	    n = sscanf(data, "%d %lf", &(PS.rl.legend.cols),
		       &(PS.rl.legend.xspan));
	    if (n == 1 || n == 2) {
		if (PS.rl.legend.cols < 0)
		    PS.rl.legend.cols = 1;
		if (n == 1)
		    PS.rl.legend.xspan = -1.;
	    }
	    else
		error(key, data, "illegal cols/span request (rlegend)");
	    continue;
	}
	if (KEY("height")) {
	    if (scan_dimen(data, &(PS.rl.height)) != 1) {
		error(key, data, "illegal height request (rlegend)");
	    }
	    continue;
	}
	if (KEY("raster")) {
	    G_strip(data);
	    mapset = G_find_file("cell", data, "");
	    if (PS.rl.mapset == NULL) {
		PS.rl.name[0] = 0;
		error(key, data, "illegal raster request (rlegend)");
	    }
	    strcpy(PS.rl.name, data);
	    strcpy(PS.rl.mapset, mapset);
	    continue;
	}
	if (KEY("range")) {
	    if (sscanf(data, "%lf %lf", &(PS.rl.min), &(PS.rl.max)) != 2) {
		PS.rl.custom_range = FALSE;
		error(key, data, "illegal range request (rlegend)");
	    }
	    else {
		double tmpD;

		PS.rl.custom_range = TRUE;
		if (PS.rl.min > PS.rl.max) {
		    tmpD = PS.rl.min;
		    PS.rl.min = PS.rl.max;
		    PS.rl.max = tmpD;
		}
		continue;
	    }
	}
	if (KEY("nodata")) {
	    PS.rl.do_nodata = scan_yesno(key, data);
	    continue;
	}
	if (KEY("gradient")) {
	    PS.rl.do_gradient = scan_yesno(key, data);
	    continue;
	}
	if (KEY("tick")) {
	    if (scan_dimen(data, &dimen) != 1) {
		error(key, data, "illegal tickbar request (rlegend)");
	    }
	    PS.rl.tickbar = (int)(dimen);
	    continue;
	}
	if (KEY("whiteframe")) {
	    if (scan_dimen(data, &dimen) != 1) {
		error(key, data, "illegal whiteframe request (rlegend)");
	    }
	    PS.rl.whiteframe = (int)(dimen);
	    continue;
	}
	if (KEY("order")) {
	    G_strip(data);
	    strncpy(PS.rl.cat_order, data, MAX_CATS);
	    //            PS.rl.cat_order[510] = 0;
	    continue;
	}
	error(key, data, "illegal rlegend sub-request");
    }

    /* end check */
    if (!PS.rl.name) {
	PS.do_rlegend = 0;
	error(key, data, "rlegend need 'raster' option sub-request");
    }
    PS.do_rlegend = 1;

    return 0;
}
