#include "strahler.h"

/* Replacement for Vect_get_node_n_lines in sloppy mode
   Gets adjacent lines by coordinate */

int StrahGetDegr(struct Map_info *In, int node)
{
    extern double sloppy;
    int degr, onode, j;
    double x, y;
    BOUND_BOX *Box;
    struct ilist *list;

    if (sloppy != 0.0) {
	Vect_get_node_coor(In, node, &x, &y, NULL);

	Vect_get_map_box(In, Box);
	Box->N = y + sloppy;
	Box->S = y - sloppy;
	Box->W = x + sloppy;
	Box->E = x - sloppy;

	list = Vect_new_list();

	/*
	   printf( "N %f\n", Box->N );
	   printf( "S %f\n", Box->S );
	   printf( "W %f\n", Box->W );
	   printf( "E %f\n", Box->E );
	 */

	Vect_select_nodes_by_box(In, Box, list);
	G_debug(3, "  %d nodes selected", list->n_values);
	/* is always 0 -why? */
	for (j = 0; j < list->n_values; j++) {
	    onode = abs(list->value[j]);
	    G_debug(3, "List %d: %d\n", j, onode);
	}
	/*              
	   Vect_list_append ( StArcs, line );
	   Vect_get_line_nodes ( &Map, line, &node1, &node2);
	   Vect_list_append ( StNodes, node1 ); 
	   Vect_list_append ( StNodes, node2 );
	 */

    }
    else {
	degr = Vect_get_node_n_lines(In, node);
    }

    G_debug(4, "node %d degr %d sloppy %f\n", node, degr, sloppy);
    return degr;
}

int StrahGetNodeLine(struct Map_info *In, int node, int d)
{

    extern double sloppy;
    int aline;

    if (sloppy != 0.0) {
	G_debug(4, "StrahGetNodeLine at node %d", node);
	/* 
	   get all nodes within sloppy from node -> from table StrahGetDegr has written
	   get all lines for each found node -> Vect_get_node_line(In, foundnode, df)
	   for ( fn=0; fn<foundnodes.length; fn++ ) {
	   degrf = Vect_get_node_n_lines( In, fn );
	   for (df = 0; df < degrf; df++) {
	   foundline = abs( Vect_get_node_line( In, fn, df ) );
	   addtolist(foundline);
	   }
	   }
	   return line d in list of foundlines;
	 */
    }
    else {
	/* method if junction is only 1 node */
	aline = abs(Vect_get_node_line(In, node, d));
    }
    return aline;
}
