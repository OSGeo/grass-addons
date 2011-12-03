/* File: r_palette.c
 *
 *  AUTHOR:    E. Jorge Tizado, Spain 2009
 *
 *  COPYRIGHT: (c) 2009 E. Jorge Tizado
 *             This program is free software under the GNU General Public
 *             License (>=v2). Read the file COPYING that comes with GRASS
 *             for details.
 */

#include <stdlib.h>
#include <string.h>
#include "colors.h"
#include "ps_info.h"
#include "local_proto.h"

#define KEY(x,n) (strncmp(key,x,n)==0)


// complementary blue 5 <<<< 180 grados
// afin red 4 <<<< 45 grados
// gradient red blue 10
// monochromatic red 10
// triadic red <<<<< whell 3 con inicio variable

int read_palette(void)
{
    char buf[1024];
    char *key, *data;
    int i;
    char name[50];
    PSCOLOR color, colorb;

    G_debug(1, "Reading palette settings ..");

    /* process options */
    while (input(2, buf)) {
	if (!key_data(buf, &key, &data)) {
	    continue;
	}
	if (KEY("wheel", 2)) {
	    if (sscanf(data, "%d %s", &i, name) != 2 || i < 2) {
		error(key, data, "illegal wheel sub-request (palette)");
	    }
	    pure_color(name, i);
	    continue;
	}
	if (KEY("monochrome", 4)) {
	    char color_name[50];

	    if (sscanf(data, "%s %d %s", color_name, &i, name) != 3) {
		error(key, data, "illegal monochrome sub-request (palette)");
	    }
	    if (i < 1 || !scan_color(color_name, &color)) {
		error(key, data, "illegal monochrome sub-request (palette)");
	    }
	    monochrome(name, &color, i);
	    continue;
	}
	if (KEY("complementary", 4)) {
	    char color_name[50];

	    if (sscanf(data, "%s %d %s", color_name, &i, name) != 3) {
		error(key, data,
		      "illegal complementary sub-request (palette)");
	    }
	    if (i < 1 || !scan_color(color_name, &color)) {
		error(key, data,
		      "illegal complementary sub-request (palette)");
	    }
	    complementary(name, &color, i, 90.);
	    continue;
	}
	if (KEY("analogous", 3)) {
	    char color_name[50];

	    if (sscanf(data, "%s %d %s", color_name, &i, name) != 3) {
		error(key, data, "illegal analogous sub-request (palette)");
	    }
	    if (i < 1 || !scan_color(color_name, &color)) {
		error(key, data, "illegal analogous sub-request (palette)");
	    }
	    analogous(name, &color, i, 90.);
	    continue;
	}
	if (KEY("pure_gradient", 4)) {
	    char A_name[50], B_name[50];

	    if (sscanf(data, "%s %s %d %s", A_name, B_name, &i, name) != 4) {
		error(key, data,
		      "illegal pure_gradient sub-request (palette)");
	    }
	    if (i < 3 || !scan_color(A_name, &color) ||
		!scan_color(B_name, &colorb)) {
		error(key, data,
		      "illegal pure_gradient sub-request (palette)");
	    }
	    gradient(name, &color, &colorb, i, 1);
	    continue;
	}
	if (KEY("gradient", 4)) {
	    char A_name[50], B_name[50];

	    if (sscanf(data, "%s %s %d %s", A_name, B_name, &i, name) != 4) {
		error(key, data, "illegal gradient sub-request (palette)");
	    }
	    if (i < 3 || !scan_color(A_name, &color) ||
		!scan_color(B_name, &colorb)) {
		error(key, data, "illegal gradient sub-request (palette)");
	    }
	    gradient(name, &color, &colorb, i, 0);
	    continue;
	}
	if (KEY("diverging", 4)) {
	    char A_name[50], B_name[50];

	    if (sscanf(data, "%s %s %d %s", A_name, B_name, &i, name) != 4) {
		error(key, data,
		      "illegal xxx diverging sub-request (palette)");
	    }
	    if (i < 3 || !scan_color(A_name, &color) ||
		!scan_color(B_name, &colorb)) {
		error(key, data,
		      "illegal yyy diverging sub-request (palette)");
	    }
	    diverging(name, &color, &colorb, i);
	    continue;
	}
	error(key, data, "illegal zzz palette sub-request");
    }

    return 0;
}
