/****************************************************************************
 *
 * MODULE:       r.dn2full.l7
 * AUTHOR(S):    Yann Chemin - ychemin@gmail.com
 * PURPOSE:      Calculate TOA Reflectance&Temperature for Landsat7 from DN.
 *
 * COPYRIGHT:    (C) 2002 by the GRASS Development Team
 *
 *               This program is free software under the GNU Lesser General Public
 *   	    	 License. Read the file COPYING that comes with GRASS for details.
 *
 * THANKS:	 Brad Douglas helped fixing the filename fetching
 *  
 *****************************************************************************/


#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <grass/gis.h>
#include <grass/glocale.h>

#define MAXFILES 9

//sun exo-atmospheric irradiance
#define KEXO1 1969.0
#define KEXO2 1840.0
#define KEXO3 1551.0
#define KEXO4 1044.0
#define KEXO5 225.7
#define KEXO7 82.07
#define KEXO8 1385.64 //to find the real value in the internet

#define PI 3.1415926


int l7_in_read(char *metfName, char *b1, char *b2, char *b3, char *b4, char *b5, char *b61, char *b62, char *b7, char *b8, double *lmin,double *lmax,double *qcalmin,double *qcalmax,double *sun_elevation, double *sun_azimuth,int *day, int *month, int *year);
int date2doy(int day, int month, int year);
double dn2rad_landsat7( double Lmin, double LMax, double QCalMax, double QCalmin, int DN );
double rad2ref_landsat7( double radiance, double doy,double sun_elevation, double k_exo );
double tempk_landsat7( double l6 );

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
	
	struct Flag *flag1;
	struct History history; //metadata

	/************************************/
	/* FMEO Declarations*****************/
	char history_buf[200];
	char *name; //input raster name
	char *result; //output raster name
	//Prepare new names for output files
	char result1[80], result2[80], result3[80], result4[80];
	char result5[80], result61[80], result62[80], result7[80],result8[80] ;
	
	//File Descriptors
	int infd[MAXFILES];
	int outfd[MAXFILES];

	char **names;
	char **ptr;
	
	int i=0,j=0;
	
	void *inrast[MAXFILES];
	unsigned char *outrast[MAXFILES];
	RASTER_MAP_TYPE in_data_type[MAXFILES];
	RASTER_MAP_TYPE out_data_type = DCELL_TYPE; /* 0=numbers  1=text */

	double		kexo[MAXFILES];
	//Metfile
	char		*metfName; //met file, header in text format
	char		b1[80],b2[80],b3[80];
	char		b4[80],b5[80],b61[80];
	char		b62[80],b7[80],b8[80];//Load .tif names
	double 		lmin[MAXFILES];
	double 		lmax[MAXFILES];
	double 		qcalmin[MAXFILES];
	double 		qcalmax[MAXFILES];
	double 		sun_elevation;
	double 		sun_azimuth;//not useful here, only for parser()
	int 		day,month,year;	
	//EndofMetfile
	int 		doy;
	/************************************/

	G_gisinit(argv[0]);

	module = G_define_module();
	module->keywords = _("DN, reflectance, temperature, import");
	module->description =
		_("Calculates Top of Atmosphere Reflectance/Temperature from Landsat 7 DN.\n");

	/* Define the different options */
	input = G_define_option() ;
	input->key        = _("metfile");
	input->type       = TYPE_STRING;
	input->required   = YES;
	input->gisprompt  = _("old_file,file,file");
	input->description= _("Landsat 7ETM+ Header File (.met)");

	output = G_define_option() ;
	output->key        = _("output");
	output->type       = TYPE_STRING;
	output->required   = YES;
	output->gisprompt  = _("new,cell,raster");
	output->description= _("Base name of the output layers (will add .x)");

	/* Define the different flags */

	flag1 = G_define_flag() ;
	flag1->key         =_('q');
	flag1->description =_("Quiet");

	/********************/
	if (G_parser(argc, argv))
		exit (-1);
	
	metfName	= input->answer;
	result		= output->answer;

	verbose = (!flag1->answer);
	//******************************************
	//Fetch parameters for DN2Rad2Ref correction
	l7_in_read(metfName,b1,b2,b3,b4,b5,b61,b62,b7,b8,lmin,lmax,qcalmin,qcalmax,&sun_elevation,&sun_azimuth,&day,&month,&year);
//	printf("%f/%f/%i-%i-%i\n",sun_elevation,sun_azimuth,day,month,year);
//	for(i=0;i<MAXFILES;i++){
//		printf("%i=>%f, %f, %f, %f\n",i,lmin[i],lmax[i],qcalmin[i],qcalmax[i]);
//	}
//	doy = date2doy(day,month,year);
//	printf("doy=%i\n",doy);
	/********************/
//	printf("b1=%s\n",b1);
//	printf("b2=%s\n",b2);
//	printf("b3=%s\n",b3);
//	printf("b4=%s\n",b4);
//	printf("b5=%s\n",b5);
//	printf("b61=%s\n",b61);
//	printf("b62=%s\n",b62);
//	printf("b7=%s\n",b7);
//	printf("b8=%s\n",b8);
//	exit(1);
	/********************/
	//Prepare the ouput file names 
	/********************/

//	printf("result=%s\n",result);
	snprintf(result1, 80, "%s%s",result,".1");
//	printf("%s\n",result1);
	snprintf(result2, 80, "%s%s",result,".2");
//	printf("%s\n",result2);
	snprintf(result3, 80, "%s%s",result,".3");
//	printf("%s\n",result3);
	snprintf(result4, 80, "%s%s",result,".4");
//	printf("%s\n",result4);
	snprintf(result5, 80, "%s%s",result,".5");
//	printf("%s\n",result5);
	snprintf(result61, 80, "%s%s",result,".61");
//	printf("%s\n",result61);
	snprintf(result62, 80, "%s%s",result,".62");
//	printf("%s\n",result62);
	snprintf(result7, 80, "%s%s",result,".7");
//	printf("%s\n",result7);
	snprintf(result8, 80, "%s%s",result,".8");
//	printf("%s\n",result8);

	/********************/
	//Prepare sun exo-atm irradiance
	/********************/
	
	kexo[0]=KEXO1;
	kexo[1]=KEXO2;
	kexo[2]=KEXO3;
	kexo[3]=KEXO4;
	kexo[4]=KEXO5;
	kexo[5]=0.0;//filling
	kexo[6]=0.0;//filling
	kexo[7]=KEXO7;
	kexo[8]=KEXO8;
	
	//******************************************
	/***************************************************/
	//Band1
	/* find map in mapset */
	mapset = G_find_cell2 (b1, "");
        if (mapset == NULL){
		G_fatal_error (_("cell file [%s] not found"), b1);
	}
	if (G_legal_filename (b1) < 0){
		G_fatal_error (_("[%s] is an illegal name"), b1);
	}
	infd[0] = G_open_cell_old (b1, mapset);
	/* Allocate input buffer */
	in_data_type[0] = G_raster_map_type(b1, mapset);
	if( (infd[0] = G_open_cell_old(b1,mapset)) < 0){
		G_fatal_error(_("Cannot open cell file [%s]"), b1);
	}
	if( (G_get_cellhd(b1,mapset,&cellhd)) < 0){
		G_fatal_error(_("Cannot read file header of [%s]"), b1);
	}
	inrast[0] = G_allocate_raster_buf(in_data_type[0]);
	/***************************************************/
	/***************************************************/
	//Band2
	/* find map in mapset */
	mapset = G_find_cell2 (b2, "");
        if (mapset == NULL){
		G_fatal_error (_("cell file [%s] not found"), b2);
	}
	if (G_legal_filename (b2) < 0){
		G_fatal_error (_("[%s] is an illegal name"), b2);
	}
	infd[1] = G_open_cell_old (b2, mapset);
	/* Allocate input buffer */
	in_data_type[1] = G_raster_map_type(b2, mapset);
	if( (infd[1] = G_open_cell_old(b2,mapset)) < 0){
		G_fatal_error(_("Cannot open cell file [%s]"), b2);
	}
	if( (G_get_cellhd(b2,mapset,&cellhd)) < 0){
		G_fatal_error(_("Cannot read file header of [%s]"), b2);
	}
	inrast[1] = G_allocate_raster_buf(in_data_type[1]);
	/***************************************************/
	/***************************************************/
	//Band3
	/* find map in mapset */
	mapset = G_find_cell2 (b3, "");
        if (mapset == NULL){
		G_fatal_error (_("cell file [%s] not found"), b3);
	}
	if (G_legal_filename (b3) < 0){
		G_fatal_error (_("[%s] is an illegal name"), b3);
	}
	infd[2] = G_open_cell_old (b3, mapset);
	/* Allocate input buffer */
	in_data_type[2] = G_raster_map_type(b3, mapset);
	if( (infd[2] = G_open_cell_old(b3,mapset)) < 0){
		G_fatal_error(_("Cannot open cell file [%s]"), b3);
	}
	if( (G_get_cellhd(b3,mapset,&cellhd)) < 0){
		G_fatal_error(_("Cannot read file header of [%s]"), b3);
	}
	inrast[2] = G_allocate_raster_buf(in_data_type[2]);
	/***************************************************/
	/***************************************************/
	//Band4
	/* find map in mapset */
	mapset = G_find_cell2 (b4, "");
        if (mapset == NULL){
		G_fatal_error (_("cell file [%s] not found"), b4);
	}
	if (G_legal_filename (b4) < 0){
		G_fatal_error (_("[%s] is an illegal name"), b4);
	}
	infd[3] = G_open_cell_old (b4, mapset);
	/* Allocate input buffer */
	in_data_type[3] = G_raster_map_type(b4, mapset);
	if( (infd[3] = G_open_cell_old(b4,mapset)) < 0){
		G_fatal_error(_("Cannot open cell file [%s]"), b4);
	}
	if( (G_get_cellhd(b4,mapset,&cellhd)) < 0){
		G_fatal_error(_("Cannot read file header of [%s]"), b4);
	}
	inrast[3] = G_allocate_raster_buf(in_data_type[3]);
	/***************************************************/
	/***************************************************/
	//Band5
	/* find map in mapset */
	mapset = G_find_cell2 (b5, "");
        if (mapset == NULL){
		G_fatal_error (_("cell file [%s] not found"), b5);
	}
	if (G_legal_filename (b5) < 0){
		G_fatal_error (_("[%s] is an illegal name"), b5);
	}
	infd[4] = G_open_cell_old (b5, mapset);
	/* Allocate input buffer */
	in_data_type[4] = G_raster_map_type(b5, mapset);
	if( (infd[4] = G_open_cell_old(b5,mapset)) < 0){
		G_fatal_error(_("Cannot open cell file [%s]"), b5);
	}
	if( (G_get_cellhd(b5,mapset,&cellhd)) < 0){
		G_fatal_error(_("Cannot read file header of [%s]"), b5);
	}
	inrast[4] = G_allocate_raster_buf(in_data_type[4]);
	/***************************************************/
	/***************************************************/
	//Band61
	/* find map in mapset */
	mapset = G_find_cell2 (b61, "");
        if (mapset == NULL){
		G_fatal_error (_("cell file [%s] not found"), b61);
	}
	if (G_legal_filename (b61) < 0){
		G_fatal_error (_("[%s] is an illegal name"), b61);
	}
	infd[5] = G_open_cell_old (b61, mapset);
	/* Allocate input buffer */
	in_data_type[5] = G_raster_map_type(b61, mapset);
	if( (infd[5] = G_open_cell_old(b61,mapset)) < 0){
		G_fatal_error(_("Cannot open cell file [%s]"), b61);
	}
	if( (G_get_cellhd(b61,mapset,&cellhd)) < 0){
		G_fatal_error(_("Cannot read file header of [%s]"), b61);
	}
	inrast[5] = G_allocate_raster_buf(in_data_type[5]);
	/***************************************************/
	/***************************************************/
	//Band62
	/* find map in mapset */
	mapset = G_find_cell2 (b62, "");
        if (mapset == NULL){
		G_fatal_error (_("cell file [%s] not found"), b62);
	}
	if (G_legal_filename (b62) < 0){
		G_fatal_error (_("[%s] is an illegal name"), b62);
	}
	infd[6] = G_open_cell_old (b62, mapset);
	/* Allocate input buffer */
	in_data_type[6] = G_raster_map_type(b62, mapset);
	if( (infd[6] = G_open_cell_old(b62,mapset)) < 0){
		G_fatal_error(_("Cannot open cell file [%s]"), b62);
	}
	if( (G_get_cellhd(b62,mapset,&cellhd)) < 0){
		G_fatal_error(_("Cannot read file header of [%s]"), b62);
	}
	inrast[6] = G_allocate_raster_buf(in_data_type[6]);
	/***************************************************/
	/***************************************************/
	//Band7
	/* find map in mapset */
	mapset = G_find_cell2 (b7, "");
        if (mapset == NULL){
		G_fatal_error (_("cell file [%s] not found"), b7);
	}
	if (G_legal_filename (b7) < 0){
		G_fatal_error (_("[%s] is an illegal name"), b7);
	}
	infd[7] = G_open_cell_old (b7, mapset);
	/* Allocate input buffer */
	in_data_type[7] = G_raster_map_type(b7, mapset);
	if( (infd[7] = G_open_cell_old(b7,mapset)) < 0){
		G_fatal_error(_("Cannot open cell file [%s]"), b7);
	}
	if( (G_get_cellhd(b7,mapset,&cellhd)) < 0){
		G_fatal_error(_("Cannot read file header of [%s]"), b7);
	}
	inrast[7] = G_allocate_raster_buf(in_data_type[7]);
	/***************************************************/
	/***************************************************/
	//Band8
	/* find map in mapset */
	mapset = G_find_cell2 (b8, "");
        if (mapset == NULL){
		G_fatal_error (_("cell file [%s] not found"), b8);
	}
	if (G_legal_filename (b8) < 0){
		G_fatal_error (_("[%s] is an illegal name"), b8);
	}
	infd[8] = G_open_cell_old (b8, mapset);
	/* Allocate input buffer */
	in_data_type[8] = G_raster_map_type(b8, mapset);
	if( (infd[8] = G_open_cell_old(b8,mapset)) < 0){
		G_fatal_error(_("Cannot open cell file [%s]"), b8);
	}
	if( (G_get_cellhd(b8,mapset,&cellhd)) < 0){
		G_fatal_error(_("Cannot read file header of [%s]"), b8);
	}
	inrast[8] = G_allocate_raster_buf(in_data_type[8]);
	/***************************************************/
	/***************************************************/
	/* Allocate output buffer, use input map data_type */
	nrows = G_window_rows();
	ncols = G_window_cols();
	out_data_type=DCELL_TYPE;
	for(i=0;i<MAXFILES;i++){
		outrast[i] = G_allocate_raster_buf(out_data_type);
	}
	if ( (outfd[0] = G_open_raster_new (result1,1)) < 0)
		G_fatal_error (_("Could not open <%s>"),result1);
	if ( (outfd[1] = G_open_raster_new (result2,1)) < 0)
		G_fatal_error (_("Could not open <%s>"),result2);
	if ( (outfd[2] = G_open_raster_new (result3,1)) < 0)
		G_fatal_error (_("Could not open <%s>"),result3);
	if ( (outfd[3] = G_open_raster_new (result4,1)) < 0)
		G_fatal_error (_("Could not open <%s>"),result4);
	if ( (outfd[4] = G_open_raster_new (result5,1)) < 0)
		G_fatal_error (_("Could not open <%s>"),result5);
	if ( (outfd[5] = G_open_raster_new (result61,1)) < 0)
		G_fatal_error (_("Could not open <%s>"),result61);
	if ( (outfd[6] = G_open_raster_new (result62,1)) < 0)
		G_fatal_error (_("Could not open <%s>"),result62);
	if ( (outfd[7] = G_open_raster_new (result7,1)) < 0)
		G_fatal_error (_("Could not open <%s>"),result7);
	if ( (outfd[8] = G_open_raster_new (result8,1)) < 0)
		G_fatal_error (_("Could not open <%s>"),result8);
	/* Process pixels */
	DCELL dout[MAXFILES];
	DCELL d[MAXFILES];
	for (row = 0; row < nrows; row++)
	{
		if (verbose){
			G_percent (row, nrows, 2);
		}
		/* read input map */
		for (i=0;i<MAXFILES;i++)
		{
			if((G_get_raster_row(infd[i],inrast[i],row,in_data_type[i])) < 0){
				G_fatal_error (_("Could not read from <%s>"),i);
			}
		}
		/*process the data */
		for (col=0; col < ncols; col++)
		{
			for(i=0;i<MAXFILES;i++)
			{
				d[i] = (double) ((CELL *) inrast[i])[col];
				dout[i]=dn2rad_landsat7(lmin[i],lmax[i],qcalmax[i],qcalmin[i],d[i]);
				if(i==5||i==6){//if band 61/62, process brightness temperature
					if(dout[i]<=0.0){
						dout[i]=-999.99;
					}else{
						dout[i]=tempk_landsat7(dout[i]);
					}
				}else{//process reflectance
					dout[i]=rad2ref_landsat7(dout[i],doy,sun_elevation,kexo[i]);
			}
			((DCELL *) outrast[i])[col] = dout[i];
 			}
		}
		for(i=0;i<MAXFILES;i++){
			if (G_put_raster_row (outfd[i], outrast[i], out_data_type) < 0)
				G_fatal_error (_("Cannot write to <%s.%i>"),result,i+1);
		}
	}
	for (i=0;i<MAXFILES;i++)
	{
		G_free (inrast[i]);
		G_close_cell (infd[i]);
		G_free (outrast[i]);
		G_close_cell (outfd[i]);
	}

	printf("Make Metadata\n");
//	G_short_history(result, "raster", &history);
//	G_command_history(&history);
//	G_write_history(result,&history);

//	//fill in data source line
//		printf("1\t");
//	strncpy(history.datsrc_1,metfName,RECORD_LEN);
//	sprintf(history_buf,"year=%d",year);
//		printf("1\t");
//	strncpy(history.datsrc_1,history_buf,RECORD_LEN);
//	sprintf(history_buf,"month=%d",month);
//		printf("1\t");
//	strncpy(history.datsrc_1,history_buf,RECORD_LEN);
//	sprintf(history_buf,"day=%d",day);
//		printf("1\t");
//	strncpy(history.datsrc_1,history_buf,RECORD_LEN);
//	sprintf(history_buf,"doy=%d",doy);
//		printf("1\t");
//	strncpy(history.datsrc_1,history_buf,RECORD_LEN);
//	sprintf(history_buf,"sun_elevation=%f",sun_elevation);
//		printf("1\t");
//	strncpy(history.datsrc_1,history_buf,RECORD_LEN);
//	sprintf(history_buf,"sun_azimuth=%f",sun_azimuth);
//		printf("1\t");
//	strncpy(history.datsrc_1,history_buf,RECORD_LEN);
//		printf("1\t");
//	history.datsrc_1[RECORD_LEN-1]='\0';//strncpy() doesn't null terminate if maxfill
//		printf("1\t");
//	G_write_history(result,&history);

	return 0;
}
