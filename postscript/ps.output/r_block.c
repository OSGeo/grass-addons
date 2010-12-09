/* File: r_block.c
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


int read_block(int i)
{
    char buf[1024];
    char *key, *data;

    G_debug(1, "Reading legend settings ..");

    /* process options */
    while (input(2, buf)) {
	if (!key_data(buf, &key, &data)) {
	    continue;
	}
	if (KEY("lpos")) {
	    if (sscanf(data, "%d", &(PS.vct[i].lpos)) != 1) {
		error(key, data, "illegal lpos request (legend)");
	    }
	    continue;
	}
	if (KEY("cols")) {
	    int n =
		sscanf(data, "%d %lf", &(PS.vct[i].cols), &(PS.vct[i].xspan));

	    if (n != 1 && n != 2) {
		error(key, data, "illegal cols/span request (legend)");
	    }
	    else {
		if (PS.vct[i].cols <= 0)
		    PS.vct[i].cols = 1;
		if (n == 1)
		    PS.vct[i].xspan = -1.;
	    }
	    continue;
	}
	if (KEY("interline") || KEY("dy")) {
	    if (scan_dimen(data, &(PS.vct[i].yspan)) != 1) {
		PS.vct[i].yspan = -1.;
		error(key, data, "illegal interline request (legend)");
	    }
	    continue;
	}
	error(key, data, "illegal block of legend sub-request");
    }

    return 0;
}
