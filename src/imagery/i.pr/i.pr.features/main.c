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

int main(int argc, char **argv)
{
    struct GModule *module;
    struct Option *opt1;
    struct Option *opt2;
    struct Option *opt3;
    struct Option *opt4;
    struct Option *opt5;
    struct Option *opt6;
    struct Option *opt7;
    struct Option *opt8;

    struct Flag *flag_s;
    char *training_file[TRAINING_MAX_INPUTFILES];
    int ntraining_file;
    int i, j;
    Features features;
    char *tmpbuf;
    int nclasses_for_pca;
    char tempbuf[500];
    char opt1desc[500];
    FILE *fp;

    /* Initialize the GIS calls */
    G_gisinit(argv[0]);

    module = G_define_module();
    G_add_keyword(_("imagery"));
    G_add_keyword(_("image processing"));
    G_add_keyword(_("pattern recognition"));
    module->description =
        _("Module to process training data for feature extration. "
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
    opt2->description = "Name of the output file containing the features.";

    opt4 = G_define_option();
    opt4->key = "normalize";
    opt4->type = TYPE_INTEGER;
    opt4->required = NO;
    opt4->description = "Numbers of the layers to be normalized.";
    opt4->multiple = YES;

    opt6 = G_define_option();
    opt6->key = "mean";
    opt6->type = TYPE_INTEGER;
    opt6->required = NO;
    opt6->description =
        "Numbers of the layers on which to compute the mean value.";
    opt6->multiple = YES;

    opt7 = G_define_option();
    opt7->key = "variance";
    opt7->type = TYPE_INTEGER;
    opt7->required = NO;
    opt7->description =
        "Numbers of the layers on which to compute the variance.";
    opt7->multiple = YES;

    opt8 = G_define_option();
    opt8->key = "prin_comp";
    opt8->type = TYPE_INTEGER;
    opt8->required = NO;
    opt8->description =
        "Numbers of the layers on which to compute the principal components.";
    opt8->multiple = YES;

    opt3 = G_define_option();
    opt3->key = "class_pc";
    opt3->type = TYPE_INTEGER;
    opt3->required = NO;
    opt3->description =
        "Classes of the data to be used for computing the principal "
        "components.\n\t\tIf not set, all the examples will be used.";
    opt3->multiple = YES;

    opt5 = G_define_option();
    opt5->key = "standardize";
    opt5->type = TYPE_INTEGER;
    opt5->required = NO;
    opt5->description = "Numbers of features to be standardize.\n\t\tWARNING: "
                        "not related to the number of layers.";
    opt5->multiple = YES;

    flag_s = G_define_flag();
    flag_s->key = 's';
    flag_s->description =
        "Print site file containing coordinates of examples and class "
        "labels\n\t(from training data) into features option and exit.";

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
    inizialize_training(&(features.training));
    for (i = 0; i < ntraining_file; i++) {
        read_training(training_file[i], &(features.training));
    }

    if (flag_s->answer) {
        if ((fp = fopen(opt2->answer, "w")) == NULL) {
            sprintf(tempbuf, "Can't open file %s for writing", opt2->answer);
            G_fatal_error(tempbuf);
        }
        for (i = 0; i < features.training.nexamples; i++) {
            fprintf(fp, "%f|%f|#%d\n", features.training.east[i],
                    features.training.north[i], features.training.class[i]);
        }
        fclose(fp);
        return 0;
    }

    /*which action to do on the data */
    features.f_normalize =
        (int *)G_calloc(features.training.nlayers + 1, sizeof(int));
    features.f_standardize =
        (int *)G_calloc(features.training.nlayers + 1, sizeof(int));
    features.f_mean =
        (int *)G_calloc(features.training.nlayers + 1, sizeof(int));
    features.f_variance =
        (int *)G_calloc(features.training.nlayers + 1, sizeof(int));
    features.f_pca =
        (int *)G_calloc(features.training.nlayers + 1, sizeof(int));

    if (opt4->answers) {
        j = 0;
        for (i = 0; (tmpbuf = opt4->answers[i]); i++) {
            j += 1;
        }
        features.f_normalize = (int *)G_calloc(2 + j, sizeof(int));
        features.f_normalize[0] = 1;
        features.f_normalize[1] = j;
        for (i = 2; i < 2 + j; i++) {
            sscanf(opt4->answers[i - 2], "%d", &(features.f_normalize[i]));
            if ((features.f_normalize[i] <= 0) ||
                (features.f_normalize[i] > features.training.nlayers)) {
                sprintf(tempbuf, "nlayers = %d\n", features.training.nlayers);
                G_fatal_error(tempbuf);
            }
            features.f_normalize[i] -= 1;
        }
    }
    else {
        features.f_normalize = (int *)G_calloc(2, sizeof(int));
    }

    if (opt6->answers) {
        j = 0;
        for (i = 0; (tmpbuf = opt6->answers[i]); i++) {
            j += 1;
        }
        features.f_mean = (int *)G_calloc(2 + j, sizeof(int));
        features.f_mean[0] = 1;
        features.f_mean[1] = j;
        for (i = 2; i < 2 + j; i++) {
            sscanf(opt6->answers[i - 2], "%d", &(features.f_mean[i]));
            if ((features.f_mean[i] <= 0) ||
                (features.f_mean[i] > features.training.nlayers)) {
                sprintf(tempbuf, "nlayers = %d\n", features.training.nlayers);
                G_fatal_error(tempbuf);
            }
            features.f_mean[i] -= 1;
        }
    }
    else {
        features.f_mean = (int *)G_calloc(2, sizeof(int));
    }

    if (opt7->answers) {
        j = 0;
        for (i = 0; (tmpbuf = opt7->answers[i]); i++) {
            j += 1;
        }
        features.f_variance = (int *)G_calloc(2 + j, sizeof(int));
        features.f_variance[0] = 1;
        features.f_variance[1] = j;
        for (i = 2; i < 2 + j; i++) {
            sscanf(opt7->answers[i - 2], "%d", &(features.f_variance[i]));
            if ((features.f_variance[i] <= 0) ||
                (features.f_variance[i] > features.training.nlayers)) {
                sprintf(tempbuf, "nlayers = %d\n", features.training.nlayers);
                G_fatal_error(tempbuf);
            }
            features.f_variance[i] -= 1;
        }
    }
    else {
        features.f_variance = (int *)G_calloc(2, sizeof(int));
    }

    if (opt8->answers) {
        j = 0;
        for (i = 0; (tmpbuf = opt8->answers[i]); i++) {
            j += 1;
        }
        features.f_pca = (int *)G_calloc(2 + j, sizeof(int));
        features.f_pca[0] = 1;
        features.f_pca[1] = j;
        for (i = 2; i < 2 + j; i++) {
            sscanf(opt8->answers[i - 2], "%d", &(features.f_pca[i]));
            if ((features.f_pca[i] <= 0) ||
                (features.f_pca[i] > features.training.nlayers)) {
                sprintf(tempbuf, "nlayers = %d\n", features.training.nlayers);
                G_fatal_error(tempbuf);
            }
            features.f_pca[i] -= 1;
        }
    }
    else {
        features.f_pca = (int *)G_calloc(2, sizeof(int));
    }

    if (features.f_pca[0]) {
        if (opt3->answers) {
            nclasses_for_pca = 0;
            for (i = 0; (tmpbuf = opt3->answers[i]); i++) {
                nclasses_for_pca += 1;
            }
            features.pca_class =
                (int *)G_calloc(2 + nclasses_for_pca, sizeof(int));
            features.pca_class[0] = 1;
            features.pca_class[1] = nclasses_for_pca;
            for (i = 2; i < 2 + nclasses_for_pca; i++) {
                sscanf(opt3->answers[i - 2], "%d", &(features.pca_class[i]));
            }
        }
        else {
            features.pca_class = (int *)G_calloc(2, sizeof(int));
        }
    }

    if (opt5->answers) {
        j = 0;
        for (i = 0; (tmpbuf = opt5->answers[i]); i++) {
            j += 1;
        }
        features.f_standardize = (int *)G_calloc(2 + j, sizeof(int));
        features.f_standardize[0] = 1;
        features.f_standardize[1] = j;
        for (i = 2; i < 2 + j; i++) {
            sscanf(opt5->answers[i - 2], "%d", &(features.f_standardize[i]));
            features.f_standardize[i] -= 1;
        }
    }
    else {
        features.f_standardize = (int *)G_calloc(2, sizeof(int));
    }

    /*fill features structure */
    compute_features(&features);

    /*standardize features */
    if (features.f_standardize[0]) {
        standardize_features(&features);
    }

    /*write features */
    write_features(opt2->answer, &features);

    return 0;
}
