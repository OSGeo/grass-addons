#include "local_proto.h"

 __inline double square(double x)
  {
    return x*x;
  }

// formulation of variogram functions
double variogram_fction(struct parameters *var_par, double *dr) 
{
  // Local variables
  int variogram = var_par->function; // theoretical variogram
  int type = var_par->type;
  double nugget;
  double part_sill;
  double h_range;
  double *T;

  if (type == 2) {
    T = &var_par->T->vals[0]; // coefficients of theoretical variogram
  }

  double radius;   // square distance of the point couple
  double h;
  double vert;
  double h_ratio;
  double teor_var, result = 0.; // estimated value of the theoretical variogram

  int n_cycles = (type == 2 && var_par->function != 5) ? 2 : 1; // # of cycles (bi- or univariate)

  for (int i=0; i < n_cycles; i++) {
    if (n_cycles == 2) { // bivariate variogram
      variogram = i==0 ? var_par->horizontal.function : var_par->vertical.function;
      h = i==0 ? dr[0] : dr[1];
      radius = SQUARE(h);
      nugget = i==0 ? var_par->horizontal.nugget : var_par->vertical.nugget;	
      part_sill = i==0 ? var_par->horizontal.sill - nugget : var_par->vertical.sill - nugget;
      h_range = i==0 ? var_par->horizontal.h_range : var_par->vertical.h_range;	
    }
    else { // univariate variogram or linear bivariate
      variogram = var_par->function;
      if (variogram == 5) {
	h = dr[0];
	vert = dr[1];
      }
      else {
	radius = SQUARE(dr[0]) + SQUARE(dr[1]) + SQUARE(dr[2]); // weighted dz
	h = sqrt(radius);

	nugget = var_par->nugget;	
	part_sill = var_par->sill - nugget;
	h_range = var_par->h_range;
      }	
    }
    
    switch (variogram) {
    case 0: // linear function   
      teor_var = linear(h, *T, *(T+1));
      break;
    case 1: // parabolic function TODO: delete
      teor_var = *T * radius + *(T+1);
      break;
    case 2: // exponential function
      teor_var = exponential(h, nugget, part_sill, h_range);     
      break;
    case 3: // spherical function
      teor_var = spherical(h, nugget, part_sill, h_range);
      break;
    case 4: // Gaussian function
      teor_var = gaussian(radius, nugget, part_sill, h_range);
      break;
    case 5:
      teor_var = *T * h + *(T+1) * vert + *(T+2);
      break;
    } // end switch (variogram)
    
    result += teor_var;
  }
  
  return result;
}

// compute coordinates of reference point - cell centre
void cell_centre(unsigned int col, unsigned int row, unsigned int dep, struct int_par *xD, struct reg_par *reg, double *r0, struct parameters *var_par)
{
  // Local variables
  int i3 = xD->i3;

  r0[0] = reg->west + (col + 0.5) * reg->ew_res;  // x0
  r0[1] = reg->north - (row + 0.5) * reg->ns_res; // y0
  if (i3 == TRUE)
    switch (var_par->function) {
    case 5:
      r0[2] = reg->bot + (dep + 0.5) * reg->bt_res; // z0
      break;
    default:
      r0[2] = xD->aniso_ratio * (reg->bot + (dep + 0.5) * reg->bt_res); // z0
      break;
    }
  else
    r0[2] = 0.;
}

// set up elements of G matrix
mat_struct *set_up_G(struct points *pnts, struct parameters *var_par, struct write *report)
{
  // Local variables
  int n = pnts->n; // number of input points
  double *r = pnts->r; // xyz coordinates of input points
  int type = var_par->type;

  int i, j;        // indices of matrix rows/cols
  int  n1 = n+1;   // number of matrix rows/cols
  double teor_var; // estimated value based on theoretical variogram and distance of the input points
  double *dr;      // coordinate differences dx, dy, dz between couples of points
  mat_struct *GM;  // GM matrix

  dr = (double *) G_malloc(3 * sizeof(double));
  GM = G_matrix_init(n1, n1, n1);    // G[n1][n1] matrix

  doublereal *md, *mu, *ml, *dbu, *dbl, *m1r, *m1c;
  dbu = &GM->vals[0]; // upper matrix elements
  dbl = &GM->vals[0]; // lower matrix elements
  md = &GM->vals[0];  // diagonal matrix elements
  m1r = &GM->vals[n1-1]; // GM - last matrix row
  m1c = &GM->vals[n1*n]; // GM - last matrix col
  
  // G[n;n]
  for (i = 0; i < n1; i++) { // for elements in each row
    dbu += n1; // new row of the U
    dbl++;     // new col of the L
    mu = dbu;  // 1st element in the new U row
    ml = dbl;  // 1st element in the new L col
    for (j = i; j < n1; j++) { // for elements in each col of upper matrix
      if (i != j && i != n && j != n) { // non-diagonal elements except last row/col
	coord_diff(i, j, r, dr); // compute coordinate differences
	if (type == 2) {
	  dr[0] = sqrt(SQUARE(dr[0]) + SQUARE(dr[1]));
	  dr[1] = dr[2];
	}
	teor_var = variogram_fction(var_par, dr);
	
	if (isnan(teor_var)) {
	  if (report->name) {
	    fprintf(report->fp, "Error (see standard output). Process killed...");
	    fclose(report->fp);
	  }
	  G_fatal_error(_("Theoretical variogram is NAN..."));
	}
      
	*mu = *ml = (doublereal) teor_var; // set the value to the matrix
	mu += n1; // go to next element in the U row
	ml++;     // go to next element in the L col
      } // end non-diagonal elements condition
    } // end j loop

    // go to the diagonal element in the next row
    dbu++;      // U
    dbl += n1;  // L
    *md = 0.0; // set diagonal
    md += n1+1;
    // Set ones
    if (i<n1-1) { // all elements except the last one...
      *m1r = *m1c = 1.0; // ... shall be 1
      m1r += n1; // go to next col in last row
      m1c++; // go to next row in last col
    } // end "last 1" condition
  } // end i loop

  free(dr);
  return GM;
}

// make G submatrix for rellevant points
mat_struct *submatrix(std::vector<int> index, mat_struct *GM_all, struct write *report)
{
  // Local variables
  int n = index.size ();
  int *lind;
  lind = &index.data ()[0];
  mat_struct *GM = GM_all;

  int i, j, k, N1 = GM->rows, n1 = n+1, *dinR0, *dinR, *dini, *dini0, *dinj0, *dinj;
  doublereal *dbo, *dbx, *dbu, *dbl, *md, *mu, *ml, *m1r, *m1c;

  mat_struct *sub;
  sub = G_matrix_init(n1,n1,n1); 
  if (sub == NULL) {
    if (report->name) { // close report file
      fprintf(report->fp, "Error (see standard output). Process killed...");
      fclose(report->fp);
    }
    G_fatal_error(_("Unable to initialize G-submatrix..."));
  }
  
  // Initialize indexes: GM[0;1]
  // - cols
  dini = &lind[0];  // i   - set processing column
  dini0 = &lind[0]; // i-1 - previous column
  // initialize new col
  dinR0 = &lind[1];  // return to first processing row - lower GM
  dinR = &lind[1];   // return to first processing row - lower GM

  dbo = &GM->vals[*dini * N1 + *dinR]; // 1st value in GM_all
  md = &sub->vals[0];   // GM - diagonal
  dbu = &sub->vals[n1]; // GM - upper
  dbl = &sub->vals[1];  // GM - lower
  m1r = &sub->vals[n1-1]; // GM - last row
  m1c = &sub->vals[n1*n]; // GM - last col

  for (i=0; i<=n; i++) { // set up cols of submatrix
    // original matrix
    dbx = dbo; // new col in GM_all
    dinj = dinR;   // orig: inicialize element (row) in (col) - upper matrix
    dinj0 = dinR;  // orig: inicialize element (row - 1) in (col)
    // submatrix
    mu = dbu;  // sub: start new column
    ml = dbl;  // sub: start new row
    for (j=i+1; j<n; j++) { // for rows 
      //submatrix
      *mu = *ml = *dbx; // general elements
      //G_debug(0,"GM=%f", *dbx);
      mu += n1; // go to element in next column
      ml++;     // go to element in next row
      // Original matrix      
      dinj0 = dinj; // save current ind
      dinj++; // set next ind
      if (j < n-1)
	dbx += *dinj - *dinj0;   
    } // end j
    // Original matrix
    dini0 = dini; // save current ind
    dini++;    // set next ind
    if (i < n-1) {
      dbu += n1+1; // new col in GM
      dbl += n1+1; // new row in GM
    }
    dinR0 = dinR;
    dinR++;
    dbo += (*dini - *dini0) * N1 + (*dinR - *dinR0);
    // Set ones     
    *m1r = *m1c = 1.0;  
    m1r += n1;  
    m1c++;
    // Set diagonals
    *md = 0.0; 
    md += n1+1;
  } // end i

  return sub;
}

// set up g0 vector
mat_struct *set_up_g0(struct int_par *xD, std::vector<int> ind, struct points *pnts, double *r0, struct parameters *var_par)
{
  // Local variables
  int i3 = xD->i3;  // 2D or 3D interpolation
  int bivar = xD->bivar;
  int type = var_par->type;
  int n;
  double *r; // xyz coordinates of input points

  int *lind, *lind0;

  if (ind.empty()) {
    n = pnts->n;
    r = &pnts->r[0];
  }
  else {
    n = ind.size (); // number of input points
    lind = &ind[0];
    lind0 = &ind[0];
    r = &pnts->r[*lind * 3]; 
  }
  int n1 = n + 1;
  
  int i;   // index of elements and length of g0 vector
  double teor_var; // estimated value based on theoretical variogram and distance of the input points
  double *dr;      // coordinate differences dx, dy, dz between couples of points
  mat_struct *g0;  // vector of estimated differences between known and unknown values 

  dr = (double *) G_malloc(3 * sizeof(double)); // Coordinate differences
  g0 = G_matrix_init(n1,1,n1);

  double *ro;
  doublereal *g;
  g = &g0->vals[0];  
  
  for (i=0; i<n; i++) { // count of input points
    // Coord diffs (input points and cell/voxel center)
    dr[0] = *r - r0[0]; // dx
    dr[1] = *(r+1) - r0[1]; // dy
    switch (i3) {
    case FALSE: 
      // Cell value diffs estimation using linear variogram
      dr[2] = 0.0; // !!! optimalize - not to be necessary to use this line
      break;
    case TRUE:
      dr[2] = *(r+2) - r0[2]; // dz
      break;
    }
    if (type == 2) {
      dr[0] = sqrt(SQUARE(dr[0]) + SQUARE(dr[1]));
      dr[1] = dr[2];
    }

    *g = variogram_fction(var_par, dr);
    g++;

    if (ind.empty())
      r += 3;
    else {
      *lind0 = *lind;
      lind++;
      r += 3 * (*lind - *lind0);
    }
  } // end i loop

  // condition: sum of weights = 1
  *g = 1.0; // g0 [n1x1]

  return g0;
}

// compute result to be located on reference point
double result(std::vector<int> ind, struct points *pnts, mat_struct *w0)
{
  int n;
  double *vo; 
  mat_struct *loc_w = w0;

  int *indo, *indo0, *lind;

  if (ind.empty())
    n = pnts->n;
  else {
    n = ind.size ();
    lind = &ind[0];
  }

  int i;
  mat_struct *ins, *w, *rslt_OK;
  doublereal *vt, *wo, *wt;
  ins = G_matrix_init(n, 1, n);
  w = G_matrix_init(1, n, 1);

  if (ind.empty())
    vo = &pnts->invals[0];// original input values
  else {
    indo = &lind[0];   // original indexes
    indo0 = &lind[0];
    vo = &pnts->invals[*indo];// original input values
  }
  
  vt = &ins->vals[0]; // selected inputs values
  wo = &loc_w->vals[0]; // selected inputs values
  wt = &w->vals[0];   // weights without last one

  for (i=0; i<n; i++) { 
    *vt = *vo;
    *wt = *wo;
    if (i<n-1) {
      indo0 = indo;
      indo++;
      if (ind.empty())
	vo++;
      else
	vo += *indo - *indo0;
      vt++;
      wo++;
      wt++;
    }
  }
  rslt_OK = G_matrix_product(w,ins);
  
  G_matrix_free(w);
  G_matrix_free(ins);

  return rslt_OK->vals[0];
}

// validation
void crossvalidation(struct int_par *xD, struct points *pnts, pcl::PointCloud<pcl::PointXYZ>::Ptr pcl_pnts, struct parameters *var_par)
{
  int n = pnts->n;     // # of input points
  double *r = pnts->r; // coordinates of points
  double *vals = pnts->invals;
  double ratio;
  mat_struct *GM = var_par->GM;

  ratio = var_par->type == 3 ? xD->aniso_ratio : 1.;

  int i, j;
  int n1;
  double radius;
  double r0[3];
  mat_struct *GM_sub;
  mat_struct *GM_Inv, *g0, *w0;
  double rslt_OK;
  pcl::KdTreeFLANN<pcl::PointXYZ> kd_tree;
  kd_tree.setInputCloud(pcl_pnts); // Set up kd-tree
  pcl::PointXYZ cellCent;
  std::vector<int> ind;
  std::vector<float> sqDist;
  struct write *crossvalid = &xD->crossvalid;
  struct write *report = &xD->report;
  double *normal, *absval, *norm, *av;
  normal = (double *) G_malloc(n * sizeof(double));
  absval = (double *) G_malloc(n * sizeof(double));
  norm = &normal[0];
  av = &absval[0];

  FILE *fp;
  if (crossvalid->name)
    fp = fopen(crossvalid->name, "w");

  radius = var_par->max_dist;

  for (i=0; i<n; i++) {
    // set up processing point
    *r0 = cellCent.x = *r;
    *(r0+1) = cellCent.y = *(r+1);
    *(r0+2) = cellCent.z = *(r+2); // if 2D: 0.

    if (kd_tree.radiusSearch(cellCent, radius, ind, sqDist) > 0 ) {
      n1 = ind.size () + 1; // number of rellevant points + weights
      GM_sub = submatrix(ind, GM, &xD->report);      
      GM_Inv = G_matrix_inverse(GM_sub);
      G_matrix_free(GM_sub);
      
      g0 = set_up_g0(xD, ind, pnts, r0, var_par); // Diffs inputs - unknowns (incl. cond. 1)) 
      w0 = G_matrix_product(GM_Inv, g0); // Vector of weights, condition SUM(w) = 1 in last row
       
      G_matrix_free(g0);
      G_matrix_free(GM_Inv);
      rslt_OK = result(ind, pnts, w0); // Estimated cell/voxel value rslt_OK = w x inputs
      G_matrix_free(w0);

      //Create output 
      *norm = *vals - rslt_OK;
      *av = fabsf(*norm);
      if (xD->i3 == TRUE)
	fprintf(fp,"%d %.3f %.3f %.2f %f %f %f\n", i, *r, *(r+1), *(r+2) / ratio, pnts->invals[i], rslt_OK, *norm);
      else
	fprintf(fp,"%d %.3f %.3f %f %f %f\n", i, *r, *(r+1), *vals, rslt_OK, *norm);
    }
    else
      fprintf(fp,"%d. point does not have neighbours in given radius\n", i);
    r += 3;
    vals++;
    norm++;
    av++;
  }
  fclose(fp);
  G_message(_("Cross validation results have been written into <%s>"), crossvalid->name);

  if (report->name) {
    double quant05, quant10, quant25, quant50, quant75, quant90, quant95;
    fprintf(report->fp, "\n************************************************\n");
    fprintf(report->fp, "*** Cross validation results ***\n");

    test_normality(n, normal, report);
    
    fprintf(report->fp, "Quantile of absolute values\n");
    quant95 = quantile(0.95, n, absval, report); 
    //quant90 = quantile(0.90, n, absval, report);
    //quant75 = quantile(0.75, n, absval, report);
    //quant50 = quantile(0.50, n, absval, report); 
    //quant25 = quantile(0.25, n, absval, report);
    //quant10 = quantile(0.10, n, absval, report);
    //quant05 = quantile(0.05, n, absval, report);
  }
}
