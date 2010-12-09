/* File: r_scalebar.c
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
#include "scalebar.h"

#define KEY(x) (strcmp(key,x)==0)
#ifndef ABS
#define ABS(x) (x > 0 ? x : -x)
#endif


int read_scalebar(void)
{
    char buf[1024];
    char *key, *data;

    G_debug(1, "Reading scalebar settings ..");

    /* default values */
    PS.sbar.ucode = SB_UNITS_AUTO;
    PS.sbar.units[0] = 0;
    PS.sbar.length = -1.;
    PS.sbar.height = 4.;	/* default height in points */
    PS.sbar.labels = 1;		/* label each segment */
    PS.sbar.segments = 4;	/* four segments */
    PS.sbar.sublabs = 1;	/* label pre-segment */
    PS.sbar.subsegs = 1;	/* division pre-segment */
    default_font(&(PS.sbar.font));
    default_frame(&(PS.sbar.box), LEFT, UPPER);
    set_color_rgb(&(PS.sbar.fcolor), 255, 255, 255);

    /* process options */
    while (input(2, buf)) {
	if (!key_data(buf, &key, &data)) {
	    continue;
	}
	if (KEY("frame")) {
	    read_frame(&(PS.sbar.box));
	    continue;
	}
	if (KEY("font")) {
	    read_font(data, &(PS.sbar.font));
	    continue;
	}
	if (KEY("fcolor")) {
	    if (!scan_color(data, &(PS.sbar.fcolor))) {
		error(key, data, "illegal fcolor request (scalebar)");
	    }
	    continue;
	}
	if (KEY("height")) {
	    if (scan_dimen(data, &(PS.sbar.height)) != 1) {
		error(key, data, "illegal height request (scalebar)");
	    }
	    continue;
	}
	if (KEY("length")) {
	    if (scan_dimen(data, &(PS.sbar.length)) != 1) {
		error(key, data, "illegal length request (scalebar)");
	    }
	    continue;
	}
	if (KEY("major") || KEY("segments")) {
	    int i, j;

	    switch (sscanf(data, "%d %d", &i, &j)) {
	    case 1:
		PS.sbar.segments = ABS(i);
		PS.sbar.labels = 1;
		break;
	    case 2:
		PS.sbar.segments = ABS(i);
		PS.sbar.labels = (j == 0 ? ABS(i) + 1 : ABS(j));
		break;
	    default:
		error(key, data, "illegal segment request (scalebar)");
		break;
	    }
	    continue;
	}
	if (KEY("minor")) {
	    int i, j;

	    switch (sscanf(data, "%d %d", &i, &j)) {
	    case 1:
		PS.sbar.subsegs = ABS(i);
		PS.sbar.sublabs = 1;
		break;
	    case 2:
		PS.sbar.subsegs = ABS(i);
		PS.sbar.sublabs = (j == 0 ? ABS(i) + 1 : ABS(j));
		break;
	    default:
		error(key, data, "illegal minor request (scalebar)");
		break;
	    }
	    continue;
	}
	if (KEY("units")) {
	    int ret;
	    char stra[50], strb[50];

	    G_strip(data);
	    ret = sscanf(data, "%s %s", stra, strb);
	    if (ret != 1 && ret != 2) {
		error(key, data, "illegal units request (scalebar)");
	    }
	    if (strcmp(stra, "auto") == 0) {
		PS.sbar.units[0] = 0;
		PS.sbar.ucode = SB_UNITS_AUTO;
		continue;
	    }
	    else if (G_projection() == PROJECTION_XY) {
		error(key, data,
		      "Earth units not available in simple XY location");
	    }
	    else if (strcmp(stra, "meters") == 0 || strcmp(stra, "m") == 0) {
		strcpy(PS.sbar.units, "meters");
		PS.sbar.ucode = SB_UNITS_METERS;
	    }
	    else if (strcmp(stra, "kilometers") == 0 ||
		     strcmp(stra, "km") == 0) {
		strcpy(PS.sbar.units, "kilometers");
		PS.sbar.ucode = SB_UNITS_KM;
	    }
	    else if (strcmp(stra, "feet") == 0 || strcmp(stra, "ft") == 0) {
		strcpy(PS.sbar.units, "feet");
		PS.sbar.ucode = SB_UNITS_FEET;
	    }
	    else if (strcmp(stra, "miles") == 0 || strcmp(stra, "mil") == 0) {
		strcpy(PS.sbar.units, "miles");
		PS.sbar.ucode = SB_UNITS_MILES;
	    }
	    else if (strcmp(stra, "nautmiles") == 0 ||
		     strcmp(stra, "nm") == 0) {
		strcpy(PS.sbar.units, "nautical miles");
		PS.sbar.ucode = SB_UNITS_NMILES;
	    }
	    else {
		error(key, data, "illegal units request (scalebar)");
	    }
	    if (ret == 2)
		strcpy(PS.sbar.units, strb);
	    continue;
	}
	error(key, data, "illegal sub-request (scalebar)");
    }

    if (PS.sbar.type == 'I')
	PS.sbar.labels = 1;

    return 0;
}
