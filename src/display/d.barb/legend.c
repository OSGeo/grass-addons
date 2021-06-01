#include <stdlib.h>
#include <string.h>
#include <grass/gis.h>
#include <grass/display.h>
#include <grass/raster.h>
#include "local_proto.h"

void do_legend(char **at_list, char **velo_list, int num_velos,
	       double key_fontsize, int style, double scale, double setpeak,
	       int color)
{
    double easting, northing, px, py, velo, angle;
    int Xpx, Ypx;
    int t, b, l, r;
    int i;
    char buff[1024];

    G_debug(1, "Doing legend ... (%d entries)", num_velos);

    if (style == TYPE_BARB || style == TYPE_SMLBARB)
	angle = -90;
    else
	angle = 90;

    D_get_screen_window(&t, &b, &l, &r);

    for (i = 0; i < num_velos; i++) {
	px = atof(at_list[i * 2]);
	py = atof(at_list[i * 2 + 1]);
	velo = atof(velo_list[i]);

	G_debug(4, "Legend entry: %.15g at [%.2f,%.2f]", velo, px, py);

	// frame percent, utm, display pixels, raster array coords.  all -> utm ?
	/* convert screen percentage to east,north */
	// check if +.5 rounding is really needed

	Xpx = (int)((px * (r - l) / 100.) + 0.5);
	Ypx = (int)(((100. - py) * (b - t) / 100.) + 0.5);
	easting = D_d_to_u_col(Xpx);
	northing = D_d_to_u_row(Ypx);

	// actually this could stay in screen pixel coords...
	//  anyway it should work if out-of-region (borders)

	G_debug(5, "  (aka east=%.2f  north=%2.f)", easting, northing);
	G_debug(5, "  (aka pixelX=%d  pixelY=%d)", Xpx, Ypx);

	D_raster_use_color(color);
	sprintf(buff, "%s", velo_list[i]);

	/* Y: center justify: */
	R_move_abs(Xpx, Ypx + key_fontsize / 2);

	/* X: right justify the text + 10px buffer (a wee bit more for wind barbs) */
	/* text width is 0.81 of text height? so even though we set width 
	   to txsiz with R_text_size(), we still have to reduce.. hmmm */
	if (style == TYPE_BARB || style == TYPE_SMLBARB)
	    R_move_rel(-20 - (strlen(buff) * key_fontsize * 0.81), 0);
	else
	    R_move_rel(-10 - (strlen(buff) * key_fontsize * 0.81), 0);

	R_text_size(key_fontsize, key_fontsize);
	R_text(buff);

	/* arrow then starts at the given x-percent, to the right of the text */
	R_move_abs(Xpx, Ypx + key_fontsize / 2);
	draw_barb(easting, northing, velo, angle, color, scale, style);

    }

    return;
}
