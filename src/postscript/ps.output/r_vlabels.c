/* File: r_vlabel.c
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


int read_vlabels(char *name)
{
    int i;
    char buf[1024];
    char *key, *data, *mapset;
    VLABELS *vector;


    G_debug(1, "Reading vlabel settings ..");

    i = vector_new();		/* G_realloc */

    /* inline argument */
    if (strcmp(name, "(none)") != 0) {
	mapset = G_find_vector(name, "");
	if (mapset == NULL) {
	    error("ERROR:", name, "Can't find vector map");
	}
	PS.vct[i].name = G_store(name);
	PS.vct[i].mapset = G_store(mapset);
	PS.vct[i].data = G_malloc(sizeof(VLABELS));

	Vect_set_open_level(2);	/* level 2: topology */
	Vect_set_fatal_error(GV_FATAL_PRINT);

	if (2 > Vect_open_old(&(PS.vct[i].Map), name, mapset)) {
	    sprintf(buf, "%s in %s", name, mapset);
	    error("ERROR:", buf, "can't open vector map");
	    return 0;
	}
	PS.vct[i].type = LABELS;
    }

    /* generic default values */
    default_vector(i);

    /* specific default values */
    vector = (VLABELS *) PS.vct[i].data;
    vector->type = GV_POINT;
    default_font(&(vector->font));
    vector->labelcol = NULL;
    vector->decimals = 0;
    vector->style = 0;

    /* process options */
    while (input(2, buf)) {
	if (!key_data(buf, &key, &data)) {
	    continue;
	}
	if (KEY("font")) {
	    read_font(data, &(vector->font));
	    continue;
	}
	if (KEY("labelcol")) {
	    G_strip(data);
	    vector->labelcol = G_store(data);
	    G_warning("Request label column from database '%s' (vlabel)",
		      vector->labelcol);
	    continue;
	}
	if (KEY("decimals")) {
	    vector->decimals = atoi(data);
	    continue;
	}
	if (KEY("circled")) {
	    scan_dimen(data, &(vector->style));
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

	    if (sscanf(data, "%d", &k) == 1) {
		PS.vct[i].lpos = k;
	    }
	    else {
		read_block(i);
	    }
	    continue;
	}
	if (KEY("setrule")) {
	    char catsbuf[128], labelbuf[128];

	    sscanf(data, "%s %[^\n]", catsbuf, labelbuf);
	    vector_rule_new(&(PS.vct[i]), catsbuf, labelbuf, 0);
	    continue;
	}
	error(key, "", "illegal request (vlabels)");
    }

    /* default label */
    if (PS.vct[i].label == NULL) {
	sprintf(buf, "%s (%s)", PS.vct[i].name, PS.vct[i].mapset);
	PS.vct[i].label = G_store(buf);
    }

    PS.vct[i].lpos = -1;	/* Not in legends */

    return 1;
}
