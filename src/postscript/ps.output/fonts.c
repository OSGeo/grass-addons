/* File: fonts.c
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
#include "ps_info.h"
#include "local_proto.h"
#include "fonts.h"

double set_ps_font_nocolor(PSFONT * font)
{
    if (font->extend == 1. || font->extend <= 0.) {
	fprintf(PS.fp, "(%s) FN %.1f FS\n", font->name, font->size);
    }
    else {
	fprintf(PS.fp, "(%s) FN %.1f %.2f FE\n", font->name, font->size,
		font->extend);
    }
    return font->size;
}

double set_ps_font(PSFONT * font)
{
    set_ps_color(&(font->color));
    set_ps_font_nocolor(font);
}
