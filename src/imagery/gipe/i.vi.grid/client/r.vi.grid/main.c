/****************************************************************************
 *
 * MODULE:       r.vi.grid
 * AUTHOR(S):    Shamim Akhter shamimakhter@gmail.com
		 Baburao Kamble baburaokamble@gmail.com
 *		 Yann Chemin - ychemin@gmail.com
 * PURPOSE:      Calculates 13 vegetation indices 
 * 		 based on biophysical parameters. 
 *
 * COPYRIGHT:    (C) 2006 by the Tokyo Institute of Technology, Japan
 * 		 (C) 2002-2006 by the GRASS Development Team
 *
 *               This program is free software under the GNU General Public
 *   	    	 License (>=v2). Read the file COPYING that comes with GRASS
 *   	    	 for details.
 * 
 * Remark:              
 *		 These are generic indices that use red and nir for most of them. 
 *               Those can be any use by standard satellite having V and IR.
 *		 However arvi uses red, nir and blue; 
 *		 GVI uses B,G,R,NIR, chan5 and chan 7 of landsat;
 *		 and GARI uses B,G,R and NIR.      
 *
 *****************************************************************************/

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "gis.h"
#include "glocale.h"

//#include "grpc.h"
#include "/usr/local/ng/include/grpc.h"

#define NUM_HOSTS 4

// Required for GridRPC call.
char * hosts[] = {"gs.alab.ip.titech.ac.jp","gs.alab.ip.titech.ac.jp","gs.alab.ip.titech.ac.jp","gs.alab.ip.titech.ac.jp"};
grpc_function_handle_t handles[NUM_HOSTS];
grpc_sessionid_t ids[NUM_HOSTS];
int ret;

double s_r( double redchan, double nirchan );
double nd_vi( double redchan, double nirchan );
double ip_vi( double redchan, double nirchan );
double d_vi( double redchan, double nirchan );
double p_vi( double redchan, double nirchan );
double wd_vi( double redchan, double nirchan );
double sa_vi( double redchan, double nirchan );
double msa_vi( double redchan, double nirchan );
double msa_vi2( double redchan, double nirchan );
double ge_mi( double redchan, double nirchan );
double ar_vi( double redchan, double nirchan, double bluechan );
double g_vi( double bluechan, double greenchan, double redchan, double nirchan, double chan5chan, double chan7chan);
double ga_ri( double redchan, double nirchan, double bluechan, double greenchan );

int main(int argc, char *argv[])
{
	struct Cell_head cellhd; //region+header info
	char *mapset; // mapset name
	int nrows, ncols;
	int row,col;

	int verbose=1;
	
	//double **db;
	//int *I;
	char *viflag;// Switch for particular index
	
	struct GModule *module;
	struct Option *input1, *input2,*input3,*input4,*input5,*input6,*input7, *output;
	
	struct Flag *flag1;	
	struct History history; //metadata
	
	/************************************/
	/* FMEO Declarations*****************/
	char *name;   // input raster name
	char *result; //output raster name
	//File Descriptors
	int infd_redchan, infd_nirchan, infd_greenchan, infd_bluechan, infd_chan5chan, infd_chan7chan;
	int outfd;
	
	char  *bluechan, *greenchan,*redchan, *nirchan, *chan5chan, *chan7chan;
	
	int i=0,j=0;
	
	void *inrast_redchan, *inrast_nirchan, *inrast_greenchan, *inrast_bluechan, *inrast_chan5chan, *inrast_chan7chan;
	unsigned char *outrast;
	RASTER_MAP_TYPE data_type_output=DCELL_TYPE;
	RASTER_MAP_TYPE data_type_redchan;
	RASTER_MAP_TYPE data_type_nirchan;
	RASTER_MAP_TYPE data_type_greenchan;
	RASTER_MAP_TYPE data_type_bluechan;
	RASTER_MAP_TYPE data_type_chan5chan;
	RASTER_MAP_TYPE data_type_chan7chan;
	
	/************************************/
	G_gisinit(argv[0]);

	module = G_define_module();
	//module->keywords = _("vegetation index, biophysical parameters");
	module->description = _("13 types of vegetation indices from red and nir, and only some requiring additional bands");

	/* Define the different options */
	input1 = G_define_option() ;
	input1->key        =_("viname");
	input1->type       = TYPE_STRING;
	input1->required   = YES;
	input1->gisprompt  =_("Name of VI");
	input1->description=_("Name of VI: sr,ndvi,ipvi,dvi,pvi,wdvi,savi,msavi,msavi2,gemi,arvi,gvi,gari.");
	input1->answer     =_("ndvi");

	input2 = G_define_option() ;
	input2->key	   = _("red");
	input2->type       = TYPE_STRING;
	input2->required   = YES;
	input2->gisprompt  =_("old,cell,raster") ;
	input2->description=_("Name of the RED Channel surface reflectance map [0.0;1.0]");
	input2->answer     =_("redchan");

	input3 = G_define_option() ;
	input3->key        =_("nir");
	input3->type       = TYPE_STRING;
	input3->required   = YES;
	input3->gisprompt  =_("old,cell,raster");
	input3->description=_("Name of the NIR Channel surface reflectance map [0.0;1.0]");
	input3->answer     =_("nirchan");

	input4 = G_define_option() ;
	input4->key        =_("green");
	input4->type       = TYPE_STRING;
	input4->required   = NO;
	input4->gisprompt  =_("old,cell,raster");
	input4->description=_("Name of the GREEN Channel surface reflectance map [0.0;1.0]");
//	input4->answer     =_("greenchan");

	input5 = G_define_option() ;
	input5->key        =_("blue");
	input5->type       = TYPE_STRING;
	input5->required   = NO;
	input5->gisprompt  =_("old,cell,raster");
	input5->description=_("Name of the BLUE Channel surface reflectance map [0.0;1.0]");
//	input5->answer     =_("bluechan");

	input6 = G_define_option() ;
	input6->key        =_("chan5");
	input6->type       = TYPE_STRING;
	input6->required   = NO;
	input6->gisprompt  =_("old,cell,raster");
	input6->description=_("Name of the CHAN5 Channel surface reflectance map [0.0;1.0]");
//	input6->answer     =_("chan5chan");

	input7 = G_define_option() ;
	input7->key        =_("chan7");
	input7->type       = TYPE_STRING;
	input7->required   = NO;
	input7->gisprompt  =_("old,cell,raster");
	input7->description=_("Name of the CHAN7 Channel surface reflectance map [0.0;1.0]");
//	input7->answer     =_("chan7chan");

	output= G_define_option() ;
	output->key        =_("vi");
	output->type       = TYPE_STRING;
	output->required   = YES;
	output->gisprompt  =_("new,cell,raster");
	output->description=_("Name of the output vi layer");
	output->answer     =_("vi");

	flag1 = G_define_flag();
	flag1->key = 'q';
	flag1->description = _("Quiet");

	/********************/
	if (G_parser(argc, argv))
		exit (EXIT_FAILURE);
	viflag		= input1->answer;
	redchan	 	= input2->answer;
	nirchan	 	= input3->answer;
	greenchan	= input4->answer;
	bluechan	= input5->answer;
	chan5chan	= input6->answer;
	chan7chan	= input7->answer;

	result  = output->answer;
	verbose = (!flag1->answer);
	/***************************************************/
	mapset = G_find_cell2(redchan, "");
	if (mapset == NULL) {
		G_fatal_error(_("cell file [%s] not found"), redchan);
	}
	data_type_redchan = G_raster_map_type(redchan,mapset);
	if ( (infd_redchan = G_open_cell_old (redchan,mapset)) < 0)
		G_fatal_error (_("Cannot open cell file [%s]"), redchan);
	if (G_get_cellhd (redchan, mapset, &cellhd) < 0)
		G_fatal_error (_("Cannot read file header of [%s])"), redchan);
	inrast_redchan = G_allocate_raster_buf(data_type_redchan);
	/***************************************************/
	mapset = G_find_cell2 (nirchan, "");
	if (mapset == NULL) {
		G_fatal_error(_("cell file [%s] not found"),nirchan);
	}
	data_type_nirchan = G_raster_map_type(nirchan,mapset);
	if ( (infd_nirchan = G_open_cell_old (nirchan,mapset)) < 0)
		G_fatal_error(_("Cannot open cell file [%s]"), nirchan);
	if (G_get_cellhd (nirchan, mapset, &cellhd) < 0)
		G_fatal_error(_("Cannot read file header of [%s]"), nirchan);
	inrast_nirchan = G_allocate_raster_buf(data_type_nirchan);
	/***************************************************/
	if(greenchan){
		mapset = G_find_cell2(greenchan, "");
		if (mapset == NULL) {
			G_fatal_error(_("cell file [%s] not found"), greenchan);
		}
		data_type_greenchan = G_raster_map_type(greenchan,mapset);
		if ( (infd_greenchan = G_open_cell_old (greenchan,mapset)) < 0)
			G_fatal_error (_("Cannot open cell file [%s]"), greenchan);
		if (G_get_cellhd (greenchan, mapset, &cellhd) < 0)
			G_fatal_error (_("Cannot read file header of [%s])"), greenchan);
		inrast_greenchan = G_allocate_raster_buf(data_type_greenchan);
	}
	/***************************************************/
	if(bluechan){
		mapset = G_find_cell2(bluechan, "");
		if (mapset == NULL) {
			G_fatal_error(_("cell file [%s] not found"), bluechan);
		}
		data_type_bluechan = G_raster_map_type(bluechan,mapset);
		if ( (infd_bluechan = G_open_cell_old (bluechan,mapset)) < 0)
			G_fatal_error (_("Cannot open cell file [%s]"), bluechan);
		if (G_get_cellhd (bluechan, mapset, &cellhd) < 0)
			G_fatal_error (_("Cannot read file header of [%s])"), bluechan);
		inrast_bluechan = G_allocate_raster_buf(data_type_bluechan);
	}
	/***************************************************/
	if(chan5chan){
		mapset = G_find_cell2(chan5chan, "");
		if (mapset == NULL) {
			G_fatal_error(_("cell file [%s] not found"), chan5chan);
		}
		data_type_chan5chan = G_raster_map_type(chan5chan,mapset);
		if ( (infd_chan5chan = G_open_cell_old (chan5chan,mapset)) < 0)
			G_fatal_error (_("Cannot open cell file [%s]"), chan5chan);
		if (G_get_cellhd (chan5chan, mapset, &cellhd) < 0)
			G_fatal_error (_("Cannot read file header of [%s])"), chan5chan);
		inrast_chan5chan = G_allocate_raster_buf(data_type_chan5chan);
	}
	/***************************************************/
	if(chan7chan){
		mapset = G_find_cell2(chan7chan, "");
		if (mapset == NULL) {
			G_fatal_error(_("cell file [%s] not found"), chan7chan);
		}
		data_type_chan7chan = G_raster_map_type(chan7chan,mapset);
		if ( (infd_chan7chan = G_open_cell_old (chan7chan,mapset)) < 0)
			G_fatal_error (_("Cannot open cell file [%s]"), chan7chan);
		if (G_get_cellhd (chan7chan, mapset, &cellhd) < 0)
			G_fatal_error (_("Cannot read file header of [%s])"), chan7chan);
		inrast_chan7chan = G_allocate_raster_buf(data_type_chan7chan);
	}
	/***************************************************/

	



	G_debug(3, "number of rows %d",cellhd.rows);
	nrows = G_window_rows();
	ncols = G_window_cols();
	outrast = G_allocate_raster_buf(data_type_output);
	//nrows=8;
	/* Create New raster files */
	if ( (outfd = G_open_raster_new (result,data_type_output)) < 0)
		G_fatal_error(_("Could not open <%s>"),result);

	double db0[ncols],db1[ncols], db2[ncols],db3[ncols],db4[ncols],db5[ncols],R[ncols];
	int I[ncols],host_n=0;


	if((ret = grpc_initialize("/home/shamim/grass-6.0.2/raster/r.vi.grid/vi.conf") != GRPC_NO_ERROR)) {
                fprintf(stderr, "Error in grpc_initialize, %d\n",ret);
                exit(2);
        }

	

	for(i = 0; i < NUM_HOSTS; i++)
                grpc_function_handle_init(&handles[i], hosts[i], "VI_Server/VI_CALC"); 

	
	/* Process pixels */
	
	for (row = 0; row < nrows; row++)
	{
	
		host_n=host_n%NUM_HOSTS;
	

		DCELL d;
		DCELL d_bluechan;
		DCELL d_greenchan;
		DCELL d_redchan;
		DCELL d_nirchan;
		DCELL d_chan5chan;
		DCELL d_chan7chan;
		if(verbose)
			G_percent(row,nrows,2);

		/* read soil input maps */	
		if(G_get_raster_row(infd_redchan,inrast_redchan,row,data_type_redchan)<0)
			G_fatal_error(_("Could not read from <%s>"),redchan);
		if(G_get_raster_row(infd_nirchan,inrast_nirchan,row,data_type_nirchan)<0)
			G_fatal_error(_("Could not read from <%s>"),nirchan);
		if(greenchan){
			if(G_get_raster_row(infd_greenchan,inrast_greenchan,row,data_type_greenchan)<0)
				G_fatal_error(_("Could not read from <%s>"),greenchan);
		}
		if(bluechan){
			if(G_get_raster_row(infd_bluechan,inrast_bluechan,row,data_type_bluechan)<0)
				G_fatal_error(_("Could not read from <%s>"),bluechan);
		}
		if(chan5chan){
			if(G_get_raster_row(infd_chan5chan,inrast_chan5chan,row,data_type_chan5chan)<0)
				G_fatal_error(_("Could not read from <%s>"),chan5chan);
		}
		if(chan7chan){
			if(G_get_raster_row(infd_chan7chan,inrast_chan7chan,row,data_type_chan7chan)<0)
				G_fatal_error(_("Could not read from <%s>"),chan7chan);
		}
		/*process the data */
		for (col=0; col < ncols; col++)
		{
			switch(data_type_redchan){
				case CELL_TYPE:
					d_redchan = (double) ((CELL *) inrast_redchan)[col];
					break;
				case FCELL_TYPE:
					d_redchan = (double) ((FCELL *) inrast_redchan)[col];
					break;
				case DCELL_TYPE:
					d_redchan = ((DCELL *) inrast_redchan)[col];
					break;
			}
			switch(data_type_nirchan){
				case CELL_TYPE:
					d_nirchan = (double) ((CELL *) inrast_nirchan)[col];
					break;
				case FCELL_TYPE:
					d_nirchan = (double) ((FCELL *) inrast_nirchan)[col];
					break;
				case DCELL_TYPE:
					d_nirchan = ((DCELL *) inrast_nirchan)[col];
					break;
			}
			if (greenchan){
				switch(data_type_greenchan){
					case CELL_TYPE:
						d_greenchan = (double) ((CELL *) inrast_greenchan)[col];
						break;
					case FCELL_TYPE:
						d_greenchan = (double) ((FCELL *) inrast_greenchan)[col];
						break;
					case DCELL_TYPE:
						d_greenchan = ((DCELL *) inrast_greenchan)[col];
						break;
				}
			}
			if (bluechan){
				switch(data_type_bluechan){
					case CELL_TYPE:
						d_bluechan = (double) ((CELL *) inrast_bluechan)[col];
						break;
					case FCELL_TYPE:
						d_bluechan = (double) ((FCELL *) inrast_bluechan)[col];
						break;
					case DCELL_TYPE:
						d_bluechan = ((DCELL *) inrast_bluechan)[col];
						break;
				}
			}
			if (chan5chan){
				switch(data_type_chan5chan){
					case CELL_TYPE:
						d_chan5chan = (double) ((CELL *) inrast_chan5chan)[col];
						break;
					case FCELL_TYPE:
						d_chan5chan = (double) ((FCELL *) inrast_chan5chan)[col];
						break;
					case DCELL_TYPE:
						d_chan5chan = ((DCELL *) inrast_chan5chan)[col];
						break;
				}
			}
			if (chan7chan){
				switch(data_type_chan7chan){
					case CELL_TYPE:
						d_chan7chan = (double) ((CELL *) inrast_chan7chan)[col];
						break;
					case FCELL_TYPE:
						d_chan7chan = (double) ((FCELL *) inrast_chan7chan)[col];
						break;
					case DCELL_TYPE:
						d_chan7chan = ((DCELL *) inrast_chan7chan)[col];
						break;
				}
			}
			
			db0[col]= d_redchan;
			db1[col]= d_nirchan;
			db2[col]= d_greenchan;
			db3[col]= d_bluechan;
			db4[col]= d_chan5chan;
			db5[col]= d_chan7chan;			

		
		// to change to multiple to output files.
			if(G_is_d_null_value(&d_redchan)){
				i=0;
			}else if(G_is_d_null_value(&d_nirchan)){
				i=0;
			}else if((greenchan)&&G_is_d_null_value(&d_greenchan)){
				i=0;
			}else if((bluechan)&&G_is_d_null_value(&d_bluechan)){
				i=0;
			}else if((chan5chan)&&G_is_d_null_value(&d_chan5chan)){
				i=0;
			}else if((chan7chan)&&G_is_d_null_value(&d_chan7chan)){
				i=0;
			} else {
				/************************************/
				/*calculate simple_ratio        */
				if (!strcoll(viflag,"sr")){	
					i=1;
				}
				/*calculate ndvi	            */
				if (!strcoll(viflag,"ndvi")){
					i=2;
				}
				/*calculate ipvi	            */
				if (!strcoll(viflag,"ipvi")){
					i=3;
				}
				/*calculate dvi	            */
				if (!strcoll(viflag,"dvi")){
					i=4;	
				}
				/*calculate pvi	            */
				if (!strcoll(viflag,"pvi")){
					i=5;	
				}
				/*calculate wdvi	            */
				if (!strcoll(viflag,"wdvi")){
					i=6;
				}
				/*calculate savi	            */
				if (!strcoll(viflag,"savi")){
					i=7;
				}
				/*calculate msavi	            */
				if (!strcoll(viflag,"msavi")){
					i=8;
				}
				/*calculate msavi2            */
				if (!strcoll(viflag,"msavi2")){
					i=9;
				}
				/*calculate gemi	            */
				if (!strcoll(viflag,"gemi")){
					i=10;				
				}
				/*calculate arvi	            */
				if (!strcoll(viflag,"arvi")){
					i=11;
				}
				/*calculate gvi            */
				if (!strcoll(viflag,"gvi")){
					i=12;
				}
				/*calculate gari	            */
				if (!strcoll(viflag,"gari")){
					i=13;
				}
				I[col]=i;

			}
		}
		
		printf("grpc call start\n");
		
		if (grpc_call(&handles[host_n],ncols,I,db0,db1,db2,db3,db4,db5, R) != GRPC_NO_ERROR) {
                        fprintf(stderr,"grpc_call ERROR\n");
                        exit(2);
                }
                
		
		printf("grpc call finish\n");
		//all outcomes comes from the server will put back in raster
		
		
		for(j=0;j<ncols;j++)
			((DCELL *) outrast)[j] = R[j];
		if (G_put_raster_row (outfd, outrast, data_type_output) < 0)
			G_fatal_error(_("Cannot write to output raster file"));
					
		host_n++;

	}

	for (i = 0;i < NUM_HOSTS; i++)
                grpc_function_handle_destruct(&handles[i]);

        grpc_finalize();

	
	G_free(inrast_redchan);
	G_close_cell(infd_redchan);
	G_free(inrast_nirchan);
	G_close_cell(infd_nirchan);
	if(greenchan){
		G_free(inrast_greenchan);	
		G_close_cell(infd_greenchan);	
	}
	if(bluechan){
		G_free(inrast_bluechan);	
		G_close_cell(infd_bluechan);	
	}
	if(chan5chan){
		G_free(inrast_chan5chan);	
		G_close_cell(infd_chan5chan);	
	}
	if(chan7chan){
		G_free(inrast_chan7chan);	
		G_close_cell(infd_chan7chan);	
	}
	G_free(outrast);
	G_close_cell(outfd);
	
	//G_short_history(result, "raster", &history);
	//G_command_history(&history);
	//G_write_history(result,&history);

	exit(EXIT_SUCCESS);
}

