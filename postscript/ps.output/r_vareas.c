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

    G_debug(1, "Reading vlines settings ..");

    i = vector_new();   /* G_realloc */

    /* inline argument */
    mapset = G_find_file("vector", name, "");
    if (mapset == NULL) {
        error("ERROR:", name, "Can't find vector map");
    }
    PS.vct[i].name   = G_store(name);
    PS.vct[i].mapset = G_store(mapset);
    PS.vct[i].data   = G_malloc(sizeof(VAREAS));

    Vect_set_open_level(2);     /* level 2: topology */
    Vect_set_fatal_error(GV_FATAL_PRINT);

    if (2 > Vect_open_old(&(PS.vct[i].Map), name, mapset))
    {
        sprintf(buf, "%s in %s", name, mapset);
        error("ERROR:", buf, "can't open vector map");
        return 0;
    }

    /* generic default values */
    PS.vct[i].type   = AREAS;
    PS.vct[i].id     = i;
    PS.vct[i].layer  = 1;
    PS.vct[i].cats   = NULL;
    PS.vct[i].where  = NULL;
    PS.vct[i].masked = 0;
    PS.vct[i].label  = G_store(name);
    PS.vct[i].lpos   = 0;

    /* specific default values */
    vector = (VAREAS *)PS.vct[i].data;
    unset_color(&(vector->fcolor));
    vector->width    = 0.;
    vector->type_pat = 1;   /* colored pattern */
    vector->pat      = NULL;
    vector->pwidth   = 1.;
    vector->scale    = 1.;
    vector->rgbcol   = NULL;

    /* process options */
    while (input(2, buf))
    {
        if (!key_data(buf, &key, &data)) {
            continue;
        }
        if (KEY("width")) {
            G_strip(data);
            scan_dimen(data, &(vector->width));
            continue;
        }
        if (KEY("line")) {
            read_psline(data, &(vector->line));
            continue;
        }
        if (KEY("fcolor")) {
            char stra[50], strb[50];
            int ret = sscanf(data, "%s %s", stra, strb);
            if (ret != 1 && ret != 2) {
                error(key, data, "illegal fcolor (vareas)");
            }
            if (!scan_color(stra, &(vector->fcolor))) {
                error(key, data, "illegal fcolor (vareas)");
            }
            if (ret == 2) {
                vector->rgbcol = G_store(strb);
                G_warning("Request fcolor from database '%s' (vareas)",
                          vector->rgbcol);
                vector->type_pat = 2;   /* uncolored pattern */
            }
            continue;
        }
        if (KEY("pat")) {
            G_chop(data);
            vector->pat = G_store(data);
            continue;
        }
        if (KEY("scale")) {
            G_chop(data);
            vector->scale = atof(data);
            continue;
        }
        if (KEY("pwidth")) {
            if (scan_dimen(data, &(vector->pwidth)) != 1) {
                error(key, data, "illegal pattern width (vareas)");
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
        error(key, "", "illegal request (vareas)");
    }

    return 1;
}
