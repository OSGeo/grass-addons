/****************************************************************
 *
 * MODULE:     i.pr
 *
 * AUTHOR(S):  Stefano Merler, ITC-irst
 *             Updated to ANSI C by G. Antoniol <giulio.antoniol@gmail.com>
 *
 * PURPOSE:    i.pr - Pattern Recognition
 *
 * COPYRIGHT:  (C) 2007 by the GRASS Development Team
 *
 *             This program is free software under the
 *             GNU General Public License (>=v2).
 *             Read the file COPYING that comes with GRASS
 *             for details.
 *
 ****************************************************************/

#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <math.h>
#include <grass/gis.h>
#include <grass/raster.h>
#include <grass/glocale.h>
#include "global.h"

int extract_array_with_null();

int main(int argc, char *argv[])
{
    struct GModule *module;
    struct Option *opt1;
    struct Option *opt2;
    int model_type;
    NearestNeighbor nn;
    GaussianMixture gm;
    Tree tree;
    SupportVectorMachine svm;
    BTree btree;
    BSupportVectorMachine bsvm;
    char tmpbuf[500];
    char *mapset;
    struct Cell_head cellhd;
    double ***matrix;
    DCELL *rowbuf;
    DCELL *tf;
    int *fd;
    int r, c, l;
    Features features;
    int i, j;
    int *space_for_each_layer;
    double *wind_vect;
    double *X;
    int borderC, borderR, borderC_upper, dim;
    double mean, sd;
    int corrent_feature;
    double *projected;
    int *compute_features;
    double **output_cell;
    int set_null;
    int n_input_map;
    int R, C;
    int last_row;

    /* Define the different options */

    opt1 = G_define_option();
    opt1->key = "input_map";
    opt1->type = TYPE_STRING;
    opt1->required = YES;
    opt1->multiple = YES;
    opt1->gisprompt = "old,cell,raster";
    opt1->description =
        "Input raster maps to be classified.\n\t\tIt is required a number of "
        "maps at least equal to the number of maps\n\t\tused for the training. "
        "If this number is greater the last maps will be "
        "ignored.\n\t\tWARNING: the order in which the maps are given should "
        "be compared \n\t\twith that used for the training.";

    opt2 = G_define_option();
    opt2->key = "model";
    opt2->type = TYPE_STRING;
    opt2->required = YES;
    opt2->description =
        "Input file containing the model (output of i .pr_model).\n\t\tIf the "
        "data used for model development are not GRASS_data the program will "
        "abort.";

    /***** Start of main *****/
    G_gisinit(argv[0]);

    module = G_define_module();
    G_add_keyword(_("imagery"));
    G_add_keyword(_("image processing"));
    G_add_keyword(_("pattern recognition"));
    module->description =
        _("Module for detection of unexploded bombs. "
          "i.pr: Pattern Recognition environment for image processing. "
          "Includes kNN, "
          "Decision Tree and SVM classification techniques. Also includes "
          "cross-validation and bagging methods for model validation.");

    if (G_parser(argc, argv) < 0)
        exit(EXIT_FAILURE);

    /*read the model */
    model_type = read_model(opt2->answer, &features, &nn, &gm, &tree, &svm,
                            &btree, &bsvm);

    if (features.training.data_type != GRASS_data) {
        sprintf(tmpbuf, "Model build using othe than GRASS data\n");
        G_fatal_error(tmpbuf);
    }
    if (model_type == 0) {
        sprintf(tmpbuf, "Model not recognized\n");
        G_fatal_error(tmpbuf);
    }

    if (model_type == GM_model) {
        compute_test_gm(&gm);
    }

    /* load current region */
    G_get_window(&cellhd);
    if (fabs((cellhd.ew_res - features.training.ew_res) /
             features.training.ew_res) > 0.1) {
        sprintf(tmpbuf, "EW resolution of training data and test map differs "
                        "more than 10%%\n");
        G_warning(tmpbuf);
    }
    if (fabs((cellhd.ns_res - features.training.ns_res) /
             features.training.ns_res) > 0.1) {
        sprintf(tmpbuf, "NS resolution of training data and test map differs "
                        "more than 10%%\n");
        G_warning(tmpbuf);
    }

    /*compute features space */
    dim = features.training.rows * features.training.cols;

    space_for_each_layer =
        (int *)G_calloc(features.training.nlayers, sizeof(int));
    compute_features = (int *)G_calloc(features.training.nlayers, sizeof(int));
    for (j = 0; j < features.training.nlayers; j++) {
        if (features.f_mean[0]) {
            for (i = 2; i < 2 + features.f_mean[1]; i++) {
                if (features.f_mean[i] == j) {
                    compute_features[j] = TRUE;
                    space_for_each_layer[j] += 1;
                }
            }
        }
        if (features.f_variance[0]) {
            for (i = 2; i < 2 + features.f_variance[1]; i++) {
                if (features.f_variance[i] == j) {
                    compute_features[j] = TRUE;
                    space_for_each_layer[j] += 1;
                }
            }
        }
        if (features.f_pca[0]) {
            for (i = 2; i < 2 + features.f_pca[1]; i++) {
                if (features.f_pca[i] == j) {
                    compute_features[j] = TRUE;
                    space_for_each_layer[j] += dim;
                }
            }
        }
        if (space_for_each_layer[j] == 0) {
            space_for_each_layer[j] = dim;
        }
    }

    /*alloc memory */
    matrix = (double ***)G_calloc(features.training.nlayers, sizeof(double **));
    for (l = 0; l < features.training.nlayers; l++) {
        matrix[l] =
            (double **)G_calloc(features.training.rows, sizeof(double *));
        for (r = 0; r < features.training.rows; r++) {
            matrix[l][r] = (double *)G_calloc(cellhd.cols, sizeof(double));
        }
    }
    fd = (int *)G_calloc(features.training.nlayers, sizeof(int));
    X = (double *)G_calloc(features.examples_dim, sizeof(double));

    wind_vect = (double *)G_calloc(dim, sizeof(double));
    projected = (double *)G_calloc(features.npc, sizeof(double));

    output_cell = (double **)G_calloc(cellhd.rows, sizeof(double *));
    for (r = 0; r < cellhd.rows; r++)
        output_cell[r] = (double *)G_calloc(cellhd.cols, sizeof(double));

    /*open the input maps */
    n_input_map = 0;
    for (l = 0; opt1->answers[l]; l++) {
        if ((mapset = (char *)G_find_raster2(opt1->answers[l], "")) == NULL) {
            sprintf(tmpbuf, "raster map [%s] not available", opt1->answers[l]);
            G_fatal_error(tmpbuf);
        }

        if ((fd[l] = Rast_open_old(opt1->answers[l], mapset)) < 0) {
            sprintf(tmpbuf, "error opening raster map [%s]", opt1->answers[l]);
            G_fatal_error(tmpbuf);
        }
        n_input_map += 1;
    }

    if (n_input_map < features.training.nlayers) {
        sprintf(tmpbuf, "Model requires %d input maps\n",
                features.training.nlayers);
        G_fatal_error(tmpbuf);
    }
    if (n_input_map > features.training.nlayers) {
        sprintf(tmpbuf, "Only first %d maps considered\n",
                features.training.nlayers);
        G_warning(tmpbuf);
    }

    /*useful vars */
    borderC = (features.training.cols - 1) / 2;
    borderC_upper = cellhd.cols - borderC;
    borderR = (features.training.rows - 1) / 2;
    last_row = features.training.rows - 1;

    /*read first rows */
    for (r = 0; r < features.training.rows; r++) {
        rowbuf = (DCELL *)G_calloc(features.training.rows * cellhd.cols,
                                   sizeof(DCELL));
        tf = rowbuf;
        for (l = 0; l < features.training.nlayers; l++) {
            Rast_get_d_row(fd[l], tf, r);
            for (c = 0; c < cellhd.cols; c++) {
                if (Rast_is_d_null_value(tf))
                    *tf = 0.0;
                matrix[l][r][c] = *tf;
                tf++;
            }
        }
        G_free(rowbuf);
    }

    /*computing... */
    r = features.training.rows;

    while (r < cellhd.rows) {
        for (c = borderC; c < borderC_upper; c++) {
            corrent_feature = 0;
            for (l = 0; l < features.training.nlayers; l++) {
                set_null = extract_array_with_null(
                    features.training.rows, features.training.cols, c, borderC,
                    matrix[l], wind_vect);

                if (set_null) {
                    break;
                }
                else {
                    mean = mean_of_double_array(wind_vect, dim);
                    sd = sd_of_double_array_given_mean(wind_vect, dim, mean);

                    if (features.f_normalize[0]) {
                        for (j = 2; j < 2 + features.f_normalize[1]; j++) {
                            if (features.f_normalize[j] == l) {
                                for (i = 0; i < dim; i++) {
                                    wind_vect[i] = (wind_vect[i] - mean) / sd;
                                }
                                break;
                            }
                        }
                    }

                    if (!compute_features[l]) {
                        for (i = 0; i < dim; i++) {
                            X[corrent_feature + i] = wind_vect[i];
                        }
                        corrent_feature += dim;
                    }
                    else {
                        if (features.f_mean[0]) {
                            for (j = 2; j < 2 + features.f_mean[1]; j++) {
                                if (features.f_mean[j] == l) {
                                    X[corrent_feature] = mean;
                                    corrent_feature += 1;
                                    break;
                                }
                            }
                        }
                        if (features.f_variance[0]) {
                            for (j = 2; j < 2 + features.f_variance[1]; j++) {
                                if (features.f_variance[j] == l) {
                                    X[corrent_feature] = sd * sd;
                                    corrent_feature += 1;
                                    break;
                                }
                            }
                        }
                        if (features.f_pca[0]) {
                            for (j = 2; j < 2 + features.f_pca[1]; j++) {
                                if (features.f_pca[j] == l) {
                                    product_double_vector_double_matrix(
                                        features.pca[l].eigmat, wind_vect, dim,
                                        features.npc, projected);

                                    for (i = 0; i < features.npc; i++) {
                                        X[corrent_feature + i] = projected[i];
                                    }
                                    corrent_feature += features.npc;
                                    break;
                                }
                            }
                        }
                    }
                }
            }
            if (set_null) {
                output_cell[r][c] = 0.0;
            }
            else {
                if (features.f_standardize[0]) {
                    for (i = 2; i < 2 + features.f_standardize[1]; i++) {
                        X[features.f_standardize[i]] =
                            (X[features.f_standardize[i]] -
                             features.mean[i - 2]) /
                            features.sd[i - 2];
                    }
                }
                if (features.nclasses == 2) {
                    switch (model_type) {
                    case NN_model:
                        output_cell[r - borderR][c] =
                            predict_nn_2class(&nn, X, nn.k, features.nclasses,
                                              features.p_classes);
                        break;
                    case GM_model:
                        output_cell[r - borderR][c] = predict_gm_2class(&gm, X);
                        break;
                    case CT_model:
                        output_cell[r - borderR][c] =
                            predict_tree_2class(&tree, X);
                        break;
                    case SVM_model:
                        output_cell[r - borderR][c] = predict_svm(&svm, X);
                        break;
                    case BCT_model:
                        output_cell[r - borderR][c] =
                            predict_btree_2class(&btree, X);
                        break;
                    case BSVM_model:
                        output_cell[r - borderR][c] = predict_bsvm(&bsvm, X);
                        break;
                    default:
                        break;
                    }
                }
                else {
                    switch (model_type) {
                    case NN_model:
                        output_cell[r - borderR][c] = predict_nn_multiclass(
                            &nn, X, nn.k, features.nclasses,
                            features.p_classes);
                        break;
                    case GM_model:
                        output_cell[r - borderR][c] =
                            predict_gm_multiclass(&gm, X);
                        break;
                    case CT_model:
                        output_cell[r - borderR][c] =
                            predict_tree_multiclass(&tree, X);
                        break;
                    case BCT_model:
                        output_cell[r - borderR][c] =
                            predict_btree_multiclass(&btree, X);
                        break;
                    default:
                        break;
                    }
                }
            }
        }
        percent(r, cellhd.rows, 1);

        if (r < cellhd.rows) {
            for (l = 0; l < features.training.nlayers; l++) {
                for (R = 0; R < last_row; R++) {
                    for (C = 0; C < cellhd.cols; C++) {
                        matrix[l][R][C] = matrix[l][R + 1][C];
                    }
                }

                rowbuf = (DCELL *)G_calloc(cellhd.cols, sizeof(DCELL));
                tf = rowbuf;

                Rast_get_d_row(fd[l], tf, r);
                for (c = 0; c < cellhd.cols; c++) {
                    if (Rast_is_d_null_value(tf))
                        *tf = 0.0;
                    matrix[l][last_row][c] = *tf;
                    tf++;
                }
                G_free(rowbuf);
            }
        }
        r += 1;
    }
    /*
       for(r=0;r<cellhd.rows;r++){
       for(c=0;c<cellhd.cols;c++)
       fprintf(stderr,"%f\t",output_cell[r][c]);
       fprintf(stderr,"\n");
       }
     */
    {
        Blob *blobs1, *blobs2;
        BlobSites *sites1, *sites2;
        int nblobs1, npoints1;
        int nblobs2, npoints2;
        double tm, tM;
        int np;
        double mdist;
        double x1, x2, y1, y2, A, B;
        double X[2], Y[2];

        mdist = 100.0;
        x1 = 1.0;
        y1 = 0.5;
        x2 = 5.0;
        y2 = 0.0;
        A = (y2 - y1) / (x2 - x1);
        B = y1 - A * x1;

        tm = 0.5;
        tM = 1000000.0;

        nblobs1 = 0;
        npoints1 = 0;
        find_blob(output_cell, cellhd.rows, cellhd.cols, &blobs1, &npoints1,
                  &nblobs1, tm, tM);
        sites1 = (BlobSites *)G_calloc(nblobs1, sizeof(BlobSites));
        extract_sites_from_blob(blobs1, npoints1, nblobs1, &cellhd, sites1,
                                output_cell);

        tm = 0.00001;
        tM = 1000000.0;
        nblobs2 = 0;
        npoints2 = 0;
        find_blob(output_cell, cellhd.rows, cellhd.cols, &blobs2, &npoints2,
                  &nblobs2, tm, tM);
        sites2 = (BlobSites *)G_calloc(nblobs2, sizeof(BlobSites));
        extract_sites_from_blob(blobs2, npoints2, nblobs2, &cellhd, sites2,
                                output_cell);

        for (i = 0; i < nblobs2; i++) {
            np = 0;
            for (j = 0; j < nblobs1; j++) {
                X[0] = sites2[i].east;
                X[1] = sites2[i].north;
                Y[0] = sites1[j].east;
                Y[1] = sites1[j].north;

                if (euclidean_distance(X, Y, 2) <= mdist)
                    np += 1;
            }

            if (np > 0) {
                if (sites2[i].max > A * np + B)
                    fprintf(stdout, "%f|%f|#%d%s%f%s%f\n", sites2[i].east,
                            sites2[i].north, sites2[i].n, "%", sites2[i].min,
                            "%", sites2[i].max);
            }
        }
        /*
           for(j=0;j<nblobs2;j++)
           if(sites2[j].n>=1)
           fprintf(stdout,"%f|%f|#%d%s%f\n",sites2[j].east,sites2[j].north,
           sites2[j].n, "%",sites2[j].min);
         */
    }
    return 0;
}

int extract_array_with_null(int R, int C, int c, int bc, double **mat,
                            double *wind_vect)
{
    int i, j;
    double sum;
    int index;

    sum = 0.0;
    index = 0;
    for (i = 0; i < R; i++) {
        for (j = 0; j < C; j++) {
            wind_vect[index] = mat[i][c - bc + j];
            sum += wind_vect[index++];
        }
    }
    if (sum == 0.0) {
        return 1;
    }
    else {
        return 0;
    }
}
