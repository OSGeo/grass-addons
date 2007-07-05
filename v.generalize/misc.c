
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
	};
    return res;
};

