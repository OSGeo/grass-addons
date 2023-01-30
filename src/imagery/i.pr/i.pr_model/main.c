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
    struct Option *opt9;
    struct Option *opt10;
    struct Option *opt11;
    struct Option *opt12;
    struct Option *opt13;
    struct Option *opt14;
    struct Option *opt15;
    struct Option *opt16;
    struct Option *opt17;
    struct Option *opt18;
    struct Option *opt19;
    struct Option *opt20;
    struct Option *opt21;
    struct Option *opt22;
    struct Option *opt23;
    struct Option *opt24;
    struct Option *opt25;
    struct Option *opt26;
    struct Option *opt27;
    struct Option *opt28;
    struct Flag *flag_g;
    struct Flag *flag_t;
    struct Flag *flag_s;
    struct Flag *flag_n;

    Features features;
    Features test_features;
    Features validation_features;
    Tree tree;
    GaussianMixture gm;
    NearestNeighbor nn;
    SupportVectorMachine svm;
    BTree btree;
    BSupportVectorMachine bsvm;

    char tmpbuf[500];
    int tree_stamps, tree_minsize;
    char svm_kernel_type[100];
    double svm_kp, svm_C, svm_tol, svm_eps;
    int svm_maxloops;
    int svm_kernel;
    int svm_verbose;
    double svm_cost;
    double *svm_W;
    int bagging, boosting, reg, reg_verbose;
    double w;
    int i, j;
    char outfile[500];
    char outfile1[500];
    int svm_l1o;
    int weights_boosting;
    double *tree_costs;
    char *tmp_costs;
    int soft_margin_boosting;
    int progressive_error;
    int parallel_boosting;
    double *misratio;
    double misclass_ratio;
    int testset;

    /* Initialize the GIS calls */
    G_gisinit(argv[0]);

    module = G_define_module();
    G_add_keyword(_("imagery"));
    G_add_keyword(_("image processing"));
    G_add_keyword(_("pattern recognition"));
    module->description =
        _("Module to generate model from features file. "
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
    opt2->key = "model";
    opt2->type = TYPE_STRING;
    opt2->required = YES;
    opt2->description = "Name of the output file containing the model.";

    opt26 = G_define_option();
    opt26->key = "validation";
    opt26->type = TYPE_STRING;
    opt26->required = NO;
    opt26->description =
        "Input file containing other features for the training\n\t\t\tand for "
        "the evaluation of the performances of the model\n\t\t\ton an "
        "independent test set (for regularized AdaBoost).";

    opt16 = G_define_option();
    opt16->key = "test";
    opt16->type = TYPE_STRING;
    opt16->required = NO;
    opt16->description =
        "Input file containing other features for the evaluation of "
        "the\n\t\t\tperformances of the model on an independent test set.";

    opt3 = G_define_option();
    opt3->key = "npc";
    opt3->type = TYPE_INTEGER;
    opt3->required = NO;
    opt3->description = "Number of the principal components to be used for the "
                        "model development.\n\t\t\tIf not set all the "
                        "principal components will be used.\n\t\t\tIgnored if "
                        "features does not contain principal components model.";

    opt13 = G_define_option();
    opt13->key = "bagging";
    opt13->type = TYPE_INTEGER;
    opt13->required = NO;
    opt13->description =
        "Number of bagging models.\n\t\t\tIf bagging = 0 the classical model "
        "will be implemented.\n\t\t\tImplemented for trees and svm only.";
    opt13->answer = "0";

    opt14 = G_define_option();
    opt14->key = "boosting";
    opt14->type = TYPE_INTEGER;
    opt14->required = NO;
    opt14->description =
        "Number of boosting models.\n\t\t\tIf boosting = 0 the classical model "
        "will be implemented.\n\t\t\tImplemented for trees and svm only.";
    opt14->answer = "0";

    opt25 = G_define_option();
    opt25->key = "reg";
    opt25->type = TYPE_INTEGER;
    opt25->required = NO;
    opt25->description = "Number of misclassification ratio intervals.";
    opt25->answer = "0";

    opt28 = G_define_option();
    opt28->key = "misclass_ratio";
    opt28->type = TYPE_DOUBLE;
    opt28->required = NO;
    opt28->description =
        "For regularized AdaBoost: misclassification ratio for\n\t\t\thard "
        "point shaving and compute the new model.";
    opt28->answer = "1.00";

    opt27 = G_define_option();
    opt27->key = "reg_verbose";
    opt27->type = TYPE_INTEGER;
    opt27->required = NO;
    opt27->description =
        "For regularized AdaBoost:\n\t\t\t- if it is set = 1 the current value "
        "of misclassification\n\t\t\t ratio and the current error will be "
        "printed.\n\t\t\t- if it is set to >1 the number of\n\t\t\t loops, "
        "accuracy and the current value of misclassification ratio\n\t\t\twill "
        "be printed.\n\t\t\t For shaving and compute:\n\t\t\t - if it is set "
        ">0 the numbers of samples shaved will be printed.";
    opt27->answer = "0";

    opt23 = G_define_option();
    opt23->key = "progressive_error";
    opt23->type = TYPE_INTEGER;
    opt23->required = NO;
    opt23->description =
        "Progressive estimate of the model error\n\t\t\tincreasing the number "
        "of aggregated models";
    opt23->answer = "0";
    opt23->options = "0,1";

    opt15 = G_define_option();
    opt15->key = "cost_boosting";
    opt15->type = TYPE_DOUBLE;
    opt15->required = NO;
    opt15->description =
        "Cost parameter for the implementation of cost-sensitive procedure(w "
        "in [0,2]).\n\t\t\tw>1 results higher weight on examples of class "
        "1.\n\t\t\tw<1 results higher weight on examples of class "
        "-1.\n\t\t\tw=1 corresponds to standard Adaboost.";
    opt15->answer = "1.0";

    opt19 = G_define_option();
    opt19->key = "weights_boosting";
    opt19->type = TYPE_INTEGER;
    opt19->required = NO;
    opt19->description = "For boosting: if weights_boosting = 1, a file "
                         "containing the evolution\n\t\t\tof the weights "
                         "associated to data points will be produced.";
    opt19->answer = "0";
    opt19->options = "0,1";

    opt24 = G_define_option();
    opt24->key = "parallel_boosting";
    opt24->type = TYPE_INTEGER;
    opt24->required = NO;
    opt24->description =
        "For boosting: number of true boosting steps for parallel "
        "boosting.\n\t\t\tImplemented only for trees!!";
    opt24->answer = "0";

    opt21 = G_define_option();
    opt21->key = "soft_margin_boosting";
    opt21->type = TYPE_INTEGER;
    opt21->required = NO;
    opt21->description = "For boosting: if soft_margin_boosting = 1, sof "
                         "margin of Ababoost\n\t\t\t will bee used. "
                         "Implemented only with trees. (Sperimental!!!!!!!!!!)";
    opt21->answer = "0";
    opt21->options = "0,1";

    opt4 = G_define_option();
    opt4->key = "tree_stamps";
    opt4->type = TYPE_INTEGER;
    opt4->required = NO;
    opt4->description = "For trees: if tree_stamps = 1, a single split tree "
                        "will be procuded,\n\t\t\tif tree_stamps = 0, a "
                        "classical tree will be procuded.";
    opt4->answer = "0";
    opt4->options = "0,1";

    opt5 = G_define_option();
    opt5->key = "tree_minsize";
    opt5->type = TYPE_INTEGER;
    opt5->required = NO;
    opt5->description =
        "For trees: minimum number of examples containined\n\t\t\tinto a node "
        "for splitting the node itself";
    opt5->answer = "0";

    opt20 = G_define_option();
    opt20->key = "tree_costs";
    opt20->type = TYPE_INTEGER;
    opt20->required = NO;
    opt20->description = "For trees: misclassification costs for each class";
    opt20->multiple = YES;

    opt6 = G_define_option();
    opt6->key = "svm_kernel";
    opt6->type = TYPE_STRING;
    opt6->required = NO;
    opt6->description = "For svm: type of employed kernel.";
    opt6->answer = "linear";
    opt6->options = "gaussian,linear,2pbk";

    opt7 = G_define_option();
    opt7->key = "svm_kp";
    opt7->type = TYPE_DOUBLE;
    opt7->required = NO;
    opt7->description = "For svm: kernel parameter (Required parameter if you "
                        "are using gaussian kernel).";

    opt8 = G_define_option();
    opt8->key = "svm_C";
    opt8->type = TYPE_DOUBLE;
    opt8->required = NO;
    opt8->description = "For svm: optimization parameter (Required parameter).";

    opt18 = G_define_option();
    opt18->key = "svm_cost";
    opt18->type = TYPE_DOUBLE;
    opt18->required = NO;
    opt18->description =
        "Cost parameter for the implementation of cost-sensitive procedure(w "
        "in [-1,1]).\n\t\t\tw>0 results higher weight on examples of class "
        "1.\n\t\t\tw<0 results higher weight on examples of class "
        "-1.\n\t\t\tw=0 corresponds to standard SVM.\n\t\t\tNot yet "
        "implemented (and may be it will be never implemented)\n\t\t\tfor "
        "bagging and boosting";
    opt18->answer = "0.0";

    opt9 = G_define_option();
    opt9->key = "svm_tol";
    opt9->type = TYPE_DOUBLE;
    opt9->required = NO;
    opt9->description = "For svm: tollerance parameter.";
    opt9->answer = "0.001";

    opt10 = G_define_option();
    opt10->key = "svm_eps";
    opt10->type = TYPE_DOUBLE;
    opt10->required = NO;
    opt10->description = "For svm: epsilon.";
    opt10->answer = "0.001";

    opt11 = G_define_option();
    opt11->key = "svm_l1o";
    opt11->type = TYPE_INTEGER;
    opt11->required = NO;
    opt11->description = "For svm: leave 1 out error estimate.";
    opt11->answer = "0";
    opt11->options = "0,1";

    opt12 = G_define_option();
    opt12->key = "svm_maxloops";
    opt12->type = TYPE_INTEGER;
    opt12->required = NO;
    opt12->description = "For svm: maximum number of optimization steps.";
    opt12->answer = "1000";

    opt22 = G_define_option();
    opt22->key = "svm_verbose";
    opt22->type = TYPE_INTEGER;
    opt22->required = NO;
    opt22->description =
        "For svm: if it is set to 1 the number of loops will be printed.";
    opt22->options = "0,1";
    opt22->answer = "0";

    opt17 = G_define_option();
    opt17->key = "nn_k";
    opt17->type = TYPE_INTEGER;
    opt17->required = NO;
    opt17->description =
        "For nn: Number of neighbor to be considered during the test phase.";
    opt17->answer = "1";

    flag_g = G_define_flag();
    flag_g->key = 'g';
    flag_g->description = "selected model: gaussian mixture.";

    flag_t = G_define_flag();
    flag_t->key = 't';
    flag_t->description = "selected model: classification trees.";

    flag_s = G_define_flag();
    flag_s->key = 's';
    flag_s->description = "selected model: support vector machines.";

    flag_n = G_define_flag();
    flag_n->key = 'n';
    flag_n->description = "selected model: nearest neighbor.";

    if (G_parser(argc, argv))
        exit(1);

    /*read parameters */
    if (opt3->answer) {
        sscanf(opt3->answer, "%d", &(features.npc));
    }
    else {
        features.npc = -1;
    }

    if (flag_n->answer) {
        sscanf(opt17->answer, "%d", &(nn.k));
        if (nn.k <= 0) {
            sprintf(tmpbuf, "number of neighbor must be > 0\n");
            G_fatal_error(tmpbuf);
        }
        if (nn.k % 2 == 0) {
            sprintf(tmpbuf, "number of neighbor must be odd\n");
            G_fatal_error(tmpbuf);
        }
    }

    if (flag_t->answer) {
        sscanf(opt4->answer, "%d", &tree_stamps);
        if ((tree_stamps != 0) && (tree_stamps != 1)) {
            sprintf(tmpbuf, "stamps must be 0 or 1\n");
            G_fatal_error(tmpbuf);
        }
        sscanf(opt5->answer, "%d", &tree_minsize);
        if (tree_minsize < 0) {
            sprintf(tmpbuf, "minsize must be >= 0\n");
            G_fatal_error(tmpbuf);
        }
    }

    if (flag_s->answer) {
        sscanf(opt6->answer, "%s", svm_kernel_type);
        sscanf(opt18->answer, "%lf", &svm_cost);

        if (strcmp(svm_kernel_type, "linear") == 0) {
            svm_kernel = SVM_KERNEL_LINEAR;
        }
        else if (strcmp(svm_kernel_type, "gaussian") == 0) {
            svm_kernel = SVM_KERNEL_GAUSSIAN;
        }
        else if (strcmp(svm_kernel_type, "2pbk") == 0) {
            svm_kernel = SVM_KERNEL_DIRECT;
        }
        else {
            sprintf(tmpbuf, "kernel type not implemended!\n");
            G_fatal_error(tmpbuf);
        }
        if (svm_kernel == SVM_KERNEL_GAUSSIAN) {
            if (!opt7->answer) {
                sprintf(tmpbuf, "Please set kernel parameter\n");
                G_fatal_error(tmpbuf);
            }
            else {
                sscanf(opt7->answer, "%lf", &svm_kp);
                if (svm_kp <= 0) {
                    sprintf(tmpbuf, "kernel parameter must be > 0\n");
                    G_fatal_error(tmpbuf);
                }
            }
        }
        else
            svm_kp = 0.0;

        if (!opt8->answer) {
            sprintf(tmpbuf, "Please set optimization parameter\n");
            G_fatal_error(tmpbuf);
        }
        else {
            sscanf(opt8->answer, "%lf", &svm_C);
            if (svm_C <= 0) {
                sprintf(tmpbuf, "optimization parameter must be > 0\n");
                G_fatal_error(tmpbuf);
            }
        }
        sscanf(opt9->answer, "%lf", &svm_tol);
        if (svm_tol <= 0) {
            sprintf(tmpbuf, "tol must be > 0\n");
            G_fatal_error(tmpbuf);
        }
        sscanf(opt10->answer, "%lf", &svm_eps);
        if (svm_eps <= 0) {
            sprintf(tmpbuf, "eps must be > 0\n");
            G_fatal_error(tmpbuf);
        }
        sscanf(opt12->answer, "%d", &svm_maxloops);
        if (svm_maxloops <= 0) {
            sprintf(tmpbuf, "maximum number of loops must be > 0\n");
            G_fatal_error(tmpbuf);
        }
        sscanf(opt11->answer, "%d", &svm_l1o);
        sscanf(opt22->answer, "%d", &svm_verbose);
    }

    sscanf(opt13->answer, "%d", &bagging);
    sscanf(opt14->answer, "%d", &boosting);
    sscanf(opt25->answer, "%d", &reg);
    sscanf(opt27->answer, "%d", &reg_verbose);
    sscanf(opt23->answer, "%d", &progressive_error);

    sscanf(opt28->answer, "%lf", &misclass_ratio);
    if ((misclass_ratio < 0) || (misclass_ratio > 1)) {
        sprintf(tmpbuf, "misclassification ratio must be > 0 and < 1\n");
        G_fatal_error(tmpbuf);
    }
    if ((misclass_ratio < 1) && (reg > 0)) {
        sprintf(tmpbuf, "Please select only one between shaving the training "
                        "set and regularized AdaBoost\n");
        G_fatal_error(tmpbuf);
    }
    if (bagging < 0) {
        bagging = 0;
    }

    if (reg < 0) {
        reg = 0;
    }

    if (boosting < 0) {
        boosting = 0;
    }

    if ((bagging > 0) && (boosting > 0)) {
        sprintf(tmpbuf,
                "Please select only one between bagging and boosting\n");
        G_fatal_error(tmpbuf);
    }

    if (boosting > 0) {
        sscanf(opt15->answer, "%lf", &w);
        if (w < 0.0 || w > 2.0) {
            sprintf(tmpbuf, "boosting cost in [0,2]\n");
            G_fatal_error(tmpbuf);
        }
        sscanf(opt19->answer, "%d", &weights_boosting);
        if ((weights_boosting != 0) && (weights_boosting != 1)) {
            sprintf(tmpbuf, "weights_boosting must be 0 or 1\n");
            G_fatal_error(tmpbuf);
        }
        sscanf(opt21->answer, "%d", &soft_margin_boosting);
        if ((soft_margin_boosting != 0) && (soft_margin_boosting != 1)) {
            sprintf(tmpbuf, "soft_margin_boosting must be 0 or 1\n");
            G_fatal_error(tmpbuf);
        }
        if (opt24->answer) {
            sscanf(opt24->answer, "%d", &parallel_boosting);
            if ((parallel_boosting <= boosting) && (parallel_boosting > 0)) {
                sprintf(tmpbuf, "parallel_boosting must be > boosting\n");
                G_fatal_error(tmpbuf);
            }
        }
    }

    /*read features */
    read_features(opt1->answer, &features, features.npc);
    if (features.nclasses == 2) {
        if ((features.p_classes[0] * features.p_classes[1]) != -1) {
            fprintf(stderr, "class %d interpreted as class -1\n",
                    features.p_classes[0]);
            fprintf(stderr, "class %d interpreted as class 1\n",
                    features.p_classes[1]);

            for (i = 0; i < features.nexamples; i++) {
                if (features.class[i] == features.p_classes[0]) {
                    features.class[i] = -1;
                }
                else {
                    features.class[i] = 1;
                }
            }
            features.p_classes[0] = -1;
            features.p_classes[1] = 1;
        }
    }

    /*now I know the classes, I can read the misclassifciation costs
       for the trees */

    if (flag_t->answer) {
        tree_costs = (double *)G_calloc(features.nclasses, sizeof(double));
        if (opt20->answers) {
            j = 0;
            for (i = 0; (tmp_costs = opt20->answers[i]); i++) {
                j += 1;
            }

            if (j > features.nclasses)
                j = features.nclasses;

            for (i = 0; i < j; i++)
                sscanf(opt20->answers[i], "%lf", &(tree_costs[i]));

            for (i = j; i < features.nclasses; i++)
                tree_costs[i] = 1.0;
        }
        else
            for (i = 0; i < features.nclasses; i++)
                tree_costs[i] = 1.0;
    }

    /*read test features */
    testset = 0;
    if (opt16->answer) {
        testset = 1;
        read_features(opt16->answer, &test_features, features.npc);
        if (test_features.nclasses == 2) {
            if ((test_features.p_classes[0] * test_features.p_classes[1]) !=
                -1) {
                fprintf(stderr, "class %d interpreted as class -1\n",
                        test_features.p_classes[0]);
                fprintf(stderr, "class %d interpreted as class 1\n",
                        test_features.p_classes[1]);

                for (i = 0; i < test_features.nexamples; i++) {
                    if (test_features.class[i] == test_features.p_classes[0]) {
                        test_features.class[i] = -1;
                    }
                    else {
                        test_features.class[i] = 1;
                    }
                }
                test_features.p_classes[0] = -1;
                test_features.p_classes[1] = 1;
            }
        }
    }

    /*read validation features */
    if ((opt26->answer) && (reg > 0)) {
        read_features(opt26->answer, &validation_features, features.npc);
        if (validation_features.nclasses == 2) {
            if ((validation_features.p_classes[0] *
                 validation_features.p_classes[1]) != -1) {
                fprintf(stderr, "class %d interpreted as class -1\n",
                        validation_features.p_classes[0]);
                fprintf(stderr, "class %d interpreted as class 1\n",
                        validation_features.p_classes[1]);

                for (i = 0; i < validation_features.nexamples; i++) {
                    if (validation_features.class[i] ==
                        validation_features.p_classes[0]) {
                        validation_features.class[i] = -1;
                    }
                    else {
                        validation_features.class[i] = 1;
                    }
                }
                validation_features.p_classes[0] = -1;
                validation_features.p_classes[1] = 1;
            }
        }
    }
    else if ((opt16->answer) && (reg > 0)) {
        fprintf(stderr, "Regularized adaboost: validation data not foud\n");
        exit(-1);
    }

    /*single models */
    if ((bagging == 0) && (boosting == 0)) {
        if (flag_t->answer) {
            /*tree */
            compute_tree(&tree, features.nexamples, features.examples_dim,
                         features.value, features.class, features.nclasses,
                         features.p_classes, tree_stamps, tree_minsize,
                         tree_costs);

            /*model test and output */
            write_tree(opt2->answer, &tree, &features);

            sprintf(outfile, "%s_tr_prediction", opt2->answer);
            fprintf(stdout, "Prediction on training data: %s\n", opt1->answer);
            test_tree(&tree, &features, outfile);
            if (opt16->answer) {
                sprintf(outfile, "%s_ts_prediction", opt2->answer);
                fprintf(stdout, "Prediction on test data: %s\n", opt16->answer);
                test_tree(&tree, &test_features, outfile);
            }
            return 0;
        }

        if (flag_g->answer) {
            /*gm */
            compute_gm(&gm, features.nexamples, features.examples_dim,
                       features.value, features.class, features.nclasses,
                       features.p_classes);

            /*model test and output */
            write_gm(opt2->answer, &gm, &features);

            compute_test_gm(&gm);

            sprintf(outfile, "%s_tr_prediction", opt2->answer);
            fprintf(stdout, "Prediction on training data: %s\n", opt1->answer);
            test_gm(&gm, &features, outfile);
            if (opt16->answer) {
                sprintf(outfile, "%s_ts_prediction", opt2->answer);
                fprintf(stdout, "Prediction on test data: %s\n", opt16->answer);
                test_gm(&gm, &test_features, outfile);
            }
            return 0;
        }

        if (flag_n->answer) {
            /*nearest neighbours */
            compute_nn(&nn, features.nexamples, features.examples_dim,
                       features.value, features.class);

            /*model test and output */
            write_nn(opt2->answer, &nn, &features);

            sprintf(outfile, "%s_tr_prediction", opt2->answer);
            fprintf(stdout, "Prediction on training data: %s\n", opt1->answer);
            test_nn(&nn, &features, nn.k, outfile);
            if (opt16->answer) {
                sprintf(outfile, "%s_ts_prediction", opt2->answer);
                fprintf(stdout, "Prediction on test data: %s\n", opt16->answer);
                test_nn(&nn, &test_features, nn.k, outfile);
            }
            return 0;
        }

        if (flag_s->answer) {
            /*svm */

            if (features.nclasses != 2) {
                sprintf(tmpbuf, "svm works only with 2 class problems\n");
                G_fatal_error(tmpbuf);
            }

            /*svm costs */
            svm_W = (double *)G_calloc(features.nexamples, sizeof(double));
            for (i = 0; i < features.nexamples; i++) {
                svm_W[i] = 1.;
                if (svm_cost > 0) {
                    if (features.class[i] < 0)
                        svm_W[i] = 1. - svm_cost;
                }
                else if (svm_cost < 0) {
                    if (features.class[i] > 0)
                        svm_W[i] = 1. + svm_cost;
                }
            }
            svm.cost = svm_cost;

            compute_svm(&svm, features.nexamples, features.examples_dim,
                        features.value, features.class, svm_kernel, svm_kp,
                        svm_C, svm_tol, svm_eps, svm_maxloops, svm_verbose,
                        svm_W);
            write_svm(opt2->answer, &svm, &features);

            /*model test and output */
            sprintf(outfile, "%s_tr_prediction", opt2->answer);
            fprintf(stdout, "Prediction on training data: %s\n", opt1->answer);
            test_svm(&svm, &features, outfile);

            /*if requested, leave 1 out error estimate */
            if (svm_l1o == 1) {
                fprintf(stdout, "Leave one out error estimate\n");
                estimate_cv_error(&svm);
            }
            if (opt16->answer) {
                sprintf(outfile, "%s_ts_prediction", opt2->answer);
                fprintf(stdout, "Prediction on test data: %s\n", opt16->answer);
                test_svm(&svm, &test_features, outfile);
            }

            return 0;
        }
    }

    /*bagging models */
    if (bagging > 0) {
        if (flag_n->answer) {
            sprintf(
                tmpbuf,
                "Sorry, bagging of nearest neighbor not yet implemented\n\n");
            G_fatal_error(tmpbuf);
        }
        if (flag_g->answer) {
            sprintf(
                tmpbuf,
                "Sorry, bagging of gaussian mixture not yet implemented\n\n");
            G_fatal_error(tmpbuf);
        }
        if (flag_t->answer) {
            /*trees */
            compute_tree_bagging(
                &btree, bagging, features.nexamples, features.examples_dim,
                features.value, features.class, features.nclasses,
                features.p_classes, tree_stamps, tree_minsize, tree_costs);

            /*model test and output */
            write_bagging_boosting_tree(opt2->answer, &btree, &features);
            sprintf(outfile, "%s_tr_prediction", opt2->answer);
            fprintf(stdout, "Prediction on training data: %s\n", opt1->answer);
            if (!progressive_error)
                test_btree(&btree, &features, outfile);
            else
                test_btree_progressive(&btree, &features, outfile);
            if (opt16->answer) {
                sprintf(outfile, "%s_ts_prediction", opt2->answer);
                fprintf(stdout, "Prediction on test data: %s\n", opt16->answer);
                if (!progressive_error)
                    test_btree(&btree, &test_features, outfile);
                else
                    test_btree_progressive(&btree, &test_features, outfile);
            }
            return 0;
        }
        if (flag_s->answer) {
            /*svm */
            if (features.nclasses != 2) {
                sprintf(tmpbuf, "svm works only with 2 class problems\n");
                G_fatal_error(tmpbuf);
            }

            svm_W = (double *)G_calloc(features.nexamples, sizeof(double));
            for (i = 0; i < features.nexamples; i++)
                svm_W[i] = 1.;

            compute_svm_bagging(
                &bsvm, bagging, features.nexamples, features.examples_dim,
                features.value, features.class, svm_kernel, svm_kp, svm_C,
                svm_tol, svm_eps, svm_maxloops, svm_verbose, svm_W);

            /*model test and output */
            write_bagging_boosting_svm(opt2->answer, &bsvm, &features);

            sprintf(outfile, "%s_tr_prediction", opt2->answer);
            fprintf(stdout, "Prediction on training data: %s\n", opt1->answer);
            if (!progressive_error)
                test_bsvm(&bsvm, &features, outfile);
            else
                test_bsvm_progressive(&bsvm, &features, outfile);
            if (opt16->answer) {
                sprintf(outfile, "%s_ts_prediction", opt2->answer);
                fprintf(stdout, "Prediction on test data: %s\n", opt16->answer);
                if (!progressive_error)
                    test_bsvm(&bsvm, &test_features, outfile);
                else
                    test_bsvm_progressive(&bsvm, &test_features, outfile);
            }
            return 0;
        }
    }

    /*boosting models */
    if (boosting > 0) {
        if (flag_n->answer) {
            sprintf(
                tmpbuf,
                "Sorry, boosting of nearest neighbor not yet implemented\n\n");
            G_fatal_error(tmpbuf);
        }
        if (flag_g->answer) {
            sprintf(
                tmpbuf,
                "Sorry, boosting of gaussian mixture not yet implemented\n\n");
            G_fatal_error(tmpbuf);
        }

        if (features.nclasses != 2) {
            sprintf(tmpbuf, "boosting works only with 2 class problems\n");
            G_fatal_error(tmpbuf);
        }
        if (flag_t->answer) {
            /*trees */
            /*regularized adboost */
            if ((parallel_boosting == 0) &&
                ((reg > 0) || (misclass_ratio < 1.00))) {
                misratio =
                    (double *)G_calloc(features.nexamples, sizeof(double));
                compute_tree_boosting_reg(
                    &btree, boosting, w, features.nexamples,
                    features.examples_dim, features.value, features.class,
                    features.nclasses, features.p_classes, tree_stamps,
                    tree_minsize, weights_boosting, tree_costs, misratio);
                if (reg_verbose != 0)
                    for (i = 0; i < features.nexamples; i++) {
                        fprintf(stdout,
                                "Misclassification ratio of point %d is %e:\n",
                                i, misratio[i]);
                    }
            }

            /*standard adboost */
            if ((parallel_boosting == 0) && (reg == 0) &&
                (misclass_ratio == 1.00)) {
                compute_tree_boosting(
                    &btree, boosting, w, features.nexamples,
                    features.examples_dim, features.value, features.class,
                    features.nclasses, features.p_classes, tree_stamps,
                    tree_minsize, weights_boosting, tree_costs);
            }
            /*parallel adaboost */
            else if (parallel_boosting > 0) {
                compute_tree_boosting_parallel(
                    &btree, boosting, parallel_boosting, w, features.nexamples,
                    features.examples_dim, features.value, features.class,
                    features.nclasses, features.p_classes, tree_stamps,
                    tree_minsize, weights_boosting, tree_costs);

                boosting = parallel_boosting;
            }

            /*if requested, boosting weights to output */
            if (weights_boosting == 1) {
                double *tmparray, *hist;

                hist = (double *)G_calloc(10000, sizeof(double));
                tmparray = (double *)G_calloc(boosting, sizeof(double));
                for (i = 0; i < features.nexamples; i++) {
                    for (j = 0; j < boosting; j++)
                        tmparray[j] = btree.w_evolution[i][j];

                    btree.w_evolution[i][boosting] =
                        mean_of_double_array(tmparray, boosting);
                    btree.w_evolution[i][boosting + 1] =
                        var_of_double_array_given_mean(
                            tmparray, boosting, btree.w_evolution[i][boosting]);
                    histo(tmparray, boosting, hist, 2 * boosting);
                    btree.w_evolution[i][boosting + 2] =
                        Entropy(hist, 2 * boosting, 0.000001);
                }
                sprintf(outfile, "%s_weights_boosting", opt2->answer);
                write_matrix(outfile, btree.w_evolution, features.nexamples,
                             boosting + 3);
            }

            /*if requested, soft margin boosting (sperimental) */
            if (soft_margin_boosting) {
                double *alpha, *beta, **M;

                alpha = (double *)G_calloc(features.nexamples, sizeof(double));
                beta = (double *)G_calloc(boosting, sizeof(double));

                M = (double **)G_calloc(features.nexamples, sizeof(double *));
                for (i = 0; i < features.nexamples; i++)
                    M[i] = (double *)G_calloc(boosting, sizeof(double));

                for (i = 0; i < features.nexamples; i++)
                    for (j = 0; j < boosting; j++)
                        M[i][j] = features.class[i] *
                                  predict_tree_multiclass(&(btree.tree[j]),
                                                          features.value[i]);

                maximize(alpha, features.nexamples, beta, boosting, M);

                for (i = 0; i < features.nexamples; i++) {
                    fprintf(stderr, "ALPHA[%d]=%e\n", i, alpha[i]);
                }
                fprintf(stderr, "\n");

                for (i = 0; i < boosting; i++) {
                    fprintf(stderr, "BETA[%d]=%e\n", i, beta[i]);
                }
                fprintf(stderr, "\n");

                for (i = 0; i < boosting; i++) {
                    btree.weights[i] = .0;
                    for (j = 0; j < features.nexamples; j++)
                        btree.weights[i] += alpha[j] * M[j][i];
                    btree.weights[i] += beta[i];
                }
            }

            /*model test and output */
            if ((reg == 0) && (misclass_ratio == 1.00)) {
                write_bagging_boosting_tree(opt2->answer, &btree, &features);
            }

            sprintf(outfile, "%s_tr_prediction", opt2->answer);
            if (!progressive_error) {

                if ((reg > 0) && (misclass_ratio == 1.00)) {
                    fprintf(stdout, "Prediction on training data: %s\n",
                            opt1->answer);
                    test_btree_reg(&btree, &features, outfile, misratio);
                }
                else if (misclass_ratio < 1.00) {
                    /* if requested, it shave the hard point (point with
                       misclassification ratio > misclass_ratio), compute the
                       new tree model and write output. */
                    sprintf(outfile1, "%s_ts_prediction", opt2->answer);
                    shaving_and_compute(
                        boosting, w, features.nexamples, features.examples_dim,
                        features.value, features.class, features.nclasses,
                        features.p_classes, tree_stamps, tree_minsize,
                        weights_boosting, tree_costs, misratio, reg_verbose,
                        misclass_ratio, outfile, opt2->answer, features,
                        test_features, outfile1, testset);
                }
                else {
                    fprintf(stdout, "Prediction on training data: %s\n",
                            opt1->answer);
                    test_btree(&btree, &features, outfile);
                }
            }
            else {
                fprintf(stdout, "Prediction on training data: %s\n",
                        opt1->answer);
                test_btree_progressive(&btree, &features, outfile);
            }

            if (((opt16->answer) && (misclass_ratio == 1.00)) ||
                ((reg > 0) && (opt26->answer))) {
                sprintf(outfile, "%s_ts_prediction", opt2->answer);

                /*if requested, it computes the regularized adaboost, model test
                 * and write output */
                {
                    if ((reg > 0) && (opt26->answer)) {
                        regularized_boosting(
                            boosting, w, features.nexamples,
                            features.examples_dim, features.value,
                            features.class, features.nclasses,
                            features.p_classes, tree_stamps, tree_minsize,
                            weights_boosting, tree_costs, misratio, reg,
                            test_features, outfile, validation_features,
                            reg_verbose, opt16->answer, opt26->answer,
                            opt2->answer, features, testset);
                    }

                    else if (!progressive_error) {
                        fprintf(stdout, "Prediction on test data: %s\n",
                                opt16->answer);
                        test_btree(&btree, &test_features, outfile);
                    }
                    else {
                        fprintf(stdout, "Prediction on test data: %s\n",
                                opt16->answer);
                        test_btree_progressive(&btree, &test_features, outfile);
                    }
                }
            }
            return 0;
        }

        if (flag_s->answer) {
            /*svm */
            svm_W = (double *)G_calloc(features.nexamples, sizeof(double));
            for (i = 0; i < features.nexamples; i++)
                svm_W[i] = 1.;

            compute_svm_boosting(
                &bsvm, boosting, w, features.nexamples, features.examples_dim,
                features.value, features.class, features.nclasses,
                features.p_classes, svm_kernel, svm_kp, svm_C, svm_tol, svm_eps,
                svm_maxloops, svm_verbose, svm_W, weights_boosting);

            /*if requested, boosting weights to output */
            if (weights_boosting == 1) {
                double *tmparray, *hist;

                hist = (double *)G_calloc(10000, sizeof(double));
                tmparray = (double *)G_calloc(boosting, sizeof(double));
                for (i = 0; i < features.nexamples; i++) {
                    for (j = 0; j < boosting; j++)
                        tmparray[j] = bsvm.w_evolution[i][j];

                    bsvm.w_evolution[i][boosting] =
                        mean_of_double_array(tmparray, boosting);
                    bsvm.w_evolution[i][boosting + 1] =
                        var_of_double_array_given_mean(
                            tmparray, boosting, bsvm.w_evolution[i][boosting]);
                    histo(tmparray, boosting, hist, 2 * boosting);
                    bsvm.w_evolution[i][boosting + 2] =
                        Entropy(hist, 2 * boosting, 0.000001);
                }
                sprintf(outfile, "%s_weights_boosting", opt2->answer);
                write_matrix(outfile, bsvm.w_evolution, features.nexamples,
                             boosting + 3);
            }

            /*model test and output */
            write_bagging_boosting_svm(opt2->answer, &bsvm, &features);

            sprintf(outfile, "%s_tr_prediction", opt2->answer);
            fprintf(stdout, "Prediction on training data: %s\n", opt1->answer);
            if (!progressive_error)
                test_bsvm(&bsvm, &features, outfile);
            else
                test_bsvm_progressive(&bsvm, &features, outfile);
            if (opt16->answer) {
                sprintf(outfile, "%s_ts_prediction", opt2->answer);
                fprintf(stdout, "Prediction on test data: %s\n", opt16->answer);
                if (!progressive_error)
                    test_bsvm(&bsvm, &test_features, outfile);
                else
                    test_bsvm_progressive(&bsvm, &test_features, outfile);
            }
            return 0;
        }
    }

    sprintf(tmpbuf, "please select a model\n");
    G_warning(tmpbuf);
    return 0;
}
