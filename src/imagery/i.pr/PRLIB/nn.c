/*
   The following routines are written and tested by Stefano Merler

   for

   structure NearestNeighbor management
 */

#include <grass/gis.h>
#include "global.h"
#include <stdlib.h>
#include <string.h>

void compute_nn(NearestNeighbor *nn, int nsamples, int nvar, double **data,
                int *data_class)

/*
   Compute nn model, given a matrix of examples data of dimension
   nsamples x nvar. Classes of each example are contained in data_class.
 */
{
    int i, j;

    nn->nsamples = nsamples;
    nn->nvars = nvar;

    nn->data = (double **)G_calloc(nn->nsamples, sizeof(double *));
    for (i = 0; i < nn->nsamples; i++) {
        nn->data[i] = (double *)G_calloc(nn->nvars, sizeof(double));
    }
    nn->class = (int *)G_calloc(nn->nsamples, sizeof(int));

    for (i = 0; i < nn->nsamples; i++) {
        for (j = 0; j < nn->nvars; j++) {
            nn->data[i][j] = data[i][j];
        }
        nn->class[i] = data_class[i];
    }
}

void write_nn(char *file, NearestNeighbor *nn, Features *features)

/*
   write nn structure to a file
 */
{
    FILE *fpout;
    int i, j;
    char tempbuf[500];

    fpout = fopen(file, "w");
    if (fpout == NULL) {
        sprintf(tempbuf, "write_nn-> Can't open file <%s> for writing", file);
        G_fatal_error(tempbuf);
    }

    write_header_features(fpout, features);
    fprintf(fpout, "#####################\n");
    fprintf(fpout, "MODEL:\n");
    fprintf(fpout, "#####################\n");

    fprintf(fpout, "Model:\n");
    fprintf(fpout, "NearestNeighbor\n");
    fprintf(fpout, "k:\n");
    fprintf(fpout, "%d\n", nn->k);
    fprintf(fpout, "number of samples:\n");
    fprintf(fpout, "%d\n", nn->nsamples);

    fprintf(fpout, "number of variables:\n");
    fprintf(fpout, "%d\n", nn->nvars);

    for (i = 0; i < nn->nsamples; i++) {
        for (j = 0; j < nn->nvars; j++) {
            fprintf(fpout, "%f\t", nn->data[i][j]);
        }
        fprintf(fpout, "%d\n", nn->class[i]);
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

int predict_nn_multiclass(NearestNeighbor *nn, double *x, int k, int nclasses,
                          int *classes)

/*
   multiclass problems: given a nn model, return the predicted class of a test
   point x using k-nearest neighbor for the prediction. the array classes (of
   length nclasses) shall contain all the possible classes to be predicted
 */
{
    int i, j;
    double *dist;
    int *pres_class, *pred_class, *index;
    int max_class;
    int max;

    dist = (double *)G_calloc(nn->nsamples, sizeof(double));
    index = (int *)G_calloc(nn->nsamples, sizeof(int));
    pred_class = (int *)G_calloc(k, sizeof(int));
    pres_class = (int *)G_calloc(nclasses, sizeof(int));

    for (i = 0; i < nn->nsamples; i++) {
        dist[i] = squared_distance(x, nn->data[i], nn->nvars);
    }

    indexx_1(nn->nsamples, dist, index);

    for (i = 0; i < k; i++) {
        pred_class[i] = nn->class[index[i]];
    }

    for (j = 0; j < k; j++) {
        for (i = 0; i < nclasses; i++) {
            if (pred_class[j] == classes[i]) {
                pres_class[i] += 1;
                break;
            }
        }
    }

    max = 0;
    max_class = 0;
    for (i = 0; i < nclasses; i++) {
        if (pres_class[i] > max) {
            max = pres_class[i];
            max_class = i;
        }
    }

    G_free(dist);
    G_free(index);
    G_free(pred_class);
    G_free(pres_class);

    return classes[max_class];
}

double predict_nn_2class(NearestNeighbor *nn, double *x, int k, int nclasses,
                         int *classes)

/*
   2 class problems: given a nn model, return the majority of the class (with
   sign) of a test point x using k-nearest neighbor for the prediction. the
   array classes (of length nclasses)  shall contain all the possible classes to
   be predicted
 */
{
    int i, j;
    double *dist;
    int *pres_class, *pred_class, *index;

    dist = (double *)G_calloc(nn->nsamples, sizeof(double));
    index = (int *)G_calloc(nn->nsamples, sizeof(int));
    pred_class = (int *)G_calloc(k, sizeof(int));
    pres_class = (int *)G_calloc(nclasses, sizeof(int));

    for (i = 0; i < nn->nsamples; i++) {
        dist[i] = squared_distance(x, nn->data[i], nn->nvars);
    }

    indexx_1(nn->nsamples, dist, index);

    for (i = 0; i < k; i++) {
        pred_class[i] = nn->class[index[i]];
    }

    for (j = 0; j < k; j++) {
        for (i = 0; i < nclasses; i++) {
            if (pred_class[j] == classes[i]) {
                pres_class[i] += 1;
                break;
            }
        }
    }

    G_free(dist);
    G_free(index);
    G_free(pred_class);

    if (pres_class[0] > pres_class[1]) {
        return (double)pres_class[0] / (double)(k * classes[0]);
    }
    else {
        return (double)pres_class[1] / (double)(k * classes[1]);
    }
}

void test_nn(NearestNeighbor *nn, Features *features, int k, char *file)

/*
   test nn model on a set of data (features) using k-nearest neighbor
   and write the results into a file. To standard output accuracy
   and error on each class
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
        sprintf(tempbuf, "test_nn-> Can't open file %s for writing", file);
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
                    if ((predD = predict_nn_2class(nn, features->value[i], k,
                                                   features->nclasses,
                                                   features->p_classes)) *
                            features->class[i] <=
                        0) {
                        error[j] += 1.0;
                        accuracy += 1.0;
                    }
                    fprintf(fp, "%d\t%f\n", features->class[i], predD);
                }
                else {
                    if ((predI = predict_nn_multiclass(
                             nn, features->value[i], k, features->nclasses,
                             features->p_classes)) != features->class[i]) {
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
