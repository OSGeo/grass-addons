
/****************************************************************
 *
 * MODULE:     netalib
 *
 * AUTHOR(S):  Daniel Bundala
 *
 * PURPOSE:    Shortest paths from a set of nodes
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

#include <stdio.h>
#include <stdlib.h>
#include <grass/gis.h>
#include <grass/Vect.h>
#include <grass/glocale.h>
#include <grass/dgl/graph.h>
#include <grass/neta.h>

/* Computes shortests paths to every node from  nodes in "from". Array "dst" contains the length of the path
 * or -1 if the node is not reachable.  Prev contains edges from predecessor along the shortest path */
int neta_distance_from_points(dglGraph_s * graph, struct ilist *from, int *dst,
			      dglInt32_t ** prev)
{
    int i, nnodes;
    dglHeap_s heap;
    nnodes = dglGet_NodeCount(graph);
    dglEdgesetTraverser_s et;
    for (i = 1; i <= nnodes; i++) {
	dst[i] = -1;
	prev[i] = NULL;
    }

    dglHeapInit(&heap);

    for (i = 0; i < from->n_values; i++) {
	int v = from->value[i];
	if (dst[v] == 0)
	    continue;		/*ingore duplicates */
	dst[v] = 0;
	dglHeapData_u heap_data;
	heap_data.ul = v;
	dglHeapInsertMin(&heap, 0, ' ', heap_data);
    }
    while (1) {
	dglInt32_t v, dist;
	dglHeapNode_s heap_node;
	dglHeapData_u heap_data;
	if (!dglHeapExtractMin(&heap, &heap_node))
	    break;
	v = heap_node.value.ul;
	dist = heap_node.key;
	if (dst[v] < dist)
	    continue;

	dglInt32_t *edge;
	dglEdgeset_T_Initialize(&et, graph,
				dglNodeGet_OutEdgeset(graph,
						      dglGetNode(graph, v)));
	for (edge = dglEdgeset_T_First(&et); edge;
	     edge = dglEdgeset_T_Next(&et)) {
	    dglInt32_t *to = dglEdgeGet_Tail(graph, edge);
	    dglInt32_t to_id = dglNodeGet_Id(graph, to);
	    dglInt32_t d = dglEdgeGet_Cost(graph, edge);
	    if (dst[to_id] == -1 || dst[to_id] > dist + d) {
		dst[to_id] = dist + d;
		prev[to_id] = edge;
		heap_data.ul = to_id;
		dglHeapInsertMin(&heap, dist + d, ' ', heap_data);
	    }
	}

	dglEdgeset_T_Release(&et);
    }

    dglHeapFree(&heap, NULL);

    return 0;
}
