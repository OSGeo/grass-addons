
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

#ifndef HAVE_LIBBLAS
#error GRASS GIS is not configured with BLAS
#endif

#ifndef HAVE_LIBLAPACK
#error GRASS GIS is not configured with LAPACK
#endif


int main(int argc, char *argv[])
{
    // Vector layer and module
    struct Map_info map;        // Input vector map
    struct GModule *module;     // Module

    struct reg_par reg;         // Region parameters
    struct points pnts;         // Input points (coordinates, extent, values, etc.)

    // Geostatistical parameters
    struct int_par xD;          // 2D/3D interpolation for 2D/3D vector layer
    struct var_par var_pars;    // Variogram (experimental and theoretical)

    // Outputs
    struct output out;          // Output layer properties

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
    opt.input = G_define_standard_option(G_OPT_V_INPUT);        // Vector input layer
    opt.input->label = _("Name of input vector points map");

    flg.d23 = G_define_flag();  // Option to process 2D or 3D interpolation
    flg.d23->key = '2';
    flg.d23->description = _("Force 2D interpolation even if input is 3D");
    flg.d23->guisection = _("3D");

    opt.field = G_define_standard_option(G_OPT_V_FIELD);

    opt.phase = G_define_option();
    opt.phase->key = "phase";
    opt.phase->options = "initial, middle, final";
    opt.phase->description =
        _("Phase of interpolation. In the initial phase, there is empirical variogram computed. In the middle phase, function of theoretical variogram is chosen by the user and its coefficients are estimated empirically. In the final phase, unknown values are interpolated using theoretical variogram from previous phase.");
    opt.phase->required = YES;

    opt.report = G_define_standard_option(G_OPT_F_OUTPUT);      // Report file
    opt.report->key = "report";
    opt.report->description = _("File to write the report");
    opt.report->required = NO;
    opt.report->guisection = _("Initial");

    opt.function_var_hz = G_define_option();    // Variogram type
    opt.function_var_hz->key = "hz_function";
    opt.function_var_hz->options =
        "linear, exponential, spherical, gaussian, bivariate";
    opt.function_var_hz->description = _("Horizontal variogram function");
    opt.function_var_hz->guisection = _("Middle");

    opt.output = G_define_option();     // Output layer
    opt.output->key = "output";
    opt.output->description = _("Name for output 2D/3D raster map");
    opt.output->guisection = _("Final");

    opt.crossvalid = G_define_standard_option(G_OPT_F_OUTPUT);  // Report file
    opt.crossvalid->key = "crossvalid";
    opt.crossvalid->description =
        _("File to write the results of cross validation");
    opt.crossvalid->required = NO;
    opt.crossvalid->guisection = _("Final");

    flg.bivariate = G_define_flag();
    flg.bivariate->key = 'b';
    flg.bivariate->description =
        _("Compute bivariate variogram (3D interpolation only)");
    flg.bivariate->guisection = _("Middle");

    flg.univariate = G_define_flag();
    flg.univariate->key = 'u';
    flg.univariate->description =
        _("Compute univariate variogram (3D interpolation only)");
    flg.univariate->guisection = _("Middle");

    opt.function_var_vert = G_define_option();  // Variogram type
    opt.function_var_vert->key = "vert_function";
    opt.function_var_vert->options =
        "linear, exponential, spherical, gaussian, bivariate";
    opt.function_var_vert->description = _("Vertical variogram function");
    opt.function_var_vert->guisection = _("Middle");

    opt.function_var_final = G_define_option(); // Variogram type
    opt.function_var_final->key = "final_function";
    opt.function_var_final->options =
        "linear, exponential, spherical, gaussian, bivariate";
    opt.function_var_final->description =
        _("Final variogram function (anisotropic or horizontal component of bivariate variogram)");
    opt.function_var_final->guisection = _("Final");

    opt.function_var_final_vert = G_define_option();    // Variogram type
    opt.function_var_final_vert->key = "final_vert_function";
    opt.function_var_final_vert->options =
        "linear, exponential, spherical, gaussian, bivariate";
    opt.function_var_final_vert->description =
        _("Final variogram function (vertical component of bivariate variogram)");
    opt.function_var_final_vert->guisection = _("Final");

    flg.detrend = G_define_flag();
    flg.detrend->key = 't';
    flg.detrend->description = _("Eliminate trend if variogram is parabolic");
    flg.detrend->guisection = _("Initial");

    opt.form_file = G_define_option();  // Variogram plot - various output formats
    opt.form_file->key = "fileformat";
    opt.form_file->options = "cdr,dxf,eps,tex,pdf,png,svg";
    opt.form_file->description =
        _("File format to save variogram plot (empty: preview in Gnuplot terminal)");
    opt.form_file->guisection = _("Middle");

    opt.intpl = G_define_standard_option(G_OPT_DB_COLUMN);      // Input values for interpolation
    opt.intpl->key = "icolumn";
    opt.intpl->description =
        _("Attribute column containing input values for interpolation");
    opt.intpl->required = YES;

    opt.zcol = G_define_standard_option(G_OPT_DB_COLUMN);       // Column with z coord (2D points)
    opt.zcol->key = "zcolumn";
    opt.zcol->description =
        _("Attribute column containing z coordinates (only for 3D interpolation based on 2D point layer)");
    opt.zcol->required = NO;
    opt.zcol->guisection = _("3D");

    opt.var_dir_hz = G_define_option();
    opt.var_dir_hz->key = "azimuth";
    opt.var_dir_hz->type = TYPE_DOUBLE;
    opt.var_dir_hz->required = NO;
    opt.var_dir_hz->answer = "45.0";
    opt.var_dir_hz->description =
        _("Azimuth of variogram computing (isotrophic)");
    opt.var_dir_hz->guisection = _("Initial");

    opt.var_dir_vert = G_define_option();
    opt.var_dir_vert->key = "zenith_angle";
    opt.var_dir_vert->type = TYPE_DOUBLE;
    opt.var_dir_vert->required = NO;
    opt.var_dir_vert->answer = "0.0";
    opt.var_dir_vert->description =
        _("Zenith angle of variogram computing (isotrophic)");
    opt.var_dir_vert->guisection = _("Initial");

    opt.nL = G_define_option();
    opt.nL->key = "lpieces";
    opt.nL->type = TYPE_INTEGER;
    opt.nL->required = NO;
    opt.nL->description = _("Number of horizontal lags");
    opt.nL->guisection = _("Initial");

    opt.nZ = G_define_option();
    opt.nZ->key = "vpieces";
    opt.nZ->type = TYPE_INTEGER;
    opt.nZ->required = NO;
    opt.nZ->description =
        _("Number of vertical lags (only for 3D variogram)");
    opt.nZ->guisection = _("Initial");

    opt.td_hz = G_define_option();
    opt.td_hz->key = "td";
    opt.td_hz->type = TYPE_DOUBLE;
    opt.td_hz->answer = "45.0";
    opt.td_hz->description = _("Angle of variogram processing");
    opt.td_hz->required = NO;
    opt.td_hz->guisection = _("Initial");

    opt.nugget_hz = G_define_option();
    opt.nugget_hz->key = "hz_nugget";
    opt.nugget_hz->type = TYPE_DOUBLE;
    opt.nugget_hz->answer = "0.0";
    opt.nugget_hz->description = _("Nugget effect of horizontal variogram");
    opt.nugget_hz->required = NO;
    opt.nugget_hz->guisection = _("Middle");

    opt.nugget_vert = G_define_option();
    opt.nugget_vert->key = "vert_nugget";
    opt.nugget_vert->type = TYPE_DOUBLE;
    opt.nugget_vert->answer = "0.0";
    opt.nugget_vert->description = _("Nugget effect of vertical variogram");
    opt.nugget_vert->required = NO;
    opt.nugget_vert->guisection = _("Middle");

    opt.nugget_final = G_define_option();
    opt.nugget_final->key = "final_nugget";
    opt.nugget_final->type = TYPE_DOUBLE;
    opt.nugget_final->answer = "0.0";
    opt.nugget_final->description =
        _("Nugget effect of anisotropic variogram (or horizontal component of bivariate variogram)");
    opt.nugget_final->required = NO;
    opt.nugget_final->guisection = _("Final");

    opt.nugget_final_vert = G_define_option();
    opt.nugget_final_vert->key = "final_vert_nugget";
    opt.nugget_final_vert->type = TYPE_DOUBLE;
    opt.nugget_final_vert->answer = "0.0";
    opt.nugget_final_vert->description =
        _("For bivariate variogram only: nuget effect of vertical component");
    opt.nugget_final_vert->required = NO;
    opt.nugget_final_vert->guisection = _("Final");

    opt.sill_hz = G_define_option();
    opt.sill_hz->key = "hz_sill";
    opt.sill_hz->type = TYPE_DOUBLE;
    opt.sill_hz->description = _("Sill of horizontal variogram");
    opt.sill_hz->required = NO;
    opt.sill_hz->guisection = _("Middle");

    opt.sill_vert = G_define_option();
    opt.sill_vert->key = "vert_sill";
    opt.sill_vert->type = TYPE_DOUBLE;
    opt.sill_vert->description = _("Sill of vertical variogram");
    opt.sill_vert->required = NO;
    opt.sill_vert->guisection = _("Middle");

    opt.sill_final = G_define_option();
    opt.sill_final->key = "final_sill";
    opt.sill_final->type = TYPE_DOUBLE;
    opt.sill_final->description =
        _("Sill of anisotropic variogram (or horizontal component of bivariate variogram)");
    opt.sill_final->required = NO;
    opt.sill_final->guisection = _("Final");

    opt.sill_final_vert = G_define_option();
    opt.sill_final_vert->key = "final_vert_sill";
    opt.sill_final_vert->type = TYPE_DOUBLE;
    opt.sill_final_vert->description =
        _("For bivariate variogram only: sill of vertical component");
    opt.sill_final_vert->required = NO;
    opt.sill_final_vert->guisection = _("Final");

    opt.range_hz = G_define_option();
    opt.range_hz->key = "hz_range";
    opt.range_hz->type = TYPE_DOUBLE;
    opt.range_hz->description = _("Range of horizontal variogram");
    opt.range_hz->required = NO;
    opt.range_hz->guisection = _("Middle");

    opt.range_vert = G_define_option();
    opt.range_vert->key = "vert_range";
    opt.range_vert->type = TYPE_DOUBLE;
    opt.range_vert->description = _("Range of vertical variogram");
    opt.range_vert->required = NO;
    opt.range_vert->guisection = _("Middle");

    opt.range_final = G_define_option();
    opt.range_final->key = "final_range";
    opt.range_final->type = TYPE_DOUBLE;
    opt.range_final->description =
        _("Range of anisotropic variogram (or horizontal component of bivariate variogram)");
    opt.range_final->required = NO;
    opt.range_final->guisection = _("Final");

    opt.range_final_vert = G_define_option();
    opt.range_final_vert->key = "final_vert_range";
    opt.range_final_vert->type = TYPE_DOUBLE;
    opt.range_final_vert->description =
        _("Range of final variogram: one value for anisotropic, two values for bivariate (hz and vert component)");
    opt.range_final_vert->required = NO;
    opt.range_final_vert->guisection = _("Final");
    /* --------------------------------------------------------- */

    G_gisinit(argv[0]);

    if (G_parser(argc, argv)) {
        exit(EXIT_FAILURE);
    }

    /* Get parameters from the parser */
    if (strcmp(opt.phase->answer, "initial") == 0) {
        xD.phase = 0;           // estimate range
    }
    else if (strcmp(opt.phase->answer, "middle") == 0) {
        xD.phase = 1;           // estimate anisotropic variogram
    }
    else if (strcmp(opt.phase->answer, "final") == 0) {
        xD.phase = 2;           // compute kriging
    }

    // Open report file if desired
    if (opt.report->answer) {
        xD.report.write2file = TRUE;
        xD.report.name = opt.report->answer;

        // initial phase: check if the file exists
        if (xD.phase == 0 && access(xD.report.name, F_OK) != -1) {
            G_fatal_error(_("Report file exists; please set up different name..."));
        }

        // middle / final phase: check if file does not exist
        if (xD.phase != 0 && access(xD.report.name, F_OK) != 0) {
            G_fatal_error(_("Report file does not exist; please check the name or repeat initial phase..."));
        }

        xD.report.fp = fopen(xD.report.name, "a");
        time(&xD.report.now);
        fprintf(xD.report.fp, "v.kriging started on %s\n\n",
                ctime(&xD.report.now));
        G_message(_("Report is being written to %s..."), xD.report.name);
    }
    else {
        xD.report.write2file = FALSE;
        G_warning(_("The name of report file missing..."));
    }

    if (opt.crossvalid->answer) {
        xD.crossvalid.write2file = TRUE;
        xD.crossvalid.name = opt.crossvalid->answer;
        xD.crossvalid.fp = fopen(xD.crossvalid.name, "w");
    }
    else {
        xD.crossvalid.write2file = FALSE;
    }

    var_pars.hz.name = var_pars.vert.name = var_pars.fin.name = opt.input->answer;      // set name of variogram
    var_pars.hz.dir = opt.var_dir_hz->answer ? DEG2RAD(atof(opt.var_dir_hz->answer)) : 0.;      // Azimuth
    var_pars.vert.dir = opt.var_dir_vert->answer ? DEG2RAD(atof(opt.var_dir_vert->answer)) : 0.;        // Zenith angle
    var_pars.fin.dir = opt.var_dir_hz->answer ? DEG2RAD(atof(opt.var_dir_hz->answer)) : 0.;     // Azimuth

    var_pars.hz.td = DEG2RAD(atof(opt.td_hz->answer));  // Angle of variogram processing

    if (opt.nL->answer) {       // Test if nL have been set up (optional)
        var_pars.hz.nLag = atoi(opt.nL->answer);
        if (var_pars.hz.nLag < 1) {     // Invalid value
            G_message(_("Number of horizontal pieces must be at least 1. Default value will be used..."));
            var_pars.hz.nLag = 20;
        }
    }

    if (opt.form_file->answer) {        // Plotting variogram
        set_gnuplot(opt.form_file->answer, &var_pars.hz);
        set_gnuplot(opt.form_file->answer, &var_pars.vert);
        set_gnuplot(opt.form_file->answer, &var_pars.fin);
    }
    else {
        strcpy(var_pars.hz.term, "");
        strcpy(var_pars.vert.term, "");
        strcpy(var_pars.fin.term, "");
    }

    xD.bivar = flg.bivariate->answer == TRUE ? TRUE : FALSE;
    xD.univar = flg.univariate->answer == TRUE ? TRUE : FALSE;
    if (xD.bivar == TRUE && xD.univar == TRUE) {
        if (xD.report.write2file == TRUE) {
            fclose(xD.report.fp);
            remove(xD.report.name);
        }
        G_fatal_error(_("You should mark either univariate, or bivariate variogram, not both of them..."));
    }                           // error

    /* ---------------------------------------------------------- */
    Vect_set_open_level(2);     // Open input vector map

    if (0 > Vect_open_old2(&map, opt.input->answer, "", opt.field->answer)) {
        if (xD.report.write2file == TRUE) {
            fclose(xD.report.fp);
            remove(xD.report.name);
        }
        G_fatal_error(_("Unable to open vector map <%s>"), opt.input->answer);
    }                           // error
    Vect_set_error_handler_io(&map, NULL);
    /* ---------------------------------------------------------- */

    /* Perform 2D or 3D interpolation ? */
    xD.i3 = flg.d23->answer ? FALSE : TRUE;     // 2D/3D interpolation
    xD.v3 = Vect_is_3d(&map);   // 2D/3D layer

    /* What could happen:
     *-------------------
     * 3D interpolation + 3D points = 3D GIS
     * 3D interpolation + 2D points = 2,5D -> 3D GIS (needs attribute column with z and 3D region)
     * 2D interpolation + 3D points = 3D -> 2,5D GIS
     * 2D interpolation + 2D points = 2,5D GIS */

    // 3D interpolation
    if (xD.i3 == TRUE) {        // 3D interpolation:
        if (xD.v3 == FALSE) {   // 2D input:
            if (!opt.zcol->answer) {    // zcolumn not available:
                if (xD.report.write2file == TRUE) {     // close report file
                    fprintf(xD.report.fp,
                            "Error (see standard output). Process killed...");
                    fclose(xD.report.fp);
                }
                G_fatal_error(_("To process 3D interpolation based on 2D input, please set attribute column containing z coordinates or switch to 2D interpolation."));
            }
        }                       // end if zcol == NULL
        // 3D or 2,5D input
        if (opt.nZ->answer) {   // Test if nZ have been set up (optional)
            if (var_pars.vert.nLag < 1) {       // Invalid value
                G_message(_("Number of vertical pieces must be at least 1. Default value will be used..."));
            }
            else {
                var_pars.vert.nLag = atof(opt.nZ->answer);
            }
        }                       // end if nZ->answer
    }                           // end if 3D interpolation

    else {                      // 2D interpolation:
        var_pars.vert.nLag = -1;        // abs will be used in next steps
        if (xD.v3 == TRUE) {
            if (xD.report.write2file == TRUE) { // close report file
                fprintf(xD.report.fp,
                        "Error (see standard output). Process killed...");
                fclose(xD.report.fp);
            }
            G_fatal_error(_("2D interpolation based on 3D input has been temporarily disabled. Please select another option..."));
        }
    }

    field = Vect_get_field_number(&map, opt.field->answer);
    if (xD.report.write2file == TRUE)
        write2file_basics(&xD, &opt);
    /* ---------------------------------------------------------- */

    /* Get... */
    get_region_pars(&xD, &reg); // ... region parameters 
    read_points(&map, &reg, &pnts, &xD, opt.zcol->answer, field, &xD.report);   // ... coordinates of points
    pnts.invals = get_col_values(&map, &xD, &pnts, field, opt.intpl->answer, flg.detrend->answer);      // ... values for interpolation

    /* Estimate 2D/3D variogram */
    switch (xD.phase) {
    case 0:                    // initial phase
        var_pars.hz.type = 0;   // horizontal variogram
        if (xD.i3 == TRUE) {    // 3D interpolation:
            var_pars.vert.type = 1;     // vertical variogram
        }

        variogram_restricts(&xD, &pnts, &var_pars.hz);  // estimate lag size and number of lags (hz)

        if (xD.i3 == TRUE) {    // 3D interpolation:
            variogram_restricts(&xD, &pnts, &var_pars.vert);    // estimate lag size and number of lags (vert)
            if (var_pars.vert.nLag > var_pars.hz.nLag) {        // more lags in vertical than in horizontal direction:
                var_pars.vert.nLag = var_pars.hz.nLag;  // set the numbers to be equal
                var_pars.vert.lag = var_pars.vert.max_dist / var_pars.vert.nLag;        // modify lag size
            }
        }
        E_variogram(0, &xD, &pnts, &var_pars);  // horizontal variogram (for both 2D and 3D interpolation)

        if (xD.report.write2file == FALSE) {
            G_message(_("\nExperimental variogram of your data has been computed. To continue interpolation performance, please repeat initial phase with non-empty <report> parameter..."));
        }

        else {
            if (xD.i3 == TRUE) {        // 3D interpolation:
                E_variogram(1, &xD, &pnts, &var_pars);  // vertical variogram
                G_message(_("\nExperimental variogram of your data has been computed. If you wish to continue with theoretical variograms computation (middle phase), please do not erase temporary files <dataE.dat> and <variogram_hz_tmp.txt> in your working directory. The files are required in the middle phase and they will be deleted automatically."));
            }
            else {
                G_message(_("\nExperimental variogram of your data has been computed. If you wish to continue with theoretical variogram computation and interpolation (final phase), please do not erase temporary files <dataE.dat> and <variogram_hz_tmp.txt> in your working directory. The files are required in the final phase and they will be deleted automatically."));
            }
        }
        goto end;

    case 1:
        read_tmp_vals("variogram_hz_tmp.txt", &var_pars.hz, &xD);       // read properties of horizontal variogram from temp file
        read_tmp_vals("variogram_vert_tmp.txt", &var_pars.vert, &xD);   // read properties of vertical variogram from temp file

        T_variogram(0, TRUE, opt, &var_pars.hz, &xD.report);    // compute theoretical variogram - hz
        T_variogram(1, TRUE, opt, &var_pars.vert, &xD.report);  // compute theoretical variogram - vert

        /* compare range of hz and vert variogram:
           - if the difference is greater than 5% -> bivariate variogram
           - if the difference is smaller than 5% - anisotropic variogram

           => choose variogram type:
         */

        sill_compare(&xD, &flg, &var_pars, &pnts);
        variogram_restricts(&xD, &pnts, &var_pars.fin);

        E_variogram(var_pars.fin.type, &xD, &pnts, &var_pars);
        G_message(_("You may continue to interpolate values (final phase)..."));
        goto end;

    case 2:                    // final phase:
        // Module should crash if:
        if (!opt.output->answer) {      // output name not available:
            if (xD.report.write2file == TRUE) { // report file available:
                fprintf(xD.report.fp,
                        "Error (see standard output). Process killed...");
                fclose(xD.report.fp);
            }
            G_fatal_error(_("Please set up name of output layer..."));
        }

        // read properties of final variogram from temp file
        if (xD.i3 == TRUE) {    // 3D kriging:
            read_tmp_vals("variogram_final_tmp.txt", &var_pars.fin, &xD);
        }
        else {                  // 2D kriging
            read_tmp_vals("variogram_hz_tmp.txt", &var_pars.fin, &xD);
        }

        // check variogram settings
        if (var_pars.fin.type == 2 && strcmp(opt.function_var_final->answer, "linear") != 0) {  // bivariate nonlinear variogram:
            // just one function type is set up (none or both should be)
            if (!
                (opt.function_var_final->answer &&
                 opt.function_var_final_vert->answer) &&
                (opt.function_var_final->answer ||
                 opt.function_var_final_vert->answer)) {
                if (xD.report.write2file == TRUE) {     // report file available:
                    fprintf(xD.report.fp,
                            "Error (see standard output). Process killed...");
                    fclose(xD.report.fp);
                }
                G_fatal_error(_("If you wish to specify components of bivariate variogram please set up function type for both of them..."));
            }

            // if both of the function types are set up:
            if (opt.function_var_final->answer &&
                opt.function_var_final_vert->answer) {
                if (!opt.nugget_final->answer) {        // horizontal nugget effect should not be missing
                    if (xD.report.write2file == TRUE) { // report file available:
                        fprintf(xD.report.fp,
                                "Error (see standard output). Process killed...");
                        fclose(xD.report.fp);
                    }
                    G_fatal_error(_("Please set up nugget effect of horizontal component of bivariate variogram..."));
                }

                if (!opt.nugget_final_vert->answer) {   // vertical nugget effect should not be missing
                    if (xD.report.write2file == TRUE) { // report file available:
                        fprintf(xD.report.fp,
                                "Error (see standard output). Process killed...");
                        fclose(xD.report.fp);
                    }
                    G_fatal_error(_("Please set up nugget effect of vertical component of bivariate variogram..."));
                }

                if (!opt.range_final->answer) { // horizontal range should not be missing
                    if (xD.report.write2file == TRUE) { // report file available:
                        fprintf(xD.report.fp,
                                "Error (see standard output). Process killed...");
                        fclose(xD.report.fp);
                    }
                    G_fatal_error(_("Please set up range of horizontal component of bivariate variogram..."));
                }

                if (!opt.range_final_vert->answer) {    // vertical range should not be missing
                    if (xD.report.write2file == TRUE) { // report file available:
                        fprintf(xD.report.fp,
                                "Error (see standard output). Process killed...");
                        fclose(xD.report.fp);
                    }
                    G_fatal_error(_("Please set up range of vertical component of bivariate variogram..."));
                }
            }
        }

        else {                  // univariate variogram
            if (xD.i3 == TRUE && (strcmp(opt.function_var_final->answer, "linear") != 0 && strcmp(opt.function_var_final->answer, "parabolic") != 0)) { // anisotropic 3D: 
                if (opt.function_var_final_vert->answer || atof(opt.nugget_final_vert->answer) != 0. || opt.range_final_vert->answer) { // vertical settings available:
                    G_fatal_error(_("Not necessary to set up vertical components properties. Anisotropic variogram will be used..."));
                }               // end if vert settings available     
            }                   // end if 3D

            if (!opt.function_var_final->answer) {      // missing function
                opt.function_var_final->answer = "linear";
                G_message(_("Linear variogram will be computed..."));
            }

            if (strcmp(opt.function_var_final->answer, "linear") != 0 && strcmp(opt.function_var_final->answer, "parabolic") != 0) {    // nonlinear and not parabolic:
                if (!opt.nugget_final->answer) {        // missing horizontal nugget effect
                    if (xD.report.write2file == TRUE) { // report file available:
                        fprintf(xD.report.fp,
                                "Error (see standard output). Process killed...");
                        fclose(xD.report.fp);
                    }
                    G_fatal_error(_("Please set up nugget effect..."));
                }               // end if nugget missing

                if (!opt.range_final->answer) { // missing horizontal range:
                    if (xD.report.write2file == TRUE) { // report file available:
                        fprintf(xD.report.fp,
                                "Error (see standard output). Process killed...");
                        fclose(xD.report.fp);
                    }
                    G_fatal_error(_("Please set up range..."));
                }               // end if range missing

                if (opt.sill_final->answer) {   // missing horizontal range:
                    var_pars.fin.sill = atof(opt.sill_final->answer);
                }               // end if sill has been changed by the user
            }                   // end nonlinear and not parabolic variogram
        }                       // end if univariate variogram (2D or 3D)

        out.name = opt.output->answer;  // Output layer name

        if (var_pars.fin.type == 3) {   // if variogram is anisotropic:
            geometric_anisotropy(&xD, &pnts);   // exaggerate z coord and rebuild the spatial index
        }

        T_variogram(var_pars.fin.type, xD.i3, opt, &var_pars.fin, &xD.report);  // compute theoretical variogram
        break;
    }

    /* Ordinary kriging (including 2D/3D raster creation) */
    ordinary_kriging(&xD, &reg, &pnts, &var_pars, &out);
    /* ---------------------------------------------------------- */

  end:

    G_free(pnts.r);
    Vect_close(&map);           // Close vector map
    exit(EXIT_SUCCESS);
}
