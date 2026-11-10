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
    struct Option *opt6;
    struct Option *opt7;
    struct Option *opt8;
    struct Option *opt9;
    struct Option *opt10;
    struct Option *opt12;
    struct Option *opt18;
    struct Option *opt23;
    struct Option *opt24;
    struct Option *opt22;
    struct Flag *flag_w;

    Features features;
    SupportVectorMachine *svm_models;
    SupportVectorMachine svm;

    char tmpbuf[500];
    char svm_kernel_type[100];
    char fs_type_string[100];
    double svm_kp, svm_C, svm_tol, svm_eps;
    int svm_maxloops;
    int svm_kernel;
    double svm_cost;
    double *svm_W;
    int i, j, k, t;
    int fs_type, fs_rfe, neliminati;
    FILE *fp_fs_out;
    FILE *fp_fs_w, *fp_fs_stats;
    char file_w[200], file_stats[200];
    int *selected, *names, *posizwsquare, *vareliminate;
    int rimanenti;
    int ncicli;
    double **H_tot, **H_tmp, *valoriDJ, *wsquarenuovo, *vareliminatedouble;
    int svm_verbose;

    /* Initialize the GIS calls */
    G_gisinit(argv[0]);

    module = G_define_module();
    G_add_keyword(_("imagery"));
    G_add_keyword(_("image processing"));
    G_add_keyword(_("pattern recognition"));
    module->description =
        _("Module for feature selection. "
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
    opt2->key = "output";
    opt2->type = TYPE_STRING;
    opt2->required = YES;
    opt2->description =
        "Name of the output file containing the selected features.";

    opt3 = G_define_option();
    opt3->key = "npc";
    opt3->type = TYPE_INTEGER;
    opt3->required = NO;
    opt3->description = "Number of the principal components to be used for the "
                        "model development.\n\t\t\tIf not set all the "
                        "principal components will be used.\n\t\t\tIgnored if "
                        "features does not contain principal components model.";

    opt6 = G_define_option();
    opt6->key = "svm_kernel";
    opt6->type = TYPE_STRING;
    opt6->required = NO;
    opt6->description = "For svm: type of employed kernel.";
    opt6->answer = "linear";
    opt6->options = "gaussian,linear";

    opt7 = G_define_option();
    opt7->key = "svm_kp";
    opt7->type = TYPE_DOUBLE;
    opt7->required = NO;
    opt7->description = "For svm: kernel parameter  (Required parameter if you "
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
        "-1.\n\t\t\tw=0 corresponds to standard SVM.";
    opt18->answer = "0.0";

    opt23 = G_define_option();
    opt23->key = "fs_type";
    opt23->type = TYPE_STRING;
    opt23->required = YES;
    opt23->description = "Feature selection method.";
    opt23->options = "rfe,e_rfe,1_rfe,sqrt_rfe";

    opt24 = G_define_option();
    opt24->key = "fs_rfe";
    opt24->type = TYPE_INTEGER;
    opt24->required = NO;
    opt24->description =
        "If you are using the e_rfe method, you have to choose the number of "
        "feartures\n\t\t\tfor the classical rfe method to start (fs_rfe>1).";

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

    flag_w = G_define_flag();
    flag_w->key = 'w';
    flag_w->description = "Produce file containing weights at each step.";

    if (G_parser(argc, argv))
        exit(1);

    /*
       read number of pc
       (May be we do not use this parameter in the next future)
     */

    if (opt3->answer) {
        sscanf(opt3->answer, "%d", &(features.npc));
    }
    else {
        features.npc = -1;
    }

    /*read SVM parameters */

    sscanf(opt6->answer, "%s", svm_kernel_type);
    sscanf(opt18->answer, "%lf", &svm_cost);

    if (strcmp(svm_kernel_type, "linear") == 0) {
        svm_kernel = SVM_KERNEL_LINEAR;
    }
    else if (strcmp(svm_kernel_type, "gaussian") == 0) {
        svm_kernel = SVM_KERNEL_GAUSSIAN;
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
    sscanf(opt22->answer, "%d", &svm_verbose);
    /* read features selection parameters (PLease check consistence!!!!) */

    sscanf(opt23->answer, "%s", fs_type_string);
    if (strcmp(fs_type_string, "rfe") == 0)
        fs_type = FS_RFE;
    else if (strcmp(fs_type_string, "e_rfe") == 0)
        fs_type = FS_E_RFE;
    else if (strcmp(fs_type_string, "1_rfe") == 0)
        fs_type = FS_ONE_RFE;
    else if (strcmp(fs_type_string, "sqrt_rfe") == 0)
        fs_type = FS_SQRT_RFE;
    else {
        sprintf(tmpbuf, "features selection method not recognized!\n");
        G_fatal_error(tmpbuf);
    }

    if (fs_type == FS_E_RFE) {
        if (!opt24->answer) {
            sprintf(tmpbuf,
                    "You selected e_rfe: please set fs_rfe parameter!\n");
            G_fatal_error(tmpbuf);
        }
        else
            sscanf(opt24->answer, "%d", &fs_rfe);

        if (fs_rfe <= 1) {
            sprintf(tmpbuf, "fs_rfe must be > 1\n");
            G_fatal_error(tmpbuf);
        }
    }

    /*output files */

    fp_fs_out = fopen(opt2->answer, "w");

    if (fp_fs_out == NULL) {
        fprintf(stderr, "Error opening file %s for writing\n", opt2->answer);
        exit(0);
    }

    if (flag_w->answer) {
        sprintf(file_w, "%s_w", opt2->answer);
        fp_fs_w = fopen(file_w, "w");

        if (fp_fs_w == NULL) {
            fprintf(stderr, "Error opening file %s for writing\n", file_w);
            exit(0);
        }
    }
    else
        fp_fs_w = NULL;

    if (fs_type == FS_E_RFE) {
        sprintf(file_stats, "%s_stats", opt2->answer);
        fp_fs_stats = fopen(file_stats, "w");

        if (fp_fs_stats == NULL) {
            fprintf(stderr, "Error opening file %s for writing\n", file_stats);
            exit(0);
        }
    }
    else
        fp_fs_stats = NULL;

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
    if (features.nclasses != 2) {
        sprintf(tmpbuf, "svm works only with 2 class problems\n");
        G_fatal_error(tmpbuf);
    }

    /*set svm parameters */
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

    /*set features selection variables */
    svm_models = (SupportVectorMachine *)G_calloc(features.examples_dim - 1,
                                                  sizeof(SupportVectorMachine));

    names = (int *)G_calloc(features.examples_dim, sizeof(int));
    selected = (int *)G_calloc(features.examples_dim, sizeof(int));

    for (j = 0; j < features.examples_dim; j++) {
        names[j] = j + 1;
    }

    /*WORK!!!! */
    if (svm_kernel == SVM_KERNEL_LINEAR) {
        /*LINEAR*/ switch (fs_type) {
        case FS_ONE_RFE:
            /*Non ricalcola linear */
            compute_svm(&svm, features.nexamples, features.examples_dim,
                        features.value, features.class, svm_kernel, svm_kp,
                        svm_C, svm_tol, svm_eps, svm_maxloops, svm_verbose,
                        svm_W);
            one_rfe_lin(&svm, names, selected, fp_fs_w);
            free_svm(&svm);
            break;
        case FS_RFE:
            /*RFE linear */
            for (i = 0; i < (features.examples_dim - 1); i++) {
                compute_svm(&(svm_models[i]), features.nexamples,
                            (features.examples_dim - i), features.value,
                            features.class, svm_kernel, svm_kp, svm_C, svm_tol,
                            svm_eps, svm_maxloops, svm_verbose, svm_W);

                rfe_lin(&(svm_models[i]), &features, names, selected, i,
                        fp_fs_w);
                free_svm(&(svm_models[i]));
            }
            selected[0] = names[0];
            break;
        case FS_E_RFE:
            /*Entropy-based RFE linear */
            rimanenti = features.examples_dim;

            ncicli = 0;
            for (i = 0; rimanenti > fs_rfe; i++) {
                compute_svm(&(svm_models[i]), features.nexamples, rimanenti,
                            features.value, features.class, svm_kernel, svm_kp,
                            svm_C, svm_tol, svm_eps, svm_maxloops, svm_verbose,
                            svm_W);

                e_rfe_lin(&(svm_models[i]), &features, names, selected, i,
                          &rimanenti, fp_fs_w, fp_fs_stats);
                free_svm(&(svm_models[i]));
                ncicli++;
            }

            for (i = ncicli; rimanenti > 1; i++) {
                compute_svm(&(svm_models[i]), features.nexamples, rimanenti,
                            features.value, features.class, svm_kernel, svm_kp,
                            svm_C, svm_tol, svm_eps, svm_maxloops, svm_verbose,
                            svm_W);
                rfe_lin(&(svm_models[i]), &features, names, selected,
                        features.examples_dim - rimanenti, fp_fs_w);
                free_svm(&(svm_models[i]));
                rimanenti--;
            }
            selected[0] = names[0];
            break;
        case FS_SQRT_RFE:
            /* Eliminate sqrt(remaining features) features at a time */
            rimanenti = features.examples_dim;
            for (i = 0; rimanenti > 1; i++) {

                compute_svm(&(svm_models[i]), features.nexamples, rimanenti,
                            features.value, features.class, svm_kernel, svm_kp,
                            svm_C, svm_tol, svm_eps, svm_maxloops, svm_verbose,
                            svm_W);

                wsquarenuovo = (double *)G_calloc(rimanenti, sizeof(double));

                for (j = 0; j < rimanenti; j++) {
                    wsquarenuovo[j] = svm_models[i].w[j] * svm_models[i].w[j];
                }

                if (fp_fs_w != NULL) {
                    fprintf(fp_fs_w, "%6.10f", wsquarenuovo[0]);
                    for (j = 1; j < rimanenti; j++) {
                        fprintf(fp_fs_w, "\t%6.10f", wsquarenuovo[j]);
                    }
                    fprintf(fp_fs_w, "\n");
                }

                posizwsquare = (int *)G_calloc(rimanenti, sizeof(int));

                indexx_1(rimanenti, wsquarenuovo, posizwsquare);

                neliminati = (int)floor(sqrt(rimanenti));

                vareliminate = (int *)G_calloc(neliminati, sizeof(int));

                vareliminatedouble =
                    (double *)G_calloc(neliminati, sizeof(double));

                for (j = 0; j < neliminati; j++) {
                    vareliminate[j] = posizwsquare[j];
                }

                for (j = 0; j < neliminati; j++) {
                    selected[rimanenti - j - 1] = names[vareliminate[j]];
                    vareliminatedouble[j] = (double)vareliminate[j];
                }

                shell(neliminati, vareliminatedouble);

                for (j = 0; j < neliminati; j++) {
                    vareliminate[j] = (int)vareliminatedouble[j];
                }

                for (j = 0; j < neliminati; j++) {
                    for (k = vareliminate[j]; k < (rimanenti - 1); k++) {
                        for (t = 0; t < features.nexamples; t++) {
                            features.value[t][k] = features.value[t][k + 1];
                        }
                        names[k] = names[k + 1];
                    }

                    for (k = j + 1; k < neliminati; k++) {
                        vareliminate[k]--;
                    }
                    rimanenti--;
                }

                G_free(wsquarenuovo);
                G_free(posizwsquare);
                G_free(vareliminate);
            }
            selected[0] = names[0];
            break;

        default:
            break;
        }
    }
    if (svm_kernel == SVM_KERNEL_GAUSSIAN) {

        H_tot = (double **)G_calloc(features.nexamples, sizeof(double *));
        for (j = 0; j < features.nexamples; j++) {
            H_tot[j] = (double *)G_calloc(features.nexamples, sizeof(double));
        }

        compute_H(H_tot, features.value, features.class, features.nexamples,
                  features.examples_dim, svm_kp);

        H_tmp = (double **)G_calloc(features.nexamples, sizeof(double *));

        for (j = 0; j < features.nexamples; j++) {
            H_tmp[j] = (double *)G_calloc(features.nexamples, sizeof(double));
        }

        switch (fs_type) {
        case FS_ONE_RFE:
            /*Non ricalcola gaussian */
            compute_svm(&svm, features.nexamples, features.examples_dim,
                        features.value, features.class, svm_kernel, svm_kp,
                        svm_C, svm_tol, svm_eps, svm_maxloops, svm_verbose,
                        svm_W);

            compute_valoriDJ(&svm, &features, H_tot, H_tmp, &valoriDJ);
            one_rfe_gauss(valoriDJ, names, selected, features.examples_dim,
                          fp_fs_w);
            free_svm(&svm);
            break;
        case FS_RFE:
            /*RFE gaussian */

            for (i = 0; i < (features.examples_dim - 1); i++) {
                compute_svm(&(svm_models[i]), features.nexamples,
                            (features.examples_dim - i), features.value,
                            features.class, svm_kernel, svm_kp, svm_C, svm_tol,
                            svm_eps, svm_maxloops, svm_verbose, svm_W);

                compute_valoriDJ(&(svm_models[i]), &features, H_tot, H_tmp,
                                 &valoriDJ);
                rfe_gauss(valoriDJ, &features, names, selected, i, H_tot, H_tmp,
                          svm_kp, fp_fs_w);
                G_free(valoriDJ);
                free_svm(&(svm_models[i]));
            }
            selected[0] = names[0];
            break;
        case FS_E_RFE:
            /*Entropy-based RFE gaussian */
            rimanenti = features.examples_dim;

            ncicli = 0;

            for (i = 0; rimanenti > fs_rfe; i++) {
                compute_svm(&(svm_models[i]), features.nexamples, rimanenti,
                            features.value, features.class, svm_kernel, svm_kp,
                            svm_C, svm_tol, svm_eps, svm_maxloops, svm_verbose,
                            svm_W);

                compute_valoriDJ(&(svm_models[i]), &features, H_tot, H_tmp,
                                 &valoriDJ);
                e_rfe_gauss(valoriDJ, &features, names, selected, i, H_tot,
                            H_tmp, &rimanenti, svm_kp, fp_fs_w, fp_fs_stats);

                G_free(valoriDJ);
                free_svm(&(svm_models[i]));
                ncicli++;
            }

            for (i = ncicli; rimanenti > 1; i++) {
                compute_svm(&(svm_models[i]), features.nexamples, rimanenti,
                            features.value, features.class, svm_kernel, svm_kp,
                            svm_C, svm_tol, svm_eps, svm_maxloops, svm_verbose,
                            svm_W);
                compute_valoriDJ(&(svm_models[i]), &features, H_tot, H_tmp,
                                 &valoriDJ);
                rfe_gauss(valoriDJ, &features, names, selected,
                          features.examples_dim - rimanenti, H_tot, H_tmp,
                          svm_kp, fp_fs_w);
                G_free(valoriDJ);
                free_svm(&(svm_models[i]));
                rimanenti--;
            }
            selected[0] = names[0];
            break;
        default:
            break;
        }
    }

    /*print output file containing the order of the relative importance */
    for (i = 0; i < features.examples_dim; i++) {
        fprintf(fp_fs_out, "%d\t%d\n", i + 1, selected[i]);
    }
    fclose(fp_fs_out);
    if (fs_type == FS_E_RFE)
        fclose(fp_fs_stats);
    if (flag_w->answer)
        fclose(fp_fs_w);

    return 0;
}
