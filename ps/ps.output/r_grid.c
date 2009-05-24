/* File: r_grid.c
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
#include "grids.h"
#include "ps_info.h"
#include "local_proto.h"
#include "conversion.h"

#define KEY(x) (strcmp(x,key)==0)


int read_grid(GRID * grid, int type)
{
    char buf[1024];
    char *key, *data;

    G_debug(1, "Reading grid settings ..");

    /* default values */
    grid->sep   = 0;
    grid->msep  = 0;
    default_font(&(grid->font));
    default_psline(&(grid->line));
    default_psline(&(grid->mline));
    set_color_rgb(&(grid->fcolor), 255, 255, 255);
    grid->format = 0;  /* inner labels */
    grid->round  = -1; /* no round */
    grid->cross  = 0.;

    /* process options */
    while (input(2, buf))
    {
		if (!key_data(buf, &key, &data)) {
			continue;
        }
        if (KEY("major") || KEY("line")) {
            char str[50];
            if (sscanf(data, "%s", str) != 1) {
                error(key, data, "illegal major request (grid)");
            }
            if (G_projection() == PROJECTION_LL || type == 1) {
                double seconds;
                scan_second(str, &seconds);
                grid->sep = (int)seconds;
            }
            else {
                grid->sep = atoi(str); /* units, usually meters */
            }
            if (grid->sep <= 0) {
                error(key, data, "illegal major request (grid)");
            }
            read_psline("", &(grid->line));
            continue;
        }
        if (KEY("minor")) {
            char str[50];
            if (sscanf(data, "%s", str) != 1) {
                error(key, data, "illegal minor request (grid)");
            }
            if (G_projection() == PROJECTION_LL || type == 1) {
                double seconds;
                scan_second(str, &seconds);
                grid->msep = (int)seconds;
            }
            else {
                grid->msep = atoi(str); /* units, usually meters */
            }
            if (grid->msep <= 0) {
                error(key, data, "illegal minor request (grid)");
            }
            read_psline("", &(grid->mline));
            continue;
        }
        if (KEY("format")) {
            G_strip(data);
            if (strncmp(data,"in",2)==0) {
                grid->format = 0;
            }
            else if (strncmp(data,"out",3)==0) {
                grid->format = 1;
            }
            else if (strncmp(data,"iho",3)==0) {
                grid->format = 2;
            }
            else
                grid->format = atoi(data);
            continue;
        }
        if (KEY("round")) {
            G_strip(data);
            grid->round = atoi(data);
            continue;
        }
        if (KEY("font")) {
			read_font(data, &(grid->font));
			continue;
		}
		if (KEY("fcolor")) {
            if (!scan_color(data, &(grid->fcolor))) {
                error(key, data, "illegal fcolor request (grid)");
            }
			continue;
		}
        if (KEY("cross")) {
            grid->cross = atof(data);
            continue;
        }
        error(key, data, "illegal request (grid)");
    }

    /* swap major and minor if ... */
    if (grid->sep < grid->msep)
    {
        int tmp;
        tmp = grid->msep;
        grid->msep = grid->sep;
        grid->sep = tmp;
    }

    return 0;
}
