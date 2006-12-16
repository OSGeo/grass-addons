/****************************************************************************
 *
 * MODULE:       r.uslek
 * AUTHOR(S):    Yann Chemin - ychemin@gmail.com
 * PURPOSE:      Transforms percentage of texture (sand/clay/silt)
 *               into USDA 1951 (p209) soil texture classes and then
 *               into USLE soil erodibility factor (K) as an output
 *
 * COPYRIGHT:    (C) 2006 by the SIC-ISDC, Ashgabat, Turkmenistan
 * 		 (C) 2002 by the GRASS Development Team
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
#include "prct2tex.h"
#include "tex2usle_k.h"

#define POLYGON_DIMENSION 20

int main(int argc, char *argv[])
{
	struct Cell_head cellhd; //region+header info
	char *mapset; // mapset name
	int nrows, ncols;
	int row,col;

	int verbose=1;
	struct GModule *module;
	struct Option *input1, *input2, *input3, *input4,*output1;
	
	struct Flag *flag1;	
	struct History history; //metadata
	
	/************************************/
	/* FMEO Declarations*****************/
	char *name;   // input raster name
	char *result; //output raster name
	//File Descriptors
	int infd_psand, infd_psilt, infd_pclay, infd_pomat;
	int outfd;
	
	char *psand,*psilt,*pclay,*pomat;
	
	int i=0,j=0;
	
	void *inrast_psand, *inrast_psilt, *inrast_pclay, *inrast_pomat;
	unsigned char *outrast;
	RASTER_MAP_TYPE data_type_output=DCELL_TYPE;
	RASTER_MAP_TYPE data_type_psand;
	RASTER_MAP_TYPE data_type_psilt;
	RASTER_MAP_TYPE data_type_pclay;
	RASTER_MAP_TYPE data_type_pomat;
	
	/************************************/
	G_gisinit(argv[0]);

	module = G_define_module();
	module->keywords = _("USLE, soil, erosion");
	module->description = _("USLE Soil Erodibility Factor (K)");

	/* Define the different options */
	input1 = G_define_option() ;
	input1->key	   = _("psand");
	input1->type       = TYPE_STRING;
	input1->required   = YES;
	input1->gisprompt  =_("old,cell,raster") ;
	input1->description=_("Name of the Soil sand fraction map [0.0-1.0]");
	input1->answer     =_("psand");

	input2 = G_define_option() ;
	input2->key        =_("pclay");
	input2->type       = TYPE_STRING;
	input2->required   = YES;
	input2->gisprompt  =_("old,cell,raster");
	input2->description=_("Name of the Soil clay fraction map [0.0-1.0]");
	input2->answer     =_("pclay");

	input3 = G_define_option() ;
	input3->key        =_("psilt");
	input3->type       = TYPE_STRING;
	input3->required   = YES;
	input3->gisprompt  =_("old,cell,raster");
	input3->description=_("Name of the Soil silt fraction map [0.0-1.0]");
	input3->answer     =_("psilt");

	input4 = G_define_option() ;
	input4->key        =_("pomat");
	input4->type       = TYPE_STRING;
	input4->required   = YES;
	input4->gisprompt  =_("old,cell,raster");
	input4->description=_("Name of the Soil Organic Matter map [0.0-1.0]");
	input4->answer     =_("pomat");

	output1 = G_define_option() ;
	output1->key        =_("usle_k");
	output1->type       = TYPE_STRING;
	output1->required   = YES;
	output1->gisprompt  =_("new,cell,raster");
	output1->description=_("Name of the output USLE K factor layer");
	output1->answer     =_("usle_k");

	flag1 = G_define_flag();
	flag1->key = 'q';
	flag1->description = _("Quiet");

	/********************/
	if (G_parser(argc, argv))
		exit (EXIT_FAILURE);

	psand	 	= input1->answer;
	pclay	 	= input2->answer;
	psilt		= input3->answer;
	pomat	 	= input4->answer;
	
	result  = output1->answer;
	verbose = (!flag1->answer);
	/***************************************************/
	mapset = G_find_cell2(psand, "");
	if (mapset == NULL) {
		G_fatal_error(_("cell file [%s] not found"), psand);
	}
	data_type_psand = G_raster_map_type(psand,mapset);
	if ( (infd_psand = G_open_cell_old (psand,mapset)) < 0)
		G_fatal_error (_("Cannot open cell file [%s]"), psand);
	if (G_get_cellhd (psand, mapset, &cellhd) < 0)
		G_fatal_error (_("Cannot read file header of [%s])"), psand);
	inrast_psand = G_allocate_raster_buf(data_type_psand);
	/***************************************************/
	mapset = G_find_cell2 (psilt, "");
	if (mapset == NULL) {
		G_fatal_error(_("cell file [%s] not found"), psilt);
	}
	data_type_psilt = G_raster_map_type(psilt,mapset);
	if ( (infd_psilt = G_open_cell_old (psilt,mapset)) < 0)
		G_fatal_error(_("Cannot open cell file [%s]"), psilt);
	if (G_get_cellhd (psilt, mapset, &cellhd) < 0)
		G_fatal_error(_("Cannot read file header of [%s]"), psilt);
	inrast_psilt = G_allocate_raster_buf(data_type_psilt);
	/***************************************************/
	mapset = G_find_cell2 (pclay, "");
	if (mapset == NULL) {
		G_fatal_error(_("Cell file [%s] not found"), pclay);
	}
	data_type_pclay = G_raster_map_type(pclay,mapset);
	if ( (infd_pclay = G_open_cell_old (pclay,mapset)) < 0)
		G_fatal_error(_("Cannot open cell file [%s]"), pclay);
	if (G_get_cellhd (pclay, mapset, &cellhd) < 0)
		G_fatal_error(_("Cannot read file header of [%s]"), pclay);
	inrast_pclay = G_allocate_raster_buf(data_type_pclay);
	/***************************************************/
	mapset = G_find_cell2 (pomat, "");
	if (mapset == NULL) {
		G_fatal_error(_("Cell file [%s] not found"), pomat);
	}
	data_type_pomat = G_raster_map_type(pomat,mapset);
	if ( (infd_pomat = G_open_cell_old (pomat,mapset)) < 0)
		G_fatal_error(_("Cannot open cell file [%s]"), pomat);
	if (G_get_cellhd (pomat, mapset, &cellhd) < 0)
		G_fatal_error(_("Cannot read file header of [%s]"), pomat);
	inrast_pomat = G_allocate_raster_buf(data_type_pomat);
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
		DCELL d_sand;
		DCELL d_clay;
		DCELL d_silt;
		DCELL d_om;
		double tex[4] = {0.0,0.0,0.0,0.0};
		if(verbose)
			G_percent(row,nrows,2);
//		printf("row = %i/%i\n",row,nrows);
		/* read soil input maps */	
		if(G_get_raster_row(infd_psand,inrast_psand,row,data_type_psand)<0)
			G_fatal_error(_("Could not read from <%s>"),psand);
		if(G_get_raster_row(infd_psilt,inrast_psilt,row,data_type_psilt)<0)
			G_fatal_error(_("Could not read from <%s>"),psilt);
		if(G_get_raster_row(infd_pclay,inrast_pclay,row,data_type_pclay)<0)
			G_fatal_error(_("Could not read from <%s>"),pclay);
		if(G_get_raster_row(infd_pomat,inrast_pomat,row,data_type_pomat)<0)
			G_fatal_error(_("Could not read from <%s>"),pomat);
		/*process the data */
		for (col=0; col < ncols; col++)
		{
		//	printf("col=%i/%i ",col,ncols);
			d_sand = ((DCELL *) inrast_psand)[col];
			//tex[0] = d;
 		//	printf("psand = %5.3f", d_sand);
			d_silt = ((DCELL *) inrast_psilt)[col];
			//tex[1] = d;
 		//	printf(" psilt = %5.3f", d_silt);
			d_clay = ((DCELL *) inrast_pclay)[col];
			//tex[2] = d;
 		//	printf(" pclay = %5.3f", d_clay);
			d_om = ((DCELL *) inrast_pomat)[col];
			//tex[3] = d;
 		//	printf("inrast_pomat = %f\n", d_om);
			if(G_is_d_null_value(&d_sand)){
				((DCELL *) outrast)[col] = 0.0;
			}else if(G_is_d_null_value(&d_clay)){
				((DCELL *) outrast)[col] = 0.0;
			}else if(G_is_d_null_value(&d_silt)){
				((DCELL *) outrast)[col] = 0.0;
			}else {
				/************************************/
				/* convert to usle_k 		    */
				d = (double) prct2tex(d_sand, d_clay, d_silt);
		//		printf(" || d=%5.3f",d);
				if((d_sand+d_clay+d_silt)!=1.0){
					printf("d=%icol=%i||%5.3f%5.3f%5.3f\n",d,col,d_sand,d_clay,d_silt);
		//			exit(EXIT_SUCCESS);
				}
				if(G_is_d_null_value(&d_om)){
					d_om=0.0;//if OM==NULL then make it 0.0
				}
				d = tex2usle_k((int) d, d_om);	
				printf(" -> %5.3f",d);
				/************************************/
				if(d>1.0){//in case some map input not standard
					d=0.0;
				}
				((DCELL *) outrast)[col] = d;
		//		printf(" -> %5.3f\n",d);
			}
		//	if(row==50){
		//		exit(EXIT_SUCCESS);
		//	}
		}
		if (G_put_raster_row (outfd, outrast, data_type_output) < 0)
			G_fatal_error(_("Cannot write to output raster file"));
	}

	G_free (inrast_psand);
	G_free (inrast_psilt);
	G_free (inrast_pclay);
	G_free (inrast_pomat);
	G_close_cell (infd_psand);
	G_close_cell (infd_psilt);
	G_close_cell (infd_pclay);
	G_close_cell (infd_pomat);
	
	G_free (outrast);
	G_close_cell (outfd);

	G_short_history(result, "raster", &history);
	G_command_history(&history);
	G_write_history(result,&history);

	exit(EXIT_SUCCESS);
}

