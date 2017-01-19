/*******************************************************************************
 *
 * MODULE:       i.superpixels.slic
 * AUTHOR(S):    Rashad Kanavath <rashadkm gmail>
 *               based on the C++ SLIC implmenetation from:  
 *               http://ivrl.epfl.ch/research/superpixels
 * PURPOSE:      Perform superpixel segmenation
 *
 * This code performs superpixel segmentation as explained in the paper:
 * "SLIC Superpixels", Radhakrishna Achanta, Appu Shaji, 
 * Kevin Smith, Aurelien Lucchi, Pascal Fua, and Sabine Susstrunk.
 * EPFL Technical Report no. 149300, June 2010. 
 * Below code is ported to grass from original C++ SLIC implmenetation 
 * available at:  http://ivrl.epfl.ch/research/superpixels
 *
 *****************************************************************************/

#include <grass/config.h>
#include <grass/gis.h>
#include <grass/raster.h>
#include <grass/glocale.h>
#include <grass/imagery.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <limits.h>
#include <float.h>

//#define MY_DEBUG 1

#ifndef MAX
#define MAX(x,y) ((x) > (y) ? (x) : (y))
#endif
#ifndef MIN
#define MIN(x,y) ((x) < (y) ? (x) : (y))
#endif

void SLIC_EnforceLabelConnectivity(int* labels, int width, int height,
				     int* nlabels, int numlabels, int K_offset);

int main(int argc, char *argv[])
{

  struct GModule *module;	/* GRASS module for parsing arguments */

  struct Option *grp;        /* imagery group input option */

  struct Option *opt_iteration, *opt_super_pixels, *opt_compactness;

  struct Option  *output;	/* option for output */

  /* initialize GIS environment */
  G_gisinit(argv[0]);

  /* initialize module */
  module = G_define_module();
  G_add_keyword(_("imagery"));
  G_add_keyword(_("segmentation"));
  G_add_keyword(_("superpixels"));
  G_add_keyword(_("SLIC"));
  module->description = _("Performa image segmentation using the SLIC segmentation method.");

  grp = G_define_standard_option(G_OPT_I_GROUP);

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
  opt_super_pixels->description = _("Number of super pixels");
  opt_super_pixels->answer = "200";

  opt_compactness = G_define_option();
  opt_compactness->key = "co";
  opt_compactness->type = TYPE_INTEGER;
  opt_compactness->required = NO;
  opt_compactness->description = _("Compactness");
  opt_compactness->answer = "20";
  
	
  output = G_define_standard_option(G_OPT_R_OUTPUT);
		 
  /* options and flags parser */
  if (G_parser(argc, argv))
    exit(EXIT_FAILURE);

  struct Ref group_ref;
  int nf; // for group_ref.nfiles;
  int nfiles;
  char grp_name[INAME_LEN];
  int nrows, ncols;
  int row, col;  
  
  G_strip(grp->answer);
  strcpy(grp_name, grp->answer);

  /* find group */
  if (!I_find_group(grp_name))
    G_fatal_error(_("Group <%s> not found"), grp_name);

  /* get the group ref */
  if (!I_get_group_ref(grp_name, (struct Ref *)&group_ref))
    G_fatal_error(_("Could not read REF file for group <%s>"), grp_name);
  nfiles = group_ref.nfiles;
  if (nfiles <= 0) {
    G_important_message(_("Group <%s> contains no raster maps; run i.group"),
			grp->answer);
    exit(EXIT_SUCCESS);
  }
	
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


  int n_compactness;
  if (opt_compactness->answer) {
    if ( sscanf(opt_compactness->answer, "%d", &n_compactness) != 1 ) {
      G_fatal_error(_("Illegal value for co (%s)"),  opt_compactness->answer);
    }
  }
  else {
    n_compactness = 20;
  }
  
  const char*  result = output->answer;
 
  /* Allocate output buffer, use input map data_type */
  nrows = Rast_window_rows();
  ncols = Rast_window_cols();

  int sz = nrows * ncols;
	
  int *pdata[group_ref.nfiles];
   
  for (nf = 0; nf < group_ref.nfiles; nf++) {

    int i_fd;
    RASTER_MAP_TYPE i_data_type;
    void *i_band;
		
    int index = 0;
		
    i_fd = Rast_open_old(group_ref.file[nf].name, group_ref.file[nf].mapset);
    i_data_type = Rast_map_type(group_ref.file[nf].name, group_ref.file[nf].mapset);
    i_band = Rast_allocate_buf(i_data_type);
				
    pdata[nf]  = G_malloc (sizeof (int) * sz);
    memset (pdata[nf], 0, sizeof (int) * sz);
    for (row = 0; row < nrows; row++) {
      G_percent(row, nrows, 2);
      Rast_get_row(i_fd, i_band, row, i_data_type);
      for (col = 0; col < ncols; col++) {
	pdata[nf][index] = ((int *) i_band)[col];
	index++;
      }
    }

    G_free(i_band);
    Rast_close(i_fd);

  }
	

  double compactness = (double) n_compactness;
  int superpixelsize = 0.5+(double)ncols * (double)nrows / (double)n_super_pixels;

  int* klabels = NULL;

  klabels = G_malloc (sizeof (int) * sz);
  int s;
  for( s = 0; s < sz; s++ )
    klabels[s] = -1;
	
  int offset =  sqrt((double)superpixelsize) + 0.5;

  double* kseedsx;
  double* kseedsy;	

  short perturbseeds = 0;
  double *edgemag;


  double d_nrows = (double)nrows;
  double d_ncols = (double)ncols;
	
  /////////////////:GetLABXYSeeds_ForGivenStepSize
	 
  short hexgrid = 0;
  int xstrips = (0.5+d_ncols / (double)offset);
  int ystrips = (0.5+d_nrows / (double)offset);

  int xerr = ncols  - offset*xstrips;
  if(xerr < 0) {
    xstrips--;
    xerr = ncols - offset*xstrips;
  }
    
  int yerr = nrows - offset*ystrips;
  if(yerr < 0)  {
    ystrips--;
    yerr = nrows - offset*ystrips;
  }


  double xerrperstrip = (double)xerr/(double)xstrips;
  double yerrperstrip = (double)yerr/(double)ystrips;

	
  int xoff = offset/2;
  int yoff = offset/2;
  //-------------------------
  const int numseeds = xstrips*ystrips;
  //-------------------------

  kseedsx = G_malloc (sizeof (double) * numseeds);
  memset (kseedsx, 0, sizeof (double) * numseeds);
	
  kseedsy = G_malloc (sizeof (double) * numseeds);
  memset (kseedsy, 0, sizeof (double) * numseeds);

  int n = 0;
  int x,y;


#ifdef MY_DEBUG
  printf("superpixelsize=%d\n", superpixelsize);
  printf("nrows=%d\n", nrows);
  printf("ncols=%d\n", ncols);  
  printf("xerrperstrip=%f\n", xerrperstrip);
  printf("yerrperstrip=%f\n", yerrperstrip);
  printf("numseeds=%d\n", numseeds);
#endif

  double* kseeds[group_ref.nfiles];
  for (nf = 0; nf < group_ref.nfiles; nf++) {
    G_percent(nf, group_ref.nfiles, 2);
    kseeds[nf] = G_malloc (sizeof (double) * numseeds);
    memset (kseeds[nf], 0, sizeof (double) * numseeds);		
  }


  for(  y = 0; y < ystrips; y++ ) {
    int ye = y*yerrperstrip;
    for(  x = 0; x < xstrips; x++ )  {
      int xe = x*xerrperstrip;
      int seedx = (x*offset+xoff+xe);
      if(hexgrid > 0 ) {
	seedx = x*offset+(xoff<<(y&0x1))+xe;
	seedx = MIN(ncols-1,seedx);
      } //for hex grid sampling
			
      int seedy = (y*offset+yoff+ye);
      int i = seedy*ncols + seedx;

			
      for (nf = 0; nf < group_ref.nfiles; nf++) {
	kseeds[nf][n] = pdata[nf][i]; 
      }
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

  double* sigma[group_ref.nfiles];
  for (nf = 0; nf < group_ref.nfiles; nf++)	{
    sigma[nf] = G_malloc (sizeof (double) * numk);
    memset (sigma[nf], 0, sizeof (double) * numk);		
  }


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


  int itr;

  double dbl_offset = (double)offset;
  for( itr = 0; itr <  n_iterations ; itr++ ) {
    for( p = 0; p < sz; p++ )
      distvec[p] = 1E+9;
	
    G_percent(itr, n_iterations, 2);
		
    for(  n = 0; n < numk; n++ )  {
      y1 = (int)MAX(0.0,	 kseedsy[n]-dbl_offset);
      y2 = (int)MIN(d_nrows,     kseedsy[n]+dbl_offset);
      x1 = (int)MAX(0.0,	 kseedsx[n]-dbl_offset);
      x2 = (int)MIN(d_ncols,	 kseedsx[n]+dbl_offset);
												
      for( y = y1; y < y2; y++ ) {				
	for(  x = x1; x < x2; x++ ) {
	  int i = y* ncols + x;
	  double dx = (double)x;
	  double dy = (double)y;
			    
	  dist = 0.0;
	  for (nf = 0; nf < group_ref.nfiles; nf++) {
	    dist += ((pdata[nf][i] - kseeds[nf][n]) * (pdata[nf][i] - kseeds[nf][n]));
	  }
	  distxy = (dx - kseedsx[n])*(dx - kseedsx[n]) +
	    (dy - kseedsy[n])*(dy - kseedsy[n]);
					
	  //------------------------------------------------------------------------
	  dist += distxy*invwt;//dist = sqrt(dist) + sqrt(distxy*invwt);//this is more exact
	  //------------------------------------------------------------------------
	  if( dist < distvec[i] ) {
	    distvec[i] = dist;
	    klabels[i]  = n;
	  }

	} //for( x=x1
      } //for( y=y1
    } //for (n=0
		
		
    for (nf = 0; nf < group_ref.nfiles; nf++) {
      memset (sigma[nf], 0, sizeof (double) * numk);
    }
		
    memset (sigmax, 0, sizeof (double) * numk);
    memset (sigmay, 0, sizeof (double) * numk);
    memset (clustersize, 0, sizeof (double) * numk);		

    int k,r,c;
    int ind = 0;   		
    for( r = 0; r < nrows; r++ )	{
      for(  c = 0; c < ncols; c++ ) {
	for (nf = 0; nf < group_ref.nfiles; nf++) {
	  sigma[nf][klabels[ind]] += pdata[nf][ind];
	}
	sigmax[klabels[ind]] += c;
	sigmay[klabels[ind]] += r;
	//------------------------------------
	//edgesum[klabels[ind]] += edgemag[ind];
	//------------------------------------
	clustersize[klabels[ind]] += 1.0;
	ind++;
      }
    }
		
    for( k = 0; k < numk; k++ ) {
      if( clustersize[k] <= 0 )
	clustersize[k] = 1;
		  
      /* computing inverse now to multiply, than divide later */
      inv[k] = 1.0/clustersize[k]; 
    }

	   
    for( k = 0; k < numk; k++ ) {
      for (nf = 0; nf < group_ref.nfiles; nf++)  {
	kseeds[nf][k] = sigma[nf][k]*inv[k];
      }
      kseedsx[k] = sigmax[k]*inv[k];
      kseedsy[k] = sigmay[k]*inv[k];
      //------------------------------------
      //edgesum[k] *= inv[k];
      //------------------------------------
    }
  }



  //numlabels = kseedsl.size();
  int numlabels = numk;

#ifdef MY_DEBUG
  printf("numk=%d\n", numk);
#endif

   
  int* nlabels;
  nlabels = G_malloc (sizeof (int) * sz);
  memset (nlabels, 0, sizeof (int) * sz);


  int k_offset = (double)sz/((double)(offset*offset));
  SLIC_EnforceLabelConnectivity(klabels, ncols, nrows, nlabels, numlabels, k_offset);

  int i, np;
  for( i = 0; i < sz; i++ )
    klabels[i] = nlabels[i];
   
	
  if(nlabels)
    G_free(nlabels);

  int outfd;
  int z = 0;
  outfd = Rast_open_new(result, CELL_TYPE);  
  for (row = 0; row < nrows; row++)	 {
    CELL *ubuff = Rast_allocate_c_buf();
    for(col = 0; col < ncols; col++) {
      ubuff[col] = klabels[z]+1; /* +1 to avoid category value 0*/
      z++;
    }

    Rast_put_row(outfd, ubuff, CELL_TYPE);
    G_free(ubuff);
  }
	
	
  G_free(kseedsx);
  G_free(kseedsy);

  G_free(sigmax);
  G_free(sigmay);
	
  G_free(klabels);

  for (nf = 0; nf < group_ref.nfiles; nf++) {
    G_free(kseeds[nf]);
    G_free(sigma[nf]);
  }
	
  Rast_close(outfd);


  exit(EXIT_SUCCESS);
}




void SLIC_EnforceLabelConnectivity(int*   labels,
				   int    width,
				   int    height,
				   int*   nlabels,//new labels
				   int    numlabels,
				   int    K_offset)  {
  
  const int dx4[4] = {-1,  0,  1,  0};
  const int dy4[4] = { 0, -1,  0,  1};

  const int sz = width*height;
  const int SUPSZ = sz/K_offset;
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
  
  int j, k, n;
  for( j = 0; j < height; j++ ) {
    for( k = 0; k < width; k++ )  {
      if( 0 > nlabels[oindex] )     { 
	nlabels[oindex] = label;
	//--------------------
	// Start a new segment
	//--------------------
	xvec[0] = k;
	yvec[0] = j;
	//-------------------------------------------------------
	// Quickly find an adjacent label for use later if needed
	//-------------------------------------------------------

	for( n = 0; n < 4; n++ ) {
	  int x = xvec[0] + dx4[n];
	  int y = yvec[0] + dy4[n];
	  if( (x >= 0 && x < width) && (y >= 0 && y < height) ) {
	    int nindex = y*width + x;
	    if(nlabels[nindex] >= 0) adjlabel = nlabels[nindex];
	  }
	}

	int c, count = 1;
	for( c = 0; c < count; c++ ) {
	  for( n = 0; n < 4; n++ ) {
	    int x = xvec[c] + dx4[n];
	    int y = yvec[c] + dy4[n];
	    
	    if( (x >= 0 && x < width) && (y >= 0 && y < height) ) {
	      int nindex = y*width + x;
	      
	      if( 0 > nlabels[nindex] && labels[oindex] == labels[nindex] ) {
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
	if(count <= SUPSZ >> 2) {
	  for( c = 0; c < count; c++ ) {
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
