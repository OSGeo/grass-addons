/* File: set_vpoints.c
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


/** Process a vector of lines */
int set_vpoints(VECTOR * vec, VPOINTS * vp)
{
    int ret, cat;
    int pt, npoints;
    double tmp, size, rotate;
    struct line_cats *lcats;
    struct line_pnts *lpoints;

    npoints = Vect_get_num_lines(&(vec->Map));

    /* Create vector array, if required */
    if (vec->cats != NULL) {
	vec->Varray = Vect_new_varray(npoints);
	Vect_set_varray_from_cat_string(&(vec->Map), vec->layer, vec->cats,
					vp->type, 1, vec->Varray);
    }
    else if (vec->where != NULL) {
	vec->Varray = Vect_new_varray(npoints);
	Vect_set_varray_from_db(&(vec->Map), vec->layer, vec->where, vp->type,
				1, vec->Varray);
    }
    else
	vec->Varray = NULL;

    /* memory for coordinates */
    lcats = Vect_new_cats_struct();
    lpoints = Vect_new_line_struct();

    /* load attributes if any */
    dbCatValArray sizecv, rotcv;

    if (vp->rotatecol != NULL) {
	load_catval_array(&(vec->Map), vp->rotatecol, &rotcv);
    }
    if (vp->sizecol != NULL) {
	load_catval_array(&(vec->Map), vp->sizecol, &sizecv);
    }

    /* read and plot lines */
    for (pt = 1; pt <= npoints; pt++) {
	ret = Vect_read_line(&(vec->Map), lpoints, lcats, pt);
	if (ret < 0)
	    continue;
	if (!(ret & GV_POINTS) || !(ret & vp->type))
	    continue;
	if (vec->Varray != NULL && vec->Varray->c[pt] == 0)
	    continue;
	/* Is it inside area? */
	int x, y;

	G_plot_where_xy(lpoints->x[0], lpoints->y[0], &x, &y);
	PS.x = (double)x / 10.;
	PS.y = (double)y / 10.;
	if (PS.x < PS.map_x || PS.x > PS.map_right || PS.y < PS.map_y ||
	    PS.y > PS.map_top)
	    continue;
	/* Oops the point is correct, I can draw it */
	Vect_cat_get(lcats, 1, &cat);
	fprintf(PS.fp, "GS ");
	fprintf(PS.fp, "%.4f %.4f TR ", PS.x, PS.y);
	/* symbol size */
	if (vp->sizecol == NULL) {
	    size = vp->size;
	}
	else {
	    get_number(&sizecv, cat, &tmp);
	    size = tmp * vp->scale + vp->bias;
	    if (vec->n_rule == 0) {
		vector_item_new(vec, tmp, (long)(vp->size * 1000.));
	    }
	    else {
		int i;

		i = vector_item_new(vec, tmp, (long)(size * 1000.));
		if (vec->item[i].rule != -1)
		    size = vec->rule[vec->item[i].rule].value;
	    }
	}
	if (size <= 0.)
	    continue;
	fprintf(PS.fp, "%.3f dup SC ", size);

	/* symbol rotate */
	if (vp->rotatecol == NULL) {
	    rotate = vp->rotate;
	}
	else {
	    get_number(&rotcv, cat, &rotate);
	}
	if (rotate > 0.)
	    fprintf(PS.fp, "%.3f ROT ", rotate);

	/* symbol line */
	fprintf(PS.fp, "%.3f LW SYMBOL%d ", (vp->line.width) / size, vec->id);
	fprintf(PS.fp, "GR\n");
    }

    return 0;
}

/** Process a vpoints with join lines */
int set_vpoints_line(VECTOR * vec, VPOINTS * vp)
{
    int ret, cat;
    double size, rotate;
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
					    vec->cats, vp->type, 1,
					    vec->Varray);
    }
    else if (vec->where != NULL) {
	vec->Varray = Vect_new_varray(nlines);
	ret =
	    Vect_set_varray_from_db(&(vec->Map), vec->layer, vec->where,
				    vp->type, 1, vec->Varray);
    }
    else
	vec->Varray = NULL;

    /* memory for coordinates */
    lcats = Vect_new_cats_struct();
    lpoints = Vect_new_line_struct();

    /* process only vectors in current window */
    Vect_set_constraint_region(&(vec->Map),
			       PS.map.north, PS.map.south, PS.map.east,
			       PS.map.west, PORT_DOUBLE_MAX,
			       -PORT_DOUBLE_MAX);

    /* prepare the symbol to draw */
    /* load attributes if any */
    dbCatValArray cv_size, cv_rot;

    if (vp->sizecol != NULL) {
	load_catval_array(&(vec->Map), vp->sizecol, &cv_size);
    }
    if (vp->rotatecol != NULL) {
	load_catval_array(&(vec->Map), vp->rotatecol, &cv_rot);
    }
    fprintf(PS.fp, "/LSYMBOL {GS %.3f TR [] 0 LD ", vp->voffset);
    /* symbol size */
    if (vp->sizecol == NULL) {
	size = vp->size;
    }
    else {
	get_number(&cv_size, cat, &size);
	size *= vp->scale;
    }
    if (size > 0.)
	fprintf(PS.fp, "%.3f dup SC ", size);
    /* symbol rotate */
    if (vp->rotatecol == NULL) {
	rotate = vp->rotate;
    }
    else {
	get_number(&cv_rot, cat, &rotate);
    }
    if (rotate > 0.)
	fprintf(PS.fp, "%.3f ROT ", rotate);
    /* symbol line */
    if (size == 0.)
	size = 1.;		/* avoid division by zero */
    fprintf(PS.fp, "%.3f LW SYMBOL%d ", (vp->line.width) / size, vec->id);
    fprintf(PS.fp, "GR} def\n");

    /* read and plot lines */
    for (ln = 1; ln <= nlines; ln++) {
	ret = Vect_read_line(&(vec->Map), lpoints, lcats, ln);
	if (ret < 0)
	    continue;
	if (!(ret & GV_LINES) || !(ret & vp->type))
	    continue;
	if (vec->Varray != NULL && vec->Varray->c[ln] == 0)
	    continue;
	/* Oops the line is correct, I can draw the conection */
	vector_line(lpoints);
	set_ps_color(&(vp->cline.color));
	set_ps_line_no_color(&(vp->cline));
	/* well, now go to draw the symbols */
	fprintf(PS.fp, "\n/inc %.2f def mark ", vp->distance);
	fprintf(PS.fp, "\n"
		"{/cy XD /cx XD cx cy M /ovr inc 2 div def}"
		"{/ly XD /lx XD /dy ly cy sub def /dx lx cx sub def "
		"/dist dx dup mul dy dup mul add sqrt def "
		"dist 0 ne {mark /nx 0 def "
		"/i ovr neg def inc dup ovr sub exch dist {/i XD i nx ++ /nx XD} for /ovr dist i sub def "
		"nx 0 gt {nx dx 0 eq {dy 0 lt {270} {90} ifelse} {dy dx atan} ifelse cx cy ]} {pop} ifelse "
		"/cx lx def /cy ly def cx cy M} if}"
		"{curveto} {closepath} pathforall S "
		"counttomark {aload pop GS TR ROT {LSYMBOL} repeat GR} repeat pop\n");
    }
    fprintf(PS.fp, "GR\n");
    return 0;
}
