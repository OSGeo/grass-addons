/* File: set_vector.c
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

int set_vector(int masked, int type)
{
    int i;
    char buf[1024];

    for (i = PS.vct_files - 1; i >= 0; i--) {
	if (masked && !PS.vct[i].masked) {
	    continue;
	}
	if (!masked && PS.vct[i].masked) {
	    continue;
	}
	if (PS.vct[i].type != type) {
	    continue;
	}
	/* select the type of output, NONE: no draw anything */
	if (PS.vct[i].type == AREAS) {
	    VAREAS *va = (VAREAS *) PS.vct[i].data;

	    if (va->name_pat != NULL) {
		set_ps_pattern(PS.vct[i].id, va->name_pat, va);
	    }
	    if (va->width != 0.) {
		set_vareas_line(&(PS.vct[i]), va);
	    }
	    else {
		set_vareas(&(PS.vct[i]), va);
	    }
	}
	else if (PS.vct[i].type == LABELS) {
	    VLABELS *vl = (VLABELS *) PS.vct[i].data;

	    set_vlabels(&(PS.vct[i]), vl);
	}
	else if (PS.vct[i].type == LINES) {
	    VLINES *vl = (VLINES *) PS.vct[i].data;

	    if (vl->hline.width > 0 && !(vl->hline.color.none)) {
		set_vlines(&(PS.vct[i]), vl, DRAW_HLINE);
		Vect_rewind(&(PS.vct[i].Map));
	    }
	    set_vlines(&(PS.vct[i]), vl, DRAW_LINE);
	}
	else if (PS.vct[i].type == POINTS) {
	    SYMBOL *symb;
	    VPOINTS *vp = (VPOINTS *) PS.vct[i].data;

	    symb = S_read(vp->symbol);
	    if (symb != NULL) {
		symbol_save(PS.vct[i].id, vp, symb);
	    }
	    else {
		set_ps_symbol_eps(PS.vct[i].id, vp->symbol);
	    }
	    if (vp->distance > 0.)
		set_vpoints_line(&(PS.vct[i]), vp);
	    else
		set_vpoints(&(PS.vct[i]), vp);
	}
    }

    return 0;
}
