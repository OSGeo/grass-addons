
/****************************************************************
 *
 * MODULE:	v.kriging
 * AUTHOR:	Eva Stopková
 *              in case of functions taken from another modules, 
 *              they are cited above the function 
 *              or at the beginning of the file (e.g. quantile.cpp 
 *              that uses slightly modified functions 
 *              taken from the module r.quantile (Clemens, G.))
 * PURPOSE: Module interpolates the values to two- or three-dimensional grid using input values
 *          located on 2D/3D point vector layer. Interpolation method
 *          Ordinary kriging has been extended for 3D points (v = f(x,y) -> v = f(x,y,z)).
 *			   
 * COPYRIGHT:  (C) 2012-2014 Eva Stopková and by the GRASS Development Team
 *
 *	This program is free software under the GNU General Public
 *	License (>=v2). Read the file COPYING that
 *	comes with GRASS for details.
 *
 **************************************************************/
#include "local_proto.h"


int main(int argc, char *argv[])
{
  // Vector layer and module
  struct Map_info map;    // Input vector map
  struct GModule *module; // Module

  struct reg_par reg;     // Region parameters
  struct points pnts;     // Input points (coordinates, extent, values, etc.)
  struct pcl_utils pclp;  // PCL structure to store coordinates of input points
    
  // Geostatistical parameters
  struct int_par xD;	  // 2D/3D interpolation for 2D/3D vector layer
  struct var_par var_par; // Variogram (experimental and theoretical)

  // Outputs
  struct output out;      // Output layer properties
  FILE *fp;
    
  // Settings
  int field;
  struct opts opt;
  struct flgs flg;

  /* ------- Module creation ------- */
  module = G_define_module();
  G_add_keyword(_("raster"));
  G_add_keyword(_("3D raster"));
  G_add_keyword(_("ordinary kriging - for 2D and 3D data"));
  module->description =
    _("Interpolates 2D or 3D raster based on input values located on 2D or 3D point vector layer (method ordinary kriging extended to 3D).");

  // Setting options
  opt.input = G_define_standard_option(G_OPT_V_INPUT); // Vector input layer
  opt.input->label = _("Name of input vector points map");

  flg.d23 = G_define_flag(); // Option to process 2D or 3D interpolation
  flg.d23->key = '2';
  flg.d23->description = _("Force 2D interpolation even if input is 3D");
  flg.d23->guisection = _("3D");

  opt.field = G_define_standard_option(G_OPT_V_FIELD);

  opt.phase = G_define_option();
  opt.phase->key = "phase";
  opt.phase->options = "initial, middle, final";
  opt.phase->description = _("Phase of interpolation. In the initial phase, there is empirical variogram computed. In the middle phase, function of theoretical variogram is chosen by the user and its coefficients are estimated empirically. In the final phase, unknown values are interpolated using theoretical variogram from previous phase.");
  opt.phase->required = YES;

  opt.output = G_define_option(); // Output layer
  opt.output->key = "output";
  opt.output->description =
    _("Name for output 2D/3D raster map");
  opt.output->guisection = _("Final");    

  opt.report = G_define_standard_option(G_OPT_F_OUTPUT); // Report file
  opt.report->key = "report";
  opt.report->description = _("Path and name of a file where the report should be written (initial phase only)");
  opt.report->required = NO;
  opt.report->guisection = _("Initial");

  opt.crossvalid = G_define_standard_option(G_OPT_F_OUTPUT); // Report file
  opt.crossvalid->key = "crossvalid";
  opt.crossvalid->description = _("Path and name of a file where the results of cross validation should be written (final phase only)");
  opt.crossvalid->required = NO;
  opt.crossvalid->guisection = _("Final");

  flg.bivariate = G_define_flag();
  flg.bivariate->key = 'b';
  flg.bivariate->description = _("Compute bivariate variogram (just in case of 3D interpolation)");
  flg.bivariate->guisection = _("Middle");

  flg.univariate = G_define_flag();
  flg.univariate->key = 'u';
  flg.univariate->description = _("Compute univariate variogram (just in case of 3D interpolation)");
  flg.univariate->guisection = _("Middle");

  opt.function_var_hz = G_define_option(); // Variogram type
  opt.function_var_hz->key = "hz_function";
  opt.function_var_hz->options = "linear, exponential, spherical, gaussian, bivariate";
  opt.function_var_hz->description = _("Type of horizontal variogram function (just in middle phase)");
  opt.function_var_hz->guisection = _("Middle");

  opt.function_var_vert = G_define_option(); // Variogram type
  opt.function_var_vert->key = "vert_function";
  opt.function_var_vert->options = "linear, exponential, spherical, gaussian, bivariate";
  opt.function_var_vert->description = _("Type of vertical variogram function (just in middle phase)");
  opt.function_var_vert->guisection = _("Middle");

  opt.function_var_final = G_define_option(); // Variogram type
  opt.function_var_final->key = "final_function";
  opt.function_var_final->options = "linear, exponential, spherical, gaussian, bivariate";
  opt.function_var_final->description = _("Type of final variogram function (just in final phase)");
  opt.function_var_final->guisection = _("Final");

  flg.detrend = G_define_flag();
  flg.detrend->key = 't';
  flg.detrend->description = _("Eliminate trend if variogram is parabolic (just in initial phase)");
  flg.detrend->guisection = _("Initial");    

  opt.form_file = G_define_option(); // Variogram plot - various output formats
  opt.form_file->key = "fileformat";
  opt.form_file->options = "cdr,dxf,eps,tex,pdf,png,svg";
  opt.form_file->description = _("Variogram plot (set up in the middle phase) can be saved in several file formats or just presented in Gnuplot terminal (if fileformat is not set)");
  opt.form_file->guisection = _("Middle");

  opt.intpl = G_define_standard_option(G_OPT_DB_COLUMN); // Input values for interpolation
  opt.intpl->key = "icolumn";
  opt.intpl->description =
    _("Name of the attribute column containing input values for interpolation");
  opt.intpl->required = YES;

  opt.zcol = G_define_standard_option(G_OPT_DB_COLUMN); // Column with z coord (2D points)
  opt.zcol->key = "zcolumn";
  opt.zcol->description =
    _("Name of the attribute column containing z coordinates - set only if you want to perform 3D interpolation based on 2D point layer");
  opt.zcol->required = NO;
  opt.zcol->guisection = _("3D");

  opt.var_dir_hz = G_define_option();
  opt.var_dir_hz->key = "azimuth";
  opt.var_dir_hz->type = TYPE_DOUBLE;
  opt.var_dir_hz->required = NO;
  opt.var_dir_hz->answer = "0.0";
  opt.var_dir_hz->description =
    _("Azimuth of variogram computing (isotrophic), initial phase only ");
  opt.var_dir_hz->guisection = _("Initial");

  opt.var_dir_vert = G_define_option();
  opt.var_dir_vert->key = "zenith_angle";
  opt.var_dir_vert->type = TYPE_DOUBLE;
  opt.var_dir_vert->required = NO;
  opt.var_dir_vert->answer = "0.0";
  opt.var_dir_vert->description =
    _("Zenith angle of variogram computing (isotrophic), initial phase only");
  opt.var_dir_vert->guisection = _("Initial");

  opt.nL = G_define_option();
  opt.nL->key = "lpieces";
  opt.nL->type = TYPE_INTEGER;
  opt.nL->required = NO;
  opt.nL->description = _("Count of length pieces, initial phase only");
  opt.nL->guisection = _("Initial");

  opt.nZ = G_define_option();
  opt.nZ->key = "vpieces";
  opt.nZ->type = TYPE_INTEGER;
  opt.nZ->required = NO;
  opt.nZ->description =
    _("Count of vertical pieces (set only for computing 3D variogram), initial phase only");
  opt.nZ->guisection = _("Initial");

  opt.td_hz = G_define_option();
  opt.td_hz->key = "td";
  opt.td_hz->type = TYPE_DOUBLE;
  opt.td_hz->answer = "90.0";
  opt.td_hz->description = _("Angle of variogram processing, initial phase only");
  opt.td_hz->required = NO;
  opt.td_hz->guisection = _("Initial");

  opt.nugget_hz = G_define_option();
  opt.nugget_hz->key = "hz_nugget";
  opt.nugget_hz->type = TYPE_DOUBLE;
  opt.nugget_hz->description = _("Nugget effect of horizontal variogram, middle phase only");
  opt.nugget_hz->required = NO;
  opt.nugget_hz->guisection = _("Middle");

  opt.nugget_vert = G_define_option();
  opt.nugget_vert->key = "vert_nugget";
  opt.nugget_vert->type = TYPE_DOUBLE;
  opt.nugget_vert->description = _("Nugget effect of vertical variogram, middle phase only");
  opt.nugget_vert->required = NO;
  opt.nugget_vert->guisection = _("Middle");

  opt.nugget_final = G_define_option();
  opt.nugget_final->key = "final_nugget";
  opt.nugget_final->type = TYPE_DOUBLE;
  opt.nugget_final->description = _("Nugget effect of final variogram, final phase only");
  opt.nugget_final->required = NO;
  opt.nugget_final->guisection = _("Final");

  opt.sill_hz = G_define_option();
  opt.sill_hz->key = "hz_sill";
  opt.sill_hz->type = TYPE_DOUBLE;
  opt.sill_hz->description = _("Sill of horizontal variogram, middle phase only");
  opt.sill_hz->required = NO;
  opt.sill_hz->guisection = _("Middle");

  opt.sill_vert = G_define_option();
  opt.sill_vert->key = "vert_sill";
  opt.sill_vert->type = TYPE_DOUBLE;
  opt.sill_vert->description = _("Sill of vertical variogram, middle phase only");
  opt.sill_vert->required = NO;
  opt.sill_vert->guisection = _("Middle");

  opt.sill_final = G_define_option();
  opt.sill_final->key = "final_sill";
  opt.sill_final->type = TYPE_DOUBLE;
  opt.sill_final->description = _("Sill of final variogram, final phase only");
  opt.sill_final->required = NO;
  opt.sill_final->guisection = _("Final");

  opt.range_hz = G_define_option();
  opt.range_hz->key = "hz_range";
  opt.range_hz->type = TYPE_DOUBLE;
  opt.range_hz->description = _("Range of horizontal variogram, middle phase only");
  opt.range_hz->required = NO;
  opt.range_hz->guisection = _("Middle");

  opt.range_vert = G_define_option();
  opt.range_vert->key = "vert_range";
  opt.range_vert->type = TYPE_DOUBLE;
  opt.range_vert->description = _("Range of vertical variogram, middle phase only");
  opt.range_vert->required = NO;
  opt.range_vert->guisection = _("Middle");

  opt.range_final = G_define_option();
  opt.range_final->key = "final_range";
  opt.range_final->type = TYPE_DOUBLE;
  opt.range_final->description = _("Range of final variogram, final phase only");
  opt.range_final->required = NO;
  opt.range_final->guisection = _("Final");
  /* --------------------------------------------------------- */

  G_gisinit(argv[0]);

  if (G_parser(argc, argv))
    exit(EXIT_FAILURE);

  /* Get parameters from the parser */
  if (strcmp(opt.phase->answer, "initial") == 0)
    xD.phase = 0; // estimate range
  else if (strcmp(opt.phase->answer, "middle") == 0)
    xD.phase = 1; // estimate anisotropic variogram
  else if (strcmp(opt.phase->answer, "final") == 0)
    xD.phase = 2; // compute kriging

  // Open report file if desired
  if (opt.report->answer) {
    xD.report.write2file = TRUE;
    xD.report.name = opt.report->answer;
    xD.report.fp = fopen(xD.report.name, "w");
    time(&xD.report.now);
    fprintf(xD.report.fp, "v.kriging started on %s\n\n", ctime(&xD.report.now));
    G_message(_("Report is being written to %s..."), xD.report.name);
  }
  else
    xD.report.write2file = FALSE;

  if (opt.crossvalid->answer) {
    xD.crossvalid.write2file = TRUE;
    xD.crossvalid.name = opt.crossvalid->answer;
    xD.crossvalid.fp = fopen(xD.crossvalid.name, "w");
  }
  else
    xD.crossvalid.write2file = FALSE;
    
  var_par.hz.name = var_par.vert.name = var_par.fin.name = opt.input->answer; // set name of variogram
  var_par.hz.dir = opt.var_dir_hz->answer ? DEG2RAD(atof(opt.var_dir_hz->answer)) : 0.; // Azimuth
  var_par.vert.dir = opt.var_dir_vert->answer ? DEG2RAD(atof(opt.var_dir_vert->answer)) : 0.; // Zenith angle
  var_par.fin.dir = opt.var_dir_hz->answer ? DEG2RAD(atof(opt.var_dir_hz->answer)) : 0.; // Azimuth

  var_par.hz.td = DEG2RAD(atof(opt.td_hz->answer)); // Angle of variogram processing
  //var_par.vert.td = DEG2RAD(atof(opt.td_vert->answer)); // Angle of variogram processing

  /*if (phase > 0) {
  //var_par.sill = atof(opt.sill->answer);
  var_par.nugget = atof(opt.nugget->answer);
  var_par.h_range = atof(opt.range->answer);
  if (/*(var_par.sill != -1. && var_par.sill <= 0.) || *//*(var_par.nugget != -1. && var_par.nugget < 0.) || (var_par.h_range != -1. && var_par.h_range <= 0.)) {
							   if (xD.report.write2file == TRUE) {
							   fclose(xD.report.fp);
							   remove(xD.report.name);
							   }
							   G_fatal_error(_("Variogram parameters should be positive..."));
							   } // error
							   }    */

  /*if (opt.nL->answer) { // Test if nL have been set up (optional)
    if (var_par.nL < 1) // Invalid value
    G_message(_("Number of horizontal pieces must be at least 1. Default value will be used..."));
    else
    var_par.nL = atof(opt.nL->answer); // todo osetrit aby sa neprepisovalo     
    }
    
    if (opt.variogram->answer) // Function of theoretical variogram
    set_function(opt.variogram->answer, &var_par, &xD.report);*/

  if (opt.form_file->answer) { // Plotting variogram
    set_gnuplot(opt.form_file->answer, &var_par.hz);
    set_gnuplot(opt.form_file->answer, &var_par.vert);
    set_gnuplot(opt.form_file->answer, &var_par.fin);
  }
  else {
    strcpy(var_par.hz.term, ""); /* TO DO: ked pouzivatel zada hlupost */
    strcpy(var_par.vert.term, "");
    strcpy(var_par.fin.term, "");
  }

  xD.bivar = flg.bivariate->answer == TRUE ? TRUE : FALSE;
  xD.univar = flg.univariate->answer == TRUE ? TRUE : FALSE;
  if (xD.bivar == TRUE && xD.univar == TRUE) {
    if (xD.report.write2file == TRUE) {
      fclose(xD.report.fp);
      remove(xD.report.name);
    }
    G_fatal_error(_("You should mark either univariate, or bivariate variogram, not both of them..."));
  } // error

  /* ---------------------------------------------------------- */
  Vect_set_open_level(2); // Open input vector map

  if (0 > Vect_open_old2(&map, opt.input->answer, "", opt.field->answer)) {
    if (xD.report.write2file == TRUE) {
      fclose(xD.report.fp);
      remove(xD.report.name);
    }
    G_fatal_error(_("Unable to open vector map <%s>"), opt.input->answer);
  } // error
  Vect_set_error_handler_io(&map, NULL);
  /* ---------------------------------------------------------- */
    
  /* Perform 2D or 3D interpolation ? */
  xD.i3 = flg.d23->answer ? FALSE : TRUE; // 2D/3D interpolation
  xD.v3 = Vect_is_3d(&map); // 2D/3D layer
    
  /* What could happen:
   *-------------------
   * 3D interpolation + 3D points = 3D GIS
   * 3D interpolation + 2D points = 2,5D -> 3D GIS (needs attribute column with z and 3D region)
   * 2D interpolation + 3D points = 3D -> 2,5D GIS
   * 2D interpolation + 2D points = 2,5D GIS */

  // 3D interpolation
  if (xD.i3 == TRUE) {
    if (xD.v3 == FALSE) { // 2D input
      if (!opt.zcol->answer) {
	if (xD.report.write2file == TRUE) { // close report file
	  fprintf(xD.report.fp, "Error (see standard output). Process killed...");
	  fclose(xD.report.fp);
	}
	G_fatal_error(_("To process 3D interpolation based on 2D input, please set attribute column containing z coordinates or switch to 2D interpolation."));
      }       
    } // end if zcol == NULL
      // 3D or 2,5D input
    if (opt.nZ->answer) { // Test if nZ have been set up (optional)
      if (var_par.vert.nLag < 1) // Invalid value
	G_message(_("Number of vertical pieces must be at least 1. Default value will be used..."));
      else
	var_par.vert.nLag = atof(opt.nZ->answer);     
    } // end if nZ->answer
      /* TO DO: chyba, ak nie je cele cislo */
  } // end if 3D interpolation

    /* 2D interpolation */  
  else {
    G_fatal_error(_("Access to 2D kriging is denied temporarily. Please feel free to use 3D kriging..."));
    var_par.vert.nLag = -1; // abs will be used in next steps
  }

  field = Vect_get_field_number(&map, opt.field->answer);
  if (xD.report.write2file == TRUE)
    write2file_basics(&xD, &opt);
  /* ---------------------------------------------------------- */

  /* Get... */ 
  get_region_pars(&xD, &reg); // ... region parameters 
  read_points(&map, &reg, &pnts, &pclp, xD, opt.zcol->answer, field, &xD.report); // ... coordinates of points
  pnts.invals = get_col_values(&map, &xD, &pnts, field, opt.intpl->answer, flg.detrend->answer); // ... values for interpolation

  /* Estimate 2D/3D variogram */
  switch (xD.phase) {
  case 0:
    /* Determine maximal horizontal (and vertical) distance + lags */
    var_par.hz.type = 0;
    if (xD.i3 == TRUE) {
      var_par.vert.type = 1;
    }
      
    variogram_restricts(&xD, &pnts, pclp.pnts_hz, &var_par.hz);
    if (xD.i3 == TRUE) {
      variogram_restricts(&xD, &pnts, pclp.pnts_vert, &var_par.vert);
    }

    if (xD.i3 == TRUE && var_par.vert.nLag > var_par.hz.nLag) {
      var_par.vert.nLag = var_par.hz.nLag;
      var_par.vert.lag = var_par.vert.max_dist / var_par.vert.nLag;
      write2file_varSets(&xD.report, &var_par.vert);
    }
    
    E_variogram(0, &xD, &pnts, &pclp, &var_par);
    if (xD.i3 == TRUE) {
      E_variogram(1, &xD, &pnts, &pclp, &var_par);
      G_message(_("You may continue to computing theoretical variograms (middle phase)..."));
    }
    else {
      G_message(_("You may continue to computing theoretical variograms (final phase)..."));
    }
    goto end;
  case 1:
    read_tmp_vals("variogram_hz_tmp.txt", &var_par.hz, &xD);
    read_tmp_vals("variogram_vert_tmp.txt", &var_par.vert, &xD);

    if (xD.report.name) {
      xD.report.write2file = TRUE;
      xD.report.fp = fopen(xD.report.name, "a");
    }

    T_variogram(0, opt, &var_par.hz, &xD.report); // Theoretical variogram
    T_variogram(1, opt, &var_par.vert, &xD.report); // Theoretical variogram


    /* difference between ranges
       - if greater than 5% - bivariate
       - if smaller than 5% - anisotropic
    */
    double sill95, diff_sill;
    sill95 = var_par.hz.sill > var_par.vert.sill ? 0.05 * var_par.hz.sill : 0.05 * var_par.vert.sill;
    diff_sill = fabsf(var_par.hz.sill - var_par.vert.sill);
    if (xD.bivar == TRUE || (!flg.univariate->answer && diff_sill > sill95)) { // zonal anisotropy
      var_par.fin.type = 2;
      var_par.fin.td = var_par.hz.td;
      var_par.fin.max_dist = var_par.hz.max_dist;
      var_par.fin.max_dist_vert = var_par.vert.max_dist;
      variogram_restricts(&xD, &pnts, pclp.pnts, &var_par.fin);
      E_variogram(2, &xD, &pnts, &pclp, &var_par); 
    }
      
    else if (xD.univar == TRUE || (!flg.bivariate->answer && diff_sill <= sill95)) { // geometric anisotropy 
      var_par.fin.type = 3; 
      var_par.fin.max_dist = var_par.hz.max_dist;
      var_par.fin.td = var_par.hz.td;
      
      xD.aniso_ratio = var_par.hz.h_range / var_par.vert.h_range;
      geometric_anisotropy(&xD, &pnts, pclp.pnts);

      variogram_restricts(&xD, &pnts, pclp.pnts, &var_par.fin);

      E_variogram(3, &xD, &pnts, &pclp, &var_par);      
    }      
    G_message(_("You may continue to interpolate values (final phase)..."));
    goto end;
  case 2:
    if (!opt.output->answer)
      G_fatal_error(_("Please set up name of output layer..."));
    out.name = opt.output->answer; // Output layer name
    
    read_tmp_vals("variogram_final_tmp.txt", &var_par.fin, &xD);

    if (xD.report.name) {
      xD.report.write2file = TRUE;
      xD.report.fp = fopen(xD.report.name, "a");
      if (xD.report.fp == NULL)
	G_fatal_error(_("Cannot open the file..."));
    }
    
    if (var_par.fin.type == 3)
      geometric_anisotropy(&xD, &pnts, pclp.pnts);
    
    T_variogram(var_par.fin.type, opt, &var_par.fin, &xD.report); // Theoretical variogram
    break;
  }

  /* Ordinary kriging (including 2D/3D raster creation) */
  ordinary_kriging(&xD, &reg, &pnts, &pclp, &var_par, &out);
  /* ---------------------------------------------------------- */

 end:
  Vect_close(&map); // Close vector map

  exit(EXIT_SUCCESS);
}

