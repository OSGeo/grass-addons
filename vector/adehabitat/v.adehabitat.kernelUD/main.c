/****************************************************************************
*
* MODULE:       v.kernelUD
*
* AUTHOR(S):    Clement Calenge (univ. Lyon 1), original code by 
*               Stefano Menegon, ITC-irst, Trento, Italy
* PURPOSE:      Generates a raster density map from vector points data using 
*               a moving 2D isotropic Gaussian kernel
* COPYRIGHT:    (C) 2004 by the GRASS Development Team
*
*               This program is free software under the GNU General Public
*   	    	License (>=v2). Read the file COPYING that comes with GRASS
*   	    	for details.
*
*****************************************************************************/
#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <float.h>
#include <grass/gis.h>
#include <grass/glocale.h>
#include <grass/gmath.h>
#include <grass/Vect.h>
#include "global.h"


static int ndists;    /* number of distances in dists */
static double *dists; /* array of all distances < dmax */
static int    npoints; 
static int verbose = 1 ;
static double dimension = 2.;


/* -----------------------------------------------------
   Sources for memory allocation from ade4 package for R
   -----------------------------------------------------*/

void taballoc (double ***tab, int l1, int c1)

{
    int i, j;
    
    if ( (*tab = (double **) calloc(l1+1, sizeof(double *))) != 0) {
	for (i=0;i<=l1;i++) {
	    if ( (*(*tab+i)=(double *) calloc(c1+1, sizeof(double))) == 0 ) {
		return;
		for (j=0;j<i;j++) {
		    free(*(*tab+j));
		}
	    }
	}
    }

}

void freetab (double **tab)
{
    int 	i, n;
    
    n = *(*(tab));
    for (i=0;i<=n;i++) {
	free((char *) *(tab+i) );
    }
    free((char *) tab);
}



void vecintalloc (int **vec, int n)
{
    if ( (*vec = (int *) calloc(n+1, sizeof(int))) != NULL) {
	**vec = n;
	return;
    } else {
	return;
    }
}

void freeintvec (int *vec)
{
    
    free((char *) vec);
    
}


/*--------------------------------------------------
*         End of sources of the ade4 package
  --------------------------------------------------*/
 



/* The score function for LSCV minimization: choice of the 
   best smoothing parameter */

double L(double smooth) 
{
  int ii;
  double resL,n;  

  n = (double) npoints;
  resL = 0.;

  for(ii=0; ii < ndists; ii++){ 
      resL+= (exp(-pow(dists[ii],2)/(4. * pow(smooth,2)))) - (4. * (exp(-pow(dists[ii],2)/(2. * pow(smooth,2.)))));
  }
  
  resL = 1./(M_PI * pow(smooth,2.) * n) + (2*resL -3*n)/(M_PI * 4. * pow(smooth,2.) * pow(n, 2.));

      G_debug(3, "smooth = %e resL = %e", smooth, resL);  
  if(verbose)
      G_message(_("\tScore Value=%f\tsmoothing parameter (standard deviation)=%f"),resL, smooth);
  
  return(resL);
}




/* Main function for the kernelUD */

int main(int argc, char **argv) 
{
    /* structures of type "option" allow to specify the options of 
       the function (defined in gis.h) */
    struct Option *in_opt, *out_opt; 
    struct Option *stddev_opt;
    
    /* structures of type "flag" specify the flags of the function */
    struct Flag *flag_o, *flag_v, *flag_q, *flag_h, *flag_r;
    
    char   *mapset;
    
    /* structure "Map_info" contains the info concerning the 
       map formats (defined in dig_structs.i) */
    struct Map_info In, Out; 
    int    fdout = 0;
    int    row,col,ii,i;
    struct Cell_head window; /* Info concerning the map header */
    double gaussian;
    double moyx = 0;
    double moyy = 0;
    double errtx = 0;
    double errty = 0;
    double cellsize;
    double hvec;
    double itt,tmple,tmpsco;
    double N,E;
    DCELL *output_cell = NULL;
    double sigma, dmax;
    
    double **coordinate;
    double **tutu, **attribue;
    int *colid, *rowid;
    int rowb = 0;
    int colb = 0;
    double sigmaOptimal, cumsu;
    struct GModule *module; /* infos related to the module 
			       (name, description) */
    double term;
    double gausmax = 0;
    
    /* Initialize the GIS calls */
    G_gisinit(argv[0]); /* this function initialize the environment: 
			   it verifies that the database and the 
			   mapset are correct */
    
    module = G_define_module(); /* define the info related to the module */
    module->keywords = _("vector, kernel UD");
    module->description = 
	_("Estimates the Utilization distribution on a raster map from vector points data using a moving 2D isotropic Gaussian kernel");
    
    
/* Options of the function: */
    in_opt              = G_define_option();
    in_opt->key         = "input";
    in_opt->type        = TYPE_STRING;
    in_opt->required    = YES;
    in_opt->description = _("input relocations");
    in_opt->gisprompt = "old,vector,vector,input";
    
    out_opt              = G_define_option();
    out_opt->key         = "output";
    out_opt->type        = TYPE_STRING;
    out_opt->required    = YES;
    out_opt->description = _("output raster map");
    
    stddev_opt              = G_define_option() ;
    stddev_opt->key         = "stddeviation";
    stddev_opt->type        = TYPE_DOUBLE;
    stddev_opt->required    = NO;
    stddev_opt->description = _("Suggested smoothing parameter");
    
/* Les flags */
    flag_o              = G_define_flag();
    flag_o->key         = 'o';
    flag_o->description = _("LSCV smoothing parameter");
    
    flag_q              = G_define_flag();
    flag_q->key         = 'q';
    flag_q->description = _("Only calculate LSCV smoothing parameter and exit (no map is written)");

    flag_h              = G_define_flag();
    flag_h->key         = 'h';
    flag_h->description = _("Given smoothing parameter");
    
    flag_v = G_define_flag();
    flag_v->key = 'v';
    flag_v->description = _("Run verbosely");

    flag_r = G_define_flag();
    flag_r->key = 'r';
    flag_r->description = _("Compute home-range volume");
    

    if (G_parser(argc, argv)) /* Any problem with the arguments? */
	exit(EXIT_FAILURE);

    /*read options*/
    if ( flag_h->answer )
	sigma = atof(stddev_opt->answer);
    verbose = flag_v->answer;
    
    if( flag_q->answer ) {
	flag_o->answer=1;
    }
    
    
    /* Get the region */
    G_get_window(&window); 
    
    G_message("RES: %f\tROWS: %d\tCOLS: %d",
	      window.ew_res, window.rows, window.cols); 
    cellsize= pow(window.ew_res, 2);
    
    /* Open input vector */
    /* G_find_vector2 finds a vector map (look but dont touch)*/
    if ((mapset = G_find_vector2 (in_opt->answer, "")) == NULL) 
	G_fatal_error (_("Could not find input map '%s'."), in_opt->answer);

    Vect_set_open_level (2); /* Essential before opening a map! 
				defines the level */
    Vect_open_old (&In, in_opt->answer, mapset); /* Opens the vector map */
    
    /* check and open the name of output map */
    if( !flag_q->answer ) {
	if(G_legal_filename( out_opt->answer ) < 0)
	    G_fatal_error(_("illegal file name [%s]."), out_opt->answer);
	
	G_set_fp_type (DCELL_TYPE); /* storage type for floating-point maps. */
	
	/* Open the output file, and return a descriptor 
	   of the file in  fdout */
	if((fdout = G_open_raster_new(out_opt->answer,DCELL_TYPE)) < 0)
	    G_fatal_error(_("error opening raster map [%s]."), out_opt->answer); 
	
	
	/* allocate output raster */
	output_cell=G_allocate_raster_buf(DCELL_TYPE);
    }
    
    /* Read points */
    npoints = read_points ( &In, &coordinate );
    
 
    if (!(flag_h->answer)) {
	
	/* average of x and y */
	for (ii = 0; ii < npoints; ii++) {
	    moyx += (coordinate[ii][0] / ((double) npoints));
	    moyy += (coordinate[ii][1] / ((double) npoints));
	}
 
	/* variance of x and y */
	for (ii = 0; ii < npoints; ii++) {
	    errtx += ((coordinate[ii][0] - moyx) * 
		      (coordinate[ii][0] - moyx)) / ((double) (npoints-1));
	    errty += ((coordinate[ii][1] - moyy) * 
		      (coordinate[ii][1] - moyy)) / ((double) (npoints-1));
	}
	/* Compute href in sigma */
	sigma = ((sqrt((errtx+errty)/2)) * pow( ((double) npoints), -1./6.));
		
	/* maximum distance 4*sigma (3.9*sigma ~ 1.0000), 
	 * keep it small, otherwise it takes 
	 * too much points and calculation on network becomes slow */
    }
    
    dmax = 400*sigma; /* used as maximum value */
	
    G_message(_("Using maximum distance between points: %f"), dmax);     
    
    ndists = compute_all_distances(coordinate,&dists,npoints,dmax);
    /* here, one computes all the distances LOWER THAN dmax */
    
    G_message(_("Number of input points: %d."), npoints);
    G_message(_("%d distances read from the map."), ndists);
    
    if (ndists == 0)
        G_fatal_error(_("distances between all points are beyond %e (4 * "
			"standard deviation) cannot calculate optimal value."), dmax);
    
    
    /* Computes the optimal smoothing parameter by LSCV */
    if( flag_o->answer ) {
	
	tmple=(( (1.5 * sigma) - (0.1 * sigma) )/100.);
	tmpsco = L((0.1 * sigma));
	sigmaOptimal=(0.1 * sigma);
	
	for (itt=(0.1 * sigma); itt<(1.5 * sigma); itt+=tmple) {
	    hvec=L(itt);
	    if (hvec < tmpsco) {
		sigmaOptimal=itt;
		tmpsco=hvec;
	    }
	}
	/* Reset sigma to calculated optimal value */
	tmpsco=(0.1 * sigma)+tmple;
	if (sigmaOptimal<tmpsco)
	    G_message(_("Convergence: no"));
	if (sigmaOptimal>=tmpsco)
	    G_message(_("Convergence: yes"));
	sigma=sigmaOptimal;
    }
    G_message(_("Smoothing parameter: %f"), sigma);
    
    
    /* in case just LSCV h is desired */
    if( flag_q->answer ) {
	Vect_close (&In);
	exit (0);
    }
    
    
    /* Now, compute the UD */
    
    term=1./(pow(sigma,2.) * 2. * M_PI * npoints);  
    dmax= sigma*4.;
        
    
    /* case where the volume is not desired */
    if (!(flag_r->answer)) {
	G_message(_("\nComputing UD using smoothing parameter=%f."), sigma);
	for(row=0; row<window.rows; row++){
	    G_percent(row,window.rows,2);
	    
	    for(col=0; col<window.cols; col++) {
		
		N = G_row_to_northing(row+0.5,&window);
		E = G_col_to_easting(col+0.5,&window);
		
		compute_distance ( N, E, &In, sigma, term, &gaussian,dmax );
		output_cell[col] = gaussian;
		if ( gaussian > gausmax ) gausmax = gaussian;
	    }
	    G_put_raster_row(fdout,output_cell,DCELL_TYPE);
	}
    	G_close_cell(fdout);
    }
    
    /* case the volume is desired */
    taballoc(&tutu, window.rows, window.cols);
    taballoc(&attribue, window.rows, window.cols);
    vecintalloc(&rowid, (window.rows * window.cols));
    vecintalloc(&colid, (window.rows * window.cols));

    if (flag_r->answer) {
	G_message(_("\nComputing UD using smoothing parameter=%f."), sigma);
	
	/* computes the UD */
	for(row=0; row<window.rows; row++){
	    G_percent(row,window.rows,2);
	    
	    for(col=0; col<window.cols; col++) {
		
		N = G_row_to_northing(row+0.5,&window);
		E = G_col_to_easting(col+0.5,&window);
		
		compute_distance ( N, E, &In, sigma, term, &gaussian,dmax );
		ii=0;
		tutu[row+1][col+1]= gaussian;
	    }
	}
	
	/* compute the volume */
	cumsu=0;
	for(row=0; row<window.rows; row++){
	    for(col=0; col<window.cols; col++) {
		cumsu+=tutu[row+1][col+1];
	    }
	}
	
	G_message(_("\nVolume under the UD=%f."), cumsu*cellsize);
	
	/* standardization of the volume */	
	for(row=0; row<window.rows; row++){
	    for(col=0; col<window.cols; col++) {
		tutu[row+1][col+1]=(tutu[row+1][col+1] / cumsu);
	    }
	}
	
	/* Sort the values */		
	G_message(_("\nComputing home ranges..."));
	ii=0;
	for(row=0; row<window.rows; row++){
	    G_percent(row,window.rows,2);
	    for(col=0; col<window.cols; col++) {
		
		tmple=-1;
		for (rowb=0; rowb<window.rows; rowb++){
		    for (colb=0; colb<window.cols; colb++) {
			if (tutu[rowb+1][colb+1] >= tmple) {
			    if (abs(attribue[rowb+1][colb+1])<0.5) {
				tmple=tutu[rowb+1][colb+1];
				rowid[ii+1]=rowb;
				colid[ii+1]=colb;
			    }
			}
		    }
		}
		attribue[rowid[ii+1]+1][colid[ii+1]+1]=1;
		ii++;
	    }
	}

	/* set the levels of the corresponding home range */
	G_message(_("\nOutput"));
	cumsu=0;
	for (i=0; i < ii; i++) {
	    if (cumsu<0.9999999) {
		cumsu+=tutu[rowid[i+1]+1][colid[i+1]+1];
	    } else {
		cumsu=1;
	    }
	    tutu[rowid[i+1]+1][colid[i+1]+1]=cumsu;
	    
	}
	
	
	/* output */
	for(row=0; row<window.rows; row++){
	    for(col=0; col<window.cols; col++) {
		output_cell[col] = tutu[row+1][col+1];
	    }
	    G_put_raster_row(fdout,output_cell,DCELL_TYPE);
	}
	
	G_close_cell(fdout);
	
    }
    
    
    Vect_close (&In);
    freetab(tutu);
    freetab(attribue);
    freeintvec(rowid);
    freeintvec(colid);
    exit(0);
}


/* Read points to array return number of points */
int read_points( struct Map_info *In, double ***coordinate)
{
  int    line, nlines, npoints, ltype, i = 0;
  double **xySites;
  static struct line_pnts *Points = NULL;
  
  if (!Points)
      Points = Vect_new_line_struct ();
  
  /* Allocate array of pointers */
  npoints = Vect_get_num_primitives(In,GV_POINT);
  xySites = (double **) G_calloc ( npoints, sizeof(double*) );
  
  nlines = Vect_get_num_lines(In);

  for ( line = 1; line <= nlines; line++){
      ltype = Vect_read_line (In, Points, NULL, line);
      if ( !(ltype & GV_POINT ) ) continue;
      
      xySites[i] = (double *)G_calloc((size_t)2, sizeof(double));
      
      xySites[i][0] = Points->x[0];
      xySites[i][1] = Points->y[0]; 
      i++;
  }	

  *coordinate = xySites;

  return (npoints);
}


/* Calculate distances < dmax between all sites in coordinate 
 * Return: number of distances in dists */
double compute_all_distances(double **coordinate, double **dists, int n, double dmax)
{
  int ii,jj,kk;
  size_t nn;

  nn = n*(n-1)/2;
  *dists = (double *) G_calloc(nn,sizeof(double));  
  kk=0;

  for(ii=0; ii < n-1; ii++){
    for(jj=ii+1; jj<n; jj++){
      double dist;

      dist = euclidean_distance(coordinate[ii],coordinate[jj],2);
      G_debug (3, "dist = %f", dist);

      if ( dist <= dmax ) {
          (*dists)[kk] = dist;
	  kk++;
      }
    }
  }

  return (kk);
}



void compute_distance( double N, double E, struct Map_info *In, 
	               double sigma, double term, double *gaussian, double dmax)
{  
  int    line, nlines;
  double a[2],b[2];
  double dist;

  /* spatial index handling, borrowed from lib/vector/Vlib/find.c */
  BOUND_BOX box; 
  static struct ilist *NList = NULL;  
  static struct line_pnts *Points = NULL;

  a[0] = E;
  a[1] = N;

  if (!NList) 
    NList = Vect_new_list (); 
  if (!Points)
      Points = Vect_new_line_struct ();

  /* create bounding box 2x2*dmax size from the current cell center */
  box.N = N + dmax;
  box.S = N - dmax;
  box.E = E + dmax;
  box.W = E - dmax;
  box.T = HUGE_VAL;
  box.B = -HUGE_VAL;

  /* number of lines within dmax box  */
  nlines = Vect_select_lines_by_box (In, &box, GV_POINT, NList);

  *gaussian=.0;  
  
  for ( line = 0; line < nlines; line++ ) { 

    Vect_read_line (In, Points, NULL, NList->value[line]); 

    b[0] = Points->x[0];
    b[1] = Points->y[0];

    dist = euclidean_distance(a,b,2); 
      
    if(dist<=dmax) 
    *gaussian += gaussianKernel(dist/sigma,term);
   
  }
}




