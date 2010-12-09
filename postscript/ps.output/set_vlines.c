/* File: set_vlines.c
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

#define DRAW_LINE   0
#define DRAW_HLINE  1


/* TO DRAW LINES */
int vector_line(struct line_pnts *lpoints)
{
    if (lpoints->n_points > 0) {
	register int i;

	set_ps_where('M', lpoints->x[0], lpoints->y[0]);
	for (i = 1; i <= lpoints->n_points - 1; i++) {
	    set_ps_where('L', lpoints->x[i], lpoints->y[i]);
	}
    }
    return 0;
}

/** Process a vector of lines */
int set_vlines(VECTOR * vec, VLINES * vl, int flag)
{
    int ret, cat;
    int ln, nlines, pt, npoints;
    struct line_cats *lcats;
    struct line_pnts *lpoints;


    nlines = Vect_get_num_lines(&(vec->Map));

    fprintf(PS.fp, "GS 1 setlinejoin NP\n");	/* lines with linejoin = round */

    /* Create vector array, if required */
    if (vec->cats != NULL) {
	vec->Varray = Vect_new_varray(nlines);
	ret =
	    Vect_set_varray_from_cat_string(&(vec->Map), vec->layer,
					    vec->cats, vl->type, 1,
					    vec->Varray);
    }
    else if (vec->where != NULL) {
	vec->Varray = Vect_new_varray(nlines);
	ret =
	    Vect_set_varray_from_db(&(vec->Map), vec->layer, vec->where,
				    vl->type, 1, vec->Varray);
    }
    else
	vec->Varray = NULL;

    /* memory for coordinates */
    lcats = Vect_new_cats_struct();
    lpoints = Vect_new_line_struct();

    /* process only vectors in current window */
    Vect_set_constraint_region(&(vec->Map),
			       PS.map.north, PS.map.south,
			       PS.map.east, PS.map.west,
			       PORT_DOUBLE_MAX, -PORT_DOUBLE_MAX);

    /* load attributes if fcolor is named */
    dbCatValArray rgbcv, idcv;

    if (flag == DRAW_LINE) {
	if (vl->rgbcol != NULL) {
	    load_catval_array(&(vec->Map), vl->rgbcol, &rgbcv);
	    if (vl->idcol != NULL)
		load_catval_array(&(vec->Map), vl->idcol, &idcv);
	}
    }

    /* read and plot lines */
    for (ln = 1; ln <= nlines; ln++) {
	ret = Vect_read_line(&(vec->Map), lpoints, lcats, ln);
	if (ret < 0)
	    continue;
	if (!(ret & GV_LINES) || !(ret & vl->type))
	    continue;
	if (vec->Varray != NULL && vec->Varray->c[ln] == 0)
	    continue;

	/* Oops the line is correct, I can draw it */
	/* How I can draw it? */
	if (flag == DRAW_HLINE) {
	    if (vl->offset != 0.) {
		double dis;
		struct line_pnts *opoints = Vect_new_line_struct();

		/* perhaps dont run in Lat/Lon */
		dis = vl->offset * POINT_TO_MM / 1000. * PS.scale;
		Vect_line_parallel(lpoints, dis, 0.1, 0, opoints);
		vector_line(opoints);
	    }
	    else {
		vector_line(lpoints);
	    }
	    set_ps_line(&(vl->hline));
	}
	else {
	    vector_line(lpoints);
	    if (vl->rgbcol == NULL) {
		set_ps_color(&(vl->line.color));
	    }
	    else {
		PSCOLOR color;

		Vect_cat_get(lcats, 1, &cat);
		set_color_name(&color, get_string(&rgbcv, cat, 0));
		color.a = vl->line.color.a;
		set_ps_color(&color);

		if (vl->idcol != NULL) {
		    double value;

		    get_number(&idcv, cat, &value);
		    vector_item_new(vec, value, color_to_long(&color));
		}
		else
		    vector_item_new(vec, 0, color_to_long(&color));
	    }
	    set_ps_line_no_color(&(vl->line));
	}
	/* paint now */
	fprintf(PS.fp, "S\n");
    }
    fprintf(PS.fp, "GR\n");
    return 0;
}
