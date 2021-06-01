/*****************************************************************************
*
* MODULE:	h.interception
*
* AUTHOR:	Massimiliano Cannata - massimiliano.cannata@supsi.ch (2005)
*
* PURPOSE:	To estimate the water loss, drainage, and storage due 
*           	to canopy rainfall interception.
*
* COPYRIGHT:	(C) 2006 by Istituto Scienze della Terra (www.ist.supsi.ch)
*
*		This program is free software under the GNU General Public
*		Licence (>=2). Read the file COPYING that cames with GRASS
*		for details.
*
/***************************************************************************/

#include <stdio.h>
#include <stdlib.h>
#include <grass/gis.h>
#include <math.h>
#include <grass/glocale.h>

static float maxarg1,maxarg2;
#define FMAX(a,b) (maxarg1=(a),maxarg2=(b),(maxarg1) > (maxarg2) ?\
        (maxarg1) : (maxarg2))

static float minarg1,minarg2;
#define FMIN(a,b) (minarg1=(a),minarg2=(b),(minarg1) < (minarg2) ?\
        (minarg1) : (minarg2))

int main(int argc, char *argv[]){

	/* region informations and handler */
	struct Cell_head cellhd;
	int nrows, ncols;
	int row, col;
	
	/* buffer for in out raster */
	DCELL *inrast_LAI,*inrast_Eo,*inrast_Wo,*inrast_R,*inrast_F,*outrast,*outrast_D,*outrast_Wt;
	unsigned char *IntLoss, *Drainage, *Wt;
	
	/* pointers to input-output raster files */
	int infd_LAI,infd_Eo,infd_Wo,infd_R,infd_F;
	int outfd, outfd_D, outfd_Wt;
	
	/* mapsets for input raster files */
	char *mapset_LAI,*mapset_Eo,*mapset_Wo,*mapset_R,*mapset_F;
	
	/* names of input-output raster files */
	char *LAI, *Eo, *Wo, *R, *F; 

	int err=0;
	
	/* input-output cell values */
	DCELL d_LAI,d_Eo,d_Wo,d_R,d_Wc,d_tao,dt,d_F,i_sat,d_Wr;
	DCELL d_Ts; //timestep
	DCELL d_IntLoss, d_Drainage, d_Wt;

	/* parser stuctures definition */
	struct GModule *module;
	struct Option *input_LAI,*input_Eo,*input_Wo,*input_R,*input_F,*output,*output_D,*output_Wt,*timestep;

/*-TO DO: INSERIRE TIMESTEP IN ORE-*/

  /* Initialize the GIS calls */
	G_gisinit(argv[0]);
	
	module = G_define_module();
	module->description =
		_("Interception module for a single time step with constant rain intensity");
	
	/* Define different options */
	input_LAI = G_define_option();
	input_LAI->key	= "LAI";
	input_LAI->type = TYPE_STRING;
	input_LAI->required = YES;
	input_LAI->gisprompt = "old,cell,raster";
	input_LAI->description = _("Name of LAI raster map");
	
	input_Eo = G_define_option();
	input_Eo->key	= "ETPls";
	input_Eo->type = TYPE_STRING;
	input_Eo->required = YES;
	input_Eo->gisprompt = "old,cell,raster";
	input_Eo->description = _("Name of Potential Evaporation raster map");
		
	input_Wo = G_define_option();
	input_Wo->key	= "Co";
	input_Wo->type = TYPE_STRING;
	input_Wo->required = YES;
	input_Wo->gisprompt = "old,cell,raster";
	input_Wo->description = _("Name of Initial Canopy Storage Level raster map");
		
	input_R = G_define_option();
	input_R->key	= "R";
	input_R->type = TYPE_STRING;
	input_R->required = YES;
	input_R->gisprompt = "old,cell,raster";
	input_R->description = _("Name of Rain raster map");
	
	input_F = G_define_option();
	input_F->key	= "Vc";
	input_F->type = TYPE_STRING;
	input_F->required = YES;
	input_F->gisprompt = "old,cell,raster";
	input_F->description = _("Name of the fraction of vegetated area raster map");
		
	timestep = G_define_option();
	timestep->key   = "Ts";	
	timestep->type	= TYPE_STRING;	
	timestep->required= NO;	
  timestep->description= _("timestep");	
	timestep->answer= "1";
	
	output = G_define_option() ;
	output->key        = "IL";
	output->type       = TYPE_STRING;
	output->required   = YES;
	output->gisprompt  = "new,cell,raster" ;
	output->description= _("Name of output Interception Loss raster map");
	
	output_D = G_define_option() ;
	output_D->key        = "D";
	output_D->type       = TYPE_STRING;
	output_D->required   = YES;
	output_D->gisprompt  = "new,cell,raster" ;
	output_D->description= _("Name of output Drainage raster map");
	
	output_Wt = G_define_option() ;
	output_Wt->key        = "Ct";
	output_Wt->type       = TYPE_STRING;
	output_Wt->required   = YES;
	output_Wt->gisprompt  = "new,cell,raster" ;
	output_Wt->description= _("Name of output Final Canopy Storage Level raster map");
	
if (G_parser(argc, argv))
		exit(EXIT_FAILURE);

	/* get entered parameters */
	LAI=input_LAI->answer;
	Eo=input_Eo->answer;
	Wo=input_Wo->answer;
	R=input_R->answer;
	F=input_F->answer;
	IntLoss=output->answer;
	Drainage=output_D->answer;
	d_Ts=atof(timestep->answer);
	Wt=output_Wt->answer;

	/* find maps in mapset */
	mapset_LAI = G_find_cell2 (LAI, "");
	if (mapset_LAI == NULL)
	        G_fatal_error (_("cell file [%s] not found"), LAI);
	mapset_Eo = G_find_cell2 (Eo, "");
	if (mapset_Eo == NULL)
	        G_fatal_error (_("cell file [%s] not found"), Eo);
	mapset_Wo = G_find_cell2 (Wo, "");
	if (mapset_Wo == NULL)
	        G_fatal_error (_("cell file [%s] not found"), Wo);
	mapset_R = G_find_cell2 (R, "");
	if (mapset_R == NULL)
	        G_fatal_error (_("cell file [%s] not found"), R);
	mapset_F = G_find_cell2 (F, "");
	if (mapset_F == NULL)
	        G_fatal_error (_("cell file [%s] not found"), F);
	
	/* check legal outputs name */ 
	if (G_legal_filename (IntLoss) < 0)
			G_fatal_error (_("[%s] is an illegal name"), IntLoss);
	if (G_legal_filename (Drainage) < 0)
			G_fatal_error (_("[%s] is an illegal name"), Drainage);
	if (G_legal_filename (Wt) < 0)
			G_fatal_error (_("[%s] is an illegal name"), Wt);
	
	/* open input map (DCELL) */
	if ( (infd_LAI = G_open_cell_old (LAI, mapset_LAI)) < 0)
		G_fatal_error (_("Cannot open cell file [%s]"), LAI);
	if ( (infd_Eo = G_open_cell_old (Eo, mapset_Eo)) < 0)
		G_fatal_error (_("Cannot open cell file [%s]"),Eo);
	if ( (infd_Wo = G_open_cell_old (Wo, mapset_Wo)) < 0)
		G_fatal_error (_("Cannot open cell file [%s]"),Wo);
	if ( (infd_R = G_open_cell_old (R, mapset_R)) < 0)
		G_fatal_error (_("Cannot open cell file [%s]"),R);
	if ( (infd_F = G_open_cell_old (F, mapset_F)) < 0)
		G_fatal_error (_("Cannot open cell file [%s]"),F);
	
	/* read header of the input map */	
	if (G_get_cellhd (LAI, mapset_LAI, &cellhd) < 0)
		G_fatal_error (_("Cannot read file header of [%s]"), LAI);
	if (G_get_cellhd (Eo, mapset_Eo, &cellhd) < 0)
		G_fatal_error (_("Cannot read file header of [%s]"), Eo);
	if (G_get_cellhd (Wo, mapset_Wo, &cellhd) < 0)
		G_fatal_error (_("Cannot read file header of [%s]"), Wo);
	if (G_get_cellhd (R, mapset_R, &cellhd) < 0)
		G_fatal_error (_("Cannot read file header of [%s]"), R);
	if (G_get_cellhd (F, mapset_F, &cellhd) < 0)
		G_fatal_error (_("Cannot read file header of [%s]"), F);

	/* Allocate input buffer */
	inrast_LAI	= G_allocate_d_raster_buf();
	inrast_Eo	= G_allocate_d_raster_buf();
	inrast_Wo	= G_allocate_d_raster_buf();
	inrast_R	= G_allocate_d_raster_buf();
	inrast_F	= G_allocate_d_raster_buf();
	
	/* Allocate output buffer */
	outrast		= G_allocate_d_raster_buf();
	outrast_D	= G_allocate_d_raster_buf();
	outrast_Wt	= G_allocate_d_raster_buf();
	
	/* open output map (DCELL) */
	if ( (outfd = G_open_raster_new (IntLoss,DCELL_TYPE)) < 0)
		G_fatal_error (_("Could not open <%s>"),IntLoss);
	if ( (outfd_D = G_open_raster_new (Drainage,DCELL_TYPE)) < 0)
		G_fatal_error (_("Could not open <%s>"),Drainage);
	if ( (outfd_Wt = G_open_raster_new (Wt,DCELL_TYPE)) < 0)
		G_fatal_error (_("Could not open <%s>"),Wt);

	/* get rows & colums number of the active region*/
	nrows		= G_window_rows();
	ncols		= G_window_cols();	
	
	/* loop along all the rows of the region*/
	for (row = 0; row < nrows; row++)
	{
				
		/* read a line input maps into buffers*/	
		if (G_get_d_raster_row (infd_LAI, inrast_LAI, row) < 0)
			G_fatal_error (_("Could not read from <%s>"),LAI);
		if (G_get_d_raster_row (infd_Eo, inrast_Eo, row) < 0)
			G_fatal_error (_("Could not read from <%s>"),Eo);
		if (G_get_d_raster_row (infd_Wo, inrast_Wo, row) < 0)
			G_fatal_error (_("Could not read from <%s>"),Wo);
		if (G_get_d_raster_row (infd_R, inrast_R, row) < 0)
			G_fatal_error (_("Could not read from <%s>"),R);
		if (G_get_d_raster_row (infd_F, inrast_F, row) < 0)
			G_fatal_error (_("Could not read from <%s>"),F);

		
		/* loop along all the columns of the line buffers */
		for (col=0; col < ncols; col++)
		{
			
			/* read a cell from the line buffers */		
			d_LAI	= ((DCELL *) inrast_LAI)[col];
			d_Eo	= ((DCELL *) inrast_Eo)[col];
			d_Wo	= ((DCELL *) inrast_Wo)[col];
			d_R	= ((DCELL *) inrast_R)[col];
			d_F	= ((DCELL *) inrast_F)[col];
			
			//d_R	= d_F * d_R; ma io ho mm/h e quindi calcolo per cella

			/* canopy storage capacity */
			d_Wc	= 0.35*d_LAI;
			
			/* calculate time to evaporate a saturated canopy */
			if (d_Eo>0)
				d_tao	= d_Wc/d_Eo;
			else
				d_tao	= d_Ts*1000; /* it avoids division by zero if no evaporation */

			/* cecking for input error! */
			if (d_Wo>d_Wc) {
				err=1;
				//d_Wo=d_Wc;
			}
			if (d_Wo<0) {
				err=2;
				//d_Wo=0;
			}
			
			//	G_fatal_error ("Input <%s> error at CELL[%d,%d]\nCanopy starting storage cannot exceed maximum storage: ",Wo,row,col);
			//if (d_Wo<0)
			//	G_fatal_error ("Input <%s> error at CELL[%d,%d]\nCanopy starting storage cannot be negative: ",Wo,row,col);
			if (d_R<0)
				G_fatal_error (_("Input <%s> error at CELL[%d,%d]\nRain cannot be negative: "),R,row,col);
			if (d_Eo<0)
				G_fatal_error (_("Input <%s> error at CELL[%d,%d]\nPotential evaporation cannot be negative: "),Eo,row,col);
			if (d_Ts<0)
				G_fatal_error (_("Input <%f> error\nTimestep cannot be negative: "),d_Ts);
			if (d_F<0||d_F>100)
				G_fatal_error (_("Input <%f> error\nFraction a canopy vegetation cover cannot be F>100 or F<0: "),d_F);
			
			/* for debugging propouse: */
      G_debug ( 5, _("LAI=%lf - Eo=%lf - Wo=%lf - R=%lf - Wc=%lf - tao=%lf\n"),d_LAI,d_Eo,d_Wo,d_R,d_Wc,d_tao);

			/* calculate interception loss */
			/*******************************/
			d_Drainage	= 0;
			d_IntLoss	= 0;
			d_Wt		= 0;
			dt			= 0;
			i_sat		= 0;
			int ciclo 	= 0;
			
			/* if it is raining more than evapo rate it is in an increasing phase*/
			if (d_R>0 && d_Eo<d_R) { 
				ciclo=1;
				G_debug ( 4, fprintf(stdout,"R>0\n") );
				
				/* if the initial storage level is equal or bigger than the maximum */
				if (d_Wo>=d_Wc) {  
				ciclo=3;
					G_debug ( 4, _("dWo=dWc: stauro\n") );
					d_IntLoss	= FMIN((d_Eo*d_Ts),(d_R*d_Ts)+(d_Wo-d_Wc));
					//d_IntLoss	= d_Eo*d_Ts;
					d_Drainage	= d_R*d_Ts - d_IntLoss + (d_Wo-d_Wc);
					d_Wt		= d_Wc;
					G_debug ( 4, _("Troughfall=%lf"),d_Drainage);
				}
				
				/* if the initial storage level is less than the maximum */
				else { 
        			G_debug ( 4, fprintf(stdout,"R<E\n") );					
				ciclo=4;
					//rain needed to saturate the storage
					i_sat	= (d_Wc-d_Wo)/(d_tao*(1-exp(-d_Ts/d_tao))); 
					
					/* if the saturation is reach into the timestep */ 
					if (d_R>=i_sat){  
            					G_debug ( 4, _("dt>=d_Ts\n") );
						ciclo=5;
						//time to have saturation
						dt	= -d_tao*log(1-((d_Wc-d_Wo)/(d_R*d_tao))); 
						
						/* some check!!! */
						if(dt>d_Ts) {
							G_warning (_("Saturation time cannot be larger than time step!\n"));
						}
						if(dt<0) {
							G_warning (_("Saturation time cannot be negative!\n"));
						}
						
						/* d_IntLoss	= FMIN( ((d_R*d_Ts)-(d_Wc-d_Wo)) , ((d_R*dt)-(d_Wc-d_Wo)+(d_Ts-dt)*d_Eo) ); */
						d_IntLoss	= (d_R*dt)-(d_Wc-d_Wo)+(d_Ts-dt)*d_Eo;
						d_Drainage	= (d_R*d_Ts) - (d_Wc-d_Wo) - d_IntLoss;
						d_Wt		= d_Wc;							
						
					}
					
					/* if the saturation is not reached into the timestep */
					else {  
            					G_debug ( 4, _("dt<d_Ts\n") );
						ciclo=6;
						/* storage level at the end of timestep */
						d_Wr		= d_R*d_tao*(1-exp(-d_Ts/d_tao)) + d_Wo; 
						d_IntLoss	= (d_R*d_Ts) - (d_Wr-d_Wo);
						d_Drainage	= 0;
						d_Wt		= d_Wr;
					}
				}
			
			}
			
			/* if it is raining less than evapo rate it is a decrease phase */ 
			else if (d_R>0 && d_Eo>=d_R) {
				ciclo=12;
				d_Drainage	= 0;
				d_Wt		= FMAX(d_Wo*exp(-d_Ts/d_tao),0);
				d_IntLoss	= d_Wo-d_Wt+d_R;
			}
			
			/* if it is not raining  it is a zero or decrease phase */ 
			else if (d_R<=0){
				/* if the storage was empty (zero phase)*/
				if (d_Wo<=0){  
				    G_debug ( 4, _("dWo=0\n") );
						ciclo=10;
						d_IntLoss	= 0;
						d_Drainage	= 0;
						d_Wt		= 0;
				}
				/* if the storage was not empty (decrease phase)*/
				else if (d_Wo<=d_Wc) {  
				    G_debug ( 4, _("dWo>0\n") );
				    ciclo=11;
						d_Drainage	= 0;
						d_Wt		= FMAX(d_Wo*exp(-d_Ts/d_tao),0);
						d_IntLoss	= d_Wo-d_Wt;
				}
				/* new added Martedì 03 Maggio */
				else {
						d_Drainage	= d_Wo-d_Wc;
						d_Wt		= FMIN(FMAX(d_Wo*exp(-d_Ts/d_tao),0),d_Wc);
						d_IntLoss	= d_Wc-d_Wt;
				}
			}
			
			else {
				G_warning (_("Exception case: Rain=%lf - Evapo=%lf\n"),d_R,d_Eo);
				d_IntLoss	= 0;
				d_Drainage	= 0;
				d_Wt		= 0;
			}				
			
			if(((d_IntLoss+d_Drainage+d_Wt-d_Wo-d_R)-0)>0.00001)
				G_debug ( 3, _("BILANCIO: %e | CICLO:%d | IL=%lf - D=%lf - Wt=%lf - d_Wo=%lf - R=%lf\n"),d_IntLoss+d_Drainage+d_Wt-d_Wo-d_R,ciclo,d_IntLoss,d_Drainage,d_Wt,d_Wo,d_R);
			
			if (d_Wt<0 || d_Wt>d_Wc) {
				G_debug ( 3, _("\nciclo: %d, d_IntLoss:%lf\nd_R:%lf, d_Eo:%lf, d_Wo:%lf, d_Wc:%lf, \ni_sat:%lf, dt:%lf, R+E:%lf"),ciclo,d_IntLoss,d_R,d_Eo,d_Wo,d_Wc,i_sat,dt,((d_R*d_Ts)+d_Wo));
			}
			
			/* write evaluated values in the buffers */
			if(d_Drainage<0){
				printf("\nciclo %d\n",ciclo);
			}
			((DCELL *) outrast)[col] = d_IntLoss*d_F;
			((DCELL *) outrast_D)[col] = (d_Drainage*d_F); 
      /* note: to get total rain reaching the ground->  d_Drainage*d_F)+(1-d_F)*d_R; */
			((DCELL *) outrast_Wt)[col] = d_Wt; 
				G_debug ( 5, _("IntLoss=%lf\n"),d_IntLoss);
		}

		/* write buffers into the output rasters */
		if (G_put_d_raster_row (outfd, outrast) < 0)
			G_fatal_error (_("Cannot write to <%s>"),IntLoss);
		if (G_put_d_raster_row (outfd_D, outrast_D) < 0)
			G_fatal_error (_("Cannot write to <%s>"),Drainage);
		if (G_put_d_raster_row (outfd_Wt, outrast_Wt) < 0)
			G_fatal_error (_("Cannot write to <%s>"),Wt);
			
	}	

if (err==1)
	G_warning (_("Canopy starting storage has exceeded maximum storage"));
if (err==2)
	G_warning (_("Canopy starting storage is negative"));


	
/* free buffer */ 	
G_free(inrast_LAI);
G_free(inrast_Eo);
G_free(inrast_Wo);
G_free(inrast_R);
G_free(inrast_F);
G_free(outrast);
G_free(outrast_D);
G_free(outrast_Wt);

/* close raster */
G_close_cell (infd_LAI);
G_close_cell (infd_Eo);
G_close_cell (infd_Wo);
G_close_cell (infd_R);
G_close_cell (infd_F);
G_close_cell (outfd);
G_close_cell (outfd_D);
G_close_cell (outfd_Wt);

return (0);
}
