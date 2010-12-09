/* Functions: symbol_save
 **
 ** Author: Radim Blazek
 ** Modified: E. Jorge Tizado
 */

#include <grass/Vect.h>
#include <grass/symbol.h>
#include "vpoints.h"
#include "ps_info.h"
#include "local_proto.h"

/* draw chain */
int draw_chain(SYMBCHAIN * chain, double s)
{
    int k, l;
    char *mvcmd;
    SYMBEL *elem;

    for (k = 0; k < chain->count; k++) {
	elem = chain->elem[k];
	switch (elem->type) {
	case S_LINE:
	    for (l = 0; l < elem->coor.line.count; l++) {
		if (k == 0 && l == 0)
		    mvcmd = "M";
		else
		    mvcmd = "L";
		fprintf(PS.fp, "%.4f %.4f %s\n", s * elem->coor.line.x[l],
			s * elem->coor.line.y[l], mvcmd);
	    }
	    break;
	case S_ARC:
	    if (elem->coor.arc.clock)
		mvcmd = "arcn";
	    else
		mvcmd = "arc";
	    fprintf(PS.fp, "%.4f %.4f %.4f %.4f %.4f %s\n",
		    s * elem->coor.arc.x,
		    s * elem->coor.arc.y, s * elem->coor.arc.r,
		    elem->coor.arc.a1, elem->coor.arc.a2, mvcmd);
	    break;
	}
    }

    return 0;
}

/* store symbol in PS file, scaled to final size and drawn with final colors */
int symbol_save(int code, VPOINTS * vp, SYMBOL * Symb)
{
    SYMBPART *part;
    SYMBCHAIN *chain;
    int i, j, points;
    double s, xo[4], yo[4];

    points = 4;
    xo[0] = 0.0;
    yo[0] = 0.5;
    xo[1] = -0.5;
    yo[1] = 0.0;
    xo[2] = 0.0;
    yo[2] = -0.5;
    xo[3] = 0.5;
    yo[3] = 0.0;

    s = 1;

    fprintf(PS.fp, "/SYMBOL%d {\n", code);

    s *= Symb->scale;
    for (i = 0; i < Symb->count; i++) {
	part = Symb->part[i];
	switch (part->type) {
	case S_POLYGON:
	    fprintf(PS.fp, "NP\n");	/* Start ring */
	    for (j = 0; j < part->count; j++) {	/* RINGS */
		chain = part->chain[j];
		draw_chain(chain, s);
		fprintf(PS.fp, "CP\n");	/* Close one ring */
	    }
	    /* Fill */
	    if (part->fcolor.color == S_COL_DEFAULT && !vp->fcolor.none) {
		set_ps_color(&(vp->fcolor));
		fprintf(PS.fp, "F\n");	/* Fill polygon */
	    }
	    else if (part->fcolor.color == S_COL_DEFINED) {
		fprintf(PS.fp, "%.3f %.3f %.3f C ", part->fcolor.fr,
			part->fcolor.fg, part->fcolor.fb);
		fprintf(PS.fp, "F\n");
	    }
	    /* Outline */
	    if (part->color.color == S_COL_DEFAULT && !vp->line.color.none) {
		set_ps_color(&(vp->line.color));
		fprintf(PS.fp, "S\n");	/* Draw boundary */
	    }
	    else if (part->color.color == S_COL_DEFINED) {
		fprintf(PS.fp, "%.3f %.3f %.3f C ", part->color.fr,
			part->color.fg, part->color.fb);
		fprintf(PS.fp, "S\n");
	    }
	    break;
	case S_STRING:		/* string has 1 chain */
	    if (part->color.color != S_COL_NONE) {
		fprintf(PS.fp, "NP\n");
		chain = part->chain[0];
		draw_chain(chain, s);
		/* Color */
		if (part->color.color == S_COL_DEFAULT &&
		    !vp->line.color.none) {
		    set_ps_color(&(vp->line.color));
		    fprintf(PS.fp, "S\n");
		}
		else {
		    fprintf(PS.fp, "%.3f %.3f %.3f C ", part->color.fr,
			    part->color.fg, part->color.fb);
		    fprintf(PS.fp, "S\n");
		}
	    }
	    break;
	}
    }
    fprintf(PS.fp, "} def\n");

    return 0;
}
