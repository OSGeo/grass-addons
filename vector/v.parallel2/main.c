/***************************************************************
 *
 * MODULE:       v.parallel
 * 
 * AUTHOR(S):    Radim Blazek, Rosen Matev
 *               
 * PURPOSE:      Create parallel lines
 *               
 * COPYRIGHT:    (C) 2001 by the GRASS Development Team
 *
 *               This program is free software under the 
 *               GNU General Public License (>=v2). 
 *               Read the file COPYING that comes with GRASS
 *               for details.
 *
 * TODO/BUG:     The vector segments are not properly connected
 *               and should be snapped.
 **************************************************************/
#include <stdlib.h> 
#include <math.h>
#include <grass/gis.h>
#include <grass/Vect.h>
#include <grass/glocale.h>

int main (int argc, char *argv[])
{
    struct GModule *module;
    struct Option *in_opt, *out_opt, *dista_opt;
    struct Option *distb_opt, *angle_opt, *side_opt;
    struct Option *tol_opt;
    struct Flag *round_flag, *loops_flag;
    struct Map_info In, Out;
    struct line_pnts *Points, *Points2;
    struct line_cats *Cats;
    int    line, nlines;
    double da, db, dalpha, tolerance;
    int side;

    G_gisinit(argv[0]);

    module = G_define_module();
    module->keywords = _("vector, geometry");
    module->description = _("Create parallel line to input lines");

    in_opt = G_define_standard_option(G_OPT_V_INPUT);
    out_opt = G_define_standard_option(G_OPT_V_OUTPUT);
    /* layer_opt = G_define_standard_option(G_OPT_V_FIELD); */
    
    dista_opt = G_define_option();
    dista_opt->key = "distance";
    dista_opt->type =  TYPE_DOUBLE;
    dista_opt->required = YES;
    dista_opt->multiple = NO;
    dista_opt->description = _("Offset along major axis in map units");

    distb_opt = G_define_option();
    distb_opt->key = "minordistance";
    distb_opt->type =  TYPE_DOUBLE;
    distb_opt->required = NO;
    distb_opt->multiple = NO;
    distb_opt->description = _("Offset along minor axis in map units");

    angle_opt = G_define_option();
    angle_opt->key = "angle";
    angle_opt->type =  TYPE_DOUBLE;
    angle_opt->required = NO;
    angle_opt->answer = "0";
    angle_opt->multiple = NO;
    angle_opt->description = _("Angle of major axis in degrees");

    side_opt = G_define_option();
    side_opt->key = "side";
    side_opt->type =  TYPE_STRING;
    side_opt->required = YES;
    side_opt->answer = "right";
    side_opt->multiple = NO;
    side_opt->options = "left,right";
    side_opt->description = _("left;Parallel line is on the left;right;Parallel line is on the right;");

    tol_opt = G_define_option();
    tol_opt->key = "tolerance";
    tol_opt->type =  TYPE_DOUBLE;
    tol_opt->required = NO;
    tol_opt->multiple = NO;
    tol_opt->description = _("Tolerance of arc polylines in map units");

    round_flag = G_define_flag();
    round_flag->key = 'r';
    round_flag->description = _("Make outside corners round");

    loops_flag = G_define_flag();
    loops_flag->key = 'l';
    loops_flag->description = _("Don't remove loops");
    
    if (G_parser (argc, argv))
        exit(EXIT_FAILURE);

    /* layer = atoi ( layer_opt->answer ); */
    da = atof(dista_opt->answer);
    
    if (distb_opt->answer)
        db = atof(distb_opt->answer);
    else
        db = da;
        
    if (angle_opt->answer)
        dalpha = atof(angle_opt->answer);
    else
        dalpha = 0;
        
    if (tol_opt->answer)
        tolerance = atof(tol_opt->answer);
    else
        tolerance = ((db<da)?db:da)/10.;
            
    if (strcmp(side_opt->answer, "right") == 0)
        side = 1;
    else if (strcmp(side_opt->answer, "left") == 0)
        side = -1;

    Vect_set_open_level (2); 
    Vect_open_old (&In, in_opt->answer, ""); 
    Vect_open_new (&Out, out_opt->answer, 0);
    Vect_copy_head_data (&In, &Out);
    Vect_hist_copy (&In, &Out);
    Vect_hist_command ( &Out );
    
    Points = Vect_new_line_struct ();
    Points2 = Vect_new_line_struct ();
    Cats = Vect_new_cats_struct ();

    nlines = Vect_get_num_lines ( &In );

    for ( line = 1; line <= nlines; line++ ) {
        int ltype;
        
        G_percent ( line, nlines, 1 );
        
        ltype = Vect_read_line ( &In, Points, Cats, line);
        
        if ( ltype & GV_LINES ) {
            Vect_line_parallel2(Points, da, db, dalpha, side, round_flag->answer, loops_flag->answer, tolerance, Points2);
            Vect_write_line(&Out, ltype, Points2, Cats);
        } else {
            Vect_write_line(&Out, ltype, Points, Cats);
        }
    }
    
    Vect_close (&In);
    Vect_build (&Out, stderr);
    Vect_close (&Out);

    exit(EXIT_SUCCESS) ;
}

