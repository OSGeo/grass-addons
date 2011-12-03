/* File: r_font.c
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
#include "fonts.h"
#include "ps_info.h"
#include "local_proto.h"

#define KEY(x) (strcmp(key,x)==0)

/* Function: get_font
 **
 ** Author: Paul W. Carlson     April 1992
 */
int get_font(char *data)
{
    char *dp;

    G_strip(data);
    /* replace spaces with dashes and make sure each
     ** word begins with a capital letter.
     */
    dp = data;
    if (*dp >= 'a' && *dp <= 'z')
	*dp = *dp - 'a' + 'A';
    while (*dp) {
	if (*dp == ' ') {
	    *dp++ = '-';
	    if (*dp >= 'a' && *dp <= 'z')
		*dp = *dp - 'a' + 'A';
	}
	else
	    dp++;
    }
    return 0;
}


int default_font(PSFONT * font)
{
    strcpy(font->name, PS.font.name);
    font->size = PS.font.size;
    font->extend = PS.font.extend;
    set_color_pscolor(&(font->color), &(PS.font.color));
}

int read_font(char *arg, PSFONT * font)
{
    char buf[1024];
    char *key, *data;

    G_debug(1, "Reading font settings ..");

    /* init values */
    default_font(font);


    /* process options */
    while (input(3, buf)) {
	if (!key_data(buf, &key, &data)) {
	    continue;
	}
	if (KEY("name")) {
	    get_font(data);
	    strcpy(font->name, data);
	    continue;
	}
	if (KEY("size")) {
	    if (scan_dimen(data, &(font->size)) != 1) {
		font->size = 10.;
		error(key, data, "illegal size request (font)");
	    }
	    continue;
	}
	if (KEY("extend")) {
	    if (scan_dimen(data, &(font->extend)) != 1) {
		font->extend = 1.;
		error(key, data, "illegal extent request (font)");
	    }
	    continue;
	}
	if (KEY("color")) {
	    if (!scan_color(data, &(font->color))) {
		error(key, data, "illegal color request (font)");
	    }
	    continue;
	}
	error(key, data, "illegal font sub-request");
    }

    return 0;
}
