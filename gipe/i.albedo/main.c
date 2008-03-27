/****************************************************************************
 *
 * MODULE:       i.albedo
 * AUTHOR(S):    Yann Chemin - ychemin@gmail.com
 * PURPOSE:      Calculate Broadband Albedo (0.3-3 Micrometers)
 *               from Surface Reflectance (Modis, AVHRR, Landsat, Aster).
 *
 * COPYRIGHT:    (C) 2004-2006 by the GRASS Development Team
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
#include "functions.h"

#define MAXFILES 10

//extern	FCELL f_f(FCELL);

double bb_alb_aster( double greenchan, double redchan, double nirchan, double swirchan1, double swirchan2, double swirchan3, double swirchan4, double swirchan5, double swirchan6 );
double bb_alb_landsat( double bluechan, double greenchan, double redchan, double nirchan, double chan5, double chan7 );
double bb_alb_noaa( double redchan, double nirchan );
double bb_alb_modis( double redchan, double nirchan, double chan3, double chan4, double chan5, double chan6, double chan7 );

int
main(int argc, char *argv[])
{
	struct Cell_head cellhd;//region+header info
	char *mapset; //mapset name
	int nrows, ncols;
	int row,col;

	int verbose=1;
	struct GModule *module;
	struct Option *input,*output;
	
	struct Flag *flag1, *flag2, *flag3, *flag4, *flag5;
	struct History history; //metadata

	/************************************/
	/* FMEO Declarations*****************/
	char *name; //input raster name
	char *result; //output raster name
	//File Descriptors
	int nfiles;
	int infd[MAXFILES];
	int outfd;

	char **names;
	char **ptr;
	
	int ok;
	
	int i=0,j=0;
	int modis=0,aster=0,avhrr=0,landsat=0;
	
	void *inrast[MAXFILES];
	unsigned char *outrast;
	int data_format; /* 0=double  1=float  2=32bit signed int  5=8bit unsigned int (ie text) */
	RASTER_MAP_TYPE in_data_type[MAXFILES],out_data_type; /* 0=numbers  1=text */

	char *fileName;
#define fileNameLe 8
#define fileNamePosition 3

	FCELL fe;
	FCELL f[MAXFILES];

	/************************************/

	G_gisinit(argv[0]);

	module = G_define_module();
	module->keywords = _("Albedo,surface reflectance,r.sun");
	module->description =
		_("Broad Band Albedo from Surface Reflectance.\n NOAA AVHRR(n), Modis(m), Landsat(l), Aster(a)\n");

	/* Define the different options */

	input = G_define_standard_option(G_OPT_R_INPUT) ;
	input->multiple   = YES;
	input->description= _("Names of surface reflectance layers");

	output = G_define_standard_option(G_OPT_R_OUTPUT) ;
	output->description= _("Name of the BB_Albedo layer");

	/* Define the different flags */

	flag1 = G_define_flag() ;
	flag1->key         = _('m');
	flag1->description = _("Modis");

	flag2 = G_define_flag() ;
	flag2->key         = _('n');
	flag2->description = _("NOAA AVHRR");

	flag3 = G_define_flag() ;
	flag3->key         = _('l');
	flag3->description = _("Landsat");

	flag4 = G_define_flag() ;
	flag4->key         =_('a');
	flag4->description =_("Aster");

	flag5 = G_define_flag() ;
	flag5->key         =_('q');
	flag5->description =_("Quiet");

// 	printf("Passed Stage 1.\n");

	/* FMEO init nfiles */
	nfiles = 1;
	/********************/
	if (G_parser(argc, argv))
		exit (-1);
	
// 	printf("Passed Stage 2.\n");

	ok = 1;
	names    = input->answers;
	ptr      = input->answers;

	result  = output->answer;
	
// 	printf("Passed Stage 3.\n");

	modis = (flag1->answer);
// 	printf("Passed Stage 3.1\n");
	avhrr = (flag2->answer);
// 	printf("Passed Stage 3.2\n");
	landsat = (flag3->answer);
// 	printf("Passed Stage 3.3\n");
	aster = (flag4->answer);
// 	printf("Passed Stage 3.4\n");
	verbose = (!flag5->answer);

// 	printf("Passed Stage 4.\n");

	for (; *ptr != NULL; ptr++)
	{
// 		printf("In-Loop Stage 1. nfiles = %i\n",nfiles);
		if (nfiles >= MAXFILES)
			G_fatal_error (_("%s - too many ETa files. Only %d allowed"), G_program_name(), MAXFILES);
// 		printf("In-Loop Stage 1..\n");
		name = *ptr;
// 		printf("In-Loop Stage 1...\n");
		/* find map in mapset */
		mapset = G_find_cell2 (name, "");
	        if (mapset == NULL)
		{
			G_fatal_error (_("cell file [%s] not found"), name);
			ok = 0;
		}
// 		printf("In-Loop Stage 1....\n");
		if (G_legal_filename (result) < 0)
		{
			G_fatal_error (_("[%s] is an illegal name"), result);
			ok = 0;
		}
// 		printf("In-Loop Stage 1.....\n");
		if (!ok){
			continue;
		}
// 		printf("In-Loop Stage 1......\n");
		infd[nfiles] = G_open_cell_old (name, mapset);
		if (infd[nfiles] < 0)
		{
			ok = 0;
			continue;
		}
// 		printf("In-Loop Stage 1.......\n");
		/* Allocate input buffer */
		in_data_type[nfiles] = G_raster_map_type(name, mapset);
		//printf("%s: data_type[%i] = %i\n",name,nfiles,in_data_type[nfiles]);
		if( (infd[nfiles] = G_open_cell_old(name,mapset)) < 0){
			G_fatal_error(_("Cannot open cell file [%s]"), name);
		}
		if( (G_get_cellhd(name,mapset,&cellhd)) < 0){
			G_fatal_error(_("Cannot read file header of [%s]"), name);
		}
		inrast[nfiles] = G_allocate_raster_buf(in_data_type[nfiles]);
// 		printf("In-Loop Stage 1........\n");
		nfiles++;
// 		printf("In-Loop Stage 1.........nfiles = %i\n",nfiles);
	}
	nfiles--;
// 	printf("Passed Loop. nfiles = %i\n",nfiles);
	if (nfiles <= 1){
		G_fatal_error(_("The min specified input map is two (that is NOAA AVHRR)"));
	}
// 	printf("Passed Stage 2\n");
	
	/***************************************************/
	/* Allocate output buffer, use input map data_type */
	nrows = G_window_rows();
	ncols = G_window_cols();
// 	printf("Passed Stage 3\n");
	out_data_type=FCELL_TYPE;
	outrast = G_allocate_raster_buf(out_data_type);
// 	printf("Passed Stage 4\n");
	
	/* FMEO *******************************************************/
/*	ew_res = cellhd.ew_res;
	ns_res = cellhd.ns_res;
*/	/**************************************************************/
	/* Create New raster files */
	if ( (outfd = G_open_raster_new (result,1)) < 0){
		G_fatal_error (_("Could not open <%s>"),result);
	}
// 	printf("Passed Stage 5\n");
	/* Process pixels */
	for (row = 0; row < nrows; row++)
	{
		if (verbose){
			G_percent (row, nrows, 2);
		}
		/* read input map */
		for (i=1;i<=nfiles;i++)
		{
			if( (G_get_raster_row(infd[i],inrast[i],row,in_data_type[i])) < 0){
				G_fatal_error (_("Could not read from <%s>"),name);
			}
		}
// 		printf("In-Loop Stage 5..\n");
		/*process the data */
		for (col=0; col < ncols; col++)
		{
// 			printf("In-Loop Stage 6..\n");
			for(i=1;i<=nfiles;i++)
			{
				switch(in_data_type[i])
				{
					case CELL_TYPE:
//						f[i] = (float) ((CELL *) inrast[i])[col];
						printf("CELL: f[%i] = %f\n",i,f[i]);
						break;
					case FCELL_TYPE:
//						f[i] = (float) ((FCELL *) inrast[i])[col];
						printf("FCELL: f[%i] = %f\n",i,f[i]);
						break;
					case DCELL_TYPE:
//						f[i] = (float) ((DCELL *) inrast[i])[col];
						printf("DCELL: f[%i] = %f\n",i,f[i]);
						break;
				}
			}
// 			printf("In-Loop Stage 7..\n");
			if(modis){
				fe = bb_alb_modis(f[1],f[2],f[3],f[4],f[5],f[6],f[7]);
//				printf("fe = %f\n",fe);
			} else if (avhrr){
				fe = bb_alb_noaa(f[1],f[2]);
			} else if (landsat){
				fe = bb_alb_landsat(f[1],f[2],f[3],f[4],f[5],f[6]);
			} else if (aster){
				fe = bb_alb_aster(f[1],f[2],f[3],f[4],f[5],f[6],f[7],f[8],f[9]);
			}
// 			printf("In-Loop Stage 8..\n");
			((FCELL *) outrast)[col] = fe;
// 			printf("In-Loop Stage 9..\n");
		}
		if (G_put_raster_row (outfd, outrast, out_data_type) < 0)
			G_fatal_error (_("Cannot write to <%s>"),result);
	}
// 	printf("In-Loop Stage 10..\n");
	for (i=1;i<=nfiles;i++)
	{
		G_free (inrast[i]);
		G_close_cell (infd[i]);
	}
	G_free (outrast);
	G_close_cell (outfd);
	return 0;
}
