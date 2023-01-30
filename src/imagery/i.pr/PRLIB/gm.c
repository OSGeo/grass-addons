/*
   The following routines are written and tested by Stefano Merler

   for

   structure GaussianMixture management
 */

#include <grass/gis.h>
#include "global.h"
#include <stdlib.h>
#include <string.h>
#include <math.h>

static void compute_covar();
static void compute_mean();

void compute_gm(GaussianMixture *gm, int nsamples, int nvar, double **data,
                int *data_class, int nclasses, int *classes)

/*
   Compute gm model, given a matrix of examples data of dimension
   nsamples x nvar. Classes of each example are contained in data_class.
   the array classes (of length nclasses) shall contain all the possible
   classes of the array data_class
 */
{
    double ***tmpMat;
    int *index2;
    int i, j, k;

    gm->classes = classes;
    gm->nclasses = nclasses;

    gm->npoints_for_class = (int *)G_calloc(gm->nclasses, sizeof(int));
    for (i = 0; i < nsamples; i++) {
        for (j = 0; j < gm->nclasses; j++) {
            if (data_class[i] == gm->classes[j]) {
                gm->npoints_for_class[j] += 1;
            }
        }
    }

    gm->nvars = nvar;
    gm->priors = (double *)G_calloc(gm->nclasses, sizeof(double));
    gm->mean = (double **)G_calloc(gm->nclasses, sizeof(double *));
    for (i = 0; i < gm->nclasses; i++)
        gm->mean[i] = (double *)G_calloc(gm->nvars, sizeof(double));
    gm->det = (double *)G_calloc(gm->nclasses, sizeof(double));
    gm->covar = (double ***)G_calloc(gm->nclasses, sizeof(double **));
    for (i = 0; i < gm->nclasses; i++) {
        gm->covar[i] = (double **)G_calloc(gm->nvars, sizeof(double *));
        for (j = 0; j < gm->nvars; j++)
            gm->covar[i][j] = (double *)G_calloc(gm->nvars, sizeof(double));
    }
    tmpMat = (double ***)G_calloc(gm->nclasses, sizeof(double **));
    for (i = 0; i < gm->nclasses; i++) {
        tmpMat[i] =
            (double **)G_calloc(gm->npoints_for_class[i], sizeof(double *));
        for (j = 0; j < gm->npoints_for_class[i]; j++)
            tmpMat[i][j] = (double *)G_calloc(gm->nvars, sizeof(double));
    }

    index2 = (int *)G_calloc(gm->nclasses, sizeof(int));
    for (i = 0; i < nsamples; i++)
        for (j = 0; j < gm->nclasses; j++)
            if (data_class[i] == gm->classes[j]) {
                for (k = 0; k < gm->nvars; k++)
                    tmpMat[j][index2[j]][k] = data[i][k];
                index2[j] += 1;
            }

    for (i = 0; i < gm->nclasses; i++)
        compute_mean(tmpMat, gm, i);

    for (i = 0; i < gm->nclasses; i++)
        compute_covar(tmpMat, gm, i);

    for (i = 0; i < gm->nclasses; i++)
        gm->priors[i] = (double)gm->npoints_for_class[i] / (double)nsamples;

    for (i = 0; i < gm->nclasses; i++)
        for (j = 0; j < gm->npoints_for_class[i]; j++)
            G_free(tmpMat[i][j]);
    G_free(tmpMat);
    G_free(index2);
}

static void compute_covar(double ***mat, GaussianMixture *gm, int class)

/*
   compute covariance matrix of all the classes
 */
{
    int i, j, k;

    for (i = 0; i < gm->nvars; i++)
        for (j = i; j < gm->nvars; j++) {
            for (k = 0; k < gm->npoints_for_class[class]; k++) {
                gm->covar[class][i][j] +=
                    (mat[class][k][i] - gm->mean[class][i]) *
                    (mat[class][k][j] - gm->mean[class][j]);
            }
            gm->covar[class][j][i] = gm->covar[class][i][j];
        }
    for (i = 0; i < gm->nvars; i++)
        for (j = 0; j < gm->nvars; j++)
            gm->covar[class][i][j] /=
                ((double)gm->npoints_for_class[class] - 1.);
}

static void compute_mean(double ***mat, GaussianMixture *gm, int class)

/*
   compute the mean of each variable for all the classes
 */
{
    int i, j;

    for (i = 0; i < gm->nvars; i++)
        for (j = 0; j < gm->npoints_for_class[class]; j++)
            gm->mean[class][i] += mat[class][j][i];

    for (i = 0; i < gm->nvars; i++)
        gm->mean[class][i] /= gm->npoints_for_class[class];
}

void write_gm(char *file, GaussianMixture *gm, Features *features)

/*
   write gm structure to a file
 */
{
    FILE *fpout;
    int i, j, k;
    char tempbuf[500];

    fpout = fopen(file, "w");
    if (fpout == NULL) {
        sprintf(tempbuf, "write_gm-> Can't open file %s for writing", file);
        G_fatal_error(tempbuf);
    }

    write_header_features(fpout, features);
    fprintf(fpout, "#####################\n");
    fprintf(fpout, "MODEL:\n");
    fprintf(fpout, "#####################\n");

    fprintf(fpout, "Model:\n");
    fprintf(fpout, "GaussianMixture\n");
    fprintf(fpout, "nclasses:\n");
    fprintf(fpout, "%d\n", gm->nclasses);

    fprintf(fpout, "nvars:\n");
    fprintf(fpout, "%d\n", gm->nvars);

    fprintf(fpout, "classes:\n");
    fprintf(fpout, "%d", gm->classes[0]);
    for (i = 1; i < gm->nclasses; i++)
        fprintf(fpout, "\t%d", gm->classes[i]);
    fprintf(fpout, "\n");

    fprintf(fpout, "priors:\n");
    fprintf(fpout, "%f", gm->priors[0]);
    for (i = 1; i < gm->nclasses; i++)
        fprintf(fpout, "\t%f", gm->priors[i]);
    fprintf(fpout, "\n");

    for (i = 0; i < gm->nclasses; i++) {
        fprintf(fpout, "CLASS %d:\n", gm->classes[i]);
        fprintf(fpout, "mean:\n");
        fprintf(fpout, "%f", gm->mean[i][0]);
        for (j = 1; j < gm->nvars; j++)
            fprintf(fpout, "\t%f", gm->mean[i][j]);
        fprintf(fpout, "\n");
        fprintf(fpout, "covar:\n");
        for (j = 0; j < gm->nvars; j++) {
            fprintf(fpout, "%f", gm->covar[i][j][0]);
            for (k = 1; k < gm->nvars; k++)
                fprintf(fpout, "\t%f", gm->covar[i][j][k]);
            fprintf(fpout, "\n");
        }
    }

    if (features->f_pca[0]) {
        fprintf(fpout, "#####################\n");
        fprintf(fpout, "PRINC. COMP.:\n");
        fprintf(fpout, "#####################\n");

        fprintf(fpout, "Number of pc:\n");
        fprintf(fpout, "%d\n", features->npc);

        for (i = 0; i < features->f_pca[1]; i++) {
            fprintf(fpout, "PCA: Layer %d\n", i + 1);
            write_pca(fpout, &(features->pca[i]));
        }
    }

    fclose(fpout);
}

void test_gm(GaussianMixture *gm, Features *features, char *file)

/*
   test gm model on a set of data (features) and write the results
   into a file. To standard output accuracy and error on each class
 */
{
    int i, j;
    int *data_in_each_class;
    FILE *fp;
    char tempbuf[500];
    int predI;
    double predD;
    double *error;
    double accuracy;

    fp = fopen(file, "w");
    if (fp == NULL) {
        sprintf(tempbuf, "test_gm-> Can't open file %s for writing", file);
        G_fatal_error(tempbuf);
    }

    data_in_each_class = (int *)G_calloc(features->nclasses, sizeof(int));
    error = (double *)G_calloc(features->nclasses, sizeof(double));

    accuracy = 0.0;
    for (i = 0; i < features->nexamples; i++) {
        for (j = 0; j < features->nclasses; j++) {
            if (features->class[i] == features->p_classes[j]) {
                data_in_each_class[j] += 1;
                if (features->nclasses == 2) {
                    if ((predD = predict_gm_2class(gm, features->value[i])) *
                            features->class[i] <=
                        0) {
                        error[j] += 1.0;
                        accuracy += 1.0;
                    }
                    fprintf(fp, "%d\t%f\n", features->class[i], predD);
                }
                else {
                    if ((predI = predict_gm_multiclass(
                             gm, features->value[i])) != features->class[i]) {
                        error[j] += 1.0;
                        accuracy += 1.0;
                    }
                    fprintf(fp, "%d\t%d\n", features->class[i], predI);
                }
                break;
            }
        }
    }

    accuracy /= features->nexamples;
    accuracy = 1.0 - accuracy;

    fclose(fp);

    fprintf(stdout, "Accuracy: %f\n", accuracy);
    fprintf(stdout, "Class\t%d", features->p_classes[0]);
    for (j = 1; j < features->nclasses; j++) {
        fprintf(stdout, "\t%d", features->p_classes[j]);
    }
    fprintf(stdout, "\n");
    fprintf(stdout, "Ndata\t%d", data_in_each_class[0]);
    for (j = 1; j < features->nclasses; j++) {
        fprintf(stdout, "\t%d", data_in_each_class[j]);
    }
    fprintf(stdout, "\n");
    fprintf(stdout, "Nerrors\t%d", (int)error[0]);
    for (j = 1; j < features->nclasses; j++) {
        fprintf(stdout, "\t%d", (int)error[j]);
    }
    fprintf(stdout, "\n");

    for (j = 0; j < features->nclasses; j++) {
        error[j] /= data_in_each_class[j];
    }

    fprintf(stdout, "Perrors\t%f", error[0]);
    for (j = 1; j < features->nclasses; j++) {
        fprintf(stdout, "\t%f", error[j]);
    }
    fprintf(stdout, "\n");
    G_free(data_in_each_class);
    G_free(error);
}

void compute_test_gm(GaussianMixture *gm)

/*
   compute inverse and determinant of each covariance matrix of a gm model
 */
{
    int i, j;

    gm->det = (double *)G_calloc(gm->nclasses, sizeof(double));
    gm->inv_covar = (double ***)G_calloc(gm->nclasses, sizeof(double **));
    for (i = 0; i < gm->nclasses; i++) {
        gm->inv_covar[i] = (double **)G_calloc(gm->nvars, sizeof(double *));
        for (j = 0; j < gm->nvars; j++)
            gm->inv_covar[i][j] = (double *)G_calloc(gm->nvars, sizeof(double));
    }

    for (j = 0; j < gm->nclasses; j++) {
        gm->det[j] = determinant_of_double_matrix(gm->covar[j], gm->nvars);
        inverse_of_double_matrix(gm->covar[j], gm->inv_covar[j], gm->nvars);
    }
}

int predict_gm_multiclass(GaussianMixture *gm, double *x)

/*
   multiclass problems: given a gm model, return the predicted class
   of a test point x
 */
{
    int i, j, c;
    double *tmpVect;
    double *distmean;
    double *posteriors;
    double delta;
    double max_posterior;
    int max_posterior_index;
    char tempbuf[500];

    tmpVect = (double *)G_calloc(gm->nvars, sizeof(double));
    distmean = (double *)G_calloc(gm->nvars, sizeof(double));
    posteriors = (double *)G_calloc(gm->nclasses, sizeof(double));

    for (c = 0; c < gm->nclasses; c++) {
        for (i = 0; i < gm->nvars; i++)
            distmean[i] = x[i] - gm->mean[c][i];

        for (i = 0; i < gm->nvars; i++)
            tmpVect[i] = 0.0;

        for (i = 0; i < gm->nvars; i++)
            for (j = 0; j < gm->nvars; j++)
                tmpVect[i] += distmean[j] * gm->inv_covar[c][j][i];

        delta = 0.0;
        for (i = 0; i < gm->nvars; i++)
            delta += tmpVect[i] * distmean[i];

        if (gm->det[c] > 0.0) {
            posteriors[c] = exp(-0.5 * delta) / sqrt(gm->det[c]);
        }
        else {
            sprintf(
                tempbuf,
                "predict_gm_multiclass-> det. of cov. matrix of class %d = 0",
                c);
            G_fatal_error(tempbuf);
        }
        posteriors[c] = posteriors[c] * gm->priors[c];
    }

    max_posterior = 0.0;
    max_posterior_index = 0;
    for (c = 0; c < gm->nclasses; c++)
        if (posteriors[c] > max_posterior) {
            max_posterior = posteriors[c];
            max_posterior_index = c;
        }

    G_free(tmpVect);
    G_free(distmean);
    G_free(posteriors);

    return gm->classes[max_posterior_index];
}

double predict_gm_2class(GaussianMixture *gm, double *x)

/*
   2 class problems: given a gm model , return the posterior of class (with
   sign) for a test point x
 */
{
    int i, j, c;
    double *tmpVect;
    double *distmean;
    double *posteriors;
    double delta;
    char tempbuf[500];

    tmpVect = (double *)G_calloc(gm->nvars, sizeof(double));
    distmean = (double *)G_calloc(gm->nvars, sizeof(double));
    posteriors = (double *)G_calloc(gm->nclasses, sizeof(double));

    for (c = 0; c < gm->nclasses; c++) {
        for (i = 0; i < gm->nvars; i++)
            distmean[i] = x[i] - gm->mean[c][i];

        for (i = 0; i < gm->nvars; i++)
            tmpVect[i] = 0.0;

        for (i = 0; i < gm->nvars; i++)
            for (j = 0; j < gm->nvars; j++)
                tmpVect[i] += distmean[j] * gm->inv_covar[c][j][i];

        delta = 0.0;
        for (i = 0; i < gm->nvars; i++)
            delta += tmpVect[i] * distmean[i];

        if (gm->det[c] > 0.0) {
            posteriors[c] = exp(-0.5 * delta) / sqrt(gm->det[c]);
        }
        else {
            sprintf(tempbuf,
                    "predict_gm_2class-> det. of cov. matrix of class %d = 0",
                    c);
            G_fatal_error(tempbuf);
        }
        posteriors[c] = posteriors[c] * gm->priors[c];
    }

    G_free(tmpVect);
    G_free(distmean);

    if (posteriors[0] > posteriors[1]) {
        return posteriors[0] / (posteriors[0] + posteriors[1]) * gm->classes[0];
    }
    else {
        return posteriors[1] / (posteriors[0] + posteriors[1]) * gm->classes[1];
    }
}
