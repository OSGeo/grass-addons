/* File: r_vpoints.c
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


int read_vpoints(char *name)
{
    int i;
    char buf[1024];
    char *key, *data, *mapset;
    VPOINTS *vector;


    G_debug(1, "Reading vpoints settings ..");

    i = vector_new();		/* G_realloc */

    /* inline argument */
    if (strcmp(name, "(none)") != 0) {
	mapset = G_find_vector(name, "");
	if (mapset == NULL) {
	    error("ERROR:", name, "Can't find vector map");
	}
	PS.vct[i].name = G_store(name);
	PS.vct[i].mapset = G_store(mapset);
	PS.vct[i].data = G_malloc(sizeof(VPOINTS));

	Vect_set_open_level(2);	/* level 2: topology */
	Vect_set_fatal_error(GV_FATAL_PRINT);

	if (2 > Vect_open_old(&(PS.vct[i].Map), name, mapset)) {
	    sprintf(buf, "%s in %s", name, mapset);
	    error("ERROR:", buf, "can't open vector map");
	    return 0;
	}
	PS.vct[i].type = POINTS;
    }

    /* generic default values */
    default_vector(i);

    /* specific default values */
    vector = (VPOINTS *) PS.vct[i].data;
    vector->type = GV_POINT;
    vector->symbol = G_store("basic/circle");
    vector->size = 1.0;
    vector->sizecol = NULL;
    vector->rotate = 0.0;
    vector->rotatecol = NULL;
    vector->scale = 1.0;
    vector->bias = 0.0;
    unset_color(&(vector->fcolor));
    default_psline(&(vector->line));
    vector->distance = 0.;
    vector->voffset = 0.;
    default_psline(&(vector->cline));


    /* process options */
    while (input(2, buf)) {
	if (!key_data(buf, &key, &data)) {
	    continue;
	}
	if (KEY("type")) {
	    G_strip(data);
	    switch (data[0]) {
	    case 'c':
		vector->type = GV_CENTROID;
		break;
	    case 'l':
		vector->type = GV_LINE;
		break;
	    case 'b':
		vector->type = GV_BOUNDARY;
		break;
	    default:
		vector->type = GV_POINT;
		break;
	    }
	    continue;
	}
	if (KEY("symbol")) {
	    vector->symbol = G_store(data);
	    continue;
	}
	if (KEY("line")) {
	    read_psline(data, &(vector->line));
	    continue;
	}
	if (KEY("fcolor")) {
	    if (!scan_color(data, &(vector->fcolor))) {
		error(key, data, "illegal fcolor request (vpoints)");
	    }
	    continue;
	}
	if (KEY("size")) {
	    char stra[50], strb[50];

	    switch (sscanf(data, "%s %s", stra, strb)) {
	    case 1:
		if (atof(stra) != 0.)
		    vector->size = atof(stra);
		else
		    vector->sizecol = G_store(stra);
		break;
	    case 2:
		vector->sizecol = G_store(stra);
		vector->size = atof(strb);
		break;
	    default:
		error(key, data, "illegal scale request (vpoints)");
	    }
	    if (vector->sizecol != NULL)
		G_warning("Request size from '%s' column (vpoints)",
			  vector->sizecol);
	    continue;
	}
	if (KEY("scale")) {
	    char stra[50], strb[50];

	    switch (sscanf(data, "%s %s", stra, strb)) {
	    case 1:
		scan_dimen(stra, &(vector->scale));
		vector->bias = 0.;
		break;
	    case 2:
		scan_dimen(stra, &(vector->scale));
		scan_dimen(strb, &(vector->bias));
		break;
	    default:
		error(key, data, "illegal scale [bias] request (vpoints)");
		break;
	    }
	    continue;
	}
	if (KEY("offset")) {
	    if (scan_dimen(data, &(vector->voffset)) != 1) {
		error(key, data, "illegal voffset request (vpoints)");
	    }
	    continue;
	}
	if (KEY("rotate")) {
	    if (atof(data) != 0.) {
		vector->rotate = atof(data);
	    }
	    else {
		vector->rotatecol = G_store(data);
		G_warning("Request rotate from '%s' column (vpoints)",
			  vector->rotatecol);
	    }
	    continue;
	}
	if (KEY("dist")) {
	    if (scan_dimen(data, &(vector->distance)) != 1) {
		error(key, data, "illegal dist request (vpoints)");
	    }
	    continue;
	}
	if (KEY("cline")) {
	    read_psline(data, &(vector->cline));
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
	    double val;
	    char str[128], catsbuf[128], labelbuf[128];

	    if (sscanf(data, "%s %[^\n]", str, labelbuf) > 0) {
		if (sscanf(str, "%[^:]:%lf", catsbuf, &val) == 1)
		    val = atof(catsbuf) * vector->scale;
		vector_rule_new(&(PS.vct[i]), catsbuf, labelbuf, val);
	    }
	    else
		error(key, data, "illegal setrule request (vpoints)");
	    continue;
	}
	error(key, "", "illegal request (vpoints)");
    }

    /* default label */
    if (PS.vct[i].label == NULL) {
	sprintf(buf, "%s (%s)", PS.vct[i].name, PS.vct[i].mapset);
	PS.vct[i].label = G_store(buf);
    }

    if (vector->sizecol == NULL) {
	vector_item_new(&(PS.vct[i]), 0, (long)(vector->size * 1000.));
    }

    return 1;
}
