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
#include <string.h>
#include <math.h>
#include <grass/gis.h>
#include <grass/raster.h>
#include <grass/glocale.h>
#include "global.h"

void generate_features();

int main(int argc, char **argv)
{
    struct GModule *module;
    struct Option *opt1;
    struct Option *opt2;
    struct Option *opt3;

    char *training_file[TRAINING_MAX_INPUTFILES];
    int ntraining_file;
    int i;
    Features features, features_out;
    char tempbuf[500];
    char opt1desc[500];

    /* Initialize the GIS calls */
    G_gisinit(argv[0]);

    module = G_define_module();
    G_add_keyword(_("imagery"));
    G_add_keyword(_("image processing"));
    G_add_keyword(_("pattern recognition"));
    module->description =
        _("Module to add new features to existing feature in i.pr.* modules. "
          "i.pr: Pattern Recognition environment for image processing. "
          "Includes kNN, "
          "Decision Tree and SVM classification techniques. Also includes "
          "cross-validation and bagging methods for model validation.");

    sprintf(opt1desc,
            "Input files (max %d) containing training data.\n\t\t2 formats are "
            "currently supported:\n\t\t1) GRASS_data (output of "
            "i.pr_training)\n\t\t2) TABLE_data.",
            TRAINING_MAX_INPUTFILES);

    /* set up command line */
    opt1 = G_define_option();
    opt1->key = "training";
    opt1->type = TYPE_STRING;
    opt1->required = YES;
    opt1->description = opt1desc;
    opt1->multiple = YES;

    opt2 = G_define_option();
    opt2->key = "features";
    opt2->type = TYPE_STRING;
    opt2->required = YES;
    opt2->description = "Name of the input file containing the features.";

    opt3 = G_define_option();
    opt3->key = "features_out";
    opt3->type = TYPE_STRING;
    opt3->required = YES;
    opt3->description =
        "Name of the output file containing the resulting features.";

    if (G_parser(argc, argv))
        exit(1);

    /*read input training files */
    ntraining_file = 0;
    for (i = 0; (training_file[ntraining_file] = opt1->answers[i]); i++) {
        ntraining_file += 1;
        if (ntraining_file > TRAINING_MAX_INPUTFILES) {
            sprintf(tempbuf, "Maximum nomber of allowed training files is %d",
                    TRAINING_MAX_INPUTFILES);
            G_fatal_error(tempbuf);
        }
    }

    /*fill training structure */
    inizialize_training(&(features_out.training));
    for (i = 0; i < ntraining_file; i++) {
        read_training(training_file[i], &(features_out.training));
    }

    /*read features */
    read_features(opt2->answer, &features, -1);

    /*which action to do on the data */
    features_out.f_normalize = features.f_normalize;
    features_out.f_standardize = features.f_standardize;
    features_out.f_mean = features.f_mean;
    features_out.f_variance = features.f_variance;
    features_out.f_pca = features.f_pca;
    features_out.f_standardize = features.f_standardize;

    if (features_out.f_pca[0]) {
        features_out.pca = features.pca;
        features_out.pca_class = (int *)G_calloc(1, sizeof(int));
    }

    /*fill features structure */
    generate_features(&features, &features_out);

    /*standardize features */
    if (features_out.f_standardize[0]) {
        features_out.mean = features.mean;
        features_out.sd = features.sd;
        standardize_features(&features_out);
    }

    /*write features */
    write_features(opt3->answer, &features_out);

    return 0;
}

void generate_features(Features *features, Features *features_out)
{
    int i, j, k, l;
    char *mapset;
    int fp;
    struct Cell_head cellhd;
    DCELL *rowbuf;
    DCELL *tf;
    DCELL **matrix;
    int r, c;
    char tempbuf[500];
    int *compute_features;
    int dim;
    DCELL *mean = NULL, *sd = NULL;
    int corrent_feature;
    int *space_for_each_layer;
    DCELL *projected = NULL;
    int addclass;

    compute_features =
        (int *)G_calloc(features_out->training.nlayers, sizeof(int));

    features_out->nexamples = features_out->training.nexamples;
    dim = features_out->training.rows * features_out->training.cols;

    /*compute space */
    space_for_each_layer =
        (int *)G_calloc(features_out->training.nlayers, sizeof(int));
    features_out->examples_dim = 0;
    for (j = 0; j < features_out->training.nlayers; j++) {
        if (features_out->f_mean[0]) {
            for (i = 2; i < 2 + features_out->f_mean[1]; i++) {
                if (features_out->f_mean[i] == j) {
                    compute_features[j] = TRUE;
                    space_for_each_layer[j] += 1;
                }
            }
        }
        if (features_out->f_variance[0]) {
            for (i = 2; i < 2 + features_out->f_variance[1]; i++) {
                if (features_out->f_variance[i] == j) {
                    compute_features[j] = TRUE;
                    space_for_each_layer[j] += 1;
                }
            }
        }
        if (features_out->f_pca[0]) {
            for (i = 2; i < 2 + features_out->f_pca[1]; i++) {
                if (features_out->f_pca[i] == j) {
                    compute_features[j] = TRUE;
                    space_for_each_layer[j] += dim;
                }
            }
        }
        if (space_for_each_layer[j] == 0) {
            space_for_each_layer[j] = dim;
        }
        features_out->examples_dim += space_for_each_layer[j];
    }

    /*alloc memory */
    features_out->value =
        (double **)G_calloc(features_out->nexamples, sizeof(double *));
    for (i = 0; i < features_out->nexamples; i++) {
        features_out->value[i] =
            (double *)G_calloc(features_out->examples_dim, sizeof(double));
    }
    features_out->class = (int *)G_calloc(features_out->nexamples, sizeof(int));

    matrix = (double **)G_calloc(features_out->nexamples, sizeof(double *));
    for (i = 0; i < features_out->nexamples; i++) {
        matrix[i] = (double *)G_calloc(dim, sizeof(double));
    }

    mean = (double *)G_calloc(features_out->nexamples, sizeof(double));
    sd = (double *)G_calloc(features_out->nexamples, sizeof(double));

    /*copy classes */
    for (i = 0; i < features_out->nexamples; i++) {
        features_out->class[i] = features_out->training.class[i];
    }

    /*compute p_classes */
    features_out->p_classes = (int *)G_calloc(1, sizeof(int));
    features_out->nclasses = 1;
    features_out->p_classes[0] = features_out->class[0];
    for (i = 1; i < features_out->nexamples; i++) {
        addclass = TRUE;
        for (j = 0; j < features_out->nclasses; j++) {
            if (features_out->class[i] == features_out->p_classes[j]) {
                addclass = FALSE;
            }
        }
        if (addclass) {
            features_out->nclasses += 1;
            features_out->p_classes = (int *)G_realloc(
                features_out->p_classes, features_out->nclasses * sizeof(int));
            features_out->p_classes[features_out->nclasses - 1] =
                features_out->class[i];
        }
    }

    if (features_out->f_pca[0]) {
        projected = (double *)G_calloc(dim, sizeof(double));
    }

    corrent_feature = 0;
    for (j = 0; j < features_out->training.nlayers; j++) {
        for (i = 0; i < features_out->nexamples; i++) {
            switch (features_out->training.data_type) {
            case GRASS_data:
                if ((mapset = (char *)G_find_raster(
                         features_out->training.mapnames[i][j], "")) == NULL) {
                    sprintf(tempbuf,
                            "generate_features-> Can't find raster map <%s>",
                            features_out->training.mapnames[i][j]);
                    G_fatal_error(tempbuf);
                }
                if ((fp = Rast_open_old(features_out->training.mapnames[i][j],
                                        mapset)) < 0) {
                    sprintf(tempbuf,
                            "generate_features-> Can't open raster map <%s> "
                            "for reading",
                            features_out->training.mapnames[i][j]);
                    G_fatal_error(tempbuf);
                }

                Rast_get_cellhd(features_out->training.mapnames[i][j], mapset,
                                &cellhd);
                G_set_window(&cellhd);
                if ((cellhd.rows != features_out->training.rows) ||
                    (cellhd.cols != features_out->training.cols)) {
                    /*      fprintf(stderr,"map number = %d\n",i); */
                    sprintf(tempbuf, "generate_features-> Dimension Error");
                    G_fatal_error(tempbuf);
                }
                rowbuf = (DCELL *)G_calloc(dim, sizeof(DCELL));
                tf = rowbuf;

                for (r = 0; r < features_out->training.rows; r++) {
                    Rast_get_d_row(fp, tf, r);
                    for (c = 0; c < features_out->training.cols; c++) {
                        if (Rast_is_d_null_value(tf))
                            *tf = 0.0;
                        matrix[i][c + (r * features_out->training.cols)] = *tf;
                        tf++;
                    }
                }
                G_free(rowbuf);

                Rast_close(fp);
                break;
            case TABLE_data:
                matrix[i] = features_out->training.data[i];
                break;
            default:
                sprintf(tempbuf, "generate_features-> Format not recognized");
                G_fatal_error(tempbuf);
                break;
            }
        }

        for (k = 0; k < features_out->nexamples; k++) {
            mean[k] = sd[k] = 0.0;
        }
        mean_and_sd_of_double_matrix_by_row(matrix, features_out->nexamples,
                                            dim, mean, sd);

        if (features_out->f_normalize[0]) {
            for (i = 2; i < 2 + features_out->f_normalize[1]; i++) {
                if (features_out->f_normalize[i] == j) {
                    for (k = 0; k < features_out->nexamples; k++) {
                        for (r = 0; r < dim; r++) {
                            matrix[k][r] = (matrix[k][r] - mean[k]) / sd[k];
                        }
                    }
                }
            }
        }

        if (!compute_features[j]) {
            for (i = 0; i < features_out->nexamples; i++) {
                for (r = 0; r < dim; r++) {
                    features_out->value[i][corrent_feature + r] = matrix[i][r];
                }
            }
            corrent_feature += dim;
        }
        else {
            if (features_out->f_mean[0]) {
                for (i = 2; i < 2 + features_out->f_mean[1]; i++) {
                    if (features_out->f_mean[i] == j) {
                        for (k = 0; k < features_out->nexamples; k++) {
                            features_out->value[k][corrent_feature] = mean[k];
                        }
                        corrent_feature += 1;
                    }
                }
            }

            if (features_out->f_variance[0]) {
                for (i = 2; i < 2 + features_out->f_variance[1]; i++) {
                    if (features_out->f_variance[i] == j) {
                        for (k = 0; k < features_out->nexamples; k++) {
                            features_out->value[k][corrent_feature] =
                                sd[k] * sd[k];
                        }
                        corrent_feature += 1;
                    }
                }
            }

            if (features_out->f_pca[0]) {
                for (i = 2; i < 2 + features_out->f_pca[1]; i++) {
                    if (features_out->f_pca[i] == j) {
                        for (l = 0; l < features_out->nexamples; l++) {
                            product_double_vector_double_matrix(
                                features_out->pca[j].eigmat, matrix[l], dim,
                                dim, projected);
                            for (r = 0; r < dim; r++) {
                                features_out->value[l][corrent_feature + r] =
                                    projected[r];
                            }
                        }
                        corrent_feature += dim;
                    }
                }
            }
        }
    }

    G_free(mean);
    G_free(sd);
    G_free(compute_features);
}
