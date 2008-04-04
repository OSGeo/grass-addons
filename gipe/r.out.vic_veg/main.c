/****************************************************************************
 *
 * MODULE:       r.out.vic_veg
 * AUTHOR(S):    Yann Chemin - yann.chemin@gmail.com
 * PURPOSE:      Creates a VIC vegetation input file.
 * 		 Filling only Land cover class, with only one class,
 * 		 and one standard root system.
 * 		 Option to add monthly LAI (12 maps).
 * 		 
 * COPYRIGHT:    (C) 2008 by the GRASS Development Team
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
#include <grass/gprojects.h>
#include <grass/glocale.h>

int veglib(char *filename);

int main(int argc, char *argv[])
{
	struct Cell_head cellhd; //region+header info
	char *mapset; // mapset name
	int nrows, ncols;
	int row,col;

	int verbose=1;
	int not_ll=0;//if proj is not lat/long, it will be 1.
	struct GModule *module;
	struct Option *input1, *input2, *output1, *output2;
	
	struct Flag *flag1;	
	struct History history; //metadata
	
	struct pj_info iproj;
	struct pj_info oproj;
	/************************************/
	/* FMEO Declarations*****************/
	char 	*landcover_name;// input raster name
	char 	lai_name[12]; 	// input monthly raster files name
	char 	*result1; 	//output raster name
	//File Descriptors
	int 	infd, infd_lai[12];

	int 	i=0,j=0;
	double 	xp, yp;
	double 	xmin, ymin;
	double 	xmax, ymax;
	double 	stepx,stepy;
	double 	latitude, longitude;

	void 			*inrast_landcover;
	void 			*inrast_lai[12];
	RASTER_MAP_TYPE 	data_type_inrast_landcover;
	RASTER_MAP_TYPE 	data_type_inrast_lai[12];

	FILE	*f; 		// output ascii file
	int 	grid_count; 	// grid cell count
	char 	*dummy_data1; 	// dummy data part 1
	char 	*dummy_data2; 	// dummy data part 2
	double	*lai[12];	// lAI data for each month
	char 	**lai_ptr;	// pointer to get the input2->answers
	int	nfiles; 	// count LAI input files
	char	**test, **ptr;	// test number of LAI input files
	/************************************/
	G_gisinit(argv[0]);

	module = G_define_module();
	module->keywords = _("VIC, hydrology, soil");
	module->description = _("creates a vegetation ascii file from land cover map. Optionally LAI data from 12 LAI maps.");

	/* Define the different options */
	input1 = G_define_standard_option(G_OPT_R_INPUT) ;
	input1->key	   = _("input");
	input1->description=_("Name of the land cover input map");

	input2 = G_define_standard_option(G_OPT_R_INPUT) ;
	input2->key	   = _("LAI");
	input2->multiple   = YES;
	input2->required   = NO;
	input2->description=_("Name of the LAI input maps (12 of them!)");
	
	output1 = G_define_option() ;
	output1->key        =_("output");
	output1->description=_("Name of the output vic soil ascii file");
	output1->answer     =_("vic_soil.asc");
	
	output2 = G_define_option() ;
	output2->key        =_("veglib");
	output2->required   = NO;
	output2->description=_("Name of a standard vegetation library file");
	output2->answer     =_("veglib");
	/********************/
	if (G_parser(argc, argv))
		exit (EXIT_FAILURE);

	landcover_name	 	= input1->answer;
	result1 	 	= output1->answer;
	/************************************************/
	/* STANDARD VEGLIB CREATION HERE 		*/
	if(output2->answer)
		veglib(output2->answer);
	/************************************************/
	/* LOADING OPTIONAL LAI MONTHLY MAPS 		*/
	if (input2->answer){
		test = input2->answers;
		for (ptr = test, nfiles = 0; *ptr != NULL; ptr++, nfiles++)
			;
		if (nfiles < 12)
			G_fatal_error(_("The exact number of LAI input maps is 12"));
		lai_ptr = input2->answers;
		for(; *lai_ptr != NULL; lai_ptr++){
			strcpy(lai_name,*lai_ptr);
		}
		for(i=0;i<12;i++){
			mapset = G_find_cell2(&lai_name[i], "");
			if (mapset == NULL) {
				G_fatal_error(_("cell file [%s] not found"), lai_name[i]);
			}
			data_type_inrast_lai[i] = G_raster_map_type(&lai_name[i],mapset);
			if ((infd_lai[i] = G_open_cell_old (&lai_name[i],mapset)) < 0)
				G_fatal_error (_("Cannot open cell file [%s]"), lai_name[i]);
			if (G_get_cellhd (&lai_name[i], mapset, &cellhd) < 0)
				G_fatal_error (_("Cannot read file header of [%s])"), lai_name[i]);
			inrast_lai[i] = G_allocate_raster_buf(data_type_inrast_lai[i]);
		}
	}
	/************************************************/
	/* LOADING REQUIRED LAND COVER MAP		*/
	mapset = G_find_cell2(landcover_name, "");
	if (mapset == NULL) {
		G_fatal_error(_("cell file [%s] not found"), landcover_name);
	}
	data_type_inrast_landcover = G_raster_map_type(landcover_name,mapset);
	if ( (infd = G_open_cell_old (landcover_name,mapset)) < 0)
		G_fatal_error (_("Cannot open cell file [%s]"), landcover_name);
	if (G_get_cellhd (landcover_name, mapset, &cellhd) < 0)
		G_fatal_error (_("Cannot read file header of [%s])"), landcover_name);
	inrast_landcover = G_allocate_raster_buf(data_type_inrast_landcover);
	/***************************************************/
	G_debug(3, "number of rows %d",cellhd.rows);

	stepx=cellhd.ew_res;
	stepy=cellhd.ns_res;

	xmin=cellhd.west;
	xmax=cellhd.east;
	ymin=cellhd.south;
	ymax=cellhd.north;

	nrows = G_window_rows();
	ncols = G_window_cols();

	/*Initialize grid cell process switch*/
	f=fopen(result1,"w");

	/*Initialize grid cell count*/
	grid_count = 1;

	/*Initialize dummy data*/
	dummy_data1 = "0.10 0.1 1.00 0.65 0.50 0.25";
	dummy_data2 = "0.312 0.413 0.413 0.413 0.413 0.488 0.975 1.150 0.625 0.312 0.312 0.312";
	
	for (row = 0; row < nrows; row++){
		CELL c_landcover;
		DCELL d_lai[12];
		G_percent(row,nrows,2);
		if(G_get_raster_row(infd,inrast_landcover,row,data_type_inrast_landcover)<0)
			G_fatal_error(_("Could not read from <%s>"),landcover_name);
		if(input2->answer){
			for(i=0;i<12;i++){
				if(G_get_raster_row(infd_lai[i],inrast_lai[i],row,data_type_inrast_lai[i])<0)
					G_fatal_error(_("Could not read from <%s>"),lai_name[i]);
				}
		}
		for (col=0; col < ncols; col++){
			/*Extract landcover data*/
			switch(data_type_inrast_landcover){
				case CELL_TYPE:
					c_landcover= (int) ((CELL *) inrast_landcover)[col];
					break;
				case FCELL_TYPE:
					c_landcover= (int) ((FCELL *) inrast_landcover)[col];
					break;
				case DCELL_TYPE:
					c_landcover= (int) ((DCELL *) inrast_landcover)[col];
					break;
			}
			/*Extract lai monthly data*/
			if(input2->answer){
				for(i=0;i<12;i++){
					switch(data_type_inrast_lai[i]){
					case CELL_TYPE:
						d_lai[i]= (double) ((CELL *) inrast_lai[i])[col];
						break;
					case FCELL_TYPE:
						d_lai[i]= (double) ((FCELL *) inrast_lai[i])[col];
						break;
					case DCELL_TYPE:
						d_lai[i]= (double) ((DCELL *) inrast_lai[i])[col];
						break;
					}
				}
			}
			if(G_is_c_null_value(&c_landcover)){
				/* Skip the Null value pixel */
			} else {
				/*Print to ascii file*/
				/*Grid cell count and number of classes in that grid cell (=1)*/
				fprintf(f,"%d 1\n", grid_count);
				/*Class number, percentage that this class covers in the
				 * grid cell(=1.0, full grid cell)
				 * 3 root zones with depths of 10cm, 10cm and 1.0m
				 * for those 3 root zone depths, how much root in each (%)
				 * here we have 0.65, 0.50 and 0.25
				 * */
				fprintf(f,"%d 1.0 %s\n", c_landcover, dummy_data1);
				/*Load monthly LAI maps data if available*/
				if(input2->answer){
					fprintf(f,"%5.3f %5.3f %5.3f %5.3f %5.3f %5.3f %5.3f %5.3f %5.3f %5.3f %5.3f %5.3f\n", lai[0], lai[1], lai[2], lai[3], lai[4], lai[5], lai[6], lai[7], lai[8], lai[9], lai[10], lai[11]);
				} else {
				//	fprintf(f,"%s\n", dummy_data2);
				}
				grid_count=grid_count+1;
			} /* End of if NULL() statement */
		}
	}
	G_free (inrast_landcover);
	G_close_cell (infd);
	if(input2->answer){
		for(i=0;i<12;i++){
			G_free (inrast_lai[i]);
			G_close_cell (infd_lai[i]);
		}
	}
	fclose(f);
	exit(EXIT_SUCCESS);
}

