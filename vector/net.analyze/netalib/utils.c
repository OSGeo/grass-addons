
/****************************************************************
 *
 * MODULE:     netalib
 *
 * AUTHOR(S):  Daniel Bundala
 *
 * PURPOSE:    netalib utility functions
 *
 * COPYRIGHT:  (C) 2002-2005 by the GRASS Development Team
 *
 *             This program is free software under the
 *             GNU General Public License (>=v2).
 *             Read the file COPYING that comes with GRASS
 *             for details.
 *
 ****************************************************************/

#include <stdio.h>
#include <stdlib.h>
#include <grass/gis.h>
#include <grass/Vect.h>
#include <grass/glocale.h>
#include <grass/dbmi.h>
#include <grass/neta.h>


void neta_add_point_on_node(struct Map_info *In, struct Map_info *Out, int node,
			    struct line_cats *Cats)
{
    static struct line_pnts *Points;
    double x, y, z;
    Points = Vect_new_line_struct();
    Vect_get_node_coor(In, node, &x, &y, &z);
    Vect_reset_line(Points);
    Vect_append_point(Points, x, y, z);
    Vect_write_line(Out, GV_POINT, Points, Cats);
    Vect_destroy_line_struct(Points);
}
