#include "local_proto.h"

#define GNUPLOT "gnuplot -persist"

// make coordinate triples xyz
double *triple(double x, double y, double z)
{
  double *t;
  t = (double *) G_malloc(3 * sizeof(double));

  *t = x;
  *(t+1) = y;
  *(t+2) = z;
  
  return t;
}

// compute coordinate differences
void coord_diff(int i, int j, double *r, double *dr)
{
  int k=3*i,l=3*j;
  double *rk, *rl, zi, zj, *drt;
 rk = &r[k];
  rl = &r[l];
  drt = &dr[0];

  if (*rk == 0. && *(rk+1) == 0. && *(rk+2) == 0.)
    G_fatal_error(_("Coordinates of point no. %d are zeros."),i);

  *drt = *rl - *rk; // dx
  *(drt+1) = *(rl+1) - *(rk+1); // dy
  *(drt+2) = *(rl+2) - *(rk+2); // dz
}

// compute horizontal radius from coordinate differences
double radius_hz_diff(double *dr)
{
  double rds;
  rds = SQUARE(dr[0]) + SQUARE(dr[1]);
  return rds;
}

// compute size of the lag
double lag_distance(int direction, struct points *pnts, pcl::PointCloud<pcl::PointXYZ>::Ptr pcl_pnts, struct parameters *var_par, struct write *report)
{
  int n = pnts->n;     // # of input points
  double *r = pnts->r; // xyz of input points
  int fction = var_par->function;
  double max_dist = (var_par->type == 2 && direction == 3) ? var_par->max_dist_vert : var_par->max_dist; // maximum horizontal distance

  int i, j, k;
  pcl::PointXYZ *searchPt;
  searchPt = &pcl_pnts->points[0];

  pcl::KdTreeFLANN<pcl::PointXYZ>::Ptr kd_tree (new pcl::KdTreeFLANN<pcl::PointXYZ>);
  kd_tree->setInputCloud(pcl_pnts);

  std::vector<int> ind;      // indices of NN
  std::vector<float> sqDist; // sqDistances of NN

  double dr[3];       // coordinate differences
  double quant_dist2 = var_par->radius; // quantile
  double lagNN;       // squared quantile - lag
  double *dist2, *d;  // radius
  dist2 = (double *) G_malloc(n * sizeof(double));
  d = &dist2[0];

  int perc5, zeros;
  int nN;
  perc5 = (int) round(0.05 * n);
  double dist0;
  int j0 = 0;
  
  for (i=0; i < n; i++) {
    zeros = 0;  // # of zero distances
    dist0 = 0.; // initial value of 5% distance
    while (dist0 != 0.) { // while 5% distance is zero
      perc5 += zeros; // 5% plus points in zero distance
      // find 5% nearest points
      if (kd_tree->nearestKSearch(*searchPt, perc5, ind, sqDist) > 0) {       
	j = ind.size () - 1; // store index of 5%-th point
	dist0 = sqDist.data ()[j]; // 5% distance

	zeros = 0; // count zero distances
	for (k=j0; k <= j; k++) {	
	  if (sqDist.data ()[k] == 0.)
	    zeros++;
	}

	if (zeros > 0) {
	  dist0 = 0.;
	  j0 = j+1;
	}    
      } // end nearestKSearch
 
      else {
	if (report->write2file == TRUE) { // close report file
	  fprintf(report->fp, "Error (see standard output). Process killed...");
	  fclose(report->fp);
	}
	G_fatal_error(_("Error searching nearest neighbours of point %d..."), i);
      } // end error
    } // end while dist0 == 0

    coord_diff(i, j, r, dr); // coordinate differences
      
    // squared distance
    switch (direction) {
    case 12: // horizontal
      *d = SQUARE(dr[0]) + SQUARE(dr[1]);
      break;
    case 3:  // vertical
      *d = SQUARE(dr[2]);
      break;
    case 0:  // all
      *d = SQUARE(dr[0]) + SQUARE(dr[1]) + SQUARE(dr[2]);
      break;
    }
    if (*d != 0.)
      quant_dist2 = MIN(quant_dist2, *d);
    d++;
    searchPt++;
  }

  lagNN = sqrt(quant_dist2);
 
  return lagNN;
}

double linear(double x, double a, double b)
{
  double y;
  y = a * x + b;

  return y;
}

double exponential(double x, double nugget, double part_sill, double h_range)
{
  double y;
  y = nugget + part_sill * (1. - exp(- 3. * x/h_range)); // practical

  return y; 
}

double spherical(double x, double a, double b, double c)
{
  double y;
  double ratio;
  if (x < c) {
    ratio = x / c;
    y = a + b * (1.5 * ratio - 0.5 * POW3(ratio));
  }
  else
    y = a + b;

  return y;
}

double gaussian(double x, double a, double b, double c)
{
  double y;
  double c2 = SQUARE(c);
  double ratio;
  ratio = x / c2;
  y = a + b * (1 - exp(-3. * ratio));

  return y;
}

// compute # of lags
int lag_number(double lag, double *varpar_max)
{
  int n; // number of lags
  n = (int) round(*varpar_max / lag); // compute number of lags
  *varpar_max = n * lag; // set up modified maximum distance (to not have empty lags)
 
  return n;
}

// maximal horizontal and vertical distance to restrict variogram computing
void variogram_restricts(struct int_par *xD, struct points *pnts, pcl::PointCloud<pcl::PointXYZ>::Ptr pcl_pnts, struct parameters *var_par)
{
  int n = pnts->n;     // # of points
  double *r = pnts->r; // xyz of points
  struct write *report = &xD->report;
  
  int i;
  double *min, *max;   // extend
  double dr[3]; // coordinate differences
  double h_maxG; // modify maximum distance (to not have empty lags)

  char type[12];
  variogram_type(var_par->type, type);

  // Find extent
  G_message(_("Computing %s variogram properties..."), type);
  min = &pnts->r_min[0]; // set up pointer to minimum xyz
  max = &pnts->r_max[0]; // set up pointer to maximum xyz

  dr[0] = *max - *min;         // x range
  dr[1] = *(max+1) - *(min+1); // y range
  dr[2] = *(max+2) - *(min+2); // z range

  switch (var_par->type) {
  case 1:
    var_par->max_dist = dr[2]; // zmax - zmin
    var_par->radius = SQUARE(var_par->max_dist); // anisotropic distance (todo: try also dz)
    break;
  default:
    var_par->radius = radius_hz_diff(dr) / 9.; // horizontal radius (1/9)
    var_par->max_dist = sqrt(var_par->radius);   // 1/3 max horizontal dist (Surfer, Golden SW)
    break;
  }
  
  if (report->name)
    write2file_varSetsIntro(var_par->type, report);

  int dimension;
  switch (var_par->type) {
  case 0:
    dimension = 12;
    break;
  case 1:
    dimension = 3;
    break;
  case 3:
    dimension = 0;
    break;
  }

  if (var_par->type == 2) {
    var_par->lag = lag_distance(12, pnts, pcl_pnts, var_par, report);  // the shortest distance between NN in horizontal direction
    var_par->nLag = lag_number(var_par->lag, &var_par->max_dist);
    var_par->max_dist = var_par->nLag * var_par->lag;

    var_par->lag_vert = lag_distance(3, pnts, pcl_pnts, var_par, report);  // the shortest distance between NN in horizontal direction
    var_par->nLag_vert = lag_number(var_par->lag_vert, &var_par->max_dist_vert);
    var_par->max_dist_vert = var_par->nLag_vert * var_par->lag_vert;
  }

  else {
    var_par->lag = lag_distance(dimension, pnts, pcl_pnts, var_par, report);  // the shortest distance between NN in horizontal direction
    var_par->nLag = lag_number(var_par->lag, &var_par->max_dist);
  }

  write2file_varSets(report, var_par);
}

void geometric_anisotropy(struct int_par *xD, struct points *pnts, pcl::PointCloud<pcl::PointXYZ>::Ptr pcl_pnts)
{
  int i;
  double ratio = xD->aniso_ratio;
  double *z;
  z = &pnts->r[2];

  for (i=0; i<pnts->n; i++) {
    *z = pcl_pnts->points[i].z = ratio * *z;
    z += 3;
  }  
}

// Least Squares Method
mat_struct *LSM(mat_struct *A, mat_struct *x)
{
  int i, nr, nc;
  mat_struct *AT, *ATA, *ATA_Inv, *ATx, *T;

  /* A[nr x nc] */
  nr = A->rows;
  nc = A->cols;

  /* LMS */
  AT = G_matrix_transpose(A);	/* Transposed design matrix */
  ATA = G_matrix_product(AT, A);	/* AT*A */
  ATA_Inv = G_matrix_inverse(ATA);	/* (AT*A)^-1 */
  ATx = G_matrix_product(AT, x);	/* AT*x */
  T = G_matrix_product(ATA_Inv, ATx);	/* theta = (AT*A)^(-1)*AT*x */

  return T;
}

mat_struct *nonlin_LMS(int n, double *dist, double *gamma)
{
  int i=0, j;
  double ctrl=1.;
  double a, b, c, mean_dy = 1., sum_dy, *h, *g, *add;
  mat_struct *y, *param, *param0, *J, *yf, *JT, *JTJ, *JT_Inv, *JTdy, *dy, *delta;
  y = G_matrix_init(n, 1, n);
  param = G_matrix_init(3, 1, 3);
  param0 = G_matrix_init(3, 1, 3);
  J = G_matrix_init(n, 3, n);
  yf = G_matrix_init(n, 1, n);

  // matrix of input elements
  g = &gamma[0];
  for (j=0; j<n; j++) {
    G_matrix_set_element(y, j, 0, *g);
    g++;
  }

  while (fabsf(mean_dy) >= 0.0001) {
    if (i==0) { // set initial parameters 
      G_matrix_set_element(param, 0, 0, 0.);
      G_matrix_set_element(param, 1, 0, 45.);
      G_matrix_set_element(param, 2, 0, 45.);      
    }
    a = param->vals[0];
    b = param->vals[1];
    c = param->vals[2];
    G_debug(0,"%d   a=%f b=%f c=%f", i, a, b, c);

    h = &dist[0];
    for (j=0; j<n; j++) {
      // Jacobi matrix
      // todo: rozdelit na variogramy    
      G_matrix_set_element(J, j, 0, 1.);  
      G_matrix_set_element(J, j, 1, 1. - exp(-3. * *h / c));
      G_matrix_set_element(J, j, 2, -3. * b * *h/SQUARE(c) * exp(-3. * *h*c));

      // f(a,b,c)
      G_matrix_set_element(yf, j, 0, b * (1. - exp(-3. * *h/c)));
      G_debug(0, "%f %f %f", G_matrix_get_element(J, j, 0), G_matrix_get_element(J, j, 1), G_matrix_get_element(J, j, 2));
      h++;
    }

    // differences
    dy = G_matrix_subtract(y, yf);
    sum_dy = 0.;
    add = &dy->vals[0];
    for (j=0; j<n; j++) {
      sum_dy += SQUARE(*add);
      add++;
    }
    mean_dy = sum_dy / n;
    G_debug(0,"%d    mean=%f", i, mean_dy);
    
    JT = G_matrix_transpose(J);
    JTJ = G_matrix_product(JT, J);
    JT_Inv = G_matrix_inverse(JTJ);
    JTdy = G_matrix_product(JT, dy);
    delta = G_matrix_product(JT_Inv, JTdy);
    G_debug(0,"a=%f b=%f c=%f", delta->vals[0], delta->vals[1], delta->vals[2]);

    param0 = G_matrix_copy(param);
    param = G_matrix_subtract(param0, delta);
    i++;
    if (i>3)
      G_fatal_error(_("stoj"));
  } 
  G_debug(0,"nugget=%f sill=%f range=%f", param->vals[0], param->vals[1], param->vals[2]);
  return param;
}

// set up type of function according to GUI (user)
int set_function(char *variogram, struct parameters *var_par, struct write *report)
{
  int function;
  if (strcmp(variogram, "linear") == 0) {
    function = 0;
    // var_par->bivar = FALSE;
  }
  else if (strcmp(variogram, "parabolic") == 0) {
    function = 1;
    //var_par->bivar = FALSE;
  }
  else if (strcmp(variogram, "exponential") == 0) {
    function = 2;
    // var_par->bivar = FALSE;
  }
  else if (strcmp(variogram, "spherical") == 0) {
    function = 3;
    //var_par->bivar = FALSE;
  }
  else if (strcmp(variogram, "gaussian") == 0) {
    function = 4;
    //var_par->bivar = FALSE;
  }
  else if (strcmp(variogram, "bivariate") == 0) {
    function = 5;
    //var_par->bivar = TRUE;
  }
  else {
    if (report->write2file == TRUE) { // close report file
      fprintf(report->fp, "Error (see standard output). Process killed...");
      fclose(report->fp);
    }
    G_fatal_error(_("Set up correct name of variogram function..."));
  }
  
  return function;
}

// set up terminal and format of output plot
void set_gnuplot(char *fileformat, struct parameters *var_par)
{
  if (strcmp(fileformat,"cdr") == 0) {
    strcpy(var_par->term, "corel");
    strcpy(var_par->ext, "cdr");
  }
  if (strcmp(fileformat,"dxf") == 0) {
    strcpy(var_par->term, "dxf");
    strcpy(var_par->ext, "dxf");
  }
  if (strcmp(fileformat,"eps") == 0) {
    strcpy(var_par->term, "postscript");
    strcpy(var_par->ext, "eps");
  }
  if (strcmp(fileformat,"pdf") == 0) {
    strcpy(var_par->term, "pdfcairo");
    strcpy(var_par->ext, "pdf");
  }
  if (strcmp(fileformat,"png") == 0) {
    strcpy(var_par->term, "png");
    strcpy(var_par->ext, "png");
  }
  if (strcmp(fileformat,"svg") == 0) {
    strcpy(var_par->term, "svg");
    strcpy(var_par->ext, "svg");
  } 
}

// plot experimental variogram
void plot_experimental_variogram(struct int_par *xD, double *h_exp, mat_struct *gamma_exp, struct parameters *var_par)
{
  int bivar = var_par->type == 2 ? TRUE : FALSE;
    
  int i, j;     // indices
  int nr, nc;   // # of rows, cols
  double *h;    // pointer to horizontal or anisotropic bins
  double *vert;
  double *gamma_var; // pointer to gamma matrix
  double *c; // pointer to number of elements
  FILE *gp; // pointer to file

  nr = gamma_exp->rows; // # of rows of gamma matrix
  nc = gamma_exp->cols; // # of cols of gamma matrix

  gamma_var = &gamma_exp->vals[0]; // values of gamma matrix
  c = &var_par->c->vals[0];
  
  gp = fopen("dataE.dat","w"); // open file to write experimental variogram
  if (gp == NULL)
    G_fatal_error(_("Error writing file"));

  /* 3D experimental variogram */  
  if (bivar == TRUE) {
    vert = &var_par->vert[0];
    for (i=0; i < nc+1; i++) {   // for each row (nZ)
      h = &var_par->h[0];
      for (j=0; j < nr+1; j++) { // for each col (nL)
	if (i == 0 && j == 0)
	  fprintf(gp, "%d ", nr); // write to file count of columns
	else if (i == 0 && j != 0) { // 1st row
	  fprintf(gp, "%f", *h); // write h to 1st row of the file
	  h++;
	  if (j < nr)
	    fprintf(gp, " "); // spaces between elements	  
	} // end 1st row setting

	else {
	  if (j == 0 && i != 0) // 1st column
	    fprintf(gp, "%f ", *vert);// write vert to 1st column of the file
	  else {
	    if (*c == 0.)
	      fprintf(gp, "NaN"); // write other elements
	    else
	      fprintf(gp, "%f", *gamma_var); // write other elements
   
	    if (j != nr)
	      fprintf(gp, " "); // spaces between elements
	    gamma_var++;
	    c++;
	  }
	} // end columns settings
      } // end j
      fprintf(gp, "\n");
      if (i!=0) // vert must not increase in the 1st loop 
      	vert++;
    } // end i
  } // end 3D

  /* 2D experimental variogram */
  else {
    h = &h_exp[0];
    for (i=0; i < nr; ++i) {
      if (*c == 0.) 
	fprintf(gp, "%f NaN\n", *h);
      else
	fprintf(gp, "%f %f\n", *h, *gamma_var);
      c++;
      h++;
      gamma_var++;
    }
  }    
  fclose(gp);

  gp = popen(GNUPLOT, "w"); /* open file to create plots */
  if (gp == NULL)
    G_message("Unable to plot variogram");

  fprintf(gp, "set terminal wxt %d size 800,450\n", var_par->type);
  
  if (bivar == TRUE) { // bivariate variogram
    fprintf(gp, "set title \"Experimental variogram (3D) of <%s>\"\n", var_par->name);
    fprintf(gp, "set xlabel \"h interval No\"\n");
    fprintf(gp, "set ylabel \"dz interval No\"\n");
    fprintf(gp, "set zlabel \"gamma(h,dz) [units^2]\" rotate by 90 left\n");
    fprintf(gp, "set key below\n");
    fprintf(gp, "set key box\n");
    fprintf(gp, "set dgrid3d %d,%d\n", nc, nr);
    fprintf(gp, "splot 'dataE.dat' every ::1:1 matrix title \"experimental variogram\"\n");
  }

  else { // univariate variogram
    char dim[6], dist[2];
    if (xD->i3 == TRUE) { // 3D
      if (var_par->type == 0)
	strcpy(dim,"hz");
      if (var_par->type == 1)
	strcpy(dim, "vert");
      if (var_par->type == 3)
	strcpy(dim, "aniso");
      fprintf(gp, "set title \"Experimental variogram (3D %s) of <%s>\"\n", dim, var_par->name);
    }
    else // 2D  
      fprintf(gp, "set title \"Experimental variogram (2D) of <%s>\"\n", var_par->name);

    fprintf(gp, "set xlabel \"h [m]\"\n");
    fprintf(gp, "set ylabel \"gamma(h) [units^2]\"\n");
    fprintf(gp, "set key bottom right\n");
    fprintf(gp, "set key box\n");
    fprintf(gp, "plot 'dataE.dat' using 1:2 title \"experimental variogram\" pointtype 5\n");
  }
  fclose(gp);

  //remove("dataE.dat");
}

// plot experimental and theoretical variogram
void plot_var(int bivar, double *h_exp, mat_struct *gamma_exp, struct parameters *var_par)
{
  int function, func_h, func_v;
  double nugget, nugget_h, nugget_v;
  double sill, sill_h, sill_v;
  double h_range, h_range_h, h_range_v;

  switch (bivar) {
  case FALSE:
    function = var_par->function;
    nugget = var_par->nugget;
    sill = var_par->sill - nugget;
    h_range = var_par->h_range;
    break;
  case TRUE:
    if (var_par->function != 5) {
      func_h = var_par->horizontal.function;
      func_v = var_par->vertical.function;

      nugget_h = var_par->horizontal.nugget;
      sill_h = var_par->horizontal.sill - nugget_h;
      h_range_h = var_par->horizontal.h_range;

      nugget_v = var_par->vertical.nugget;
      sill_v = var_par->vertical.sill - nugget_v;
      h_range_v = var_par->vertical.h_range;
    }
    break;
  }

  int i, j;     // indices
  int nr, nc;   // # of rows, cols
  double *h;    // pointer to horizontal or anisotropic bins
  double *vert; // pointer to vertical bins
  //double *T_cf; // coefficients of theoretical variogram - vals
  double h_ratio;
  double g_teor;
  double *c;
  double *gamma_var; // pointer to gamma matrix
  double *T; // coefficients of theoretical variogram - matrix
  FILE *gp; // pointer to file  

  nr = gamma_exp->rows; // # of rows of gamma matrix
  nc = gamma_exp->cols; // # of cols of gamma matrix

  c = &var_par->c->vals[0];
  gamma_var = &gamma_exp->vals[0]; // values of gamma matrix
   
  if (var_par->type != 2) { // univariate variogram
    gp = fopen("dataE.dat","w"); // open file to write experimental variogram
    if (gp == NULL)
      G_fatal_error(_("Error writing file"));

    h = &h_exp[0];
    for (i=0; i < nr; i++) {
      if (*c == 0.)
	fprintf(gp, "%f NaN\n", *h); // write other elements
      else
	fprintf(gp, "%f %f\n", *h, *gamma_var);
      h++;
      c++;
      gamma_var++;
    }  
  }
  else {
    gp = fopen("dataE.dat","r"); // open file to write experimental variogram
    if (gp == NULL)
      G_fatal_error(_("You have probably deleted dataE.dat - process middle phase again, please."));
  }
  
  if (fclose(gp) != 0)
    G_fatal_error(_("Error closing file..."));

  /* Theoretical variogram */
  gp = fopen("dataT.dat","w"); // open file to write theoretical variogram
  if (gp == NULL)
    G_fatal_error(_("Error opening file..."));

  double dd;
  double hh;
  double hv[2];
  h = &h_exp[0];

  

  switch (bivar) {
  case 0: // Univariate variogram
    for (i=0; i <= nr; i++) {
      hh = i==0 ? 0. : *h;

      switch (function) {
      case 0: // linear
	dd = *T * hh + *(T+1);
	break;
      case 1: // parabolic
	dd = *T * SQUARE(hh) + *(T+1);
	break;
      case 2: // exponential
	dd = nugget + sill * (1 - exp(- 3. * hh/h_range)); // practical
	break;
      case 3: // spherical
	if (hh < h_range) {
	  h_ratio = hh / h_range;
	  dd = nugget + sill * (1.5 * h_ratio - 0.5 * POW3(h_ratio));
	}
	else
	  dd = sill + nugget;
	break;
      case 4: // Gaussian
	h_ratio = SQUARE(hh) / SQUARE(h_range);
	dd = nugget + sill * (1 - exp(-3. * h_ratio));
	break;
      }
      fprintf(gp, "%f %f\n", hh, dd);

      if (i > 0)
	h++;
    } // end i for cycle
    break;

  case 1: // bivariate (3D) 
    // Coefficients of theoretical variogram
    T = &var_par->T->vals[0]; // values 
    vert = &var_par->vert[0];
    for (i=0; i < nc+1; i++) {   // for each row
      h = &var_par->h[0];
      for (j=0; j < nr+1; j++) { // for each col
	if (i == 0 && j == 0)    // the 0-th element...
	  fprintf(gp, "%d ", nr); // ... is number of columns
	else if (i == 0 && j != 0) { // for the other elements in 1st row...
	  fprintf(gp, "%f", *h); // ... write h
	  if (j < nr)
	    fprintf(gp, " "); // ... write a space
	  h++; // go to next h
	}
	else { // other rows
	  if (j == 0 && i != 0) // write vert to 1st column
	    fprintf(gp, "%f ", *vert);
	  else { // fill the other columns with g_teor
	    hv[0] = *h;
	    hv[1] = *vert;
	    g_teor = variogram_fction(var_par, hv);
	    fprintf(gp, "%f", g_teor);
	    if (j != nr)
	      fprintf(gp, " ");
	    h++;
	  } // end else: fill the other columns
	} // end fill the other rows
      } //end j
      if (i != 0 && j != 0)
	vert++;
      fprintf(gp, "\n");
    } //end i
    break;
    }

  if (fclose(gp) == EOF)
    G_fatal_error(_("Error closing file..."));

  gp = popen(GNUPLOT, "w"); /* open file to create plots */
  if (gp == NULL)
    G_message(_("Unable to plot variogram"));

  if (strcmp(var_par->term,"") != 0) {
    //fprintf(gp, "set terminal %s size 750,450\n", var_par->term);
    fprintf(gp, "set terminal wxt size 750,450\n", var_par->type);
    switch (var_par->type) {
    case 0:
      if (bivar == TRUE)
	fprintf(gp, "set output \"variogram_bivar.%s\"\n", var_par->ext);
      else
	fprintf(gp, "set output \"variogram_horizontal.%s\"\n", var_par->ext);
      break;
    case 1:
      fprintf(gp, "set output \"variogram_vertical.%s\"\n", var_par->ext);
      break;
    case 2:
      if (bivar == TRUE)
	fprintf(gp, "set output \"variogram_bivariate.%s\"\n", var_par->ext);
      else
	fprintf(gp, "set output \"variogram_anisotropic.%s\"\n", var_par->ext);
      break;
    }
  }
  else {
    G_warning("\nVariogram output> If you wish some special file format, please set it at the beginning.\n");
    fprintf(gp, "set terminal wxt %d size 800,450\n", var_par->type);
  }

  if (bivar == TRUE) { // bivariate variogram
    fprintf(gp, "set title \"Experimental and theoretical variogram (3D) of <%s>\"\n", var_par->name);
    
    fprintf(gp, "set xlabel \"h interval No\"\n");
    fprintf(gp, "set ylabel \"dz interval No\"\n");
    fprintf(gp, "set zlabel \"gamma(h,dz) [units^2]\" rotate by 90 left\n");
    fprintf(gp, "set key below\n");
    fprintf(gp, "set key box\n");
    fprintf(gp, "set dgrid3d %d,%d\n", nc, nr);
    fprintf(gp, "splot 'dataE.dat' every ::1:1 matrix title \"experimental variogram\", 'dataT.dat' every ::1:1 matrix with lines title \"theoretical variogram\" palette\n");
  }

  else { // univariate variogram*/
  //if (xD->i3 == TRUE) { // 3D
  if (var_par->type == 0) { // horizontal variogram
    fprintf(gp, "set title \"Experimental and theoretical variogram (3D hz) of <%s>\"\n", var_par->name);
    //fprintf(gp, "set label \"linear: gamma(h) = %f*h + %f\" at screen 0.30,0.90\n", var_par->T->vals[0], var_par->T->vals[1]);
      }
  else if (var_par->type == 1) { // vertical variogram
    fprintf(gp, "set title \"Experimental and theoretical variogram (3D vert) of <%s>\"\n", var_par->name);
    //fprintf(gp, "set label \"linear: gamma(h) = %f*h + %f\" at screen 0.30,0.90\n", var_par->T->vals[0], var_par->T->vals[1]);
  }
  else if (var_par->type == 3) // anisotropic variogram
    fprintf(gp, "set title \"Experimental and theoretical variogram (3D) of <%s>\"\n", var_par->name);
  //}

/*else // 2D  
  fprintf(gp, "set title \"Experimental and theoretical variogram (2D) of <%s>\"\n", var_par->name);*/

  //if (var_par->type == 2/* || xD->i3 == FALSE*/) {
      switch (var_par->function) {
      case 0: // linear
	fprintf(gp, "set label \"linear: gamma(h) = %f*h + %f\" at screen 0.30,0.90\n", var_par->T->vals[0], var_par->T->vals[1]);
	break;
      case 1: // parabolic
	fprintf(gp, "set label \"parabolic: gamma(h) = %f*h^2 + %f\" at screen 0.25,0.90\n", var_par->T->vals[0], var_par->T->vals[1]);
	break;
      case 2: // exponential
	fprintf(gp, "set rmargin 5\n");
	fprintf(gp, "set label \"exponential: gamma(h) = %f + %f * (1 - exp(-3*h / %f))\" at screen 0.10,0.90\n", var_par->nugget, var_par->sill - var_par->nugget, var_par->h_range);
	break;
      case 3: // spherical
	fprintf(gp, "set rmargin 5\n");
	fprintf(gp, "set label \"spherical: gamma(h) = %f+%f*(1.5*h/%f-0.5*(h/%f)^3)\" at screen 0.05,0.90\n", var_par->nugget, var_par->sill - var_par->nugget, var_par->h_range, var_par->h_range);
	break;
      case 4: // gaussian
	fprintf(gp, "set label \"gaussian: gamma(h) = %f + %f * (1 - exp(-3*(h / %f)^2))\" at screen 0.10,0.90\n", var_par->nugget, var_par->sill - var_par->nugget, var_par->h_range);
	break;
      }
      //}
    fprintf(gp, "set xlabel \"h [m]\"\n");
    fprintf(gp, "set ylabel \"gamma(h) [units^2]\"\n");
    fprintf(gp, "set key bottom right\n");
    fprintf(gp, "set key box\n");
    fprintf(gp, "plot 'dataE.dat' using 1:2 title \"experimental variogram\" pointtype 5, 'dataT.dat' using 1:2 title \"theoretical variogram\" with linespoints\n");
  }
  fclose(gp);

  //remove("dataE.dat");
  //remove("dataT.dat");
}
