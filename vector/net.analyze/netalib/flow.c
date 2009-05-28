
/****************************************************************
 *
 * MODULE:     netalib
 *
 * AUTHOR(S):  Daniel Bundala
 *
 * PURPOSE:    Computes the legngth of the shortest path between
 *             all pairs of nodes in the network
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

dglInt32_t sign(dglInt32_t x)
{
    if (x >= 0)
	return 1;
    return -1;
}

/*
 * returns max flow from source to sink. Array flow stores flow for
 * each edge. Negative flow corresponds to a flow in opposite direction
 * The function assumes that the edge costs correspond to edge capacities.
 */
int neta_flow(dglGraph_s * graph, int source, int sink, int *flow)
{
    int nnodes, nlines, i;
    dglEdgesetTraverser_s et;
    dglInt32_t *queue;
    dglInt32_t **prev;
    int begin, end, total_flow;

    nnodes = dglGet_NodeCount(graph);
    nlines = dglGet_EdgeCount(graph) / 2;	/*each line corresponds to two edges. One in each direction */
    queue = (dglInt32_t *) G_calloc(nnodes + 3, sizeof(dglInt32_t));
    prev = (dglInt32_t **) G_calloc(nnodes + 3, sizeof(dglInt32_t *));
    if (!queue || !prev) {
	G_fatal_error(_("Out of memory"));
	return -1;
    }
    for (i = 0; i <= nlines; i++)
	flow[i] = 0;
    total_flow = 0;
    while (1) {
	dglInt32_t node, edge_id, min_residue;
	int found = 0;
	begin = 0;
	end = 1;
	queue[0] = source;
	for (i = 1; i <= nnodes; i++) {
	    prev[i] = NULL;
	}
	while (begin != end && !found) {
	    dglInt32_t vertex = queue[begin++];
	    dglInt32_t *edge, *node = dglGetNode(graph, vertex);
	    dglEdgeset_T_Initialize(&et, graph,
				    dglNodeGet_OutEdgeset(graph, node));
	    for (edge = dglEdgeset_T_First(&et); edge;
		 edge = dglEdgeset_T_Next(&et)) {
		dglInt32_t cap = dglEdgeGet_Cost(graph, edge);
		dglInt32_t id = dglEdgeGet_Id(graph, edge);
		dglInt32_t to =
		    dglNodeGet_Id(graph, dglEdgeGet_Tail(graph, edge));
		if (to != source && prev[to] == NULL &&
		    cap > sign(id) * flow[abs(id)]) {
		    prev[to] = edge;
		    if (to == sink) {
			found = 1;
			break;
		    }
		    queue[end++] = to;
		}
	    }
	    dglEdgeset_T_Release(&et);
	}
	if (!found)
	    break;		/*no augmenting path */
	/*find minimum residual capacity along the augmenting path */
	node = sink;
	edge_id = dglEdgeGet_Id(graph, prev[node]);
	min_residue =
	    dglEdgeGet_Cost(graph,
			    prev[node]) - sign(edge_id) * flow[abs(edge_id)];
	while (node != source) {
	    dglInt32_t residue;
	    edge_id = dglEdgeGet_Id(graph, prev[node]);
	    residue =
		dglEdgeGet_Cost(graph,
				prev[node]) -
		sign(edge_id) * flow[abs(edge_id)];
	    if (residue < min_residue)
		min_residue = residue;
	    node = dglNodeGet_Id(graph, dglEdgeGet_Head(graph, prev[node]));
	}
	total_flow += min_residue;
	/*update flow along the augmenting path */
	node = sink;
	while (node != source) {
	    edge_id = dglEdgeGet_Id(graph, prev[node]);
	    flow[abs(edge_id)] += sign(edge_id) * min_residue;
	    node = dglNodeGet_Id(graph, dglEdgeGet_Head(graph, prev[node]));
	}
    }

    G_free(queue);
    G_free(prev);

    return total_flow;
}
