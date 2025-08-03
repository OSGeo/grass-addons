/****************************************************************************
 *
 * MODULE:       i.spec.unmix
 *
 * AUTHOR(S):    Markus Neteler  <neteler osgeo.org>: 1998,
 *                  Original GRASS 5 version
 *               Mohammed Rashad <rashadkm gmail.com>: 2012, update to GRASS 7
 *
 * PURPOSE:      Spectral mixture analysis of satellite/aerial images
 *
 * Notes:        The original version was implemented with MESCHACH, the actual
 *               version is instead using BLAS/LAPACK via GMATHLIB.
 *               An error minimization approach is used instead of Single Value
 *               Decomposition (SVD) which is numerically unstable. See MN's
 *               related journal publication from 2005 for details.
 *
 * COPYRIGHT:    (C) 1999-2012 by the GRASS Development Team
 *
 *               This program is free software under the GNU General
 *               Public License (>=v2). Read the file COPYING that
 *               comes with GRASS for details.
 *
 * TODO:         test with synthetic mixed pixels; speed up code
 *****************************************************************************/

#define GLOBAL

#include <grass/config.h>

#ifndef HAVE_LIBBLAS
#error GRASS is not configured with BLAS
#endif

#ifndef HAVE_LIBLAPACK
#error GRASS is not configured with LAPACK
#endif

#include <stdio.h>
#include <stdlib.h>
#include <strings.h>
#include <math.h>
#include <grass/gis.h>
#include <grass/imagery.h>
#include <grass/gmath.h>
#include <grass/glocale.h>
#include "global.h"

#define GAMMA                                                \
    10 /* last row value in Matrix and last b vector element \
        * for constraint Sum xi = 1 (GAMMA=weight)           \
        */

static double find_max(double x, double y)
{
    return ((x * (x > y)) + (y * (x <= y)));
}

int main(int argc, char *argv[])
{
    char result_name[GNAME_MAX];
    int nrows, ncols;
    int row;
    int i, j, k;
    vec_struct *b_gamma;
    struct Cell_head region;

    vec_struct *startvector, *A_times_startvector, *errorvector, *temp;
    mat_struct *A, *A_tilde, *A_tilde_trans_mu, *A_tilde_trans;
    mat_struct B, B_tilde, B_tilde_trans_mu;
    struct Colors colors;
    struct History hist;

    struct GModule *module;

    double max_total = 0.0;
    double mu;
    float anglefield[255][255];
    double error = 0.0;
    struct {
        struct Option *group, *matrixfile, *result, *error, *iter;
    } parm;

    /* initialize GIS engine */
    G_gisinit(argv[0]);

    module = G_define_module();
    G_add_keyword(_("imagery"));
    G_add_keyword(_("spectral unmixing"));
    module->description =
        _("Performs Spectral mixture analysis of satellite/aerial images");

    parm.group = G_define_standard_option(G_OPT_I_GROUP);

    parm.matrixfile = G_define_standard_option(G_OPT_F_INPUT);
    parm.matrixfile->key = "matrix";
    parm.matrixfile->type = TYPE_STRING;
    parm.matrixfile->required = YES;
    parm.matrixfile->label = _("Open Matrix file");
    parm.matrixfile->description =
        _("Matrix file containing spectral signatures");

    parm.result = G_define_option();
    parm.result->key = "result";
    parm.result->description =
        _("Name of raster map prefix to hold spectral unmixing results");
    parm.result->guisection = _("Required");

    parm.error = G_define_standard_option(G_OPT_R_OUTPUT);
    parm.error->key = "error";
    parm.error->required = NO;
    parm.error->description = _("Name of raster map to hold unmixing error");

    parm.iter = G_define_standard_option(G_OPT_R_OUTPUT);
    parm.iter->key = "iter";
    parm.iter->required = NO;
    parm.iter->description = _("Raster map to hold number of iterations");

    if (G_parser(argc, argv))
        exit(EXIT_FAILURE);

    /* here we go... A is created here */
    A = open_files(parm.matrixfile->answer, parm.group->answer,
                   parm.result->answer, parm.iter->answer, parm.error->answer);

    /* ATTENTION: Internally we work here with col-oriented matrixfile,
     *  but the user has to enter the spectra row-wise for his/her's
     *  convenience...  That means: Don't mix row- and col-orientation
     *  in source code and modules messages output!
     *
     * Spectral Matrix is stored in A now (diagonally flipped to input
     * file) Generally:    n: cols ....  for matrix A
     *             m: rows
     *                 |
     *                 |
     **/

    /* 1. Check matrix orthogonality:
     *    Ref: Youngsinn Sohn, Roger M. McCoy 1997: Mapping desert shrub
     *    rangeland using spectral unmixing and modeling spectral
     *    mixtrues with TM data. Photogrammetric Engineering &
     *    Remote Sensing,  Vol.63,  No6.
     *
     *
     * 2. Beside checking matrix orthogonality we find out the maximum
     *    entry of the matrix for configuring stepsize mu later.  */

    /* go columnwise through matrix */

    for (i = 0; i < A->cols; i++) {
        vec_struct *Avector1, *Avector2;
        double max1, max2;

        Avector1 = G_matvect_get_column(A, i);

        /* get the max. element of this vector */
        max1 = G_vector_norm_maxval(Avector1, 1);

        double dtemp = max1;

        for (j = 0; j < A->cols; j++) {
            if (j != i) {
                /* get next col in A */
                Avector2 = G_matvect_get_column(A, j);

                /*  get the max. element of this vector */
                max2 = G_vector_norm_maxval(Avector2, 1);

                if (max2 > max1)
                    dtemp = max2;
                if (dtemp > max_total)
                    max_total = dtemp;
                /* find max of matrix A  */
                /* max_total = (find_max (max1, max2), max_total); */

                /* save angle in degree */
                anglefield[i][j] = spectral_angle(Avector1, Avector2);

                G_vector_free(Avector2);
            }
        }

        G_vector_free(Avector1);
    }

    G_message(
        "%s",
        _("Checking linear dependencies (orthogonality check) of Matrix A..."));

    for (i = 0; i < A->cols; i++)
        for (j = 0; j < A->cols; j++)
            if (j != i)
                /* internally this is col and not row certainly */
                G_message(_("Angle between row %i and row %i: %g degree"),
                          (i + 1), (j + 1), anglefield[i][j]);

    for (i = 0; i < A->cols; i++)
        for (j = 0; j < A->cols; j++)
            if (j != i)
                if (anglefield[i][j] < 8.0)
                    G_message(_("Spectral entries row %i: and row %i: in "
                                "your matrix are linear dependent!\nYou "
                                "have to revise your reference spectra."),
                              i, j);

    if (!error)
        G_message(_("Spectral matrix is o.k. Proceeding..."));

    /* Begin calculations
     * 1. contraint SUM xi = 1
     *   add last row "1" elements to Matrix A, store in A_tilde
     *   A_tilde is one row-dimension more than A
     */

    /* memory allocation */
    A_tilde = G_matrix_init(A->rows + 1, A->cols, A->rows + 1);
    if (A_tilde == NULL)
        G_fatal_error(_("Unable to allocate memory for matrix"));

    for (i = 0; i < A->rows; i++)
        for (j = 0; j < A->cols; j++)
            G_matrix_set_element(A_tilde, i, j, G_matrix_get_element(A, i, j));

    /* fill last row with 1 elements */
    for (j = 0; j < A_tilde->cols; j++) {
        G_matrix_set_element(A_tilde, i, j, GAMMA);
    }

    /* now we have an overdetermined (non-square) system

     * We have a least square problem here: error minimization
     *                             T          -1         T
     * unknown fraction = [A_tilde * A_tilde]  * A_tilde * b
     *
     * A_tilde is the non-square matrix with first constraint in last row.
     * b is pixel vector from satellite image
     *
     * Solve this by deriving above equation and searching the
     * minimum of this error function in an iterative loop within
     * both constraints.
     */

    /* calculate the transpose of A_tilde */
    A_tilde_trans = G_matrix_transpose(A_tilde);

    /* initialize some values
     * step size must be small enough for covergence  of iteration:
     *  mu = 0.000001;      step size for spectra in range of W/m^2/um
     *  mu = 0.000000001;   step size for spectra in range of mW/m^2/um
     *  mu = 0.000001;      step size for spectra in range of reflectance
     */

    /* check  max_total for number of digits to configure mu size */
    mu = 0.0001 * pow(10, -1 * ceil(log10(max_total)));

    /* TODO: Missing? startvector = G_vector_init (0, 0, RVEC); */
    startvector = G_vector_init(A->cols, 1, RVEC);

    if (startvector == NULL)
        G_fatal_error(_("Unable to allocate memory for vector"));

    /* TODO: Missing? A_times_startvector = G_vector_init (0, 0, RVEC); */
    A_times_startvector =
        G_vector_init(A_tilde->rows, 1, RVEC); /* length: no. of bands   */
    /* TODO: Missing? errorvector = G_vector_init (0, 0, RVEC); */
    errorvector =
        G_vector_init(A_tilde->rows, 1, RVEC); /* length: no. of bands   */
    /* TODO: Missing? temp = G_vector_init (0, 0, RVEC); */
    temp = G_vector_init(A_tilde->cols, 1, RVEC); /* length: no. of spectra */

    /* length: no. of bands   */
    if (A_times_startvector == NULL)
        G_fatal_error(_("Unable to allocate memory for vector"));

    /* length: no. of bands   */
    if (errorvector == NULL)
        G_fatal_error(_("Unable to allocate memory for vector"));

    /* length: no. of spectra */
    if (temp == NULL)
        G_fatal_error(_("Unable to allocate memory for vector"));

    A_tilde_trans_mu =
        G_matrix_init(A_tilde->rows, A_tilde->cols, A_tilde->rows);
    if (A_tilde_trans_mu == NULL)
        G_fatal_error(_("Unable to allocate memory for matrix"));

    /* Now we can calculated the fractions pixelwise */
    G_get_window(&region); /* get geographical region */

    nrows = region.rows;
    ncols = region.cols;

    G_message(_("Calculating for %i x %i pixels (%i bands) = %i pixelvectors."),
              nrows, ncols, Ref.nfiles, (ncols * ncols));

    for (row = 0; row < nrows; row++) {
        int col, band;

        G_percent(row, nrows, 1);

        /* get one row for all bands */
        for (band = 0; band < Ref.nfiles; band++)
            Rast_get_c_row(cellfd[band], cell[band], row);

        for (col = 0; col < ncols; col++) {

            double change = 1000;
            double deviation = 1000;
            int iterations = 0;

            /* get pixel values of each band and store in b vector: */
            /* length: no. of bands + 1 (GAMMA) */

            b_gamma = G_vector_init(A_tilde->rows, 1, RVEC);

            if (b_gamma == NULL)
                G_fatal_error(_("Unable to allocate memory for matrix"));

            for (band = 0; band < Ref.nfiles; band++)
                G_matrix_set_element(b_gamma, 0, band, cell[band][col]);

            /* add GAMMA for 1. constraint as last element */
            G_matrix_set_element(b_gamma, 0, Ref.nfiles, GAMMA);

            for (k = 0; k < A_tilde->cols; k++)
                G_matrix_set_element(startvector, 0, k, (1.0 / A_tilde->cols));

            /* calculate fraction vector for current pixel
               Result is stored in fractions vector
               with second constraint: Sum x_i = 1
             */

            /* get start vector and initialize it with equal fractions:
               using the neighbor pixelvector as startvector
             */

            /* solve with iterative solution: */
            while (fabs(change) > 0.0001) {

                G_matvect_product(A_tilde, startvector, A_times_startvector);

                G_vector_sub(A_times_startvector, b_gamma, errorvector);

                A_tilde_trans_mu =
                    G_matrix_scalar_mul(mu, A_tilde_trans, A_tilde_trans_mu);

                G_matvect_product(A_tilde_trans_mu, errorvector, temp);
                G_vector_sub(startvector, temp,
                             startvector); /* update startvector */

                for (k = 0; k < A_tilde->cols; k++)
                    /* no. of spectra times */
                    /* if one element gets negative, set it to zero */
                    if ((G_matrix_get_element(startvector, 0, k) < 0))
                        G_matrix_set_element(startvector, 0, k, 0);

                /* Check the deviation */
                double norm = G_vector_norm_euclid(errorvector);

                change = deviation - norm;
                deviation = norm;

                iterations++;

                /* G_message("change=%lf, norm2=%lf",change, norm);   */
            }

            vec_struct *fraction;

            /* G_message("fcol %d  and A->cols %d", startvector->dim, A->cols);
             */
            fraction =
                G_vector_init(A->cols, 1, RVEC); /* length: no. of spectra */
            error = deviation / G_vector_norm_euclid(b_gamma);
            fraction = G_vector_copy(startvector, NO_COMPACT);

            /* write result in full percent */
            for (i = 0; i < A->cols; i++) /* no. of spectra */
                result_cell[i][col] =
                    (CELL)(100 * G_matrix_get_element(fraction, 0, i) * 100.0 /
                           255.0);

            /* save error and iterations */
            if (error_fd >= 0)
                error_cell[col] = (CELL)(100 * error);
            if (iter_fd >= 0)
                iter_cell[col] = iterations;

            G_vector_free(fraction);
            G_vector_free(b_gamma);
        } /* end cols loop */

        /* write the resulting rows into output files:  */
        for (i = 0; i < A->cols; i++) /* no. of spectra  */
            Rast_put_c_row(resultfd[i], result_cell[i]);

        if (error_fd >= 0)
            Rast_put_c_row(error_fd, error_cell);

        if (iter_fd >= 0)
            Rast_put_c_row(iter_fd, iter_cell);

    } /* rows loop  */

    G_percent(row, nrows, 2);

    /* close files  */
    for (i = 0; i < Ref.nfiles; i++) /* no. of bands  */
        Rast_unopen(cellfd[i]);

    /* make grey scale color table for output maps */
    Rast_init_colors(&colors);
    Rast_set_c_color(0, 0, 0, 0, &colors);
    Rast_set_c_color(100, 255, 255, 255, &colors);

    for (i = 0; i < A->cols; i++) { /* no. of spectra  */
        sprintf(result_name, "%s.%d", parm.result->answer, (i + 1));

        /* close output map */
        Rast_close(resultfd[i]);

        /* set colors */
        Rast_write_colors(result_name, G_mapset(), &colors);

        /* write map history (meta data) */
        Rast_short_history(result_name, "raster", &hist);
        Rast_format_history(&hist, HIST_DATSRC_1, "Group: %s",
                            parm.group->answer);
        Rast_format_history(&hist, HIST_DATSRC_2, "Matrix file: %s",
                            parm.matrixfile->answer);
        Rast_format_history(&hist, HIST_KEYWRD, "Spectrum %d:", i + 1);
        Rast_command_history(&hist);
        Rast_write_history(result_name, &hist);

        /* create histogram */
        do_histogram(result_name, G_mapset());
    }

    if (error_fd >= 0) {
        CELL min, max;
        struct Range range;

        Rast_close(error_fd);

        sprintf(result_name, "%s", parm.error->answer);

        /* set colors to gyr */
        Rast_read_range(result_name, G_mapset(), &range);
        Rast_get_range_min_max(&range, &min, &max);
        Rast_make_colors(&colors, "gyr", min, max);
        Rast_write_colors(result_name, G_mapset(), &colors);

        /* write map history (meta data) */
        Rast_short_history(result_name, "raster", &hist);
        Rast_format_history(&hist, HIST_DATSRC_1, "Group: %s",
                            parm.group->answer);
        Rast_format_history(&hist, HIST_DATSRC_2, "Matrix file: %s",
                            parm.matrixfile->answer);
        Rast_set_history(&hist, HIST_KEYWRD, "unmixing error");
        Rast_command_history(&hist);
        Rast_write_history(result_name, &hist);
    }

    if (iter_fd >= 0) {
        Rast_close(iter_fd);

        sprintf(result_name, "%s", parm.iter->answer);

        /* write map history (meta data) */
        Rast_short_history(result_name, "raster", &hist);
        Rast_format_history(&hist, HIST_DATSRC_1, "Group: %s",
                            parm.group->answer);
        Rast_format_history(&hist, HIST_DATSRC_2, "Matrix file: %s",
                            parm.matrixfile->answer);
        Rast_set_history(&hist, HIST_KEYWRD, "number of iterations");
        Rast_command_history(&hist);
        Rast_write_history(result_name, &hist);
    }

    G_matrix_free(A);
    G_vector_free(errorvector);
    G_vector_free(temp);
    G_vector_free(startvector);
    G_vector_free(A_times_startvector);

    /* disabled, done separately for the different types of output */
    /*
    make_history(result_name, parm.group->answer, parm.matrixfile->answer);
    */

    G_done_msg(" ");

    exit(EXIT_SUCCESS);
}
