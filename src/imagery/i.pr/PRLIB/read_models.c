/*
   The following routines are written and tested by Stefano Merler

   for

   loading different model types
 */

#include <grass/gis.h>
#include "global.h"
#include <stdlib.h>
#include <string.h>

static void read_bsvm();
static void read_btree();
static void read_tree();
static void read_svm();
static void read_gm();
static void read_nn();

int read_model(char *file, Features *features, NearestNeighbor *nn,
               GaussianMixture *gm, Tree *tree, SupportVectorMachine *svm,
               BTree *btree, BSupportVectorMachine *bsvm)

/*read a model from file and fill the structure according to the
   model type. Moreover load the features */
{
    int model_type;
    FILE *fp;
    char tempbuf[500];
    char *line = NULL;
    int i;

    fp = fopen(file, "r");
    if (fp == NULL) {
        sprintf(tempbuf, "read_model-> Can't open file %s for reading", file);
        G_fatal_error(tempbuf);
    }

    read_header_features(fp, features);

    /* scan model type */
    line = GetLine(fp);
    line = GetLine(fp);
    line = GetLine(fp);
    if (strcmp(line, "GaussianMixture") == 0) {
        model_type = GM_model;
    }
    else if (strcmp(line, "NearestNeighbor") == 0) {
        model_type = NN_model;
    }
    else if (strcmp(line, "ClassificationTree") == 0) {
        model_type = CT_model;
    }
    else if (strcmp(line, "SupportVectorMachine") == 0) {
        model_type = SVM_model;
    }
    else if (strcmp(line, "B-ClassificationTree") == 0) {
        model_type = BCT_model;
    }
    else if (strcmp(line, "B-SupportVectorMachine") == 0) {
        model_type = BSVM_model;
    }
    else {
        return 0;
    }

    /* read model */
    switch (model_type) {
    case NN_model:
        read_nn(fp, &nn);
        break;
    case GM_model:
        read_gm(fp, &gm);
        break;
    case CT_model:
        read_tree(fp, &tree);
        break;
    case SVM_model:
        read_svm(fp, &svm);
        break;
    case BCT_model:
        read_btree(fp, &btree);
        break;
    case BSVM_model:
        read_bsvm(fp, &bsvm);
        break;
    case 0:
        return 0;
        break;
    }

    if (features->f_pca[0]) {
        features->pca = (Pca *)G_calloc(features->f_pca[1], sizeof(Pca));

        line = GetLine(fp);
        line = GetLine(fp);
        line = GetLine(fp);
        sscanf(line, "%d", &(features->npc));

        for (i = 0; i < features->f_pca[1]; i++) {
            features->pca[i].n =
                features->training.rows * features->training.cols;
            read_pca(fp, &(features->pca[i]));
        }
    }

    fclose(fp);

    return model_type;
}

static void read_bsvm(FILE *fp, BSupportVectorMachine **bsvm)
{
    char *line = NULL;
    int i;
    SupportVectorMachine *tmp_svm;

    line = GetLine(fp);
    line = GetLine(fp);
    sscanf(line, "%lf", &((*bsvm)->w));
    line = GetLine(fp);
    line = GetLine(fp);
    sscanf(line, "%d", &((*bsvm)->nsvm));

    (*bsvm)->weights = (double *)G_calloc((*bsvm)->nsvm, sizeof(double));
    (*bsvm)->svm = (SupportVectorMachine *)G_calloc(
        (*bsvm)->nsvm, sizeof(SupportVectorMachine));

    line = GetLine(fp);
    line = GetLine(fp);
    for (i = 0; i < (*bsvm)->nsvm; i++) {
        sscanf(line, "%lf", &((*bsvm)->weights[i]));
        line = (char *)strchr(line, '\t');
        line++;
    }

    for (i = 0; i < (*bsvm)->nsvm; i++) {
        tmp_svm = &((*bsvm)->svm[i]);
        read_svm(fp, &tmp_svm);
    }
}

static void read_btree(FILE *fp, BTree **btree)
{
    char *line = NULL;
    int i;
    Tree *tmp_tree;

    line = GetLine(fp);
    line = GetLine(fp);
    sscanf(line, "%lf", &((*btree)->w));
    line = GetLine(fp);
    line = GetLine(fp);
    sscanf(line, "%d", &((*btree)->ntrees));

    (*btree)->weights = (double *)G_calloc((*btree)->ntrees, sizeof(double));
    (*btree)->tree = (Tree *)G_calloc((*btree)->ntrees, sizeof(Tree));

    line = GetLine(fp);
    line = GetLine(fp);
    for (i = 0; i < (*btree)->ntrees; i++) {
        sscanf(line, "%lf", &((*btree)->weights[i]));
        line = (char *)strchr(line, '\t');
        line++;
    }

    for (i = 0; i < (*btree)->ntrees; i++) {
        tmp_tree = &((*btree)->tree[i]);
        read_tree(fp, &tmp_tree);
    }
}

static void read_tree(FILE *fp, Tree **tree)
{
    char *line = NULL;
    int i, j;
    int nclasses;
    int nvar;

    line = GetLine(fp);
    line = GetLine(fp);
    sscanf(line, "%d", &((*tree)->nnodes));
    line = GetLine(fp);
    line = GetLine(fp);
    sscanf(line, "%d", &nclasses);
    line = GetLine(fp);
    line = GetLine(fp);
    sscanf(line, "%d", &nvar);

    (*tree)->node = (Node *)G_calloc((*tree)->nnodes, sizeof(Node));

    for (i = 0; i < (*tree)->nnodes; i++) {
        (*tree)->node[i].npoints_for_class =
            (int *)G_calloc(nclasses, sizeof(int));
        (*tree)->node[i].priors = (double *)G_calloc(nclasses, sizeof(double));
    }

    line = GetLine(fp);
    line = GetLine(fp);
    for (i = 0; i < (*tree)->nnodes; i++) {
        line = GetLine(fp);
        (*tree)->node[i].nclasses = nclasses;
        (*tree)->node[i].nvar = nvar;
        sscanf(line, "%d", &((*tree)->node[i].terminal));
        line = (char *)strchr(line, '\t');
        line++;
        sscanf(line, "%d", &((*tree)->node[i].npoints));
        line = (char *)strchr(line, '\t');
        line++;
        for (j = 0; j < nclasses; j++) {
            sscanf(line, "%d", &((*tree)->node[i].npoints_for_class[j]));
            line = (char *)strchr(line, '\t');
            line++;
        }
        for (j = 0; j < nclasses; j++) {
            sscanf(line, "%lf", &((*tree)->node[i].priors[j]));
            line = (char *)strchr(line, '\t');
            line++;
        }
        sscanf(line, "%d", &(*tree)->node[i].class);
        line = (char *)strchr(line, '\t');
        line++;
        if (!(*tree)->node[i].terminal) {
            sscanf(line, "%d", &((*tree)->node[i].left));
            line = (char *)strchr(line, '\t');
            line++;
            sscanf(line, "%d", &((*tree)->node[i].right));
            line = (char *)strchr(line, '\t');
            line++;
            sscanf(line, "%d", &((*tree)->node[i].var));
            line = (char *)strchr(line, '\t');
            line++;
            sscanf(line, "%lf", &((*tree)->node[i].value));
        }
    }
}

static void read_svm(FILE *fp, SupportVectorMachine **svm)
{
    char *line = NULL;
    int i, j;

    line = GetLine(fp);
    line = GetLine(fp);
    sscanf(line, "%d", &((*svm)->convergence));
    line = GetLine(fp);
    line = GetLine(fp);
    if (strcmp(line, "gaussian_kernel") == 0) {
        (*svm)->kernel_type = SVM_KERNEL_GAUSSIAN;
    }
    else if (strcmp(line, "linear_kernel") == 0) {
        (*svm)->kernel_type = SVM_KERNEL_LINEAR;
    }
    else {
        G_fatal_error("kernel not recognized\n");
    }

    line = GetLine(fp);
    line = GetLine(fp);
    sscanf(line, "%lf", &((*svm)->two_sigma_squared));
    line = GetLine(fp);
    line = GetLine(fp);
    sscanf(line, "%lf", &((*svm)->C));
    line = GetLine(fp);
    line = GetLine(fp);
    sscanf(line, "%lf", &((*svm)->cost));
    line = GetLine(fp);
    line = GetLine(fp);
    line = GetLine(fp);
    sscanf(line, "%lf%lf%d", &((*svm)->tolerance), &((*svm)->eps),
           &((*svm)->maxloops));
    line = GetLine(fp);
    line = GetLine(fp);
    sscanf(line, "%d", &((*svm)->N));
    line = GetLine(fp);
    line = GetLine(fp);
    sscanf(line, "%d", &((*svm)->d));
    line = GetLine(fp);
    line = GetLine(fp);
    sscanf(line, "%lf", &((*svm)->b));
    line = GetLine(fp);

    if ((*svm)->kernel_type == SVM_KERNEL_GAUSSIAN) {
        (*svm)->dense_points = (double **)G_calloc((*svm)->N, sizeof(double *));
        for (i = 0; i < (*svm)->N; i++) {
            (*svm)->dense_points[i] =
                (double *)G_calloc((*svm)->d, sizeof(double));
        }
        (*svm)->target = (int *)G_calloc((*svm)->N, sizeof(int));
        (*svm)->alph = (double *)G_calloc((*svm)->N, sizeof(double));

        for (i = 0; i < (*svm)->N; i++) {
            line = GetLine(fp);
            for (j = 0; j < (*svm)->d; j++) {
                sscanf(line, "%lf", &((*svm)->dense_points[i][j]));
                line = (char *)strchr(line, '\t');
                line++;
            }
            sscanf(line, "%d", &((*svm)->target[i]));
            line = (char *)strchr(line, '\t');
            line++;
            sscanf(line, "%lf", &((*svm)->alph[i]));
        }
    }
    if ((*svm)->kernel_type == SVM_KERNEL_LINEAR) {
        (*svm)->w = (double *)G_calloc((*svm)->d, sizeof(double));
        line = GetLine(fp);
        for (j = 0; j < (*svm)->d; j++) {
            sscanf(line, "%lf", &((*svm)->w[j]));
            line = (char *)strchr(line, '\t');
            line++;
        }
    }
}

static void read_gm(FILE *fp, GaussianMixture **gm)
{
    char *line = NULL;
    int i, j, k;

    line = GetLine(fp);
    line = GetLine(fp);
    sscanf(line, "%d", &((*gm)->nclasses));
    line = GetLine(fp);
    line = GetLine(fp);
    sscanf(line, "%d", &((*gm)->nvars));

    (*gm)->classes = (int *)G_calloc((*gm)->nclasses, sizeof(int));
    (*gm)->priors = (double *)G_calloc((*gm)->nclasses, sizeof(double));

    (*gm)->mean = (double **)G_calloc((*gm)->nclasses, sizeof(double *));
    for (i = 0; i < (*gm)->nclasses; i++)
        (*gm)->mean[i] = (double *)G_calloc((*gm)->nvars, sizeof(double));

    (*gm)->covar = (double ***)G_calloc((*gm)->nclasses, sizeof(double **));
    for (i = 0; i < (*gm)->nclasses; i++) {
        (*gm)->covar[i] = (double **)G_calloc((*gm)->nvars, sizeof(double *));
        for (j = 0; j < (*gm)->nvars; j++)
            (*gm)->covar[i][j] =
                (double *)G_calloc((*gm)->nvars, sizeof(double));
    }

    line = GetLine(fp);
    line = GetLine(fp);
    for (i = 0; i < (*gm)->nclasses; i++) {
        sscanf(line, "%d", &((*gm)->classes[i]));
        line = (char *)strchr(line, '\t');
        line++;
    }

    line = GetLine(fp);
    line = GetLine(fp);
    for (i = 0; i < (*gm)->nclasses; i++) {
        sscanf(line, "%lf", &((*gm)->priors[i]));
        line = (char *)strchr(line, '\t');
        line++;
    }

    for (i = 0; i < (*gm)->nclasses; i++) {
        line = GetLine(fp);
        line = GetLine(fp);
        line = GetLine(fp);
        for (j = 0; j < (*gm)->nvars; j++) {
            sscanf(line, "%lf", &((*gm)->mean[i][j]));
            line = (char *)strchr(line, '\t');
            line++;
        }
        line = GetLine(fp);
        for (k = 0; k < (*gm)->nvars; k++) {
            line = GetLine(fp);
            for (j = 0; j < (*gm)->nvars; j++) {
                sscanf(line, "%lf", &((*gm)->covar[i][k][j]));
                line = (char *)strchr(line, '\t');
                line++;
            }
        }
    }
}

static void read_nn(FILE *fp, NearestNeighbor **nn)
{
    char *line = NULL;
    int i, j;

    line = GetLine(fp);
    line = GetLine(fp);
    sscanf(line, "%d", &((*nn)->k));
    line = GetLine(fp);
    line = GetLine(fp);
    sscanf(line, "%d", &((*nn)->nsamples));
    line = GetLine(fp);
    line = GetLine(fp);
    sscanf(line, "%d", &((*nn)->nvars));

    (*nn)->data = (double **)G_calloc((*nn)->nsamples, sizeof(double *));
    for (i = 0; i < (*nn)->nsamples; i++)
        (*nn)->data[i] = (double *)G_calloc((*nn)->nvars, sizeof(double));

    (*nn)->class = (int *)G_calloc((*nn)->nsamples, sizeof(int));

    for (i = 0; i < (*nn)->nsamples; i++) {
        line = GetLine(fp);
        for (j = 0; j < (*nn)->nvars; j++) {
            sscanf(line, "%lf", &((*nn)->data[i][j]));
            line = (char *)strchr(line, '\t');
            line++;
        }
        sscanf(line, "%d", &((*nn)->class[i]));
    }
}
