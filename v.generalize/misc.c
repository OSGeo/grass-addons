
/****************************************************************
 *
 * MODULE:     v.generalize
 *
 * AUTHOR(S):  Daniel Bundala
 *
 * PURPOSE:    miscellaneous functions of v.generalize
 *          
 *
 * COPYRIGHT:  (C) 2002-2005 by the GRASS Development Team
 *
 *             This program is free software under the
 *             GNU General Public License (>=v2).
 *             Read the file COPYING that comes with GRASS
 *             for details.
 *
 ****************************************************************/

#include <grass/gis.h>
#include <grass/Vect.h>
#include <grass/glocale.h>
#include "misc.h"

int check_range(char *s)
{
    int from, to;
    char dummy[2];
    if (strlen(s) == 0)
	return 0;

    dummy[0] = 0;
    if (sscanf(s, "%d-%d%1s", &from, &to, dummy) == 2)
	return (from <= to) && (dummy[0] == 0);

    if (sscanf(s, "%d%1s", &from, dummy) == 1)
	return (dummy[0] == 0);

    return 0;
};

int get_ranges(char **s, RANGE ** out, int *count)
{
    int n, i;
    int from, to;

    n = 0;
    while (s[n])
	n++;
    *count = n;

    *out = (RANGE *) G_malloc(sizeof(RANGE) * n);

    if (!out) {
	G_fatal_error(_("Out of memory"));
	return 0;
    };


    for (i = 0; i < n; i++) {
	if (strchr(s[i], '-') == NULL) {
	    sscanf(s[i], "%d", &from);
	    to = from;
	}
	else
	    sscanf(s[i], "%d-%d", &from, &to);
	(*out)[i].from = from;
	(*out)[i].to = to;
    };

    return 1;
};

int cat_test(struct line_cats *Cats, RANGE * r, int n)
{
    int i, j;

    for (i = 0; i < Cats->n_cats; i++) {
	for (j = 0; j < n; j++)
	    if (Cats->cat[i] >= r[j].from && Cats->cat[i] <= r[j].to)
		return 1;
    };

    return 0;
};
