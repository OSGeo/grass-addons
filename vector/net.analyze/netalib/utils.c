
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


/* Writes GV_POINT to Out at the position of the node in In */
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

/* Returns the list of all points with the given category and field */
/*void neta_get_points_by_category(struct Map_info *In, int field, int cat, struct ilist *point_list)
 * {
 * int i, nlines;
 * struct line_cats *Cats;
 * Cats = Vect_new_cats_struct();
 * Vect_get_num_lines(In);
 * for(i=1;i<=nlines;i++){
 * int type = Vect_read_line(In, NULL, Cats, i);
 * if(type!=GV_POINT)continue;
 * }
 * 
 * Vect_destroy_cats_struct(Cats);
 * }
 */

/* Finds the node corresponding to each point in the point_list */
void neta_points_to_nodes(struct Map_info *In, struct ilist *point_list)
{
    int i, node;
    for (i = 0; i < point_list->n_values; i++) {
	Vect_get_line_nodes(In, point_list->value[i], &node, NULL);
	point_list->value[i] = node;
    }
}

/* For each node in the map, finds the category of the point on it (if there is any) and stores the value
 * associated with this category in the array node_costs. If there is no point with a category, node_costs=0.
 * 
 * node_costs are multiplied by 1000000 and truncated to integers (as is done in Vect_net_build_graph) 
 * 
 * Returns 1 on success, 0 on failure.
 */
int neta_get_node_costs(struct Map_info *In, int layer, char *column,
			int *node_costs)
{
    int i, nlines, nnodes;
    dbCatValArray vals;
    struct line_cats *Cats;
    struct line_pnts *Points;

    dbDriver *driver;
    struct field_info *Fi;
    Fi = Vect_get_field(In, layer);
    driver = db_start_driver_open_database(Fi->driver, Fi->database);
    if (driver == NULL)
	G_fatal_error(_("Unable to open database <%s> by driver <%s>"),
		      Fi->database, Fi->driver);

    nlines = Vect_get_num_lines(In);
    nnodes = Vect_get_num_nodes(In);
    Cats = Vect_new_cats_struct();
    Points = Vect_new_line_struct();
    for (i = 1; i <= nnodes; i++)
	node_costs[i] = 0;

    db_CatValArray_init(&vals);

    if (db_select_CatValArray(driver, Fi->table, Fi->key, column, NULL, &vals)
	== -1)
	return 0;
    for (i = 1; i <= nlines; i++) {
	int type = Vect_read_line(In, Points, Cats, i);
	if (type == GV_POINT) {
	    int node, cat;
	    double value;
	    if (!Vect_cat_get(Cats, layer, &cat))
		continue;
	    Vect_get_line_nodes(In, i, &node, NULL);
	    if (db_CatValArray_get_value_double(&vals, cat, &value) == DB_OK)
		node_costs[node] = value * 1000000.0;
	}
    }

    Vect_destroy_cats_struct(Cats);
    db_CatValArray_free(&vals);
    db_close_database_shutdown_driver(driver);
    return 1;
}

/*returns the list of all nodes on features selected by varray.
 * nodes_to_features conains the index of a feature adjecent to each node or -1 if no such feature
 * specified by varray exists */
void neta_varray_to_nodes(struct Map_info *map, VARRAY * varray,
			  struct ilist *nodes, int *nodes_to_features)
{
    int nlines, nnodes, i;
    nlines = Vect_get_num_lines(map);
    nnodes = Vect_get_num_nodes(map);
    for (i = 1; i <= nnodes; i++)
	nodes_to_features[i] = -1;

    for (i = 1; i <= nlines; i++)
	if (varray->c[i]) {
	    int type = Vect_read_line(map, NULL, NULL, i);
	    if (type == GV_POINT) {
		int node;
		Vect_get_line_nodes(map, i, &node, NULL);
		Vect_list_append(nodes, node);
		nodes_to_features[node] = i;
	    }
	    else {
		int node1, node2;
		Vect_get_line_nodes(map, i, &node1, &node2);
		Vect_list_append(nodes, node1);
		Vect_list_append(nodes, node2);
		nodes_to_features[node1] = nodes_to_features[node2] = i;
	    }
	}
}
