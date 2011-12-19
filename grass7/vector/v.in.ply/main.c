
/****************************************************************************
 *
 * MODULE:       v.in.ply
 *               
 * AUTHOR(S):    Markus Metz
 *
 * PURPOSE:      Convert PLY (Polygon file format) files to GRASS vectors
 *
 * COPYRIGHT:    (C) 2011 by the GRASS Development Team
 *
 *               This program is free software under the GNU General Public
 *               License (>=v2). Read the file COPYING that comes with GRASS
 *               for details.
 *
 *****************************************************************************/
#include <stdio.h>
#include <string.h>
#include <unistd.h>
#include <stdlib.h>
#include <grass/gis.h>
#include <grass/dbmi.h>
#include <grass/vector.h>
#include <grass/glocale.h>
#include "local_proto.h"

int ply_type_size[] = { 0, 1, 1, 2, 2, 4, 4, 4, 8 };

int main(int argc, char *argv[])
{
    struct GModule *module;
    struct Option *old, *new, *x_opt, *y_opt, *z_opt;
    struct Flag *table_flag, *notopo_flag, *region_flag;
    char *table;
    int i, j, type, max_cat;
    int zcoor = WITHOUT_Z, make_table;
    int xprop, yprop, zprop;
    struct ply_file ply;
    struct prop_data *data = NULL;
    double x, y, z, coord;

    struct Map_info Map;
    struct line_pnts *Points;
    struct line_cats *Cats;

    G_gisinit(argv[0]);

    module = G_define_module();
    G_add_keyword(_("vector"));
    G_add_keyword(_("import"));
    module->description =
	_("Creates a vector map from a PLY file.");

    /************************** Command Parser ************************************/
    old = G_define_standard_option(G_OPT_F_INPUT);
    old->label = _("Name of input file to be imported");
    old->description = ("'-' for standard input");
    
    new = G_define_standard_option(G_OPT_V_OUTPUT);

    x_opt = G_define_option();
    x_opt->key = "x";
    x_opt->type = TYPE_INTEGER;
    x_opt->required = NO;
    x_opt->multiple = NO;
    x_opt->answer = "1";
    x_opt->label = ("Number of vertex property used as x coordinate");
    x_opt->description = _("First vertex property is 1");

    y_opt = G_define_option();
    y_opt->key = "y";
    y_opt->type = TYPE_INTEGER;
    y_opt->required = NO;
    y_opt->multiple = NO;
    y_opt->answer = "2";
    y_opt->label = _("Number of vertex property used as y coordinate");
    y_opt->description = _("First vertex property is 1");

    z_opt = G_define_option();
    z_opt->key = "z";
    z_opt->type = TYPE_INTEGER;
    z_opt->required = NO;
    z_opt->multiple = NO;
    z_opt->answer = "3";
    z_opt->label = _("Number of vertex property used as z coordinate");
    z_opt->description = _("First vertex property is 1. If 0, z coordinate is not used");

    table_flag = G_define_flag();
    table_flag->key = 't';
    table_flag->description = _("Do not create attribute table");

    notopo_flag = G_define_flag();
    notopo_flag->key = 'b';
    notopo_flag->description = _("Do not build topology");

    region_flag = G_define_flag();
    region_flag->key = 'r';
    region_flag->description =
	_("Only import points falling within current region (points mode)");
    region_flag->guisection = _("Points");

    if (G_parser(argc, argv))
	exit(EXIT_FAILURE);

    /* coords */
    xprop = atoi(x_opt->answer);
    yprop = atoi(y_opt->answer);
    zprop = atoi(z_opt->answer);

    /* 3D */
    zcoor = zprop > 0;

    if (xprop < 1 || yprop < 1)
	G_fatal_error(_("x and y must be positive"));
    
    if (xprop == yprop || xprop == zprop || yprop == zprop)
	G_fatal_error(_("x, y, z must be three different numbers"));

    /* init ply object */
    ply.fp = NULL;
    ply.file_type = 0;
    ply.version = NULL;
    ply.n_elements = 0;
    ply.element = NULL;
    ply.curr_element = NULL;
    ply.n_comments = 0;
    ply.comment = NULL;
    ply.header_size = 0;
    ply.list.n_alloc = 10;
    ply.list.index = G_malloc(sizeof(int) * ply.list.n_alloc);
    ply.x = xprop - 1;
    ply.y = yprop - 1;
    ply.z = zprop - 1;

    /* open input file */
    if ((ply.fp = fopen(old->answer, "r")) == NULL)
	G_fatal_error(_("Can not open input file <%s>"), old->answer);

    /* read ply header */
    read_ply_header(&ply);
    
    for (i = 0; i < ply.n_elements; i++) {
	G_debug(0, "element name: _%s_", ply.element[i]->name);
	G_debug(0, "element type: %d", ply.element[i]->type);

	for (j = 0; j < ply.element[i]->n_properties; j++) {
	    G_debug(0, "poperty name: _%s_", ply.element[i]->property[j]->name);
	    G_debug(0, "poperty type: %d", ply.element[i]->property[j]->type);
	}
    }
    
    
    /* vertices present ? */
    ply.curr_element = NULL;
    for (i = 0; i < ply.n_elements; i++) {
	if (ply.element[i]->type == PLY_VERTEX) {
	    ply.curr_element = ply.element[i];
	}
	else if (ply.element[i]->type == PLY_FACE) {
	    if (ply.element[i]->n_properties != 1) {
		G_fatal_error(_("PLY faces must have only one property"));
	    }
	    else if (ply.element[i]->property[0]->is_list != 1) {
		G_fatal_error(_("PLY faces need a list of vertices"));
	    }
	}
    }
    if (!ply.curr_element)
	G_fatal_error(_("No vertices in PLY file"));
    if (ply.curr_element->n == 0)
	G_fatal_error(_("No vertices in PLY file"));
    
    Vect_open_new(&Map, new->answer, zcoor);
    Vect_hist_command(&Map);
    
    /* table for vertices only
     * otherwise we would need to put faces and edges into separate layers */

    /* alloc memory for vertex data */
    data = (struct prop_data *)G_realloc(data,
           sizeof(struct prop_data) * ply.curr_element->n_properties);

    Points = Vect_new_line_struct();
    Cats = Vect_new_cats_struct();

    G_message(_("%d vertices"), ply.curr_element->n);

    x = y = z = 0.0;
    max_cat = 0;
    for (i = 0; i < ply.curr_element->n; i++) {
	G_percent(i, ply.curr_element->n, 4);
	get_element_data(&ply, data);
	
	Vect_reset_line(Points);
	Vect_reset_cats(Cats);
	Vect_cat_set(Cats, 1, i);
	
	/* x, y, z coord */
	for (j = 0; j < ply.curr_element->n_properties; j++) {
	    if (j == ply.x || j == ply.y || j == ply.z) {
		type = ply.curr_element->property[j]->type;
		coord = 0.0;

		if (type == PLY_UCHAR)
		    coord = data[j].int_val;
		else if (type == PLY_CHAR)
		    coord = data[j].int_val;
		else if (type == PLY_USHORT)
		    coord = data[j].int_val;
		else if (type == PLY_SHORT)
		    coord = data[j].int_val;
		else if (type == PLY_UINT)
		    coord = data[j].int_val;
		else if (type == PLY_FLOAT || type == PLY_DOUBLE)
		    coord = data[j].dbl_val;
		    
		if (j == ply.x)
		    x = coord;
		else if (j == ply.y)
		    y = coord;
		else if (j == ply.z)
		    z = coord;
		
		
	    }
	}
	Vect_append_point(Points, x, y, z);
	Vect_write_line(&Map, GV_POINT, Points, Cats);

	max_cat = i;
    }
    G_percent(1, 1, 1);
    G_free(data);
    
    /* other elements */
    ply.curr_element = NULL;
    for (i = 0; i < ply.n_elements; i++) {
	if (ply.element[i]->type == PLY_VERTEX) {
	    continue;
	}
	if (ply.element[i]->n == 0) {
	    continue;
	}

	ply.curr_element = ply.element[i];
	
	/* faces: get vertex list */
	if (ply.element[i]->type == PLY_FACE) {
	    for (j = 0; j < ply.element[i]->n; j++) {
		int k;

		get_element_list(&ply);
		
		/* fetch points from vector map, sequential reading
		 * this is going to be slow */
		Vect_reset_line(Points);
		Vect_reset_cats(Cats);
		Vect_cat_set(Cats, 2, j);
		 
		 for (k = 0; k < ply.list.n_values; k++) {
		     append_vertex(&Map, Points, ply.list.index[k]);
		 }
		 if (ply.list.n_values > 2) {
		     Vect_append_point(Points,
		                       Points->x[Points->n_points - 1],
		                       Points->y[Points->n_points - 1],
		                       Points->z[Points->n_points - 1]);
		    
		    Vect_write_line(&Map, GV_FACE, Points, Cats);
		 }
	    }
	}

    }


    if (!notopo_flag->answer)
	Vect_build(&Map);

    Vect_close(&Map);

    G_done_msg(" ");

    exit(EXIT_SUCCESS);
}
