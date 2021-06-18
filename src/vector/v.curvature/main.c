/****************************************************************
* 
*  MODULE:       v.curvature
*  
*  AUTHOR(S):    Radim Blazek
*                
*  PURPOSE:      Calculate something similar to curvature of line
*                in specified segment. Module reads from stdin:
*                
*                  segment_id line_category from to
*                
*                  segment_id - identifier for one segment we need curvature for 
*                  line_category - category of line the segment is on
*                  from - distance of segment start from the beginnig of the line
*                  to - distance of end of segment from the beginnig of the line
*
*                Note that if segment limits may exceed the line, segment is cuted
*                by line ends.
*
*                Output is written to stdout in format:
*
*                  segment_id average_curvature average_radius
*                
*                
*  COPYRIGHT:    (C) 2001 by the GRASS Development Team
* 
*                This program is free software under the 
*                GNU General Public License (>=v2). 
*                Read the file COPYING that comes with GRASS
*                for details.
* 
****************************************************************/
#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <math.h>
#include <grass/gis.h>
#include <grass/Vect.h>
#include <grass/glocale.h>

#define OPTION_SEGMENT 1
#define OPTION_LINES   2


double calc_curv (struct line_pnts *Points, int part);
double part_length (struct line_pnts *Points, int part);

int 
main (int argc, char *argv[])
{
    int    i, row;
    char   buf[1024];
    struct Map_info Map;
    struct line_pnts *Points;
    struct line_cats *Cats;
    int    field, type, ctype, action;
    int    id, cat, ccat, part, end;
    double from, to, rad;
    double line_len, seg_len, calc_len, part_len, rest_len, dist, len;
    double x, y, z, dx, dy, dz;
    double cur, curva;
    int field_index, cinlines;
    struct GModule *module;
    struct Option *map_opt, *type_opt, *field_opt, *act_opt;
    struct Flag *abs_flag;

    module = G_define_module();
    module->keywords = _("vector, segment, curvature");
    module->description = _("Calculate curvature. With segment option it reads from standard input:\n"
			  "segment_id line_category from to\n"
			  "and writes to standard output:\n"
			  "segment_id average_curvature average_radius\n"
			  "If a segment given runs outside the line, it is cut. "
			  "If more lines with the same category "
			  "are found, curvature is not calculated and warning is printed.");

    map_opt = G_define_standard_option(G_OPT_V_INPUT);
    map_opt->key = "map";
    
    type_opt = G_define_standard_option(G_OPT_V_TYPE) ;
    type_opt->options = "line,boundary";
    type_opt->answer = "line";

    field_opt = G_define_standard_option(G_OPT_V_FIELD);

    act_opt = G_define_option() ;
    act_opt->key        = "option" ;
    act_opt->type       = TYPE_STRING ;
    act_opt->required   = NO ;
    act_opt->multiple   = NO;
    act_opt->answer     = "segment" ;
    act_opt->options    = "segment,lines";
    act_opt->description= _("Option");
    act_opt->descriptions= _("segment; reads segments from standard input;"
			   "lines; calculate curvature for all sements of all lines");
    
    abs_flag = G_define_flag ();
    abs_flag->key         = 'a';
    abs_flag->description = _("Calculate average from absolute values "
			    "(if not used, segment over 2 successive contrary "
			    "curves can result in curvature near 0).");
    
    G_gisinit(argv[0]);
    if (G_parser (argc, argv))
	exit(EXIT_FAILURE); 
    
    field = atoi( field_opt->answer );
    
    i = 0;
    ctype = 0;
    while (type_opt->answers[i])
    {
	switch ( type_opt->answers[i][0] )
	{
	    case 'l':
		ctype |= GV_LINE;
		break;
	    case 'b':
		ctype |= GV_BOUNDARY;
		break;
	}
	i++;
    }

    action = OPTION_SEGMENT;
    if ( act_opt->answer[0] == 'l' )
        action = OPTION_LINES;

    Points = Vect_new_line_struct ();
    Cats = Vect_new_cats_struct ();
    
    /* open input vector */
    Vect_set_open_level (2); 
    Vect_open_old (&Map, map_opt->answer, "");

    cinlines = Vect_cidx_get_type_count ( &Map, field, ctype);

    if ( cinlines == 0 ) 
    { 
	G_warning ( _("No lines in layer %d"), field );
    }

    if ( action == OPTION_SEGMENT && cinlines > 0 ) {
	int idx, line, type, cincats, dummy1, dummy2;

	field_index = Vect_cidx_get_field_index ( &Map, field );
	cincats = Vect_cidx_get_num_cats_by_index ( &Map, field_index );
        G_debug ( 3, "cincats = %d", cincats );

	row = 0;
	while ( fgets(buf,1024,stdin) != NULL ) {
	    row++;
	    if ( sscanf(buf, "%d %d %lf %lf", &id, &ccat, &from, &to) != 4 ) {
		 G_warning (_("Incorrect format on row %d: %s"), row, buf); 
		 continue;
	    }

	    G_debug (2, "read: %d %d %f %f", id, ccat, from, to);

	    /* Find line by category */
	    idx = Vect_cidx_find_next ( &Map, field_index, ccat, ctype, 0, &type, &line );
	
            if ( idx < 0 ) {
		G_warning ( _("Line with category %d not found"), ccat );
		fprintf (stdout, "%d - -\n", id);
		continue;
	    }
        
            if ( (idx + 1 < cincats) &&
		 Vect_cidx_find_next ( &Map, field_index, ccat, ctype, idx+1, &dummy1, &dummy2 ) >= 0 )
            {
		/* Second line found */
		G_warning ( _("More lines with category %d found"), ccat );
		fprintf (stdout, "%d - -\n", id);
		continue;
	    }
	    
	    Vect_read_line ( &Map, Points, Cats, line );
		
	    G_debug (2, "n_points = %d", Points->n_points );
	    if ( Points->n_points < 2 ) {
		G_warning ( _("Degenerated line with category %d"), ccat );
		fprintf (stdout, "%d - -\n", id);
		continue; 
	    }

	    line_len = Vect_line_length (Points);
	    
	    if ( from > line_len || to < 0 ) { 
		G_warning ( _("Segment outside the line (id = %d)"), id );
		fprintf (stdout, "%d - -\n", id);
		continue;
	    }
	    
	    if ( from < 0 ) {
		G_warning ( _("Start of segment %d < 0"), id );
		from = 0.;
	    }
	    if ( to > line_len ) {
		G_warning ( _("End of segment %d > line length"), id );
		to = line_len;
	    }	
	    seg_len = to - from;
	    G_debug (2, "seg_len = %f", seg_len);
	    
	    /* first segment */
	    part = Vect_point_on_line ( Points, from, &x, &y, &z, NULL, NULL );
	    G_debug (2, "first part = %d", part);

	    /* distance from the beginnig of line part */
	    dx = x - Points->x[part-1];
	    dy = y - Points->y[part-1];
	    dz = z - Points->z[part-1];
	    dist = hypot (dx, dy);
	    dist = hypot (dist, dz);
	    
	    calc_len = 0; curva = 0; end = 0;
	    for ( i = part; i < Points->n_points; i++ ) {
		G_debug (2, "i = %d", i);
		
		part_len = part_length (Points, i);
		cur = calc_curv (Points, i);
		if (abs_flag->answer && (cur < 0) ) cur = -cur;
		
		rest_len = seg_len - calc_len;

		/* length of used part of part */	
		if ( part_len >= (rest_len + dist) ) { /* end of segment reached */
		    len =  rest_len;
		    end = 1;
		} else {
		    len = part_len - dist;
		}
		G_debug (2, "part_len = %f len = %f", part_len, len);
	
	  
		/* cumulate curvature */
		curva += cur * len; 
		G_debug (2, "curva = %f", curva );
		
		calc_len += len; 
		
		if ( end ) break;
		
		dist = 0; /* start of segment from the beginnig of part for next parts */
	    }

	    curva /= seg_len; 
	    rad = 1 / curva;        
	   
	    fprintf (stdout, "%d %f %f\n", id, curva, rad);
	    fflush (stdout);
	}
    } else if ( OPTION_LINES && cinlines > 0 ) { 
	Vect_rewind ( &Map );
	while ( (type = Vect_read_next_line (&Map, Points, Cats)) > 0) {
	    if ( !(type & ctype) ) continue;
	    
            /* TODO: more cats int the same layer */ 
	    cat = 0;
	    if( Vect_cat_get(Cats, field, &cat) == 0 ) {
		continue;
	    }
       
	    G_debug (2, "n_points = %d", Points->n_points );
	    if ( Points->n_points < 2 ) {
		G_warning ( _("Degenerated line with category %d"), ccat );
		continue; 
	    }

	    for ( part = 1; part < Points->n_points; part++ ) {
		G_debug (2, "part = %d", part);
		
		part_len = part_length (Points, part);
		cur = calc_curv (Points, part);
                if (abs_flag->answer && (cur < 0) ) cur = -cur;

		rad = 1 / cur;        
	       
		fprintf (stdout, "%d %f %f %f\n", cat, part_len, cur, rad);
		fflush (stdout);
	    }
	}
    }

    Vect_close (&Map);

    exit(EXIT_SUCCESS) ;
}

/* Calculate curvature of segment */
double calc_curv (struct line_pnts *Points, int part)
{
    double part_len;
    double dx, dy;
    double ang, ang1, ang2, part_ang, cur;

    /* segment angle */     
    dx = Points->x[part] - Points->x[part-1];
    dy = Points->y[part] - Points->y[part-1];
    part_ang = atan2 ( dy, dx );  
    G_debug (2, "part: dx = %f dy = %f part_ang = %f", dx, dy, part_ang);
    
    /* angle 1 */
    if ( part == 1 ) { /* first segment */
	ang1 = 0;
	G_debug (2, "1: first seg ang1 = 0");
    } else { 
	dx = Points->x[part-1] - Points->x[part-2];
	dy = Points->y[part-1] - Points->y[part-2];
	ang = atan2 ( dy, dx );  
	ang1 = part_ang - ang;  
	G_debug (2, "1: %d->%d: %f, %f -> %f, %f",part-2,part-1,
		    Points->x[part-2], Points->y[part-2],  Points->x[part-1], Points->y[part-1] );
	G_debug (2, "1: dx = %f dy = %.10f ang = %f, ang1 = %f", dx, dy, ang, ang1);
	if ( ang1 < -M_PI ) ang1 += 2 * M_PI;
	if ( ang1 >  M_PI ) ang1 -= 2 * M_PI;
	G_debug (2, "1: -> ang1 = %f", ang1);
    }
    /* angle 2 */
    if ( part == Points->n_points - 1 ) { /* last segment */
	ang2 = 0;
	G_debug (2, "2: last seg ang2 = 0");
    } else { 
	dx = Points->x[part+1] - Points->x[part];
	dy = Points->y[part+1] - Points->y[part];
	ang = atan2 ( dy, dx );
	ang2 = ang - part_ang;
	G_debug (2, "2: %d->%d: %f, %f -> %f, %f",part,part+1,
		    Points->x[part+1], Points->y[part+1],  Points->x[part], Points->y[part] );
	G_debug (2, "2: dx = %f dy = %.10f ang = %f ang2 = %f", dx, dy, ang, ang2);
	if ( ang2 < -M_PI ) ang2 += 2 * M_PI;
	if ( ang2 >  M_PI ) ang2 -= 2 * M_PI;
	G_debug (2, "2: -> ang2 = %f", ang2);
    }
    
    /* curvature */
    part_len = part_length (Points, part);
    cur =  2 * sin ( (ang1 + ang2) / 4 ) / part_len ;

    G_debug (2, "cur = %f R = %f", cur, 1/cur );

    return cur;
}

double part_length (struct line_pnts *Points, int part) {
    double dx, dy, dz, len;
    
    /* length of segment */
    dx = Points->x[part] - Points->x[part-1];
    dy = Points->y[part] - Points->y[part-1];
    dz = Points->z[part] - Points->z[part-1];
    len = hypot (dx, dy);
    len = hypot (len, dz);

    return len;
}

