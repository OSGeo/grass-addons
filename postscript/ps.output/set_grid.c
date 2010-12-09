/* File: set_grid.c
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
#include "grids.h"
#include "conversion.h"
#include "ps_info.h"
#include "local_proto.h"


/*
 * LINES OF THE GRATICULE
 */

int set_lines_grid(void)
{
    fprintf(PS.fp, "/XY {get aload pop exch pop} D\n");

    if (PS.grid.msep > 0) {
	set_grid_lines('m', &(PS.grid.mline), PS.grid.msep);
    }
    set_grid_lines('M', &(PS.grid.line), PS.grid.sep);
}

int set_grid_lines(char code, PSLINE * line, int grid_sep)
{
    char label[50], h;
    int i, x, y, zero, d, m;
    double sep, north, west, dx, dy, s;

    if (grid_sep <= 0)
	return 0;

    /* detect trailer zeros if format zero and not LL */
    zero = 1;
    if (PS.map.proj == PROJECTION_LL) {
	sep = (double)grid_sep / 3600.;
	/* break iho */
    }
    else {
	sep = (double)grid_sep;
	if (PS.grid.format < 2 && PS.grid.trim > 0) {
	    while (PS.grid.sep % zero == 0)
		zero *= 10;
	    if (zero > 1) {
		zero /= 10;
		for (i = 0, x = 1; i < PS.grid.trim; i++)
		    x *= 10;
		if (zero > x)
		    zero = x;
	    }
	}
    }

    /* vertical numbers */
    fprintf(PS.fp, "/VGR%c [\n", code);
    north = floor(PS.map.north / sep) * sep;
    for (; north >= PS.map.south; north -= sep) {
	G_plot_where_xy(PS.map.east, north, &x, &y);
	dy = ((double)y) / 10.;
	if (PS.grid.format == 2) {
	    format_iho(north, label);
	}
	else {
	    format_easting(north / zero, label, PS.map.proj);
	}
	fprintf(PS.fp, "[(%s) %.2f]\n", label, dy);
    }
    fprintf(PS.fp, "] def\n");

    /* horizontal numbers */
    fprintf(PS.fp, "/HGR%c [\n", code);
    west = ceil(PS.map.west / sep) * sep;
    for (; west < PS.map.east; west += sep) {
	G_plot_where_xy(west, PS.map.south, &x, &y);
	dx = ((double)x) / 10.;
	if (PS.grid.format == 2) {
	    format_iho(west, label);
	}
	else {
	    format_easting(west / zero, label, PS.map.proj);
	}
	fprintf(PS.fp, "[(%s) %.2f]\n", label, dx);
    }
    fprintf(PS.fp, "] def\n");


    if (line->color.none != 1) {
	set_ps_line(line);
	if (PS.grid.cross <= 0.) {	/* draw lines */
	    fprintf(PS.fp,
		    "VGR%c 0 1 2 index length -- {1 index exch XY "
		    "%.2f exch dup %.2f exch M LS} for pop\n", code, PS.map_x,
		    PS.map_right);
	    fprintf(PS.fp,
		    "HGR%c 0 1 2 index length -- {1 index exch XY "
		    "%.2f 1 index %.2f M LS} for pop\n", code, PS.map_y,
		    PS.map_top);
	}
	else {			/* draw crosses */

	    G_plot_where_xy(PS.map.east, PS.map.north, &x, &y);
	    dx = ((double)x) / 10.;
	    G_plot_where_xy(PS.map.east - PS.grid.cross, PS.map.north, &x,
			    &y);
	    dy = ((double)x) / 10.;

	    fprintf(PS.fp,
		    "VGR%c 0 1 2 index length -- {1 index exch XY "
		    "HGR%c 0 1 2 index length -- {1 index exch XY "
		    "2 index M 0 90 270 {GS ROT 0 %.2f LRS GR} for} "
		    "for pop pop} for pop\n", code, code, dx - dy);
	}
    }
    /* draw crosses como rotate una longitud desde el punto central */
    return 0;
}

/*
 * NUMBERS OF THE GRATICULE
 */

int set_numbers_grid(void)
{
    set_ps_color(&(PS.grid.fcolor));

    /* make numbers */
    switch (PS.grid.format) {
    case 0:
	set_ps_brd2(.2 * MM_TO_POINT, 0.);
	set_grid_inner_numbers();
	break;
    case 1:
	set_ps_brd2(.2 * MM_TO_POINT, 0.);
	if (PS.grid.msep > 0) {
	    if (PS.grid.msubdiv >= 0) {
		double mrga = 0.4 * PS.brd.width - .2 * MM_TO_POINT;
		double mrgb = 0.6 * PS.brd.width - .2 * MM_TO_POINT;

		set_grid_minordiv_border(PS.grid.msubdiv, .2 * MM_TO_POINT,
					 mrga);
		set_grid_minor_border(.2 * MM_TO_POINT + mrga, mrgb, mrgb);
	    }
	    else
		set_grid_minor_border(.2 * MM_TO_POINT,
				      PS.brd.width - .2 * MM_TO_POINT,
				      PS.brd.width);
	}
	set_grid_outer_numbers(2);
	break;
    case 2:
	set_ps_brd2(.2 * MM_TO_POINT, 0.);
	if (PS.grid.msep > 0) {
	    fprintf(PS.fp, "0.2 mm LW ");
	    set_grid_minordiv_border(PS.grid.msubdiv, 0.2 * MM_TO_POINT,
				     0.4 * MM_TO_POINT);
	    set_grid_minor_border(0.8 * MM_TO_POINT, 1.0 * MM_TO_POINT,
				  0.2 * MM_TO_POINT);
	    fprintf(PS.fp, "0.8 mm LW ");
	    set_grid_major_border(2.0 * MM_TO_POINT, 9.9 * MM_TO_POINT);
	    set_grid_iho_numbers(2.0 * MM_TO_POINT, 9.9 * MM_TO_POINT);
	}
	else {
	    fprintf(PS.fp, "0.8 mm LW ");
	    set_grid_major_border(0.2 * MM_TO_POINT, 11.7 * MM_TO_POINT);
	    set_grid_iho_numbers(0.2 * MM_TO_POINT, 11.7 * MM_TO_POINT);
	}
	break;
    case 3:
	fprintf(PS.fp, "0.005 inch LW ");
	set_grid_minordiv_border(PS.grid.msubdiv, 0.005 * INCH_TO_POINT,
				 0.035 * INCH_TO_POINT);
	if (PS.grid.msep > 0) {
	    set_grid_minor_border(0.045 * INCH_TO_POINT,
				  0.025 * INCH_TO_POINT,
				  0.025 * INCH_TO_POINT);
	}
	set_ps_brd(15.605 * MM_TO_POINT);
	set_ps_brd2(0.025 * INCH_TO_POINT, 17.3322 * MM_TO_POINT);
	set_grid_can_numbers(0.075 * INCH_TO_POINT, 13.7 * MM_TO_POINT);
	break;
    }
    return 1;
}


/* FORMAT 0: inner numbers */
int set_grid_inner_numbers(void)
{
    fprintf(PS.fp, "GS\n");
    fprintf(PS.fp, "/m %.3f def \n", 0.2 * PS.grid.font.size);

    set_ps_font(&(PS.grid.font));

    /* vertical numbers */
    fprintf(PS.fp, "0 1 VGRM length -- {VGRM exch GET %.2f exch M ",
	    PS.map_x);
    if (PS.grid.fcolor.none) {
	fprintf(PS.fp, ".2 mm .2 mm MR ");
    }
    else {
	fprintf(PS.fp,
		"dup SWH m 2 mul add exch m 1 add add exch "
		"dup 2 div neg 0 exch MR GS ");
	set_ps_color(&(PS.grid.fcolor));
	fprintf(PS.fp, "Rf GR 1 m MR ");
    }
    fprintf(PS.fp, "%s} for\n", (PS.grid.trim < 0 ? "COOR" : "SHL"));

    /* horizontal numbers */
    fprintf(PS.fp, "0 1 HGRM length -- {HGRM exch GET %.2f M ", PS.map_top);
    if (PS.grid.fcolor.none) {
	fprintf(PS.fp, "dup SW .5 add neg -.5 exch MR ");
    }
    else {
	fprintf(PS.fp,
		"dup SWH m 2 mul add exch m 1 add add "
		"1 index 2 div 1 index neg MR exch neg exch GS ");
	set_ps_color(&(PS.grid.fcolor));
	fprintf(PS.fp, "Rf GR m neg m MR ");
    }
    fprintf(PS.fp, "GS 90 ROT %s GR} for\n",
	    (PS.grid.trim < 0 ? "COOR" : "SHL"));

    fprintf(PS.fp, "GR\n");
    return 0;
}


/* FORMAT 1: outer numbers */
int set_grid_outer_numbers(int M)
{
    fprintf(PS.fp, "GS\n");

    set_ps_font(&(PS.grid.font));

    /* vertical numbers */
    fprintf(PS.fp, "0 1 VGRM length -- {VGRM exch GET %.2f exch M ",
	    PS.map_x);
    fprintf(PS.fp, "dup SW -2 div -%.2f exch MR ", PS.brd.width + M);
    fprintf(PS.fp, "GS 90 ROT %s GR} for\n",
	    (PS.grid.trim < 0 ? "COOR" : "SHL"));

    /* horizontal numbers */
    fprintf(PS.fp, "0 1 HGRM length -- {HGRM exch GET %.2f M ", PS.map_top);
    fprintf(PS.fp, "dup SW -2 div %.2f MR ", PS.brd.width + M);
    fprintf(PS.fp, "%s} for\n", (PS.grid.trim < 0 ? "COOR" : "SHL"));

    if (PS.grid.lsides == 4) {
	/* right vertical numbers */
	fprintf(PS.fp, "0 1 VGRM length -- {VGRM exch GET %.2f exch M ",
		PS.map_right);
	fprintf(PS.fp, "dup SW 2 div %.2f exch MR ", PS.brd.width + M);
	fprintf(PS.fp, "GS 270 ROT %s GR} for\n",
		(PS.grid.trim < 0 ? "COOR" : "SHL"));

	/* bottom horizontal numbers */
	fprintf(PS.fp, "0 1 HGRM length -- {HGRM exch GET %.2f M ", PS.map_y);
	fprintf(PS.fp, "dup SWH %.2f add neg exch -2 div exch MR ",
		PS.brd.width + M);
	fprintf(PS.fp, "%s} for\n", (PS.grid.trim < 0 ? "COOR" : "SHL"));
    }

    fprintf(PS.fp, "GR\n");
    return 0;
}

/* FORMAT 2: I.H.O. numbers */
int set_grid_iho_numbers(double A, double B)
{
    fprintf(PS.fp, "GS\n");

    set_ps_font(&(PS.grid.font));

    /* vertical numbers */
    fprintf(PS.fp, "0 1 VGRM length -- {VGRM exch GET %.2f exch M ",
	    PS.map_x - A - B / 2.);
    fprintf(PS.fp, " (|) search pop exch pop ");
    fprintf(PS.fp,
	    "GS 0 1.25 MR SHC GR GS FR dup SWH exch pop 1.25 add neg 0 exch MR SHC GR} for\n");

    /* right vertical numbers */
    fprintf(PS.fp, "0 1 VGRM length -- {VGRM exch GET %.2f exch M ",
	    PS.map_right + A + B / 2.);
    fprintf(PS.fp, " (|) search pop exch pop ");
    fprintf(PS.fp,
	    "GS 0 1.25 MR SHC GR GS FR dup SWH exch pop 1.25 add neg 0 exch MR SHC GR} for\n");

    /* horizontal numbers */
    fprintf(PS.fp, "0 1 HGRM length -- {HGRM exch GET %.2f M ",
	    PS.map_top + A + B / 2.);
    fprintf(PS.fp, " (|) search pop exch pop ");
    fprintf(PS.fp, "GS -1.25 0 MR SHRC GR GS FR 1.25 0 MR SHLC GR} for\n");

    /* bottom horizontal numbers */
    fprintf(PS.fp, "0 1 HGRM length -- {HGRM exch GET %.2f M ",
	    PS.map_y - A - B / 2.);
    fprintf(PS.fp, " (|) search pop exch pop ");
    fprintf(PS.fp, "GS -1.25 0 MR SHRC GR GS FR 1.25 0 MR SHLC GR} for\n");

    fprintf(PS.fp, "GR\n");
    return 0;
}

/* FORMAT 3: Canadian numbers */
int set_grid_can_numbers(double A, double B)
{
    fprintf(PS.fp, "GS\n");

    set_ps_font(&(PS.grid.font));

    /* vertical numbers */
    fprintf(PS.fp, "0 1 VGRM length -- {VGRM exch GET %.2f exch M ",
	    PS.map_x - A - B / 2.);
    fprintf(PS.fp, "dup SWH 2 div neg exch 2 div neg exch MR COOR} for\n");

    /* right vertical numbers */
    fprintf(PS.fp, "0 1 VGRM length -- {VGRM exch GET %.2f exch M ",
	    PS.map_right + A + B / 2.);
    fprintf(PS.fp, "dup SWH 2 div neg exch 2 div neg exch MR COOR} for\n");

    /* horizontal numbers */
    fprintf(PS.fp, "0 1 HGRM length -- {HGRM exch GET %.2f M ",
	    PS.map_top + A + B / 2.);
    fprintf(PS.fp, "dup SWH 2 div neg exch 2 div neg exch MR COOR} for\n");

    /* bottom horizontal numbers */
    fprintf(PS.fp, "0 1 HGRM length -- {HGRM exch GET %.2f M ",
	    PS.map_y - A - B / 2.);
    fprintf(PS.fp, "dup SWH 2 div neg exch 2 div neg exch MR COOR} for\n");

    fprintf(PS.fp, "GR\n");
    return 0;
}

/*
 * BORDER TYPES OF THE GRATICULE
 */

void set_grid_minordiv_border(int div, double margin, double width)
{
    fprintf(PS.fp, "%.2f %.2f %.2f %.2f RO\n", PS.map_x, PS.map_top + margin,
	    PS.map_w, width);

    fprintf(PS.fp, "%.2f %.2f %.2f %.2f RO\n", PS.map_x, PS.map_y - margin,
	    PS.map_w, -width);

    fprintf(PS.fp, "%.2f %.2f %.2f %.2f RO\n", PS.map_x - margin - width,
	    PS.map_y, width, PS.map_h);

    fprintf(PS.fp, "%.2f %.2f %.2f %.2f RO\n", PS.map_right + margin,
	    PS.map_y, width, PS.map_h);

    if (div > 0) {
	fprintf(PS.fp,
		"1 1 VGRm length -- {dup VGRm exch XY exch -- VGRm exch XY "
		"1 index sub %d div exch %d ++ {"
		"dup %.2f exch M %.2f 0 LR dup %.2f exch M %.2f 0 LR S "
		"1 index add} repeat pop pop} for ", div, div,
		PS.map_x - margin, -width, PS.map_right + margin, width);

	fprintf(PS.fp,
		"1 1 HGRm length -- {dup HGRm exch XY exch -- HGRm exch XY "
		"1 index sub %d div exch %d ++ {"
		"dup %.2f M 0 %.2f LR dup %.2f M 0 %.2f LR S "
		"1 index add} repeat pop pop} for ", div, div,
		PS.map_y - margin, -width, PS.map_top + margin, width);
    }
    if (div > 1) {
	fprintf(PS.fp,
		"VGRm 0 XY VGRm 1 XY 1 index sub neg %d div exch {"
		"1 index add dup %.2f gt {exit} {"
		"dup %.2f exch M %.2f 0 LR dup %.2f exch M %.2f 0 LR S "
		"} ifelse} loop ", div, PS.map_top, PS.map_x - margin, -width,
		PS.map_right + margin, width);

	fprintf(PS.fp,
		"/i VGRm length -- def VGRm i XY VGRm i -- XY 1 index sub neg %d div exch {"
		"1 index add dup %.2f lt {exit} {"
		"dup %.2f exch M %.2f 0 LR dup %.2f exch M %.2f 0 LR S "
		"} ifelse} loop ", div, PS.map_y, PS.map_x - margin, -width,
		PS.map_right + margin, width);


	fprintf(PS.fp,
		"HGRm 0 XY HGRm 1 XY 1 index sub neg %d div exch {"
		"1 index add dup %.2f lt {exit} {"
		"dup %.2f M 0 %.2f LR dup %.2f M 0 %.2f LR S "
		"} ifelse} loop ", div, PS.map_x, PS.map_y - margin, -width,
		PS.map_top + margin, width);

	fprintf(PS.fp,
		"/i HGRm length -- def HGRm i XY HGRm i -- XY 1 index sub neg %d div exch {"
		"1 index add dup %.2f gt {exit} {"
		"dup %.2f M 0 %.2f LR dup %.2f M 0 %.2f LR S "
		"} ifelse} loop\n", div, PS.map_right, PS.map_y - margin,
		-width, PS.map_top + margin, width);
    }
}

void set_grid_minor_border(double margin, double width, double midline)
{
    double dist;

    set_ps_brd(margin + width);
    set_grid_corners(0, margin + width);

    dist = margin + width / 2.;

    fprintf(PS.fp,
	    "0 1 VGRm length -- {VGRm exch XY dup "
	    "%.2f exch M %.2f 0 LR %.2f exch M %.2f 0 LRS} for\n",
	    PS.map_x - margin, -width, PS.map_right + margin, width);

    fprintf(PS.fp,
	    "0 1 HGRm length -- {HGRm exch XY dup "
	    "%.2f M %.2f 0 exch LR %.2f M %.2f 0 exch LRS} for\n",
	    PS.map_y - margin, -width, PS.map_top + margin, width);

    if (midline > 0) {
	fprintf(PS.fp, "GS %.2f LW ", midline);

	fprintf(PS.fp,
		"1 2 VGRm length -- {/i XD VGRm i XY VGRm i -- XY 2 copy "
		"%.2f exch M cP pop exch LS %.2f exch M cP pop exch LS} for\n",
		PS.map_x - dist, PS.map_right + dist);

	fprintf(PS.fp,
		"1 2 HGRm length -- {/i XD HGRm i XY HGRm i -- XY 2 copy "
		"%.2f M cP exch pop LS %.2f M cP exch pop LS} for\n",
		PS.map_y - dist, PS.map_top + dist);

	fprintf(PS.fp,
		"VGRm length 2 mod 0 ne {VGRm dup length -- XY %.2f 2 copy "
		"%.2f exch M cP pop exch LS %.2f exch M cP pop exch LS} if\n",
		PS.map_y, PS.map_x - dist, PS.map_right + dist);

	fprintf(PS.fp,
		"HGRm length 2 mod 0 ne {HGRm dup length -- XY %.2f 2 copy "
		"%.2f M cP exch pop LS %.2f M cP exch pop LS} if\n",
		PS.map_right, PS.map_y - dist, PS.map_top + dist);

	fprintf(PS.fp, "GR\n");
    }
}

void set_grid_major_border(double margin, double width)
{
    set_ps_brd(margin + width);

    fprintf(PS.fp, ".2 mm LW ");
    fprintf(PS.fp,
	    "0 1 VGRM length -- {VGRM exch XY dup "
	    "%.2f exch M %.2f 0 LR %.2f exch M %.2f 0 LR S} for\n",
	    PS.map_x - margin, -width, PS.map_right + margin, width);

    fprintf(PS.fp,
	    "0 1 HGRM length -- {HGRM exch XY dup "
	    "%.2f M %.2f 0 exch LR %.2f M %.2f 0 exch LR S} for\n",
	    PS.map_y - margin, -width, PS.map_top + margin, width);
}


void set_grid_corners(double margin, double width)
{
    fprintf(PS.fp, "%.2f cLW 2 div sub %.2f cLW 2 div sub M "
	    "%.2f dup 0 LR neg 0 exch LRS ", PS.map_x - margin - width,
	    PS.map_y - margin, width);

    fprintf(PS.fp, "%.2f cLW 2 div sub %.2f cLW 2 div add M "
	    "%.2f dup 0 LR 0 exch LRS ", PS.map_x - margin - width,
	    PS.map_top + margin, width);

    fprintf(PS.fp, "%.2f cLW 2 div add %.2f cLW 2 div sub M "
	    "%.2f neg dup 0 LR 0 exch LRS ", PS.map_right + margin + width,
	    PS.map_y - margin, width);

    fprintf(PS.fp, "%.2f cLW 2 div add %.2f cLW 2 div add M "
	    "%.2f dup neg 0 LR 0 exch LRS ", PS.map_right + margin + width,
	    PS.map_top + margin, width);
}
