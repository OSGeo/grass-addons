
/****************************************************************************
 *
 * MODULE:       r.crater
 * AUTHOR(S):    Yann Chemin - yann.chemin@gmail.com
 * PURPOSE:      Creates craters from meteorites
 *               or meteorites from craters
 *               original code was in fortran77 from Meloch
 *
 * COPYRIGHT:    (C) 2013 by the GRASS Development Team
 *
 *               This program is free software under the GNU General Public
 *   	    	 License (>=v2). Read the file COPYING that comes with GRASS
 *   	    	 for details.
 *
 *****************************************************************************/
     
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <grass/gis.h>
#include <grass/raster.h>
#include <grass/glocale.h>

int main(int argc, char *argv[]) 
{
    int nrows, ncols;
    int row, col;
    struct GModule *module;
    struct Flag *flag, *flag1, *flag2, *flag3;
    struct Option *input1, *input2, *input3, *input4, *input5;
    struct Option *input6, *input7, *input8, *input9, *output;
    struct History history;	/*metadata */

    char *result;		/*output raster name */
    int infd_v, infd_theta, infd_rhotarget;
    int infd_g, infd_rhoproj, infd_ttyp, infd_ttype;
    int infd_L, infd_Dt, infd_Dfinal;/*Modes parameters*/
    int outfd;
    char *ivelocity, *iangle, *idensity, *idiameter; /*Impactor*/
    char *tg, *ttype, *tdensity; /*Target*/
    char *tcrater_diameter_transient, *tcrater_diameter_final; /*Target crater*/ 
    void *inrast_v, *inrast_theta, *inrast_rhotarget;
    void *inrast_g, *inrast_ttype, *inrast_rhoproj;
    void *inrast_L, *inrast_Dt, *inrast_Dfinal;
    DCELL *outrast;
    
    /************************************/ 
    G_gisinit(argv[0]);
    module = G_define_module();
    G_add_keyword(_("raster"));
    G_add_keyword(_("planetary"));
    G_add_keyword(_("impact"));
    G_add_keyword(_("meteorite"));
    G_add_keyword(_("crater"));
    module->description = _("Creates meteorites from craters (-c) or craters from meteorites (default).");
    
    /* Define the different options */ 
    input1 = G_define_standard_option(G_OPT_R_INPUT);
    input1->key = "impactor_velocity";
    input1->description = _("Name of impactor velocity raster map [km/s]");

    input2 = G_define_standard_option(G_OPT_R_INPUT);
    input2->key = "impactor_angle";
    input2->description = _("Name of impactor angle raster map [dd.ddd]");

    input3 = G_define_standard_option(G_OPT_R_INPUT);
    input3->key = "target_density";
    input3->description = _("Name of target density raster map [kg/m^3]");

    input4 = G_define_standard_option(G_OPT_R_INPUT);
    input4->key = "gravity_acceleration";
    input4->description = _("Name of gravity acceleration raster map [m/s^-2]");

    input5 = G_define_standard_option(G_OPT_R_INPUT);
    input5->key = "target_type";
    input5->description = _("Name of target type raster map [1=liq.H2O, 2=Loose Sand, 3=Competent Rock/Saturated Soil]");
    /**TODO Think about modeling impact on a mixed land cover**/

    input6 = G_define_standard_option(G_OPT_R_INPUT);
    input6->key = "impactor_density";
    input6->description = _("Name of impactor density raster map [kg/m^3]");

    input7 = G_define_standard_option(G_OPT_R_INPUT);
    input7->key = "projectile_diameter";
    input7->description = _("Flag -c: Name of projectile diameter raster map [m]");
    input7->required = NO;

    input8 = G_define_standard_option(G_OPT_R_INPUT);
    input8->key = "transient_crater_diameter";
    input8->description = _("Default mode: Name of transient crater diameter raster map [kg/m^3]");
    input8->required = NO;

    input9 = G_define_standard_option(G_OPT_R_INPUT);
    input9->key = "final_crater_diameter";
    input9->description = _("Default mode: Name of final crater diameter raster map [kg/m^3]");
    input8->required = NO;

    output = G_define_standard_option(G_OPT_R_OUTPUT);
    output->description = _("Name for projectile size (default) or crater size (-c) or crater creation time (-t) raster map [m] or [s]");

    flag = G_define_flag();
    flag->key = 'c';
    flag->description = _("Estimate crater diameter from projectile size [m]");

    flag1 = G_define_flag();
    flag1->key = 't';
    flag1->description = _("output the time of crater formation for Pi scaling [s]");

    flag2 = G_define_flag();
    flag2->key = 'g';
    flag2->description = _("use the Gault instead of default Pi scaling");

    flag3 = G_define_flag();
    flag3->key = 'y';
    flag3->description = _("use the Yield instead of default Pi scaling");

    /********************/ 
    if (G_parser(argc, argv))
        exit(EXIT_FAILURE);

    /*Impactor parameters*/
    ivelocity = input1->answer;
    iangle = input2->answer;
    idensity = input6->answer;
    if(input7->answer) idiameter = input7->answer;
    /*Target parameters*/
    tg = input4->answer;
    ttype = input5->answer;
    tdensity = input3->answer;
    if(input8->answer) tcrater_diameter_transient = input8->answer;
    if(input9->answer) tcrater_diameter_final = input9->answer;
    /*output*/ 
    result = output->answer;
    
    /*Default Mode: Estimate projectile size from crater diameter*/
    int comptype = 0; 

    /*Check if return of duration of impact was requested*/
    int return_time = 0;
    if(flag1->answer) return_time = 1;

    /*Check if Gault scaling was requested */
    int scaling_law = 0;
    if(flag2->answer && !flag3->answer) scaling_law = 1;
    if(flag3->answer && !flag2->answer) scaling_law = 2;
    if(flag2->answer && flag3->answer){
        scaling_law = 0;
        G_message("Confusion for the scaling law flags, using default");
    }
    if(flag->answer && input7->answer){
        /*Flagged Mode: Estimate crater diameter from projectile size*/
        infd_L = Rast_open_old(idiameter, "");
        inrast_L = Rast_allocate_d_buf();
        comptype = 1;/*Switch to pass to crater function for non default mode*/
        /*Projectile Diameter Size*/
    }else{
        /*Default Mode: Estimate projectile size from crater diameter*/
        infd_Dt = Rast_open_old(tcrater_diameter_transient, "");
        inrast_Dt = Rast_allocate_d_buf();
        /*Transient Crater Diameter*/

        infd_Dfinal = Rast_open_old(tcrater_diameter_final, "");
        inrast_Dfinal = Rast_allocate_d_buf();
        /*If known, the final crater diameter*/
    }

    /***************************************************/ 
    infd_v = Rast_open_old(ivelocity, "");
    inrast_v = Rast_allocate_d_buf();
    /*v = Impact velocity in km/s*/

    infd_theta = Rast_open_old(iangle, "");
    inrast_theta = Rast_allocate_d_buf();
    /*theta = Impact angle in degrees*/

    infd_rhotarget = Rast_open_old(tdensity, "");
    inrast_rhotarget = Rast_allocate_d_buf();
    /*rhotarget = Target Density in kg/m^3*/

    infd_g = Rast_open_old(tg, "");
    inrast_g = Rast_allocate_d_buf();
    /*g = Acceleration of gravity in m/s*/

    infd_ttype = Rast_open_old(ttype, "");
    inrast_ttype = Rast_allocate_d_buf();
    /*targype = liqH2O=1 Loose_Sand=2 Competent_rock/saturated_soil=3*/

    infd_rhoproj = Rast_open_old(idensity, "");
    inrast_rhoproj = Rast_allocate_d_buf();
    /*rhoproj = Density of Projectile */
    
    /***************************************************/ 
    nrows = Rast_window_rows();
    ncols = Rast_window_cols();
    outrast = Rast_allocate_d_buf();
    
    /* Create New raster files */ 
    outfd = Rast_open_new(result, DCELL_TYPE);
    
    /* Process pixels */ 
    for (row = 0; row < nrows; row++)
    {
	DCELL d;
	DCELL d_v;
	DCELL d_theta;
	DCELL d_rhotarget;
	DCELL d_rhoproj;
	DCELL d_g;
	DCELL d_ttype;
        DCELL d_L;
        DCELL d_Dt;
        DCELL d_Dfinal;
	G_percent(row, nrows, 2);
	
	/* read input maps */ 
	Rast_get_d_row(infd_v, inrast_v, row);
	Rast_get_d_row(infd_theta, inrast_theta, row);
	Rast_get_d_row(infd_rhotarget, inrast_rhotarget, row);
	Rast_get_d_row(infd_rhoproj, inrast_rhoproj, row);
	Rast_get_d_row(infd_g, inrast_g, row);
	Rast_get_d_row(infd_ttype, inrast_ttype, row);
        if(flag->answer && input7->answer){
            Rast_get_d_row(infd_L, inrast_L, row);
	}else{
            Rast_get_d_row(infd_Dt, inrast_Dt, row);
            Rast_get_d_row(infd_Dfinal, inrast_Dfinal, row);
        }
	
        /*process the data */ 
	for (col = 0; col < ncols; col++)
	{
	    d_v = ((DCELL *) inrast_v)[col];
	    d_theta = ((DCELL *) inrast_theta)[col];
	    d_rhotarget = ((DCELL *) inrast_rhotarget)[col];
	    d_rhoproj = ((DCELL *) inrast_rhoproj)[col];
            d_g = ((DCELL *) inrast_g)[col];
            d_ttype = ((DCELL *) inrast_ttype)[col];
            if(flag->answer){
                d_L = ((DCELL *) inrast_L)[col];
            } else {
                d_Dt = ((DCELL *) inrast_Dt)[col];
                d_Dfinal = ((DCELL *) inrast_Dfinal)[col];
            }
	    if (Rast_is_d_null_value(&d_v) || 
                Rast_is_d_null_value(&d_theta) ||
                Rast_is_d_null_value(&d_rhotarget) ||
                Rast_is_d_null_value(&d_rhoproj) ||
                Rast_is_d_null_value(&d_g) ||
                Rast_is_d_null_value(&d_ttype) ||
                ((d_ttype < 1) || (d_ttype > 3)) ||
                Rast_is_d_null_value(&d_rhoproj) ||
                ((input7->answer)&&(Rast_is_d_null_value(&d_L))) ||
                ((input8->answer)&&(Rast_is_d_null_value(&d_Dt))) ||
                ((input9->answer)&&(Rast_is_d_null_value(&d_Dfinal))) ) 
		    Rast_set_d_null_value(&outrast[col], 1);
	    else {
                if(flag->answer){
                    d_Dt = 0.0;
                    d_Dfinal = 0.0;
                } else {
                    d_L = 0.0;
                }
                d = crater(d_v, d_theta, d_rhotarget, d_g, d_ttype, d_rhoproj, d_L, d_Dt, d_Dfinal, scaling_law, return_time, comptype);
		outrast[col] = d;
            }
	}
	Rast_put_d_row(outfd, outrast);
    }
    G_free(inrast_v);
    G_free(inrast_theta);
    G_free(inrast_rhoproj);
    G_free(inrast_g);
    Rast_close(infd_v);
    Rast_close(infd_theta);
    Rast_close(infd_rhotarget);
    Rast_close(infd_rhoproj);
    Rast_close(infd_g);
    G_free(outrast);
    Rast_close(outfd);
    
    Rast_short_history(result, "raster", &history);
    Rast_command_history(&history);
    Rast_write_history(result, &history);
    
    exit(EXIT_SUCCESS);
}
