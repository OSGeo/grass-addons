/****************************************************************
 * MODULE:     v.path.obstacles
 *
 * AUTHOR(S):  Maximilian Maldacker
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

#include <stdlib.h>
#include <grass/gis.h>
#include <grass/Vect.h>
#include <grass/glocale.h>
#include "visibility.h"

void load_lines( struct Map_info * map, struct Point ** points, int * num_points, struct Line ** lines, int * num_lines );
void count( struct Map_info * map, int * num_points, int * num_lines);
void process_point( struct line_pnts * sites, struct Point ** points, int * index_point, int cat);
void process_line( struct line_pnts * sites, struct Point ** points, int * index_point, struct Line ** lines, int * index_line, int cat);
void process_boundary( struct line_pnts * sites, struct Point ** points, int * index_point, struct Line ** lines, int * index_line, int cat);

int main( int argc, char* argv[])
{
	struct Map_info in, out;
	struct GModule *module;     /* GRASS module for parsing arguments */
	struct Option *input, *output; /* The input map */
	char*mapset;
	
	struct Point * points;
	struct Line * lines;
	int num_points, num_lines;
	

	
    /* initialize GIS environment */
    G_gisinit(argv[0]);		/* reads grass env, stores program name to G_program_name() */

    /* initialize module */
    module = G_define_module();
    module->keywords = _("vector, path, visibility");
    module->description = _("Shortest path in free vector space");

	/* define the arguments needed */
	input = G_define_standard_option(G_OPT_V_INPUT);
	output = G_define_standard_option(G_OPT_V_OUTPUT);
	
	
	/* options and flags parser */
    if (G_parser(argc, argv))
		exit(EXIT_FAILURE);

	Vect_check_input_output_name ( input->answer, output->answer, GV_FATAL_EXIT );

	Vect_set_open_level(2);

	mapset = G_find_vector2 (input->answer, NULL); 		/* finds the map */
	
	if ( mapset == NULL )
		G_fatal_error("Map <%s> not found", input->answer );
	
	if(Vect_open_old(&in, input->answer, mapset) < 1) /* opens the map */
		G_fatal_error(_("Could not open input"));

    if (Vect_open_new(&out, output->answer, WITHOUT_Z) < 0) 
	{
		Vect_close(&in);
		G_fatal_error(_("Could not open output"));
    }

	 
	if (G_projection () == PROJECTION_LL)
		G_warning("We are in LL projection");

	load_lines( &in, &points, &num_points, &lines, &num_lines);
	
	construct_visibility( points, num_points, lines, num_lines, &out );
	
	G_free(points);
	G_free(lines);
	
	Vect_build(&out, stdout);
	Vect_close(&out);
	Vect_close(&in);
	exit(EXIT_SUCCESS);
}

/** counts the number of individual segments ( boundaries and lines ) and vertices
*/
void count( struct Map_info * map, int * num_points, int * num_lines)
{
	int index_line = 0;
	int index_point = 0;
	struct line_pnts* sites;
	struct line_cats* cats;
	int type,i;
	
	sites = Vect_new_line_struct();
	cats = Vect_new_cats_struct();

	for( i = 1; i <= map->plus.n_lines ; i++ )
	{
	
		type = Vect_read_line( map, sites, cats, i);
		
		if ( type != GV_LINE && type != GV_BOUNDARY && type != GV_POINT)
			continue;
		
		if ( type == GV_LINE )
		{
			index_point+= sites->n_points;
			index_line+= sites->n_points-1;
		}
		else if ( type == GV_BOUNDARY )
		{
			index_point+= sites->n_points-1;
			index_line+= sites->n_points-1;
		}
		else if ( type == GV_POINT )
		{
			index_point++;
		}
		
		
	}
	
	*num_points = index_point;
	*num_lines = index_line;

}


/** Get the lines and boundaries from the map and load them in an array
*/
void load_lines( struct Map_info * map, struct Point ** points, int * num_points, struct Line ** lines, int * num_lines )
{
	int index_line = 0;
	int index_point = 0;
	struct line_pnts* sites;
	int i;
	struct line_cats* cats;
	int cat = 0;
	int type;
	
	sites = Vect_new_line_struct();
	cats = Vect_new_cats_struct();
	
	count( map, num_points, num_lines);
	
	*points = G_malloc( *num_points * sizeof( struct Point ));
	*lines = G_malloc( *num_lines * sizeof( struct Line ));
	
	
	
	while( ( type = Vect_read_next_line( map, sites, cats) ) > -1 )
	{
	
		if ( type != GV_LINE && type != GV_BOUNDARY && type != GV_POINT)
			continue;
		
		if ( type == GV_LINE )
			process_line(sites, points, &index_point, lines, &index_line, -1);
		else if ( type == GV_BOUNDARY )
			process_boundary(sites, points, &index_point, lines, &index_line, cat++);
		else if ( type == GV_POINT )
			process_point( sites, points, &index_point, -1);
		
		
	}
}

void process_point( struct line_pnts * sites, struct Point ** points, int * index_point, int cat)
{
	(*points)[*index_point].x = sites->x[0];
	(*points)[*index_point].y = sites->y[0];
	(*points)[*index_point].cat = cat;

	(*points)[*index_point].line1 = NULL;
	(*points)[*index_point].line2 = NULL;
		
	(*points)[*index_point].left_brother = NULL;
	(*points)[*index_point].right_brother = NULL;
	(*points)[*index_point].father = NULL;
	(*points)[*index_point].rightmost_son = NULL;	
	
	(*index_point)++;
}

/** extract all segments from the line 
*/
void process_line( struct line_pnts * sites, struct Point ** points, int * index_point, struct Line ** lines, int * index_line, int cat)
{
	int n = sites->n_points;
	int i;

	for ( i = 0; i < n; i++ )
	{
	
		(*points)[*index_point].x = sites->x[i];
		(*points)[*index_point].y = sites->y[i];
		(*points)[*index_point].cat = cat;
		
		if ( i == 0 )
		{
			(*points)[*index_point].line1 = NULL;
			(*points)[*index_point].line2 = &((*lines)[*index_line]);
		}
		else if ( i == n-1 )
		{
			(*points)[*index_point].line1 = &((*lines)[(*index_line)-1]);
			(*points)[*index_point].line2 = NULL;
		}	
		else
		{
			(*points)[*index_point].line1 = &((*lines)[(*index_line)-1]);
			(*points)[*index_point].line2 = &((*lines)[*index_line]);
		}
		
		(*points)[*index_point].left_brother = NULL;
		(*points)[*index_point].right_brother = NULL;
		(*points)[*index_point].father = NULL;
		(*points)[*index_point].rightmost_son = NULL;
		
		
		(*index_point)++;
		
		if ( i < n-1 )
		{
			(*lines)[*index_line].p1 = &((*points)[(*index_point)-1]);
			(*lines)[*index_line].p2 = &((*points)[*index_point]);
			(*index_line)++;
		}
	}
}

/** extract all segments from the boundary 
*/
void process_boundary( struct line_pnts * sites, struct Point ** points, int * index_point, struct Line ** lines, int * index_line, int cat)
{
	int n = sites->n_points;
	int i; 

	for ( i = 0; i < n-1; i++ )
	{
		(*points)[*index_point].cat = cat;
		(*points)[*index_point].x = sites->x[i];
		(*points)[*index_point].y = sites->y[i];
		
		if ( i == 0 )
		{
			(*points)[*index_point].line1 = &((*lines)[(*index_line)+n-2]);
			(*points)[*index_point].line2 = &((*lines)[*index_line]);
		}	
		else
		{
			(*points)[*index_point].line1 = &((*lines)[(*index_line)-1]);
			(*points)[*index_point].line2 = &((*lines)[*index_line]);
		}
		
		(*points)[*index_point].left_brother = NULL;
		(*points)[*index_point].right_brother = NULL;
		(*points)[*index_point].father = NULL;
		(*points)[*index_point].rightmost_son = NULL;
		
		
		(*index_point)++;
		
		if ( i == n-2 )
		{
			(*lines)[*index_line].p1 = &((*points)[(*index_point)-1]);
			(*lines)[*index_line].p2 = &((*points)[(*index_point)-n+2]);
		}
		else
		{
			(*lines)[*index_line].p1 = &((*points)[(*index_point)-1]);
			(*lines)[*index_line].p2 = &((*points)[*index_point]);
		}
			
		(*index_line)++;
	}

}

