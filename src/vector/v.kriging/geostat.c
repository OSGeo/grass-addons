#include "local_proto.h"

/* experimental variogram
 * based on  2D variogram (alghalandis.com/?page_id=463)) */
void E_variogram(int type, struct int_par *xD, struct points *pnts,
                 struct var_par *pars)
{
    // Variogram properties
    struct parameters *var_pars;
    int direction;
    double max_dist, max_dist_vert; // max distance of interpolated points
    double radius,
        radius_vert; // radius of interpolation in the horizontal plane

    switch (type) {
    case 0:                   // horizontal variogram
        var_pars = &pars->hz; // 0: horizontal variogram
        direction = 12;
        break;
    case 1:                     // vertical variogram
        var_pars = &pars->vert; // 1: vertical variogram
        direction = 3;
        break;
    case 2: // bivariate variogram
        var_pars = &pars->fin;

        max_dist = var_pars->horizontal.max_dist;
        max_dist_vert = var_pars->vertical.max_dist;
        radius_vert = SQUARE(max_dist_vert);
        break;
    case 3:                    // anisotropic variogram
        var_pars = &pars->fin; // default: final variogram
        max_dist = max_dist_vert = var_pars->max_dist;
        radius = radius_vert = SQUARE(max_dist);
        direction = 0;
        break;
    }

    if (type < 2) {
        max_dist = var_pars->max_dist;
    }
    radius = SQUARE(max_dist);

    // Local variables
    int n = pnts->n;             // # of input points
    double *pnts_r = pnts->r;    // xyz coordinates of input points
    double *r;                   // pointer to xyz coordinates
    double *search;              // pointer to search point coordinates
    double *vals = pnts->invals; // values to be used for interpolation
    int phase = xD->phase;       // phase: initial / middle / final

    int nLag;                   // # of horizontal bins
    int nLag_vert;              // # of vertical bins
    double *vert;               // pointer to vertical bins
    double dir = var_pars->dir; // azimuth
    double td = var_pars->td;   // angle tolerance
    double lag = var_pars->lag; // size of horizontal bin
    double lag_vert;

    if (type == 2) { // bivariate variogram
        nLag = var_pars->horizontal.nLag;
        nLag_vert = var_pars->vertical.nLag;

        dir = var_pars->dir;
        td = var_pars->td;
        lag = var_pars->horizontal.lag;
        lag_vert = var_pars->vertical.lag;
    }

    else { // univariate variogram
        nLag = var_pars->nLag;
        dir = var_pars->dir;
        td = var_pars->td;
        lag = var_pars->lag;
    }

    // depend on variogram type:
    int nrows = nLag;
    int ncols = type == 2 ? nLag_vert : 1;

    struct write *report = xD->report;

    // Variogram processing variables
    int s;        // index of horizontal segment
    int b;        // index of verical segment (bivariate only)
    int i, j;     // indices of the input points
    int err0 = 0; // number of invalid values

    double *dr; // coordinate differences of each couple
    double *h;  // distance of boundary of the horizontal segment
    double tv;  // bearing of the line between the couple of the input points
    double ddir1, ddir2; // the azimuth of computing variogram
    double rv;           // radius of the couple of points
    double rvh; // difference between point distance and the horizontal segment
                // boundary
    double dv;  // difference of the values to be interpolated that are located
                // on the couple of points

    struct ilist *list; // list of selected nearest neighbours
    int n_vals;         // # of selected NN

    double *i_vals, *j_vals; // values located on the point couples

    int *ii; // difference of indices between rellevant input points

    double gamma_lag;    // sum of dissimilarities in one bin
    double cpls;         // # of dissimilarities in one bin
    mat_struct *gamma_M; // gamma matrix (hz, vert or bivar)
    mat_struct *c_M;     // matrix of # of dissimilarities
    double *gamma;       // pointer to gamma matrix
    double *c;           // pointer to c matrix

    unsigned int percents = 50;

    double gamma_sum; // sum of gamma elements (non-nan)
    int gamma_n;      // # of gamma elements (non-nan)

    /* Allocated vertices and matrices:
     * --------------------------------
     * dr - triple of coordinate differences (e.g. dx, dy, dz)
     * h - vector of length pieces [nL x 1]
     * vert - vector of vertical pieces [nZ x 1] (3D only)
     * c - matrix containing number of points in each sector defined by h (and
     * vert) [nL x nZ; in 2D nZ = 1] gama - matrix of values of experimental
     * variogram
     */

    // allocate:
    dr = (double *)G_malloc(3 *
                            sizeof(double)); // vector of coordinate differences
    search = (double *)G_malloc(
        3 * sizeof(double)); // vector of search point coordinates

    if (type != 2) {
        var_pars->h =
            (double *)G_malloc(nLag * sizeof(double)); // vector of bins
    }

    if (type == 2) {
        var_pars->horizontal.h =
            (double *)G_malloc(nLag * sizeof(double)); // vector of bins
        var_pars->vertical.h =
            (double *)G_malloc(nLag_vert * sizeof(double)); // vector of bins
    }

    // control initialization:
    if (dr == NULL || search == NULL || var_pars->h == NULL ||
        (type == 2 && var_pars->vert == NULL)) {
        report_error(xD->report);
        G_fatal_error(_("Memory allocation failed..."));
    }

    // initialize:
    c_M = G_matrix_init(nrows, ncols, nrows); // temporal matrix of counts
    gamma_M = G_matrix_init(nrows, ncols,
                            nrows); // temporal matrix (vector) of gammas

    if (c_M == NULL || gamma_M == NULL) {
        report_error(xD->report);
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
    for (b = 0; b < ncols; b++) { // for each vertical lag...
        if (type == 2) {          // just in case that the variogram is vertical
            *vert = (b + 1) * lag_vert; // lag distance
        }

        h = type == 2 ? &var_pars->horizontal.h[0]
                      : &var_pars->h[0]; // ... horizontal lags

        for (s = 0; s < nrows;
             s++) {             // for each horizontal lag (isotrophy!!!)...
            *h = (s + 1) * lag; // lag distance

            // for every bs cycle ...
            r = &pnts->r[0];   // pointer to the input coordinates
            i_vals = &vals[0]; // pointer to input values to be interpolated
            gamma_lag = 0.;    // gamma in dir direction and h distance
            cpls = 0.; // count of couples in dir direction and h distance

            /* Compute variogram for points in relevant neighbourhood */
            for (i = 0; i < n - 1; i++) { // for each input point...
                search = &pnts->r[3 * i];
                switch (type) { // find NNs according to variogram type
                case 0:         // horizontal variogram
                    list = find_NNs_within(2, search, pnts, max_dist, -1);
                    break;
                case 1: // vertical variogram
                    list = find_NNs_within(1, search, pnts, -1, max_dist);
                    break;
                default: // anisotropic or bivariate variogram
                    list = find_NNs_within(3, search, pnts, max_dist,
                                           max_dist_vert);
                    break;
                }

                n_vals = list->n_values; // # of input values located on NN
                if (n_vals > 0) {
                    correct_indices(direction, list, r, pnts, var_pars);
                    ii = &list->value[0]; // indices of these input values
                                          // (note: increased by 1)
                    j_vals = &vals[*ii];  // pointer to input values

                    for (j = 1; j < n_vals;
                         j++) { // for each point within overlapping rectangle
                        if (*ii > i) { // use the points just once
                            coord_diff(i, *ii, pnts_r,
                                       dr); // compute coordinate differences

                            // Variogram processing
                            if (type == 1) { // vertical variogram:
                                tv = 0.5 * PI -
                                     zenith_angle(dr); // compute zenith angle
                                                       // instead of bearing
                                td = 0.5 * PI; // todo: repair, 0.25 usually
                            }
                            else { // hz / aniso / bivar variogram:
                                tv = atan2(*(dr + 1), *dr); // bearing
                            }

                            ddir1 =
                                tv -
                                dir; // difference between bearing and azimuth
                            ddir2 = tv + (PI - dir); // reverse

                            if (fabsf(ddir1) <= td ||
                                fabsf(ddir2) <=
                                    td) { // angle test: compare the diff with
                                          // critical value
                                // test squared distance: vertical variogram =>
                                // 0., ...
                                rv = type == 1 ? 0.
                                               : radius_hz_diff(
                                                     dr); // ... otherwise
                                                          // horizontal distance

                                if (type == 1 ||
                                    type == 3) { // vertical or anisotropic
                                                 // variogram:
                                    rv += SQUARE(*(
                                        dr +
                                        2)); // consider also vertical direction
                                }

                                rvh = *h - sqrt(rv); // the difference between
                                                     // distance and lag
                                // distance test: compare the distance with
                                // critical value: find out if the j-point is
                                // located within i-lag
                                if (rv <= radius && 0. <= rvh &&
                                    rvh <= lag) { // 0. <= rvh && rvh <= lag
                                    // vertical test for bivariate variogram:
                                    if (type == 2) {
                                        rvh = *(dr + 2) -
                                              *vert; // compare vertical

                                        if (fabs(rvh) <=
                                            lag_vert) { // elevation test:
                                                        // vertical lag
                                            goto delta_V;
                                        }
                                        else {
                                            goto end;
                                        }
                                    } // end if: type == 2
                                delta_V:
                                    dv =
                                        *j_vals -
                                        *i_vals; // difference of values located
                                                 // on pair of points i, j
                                    gamma_lag += SQUARE(
                                        dv);    // sum of squared differences
                                    cpls += 1.; // count of elements
                                } // end distance test: rv <= radius ^ |rvh| <=
                                  // lag
                            }     // end angle test: |ddir| <= td
                        }         // end i test: *ii > i
                    end:
                        ii++;                      // go to the next index
                        j_vals += *ii - *(ii - 1); // go to the next value
                    } // end j for loop: points within overlapping rectangles
                }     // end test: n_vals > 0
                else {
                    report_error(report);
                    G_fatal_error(_("This point does not have neighbours in "
                                    "given radius..."));
                }
                r += 3;             // go to the next search point
                i_vals++;           // and to its value
                G_free_ilist(list); // free list memory
            } // end for loop i: variogram computation for each i-th search
              // point

            if (isnan(gamma_lag) || cpls == 0.0) { // empty lags:
                err0++;                            // error indicator
                goto gamma_isnan;
            }

            *gamma = 0.5 * gamma_lag / cpls; // element of gamma matrix
            *c = cpls; // # of values that have been used to compute gamma_e

            gamma_sum += *gamma; // sum of gamma elements (non-nan)
            gamma_n++;           // # of gamma elements (non-nan)

        gamma_isnan: // there are no available point couples to compute the
                     // dissimilarities in the lag:
            h++;
            c++;
            gamma++;
            // G_fatal_error(_("end 1st loop"));
        } // end for loop s

        if (type == 2) { // vertical variogram:
            vert++;
        }
    } // end for loop b

    if (err0 == nLag) { // todo> kedy nie je riesitelny teoreticky variogram?
        report_error(report);
        G_fatal_error(_("Unable to compute experimental variogram..."));
    } // end error

    var_pars->gamma = G_matrix_copy(gamma_M);
    var_pars->gamma_sum = gamma_sum;
    var_pars->gamma_n = gamma_n;

    plot_experimental_variogram(xD, var_pars);

    if (phase < 2) {    // initial and middle phase:
        sill(var_pars); // compute sill
    }

    if (report->name) {                            // report file available:
        write2file_variogram_E(xD, var_pars, c_M); // write to file
    }

    write_temporary2file(xD, var_pars);

    G_matrix_free(c_M);
    G_matrix_free(gamma_M);
}

/* theoretical variogram */
void T_variogram(int type, struct opts opt, struct parameters *var_pars,
                 struct int_par *xD)
{
    int i3 = xD->i3;
    struct write *report;

    report = xD->report;

    char *variogram;

    // report
    if (report->name) { // report file available:
        report->fp = fopen(report->name, "a");
        time(&report->now); // write down time of start
        // just for the beginning of the phase => type 0 or 2
        if (type != 1) {
            fprintf(report->fp,
                    "\nComputation of theoretical variogram started on %s\n",
                    ctime(&report->now));
        }
    }

    // set up:
    var_pars->type = type;   // hz / vert / bivar / aniso
    var_pars->const_val = 0; // input values are not constants

    switch (type) {
        // horizontal variogram
    case 0:
        // 3D interpolation (middle phase)
        if (i3 == TRUE) {
            variogram = opt.function_var_hz->answer; // function type available:
            var_pars->function = set_function(variogram, report);

            // nonlinear or not parabolic
            if (strcmp(variogram, "linear") != 0) {
                var_pars->nugget = atof(opt.nugget_hz->answer);
                var_pars->h_range = atof(opt.range_hz->answer);
                if (opt.sill_hz->answer) {
                    var_pars->sill = atof(opt.sill_hz->answer);
                }
            }
            // function type not available:
            else {
                LMS_variogram(var_pars, report);
            }
        }

        // 2D interpolation (final phase)
        else {
            variogram =
                opt.function_var_final->answer; // function type available:
            var_pars->function = set_function(variogram, report);

            // nonlinear or not parabolic
            if (strcmp(variogram, "linear") != 0) {
                var_pars->nugget = atof(opt.nugget_final->answer);
                var_pars->h_range = atof(opt.range_final->answer);
                if (opt.sill_final->answer) {
                    var_pars->sill = atof(opt.sill_final->answer);
                }
            }
            else { // function type not available:
                LMS_variogram(var_pars, report);
            }
        }

        if (report->name && strcmp(variogram, "linear") != 0) {
            report->fp = fopen(report->name, "a");
            fprintf(report->fp, "Parameters of horizontal variogram:\n");
            fprintf(report->fp, "Nugget effect: %f\n", var_pars->nugget);
            fprintf(report->fp, "Sill:          %f\n", var_pars->sill);
            fprintf(report->fp, "Range:         %f\n", var_pars->h_range);
        }
        break;

        // vertical variogram
    case 1:
        var_pars->nugget = atof(opt.nugget_vert->answer);
        var_pars->h_range = atof(opt.range_vert->answer);

        if (opt.sill_vert->answer) {
            var_pars->sill = atof(opt.sill_vert->answer);
        }

        variogram = opt.function_var_vert->answer;
        var_pars->function = set_function(variogram, report);

        if (report->name && strcmp(variogram, "linear") != 0) {
            fprintf(report->fp, "Parameters of vertical variogram:\n");
            fprintf(report->fp, "Nugget effect: %f\n", var_pars->nugget);
            fprintf(report->fp, "Sill:          %f\n", var_pars->sill);
            fprintf(report->fp, "Range:         %f\n", var_pars->h_range);
        }
        break;

        // bivariate variogram (just final phase)
    case 2:
        if (!(opt.function_var_final->answer &&
              opt.function_var_final_vert->answer) ||
            strcmp(opt.function_var_final->answer, "linear") ==
                0) {                // planar function:
            var_pars->function = 5; // planar variogram (3D)
            LMS_variogram(var_pars, report);
        }

        else { // function type was set up by the user:
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

        plot_var(xD, TRUE, var_pars); // Plot variogram using gnuplot
        break;

    case 3: // univariate (just final phase)
        variogram = opt.function_var_final->answer;
        var_pars->function = set_function(variogram, report);

        // nonlinear and not parabolic variogram:
        if (strcmp(variogram, "linear") != 0) {
            var_pars->nugget = atof(opt.nugget_final->answer);
            var_pars->h_range = atof(opt.range_final->answer);
            if (opt.sill_final->answer) {
                var_pars->sill = atof(opt.sill_final->answer);
            }
            variogram = opt.function_var_final->answer;
            if (report->name) {
                if (i3 == TRUE) { // 3D interpolation:
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
        // linear variogram:
        else { // linear or parabolic variogram
            LMS_variogram(var_pars, report);
        }
        break;
    }

    if (type != 2) {
        plot_var(xD, FALSE, var_pars); // Plot variogram using gnuplot
    }
}

void ordinary_kriging(struct int_par *xD, struct reg_par *reg,
                      struct points *pnts, struct var_par *pars,
                      struct output *out)
{
    // Local variables
    int i3 = xD->i3;
    struct write *report = xD->report;
    struct write *crossvalid = xD->crossvalid;
    struct parameters *var_par = &pars->fin;

    int type = var_par->type;
    double max_dist =
        type == 2 ? var_par->horizontal.max_dist : var_par->max_dist;
    // max_dist = sqrt(0.5 * SQUARE(max_dist));

    double max_dist_vert =
        type == 2 ? var_par->vertical.max_dist : var_par->max_dist;

    unsigned int percents = 50; // counter
    unsigned int row, col, dep; // indices of cells/voxels
    int resample;
    struct krig_pars krig;
    int add_trend = (out->trend[0] == 0. && out->trend[1] == 0. &&
                     out->trend[2] == 0. && out->trend[3] == 0.)
                        ? FALSE
                        : TRUE;

    pnts->max_dist = var_par->lag;
    struct ilist *list, *list_new;

    double *r0, rslt, trend_val; // xyz coordinates of cell/voxel centre

    // Cell/voxel center coords (location of interpolated value)
    r0 = (double *)G_malloc(3 * sizeof(double));

    int *row_init, *row0, count, next = 1, total, complete, new_matrix = 0,
                                 setup, mat_row;
    row_init = (int *)G_malloc(reg->ncols * sizeof(int));
    row0 = &row_init[0];

    int i, ndeps = reg->ndeps, nrows = reg->nrows, ncols = reg->ncols;

    krig.rslt = G_matrix_init(nrows * ndeps, ncols, nrows * ndeps);
    krig.first = TRUE;

    if (report->name) { // report file available:
        time(&report->now);
        fprintf(report->fp, "Interpolating values started on %s\n\n",
                ctime(&report->now));
        fflush(report->fp);
    }

    if (percents) {
        G_percent_reset();
    }

    open_layer(xD, reg, out); // open 2D/3D raster

    if (var_par->const_val == 1) { // input values are constant:
        goto constant_voxel_centre;
    }

    set_up_G(pnts, var_par, xD->report,
             &krig); // set up matrix of dissimilarities of input points
    var_par->GM =
        G_matrix_copy(krig.GM); // copy matrix because of cross validation

    // perform cross validation...
    if (crossvalid->name) { // ... if desired
        crossvalidation(xD, pnts, var_par, reg);
    }

    G_message(_("Interpolating unknown values..."));
constant_voxel_centre:
    count = 0;
    col = row = dep = 0;
    total = ndeps * nrows * ncols;

    while (count <= total) {
        if (percents) {
            G_percent(count, total, 1);
        }

        if (var_par->const_val == 1) { // constant input values
            goto constant_voxel_val;
        }

        // coordinates of output point (center of the pixel / voxel)
        if (next < 2) {
            cell_centre(col, row, dep, xD, reg, r0, var_par);

            // initial subsample
            if (col == 0 && row == 0 && dep == 0) {
                list = list_NN(xD, r0, pnts, max_dist, max_dist_vert);
                make_subsamples(xD, list, r0, dep * nrows + row, col, pnts,
                                var_par, &krig);
            }
            // lists to compare
            else if (krig.new == FALSE) {
                list_new = list_NN(xD, r0, pnts, max_dist, max_dist_vert);
                next = compare_NN(list, list_new, krig.modified);
            }
        }

        if (next > 0) {
            rslt = interpolate(xD, list, r0, pnts, var_par, &krig);
            if (add_trend == TRUE) {
                trend_val = trend(r0, out, var_par->function, xD);
                rslt += trend_val;
            }
            mat_row = dep * nrows + row;

            setup = G_matrix_set_element(krig.rslt, mat_row, col, rslt);

            if (G_matrix_get_element(krig.rslt, 0, 0) == 0. && (row != 0))
                G_fatal_error(
                    _("%d %d %d   %d %f %f"), dep, row, col, mat_row,
                    G_matrix_get_element(krig.rslt, 0, 0),
                    krig.rslt->vals[(dep * nrows + row) * ncols + col]);

            if (setup < 0) {
                report_error(report);
                G_fatal_error(
                    _("The value %f was not written to the cell %d %d %d"),
                    rslt, dep, row, col);
            }
            count++;
            krig.new = FALSE;

            next = next == 2 ? 1 : next; // mark it as coincident

            // Create output
        constant_voxel_val:
            if (var_par->const_val == 1) {    // constant input values:
                rslt = (double)*pnts->invals; // setup input as output
            }
        } // end if next > 0

        // go to the next cell point:
        switch (next) {
            // the cell was not interpolated:
        case 0:
            // new column:
            if (row == 0 || row == *row0) {
                Vect_reset_list(list);                 // refresh list
                Vect_list_append_list(list, list_new); // add new list
                G_free_ilist(list_new);                // free list memory
                krig.modified = 1;
                krig.new = TRUE;
                next = 2;                   // interpolate using new subsample
                G_matrix_free(krig.GM_Inv); // free old matrix
                new_matrix++;               // counter of skipped matrices
                make_subsamples(xD, list, r0, dep * nrows + row, col, pnts,
                                var_par, &krig);
            }
            // the same column:
            else {
                *row0 = row; // save row index to continue

                // general cells:
                if (col < ncols - 1) {
                    col++;  // go to the next row
                    row0++; // go to the col index in the next row
                    while (*row0 == nrows) {
                        if (col < ncols - 1) {
                            col++;  // go to the next row
                            row0++; // go to the col index in the next row
                        }
                        else {
                            krig.first = FALSE;
                            col = 0;
                            row0 = &row_init[0];
                        }
                    }
                }
                // last column:
                else {
                    krig.first = FALSE;
                    col = 0;             // start new sampling
                    row0 = &row_init[0]; // from the beginning;

                    // skip full cols:
                    while (*row0 == nrows) { // full row
                        if (col < ncols - 1) {
                            col++;  // go to the next row
                            row0++; // to test if it is completed
                        }
                    } // end while: full row
                }     // end else: last column
            }         // end else: the same column

            row = krig.first == TRUE ? 0 : *row0; // setup starting cell
            break;                                // count does not rise

            // the cell was interpolated -> examine the next one
        case 1:
            // save index to continue:
            row++; // continue in the row

            // last row (full column):
            if (row == nrows) {
                *row0 = row; // save the number to distinguish full columns

                // the last column
                if (col == ncols - 1) {
                    // start from the beginning
                    krig.first = FALSE;
                    col = 0;
                    row0 = &row_init[0];

                    // skip full columns
                    while (*row0 == nrows) {
                        if (col < ncols - 1) {
                            col++;
                            row0++;
                        }
                        else {
                            if (i3 == FALSE || dep == ndeps - 1) {
                                if (dep > 1) {
                                    G_message(_("Vertical level %d has been "
                                                "processed..."),
                                              dep + 1);
                                }
                                goto accomplished;
                            }
                            else {
                                dep++;   // next vertical level
                                col = 0; // the first column

                                // refresh rows
                                new_vertical(row_init, ncols); // row0 = 0
                                row0 = &row_init[0];
                                row = *row0;

                                next = new_sample(xD, list, list_new, pnts, dep,
                                                  row, col, r0, max_dist,
                                                  max_dist_vert, reg, var_par,
                                                  &krig, &new_matrix);
                                goto new_dep;
                            } // end else: complete level
                        }
                    } // end if: *row0 == nrows
                }     // end if: last column

                else {
                    col++;
                    row0++; // read starting row
                    complete = 0;

                    while (*row0 == nrows) {
                        if (col < ncols - 1) {
                            col++;
                            row0++;
                            complete++;
                        }
                        else {
                            krig.first = FALSE;
                            col = 0;
                            row0 = &row_init[0];
                            complete = 0;
                        }
                        if (complete == ncols - 1) {
                            if (i3 == FALSE || dep == ndeps - 1) {
                                if (dep > 1) {
                                    G_message(_("Vertical level %d has been "
                                                "processed..."),
                                              dep + 1);
                                }
                                goto accomplished;
                            }
                            else {
                                dep++;   // next vertical level
                                col = 0; // the first column

                                // refresh rows
                                new_vertical(row_init, ncols); // row0 = 0
                                row0 = &row_init[0];
                                row = *row0;

                                next = new_sample(xD, list, list_new, pnts, dep,
                                                  row, col, r0, max_dist,
                                                  max_dist_vert, reg, var_par,
                                                  &krig, &new_matrix);
                                goto new_dep;
                            } // end else: complete level
                        }     // if: complete == ncols - 1
                    }         // while: *row0 == nrows
                }             // else: general row
                row = krig.first == TRUE ? 0 : *row0;
            } // end else: go to the new column

            break;
        } // end switch next
    new_dep:
        if (row == 0 && col == 0) {
            G_message(_("Vertical level %d has been processed..."), dep);
        }
    } // end while

accomplished:
    G_message(_("# of points: %d   # of matrices: %d   diff: %d"), total,
              new_matrix, total - new_matrix);

    // write output to the (3D) raster layer
    write2layer(xD, reg, out, krig.rslt);

    if (report->name) {
        fprintf(report->fp,
                "\n************************************************\n\n");
        time(&report->now);
        fprintf(report->fp, "v.kriging completed on %s", ctime(&report->now));
        fclose(report->fp);
    }
}
