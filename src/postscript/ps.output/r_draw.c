/* File: r_draw.c
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
#include "draws.h"
#include "ps_info.h"
#include "local_proto.h"

#define KEY(x) (strcmp(key,x)==0)


int read_draw(char *name)
{
    char buf[1024];
    char *key, *data;
    int type = 0;

    G_debug(1, "Reading draw settings ..");

    if (strcmp(name, "free") == 0)
	type = 1;
    else if (strcmp(name, "paper") == 0)
	type = 2;
    else if (strcmp(name, "legend") == 0)
	type = 3;

    /* process options */
    while (input(2, buf)) {
	if (!key_data(buf, &key, &data)) {
	    continue;
	}

	/* TODO: permit command with ';' separation */

	PS.draw.flag[PS.n_draws] = type;
	PS.draw.key[PS.n_draws] = G_store(key);
	PS.draw.data[PS.n_draws] = G_store(data);
	++PS.n_draws;
	if (PS.n_draws == MAX_DRAWS)
	    error(key, data, "many draw commands sub-request");
    }

    return 0;
}
