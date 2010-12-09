/*
 * File: set_vlegend.c AUTHOR: E. Jorge Tizado, Spain 2009 COPYRIGHT:
 * (c) 2009 E. Jorge Tizado, and the GRASS Development Team This program
 * is free software under the GNU General Public License (>=v2). Read the
 * file COPYING that comes with GRASS for details.
 */

#include "vlegend.h"
#include "ps_info.h"
#include "local_proto.h"
#include "vector.h"


int cmpitems(const void *i1, const void *i2)
{
    if (((ITEMS *) i1)->rule < ((ITEMS *) i2)->rule)
	return -1;
    else if (((ITEMS *) i1)->rule > ((ITEMS *) i2)->rule)
	return 1;
    else
	return 0;
}

int set_vlegend()
{
    int i, j, n_vct;

    G_debug(1, "Placing vlegend ...");

    /* How many vectors to draw? */
    for (n_vct = 0, i = 0; i < PS.vct_files; i++) {
	if (PS.vct[i].lpos >= 0)
	    ++n_vct;
    }
    if (n_vct == 0)
	return 1;

    /* Reorder as defined by the user */
    int *ip = (int *)G_malloc(n_vct * sizeof(int));

    for (i = 0; i < n_vct; i++) {
	ip[i] = -1;
    }
    for (i = 0; i < PS.vct_files; i++) {
	if (PS.vct[i].lpos > 0) {
	    j = PS.vct[i].lpos - 1;
	    if (j < n_vct && ip[j] < 0) {
		ip[j] = i;
		PS.vct[i].lpos = -1;
	    }
	    else
		PS.vct[i].lpos = 0;
	}
    }
    for (i = 0; i < PS.vct_files; i++) {
	if (PS.vct[i].lpos == 0) {
	    j = 0;
	    while (j < n_vct && ip[j] >= 0)
		j++;
	    if (j < n_vct)
		ip[j] = i;
	}
    }

    /* Use default values to undefined variables */
    if (PS.vl.legend.box.margin < 0.)
	PS.vl.legend.box.margin = 0.4 * PS.vl.legend.font.size;

    if (PS.vl.legend.width <= 0)
	PS.vl.legend.width = 2.4 * PS.vl.legend.font.size;

    if (PS.vl.legend.xspan <= 0)
	PS.vl.legend.xspan = PS.vl.legend.box.margin;

    if (PS.vl.legend.yspan <= 0)
	PS.vl.legend.yspan = .5 * PS.vl.legend.font.size;

    /* Define 'mg', 'hg', 'wd', 'dxx', 'dyy', 'syw', 'roh', and 'cow' */
    fprintf(PS.fp, "/mg %.5f def\n", PS.vl.legend.box.margin);
    fprintf(PS.fp, "/hg mg 2 mul def /wd mg 2 mul def\n");
    fprintf(PS.fp, "/dxx %.2f def\n", PS.vl.legend.xspan);
    fprintf(PS.fp, "/dyy %.2f def\n", PS.vl.legend.yspan);
    fprintf(PS.fp, "/syw %.4f def\n", PS.vl.legend.width);
    fprintf(PS.fp, "/roh %.2f def\n", PS.vl.legend.font.size);
    fprintf(PS.fp, "/cow 0 def\n");

    /* Con join puede haber menos elementos que vectores y hay que ponerlos a cero */
    fprintf(PS.fp, "%d {0} repeat %d array astore /BKh XD\n", n_vct, n_vct);
    fprintf(PS.fp, "%d {0} repeat %d array astore /BKw XD\n", n_vct, n_vct);
    fprintf(PS.fp, "%d {0} repeat %d array astore /BKt XD\n", n_vct, n_vct);

    /* Prepare the content of legend by vector */
    int K, n;

    for (i = 0; i < n_vct; i++) {
	j = ip[i];
	qsort(PS.vct[j].item, PS.vct[j].n_item, sizeof(ITEMS), cmpitems);
	if (PS.vct[j].yspan <= 0)
	    PS.vct[j].yspan = PS.vl.legend.yspan;
    }
    set_ps_font(&(PS.vl.legend.font));
    for (K = 0, i = 0; i < n_vct; i++, K++) {
	j = ip[i];
	/* if (PS.vct[j].n_item == 1) continue; con K-- */
	if (PS.vct[j].n_item == 1) {
	    n = 0;
	    while ((i + n) < n_vct && PS.vct[ip[i + n]].n_item == 1) {
		++n;
	    }
	    set_vlegend_simple(K, ip + i, n);
	    i += (n - 1);
	}
	else {
	    set_vlegend_multi(K, &(PS.vct[j]));
	}
    }
    n_vct = K;
    G_free(ip);

    /* Prepare the title of the legend */
    if (!PS.vl.legend.title || PS.vl.legend.title[0] == 0) {
	fprintf(PS.fp, "/mgy 0 def\n");
    }
    else {
	fprintf(PS.fp, "GS ");
	set_ps_font(&(PS.vl.legend.title_font));
	fprintf(PS.fp, "(%s) SWH ", PS.vl.legend.title);
	fprintf(PS.fp, "mg add dup /mgy XD hg add /hg XD ");
	fprintf(PS.fp, "mg 2 mul add wd 2 copy lt {exch} if pop /wd XD ");
	fprintf(PS.fp, "GR\n");
    }

    /* Prepare and draw the frame of the legend */
    fprintf(PS.fp,
	    "hg BKh {add dyy add} forall dyy sub BKt {add} forall /hg XD\n");
    fprintf(PS.fp,
	    "wd BKw {mg 2 mul add 2 copy lt {exch} if pop} forall /wd XD\n");
    set_box_orig(&(PS.vl.legend.box));
    set_box_draw(&(PS.vl.legend.box));


    /* Draw the title of the legend */
    if (PS.vl.legend.title && PS.vl.legend.title[0] != 0) {
	fprintf(PS.fp, "GS ");
	set_ps_font(&(PS.vl.legend.title_font));
	fprintf(PS.fp, "xo mg add yo mgy sub M wd mg 2 mul sub (%s) SHS\n",
		PS.vl.legend.title);
	fprintf(PS.fp, "GR\n");
    }

    /* Draw the vectors of the legend */
    fprintf(PS.fp,
	    "/VLEGEND {"
	    "dup 0 get /dy XD\n"
	    "dup 1 get dup length 0 eq {pop} {x y dy add MS} ifelse y roh sub /y XD /yt y def\n"
	    "dup 2 exch length 2 sub getinterval {"
	    "dup 0 3 2 index length -- {"
	    "3 getinterval aload pop /code XD aload pop\n");
    fprintf(PS.fp,
	    "code %d eq {"
	    "GS 0 ne {LW 0 LD C x syw add 0 roh sub 2 div neg y add dup x exch ML [] 0 LD} if "
	    "x syw 2 div add 0.65 roh mul 2 div y add TR SC ROT LW cvx cvn exec GR} if\n",
	    POINTS);
    fprintf(PS.fp, "code %d eq {"
	    //            "GS {LW 0 LD C roh .35 mul /z XD x y z add M syw .3 mul z neg syw .6 mul z syw .9 mul 0 rcurveto S} repeat GR} if\n", LINES);
	    "GS {LW 0 LD C x syw add y roh 0.35 mul add dup x exch ML} repeat GR} if\n",
	    LINES);
    fprintf(PS.fp,
	    "code %d eq {"
	    "GS [] 0 LD x y -- x syw .9 mul add y roh add -- B "
	    "GS 0 ne {0 eq {C} {setpattern} ifelse fill} if GR 0 ne {LW 0 LD C S} if GR} if\n",
	    AREAS);
    set_ps_color(&(PS.vl.legend.font.color));
    fprintf(PS.fp,
	    "x syw add y MS\n"
	    "y roh dy add sub /y XD dup} for pop pop\n"
	    "x cow dxx add add /x XD yt /y XD} forall} D\n");

    fprintf(PS.fp, "yo mgy mg add sub /yo XD\n");
    for (i = 0; i < n_vct; i++) {
	/* caja del elemento *
	   fprintf(PS.fp, "GS .2 LW [1] 0 LD ");
	   fprintf(PS.fp, "xo mg add yo BKw %d get BKh %d get BKt %d get add neg RE GR\n", i, i, i);
	 */
	fprintf(PS.fp, "/x xo mg add def ");
	fprintf(PS.fp, "/y yo BKt %d get sub def\n", i);
	fprintf(PS.fp, "BK%d VLEGEND\n", i);
	fprintf(PS.fp, "yo BKh %i get BKt %d get dyy add add sub /yo XD\n", i,
		i);
    }

    return 1;
}

void make_vareas(VECTOR * vec, int rows)
{
    int i, item;
    VAREAS *va = (VAREAS *) vec->data;

    /* Set the title of the vector */
    fprintf(PS.fp, "(");
    if (va->rgbcol != NULL)
	fprintf(PS.fp, "%s", vec->label);
    fprintf(PS.fp, ")\n");

    /* Iterate by items */
    fprintf(PS.fp, "[\n");
    for (item = 0, i = 0; i < vec->n_item; i++, item++) {
	if (item == rows) {
	    item = 0;
	    fprintf(PS.fp, "][\n");
	}
	/* set the label of the item */
	if (va->rgbcol == NULL) {
	    fprintf(PS.fp, "( %s)", vec->label);
	}
	else {
	    int id = vec->item[i].rule;

	    if (id == -1) {
		fprintf(PS.fp, "( )");
	    }
	    else {
		fprintf(PS.fp, "( %s)", vec->rule[id].label);
	    }
	    long_to_color(vec->item[i].data, &(va->fcolor));
	}
	/* set the specific data of the item */
	fprintf(PS.fp, " [");
	if (va->line.color.none || va->line.width <= 0) {
	    fprintf(PS.fp, "0 ");
	}
	else {
	    fprintf(PS.fp, "%.3f %.3f %.3f [%s] %.3f 1 ",
		    va->line.color.r, va->line.color.g, va->line.color.b,
		    va->line.dash, va->line.width);
	}
	if (va->fcolor.none && va->name_pat == NULL) {
	    fprintf(PS.fp, "0");
	}
	else {
	    if (va->name_pat == NULL || va->type_pat == 2) {
		fprintf(PS.fp, "%.3f %.3f %.3f ",
			va->fcolor.r, va->fcolor.g, va->fcolor.b);
	    }
	    if (va->name_pat != NULL) {
		fprintf(PS.fp, "PATTERN%d 1 1", vec->id);
	    }
	    else {
		fprintf(PS.fp, "0 1");
	    }
	}
	fprintf(PS.fp, "] %d\n", vec->type);
    }
    fprintf(PS.fp, "]\n");
}

void make_vlines(VECTOR * vec, int rows)
{
    int i, item;
    VLINES *vl = (VLINES *) vec->data;

    /* Set the title of the vector */
    fprintf(PS.fp, "(");
    if (vl->rgbcol != NULL)
	fprintf(PS.fp, "%s", vec->label);
    fprintf(PS.fp, ")\n");

    /* Iterate by items */
    fprintf(PS.fp, "[\n");
    for (item = 0, i = 0; i < vec->n_item; i++, item++) {
	if (item == rows) {
	    item = 0;
	    fprintf(PS.fp, "][\n");
	}
	/* set the label of the item */
	if (vl->rgbcol == NULL) {
	    fprintf(PS.fp, "( %s)", vec->label);
	}
	else {
	    int id = vec->item[i].rule;

	    if (id == -1) {
		fprintf(PS.fp, "( )");
	    }
	    else {
		fprintf(PS.fp, "( %s)", vec->rule[id].label);
	    }
	    long_to_color(vec->item[i].data, &(vl->line.color));
	}
	/* set the specific data of the item */
	fprintf(PS.fp, " [");
	fprintf(PS.fp, "%.3f %.3f %.3f [%s] %.4f",
		vl->line.color.r, vl->line.color.g, vl->line.color.b,
		vl->line.dash, vl->line.width);
	if (vl->hline.width <= 0) {
	    fprintf(PS.fp, " 1");
	}
	else {
	    fprintf(PS.fp, " %.3f %.3f %.3f [%s] %.4f",
		    vl->hline.color.r, vl->hline.color.g, vl->hline.color.b,
		    vl->hline.dash, vl->hline.width);
	    fprintf(PS.fp, " 2");
	}
	fprintf(PS.fp, "] %d\n", vec->type);
    }
    fprintf(PS.fp, "]\n");
}

void make_vpoints(VECTOR * vec, int rows)
{
    int i, item;
    VPOINTS *vp = (VPOINTS *) vec->data;

    /* Set the title of the vector */
    fprintf(PS.fp, "(");
    if (vp->sizecol != NULL && vec->n_rule > 0)
	fprintf(PS.fp, "%s", vec->label);
    fprintf(PS.fp, ")\n");

    /* Iterate by items */
    fprintf(PS.fp, "[\n");
    for (item = 0, i = 0; i < vec->n_item; i++, item++) {
	/* if vp->size == 0 => no draw? */

	if (item == rows) {
	    item = 0;
	    fprintf(PS.fp, "][\n");
	}
	/* set the label of the item */
	if (vp->sizecol == NULL || vec->n_rule == 0) {
	    fprintf(PS.fp, "( %s)", vec->label);
	}
	else {
	    int id = vec->item[i].rule;

	    if (id == -1) {
		vp->size = (double)(vec->item[i].data / 1000.);
		fprintf(PS.fp, "( %.3f)", vp->size);
	    }
	    else {
		fprintf(PS.fp, "( %s)", vec->rule[id].label);
		vp->size = vec->rule[id].value;
	    }

	}
	/* set the specific data of the item */
	fprintf(PS.fp, " [");
	fprintf(PS.fp, "(SYMBOL%d)", vec->id);
	//      fprintf(PS.fp, " %.4f", vp->line.width / vp->size);     /* div! 0 */
	if (vp->size == 0.)
	    fprintf(PS.fp, " %.4f", vp->line.width);
	else
	    fprintf(PS.fp, " %.4f", vp->line.width / vp->size);
	fprintf(PS.fp, " %.3f", vp->rotate);
	fprintf(PS.fp, " %.3f dup", vp->size);
	if (vp->distance != 0.) {
	    fprintf(PS.fp, " %.3f %.3f %.3f [%s] %.4f",
		    vp->cline.color.r, vp->cline.color.g, vp->cline.color.b,
		    vp->cline.dash, vp->cline.width);
	    fprintf(PS.fp, " 1");
	}
	else {
	    fprintf(PS.fp, " 0");
	}
	fprintf(PS.fp, "] %d\n", vec->type);
    }
    fprintf(PS.fp, "]\n");
}

/* Join vector legend with simple line */
int set_vlegend_simple(int i, const int *ip, int items)
{
    int x, rows, cols, item;

    cols = (items > PS.vl.legend.cols) ? PS.vl.legend.cols : items;
    rows = items / cols;
    if ((items % cols))
	++rows;

    fprintf(PS.fp, "/BK%d [\n%.4f ()\n[\n", i, PS.vl.legend.yspan);
    for (item = 0, x = 0; x < items; x++, item++) {
	VECTOR *vec = &(PS.vct[ip[x]]);

	if (item == rows) {
	    item = 0;
	    fprintf(PS.fp, "][\n");
	}
	fprintf(PS.fp, "( %s)", vec->label);
	switch (vec->type) {
	case AREAS:
	    {
		VAREAS *va = (VAREAS *) vec->data;

		fprintf(PS.fp, " [");
		if (va->line.color.none || va->line.width <= 0) {
		    fprintf(PS.fp, "0 ");
		}
		else {
		    fprintf(PS.fp, "%.3f %.3f %.3f [%s] %.3f 1 ",
			    va->line.color.r, va->line.color.g,
			    va->line.color.b, va->line.dash, va->line.width);
		}
		if (va->fcolor.none && va->name_pat == NULL) {
		    fprintf(PS.fp, "0");
		}
		else {
		    if (va->name_pat == NULL || va->type_pat == 2) {
			fprintf(PS.fp, "%.3f %.3f %.3f ",
				va->fcolor.r, va->fcolor.g, va->fcolor.b);
		    }
		    if (va->name_pat != NULL) {
			fprintf(PS.fp, "PATTERN%d 1 1", vec->id);
		    }
		    else {
			fprintf(PS.fp, "0 1");
		    }
		}
		fprintf(PS.fp, "] %d\n", vec->type);
	    }
	    break;
	case LINES:
	    {
		VLINES *vl = (VLINES *) vec->data;

		fprintf(PS.fp, " [");
		fprintf(PS.fp, "%.3f %.3f %.3f [%s] %.4f",
			vl->line.color.r, vl->line.color.g, vl->line.color.b,
			vl->line.dash, vl->line.width);
		if (vl->hline.width <= 0) {
		    fprintf(PS.fp, " 1");
		}
		else {
		    fprintf(PS.fp, " %.3f %.3f %.3f [%s] %.4f",
			    vl->hline.color.r, vl->hline.color.g,
			    vl->hline.color.b, vl->hline.dash,
			    vl->hline.width);
		    fprintf(PS.fp, " 2");
		}
		fprintf(PS.fp, "] %d\n", vec->type);
	    }
	    break;
	case POINTS:
	    {
		VPOINTS *vp = (VPOINTS *) vec->data;

		fprintf(PS.fp, " [");
		fprintf(PS.fp, "(SYMBOL%d)", vec->id);
		fprintf(PS.fp, " %.4f", vp->line.width / vp->size);	/* div! 0 */
		fprintf(PS.fp, " %.3f", vp->rotate);
		fprintf(PS.fp, " %.3f dup", vp->size);
		if (vp->distance != 0.) {
		    fprintf(PS.fp, " %.3f %.3f %.3f [%s] %.4f",
			    vp->cline.color.r, vp->cline.color.g,
			    vp->cline.color.b, vp->cline.dash,
			    vp->cline.width);
		    fprintf(PS.fp, " 1");
		}
		else {
		    fprintf(PS.fp, " 0");
		}
		fprintf(PS.fp, "] %d\n", vec->type);
	    }
	    break;
	}
    }
    fprintf(PS.fp, "]\n] def\n");

    /* Evaluate result */
    set_vlegend_ps(i, rows, cols);

    return 1;
}

/* Make a vector legend with multiline rules */
int set_vlegend_multi(int i, VECTOR * vec)
{
    int rows, cols, items;

    items = vec->n_item;
    cols = (items > vec->cols) ? vec->cols : items;
    rows = items / cols;
    if ((items % cols))
	++rows;

    /* Make de legend */
    fprintf(PS.fp, "/BK%d [\n%.4f ", i, vec->yspan);
    switch (vec->type) {
    case AREAS:
	{
	    make_vareas(vec, rows);
	}
	break;
    case LINES:
	{
	    make_vlines(vec, rows);
	}
	break;
    case POINTS:
	{
	    make_vpoints(vec, rows);
	}
	break;
    }
    fprintf(PS.fp, "] def\n");

    /* Evaluate result */
    set_vlegend_ps(i, rows, cols);

    return 1;
}

/* Post-evaluation of postscript block legend */
void set_vlegend_ps(int i, int rows, int cols)
{
    fprintf(PS.fp, "BK%d aload length 2 sub {"
	    "aload length 3 idiv"
	    "{pop pop SW syw add cow 2 copy lt {pop} {exch /cow XD} ifelse pop}"
	    "repeat} repeat exch /dy XD\n", i);

    fprintf(PS.fp, "BKh %d roh dy add %d mul dy sub put\n", i, rows);
    fprintf(PS.fp, "BKw %d cow dxx add %d mul dxx sub put\n", i, cols);

    fprintf(PS.fp, "dup length 0 eq {BKt %d 0 put} ", i);
    fprintf(PS.fp, "{SWH BKt %d 3 -1 roll dy add put ", i);
    fprintf(PS.fp,
	    "BKw %d get 2 copy gt {pop BKw %d 3 -1 roll put} {pop pop} ifelse} ifelse\n",
	    i, i);
}
