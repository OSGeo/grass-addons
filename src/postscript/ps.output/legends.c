/* File: legends.c
 *
 *  AUTHOR:    E. Jorge Tizado, Spain 2009
 *
 *  COPYRIGHT: (c) 2009 E. Jorge Tizado, and the GRASS Development Team
 *             This program is free software under the GNU General Public
 *             License (>=v2). Read the file COPYING that comes with GRASS
 *             for details.
 */

#include "ps_info.h"
#include "legends.h"
#include "local_proto.h"


void set_legend_adjust(LEGEND * legend, double height)
{
    /* Initialize */
    if (legend->box.margin < 0.)
	legend->box.margin = 0.4 * legend->font.size;

    if (legend->width < 0.)
	legend->width = 2.4 * legend->font.size;

    /* Margins "mg", "mgx" and "mgy" */
    fprintf(PS.fp, "/mg %.5f def\n", legend->box.margin);	/* inner box margin */
    fprintf(PS.fp, "/mgx mg def\n");	/* to RESET and COL */
    fprintf(PS.fp, "/mgy mg def\n");	/* to RESET and ROW */

    /* Symbol width "syw" and adding to all width columns */
    fprintf(PS.fp, "/syw %.5f def\n", legend->width);	/* symbol width */
    fprintf(PS.fp,
	    "0 1 ARw length -- {ARw exch dup ARw exch get syw add put} for\n");

    /* Height "hg", content height "chg", and interline "dy" */
    if (height > 0.) {
	fprintf(PS.fp, "/hg %.5f def\n", height);	/* height */
	fprintf(PS.fp, "/chg hg mg 2 mul sub def\n");	/* content height */
	fprintf(PS.fp, "/dy ARh length 1 eq {0} {chg ARh {sub} forall ARh length -- div} ifelse def\n");	/* rowsep */
    }
    else {
	fprintf(PS.fp, "/dy %.5f def\n", .5 * legend->font.size);	/* standard row sep */
	fprintf(PS.fp, "/chg dy neg ARh {add dy add} forall def\n");	/* content height */
	fprintf(PS.fp, "/hg chg mg 2 mul add def\n");	/* height */
    }

    /* Width "wd", content width "cwd", and colspan "dx" */
    if (legend->xspan < 0.) {	/* auto-adjust */
	fprintf(PS.fp, "/wd %.5f def ", -(PS.map_w * legend->xspan));	/* width */
	fprintf(PS.fp, "/cwd wd mg 2 mul sub def\n");	/* content width */
	fprintf(PS.fp, "/dx ARw length 1 eq {0} {cwd ARw {sub} forall ARw length -- div} ifelse def\n");	/* colspan */
    }
    else {
	if (legend->xspan == 0.)
	    legend->xspan = legend->box.margin;
	fprintf(PS.fp, "/dx %.4f def\n", legend->xspan);	/* colspan */
	fprintf(PS.fp, "/cwd dx neg ARw {add dx add} forall def\n");	/* content width */
	fprintf(PS.fp, "/wd cwd mg 2 mul add def\n");	/* width */
    }
}
