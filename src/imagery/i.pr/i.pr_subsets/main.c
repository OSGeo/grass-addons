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

void write_matrix();

int main(int argc, char **argv)
{
    struct GModule *module;
    struct Option *opt1;
    struct Option *opt2;
    struct Option *opt3;
    struct Flag *flag_c;
    struct Flag *flag_b;
    struct Flag *flag_s;

    Features features;
    Features *tr_features;
    Features *ts_features;

    char tmpbuf[500];
    int n_sets;
    int i, j, k;
    char fileout[500], filelab[500];
    FILE *flab;
    double *prob, *prob_pos, *prob_neg;
    int *random_labels, *non_extracted, *random_labels_pos, *random_labels_neg;
    int n_non_extracted;
    int npos, nneg;
    int n_extracted;
    int extracted;
    int indx;
    int idum;
    double probok;
    int seed;

    /* Initialize the GIS calls */
    G_gisinit(argv[0]);

    module = G_define_module();
    G_add_keyword(_("imagery"));
    G_add_keyword(_("image processing"));
    G_add_keyword(_("pattern recognition"));
    module->description =
        _("Module to create features file for experiment using a features file "
          "and applying cross-validation or bootstrap resampling. "
          "i.pr: Pattern Recognition environment for image processing. "
          "Includes kNN, "
          "Decision Tree and SVM classification techniques. Also includes "
          "cross-validation and bagging methods for model validation.");

    /* set up command line */
    opt1 = G_define_option();
    opt1->key = "features";
    opt1->type = TYPE_STRING;
    opt1->required = YES;
    opt1->description =
        "Input file containing the features (output of i.pr_features).";

    opt2 = G_define_option();
    opt2->key = "n_sets";
    opt2->type = TYPE_INTEGER;
    opt2->required = YES;
    opt2->description =
        "Number of subsets (>=1). If you set n_sets=1 and select  "
        "cross-validation,\n\t\tleave one out cv will be implemented.";

    opt3 = G_define_option();
    opt3->key = "seed";
    opt3->type = TYPE_INTEGER;
    opt3->required = YES;
    opt3->description =
        "Seed for the initialization (>=0), which specifies a starting "
        "point\n\t\tfor the random number sequence. Replicate same experiment.";
    opt3->answer = "0";

    flag_c = G_define_flag();
    flag_c->key = 'c';
    flag_c->description = "selected method: cross-validation.";

    flag_b = G_define_flag();
    flag_b->key = 'b';
    flag_b->description = "selected method: bootstrap.";

    flag_s = G_define_flag();
    flag_s->key = 's';
    flag_s->description =
        "selected method: stratified bootstrap (works only with two classes.";

    if (G_parser(argc, argv))
        exit(1);

    /*read parameters */
    sscanf(opt2->answer, "%d", &n_sets);
    if (n_sets <= 0) {
        sprintf(tmpbuf, "n_sets must be >0");
        G_fatal_error(tmpbuf);
    }

    sscanf(opt3->answer, "%d", &seed);
    if (seed < 0) {
        sprintf(tmpbuf, "seed must be >=0");
        G_fatal_error(tmpbuf);
    }

    if (!flag_b->answer && !flag_c->answer) {
        sprintf(tmpbuf, "Neither -b nor -c flag set!\n");
        G_fatal_error(tmpbuf);
    }

    /*read features */
    read_features(opt1->answer, &features, -1);

    if (flag_b->answer && !flag_s->answer) {
        sprintf(filelab, "%s__bootstrap__labels", opt1->answer);
        flab = fopen(filelab, "w");

        tr_features = (Features *)G_calloc(n_sets, sizeof(Features));
        ts_features = (Features *)G_calloc(n_sets, sizeof(Features));

        prob = (double *)G_calloc(features.nexamples, sizeof(double));
        for (i = 0; i < features.nexamples; i++)
            prob[i] = 1. / features.nexamples;
        random_labels = (int *)G_calloc(features.nexamples, sizeof(int));
        non_extracted = (int *)G_calloc(features.nexamples, sizeof(int));

        for (i = 0; i < n_sets; i++) {
            idum = i + seed;
            Bootsamples_rseed(features.nexamples, prob, random_labels, &idum);

            /*training */
            tr_features[i].file = features.file;
            tr_features[i].nexamples = features.nexamples;
            tr_features[i].examples_dim = features.examples_dim;
            tr_features[i].value =
                (double **)G_calloc(tr_features[i].nexamples, sizeof(double *));
            tr_features[i].class =
                (int *)G_calloc(tr_features[i].nexamples, sizeof(int));
            for (j = 0; j < tr_features[i].nexamples; j++) {
                tr_features[i].value[j] = features.value[random_labels[j]];
                tr_features[i].class[j] = features.class[random_labels[j]];
            }
            tr_features[i].p_classes = features.p_classes;
            tr_features[i].nclasses = features.nclasses;
            tr_features[i].mean = features.mean;
            tr_features[i].sd = features.sd;
            tr_features[i].f_normalize = features.f_normalize;
            tr_features[i].f_standardize = features.f_standardize;
            tr_features[i].f_mean = features.f_mean;
            tr_features[i].f_variance = features.f_variance;
            tr_features[i].f_pca = features.f_pca;
            tr_features[i].pca_class = features.pca_class;
            tr_features[i].pca = features.pca;
            tr_features[i].training = features.training;
            tr_features[i].npc = features.npc;
            tr_features[i].training.file = "generated by i.pr_subsets";

            sprintf(fileout, "%s__tr_bootstrap__%d", opt1->answer, i + 1);
            write_features(fileout, &tr_features[i]);

            fprintf(flab, "Training %d:\n", i + 1);

            for (j = 0; j < (tr_features[i].nexamples - 1); j++) {
                fprintf(flab, "%d\t", random_labels[j] + 1);
            }
            fprintf(flab, "%d\n",
                    random_labels[tr_features[i].nexamples - 1] + 1);

            /*test */
            n_non_extracted = 0;
            for (k = 0; k < tr_features[i].nexamples; k++) {
                extracted = 0;
                for (j = 0; j < tr_features[i].nexamples; j++) {
                    if (k == random_labels[j]) {
                        extracted = 1;
                        break;
                    }
                }
                if (!extracted) {
                    non_extracted[n_non_extracted] = k;
                    n_non_extracted++;
                }
            }

            ts_features[i].file = features.file;
            ts_features[i].nexamples = n_non_extracted;
            ts_features[i].examples_dim = features.examples_dim;
            ts_features[i].value =
                (double **)G_calloc(n_non_extracted, sizeof(double *));
            ts_features[i].class =
                (int *)G_calloc(n_non_extracted, sizeof(int));
            for (j = 0; j < n_non_extracted; j++) {
                ts_features[i].value[j] = features.value[non_extracted[j]];
                ts_features[i].class[j] = features.class[non_extracted[j]];
            }
            ts_features[i].p_classes = features.p_classes;
            ts_features[i].nclasses = features.nclasses;
            ts_features[i].mean = features.mean;
            ts_features[i].sd = features.sd;
            ts_features[i].f_normalize = features.f_normalize;
            ts_features[i].f_standardize = features.f_standardize;
            ts_features[i].f_mean = features.f_mean;
            ts_features[i].f_variance = features.f_variance;
            ts_features[i].f_pca = features.f_pca;
            ts_features[i].pca_class = features.pca_class;
            ts_features[i].pca = features.pca;
            ts_features[i].training = features.training;
            ts_features[i].npc = features.npc;
            ts_features[i].training.file = "generated by i.pr_subsets";

            sprintf(fileout, "%s__ts_bootstrap__%d", opt1->answer, i + 1);
            write_features(fileout, &ts_features[i]);

            fprintf(flab, "Test %d:\n", i + 1);

            for (j = 0; j < (ts_features[i].nexamples - 1); j++) {
                fprintf(flab, "%d\t", non_extracted[j] + 1);
            }
            fprintf(flab, "%d\n",
                    non_extracted[ts_features[i].nexamples - 1] + 1);
        }
        G_free(prob);
        G_free(random_labels);
        G_free(non_extracted);

        return 0;
    }

    /*stratified bootstrap */
    if (flag_s->answer && flag_b->answer) {

        sprintf(filelab, "%s__str_bootstrap__labels", opt1->answer);
        flab = fopen(filelab, "w");

        tr_features = (Features *)G_calloc(n_sets, sizeof(Features));
        ts_features = (Features *)G_calloc(n_sets, sizeof(Features));

        random_labels = (int *)G_calloc(features.nexamples, sizeof(int));
        non_extracted = (int *)G_calloc(features.nexamples, sizeof(int));

        npos = 0;
        nneg = 0;

        for (i = 0; i < features.nexamples; i++) {
            if (features.class[i] == 1) {
                npos++;
            }
            else if (features.class[i] == -1) {
                nneg++;
            }
        }

        prob_pos = (double *)G_calloc(features.nexamples, sizeof(double));
        prob_neg = (double *)G_calloc(features.nexamples, sizeof(double));
        random_labels_pos = (int *)G_calloc(npos, sizeof(int));
        random_labels_neg = (int *)G_calloc(nneg, sizeof(int));

        for (i = 0; i < features.nexamples; i++) {
            if (features.class[i] == 1) {
                prob_pos[i] = 1. / npos;
                prob_neg[i] = 0;
            }
            else if (features.class[i] == -1) {
                prob_pos[i] = 0.;
                prob_neg[i] = 1. / nneg;
            }
        }

        for (i = 0; i < n_sets; i++) {
            idum = i + seed;

            Bootsamples_rseed(npos, prob_pos, random_labels_pos, &idum);
            Bootsamples_rseed(nneg, prob_neg, random_labels_neg, &idum);

            for (j = 0; j < npos; j++) {
                random_labels[j] = random_labels_pos[j];
            }

            for (j = 0; j < nneg; j++) {
                random_labels[npos + j] = (random_labels_neg[j] + npos);
            }

            /*training */
            tr_features[i].file = features.file;
            tr_features[i].nexamples = features.nexamples;
            tr_features[i].examples_dim = features.examples_dim;
            tr_features[i].value =
                (double **)G_calloc(tr_features[i].nexamples, sizeof(double *));
            tr_features[i].class =
                (int *)G_calloc(tr_features[i].nexamples, sizeof(int));
            for (j = 0; j < tr_features[i].nexamples; j++) {
                tr_features[i].value[j] = features.value[random_labels[j]];
                tr_features[i].class[j] = features.class[random_labels[j]];
            }
            tr_features[i].p_classes = features.p_classes;
            tr_features[i].nclasses = features.nclasses;
            tr_features[i].mean = features.mean;
            tr_features[i].sd = features.sd;
            tr_features[i].f_normalize = features.f_normalize;
            tr_features[i].f_standardize = features.f_standardize;
            tr_features[i].f_mean = features.f_mean;
            tr_features[i].f_variance = features.f_variance;
            tr_features[i].f_pca = features.f_pca;
            tr_features[i].pca_class = features.pca_class;
            tr_features[i].pca = features.pca;
            tr_features[i].training = features.training;
            tr_features[i].npc = features.npc;
            tr_features[i].training.file = "generated by i.pr_subsets";

            sprintf(fileout, "%s__tr_bootstrap__%d", opt1->answer, i + 1);
            write_features(fileout, &tr_features[i]);

            fprintf(flab, "Training %d:\n", i + 1);

            for (j = 0; j < (tr_features[i].nexamples - 1); j++) {
                fprintf(flab, "%d\t", random_labels[j] + 1);
            }
            fprintf(flab, "%d\n",
                    random_labels[tr_features[i].nexamples - 1] + 1);

            /*test */
            n_non_extracted = 0;
            for (k = 0; k < tr_features[i].nexamples; k++) {
                extracted = 0;
                for (j = 0; j < tr_features[i].nexamples; j++) {
                    if (k == random_labels[j]) {
                        extracted = 1;
                        break;
                    }
                }
                if (!extracted) {
                    non_extracted[n_non_extracted] = k;
                    n_non_extracted++;
                }
            }

            ts_features[i].file = features.file;
            ts_features[i].nexamples = n_non_extracted;
            ts_features[i].examples_dim = features.examples_dim;
            ts_features[i].value =
                (double **)G_calloc(n_non_extracted, sizeof(double *));
            ts_features[i].class =
                (int *)G_calloc(n_non_extracted, sizeof(int));
            for (j = 0; j < n_non_extracted; j++) {
                ts_features[i].value[j] = features.value[non_extracted[j]];
                ts_features[i].class[j] = features.class[non_extracted[j]];
            }
            ts_features[i].p_classes = features.p_classes;
            ts_features[i].nclasses = features.nclasses;
            ts_features[i].mean = features.mean;
            ts_features[i].sd = features.sd;
            ts_features[i].f_normalize = features.f_normalize;
            ts_features[i].f_standardize = features.f_standardize;
            ts_features[i].f_mean = features.f_mean;
            ts_features[i].f_variance = features.f_variance;
            ts_features[i].f_pca = features.f_pca;
            ts_features[i].pca_class = features.pca_class;
            ts_features[i].pca = features.pca;
            ts_features[i].training = features.training;
            ts_features[i].npc = features.npc;
            ts_features[i].training.file = "generated by i.pr_subsets";

            sprintf(fileout, "%s__ts_bootstrap__%d", opt1->answer, i + 1);
            write_features(fileout, &ts_features[i]);

            fprintf(flab, "Test %d:\n", i + 1);

            for (j = 0; j < (ts_features[i].nexamples - 1); j++) {
                fprintf(flab, "%d\t", non_extracted[j] + 1);
            }
            fprintf(flab, "%d\n",
                    non_extracted[ts_features[i].nexamples - 1] + 1);
        }
        G_free(prob_pos);
        G_free(prob_neg);
        G_free(random_labels);
        G_free(random_labels_pos);
        G_free(random_labels_neg);
        G_free(non_extracted);

        return 0;
    }

    if (flag_c->answer && !flag_s->answer) {
        if (n_sets == 1) {
            tr_features =
                (Features *)G_calloc(features.nexamples, sizeof(Features));
            ts_features =
                (Features *)G_calloc(features.nexamples, sizeof(Features));

            /*training */
            for (i = 0; i < features.nexamples; i++) {
                tr_features[i].file = features.file;
                tr_features[i].nexamples = features.nexamples - 1;
                tr_features[i].examples_dim = features.examples_dim;
                tr_features[i].value = (double **)G_calloc(
                    features.nexamples - 1, sizeof(double *));
                tr_features[i].class =
                    (int *)G_calloc(features.nexamples - 1, sizeof(int));
                indx = 0;
                for (j = 0; j < features.nexamples; j++) {
                    if (j != i) {
                        tr_features[i].value[indx] = features.value[j];
                        tr_features[i].class[indx++] = features.class[j];
                    }
                }

                tr_features[i].p_classes = features.p_classes;
                tr_features[i].nclasses = features.nclasses;
                tr_features[i].mean = features.mean;
                tr_features[i].sd = features.sd;
                tr_features[i].f_normalize = features.f_normalize;
                tr_features[i].f_standardize = features.f_standardize;
                tr_features[i].f_mean = features.f_mean;
                tr_features[i].f_variance = features.f_variance;
                tr_features[i].f_pca = features.f_pca;
                tr_features[i].pca_class = features.pca_class;
                tr_features[i].pca = features.pca;
                tr_features[i].training = features.training;
                tr_features[i].npc = features.npc;
                tr_features[i].training.file = "generated by i.pr_subsets";

                sprintf(fileout, "%s__tr_l1ocv__%d", opt1->answer, i + 1);
                write_features(fileout, &tr_features[i]);

                /*test */
                ts_features[i].file = features.file;
                ts_features[i].nexamples = 1;
                ts_features[i].examples_dim = features.examples_dim;
                ts_features[i].value = (double **)G_calloc(1, sizeof(double *));
                ts_features[i].class = (int *)G_calloc(1, sizeof(int));
                ts_features[i].value[0] = features.value[i];
                ts_features[i].class[0] = features.class[i];

                ts_features[i].p_classes = features.p_classes;
                ts_features[i].nclasses = features.nclasses;
                ts_features[i].mean = features.mean;
                ts_features[i].sd = features.sd;
                ts_features[i].f_normalize = features.f_normalize;
                ts_features[i].f_standardize = features.f_standardize;
                ts_features[i].f_mean = features.f_mean;
                ts_features[i].f_variance = features.f_variance;
                ts_features[i].f_pca = features.f_pca;
                ts_features[i].pca_class = features.pca_class;
                ts_features[i].pca = features.pca;
                ts_features[i].training = features.training;
                ts_features[i].npc = features.npc;
                ts_features[i].training.file = "generated by i.pr_subsets";

                sprintf(fileout, "%s__ts_l1ocv__%d", opt1->answer, i + 1);
                write_features(fileout, &ts_features[i]);
            }
            return 0;
        }
        else {
            sprintf(filelab, "%s__cv__labels", opt1->answer);
            flab = fopen(filelab, "w");

            tr_features = (Features *)G_calloc(n_sets, sizeof(Features));
            ts_features = (Features *)G_calloc(n_sets, sizeof(Features));

            if (n_sets > features.nexamples) {
                sprintf(tmpbuf,
                        "n_sets must be <= %d (=number of training data) if "
                        "you want to use cross-validation",
                        features.nexamples);
                G_fatal_error(tmpbuf);
            }

            probok = pow(1. - pow(1. - 1. / n_sets, (double)features.nexamples),
                         (double)n_sets);
            if (probok < 0.95) {
                sprintf(tmpbuf,
                        "the probability of extracting %d non empty test sets "
                        "is less than 0.95 (the probability is exactly %e). "
                        "Sorry but I don't like to take this risk.",
                        n_sets, probok);
                G_fatal_error(tmpbuf);
            }

            random_labels = (int *)G_calloc(features.nexamples, sizeof(int));
            for (i = 0; i < n_sets; i++) {
                idum = i + seed;
                for (j = 0; j < features.nexamples; j++)
                    random_labels[j] = (int)(n_sets * ran1(&idum));

                /*training */
                n_extracted = 0;
                for (j = 0; j < features.nexamples; j++)
                    if (random_labels[j] != i)
                        n_extracted++;

                tr_features[i].file = features.file;
                tr_features[i].nexamples = n_extracted;
                tr_features[i].examples_dim = features.examples_dim;
                tr_features[i].value =
                    (double **)G_calloc(n_extracted, sizeof(double *));
                tr_features[i].class =
                    (int *)G_calloc(n_extracted, sizeof(int));

                fprintf(flab, "Training %d:\n", i + 1);

                indx = 0;

                for (j = 0; j < (features.nexamples - 1); j++) {
                    if (random_labels[j] != i) {
                        tr_features[i].value[indx] = features.value[j];
                        tr_features[i].class[indx++] = features.class[j];
                        fprintf(flab, "%d\t", j + 1);
                    }
                }

                if (random_labels[features.nexamples - 1] != i) {
                    tr_features[i].value[indx] =
                        features.value[features.nexamples - 1];
                    tr_features[i].class[indx++] =
                        features.class[features.nexamples - 1];
                    fprintf(flab, "%d", features.nexamples);
                }

                fprintf(flab, "\n");

                tr_features[i].p_classes = features.p_classes;
                tr_features[i].nclasses = features.nclasses;
                tr_features[i].mean = features.mean;
                tr_features[i].sd = features.sd;
                tr_features[i].f_normalize = features.f_normalize;
                tr_features[i].f_standardize = features.f_standardize;
                tr_features[i].f_mean = features.f_mean;
                tr_features[i].f_variance = features.f_variance;
                tr_features[i].f_pca = features.f_pca;
                tr_features[i].pca_class = features.pca_class;
                tr_features[i].pca = features.pca;
                tr_features[i].training = features.training;
                tr_features[i].npc = features.npc;
                tr_features[i].training.file = "generated by i.pr_subsets";

                sprintf(fileout, "%s__tr_%dcv__%d", opt1->answer, n_sets,
                        i + 1);
                write_features(fileout, &tr_features[i]);

                /*test */
                n_non_extracted = 0;
                for (j = 0; j < features.nexamples; j++)
                    if (random_labels[j] == i)
                        n_non_extracted++;

                tr_features[i].file = features.file;
                tr_features[i].nexamples = n_non_extracted;
                tr_features[i].examples_dim = features.examples_dim;
                tr_features[i].value =
                    (double **)G_calloc(n_non_extracted, sizeof(double *));
                tr_features[i].class =
                    (int *)G_calloc(n_non_extracted, sizeof(int));

                fprintf(flab, "Test %d:\n", i + 1);

                indx = 0;
                for (j = 0; j < (features.nexamples - 1); j++) {
                    if (random_labels[j] == i) {
                        tr_features[i].value[indx] = features.value[j];
                        tr_features[i].class[indx++] = features.class[j];
                        fprintf(flab, "%d\t", j + 1);
                    }
                }

                if (random_labels[features.nexamples - 1] == i) {
                    tr_features[i].value[indx] =
                        features.value[features.nexamples - 1];
                    tr_features[i].class[indx++] =
                        features.class[features.nexamples - 1];
                    fprintf(flab, "%d", features.nexamples);
                }

                fprintf(flab, "\n");

                tr_features[i].p_classes = features.p_classes;
                tr_features[i].nclasses = features.nclasses;
                tr_features[i].mean = features.mean;
                tr_features[i].sd = features.sd;
                tr_features[i].f_normalize = features.f_normalize;
                tr_features[i].f_standardize = features.f_standardize;
                tr_features[i].f_mean = features.f_mean;
                tr_features[i].f_variance = features.f_variance;
                tr_features[i].f_pca = features.f_pca;
                tr_features[i].pca_class = features.pca_class;
                tr_features[i].pca = features.pca;
                tr_features[i].training = features.training;
                tr_features[i].npc = features.npc;
                tr_features[i].training.file = "generated by i.pr_subsets";

                sprintf(fileout, "%s__ts_%dcv__%d", opt1->answer, n_sets,
                        i + 1);
                write_features(fileout, &tr_features[i]);
            }
            G_free(random_labels);
            return 0;
        }
    }

    if (flag_c->answer && flag_s->answer) {
        fprintf(stderr, "Stratified Cross validation not implemented (yet)!\n");
        exit(0);
    }
    return 0;
}
