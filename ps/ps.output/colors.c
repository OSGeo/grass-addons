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


void unset_color(PSCOLOR *color)
{
    color->none = 1;
    color->r = color->g = color->b = 0.;
}

int set_color_name(PSCOLOR *color, char *name)
{
    int R, G, B;

    if (strcmp(name, "none") == 0)
    {
        unset_color(color);
        return 1;
    }
    /* standard GRASS colors */
    if (G_str_to_color(name, &R, &G, &B) == 1)
    {
        set_color_rgb(color, R, G, B);
        return 1;
    }
    /* PS3 palette colors */
    if (PS_str_to_color(name, color) == 1)
    {
        return 1;
    }
    unset_color(color);
    return 0;
}

void set_color_rgb(PSCOLOR *color, int r, int g, int b)
{
    color->none = 0;

    color->r = (double)r / 255.;
    color->g = (double)g / 255.;
    color->b = (double)b / 255.;
}

/* PostScript shortcut */

void set_ps_color(PSCOLOR *color)
{
    if (!color->none)
        fprintf(PS.fp, "%.3f %.3f %.3f C ",
                color->r, color->g, color->b);
}

int set_ps_grey(PSCOLOR *color)
{
    if (!color->none)
        fprintf(PS.fp, "%.3f %.3f %.3f CG ",
                color->r, color->g, color->b);
    return 0;
}

void set_ps_rgb(int R, int G, int B)
{
    fprintf(PS.fp, "%.3f %.3f %.3f C ",
            (double)R/255., (double)G/255., (double)B/255.);
}


