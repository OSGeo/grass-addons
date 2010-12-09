/* File: r_vareas.c
 *
 *  AUTHOR:    E. Jorge Tizado, Spain 2009
 *
 *  COPYRIGHT: (c) 2009 E. Jorge Tizado, and the GRASS Development Team
 *             This program is free software under the GNU General Public
 *             License (>=v2). Read the file COPYING that comes with GRASS
 *             for details.
 */

#include <stdlib.h>
#include <string.h>
#include <grass/Vect.h>
#include "vector.h"
#include "ps_info.h"
#include "local_proto.h"

#define KEY(x) (strcmp(key,x)==0)


int read_vareas(char *name)
{
    int i;
    char buf[1024];
    char *key, *data, *mapset;
    VAREAS *vector = NULL;

    G_debug(1, "Reading vareas settings ..");

    i = vector_new();		/* G_realloc */
    default_vector(i);

    /* inline argument */
    if (strcmp(name, "(none)") != 0) {
	mapset = G_find_vector(name, "");
	if (mapset == NULL) {
	    error("ERROR:", name, "Can't find vector map");
	}
	PS.vct[i].name = G_store(name);
	PS.vct[i].mapset = G_store(mapset);
	PS.vct[i].data = G_malloc(sizeof(VAREAS));

	Vect_set_open_level(2);	/* level 2: topology */
	Vect_set_fatal_error(GV_FATAL_PRINT);

	if (2 > Vect_open_old(&(PS.vct[i].Map), name, mapset)) {
	    sprintf(buf, "%s in %s", name, mapset);
	    error("ERROR:", buf, "can't open vector map");
	    return 0;
	}
	PS.vct[i].type = AREAS;
    }

    /* specific default values */
    vector = (VAREAS *) PS.vct[i].data;
    unset_color(&(vector->fcolor));
    vector->width = 0;
    vector->type_pat = 1;	/* colored pattern */
    vector->name_pat = NULL;
    vector->lw_pat = 1.;
    vector->sc_pat = 1.;
    vector->island = 1;
    vector->rgbcol = NULL;
    vector->idcol = NULL;

    /* process options */
    while (input(2, buf)) {
	if (!key_data(buf, &key, &data)) {
	    continue;
	}
	if (KEY("lwidth")) {
	    G_strip(data);
	    if (scan_dimen(data, &(vector->width)) != 1)
		error(key, data, "illegal 'lwidth' width (vareas)");
	    continue;
	}
	if (KEY("line")) {
	    read_psline(data, &(vector->line));
	    continue;
	}
	if (KEY("fcolor")) {
	    char stra[50], strb[50];
	    int ret = sscanf(data, "%s %[^\n]", stra, strb);

	    if (ret == 1 || ret == 2) {
		if (!scan_color(stra, &(vector->fcolor))) {
		    double alpha;

		    if (ret == 2)
			vector->idcol = G_store(strb);

		    ret = sscanf(stra, "%[^$]$%lf", strb, &alpha);
		    vector->rgbcol = G_store(strb);
		    vector->fcolor.a = (ret == 2) ? alpha : 1.;
		    G_message(" >>> Request fcolor from column '%s' (vareas)",
			      vector->rgbcol);
		    vector->type_pat = 2;	/* uncolored pattern */
		}
	    }
	    else {
		error(key, data, "illegal data in 'fcolor' (vareas)");
	    }
	    continue;
	}
	if (KEY("pat")) {
	    G_chop(data);
	    vector->name_pat = G_store(data);
	    continue;
	}
	if (KEY("pscale")) {
	    G_chop(data);
	    vector->sc_pat = atof(data);
	    continue;
	}
	if (KEY("pwidth")) {
	    if (scan_dimen(data, &(vector->lw_pat)) != 1)
		error(key, data, "illegal pattern width (vareas)");
	    continue;
	}
	if (KEY("island")) {
	    vector->island = scan_yesno(key, data);
	    continue;
	}
	/* common options of all vectors */
	if (KEY("layer")) {
	    G_strip(data);
	    PS.vct[i].layer = atoi(data);
	    if (PS.vct[i].layer < 1)
		PS.vct[i].layer = 1;
	    continue;
	}
	if (KEY("cats") || KEY("cat")) {
	    G_strip(data);
	    PS.vct[i].cats = G_store(data);
	    continue;
	}
	if (KEY("where")) {
	    G_strip(data);
	    PS.vct[i].where = G_store(data);
	    continue;
	}
	if (KEY("masked")) {
	    PS.vct[i].masked = scan_yesno(key, data);
	    if (PS.vct[i].masked)
		PS.need_mask = 1;
	    continue;
	}
	if (KEY("label")) {
	    G_strip(data);
	    PS.vct[i].label = G_store(data);
	    continue;
	}
	if (KEY("legend") || KEY("lpos")) {
	    int k;

	    if (sscanf(data, "%d", &k) == 1)
		PS.vct[i].lpos = k;
	    else
		read_block(i);
	    continue;
	}
	if (KEY("setrule")) {
	    double val;
	    char str[128], catsbuf[128], labelbuf[128];

	    if (sscanf(data, "%s %[^\n]", str, labelbuf) > 0) {
		if (sscanf(str, "%[^:]:%lf", catsbuf, &val) == 1)
		    val = 0.;
		vector_rule_new(&(PS.vct[i]), catsbuf, labelbuf, val);
	    }
	    else
		error(key, data, "illegal 'setrule' request (vareas)");
	    continue;
	}
	error(key, "", "illegal request (vareas)");
    }

    /* default label */
    if (PS.vct[i].label == NULL) {
	sprintf(buf, "%s (%s)", PS.vct[i].name, PS.vct[i].mapset);
	PS.vct[i].label = G_store(buf);
    }

    if (vector->rgbcol == NULL) {
	vector_item_new(&(PS.vct[i]), 0, color_to_long(&(vector->fcolor)));
    }

    /*
       int x, y;
       for (x = 0; x < PS.vct[i].n_rule; x++)
       {
       printf("::: RULE %d :::", x+1);
       for (y = 0; y < PS.vct[i].rule[x].count; y += 2)
       {
       printf(" %f-%f (%f): %s\n",
       PS.vct[i].rule[x].val_list[y], PS.vct[i].rule[x].val_list[y+1],
       PS.vct[i].rule[x].value, PS.vct[i].rule[x].label);
       }
       }
     */

    return 1;
}
