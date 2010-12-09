/* File: set_vlabels.c
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
#include <grass/symbol.h>
#include <grass/Vect.h>
#include <grass/dbmi.h>
#include "vector.h"
#include "ps_info.h"
#include "local_proto.h"


/** Process a vector with labels */
int set_vlabels(VECTOR * vec, VLABELS * vx)
{
    int ret, cat;
    int x, y, pt, npoints;
    struct line_cats *lcats;
    struct line_pnts *lpoints;

    npoints = Vect_get_num_lines(&(vec->Map));

    /* Create vector array, if required */
    if (vec->cats != NULL) {
	vec->Varray = Vect_new_varray(npoints);
	Vect_set_varray_from_cat_string(&(vec->Map), vec->layer, vec->cats,
					vx->type, 1, vec->Varray);
    }
    else if (vec->where != NULL) {
	vec->Varray = Vect_new_varray(npoints);
	Vect_set_varray_from_db(&(vec->Map), vec->layer, vec->where, vx->type,
				1, vec->Varray);
    }
    else
	vec->Varray = NULL;

    /* memory for coordinates */
    lcats = Vect_new_cats_struct();
    lpoints = Vect_new_line_struct();

    /* load attributes if any */
    dbCatValArray cv_label;

    if (vx->labelcol != NULL) {
	load_catval_array(&(vec->Map), vx->labelcol, &cv_label);
    }
    else
	return 0;

    fprintf(PS.fp, "GS\n");
    set_ps_font(&(vx->font));

    /* read and plot lines */
    for (pt = 1; pt <= npoints; pt++) {
	ret = Vect_read_line(&(vec->Map), lpoints, lcats, pt);
	if (ret < 0)
	    continue;
	if (!(ret & GV_POINTS) || !(ret & vx->type))
	    continue;
	if (vec->Varray != NULL && vec->Varray->c[pt] == 0)
	    continue;
	/* Is it inside area? */
	G_plot_where_xy(lpoints->x[0], lpoints->y[0], &x, &y);
	PS.x = (double)x / 10.;
	PS.y = (double)y / 10.;
	if (PS.x < PS.map_x || PS.x > PS.map_right || PS.y < PS.map_y ||
	    PS.y > PS.map_top)
	    continue;
	/* Oops the point is correct, I can draw it */
	Vect_cat_get(lcats, 1, &cat);

	fprintf(PS.fp, "%.4f %.4f M (%s) ",
		PS.x, PS.y, get_string(&cv_label, cat, vx->decimals));

	/* Draw text with a style */
	if (vx->style != 0) {
	    fprintf(PS.fp, "GS %.2f LW [] 0 LD dup TCIR GR\n", vx->style);
	}
	fprintf(PS.fp, "SHCC ");
    }
    fprintf(PS.fp, "GR\n");

    return 0;
}
