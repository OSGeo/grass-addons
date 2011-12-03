/* File: r_line.c
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
#include "ps_info.h"
#include "local_proto.h"

#define KEY(x) (strcmp(key,x)==0)


int default_psline(PSLINE * line)
{
    line->width = 1.;
    set_color_rgb(&(line->color), 0, 0, 0);
    line->dash = G_store("");
    line->odash = 0;
    line->cap = line->join = -1;

    return 0;
}

int read_psline(char *arg, PSLINE * line)
{
    char buf[1024];
    char *key, *data;
    char i, dash[31];

    G_debug(1, "Reading line settings ..");

    /* init values */
    default_psline(line);

    /* inline argument: width */
    if (arg[0] != 0) {
	if (scan_dimen(arg, &(line->width)) != 1) {
	    line->width = 1.;
	    error("ERROR:", arg, "illegal line width request");
	}
	return 0;
    }

    /* process options */
    while (input(3, buf)) {
	if (!key_data(buf, &key, &data)) {
	    continue;
	}
	if (KEY("width")) {
	    if (scan_dimen(data, &(line->width)) != 1) {
		line->width = -1.;
		error(key, data, "illegal line width request");
	    }
	    continue;
	}
	if (KEY("color")) {
	    if (!scan_color(data, &(line->color))) {
		error(key, data, "illegal line color request");
	    }
	    continue;
	}
	if (KEY("style")) {
	    char str[50];
	    int x, o;

	    x = sscanf(data, "%s %s", str, &o);
	    if (x != 1 && x != 2) {
		error(key, data, "illegal line style request");
		continue;
	    }
	    if (x == 2)
		line->odash = o;

	    G_strip(str);
	    if (strncmp(str, "solid", 5) == 0) {
		line->dash = G_store("");
		continue;
	    }
	    else if (strncmp(str, "dashed", 5) == 0) {
		line->dash = G_store("3 2");
		continue;
	    }
	    else if (strncmp(str, "dotted", 3) == 0) {
		line->dash = G_store("1");
		continue;
	    }
	    else if (strncmp(str, "dashdotted", 5) == 0) {
		line->dash = G_store("4 2 1 2");
		continue;
	    }
	    char *dp;

	    for (i = 0, dp = str; *dp && i < 20; dp++) {
		if (*dp < '0' || *dp > '9')
		    break;
		dash[i++] = *dp;
		dash[i++] = ' ';
	    }
	    if (i == 0) {
		error(key, str, "illegal line style");
		continue;
	    }
	    dash[--i] = 0;
	    line->dash = G_store(dash);
	    continue;
	}
	if (KEY("cap")) {
	    G_strip(data);
	    if (strncmp(data, "butt", 2) == 0) {
		line->cap = LINECAP_BUTT;
		continue;
	    }
	    else if (strncmp(data, "round", 2) == 0) {
		line->cap = LINECAP_ROUND;
		continue;
	    }
	    else if (strncmp(data, "extended_butt", 2) == 0) {
		line->cap = LINECAP_EXTBUTT;
		continue;
	    }
	    else
		error(key, data, "illegal line cap");
	    continue;
	}
	error(key, data, "illegal line sub-request");
    }

    return 0;
}
