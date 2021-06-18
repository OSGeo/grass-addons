/*****************************************************************************
*
* MODULE:	r.snow
*
* AUTHOR:	Massimiliano Cannata - massimiliano.cannata[]supsi.ch (2005)
*
* PURPOSE:	Estimate the snowpack water equivalent, 
*               the snowamelt and the snowpack energy with a modified
*               SHE model approach.
*
* COPYRIGHT:	(C) 2006 by Istituto Scienze della Terra (www.ist.supsi.ch)
*
*		This program is free software under the GNU General Public
*		Licence (>=2). Read the file COPYING that cames with GRASS
*		for details.
*
/***************************************************************************/

#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <unistd.h>
#include <grass/gis.h>
#include <math.h>
#include <grass/glocale.h>

#define min(a,b) ((a) < (b) ? (a) : (b))
#define max(a,b) ((a) > (b) ? (a) : (b))

#define Tr 3		/* °C */
#define Tb -1		/* °C */
#define Cs 2.09	        /* KJ*Kg¯¹*°C-¹*/
#define rhoW 1000	/* Kg*m¯³ */
#define hf 333.5	/* KJ*Kg¯¹ */
#define cW 4.18	        /* [KJ*Kg¯¹*°C¯¹] */
#define cs 0.5 	        /* ice heat capacity [Kcal*Kg¯¹*°K¯¹]*/
#define cf 79.6 	/* [Kcal*Kg¯¹] */
#define T0 273.15 	/* [°K] */


int main(int argc, char *argv[]){

	struct Cell_head cellhd;
	
	/* input-output raster files */
	int infd_TEMP,infd_RAD,infd_RAIN,infd_SNOW,infd_ENERGY;
	int outfd_SNOW,outfd_ENERGY,outfd_SNOWMELT;
	
	/* mapset name locator */
	char *mapset_TEMP,*mapset_RAD,*mapset_RAIN,*mapset_SNOW,*mapset_ENERGY;

	/* buffer for input-output raster */
	DCELL *inrast_TEMP;			/* temperature map [°C]*/
	DCELL *inrast_RAD;			/* radiation map with rigth albedo! [W/m²]*/
	DCELL *inrast_RAIN;			/* precipitation intensity map [mm/h] */
	DCELL *inrast_SNOW;			/* snowpack heigth at previous step [mm] */ 
	DCELL *inrast_ENERGY;		/* energy at previous step [Kcal*m¯²*h¯¹] */ 	
	DCELL *outrast_SNOW;			/* snowpack heigth at previous step [mm] */ 
	DCELL *outrast_ENERGY;		/* energy at previous step [Kcal*m¯²*h¯¹] */ 	
	DCELL *outrast_SNOWMELT;	/* snowmelt for the current timestep */

	/* cell values */
	DCELL d_TEMP,d_RAD,d_RAIN,d_SNOW,d_ENERGY;
	DCELL d_SNOWt,d_ENERGYt,d_SNOWMELT;
	
	double Pr=0, Ps=0;
	double E0,Qp,Z0,En;
	
	/* cell counters */
	int nrows, ncols;
	int row, col;
	
	/* variables to handle user inputs */
	char *TEMP,*RAD, *RAIN, *SNOW, *ENERGY, *SNOWt, *ENERGYt, *SNOWMELT; 
	
	/* GRASS structure */
	struct GModule *module;
	struct Option *input_TEMP, *input_RAD, *input_RAIN, *input_SNOW, *input_ENERGY;
	struct Option *output_SNOW, *output_ENERGY, *output_SNOWMELT;

	G_gisinit(argv[0]);
	
	module = G_define_module();
	module->description =
		"Snowmelt and Accumulation Model along a timestep t";
	
	/* Define different options */
	input_TEMP = G_define_option();
	input_TEMP->key	= "temp";
	input_TEMP->type = TYPE_STRING;
	input_TEMP->required = YES;
	input_TEMP->gisprompt = "old,cell,raster";
	input_TEMP->description = _("Name of temperature raster map in [°C]");
	
	input_RAD = G_define_option();
	input_RAD->key	= "RAD";
	input_RAD->type = TYPE_STRING;
	input_RAD->required = YES;
	input_RAD->gisprompt = "old,cell,raster";
	input_RAD->description = _("Name of net solar radiation raster map in [W*m¯²*t¯¹]");
		
	input_RAIN = G_define_option();
	input_RAIN->key	= "rain";
	input_RAIN->type = TYPE_STRING;
	input_RAIN->required = YES;
	input_RAIN->gisprompt = "old,cell,raster";
	input_RAIN->description = _("Name of rain intensity raster map in [mm*t¯¹]");
		
	input_SNOW = G_define_option();
	input_SNOW->key	= "in_snow";
	input_SNOW->type = TYPE_STRING;
	input_SNOW->required = YES;
	input_SNOW->gisprompt = "old,cell,raster";
	input_SNOW->description = _("Name of snow width raster map in [mm] of water equivalent");
	
	input_ENERGY = G_define_option();
	input_ENERGY->key	= "in_energy";
	input_ENERGY->type = TYPE_STRING;
	input_ENERGY->required = YES;
	input_ENERGY->gisprompt = "old,cell,raster";
	input_ENERGY->description = _("Name of snow energy raster map in [Kcal*m¯²*t¯¹]");	
	
	output_SNOW = G_define_option() ;
	output_SNOW->key        = "out_snow";
	output_SNOW->type       = TYPE_STRING;
	output_SNOW->required   = YES;
	output_SNOW->gisprompt  = "new,cell,raster" ;
	output_SNOW->description= _("Name of output snow width raster map in [mm] of water equivalent");

	output_ENERGY = G_define_option() ;
	output_ENERGY->key        = "out_energy";
	output_ENERGY->type       = TYPE_STRING;
	output_ENERGY->required   = YES;
	output_ENERGY->gisprompt  = "new,cell,raster" ;
	output_ENERGY->description= _("Name of output snow energy raster map in [Kcal*m¯²*t¯¹]");

	output_SNOWMELT = G_define_option() ;
	output_SNOWMELT->key        = "out_snowmelt";
	output_SNOWMELT->type       = TYPE_STRING;
	output_SNOWMELT->required   = YES;
	output_SNOWMELT->gisprompt  = "new,cell,raster" ;
	output_SNOWMELT->description= _("Name of output snowmelt raster map in [mm*t¯¹]");
	
	if (G_parser(argc, argv))
		exit (-1);
	
	/* get entered parameters */
	TEMP=input_TEMP->answer;
	RAD=input_RAD->answer;
	RAIN=input_RAIN->answer;
	SNOW=input_SNOW->answer;
	ENERGY=input_ENERGY->answer;
	SNOWt=output_SNOW->answer;
	ENERGYt=output_ENERGY->answer;
	SNOWMELT=output_SNOWMELT->answer;
		
	/* find maps in mapset */
	mapset_TEMP = G_find_cell2 (TEMP, "");
	if (mapset_TEMP == NULL)
	        G_fatal_error (_("cell file [%s] not found"), TEMP);
	mapset_RAD = G_find_cell2 (RAD, "");
	if (mapset_RAD == NULL)
	        G_fatal_error (_("cell file [%s] not found"), RAD);
	mapset_RAIN = G_find_cell2 (RAIN, "");
	if (mapset_RAIN == NULL)
	        G_fatal_error (_("cell file [%s] not found"), RAIN);
	mapset_SNOW = G_find_cell2 (SNOW, "");
	if (mapset_SNOW == NULL)
	        G_fatal_error (_("cell file [%s] not found"), SNOW);
	mapset_ENERGY = G_find_cell2 (ENERGY, "");
	if (mapset_ENERGY == NULL)
	        G_fatal_error (_("cell file [%s] not found"), ENERGY);	        

	/* check legal output name */ 
	if (G_legal_filename (ENERGYt) < 0)
			G_fatal_error (_("[%s] is an illegal name"), ENERGYt);
	if (G_legal_filename (SNOWt) < 0)
			G_fatal_error (_("[%s] is an illegal name"), SNOWt);
	if (G_legal_filename (SNOWMELT) < 0)
			G_fatal_error (_("[%s] is an illegal name"), SNOWMELT);

	/* open input raster files */
	if ( (infd_TEMP = G_open_cell_old (TEMP, mapset_TEMP)) < 0)
		G_fatal_error (_("Cannot open cell file [%s]"), TEMP);
	if ( (infd_RAD = G_open_cell_old (RAD, mapset_RAD)) < 0)
		G_fatal_error (_("Cannot open cell file [%s]"),RAD);
	if ( (infd_RAIN = G_open_cell_old (RAIN, mapset_RAIN)) < 0)
		G_fatal_error (_("Cannot open cell file [%s]"),RAIN);
	if ( (infd_SNOW = G_open_cell_old (SNOW, mapset_SNOW)) < 0)
		G_fatal_error (_("Cannot open cell file [%s]"),SNOW);
	if ( (infd_ENERGY = G_open_cell_old (ENERGY, mapset_ENERGY)) < 0)
		G_fatal_error (_("Cannot open cell file [%s]"),ENERGY);		

	if (G_get_cellhd (TEMP, mapset_TEMP, &cellhd) < 0)
		G_fatal_error (_("Cannot read file header of [%s]"), TEMP);
	if (G_get_cellhd (RAD, mapset_RAD, &cellhd) < 0)
		G_fatal_error (_("Cannot read file header of [%s]"), RAD);
	if (G_get_cellhd (RAIN, mapset_RAIN, &cellhd) < 0)
		G_fatal_error (_("Cannot read file header of [%s]"), RAIN);
	if (G_get_cellhd (SNOW, mapset_SNOW, &cellhd) < 0)
		G_fatal_error (_("Cannot read file header of [%s]"), SNOW);
	if (G_get_cellhd (ENERGY, mapset_ENERGY, &cellhd) < 0)
		G_fatal_error (_("Cannot read file header of [%s]"), ENERGY);
	
	/* open output raster */
	if ( (outfd_SNOW = G_open_raster_new (SNOWt,DCELL_TYPE)) < 0)
		G_fatal_error (_("Could not open <%s>"),SNOWt);
	if ( (outfd_ENERGY = G_open_raster_new (ENERGYt,DCELL_TYPE)) < 0)
		G_fatal_error (_("Could not open <%s>"),ENERGYt);
	if ( (outfd_SNOWMELT = G_open_raster_new (SNOWMELT,DCELL_TYPE)) < 0)
		G_fatal_error (_("Could not open <%s>"),SNOWMELT);

		
	/* Allocate input buffer */
	inrast_TEMP	= G_allocate_d_raster_buf();
	inrast_RAD	= G_allocate_d_raster_buf();
	inrast_RAIN	= G_allocate_d_raster_buf();
	inrast_SNOW	= G_allocate_d_raster_buf();
	inrast_ENERGY	= G_allocate_d_raster_buf();	

	/* Allocate output buffer */
	outrast_SNOW	= G_allocate_d_raster_buf();
	outrast_ENERGY	= G_allocate_d_raster_buf();
	outrast_SNOWMELT	= G_allocate_d_raster_buf();	

	/* get windows rows & cols */
	nrows	= G_window_rows();
	ncols	= G_window_cols();

	for (row = 0; row < nrows; row++)
	{
		G_percent (row, nrows, 2);
				
		/* read a line input maps into buffers*/	
		if (G_get_d_raster_row (infd_TEMP, inrast_TEMP, row) < 0)
			G_fatal_error (_("Could not read from <%s>"),TEMP);
		if (G_get_d_raster_row (infd_RAD, inrast_RAD, row) < 0)
			G_fatal_error (_("Could not read from <%s>"),RAD);
		if (G_get_d_raster_row (infd_RAIN, inrast_RAIN, row) < 0)
			G_fatal_error (_("Could not read from <%s>"),RAIN);
		if (G_get_d_raster_row (infd_SNOW, inrast_SNOW, row) < 0)
			G_fatal_error (_("Could not read from <%s>"),SNOW);
		if (G_get_d_raster_row (infd_ENERGY, inrast_ENERGY, row) < 0)
			G_fatal_error (_("Could not read from <%s>"),ENERGY);
		
		/* read every cell in the line buffers */
		for (col=0; col < ncols; col++)
		{
			d_TEMP	= ((DCELL *) inrast_TEMP)[col]; 		/* [°C] */
			d_RAD		= ((DCELL *) inrast_RAD)[col];		/* [W/m²] */
			d_RAIN	= ((DCELL *) inrast_RAIN)[col];		/* [mm] */
			d_SNOW	= ((DCELL *) inrast_SNOW)[col];		/* [mm] */
			d_ENERGY	= ((DCELL *) inrast_ENERGY)[col];	/* [Kcal*m¯²] */
			
			
			/* partition of the precipitations in rain (Pr)and snow (Ps) */
			if (d_TEMP>=Tr)
				Pr	=	d_RAIN;
			if (d_TEMP<Tr && d_TEMP>Tb)
				Pr	=	d_RAIN*(d_TEMP-Tb)/(Tr-Tb);
			if (d_TEMP<=Tb)
				Pr	=	0;
			
			/* Ps	=	(d_RAIN-Pr)*F; it accounts for wind drift */
			Ps	=	(d_RAIN-Pr);	/* [mm] */
			
			/* water and energy estimation with zero snowmelt hypotesis */
			Z0	=	d_SNOW + Ps;	/* [mm] */
			Qp	=	0.001*((Ps*Cs*rhoW*min(d_TEMP,0)) + (Pr*(hf*rhoW + (cW*rhoW*max(d_TEMP,0))))); /* [KJ*m¯²]*/
			E0	=	d_ENERGY + (d_RAD*0.8604206501) + (Qp/4.184);	/* [Kcal*m¯²] */ 
			En = cs*Z0*T0;
			/* E0=available energy; En=energy to maintain the solid phase */
			
			G_debug ( 5, _("Z0=%lf, E0=%lf, d_RAD=%lf, Qp=%lf, Pr=%lf, Ps=%lf\n"),Z0,E0,d_RAD,Qp,Pr,Ps);
			
			
			if (Z0==0) {
				d_SNOWMELT	=	0;
				d_SNOWt		=	0;
				d_ENERGYt	=	0;
			}	
			
			/* estimation of output values at the end of timestep (SNOW;ENERGY;SNOMELT) */ 
			else if (En>=E0) {
				d_SNOWMELT	=	0;
				d_SNOWt		=	Z0;
				d_ENERGYt	=	E0;
				
				G_debug ( 5, _("Melt=%lf, Snow=%lf, Ener=%lf, Ps=%lf,cs*T0*Z0=%lf\n"),d_SNOWMELT,d_SNOWt,d_ENERGYt,Ps,cs*T0*Z0 );
			}
			else {
				d_SNOWMELT	=	min((E0-En)/cf,Z0);
				d_SNOWt		=	max(0,Z0-d_SNOWMELT);
				d_ENERGYt	=	E0 - ((cs*T0+cf)*d_SNOWMELT);
				
				G_debug ( 5, _("Melt=%lf, Snow=%lf, Ener=%lf, Ps=%lf,cs*T0*Z0=%lf\n"),d_SNOWMELT,d_SNOWt,d_ENERGYt,Ps,cs*T0*Z0 );
				G_debug ( 5, _("Z0=%lf, E0=%lf, d_RAD=%lf, Qp=%lf, Pr=%lf, Ps=%lf\n"),Z0,E0,d_RAD,Qp,Pr,Ps );
			}			
			
			((DCELL *) outrast_SNOWMELT)[col]	= d_SNOWMELT;
			((DCELL *) outrast_SNOW)[col]			= d_SNOWt;
			((DCELL *) outrast_ENERGY)[col]		= d_ENERGYt;

		}
		
		if (G_put_d_raster_row (outfd_SNOW, outrast_SNOW) < 0)
			G_fatal_error (_("Cannot write to <%s>"),SNOWt);
		if (G_put_d_raster_row (outfd_ENERGY, outrast_ENERGY) < 0)
			G_fatal_error (_("Cannot write to <%s>"),ENERGYt);
		if (G_put_d_raster_row (outfd_SNOWMELT, outrast_SNOWMELT) < 0)
			G_fatal_error (_("Cannot write to <%s>"),SNOWMELT);
			
	}	
G_free(inrast_TEMP);
G_free(inrast_RAD);
G_free(inrast_RAIN);
G_free(inrast_SNOW);
G_free(inrast_ENERGY);
G_free(outrast_SNOW);
G_free(outrast_ENERGY);
G_free(outrast_SNOWMELT);

G_close_cell (infd_TEMP);
G_close_cell (infd_RAD);
G_close_cell (infd_RAIN);
G_close_cell (infd_SNOW);
G_close_cell (infd_ENERGY);
G_close_cell (outfd_SNOW);
G_close_cell (outfd_ENERGY);
G_close_cell (outfd_SNOWMELT);

return (0);
}
