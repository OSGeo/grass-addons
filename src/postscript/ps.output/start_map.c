/* File: start_map.c
 *
 *  AUTHOR:    E. Jorge Tizado, Spain 2009
 *
 *  COPYRIGHT: (c) 2009 E. Jorge Tizado, and the GRASS Development Team
 *             This program is free software under the GNU General Public
 *             License (>=v2). Read the file COPYING that comes with GRASS
 *             for details.
 */

#include <grass/gis.h>
#include <grass/glocale.h>
#include "ps_info.h"
#include "local_proto.h"

#include "conversion.h"

int move_local(int x, int y);
int cont_local(int x, int y);

int start_map(void)
{
    double width, height;
    double fact, d_ns, ns, d_ew, ew;

    /* default position */
    if (PS.map_x < 0) {
	PS.map_x = PS.page.left + PS.brd.width;
    }
    if (PS.map_top < 0) {
	PS.map_top = PS.page.top + PS.brd.width;
    }

    /* maximun space to print from position */
    width = PS.page.width - PS.map_x - (PS.page.right + PS.brd.width);
    height = PS.page.height - PS.map_top - (PS.page.bot + PS.brd.width);

    /* default size */
    if (PS.map_w < 0 || PS.map_w > width) {
	PS.map_w = width;
    }
    if (PS.map_h < 0 || PS.map_h > height) {
	PS.map_h = height;
    }

    /* distance calculation, throught center of map */
    G_begin_distance_calculations();

    if (PS.map.proj == PROJECTION_LL) {
	ns = (PS.map.north + PS.map.south) / 2.;
	d_ew = G_distance(PS.map.east, ns, PS.map.west, ns);

	ew = (PS.map.east + PS.map.west) / 2.;
	d_ns = G_distance(ew, PS.map.north, ew, PS.map.south);
    }
    else {
	d_ew = (PS.map.east - PS.map.west);
	d_ns = (PS.map.north - PS.map.south);
    }

    /* to define the scale */
    if (PS.scale > 0) {
	fact = MT_TO_POINT / (double)PS.scale;
	ew = fact * d_ew;
	ns = fact * d_ns;
	if (ew <= PS.map_w && ns <= PS.map_h) {
	    PS.map_w = ew;
	    PS.map_h = ns;
	}
	else
	    PS.scale = 0;	/* forze readjust scale */
    }
    /* auto scale */
    if (PS.scale <= 0) {
	ew = d_ew / PS.map_w;
	ns = d_ns / PS.map_h;
	fact = (ew > ns) ? ew : ns;
	PS.scale = (int)(MT_TO_POINT * fact);

	fact = 1000. * MM_TO_POINT / (double)PS.scale;
	PS.map_w = fact * d_ew;
	PS.map_h = fact * d_ns;
    }

    G_message(_("Scale set to  1 : %d"), PS.scale);

    /* now I can calculate the 'y' position */
    PS.map_y = PS.page.height - PS.map_h - PS.map_top;

    /* to complete */
    PS.map_right = PS.map_x + PS.map_w;
    PS.map_top = PS.map_y + PS.map_h;

    G_setup_plot(10. * (PS.map_y + PS.map_h), 10. * PS.map_y,
		 10. * PS.map_x, 10. * (PS.map_x + PS.map_w), move_local,
		 cont_local);

    return 0;
}

/* Needed by G_setup_plot */
int move_local(int x, int y)
{
    fprintf(PS.fp, "%.1f %.1f M\n", (double)x / 10., (double)y / 10.);
    return 0;
}

int cont_local(int x, int y)
{
    fprintf(PS.fp, "%.1f %.1f L ", (double)x / 10., (double)y / 10.);
    return 0;
}
