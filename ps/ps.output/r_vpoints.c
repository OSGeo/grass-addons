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


    G_debug(1, "Reading vlines settings ..");

    i = vector_new();   /* G_realloc */

    /* inline argument */
    mapset = G_find_file("vector", name, "");
    if (mapset == NULL) {
        error("ERROR:", name, "Can't find vector map");
    }
    PS.vct[i].name   = G_store(name);
    PS.vct[i].mapset = G_store(mapset);
    PS.vct[i].data   = G_malloc(sizeof(VPOINTS));

    Vect_set_open_level(2);     /* level 2: topology */
    Vect_set_fatal_error(GV_FATAL_PRINT);

    if (2 > Vect_open_old(&(PS.vct[i].Map), name, mapset))
    {
        sprintf(buf, "%s in %s", name, mapset);
        error("ERROR:", buf, "can't open vector map");
        return 0;
    }

    /* generic default values */
    PS.vct[i].type   = POINTS;
    PS.vct[i].id     = i;
    PS.vct[i].layer  = 1;
    PS.vct[i].cats   = NULL;
    PS.vct[i].where  = NULL;
    PS.vct[i].masked = 0;
    PS.vct[i].label  = NULL;
    PS.vct[i].lpos   = 0;

    /* specific default values */
    vector            = (VPOINTS *)PS.vct[i].data;
    vector->type      = GV_POINT;
    vector->symbol    = G_store("basic/circle");
    vector->size      = 1.0;
    vector->sizecol   = NULL;
    vector->rotate    = 0.0;
    vector->rotatecol = NULL;
    vector->scale     = 1.0;
    unset_color(&(vector->fcolor));
    default_psline(&(vector->line));

    /* process options */
    while (input(2, buf))
    {
        if (!key_data(buf, &key, &data)) {
            continue;
        }
        if (KEY("type")) {
            G_strip(data);
            if (strcmp(data, "centroid"))
                vector->type = GV_CENTROID;
            /* else default GV_POINT */
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
            int ret = sscanf(data, "%s %s", stra, strb);
            if (ret != 1 && ret != 2) {
                error(key, data, "illegal size request (vpoints)");
            }
            vector->size = atof(stra);
            if (ret == 2)
                vector->sizecol = G_store(strb);
            continue;
        }
        if (KEY("scale")) {
            if (scan_dimen(data, &(vector->scale)) != 1) {
                error(key, data, "illegal scale request (vpoints)");
            }
            continue;
        }
        if (KEY("rotate")) {
            char stra[50], strb[50];
            int ret = sscanf(data, "%s %s", stra, strb);
            if (ret != 1 && ret != 2) {
                error(key, data, "illegal rotate request (vpoints)");
            }
            vector->rotate = atof(stra);
            if (ret == 2)
                vector->rotatecol = G_store(strb);
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
        error(key, "", "illegal request (vpoints)");
    }

    return 1;
}
