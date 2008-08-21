/****************************************************************************
 *
 * MODULE:       i.evapo.time_integration
 * AUTHOR(S):    Yann Chemin - yann.chemin@gmail.com
 * PURPOSE:      Integrate in time the evapotranspiration from satellite,
 *		 following a daily pattern from meteorological ETo.
 *
 * COPYRIGHT:    (C) 2008 by the GRASS Development Team
 *
 *               This program is free software under the GNU Lesser General Public
 *   	    	 License. Read the file COPYING that comes with GRASS for details.
 *
 *****************************************************************************/


#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <grass/gis.h>
#include <grass/glocale.h>

#define MAXFILES 400

int
main(int argc, char *argv[])
{
	struct Cell_head cellhd;/*region+header info*/
	char *mapset; /*mapset name*/
	int nrows, ncols;
	int row,col;

	struct GModule *module;
	struct Option *input, *input1, *input2, *input3, *output;
	
	struct History history; /*metadata*/
	struct Colors colors; /*Color rules*/
	/************************************/
	/* FMEO Declarations*****************/
	char *name,*name1,*name2; /*input raster name*/
	char *result; /*output raster name*/
	/*File Descriptors*/
	int nfiles, nfiles1, nfiles2;
	int infd[MAXFILES], infd1[MAXFILES], infd2[MAXFILES];
	int outfd;
	/****************************************/
	/* Pointers for file names 		*/
	char **names;
	char **ptr;
	char **names1;
	char **ptr1;
	char **names2;
	char **ptr2;
	/****************************************/
	double DOYbeforeETa[MAXFILES],DOYafterETa[MAXFILES];
	int bfr,aft;
	/****************************************/
	
	int ok;
	int i=0,j=0;
	double etodoy; /*minimum ETo DOY*/
	
	void *inrast[MAXFILES], *inrast1[MAXFILES], *inrast2[MAXFILES];
	DCELL *outrast;
	int data_format; /* 0=double  1=float  2=32bit signed int  5=8bit unsigned int (ie text) */
	RASTER_MAP_TYPE in_data_type[MAXFILES]; /* ETa */
	RASTER_MAP_TYPE in_data_type1[MAXFILES]; /* DOY of ETa */
	RASTER_MAP_TYPE in_data_type2[MAXFILES]; /* ETo */
	RASTER_MAP_TYPE out_data_type = DCELL_TYPE;

	/************************************/
	G_gisinit(argv[0]);

	module = G_define_module();
	module->keywords = _("evapotranspiration,temporal,integration");
	module->description =
		_("Temporal integration of satellite ET actual (ETa) following the daily ET reference (ETo) from meteorological station(s)\n");

	/* Define the different options */

	input = G_define_standard_option(G_OPT_R_INPUTS) ;
	input->key        =_("eta");
	input->description= _("Names of satellite ETa layers [mm/d or cm/d]");

	input1 = G_define_standard_option(G_OPT_R_INPUTS) ;
	input1->key        =_("eta_doy");
	input1->description= _("Names of satellite ETa Day of Year (DOY) layers [0-400] [-]");

	input2 = G_define_standard_option(G_OPT_R_INPUTS) ;
	input2->key        =_("eto");
	input2->description= _("Names of meteorological station ETo layers [0-400] [mm/d or cm/d]");

	input3 = G_define_option() ;
	input3->key        =_("eto_doy_min");
	input3->type       = TYPE_DOUBLE;
	input3->required   = YES;
	input3->description =_("Value of DOY for ETo first day");

	output = G_define_standard_option(G_OPT_R_OUTPUT) ;
	output->description= _("Name of the output temporally integrated ETa layer");

	/* FMEO init nfiles */
	nfiles = 1;
	nfiles1 = 1;
	nfiles2 = 1;
	/********************/
	if (G_parser(argc, argv))
		exit (-1);
	
	ok = 1;
	names	= input->answers;
	ptr	= input->answers;
	names1	= input1->answers;
	ptr1	= input1->answers;
	names2	= input2->answers;
	ptr2	= input2->answers;
	etodoy	= atof(input3->answer);

	result	= output->answer;
	/****************************************/
	if (G_legal_filename (result) < 0)
	{
		G_fatal_error (_("[%s] is an illegal name"), result);
		ok = 0;
	}
	/****************************************/
	for (; *ptr != NULL; ptr++)
	{
		if (nfiles > MAXFILES)
			G_fatal_error (_("%s - too many ETa files. Only %d allowed"), G_program_name(), MAXFILES);
		name = *ptr;
		/* find map in mapset */
		mapset = G_find_cell2 (name, "");
	        if (mapset == NULL)
		{
			G_fatal_error (_("cell file [%s] not found"), name);
			ok = 0;
		}
		if (!ok){
			continue;
		}
		infd[nfiles] = G_open_cell_old (name, mapset);
		if (infd[nfiles] < 0)
		{
			ok = 0;
			continue;
		}
		/* Allocate input buffer */
		in_data_type[nfiles] = G_raster_map_type(name, mapset);
		if( (infd[nfiles] = G_open_cell_old(name,mapset)) < 0){
			G_fatal_error(_("Cannot open cell file [%s]"), name);
		}
		if( (G_get_cellhd(name,mapset,&cellhd)) < 0){
			G_fatal_error(_("Cannot read file header of [%s]"), name);
		}
		inrast[nfiles] = G_allocate_raster_buf(in_data_type[nfiles]);
		nfiles++;
	}
	nfiles--;
	if (nfiles <= 1){
		G_fatal_error(_("The min specified input map is two"));
	}
	/****************************************/
	/****************************************/
	/****************************************/
	ok=1;
	for (; *ptr1 != NULL; ptr1++)
	{
		if (nfiles1 > MAXFILES)
			G_fatal_error (_("%s - too many ETa files. Only %d allowed"), G_program_name(), MAXFILES);
		name1 = *ptr1;
		/* find map in mapset */
		mapset = G_find_cell2 (name1, "");
	        if (mapset == NULL)
		{
			G_fatal_error (_("cell file [%s] not found"), name1);
			ok = 0;
		}
		if (!ok){
			continue;
		}
		infd1[nfiles] = G_open_cell_old (name1, mapset);
		if (infd1[nfiles] < 0)
		{
			ok = 0;
			continue;
		}
		/* Allocate input buffer */
		in_data_type1[nfiles] = G_raster_map_type(name1, mapset);
		if( (infd1[nfiles] = G_open_cell_old(name1,mapset)) < 0){
			G_fatal_error(_("Cannot open cell file [%s]"), name1);
		}
		if( (G_get_cellhd(name1,mapset,&cellhd)) < 0){
			G_fatal_error(_("Cannot read file header of [%s]"), name1);
		}
		inrast1[nfiles] = G_allocate_raster_buf(in_data_type[nfiles1]);
		nfiles1++;
	}
	nfiles1--;
	if (nfiles1 <= 1){
		G_fatal_error(_("The min specified input map is two"));
	}
	/****************************************/
	if(nfiles!=nfiles1)	
		G_fatal_error (_("ETa and ETa_DOY file numbers are not equal!"));
	/****************************************/
	/****************************************/
	ok=1;
	for (; *ptr2 != NULL; ptr2++)
	{
		if (nfiles > MAXFILES)
			G_fatal_error (_("%s - too many ETa files. Only %d allowed"), G_program_name(), MAXFILES);
		name2 = *ptr2;
		/* find map in mapset */
		mapset = G_find_cell2 (name2, "");
	        if (mapset == NULL)
		{
			G_fatal_error (_("cell file [%s] not found"), name2);
			ok = 0;
		}
		if (!ok){
			continue;
		}
		infd2[nfiles2] = G_open_cell_old (name2, mapset);
		if (infd2[nfiles2] < 0)
		{
			ok = 0;
			continue;
		}
		/* Allocate input buffer */
		in_data_type2[nfiles2] = G_raster_map_type(name2, mapset);
		if( (infd2[nfiles2] = G_open_cell_old(name2,mapset)) < 0){
			G_fatal_error(_("Cannot open cell file [%s]"), name2);
		}
		if( (G_get_cellhd(name2,mapset,&cellhd)) < 0){
			G_fatal_error(_("Cannot read file header of [%s]"), name2);
		}
		inrast2[nfiles2] = G_allocate_raster_buf(in_data_type2[nfiles2]);
		nfiles2++;
	}
	nfiles2--;
	if (nfiles2 <= 1){
		G_fatal_error(_("The min specified input map is two"));
	}
	/****************************************/
	/****************************************/
	
	/***************************************************/
	/* Allocate output buffer, use input map data_type */
	nrows = G_window_rows();
	ncols = G_window_cols();
	outrast = G_allocate_raster_buf(out_data_type);
	
	/* Create New raster files */
	if ( (outfd = G_open_raster_new (result,1)) < 0){
		G_fatal_error (_("Could not open <%s>"),result);
	}
	/*******************/
	/* Process pixels */
	double doy[MAXFILES];
	double sum[MAXFILES];
	for (row = 0; row < nrows; row++)
	{
		DCELL d_out;
		DCELL d_ETrF[MAXFILES];
		DCELL d[MAXFILES];
		DCELL d1[MAXFILES];
		DCELL d2[MAXFILES];
		G_percent (row, nrows, 2);
		/* read input map */
		for (i=1;i<=nfiles;i++)
		{
			if( (G_get_raster_row(infd[i],inrast[i],row,in_data_type[i])) < 0){
				G_fatal_error (_("Could not read from <%s>"),name);
			}
		}
		for (i=1;i<=nfiles1;i++)
		{
			if( (G_get_raster_row(infd1[i],inrast1[i],row,in_data_type1[i])) < 0){
				G_fatal_error (_("Could not read from <%s>"),name1);
			}
		}
		for (i=1;i<=nfiles2;i++)
		{
			if( (G_get_raster_row(infd2[i],inrast2[i],row,in_data_type2[i])) < 0){
				G_fatal_error (_("Could not read from <%s>"),name2);
			}
		}
		/*process the data */
		for (col=0; col < ncols; col++)
		{
			for(i=1;i<=nfiles;i++)
			{
				switch(in_data_type[i])
				{
					case CELL_TYPE:
						d[i] = (double) ((CELL *) inrast[i])[col];
						break;
					case FCELL_TYPE:
						d[i] = (double) ((FCELL *) inrast[i])[col];
						break;
					case DCELL_TYPE:
						d[i] = (double) ((DCELL *) inrast[i])[col];
						break;
				}
			}
			for(i=1;i<=nfiles1;i++)
			{
				switch(in_data_type1[i])
				{
					case CELL_TYPE:
						d1[i] = (double) ((CELL *) inrast1[i])[col];
						break;
					case FCELL_TYPE:
						d1[i] = (double) ((FCELL *) inrast1[i])[col];
						break;
					case DCELL_TYPE:
						d1[i] = (double) ((DCELL *) inrast1[i])[col];
						break;
				}
			}
			for(i=1;i<=nfiles2;i++)
			{
				switch(in_data_type2[i])
				{
					case CELL_TYPE:
						d2[i] = (double) ((CELL *) inrast2[i])[col];
						break;
					case FCELL_TYPE:
						d2[i] = (double) ((FCELL *) inrast2[i])[col];
						break;
					case DCELL_TYPE:
						d2[i] = (double) ((DCELL *) inrast2[i])[col];
						break;
				}
			}
			/* Find out the DOY of the eto image	*/
			/* DOY_eto_index = ModisDOY - etodoymin	*/
			for(i=1;i<=nfiles1;i++)
			{
				doy[i] = d1[i] - etodoy;
				d_ETrF[i]=d[i]/d2[(int)doy[i]];
			}
			for(i=1;i<=nfiles1;i++)
			{
				if(i==1)
					DOYbeforeETa[i]=etodoy;
				else
					DOYbeforeETa[i]=(d[i]-d[i-1])/2.0;
				if(i==nfiles1)
					DOYafterETa[i]=etodoy+nfiles2;
				else
					DOYafterETa[i]=(d[i+1]-d[i])/2.0;
			}	
			sum[MAXFILES]=0.0;
			for(i=1;i<=nfiles1;i++)
			{
				bfr = (int) DOYbeforeETa[i];
				aft = (int) DOYafterETa[i];
				for(j=bfr;j<aft;j++)
				{
					sum[i]+=d2[j];	
				}
			}
			d_out = 0.0;
			for(i=1;i<=nfiles1;i++)
			{
				d_out += d_ETrF[i]*sum[i];
			}	
			outrast[col] = d_out;
		}
		if (G_put_raster_row (outfd, outrast, out_data_type) < 0)
			G_fatal_error (_("Cannot write to <%s>"),result);
	}
	for (i=1;i<=nfiles;i++)
	{
		G_free (inrast[i]);
		G_close_cell (infd[i]);
		G_free (inrast1[i]);
		G_close_cell (infd1[i]);
		G_free (inrast2[i]);
		G_close_cell (infd2[i]);
	}
	G_free (outrast);
	G_close_cell (outfd);
	
	/* Color table from 0.0 to 10.0 */
	G_init_colors(&colors);
	G_add_color_rule(0.0,0,0,0,10.0,255,255,255,&colors);
	/* Metadata */
	G_short_history(result,"raster",&history);
	G_command_history(&history);
	G_write_history(result,&history);

	exit(EXIT_SUCCESS);
}
