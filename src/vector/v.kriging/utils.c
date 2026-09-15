#include "local_proto.h"

#define GNUPLOT "gnuplot -persist"

int cmpVals(const void *v1, const void *v2)
{
    int *p1, *p2;

    p1 = (int *)v1;
    p2 = (int *)v2;
    if (p1[0] > p2[0])
        return 1;
    else if (p1[0] < p2[0])
        return -1;
    else
        return 0;
}

// make coordinate triples xyz
void triple(double x, double y, double z, double *triple)
{
    double *t;

    t = &triple[0];

    *t = x;
    *(t + 1) = y;
    *(t + 2) = z;

    return;
}

// compute coordinate differences
void coord_diff(int i, int j, double *r, double *dr)
{
    int k = 3 * i, l = 3 * j;
    double *rk, *rl, *drt;

    rk = &r[k];
    rl = &r[l];
    drt = &dr[0];

    if ((*rk == 0.) && (*(rk + 1) == 0.) && (*(rk + 2) == 0.)) {
        G_fatal_error(_("Coordinates of point no. %d are zeros."), i);
    }

    *drt = *rl - *rk;                   // dx
    *(drt + 1) = *(rl + 1) - *(rk + 1); // dy
    *(drt + 2) = *(rl + 2) - *(rk + 2); // dz

    return;
}

// compute horizontal radius from coordinate differences
double radius_hz_diff(double dr[3])
{
    double rds;

    rds = SQUARE(dr[0]) + SQUARE(dr[1]);

    return rds;
}

double squared_distance(int direction, double *dr)
{
    double d;

    switch (direction) {
    case 12: // horizontal
        d = SQUARE(dr[0]) + SQUARE(dr[1]);
        break;
    case 3: // vertical
        d = SQUARE(dr[2]);
        break;
    case 0: // all
        d = SQUARE(dr[0]) + SQUARE(dr[1]) + SQUARE(dr[2]);
        break;
    }

    return d;
}

// compute zenith angle
double zenith_angle(double dr[3])
{
    double zenith;

    zenith = atan2(dr[2], sqrt(SQUARE(dr[0]) + SQUARE(dr[1])));

    return zenith;
}

void correct_indices(int direction, struct ilist *list, double *r0,
                     struct points *pnts, struct parameters *var_pars)
{
    int i;
    int n = list->n_values;
    int *vals = list->value;
    double dr[3];
    int type = var_pars->type;
    double max_dist = var_pars->max_dist;

    int skip = FALSE; // do not skip relevant points
    int n_new = 0; // # of effective indices (not identical points, nor too far)
    int *newvals, *save; // effective indices

    // values of the new list (if necesary)
    newvals = (int *)G_malloc(n * sizeof(int));
    save = &newvals[0];

    double *r, sqDist_i;

    for (i = 0; i < n; i++) {
        *vals -= 1;              // decrease value by 1
        r = &pnts->r[3 * *vals]; // find point coordinates

        // coordinate differences
        *dr = *r - *r0;
        *(dr + 1) = *(r + 1) - *(r0 + 1);
        *(dr + 2) = *(r + 2) - *(r0 + 2);

        // compute squared distance
        sqDist_i = squared_distance(direction, dr);

        // compare with maximum
        skip = sqDist_i <= max_dist ? FALSE : TRUE;

        // if:
        // - univariate variogram with only one non-zero value or
        // - the distance (circular) does not exceed max_dist
        if (type != 2 && (n == 1 || (sqDist_i != 0.)) || skip == FALSE) {
            *save = *vals;
            n_new++;
            save++;
            skip = FALSE;
        }
        vals++;
    }

    if (type != 2 && n_new < n) {
        list->n_values = n_new;
        list->value = (int *)G_realloc(list->value, n_new * sizeof(int));
        memcpy(list->value, newvals, n_new * sizeof(int));
    }

    G_free(newvals);

    return;
}

// compute size of the lag
double lag_size(int i3, int direction, struct points *pnts,
                struct parameters *var_pars, struct write *report)
{
    // local variables
    int n = pnts->n;     // # of input points
    double *r = pnts->r; // xyz of input points
    int type = var_pars->type;
    double max_dist =
        type == 2 ? var_pars->horizontal.max_dist
                  : var_pars->max_dist; // maximum horizontal distance (or
                                        // vertical for vertical variogram)
    double max_dist_vert =
        type == 2 ? var_pars->vertical.max_dist
                  : var_pars->max_dist; // maximum vertical distance (just for
                                        // bivariate variogram)

    int i, j;           // loop indices
    int n_vals;         // number of the nearest neighbors (NN)
    int *j_vals;        // indices of NN (NOT sorted by distance)
    struct ilist *list; // list of NN

    double dr[3]; // coordinate differences
    double d_min =
        SQUARE(max_dist) +
        SQUARE(max_dist_vert); // the shortest distance of the 5%-th NN
    double lagNN;              // square root of d_min -> lag
    double dist2; // square of the distances between search point and NN

    double *search; // search point
    int perc5;      // 5% from total number of NN
    int add_ident;  // number of identical points to add to perc5

    for (i = 0; i < n; i++) { // for each input point...

        add_ident =
            0; // number of points identical to search point equals to zero
        search = &pnts->r[3 * i];

        switch (direction) {
        case 12: // horizontal variogram
            list = find_NNs_within(2, search, pnts, max_dist, -1);
            break;
        case 3: // vertical variogram
            list = find_NNs_within(1, search, pnts, max_dist, max_dist_vert);
            break;
        default: // anisotropic and bivariate variogram
            list = find_NNs_within(3, search, pnts, max_dist, max_dist_vert);
            break;
        }
        n_vals = list->n_values; // number of overlapping rectangles

        // find number of points identical to the search point
        if (n_vals > 0) {
            j_vals = &list->value[0]; // indices of overlapping rectangles
                                      // (note: increased by 1)

            for (j = 0; j < n_vals; j++) { // for each overlapping rectangle:
                coord_diff(i, (*j_vals - 1), pnts->r,
                           dr);      // compute coordinate differences
                switch (direction) { // and count those which equal to zero
                case 12:             // horizontal
                    if (i3 == FALSE && (dr[0] == 0. && dr[1] == 0.)) {
                        add_ident++;
                    }
                    break;
                case 3: // vertical
                    if (dr[2] == 0.) {
                        add_ident++;
                    }
                    break;
                default: // aniso / bivar
                    if (dr[0] == 0. && dr[1] == 0. && dr[2] == 0.) {
                        add_ident++;
                    }
                    break;
                } // end switch: test direction
                j_vals++; // index of the next NN
            } // end j for loop
        } // end if: n_vals > 0

        else {
            report_error(report);
            G_fatal_error(
                _("Error: There are no nearest neighbours of point %d..."), i);
        } // end error

        perc5 = (int)ceil(0.05 * n) +
                add_ident; // set up 5% increased by number of identical points

        coord_diff(i, perc5, pnts->r,
                   dr); // coordinate differences of search point and 5%th NN
        switch (
            direction) { // compute squared distance for particular direction
        case 12:         // horizontal
            dist2 = SQUARE(dr[0]) + SQUARE(dr[1]);
            break;
        case 3: // vertical
            dist2 = SQUARE(dr[2]);
            break;
        default: // aniso / bivar
            dist2 = SQUARE(dr[0]) + SQUARE(dr[1]) + SQUARE(dr[2]);
            break;
        }

        if (dist2 != 0.) { // and compare it with minimum distance between
                           // search point and 5% NN
            d_min = MIN(d_min, dist2);
        }

        G_free_ilist(list); // free list memory
        r += 3;             // go to next search point
    } // end i for loop: distance of i-th search pt and 5%-th NN

    lagNN = sqrt(d_min);

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

    y = nugget + part_sill * (1. - exp(-3. * x / h_range)); // practical

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

    n = (int)round(*varpar_max / lag); // compute number of lags
    *varpar_max =
        n * lag; // set up modified maximum distance (to not have empty lags)

    return n;
}

void optimize(double *lag, int *nLag, double max)
{
    if (*nLag > 20) {
        *nLag = 20;
        *lag = max / *nLag;
    }

    return;
}

// maximal horizontal and vertical distance to restrict variogram computing
void variogram_restricts(struct int_par *xD, struct points *pnts,
                         struct parameters *var_pars)
{
    struct write *report = xD->report;

    double *min, *max; // extend
    double dr[3];      // coordinate differences

    int dimension; // dimension: hz / vert / aniso
    char type[12];

    variogram_type(
        var_pars->type,
        type); // set up: 0 - "hz", 1 - "vert", 2 - "bivar", 3 - "aniso"

    // Find extent
    G_message(_("Computing %s variogram properties..."), type);

    min = &pnts->r_min[0]; // set up pointer to minimum xyz
    max = &pnts->r_max[0]; // set up pointer to maximum xyz

    dr[0] = *max - *min;             // x range
    dr[1] = *(max + 1) - *(min + 1); // y range
    dr[2] = *(max + 2) - *(min + 2); // z range

    switch (var_pars->type) {
    case 1: // vertical variogram
        if (var_pars->max_dist == -1.) {
            var_pars->max_dist = dr[2]; // zmax - zmin
        }
        var_pars->radius = SQUARE(
            var_pars->max_dist); // anisotropic distance (todo: try also dz)
        break;
    default:
        if (var_pars->max_dist == -1.) {
            var_pars->radius =
                radius_hz_diff(dr) / 9.; // horizontal radius (1/9)
            var_pars->max_dist = sqrt(
                var_pars
                    ->radius); // 1/3 max horizontal dist (Surfer, Golden SW)
        }
        else {
            var_pars->radius = SQUARE(var_pars->max_dist);
        }
        break;
    }
    if (var_pars->max_dist <= 0.) {
        G_fatal_error(_("Maximum distance must be greater than 0."));
    }

    if (report->name) { // report name available:
        write2file_varSetsIntro(var_pars->type, report); // describe properties
    }

    // set up code according to type
    switch (var_pars->type) {
    case 0: // horizontal
        dimension = 12;
        break;
    case 1: // vertical
        dimension = 3;
        break;
    case 3: // anisotropic
        dimension = 0;
        break;
    }

    if (var_pars->type == 2) { // bivariate variogram
        // horizontal direction:
        if (var_pars->nLag == -1) {
            var_pars->lag =
                lag_size(xD->i3, 12, pnts, var_pars, report); // lag distance
            var_pars->nLag = lag_number(var_pars->lag,
                                        &var_pars->max_dist); // number of lags
            optimize(&var_pars->lag, &var_pars->nLag, var_pars->max_dist);
            var_pars->max_dist =
                var_pars->nLag * var_pars->lag; // maximum distance
        }
        else {
            var_pars->lag = var_pars->max_dist / var_pars->nLag; // lag size
        }

        // vertical direction
        if (var_pars->nLag_vert == -1) {
            var_pars->lag_vert =
                lag_size(xD->i3, 3, pnts, var_pars, report); // lag distance
            var_pars->nLag_vert = lag_number(
                var_pars->lag_vert, &var_pars->max_dist_vert); // # of lags
            optimize(&var_pars->lag_vert, &var_pars->nLag_vert,
                     var_pars->max_dist_vert);
            var_pars->max_dist_vert =
                var_pars->nLag_vert * var_pars->lag_vert; // max distance
        }
        else {
            var_pars->lag_vert =
                var_pars->max_dist_vert / var_pars->nLag_vert; // lag size
        }
    }

    else { // univariate variograms (hz / vert / aniso)
        if (var_pars->nLag == -1) {
            var_pars->lag =
                lag_size(xD->i3, dimension, pnts, var_pars, report); // lag size
            var_pars->nLag =
                lag_number(var_pars->lag, &var_pars->max_dist); // # of lags
            optimize(&var_pars->lag, &var_pars->nLag, var_pars->max_dist);
            var_pars->max_dist =
                var_pars->nLag * var_pars->lag; // maximum distance
        }
        else {
            var_pars->lag = var_pars->max_dist / var_pars->nLag; // lag size
        }
    }

    if (report->name) {                       // report name available:
        write2file_varSets(report, var_pars); // describe properties
    }
}

void geometric_anisotropy(struct int_par *xD, struct points *pnts)
{
    int i;
    double ratio = xD->aniso_ratio;

    if (ratio <= 0.) {          // ratio is negative or zero:
        if (xD->report->name) { // close report file
            fprintf(xD->report->fp,
                    "Error (see standard output). Process killed...");
            fclose(xD->report->fp);
        }
        G_fatal_error(_("Anisotropy ratio must be greater than zero..."));
    }

    double *r;

    r = &pnts->r[0];

    struct RTree *R_tree; // spatial index for input
    struct RTree_Rect *rect;

    R_tree = RTreeCreateTree(-1, 0, 3); // create 3D spatial index

    for (i = 0; i < pnts->n; i++) {
        *(r + 2) = ratio * *(r + 2);

        rect = RTreeAllocRect(R_tree);
        RTreeSetRect3D(rect, R_tree, *r, *r, *(r + 1), *(r + 1), *(r + 2),
                       *(r + 2));
        RTreeInsertRect(rect, i + 1, R_tree);

        r += 3;
    }

    pnts->R_tree = R_tree;
}

// Least Squares Method
mat_struct *LSM(mat_struct *A, mat_struct *x)
{
    mat_struct *AT, *ATA, *ATA_Inv, *ATx, *T;

    /* LMS */
    AT = G_matrix_transpose(A);         /* Transposed design matrix */
    ATA = G_matrix_product(AT, A);      /* AT*A */
    ATA_Inv = G_matrix_inverse(ATA);    /* (AT*A)^-1 */
    ATx = G_matrix_product(AT, x);      /* AT*x */
    T = G_matrix_product(ATA_Inv, ATx); /* theta = (AT*A)^(-1)*AT*x */

    return T;
}

// set up type of function according to GUI (user)
int set_function(char *variogram, struct write *report)
{
    int function;

    if (strcmp(variogram, "linear") == 0) {
        function = 0;
    }
    else if (strcmp(variogram, "parabolic") == 0) {
        function = 1;
    }
    else if (strcmp(variogram, "exponential") == 0) {
        function = 2;
    }
    else if (strcmp(variogram, "spherical") == 0) {
        function = 3;
    }
    else if (strcmp(variogram, "gaussian") == 0) {
        function = 4;
    }
    else if (strcmp(variogram, "bivariate") == 0) {
        function = 5;
    }
    else {
        report_error(report);
        G_fatal_error(_("Set up correct name of variogram function..."));
    }

    return function;
}

// set up terminal and format of output plot
void set_gnuplot(char *fileformat, struct parameters *var_pars)
{
    if (strcmp(fileformat, "cdr") == 0) {
        strcpy(var_pars->term, "corel");
        strcpy(var_pars->ext, "cdr");
    }
    if (strcmp(fileformat, "dxf") == 0) {
        strcpy(var_pars->term, "dxf");
        strcpy(var_pars->ext, "dxf");
    }
    if (strcmp(fileformat, "eps") == 0) {
        strcpy(var_pars->term, "postscript");
        strcpy(var_pars->ext, "eps");
    }
    if (strcmp(fileformat, "pdf") == 0) {
        strcpy(var_pars->term, "pdfcairo");
        strcpy(var_pars->ext, "pdf");
    }
    if (strcmp(fileformat, "png") == 0) {
        strcpy(var_pars->term, "png");
        strcpy(var_pars->ext, "png");
    }
    if (strcmp(fileformat, "svg") == 0) {
        strcpy(var_pars->term, "svg");
        strcpy(var_pars->ext, "svg");
    }
}

// plot experimental variogram
void plot_experimental_variogram(struct int_par *xD, struct parameters *var_par)
{
    int bivar = var_par->type == 2 ? TRUE : FALSE;

    int i, j;   // indices
    int nr, nc; // # of rows, cols
    double *h;  // pointer to horizontal or anisotropic bins
    double *vert;
    mat_struct *gamma_M = var_par->gamma; // pointer to gamma matrix
    FILE *gp;                             // pointer to file

    nr = gamma_M->rows; // # of rows of gamma matrix
    nc = gamma_M->cols; // # of cols of gamma matrix

    double *gamma;

    gamma = &gamma_M->vals[0]; // values of gamma matrix

    gp =
        fopen("dataE.dat",
              "w"); // open file to write experimental variogram (initial phase)
    if (access("dataE.dat", W_OK) < 0) {
        report_error(xD->report);
        G_fatal_error(_("Something went wrong opening tmp file..."));
    }

    /* 3D experimental variogram */
    if (bivar == TRUE) {
        vert = &var_par->vertical.h[0];
        for (i = 0; i < nc + 1; i++) { // for each row (nZ)
            h = &var_par->horizontal.h[0];
            for (j = 0; j < nr + 1; j++) { // for each col (nL)
                if (i == 0 && j == 0) {
                    fprintf(gp, "%d ", nr); // write to file count of columns
                }
                else if (i == 0 && j != 0) { // 1st row
                    fprintf(gp, "%f", *h);   // write h to 1st row of the file
                    h++;
                    if (j < nr) {
                        fprintf(gp, " "); // spaces between elements
                    }
                } // end 1st row setting

                else {
                    if (j == 0 && i != 0) // 1st column
                        fprintf(gp, "%f ",
                                *vert); // write vert to 1st column of the file
                    else {
                        if (isnan(*gamma)) {
                            fprintf(gp, "NaN"); // write other elements
                        }
                        else {
                            fprintf(gp, "%f", *gamma); // write other elements
                        }

                        if (j != nr) {
                            fprintf(gp, " "); // spaces between elements
                        }
                        gamma++;
                    }
                } // end columns settings
            } // end j
            fprintf(gp, "\n");
            if (i != 0) { // vert must not increase in the 1st loop
                vert++;
            }
        } // end i
    } // end 3D

    /* 2D experimental variogram */
    else {
        h = &var_par->h[0];
        for (i = 0; i < nr; ++i) {
            if (isnan(*gamma)) {
                fprintf(gp, "%f NaN\n", *h);
            }
            else {
                fprintf(gp, "%f %f\n", *h, *gamma);
            }
            h++;
            gamma++;
        }
    }
    fclose(gp);

    gp = popen(GNUPLOT, "w"); /* open file to create plots */
    if (gp == NULL)
        G_message("Unable to plot variogram");

    fprintf(gp, "set terminal wxt %d size 800,450\n", var_par->type);
    if (bivar == TRUE) { // bivariate variogram
        fprintf(gp, "set title \"Experimental variogram (3D) of <%s>\"\n",
                var_par->name);
        fprintf(gp, "set xlabel \"h interval No\"\n");
        fprintf(gp, "set ylabel \"dz interval No\"\n");
        fprintf(gp, "set zlabel \"gamma(h,dz) [units^2]\" rotate by 90 left\n");
        fprintf(gp, "set key below\n");
        fprintf(gp, "set key box\n");
        fprintf(gp, "set dgrid3d %d,%d\n", nc, nr);
        fprintf(gp, "splot 'dataE.dat' every ::1:1 matrix title \"experimental "
                    "variogram\"\n");
    }

    // plot experimental variogram
    else { // univariate variogram
        char dim[6];

        if (xD->i3 == TRUE) { // 3D
            if (var_par->type == 0) {
                strcpy(dim, "hz");
            }
            if (var_par->type == 1) {
                strcpy(dim, "vert");
            }
            if (var_par->type == 3) {
                strcpy(dim, "aniso");
            }
            fprintf(gp,
                    "set title \"Experimental variogram (3D %s) of <%s>\"\n",
                    dim, var_par->name);
        }
        else { // 2D
            fprintf(gp, "set title \"Experimental variogram (2D) of <%s>\"\n",
                    var_par->name);
        }

        fprintf(gp, "set xlabel \"h [m]\"\n");
        fprintf(gp, "set ylabel \"gamma(h) [units^2]\"\n");
        fprintf(gp, "set key bottom right\n");
        fprintf(gp, "set key box\n");
        fprintf(gp, "plot 'dataE.dat' using 1:2 title \"experimental "
                    "variogram\" pointtype 5\n");
    }
    fclose(gp);

    if (!xD->report->name) {
        remove("dataE.dat");
    }
}

// plot experimental and theoretical variogram
void plot_var(struct int_par *xD, int bivar, struct parameters *var_pars)
{
    int i3 = xD->i3;
    struct write *report = xD->report;
    int function;
    double nugget, nugget_h, nugget_v;
    double sill;
    double h_range;
    double *T;

    // setup theoretical variogram parameters
    if (bivar == FALSE) { // univariate variogram
        function = var_pars->function;
        if (function > 1) { // nonlinear and not parabolic variogram
            nugget = var_pars->nugget;
            sill = var_pars->sill - nugget;
            h_range = var_pars->h_range;
        }
    }

    if (var_pars->function < 2) { // linear or parabolic variogram
        T = &var_pars->T->vals[0];
    }

    int i, j;   // indices
    int nr, nc; // # of rows, cols
    int type = var_pars->type;
    double *h;    // pointer to horizontal or anisotropic bins
    double *vert; // pointer to vertical bins
    double h_ratio;
    double g_teor;
    double *gamma_var; // pointer to gamma matrix
    FILE *gp;          // pointer to file

    nr = var_pars->gamma->rows; // # of rows of gamma matrix
    nc = var_pars->gamma->cols; // # of cols of gamma matrix

    gamma_var = &var_pars->gamma->vals[0]; // values of gamma matrix

    if (type != 2) { // univariate variogram
        gp = fopen("dataE.dat",
                   "w"); // open file to write experimental variogram
        if (access("dataE.dat", W_OK) < 0) {
            report_error(report);
            G_fatal_error(_("Something went wrong opening tmp file..."));
        }
        if (gp == NULL) {
            report_error(report);
            G_fatal_error(_("Error writing file"));
        }

        h = &var_pars->h[0];
        for (i = 0; i < nr; i++) {
            if (isnan(*gamma_var)) {
                fprintf(gp, "%f NaN\n", *h); // write other elements
            }
            else {
                fprintf(gp, "%f %f\n", *h, *gamma_var);
            }
            h++;
            gamma_var++;
        }
    }

    else { // bivariate variogram
        gp =
            fopen("dataE.dat", "r"); // open file to read experimental variogram
        if (access("dataE.dat", F_OK) < 0) {
            report_error(report);
            G_fatal_error(_("You have probably deleted dataE.dat - process "
                            "middle phase again, please."));
        }
    }

    if (fclose(gp) != 0) {
        report_error(report);
        G_fatal_error(_("Error closing file..."));
    }

    /* Theoretical variogram */
    gp = fopen("dataT.dat", "w"); // open file to write theoretical variogram
    if (access("dataT.dat", W_OK) < 0) {
        report_error(report);
        G_fatal_error(_("Something went wrong opening tmp file..."));
    }

    double dd;
    double hh;
    double hv[2];

    h = type == 2 ? &var_pars->horizontal.h[0] : &var_pars->h[0];

    // Compute theoretical variogram
    switch (bivar) {
    case 0: // Univariate variogram:
        for (i = 0; i <= nr; i++) {
            hh = i == 0 ? 0. : *h;

            switch (function) {
            case 0:           // linear
                dd = *T * hh; // todo: add nugget effect
                break;
            case 1: // parabolic
                dd = *T * SQUARE(hh) + *(T + 1);
                break;
            case 2: // exponential
                dd = nugget + sill * (1 - exp(-3. * hh / h_range)); // practical
                break;
            case 3: // spherical
                if (hh < h_range) {
                    h_ratio = hh / h_range;
                    dd = nugget + sill * (1.5 * h_ratio - 0.5 * POW3(h_ratio));
                }
                else {
                    dd = sill + nugget;
                }
                break;
            case 4: // Gaussian
                h_ratio = SQUARE(hh) / SQUARE(h_range);
                dd = nugget + sill * (1 - exp(-3. * h_ratio));
                break;
            }
            fprintf(gp, "%f %f\n", hh, dd);

            if (i > 0) {
                h++;
            }
        } // end i for cycle
        break;

    case 1: // bivariate (3D)
        // Coefficients of theoretical variogram
        T = &var_pars->T->vals[0]; // values
        vert = &var_pars->vertical.h[0];
        for (i = 0; i < nc + 1; i++) { // for each row
            h = &var_pars->horizontal.h[0];
            for (j = 0; j < nr + 1; j++) {  // for each col
                if (i == 0 && j == 0) {     // the 0-th element...
                    fprintf(gp, "%d ", nr); // ... is number of columns
                }
                else if (i == 0 &&
                         j != 0) { // for the other elements in 1st row...
                    fprintf(gp, "%f", *h); // ... write h
                    if (j < nr) {
                        fprintf(gp, " "); // ... write a space
                    }
                    h++; // go to next h
                }
                else {                      // other rows
                    if (j == 0 && i != 0) { // write vert to 1st column
                        fprintf(gp, "%f ", *vert);
                    }
                    else { // fill the other columns with g_teor
                        hv[0] = *h;
                        hv[1] = *vert;
                        g_teor = variogram_fction(var_pars, hv);
                        fprintf(gp, "%f", g_teor);
                        if (j != nr) {
                            fprintf(gp, " ");
                        }
                        h++;
                    } // end else: fill the other columns
                } // end fill the other rows
            } // end j
            if (i != 0 && j != 0) {
                vert++;
            }
            fprintf(gp, "\n");
        } // end i
        break;
    }

    if (fclose(gp) == EOF) {
        report_error(report);
        G_fatal_error(_("Error closing file..."));
    }

    gp = popen(GNUPLOT, "w"); // open file to create plots
    if (gp == NULL) {
        G_message(_("Unable to plot variogram"));
    }

    if (strcmp(var_pars->term, "") != 0) {
        fprintf(gp, "set terminal %s size 750,450\n", var_pars->term);

        switch (var_pars->type) {
        case 0: // horizontal component of bivariate variogram
            if (var_pars->function == 5) { // component of 3D bivariate
                fprintf(gp, "set output \"variogram_bivar.%s\"\n",
                        var_pars->ext);
            }
            else { // horizontal variogram
                fprintf(gp, "set output \"variogram_hz.%s\"\n", var_pars->ext);
            }
            break;
        case 1: // vertical variogram
            fprintf(gp, "set output \"variogram_vertical.%s\"\n",
                    var_pars->ext);
            break;
        case 2: // bivariate variogram
            if (bivar == TRUE) {
                fprintf(gp, "set output \"variogram_bivariate.%s\"\n",
                        var_pars->ext);
            }
            break;
        case 3: // anisotropic variogram
            fprintf(gp, "set output \"variogram_final.%s\"\n", var_pars->ext);
            break;
        }
    }
    else {
        G_warning("\nVariogram output> If you wish some special file format, "
                  "please set it at the beginning.\n");
        fprintf(gp, "set terminal wxt %d size 800,450\n", var_pars->type);
    }

    if (bivar == TRUE) { // bivariate variogram
        fprintf(gp,
                "set title \"Experimental and theoretical variogram (3D) of "
                "<%s>\"\n",
                var_pars->name);

        fprintf(gp, "set xlabel \"h interval No\"\n");
        fprintf(gp, "set ylabel \"dz interval No\"\n");
        fprintf(gp, "set zlabel \"gamma(h,dz) [units^2]\" rotate by 90 left\n");
        fprintf(gp, "set key below\n");
        fprintf(gp, "set key box\n");
        fprintf(gp, "set dgrid3d %d,%d\n", nc, nr);
        fprintf(gp, "splot 'dataE.dat' every ::1:1 matrix title \"experimental "
                    "variogram\", 'dataT.dat' every ::1:1 matrix with lines "
                    "title \"theoretical variogram\" palette\n");
    }

    else {                             // univariate variogram
        if (i3 == TRUE) {              // 3D variogram
            if (var_pars->type == 0) { // horizontal variogram
                if (i3 == TRUE) {
                    fprintf(gp,
                            "set title \"Experimental and theoretical "
                            "variogram (3D hz) of <%s>\"\n",
                            var_pars->name);
                }
                else {
                    fprintf(gp,
                            "set title \"Experimental and theoretical "
                            "variogram (2D hz) of <%s>\"\n",
                            var_pars->name);
                }
            }
            else if (var_pars->type == 1) { // vertical variogram
                fprintf(gp,
                        "set title \"Experimental and theoretical variogram "
                        "(3D vert) of <%s>\"\n",
                        var_pars->name);
            }
            else if (var_pars->type == 3) { // anisotropic variogram
                fprintf(gp,
                        "set title \"Experimental and theoretical variogram "
                        "(3D) of <%s>\"\n",
                        var_pars->name);
            }
        }

        else { // 2D
            fprintf(gp,
                    "set title \"Experimental and theoretical variogram (2D) "
                    "of <%s>\"\n",
                    var_pars->name);
        }

        switch (var_pars->function) {
        case 0: // linear
            fprintf(
                gp,
                "set label \"linear: gamma(h) = %f*h\" at screen 0.30,0.90\n",
                var_pars->T->vals[0]);
            break;
        case 1: // parabolic
            fprintf(gp,
                    "set label \"parabolic: gamma(h) = %f*h^2\" at screen "
                    "0.25,0.90\n",
                    var_pars->T->vals[0]);
            break;
        case 2: // exponential
            fprintf(gp, "set rmargin 5\n");
            fprintf(gp,
                    "set label \"exponential: gamma(h) = %f + %f * (1 - "
                    "exp(-3*h / %f))\" at screen 0.10,0.90\n",
                    var_pars->nugget, var_pars->sill - var_pars->nugget,
                    var_pars->h_range);
            break;
        case 3: // spherical
            fprintf(gp, "set rmargin 5\n");
            fprintf(gp,
                    "set label \"spherical: gamma(h) = "
                    "%f+%f*(1.5*h/%f-0.5*(h/%f)^3)\" at screen 0.05,0.90\n",
                    var_pars->nugget, var_pars->sill - var_pars->nugget,
                    var_pars->h_range, var_pars->h_range);
            break;
        case 4: // gaussian
            fprintf(gp,
                    "set label \"gaussian: gamma(h) = %f + %f * (1 - exp(-3*(h "
                    "/ %f)^2))\" at screen 0.10,0.90\n",
                    var_pars->nugget, var_pars->sill - var_pars->nugget,
                    var_pars->h_range);
            break;
        }

        fprintf(gp, "set xlabel \"h [m]\"\n");
        fprintf(gp, "set ylabel \"gamma(h) [units^2]\"\n");
        fprintf(gp, "set key bottom right\n");
        fprintf(gp, "set key box\n");
        fprintf(gp, "plot 'dataE.dat' using 1:2 title \"experimental "
                    "variogram\" pointtype 5, 'dataT.dat' using 1:2 title "
                    "\"theoretical variogram\" with linespoints\n");
    }
    fclose(gp);

    remove("dataE.dat");
    remove("dataT.dat");
}

void new_vertical(int *row0, int n)
{
    int i;
    int *value;

    value = &row0[0];

    for (i = 0; i < n; i++) {
        *value = 0;
        value++;
    }
}
