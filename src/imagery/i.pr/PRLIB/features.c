/*
   The following routines are written and tested by Stefano Merler

   for

   structure Feature management
 */

#include <grass/gis.h>
#include <grass/raster.h>
#include "global.h"
#include <stdlib.h>
#include <string.h>

void compute_features(Features *features)

/*
   given a training structure in input, fill the features structure
   according to specification lyke
   features->f_mean
   features->f_variance
   features->f_pca
   features->f_texture (not yet implemented)
 */
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
    DCELL **pca_matrix = NULL;
    int ndata_for_pca = 0;
    int index;
    int thisclassok;
    int addclass;

    compute_features = (int *)G_calloc(features->training.nlayers, sizeof(int));

    features->nexamples = features->training.nexamples;
    dim = features->training.rows * features->training.cols;

    /*compute space */
    space_for_each_layer =
        (int *)G_calloc(features->training.nlayers, sizeof(int));

    features->examples_dim = 0;
    for (j = 0; j < features->training.nlayers; j++) {
        if (features->f_mean[0]) {
            for (i = 2; i < 2 + features->f_mean[1]; i++) {
                if (features->f_mean[i] == j) {
                    compute_features[j] = TRUE;
                    space_for_each_layer[j] += 1;
                }
            }
        }
        if (features->f_variance[0]) {
            for (i = 2; i < 2 + features->f_variance[1]; i++) {
                if (features->f_variance[i] == j) {
                    compute_features[j] = TRUE;
                    space_for_each_layer[j] += 1;
                }
            }
        }
        if (features->f_pca[0]) {
            for (i = 2; i < 2 + features->f_pca[1]; i++) {
                if (features->f_pca[i] == j) {
                    compute_features[j] = TRUE;
                    space_for_each_layer[j] += dim;
                }
            }
        }
        if (space_for_each_layer[j] == 0) {
            space_for_each_layer[j] = dim;
        }
        features->examples_dim += space_for_each_layer[j];
    }

    /*alloc memory */
    features->value =
        (double **)G_calloc(features->nexamples, sizeof(double *));
    for (i = 0; i < features->nexamples; i++) {
        features->value[i] =
            (double *)G_calloc(features->examples_dim, sizeof(double));
    }
    features->class = (int *)G_calloc(features->nexamples, sizeof(int));

    matrix = (double **)G_calloc(features->nexamples, sizeof(double *));
    for (i = 0; i < features->nexamples; i++) {
        matrix[i] = (double *)G_calloc(dim, sizeof(double));
    }

    mean = (double *)G_calloc(features->nexamples, sizeof(double));
    sd = (double *)G_calloc(features->nexamples, sizeof(double));

    /*copy classes */
    for (i = 0; i < features->nexamples; i++) {
        features->class[i] = features->training.class[i];
    }

    /*compute p_classes */
    features->p_classes = (int *)G_calloc(1, sizeof(int));
    features->nclasses = 1;
    features->p_classes[0] = features->class[0];
    for (i = 1; i < features->nexamples; i++) {
        addclass = TRUE;
        for (j = 0; j < features->nclasses; j++) {
            if (features->class[i] == features->p_classes[j]) {
                addclass = FALSE;
            }
        }
        if (addclass) {
            features->nclasses += 1;
            features->p_classes = (int *)G_realloc(
                features->p_classes, features->nclasses * sizeof(int));
            features->p_classes[features->nclasses - 1] = features->class[i];
        }
    }

    /*space for pca */
    if (features->f_pca[0]) {
        features->pca =
            (Pca *)G_calloc(features->training.nlayers, sizeof(Pca));
        for (i = 0; i < features->training.nlayers; i++) {
            inizialize_pca(&(features->pca[i]), dim);
        }
        projected = (double *)G_calloc(dim, sizeof(double));

        if (features->pca_class[0] == 0) {
            fprintf(stderr,
                    "principal components computed on all training data\n");
        }
        else {
            fprintf(stderr, "principal components computed on data of classes");
            for (l = 1; l <= features->pca_class[1]; l++) {
                thisclassok = FALSE;
                for (k = 0; k < features->nclasses; k++) {
                    if (features->pca_class[1 + l] == features->p_classes[k]) {
                        thisclassok = TRUE;
                        fprintf(stderr, " %d", features->p_classes[k]);
                        break;
                    }
                }
                if (!thisclassok) {
                    sprintf(tempbuf,
                            "compute_features-> Class %d for pc not recognized",
                            features->pca_class[1 + l]);
                    G_fatal_error(tempbuf);
                }
            }
            fprintf(stderr, "\n");
        }

        ndata_for_pca = 0;
        for (l = 0; l < features->nexamples; l++) {
            for (r = 2; r < (2 + features->pca_class[1]); r++) {
                if (features->class[l] == features->pca_class[r]) {
                    ndata_for_pca += 1;
                }
            }
        }
        pca_matrix = (double **)G_calloc(ndata_for_pca, sizeof(double *));
        for (l = 0; l < ndata_for_pca; l++) {
            pca_matrix[l] = (double *)G_calloc(dim, sizeof(double));
        }
    }

    corrent_feature = 0;
    for (j = 0; j < features->training.nlayers; j++) {
        for (i = 0; i < features->nexamples; i++) {
            switch (features->training.data_type) {
            case GRASS_data:
                fprintf(stdout, "%s\n", features->training.mapnames[i][j]);
                if ((mapset = (char *)G_find_raster(
                         features->training.mapnames[i][j], "")) == NULL) {
                    sprintf(tempbuf,
                            "compute_features-> Can't find raster map <%s>",
                            features->training.mapnames[i][j]);
                    G_fatal_error(tempbuf);
                }
                if ((fp = Rast_open_old(features->training.mapnames[i][j],
                                        mapset)) < 0) {
                    sprintf(tempbuf,
                            "compute_features-> Can't open raster map <%s> for "
                            "reading",
                            features->training.mapnames[i][j]);
                    G_fatal_error(tempbuf);
                }

                Rast_get_cellhd(features->training.mapnames[i][j], mapset,
                                &cellhd);
                G_set_window(&cellhd);
                if ((cellhd.rows != features->training.rows) ||
                    (cellhd.cols != features->training.cols)) {
                    sprintf(tempbuf, "compute_features-> Dimension Error");
                    G_fatal_error(tempbuf);
                }
                rowbuf = (DCELL *)G_calloc(dim, sizeof(DCELL));
                tf = rowbuf;

                for (r = 0; r < features->training.rows; r++) {
                    Rast_get_d_row(fp, tf, r);
                    for (c = 0; c < features->training.cols; c++) {
                        if (Rast_is_d_null_value(tf))
                            *tf = 0.0;
                        matrix[i][c + (r * features->training.cols)] = *tf;
                        tf++;
                    }
                }
                G_free(rowbuf);

                Rast_close(fp);

                break;
            case TABLE_data:
                matrix[i] = features->training.data[i];
                break;
            default:
                sprintf(tempbuf, "compute_features-> Format not recognized");
                G_fatal_error(tempbuf);
                break;
            }
        }

        for (k = 0; k < features->nexamples; k++) {
            mean[k] = sd[k] = 0.0;
        }
        mean_and_sd_of_double_matrix_by_row(matrix, features->nexamples, dim,
                                            mean, sd);

        if (features->f_normalize[0]) {
            for (i = 2; i < 2 + features->f_normalize[1]; i++) {
                if (features->f_normalize[i] == j) {
                    for (k = 0; k < features->nexamples; k++) {
                        for (r = 0; r < dim; r++) {
                            matrix[k][r] = (matrix[k][r] - mean[k]) / sd[k];
                        }
                    }
                }
            }
        }

        if (!compute_features[j]) {
            for (i = 0; i < features->nexamples; i++) {
                for (r = 0; r < dim; r++) {
                    features->value[i][corrent_feature + r] = matrix[i][r];
                }
            }
            corrent_feature += dim;
        }
        else {
            if (features->f_mean[0]) {
                for (i = 2; i < 2 + features->f_mean[1]; i++) {
                    if (features->f_mean[i] == j) {
                        for (k = 0; k < features->nexamples; k++) {
                            features->value[k][corrent_feature] = mean[k];
                        }
                        corrent_feature += 1;
                    }
                }
            }

            if (features->f_variance[0]) {
                for (i = 2; i < 2 + features->f_variance[1]; i++) {
                    if (features->f_variance[i] == j) {
                        for (k = 0; k < features->nexamples; k++) {
                            features->value[k][corrent_feature] = sd[k] * sd[k];
                        }
                        corrent_feature += 1;
                    }
                }
            }

            if (features->f_pca[0]) {
                for (i = 2; i < 2 + features->f_pca[1]; i++) {
                    if (features->f_pca[i] == j) {
                        if (features->pca_class[0] == 0) {
                            covariance_of_double_matrix(
                                matrix, features->nexamples, dim,
                                features->pca[j].covar);
                        }
                        else {
                            index = 0;
                            for (l = 0; l < features->nexamples; l++) {
                                for (r = 2; r < (2 + features->pca_class[1]);
                                     r++) {
                                    if (features->training.class[l] ==
                                        features->pca_class[r]) {
                                        pca_matrix[index++] = matrix[l];
                                    }
                                }
                            }
                            covariance_of_double_matrix(pca_matrix,
                                                        ndata_for_pca, dim,
                                                        features->pca[j].covar);
                        }
                        eigen_of_double_matrix(features->pca[j].covar,
                                               features->pca[j].eigmat,
                                               features->pca[j].eigval, dim);
                        eigsrt(features->pca[j].eigval, features->pca[j].eigmat,
                               dim);
                        for (l = 0; l < features->nexamples; l++) {
                            product_double_vector_double_matrix(
                                features->pca[j].eigmat, matrix[l], dim, dim,
                                projected);
                            for (r = 0; r < dim; r++) {
                                features->value[l][corrent_feature + r] =
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

void write_features(char *file, Features *features)

/*
   write the features into a file
 */
{
    FILE *fp;
    int i, j, l, k;
    int dim;
    char tempbuf[500];
    int write_x;

    fp = fopen(file, "w");
    if (fp == NULL) {
        sprintf(tempbuf, "write_features-> Can't open file %s for writing",
                file);
        G_fatal_error(tempbuf);
    }

    fprintf(fp, "#####################\n");
    fprintf(fp, "TRAINING: (%s)\n", features->training.file);
    fprintf(fp, "#####################\n");

    fprintf(fp, "Type of data:\n");
    fprintf(fp, "%d\n", features->training.data_type);

    fprintf(fp, "Number of layers:\n");
    fprintf(fp, "%d\n", features->training.nlayers);

    fprintf(fp, "Training dimensions:\n");
    fprintf(fp, "%d\t%d\n", features->training.rows, features->training.cols);

    dim = features->training.rows * features->training.cols;

    fprintf(fp, "EW-res\tNS-res\n");
    fprintf(fp, "%f\t%f\n", features->training.ew_res,
            features->training.ns_res);

    fprintf(fp, "#####################\n");
    fprintf(fp, "FEATURES:\n");
    fprintf(fp, "#####################\n");

    fprintf(fp, "normalize:\n");
    if (features->f_normalize[0]) {
        fprintf(fp, "%d\t%d\t%d", features->f_normalize[0],
                features->f_normalize[1], features->f_normalize[2] + 1);
        for (i = 3; i < 2 + features->f_normalize[1]; i++) {
            fprintf(fp, "\t%d", features->f_normalize[2] + 1);
        }
        fprintf(fp, "\n");
    }
    else {
        fprintf(fp, "0\n");
    }

    fprintf(fp, "standardize:\n");
    if (features->f_standardize[0]) {
        fprintf(fp, "%d\t%d\t%d", features->f_standardize[0],
                features->f_standardize[1], features->f_standardize[2] + 1);
        for (i = 3; i < 2 + features->f_standardize[1]; i++) {
            fprintf(fp, "\t%d", features->f_standardize[i] + 1);
        }
        fprintf(fp, "\n");
    }
    else {
        fprintf(fp, "0\n");
    }

    fprintf(fp, "mean:\n");
    if (features->f_mean[0]) {
        fprintf(fp, "%d\t%d\t%d", features->f_mean[0], features->f_mean[1],
                features->f_mean[2] + 1);
        for (i = 3; i < 2 + features->f_mean[1]; i++) {
            fprintf(fp, "\t%d", features->f_mean[i] + 1);
        }
        fprintf(fp, "\n");
    }
    else {
        fprintf(fp, "0\n");
    }

    fprintf(fp, "variance:\n");
    if (features->f_variance[0]) {
        fprintf(fp, "%d\t%d\t%d", features->f_variance[0],
                features->f_variance[1], features->f_variance[2] + 1);
        for (i = 3; i < 2 + features->f_variance[1]; i++) {
            fprintf(fp, "\t%d", features->f_variance[i] + 1);
        }
        fprintf(fp, "\n");
    }
    else {
        fprintf(fp, "0\n");
    }

    fprintf(fp, "pca:\n");
    if (features->f_pca[0]) {
        fprintf(fp, "%d\t%d\t%d", features->f_pca[0], features->f_pca[1],
                features->f_pca[2] + 1);
        for (i = 3; i < 2 + features->f_pca[1]; i++) {
            fprintf(fp, "\t%d", features->f_pca[i] + 1);
        }
        fprintf(fp, "\n");
    }
    else {
        fprintf(fp, "0\n");
    }

    fprintf(fp, "Number of classes:\n");
    fprintf(fp, "%d\n", features->nclasses);

    fprintf(fp, "Classes:\n");
    fprintf(fp, "%d", features->p_classes[0]);
    for (i = 1; i < features->nclasses; i++) {
        fprintf(fp, "\t%d", features->p_classes[i]);
    }
    fprintf(fp, "\n");

    fprintf(fp, "Standardization values:\n");
    if (features->f_standardize[0]) {
        fprintf(fp, "%f", features->mean[0]);
        for (i = 1; i < features->f_standardize[1]; i++) {
            fprintf(fp, "\t%f", features->mean[i]);
        }
        fprintf(fp, "\n");
        fprintf(fp, "%f", features->sd[0]);
        for (i = 1; i < features->f_standardize[1]; i++) {
            fprintf(fp, "\t%f", features->sd[i]);
        }
        fprintf(fp, "\n");
    }
    else {
        fprintf(fp, "NULL\n");
        fprintf(fp, "NULL\n");
    }

    fprintf(fp, "Features dimensions:\n");
    fprintf(fp, "%d\t%d\n", features->nexamples, features->examples_dim);

    fprintf(fp, "Features:\n");

    for (i = 0; i < features->training.nlayers; i++) {
        write_x = TRUE;
        if (features->f_mean[0]) {
            for (j = 2; j < 2 + features->f_mean[1]; j++) {
                if (features->f_mean[j] == i) {
                    write_x = FALSE;
                    fprintf(fp, "l%d_mean\t", i + 1);
                }
            }
        }
        if (features->f_variance[0]) {
            for (j = 2; j < 2 + features->f_variance[1]; j++) {
                if (features->f_variance[j] == i) {
                    write_x = FALSE;
                    fprintf(fp, "l%d_variance\t", i + 1);
                }
            }
        }
        if (features->f_pca[0]) {
            for (j = 2; j < 2 + features->f_pca[1]; j++) {
                if (features->f_pca[j] == i) {
                    write_x = FALSE;
                    for (k = 0; k < dim; k++) {
                        fprintf(fp, "l%d_pc%d\t", i + 1, k + 1);
                    }
                }
            }
        }

        if (write_x) {
            for (j = 0; j < dim; j++) {
                fprintf(fp, "l%d_x%d\t", i + 1, j + 1);
            }
        }
        if ((i + 1) == features->training.nlayers) {
            fprintf(fp, "class\n");
        }
    }

    for (i = 0; i < features->nexamples; i++) {
        for (j = 0; j < features->examples_dim; j++) {
            fprintf(fp, "%f\t", features->value[i][j]);
        }
        fprintf(fp, "%d\n", features->class[i]);
    }

    if (features->f_pca[0]) {

        fprintf(fp, "#####################\n");
        fprintf(fp, "PRINC. COMP.:");
        if (features->pca_class[0] == 0) {
            fprintf(fp, " all classes used\n");
        }
        else {
            for (i = 0; i < features->pca_class[1]; i++) {
                fprintf(fp, " %d", features->pca_class[2 + i]);
            }
            fprintf(fp, " classes used\n");
        }
        fprintf(fp, "#####################\n");
        for (l = 2; l < 2 + features->f_pca[1]; l++) {
            fprintf(fp, "PCA: Layer %d\n", features->f_pca[l] + 1);
            write_pca(fp, &(features->pca[l - 2]));
        }
    }
    fclose(fp);
}

void standardize_features(Features *features)

/*
   standardize fetures accordining to the fetures.f_standardize array
 */
{
    int j, k;

    double *tmparray;
    char tempbuf[500];

    for (j = 2; j < 2 + features->f_standardize[1]; j++) {
        if ((features->f_standardize[j] < 0) ||
            (features->f_standardize[j] >= features->examples_dim)) {
            sprintf(tempbuf,
                    "standardize_features-> Can't standardize var number %d: "
                    "no such variable",
                    features->f_standardize[j] + 1);
            G_fatal_error(tempbuf);
        }
    }

    tmparray = (double *)G_calloc(features->nexamples, sizeof(double));

    features->mean =
        (double *)G_calloc(features->f_standardize[1], sizeof(double));
    features->sd =
        (double *)G_calloc(features->f_standardize[1], sizeof(double));

    for (j = 2; j < 2 + features->f_standardize[1]; j++) {
        for (k = 0; k < features->nexamples; k++) {
            tmparray[k] = features->value[k][features->f_standardize[j]];
        }
        features->mean[j - 2] =
            mean_of_double_array(tmparray, features->nexamples);
        features->sd[j - 2] = sd_of_double_array_given_mean(
            tmparray, features->nexamples, features->mean[j - 2]);
        if (features->sd[j - 2] == 0) {
            sprintf(
                tempbuf,
                "standardize_features-> Can't standardize var number %d: sd=0",
                features->f_standardize[j] + 1);
            G_fatal_error(tempbuf);
        }
        for (k = 0; k < features->nexamples; k++) {
            features->value[k][features->f_standardize[j]] =
                (tmparray[k] - features->mean[j - 2]) / features->sd[j - 2];
        }
    }

    G_free(tmparray);
}

void write_header_features(FILE *fp, Features *features)

/*
   write the header features into the pointed  file
 */
{
    int i;
    int dim;

    fprintf(fp, "#####################\n");
    fprintf(fp, "TRAINING:\n");
    fprintf(fp, "#####################\n");

    fprintf(fp, "Type of data:\n");
    fprintf(fp, "%d\n", features->training.data_type);

    fprintf(fp, "Number of layers:\n");
    fprintf(fp, "%d\n", features->training.nlayers);

    fprintf(fp, "Training dimensions:\n");
    fprintf(fp, "%d\t%d\n", features->training.rows, features->training.cols);

    dim = features->training.rows * features->training.cols;

    fprintf(fp, "EW-res\tNS-res\n");
    fprintf(fp, "%f\t%f\n", features->training.ew_res,
            features->training.ns_res);

    fprintf(fp, "#####################\n");
    fprintf(fp, "FEATURES: (%s)\n", features->file);
    fprintf(fp, "#####################\n");

    fprintf(fp, "normalize:\n");
    if (features->f_normalize[0]) {
        fprintf(fp, "%d\t%d\t%d", features->f_normalize[0],
                features->f_normalize[1], features->f_normalize[2] + 1);
        for (i = 3; i < 2 + features->f_normalize[1]; i++) {
            fprintf(fp, "\t%d", features->f_normalize[2] + 1);
        }
        fprintf(fp, "\n");
    }
    else {
        fprintf(fp, "0\n");
    }

    fprintf(fp, "standardize:\n");
    if (features->f_standardize[0]) {
        fprintf(fp, "%d\t%d\t%d", features->f_standardize[0],
                features->f_standardize[1], features->f_standardize[2] + 1);
        for (i = 3; i < 2 + features->f_standardize[1]; i++) {
            fprintf(fp, "\t%d", features->f_standardize[i] + 1);
        }
        fprintf(fp, "\n");
    }
    else {
        fprintf(fp, "0\n");
    }

    fprintf(fp, "mean:\n");
    if (features->f_mean[0]) {
        fprintf(fp, "%d\t%d\t%d", features->f_mean[0], features->f_mean[1],
                features->f_mean[2] + 1);
        for (i = 3; i < 2 + features->f_mean[1]; i++) {
            fprintf(fp, "\t%d", features->f_mean[i] + 1);
        }
        fprintf(fp, "\n");
    }
    else {
        fprintf(fp, "0\n");
    }

    fprintf(fp, "variance:\n");
    if (features->f_variance[0]) {
        fprintf(fp, "%d\t%d\t%d", features->f_variance[0],
                features->f_variance[1], features->f_variance[2] + 1);
        for (i = 3; i < 2 + features->f_variance[1]; i++) {
            fprintf(fp, "\t%d", features->f_variance[i] + 1);
        }
        fprintf(fp, "\n");
    }
    else {
        fprintf(fp, "0\n");
    }

    fprintf(fp, "pca:\n");
    if (features->f_pca[0]) {
        fprintf(fp, "%d\t%d\t%d", features->f_pca[0], features->f_pca[1],
                features->f_pca[2] + 1);
        for (i = 3; i < 2 + features->f_pca[1]; i++) {
            fprintf(fp, "\t%d", features->f_pca[i] + 1);
        }
        fprintf(fp, "\n");
    }
    else {
        fprintf(fp, "0\n");
    }

    fprintf(fp, "Number of classes:\n");
    fprintf(fp, "%d\n", features->nclasses);

    fprintf(fp, "Classes:\n");
    fprintf(fp, "%d", features->p_classes[0]);
    for (i = 1; i < features->nclasses; i++) {
        fprintf(fp, "\t%d", features->p_classes[i]);
    }
    fprintf(fp, "\n");

    fprintf(fp, "Standardization values:\n");
    if (features->f_standardize[0]) {
        fprintf(fp, "%f", features->mean[0]);
        for (i = 1; i < features->f_standardize[1]; i++) {
            fprintf(fp, "\t%f", features->mean[i]);
        }
        fprintf(fp, "\n");
        fprintf(fp, "%f", features->sd[0]);
        for (i = 1; i < features->f_standardize[1]; i++) {
            fprintf(fp, "\t%f", features->sd[i]);
        }
        fprintf(fp, "\n");
    }
    else {
        fprintf(fp, "NULL\n");
        fprintf(fp, "NULL\n");
    }

    fprintf(fp, "Features dimensions:\n");
    fprintf(fp, "%d\t%d\n", features->nexamples, features->examples_dim);
}

void read_features(char *file, Features *features, int npc)

/*
   read the features from a file. If pc structure is contained
   within features, only load the first npc component. If npc < 0
   all the pc will be loaded.
 */
{
    FILE *fp;
    char tempbuf[500];
    char *line = NULL;
    int i, j, l, r;
    int dim;
    int *features_to_be_loaded;
    int orig_dim;
    int index;
    int corrent_feature;

    fp = fopen(file, "r");
    if (fp == NULL) {
        sprintf(tempbuf, "read_features-> Can't open file %s for reading",
                file);
        G_fatal_error(tempbuf);
    }

    features->file = file;

    line = GetLine(fp);
    line = GetLine(fp);
    line = GetLine(fp);
    sscanf(line, "%d", &(features->training.data_type));
    line = GetLine(fp);
    line = GetLine(fp);
    sscanf(line, "%d", &(features->training.nlayers));
    line = GetLine(fp);
    line = GetLine(fp);
    sscanf(line, "%d%d", &(features->training.rows),
           &(features->training.cols));
    line = GetLine(fp);
    line = GetLine(fp);
    sscanf(line, "%lf%lf", &(features->training.ew_res),
           &(features->training.ns_res));

    line = GetLine(fp);
    line = GetLine(fp);
    line = GetLine(fp);
    features->f_normalize = (int *)G_calloc(2, sizeof(int));
    sscanf(line, "%d", &(features->f_normalize[0]));
    if (features->f_normalize[0]) {
        line = (char *)strchr(line, '\t');
        line++;
        sscanf(line, "%d", &(features->f_normalize[1]));
        features->f_normalize =
            (int *)G_realloc(features->f_normalize,
                             (2 + features->f_normalize[1]) * sizeof(int));
        for (i = 0; i < features->f_normalize[1]; i++) {
            line = (char *)strchr(line, '\t');
            line++;
            sscanf(line, "%d", &(features->f_normalize[i + 2]));
            features->f_normalize[i + 2] -= 1;
        }
    }

    line = GetLine(fp);
    line = GetLine(fp);
    features->f_standardize = (int *)G_calloc(2, sizeof(int));
    sscanf(line, "%d", &(features->f_standardize[0]));
    if (features->f_standardize[0]) {
        line = (char *)strchr(line, '\t');
        line++;
        sscanf(line, "%d", &(features->f_standardize[1]));
        features->f_standardize =
            (int *)G_realloc(features->f_standardize,
                             (2 + features->f_standardize[1]) * sizeof(int));
        for (i = 0; i < features->f_standardize[1]; i++) {
            line = (char *)strchr(line, '\t');
            line++;
            sscanf(line, "%d", &(features->f_standardize[i + 2]));
            features->f_standardize[i + 2] -= 1;
        }
    }

    line = GetLine(fp);
    line = GetLine(fp);
    features->f_mean = (int *)G_calloc(2, sizeof(int));
    sscanf(line, "%d", &(features->f_mean[0]));
    if (features->f_mean[0]) {
        line = (char *)strchr(line, '\t');
        line++;
        sscanf(line, "%d", &(features->f_mean[1]));
        features->f_mean = (int *)G_realloc(
            features->f_mean, (2 + features->f_mean[1]) * sizeof(int));
        for (i = 0; i < features->f_mean[1]; i++) {
            line = (char *)strchr(line, '\t');
            line++;
            sscanf(line, "%d", &(features->f_mean[i + 2]));
            features->f_mean[i + 2] -= 1;
        }
    }

    line = GetLine(fp);
    line = GetLine(fp);
    features->f_variance = (int *)G_calloc(2, sizeof(int));
    sscanf(line, "%d", &(features->f_variance[0]));
    if (features->f_variance[0]) {
        line = (char *)strchr(line, '\t');
        line++;
        sscanf(line, "%d", &(features->f_variance[1]));
        features->f_variance = (int *)G_realloc(
            features->f_variance, (2 + features->f_variance[1]) * sizeof(int));
        for (i = 0; i < features->f_variance[1]; i++) {
            line = (char *)strchr(line, '\t');
            line++;
            sscanf(line, "%d", &(features->f_variance[i + 2]));
            features->f_variance[i + 2] -= 1;
        }
    }

    line = GetLine(fp);
    line = GetLine(fp);
    features->f_pca = (int *)G_calloc(2, sizeof(int));
    sscanf(line, "%d", &(features->f_pca[0]));
    if (features->f_pca[0]) {
        line = (char *)strchr(line, '\t');
        line++;
        sscanf(line, "%d", &(features->f_pca[1]));
        features->f_pca = (int *)G_realloc(
            features->f_pca, (2 + features->f_pca[1]) * sizeof(int));
        for (i = 0; i < features->f_pca[1]; i++) {
            line = (char *)strchr(line, '\t');
            line++;
            sscanf(line, "%d", &(features->f_pca[i + 2]));
            features->f_pca[i + 2] -= 1;
        }
    }

    line = GetLine(fp);
    line = GetLine(fp);
    sscanf(line, "%d", &(features->nclasses));
    features->p_classes = (int *)G_calloc(features->nclasses, sizeof(int));
    line = GetLine(fp);
    line = GetLine(fp);
    for (i = 0; i < features->nclasses; i++) {
        sscanf(line, "%d", &(features->p_classes[i]));
        line = (char *)strchr(line, '\t');
        line++;
    }

    if (!features->f_standardize[0]) {
        line = GetLine(fp);
        line = GetLine(fp);
        line = GetLine(fp);
    }
    else {
        features->mean =
            (double *)G_calloc(features->f_standardize[1], sizeof(double));
        features->sd =
            (double *)G_calloc(features->f_standardize[1], sizeof(double));
        line = GetLine(fp);
        line = GetLine(fp);
        for (i = 0; i < features->f_standardize[1]; i++) {
            sscanf(line, "%lf", &(features->mean[i]));
            line = (char *)strchr(line, '\t');
            line++;
        }
        line = GetLine(fp);
        for (i = 0; i < features->f_standardize[1]; i++) {
            sscanf(line, "%lf", &(features->sd[i]));
            line = (char *)strchr(line, '\t');
            line++;
        }
    }

    if (features->f_pca[0]) {
        features->pca = (Pca *)G_calloc(features->f_pca[1], sizeof(Pca));
    }

    if (npc > (features->training.rows * features->training.cols)) {
        npc = features->training.rows * features->training.cols;
    }

    dim = features->training.rows * features->training.cols;
    line = GetLine(fp);
    line = GetLine(fp);
    if ((!features->f_pca[0]) || (features->f_pca[0] && npc < 0)) {
        sscanf(line, "%d%d", &(features->nexamples), &(features->examples_dim));

        features->value =
            (double **)G_calloc(features->nexamples, sizeof(double *));
        for (i = 0; i < features->nexamples; i++) {
            features->value[i] =
                (double *)G_calloc(features->examples_dim, sizeof(double));
        }
        features->class = (int *)G_calloc(features->nexamples, sizeof(int));

        line = GetLine(fp);
        line = GetLine(fp);
        for (i = 0; i < features->nexamples; i++) {
            line = GetLine(fp);
            for (j = 0; j < features->examples_dim; j++) {
                sscanf(line, "%lf", &(features->value[i][j]));
                line = (char *)strchr(line, '\t');
                line++;
            }
            sscanf(line, "%d", &(features->class[i]));
        }
    }
    else {
        sscanf(line, "%d%d", &(features->nexamples), &orig_dim);

        features_to_be_loaded = (int *)G_calloc(orig_dim, sizeof(int));

        corrent_feature = 0;
        features->examples_dim = 0;
        for (i = 0; i < features->training.nlayers; i++) {
            if (features->f_mean[0]) {
                for (j = 2; j < 2 + features->f_mean[1]; j++) {
                    if (features->f_mean[j] == i) {
                        features_to_be_loaded[corrent_feature] = 1;
                        corrent_feature += 1;
                        features->examples_dim += 1;
                    }
                }
            }
            if (features->f_variance[0]) {
                for (j = 2; j < 2 + features->f_variance[1]; j++) {
                    if (features->f_variance[j] == i) {
                        features_to_be_loaded[corrent_feature] = 1;
                        corrent_feature += 1;
                        features->examples_dim += 1;
                    }
                }
            }
            if (features->f_pca[0]) {
                for (j = 2; j < 2 + features->f_pca[1]; j++) {
                    if (features->f_pca[j] == i) {
                        for (r = 0; r < npc; r++) {
                            features_to_be_loaded[corrent_feature + r] = 1;
                        }
                        corrent_feature += dim;
                        features->examples_dim += npc;
                    }
                }
            }
        }

        features->value =
            (double **)G_calloc(features->nexamples, sizeof(double *));
        for (i = 0; i < features->nexamples; i++) {
            features->value[i] =
                (double *)G_calloc(features->examples_dim, sizeof(double));
        }
        features->class = (int *)G_calloc(features->nexamples, sizeof(int));

        line = GetLine(fp);
        line = GetLine(fp);
        for (i = 0; i < features->nexamples; i++) {
            line = GetLine(fp);
            index = 0;
            for (j = 0; j < orig_dim; j++) {
                if (features_to_be_loaded[j] == 1) {
                    sscanf(line, "%lf", &(features->value[i][index++]));
                }
                line = (char *)strchr(line, '\t');
                line++;
            }
            sscanf(line, "%d", &(features->class[i]));
        }
    }
    if (features->f_pca[0]) {
        line = GetLine(fp);

        for (l = 0; l < features->f_pca[1]; l++) {
            features->pca[l].n =
                features->training.rows * features->training.cols;
            read_pca(fp, &(features->pca[l]));
        }
    }
    fclose(fp);
}

void read_header_features(FILE *fp, Features *features)

/*
   read the hearder features from the file pointed
 */
{
    char *line = NULL;
    int i;

    line = GetLine(fp);
    line = GetLine(fp);
    line = GetLine(fp);
    sscanf(line, "%d", &(features->training.data_type));
    line = GetLine(fp);
    line = GetLine(fp);
    sscanf(line, "%d", &(features->training.nlayers));
    line = GetLine(fp);
    line = GetLine(fp);
    sscanf(line, "%d%d", &(features->training.rows),
           &(features->training.cols));
    line = GetLine(fp);
    line = GetLine(fp);
    sscanf(line, "%lf%lf", &(features->training.ew_res),
           &(features->training.ns_res));

    line = GetLine(fp);
    line = GetLine(fp);
    line = GetLine(fp);
    features->f_normalize = (int *)G_calloc(2, sizeof(int));
    sscanf(line, "%d", &(features->f_normalize[0]));
    if (features->f_normalize[0]) {
        line = (char *)strchr(line, '\t');
        line++;
        sscanf(line, "%d", &(features->f_normalize[1]));
        features->f_normalize =
            (int *)G_realloc(features->f_normalize,
                             (2 + features->f_normalize[1]) * sizeof(int));
        for (i = 0; i < features->f_normalize[1]; i++) {
            line = (char *)strchr(line, '\t');
            line++;
            sscanf(line, "%d", &(features->f_normalize[i + 2]));
            features->f_normalize[i + 2] -= 1;
        }
    }

    line = GetLine(fp);
    line = GetLine(fp);
    features->f_standardize = (int *)G_calloc(2, sizeof(int));
    sscanf(line, "%d", &(features->f_standardize[0]));
    if (features->f_standardize[0]) {
        line = (char *)strchr(line, '\t');
        line++;
        sscanf(line, "%d", &(features->f_standardize[1]));
        features->f_standardize =
            (int *)G_realloc(features->f_standardize,
                             (2 + features->f_standardize[1]) * sizeof(int));
        for (i = 0; i < features->f_standardize[1]; i++) {
            line = (char *)strchr(line, '\t');
            line++;
            sscanf(line, "%d", &(features->f_standardize[i + 2]));
            features->f_standardize[i + 2] -= 1;
        }
    }

    line = GetLine(fp);
    line = GetLine(fp);
    features->f_mean = (int *)G_calloc(2, sizeof(int));
    sscanf(line, "%d", &(features->f_mean[0]));
    if (features->f_mean[0]) {
        line = (char *)strchr(line, '\t');
        line++;
        sscanf(line, "%d", &(features->f_mean[1]));
        features->f_mean = (int *)G_realloc(
            features->f_mean, (2 + features->f_mean[1]) * sizeof(int));
        for (i = 0; i < features->f_mean[1]; i++) {
            line = (char *)strchr(line, '\t');
            line++;
            sscanf(line, "%d", &(features->f_mean[i + 2]));
            features->f_mean[i + 2] -= 1;
        }
    }

    line = GetLine(fp);
    line = GetLine(fp);
    features->f_variance = (int *)G_calloc(2, sizeof(int));
    sscanf(line, "%d", &(features->f_variance[0]));
    if (features->f_variance[0]) {
        line = (char *)strchr(line, '\t');
        line++;
        sscanf(line, "%d", &(features->f_variance[1]));
        features->f_variance = (int *)G_realloc(
            features->f_variance, (2 + features->f_variance[1]) * sizeof(int));
        for (i = 0; i < features->f_variance[1]; i++) {
            line = (char *)strchr(line, '\t');
            line++;
            sscanf(line, "%d", &(features->f_variance[i + 2]));
            features->f_variance[i + 2] -= 1;
        }
    }

    line = GetLine(fp);
    line = GetLine(fp);
    features->f_pca = (int *)G_calloc(2, sizeof(int));
    sscanf(line, "%d", &(features->f_pca[0]));
    if (features->f_pca[0]) {
        line = (char *)strchr(line, '\t');
        line++;
        sscanf(line, "%d", &(features->f_pca[1]));
        features->f_pca = (int *)G_realloc(
            features->f_pca, (2 + features->f_pca[1]) * sizeof(int));
        for (i = 0; i < features->f_pca[1]; i++) {
            line = (char *)strchr(line, '\t');
            line++;
            sscanf(line, "%d", &(features->f_pca[i + 2]));
            features->f_pca[i + 2] -= 1;
        }
    }

    line = GetLine(fp);
    line = GetLine(fp);
    sscanf(line, "%d", &(features->nclasses));
    features->p_classes = (int *)G_calloc(features->nclasses, sizeof(int));
    line = GetLine(fp);
    line = GetLine(fp);
    for (i = 0; i < features->nclasses; i++) {
        sscanf(line, "%d", &(features->p_classes[i]));
        line = (char *)strchr(line, '\t');
        line++;
    }

    if (!features->f_standardize[0]) {
        line = GetLine(fp);
        line = GetLine(fp);
        line = GetLine(fp);
    }
    else {
        features->mean =
            (double *)G_calloc(features->f_standardize[1], sizeof(double));
        features->sd =
            (double *)G_calloc(features->f_standardize[1], sizeof(double));
        line = GetLine(fp);
        line = GetLine(fp);
        for (i = 0; i < features->f_standardize[1]; i++) {
            sscanf(line, "%lf", &(features->mean[i]));
            line = (char *)strchr(line, '\t');
            line++;
        }
        line = GetLine(fp);
        for (i = 0; i < features->f_standardize[1]; i++) {
            sscanf(line, "%lf", &(features->sd[i]));
            line = (char *)strchr(line, '\t');
            line++;
        }
    }

    line = GetLine(fp);
    line = GetLine(fp);
    sscanf(line, "%d%d", &(features->nexamples), &(features->examples_dim));
}
