/* File: lines.c
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
#include "lines.h"

/* PostScript shortcut */

int set_ps_linewidth(double width)
{
    if (width > 0.)
	fprintf(PS.fp, "%.3f LW ", width);
    return 0;

}

int set_ps_line(PSLINE * line)
{
    set_ps_color(&(line->color));
    set_ps_linewidth(line->width);

    fprintf(PS.fp, "[%s] %d LD ", line->dash, line->odash);
    if (line->cap > 0)
	fprintf(PS.fp, "%d LC ", line->cap);
    if (line->join > 0)
	fprintf(PS.fp, "%d LJ ", line->join);

    fprintf(PS.fp, "\n");
    return 0;
}

int set_ps_line_no_color(PSLINE * line)
{
    set_ps_linewidth(line->width);

    fprintf(PS.fp, "[%s] %d LD ", line->dash, line->odash);
    if (line->cap > 0)
	fprintf(PS.fp, "%d LC ", line->cap);
    if (line->join > 0)
	fprintf(PS.fp, "%d LJ ", line->join);

    return 0;
}
