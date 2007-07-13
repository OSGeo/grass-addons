
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

int type_mask(struct Option *type_opt)
{
    int res = 0;
    int i;
    for (i = 0; type_opt->answers[i]; i++)
	switch (type_opt->answers[i][0]) {
	case 'l':
	    res |= GV_LINE;
	    break;
	case 'b':
	    res |= GV_BOUNDARY;
	    break;
	case 'a':
	    res |= GV_AREA;
	};
    return res;
};

int get_furthest(struct line_pnts *Points, int a, int b, int with_z,
		 double *dist)
{
    int index = a;
    double d = 0;

    int i;
    double x0 = Points->x[a];
    double x1 = Points->x[b];
    double y0 = Points->y[a];
    double y1 = Points->y[b];
    double z0 = Points->z[a];
    double z1 = Points->z[b];

    double px, py, pz, pdist, di;
    int status;

    for (i = a + 1; i < b; i++) {
	di = dig_distance2_point_to_line(Points->x[i], Points->y[i],
					 Points->z[i], x0, y0, z0, x1, y1, z1,
					 with_z, &px, &py, &pz, &pdist,
					 &status);
	if (di > d) {
	    d = di;
	    index = i;
	};
    };
    *dist = d;
    return index;
};
