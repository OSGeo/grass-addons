/****************************************************************************
 *
 * MODULE:       i.lmf
 * AUTHOR(S):    Yann Chemin - yann.chemin@gmail.com
 * PURPOSE:      Clean temporal signature using what is called
 * 		 Local Maximum Fitting (LMF)
 * 		 Initially created for Vegetation Indices from AVHRR.
 *
 *               Translated from Fortran, unconfused, removed unused and
 *               other redundant variables. Removed BSQ Binary loading.
 *
 * 		 SHORT HISTORY OF THE CODE
 * 		 -------------------------
 *               Original Fortran Beta-level code was written 
 *               by Yoshito Sawada (2000), in OpenMP Fortran 
 *               for SGI Workstation. Recovered broken code from 
 *               their website in 2003, regenerated missing code and 
 *               made it work in Linux.
 *               ORIGINAL WEBSITE
 *               ----------------
 *               http://www.affrc.go.jp/ANDES/sawady/index.html
 *               ENGLISH WEBSITE
 *               ---------------
 *               http://www.rsgis.ait.ac.th/~honda/lmf/lmf.html
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

#define MAXFILES 366

int lmf(int nbands, int npoint, double *inpix, double *outpix);

int
main(int argc, char *argv[])
{
	struct 	Cell_head cellhd;/*region+header info*/
	char 	*mapset; /*mapset name*/
	int 	nrows, ncols;
	int 	row,col;

	struct 	GModule *module;
	struct 	Option *input,*ndate,*output;
	
	struct 	History history; /*metadata*/
	/************************************/
	/* FMEO Declarations*****************/
	char 	*name; /*input raster name*/
	char 	*result[MAXFILES]; /*output raster name*/
	/*File Descriptors*/
	int 	nfiles;
	int 	infd[MAXFILES];
	int 	outfd[MAXFILES];

	char 	**names;
	char 	**ptr;
	
	int 	ok;
	
	int 	i=0,j=0;
	
	void 	*inrast[MAXFILES];
	DCELL 	*outrast[MAXFILES];
	int 	data_format; /* 0=double  1=float  2=32bit signed int  5=8bit unsigned int (ie text) */
	RASTER_MAP_TYPE in_data_type[MAXFILES]; /* 0=numbers  1=text */
	RASTER_MAP_TYPE out_data_type = DCELL_TYPE;

	int	ndates;
	double	inpix[MAXFILES]={0.0};
	double	outpix[MAXFILES]={0.0};
	/************************************/

	G_gisinit(argv[0]);

	module = G_define_module();
	module->keywords = _("LMF,Vegetation Indices,Atmospheric temporal correction");
	module->description =
		_("Temporal Local Maximum Fitting of vegetation indices, works also for surface reflectance data. Number of bands is potentially several years, nfiles and ndates are respectively the number of pixels and the number of pixels in a year\n");

	/* Define the different options */

	input 		  = G_define_standard_option(G_OPT_R_INPUTS) ;
	input->description= _("Names of input layers");

	ndate 		  = G_define_option();
	ndate->key	  = _("ndate");
	ndate->type       = TYPE_INTEGER;
	ndate->required   = YES;
	ndate->gisprompt  =_("parameter, integer");
	ndate->description= _("Number of map layers per year");

	output 		   = G_define_standard_option(G_OPT_R_OUTPUT) ;
	output->description= _("Name of the output layer");

	/* FMEO init nfiles */
	nfiles = 1;
	/********************/
	if (G_parser(argc, argv))
		exit (-1);
	
	ok = 1;
	names	= input->answers;
	ptr	= input->answers;

	ndates  = atoi(ndate->answer);

	for (; *ptr != NULL; ptr++)
	{
		if (nfiles >= MAXFILES)
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
	if (nfiles <= 10){
		G_fatal_error(_("The min specified input map is ten"));
	}
	
	/***************************************************/
	/* Allocate output buffer, use input map data_type */
	nrows = G_window_rows();
	ncols = G_window_cols();
	for(i=0;i<nfiles;i++){
		sprintf(result[i],output->answer,".",i+1);
		if (G_legal_filename (result[i]) < 0)
		{
			G_fatal_error (_("[%s] is an illegal name"), result[i]);
			ok = 0;
		}
		outrast[i] = G_allocate_raster_buf(out_data_type);
		/* Create New raster files */
		if ( (outfd[i] = G_open_raster_new (result[i],1)) < 0){
			G_fatal_error (_("Could not open <%s>"),result[i]);
		}
	}
	/*******************/
	/* Process pixels */
	for (row = 0; row < nrows; row++)
	{
		DCELL de;
		DCELL d[MAXFILES];
		G_percent (row, nrows, 2);
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
						inpix[i-1] = (double) ((CELL *) inrast[i])[col];
						break;
					case FCELL_TYPE:
						inpix[i-1] = (double) ((FCELL *) inrast[i])[col];
						break;
					case DCELL_TYPE:
						inpix[i-1] = (double) ((DCELL *) inrast[i])[col];
						break;
				}
			}
			lmf(nfiles, ndates, inpix, outpix);
			/* Put the resulting temporal curve 
			 * in the output layers */
			for(i=0;i<nfiles;i++){
				outrast[i][col] = outpix[i];
			}
		}
		for(i=0;i<nfiles;i++){
			if (G_put_raster_row (outfd[i], outrast[i], out_data_type) < 0)
				G_fatal_error (_("Cannot write to <%s>"),result[i]);
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
