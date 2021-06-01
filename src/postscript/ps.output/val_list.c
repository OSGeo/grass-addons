/* File: val_list.c
 *
 *  COPYRIGHT: (c) 2009 GRASS Development Team
 *             This program is free software under the GNU General Public
 *             License (>=v2). Read the file COPYING that comes with GRASS
 *             for details.
 */

#include "ps_info.h"
#include "local_proto.h"


/* Sort categories by user */
int sort_list(char *order, int items, CELL ** item)
{
    int i, j, k, count, tmp;
    CELL *ip, val;
    DCELL *vlist;

    /* initial order */
    ip = (CELL *) G_malloc(sizeof(CELL) * items);
    for (i = 0; i < items; i++)
	ip[i] = i;

    /* if any to order */
    if (order[0] != 0 && (count = parse_val_list(order, &vlist)) > 0) {
	for (i = 0, j = 0; j < count; j += 2) {
	    for (val = vlist[j]; val <= vlist[j + 1]; val++) {
		for (k = i; k < items; k++) {
		    if ((*item)[k] == val) {
			tmp = ip[k];
			ip[k] = ip[i];
			ip[i] = tmp;
			(*item)[k] = (*item)[i];
			i++;
			break;
		    }
		}
	    }
	}
    }

    G_free(*item);
    *item = ip;
    return 0;
}


/***********************************************************
 * parse_val_list (buf, list)
 *   char *buf; int **list;
 *
 * buf is a comma separated list of values
 * or value ranges: 1,2,6-10,12
 *
 * actual usage is
 *   char buf[300]; DCELL *list;
 *
 *   count = parse_val_list (buf, &list);
 *
 *   for (i = 0; i < count; i += 2)
 *  {
 *          min = list[i];
 *      max = list[i+1];
 *  }
 *
 * count will be negative if list is not valid
 ********************************************************/
#include <grass/gis.h>

int parse_val_list(char *buf, DCELL ** list)
{
    int count;
    DCELL a, b;
    DCELL *lp;

    count = 0;
    lp = (DCELL *) G_malloc(sizeof(DCELL));
    while (*buf) {
	while (*buf == ' ' || *buf == '\t' || *buf == ',' || *buf == '\n') {
	    buf++;
	}
	if (sscanf(buf, "%lf-%lf", &a, &b) == 2) {
	    if (a > b) {
		DCELL t;

		t = a;
		a = b;
		b = t;
	    }
	    lp = (DCELL *) G_realloc(lp, (count + 2) * sizeof(DCELL));
	    lp[count++] = a;
	    lp[count++] = b;
	}
	else if (sscanf(buf, "%lf", &a) == 1) {
	    lp = (DCELL *) G_realloc(lp, (count + 2) * sizeof(DCELL));
	    lp[count++] = a;
	    lp[count++] = a;
	}
	else {
	    G_free(lp);
	    return -1;
	}
	while (*buf && (*buf != ','))
	    buf++;
    }
    *list = lp;
    return count;
}
