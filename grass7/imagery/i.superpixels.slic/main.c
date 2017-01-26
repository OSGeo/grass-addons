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

/*#define MY_DEBUG 1 */

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



  struct Ref group_ref;

  char grp_name[INAME_LEN];

  int n_iterations, n_super_pixels;

  struct Option *output;  /* option for output */

  int nrows, ncols;
  
  DCELL **pdata;

  off_t sz;

  /* loop variables */
  int nf;
  int *ifd, index, row, col, nbands;
  DCELL **ibuf, *min, *max, *rng;
  struct FPRange drange;

  double compactness;
  int superpixelsize;
  int* klabels = NULL;
  int offset;

  double d_nrows, d_ncols, xerrperstrip, yerrperstrip;
  int xstrips, ystrips, xerr, yerr, xoff, yoff;
  double *kseedsx, *kseedsy;
  double **kseeds;

  int n;

  /* loop variables */
  int s, x, y, xe, ye, seedx;
  short hexgrid, perturbseeds;
  int seedy, cindex;

  double *edgemag;

  double *clustersize, *inv, *sigmax, *sigmay;
  
  double** sigma;

  /* loop variables */
  int p;

  double invwt;

  int x1, y1, x2, y2, itr;
  double dist, distxy, dx, dy, dbl_offset;
  double distsum;
 
  
  int* nlabels;
  int k, r, c, ind, i;
  int k_offset, np, outfd, z;

  CELL *obuf;
  perturbseeds = 0;
  hexgrid = 0;
  compactness = 0;
  superpixelsize = 0; 
 

  /* initialize GIS environment */
  G_gisinit(argv[0]);

  /* initialize module */
  module = G_define_module();
  G_add_keyword(_("imagery"));
  G_add_keyword(_("segmentation"));
  G_add_keyword(_("superpixels"));
  G_add_keyword(_("SLIC"));
  module->description = _("Perform image segmentation using the SLIC segmentation method.");

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
  opt_compactness->type = TYPE_DOUBLE;
  opt_compactness->required = NO;
  opt_compactness->description = _("Compactness");
  opt_compactness->answer = "20";
  
	
  output = G_define_standard_option(G_OPT_R_OUTPUT);
		 
  /* options and flags parser */
  if (G_parser(argc, argv))
    exit(EXIT_FAILURE);
  
  G_strip(grp->answer);
  strcpy(grp_name, grp->answer);

  /* find group */
  if (!I_find_group(grp_name))
    G_fatal_error(_("Group <%s> not found"), grp_name);

  /* get the group ref */
  if (!I_get_group_ref(grp_name, (struct Ref *)&group_ref))
    G_fatal_error(_("Could not read REF file for group <%s>"), grp_name);
  nbands = group_ref.nfiles;
  if (nbands <= 0) {
    G_important_message(_("Group <%s> contains no raster maps; run i.group"),
			grp->answer);
    exit(EXIT_SUCCESS);
  }
  

  if (opt_iteration->answer) {
    if ( sscanf(opt_iteration->answer, "%d", &n_iterations) != 1 ) {
      G_fatal_error(_("Illegal value for iter (%s)"),  opt_iteration->answer);
    }
  }
  else {
    n_iterations = 10;
  }

  
  if (opt_super_pixels->answer) {
    if ( sscanf(opt_super_pixels->answer, "%d", &n_super_pixels) != 1 ) {
      G_fatal_error(_("Illegal value for k (%s)"),  opt_super_pixels->answer);
    }
  }
  else {
    n_super_pixels = 200;
  }

  if (opt_compactness->answer) {
    if ( sscanf(opt_compactness->answer, "%lf", &compactness) != 1 ) {
      G_fatal_error(_("Illegal value for co (%s)"),  opt_compactness->answer);
    }
  }
  else {
    compactness = 20;
  }
  
  const char *outname = output->answer;
 
  nrows = Rast_window_rows();
  ncols = Rast_window_cols();

  pdata  = G_malloc (sizeof (DCELL *) * group_ref.nfiles);

  sz = nrows * ncols;
   
  ifd = G_malloc (sizeof (int *) * group_ref.nfiles);
  ibuf = G_malloc (sizeof (DCELL **) * group_ref.nfiles);
  min = G_malloc (sizeof (DCELL) * group_ref.nfiles);
  max = G_malloc (sizeof (DCELL) * group_ref.nfiles);
  rng = G_malloc (sizeof (DCELL) * group_ref.nfiles);

  for (nf = 0; nf < group_ref.nfiles; nf++) {
    ibuf[nf] = Rast_allocate_d_buf();
    ifd[nf] = Rast_open_old(group_ref.file[nf].name, group_ref.file[nf].mapset);

    Rast_read_fp_range(group_ref.file[nf].name, group_ref.file[nf].mapset,
		       &drange);
    Rast_get_fp_range_min_max(&drange, &min[nf], &max[nf]);
    rng[nf] = max[nf] - min[nf];

    pdata[nf]  = G_malloc (sizeof (DCELL) * sz);
    memset (pdata[nf], 0, sizeof (DCELL) * sz);
  }

  for (row = 0; row < nrows; row++) {
    G_percent(row, nrows, 2);

    for (nf = 0; nf < group_ref.nfiles; nf++)
      Rast_get_d_row(ifd[nf], ibuf[nf], row);
    for (col = 0; col < ncols; col++) {
      int isnull = 0;

      for (nf = 0; nf < group_ref.nfiles; nf++) {
	if (Rast_is_d_null_value(&ibuf[nf][col])) {
	    isnull = 1;
	    break;
	}
        pdata[nf][row * ncols + col] = (ibuf[nf][col] - min[nf]) / rng[nf];
      }
      if (isnull) {
        for (nf = 0; nf < group_ref.nfiles; nf++)
	  Rast_set_d_null_value(&pdata[nf][row * ncols + col], 1);
      }
    }
  }

  for (nf = 0; nf < group_ref.nfiles; nf++) {
    Rast_close(ifd[nf]);
    G_free(ibuf[nf]);
  }
  G_free(ifd);
  G_free(ibuf);
	
  
  superpixelsize = 0.5+(double)ncols * (double)nrows / (double)n_super_pixels;


  klabels = G_malloc (sizeof (int) * sz);
  for( s = 0; s < sz; s++ )
    klabels[s] = -1;
	
  offset =  sqrt((double)superpixelsize) + 0.5;

  d_nrows = (double)nrows;
  d_ncols = (double)ncols;
	
  /* :GetLABXYSeeds_ForGivenStepSize */
	 
  
  xstrips = (0.5+d_ncols / (double)offset);
  ystrips = (0.5+d_nrows / (double)offset);

  xerr = ncols  - offset*xstrips;
  if(xerr < 0) {
    xstrips--;
    xerr = ncols - offset*xstrips;
  }
    
  yerr = nrows - offset*ystrips;
  if(yerr < 0)  {
    ystrips--;
    yerr = nrows - offset*ystrips;
  }


  xerrperstrip = (double)xerr/(double)xstrips;
  yerrperstrip = (double)yerr/(double)ystrips;

  
  xoff = offset/2;
  yoff = offset/2;
  
  const int numseeds = xstrips*ystrips; 

  kseedsx = G_malloc (sizeof (double) * numseeds);
  memset (kseedsx, 0, sizeof (double) * numseeds);
	
  kseedsy = G_malloc (sizeof (double) * numseeds);
  memset (kseedsy, 0, sizeof (double) * numseeds);

  n = 0;

#ifdef MY_DEBUG
  printf("superpixelsize=%d\n", superpixelsize);
  printf("nrows=%d\n", nrows);
  printf("ncols=%d\n", ncols);  
  printf("xerrperstrip=%f\n", xerrperstrip);
  printf("yerrperstrip=%f\n", yerrperstrip);
  printf("numseeds=%d\n", numseeds);
#endif

  kseeds  = G_malloc (sizeof (double *) * group_ref.nfiles);
  for (nf = 0; nf < group_ref.nfiles; nf++) {
    G_percent(nf, group_ref.nfiles, 2);
    kseeds[nf] = G_malloc (sizeof (double) * numseeds);
    memset (kseeds[nf], 0, sizeof (double) * numseeds);		
  }


  for(  y = 0; y < ystrips; y++ ) {
    ye = y*yerrperstrip;
    for(  x = 0; x < xstrips; x++ )  {
      xe = x*xerrperstrip;
      seedx = (x*offset+xoff+xe);
      if(hexgrid > 0 ) {
	seedx = x*offset+(xoff<<(y&0x1))+xe;
	seedx = MIN(ncols-1,seedx);
      } /* for hex grid sampling */
			
      seedy = (y*offset+yoff+ye);
      cindex = seedy*ncols + seedx;

			
      for (nf = 0; nf < group_ref.nfiles; nf++) {
	kseeds[nf][n] = pdata[nf][cindex]; 
      }
      kseedsx[n] = seedx;
      kseedsy[n] = seedy;
      n++;
    }
  }

  const int numk = numseeds;

  clustersize = G_malloc (sizeof (double) * numk);
  memset (clustersize, 0, sizeof (double) * numk);

  inv = G_malloc (sizeof (double) * numk);
  memset (inv, 0, sizeof (double) * numk);

  sigma  = G_malloc (sizeof (double *) * group_ref.nfiles);
  for (nf = 0; nf < group_ref.nfiles; nf++)	{
    sigma[nf] = G_malloc (sizeof (double) * numk);
    memset (sigma[nf], 0, sizeof (double) * numk);		
  }

  sigmax = G_malloc (sizeof (double) * numk);
  memset (sigmax, 0, sizeof (double) * numk);

  sigmay = G_malloc (sizeof (double) * numk);
  memset (sigmay, 0, sizeof (double) * numk);


  double *distvec;
  distvec = G_malloc (sizeof (double) * sz);

  double *distspec;
  distspec = G_malloc (sizeof (double) * sz);

  for( s = 0; s < sz; s++ )
    distspec[s] = 0;

  double *maxdistspec;
  maxdistspec = G_malloc (sizeof (double) * numk);

  for(  n = 0; n < numk; n++ )
    maxdistspec[n] = 1;

  invwt = compactness * 0.005 / (offset * offset);


  dbl_offset = (double)offset;
  for( itr = 0; itr <  n_iterations ; itr++ ) {
    G_percent(itr, n_iterations, 2);

    for( p = 0; p < sz; p++ )
      distvec[p] = 1E+9;
	
    for( p = 0; p < sz; p++ )
      distspec[p] = 0;

		
    for(  n = 0; n < numk; n++ )  {
      y1 = (int)MAX(0.0,	 kseedsy[n]-dbl_offset);
      y2 = (int)MIN(d_nrows,     kseedsy[n]+dbl_offset);
      x1 = (int)MAX(0.0,	 kseedsx[n]-dbl_offset);
      x2 = (int)MIN(d_ncols,	 kseedsx[n]+dbl_offset);
												
      for( y = y1; y < y2; y++ ) {				
	for(  x = x1; x < x2; x++ ) {
	  i = y* ncols + x;
	  dx = (double)x;
	  dy = (double)y;
			    
	  dist = 0.0;
	  for (nf = 0; nf < group_ref.nfiles; nf++) {
	    dist += ((pdata[nf][i] - kseeds[nf][n]) * (pdata[nf][i] - kseeds[nf][n]));
	  }
	  dist /= nbands;
	  distxy = (dx - kseedsx[n])*(dx - kseedsx[n]) +
	    (dy - kseedsy[n])*(dy - kseedsy[n]);
					
	  /* ----------------------------------------------------------------------- */
	  distsum = dist / maxdistspec[n] + distxy*invwt;
	  /* dist = sqrt(dist) + sqrt(distxy*invwt);  this is more exact */
	  /*------------------------------------------------------------------------ */
	  if( distsum < distvec[i] ) {
	    distvec[i] = distsum;
	    distspec[i] = dist;
	    klabels[i]  = n;
	  }

	} /* for( x=x1 */
      } /* for( y=y1 */
    } /* for (n=0 */
		
#if 0
    if (itr == 0) {
      for(  n = 0; n < numk; n++ )
	maxdistspec[n] = 0;
    }
    for( s = 0; s < sz; s++ ) {
      if (maxdistspec[klabels[s]] < distspec[s])
	maxdistspec[klabels[s]] = distspec[s];
    }
#endif		
    for (nf = 0; nf < group_ref.nfiles; nf++) {
      memset (sigma[nf], 0, sizeof (double) * numk);
    }
		
    memset (sigmax, 0, sizeof (double) * numk);
    memset (sigmay, 0, sizeof (double) * numk);
    memset (clustersize, 0, sizeof (double) * numk);		

    ind = 0;   		
    for( r = 0; r < nrows; r++ )	{
      for(  c = 0; c < ncols; c++ ) {
	for (nf = 0; nf < group_ref.nfiles; nf++) {
	  sigma[nf][klabels[ind]] += pdata[nf][ind];
	}
	sigmax[klabels[ind]] += c;
	sigmay[klabels[ind]] += r;
	/*-------------------------------------------*/
	/* edgesum[klabels[ind]] += edgemag[ind];    */
	/*-------------------------------------------*/
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
      /*------------------------------------*/
      /* edgesum[k] *= inv[k];              */
      /*------------------------------------*/
    }
  }
  G_percent(1, 1, 1);



  const int numlabels = numk;

#ifdef MY_DEBUG
  printf("numk=%d\n", numk);
#endif


  nlabels = G_malloc (sizeof (int) * sz);
  memset (nlabels, 0, sizeof (int) * sz);

  k_offset = (double)sz/((double)(offset*offset));
  SLIC_EnforceLabelConnectivity(klabels, ncols, nrows, nlabels, numlabels, k_offset);

  for( i = 0; i < sz; i++ )
    klabels[i] = nlabels[i];
   	
  if(nlabels)
    G_free(nlabels);

  z = 0;
  outfd = Rast_open_new(outname, CELL_TYPE);  
  obuf = Rast_allocate_c_buf();
  for (row = 0; row < nrows; row++)	 {
    for(col = 0; col < ncols; col++) {
      obuf[col] = klabels[z]+1; /* +1 to avoid category value 0*/
      z++;
    }

    Rast_put_row(outfd, obuf, CELL_TYPE);
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
				   int*   nlabels, /*new labels */
				   int    numlabels,
				   int    K_offset)  {
  
  const int dx4[4] = {-1,  0,  1,  0};
  const int dy4[4] = { 0, -1,  0,  1};

  int i, j, k, n, label, oindex, adjlabel;
  int x,y, nindex, c, count, ind;
  int *xvec, *yvec;
    
  const int sz = width*height;
  const int SUPSZ = sz/K_offset;

  for( i = 0; i < sz; i++ ) nlabels[i] = -1;
  label = 0;
  
  xvec = G_malloc (sizeof (int) * sz);
  memset (xvec, 0, sizeof (int) * sz);
  
  yvec = G_malloc (sizeof (int) * sz);
  memset (yvec, 0, sizeof (int) * sz);  

  oindex = 0;
  adjlabel = 0; /* adjacent label */
  
  for( j = 0; j < height; j++ ) {
    for( k = 0; k < width; k++ )  {
      if( 0 > nlabels[oindex] )     { 
	nlabels[oindex] = label;
	/*--------------------
	 Start a new segment
	 --------------------*/
	xvec[0] = k;
	yvec[0] = j;
	/*-------------------------------------------------------
	 Quickly find an adjacent label for use later if needed
	 -------------------------------------------------------*/

	for( n = 0; n < 4; n++ ) {
	  x = xvec[0] + dx4[n];
	  y = yvec[0] + dy4[n];
	  if( (x >= 0 && x < width) && (y >= 0 && y < height) ) {
	    nindex = y*width + x;
	    if(nlabels[nindex] >= 0) adjlabel = nlabels[nindex];
	  }
	}

	count = 1;
	for( c = 0; c < count; c++ ) {
	  for( n = 0; n < 4; n++ ) {
	    x = xvec[c] + dx4[n];
	    y = yvec[c] + dy4[n];
	    
	    if( (x >= 0 && x < width) && (y >= 0 && y < height) ) {
	      nindex = y*width + x;
	      
	      if( 0 > nlabels[nindex] && labels[oindex] == labels[nindex] ) {
		xvec[count] = x;
		yvec[count] = y;
		nlabels[nindex] = label;
		count++;
	      }
	    }  
	  }
	}
	/*-------------------------------------------------------
	 If segment size is less then a limit, assign an
	 adjacent label found before, and decrement label count.
	-------------------------------------------------------*/
	if(count <= 0) {
	  for( c = 0; c < count; c++ ) {
	    ind = yvec[c]*width+xvec[c];
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
