#include "local_proto.h"

/* experimental variogram 
 * based on  2D variogram (alghalandis.com/?page_id=463)) */
void E_variogram(int type, struct int_par *xD, struct points *pnts, struct pcl_utils *pclp, struct var_par *pars)
{
  // Variogram type
  struct parameters *var_par, *var_par_vert;
  pcl::PointCloud<pcl::PointXYZ>::Ptr pcl_pnts;
  switch (type) {
  case 0:
    var_par = &pars->hz;
    pcl_pnts = pclp->pnts_hz;
    break;
  case 1:
    var_par = &pars->vert;
    pcl_pnts = pclp->pnts_vert;
    break;
  default:
    var_par = &pars->fin;
    pcl_pnts = pclp->pnts;
    break;  
  }

  // Local variables
  int n = pnts->n; // # of input points
  double *r;       // xyz coordinates of input points
  double *vals = pnts->invals; // values to be used for interpolation
  int phase = xD->phase;
  int function = var_par->function; // type of theoretical variogram

  int nLag = var_par->nLag;       // # of horizontal bins
  int nLag_vert;
  double *vert;
  double dir = var_par->dir; // azimuth
  double td = var_par->td;   // angle tolerance
  double lag = var_par->lag; // size of horizontal bin
  double lag_vert;

  /*switch (type) {
  case 1:
    td = var_par->tz; 
    break; 
  case 2:
    td = var_par->horizontal->td; 
    tz = var_par->vertical->td; 
    break;
  default:
    td = var_par->td;
    break;
    }*/
 
  // depend on variogram type: 
  int k; // index of variogram to be computed
  int nrows = nLag;

  double max_dist = var_par->max_dist; // max distance of interpolated points
  double radius = SQUARE(max_dist); // radius of interpolation in the horizontal plane
  struct write *report = &xD->report;

  if (type == 2) {
    nLag_vert = var_par->nLag_vert;       // # of horizontal bins
    lag_vert = var_par->lag_vert;  // size of horizontal bin
  }

  int ncols = type == 2 ? nLag_vert : 1;
        
  // Variogram processing variables
  int s; // index of horizontal segment
  int b; // index of verical segment (bivariate only)
  int i, j; // indices of the input points
  int err0=0; // number of invalid values

  double *dr;   // coordinate differences of each couple
  double *h;    // distance of boundary of the horizontal segment
  double tv;    // bearing of the line between the couple of the input points
  double ddir;  // the azimuth of computing variogram
  double rv;    // radius of the couple of points
  double drv;   // distance between the points
  double rvh;   // difference between point distance and the horizontal segment boundary
  double dv;    // difference of the values to be interpolated that are located on the couple of points

  double *i_vals, *j_vals; // values located on the point couples

  int n1 = n+1; // number of points + 1
  pcl::KdTreeFLANN<pcl::PointXYZ>::Ptr kd_tree (new pcl::KdTreeFLANN<pcl::PointXYZ>);

  pcl::PointXYZ *searchPt;         // search point (each input point)
  std::vector<int> ind;            // vector of indices
  std::vector<float> sqDist;
  int n_ind;      // number of elements (including 1st irrelevant)
  int *indices;   // save indices into matrix to use them later
  int *idx;       // index to be set (output)
  int *ii, *i0;   // difference of indices between rellevant input points
  int *ip;        // index to be set into the index matrix (input)
  
  double gamma_sum; // sum of dissimilarities in one bin
  double cpls;      // # of dissimilarities in one bin
  double gamma_E;   // average of dissimilarities in one bin (element of gamma matrix)
  mat_struct *gamma_temp; // gamma matrix (hz, vert or bivar)
  mat_struct *c_temp;     // matrix of # of dissimilarities
  double *gamma; // pointer to gamma matrix
  double *c;     // pointer to c matrix

  unsigned int percents = 50;
  int counter;
  int count;

  double gamma_stat; // sum of gamma elements (non-nan)
  int gamma_n;       // # of gamma elements (non-nan)
  double gamma_sill; // sill

  double nugget, sum_nugget = 0.;
  int n_nugget = 0;
 
  /* Allocated vertices and matrices:
   * --------------------------------
   * dr - triple of coordinate differences (e.g. dx, dy, dz)
   * h - vector of length pieces [nL x 1]
   * vert - vector of vertical pieces [nZ x 1] (3D only)
   * c - matrix containing number of points in each sector defined by h (and vert) [nL x nZ; in 2D nZ = 1]
   * gama - matrix of values of experimental variogram
  */

  // allocate:
  dr = (double *) G_malloc(3 * sizeof(double));   // vector of coordinate differences
  var_par->h = (double *) G_malloc(nLag * sizeof(double)); // vector of bins

  if (type == 2) {
    var_par->vert = (double *) G_malloc(nLag_vert * sizeof(double)); // vector of bins
  }

  // control initialization:
  if (dr == NULL || var_par->h == NULL || (type == 2 && var_par->vert == NULL)) {
    if (xD->report.write2file == TRUE) { // close report file
      fprintf(xD->report.fp, "Error (see standard output). Process killed...");
      fclose(xD->report.fp);
    }
    G_fatal_error(_("Memory allocation failed..."));
  }
  
  r = &pnts->r[0];  // set up pointer to input coordinates
  indices = (int *) G_malloc(n1*n * sizeof(int)); // matrix of indices of neighbouring points
  if (indices == NULL) {
    if (xD->report.write2file == TRUE) { // close report file
      fprintf(xD->report.fp, "Error (see standard output). Process killed...");
      fclose(xD->report.fp);
    }
    G_fatal_error(_("Memory allocation failed..."));
  }

  kd_tree->setInputCloud(pcl_pnts);
  searchPt = &pcl_pnts->points[0];
      
  // initialize:
  c_temp = G_matrix_init(nrows, ncols, nrows);     // temporal matrix of counts
  gamma_temp = G_matrix_init(nrows, ncols, nrows); // temporal matrix (vector) of gammas

  if (c_temp == NULL || gamma_temp == NULL) {
    if (xD->report.write2file == TRUE) { // close report file
      fprintf(xD->report.fp, "Error (see standard output). Process killed...");
      fclose(xD->report.fp);
    }
    G_fatal_error(_("Memory allocation failed..."));
  }
  
  // set up pointers
  c = &c_temp->vals[0];
  gamma = &gamma_temp->vals[0];

  // set up starting values
  gamma_stat = 0.; // 
  gamma_n = 0; //

  if (percents) {
    G_percent_reset();
  }
  counter = nrows * ncols;
  count = 0;

  if (type == 2) {
    vert = &var_par->vert[0]; 
  }

  for (b = 0; b < ncols; b++) {
    if (type == 2) {
      *vert = (b+1) * lag_vert;
    }
   
    // set up vector of distances...
    h = &var_par->h[0]; // ... horizontal

    for (s = 0; s < nrows; s++) { // process of the horizontal piece (isotrophy!!!)
      *h = (s+1) * lag; // distance of horizontal lag
          	    
      // for every bs cycle ...
      i_vals = &vals[0]; // ... i-vals start at the beginning 
      gamma_sum = 0.;    // gamma in dir direction and h distance
      cpls = 0.;         // count of couples in dir direction and h distance

      /* Compute variogram for points in relevant neighbourhood */
      for (i = 0; i < n-1; i++) { // for every input point...
	if (b == 0 && s == 0) { // ... create vector of points in neighborhood
	  if (kd_tree->radiusSearch(*searchPt, max_dist, ind, sqDist) > 0) {
	    n_ind = ind.size (); // size of indices to 1st row
	    ip = &ind.data ()[1]; // values of indices to the next rows
	    idx = &indices[n1*i]; // begin new column
	    *idx = n_ind-1; // size of index vector as 1st element of row
	    for (j = 1; j < n_ind; j++) {
	      idx++; // next row
	      *idx = *ip; // set indices to the rest of the rows
	      ip++; // next index
	    } // end setting elements
	  } // end radiusSearch
	  else {
	    if (report->write2file == TRUE) { // close report file
	      fprintf(report->fp, "Error (see standard output). Process killed...");
	      fclose(report->fp);
	    }
	    G_fatal_error(_("There are no points in the surrounding of point no. %d..."), i);
	  } // end error
	  searchPt++; // next search point
	} // end set up indices
	  
	idx = &indices[n1*i]; // ... new column of matrix is attached 
	ii = &indices[n1*i+1];
	i0 = &indices[n1*i+1];
	n_ind = *idx; // number of neighbouring points
	
	j_vals = &vals[*ii];
	for (j = 1; j < n_ind; j++) { // points within searchRadius
	  if (*ii > i) {
	    coord_diff(i, *ii, r, dr); // coordinate differences 
     
	    /* Variogram processing */
	    if (type == 1) { // in case of vertical variogram...
	      tv = 0.5 * PI - atan2(dr[2], sqrt(SQUARE(dr[0]) + SQUARE(dr[1]))); // ... compute zenith angle instead of bearing
	      td = 0.5 * PI; // 0.25 usually
	    }
	    else
	      tv = atan2(*(dr+1), *dr); // bearing
	      
	    ddir = tv - dir;   // difference between bearing and azimuth
	    if (fabsf(ddir) <= td) { // is the difference acceptable according to tolerance?
	      // test distance
	      rv = type == 1 ? 0. : SQUARE(dr[0]) + SQUARE(dr[1]); // horizontal distance
	      if (type == 1 || type == 3) { // anisotropic only
		rv += SQUARE(dr[2]); // vertical or anisotropic distance
	      }
	      rvh = sqrt(rv) - *h;   // difference between distance and lag
	      if (rv <= radius && 0. <= rvh && rvh <= lag) { // distance test
		if (type == 2) { // vertical test for bivariate variogram
		  rvh = *(dr+2) - *vert;
		  if (fabsf(rvh) <= lag_vert) { // elevation test
		    goto delta_V;
		  }
		  else {
		    goto end;
		  }
		}
	      delta_V:
		dv = *j_vals - *i_vals; // difference of values located on pair of points i, j
		gamma_sum += dv * dv;   // sum of squared differences
		cpls += 1.; // count of elements
	      } // end distance test
	    } // end bearing test
	    //} // end dr2 test
	  } // end point selection
	end:
	  *i0 = *ii;
	  ii++;
	  j_vals += *ii - *i0;
	} // end j
	i_vals++;
      } // end i
      
      if (isnan(gamma_sum) || cpls == 0.0) {
	err0++;
	goto gamma_isnan;
      }

      gamma_E = 0.5 * gamma_sum / cpls; // element of gamma matrix     
      *c = cpls; // # of values that have been used to compute gamma_e
      *gamma = gamma_E;

      gamma_stat += gamma_E; // sum of gamma elements (non-nan)
      gamma_n++; // # of gamma elements (non-nan)

    gamma_isnan:
      h++;
      c++;
      gamma++;
      count++;
    } // end s

    if (type == 2) {
      vert++;
    }
  } // end b

  free(indices);
   
  if (err0 == nLag) { // todo> kedy nie je riesitelny teoreticky variogram?
    if (report->write2file == TRUE) { // close report file
      fprintf(report->fp, "Error (see standard output). Process killed...");
      fclose(report->fp);
    }
    G_fatal_error(_("Unable to compute experimental variogram...")); 
  } // end error

  var_par->gamma = G_matrix_copy(gamma_temp);
  var_par->c = G_matrix_copy(c_temp);
  plot_experimental_variogram(xD, var_par->h, gamma_temp, var_par);

  if (report->name) {  
    write2file_variogram_E(xD, var_par);
  }
      
  // Compute sill
  if (phase < 2) {
    switch (type) {
    case 2:
      int nh, nv;
      double c_h, c_v, gamma_h, gamma_v; 
      char type[12];
      nh = nv = 0;
      gamma_h = gamma_v = 0.;

      for (i=0; i<nrows; i++) {
	c_h = G_matrix_get_element(c_temp, i, 0);
	if (c_h != 0.) {
	  gamma_h += G_matrix_get_element(gamma_temp, i, 0);
	  nh++;
	}
      }

      for (j=0; j<ncols; j++) {	  
	c_v = G_matrix_get_element(c_temp, 0, j);
	if (c_v != 0.) {
	  gamma_v += G_matrix_get_element(gamma_temp, 0, j);
	  nv++;
	}
      }

      var_par->horizontal.sill = gamma_h / nh;
      var_par->vertical.sill = gamma_v / nv;
      break;

    default:
      var_par->sill = gamma_stat / gamma_n; // mean of gamma elements
      
      variogram_type(var_par->type, type);
      G_message(_("Default sill of %s variogram: %f"), type, var_par->sill);
      break;
    }
  } // end compute sill

  write_temporary2file(xD, var_par, gamma_temp);
     
  G_matrix_free(c_temp);
  G_matrix_free(gamma_temp);
}

/* theoretical variogram */
void T_variogram(int type, struct opts opt, struct parameters *var_par, struct write *report)
{
  // report
  if (report->name) {
    time(&report->now);
    if (type != 1) {
      fprintf(report->fp, "\nComputation of theoretical variogram started on %s\n", ctime(&report->now));    
    }  
  }

  // set up:
  var_par->type = type;
        
  char *variogram;
  switch (type) {
  case 0: // horizontal
    var_par->nugget = atof(opt.nugget_hz->answer);
    var_par->h_range = atof(opt.range_hz->answer);
    if (opt.sill_hz->answer) {
      var_par->sill = atof(opt.sill_hz->answer);
    }
    variogram = opt.function_var_hz->answer;
    if (report->name) {
      fprintf(report->fp, "Parameters of horizontal variogram:\n");
      fprintf(report->fp, "Nugget effect: %f\n", var_par->nugget);
      fprintf(report->fp, "Sill:          %f\n", var_par->sill);
      fprintf(report->fp, "Range:         %f\n", var_par->h_range);
    }
    break;
  case 1: // vertical
    var_par->nugget = atof(opt.nugget_vert->answer);
    var_par->h_range = atof(opt.range_vert->answer);
    if (opt.sill_vert->answer) {
      var_par->sill = atof(opt.sill_vert->answer);
    }
    variogram = opt.function_var_vert->answer;
    if (report->name) {
      fprintf(report->fp, "Parameters of vertical variogram:\n");
      fprintf(report->fp, "Nugget effect: %f\n", var_par->nugget);
      fprintf(report->fp, "Sill:          %f\n", var_par->sill);
      fprintf(report->fp, "Range:         %f\n", var_par->h_range);
    }
    break;
  case 2: // bivariate variogram
    if (opt.function_var_hz->answer == NULL && opt.function_var_vert->answer == NULL) { // linear function
      int nZ, nL, nr, i, j, nc;
      double *h, *vert, *gamma, *c;
      mat_struct *gR;

      var_par->function = 5;

      nL = var_par->gamma->rows; // # of cols (horizontal bins)
      nZ = var_par->gamma->cols; // # of rows (vertical bins)
      gamma = &var_par->gamma->vals[0]; // pointer to experimental variogram
      c = &var_par->c->vals[0];
  
      // Test length of design matrix
      nr = 0; // # of rows of design matrix A - depend on # of non-nan gammas
      for (i = 0; i < nZ; i++) {
	for (j = 0; j < nL; j++) {
	  if (*c != 0.) { // todo: upgrade: !isnan(*c) L434 too
	    nr++;
	  }
	  gamma++;
	  c++;
	} // end j
      } // end i
    
      // Number of columns of design matrix A
      nc = var_par->function == 5 ? 3 : 2; 

      var_par->A = G_matrix_init(nr, nc, nr); // initialise design matrix
      gR = G_matrix_init(nr, 1, nr); // initialise vector of observations
  
      // Set design matrix A
      nr = 0; // index of matrix row
      gamma = &var_par->gamma->vals[0]; // pointer to experimental variogram
      c = &var_par->c->vals[0];
  
      if (var_par->function == 5) { // in case of bivariate variogram
	vert = &var_par->vert[0]; // use separate variable for vertical direction
      }

      for (i = 0; i < nZ; i++) {
	h = &var_par->h[0];
	for (j = 0; j < nL; j++) {
	  if (*c != 0.) { // write to matrix - each valid element of gamma
	    switch (var_par->function) { // function of theoretical variogram
	    case 5: // bivariate planar
	      G_matrix_set_element(var_par->A, nr, 0, *h);
	      G_matrix_set_element(var_par->A, nr, 1, *vert);
	      G_matrix_set_element(var_par->A, nr, 2, 1.);
	      G_matrix_set_element(gR, nr, 0, *gamma);
	      break;
	    default:
	      G_matrix_set_element(var_par->A, nr, 0, *h);
	      G_matrix_set_element(var_par->A, nr, 1, 1.);
	      G_matrix_set_element(gR, nr, 0, *gamma);
	      break;
	    } // end switch variogram fuction
	    nr++; // length of vector of valid elements (not null)		
	  } // end test if !isnan(*gamma)
	  h++;
	  gamma++;
	  c++;
	} // end j
	if (var_par->function == 5) {
	  vert++;
	}
      } // end i
    end_loop:

      // Estimate theoretical variogram coefficients 
      var_par->T = LSM(var_par->A, gR); // Least Square Method
      
      // Test of theoretical variogram estimation 
      if (var_par->T->vals == NULL) { // NULL values of theoretical variogram
	if (report->write2file == TRUE) { // close report file
	  fprintf(report->fp, "Error (see standard output). Process killed...");
	  fclose(report->fp);
    }
	G_fatal_error("Unable to compute 3D theoretical variogram..."); 
      } // error

      // constant raster
      G_debug(0,"%f %f %f", var_par->T->vals[0], var_par->T->vals[1], var_par->T->vals[2]);
      if (var_par->T->vals[0] == 0. && var_par->T->vals[1] == 0.) { //to do: otestuj pre 2d
	var_par->const_val = 1;
	G_message(_("Input values to be interpolated are constant."));
      } // todo: cnstant raster for exponential etc.
      else {
	var_par->const_val = 0;
      }

      // coefficients of theoretical variogram (linear)
      if (report->name) {
	fprintf(report->fp, "Parameters of bivariate variogram:\n");
	fprintf(report->fp, "Function: linear\n\n");
	fprintf(report->fp, "gamma(h, vert) = %f * h + %f * vert + c\n", var_par->T->vals[0], var_par->T->vals[1], var_par->T->vals[2]);
      }
    }

    else {
      var_par->horizontal.nugget = atof(opt.nugget_hz->answer);
      var_par->horizontal.h_range = atof(opt.range_hz->answer);
      //var_par->horizontal.variogram = opt.variogram_hz->answer;
      if (opt.sill_hz->answer) {
	var_par->horizontal.sill = atof(opt.sill_hz->answer);
      }

      var_par->vertical.nugget = atof(opt.nugget_vert->answer);
      var_par->vertical.h_range = atof(opt.range_vert->answer);
      //var_par->vertical.variogram = opt.variogram_vert->answer;
      if (opt.sill_hz->answer) {
	var_par->vertical.sill = atof(opt.sill_vert->answer);
      }

      var_par->horizontal.function = set_function(opt.function_var_hz->answer, var_par, report);
      var_par->vertical.function = set_function(opt.function_var_vert->answer, var_par, report);

      if (report->name) {
	fprintf(report->fp, "Parameters of bivariate variogram:\n");
	fprintf(report->fp, "Nugget effect (hz):   %f\n", var_par->horizontal.nugget);
	fprintf(report->fp, "Sill (hz):            %f\n", var_par->horizontal.sill);
	fprintf(report->fp, "Range (hz):           %f\n", var_par->horizontal.h_range);
	fprintf(report->fp, "Function: %s\n\n", opt.function_var_hz->answer);
	fprintf(report->fp, "Nugget effect (vert): %f\n", var_par->vertical.nugget);
	fprintf(report->fp, "Sill (vert):          %f\n", var_par->vertical.sill);
	fprintf(report->fp, "Range (vert):         %f\n", var_par->vertical.h_range);
	fprintf(report->fp, "Function: %s\n", opt.function_var_vert->answer);
      }
    }

    plot_var(TRUE, var_par->h, var_par->gamma, var_par); // Plot variogram using gnuplot
    break;
  case 3: // anisotropic
    var_par->nugget = atof(opt.nugget_final->answer);
    var_par->h_range = atof(opt.range_final->answer);
    if (opt.sill_final->answer) {
      var_par->sill = atof(opt.sill_final->answer);
    }
    variogram = opt.function_var_final->answer;
    if (report->name) {
      fprintf(report->fp, "Parameters of anisotropic variogram:\n");
      fprintf(report->fp, "Nugget effect: %f\n", var_par->nugget);
      fprintf(report->fp, "Sill:          %f\n", var_par->sill);
      fprintf(report->fp, "Range:         %f\n", var_par->h_range);
    }
    break;
  }

  if (type != 2) {
    var_par->function = set_function(variogram, var_par, report);
    plot_var(FALSE, var_par->h, var_par->gamma, var_par); // Plot variogram using gnuplot
  }
}

void ordinary_kriging(struct int_par *xD, struct reg_par *reg, struct points *pnts, struct pcl_utils *pclp, struct var_par *pars, struct output *out)
{
  // Local variables
  int n = pnts->n;
  double *r = pnts->r;          // xyz coordinates of input poinst
  double *vals = pnts->invals;  // values to be used for interpolation
  struct write *report = &xD->report;
  struct write *crossvalid = &xD->crossvalid;
  struct parameters *var_par;
  pcl::PointCloud<pcl::PointXYZ>::Ptr pcl_pnts;
  double ratio;

  var_par = &pars->fin;
  pcl_pnts = pclp->pnts;
  ratio = var_par->type == 3 ? xD->aniso_ratio : 1.;
       
  unsigned int passed=0;      // number of successfully interpolated valuesy
  unsigned int percents=50;   // counter
  unsigned int nrcd;          // number of cells/voxels
  unsigned int row, col, dep; // indices of cells/voxels
  double rslt_OK;     // interpolated value located on r0

  int i, j;
  unsigned int n1;
  double *r0;         // xyz coordinates of cell/voxel centre
  mat_struct *GM;
  mat_struct *GM_sub; // submatrix of the points that are rellevant to the interpolation due the distance
  mat_struct *GM_Inv; // inverted GM (GM_sub) matrix
  mat_struct *g0;     // vector of diffences between known and unknown values estimated using distances and the theoretical variogram
  mat_struct *w0;     // weights of values located on the input points 

  // Cell/voxel center coords (location of interpolated value)
  r0 = (double *) G_malloc(3 * sizeof(double));   
  pcl::KdTreeFLANN<pcl::PointXYZ> kd_tree;
  kd_tree.setInputCloud(pcl_pnts); // Set up kd-tree
  pcl::PointXYZ cellCent;
  std::vector<int> ind;
  std::vector<float> sqDist;
  
  double radius;
  FILE *fp;

  if (report->name) {
    report->write2file = TRUE;
    report->fp = fopen(report->name, "a");
    time(&report->now);
    fprintf(report->fp, "Interpolating values started on %s\n\n", ctime(&report->now));
  }

  G_message(_("Interpolating unknown values..."));
  if (percents) {
    G_percent_reset();
  }

  open_layer(xD, reg, out); // open 2D/3D raster

  if (var_par->const_val == 1) {
    goto constant_voxel_centre;
  }
  
  radius = var_par->max_dist;

  GM = set_up_G(pnts, var_par, &xD->report);
  var_par->GM = G_matrix_copy(GM);
  if (n < 1000) {
    GM_Inv = G_matrix_inverse(GM);
  }

  if (crossvalid->name) {
    crossvalidation(xD, pnts, pcl_pnts, var_par);
  }
  
  constant_voxel_centre:
  for (dep=0; dep < reg->ndeps; dep++) {
    if (xD->i3 == TRUE) {
      if (percents) {
	G_percent(dep, reg->ndeps, 1);
      }
    }
    for (row=0; row < reg->nrows; row++) {
      if (xD->i3 == FALSE) {
	if (percents) {
	  G_percent(row, reg->nrows, 1);
	}
      }
      //#pragma omp parallel for private(col, r0, cellCent, ind, sqDist, n1, GM, GM_Inv, g0, w0, rslt_OK)
      for (col=0; col < reg->ncols; col++) {
	
	if (var_par->const_val == 1) {
	  goto constant_voxel_val;
	}

	cell_centre(col, row, dep, xD, reg, r0, var_par); // Output point
	if (n < 1000)
	  goto small_sample;

	cellCent.x = *r0;
	cellCent.y = *(r0+1);
	cellCent.z = *(r0+2); // if 2D: 0.
	
	if (kd_tree.radiusSearch(cellCent, radius, ind, sqDist) > 0 ) { 
	  GM_sub = submatrix(ind, GM, report);
	  GM_Inv = G_matrix_inverse(GM_sub);
	  G_matrix_free(GM_sub);

	small_sample:
	  g0 = set_up_g0(xD, ind, pnts, r0, var_par); // Diffs inputs - unknowns (incl. cond. 1))
	  w0 = G_matrix_product(GM_Inv, g0); // Vector of weights, condition SUM(w) = 1 in last row
	
	  if (n >= 1000) {
	    G_matrix_free(GM_Inv); 
	    G_matrix_free(g0);
	  }

	  rslt_OK = result(ind, pnts, w0); // Estimated cell/voxel value rslt_OK = w x inputs
	  //if (pnts->trend != NULL) {
	    /* normal gravity:  rslt_OK += pnts->trend->vals[0] * r0[0] + pnts->trend->vals[1] * r0[0]*r0[1]*r0[2]/ratio + pnts->trend->vals[2] * r0[0]*r0[1] + pnts->trend->vals[3] * r0[0]*r0[2]/ratio + pnts->trend->vals[4] * r0[1]*r0[2]/ratio + pnts->trend->vals[5] * r0[2]/ratio + pnts->trend->vals[6];*/
	  //}

	  // Create output
	constant_voxel_val:
	  if (xD->const_val == 1)
	    rslt_OK = (double) *vals;
	  if (write2layer(xD, reg, out, col, row, dep, rslt_OK) == 0) {
	    if (report->name) { // close report file
	      fprintf(report->fp, "Error (see standard output). Process killed...");
	      fclose(report->fp);
	    }
	    G_fatal_error(_("Error writing result into output layer..."));
	  }
	} // end if searchRadius
	else {
	  if (report->name) { // close report file
	    fprintf(report->fp, "Error (see standard output). Process killed...");
	    fclose(report->fp);
	  }
	  G_fatal_error(_("This point does not have neighbours in given radius..."));
	}
      } // end col
    } // end row 
  } // end dep

  if (report->name) {
    fprintf(report->fp, "\n************************************************\n\n");    
    time(&report->now);
    fprintf(report->fp, "v.kriging completed on %s", ctime(&report->now));
    fclose(report->fp);
  }

  switch (xD->i3) {
  case TRUE:
    Rast3d_close(out->fd_3d); // Close 3D raster map
    break;
  case FALSE:
    Rast_close(out->fd_2d); // Close 2D raster map
    break;
  }     
}

