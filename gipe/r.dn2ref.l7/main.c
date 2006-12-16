/****************************************************************************
 *
 * MODULE:       r.dn2ref.l7
 * AUTHOR(S):    Yann Chemin - ychemin@gmail.com
 * PURPOSE:      Calculate TOA Reflectance for Landsat7 from DN.
 *
 * COPYRIGHT:    (C) 2006 by the Asian Institute of Technology, Thailand
 * 		 (C) 2002 by the GRASS Development Team
 *
 *               This program is free software under the GNU Lesser General Public
 *   	    	 License. Read the file COPYING that comes with GRASS for details.
 *
 * CHANGES:	08/11/2006: Added .met input file, that loads all calibration
 * 		parameters, sun elevation and ephemeris
 *  
 *****************************************************************************/


#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <grass/gis.h>
#include <grass/glocale.h>

#define MAXFILES 7

//sun exo-atmospheric irradiance
#define KEXO1 1969.0
#define KEXO2 1840.0
#define KEXO3 1551.0
#define KEXO4 1044.0
#define KEXO5 225.7
#define KEXO7 82.07

#define PI 3.1415926
int l7_in_read(char *met_file, double *lmin,double *lmax,double *qcalmin,double *qcalmax,double *sun_elevation, double *sun_azimuth,int *day, int *month, int *year);
int date2doy(int day, int month, int year);
double dn2rad_landsat7( double Lmin, double LMax, double QCalMax, double QCalmin, int DN );
double rad2ref_landsat7( double radiance, double doy,double sun_elevation, double k_exo );

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
	char *result5;
	
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

	double		kexo[MAXFILES];
	//Metfile
	char		*metfName; //met file, header in text format
	double 		lmin[MAXFILES+2];
	double 		lmax[MAXFILES+2];
	double 		qcalmin[MAXFILES+2];
	double 		qcalmax[MAXFILES+2];
	double 		sun_elevation;
	double 		sun_azimuth;//not useful here, only for parser()
	int 		day,month,year;	
	//EndofMetfile
	int 		doy;
	/************************************/

	G_gisinit(argv[0]);

	module = G_define_module();
	module->keywords = _("DN, radiance, reflectance, import");
	module->description =
		_("Calculates Top of Atmosphere Reflectance from Landsat 7 DN.\n");

	/* Define the different options */
	input = G_define_option() ;
	input->key        = _("metfile");
	input->type       = TYPE_STRING;
	input->required   = YES;
	input->gisprompt  = _(".met file");
	input->description= _("Landsat 7ETM+ Header File (.met)");

	input1 = G_define_option() ;
	input1->key        = _("input");
	input1->type       = TYPE_STRING;
	input1->required   = YES;
	input1->multiple   = YES;
	input1->gisprompt  = _("old,cell,raster");
	input1->description= _("Names of L7 DN layers (1,2,3,4,5,7)");

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
	metfName = input->answer;
	names   = input1->answers;
	ptr     = input1->answers;

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
	
	result0=strcat(result0,".1");
	result1=strcat(result1,".2");
	result2=strcat(result2,".3");
	result3=strcat(result3,".4");
	result4=strcat(result4,".5");
	result5=strcat(result5,".7");

	/********************/
	//Prepare sun exo-atm irradiance
	/********************/
	
	kexo[0]=KEXO1;
	kexo[1]=KEXO2;
	kexo[2]=KEXO3;
	kexo[3]=KEXO4;
	kexo[4]=KEXO5;
	kexo[5]=KEXO7;
	
	//******************************************
	//Fetch parameters for DN2Rad2Ref correction
	l7_in_read(metfName,lmin,lmax,qcalmin,qcalmax,&sun_elevation,&sun_azimuth,&day,&month,&year);
	//printf("%f/%f/%i-%i-%i\n",sun_elevation,sun_azimuth,day,month,year);
	//for(i=0;i<MAXFILES;i++){
	//printf("%i=>%f, %f, %f, %f\n",i,lmin[i],lmax[i],qcalmin[i],qcalmax[i]);
	//}
	doy = date2doy(day,month,year);
	//printf("doy=%i\n",doy);
	/********************/
	//Remap calibration parameters for this program
	//copy layer 8 (band 7) to layer 6
	//because we only use band 1,2,3,4,5,7
	//Change this if you use more bands
	//Remove this if you use all bands
	/********************/
	lmin[5]=lmin[7];
	lmax[5]=lmax[7];
	qcalmin[5]=qcalmin[7];
	qcalmax[5]=qcalmax[7];
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
				dout[i]=dn2rad_landsat7(lmin[i],lmax[i],qcalmax[i],qcalmin[i],d[i]);
			} else {
				dout[i]=dn2rad_landsat7(lmin[i],lmax[i],qcalmax[i],qcalmin[i],d[i]);
				dout[i]=rad2ref_landsat7(dout[i],doy,sun_elevation,kexo[i]);
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
