/* File: set_rlegend.c
 *
 *  AUTHOR:    E. Jorge Tizado, Spain 2009
 *
 *  COPYRIGHT: (c) 2009 E. Jorge Tizado, and the GRASS Development Team
 *             This program is free software under the GNU General Public
 *             License (>=v2). Read the file COPYING that comes with GRASS
 *             for details.
 */

#include <grass/glocale.h>
#include "ps_info.h"
#include "raster.h"
#include "rlegend.h"
#include "local_proto.h"

static double nice_step(double, int, int *);


int set_rlegend_cats(void)
{
    int i, j, k, n, R, G, B;
    char *label;
    int num_cats, rows, cols;
    double fontsize, fwidth;
    DCELL dmin, dmax, val;

    /* Let user know what's happenning */
    G_message(_("Raster legend with category <%s in %s>..."), PS.rl.name,
	      PS.rl.mapset);

    /* Load the categories */
    if (G_read_raster_cats(PS.rl.name, PS.rl.mapset, &(PS.rst.cats)) != 0) {
	G_warning(_("Category file for <%s> not available"), PS.rl.name);
	return 1;
    }

    /* Reload colors if raster in rlegend is not the same as raster command.
       If the same, don't touch to not overwrite setcolor command */
    if (strcmp(PS.rl.name, PS.rst.name[0]) != 0) {
	G_warning("Using color table of %s in %s", PS.rl.name, PS.rl.mapset);
	if (G_read_colors(PS.rl.name, PS.rl.mapset, &PS.rst.colors[0]) == -1) {
	    G_warning("Can't load color table of %s in %s", PS.rl.name,
		      PS.rl.mapset);
	    return 1;
	}
	PS.rst.do_grey = 0;	/* Null grey because is not the same map as raster */
    }

    /* Sort categories by user (min value) */
    CELL *ip = (CELL *) G_malloc(sizeof(CELL) * PS.rst.cats.ncats);

    for (i = 0; i < PS.rst.cats.ncats; i++) {
	G_get_ith_d_raster_cat(&(PS.rst.cats), i, &dmin, &dmax);
	ip[i] = (CELL) dmin;
    }
    sort_list(PS.rl.cat_order, PS.rst.cats.ncats, &ip);

    /* How many categories to show */
    G_debug(3, "colortable: %d categories", num_cats);
    num_cats = PS.rst.cats.ncats;
    if (num_cats <= 0) {
	G_warning(_("Your cats/ file is invalid. A cats/ file with "
		    "categories and labels is required for 'colortable' when using "
		    "CELL rasters. No colortable will be assigned to this output "
		    "postscript file."));
	return 1;
    }
    else if (num_cats > 100) {
	G_warning(_("Your cats/ file has %d cats (limit to 100)!"), num_cats);
    }
    if (PS.rl.do_nodata)
	++num_cats;		/* slot for no_data */

    /* define number of rows */
    if (num_cats < PS.rl.legend.cols) {
	PS.rl.legend.cols = num_cats;
	rows = 1;
    }
    else {
	rows = (int)num_cats / PS.rl.legend.cols;
	if (num_cats % PS.rl.legend.cols)
	    ++rows;
    }
    cols = PS.rl.legend.cols;

    if (!PS.rl.do_nodata)
	++num_cats;		/* slot for no_data */

    /* set font */
    fontsize = set_ps_font(&(PS.rl.legend.font));

    /* Array of data */
    fprintf(PS.fp, "/ARh %d array def\n", rows);
    fprintf(PS.fp, "0 1 %d {ARh exch %.2f put} for\n", rows - 1, fontsize);

    fprintf(PS.fp, "/ARw %d array def\n", cols);
    i = PS.rl.do_nodata ? 0 : 1;
    for (n = 0; n < cols; n++) {
	fprintf(PS.fp, "/AR%d [\n", n);
	for (j = 0; j < rows && i < num_cats; j++, i++) {
	    /* labels */
	    if (i == 0) {
		fprintf(PS.fp, "(%s) ", "no data");
		G_get_null_value_color(&R, &G, &B, &(PS.rst.colors[0]));
		dmin = dmax = 0.;
	    }
	    else {
		label =
		    G_get_ith_d_raster_cat(&(PS.rst.cats), ip[i - 1], &dmin,
					   &dmax);
		fprintf(PS.fp, "(%s) ", label);
	    }
	    /* colors */
	    fprintf(PS.fp, "[");
	    if (dmin == dmax) {
		G_get_d_raster_color(&dmin, &R, &G, &B, &(PS.rst.colors[0]));
		fprintf(PS.fp, "%.3f %.3f %.3f", R / 255., G / 255.,
			B / 255.);
	    }
	    else {
		for (k = 0; k < 5; k++) {
		    val = dmin + (double)k *(dmax - dmin) / 5;

		    G_get_d_raster_color(&val, &R, &G, &B,
					 &(PS.rst.colors[0]));
		    fprintf(PS.fp, "%.3f %.3f %.3f ", R / 255., G / 255.,
			    B / 255.);
		}
	    }
	    fprintf(PS.fp, "]\n");
	}
	fprintf(PS.fp, "] def\n");
	fprintf(PS.fp, "/mx 0 def 0 2 AR%d length -- {", n);
	fprintf(PS.fp, "AR%d exch get SW /t XD t mx gt {/mx t def} if} for\n",
		n);
	fprintf(PS.fp, "ARw %d mx put\n", n);
    }

    G_free(ip);

    /* Adjust Legend Box */
    set_box_orig(&(PS.rl.legend.box));
    set_legend_adjust(&(PS.rl.legend), -1.);
    if (PS.rl.legend.title[0])
	fprintf(PS.fp, "(%s) READJUST ", PS.rl.legend.title);
    set_box_draw(&(PS.rl.legend.box));

    fwidth = .5;		/* basic linewidth */

    /* Make the raster legend */
    fprintf(PS.fp, "RESET %.5f LW\n", fwidth);
    fprintf(PS.fp, "/xw syw %.2f mul def ", 0.8);	/* symbol-width */
    fprintf(PS.fp, "/yh %.2f def ", -fontsize);	/* symbol-height */
    fprintf(PS.fp, "/t yh %d div def\n", 5);	/* gradient symbol-height, if any */
    for (n = 0; n < cols; n++) {
	fprintf(PS.fp, "%d COL 0 ROW\n", n);
	fprintf(PS.fp, "0 2 AR%d length -- {/i XD\n", n);
	fprintf(PS.fp, "x y -- xw yh\nAR%d i ++ get aload length 3 eq ", n);
	fprintf(PS.fp, "{%s 4 copy RF} ", PS.rst.do_grey ? "CG" : "C");
	fprintf(PS.fp,
		"{/z y def %d {C /z t add def x z xw t neg RF} repeat} ", 5);
	fprintf(PS.fp, "ifelse\n0 0 0 C RE\n");
	set_ps_color(&(PS.rl.legend.font.color));
	fprintf(PS.fp,
		"AR%d i get x syw add y ARh row get sub MS row 1 add ROW} for\n",
		n);
    }

    /* Make the title of legend */
    if (PS.rl.legend.title[0] != 0) {
	set_ps_font(&(PS.rl.legend.title_font));
	fprintf(PS.fp,
		"xo mgx add yo mgy mg sub sub M wd mgx 2 mul sub (%s) SHS\n",
		PS.rl.legend.title);
    }

    return 0;
}


int set_rlegend_gradient(void)
{
    int i, k, rows, nlines, dec;
    int R, G, B;
    DCELL dmin, dmax, val;
    double fontsize, step, fwidth;
    struct Colors colors;
    struct FPRange range;
    char *units[GNAME_MAX];
    char format[50];

    /* let user know what's happenning */
    G_message(_("Raster legend with gradient <%s in %s> ..."), PS.rl.name,
	      PS.rl.mapset);

    /* Get color range */
    if (G_read_fp_range(PS.rl.name, PS.rl.mapset, &range) == -1) {
	G_warning(_("Range information not available (run r.support)"));
	return 1;
    }

    /* range and check */
    if (PS.rl.custom_range) {
	dmin = PS.rl.min;
	dmax = PS.rl.max;
    }
    else {
	G_get_fp_range_min_max(&range, &dmin, &dmax);
	PS.rl.min = dmin;
	PS.rl.max = dmax;
    }

    if (dmin == dmax) {
	G_warning(_("It is not a range of values (max = min)"));
	return 1;
    }

    /* color table */
    if (G_read_colors(PS.rl.name, PS.rl.mapset, &colors) == -1) {
	G_warning(_("Unable to read colors for rlegend"));
    }

    /* units label */
    if (G_read_raster_units(PS.rl.name, PS.rl.mapset, (char *)units) != 0) {
	units[0] = 0;
    }

    /* initialize */
    fontsize = set_ps_font(&(PS.rl.legend.font));

    /* set standard height */
    if (PS.rl.height <= 0.) {
	PS.rl.height = 15. * fontsize;
	rows = 10;		/* = PS.rl.height / 1.5*fontsize */
    }
    else
	rows = (int)(PS.rl.height / (1.5 * fontsize));

    /* Nice step and first value as ps_fctltbl */
    step = nice_step(dmax - dmin, rows, &dec);
    val = step * (int)(dmin / step);
    if (val < dmin)
	val += step;

    /* Array of strings and widths */
    sprintf(format, "(%%.%df) %%.8f\n", dec);
    fprintf(PS.fp, "/AR0 [\n");
    while (val <= dmax) {
	fprintf(PS.fp, format, val, (dmax - val) / (dmax - dmin));
	val += step;
    }
    fprintf(PS.fp, "] def\n");
    fprintf(PS.fp, "/ARh 1 array def ARh 0 %.2f put\n", fontsize);
    fprintf(PS.fp, "/ARw 1 array def "
	    "/mx 0 def 0 2 AR0 length 1 sub {"
	    "AR0 exch get SW /t XD t mx gt {/mx t def} if } for "
	    "ARw 0 mx put\n");

    PS.rl.legend.xspan = 0.;	/* needed for auto adjust */

	/** Adjust - box legend */
    set_box_orig(&(PS.rl.legend.box));
    set_legend_adjust(&(PS.rl.legend), PS.rl.height);
    if (units[0] != 0)
	set_inner_readjust(-1., -1., -1., 0.8 * fontsize);
    set_box_draw(&(PS.rl.legend.box));

    fwidth = .5;

    nlines = (int)(PS.rl.height * 2.5);	/* = 2.5 * 72 = 180 ppp */
    step = (dmax - dmin) / nlines;

    /* Draw the labels */
    set_ps_color(&(PS.rl.legend.font.color));
    fprintf(PS.fp, "RESET %.3f LW /ch chg %.3f sub def\n", fwidth, fwidth);
    fprintf(PS.fp, "/x x syw %s add def ", (PS.rl.tickbar ? "++" : "2 add"));
    fprintf(PS.fp, "/y y %.3f sub def\n", fwidth / 2.);
    fprintf(PS.fp, "0 2 AR0 length -- {/i XD\n");
    fprintf(PS.fp, "x y ch AR0 i ++ get mul\n");
    if (PS.rl.tickbar) {
	fprintf(PS.fp, "GS ");
	fprintf(PS.fp, "3 copy sub ");
	fprintf(PS.fp, "NM -1 0 MR -%d 0 LR CS GR\n", PS.rl.tickbar);	/* length of tickbar */
    }
    /* Ajusta los extremos que no salgan de la barra */
    fprintf(PS.fp, "%.3f ", 0.6 * fontsize);	/* aprox part upper tickbar */
    fprintf(PS.fp,
	    "2 copy lt {2 div add}"
	    " {2 div add dup ch gt {pop ch} if} ifelse ");
    fprintf(PS.fp, "sub M AR0 i get show} for\n");

    /* Prepare the border and stroke area */
    fprintf(PS.fp, "RESET\n");
    fprintf(PS.fp, "/dy chg %d div def ", nlines);	/* dy: linewidth */
    fprintf(PS.fp, "/dx syw %d sub def\n", PS.rl.tickbar);	/* dx: barwidth, here, here */
    fprintf(PS.fp, "x y dx chg neg ");	/* to rectstroke */

    /* draw the colorbar and frame */
    fprintf(PS.fp, "dy 1.1 mul LW x y chg sub\n");	/* stack x and y */
    fprintf(PS.fp, "[\n");
    for (val = dmin; val <= dmax; val += step) {
	G_get_d_raster_color(&val, &R, &G, &B, &colors);
	if (PS.rst.do_grey)
	    fprintf(PS.fp, "[%.3f]\n",
		    (0.30 * (double)R + 0.59 * (double)G +
		     0.11 * (double)B) / 255.);
	else
	    fprintf(PS.fp, "[%.3f %.3f %.3f]\n", R / 255., G / 255.,
		    B / 255.);
    }
    fprintf(PS.fp, "] {aload pop %c 2 copy M dx 0 LR stroke dy add} forall\n",
	    PS.rst.do_grey ? 'G' : 'C');
    fprintf(PS.fp, "pop pop\n");
    fprintf(PS.fp, "GS 4 copy RC\n");
    if (PS.rl.whiteframe > 0.)	/* white border: print on colors */
	fprintf(PS.fp, "4 copy 1 1 1 C %d LW RE\n", PS.rl.whiteframe);
    fprintf(PS.fp, "GR ");
    set_ps_color(&(PS.rl.legend.font.color));
    fprintf(PS.fp, "%.5f LW RO\n", fwidth);

    /* print units label, if present */
    if (units[0]) {
	set_ps_color(&(PS.rl.legend.font.color));
	fprintf(PS.fp, "%.1f FS ", 0.8 * fontsize);
	fprintf(PS.fp, "RESET (%s) dup SW ", units);
	fprintf(PS.fp, "x cwd add exch sub y chg %.1f add sub MS\n",
		fontsize);
    }

    G_free_colors(&colors);

    return 0;
}

/* Extract from function ps_fcolortable
 * Author: Radim Blazek, leto 02
 */
static double nice_step(double diff, int cuts, int *cur_dec)
{
    int i, cur_step, dec;
    double nice_steps[4] = { 1.0, 2.0, 2.5, 5.0 };	/* nice steps */
    double step, ex, cur_d, cur_ex;

    step = diff / cuts;

    for (i = 0; i < 4; i++) {
	dec = 0;
	/* smalest n for which nice step >= raw step */
	if (nice_steps[i] <= step) {
	    ex = 1;
	    while (nice_steps[i] * ex < step)
		ex *= 10;
	}
	else {
	    ex = 0.1;
	    while (nice_steps[i] * ex > step) {
		++dec;
		ex *= 0.1;
	    }
	    ex *= 10;
	}
	if (i == 0 || (nice_steps[i] * ex - step) < cur_d) {
	    cur_step = i;
	    cur_d = nice_steps[i] * ex - step;
	    cur_ex = ex;
	    *cur_dec = dec;
	}
    }

    return nice_steps[cur_step] * cur_ex;
}
