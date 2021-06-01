/* File: set_geogrid.c
 *
 *  AUTHOR:    E. Jorge Tizado, Spain 2009
 *
 *  COPYRIGHT: (c) 2009 E. Jorge Tizado, and the GRASS Development Team
 *             This program is free software under the GNU General Public
 *             License (>=v2). Read the file COPYING that comes with GRASS
 *             for details.
 */

#include <string.h>
#include <math.h>
#include <grass/gis.h>
#include <grass/glocale.h>
#include <grass/gprojects.h>
#include "grids.h"
#include "ps_info.h"
#include "local_proto.h"


/*
 * LINES OF THE GEOGRID
 */

int set_lines_geogrid(void)
{
    /* make lines */
    set_geogrid_lines(&(PS.geogrid.mline), PS.geogrid.msep);
    set_geogrid_lines(&(PS.geogrid.line), PS.geogrid.sep);

    return 1;
}

int set_geogrid_lines(PSLINE * line, int grid_sep)
{
    double sep, n_min, nmin, e_min, emin;
    double e, n, east, west, north, south;
    struct pj_info ll_proj, proj;

    if (PS.geogrid.sep <= 0 || PS.geogrid.line.color.none)
	return 0;

    fprintf(PS.fp, "GS\n");
    /* set color and set line width */
    set_ps_line(line);

    sep = (double)grid_sep / 3600.;	/* to degrees */

    /* preparing projections */
    init_proj(&ll_proj, &proj);
    find_limits(&north, &south, &east, &west, &ll_proj, &proj);
    n_min = ceil(north / sep) * sep;
    e_min = ceil(east / sep) * sep;

    /* latitude lines */
    for (nmin = n_min; nmin >= south; nmin -= sep) {
	for (emin = e_min; emin >= west; emin -= sep) {
	    e = emin;
	    n = nmin;
	    pj_do_proj(&e, &n, &ll_proj, &proj);	/* LL to PROJ */
	    set_ps_where('M', e, n);	/* PROJ to XY */
	    e = emin - sep;
	    n = nmin;
	    pj_do_proj(&e, &n, &ll_proj, &proj);
	    set_ps_where('L', e, n);
	    fprintf(PS.fp, "S\n");
	}
    }
    /* longitude lines */
    for (emin = e_min; emin >= west; emin -= sep) {
	for (nmin = n_min; nmin >= south; nmin -= sep) {
	    e = emin;
	    n = nmin;
	    pj_do_proj(&e, &n, &ll_proj, &proj);
	    set_ps_where('M', e, n);
	    e = emin;
	    n = nmin - sep;
	    pj_do_proj(&e, &n, &ll_proj, &proj);
	    set_ps_where('L', e, n);
	    fprintf(PS.fp, "S\n");
	}
    }

    fprintf(PS.fp, "GR\n");
    return 0;
}


/* select type of number presentation */
int set_numbers_geogrid(void)
{
    char label[50];
    int i, x, y;
    double dx, dy;
    double grid_sep, nmin, emin, dif;
    double e, n, east, west, north, south;
    struct pj_info ll_proj, proj;

    if (PS.geogrid.sep <= 0)
	return 1;

    grid_sep = (double)PS.geogrid.sep / 3600.;	/* to degrees */

    /* preparing projections */
    init_proj(&ll_proj, &proj);
    find_limits(&north, &south, &east, &west, &ll_proj, &proj);

    /* printf("North %f  South %f\n", north, south); */
    /* printf("West %f  East %f\n", west, east); */

    /* vertical-right numbers */
    fprintf(PS.fp, "/GRR [\n");
    nmin = floor(north / grid_sep) * grid_sep;
    for (; nmin > south; nmin -= grid_sep) {
	e = east;
	n = nmin;
	pj_do_proj(&e, &n, &ll_proj, &proj);
	e = PS.map.east;
	pj_do_proj(&e, &n, &proj, &ll_proj);
	n = nmin;
	pj_do_proj(&e, &n, &ll_proj, &proj);
	if (n > PS.map.north || n < PS.map.south)
	    continue;
	G_plot_where_xy(PS.map.east, n, &x, &y);
	dx = ((double)x) / 10.;
	dy = ((double)y) / 10.;
	format_northing(nmin, label, PROJECTION_LL);
	fprintf(PS.fp, "[(%s) %.1f %.1f]\n", label, dx, dy);
    }
    fprintf(PS.fp, "] def\n");

    /* horizontal-bottom numbers */
    fprintf(PS.fp, "/GRB [\n");
    emin = floor(east / grid_sep) * grid_sep;
    for (; emin > west; emin -= grid_sep) {
	n = south;
	e = emin;
	pj_do_proj(&e, &n, &ll_proj, &proj);
	n = PS.map.south;
	pj_do_proj(&e, &n, &proj, &ll_proj);
	e = emin;
	pj_do_proj(&e, &n, &ll_proj, &proj);
	if (e > PS.map.east || e < PS.map.west)
	    continue;
	G_plot_where_xy(e, PS.map.south, &x, &y);
	dx = ((double)x) / 10.;
	dy = ((double)y) / 10.;
	format_easting(emin, label, PROJECTION_LL);
	fprintf(PS.fp, "[(%s) %.1f %.1f]\n", label, dx, dy);
    }
    fprintf(PS.fp, "] def\n");

    /* select format */
    switch (PS.geogrid.format) {
    case 0:
	set_geogrid_inner_numbers();
	break;
    case 1:
	set_geogrid_outer_numbers();
	break;
    }
    return 1;
}


/* geogrid with inner numbers */
int set_geogrid_inner_numbers(void)
{
    fprintf(PS.fp, "GS ");
    set_ps_font(&(PS.geogrid.font));
    fprintf(PS.fp, "/m %.3f def \n", 0.2 * PS.geogrid.font.size);

    /* vertical numbers */
    fprintf(PS.fp, "0 1 GRR length -- {GRR exch GET M dup ");
    set_ps_color(&(PS.geogrid.fcolor));
    if (PS.geogrid.fcolor.none)
	fprintf(PS.fp, "SW .5 add neg .5 MR ");
    else
	fprintf(PS.fp,
		"SWH m 2 mul add 1 index m 1 add add neg "
		"exch dup -2 div 0 exch MR Rf ++ neg m MR ");
    set_ps_color(&(PS.geogrid.font.color));
    fprintf(PS.fp, "%s} for\n", (PS.geogrid.trim < 0 ? "COOR" : "SHL"));

    /* horizontal numbers */
    fprintf(PS.fp, "0 1 GRB length -- {GRB exch GET M dup ");
    set_ps_color(&(PS.geogrid.fcolor));
    if (PS.geogrid.fcolor.none)
	fprintf(PS.fp, "pop -.5 .5 MR ");
    else
	fprintf(PS.fp,
		"SWH m 2 mul add exch m 1 add add 1 index -2 div 0 MR "
		"1 index exch Rf m sub 1 MR ");
    set_ps_color(&(PS.geogrid.font.color));
    fprintf(PS.fp, "GS 90 ROT %s GR} for\n",
	    (PS.geogrid.trim < 0 ? "COOR" : "SHL"));

    fprintf(PS.fp, "GR\n");
    return 0;
}

/* geogrid with outer numbers */
int set_geogrid_outer_numbers(void)
{
    fprintf(PS.fp, "GS ");
    set_ps_font(&(PS.geogrid.font));

    /* vertical numbers */
    fprintf(PS.fp,
	    "0 1 GRR length -- {GRR exch GET M dup "
	    "SW 2 div %.2f exch MR GS 270 ROT %s GR} for ", PS.brd.width + 1.,
	    (PS.geogrid.trim < 0 ? "COOR" : "SHL"));

    /* horizontal numbers */
    fprintf(PS.fp,
	    "0 1 GRB length -- {GRB exch GET M dup "
	    "SWH %.2f add neg exch -2 div exch MR %s} for ",
	    PS.brd.width + 1., (PS.geogrid.trim < 0 ? "COOR" : "SHL"));

    fprintf(PS.fp, "GR\n");
    return 0;
}
