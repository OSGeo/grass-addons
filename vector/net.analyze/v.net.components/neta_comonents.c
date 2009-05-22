
/****************************************************************
 *
 * MODULE:     v.net.components
 *
 * AUTHOR(S):  Daniel Bundala
 *
 * PURPOSE:    Computes strongly and weakly connected components
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

int neta_weakly_connected_components(dglGraph_s * graph, int *component)
{
    int nnodes;
    dglInt32_t *stack;
    int *visited;
    int stack_size, components;
    dglInt32_t *cur_node;
    dglNodeTraverser_s nt;

    components = 0;
    nnodes = dglGet_NodeCount(graph);
    stack = (dglInt32_t *) G_calloc(nnodes + 1, sizeof(dglInt32_t));
    visited = (int *)G_calloc(nnodes + 1, sizeof(int));
    if (!stack || !visited) {
	G_fatal_error(_("Out of memory"));
	return -1;
    }

    dglNode_T_Initialize(&nt, graph);

    for (cur_node = dglNode_T_First(&nt); cur_node;
	 cur_node = dglNode_T_Next(&nt)) {
	dglInt32_t node_id = dglNodeGet_Id(graph, cur_node);
	if (!visited[node_id]) {
	    visited[node_id] = 1;
	    stack[0] = node_id;
	    stack_size = 1;
	    component[node_id] = ++components;
	    while (stack_size) {
		dglInt32_t *node, *edgeset, *edge;
		dglEdgesetTraverser_s et;
		node = dglGetNode(graph, stack[--stack_size]);
		edgeset = dglNodeGet_OutEdgeset(graph, node);
		dglEdgeset_T_Initialize(&et, graph, edgeset);
		for (edge = dglEdgeset_T_First(&et); edge;
		     edge = dglEdgeset_T_Next(&et)) {
		    dglInt32_t to;
		    to = dglNodeGet_Id(graph, dglEdgeGet_Tail(graph, edge));
		    if (!visited[to]) {
			visited[to] = 1;
			component[to] = components;
			stack[stack_size++] = to;
		    }
		}
		dglEdgeset_T_Release(&et);
	    }
	}
    }
    dglNode_T_Release(&nt);
    G_free(visited);
    return components;
}

int neta_strongly_connected_components(dglGraph_s * graph, int *component)
{
    int nnodes;
    dglInt32_t *stack, *order;
    int *visited, *processed;
    int stack_size, order_size, components;
    dglInt32_t *node;
    dglNodeTraverser_s nt;

    components = 0;
    nnodes = dglGet_NodeCount(graph);
    stack = (dglInt32_t *) G_calloc(nnodes + 1, sizeof(dglInt32_t));
    order = (dglInt32_t *) G_calloc(nnodes + 1, sizeof(dglInt32_t));
    visited = (int *)G_calloc(nnodes + 1, sizeof(int));
    processed = (int *)G_calloc(nnodes + 1, sizeof(int));
    if (!stack || !visited || !order || !processed) {
	G_fatal_error(_("Out of memory"));
	return -1;
    }

    order_size = 0;
    dglNode_T_Initialize(&nt, graph);

    for (node = dglNode_T_First(&nt); node; node = dglNode_T_Next(&nt)) {
	dglInt32_t node_id = dglNodeGet_Id(graph, node);
	component[node_id] = 0;
	if (!visited[node_id]) {
	    visited[node_id] = 1;
	    stack[0] = node_id;
	    stack_size = 1;
	    while (stack_size) {
		dglInt32_t *node, *edgeset, *edge;
		dglEdgesetTraverser_s et;
		dglInt32_t cur_node_id = stack[stack_size - 1];
		if (processed[cur_node_id]) {
		    stack_size--;
		    order[order_size++] = cur_node_id;
		    continue;
		}
		processed[cur_node_id] = 1;
		node = dglGetNode(graph, cur_node_id);
		edgeset = dglNodeGet_OutEdgeset(graph, node);
		dglEdgeset_T_Initialize(&et, graph, edgeset);
		for (edge = dglEdgeset_T_First(&et); edge;
		     edge = dglEdgeset_T_Next(&et)) {
		    dglInt32_t to;
		    if (dglEdgeGet_Id(graph, edge) < 0)
			continue;	/*ignore backward edges */
		    to = dglNodeGet_Id(graph, dglEdgeGet_Tail(graph, edge));
		    if (!visited[to]) {
			visited[to] = 1;
			stack[stack_size++] = to;
		    }
		}
		dglEdgeset_T_Release(&et);
	    }
	}
    }

    dglNode_T_Release(&nt);

    while (order_size) {
	dglInt32_t node_id = order[--order_size];
	if (component[node_id])
	    continue;
	components++;
	component[node_id] = components;
	stack[0] = node_id;
	stack_size = 1;
	while (stack_size) {
	    dglInt32_t *node, *edgeset, *edge;
	    dglEdgesetTraverser_s et;
	    dglInt32_t cur_node_id = stack[--stack_size];
	    node = dglGetNode(graph, cur_node_id);
	    edgeset = dglNodeGet_OutEdgeset(graph, node);
	    dglEdgeset_T_Initialize(&et, graph, edgeset);
	    for (edge = dglEdgeset_T_First(&et); edge;
		 edge = dglEdgeset_T_Next(&et)) {
		dglInt32_t to;
		if (dglEdgeGet_Id(graph, edge) > 0)
		    continue;	/*ignore forward edges */
		to = dglNodeGet_Id(graph, dglEdgeGet_Tail(graph, edge));
		if (!component[to]) {
		    component[to] = components;
		    stack[stack_size++] = to;
		}
	    }
	    dglEdgeset_T_Release(&et);
	}
    }

    G_free(stack);
    G_free(visited);
    G_free(order);
    G_free(processed);
    return components;
}
