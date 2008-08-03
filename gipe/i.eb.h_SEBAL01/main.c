/****************************************************************************
 *
 * MODULE:       i.eb.h_SEBAL01
 * AUTHOR(S):    Yann Chemin - yann.chemin@gmail.com
 * PURPOSE:      Calculates sensible heat flux by SEBAL iteration
 *               Delta T will be reassessed in the iterations !
 *               This has been seen in Bastiaanssen (1995), 
 *               later modified by Chemin and Alexandridis (2001).
 *
 * COPYRIGHT:    (C) 2002-2009 by the GRASS Development Team
 *
 *               This program is free software under the GNU General Public
 *   	    	 License (>=v2). Read the file COPYING that comes with GRASS
 *   	    	 for details.
 *
 * CHANGELOG:	
 *
 *****************************************************************************/

#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <math.h>
#include <grass/gis.h>
#include <grass/glocale.h>

#define PI 3.14159265358979

double **G_alloc_matrix (int rows, int cols)
{
	double **m;
	int i;
	m = (double **) G_calloc (rows, sizeof(double *));
	m[0] = (double *) G_calloc (rows*cols, sizeof(double));
	for (i = 1; i < rows; i++)
		m[i] = m[i-1] + cols;
		
	return m;	
}

int main(int argc, char *argv[])
{	
	struct Cell_head cellhd;
	char *mapset; // mapset name
	
	/* buffer for in, tmp and out raster */
	void *inrast_z0m, *inrast_t0dem;
	DCELL *outrast;
	
	int nrows, ncols;
	int row, col;
	int row_wet, col_wet;
	int row_dry, col_dry;
	double m_row_wet, m_col_wet;
	double m_row_dry, m_col_dry;
	int infd_z0m, infd_t0dem;
	//int tmprohfd, tmprahfd;
	int outfd;
	
	char *mapset_z0m, *mapset_t0dem;
	char *z0m, *t0dem; 
	char *h0;
	double ustar, ea, h_dry;
	
        struct History history;
	struct GModule *module;
	struct Option *input_z0m, *input_t0dem, *input_ustar;
	struct Option *input_ea, *input_h_dry, *output;
	struct Option *input_row_wet, *input_col_wet;
	struct Option *input_row_dry, *input_col_dry;
	struct Flag *flag3;
	/********************************/
	RASTER_MAP_TYPE data_type_z0m;
	RASTER_MAP_TYPE data_type_t0dem;
	RASTER_MAP_TYPE data_type_output=DCELL_TYPE;
	/********************************/
	double xp, yp;
	double xmin, ymin;
	double xmax, ymax;
	double stepx,stepy;
	double latitude, longitude;

	int rowDry, colDry, rowWet, colWet;
	/********************************/
	G_gisinit(argv[0]);
	
	module = G_define_module();
	module->description = _("Sensible Heat Flux iteration SEBAL 01");
	
	/* Define different options */
	input_z0m = G_define_standard_option(G_OPT_R_INPUT);
	input_z0m->key	= "z0m";
	input_z0m->description = _("Name of aerodynamic resistance to heat momentum [s/m]");

	input_t0dem = G_define_standard_option(G_OPT_R_INPUT);
	input_t0dem->key	= "t0dem";
	input_t0dem->description = _("Name of altitude corrected surface temperature [K]");
		
	input_ustar 			= G_define_option();
	input_ustar->key		= "ustar";
	input_ustar->type 		= TYPE_DOUBLE;
	input_ustar->required 		= YES;
	input_ustar->gisprompt 		= "old,value";
	input_ustar->answer 		= "0.32407";
	input_ustar->description 	= _("Value of the friction velocity [m/s]");
	input_ustar->guisection		= _("Parameters");
		
	input_ea 			= G_define_option();
	input_ea->key			= "ea";
	input_ea->type 			= TYPE_DOUBLE;
	input_ea->required 		= YES;
	input_ea->gisprompt 		= "old,value";
	input_ea->answer 		= "1.511";
	input_ea->description 		= _("Value of the actual vapour pressure [KPa]");
	input_ea->guisection		= _("Parameters");
		
	input_h_dry 			= G_define_option();
	input_h_dry->key		= "h_dry";
	input_h_dry->type 		= TYPE_DOUBLE;
	input_h_dry->required 		= YES;
	input_h_dry->gisprompt 		= "old,value";
	input_h_dry->answer 		= "222.07";
	input_h_dry->description 	= _("Initial value of h0 at dry pixel (Rn-g0) [W/m2]");
	input_h_dry->guisection		= _("Parameters");
	
	input_row_wet 			= G_define_option();
	input_row_wet->key		= "row_wet";
	input_row_wet->type 		= TYPE_DOUBLE;
	input_row_wet->required 	= YES;
	input_row_wet->gisprompt 	= "old,value";
	input_row_wet->description 	= _("Row value of the wet pixel");
	input_row_wet->guisection	= _("Parameters");
	
	input_col_wet 			= G_define_option();
	input_col_wet->key		= "col_wet";
	input_col_wet->type 		= TYPE_DOUBLE;
	input_col_wet->required 	= YES;
	input_col_wet->gisprompt 	= "old,value";
	input_col_wet->description 	= _("Column value of the wet pixel");
	input_col_wet->guisection	= _("Parameters");
	
	input_row_dry 			= G_define_option();
	input_row_dry->key		= "row_dry";
	input_row_dry->type 		= TYPE_DOUBLE;
	input_row_dry->required 	= YES;
	input_row_dry->gisprompt 	= "old,value";
	input_row_dry->description 	= _("Row value of the dry pixel");
	input_row_dry->guisection	= _("Parameters");
	
	input_col_dry 			= G_define_option();
	input_col_dry->key		= "col_dry";
	input_col_dry->type 		= TYPE_DOUBLE;
	input_col_dry->required 	= YES;
	input_col_dry->gisprompt 	= "old,value";
	input_col_dry->description 	= _("Column value of the dry pixel");
	input_col_dry->guisection	= _("Parameters");

	output = G_define_standard_option(G_OPT_R_OUTPUT) ;
	output->key        = "h0";
	output->description= _("Name of output sensible heat flux layer [W/m2]");
	
	/* Define the different flags */
	flag3 = G_define_flag() ;
	flag3->key         = 'c' ;
	flag3->description = _("Dry/Wet pixels coordinates are in image projection, not row/col");
	
	if (G_parser(argc, argv))
		exit(EXIT_FAILURE);
	
	/* get entered parameters */
	z0m	= input_z0m->answer;
	t0dem	= input_t0dem->answer;
	
	h0	= output->answer;

	ustar = atof(input_ustar->answer);
	ea = atof(input_ea->answer);
	h_dry = atof(input_h_dry->answer);

	m_row_wet = atof(input_row_wet->answer);
	m_col_wet = atof(input_col_wet->answer);
	m_row_dry = atof(input_row_dry->answer);
	m_col_dry = atof(input_col_dry->answer);
	if(flag3->answer){
		G_message("Manual wet/dry pixels in image coordinates");
		G_message("Wet Pixel=> x:%f y:%f",m_col_wet,m_row_wet);
		G_message("Dry Pixel=> x:%f y:%f",m_col_dry,m_row_dry);
	} else {
		G_message("Wet Pixel=> row:%.0f col:%.0f",m_row_wet,m_col_wet);
		G_message("Dry Pixel=> row:%.0f col:%.0f",m_row_dry,m_col_dry);
	}
	/* find maps in mapset */
	mapset_z0m = G_find_cell2 (z0m, "");
	if (mapset_z0m == NULL)
        	G_fatal_error (_("cell file [%s] not found"), z0m);
	mapset_t0dem = G_find_cell2 (t0dem, "");
	if (mapset_t0dem == NULL)
	        G_fatal_error (_("cell file [%s] not found"), t0dem);
	
	/* check legal output name */ 
	if (G_legal_filename (h0) < 0)
			G_fatal_error (_("[%s] is an illegal name"), h0);
		
	/* determine the input map type (CELL/FCELL/DCELL) */
	data_type_z0m 	= G_raster_map_type(z0m, mapset_z0m);
	data_type_t0dem	= G_raster_map_type(t0dem, mapset_t0dem);
	
	if ( (infd_z0m = G_open_cell_old (z0m, mapset_z0m)) < 0)
		G_fatal_error (_("Cannot open cell file [%s]"), z0m);
	if ( (infd_t0dem = G_open_cell_old (t0dem, mapset_t0dem)) < 0)
		G_fatal_error (_("Cannot open cell file [%s]"),t0dem);
	
	if (G_get_cellhd (z0m, mapset_z0m, &cellhd) < 0)
		G_fatal_error (_("Cannot read file header of [%s]"), z0m);
	if (G_get_cellhd (t0dem, mapset_t0dem, &cellhd) < 0)
		G_fatal_error (_("Cannot read file header of [%s]"), t0dem);
	
	/* Allocate input buffer */
	inrast_z0m  	= G_allocate_raster_buf(data_type_z0m);
	inrast_t0dem 	= G_allocate_raster_buf(data_type_t0dem);
	/***************************************************/
	G_debug(3, "number of rows %d",cellhd.rows);
	/***************************************************/
	/* Setup pixel location variables */
	/***************************************************/
	stepx=cellhd.ew_res;
	stepy=cellhd.ns_res;

	xmin=cellhd.west;
	xmax=cellhd.east;
	ymin=cellhd.south;
	ymax=cellhd.north;

	nrows = G_window_rows();
	ncols = G_window_cols();
	/***************************************************/
	/* Allocate output buffer */
	/***************************************************/
	outrast = G_allocate_d_raster_buf();

	if((outfd = G_open_raster_new (h0,DCELL_TYPE)) < 0)
		G_fatal_error (_("Could not open <%s>"),h0);

	/***************************************************/
	/* Allocate memory for temporary images		   */
	double **d_Roh, **d_Rah;
     	if( (d_Roh = G_alloc_matrix(nrows,ncols)) == NULL) 
		G_message("cannot allocate memory for temporary d_Roh image");
     	if( (d_Rah = G_alloc_matrix(nrows,ncols)) == NULL) 
		G_message("cannot allocate memory for temporary d_Rah image");
	/***************************************************/

	/* MANUAL T0DEM WET/DRY PIXELS */
	DCELL d_t0dem_dry;
	DCELL d_t0dem_wet;
	/*DRY PIXEL*/
	if(flag3->answer){
		/*Calculate coordinates of row/col from projected ones*/
		row = (int) (( ymax - m_row_dry ) / (double) stepy) ;
		col = (int) (( m_col_dry - xmin ) / (double) stepx) ;
		G_message("Dry Pixel | row:%i col:%i",row,col);
	} else {
		row = (int) m_row_dry;
		col = (int) m_col_dry;
		G_message("Dry Pixel | row:%i col:%i",row,col);
	}
	rowDry=row;
	colDry=col;
	if(G_get_raster_row(infd_t0dem,inrast_t0dem,row,data_type_t0dem)<0)
		G_fatal_error(_("Could not read from <%s>"),t0dem);
	switch(data_type_t0dem){
		case CELL_TYPE:
			d_t0dem_dry = (double) ((CELL *) inrast_t0dem)[col];
			break;
		case FCELL_TYPE:
			d_t0dem_dry = (double) ((FCELL *) inrast_t0dem)[col];
			break;
		case DCELL_TYPE:
			d_t0dem_dry = (double) ((DCELL *) inrast_t0dem)[col];
			break;
	}
	/*WET PIXEL*/
	if(flag3->answer){
		/*Calculate coordinates of row/col from projected ones*/
		row = (int) (( ymax - m_row_wet ) / (double) stepy) ;
		col = (int) (( m_col_wet - xmin ) / (double) stepx) ;
		G_message("Wet Pixel | row:%i col:%i",row,col);
	} else {
		row = m_row_wet;
		col = m_col_wet;
		G_message("Wet Pixel | row:%i col:%i",row,col);
	}
	rowWet=row;
	colWet=col;
	if(G_get_raster_row(infd_t0dem,inrast_t0dem,row,data_type_t0dem)<0)
		G_fatal_error(_("Could not read from <%s>"),t0dem);
	switch(data_type_t0dem){
		case CELL_TYPE:
			d_t0dem_wet = (double) ((CELL *) inrast_t0dem)[col];
			break;
		case FCELL_TYPE:
			d_t0dem_wet = (double) ((FCELL *) inrast_t0dem)[col];
			break;
		case DCELL_TYPE:
			d_t0dem_wet = (double) ((DCELL *) inrast_t0dem)[col];
			break;
	}
	/* END OF MANUAL WET/DRY PIXELS */
	G_message("t0dem_dry = %f",d_t0dem_dry);
	G_message("t0dem_wet = %f",d_t0dem_wet);
	DCELL d_rah_dry;
	DCELL d_roh_dry;

	/* INITIALIZATION */
	for (row = 0; row < nrows; row++)
	{	
		DCELL d_t0dem;
		DCELL d_z0m; 	
		DCELL d_rah1; 	
		DCELL d_roh1; 	
		DCELL d_u5;
		G_percent(row,nrows,2);
		/* read a line input maps into buffers*/	
		if(G_get_raster_row(infd_z0m,inrast_z0m,row,data_type_z0m)<0)
			G_fatal_error(_("Could not read from <%s>"),z0m);
		if(G_get_raster_row(infd_t0dem,inrast_t0dem,row,data_type_t0dem) < 0)
			G_fatal_error(_("Could not read from <%s>"),t0dem);
		/* read every cell in the line buffers */
		for(col=0;col<ncols;col++)
		{
			switch(data_type_z0m){
				case CELL_TYPE:
					d_z0m = (double) ((CELL *) inrast_z0m)[col];
					break;
				case FCELL_TYPE:
					d_z0m = (double) ((FCELL *) inrast_z0m)[col];
					break;
				case DCELL_TYPE:
					d_z0m = (double) ((DCELL *) inrast_z0m)[col];
					break;
			}
			switch(data_type_t0dem){
				case CELL_TYPE:
					d_t0dem = (double) ((CELL *) inrast_t0dem)[col];
					break;
				case FCELL_TYPE:
					d_t0dem = (double) ((FCELL *) inrast_t0dem)[col];
					break;
				case DCELL_TYPE:
					d_t0dem = (double) ((DCELL *) inrast_t0dem)[col];
					break;
			}
			if(G_is_d_null_value(&d_t0dem) ||
				G_is_d_null_value(&d_z0m)){
				/* do nothing */
				d_Roh[row][col] = -999.9;
				d_Rah[row][col] = -999.9;
			} else {
				d_u5=(ustar/0.41)*log(5/d_z0m);
				d_rah1=(1/(d_u5*pow(0.41,2)))*log(5/d_z0m)*log(5/(d_z0m*0.1));
				d_roh1=((998-ea)/(d_t0dem*2.87))+(ea/(d_t0dem*4.61));
				if(d_roh1>5){
					d_roh1=1.0;
				} else {
					d_roh1=((1000-4.65)/(d_t0dem*2.87))+(4.65/(d_t0dem*4.61));
				}
				if(row==rowDry&&col==colDry){//collect dry pix info
					d_rah_dry = d_rah1;
					d_roh_dry = d_roh1;
					G_message("d_rah_dry=%f d_roh_dry=%f",d_rah_dry,d_roh_dry);
				}
				d_Roh[row][col] = d_roh1;
				d_Rah[row][col] = d_rah1;
			}
		}
	}	
	DCELL d_dT_dry;
	// Calculate dT_dry	
	d_dT_dry = (h_dry*d_rah_dry)/(1004*d_roh_dry);
	double a, b;
	// Calculate coefficients for next dT equation	
//	a = 1.0/ ((d_dT_dry-0.0) / (d_t0dem_dry-d_t0dem_wet));
//	b = ( a * d_t0dem_wet ) * (-1.0);

	double sumx=d_t0dem_wet+d_t0dem_dry;
	double sumy=d_dT_dry+0.0;
	double sumx2=pow(d_t0dem_wet,2)+pow(d_t0dem_dry,2);
	double sumxy=(d_t0dem_wet*0.0)+(d_t0dem_dry*d_dT_dry);
	a = (sumxy - ((sumx * sumy) / 2.0)) / (sumx2 - (pow(sumx,2)/2.0));
	b = (sumy - ( a * sumx)) / 2.0; 
	G_message("d_dT_dry=%f",d_dT_dry);
	G_message("dT1=%f * t0dem + (%f)", a, b);
	DCELL d_h_dry;

	/* ITERATION 1 */
	
	for (row = 0; row < nrows; row++)
	{	
		DCELL d_t0dem;
		DCELL d_z0m; 	
		DCELL d_h1; 	
		DCELL d_rah1; 	
		DCELL d_rah2; 	
		DCELL d_roh1; 	
		DCELL d_L; 	
		DCELL d_x; 	
		DCELL d_psih; 	
		DCELL d_psim; 	
		DCELL d_u5;
		G_percent(row,nrows,2);
		/* read a line input maps into buffers*/	
		if(G_get_raster_row(infd_z0m,inrast_z0m,row,data_type_z0m)<0)
			G_fatal_error(_("Could not read from <%s>"),z0m);
		if(G_get_raster_row(infd_t0dem,inrast_t0dem,row,data_type_t0dem) < 0)
			G_fatal_error(_("Could not read from <%s>"),t0dem);
		/* read every cell in the line buffers */
		for(col=0;col<ncols;col++)
		{
			switch(data_type_z0m){
				case CELL_TYPE:
					d_z0m = (double) ((CELL *) inrast_z0m)[col];
					break;
				case FCELL_TYPE:
					d_z0m = (double) ((FCELL *) inrast_z0m)[col];
					break;
				case DCELL_TYPE:
					d_z0m = (double) ((DCELL *) inrast_z0m)[col];
					break;
			}
			switch(data_type_t0dem){
				case CELL_TYPE:
					d_t0dem = (double) ((CELL *) inrast_t0dem)[col];
					break;
				case FCELL_TYPE:
					d_t0dem = (double) ((FCELL *) inrast_t0dem)[col];
					break;
				case DCELL_TYPE:
					d_t0dem = (double) ((DCELL *) inrast_t0dem)[col];
					break;
			}
			d_rah1 = d_Rah[row][col];
			d_roh1 = d_Roh[row][col];
			if(G_is_d_null_value(&d_t0dem) ||
				G_is_d_null_value(&d_z0m)){
				/* do nothing */
			} else {
				if(d_rah1<1.0){
					d_h1 = 0.0;
				} else {
					d_h1 = (1004*d_roh1)*(a*d_t0dem+b)/d_rah1;
				}
				d_L=-1004*d_roh1*pow(ustar,3)*d_t0dem/(d_h1*9.81*0.41);
				d_x=pow((1-16*(5/d_L)),0.25);
				d_psim=2*log((1+d_x)/2)+log((1+pow(d_x,2))/2)-2*atan(d_x)+0.5*PI;
				d_psim=2*log((1+pow(d_x,2))/2);
				d_u5=(ustar/0.41)*log(5/d_z0m);
				d_rah2=(1/(d_u5*pow(0.41,2)))*log((5/d_z0m)-d_psim)*log((5/(d_z0m*0.1))-d_psih);
				if(row==rowDry&&col==colDry){//collect dry pix info
					d_rah_dry = d_rah2;
					d_h_dry = d_h1;
				}
				d_Rah[row][col] = d_rah1;
			}
		}
	}

	// Calculate dT_dry	
	d_dT_dry = (d_h_dry*d_rah_dry)/(1004*d_roh_dry);
	// Calculate coefficients for next dT equation	
//	a = (d_dT_dry-0)/(d_t0dem_dry-d_t0dem_wet);
//	b = (-1.0) * ( a * d_t0dem_wet );
//	G_message("d_dT_dry=%f",d_dT_dry);
//	G_message("dT2=%f * t0dem + (%f)", a, b);
	sumx=d_t0dem_wet+d_t0dem_dry;
	sumy=d_dT_dry+0.0;
	sumx2=pow(d_t0dem_wet,2)+pow(d_t0dem_dry,2);
	sumxy=(d_t0dem_wet*0.0)+(d_t0dem_dry*d_dT_dry);
	a = (sumxy - ((sumx * sumy) / 2.0)) / (sumx2 - (pow(sumx,2)/2.0));
	b = (sumy - ( a * sumx)) / 2.0; 
	G_message("d_dT_dry=%f",d_dT_dry);
	G_message("dT1=%f * t0dem + (%f)", a, b);

	/* ITERATION 2 */
	/***************************************************/
	/***************************************************/
	
	for (row = 0; row < nrows; row++)
	{	
		DCELL d_t0dem;
		DCELL d_z0m; 	
		DCELL d_rah2; 	
		DCELL d_rah3; 	
		DCELL d_roh1; 	
		DCELL d_h2; 	
		DCELL d_L; 	
		DCELL d_x; 	
		DCELL d_psih; 	
		DCELL d_psim; 	
		DCELL d_u5;
		G_percent(row,nrows,2);
		/* read a line input maps into buffers*/	
		if(G_get_raster_row(infd_z0m,inrast_z0m,row,data_type_z0m)<0)
			G_fatal_error(_("Could not read from <%s>"),z0m);
		if(G_get_raster_row(infd_t0dem,inrast_t0dem,row,data_type_t0dem) < 0)
			G_fatal_error(_("Could not read from <%s>"),t0dem);
		/* read every cell in the line buffers */
		for(col=0;col<ncols;col++)
		{
			switch(data_type_z0m){
				case CELL_TYPE:
					d_z0m = (double) ((CELL *) inrast_z0m)[col];
					break;
				case FCELL_TYPE:
					d_z0m = (double) ((FCELL *) inrast_z0m)[col];
					break;
				case DCELL_TYPE:
					d_z0m = (double) ((DCELL *) inrast_z0m)[col];
					break;
			}
			switch(data_type_t0dem){
				case CELL_TYPE:
					d_t0dem = (double) ((CELL *) inrast_t0dem)[col];
					break;
				case FCELL_TYPE:
					d_t0dem = (double) ((FCELL *) inrast_t0dem)[col];
					break;
				case DCELL_TYPE:
					d_t0dem = (double) ((DCELL *) inrast_t0dem)[col];
					break;
			}
			d_rah2 = d_Rah[row][col];
			d_roh1 = d_Roh[row][col];
			if(G_is_d_null_value(&d_t0dem) ||
				G_is_d_null_value(&d_z0m)){
				/* do nothing */
			} else {
				if(d_rah2<1.0){
					d_h2=0.0;
				} else {
					d_h2 = (1004*d_roh1)*(a*d_t0dem+b)/d_rah2;
				}
				d_L=-1004*d_roh1*pow(ustar,3)*d_t0dem/(d_h2*9.81*0.41);
				d_x=pow((1-16*(5/d_L)),0.25);
				d_psim=2*log((1+d_x)/2)+log((1+pow(d_x,2))/2)-2*atan(d_x)+0.5*PI;
				d_psim=2*log((1+pow(d_x,2))/2);
				d_u5=(ustar/0.41)*log(5/d_z0m);
				d_rah3=(1/(d_u5*pow(0.41,2)))*log((5/d_z0m)-d_psim)*log((5/(d_z0m*0.1))-d_psih);
				if(row==rowDry&&col==colDry){//collect dry pix info
					d_rah_dry = d_rah2;
					d_h_dry = d_h2;
				}
				d_Rah[row][col] = d_rah2;
			}
		}
	}

	// Calculate dT_dry	
	d_dT_dry = (d_h_dry*d_rah_dry)/(1004*d_roh_dry);
	// Calculate coefficients for next dT equation	
//	a = (d_dT_dry-0)/(d_t0dem_dry-d_t0dem_wet);
//	b = (-1.0) * ( a * d_t0dem_wet );
//	G_message("d_dT_dry=%f",d_dT_dry);
//	G_message("dT3=%f * t0dem + (%f)", a, b);
	sumx=d_t0dem_wet+d_t0dem_dry;
	sumy=d_dT_dry+0.0;
	sumx2=pow(d_t0dem_wet,2)+pow(d_t0dem_dry,2);
	sumxy=(d_t0dem_wet*0.0)+(d_t0dem_dry*d_dT_dry);
	a = (sumxy - ((sumx * sumy) / 2.0)) / (sumx2 - (pow(sumx,2)/2.0));
	b = (sumy - ( a * sumx)) / 2.0; 
	G_message("d_dT_dry=%f",d_dT_dry);
	G_message("dT1=%f * t0dem + (%f)", a, b);



	/* ITERATION 3 */
	/***************************************************/
	/***************************************************/
	
	for (row = 0; row < nrows; row++)
	{	
		DCELL d_t0dem;
		DCELL d_z0m; 	
		DCELL d_rah3; 	
		DCELL d_roh1; 	
		DCELL d_h3; 	
		DCELL d_L; 	
		DCELL d_x; 	
		DCELL d_psih; 	
		DCELL d_psim; 	
		DCELL d;	/* Output pixel */
		G_percent(row,nrows,2);
		/* read a line input maps into buffers*/	
		if(G_get_raster_row(infd_z0m,inrast_z0m,row,data_type_z0m)<0)
			G_fatal_error(_("Could not read from <%s>"),z0m);
		if(G_get_raster_row(infd_t0dem,inrast_t0dem,row,data_type_t0dem) < 0)
			G_fatal_error(_("Could not read from <%s>"),t0dem);
		/* read every cell in the line buffers */
		for(col=0;col<ncols;col++)
		{
			switch(data_type_z0m){
				case CELL_TYPE:
					d_z0m = (double) ((CELL *) inrast_z0m)[col];
					break;
				case FCELL_TYPE:
					d_z0m = (double) ((FCELL *) inrast_z0m)[col];
					break;
				case DCELL_TYPE:
					d_z0m = (double) ((DCELL *) inrast_z0m)[col];
					break;
			}
			switch(data_type_t0dem){
				case CELL_TYPE:
					d_t0dem = (double) ((CELL *) inrast_t0dem)[col];
					break;
				case FCELL_TYPE:
					d_t0dem = (double) ((FCELL *) inrast_t0dem)[col];
					break;
				case DCELL_TYPE:
					d_t0dem = (double) ((DCELL *) inrast_t0dem)[col];
					break;
			}
			d_rah3 = d_Rah[row][col];
			d_roh1 = d_Roh[row][col];
			if(G_is_d_null_value(&d_t0dem) ||
				G_is_d_null_value(&d_z0m)){
				G_set_d_null_value(&outrast[col],1);
			} else {
				if(d_rah3 < 1.0){
					d_h3=0.0;
				} else {
					d_h3 = (1004*d_roh1)*(a*d_t0dem+b)/d_rah3;
				}
				if( d_h3 < 0 && d_h3 > -50 ){
					d_h3 = 0.0;
				}
				if( d_h3 < -50 || d_h3 > 1000 ){
					G_set_d_null_value(&outrast[col],1);
				}
				outrast[col] = d_h3;
			}
		}
		if (G_put_d_raster_row (outfd, outrast) < 0)
			G_fatal_error ("Cannot write to output file <%s>",h0);
	}


	G_free(inrast_z0m);
	G_close_cell (infd_z0m);
	G_free(inrast_t0dem);
	G_close_cell (infd_t0dem);

	G_free(outrast);
	G_close_cell (outfd);
        
	/* add command line incantation to history file */
        G_short_history(h0, "raster", &history);
        G_command_history(&history);
        G_write_history(h0, &history);

	exit(EXIT_SUCCESS);
}
