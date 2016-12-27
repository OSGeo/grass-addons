/****************************************************************************
 *
 * MODULE:       i.superpixels.slic
 * PURPOSE:      Preform superpixel segmenation
 *****************************************************************************/

/*
 * This code performs superpixel segmentation as explained in the paper:
 * "SLIC Superpixels", Radhakrishna Achanta, Appu Shaji, 
 * Kevin Smith, Aurelien Lucchi, Pascal Fua, and Sabine Susstrunk.
 * EPFL Technical Report no. 149300, June 2010. 
 *
 *
 * Below code is ported to grass from original C++ SLIC implmenetation 
 * available at:  http://ivrl.epfl.ch/research/superpixels
 *
 */

#include <grass/config.h>

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <grass/gis.h>
#include <grass/raster.h>
#include <grass/glocale.h>
#include <math.h>
#include <limits.h>
#include <float.h>

#ifndef MAX
#define MAX(x,y) ((x) > (y) ? (x) : (y))
#endif
#ifndef MIN
#define MIN(x,y) ((x) < (y) ? (x) : (y))
#endif


void SLIC_EnforceLabelConnectivity(
	int*				labels,
	int					width,
	int					height,
	int*	     		nlabels,//new labels
	int	     			numlabels,
	int					K) 
{
//	const int dx8[8] = {-1, -1,  0,  1, 1, 1, 0, -1};
//	const int dy8[8] = { 0, -1, -1, -1, 0, 1, 1,  1};

	const int dx4[4] = {-1,  0,  1,  0};
	const int dy4[4] = { 0, -1,  0,  1};

	const int sz = width*height;
	const int SUPSZ = sz/K;
	//nlabels.resize(sz, -1);
	int i;
	for( i = 0; i < sz; i++ ) nlabels[i] = -1;
	int label = 0; //(0);
	
	int* xvec;
	xvec = G_malloc (sizeof (int) * sz);
	memset (xvec, 0, sizeof (int) * sz);

	int* yvec;
	yvec = G_malloc (sizeof (int) * sz);
	memset (yvec, 0, sizeof (int) * sz);
	
	
	int oindex=0;
	int adjlabel=0; ;//adjacent label

	int j, k;
	for( j = 0; j < height; j++ )
	{
		for( k = 0; k < width; k++ )
		{
			if( 0 > nlabels[oindex] )
			{
				nlabels[oindex] = label;
				//--------------------
				// Start a new segment
				//--------------------
				xvec[0] = k;
				yvec[0] = j;
				//-------------------------------------------------------
				// Quickly find an adjacent label for use later if needed
				//-------------------------------------------------------
				
				{int n; for( n = 0; n < 4; n++ )
				{
					int x = xvec[0] + dx4[n];
					int y = yvec[0] + dy4[n];
					if( (x >= 0 && x < width) && (y >= 0 && y < height) )
					{
						int nindex = y*width + x;
						if(nlabels[nindex] >= 0) adjlabel = nlabels[nindex];
					}
				}}

				int count = 1;
				int c; for( c = 0; c < count; c++ )
				{
					int n; for( n = 0; n < 4; n++ )
					{
						int x = xvec[c] + dx4[n];
						int y = yvec[c] + dy4[n];

						if( (x >= 0 && x < width) && (y >= 0 && y < height) )
						{
							int nindex = y*width + x;

							if( 0 > nlabels[nindex] && labels[oindex] == labels[nindex] )
							{
								xvec[count] = x;
								yvec[count] = y;
								nlabels[nindex] = label;
								count++;
							}
						}

					}
				}
				//-------------------------------------------------------
				// If segment size is less then a limit, assign an
				// adjacent label found before, and decrement label count.
				//-------------------------------------------------------
				if(count <= SUPSZ >> 2)
				{ int c;
					for( c = 0; c < count; c++ )
					{
						int ind = yvec[c]*width+xvec[c];
						nlabels[ind] = adjlabel;
					}
					label--;
				}
				label++;
			}
			oindex++;
		}
	}
	numlabels = label;

	if(xvec) G_free(xvec);
	if(yvec) G_free(yvec);
	
}



/*
 * main function
 * it copies raster input raster map, calling the appropriate function for each
 * data type (CELL, DCELL, FCELL)
 */
int main(int argc, char *argv[])
{
    struct Cell_head r_cellhd;	/* it stores region information, */
struct Cell_head g_cellhd;
 struct Cell_head b_cellhd;
/*				   and header information of rasters */


    char *r_mapset;		/* mapset name */
	char *g_mapset;
	char *b_mapset;

    int nrows, ncols;
    int row, col;


	void *r_band;
	void *g_band;
	void *b_band;
	int r_fd, g_fd, b_fd;
    RASTER_MAP_TYPE r_data_type, g_data_type, b_data_type;	/* type of the map (CELL/DCELL/...) */
    struct History history;	/* holds meta-data (title, comments,..) */

    struct GModule *module;	/* GRASS module for parsing arguments */

    struct Option *r_input, *g_input, *b_input, *output;	/* options */

    /* initialize GIS environment */
    G_gisinit(argv[0]);		/* reads grass env, stores program name to G_program_name() */

    /* initialize module */
    module = G_define_module();
    G_add_keyword(_("imagery"));
    G_add_keyword(_("segmentation"));
    G_add_keyword(_("superpixels"));
	G_add_keyword(_("SLIC"));
    module->description = _("SLIC segmenation");


    /* Define the different options as defined in gis.h */
    r_input = G_define_standard_option(G_OPT_R_INPUT);
	r_input->key = "red";
	r_input->answer = NULL;
	r_input->description = "Name of raster map to be used for <red>";

	g_input = G_define_standard_option(G_OPT_R_INPUT);
	g_input->key = "green";
	g_input->answer = NULL;
	g_input->description = "Name of raster map to be used for <green>";
	
	b_input = G_define_standard_option(G_OPT_R_INPUT);
	b_input->key = "blue";
	b_input->answer = NULL;
	b_input->description = "Name of raster map to be used for <blue>";

	struct Option *opt_iteration, *opt_super_pixels;
    opt_iteration = G_define_option();
    opt_iteration->key = "iter";
    opt_iteration->type = TYPE_INTEGER;
    opt_iteration->required = NO;
    opt_iteration->description = _("Maximum number of iterations");
    opt_iteration->answer = "10";

    opt_super_pixels = G_define_option();
    opt_super_pixels->key = "k";
    opt_super_pixels->type = TYPE_INTEGER;
    opt_super_pixels->required = NO;
    opt_super_pixels->description = _("No of super pixels");
    opt_super_pixels->answer = "200";

	
    output = G_define_standard_option(G_OPT_R_OUTPUT);
		

    /* options and flags parser */
    if (G_parser(argc, argv))
	exit(EXIT_FAILURE);

	int n_iterations;
    if (opt_iteration->answer) {
		if ( sscanf(opt_iteration->answer, "%d", &n_iterations) != 1 ) {
			G_fatal_error(_("Illegal value for iter (%s)"),  opt_iteration->answer);
		}
	}
    else {
		n_iterations = 10;
	}

	int n_super_pixels;
    if (opt_super_pixels->answer) {
		if ( sscanf(opt_super_pixels->answer, "%d", &n_super_pixels) != 1 ) {
			G_fatal_error(_("Illegal value for k (%s)"),  opt_super_pixels->answer);
		}
	}
    else {
		n_super_pixels = 200;
	}
	
	
    /* stores options and flags to variables */
	//		char *r_name, g_name, b_name;	
	const char*    r_name = r_input->answer;
	const char*	   g_name = g_input->answer;
	const char*	   b_name = b_input->answer;
	const char*    result = output->answer;

    /* returns NULL if the map was not found in any mapset, 
     * mapset name otherwise */
    r_mapset = (char *) G_find_raster2(r_name, "");
    if (r_mapset == NULL)
	G_fatal_error(_("Raster map <%s> not found"), r_name);

    g_mapset = (char *) G_find_raster2(g_name, "");
    if (g_mapset == NULL)
	G_fatal_error(_("Raster map <%s> not found"), g_name);

	b_mapset = (char *) G_find_raster2(b_name, "");
    if (b_mapset == NULL)
	G_fatal_error(_("Raster map <%s> not found"), b_name);
	
    /* determine the inputmap type (CELL/FCELL/DCELL) */
    r_data_type = Rast_map_type(r_name, r_mapset);
	g_data_type = Rast_map_type(g_name, g_mapset);
	b_data_type = Rast_map_type(b_name, b_mapset);

    /* Rast_open_old - returns file destriptor (>0) */
    r_fd = Rast_open_old(r_name, r_mapset);
	g_fd = Rast_open_old(g_name, g_mapset);
	b_fd = Rast_open_old(b_name, b_mapset);

    /* controlling, if we can open input raster */
    Rast_get_cellhd(r_name, r_mapset, &r_cellhd);

    G_debug(3, "number of rows in R %d", r_cellhd.rows);


    /* controlling, if we can open input raster */
    Rast_get_cellhd(g_name, g_mapset, &g_cellhd);

    G_debug(3, "number of rows in G %d", g_cellhd.rows);

    /* controlling, if we can open input raster */
    Rast_get_cellhd(b_name, b_mapset, &b_cellhd);

    G_debug(3, "number of rows in B %d", b_cellhd.rows);
		
    /* Allocate input buffer */
    r_band = Rast_allocate_buf(r_data_type);
	g_band = Rast_allocate_buf(g_data_type);
	b_band = Rast_allocate_buf(b_data_type);

    /* Allocate output buffer, use input map data_type */
    nrows = Rast_window_rows();
    ncols = Rast_window_cols();

	int m_size = nrows*ncols;
	double *L = NULL;
	double *A = NULL;
	double *B = NULL;

	L = G_malloc (sizeof (double) * m_size);
	memset (L, 0, sizeof (double) * m_size);
	
	A = G_malloc (sizeof (double) * m_size);
	memset (A, 0, sizeof (double) * m_size);
	
	B = G_malloc (sizeof (double) * m_size);
	memset (B, 0, sizeof (double) * m_size);


	int index = 0;
		
    /* for each row */
    for (row = 0; row < nrows; row++) {
	G_percent(row, nrows, 2);

	/* read input map */
	Rast_get_row(r_fd, r_band, row, r_data_type);
	Rast_get_row(g_fd, g_band, row, g_data_type);
	Rast_get_row(b_fd, b_band, row, b_data_type);

	
	/* process the data */
	for (col = 0; col < ncols; col++) {

		//HERE: convert pixel to lab colour space
		
		int r = ((int *) r_band)[col];
		int g = ((int *) g_band)[col];
		int b = ((int *) b_band)[col];

		float var_R = (r / 255.0f); //R from 0 to 255
		float var_G = (g / 255.0f); //G from 0 to 255
		float var_B = (b / 255.0f); //B from 0 to 255


		if (var_R > 0.04045f) {
			var_R = powf(( (var_R + 0.055f) / 1.055f), 2.4f);
		} else {
			var_R = var_R / 12.92f;
		}
		
		if (var_G > 0.04045) {
			var_G = powf(( (var_G + 0.055f) / 1.055f), 2.4f);
		} else {
			var_G = var_G / 12.92f;
		}
		
		if (var_B > 0.04045f) {
			var_B = powf(( (var_B + 0.055f) / 1.055f), 2.4f);
		} else {
			var_B = var_B / 12.92f;
		}
		
		var_R = var_R * 100;
		var_G = var_G * 100;
		var_B = var_B * 100;
		
		//Observer. = 2°, Illuminant = D65
		double X = var_R * 0.4124f + var_G * 0.3576f + var_B * 0.1805f;
		double Y = var_R * 0.2126f + var_G * 0.7152f + var_B * 0.0722f;
		double Z = var_R * 0.0193f + var_G * 0.1192f + var_B * 0.9505f;
		
		
		double ref_X = 95.047;
		double ref_Y = 100.000;
		double ref_Z = 108.883;
		
		double var_X = X / ref_X;      
		double var_Y = Y / ref_Y;      
		double var_Z = Z / ref_Z;      
		
		if ( var_X > 0.008856 ) var_X = powf(var_X, 1.0/3.0);
		else                    var_X = ( 7.787 * var_X ) + ( 16 / 116 );
		
		if ( var_Y > 0.008856 ) var_Y = powf(var_Y, 1.0/3.0);
		else                    var_Y = ( 7.787 * var_Y ) + ( 16 / 116 );
		
		if ( var_Z > 0.008856 )
			var_Z = powf(var_Z, 1.0/3.0);
		else
			var_Z = ( 7.787 * var_Z ) + ( 16 / 116 );
		
		L[index] = ( 116 * var_Y ) - 16;
		A[index] = 500 * ( var_X - var_Y );
		B[index] = 200 *(var_Y - var_Z );
		
		
		index = index + 1;
	}
	
    }




	

	int g_width = ncols;
	int g_height = nrows;

	//HERE

	double compactness = 20;
	int superpixelsize = 0.5+(double)g_width*(double)g_height/(double)	n_super_pixels;

	int* klabels = NULL;
	int sz = nrows * ncols;


	
	klabels = G_malloc (sizeof (int) * sz);
	int s;
	for( s = 0; s < sz; s++ ) klabels[s] = -1;
	
	int offset =  sqrt((double)superpixelsize) + 0.5;
	double* kseedsl;
	double* kseedsa;
	double* kseedsb;
	double* kseedsx;
	double* kseedsy;


	/* int g_width = ncols; */
	/* int g_height = nrows; */
	



	short perturbseeds = 0;
	double *edgemag;


	/////////////////:GetLABXYSeeds_ForGivenStepSize
	 
	short hexgrid = 0;
	int xstrips = (0.5+(double)g_width / (double)offset);
	int ystrips = (0.5+(double)g_height / (double)offset);

    int xerr = g_width  - offset*xstrips;
	if(xerr < 0)	{		xstrips--;		xerr = g_width - offset*xstrips;	}
    int yerr = g_height - offset*ystrips;
	if(yerr < 0)	{		ystrips--;		yerr = g_height - offset*ystrips;	}

	#ifdef MY_DEBUG
	printf("superpixelsize=%d\n", superpixelsize);
	printf("g_height=%d\n", g_height);
	printf("g_width=%d\n", g_width);


	printf("ystrips=%d\n", ystrips);
	
	printf("xstrips=%d\n", xstrips);
	 		 
	printf("xerr=%d\n", xerr);
	printf("yerr=%d\n", yerr);
   #endif


	double xerrperstrip = (double)xerr/(double)xstrips;
	double yerrperstrip = (double)yerr/(double)ystrips;

	#ifdef MY_DEBUG
	printf("xerrperstrip=%f\n", xerrperstrip);
	printf("yerrperstrip=%f\n", yerrperstrip);
	#endif
	
	int xoff = offset/2;
	int yoff = offset/2;
	//-------------------------
	const int numseeds = xstrips*ystrips;
	//-------------------------

	kseedsl = G_malloc (sizeof (double) * numseeds);
	memset (kseedsl, 0, sizeof (double) * numseeds);

	kseedsa = G_malloc (sizeof (double) * numseeds);
	memset (kseedsa, 0, sizeof (double) * numseeds);	

	kseedsb = G_malloc (sizeof (double) * numseeds);
	memset (kseedsb, 0, sizeof (double) * numseeds);
	
	kseedsx = G_malloc (sizeof (double) * numseeds);
	memset (kseedsx, 0, sizeof (double) * numseeds);
	
	kseedsy = G_malloc (sizeof (double) * numseeds);
	memset (kseedsy, 0, sizeof (double) * numseeds);

	int x,y;
	int n = 0;

	#ifdef MY_DEBUG
	 printf("numseeds=%d\n", numseeds);
	 #endif
	 //numseeds = numlabels;
	 
	for(  y = 0; y < ystrips; y++ )
	{
		 int ye = y*yerrperstrip;
		for(  x = 0; x < xstrips; x++ )
		{
			int xe = x*xerrperstrip;
             int seedx = (x*offset+xoff+xe);
            if(hexgrid > 0 )
			{
				seedx = x*offset+(xoff<<(y&0x1))+xe;
				seedx = MIN(g_width-1,seedx);
			} //for hex grid sampling
			
			int seedy = (y*offset+yoff+ye);
			int i = seedy*g_width + seedx;

			//	printf("L[i]=%f where i=%d \n", L[i], i);
			kseedsl[n] = L[i];
			kseedsa[n] = A[i];
			kseedsb[n] = B[i];
            kseedsx[n] = seedx;
            kseedsy[n] = seedy;
			n++;
		}
	}
	

	int numk = numseeds;
	//----------------

	double *clustersize;
	clustersize = G_malloc (sizeof (double) * numk);
	memset (clustersize, 0, sizeof (double) * numk);

	double *inv;
	inv = G_malloc (sizeof (double) * numk);
	memset (inv, 0, sizeof (double) * numk);
	
	double *sigmal;
	sigmal = G_malloc (sizeof (double) * numk);
	memset (sigmal, 0, sizeof (double) * numk);

	
	double *sigmaa;
	sigmaa = G_malloc (sizeof (double) * numk);
	memset (sigmaa, 0, sizeof (double) * numk);

	
	double *sigmab;
	sigmab = G_malloc (sizeof (double) * numk);
	memset (sigmab, 0, sizeof (double) * numk);

	double *sigmax;
	sigmax = G_malloc (sizeof (double) * numk);
	memset (sigmax, 0, sizeof (double) * numk);

	double *sigmay;
	sigmay = G_malloc (sizeof (double) * numk);
	memset (sigmay, 0, sizeof (double) * numk);


	//double *distvec;
	//	distvec = G_malloc (sizeof (double) * sz);

	double distvec[sz];
	int p;
	for( p = 0; p < sz; p++ ) distvec[p] = 1E+9;

	double invwt = 1.0/((offset/compactness)*(offset/compactness));

	int x1, y1, x2, y2;
	double dist;
	double distxy;

	//int n,x,y;

	int itr;
	double he = (double)g_height;
	double wi = (double)g_width;
	double dbl_offset = (double)offset;
	for( itr = 0; itr <  n_iterations ; itr++ )
	{
		for( p = 0; p < sz; p++ ) distvec[p] = 1E+9;
	
		int n;
		for(  n = 0; n < numk; n++ )
		{
			y1 = (int)MAX(0.0,	 kseedsy[n]-dbl_offset);
			y2 = (int)MIN(he,   kseedsy[n]+dbl_offset);
			x1 = (int)MAX(0.0,	 kseedsx[n]-dbl_offset);
			x2 = (int)MIN(wi,	 kseedsx[n]+dbl_offset);
			
			int y;

			//	printf("y1= %d y2=%d x1=%d x2=%d \n", y1, y2, x1, x2);
									
			for( y = y1; y < y2; y++ )
			{
				int x;
				for(  x = x1; x < x2; x++ )
				{
					int  i = y* g_width + x;
					double dx = (double)x;
					double dy = (double)y;
					
					dist =	(L[i] - kseedsl[n])*(L[i] - kseedsl[n]) +
						(A[i] - kseedsa[n])*(A[i] - kseedsa[n]) +
						(B[i] - kseedsb[n])*(B[i] - kseedsb[n]);
					
					distxy =   (dx - kseedsx[n])*(dx - kseedsx[n]) +
						(dy - kseedsy[n])*(dy - kseedsy[n]);
					
					//------------------------------------------------------------------------
					dist += distxy*invwt;//dist = sqrt(dist) + sqrt(distxy*invwt);//this is more exact
					//------------------------------------------------------------------------
					if( dist < distvec[i] )
					{
						//	printf("n=%d with i=<%d>\n", n, i);
						distvec[i] = dist;
						klabels[i]  = n;
					}
					else
					{

						//	printf("distvec[i]=%f and dist=%f with i=<%d>\n", distvec[i], i);
					}
				}
			}
		}

		/*
		int ww;
	for( ww = 0; ww < sz; ww++ )
	{
		if( klabels[ww] > -1)
	   	printf("klabels[%d]=%d\n", ww, klabels[ww]);
	}
		*/
		
		//-----------------------------------------------------------------
		// Recalculate the centroid and store in the seed values
		//------------------------------------------wi-----------------------
		//instead of reassigning memory on each iteration, just reset.

		memset (sigmal, 0, sizeof (double) * numk);
		memset (sigmaa, 0, sizeof (double) * numk);
		memset (sigmab, 0, sizeof (double) * numk);
		memset (sigmax, 0, sizeof (double) * numk);
		memset (sigmay, 0, sizeof (double) * numk);
		memset (clustersize, 0, sizeof (double) * numk);		
		
		{int ind = 0;
		int r,c;
		for( r = 0; r < g_height; r++ )
		{
			for(  c = 0; c < g_width; c++ )
			{
				sigmal[klabels[ind]] += L[ind];
				sigmaa[klabels[ind]] += A[ind];
				sigmab[klabels[ind]] += B[ind];
				sigmax[klabels[ind]] += c;
				sigmay[klabels[ind]] += r;
				//------------------------------------
				//edgesum[klabels[ind]] += edgemag[ind];
				//------------------------------------
				clustersize[klabels[ind]] += 1.0;
				ind++;
			}
		}}
		
		{int k;
		for( k = 0; k < numk; k++ )
		{
			if( clustersize[k] <= 0 ) clustersize[k] = 1;
			inv[k] = 1.0/clustersize[k];//computing inverse now to multiply, than divide later
		}}

	   
		
		{ int k;
			for( k = 0; k < numk; k++ )
		{
			kseedsl[k] = sigmal[k]*inv[k];
			kseedsa[k] = sigmaa[k]*inv[k];
			kseedsb[k] = sigmab[k]*inv[k];
			kseedsx[k] = sigmax[k]*inv[k];
			kseedsy[k] = sigmay[k]*inv[k];
			//------------------------------------
			//edgesum[k] *= inv[k];
			//------------------------------------
		}}
	}



	//numlabels = kseedsl.size();
	int numlabels = numk;

	#ifdef MY_DEBUG
	printf("numk=%d\n", numk);
	#endif

   
	int* nlabels;
	nlabels = G_malloc (sizeof (int) * sz);
	memset (nlabels, 0, sizeof (int) * sz);

	
	
	SLIC_EnforceLabelConnectivity(klabels, g_width, g_height,
							 nlabels,
							 numlabels,
							 (double)sz/((double)(offset*offset)));

	
	{int i;
	for( i = 0; i < sz; i++ ) klabels[i] = nlabels[i];}
	
	if(nlabels) G_free(nlabels);





	int outfd;
	

	const int dx8[8] = {-1, -1,  0,  1, 1, 1, 0, -1};
	const int dy8[8] = { 0, -1, -1, -1, 0, 1, 1,  1};


	
	int mainindex=0;
	int cind =0;

	short *istaken;
	istaken = G_malloc (sizeof (short) * sz);
	memset (istaken, 0, sizeof (short) * sz);

	int *contourx;
	contourx = G_malloc (sizeof (int) * sz);
	memset (contourx, 0, sizeof (int) * sz);

	int *contoury;
	contoury = G_malloc (sizeof (int) * sz);
	memset (contoury, 0, sizeof (int) * sz);

	int j,k;
	for(  j = 0; j < g_height; j++ )
	{
		for(  k = 0; k < g_width; k++ )
		{
			int np = 0;
			int i;
			for( i = 0; i < 8; i++ )
			{
				int x = k + dx8[i];
				int y = j + dy8[i];

				if( (x >= 0 && x < g_width) && (y >= 0 && y < g_height) )
				{
					int index = y*g_width + x;

					//					if(  istaken[index] < 1 ) //comment this to obtain internal contours
					{
						if( klabels[mainindex] != klabels[index] ) np++;
					}
				}
			}
			if( np > 1 )
			{
				contourx[cind] = k;
				contoury[cind] = j;
				istaken[mainindex] = 1;
				//img[mainindex] = color;
				cind++;
			}
			mainindex++;
		}
	}

	
	int r,c;

	DCELL *ubuff[nrows];
	for(  r = 0; r < nrows; r++ )
	{
		ubuff[r] = Rast_allocate_d_buf();
	}

	int numboundpix = cind;//int(contourx.size());
	
	for(  j = 0; j < numboundpix; j++ )
	{
		//		int ii = contoury[j]*g_width + contourx[j];
		ubuff[ contoury[j] ][ contourx[j] ] = 1;

		int n;
		for(  n = 0; n < 8; n++ )
		{
			int x = contourx[j] + dx8[n];
			int y = contoury[j] + dy8[n];
			if( (x >= 0 && x < g_width) && (y >= 0 && y < g_height) )
			{
				int ind = y*g_width + x;
				if(istaken[ind] < 1) {
					ubuff[y][x] =0;
				}
			}
		}
	}



    outfd = Rast_open_new(result, DCELL_TYPE);

	int z;
	for (z = 0; z < nrows; z++)
	{
	Rast_put_row(outfd, ubuff[z], DCELL_TYPE);
	}

	for (z = 0; z < nrows; z++)
	{
		G_free(ubuff[z]);
	}
	

    /* memory cleanup */


	G_free(kseedsl);
	G_free(kseedsa);
	G_free(kseedsb);	
	G_free(kseedsx);
	G_free(kseedsy);

	G_free(sigmal);
	G_free(sigmaa);
	G_free(sigmab);	
	G_free(sigmax);
	G_free(sigmay);
	
	G_free(klabels);
	
	G_free(L);
	G_free(A);
	G_free(B);

   	
    G_free(r_band);
	G_free(g_band);
	G_free(b_band);

    /* closing raster maps */
    Rast_close(r_fd);
	Rast_close(g_fd);
	Rast_close(b_fd);
	Rast_close(outfd);


    exit(EXIT_SUCCESS);
}
