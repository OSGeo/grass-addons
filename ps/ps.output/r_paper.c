/* File: r_paper.c
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
#include "ps_info.h"
#include "local_proto.h"

#define KEY(x) (strcmp(key,x)==0)

int read_paper(char *arg)
{
    char buf[1024];
    char *key, *data;
    int do_landscape;
    double point;

    G_debug(1, "Reading paper settings ..");

    /* default values */
    if (arg[0] != 0) {
        set_paper(arg);
    }
    do_landscape = 0;

    while (input(2, buf))
    {
        if (!key_data(buf, &key, &data)) {
            continue;
        }
        if (KEY("width")) {
            if(scan_dimen(data, &(point)) != 1) {
                error(key, data, "illegal paper width request");
            }
            PS.page.width = (int)(point);
            continue;
        }
        if (KEY("height")) {
            if(scan_dimen(data, &(point)) != 1) {
                error(key, data, "illegal paper width request");
            }
            PS.page.height = (int)(point);
            continue;
        }
        if (KEY("left")) {
            if (scan_dimen(data, &(point)) != 1) {
                error(key, data, "illegal paper width request");
            }
            PS.page.left = point;
            continue;
        }
        if (KEY("right")) {
            if(scan_dimen(data, &(point)) != 1) {
                error(key, data, "illegal paper width request");
            }
            PS.page.right = point;
            continue;
        }
        if (KEY("top")) {
            if(scan_dimen(data, &(point)) != 1) {
                error(key, data, "illegal paper width request");
            }
            PS.page.top = point;
            continue;
        }
        if (KEY("bottom")) {
            if(scan_dimen(data, &(point)) != 1) {
                error(key, data, "illegal paper width request");
            }
            PS.page.bot = point;
            continue;
        }
        if (KEY("landscape")) {
            do_landscape = scan_yesno(key, data);
            continue;
        }
        error(key, data, "illegal paper sub-request");
    }

    if (do_landscape != 0)
    {
        int tmp;
        tmp = PS.page.width;
        PS.page.width = PS.page.height;
        PS.page.height = tmp;
    }

    G_debug(1, "Setting paper: %.1f %.1f : %d %d\n",
            PS.page.left, PS.page.top,
            PS.page.width, PS.page.height);

    return 0;
}
