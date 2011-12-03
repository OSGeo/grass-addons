/* File: set_vareas.c
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


/* TO DRAW AREAS */
int vector_area(struct line_pnts *lpoints, double sep)
{
    if (lpoints->n_points > 0) {
	struct line_pnts *opoints;

	opoints = Vect_new_line_struct();

	register int i;

	set_ps_where('M', lpoints->x[0], lpoints->y[0]);
	for (i = 1; i < lpoints->n_points; i++) {
	    set_ps_where('L', lpoints->x[i], lpoints->y[i]);
	}
	Vect_line_parallel(lpoints, sep, 0.01, 0, opoints);
	Vect_line_reverse(opoints);
	for (i = 0; i < opoints->n_points; i++) {
	    set_ps_where('L', opoints->x[i], opoints->y[i]);
	}
	set_ps_where('L', lpoints->x[0], lpoints->y[0]);
    }
    return 0;
}

/* Process a vector of areas */
int set_vareas(VECTOR * vec, VAREAS * va)
{
    int k, ret, cat;
    int area, nareas, island, nislands, centroid;
    struct line_cats *lcats;
    struct line_pnts *lpoints;
    BOUND_BOX box;

    nareas = Vect_get_num_areas(&(vec->Map));

    fprintf(PS.fp, "GS 1 setlinejoin\n");

    /* Create vector array, if required */
    if (vec->cats != NULL) {
	vec->Varray = Vect_new_varray(nareas);
	Vect_set_varray_from_cat_string(&(vec->Map), vec->layer, vec->cats,
					GV_AREA, 1, vec->Varray);
    }
    else if (vec->where != NULL) {
	vec->Varray = Vect_new_varray(nareas);
	Vect_set_varray_from_db(&(vec->Map), vec->layer, vec->where, GV_AREA,
				1, vec->Varray);
    }
    else
	vec->Varray = NULL;

    /* memory for categories and coordinates */
    lcats = Vect_new_cats_struct();
    lpoints = Vect_new_line_struct();

    /* load attributes if fcolor is named */
    dbCatValArray rgbcv, idcv;

    if (va->rgbcol != NULL) {
	load_catval_array(&(vec->Map), va->rgbcol, &rgbcv);
	if (va->idcol != NULL)
	    load_catval_array(&(vec->Map), va->idcol, &idcv);
    }

    /* read and plot vectors */
    for (area = 1; area <= nareas; area++) {
	if (vec->Varray != NULL && vec->Varray->c[area] == 0) {
	    continue;
	}
	/* check if is a island */
	centroid = Vect_get_area_centroid(&(vec->Map), area);
	if (centroid < 1)
	    continue;
	/* check if in window */
	Vect_get_area_box(&(vec->Map), area, &box);
	if (box.N < PS.map.south || box.S > PS.map.north ||
	    box.E < PS.map.west || box.W > PS.map.east)
	    continue;
	/* Oops is a correct area, I can draw it */
	if (Vect_get_area_points(&(vec->Map), area, lpoints) < 0)
	    break;
	/* main area */
	fprintf(PS.fp, "NP ");
	vector_line(lpoints);
	fprintf(PS.fp, "CP\n");
	/* islands */
	if (centroid > 0 && va->island) {
	    nislands = Vect_get_area_num_isles(&(vec->Map), area);
	    for (island = 0; island < nislands; island++) {
		k = Vect_get_area_isle(&(vec->Map), area, island);
		if (Vect_get_isle_points(&(vec->Map), k, lpoints) < 0)
		    return -1;	/* ? break; */

		vector_line(lpoints);
		fprintf(PS.fp, "CP\n");
	    }
	}
	/* set the fill */
	if (!va->fcolor.none || va->rgbcol != NULL) {
	    PSCOLOR color;

	    if (va->rgbcol == NULL) {
		set_color_pscolor(&color, &(va->fcolor));
	    }
	    else {
		cat = Vect_get_area_cat(&(vec->Map), area, vec->layer);
		set_color_name(&color, get_string(&rgbcv, cat, 0));
		color.a = va->fcolor.a;

		if (va->idcol != NULL) {
		    double value;

		    get_number(&idcv, cat, &value);
		    vector_item_new(vec, value, color_to_long(&color));
		}
		else {
		    vector_item_new(vec, 0, color_to_long(&color));
		}
	    }
	    /* set the type of fill if color */
	    if (!color.none) {
		fprintf(PS.fp, "GS %.2f O ", color.a);
		if (va->name_pat == NULL || va->type_pat == 2) {
		    fprintf(PS.fp, "%.3f %.3f %.3f ", color.r, color.g,
			    color.b);
		}
		if (va->name_pat != NULL) {
		    fprintf(PS.fp, "PATTERN%d setpattern ", vec->id);
		}
		else {
		    fprintf(PS.fp, "C ");
		}
		fprintf(PS.fp, "fill GR ");
	    }
	}
	/* set the line style */
	if (va->line.width > 0. && !va->line.color.none) {
	    set_ps_line(&(va->line));
	    fprintf(PS.fp, "S\n");
	}
    }
    fprintf(PS.fp, "GR\n");

    return 0;
}

/** Process a vareas from line data */
int set_vareas_line(VECTOR * vec, VAREAS * va)
{
    int ret, cat;
    int ln, nlines, pt, npoints;
    double width;
    struct line_cats *lcats;
    struct line_pnts *lpoints;


    nlines = Vect_get_num_lines(&(vec->Map));

    fprintf(PS.fp, "GS 1 setlinejoin\n");	/* lines with linejoin = round */

    /* Create vector array, if required */
    if (vec->cats != NULL) {
	vec->Varray = Vect_new_varray(nlines);
	ret =
	    Vect_set_varray_from_cat_string(&(vec->Map), vec->layer,
					    vec->cats, GV_LINE, 1,
					    vec->Varray);
    }
    else if (vec->where != NULL) {
	vec->Varray = Vect_new_varray(nlines);
	ret =
	    Vect_set_varray_from_db(&(vec->Map), vec->layer, vec->where,
				    GV_LINE, 1, vec->Varray);
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

    /* read and plot lines */
    for (ln = 1; ln <= nlines; ln++) {
	ret = Vect_read_line(&(vec->Map), lpoints, lcats, ln);
	if (ret < 0)
	    continue;
	if (!(ret & GV_LINE))
	    continue;
	if (vec->Varray != NULL && vec->Varray->c[ln] == 0)
	    continue;

	/* Oops the line is correct, I can draw it */
	fprintf(PS.fp, "NP ");
	vector_area(lpoints, va->width * POINT_TO_MM / 1000. * PS.scale);
	fprintf(PS.fp, "CP\n");
	/* set the fill */
	if (!va->fcolor.none) {
	    fprintf(PS.fp, "GS %.2f O %.3f %.3f %.3f ",
		    va->fcolor.a, va->fcolor.r, va->fcolor.g, va->fcolor.b);
	    if (va->name_pat != NULL)
		fprintf(PS.fp, "PATTERN%d setpattern fill ", vec->id);
	    else
		fprintf(PS.fp, "C fill ");
	    fprintf(PS.fp, "GR ");
	}
	/* set the line style */
	if (va->line.width > 0. && !va->line.color.none) {
	    set_ps_line(&(va->line));
	    fprintf(PS.fp, "S\n");
	}
    }
    fprintf(PS.fp, "GR\n");
    return 0;
}
