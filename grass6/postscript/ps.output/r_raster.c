/* File: raster.c
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
#include "raster.h"
#include "ps_info.h"
#include "local_proto.h"

#define KEY(x) (strcmp(key,x)==0)


int read_raster(char *arg)
{
    char buf[1024];
    char *key, *data;
    char name[3][100];
    int ret;

    G_debug(1, "Reading raster settings ..");

    /* default values */
    PS.rst.do_rgb = 0;
    PS.rst.do_grey = 0;
    PS.rst.do_mask = 0;
    default_psline(&(PS.rst.outline));
    PS.rst.outline.width = 0.;
    set_color_rgb(&(PS.rst.mask_color), 0, 0, 0);

    /* inline argument */
    ret = sscanf(arg, "%s %s %s", name[0], name[1], name[2]);
    if (ret != 1 && ret != 3) {
	error(key, data, "illegal raster request");
    }
    if (ret == 3) {
	PS.rst.files = load_rgb(name[0], name[1], name[2]);
	PS.rst.do_rgb = 1;
    }
    else {
	if (name[0][0] == ':') {
	    PS.rst.files = load_group(name[0] + 1);
	    PS.rst.do_rgb = 1;
	}
	else {
	    PS.rst.files = load_cell(0, name[0]);
	    PS.rst.fd[1] = PS.rst.fd[2] = -1;
	    PS.rst.do_rgb = 0;
	}
    }

    /* process options */
    while (input(2, buf)) {
	if (!key_data(buf, &key, &data)) {
	    continue;
	}
	if (KEY("grey") || KEY("gray")) {
	    PS.rst.do_grey = scan_yesno(key, data);
	    continue;
	}
	if (KEY("maskcolor")) {
	    if (!scan_color(data, &(PS.rst.mask_color))) {
		error(key, data, "illegal raster mask color request");
	    }
	    continue;
	}
	if (KEY("maskcell")) {
	    if (PS.rst.do_rgb) {
		error(key, data, "illegal maskcell with rgb/group raster");
	    }
	    ret = sscanf(data, "%s %s", name[1], name[2]);
	    if (ret != 1 && ret != 2) {
		error(key, data, "illegal maskcell raster request");
	    }
	    PS.rst.do_mask = 1;
	    load_cell(1, name[1]);	/* slot 1: mask */
	    if (ret == 2)
		load_cell(2, name[2]);	/* slot 2: background */
	    continue;
	}
	if (KEY("outline")) {
	    if (PS.rst.do_rgb) {
		error(key, data, "illegal outline with rgb raster");
	    }
	    read_psline(data, &(PS.rst.outline));
	    continue;
	}
	if (KEY("setcolor")) {
	    int i, count, R, G, B;
	    PSCOLOR color;
	    DCELL *val_list, dmin, dmax;
	    char colorbuf[100], catsbuf[100];

	    /* set color inline */
	    if (PS.rst.fd[0] < 0 || PS.rst.do_rgb) {
		error(key, data, "setcolor is not for RGB raster");
	    }
	    if (sscanf(data, "%s %[^\n]", catsbuf, colorbuf) == 2) {
		if (!scan_color(colorbuf, &color)) {
		    error(key, data, "illegal setcolor request");
		    continue;
		}
		R = (int)(255. * color.r);
		G = (int)(255. * color.g);
		B = (int)(255. * color.b);
		if (strncmp(catsbuf, "null", 4) == 0) {
		    G_set_null_value_color(R, G, B, &(PS.rst.colors[0]));
		    continue;
		}
		if (strncmp(catsbuf, "default", 7) == 0) {
		    G_set_default_color(R, G, B, &(PS.rst.colors[0]));
		    continue;
		}
		if ((count = parse_val_list(catsbuf, &val_list)) < 0) {
		    /* G_free(val_list); */
		    error(key, data, "illegal value list");
		    continue;
		}
		for (i = 0; i < count; i += 2) {
		    dmin = val_list[i];
		    dmax = val_list[i + 1];
		    G_add_d_raster_color_rule(&dmin, R, G, B, &dmax, R, G, B,
					      &(PS.rst.colors[0]));
		}
		G_free(val_list);
	    }
	    continue;
	}
	error(key, data, "illegal raster sub-request");
    }

    return 0;
}
