/****************************************************************************
 *
 * MODULE:       r.dn2ref.ast
 * AUTHOR(S):    Yann Chemin - ychemin@gmail.com
 * PURPOSE:      Calculate TOA Reflectance for Aster from DN.
 * 		 Input 9 bands (VNIR and SWIR).
 *
 * COPYRIGHT:    (C) 2006 by the Asian Institute of Technology, Thailand
 * 		 (C) 2002 by the GRASS Development Team
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

#define MAXFILES 9

// DN to radiance conversion factors 
#define L1GAIN 0.676
#define L1OFFS -0.676
#define L2GAIN 0.862
#define L2OFFS -0.862
#define L3GAIN 0.217
#define L3OFFS -0.217
#define L4GAIN 0.0696
#define L4OFFS -0.0696
#define L5GAIN 0.0696
#define L5OFFS -0.0696
#define L6GAIN 0.0696
#define L6OFFS -0.0696
#define L7GAIN 0.0696
#define L7OFFS -0.0696
#define L8GAIN 0.0696
#define L8OFFS -0.0696
#define L9GAIN 0.0318
#define L9OFFS -0.0318

//sun exo-atmospheric irradiance
#define KEXO1 1828.0
#define KEXO2 1559.0
#define KEXO3 1045.0
#define KEXO4 226.73
#define KEXO5 86.50
#define KEXO6 81.99
#define KEXO7 74.72
#define KEXO8 66.41
#define KEXO9 59.83

#define PI 3.1415926

double rad2ref_aster( double radiance, double doy,double sun_elevation, double k_exo );

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
	struct Option *input1,*input2;
	
	struct Flag *flag1, *flag2;
	struct History history; //metadata

	/************************************/
	/* FMEO Declarations*****************/
	char *name; //input raster name
	char *result; //output raster name
	
	//Prepare new names for output files
	char *result0, *result1, *result2, *result3, *result4;
	char *result5, *result6, *result7, *result8;
	
	//File Descriptors
	int nfiles;
	int infd[MAXFILES];
	int outfd[MAXFILES];

	char **names;
	char **ptr;
	
	int ok;
	
	int i=0,j=0;
	int radiance=0;
	
	void *inrast[MAXFILES];
	unsigned char *outrast[MAXFILES];
	int data_format; /* 0=double  1=float  2=32bit signed int  5=8bit unsigned int (ie text) */
	RASTER_MAP_TYPE in_data_type[MAXFILES];
	RASTER_MAP_TYPE out_data_type = DCELL_TYPE; /* 0=numbers  1=text */

	char *fileName;
#define fileNameLe 8
#define fileNamePosition 3

	double gain[MAXFILES], offset[MAXFILES];
	double kexo[MAXFILES];
	double doy,sun_elevation;
	/************************************/

	G_gisinit(argv[0]);

	module = G_define_module();
	module->keywords = _("DN, radiance, reflectance, import");
	module->description =
		_("Calculates Top of Atmosphere Reflectance from ASTER DN.\n");

	/* Define the different options */

	input = G_define_option() ;
	input->key        = _("input");
	input->type       = TYPE_STRING;
	input->required   = YES;
	input->multiple   = YES;
	input->gisprompt  = _("old,cell,raster");
	input->description= _("Names of ASTER DN layers (9 layers)");

	input1 = G_define_option() ;
	input1->key        = _("doy");
	input1->type       = TYPE_DOUBLE;
	input1->required   = YES;
	input1->gisprompt  = _("value, parameter");
	input1->description= _("Day of Year of satellite overpass [0-366]");
	
	input2 = G_define_option() ;
	input2->key        = _("sun_elevation");
	input2->type       = TYPE_DOUBLE;
	input2->required   = YES;
	input2->gisprompt  = _("value, parameter");
	input2->description= _("Sun elevation angle (degrees, < 90.0)");
	
	output = G_define_option() ;
	output->key        = _("output");
	output->type       = TYPE_STRING;
	output->required   = YES;
	output->gisprompt  = _("new,cell,raster");
	output->description= _("Base name of the output layers (will add .x)");

	/* Define the different flags */

	flag1 = G_define_flag() ;
	flag1->key         = _('r');
	flag1->description = _("output is radiance (W/m2)");

	flag2 = G_define_flag() ;
	flag2->key         =_('q');
	flag2->description =_("Quiet");

// 	printf("Passed Stage 1.\n");

	/* FMEO init nfiles */
	nfiles = 1;
	/********************/
	if (G_parser(argc, argv))
		exit (-1);
	
	ok = 1;
	names   = input->answers;
	ptr     = input->answers;

	doy	= atof(input1->answer);
	sun_elevation = atof(input2->answer);

	result  = output->answer;
	
	radiance = (flag1->answer);
	verbose = (!flag2->answer);


	/********************/
	//Prepare the ouput file names 
	/********************/

	result0=result;
	result1=result;
	result2=result;
	result3=result;
	result4=result;
	result5=result;
	result6=result;
	result7=result;
	result8=result;
	
	result0=strcat(result0,".1");
	result1=strcat(result1,".2");
	result2=strcat(result2,".3");
	result3=strcat(result3,".4");
	result4=strcat(result4,".5");
	result5=strcat(result5,".6");
	result6=strcat(result6,".7");
	result7=strcat(result7,".8");
	result8=strcat(result8,".9");

	/********************/
	//Prepare radiance boundaries
	/********************/
	
	gain[0]=L1GAIN;
	gain[1]=L2GAIN;
	gain[2]=L3GAIN;
	gain[3]=L4GAIN;
	gain[4]=L5GAIN;
	gain[5]=L6GAIN;
	gain[6]=L7GAIN;
	gain[7]=L8GAIN;
	gain[8]=L9GAIN;

	offset[0]=L1OFFS;
	offset[1]=L2OFFS;
	offset[2]=L3OFFS;
	offset[3]=L4OFFS;
	offset[4]=L5OFFS;
	offset[5]=L6OFFS;
	offset[6]=L7OFFS;
	offset[7]=L8OFFS;
	offset[8]=L9OFFS;
	
	/********************/
	//Prepare sun exo-atm irradiance
	/********************/
	
	kexo[0]=KEXO1;
	kexo[1]=KEXO2;
	kexo[2]=KEXO3;
	kexo[3]=KEXO4;
	kexo[4]=KEXO5;
	kexo[5]=KEXO6;
	kexo[6]=KEXO7;
	kexo[7]=KEXO8;
	kexo[8]=KEXO9;
	
	/********************/
	/********************/
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
		G_fatal_error(_("The input band number should be 6"));
	}
// 	printf("Passed Stage 2\n");
	
	/***************************************************/
	/* Allocate output buffer, use input map data_type */
	nrows = G_window_rows();
	ncols = G_window_cols();
// 	printf("Passed Stage 3\n");
	out_data_type=DCELL_TYPE;
	for(i=0;i<nfiles;i++){
		outrast[i] = G_allocate_raster_buf(out_data_type);
	}
	if ( (outfd[0] = G_open_raster_new (result0,1)) < 0)
		G_fatal_error (_("Could not open <%s>"),result0);
	if ( (outfd[1] = G_open_raster_new (result1,1)) < 0)
		G_fatal_error (_("Could not open <%s>"),result1);
	if ( (outfd[2] = G_open_raster_new (result2,1)) < 0)
		G_fatal_error (_("Could not open <%s>"),result2);
	if ( (outfd[3] = G_open_raster_new (result3,1)) < 0)
		G_fatal_error (_("Could not open <%s>"),result3);
	if ( (outfd[4] = G_open_raster_new (result4,1)) < 0)
		G_fatal_error (_("Could not open <%s>"),result4);
	if ( (outfd[5] = G_open_raster_new (result5,1)) < 0)
		G_fatal_error (_("Could not open <%s>"),result5);
	if ( (outfd[6] = G_open_raster_new (result6,1)) < 0)
		G_fatal_error (_("Could not open <%s>"),result6);
	if ( (outfd[7] = G_open_raster_new (result7,1)) < 0)
		G_fatal_error (_("Could not open <%s>"),result7);
	if ( (outfd[8] = G_open_raster_new (result8,1)) < 0)
		G_fatal_error (_("Could not open <%s>"),result8);
// 	printf("Passed Stage 5\n");
	/* Process pixels */

	DCELL dout[MAXFILES];
	DCELL d[MAXFILES];
	
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
			
			if(radiance){
				dout[i] = gain[i]*d[i]+offset[i];
			} else {
				dout[i] = gain[i]*d[i]+offset[i];
				dout[i]	= rad2ref_aster(dout[i],doy,sun_elevation,kexo[i]);
			}
			((DCELL *) outrast[i])[col] = dout[i];
 			}
		}
		for(i=0;i<nfiles;i++){
			if (G_put_raster_row (outfd[i], outrast[i], out_data_type) < 0)
				G_fatal_error (_("Cannot write to <%s.%i>"),result,i+1);
		}
	}
	for (i=1;i<=nfiles;i++)
	{
		G_free (inrast[i]);
		G_close_cell (infd[i]);
		G_free (outrast[i]);
		G_close_cell (outfd[i]);
	}
	return 0;
}
