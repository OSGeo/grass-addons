/****************************************************************************
 *
 * MODULE:       i.eb.ustar
 * AUTHOR(S):    Yann Chemin - yann.chemin@gmail.com
 * PURPOSE:      Calculates the nominal wind speed
 *
 * COPYRIGHT:    (C) 2002-2008 by the GRASS Development Team
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
#include <grass/glocale.h>


double u_star(double ublend,double hblend,double disp,double z0m,double psim);

int main(int argc, char *argv[])
{
	struct Cell_head cellhd; /*region+header info*/
	char *mapset; /*mapset name*/
	int nrows, ncols;
	int row,col;

	struct GModule *module;
	struct Option *input1, *input2, *input3, *input4, *input5, *output1;
	
	struct Flag *flag1;	
	struct History history; /*metadata*/
	
	/************************************/
	/* FMEO Declarations*****************/
	char *name;   /*input raster name*/
	char *result; /*output raster name*/
	/*File Descriptors*/
	int infd_ublend, infd_disp,infd_z0m,infd_psim;
	int outfd;
	
	char *ublend, *disp, *z0m, *psim;

	double hblend;
	int i=0,j=0;
	
	void *inrast_ublend, *inrast_disp, *inrast_z0m, *inrast_psim;
	DCELL *outrast;
	RASTER_MAP_TYPE data_type_output=DCELL_TYPE;
	RASTER_MAP_TYPE data_type_ublend;
	RASTER_MAP_TYPE data_type_disp;
	RASTER_MAP_TYPE data_type_z0m;
	RASTER_MAP_TYPE data_type_psim;
	/************************************/
	G_gisinit(argv[0]);

	module = G_define_module();
	module->keywords = _("ustar, energy balance, SEBAL");
	module->description = _("Nominal wind speed.");

	/* Define the different options */
	input1 = G_define_standard_option(G_OPT_R_INPUT) ;
	input1->key	   = _("ublend");
	input1->description=_("Name of the wind speed at blending height layer");

	input2 = G_define_option() ;
	input2->key        =_("hblend");
	input2->type       = TYPE_DOUBLE;
	input2->required   = YES;
	input2->gisprompt  =_("Value, parameter");
	input2->description=_("Value of the blending height (100.0 in Pawan, 2004)");
	input2->answer     =_("100.0");

	input3 = G_define_standard_option(G_OPT_R_INPUT) ;
	input3->key        =_("disp");
	input3->description=_("Name of the displacement height layer");

	input4 = G_define_standard_option(G_OPT_R_INPUT) ;
	input4->key        =_("z0m");
	input4->description=_("Name of the surface roughness for momentum layer");
	
	input5 = G_define_standard_option(G_OPT_R_INPUT) ;
	input5->key        =_("psim");
	input5->description=_("Name of the psichrometric parameter for momentum layer");

	output1 = G_define_standard_option(G_OPT_R_OUTPUT) ;
	output1->description=_("Name of the output ustar layer");

	/********************/
	if (G_parser(argc, argv))
		exit (EXIT_FAILURE);

	ublend	 	= input1->answer;
	hblend	 	= atof(input2->answer);
	disp	 	= input3->answer;
	z0m	 	= input4->answer;
	psim		= input5->answer;
	
	result  = output1->answer;
	/***************************************************/
	mapset = G_find_cell2 (ublend, "");
	if (mapset == NULL) {
		G_fatal_error(_("Cell file [%s] not found"), ublend);
	}
	data_type_ublend = G_raster_map_type(ublend,mapset);
	if ( (infd_ublend = G_open_cell_old (ublend,mapset)) < 0)
		G_fatal_error(_("Cannot open cell file [%s]"), ublend);
	if (G_get_cellhd (ublend, mapset, &cellhd) < 0)
		G_fatal_error(_("Cannot read file header of [%s]"), ublend);
	inrast_ublend = G_allocate_raster_buf(data_type_ublend);
	/***************************************************/
	mapset = G_find_cell2 (disp, "");
	if (mapset == NULL) {
		G_fatal_error(_("Cell file [%s] not found"), disp);
	}
	data_type_disp = G_raster_map_type(disp,mapset);
	if ( (infd_disp = G_open_cell_old (disp,mapset)) < 0)
		G_fatal_error(_("Cannot open cell file [%s]"), disp);
	if (G_get_cellhd (disp, mapset, &cellhd) < 0)
		G_fatal_error(_("Cannot read file header of [%s]"), disp);
	inrast_disp = G_allocate_raster_buf(data_type_disp);
	/***************************************************/
	mapset = G_find_cell2 (z0m, "");
	if (mapset == NULL) {
		G_fatal_error(_("Cell file [%s] not found"), z0m);
	}
	data_type_z0m = G_raster_map_type(z0m,mapset);
	if ( (infd_z0m = G_open_cell_old (z0m,mapset)) < 0)
		G_fatal_error(_("Cannot open cell file [%s]"), z0m);
	if (G_get_cellhd (z0m, mapset, &cellhd) < 0)
		G_fatal_error(_("Cannot read file header of [%s]"), z0m);
	inrast_z0m = G_allocate_raster_buf(data_type_z0m);
	/***************************************************/
	mapset = G_find_cell2 (psim, "");
	if (mapset == NULL) {
		G_fatal_error(_("Cell file [%s] not found"), psim);
	}
	data_type_psim = G_raster_map_type(psim,mapset);
	if ( (infd_psim = G_open_cell_old (psim,mapset)) < 0)
		G_fatal_error(_("Cannot open cell file [%s]"), psim);
	if (G_get_cellhd (psim, mapset, &cellhd) < 0)
		G_fatal_error(_("Cannot read file header of [%s]"), psim);
	inrast_psim = G_allocate_raster_buf(data_type_psim);
	/***************************************************/
	G_debug(3, "number of rows %d",cellhd.rows);
	nrows = G_window_rows();
	ncols = G_window_cols();
	outrast = G_allocate_raster_buf(data_type_output);
	/* Create New raster files */
	if ( (outfd = G_open_raster_new (result,data_type_output)) < 0)
		G_fatal_error(_("Could not open <%s>"),result);
	/* Process pixels */
	for (row = 0; row < nrows; row++)
	{
		DCELL d;
		DCELL d_ublend;
		DCELL d_disp;
		DCELL d_z0m;
		DCELL d_psim;
		DCELL d_ustar;
		G_percent(row,nrows,2);
		/* read input maps */	
		if(G_get_raster_row(infd_ublend,inrast_ublend,row,data_type_ublend)<0)
			G_fatal_error(_("Could not read from <%s>"),ublend);
		if(G_get_raster_row(infd_disp,inrast_disp,row,data_type_disp)<0)
			G_fatal_error(_("Could not read from <%s>"),disp);
		if(G_get_raster_row(infd_z0m,inrast_z0m,row,data_type_z0m)<0)
			G_fatal_error(_("Could not read from <%s>"),z0m);
		if(G_get_raster_row(infd_psim,inrast_psim,row,data_type_psim)<0)
			G_fatal_error(_("Could not read from <%s>"),psim);
		/*process the data */
		for (col=0; col < ncols; col++)
		{
			d_ublend = ((DCELL *) inrast_ublend)[col];
			d_disp = ((DCELL *) inrast_disp)[col];
			d_z0m = ((DCELL *) inrast_z0m)[col];
			d_psim = ((DCELL *) inrast_psim)[col];
			if(G_is_d_null_value(&d_disp)||
			G_is_d_null_value(&d_z0m)||
			G_is_d_null_value(&d_psim)||
			G_is_d_null_value(&d_ublend)){
				G_set_d_null_value(&outrast[col],1);
			}else {
				/************************************/
				/* calculate ustar   */
				d_ustar=u_star(d_ublend, hblend, d_disp, d_z0m, d_psim);
				outrast[col] = d_ustar;
			}
		}
		if (G_put_raster_row (outfd, outrast, data_type_output) < 0)
			G_fatal_error(_("Cannot write to output raster file"));
	}
	G_free (inrast_ublend);
	G_free (inrast_disp);
	G_free (inrast_z0m);
	G_free (inrast_psim);

	G_close_cell (infd_ublend);
	G_close_cell (infd_disp);
	G_close_cell (infd_z0m);
	G_close_cell (infd_psim);
	
	G_free (outrast);
	G_close_cell (outfd);

	G_short_history(result, "raster", &history);
	G_command_history(&history);
	G_write_history(result,&history);

	exit(EXIT_SUCCESS);
}

