/****************************************************************************
 *
 * MODULE:     r.vi.mpi
 * AUTHOR(S):  Shamim Akhter shamimakhter@gmail.com
		 Baburao Kamble baburaokamble@gmail.com
 *		 Yann Chemin - ychemin@gmail.com
 * PURPOSE:    Calculates 13 vegetation indices 
 * 		 based on biophysical parameters. 
 *
 * COPYRIGHT:  (C) 2006 by the Tokyo Institute of Technology, Japan
 *		 (C) 2006 by the Asian Institute of Technology, Thailand
 * 		 (C) 2002 by the GRASS Development Team
 *
 *             This program is free software under the GNU General Public
 *   	    	 License (>=v2). Read the file COPYING that comes with GRASS
 *   	    	 for details.
 * 
 * Remark:              
 *		 These are generic indices that use red and nir for most of them. 
 *             Those can be any use by standard satellite having V and IR.
 *		 However arvi uses red, nir and blue; 
 *		 GVI uses B,G,R,NIR, chan5 and chan 7 of landsat;
 *		 and GARI uses B,G,R and NIR.      
 *
 *****************************************************************************/

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include "grass/gis.h"
#include "grass/glocale.h"
#include "mpi.h"

int main(int argc, char *argv[])
{
	int me,host_n,nrows,ncols;
	int NUM_HOSTS;
	MPI_Status status;
	MPI_Init(&argc,&argv);
	MPI_Comm_size(MPI_COMM_WORLD,&NUM_HOSTS);
	MPI_Comm_rank(MPI_COMM_WORLD,&me);
 
	//printf("rank =%d\n",me);	
	if(!me)
	{

		printf("I am Master\n");
		struct Cell_head cellhd; //region+header info
		char *mapset; // mapset name
		int row,col,row_n;
		int verbose=1;
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
		redchan	 = input2->answer;
		nirchan	 = input3->answer;
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
		if(bluechan)
		{
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
		if(chan5chan)
		{
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
		if(chan7chan)
		{
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
		//nrows=9;
	
		outrast = G_allocate_raster_buf(data_type_output);
	/* Create New raster files */
		if ( (outfd = G_open_raster_new (result,data_type_output)) < 0)
			G_fatal_error(_("Could not open <%s>"),result);

		double db0[ncols],db1[ncols], db2[ncols],db3[ncols],db4[ncols],db5[ncols],R[ncols],outputImage[NUM_HOSTS][ncols];
		int I[ncols];
		host_n=1;

		for(i=1;i<NUM_HOSTS;i++){

			MPI_Send(&nrows,1,MPI_INT,i,1,MPI_COMM_WORLD);
                	MPI_Send(&ncols,1,MPI_INT,i,1,MPI_COMM_WORLD);
		}
		/* Process pixels */
		int k,r,nh,cn;
	
		for (r = 1; r*(NUM_HOSTS-1) <= nrows;r++ )
		{
			
			for(k=1;k<NUM_HOSTS;k++)
			{

				
				row=(r-1)*(NUM_HOSTS-1)+k-1;

				DCELL d_bluechan;
				DCELL d_greenchan;
				DCELL d_redchan;
				DCELL d_nirchan;
				DCELL d_chan5chan;
				DCELL d_chan7chan;
				if(verbose)
					G_percent(row,nrows,2);
				printf("r=%d, k=%d, row=%d\n",r,k,row);
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

					}//else
			
				}//col
				//printf("Row data has genareted\n");
				row_n=k-1;
				MPI_Send(&row_n,1,MPI_INT,k,1,MPI_COMM_WORLD);
				MPI_Send(I,ncols,MPI_INT,k,1,MPI_COMM_WORLD);
				MPI_Send(db0,ncols,MPI_DOUBLE,k,1,MPI_COMM_WORLD);
				MPI_Send(db1,ncols,MPI_DOUBLE,k,1,MPI_COMM_WORLD);
				//MPI_Send(db2,ncols,MPI_DOUBLE,k,1,MPI_COMM_WORLD);
				//MPI_Send(db3,ncols,MPI_DOUBLE,k,1,MPI_COMM_WORLD);
				//MPI_Send(db4,ncols,MPI_DOUBLE,k,1,MPI_COMM_WORLD);
				//MPI_Send(db5,ncols,MPI_DOUBLE,k,1,MPI_COMM_WORLD);
						
	
			}//k				
			for(k=1;k<NUM_HOSTS;k++){
				MPI_Recv(&row_n,1,MPI_INT,k,1,MPI_COMM_WORLD,&status);
				MPI_Recv(R,ncols,MPI_DOUBLE,k,1,MPI_COMM_WORLD,&status);
				for (cn=0;cn<ncols;cn++)
					outputImage[row_n][cn]=R[cn];
			}
			
			for(k=0;k<(NUM_HOSTS-1);k++)
                	{
                        	for(j=0;j<ncols;j++)
                        		((DCELL *) outrast)[j] = outputImage[k][j];
                        	if (G_put_raster_row (outfd, outrast, data_type_output) < 0)
                                	G_fatal_error(_("Cannot write to output raster file"));

                	}

	
		}//r
		k=1;
		int lm=0;	
		for(r=row+1;r<nrows;r++)
		{	

			
                          printf("row %d, node %d\n",r,k);
                        	DCELL d_bluechan;
                        	DCELL d_greenchan;
                                DCELL d_redchan;
                                DCELL d_nirchan;
                                DCELL d_chan5chan;
                                DCELL d_chan7chan;
                                if(verbose)
                                        G_percent(row,nrows,2);

                                /* read soil input maps */
                                if(G_get_raster_row(infd_redchan,inrast_redchan,r,data_type_redchan)<0)
                                        G_fatal_error(_("Could not read from <%s>"),redchan);
                                if(G_get_raster_row(infd_nirchan,inrast_nirchan,r,data_type_nirchan)<0)
                                        G_fatal_error(_("Could not read from <%s>"),nirchan);
                                if(greenchan){
                                        if(G_get_raster_row(infd_greenchan,inrast_greenchan,r,data_type_greenchan)<0)
                                                G_fatal_error(_("Could not read from <%s>"),greenchan);
                                }
                                if(bluechan){
                                        if(G_get_raster_row(infd_bluechan,inrast_bluechan,r,data_type_bluechan)<0)
                                                G_fatal_error(_("Could not read from <%s>"),bluechan);
                                }
                                if(chan5chan){
                                        if(G_get_raster_row(infd_chan5chan,inrast_chan5chan,r,data_type_chan5chan)<0)
                                                G_fatal_error(_("Could not read from <%s>"),chan5chan);
                                }
                                if(chan7chan){
                                        if(G_get_raster_row(infd_chan7chan,inrast_chan7chan,r,data_type_chan7chan)<0)
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
                                        } else 
					{
                                        /************************************/
                                        /*calculate simple_ratio        */
                                                if (!strcoll(viflag,"sr")){
                                                        i=1;
                                                }
                                        /*calculate ndvi                    */
                                                if (!strcoll(viflag,"ndvi")){
                                                        i=2;
                                                }
                                        /*calculate ipvi                    */
                                                if (!strcoll(viflag,"ipvi")){
                                                        i=3;
                                                }
                                        /*calculate dvi             */
                                                if (!strcoll(viflag,"dvi")){
                                                        i=4;
                                                }
                                        /*calculate pvi             */
                                                if (!strcoll(viflag,"pvi")){
                                                        i=5;
                                                }
                                        /*calculate wdvi                    */
                                                if (!strcoll(viflag,"wdvi")){
                                                        i=6;
                                                }
                                        /*calculate savi                    */
                                                if (!strcoll(viflag,"savi")){
                                                        i=7;
                                                }
                                        /*calculate msavi                   */
                                                if (!strcoll(viflag,"msavi")){
                                                        i=8;
                                                }
                                        /*calculate msavi2            */
                                                if (!strcoll(viflag,"msavi2")){
                                                        i=9;
                                                }
                                        /*calculate gemi                    */
                                                if (!strcoll(viflag,"gemi")){
                                                        i=10;
                                                }
                                        /*calculate arvi                    */
                                                if (!strcoll(viflag,"arvi")){
                                                        i=11;
                                                }
                                        /*calculate gvi            */
                                                if (!strcoll(viflag,"gvi")){
                                                        i=12;
                                                }
                                        /*calculate gari                    */
                                                if (!strcoll(viflag,"gari")){
                                                        i=13;
                                                }
					}
                                                I[col]=i;
				}//col
                      		row_n=k-1;
                                MPI_Send(&row_n,1,MPI_INT,k,1,MPI_COMM_WORLD);
                                MPI_Send(I,ncols,MPI_INT,k,1,MPI_COMM_WORLD);
                                MPI_Send(db0,ncols,MPI_DOUBLE,k,1,MPI_COMM_WORLD);
                                MPI_Send(db1,ncols,MPI_DOUBLE,k,1,MPI_COMM_WORLD);
                                //MPI_Send(db2,ncols,MPI_DOUBLE,k,1,MPI_COMM_WORLD);
                                //MPI_Send(db3,ncols,MPI_DOUBLE,k,1,MPI_COMM_WORLD);
                                //MPI_Send(db4,ncols,MPI_DOUBLE,k,1,MPI_COMM_WORLD);
                                //MPI_Send(db5,ncols,MPI_DOUBLE,k,1,MPI_COMM_WORLD);
				k++;
				lm=1;		
			}//r 
			if(lm)
			{	
				for(nh=1;nh<k;nh++){
                                	MPI_Recv(&row_n,1,MPI_INT,nh,1,MPI_COMM_WORLD,&status);
                                	MPI_Recv(R,ncols,MPI_DOUBLE,nh,1,MPI_COMM_WORLD,&status);
                                	for (cn=0;cn<ncols;cn++)
                                        	outputImage[row_n][cn]=R[cn];
                        	}

                        	for(nh=0;nh<(k-1);nh++)
                        	{
                                	for(j=0;j<ncols;j++)
                                        	((DCELL *) outrast)[j] = outputImage[nh][j];
                                	if (G_put_raster_row (outfd, outrast, data_type_output) < 0)
                                        	G_fatal_error(_("Cannot write to output raster file"));

                        	}
			}



        	MPI_Finalize();
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
	}//if end	
	else if(me){

		int col,n_rows,i,row_n,modv,nrows,ncols;
		int *I;
		double *a, *b, *c, *d, *e, *f, *r;
		MPI_Recv(&nrows,1,MPI_INT,0,1,MPI_COMM_WORLD,&status);
        	MPI_Recv(&ncols,1,MPI_INT,0,1,MPI_COMM_WORLD,&status);
		printf("Slave->%d: nrows=%d, ncols=%d \n",me,nrows,ncols);
 	
		I=(int *)malloc((ncols+1)*sizeof(int));
        	a=(double *)malloc((ncols+1)*sizeof(double));
        	b=(double *)malloc((ncols+1)*sizeof(double));
        	c=(double *)malloc((ncols+1)*sizeof(double));
       		d=(double *)malloc((ncols+1)*sizeof(double));
        	e=(double *)malloc((ncols+1)*sizeof(double));
        	f=(double *)malloc((ncols+1)*sizeof(double));
        	r=(double *)malloc((ncols+1)*sizeof(double));
	
		n_rows=nrows/(NUM_HOSTS-1);
		modv=nrows%(NUM_HOSTS-1);
	
		int temp;	
		if(modv>=me)
			n_rows++;
		for(i=0;i<n_rows;i++)
		{
				
			MPI_Recv(&row_n,1,MPI_INT,0,1,MPI_COMM_WORLD,&status);
			MPI_Recv(I,ncols,MPI_INT,0,1,MPI_COMM_WORLD,&status);
			MPI_Recv(a,ncols,MPI_DOUBLE,0,1,MPI_COMM_WORLD,&status);
			MPI_Recv(b,ncols,MPI_DOUBLE,0,1,MPI_COMM_WORLD,&status);
			//MPI_Recv(c,ncols,MPI_DOUBLE,0,1,MPI_COMM_WORLD,&status);
			//MPI_Recv(d,ncols,MPI_DOUBLE,0,1,MPI_COMM_WORLD,&status);
			//MPI_Recv(e,ncols,MPI_DOUBLE,0,1,MPI_COMM_WORLD,&status);
			//MPI_Recv(f,ncols,MPI_DOUBLE,0,1,MPI_COMM_WORLD,&status);
			
			for (col=0; col<ncols; col++)
			{
	
				for(temp=0;temp<2000;temp++)
				{//increase arbirtrarily the number of operations for testing MPI		
			
				if (I[col]==0) r[col]=-999.99;
				else if (I[col]==1){
				//sr
					if(  a[col] ==  0.0 ){
						r[col] = -1.0;
					} else {
						r[col] = (b[col]/ a[col]);
					}	
				}
				else if (I[col]==2){
				//ndvi
					if( ( b[col] + a[col] ) ==  0.0 ){
						r[col] = -1.0;
					} else {
						r[col] = ( b[col] - a[col] ) / ( b[col] + a[col] );
					}
				}
				else if (I[col]==3){
				//ipvi	
		
					if( ( b[col] + a[col] ) ==  0.0 ){
						r[col] = -1.0;
					} else {
						r[col] = ( b[col] ) / ( b[col] + a[col] );
					}	

				}	
				else if (I[col]==4){
				//dvi
					if( ( b[col] + a[col] ) ==  0.0 ){
						r[col] = -1.0;
					} else {
						r[col] = ( b[col] - a[col] ) ;
					}		
				}
				else if (I[col]==5){
				//pvi
					if( ( b[col] + a[col] ) ==  0.0 ){
						r[col] = -1.0;
					} else {
						r[col] = (sin(1.0) * b[col] ) / ( cos(1.0) * a[col] ); 
					}
				}
				else if (I[col]==6){
				//wdvi
					double slope=1;//slope of soil line //
					if( ( b[col] + a[col] ) ==  0.0 ){
						r[col] = -1.0;
					} else {
						r[col] = ( b[col] - slope*a[col] );
					}
				}
				else if (I[col]==7){
				//savi
					if( ( b[col] + a[col] ) ==  0.0 ){
						r[col] = -1.0;
					} else {
						r[col] = ((1+0.5)*( b[col] - a[col] )) / ( b[col] + a[col] +0.5);
					}
				}
				else if (I[col]==8){
				//msavi
					if( ( b[col] + a[col] ) ==  0.0 ){
						r[col] = -1.0;
					} else {
						r[col] =(1/2)*(2 * (b[col]+1)-sqrt((2*b[col]+1)*(2*b[col]+1))-(8 *(b[col]-a[col]))) ;
					}
				}
				else if (I[col]==9){
				//msavi2
					if( ( b[col] + a[col] ) ==  0.0 ){
						r[col] = -1.0;
					} else {
						r[col] =(1/2)*(2 * (b[col]+1)-sqrt((2*b[col]+1)*(2*b[col]+1))-(8 *(b[col]-a[col]))) ;
					}
				}
				else if (I[col]==10){
				//gemi
					if( ( b[col] + a[col] ) ==  0.0 ){
						r[col] = -1.0;
					} else {
						r[col] = (( (2*((b[col] * b[col])-(a[col] * a[col]))+1.5*b[col]+0.5*a[col]) /(b[col]+ a[col] + 0.5)) * (1 - 0.25 * (2*((b[col] * b[col])-(a[col] * a[col]))+1.5*b[col]+0.5*a[col]) /(b[col] + a[col] + 0.5))) -( (a[col] - 0.125) / (1 - a[col])) ;
					}
				}
				else if (I[col]==11){
				//arvi
					if( ( b[col] + a[col] ) ==  0.0 ){
						r[col] = -1.0;
					} else {
						r[col] = ( b[col] - (2*a[col] - d[col])) / ( b[col] + (2*a[col] - d[col]));
					}
				}
				else if (I[col]==12){
				//gvi
					if( ( b[col] + a[col] ) ==  0.0 ){
						r[col] = -1.0;
					} else	{
						r[col] = (-0.2848*d[col]-0.2435*c[col]-0.5436*a[col]+0.7243*b[col]+0.0840*e[col]- 0.1800*f[col]);
					}
				}
				else if (I[col]==13){
				//gari
					r[col] = ( b[col] - (c[col]-(d[col] - a[col]))) / ( b[col] + (c[col]-(d[col] - a[col]))) ;
				}

				} //for temp

		}// col end
	
		MPI_Send(&row_n,1,MPI_INT,0,1,MPI_COMM_WORLD);
		MPI_Send(r,ncols,MPI_DOUBLE,0,1,MPI_COMM_WORLD);
	}//row end

	free(I);
	free(a);
	free(b);
	free(c);
	free(d);
	free(e);
	free(f);
	free(r);
	MPI_Finalize();	

   	}//if end
}//main end

