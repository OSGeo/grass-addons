/* File: r_vlines.c
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


int read_vlines(char *name)
{
    int i;
    char buf[1024];
    char *key, *data, *mapset;
    VLINES *vector;


    G_debug(1, "Reading vlines settings ..");

    i = vector_new();   /* G_realloc */

    /* inline argument */
    mapset = G_find_file("vector", name, "");
    if (mapset == NULL) {
        error("ERROR:", name, "Can't find vector map");
    }
    PS.vct[i].name   = G_store(name);
    PS.vct[i].mapset = G_store(mapset);
    PS.vct[i].data   = G_malloc(sizeof(VLINES));

    Vect_set_open_level(2);     /* level 2: topology */
    Vect_set_fatal_error(GV_FATAL_PRINT);

    if (2 > Vect_open_old(&(PS.vct[i].Map), name, mapset))
    {
        sprintf(buf, "%s in %s", name, mapset);
        error("ERROR:", buf, "can't open vector map");
        return 0;
    }

    /* generic default values */
    PS.vct[i].type   = LINES;
    PS.vct[i].id     = i;
    PS.vct[i].layer  = 1;
    PS.vct[i].cats   = NULL;
    PS.vct[i].where  = NULL;
    PS.vct[i].masked = 0;
    PS.vct[i].label  = NULL;
    PS.vct[i].lpos   = 0;

    /* specific default values */
    vector = (VLINES *)PS.vct[i].data;
    vector->type        = GV_LINE;
    default_psline(&(vector->line));
    default_psline(&(vector->hline));
    vector->hline.width = 0.;
    vector->rgbcol      = NULL;
    vector->offset      = 0.;


    /* process options */
    while (input(2, buf))
    {
        if (!key_data(buf, &key, &data)) {
            continue;
        }
        if (KEY("type")) {
            G_strip(data);
            if (strcmp(data, "boundary") == 0)
                vector->type = GV_BOUNDARY;
            /* else default GV_LINE */
            continue;
        }
        if (KEY("rgbcol")) {
            G_strip(data);
            vector->rgbcol = G_store(data);
            G_warning("Request line color from database '%s' (vlines)",
                      vector->rgbcol);
            continue;
        }
        if (KEY("line")) {
            read_psline(data, &(vector->line));
            continue;
        }
        if (KEY("hline")) {
            if (scan_dimen(data, &(vector->offset)) == 0) {
                vector->offset = 0.;
            }
            read_psline("", &(vector->hline));
            if (vector->hline.width > 0 && vector->offset == 0.) {
                vector->hline.width =
                        vector->line.width +
                        2. * vector->hline.width;
            }
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
            if (PS.vct[i].lpos == 0)
                PS.vct[i].lpos = 1;
            continue;
        }
        if (KEY("lpos")) {
            G_strip(data);
            PS.vct[i].lpos = atoi(data);
            continue;
        }
        error(key, "", "illegal request (vlines)");
    }

    return 1;
}
