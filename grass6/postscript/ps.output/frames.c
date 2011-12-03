/* File: frames.c
 *
 *  AUTHOR:    E. Jorge Tizado, Spain 2009
 *
 *  COPYRIGHT: (c) 2009 E. Jorge Tizado, and the GRASS Development Team
 *             This program is free software under the GNU General Public
 *             License (>=v2). Read the file COPYING that comes with GRASS
 *             for details.
 */

#include "frames.h"
#include "ps_info.h"
#include "local_proto.h"


/* Postscipt variables: -- */
void set_box_orig(PSFRAME * box)
{
    double x, y;

    if (box->x <= 0.0) {
	box->x = PS.map_x - PS.map_w * (box->x / 100.);
    }
    /*
       else {
       box->x = 0 + box->x;
       }
     */
    if (box->y <= 0.0) {
	box->y = PS.map_y - PS.map_h * (box->y / 100.);
    }
    else {
	box->y = PS.page.height - box->y;
    }
}

/* Postscript variables: mg hg chg wd cwd  */
void set_box_size(PSFRAME * box, double width, double height)
{
    /* Margin "mg" */
    if (box->margin < 0.)
	box->margin = 0.;
    fprintf(PS.fp, "/mg %.4f def\n", box->margin);

    /* Height "hg" and content height "chg" */
    if (height > 0.) {
	fprintf(PS.fp, "/hg %.4f def\n", height);	/* height */
	fprintf(PS.fp, "/chg hg mg 2 mul sub def\n");	/* content height */
    }

    /* Width "wd" and content width "cwd" */
    if (width > 0.) {
	fprintf(PS.fp, "/wd %.4f def\n", width);	/* width */
	fprintf(PS.fp, "/cwd wd mg 2 mul sub def\n");	/* content width */
    }
}

/* Draw the box with outer border: xo yo */
void set_box_draw(PSFRAME * box)
{
    /* Re-location */
    if (box->xref == RIGHT)
	fprintf(PS.fp, "/xo %.4f wd sub def\n", box->x + box->xset);
    else if (box->xref == CENTER)
	fprintf(PS.fp, "/xo %.4f wd 2 div sub def\n", box->x + box->xset);
    else
	fprintf(PS.fp, "/xo %.4f def\n", box->x + box->xset);

    if (box->yref == LOWER)
	fprintf(PS.fp, "/yo %.4f hg add def\n", box->y + box->yset);
    else if (box->yref == CENTER)
	fprintf(PS.fp, "/yo %.4f hg 2 div add def\n", box->y + box->yset);
    else
	fprintf(PS.fp, "/yo %.4f def\n", box->y + box->yset);

    /* Make color background, if set */
    if (!box->fcolor.none) {
	set_ps_color(&(box->fcolor));
	fprintf(PS.fp, "xo yo wd hg neg RF\n");
    }
    /* Draw the border, if set */
    if (box->border > 0.) {
	set_ps_color(&(box->color));
	fprintf(PS.fp, "%.4f LW xo yo wd hg neg RO\n", box->border);
    }
}


/* Postscript auto size with ARh y ARw */
void set_box_auto(PSFRAME * box, PSFONT * font, double factor)
{
    if (factor <= 0.)
	factor = 0.5;		/* standard row height by fontsize */

    /* Initialize */
    if (box->margin < 0.)
	box->margin = 0.4 * font->size;

    /* Margins "mg", 'mgx', 'mgy' */
    fprintf(PS.fp, "/mg %.8f def\n", box->margin);
    fprintf(PS.fp, "/mgx mg def /mgy mg def\n");

    /* Height "hg", content height "chg", and interline "dy" */
    fprintf(PS.fp, "/dy %.4f def\n", factor * font->size);	/* standard row sep */
    fprintf(PS.fp, "/chg dy neg ARh {add dy add} forall def\n");	/* content height */
    fprintf(PS.fp, "/hg chg mg 2 mul add def\n");	/* height */

    /* Width "wd", content width "cwd", and intercolum "dx" */
    fprintf(PS.fp, "/dx mg def\n");	/* standard col sep */
    fprintf(PS.fp, "/cwd dx neg ARw {add dx add} forall def\n");	/* content width */
    fprintf(PS.fp, "/wd cwd mg 2 mul add def\n");	/* width */
}

/* INNER ONLY ADJUST */
/* Readjust the size of a box with new margins */
void set_inner_readjust(double left, double top, double width, double height)
{
    if (left > 0.) {
	if (width >= 0.)
	    width += left;
	else
	    width = left;
	fprintf(PS.fp, "/mgx mg %.4f add def\n", left);
    }
    if (top > 0.) {
	if (height >= 0.)
	    height += top;
	else
	    height = top;
	fprintf(PS.fp, "/mgy mg %.4f add def\n", top);
    }
    if (height > 0.) {
	fprintf(PS.fp, "/hg hg %.4f add def\n", height);
    }
    if (width > 0.) {
	fprintf(PS.fp, "/wd wd %.4f add def\n", width);
    }
}
