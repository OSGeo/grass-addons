/*
   The following routines are written and tested by Stefano Merler

   and Maria Serafini

   for

   Features Selction with SVM
 */

#include <grass/gis.h>
#include "global.h"
#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <math.h>

void compute_valoriDJ(svm, features, H_tot, H_tmp,
                      valoriDJ) SupportVectorMachine *svm;
Features *features;
double **H_tot, **H_tmp, **valoriDJ;
{
    double diag, resto;
    int i, j, t;
    double DJ;

    (*valoriDJ) = (double *)G_calloc(svm->d, sizeof(double));

    diag = 0;
    resto = 0;

    for (i = 0; i < features->nexamples; i++) {
        if (svm->alph[i] != 0) {
            diag = diag + svm->alph[i] * svm->alph[i] * H_tot[i][i];
            for (j = i + 1; j < features->nexamples; j++) {
                if (svm->alph[j] != 0) {
                    resto = resto + svm->alph[i] * svm->alph[j] * H_tot[i][j];
                }
            }
        }
    }

    DJ = 0.5 * diag + resto;

    for (i = 0; i < svm->d; i++) {
        compute_H_perdiff(H_tot, H_tmp, features->value, features->nexamples,
                          svm->two_sigma_squared, i);

        (*valoriDJ)[i] = 0;

        diag = 0;
        resto = 0;

        for (t = 0; t < features->nexamples; t++) {
            if (svm->alph[t] != 0) {
                diag = diag + svm->alph[t] * svm->alph[t] * H_tmp[t][t];
                for (j = t + 1; j < features->nexamples; j++) {
                    if (svm->alph[j] != 0) {
                        resto =
                            resto + svm->alph[t] * svm->alph[j] * H_tmp[t][j];
                    }
                }
            }
        }

        (*valoriDJ)[i] = 0.5 * diag + resto;

        (*valoriDJ)[i] = DJ - (*valoriDJ)[i];
    }
}

void free_svm(svm) SupportVectorMachine *svm;
{
    int j;

    for (j = 0; j < svm->N; j++) {
        G_free(svm->dense_points[j]);
    }
    G_free(svm->target);
    G_free(svm->Cw);
    G_free(svm->alph);
    G_free(svm->w);
    G_free(svm->error_cache);
    G_free(svm->precomputed_self_dot_product);
}

void e_rfe_lin(svm, features, names, selected, i, rimanenti, fp_fs_w,
               fp_fs_stats) SupportVectorMachine *svm;
Features *features;
int *names, *selected;
int i;
int *rimanenti;
FILE *fp_fs_w, *fp_fs_stats;
{
    double *wsquare;
    int j;
    int *h;
    int nbin;
    double *pi;
    double entro;
    double maxentro, media;
    int nel;
    int *eliminati;
    double *valoriDJ;
    int index;
    double lim;
    double *wlog;
    int minorimedia;
    double mediamod;
    int conv;
    int *sortindex, *indexordinati;
    int k, t;

    wsquare = (double *)G_calloc(*rimanenti, sizeof(double));

    for (j = 0; j < *rimanenti; j++) {
        wsquare[j] = svm->w[j] * svm->w[j];
    }

    if (fp_fs_w != NULL) {
        fprintf(fp_fs_w, "%6.10f", wsquare[0]);
        for (j = 1; j < *rimanenti; j++) {
            fprintf(fp_fs_w, "\t%f", wsquare[j]);
        }
        fprintf(fp_fs_w, "\n");
    }

    nbin = (int)floor(sqrt(*rimanenti));
    traslo(wsquare, *rimanenti);
    h = (int *)G_calloc(nbin, sizeof(int));
    histo1(wsquare, *rimanenti, h, nbin);
    pi = (double *)G_calloc(nbin, sizeof(double));
    for (j = 0; j < nbin; j++) {
        pi[j] = (double)h[j] / (*rimanenti);
    }
    entro = Entropy(pi, nbin, 0.000001);

    if (entro < 0.0) {
        fprintf(stderr, "problemi con l'entropia \n");
        exit(0);
    }

    maxentro = log(nbin) / log(2);

    media = 0.0;
    for (j = 0; j < *rimanenti; j++) {
        media += wsquare[j];
    }
    media /= *rimanenti;

    if (entro > 0.5 * maxentro && media > 0.2) {

        nel = h[0];

        if (fp_fs_stats != NULL)
            fprintf(fp_fs_stats, "%d\tunif\t%f\t%f\t%d\n", *rimanenti, entro,
                    maxentro, nel);

        eliminati = (int *)G_calloc(nel, sizeof(int));
        valoriDJ = (double *)G_calloc(nel, sizeof(double));

        index = 0;

        lim = (double)1 / nbin;

        for (j = 0; j < *rimanenti; j++) {
            if (wsquare[j] <= lim) {
                eliminati[index] = j;
                valoriDJ[index] = wsquare[j];
                index += 1;
            }
        }
    }
    else {

        wlog = (double *)G_calloc(*rimanenti, sizeof(double));

        for (j = 0; j < *rimanenti; j++) {
            wlog[j] = log(wsquare[j] + 1.0);
        }

        media = 0.0;

        for (j = 0; j < *rimanenti; j++) {
            media += wlog[j];
        }

        media /= *rimanenti;

        minorimedia = 0;

        for (j = 0; j < *rimanenti; j++) {
            if (wlog[j] < media) {
                minorimedia += 1;
            }
        }

        mediamod = media;

        conv = 0;

        while (conv == 0) {
            nel = 0;
            mediamod = 0.5 * mediamod;

            for (j = 0; j < *rimanenti; j++) {
                if (wlog[j] < mediamod) {
                    nel += 1;
                }
            }

            if (nel <= 0.5 * minorimedia && nel != 0) {
                conv = 1;

                eliminati = (int *)G_calloc(nel, sizeof(int));
                valoriDJ = (double *)G_calloc(nel, sizeof(double));

                index = 0;

                for (j = 0; j < *rimanenti; j++) {
                    if (wlog[j] < mediamod) {
                        eliminati[index] = j;
                        valoriDJ[index] = wlog[j];
                        index += 1;
                    }
                }
            }
        }

        if (fp_fs_stats != NULL)
            fprintf(fp_fs_stats, "%d\tnon-unif\t%f\t%f\t%d\n", *rimanenti,
                    entro, maxentro, nel);

        G_free(wlog);
    }

    sortindex = (int *)G_calloc(nel, sizeof(int));

    indexx_1(nel, valoriDJ, sortindex);

    indexordinati = (int *)G_calloc(nel, sizeof(int));

    for (j = 0; j < nel; j++) {
        indexordinati[j] = eliminati[sortindex[j]];
    }

    for (j = 0; j < nel; j++) {
        selected[*rimanenti - j - 1] = names[indexordinati[j]];
    }

    for (j = 0; j < nel; j++) {
        for (k = eliminati[j]; k < (*rimanenti - 1); k++) {
            for (t = 0; t < features->nexamples; t++) {
                features->value[t][k] = features->value[t][k + 1];
            }
            names[k] = names[k + 1];
        }
        for (k = j + 1; k < nel; k++) {
            eliminati[k]--;
        }
        (*rimanenti)--;
    }

    G_free(sortindex);
    G_free(indexordinati);
    G_free(pi);
    G_free(h);
    G_free(eliminati);
    G_free(valoriDJ);
    G_free(wsquare);
}

void e_rfe_gauss(valoriDJ, features, names, selected, i, H_tot, H_tmp,
                 rimanenti, svm_kp, fp_fs_w, fp_fs_stats) double *valoriDJ;
Features *features;
double **H_tot, **H_tmp;
int *names, *selected;
int i;
int *rimanenti;
double svm_kp;
FILE *fp_fs_w, *fp_fs_stats;
{
    int j;
    int *h;
    int nbin;
    double *pi;
    double entro;
    double maxentro, media;
    int nel;
    int *eliminati;
    double *valorieliminati;
    int index;
    double lim;
    double *wlog;
    int minorimedia;
    double mediamod;
    int conv;
    int *sortindex, *indexordinati;
    int k, t;

    if (fp_fs_w != NULL) {
        fprintf(fp_fs_w, "%6.10f", valoriDJ[0]);
        for (j = 1; j < *rimanenti; j++) {
            fprintf(fp_fs_w, "\t%6.10f", valoriDJ[j]);
        }
        fprintf(fp_fs_w, "\n");
    }

    nbin = (int)floor(sqrt(*rimanenti));
    traslo(valoriDJ, *rimanenti);
    h = (int *)G_calloc(nbin, sizeof(int));
    histo1(valoriDJ, *rimanenti, h, nbin);
    pi = (double *)G_calloc(nbin, sizeof(double));
    for (j = 0; j < nbin; j++) {
        pi[j] = (double)h[j] / (*rimanenti);
    }
    entro = Entropy(pi, nbin, 0.000001);

    if (entro < 0.0) {
        fprintf(stderr, "problemi con l'entropia \n");
        exit(0);
    }

    maxentro = log(nbin) / log(2);
    media = 0.0;
    for (j = 0; j < *rimanenti; j++) {
        media += valoriDJ[j];
    }
    media /= *rimanenti;

    if (entro > 0.5 * maxentro && media > 0.2) {

        nel = h[0];

        if (fp_fs_stats != NULL)
            fprintf(fp_fs_stats, "%d\tunif\t%f\t%f\t%d\n", *rimanenti, entro,
                    maxentro, nel);

        eliminati = (int *)G_calloc(nel, sizeof(int));
        valorieliminati = (double *)G_calloc(nel, sizeof(double));

        index = 0;

        lim = (double)1 / nbin;

        for (j = 0; j < *rimanenti; j++) {
            if (valoriDJ[j] <= lim) {
                eliminati[index] = j;
                valorieliminati[index] = valoriDJ[j];
                index += 1;
            }
        }
    }
    else {

        wlog = (double *)G_calloc(*rimanenti, sizeof(double));

        for (j = 0; j < *rimanenti; j++) {
            wlog[j] = log(valoriDJ[j] + 1.0);
        }

        media = 0.0;

        for (j = 0; j < *rimanenti; j++) {
            media += wlog[j];
        }

        media /= *rimanenti;

        minorimedia = 0;

        for (j = 0; j < *rimanenti; j++) {
            if (wlog[j] < media) {
                minorimedia += 1;
            }
        }

        mediamod = media;

        conv = 0;

        while (conv == 0) {
            nel = 0;
            mediamod = 0.5 * mediamod;

            for (j = 0; j < *rimanenti; j++) {
                if (wlog[j] < mediamod) {
                    nel += 1;
                }
            }

            if (nel <= 0.5 * minorimedia && nel != 0) {
                conv = 1;

                eliminati = (int *)G_calloc(nel, sizeof(int));
                valorieliminati = (double *)G_calloc(nel, sizeof(double));

                index = 0;

                for (j = 0; j < *rimanenti; j++) {
                    if (wlog[j] < mediamod) {
                        eliminati[index] = j;
                        valorieliminati[index] = wlog[j];
                        index += 1;
                    }
                }
            }
        }

        if (fp_fs_stats != NULL)
            fprintf(fp_fs_stats, "%d\tnon-unif\t%f\t%f\t%d\n", *rimanenti,
                    entro, maxentro, nel);

        G_free(wlog);
    }

    sortindex = (int *)G_calloc(nel, sizeof(int));

    indexx_1(nel, valorieliminati, sortindex);

    indexordinati = (int *)G_calloc(nel, sizeof(int));

    for (j = 0; j < nel; j++) {
        indexordinati[j] = eliminati[sortindex[j]];
    }

    for (j = 0; j < nel; j++) {
        selected[*rimanenti - j - 1] = names[indexordinati[j]];
    }

    for (k = 0; k < nel; k++) {

        compute_H_perdiff(H_tot, H_tmp, features->value, features->nexamples,
                          svm_kp, eliminati[k]);

        for (j = 0; j < features->nexamples; j++) {
            for (t = 0; t < features->nexamples; t++) {
                H_tot[j][t] = H_tmp[j][t];
            }
        }
    }

    for (j = 0; j < nel; j++) {
        for (k = eliminati[j]; k < (*rimanenti - 1); k++) {
            for (t = 0; t < features->nexamples; t++) {
                features->value[t][k] = features->value[t][k + 1];
            }
            names[k] = names[k + 1];
        }
        for (k = j + 1; k < nel; k++) {
            eliminati[k]--;
        }
        (*rimanenti)--;
    }

    G_free(sortindex);
    G_free(indexordinati);
    G_free(pi);
    G_free(h);
    G_free(eliminati);
    G_free(valorieliminati);
}

void one_rfe_lin(svm, names, selected, fp_fs_w) SupportVectorMachine *svm;
int *names, *selected;
FILE *fp_fs_w;
{
    double *wsquare;
    int i, j;
    int *sortindex;

    wsquare = (double *)G_calloc(svm->d, sizeof(double));
    sortindex = (int *)G_calloc(svm->d, sizeof(int));

    for (j = 0; j < svm->d; j++) {
        wsquare[j] = svm->w[j] * svm->w[j];
    }

    if (fp_fs_w != NULL) {
        fprintf(fp_fs_w, "%6.10f", wsquare[0]);
        for (j = 1; j < svm->d; j++) {
            fprintf(fp_fs_w, "\t%6.10f", wsquare[j]);
        }
        fprintf(fp_fs_w, "\n");
    }

    indexx_1(svm->d, wsquare, sortindex);

    for (i = 0; i < svm->d; i++) {
        selected[svm->d - i - 1] = names[sortindex[i]];
    }

    G_free(wsquare);
    G_free(sortindex);
}

void one_rfe_gauss(valoriDJ, names, selected, n, fp_fs_w) double *valoriDJ;
int *names, *selected;
int n;
FILE *fp_fs_w;
{
    int i, j;
    int *sortindex;

    if (fp_fs_w != NULL) {
        fprintf(fp_fs_w, "%6.10f", valoriDJ[0]);
        for (j = 1; j < n; j++) {
            fprintf(fp_fs_w, "\t%6.10f", valoriDJ[j]);
        }
        fprintf(fp_fs_w, "\n");
    }

    sortindex = (int *)G_calloc(n, sizeof(int));

    indexx_1(n, valoriDJ, sortindex);

    for (i = 0; i < n; i++) {
        selected[n - i - 1] = names[sortindex[i]];
    }

    G_free(sortindex);
}

void rfe_lin(svm, features, names, selected, i,
             fp_fs_w) SupportVectorMachine *svm;
Features *features;
int *names, *selected;
int i;
FILE *fp_fs_w;
{
    double *wsquare;
    double wmin;
    int wmin_index;
    int j, t;

    wsquare = (double *)G_calloc(svm->d, sizeof(double));

    for (j = 0; j < svm->d; j++) {
        wsquare[j] = svm->w[j] * svm->w[j];
    }

    if (fp_fs_w != NULL) {
        fprintf(fp_fs_w, "%6.10f", wsquare[0]);
        for (j = 1; j < svm->d; j++) {
            fprintf(fp_fs_w, "\t%6.10f", wsquare[j]);
        }
        fprintf(fp_fs_w, "\n");
    }

    wmin = wsquare[0];
    wmin_index = 0;

    for (j = 1; j < svm->d; j++) {
        if (wmin > wsquare[j]) {
            wmin = wsquare[j];
            wmin_index = j;
        }
    }

    selected[features->examples_dim - i - 1] = names[wmin_index];

    for (j = wmin_index; j < features->examples_dim; j++) {
        for (t = 0; t < features->nexamples; t++) {
            features->value[t][j] = features->value[t][j + 1];
        }
        names[j] = names[j + 1];
    }
    G_free(wsquare);
}

void rfe_gauss(valoriDJ, features, names, selected, i, H_tot, H_tmp, svm_kp,
               fp_fs_w) Features *features;
double *valoriDJ;
int *names, *selected;
double **H_tot, **H_tmp;
int i;
double svm_kp;
FILE *fp_fs_w;
{
    double wmin;
    int wmin_index;
    int j, t;

    if (fp_fs_w != NULL) {
        fprintf(fp_fs_w, "%6.10f", valoriDJ[0]);
        for (j = 1; j < features->examples_dim - i; j++) {
            fprintf(fp_fs_w, "\t%6.10f", valoriDJ[j]);
        }
        fprintf(fp_fs_w, "\n");
    }

    wmin = valoriDJ[0];
    wmin_index = 0;

    for (j = 1; j < features->examples_dim - i; j++) {
        if (wmin > valoriDJ[j]) {
            wmin = valoriDJ[j];
            wmin_index = j;
        }
    }

    selected[features->examples_dim - i - 1] = names[wmin_index];

    compute_H_perdiff(H_tot, H_tmp, features->value, features->nexamples,
                      svm_kp, wmin_index);

    for (j = 0; j < features->nexamples; j++) {
        for (t = 0; t < features->nexamples; t++) {
            H_tot[j][t] = H_tmp[j][t];
        }
    }

    for (j = wmin_index; j < features->examples_dim - i - 1; j++) {
        for (t = 0; t < features->nexamples; t++) {
            features->value[t][j] = features->value[t][j + 1];
        }
        names[j] = names[j + 1];
    }
}

void compute_H(matrix, XX, y, ndati, nfeat, sigma) double **matrix, **XX;
int *y;
double sigma;
int ndati, nfeat;
{
    int r, s;

    for (r = 0; r < ndati; r++) {
        for (s = r; s < ndati; s++) {
            matrix[r][s] = y[r] * y[s] *
                           squared_gaussian_kernel(XX[r], XX[s], nfeat, sigma);
            matrix[s][r] = matrix[r][s];
        }
    }
}

void compute_H_perdiff(Hvecchia, Hnuova, XX, ndati, sigma,
                       featdaelim) double **Hvecchia,
    **Hnuova, **XX;
double sigma;
int ndati, featdaelim;

// featdaelim e' la variabile numerata come numera C (0...nfeat-1)
{
    int r, s;

    for (r = 0; r < ndati; r++) {
        for (s = r; s < ndati; s++) {
            Hnuova[r][s] =
                Hvecchia[r][s] *
                (exp((XX[r][featdaelim] - XX[s][featdaelim]) *
                     (XX[r][featdaelim] - XX[s][featdaelim]) / sigma));
            Hnuova[s][r] = Hnuova[r][s];
        }
    }
}

void traslo(x, n) double *x;
int n;
{
    int j;
    double m, M;

    m = min(x, n);
    M = max(x, n);
    if (m == M) {
        fprintf(stdout, "i pesi sono tutti uguali e non e' possibile fare "
                        "feature selection \n");
        exit(0);
    }
    for (j = 0; j < n; j++) {
        x[j] = (x[j] - m) / (M - m);
    }
}
