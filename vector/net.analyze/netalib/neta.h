
/****************************************************************
 *
 * MODULE:     netalib
 *
 * AUTHOR(S):  Daniel Bundala
 *
 * PURPOSE:    NETwork Analysis Library
 *
 * COPYRIGHT:  (C) 2002-2005 by the GRASS Development Team
 *
 *             This program is free software under the
 *             GNU General Public License (>=v2).
 *             Read the file COPYING that comes with GRASS
 *             for details.
 *
 ****************************************************************/

#ifndef _NETA_H_
#define _NETA_H_

#include <stdio.h>
#include <stdlib.h>
#include <grass/gis.h>
#include <grass/Vect.h>
#include <grass/glocale.h>
#include <grass/dgl/graph.h>

/*neta_bridge.c*/
int neta_compute_bridges(struct dglGraph_s *graph, struct ilist *bridge_list);
int neta_articulation_points(struct dglGraph_s *graph, struct ilist *articulation_list);

/*neta_components.c*/
int neta_weakly_connected_components(struct dglGraph_s *graph, int *component);
int neta_strongly_connected_components(struct dglGraph_s *graph, int *component);

/*neta_spanningtree.c*/
int neta_spanning_tree(struct dglGraph_s *graph, struct ilist *tree_list);
#endif
