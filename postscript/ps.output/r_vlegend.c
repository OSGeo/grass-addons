/* File: r_vlegend.c
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
#include "vlegend.h"
#include "ps_info.h"
#include "local_proto.h"

#define KEY(x) (strcmp(key,x)==0)

int read_vlegend(char *arg)
{
    char buf[1024];
    char *key, *data;


    G_debug(1, "Reading vlegend settings ..");

    /* default values */
    G_strip(arg);
    strncpy(PS.vl.legend.title, arg, TITLE_LEN);
    default_font(&(PS.vl.legend.title_font));
    default_font(&(PS.vl.legend.font));
    default_frame(&(PS.vl.legend.box), LEFT, LOWER);
    PS.vl.legend.cols = 1;
    PS.vl.legend.width = -1;
    PS.vl.legend.xspan = -1;
    PS.vl.legend.yspan = -1;

    /* process options */
    while (input(2, buf)) {
	if (!key_data(buf, &key, &data)) {
	    continue;
	}
	if (KEY("title") || KEY("title_font")) {
	    G_strip(data);
	    read_font(data, &(PS.vl.legend.title_font));
	    continue;
	}
	if (KEY("font")) {
	    read_font(data, &(PS.vl.legend.font));
	    continue;
	}
	if (KEY("frame")) {
	    read_frame(&(PS.vl.legend.box));
	    continue;
	}
	if (KEY("cols")) {
	    int n = sscanf(data, "%d %lf",
			   &(PS.vl.legend.cols), &(PS.vl.legend.xspan));

	    if (n == 1 || n == 2) {
		if (PS.vl.legend.cols <= 0)
		    PS.vl.legend.cols = 1;
		if (n == 1)
		    PS.vl.legend.xspan = -1.;
	    }
	    else
		error(key, data, "illegal cols/xspan request (vlegend)");
	    continue;
	}
	if (KEY("swidth")) {
	    if (scan_dimen(data, &(PS.vl.legend.width)) != 1) {
		PS.vl.legend.width = -1.;
		error(key, data, "illegal swidth request (vlegend)");
	    }
	    continue;
	}
	if (KEY("interline") || KEY("dy")) {
	    if (scan_dimen(data, &(PS.vl.legend.yspan)) != 1) {
		error(key, data, "illegal interline request (vlegend)");
	    }
	    continue;
	}

	error(key, data, "illegal vlegend sub-request");
    }

    PS.do_vlegend = 1;
    return 0;
}
