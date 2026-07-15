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
#include <grass/glocale.h>
#include "global.h"
#include <grass/raster.h>
/*#include "edit.h" */
#include "localproto.h"

#define TINY      1.0e-20
#define MAXLIMITS 10000

void pearsn();
double erfcc();

int main(int argc, char *argv[])
{
    struct GModule *module;
    struct Option *opt1;
    struct Option *opt2;
    struct Option *opt3;
    struct Option *opt4;
    Features features;
    char tempbuf[500];
    char *tmpbuf;
    int corr[MAXLIMITS];
    int i, j, h, k;
    double **mat;
    double min, max, NEWmin, NEWmax, a;
    CELL **intmat;
    struct Cell_head cellhd;
    struct Cell_head cellhd_orig;
    char outputmap_name[500];
    int FD;
    int npca;
    double sqrt_npca;
    int ROW, COL;
    int index;
    char *outputxgraph_name;
    FILE *FP;
    double sum;
    double tmp;
    double *vett1, *vett2;
    int maxeig = 0;
    int layer;
    int ncorr;
    int *npoints_for_class;
    double **DataMat;
    double d, prob, coeffcorr, pvalue, zvalue;
    double mean, sd;
    int *indexA;

    G_gisinit(argv[0]);

    module = G_define_module();
    G_add_keyword(_("imagery"));
    G_add_keyword(_("image processing"));
    G_add_keyword(_("pattern recognition"));
    module->description =
        _("Module to calculate feature statistics. "
          "i.pr: Pattern Recognition environment for image processing. "
          "Includes kNN, "
          "Decision Tree and SVM classification techniques. Also includes "
          "cross-validation and bagging methods for model validation.");

    opt1 = G_define_option();
    opt1->key = "features";
    opt1->type = TYPE_STRING;
    opt1->required = YES;
    opt1->description =
        "Input file containing the features (output of i.pr_features).";

    opt3 = G_define_option();
    opt3->key = "layer";
    opt3->type = TYPE_INTEGER;
    opt3->required = NO;
    opt3->description = "Number of the layer to be analized (concerning with "
                        "the principal components).\n\t\tIgnored if features "
                        "does not contain principal components model.";
    opt3->answer = "1";

    opt2 = G_define_option();
    opt2->key = "npc";
    opt2->type = TYPE_INTEGER;
    opt2->required = NO;
    opt2->description =
        "Number of principal components to be analized.\n\t\tIf this number is "
        "greater then the dimension of the data,\n\t\tall the principal "
        "components will be considered.\n\t\tIgnored if features does not "
        "contain principal components model.";

    opt4 = G_define_option();
    opt4->key = "corr";
    opt4->type = TYPE_INTEGER;
    opt4->required = NO;
    opt4->multiple = YES;
    opt4->description = "Index of columns to compute correlation.";

    /***** Start of main *****/

    if (G_parser(argc, argv) < 0)
        exit(-1);

    sscanf(opt3->answer, "%d", &layer);

    read_features(opt1->answer, &features, -1);
    if ((layer <= 0) || (layer > features.training.nlayers)) {
        sprintf(tempbuf, "Number of layers is %d\n", features.training.nlayers);
        G_fatal_error(tempbuf);
    }

    ncorr = 0;
    /*get index for correlation */
    if (opt4->answers) {
        for (i = 0; (tmpbuf = opt4->answers[i]); i++, ncorr++) {
            if (i == MAXLIMITS)
                break;
            sscanf(tmpbuf, "%d", &(corr[i]));
            if (corr[i] == 0) {
                ncorr = features.examples_dim;
                for (j = 0; j < ncorr; j++) {
                    corr[j] = j + 1;
                }
                break;
            }
            if (corr[i] < 0 || corr[i] > features.examples_dim) {
                sprintf(tempbuf, "Negative index of columns or wrong index\n");
                G_fatal_error(tempbuf);
            }
        }

        if (ncorr == 1) {
            sprintf(tempbuf, "Can't do correlation with 1 column!!\n");
            G_fatal_error(tempbuf);
        }

        /* calcolo la correlazione tra le varie variabili */

        vett1 = (double *)G_calloc(features.nexamples, sizeof(double));
        vett2 = (double *)G_calloc(features.nexamples, sizeof(double));

        for (i = 0; i < ncorr; i++) {
            for (k = 0; k < features.nexamples; k++) {
                vett1[k] = features.value[k][corr[i] - 1];
            }
            for (j = i + 1; j < ncorr; j++) {
                for (k = 0; k < features.nexamples; k++) {
                    vett2[k] = features.value[k][corr[j] - 1];
                }

                pearsn(vett1, vett2, features.nexamples, &coeffcorr, &pvalue,
                       &zvalue);

                fprintf(stdout,
                        "features %d, %d:\t correlation coeff. %f \t pvalue %f",
                        corr[i], corr[j], coeffcorr, pvalue);

                if (pvalue < 0.001)
                    fprintf(stdout, " (***)\n");
                else if (pvalue < 0.01)
                    fprintf(stdout, " (**)\n");
                else if (pvalue < 0.05)
                    fprintf(stdout, " (*)\n");
                else
                    fprintf(stdout, "\n");
            }
        }
        exit(0);
    }

    npoints_for_class = (int *)G_calloc(features.nclasses, sizeof(int));
    for (i = 0; i < features.nexamples; i++) {
        for (j = 0; j < features.nclasses; j++) {
            if (features.class[i] == features.p_classes[j]) {
                npoints_for_class[j] += 1;
            }
        }
    }

    DataMat = (double **)G_calloc(features.nclasses, sizeof(double *));
    for (i = 0; i < features.nclasses; i++) {
        DataMat[i] = (double *)G_calloc(npoints_for_class[i], sizeof(double));
    }

    indexA = (int *)G_calloc(features.nclasses, sizeof(int));

    for (i = 0; i < features.examples_dim; i++) {
        for (k = 0; k < features.nclasses; k++) {
            indexA[k] = 0;
        }
        for (j = 0; j < features.nexamples; j++) {
            for (k = 0; k < features.nclasses; k++) {
                if (features.class[j] == features.p_classes[k]) {
                    DataMat[k][indexA[k]] = features.value[j][i];
                    indexA[k] += 1;
                    break;
                }
            }
        }
        for (k = 0; k < features.nclasses - 1; k++) {
            mean = mean_of_double_array(DataMat[k], npoints_for_class[k]);
            sd = sd_of_double_array_given_mean(DataMat[k], npoints_for_class[k],
                                               mean);

            fprintf(stdout, "features %d class %d:mean %f sd %f\n", i + 1,
                    features.p_classes[k], mean, sd);
            for (h = k + 1; h < features.nclasses; h++) {
                mean = mean_of_double_array(DataMat[h], npoints_for_class[h]);
                sd = sd_of_double_array_given_mean(DataMat[h],
                                                   npoints_for_class[h], mean);
                fprintf(stdout, "features %d class %d:mean %f sd %f\n", i + 1,
                        features.p_classes[h], mean, sd);
                kstwo(DataMat[k], npoints_for_class[k], DataMat[h],
                      npoints_for_class[h], &d, &prob);
                fprintf(stdout, "features %d: KS-test(class %d-%d): %f\t%f",
                        i + 1, features.p_classes[k], features.p_classes[h], d,
                        prob);
                if (prob < 0.001)
                    fprintf(stdout, " (***)\n");
                else if (prob < 0.01)
                    fprintf(stdout, " (**)\n");
                else if (prob < 0.05)
                    fprintf(stdout, " (*)\n");
                else
                    fprintf(stdout, "\n");
                tutest(DataMat[k], npoints_for_class[k], DataMat[h],
                       npoints_for_class[h], &d, &prob);
                fprintf(stdout, "features %d: T_test(class %d-%d): %f\t%f",
                        i + 1, features.p_classes[k], features.p_classes[h], d,
                        prob);
                if (prob < 0.001)
                    fprintf(stdout, " (***)\n");
                else if (prob < 0.01)
                    fprintf(stdout, " (**)\n");
                else if (prob < 0.05)
                    fprintf(stdout, " (*)\n");
                else
                    fprintf(stdout, "\n");
            }
        }
    }

    layer -= 1;

    if (features.f_pca[0]) {
        for (i = 2; i < 2 + features.f_pca[1]; i++) {
            if (features.f_pca[i] == layer) {
                /*set number of maps to be displaied */
                for (i = 0;
                     i < (features.training.rows * features.training.cols); i++)
                    if (features.pca[layer].eigval[i] > .0)
                        maxeig = i + 1;

                if (opt2->answer == NULL)
                    npca = maxeig;
                else {
                    sscanf(opt2->answer, "%d", &npca);
                    if (npca <= 0) {
                        sprintf(tempbuf, "npca must be > 0");
                        G_fatal_error(tempbuf);
                    }
                }
                if (npca > maxeig)
                    npca = maxeig;

                if (features.training.rows > 1 && features.training.cols > 1) {
                    /*make sure avalability of monitor */
                    if (R_open_driver() != 0)
                        G_fatal_error(_("No graphics device selected."));
                    R_close_driver();

                    /*number of rows and cols on the virtual screen */

                    sqrt_npca = sqrt(npca);
                    if (((int)sqrt_npca * (int)sqrt_npca) >= npca) {
                        ROW = (int)sqrt_npca;
                        COL = ROW;
                    }
                    else {
                        ROW = (int)sqrt_npca + 1;
                        COL = ROW;
                    }
                    if ((ROW * (COL - 1)) >= npca)
                        COL = COL - 1;

                    /* set region */
                    G_get_window(&cellhd_orig);
                    cellhd = cellhd_orig;
                    cellhd.rows = features.training.rows * ROW;
                    cellhd.cols = features.training.cols * COL;
                    cellhd.ew_res = 1.0;
                    cellhd.ns_res = 1.0;
                    cellhd.north = (double)(cellhd.rows);
                    cellhd.south = .0;
                    cellhd.east = (double)(cellhd.cols);
                    cellhd.west = .0;
                    if (G_set_window(&cellhd) == -1) {
                        sprintf(tempbuf, "error setting working window");
                        G_fatal_error(tempbuf);
                    }

                    /*open output raster map */

                    sprintf(outputmap_name, "%s_tmpimage", opt1->answer);

                    if (outputmap_name != NULL)
                        FD = open_new_CELL(outputmap_name);
                    else {
                        sprintf(tempbuf, "error setting the output name");
                        G_fatal_error(tempbuf);
                    }

                    /* alloc memory */
                    mat = (double **)G_calloc(cellhd.rows, sizeof(double *));
                    for (i = 0; i < cellhd.rows; i++)
                        mat[i] =
                            (double *)G_calloc(cellhd.cols, sizeof(double));
                    intmat = (int **)G_calloc(cellhd.rows, sizeof(int *));
                    for (i = 0; i < cellhd.rows; i++)
                        intmat[i] = (int *)G_calloc(cellhd.cols, sizeof(int));

                    for (i = 0; i < cellhd.rows; i++)
                        Rast_zero_c_buf(intmat[i]);

                    /*compute output raster map */
                    index = 0;
                    for (k = 0; k < ROW; k++) {
                        for (h = 0; h < COL; h++) {

                            /*an aoutovector */
                            if (index < npca) {
                                min = features.pca[layer].eigmat[0][index];
                                max = features.pca[layer].eigmat[0][index];

                                for (i = 0; i < features.training.rows; i++)
                                    for (j = 0; j < features.training.cols;
                                         j++) {
                                        mat[i][j] =
                                            features.pca[layer].eigmat
                                                [i * features.training.cols + j]
                                                [index];
                                        if (mat[i][j] < min)
                                            min = mat[i][j];
                                        if (mat[i][j] > max)
                                            max = mat[i][j];
                                    }

                                /*converted the aoutovalue in 0-256 */
                                NEWmin = 1.;
                                NEWmax = 255.;

                                if (max != min)
                                    a = (NEWmax - NEWmin) / (max - min);
                                else {
                                    sprintf(tempbuf,
                                            "min of eigenvect %d = max of "
                                            "eigenvect %d",
                                            index, index);
                                    G_fatal_error(tempbuf);
                                }

                                for (i = 0; i < features.training.rows; i++)
                                    for (j = 0; j < features.training.cols; j++)
                                        intmat[k * features.training.rows + i]
                                              [h * features.training.cols + j] =
                                                  (CELL)(a * (mat[i][j] - min) +
                                                         NEWmin);
                            }
                            index += 1;
                        }
                    }

                    /*write output map */
                    for (i = 0; i < cellhd.rows; i++)
                        if (G_put_map_row(FD, intmat[i]) == -1) {
                            sprintf(tempbuf, "error writing tmp raster map");
                            G_fatal_error(tempbuf);
                        }

                    if (Rast_close(FD) == -1) {
                        sprintf(tempbuf, "error closing tmp raster map");
                        G_fatal_error(tempbuf);
                    }

                    /*colors */
                    sprintf(tempbuf, "r.colors map=%s color=grey",
                            outputmap_name);
                    system(tempbuf);

                    /*graphics */
                    if (G_put_window(&cellhd) == -1) {
                        sprintf(tempbuf, "error writing working region");
                        G_fatal_error(tempbuf);
                    }
                    sprintf(tempbuf, "d.frame -e");
                    system(tempbuf);
                    if (R_open_driver() != 0)
                        G_fatal_error(_("No graphics device selected."));
                    Dcell(outputmap_name, G_mapset(), 0);
                    R_close_driver();
                    if (G_put_window(&cellhd_orig) == -1) {
                        sprintf(tempbuf,
                                "error writing original working region");
                        G_fatal_error(tempbuf);
                    }

                    /*remove */
                    G_remove("cats", outputmap_name);
                    G_remove("cell", outputmap_name);
                    G_remove("cell_misc", outputmap_name);
                    G_remove("cellhd", outputmap_name);
                    G_remove("colr", outputmap_name);
                    G_remove("hist", outputmap_name);
                }
                /*xgraph 1 */
                outputxgraph_name = G_tempfile();
                if ((FP = fopen(outputxgraph_name, "w")) == NULL) {
                    sprintf(tempbuf, "error opening tmp file for xgraph");
                    G_fatal_error(tempbuf);
                }

                fprintf(stdout,
                        "Principal components layer %d: cumulative explained "
                        "variance\n",
                        layer + 1);
                sum = .0;
                for (i = 0;
                     i < (features.training.rows * features.training.cols);
                     i++) {
                    features.pca[layer].eigval[i] =
                        features.pca[layer].eigval[i] *
                        features.pca[layer].eigval[i];
                    sum += features.pca[layer].eigval[i];
                }

                fprintf(FP, "0 0\n");
                if (sum != .0) {
                    tmp = .0;
                    for (i = 0; i < npca; i++) {
                        fprintf(FP, "%d %f\n", i + 1,
                                tmp + features.pca[layer].eigval[i] / sum);
                        fprintf(stdout, "p.c. %d: %f\n", i + 1,
                                tmp + features.pca[layer].eigval[i] / sum);
                        tmp += features.pca[layer].eigval[i] / sum;
                    }
                }
                else {
                    sprintf(tempbuf, "divide by 0");
                    G_fatal_error(tempbuf);
                }

                fclose(FP);

                sprintf(tempbuf, "xgraph -0 variance -P %s", outputxgraph_name);
                system(tempbuf);
                sprintf(tempbuf, "rm %s", outputxgraph_name);
                system(tempbuf);
                return 0;
            }
        }
    }
    return 0;
}

void pearsn(double x[], double y[], int n, double *r, double *prob, double *z)
{
    int j;
    double yt, xt, t, df;
    double syy = 0.0, sxy = 0.0, sxx = 0.0, ay = 0.0, ax = 0.0;
    double betai(), erfcc();

    /*calcolo della media */

    for (j = 1; j <= n; j++) {
        ax += x[j];
        ay += y[j];
    }

    ax /= n;
    ay /= n;

    /*calcolo del coefficiente di correlazione */

    for (j = 1; j <= n; j++) {
        xt = x[j] - ax;
        yt = y[j] - ay;
        sxx += xt * xt;
        syy += yt * yt;
        sxy += xt * yt;
    }

    *r = sxy / sqrt(sxx * syy);
    *z = 0.5 * log((1.0 + (*r) + TINY) / (1.0 - (*r) + TINY));
    df = n - 2;
    t = (*r) * sqrt(df / ((1.0 - (*r) + TINY) * (1.0 + (*r) + TINY)));
    *prob = betai(0.5 * df, 0.5, df / (df + t * t));
    /* *prob=erfcc(fabs((*z)*sqrt(n-1.0))/1.4142136); */
}

double erfcc(double x)
{
    double t, z, ans;

    z = fabs(x);
    t = 1.0 / (1.0 + 0.5 * z);
    ans =
        t * exp(-z * z - 1.26551223 +
                t * (1.00002368 +
                     t * (0.37409196 +
                          t * (0.09678418 +
                               t * (-0.18628806 +
                                    t * (0.27886807 +
                                         t * (-1.13520398 +
                                              t * (1.48851587 +
                                                   t * (-0.82215223 +
                                                        t * 0.17087277)))))))));
    return x >= 0.0 ? ans : 2.0 - ans;
}
