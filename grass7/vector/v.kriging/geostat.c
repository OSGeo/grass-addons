#include "local_proto.h"

/* experimental variogram 
 * based on  2D variogram (alghalandis.com/?page_id=463)) */
void E_variogram(int type, struct int_par *xD, struct points *pnts,
                 struct var_par *pars)
{
    // Variogram properties
    struct parameters *var_pars;
    double max_dist, max_dist_vert;     // max distance of interpolated points
    double radius, radius_vert; // radius of interpolation in the horizontal plane

    switch (type) {
    case 0:                    // horizontal variogram
        var_pars = &pars->hz;   // 0: horizontal variogram
        break;
    case 1:                    // vertica variogram
        var_pars = &pars->vert; // 1: vertical variogram    
        break;
    case 2:                    // bivariate variogram
        var_pars = &pars->fin;

        max_dist = var_pars->horizontal.max_dist;
        max_dist_vert = var_pars->vertical.max_dist;
        radius_vert = SQUARE(max_dist_vert);
        break;
    case 3:                    //anisotropic variogram
        var_pars = &pars->fin;  // default: final variogram
        max_dist = max_dist_vert = var_pars->max_dist;
        radius = radius_vert = SQUARE(max_dist);
        break;
    }

    if (type < 2) {
        max_dist = var_pars->max_dist;
    }
    radius = SQUARE(max_dist);

    // Local variables
    int n = pnts->n;            // # of input points
    double *pnts_r = pnts->r;   // xyz coordinates of input points
    double *r;                  // pointer to xyz coordinates
    double *search;             // pointer to search point coordinates
    double *vals = pnts->invals;        // values to be used for interpolation
    int phase = xD->phase;      // phase: initial / middle / final

    int nLag;                   // # of horizontal bins
    int nLag_vert;              // # of vertical bins
    double *vert;               // pointer to vertical bins
    double dir = var_pars->dir; // azimuth
    double td = var_pars->td;   // angle tolerance
    double lag = var_pars->lag; // size of horizontal bin
    double lag_vert;

    if (type == 2) {            // bivariate variogram
        nLag = var_pars->horizontal.nLag;
        nLag_vert = var_pars->vertical.nLag;

        dir = var_pars->dir;
        td = var_pars->td;
        lag = var_pars->horizontal.lag;
        lag_vert = var_pars->vertical.lag;
    }

    else {                      // univariate variogram 
        nLag = var_pars->nLag;
        dir = var_pars->dir;
        td = var_pars->td;
        lag = var_pars->lag;
    }

    // depend on variogram type: 
    int nrows = nLag;
    int ncols = type == 2 ? nLag_vert : 1;

    struct write *report = &xD->report;

    // Variogram processing variables
    int s;                      // index of horizontal segment
    int b;                      // index of verical segment (bivariate only)
    int i, j;                   // indices of the input points
    int err0 = 0;               // number of invalid values

    double *dr;                 // coordinate differences of each couple
    double *h;                  // distance of boundary of the horizontal segment
    double tv;                  // bearing of the line between the couple of the input points
    double ddir1, ddir2;        // the azimuth of computing variogram
    double rv;                  // radius of the couple of points
    double rvh;                 // difference between point distance and the horizontal segment boundary
    double dv;                  // difference of the values to be interpolated that are located on the couple of points

    struct ilist *list;         // list of selected nearest neighbours
    int n_vals;                 // # of selected NN

    double *i_vals, *j_vals;    // values located on the point couples

    int *ii;                    // difference of indices between rellevant input points

    double gamma_lag;           // sum of dissimilarities in one bin
    double cpls;                // # of dissimilarities in one bin
    mat_struct *gamma_M;        // gamma matrix (hz, vert or bivar)
    mat_struct *c_M;            // matrix of # of dissimilarities
    double *gamma;              // pointer to gamma matrix
    double *c;                  // pointer to c matrix

    unsigned int percents = 50;

    double gamma_sum;           // sum of gamma elements (non-nan)
    int gamma_n;                // # of gamma elements (non-nan)

    /* Allocated vertices and matrices:
     * --------------------------------
     * dr - triple of coordinate differences (e.g. dx, dy, dz)
     * h - vector of length pieces [nL x 1]
     * vert - vector of vertical pieces [nZ x 1] (3D only)
     * c - matrix containing number of points in each sector defined by h (and vert) [nL x nZ; in 2D nZ = 1]
     * gama - matrix of values of experimental variogram
     */

    // allocate:
    dr = (double *)G_malloc(3 * sizeof(double));        // vector of coordinate differences
    search = (double *)G_malloc(3 * sizeof(double));    // vector of search point coordinates

    if (type != 2) {
        var_pars->h = (double *)G_malloc(nLag * sizeof(double));        // vector of bins
    }

    if (type == 2) {
        var_pars->horizontal.h = (double *)G_malloc(nLag * sizeof(double));     // vector of bins
        var_pars->vertical.h = (double *)G_malloc(nLag_vert * sizeof(double));  // vector of bins
    }

    // control initialization:
    if (dr == NULL || search == NULL || var_pars->h == NULL ||
        (type == 2 && var_pars->vert == NULL)) {
        if (xD->report.write2file == TRUE) {    // close report file
            fprintf(xD->report.fp,
                    "Error (see standard output). Process killed...");
            fclose(xD->report.fp);
        }
        G_fatal_error(_("Memory allocation failed..."));
    }

    // initialize:
    c_M = G_matrix_init(nrows, ncols, nrows);   // temporal matrix of counts
    gamma_M = G_matrix_init(nrows, ncols, nrows);       // temporal matrix (vector) of gammas

    if (c_M == NULL || gamma_M == NULL) {
        if (xD->report.write2file == TRUE) {    // close report file
            fprintf(xD->report.fp,
                    "Error (see standard output). Process killed...");
            fclose(xD->report.fp);
        }
        G_fatal_error(_("Memory allocation failed..."));
    }

    // set up pointers
    c = &c_M->vals[0];
    gamma = &gamma_M->vals[0];

    // set up starting values
    gamma_sum = 0.;
    gamma_n = 0;

    if (percents) {
        G_percent_reset();
    }

    if (type == 2) {
        vert = &var_pars->vertical.h[0];
    }

    /* *** Experimental variogram computation *** */
    for (b = 0; b < ncols; b++) {       // for each vertical lag...
        if (type == 2) {        // just in case that the variogram is vertical
            *vert = (b + 1) * lag_vert; // lag distance
        }

        h = type == 2 ? &var_pars->horizontal.h[0] : &var_pars->h[0];   // ... horizontal lags

        for (s = 0; s < nrows; s++) {   // for each horizontal lag (isotrophy!!!)...
            *h = (s + 1) * lag; // lag distance
            r = &pnts->r[0];    // pointer to the input coordinates

            // for every bs cycle ...
            i_vals = &vals[0];  // pointer to input values to be interpolated 
            gamma_lag = 0.;     // gamma in dir direction and h distance
            cpls = 0.;          // count of couples in dir direction and h distance     

            /* Compute variogram for points in relevant neighbourhood */
            for (i = 0; i < n - 1; i++) {       // for each input point... 
                search = &pnts->r[3 * i];
                switch (type) { // find NNs according to variogram type
                case 0:        // horizontal variogram
                    list = find_NNs_within(2, search, pnts, max_dist, -1);
                    break;
                case 1:        // vertical variogram
                    list = find_NNs_within(1, search, pnts, -1, max_dist);
                    break;
                default:       // anisotropic or bivariate variogram    
                    list =
                        find_NNs_within(3, search, pnts, max_dist,
                                        max_dist_vert);
                    break;
                }

                n_vals = list->n_values;        // # of input values located on NN
                if (n_vals > 0) {
                    correct_indices(list, r, pnts, var_pars);
                    ii = &list->value[0];       // indices of these input values (note: increased by 1)
                    j_vals = &vals[*ii];        // pointer to input values

                    for (j = 1; j < n_vals; j++) {      // for each point within overlapping rectangle
                        if (*ii > i) {  // use the points just once
                            coord_diff(i, *ii, pnts_r, dr);     // compute coordinate differences 

                            // Variogram processing
                            if (type == 1) {    // vertical variogram:
                                tv = 0.5 * PI - zenith_angle(dr);       // compute zenith angle instead of bearing
                                td = 0.5 * PI;  // todo: repair, 0.25 usually
                            }
                            else {      // hz / aniso / bivar variogram: 
                                tv = atan2(*(dr + 1), *dr);     // bearing
                                if (tv < 0.) {
                                    tv += 2. * PI;
                                }
                            }

                            ddir1 = dir - tv;   // difference between bearing and azimuth
                            ddir2 = (dir + PI) - tv;

                            if (fabs(ddir1) <= td || fabs(ddir2) <= td) {       // angle test: compare the diff with critical value
                                // test squared distance: vertical variogram => 0., ...
                                rv = type == 1 ? 0. : radius_hz_diff(dr);       // ... otherwise horizontal distance

                                if (type == 1 || type == 3) {   // vertical or anisotropic variogram:
                                    rv += SQUARE(*(dr + 2));    // consider also vertical direction
                                }

                                rvh = sqrt(rv) - *h;    // the difference between distance and lag
                                if (rv <= radius && fabs(rvh) <= lag) { // distance test: compare the distance with critical value and find out if the j-point is located within i-lag
                                    if (type == 2) {    // vertical test for bivariate variogram:
                                        rvh = *(dr + 2) - *vert;        // compare vertical

                                        if (fabs(rvh) <= lag_vert) {    // elevation test: vertical lag
                                            goto delta_V;
                                        }
                                        else {
                                            goto end;
                                        }
                                    }
                                  delta_V:
                                    dv = *j_vals - *i_vals;     // difference of values located on pair of points i, j
                                    gamma_lag += SQUARE(dv);    // sum of squared differences
                                    cpls += 1.; // count of elements
                                }       // end distance test: rv <= radius ^ |rvh| <= lag
                            }   // end angle test: |ddir| <= td
                        }       // end i test: *ii > i
                      end:
                        ii++;   // go to the next index
                        j_vals += *ii - *(ii - 1);      // go to the next value 
                    }           // end j for loop: points within overlapping rectangles
                }               // end test: n_vals > 0
                else {
                    if (report->name) { // close report file
                        fprintf(report->fp,
                                "Error (see standard output). Process killed...");
                        fclose(report->fp);
                    }
                    G_fatal_error(_("This point does not have neighbours in given radius..."));
                }

                r += 3;         // go to the next search point
                i_vals++;       // and to its value
            }                   // end for loop i: variogram computation for each i-th search point

            if (isnan(gamma_lag) || cpls == 0.0) {      // empty lags:
                err0++;         // error indicator
                goto gamma_isnan;
            }

            *gamma = 0.5 * gamma_lag / cpls;    // element of gamma matrix     
            *c = cpls;          // # of values that have been used to compute gamma_e

            gamma_sum += *gamma;        // sum of gamma elements (non-nan)
            gamma_n++;          // # of gamma elements (non-nan)

          gamma_isnan:         // there are no available point couples to compute the dissimilarities in the lag:
            h++;
            c++;
            gamma++;
        }                       // end for loop s

        if (type == 2) {        // vertical variogram:
            vert++;
        }
    }                           // end for loop b

    if (err0 == nLag) {         // todo> kedy nie je riesitelny teoreticky variogram?
        if (report->write2file == TRUE) {       // close report file
            fprintf(report->fp,
                    "Error (see standard output). Process killed...");
            fclose(report->fp);
        }
        G_fatal_error(_("Unable to compute experimental variogram..."));
    }                           // end error

    var_pars->gamma = G_matrix_copy(gamma_M);
    var_pars->gamma_sum = gamma_sum;
    var_pars->gamma_n = gamma_n;

    plot_experimental_variogram(xD, var_pars);

    if (phase < 2) {            // initial and middle phase:
        sill(var_pars);         // compute sill
    }

    if (report->write2file == TRUE) {   // report file available: 
        write2file_variogram_E(xD, var_pars, c_M);      // write to file
    }

    write_temporary2file(xD, var_pars);

    G_free_ilist(list);         // free list memory
    G_matrix_free(c_M);
    G_matrix_free(gamma_M);
}

/* theoretical variogram */
void T_variogram(int type, int i3, struct opts opt,
                 struct parameters *var_pars, struct write *report)
{
    char *variogram;

    // report
    if (report->write2file == TRUE) {   // report file available:
        time(&report->now);     // write down time of start
        if (type != 1) {
            fprintf(report->fp,
                    "\nComputation of theoretical variogram started on %s\n",
                    ctime(&report->now));
        }
    }

    // set up:
    var_pars->type = type;      // hz / vert / bivar / aniso
    var_pars->const_val = 0;    // input values are not constants

    switch (type) {
    case 0:                    // horizontal variogram
        if (i3 == TRUE) {       // 3D interpolation (middle phase)
            variogram = opt.function_var_hz->answer;    // function type available:
            var_pars->function = set_function(variogram, report);

            if (strcmp(variogram, "linear") != 0 && strcmp(variogram, "parabolic") != 0) {      // nonlinear or not parabolic
                var_pars->nugget = atof(opt.nugget_hz->answer);
                var_pars->h_range = atof(opt.range_hz->answer);
                if (opt.sill_hz->answer) {
                    var_pars->sill = atof(opt.sill_hz->answer);
                }
            }
            else {              // function type not available:
                LMS_variogram(var_pars, report);
            }
        }
        else {                  // 2D interpolation (final phase)
            variogram = opt.function_var_final->answer; // function type available:
            var_pars->function = set_function(variogram, report);

            if (strcmp(variogram, "linear") != 0 && strcmp(variogram, "parabolic") != 0) {      // nonlinear or not parabolic      
                var_pars->nugget = atof(opt.nugget_final->answer);
                var_pars->h_range = atof(opt.range_final->answer);
                if (opt.sill_final->answer) {
                    var_pars->sill = atof(opt.sill_final->answer);
                }
            }
            else {              // function type not available:
                LMS_variogram(var_pars, report);
            }
        }

        if (report->name) {
            fprintf(report->fp, "Parameters of horizontal variogram:\n");
            fprintf(report->fp, "Nugget effect: %f\n", var_pars->nugget);
            fprintf(report->fp, "Sill:          %f\n", var_pars->sill);
            fprintf(report->fp, "Range:         %f\n", var_pars->h_range);
        }
        break;

    case 1:                    // vertical variogram
        var_pars->nugget = atof(opt.nugget_vert->answer);
        var_pars->h_range = atof(opt.range_vert->answer);
        if (opt.sill_vert->answer) {
            var_pars->sill = atof(opt.sill_vert->answer);
        }
        variogram = opt.function_var_vert->answer;
        var_pars->function = set_function(variogram, report);

        if (report->name) {
            fprintf(report->fp, "Parameters of vertical variogram:\n");
            fprintf(report->fp, "Nugget effect: %f\n", var_pars->nugget);
            fprintf(report->fp, "Sill:          %f\n", var_pars->sill);
            fprintf(report->fp, "Range:         %f\n", var_pars->h_range);
        }
        break;
    case 2:                    // bivariate variogram (just final phase)
        if (!(opt.function_var_final->answer && opt.function_var_final_vert->answer) || strcmp(opt.function_var_final->answer, "linear") == 0) {        // planar function:
            var_pars->function = 5;     // planar variogram (3D)
            LMS_variogram(var_pars, report);
        }

        else {                  // function type was set up by the user:
            var_pars->horizontal.nugget = atof(opt.nugget_final->answer);
            var_pars->horizontal.h_range = atof(opt.range_final->answer);
            if (opt.sill_final->answer) {
                var_pars->horizontal.sill = atof(opt.sill_final->answer);
            }

            var_pars->vertical.nugget = atof(opt.nugget_final_vert->answer);
            var_pars->vertical.h_range = atof(opt.range_final_vert->answer);
            if (opt.sill_final_vert->answer) {
                var_pars->vertical.sill = atof(opt.sill_final_vert->answer);
            }

            var_pars->horizontal.function =
                set_function(opt.function_var_final->answer, report);
            var_pars->vertical.function =
                set_function(opt.function_var_final_vert->answer, report);

            if (report->name) {
                fprintf(report->fp, "Parameters of bivariate variogram:\n");
                fprintf(report->fp, "Nugget effect (hz):   %f\n",
                        var_pars->horizontal.nugget);
                fprintf(report->fp, "Sill (hz):            %f\n",
                        var_pars->horizontal.sill);
                fprintf(report->fp, "Range (hz):           %f\n",
                        var_pars->horizontal.h_range);
                fprintf(report->fp, "Function: %s\n\n",
                        opt.function_var_hz->answer);
                fprintf(report->fp, "Nugget effect (vert): %f\n",
                        var_pars->vertical.nugget);
                fprintf(report->fp, "Sill (vert):          %f\n",
                        var_pars->vertical.sill);
                fprintf(report->fp, "Range (vert):         %f\n",
                        var_pars->vertical.h_range);
                fprintf(report->fp, "Function: %s\n",
                        opt.function_var_vert->answer);
            }
        }

        plot_var(i3, TRUE, var_pars);   // Plot variogram using gnuplot
        break;

    case 3:                    // univariate (just final phase)
        variogram = opt.function_var_final->answer;
        var_pars->function = set_function(variogram, report);

        if (strcmp(variogram, "linear") != 0 && strcmp(variogram, "parabolic") != 0) {  // nonlinear and not parabolic variogram:
            var_pars->nugget = atof(opt.nugget_final->answer);
            var_pars->h_range = atof(opt.range_final->answer);
            if (opt.sill_final->answer) {
                var_pars->sill = atof(opt.sill_final->answer);
            }
            variogram = opt.function_var_final->answer;
            if (report->write2file == TRUE) {
                if (i3 == TRUE) {       // 3D interpolation:
                    fprintf(report->fp,
                            "Parameters of anisotropic variogram:\n");
                }
                else {
                    fprintf(report->fp, "Parameters of 2D variogram:\n");
                }
                fprintf(report->fp, "Nugget effect: %f\n", var_pars->nugget);
                fprintf(report->fp, "Sill:          %f\n", var_pars->sill);
                fprintf(report->fp, "Range:         %f\n", var_pars->h_range);
            }
        }
        else {                  // linear or parabolic variogram
            LMS_variogram(var_pars, report);
        }
        break;
    }

    if (type != 2) {
        plot_var(i3, FALSE, var_pars);  // Plot variogram using gnuplot
    }
}

void ordinary_kriging(struct int_par *xD, struct reg_par *reg,
                      struct points *pnts, struct var_par *pars,
                      struct output *out)
{
    G_fatal_error(_("Interpolating values is currently under maintenance (optimization). Theoretical variogram of your data has been computed."));
    // Local variables
    int i3 = xD->i3;
    double *vals = pnts->invals;        // values to be used for interpolation
    struct write *report = &xD->report;
    struct write *crossvalid = &xD->crossvalid;
    struct parameters *var_par = &pars->fin;

    int type = var_par->type;
    double max_dist =
        type == 2 ? var_par->horizontal.max_dist : var_par->max_dist;
    //max_dist = sqrt(0.5 * SQUARE(max_dist));

    double max_dist_vert =
        type == 2 ? var_par->vertical.max_dist : var_par->max_dist;

    unsigned int percents = 50; // counter
    unsigned int row, col, dep; // indices of cells/voxels
    double rslt_OK;             // interpolated value located on r0

    pnts->max_dist = var_par->lag;
    struct ilist *list;

    double *r0;                 // xyz coordinates of cell/voxel centre
    mat_struct *GM;
    mat_struct *GM_sub;         // submatrix of selected points
    mat_struct *GM_Inv;         // inverted GM (GM_sub) matrix
    mat_struct *g0;             // diffences between known and unknown values = theor_var(dist)
    mat_struct *w0;             // weights of values located on the input points 

    // Cell/voxel center coords (location of interpolated value)
    r0 = (double *)G_malloc(3 * sizeof(double));

    if (report->write2file) {   // report file available:
        time(&report->now);
        fprintf(report->fp, "Interpolating values started on %s\n\n",
                ctime(&report->now));
        fflush(report->fp);
    }

    G_message(_("Interpolating unknown values..."));
    G_fatal_error(_("... is currently under maintenance (optimization). Theoretical variogram of your data has been computed."));
    if (percents) {
        G_percent_reset();
    }

    open_layer(xD, reg, out);   // open 2D/3D raster

    if (var_par->const_val == 1) {      // input values are constant:
        goto constant_voxel_centre;
    }

    GM = set_up_G(pnts, var_par, &xD->report);  // set up matrix of dissimilarities of input points
    var_par->GM = G_matrix_copy(GM);    // copy matrix because of cross validation

    // perform cross validation...
    if (crossvalid->write2file) {       // ... if desired
        crossvalidation(xD, pnts, var_par);
    }

  constant_voxel_centre:
    for (dep = 0; dep < reg->ndeps; dep++) {
        if (xD->i3 == TRUE) {
            if (percents) {
                G_percent(dep, reg->ndeps, 1);
            }
        }
        for (row = 0; row < reg->nrows; row++) {
            if (xD->i3 == FALSE) {
                if (percents) {
                    G_percent(row, reg->nrows, 1);
                }
            }
            //#pragma omp parallel for private(col, r0, GM, GM_Inv, g0, w0, rslt_OK)
            for (col = 0; col < reg->ncols; col++) {

                if (var_par->const_val == 1) {  // constant input values
                    goto constant_voxel_val;
                }

                cell_centre(col, row, dep, xD, reg, r0, var_par);       // coords of output point

                // add cell centre to the R-tree
                list = G_new_ilist();   // create list of overlapping rectangles

                if (i3 == TRUE) {       // 3D kriging:
                    list =
                        find_NNs_within(3, r0, pnts, max_dist, max_dist_vert);
                }
                else {          // 2D kriging:
                    list =
                        find_NNs_within(2, r0, pnts, max_dist, max_dist_vert);
                }

                if (list->n_values > 1) {       // positive # of selected points: 
                    correct_indices(list, r0, pnts, var_par);

                    GM_sub = submatrix(list, GM, report);       // make submatrix for selected points
                    GM_Inv = G_matrix_inverse(GM_sub);  // invert submatrix
                    G_matrix_free(GM_sub);

                    g0 = set_up_g0(xD, pnts, list, r0, var_par);        // Diffs inputs - unknowns (incl. cond. 1))
                    w0 = G_matrix_product(GM_Inv, g0);  // Vector of weights, condition SUM(w) = 1 in last row

                    G_matrix_free(GM_Inv);
                    G_matrix_free(g0);

                    rslt_OK = result(pnts, list, w0);   // Estimated cell/voxel value rslt_OK = w x inputs
                    G_matrix_free(w0);
                }
                else if (list->n_values == 1) {
                    rslt_OK = vals[list->value[0] - 1]; // Estimated cell/voxel value rslt_OK = w x inputs
                }
                else if (list->n_values == 0) {
                    if (report->write2file) {   // report file available:
                        fprintf(report->fp,
                                "Error (see standard output). Process killed...");
                        fclose(report->fp);
                    }
                    G_fatal_error(_("This point does not have neighbours in given radius..."));
                }               // end else: error

                G_free_ilist(list);     // free list memory  

                // Create output
              constant_voxel_val:
                if (var_par->const_val == 1) {  // constant input values:
                    rslt_OK = (double)*vals;    // setup input as output
                }

                // write output to the (3D) raster layer
                if (write2layer(xD, reg, out, col, row, dep, rslt_OK) == 0) {
                    if (report->write2file) {   // report file available
                        fprintf(report->fp,
                                "Error (see standard output). Process killed...");
                        fclose(report->fp);     // close report file
                    }
                    G_fatal_error(_("Error writing result into output layer..."));
                }
            }                   // end col
        }                       // end row 
    }                           // end dep

    if (report->write2file) {
        fprintf(report->fp,
                "\n************************************************\n\n");
        time(&report->now);
        fprintf(report->fp, "v.kriging completed on %s", ctime(&report->now));
        fclose(report->fp);
    }

    switch (xD->i3) {
    case TRUE:
        Rast3d_close(out->fd_3d);       // Close 3D raster map
        break;
    case FALSE:
        Rast_close(out->fd_2d); // Close 2D raster map
        break;
    }
}
