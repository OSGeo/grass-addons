/* File: colors.c
 *
 *  AUTHOR:    E. Jorge Tizado, Spain 2009
 *
 *  COPYRIGHT: (c) 2009 E. Jorge Tizado, and the GRASS Development Team
 *             This program is free software under the GNU General Public
 *             License (>=v2). Read the file COPYING that comes with GRASS
 *             for details.
 */

#include <stdio.h>
#include <string.h>
#include <grass/gis.h>
#include "colors.h"
#include "ps_info.h"
#include "local_proto.h"


void unset_color(PSCOLOR * color)
{
    color->none = 1;
    color->r = color->g = color->b = 0.;
}

int set_color_name(PSCOLOR * color, char *name)
{
    int R, G, B;

    if (*name == 0 || strcmp(name, "none") == 0) {
	unset_color(color);
	return 1;
    }
    /* standard GRASS colors */
    if (G_str_to_color(name, &R, &G, &B) == 1) {
	set_color_rgb(color, R, G, B);
	return 1;
    }
    /* PS3 palette colors */
    if (PS_str_to_color(name, color) == 1) {
	return 1;
    }
    unset_color(color);
    return 0;
}

void set_color_rgb(PSCOLOR * color, int r, int g, int b)
{
    color->none = 0;

    color->a = 1.;
    color->r = (double)r / 255.;
    color->g = (double)g / 255.;
    color->b = (double)b / 255.;
}

void set_color_pscolor(PSCOLOR * color, PSCOLOR * pscolor)
{
    color->none = pscolor->none;

    color->a = pscolor->a;
    color->r = pscolor->r;
    color->g = pscolor->g;
    color->b = pscolor->b;
}

long color_to_long(PSCOLOR * color)
{
    return (16711680 * color->r + 65280 * color->g + 255 * color->b);
}

int long_to_color(long ln, PSCOLOR * color)
{
    color->none = 0;

    color->r = (double)((ln & 16711680) >> 16) / 255.;
    color->g = (double)((ln & 65280) >> 8) / 255.;
    color->b = (double)(ln & 255) / 255.;
    /*
       fprintf(PS.fp, "%.3f %.3f %.3f ",
       (double)((ln & 16711680) >> 16)/255.,
       (double)((ln & 65280) >> 8)/255.,
       (double)(ln & 255)/255.);
     */
    return 0;
}

/* PostScript shortcut */

int set_ps_color(PSCOLOR * color)
{
    if (!color->none) {
	fprintf(PS.fp, "%.3f %.3f %.3f C ", color->r, color->g, color->b);

	if ((PS.flag & 1) && color->a > 0.)
	    fprintf(PS.fp, "%.2f O ", color->a);
    }
    return 0;
}

int set_ps_grey(PSCOLOR * color)
{
    if (!color->none) {
	fprintf(PS.fp, "%.3f %.3f %.3f CG ", color->r, color->g, color->b);

	if ((PS.flag & 1) && color->a > 0.)
	    fprintf(PS.fp, "%.2f O ", color->a);
    }
    return 0;
}
