#include <unistd.h>
#include <stdlib.h>
#include <stdio.h>
#include <math.h>
#include <string.h>
#include <signal.h>

#include <grass/config.h>
#ifdef HAVE_FFTW3_H
#include <fftw3.h>
#endif
#ifdef HAVE_DFFTW_H
#include <dfftw.h>
#endif

#include <grass/gis.h>
#include <grass/raster.h>
#include <grass/imagery.h>
#include <grass/gmath.h>
#include <grass/glocale.h>
#include "globals.h"
#include "local_proto.h"

static void diagonal(double *dg, double *d2, double dx, double dy)
{
    *d2 = dx * dx + dy * dy;
    *dg = sqrt(*d2);
}

void Extract_matrix_auto(void)
{
    char *first_map_R_mapset;
    char *first_map_R_name;
    int first_map_R_fd;
    RASTER_MAP_TYPE first_map_R_type;
    char *second_map_R_mapset;
    char *second_map_R_name;
    int second_map_R_fd;
    RASTER_MAP_TYPE second_map_R_type;
    struct Cell_head cellhd_zoom1;
    struct Cell_head cellhd_zoom2;
    int ncols1, ncols2, nrows1, nrows2;
    double fft_thresh;
    int fft_windows, fft_size;
    int i;
    int check_reading;
    char *group_name;
    char *group_MAPSET;
    char *group_LOCATION_NAME;
    char *group_GISDBASE;
    DCELL *rowbuf1_R;
    DCELL tf1_R;
    DCELL *rowbuf2_R;
    DCELL tf2_R;
    DCELL *mat1, *mat2;
    int r, c;
    int q;
    char file_name[GPATH_MAX];
    FILE *fp;
    char xname[GNAME_MAX], xmapset[GMAPSET_MAX];

    G_debug(1, "Extract_matrix_auto()");

    select_env(SRC_ENV);

    /* Load environmental vars */
    group_LOCATION_NAME = G_store(G_getenv("LOCATION_NAME"));
    group_GISDBASE = G_store(G_getenv("GISDBASE"));
    group_MAPSET = G_store(G_getenv("MAPSET"));

    if (G_name_is_fully_qualified(group.name, xname, xmapset)) {
        group_name = xname;
    }
    else {
        group_name = group.name;
    }

    first_map_R_name = group.img;
    first_map_R_mapset = (char *)G_find_raster2(first_map_R_name, "");

    /* get source cell head */
    G_debug(1, "get source image cellhd");
    Rast_get_cellhd(first_map_R_name, first_map_R_mapset, &cellhd1);
    Rast_get_cellhd(first_map_R_name, first_map_R_mapset, &cellhd_zoom1);

    /* Find second map */
    select_env(TGT_ENV);

    second_map_R_name = group.tgt_img;
    second_map_R_mapset = (char *)G_find_raster2(second_map_R_name, "");

    /* get target cell head */
    G_debug(1, "get target image cellhd");
    Rast_get_cellhd(second_map_R_name, second_map_R_mapset, &cellhd2);
    Rast_get_cellhd(second_map_R_name, second_map_R_mapset, &cellhd_zoom2);

    G_debug(1, "north: map1 %f, map2 %f", curr_window.north, tgt_window.north);
    G_debug(1, "south: map1 %f, map2 %f", curr_window.south, tgt_window.south);
    G_debug(1, "east: map1 %f, map2 %f", curr_window.east, tgt_window.east);
    G_debug(1, "west: map1 %f, map2 %f", curr_window.west, tgt_window.west);

    G_debug(1, "rows: map1 %d, map2 %d", curr_window.rows, tgt_window.rows);
    G_debug(1, "cols: map1 %d, map2 %d", curr_window.cols, tgt_window.cols);

    select_env(SRC_ENV);

    /* Open first map: load for current region */
    G_debug(1, "load source image");
    Rast_set_input_window(&curr_window);

    if ((first_map_R_fd = Rast_open_old(first_map_R_name, first_map_R_mapset)) <
        0) {
        G_fatal_error(_("Error opening first raster map <%s>"),
                      first_map_R_name);
    }
    if ((first_map_R_type =
             Rast_map_type(first_map_R_name, first_map_R_mapset)) < 0)
        G_fatal_error(_("Error getting first raster map type"));

    nrows1 = curr_window.rows;
    ncols1 = curr_window.cols;

    /* Memory allocation for map_1: */
    mat1 = (DCELL *)G_calloc((nrows1 * ncols1), sizeof(DCELL));

    rowbuf1_R = Rast_allocate_d_input_buf();

    /* Load first map */

    check_reading = 0;

    for (r = 0; r < nrows1; r++) {
        Rast_get_row(first_map_R_fd, rowbuf1_R, r, DCELL_TYPE);

        for (c = 0; c < ncols1; c++) {
            tf1_R = rowbuf1_R[c];
            if (!Rast_is_d_null_value(&tf1_R))
                mat1[(ncols1 * (r)) + c] = tf1_R;
            else
                mat1[(ncols1 * (r)) + c] = 0.0;

            if (mat1[(ncols1 * (r)) + c])
                check_reading = 1;
        }
    }
    Rast_close(first_map_R_fd);
    G_free(rowbuf1_R);

    if (!check_reading)
        G_fatal_error(_("Nothing read from map1 %d"), check_reading);

    /* Load second map */

    select_env(TGT_ENV);
    Rast_set_input_window(&tgt_window);

    /* Open second map */
    G_debug(1, "load target image");
    G_debug(1, "location: %s", G_location());
    G_debug(1, "projection: %s", G_projection_name(G_projection()));
    G_debug(1, "tgt_window projection: %s", G_projection_name(tgt_window.proj));
    G_debug(1, "cellhd2 projection: %s", G_projection_name(cellhd2.proj));

    if ((second_map_R_fd =
             Rast_open_old(second_map_R_name, second_map_R_mapset)) < 0) {
        G_fatal_error(_("Error opening second raster map <%s>"),
                      second_map_R_name);
    }
    G_debug(1, "target image map type");
    if ((second_map_R_type =
             Rast_map_type(second_map_R_name, second_map_R_mapset)) < 0)
        G_fatal_error(_("Error getting second raster map type"));

    nrows2 = tgt_window.rows;
    ncols2 = tgt_window.cols;

    /* Memory allocation for zoom_map_2 */
    mat2 = (DCELL *)G_calloc((nrows2 * ncols2), sizeof(DCELL));

    rowbuf2_R = Rast_allocate_d_input_buf();

    check_reading = 0;

    G_debug(1, "read target image");
    for (r = 0; r < nrows2; r++) {
        Rast_get_row(second_map_R_fd, rowbuf2_R, r, DCELL_TYPE);
        for (c = 0; c < ncols2; c++) {
            tf2_R = rowbuf2_R[c];
            if (!Rast_is_d_null_value(&tf2_R))
                mat2[(ncols2 * (r)) + c] = tf2_R;
            else
                mat2[(ncols2 * (r)) + c] = 0.0;

            if (mat1[(ncols2 * (r)) + c])
                check_reading = 1;
        }
    }

    Rast_close(second_map_R_fd);
    G_free(rowbuf2_R);

    if (!check_reading)
        G_fatal_error(_("Nothing read from map1 %d"), check_reading);

    select_env(SRC_ENV);
    Rast_set_input_window(&curr_window);

    /* Initialize control points */
    sPoints.count = 1;
    sPoints.e1 = (double *)G_malloc(sPoints.count * sizeof(double));
    sPoints.n1 = (double *)G_malloc(sPoints.count * sizeof(double));
    sPoints.e2 = (double *)G_malloc(sPoints.count * sizeof(double));
    sPoints.n2 = (double *)G_malloc(sPoints.count * sizeof(double));
    sPoints.status = (int *)G_malloc(sPoints.count * sizeof(int));

    /* define fft parameters */
    fft_size = detail;
    fft_windows = n_new_points;
    fft_thresh = 0.4;

    /******************************************/
    /* function --> Search_correlation_points */
    /******************************************/
    Search_correlation_points_auto(mat1, mat2, fft_size, fft_windows,
                                   fft_thresh);

    /* Build or update group/POINTS file */
    sPoints.count -= 1;
    if (sPoints.count > 0) {
        int n_points_filtered = sPoints.count;

        sprintf(file_name, "%s/%s/%s/group/%s/POINTS", group_GISDBASE,
                group_LOCATION_NAME, group_MAPSET, group_name);
        if (access(file_name, F_OK)) {
            q = 0;
        }
        else {
            q = 1;
        }

        G_debug(1, "Write new control points");
        fp = fopen(file_name, "a");
        if (q == 0) {
            fprintf(fp, "# %7s %15s %15s %15s %9s status\n", "", "image", "",
                    "target", "");
            fprintf(fp, "# %15s %15s %15s %15s   (1=ok)\n", "east", "north",
                    "east", "north");
            fprintf(fp, "#\n");
        }

        /* filter with RMS threshold */
        for (i = 0; i < sPoints.count; i++) {
            double e, n;
            double rx, ry, rd, rd2;

            /* calculate backward RMS error */
            CRS_georef(sPoints.e2[i], sPoints.n2[i], &e, &n, group.E21,
                       group.N21, transform_order);

            rx = fabs(e - sPoints.e1[i]);
            ry = fabs(n - sPoints.n1[i]);
            diagonal(&rd, &rd2, rx, ry);

            if (rd > rms_threshold) {
                sPoints.status[i] = -1;
                n_points_filtered--;
            }
        }

        for (i = 0; i < sPoints.count; i++) {
            if (sPoints.status[i] != -1) {
                fprintf(fp, "  %15f %15f %15f %15f %4d\n", sPoints.e1[i],
                        sPoints.n1[i], sPoints.e2[i], sPoints.n2[i],
                        sPoints.status[i]);
            }
        }

        fclose(fp);

        /* Load new control points */
        G_debug(1, "Load new control points");

        for (i = 0; i < sPoints.count; i++) {
            if (sPoints.status[i] != -1) {
                I_new_control_point(&group.points, sPoints.e1[i], sPoints.n1[i],
                                    sPoints.e2[i], sPoints.n2[i],
                                    sPoints.status[i]);
            }
        }
        if (sPoints.count < n_new_points)
            G_message(_("%d of %d points had a poor FFT correlation"),
                      n_new_points - sPoints.count, n_new_points);
        if (n_points_filtered == 0)
            G_message(
                _("%d points found but no point was below RMS threshold %.4G"),
                sPoints.count, rms_threshold);
        else if (rms_threshold > 0 && n_points_filtered < sPoints.count)
            G_message(_("%d points found, %d point%s below RMS threshold %.4G"),
                      sPoints.count, n_points_filtered,
                      n_points_filtered > 1 ? _("s were") : (" was"),
                      rms_threshold);
        else
            G_message(_("%d points found"), sPoints.count);

        select_current_env();
    }

    G_debug(1, "Free memory");
    /* Free memory */

    G_free(mat1);
    G_free(mat2);

    G_debug(1, "Free points");
    G_free(sPoints.e1);
    G_free(sPoints.n1);
    G_free(sPoints.n2);
    G_free(sPoints.e2);
    G_free(sPoints.status);

    G_message(_("Done searching"));
    return;
}

void Search_correlation_points_auto(DCELL *mat1_R, DCELL *mat2_R,
                                    int search_window_dim, int n_windows,
                                    double thresh)
{
    int search_border;
    struct Control_Points fftPoints;
    double *fft_first_s[2];
    double *fft_second_s[2];
    double *fft_prod_con_s[2];
    int fft_rows, fft_cols;
    long fft_size;
    int fft_r, fft_c, i, j;
    int squared_search_window_dim;
    long l_i;
    int r_start, c_start, r_start1, c_start1, r_end, c_end;
    double *cc;
    int fft_nr = 0;
    double north1, east1, north2, east2;
    int shift_r, shift_c;
    double mean_1, mean_2;
    double fft_prod_real, fft_prod_img;
    double v_product;
    int check_reading;
    int dump_unity_pulse = 0;
    long nc, nt;

    G_debug(1, "Search_correlation_points_auto()");
    G_debug(1, "search_window_dim %d", search_window_dim);

    /* Correlation parameters */
    squared_search_window_dim = search_window_dim * search_window_dim;
    search_border = search_window_dim / 2;

    fft_rows = search_window_dim;
    fft_cols = search_window_dim;
    fft_size = fft_rows * fft_cols;

    /* Memory allocation */
    G_debug(1, "Memory allocation");
    fft_first_s[0] = (double *)G_malloc(fft_size * sizeof(double));
    fft_first_s[1] = (double *)G_malloc(fft_size * sizeof(double));
    fft_second_s[0] = (double *)G_malloc(fft_size * sizeof(double));
    fft_second_s[1] = (double *)G_malloc(fft_size * sizeof(double));
    fft_prod_con_s[0] = (double *)G_malloc(fft_size * sizeof(double));
    fft_prod_con_s[1] = (double *)G_malloc(fft_size * sizeof(double));

    cc = (double *)G_malloc(n_windows * sizeof(double));
    fftPoints.n1 = (double *)G_malloc(n_windows * sizeof(double));
    fftPoints.e1 = (double *)G_malloc(n_windows * sizeof(double));
    fftPoints.n2 = (double *)G_malloc(n_windows * sizeof(double));
    fftPoints.e2 = (double *)G_malloc(n_windows * sizeof(double));
    fftPoints.count = 0;

    /* Begin computation */
    G_debug(1, "begin computation");

    r_end = curr_window.rows - search_border;
    c_end = curr_window.cols - search_border;

    /* go through maps */
    init_rand();
    nc = curr_window.rows * curr_window.cols;
    nt = n_windows;

    G_debug(1, "start loops");
    for (fft_r = search_border; fft_r < r_end; fft_r++) {
        r_start = fft_r - search_border;

        G_percent(r_start, r_end - search_border, 2);

        for (fft_c = search_border; fft_c < c_end; fft_c++) {
            c_start = fft_c - search_border;

            nc--;

            /* Coordinates of center point point for reference matrix 2 */

            G_debug(2, "get map2 center point");

            north2 = tgt_window.north - (fft_r + 0.5) * tgt_window.ns_res;
            east2 = tgt_window.west + (fft_c + 0.5) * tgt_window.ew_res;

            /* estimate center point in map 1 */
            CRS_georef(east2, north2, &east1, &north1, group.E21, group.N21,
                       transform_order);

            /* northing to row */
            r_start1 = (curr_window.north - north1) / curr_window.ns_res;
            c_start1 = (east1 - curr_window.west) / curr_window.ew_res;

            r_start1 -= search_border;
            if (r_start1 < 0 || r_start1 + search_window_dim > curr_window.rows)
                continue;
            c_start1 -= search_border;
            if (c_start1 < 0 || c_start1 + search_window_dim > curr_window.cols)
                continue;

            if (make_rand() % nc >= nt)
                continue;

            /* only decrement if point with ok FFT correlation found, see below
             */
            /* nt--; */

            /*  Initialize fft vectors */

            G_debug(2, "initialize fft vectors");
            for (l_i = 0; l_i < fft_size; l_i++) {
                fft_first_s[0][l_i] = 0.0;
                fft_first_s[1][l_i] = 0.0;
                fft_second_s[0][l_i] = 0.0;
                fft_second_s[1][l_i] = 0.0;
                fft_prod_con_s[0][l_i] = 0.0;
                fft_prod_con_s[1][l_i] = 0.0;
            }

            /* Get means for search window extends of map1 and map2 */

            mean_1 = 0.0;
            mean_2 = 0.0;
            for (i = 0; i < search_window_dim; i++) {
                for (j = 0; j < search_window_dim; j++) {

                    mean_1 += mat1_R[(r_start1 + i) * curr_window.cols +
                                     c_start1 + j];

                    mean_2 +=
                        mat2_R[(r_start + i) * tgt_window.cols + c_start + j];
                }
            }

            mean_1 = (mean_1 / squared_search_window_dim);
            mean_2 = (mean_2 / squared_search_window_dim);

            /* copy search window extends of map1 and map2 to fft arrays */
            check_reading = 0;

            for (i = 0; i < search_window_dim; i++) {

                for (j = 0; j < search_window_dim; j++) {

                    fft_first_s[0][i * search_window_dim + j] =
                        (mat1_R[(r_start1 + i) * curr_window.cols + c_start1 +
                                j] -
                         mean_1);

                    fft_second_s[0][i * search_window_dim + j] =
                        (mat2_R[(r_start + i) * tgt_window.cols + c_start + j] -
                         mean_2);

                    if (fft_first_s[0][i * search_window_dim + j])
                        check_reading = 1;
                }
            }

            if (check_reading == 0) {
                G_warning(_("First matrix not copied"));
                continue;
            }

            /* real to complex fft of the 2 real windows */
            fft(-1, fft_first_s, fft_size, fft_cols, fft_rows);
            fft(-1, fft_second_s, fft_size, fft_cols, fft_rows);

            /* overlay the two signals: multiplication
               product of the first fft with the conjugate of the second one

               division by magnitude |F(map1) * F(map2)*|
             */

            G_debug(2, "compute power spectrum");
            check_reading = 0;
            v_product = 0.0;
            for (l_i = 0; l_i < fft_size; l_i++) {

                fft_prod_real = (fft_first_s[0][l_i] * fft_second_s[0][l_i]) +
                                (fft_first_s[1][l_i] * fft_second_s[1][l_i]);

                fft_prod_img = (fft_first_s[1][l_i] * fft_second_s[0][l_i]) -
                               (fft_first_s[0][l_i] * fft_second_s[1][l_i]);

                v_product += sqrt(fft_prod_real * fft_prod_real +
                                  fft_prod_img * fft_prod_img);
            }
            v_product /= search_window_dim; /* fft_size; */

            for (l_i = 0; l_i < fft_size; l_i++) {
                fft_prod_real = (fft_first_s[0][l_i] * fft_second_s[0][l_i]) +
                                (fft_first_s[1][l_i] * fft_second_s[1][l_i]);

                fft_prod_img = (fft_first_s[1][l_i] * fft_second_s[0][l_i]) -
                               (fft_first_s[0][l_i] * fft_second_s[1][l_i]);

                fft_prod_con_s[0][l_i] = (fft_prod_real / v_product);
                fft_prod_con_s[1][l_i] = (fft_prod_img / v_product);

                if (fft_prod_real != 0.0 && fft_prod_img != 0.0) {
                    check_reading = 1;
                }
            }

            if (check_reading == 0) {
                G_debug(2, "FFT product error");
                continue;
            }

            /* reverse fft to create a compound signal */
            /* fft^{-1} of the product <==> cross-correlation at different lag
               between the two orig. (complex) windows */
            fft(1, fft_prod_con_s, fft_size, fft_cols, fft_rows);

            /* Search the lag corresponding to the maximum correlation */
            /* actually the unity pulse */
            cc[fftPoints.count] = 0.0;
            shift_r = shift_c = 0;

            G_debug(2, "find unity pulse");

            for (i = 0; i < search_window_dim; i++) {
                for (j = 0; j < search_window_dim; j++)
                    if (fft_prod_con_s[0][(i * fft_cols) + j] >
                        cc[fftPoints.count]) {
                        cc[fftPoints.count] =
                            fft_prod_con_s[0][(i * fft_cols) + j];
                        shift_r = i;
                        shift_c = j;
                    }
            }

            /* cc was somewhere larger than thresh */
            if (cc[fftPoints.count] > thresh) {
                G_debug(2, "correlation: %4e", cc[fftPoints.count]);

                /* Get row and col of "ending" point in map 2 */

                /* not yet understood layout of inverse fft
                 * if tmp_r < search_border, tmp_r = tmp_r + search_border
                 * if tmp_r >= search_border, tmp_r = tmp_r - search_border
                 * if tmp_c < search_border, tmp_c = tmp_c + search_border
                 * if tmp_c >= search_border, tmp_c = tmp_c - search_border
                 *
                 * now get shift: tmp_r = tmp_r - search_border
                 *
                 * now add shift to r
                 */

                /* indices are zero-based: the nth row is row n-1 */
                if (shift_r < search_border)
                    shift_r = shift_r + search_border;
                else
                    shift_r = shift_r - search_border;
                shift_r = shift_r - search_border;

                if (shift_c < search_border)
                    shift_c = shift_c + search_border;
                else
                    shift_c = shift_c - search_border;
                shift_c = shift_c - search_border;

                G_debug(2, "row shift %d, col shift %d", shift_r, shift_c);

                /* Get coordinates of "ending" point in source map 1 */
                r_start1 += search_border;
                north1 = curr_window.north -
                         (r_start1 + shift_r + 0.5) * curr_window.ns_res;
                c_start1 += search_border;
                east1 = curr_window.west +
                        (c_start1 + shift_c + 0.5) * curr_window.ew_res;

                /* Fill the fftPoints array */
                fftPoints.e1[fftPoints.count] = east1;
                fftPoints.n1[fftPoints.count] = north1;
                fftPoints.e2[fftPoints.count] = east2;
                fftPoints.n2[fftPoints.count] = north2;
                fftPoints.count++;

                /* dump unity pulse */
                if (dump_unity_pulse) {
                    int rd, cd, fd;
                    DCELL *dump, dnullval;
                    char dumpfile[GNAME_MAX];

                    sprintf(dumpfile, "unity_pulse_%d", fftPoints.count);
                    fd = Rast_open_new(dumpfile, DCELL_TYPE);

                    dump = Rast_allocate_d_input_buf();
                    Rast_set_d_null_value(&dnullval, 1);

                    r_start1 -= search_border;
                    c_start1 -= search_border;

                    for (rd = 0; rd < curr_window.rows; rd++) {
                        for (cd = 0; cd < curr_window.cols; cd++) {

                            if (rd < r_start1 ||
                                rd >= r_start1 + search_window_dim)
                                dump[cd] = dnullval;
                            else if (cd < c_start1 ||
                                     cd >= c_start1 + search_window_dim)
                                dump[cd] = dnullval;
                            else
                                dump[cd] = fft_prod_con_s[0][((rd - r_start1) *
                                                              fft_cols) +
                                                             (cd - c_start1)];
                        }
                        Rast_put_d_row(fd, dump);
                    }
                    Rast_close(fd);
                    G_free(dump);
                }
                /* point with sufficiently good FFT correlation: decrease nt */
                nt--;
            }
            else {
                G_debug(2, "correlation: %4e", cc[fftPoints.count]);
            }
            fft_nr++;
        }
    }
    G_percent(1, 1, 2); /* finish it */

    if (fftPoints.count > 0) {

        for (i = 0; i < fftPoints.count; i++) {
            /* Fill the sPoints array */
            sPoints.e1[sPoints.count - 1] = fftPoints.e1[i];
            sPoints.n1[sPoints.count - 1] = fftPoints.n1[i];
            sPoints.e2[sPoints.count - 1] = fftPoints.e2[i];
            sPoints.n2[sPoints.count - 1] = fftPoints.n2[i];

            sPoints.status[sPoints.count - 1] = 1;
            sPoints.count += 1;
            sPoints.e1 =
                (double *)G_realloc(sPoints.e1, sPoints.count * sizeof(double));
            sPoints.n1 =
                (double *)G_realloc(sPoints.n1, sPoints.count * sizeof(double));
            sPoints.e2 =
                (double *)G_realloc(sPoints.e2, sPoints.count * sizeof(double));
            sPoints.n2 =
                (double *)G_realloc(sPoints.n2, sPoints.count * sizeof(double));
            sPoints.status =
                (int *)G_realloc(sPoints.status, sPoints.count * sizeof(int));
        }
    }

    /* free memory */
    G_free(fft_first_s[0]);
    G_free(fft_first_s[1]);
    G_free(fft_second_s[0]);
    G_free(fft_second_s[1]);
    G_free(fft_prod_con_s[0]);
    G_free(fft_prod_con_s[1]);

    G_free(fftPoints.n1);
    G_free(fftPoints.e1);
    G_free(fftPoints.n2);
    G_free(fftPoints.e2);

    return;
}
