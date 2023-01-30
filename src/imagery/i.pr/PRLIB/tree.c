/*
   The following routines are written and tested by Stefano Merler

   for

   structure Tree and BTree management
 */

#include <grass/gis.h>
#include "global.h"
#include <stdlib.h>
#include <string.h>
#include <math.h>

static void split_node();

void compute_tree(Tree *tree, int nsamples, int nvar, double **data,
                  int *data_class, int nclasses, int *classes, int stamps,
                  int minsize, double *costs)

/*
   receives in input training data of dimensions nsamples x nvar,
   with class labels data_class, the possible classes (of length nclasses)
   optionally, the user can build stamps
   and decide the minimal number of cases within a node as
   stopping criteria.
 */
{

    int i, j;
    int node_class_index;
    int max_node_points;
    int xx;
    double sumpriors;

    tree->stamps = stamps;
    tree->minsize = minsize;

    tree->node = (Node *)G_malloc(sizeof(Node));
    tree->node[0].nclasses = nclasses;

    tree->node[0].npoints = nsamples;
    tree->node[0].nvar = nvar;
    tree->node[0].data = data;
    tree->node[0].classes = data_class;

    tree->node[0].npoints_for_class = (int *)G_calloc(nclasses, sizeof(int));
    tree->node[0].priors = (double *)G_calloc(nclasses, sizeof(double));

    for (i = 0; i < tree->node[0].npoints; i++) {
        for (j = 0; j < nclasses; j++)
            if (classes[j] == tree->node[0].classes[i]) {
                tree->node[0].npoints_for_class[j] += 1;
                break;
            }
    }

    node_class_index = 0;
    max_node_points = 0;
    for (j = 0; j < nclasses; j++)
        if (tree->node[0].npoints_for_class[j] > max_node_points) {
            max_node_points = tree->node[0].npoints_for_class[j];
            node_class_index = j;
        }
    tree->node[0].class = classes[node_class_index];

    sumpriors = .0;
    for (j = 0; j < nclasses; j++)
        sumpriors += costs[j] * tree->node[0].npoints_for_class[j];
    for (j = 0; j < nclasses; j++)
        tree->node[0].priors[j] =
            costs[j] * tree->node[0].npoints_for_class[j] / sumpriors;

    tree->node[0].terminal = TRUE;
    if (entropy(tree->node[0].priors, nclasses) > 0)
        tree->node[0].terminal = FALSE;

    tree->nnodes = 1;
    for (xx = 0; xx < tree->nnodes; xx++)
        if (!tree->node[xx].terminal) {
            tree->node[xx].left = tree->nnodes;
            tree->node[xx].right = tree->nnodes + 1;
            tree->node = (Node *)G_realloc(tree->node,
                                           (tree->nnodes + 2) * sizeof(Node));
            split_node(&(tree->node[xx]), &(tree->node[tree->nnodes]),
                       &(tree->node[tree->nnodes + 1]), classes, nclasses,
                       costs);
            if (tree->minsize > 0) {
                if (tree->node[tree->nnodes].npoints < tree->minsize)
                    tree->node[tree->nnodes].terminal = TRUE;
                if (tree->node[tree->nnodes + 1].npoints < tree->minsize)
                    tree->node[tree->nnodes + 1].terminal = TRUE;
            }
            if (tree->stamps) {
                tree->node[tree->nnodes].terminal = TRUE;
                tree->node[tree->nnodes + 1].terminal = TRUE;
            }
            tree->nnodes += 2;
        }
}

static void split_node(Node *node, Node *nodeL, Node *nodeR, int *classes,
                       int nclasses, double *costs)
{
    int **indx;
    double *tmpvar;
    int i, j, k;
    int **npL, **npR;
    double **prL, **prR;
    int totL, totR;
    double a, b;
    double *decrease_in_inpurity;
    double max_decrease;
    int splitvar = 0;
    int splitvalue = 0;
    int morenumerous;
    double sumpriors;

    nodeL->priors = (double *)G_calloc(nclasses, sizeof(double));
    nodeR->priors = (double *)G_calloc(nclasses, sizeof(double));
    nodeL->npoints_for_class = (int *)G_calloc(nclasses, sizeof(int));
    nodeR->npoints_for_class = (int *)G_calloc(nclasses, sizeof(int));

    indx = (int **)G_calloc(node->nvar, sizeof(int *));
    for (i = 0; i < node->nvar; i++)
        indx[i] = (int *)G_calloc(node->npoints, sizeof(int));

    tmpvar = (double *)G_calloc(node->npoints, sizeof(double));
    decrease_in_inpurity =
        (double *)G_calloc(node->npoints - 1, sizeof(double));

    npL = (int **)G_calloc(node->npoints, sizeof(int *));
    for (i = 0; i < node->npoints; i++)
        npL[i] = (int *)G_calloc(nclasses, sizeof(int));
    npR = (int **)G_calloc(node->npoints, sizeof(int *));
    for (i = 0; i < node->npoints; i++)
        npR[i] = (int *)G_calloc(nclasses, sizeof(int));

    prL = (double **)G_calloc(node->npoints, sizeof(double *));
    for (i = 0; i < node->npoints; i++)
        prL[i] = (double *)G_calloc(nclasses, sizeof(double));
    prR = (double **)G_calloc(node->npoints, sizeof(double *));
    for (i = 0; i < node->npoints; i++)
        prR[i] = (double *)G_calloc(nclasses, sizeof(double));

    for (i = 0; i < node->nvar; i++) {
        for (j = 0; j < node->npoints; j++)
            tmpvar[j] = node->data[j][i];

        indexx_1(node->npoints, tmpvar, indx[i]);

        for (k = 0; k < nclasses; k++)
            if (node->classes[indx[i][0]] == classes[k]) {
                npL[0][k] = 1;
                npR[0][k] = node->npoints_for_class[k] - npL[0][k];
            }
            else {
                npL[0][k] = 0;
                npR[0][k] = node->npoints_for_class[k];
            }

        for (j = 1; j < node->npoints - 1; j++)
            for (k = 0; k < nclasses; k++)
                if (node->classes[indx[i][j]] == classes[k]) {
                    npL[j][k] = npL[j - 1][k] + 1;
                    npR[j][k] = node->npoints_for_class[k] - npL[j][k];
                }
                else {
                    npL[j][k] = npL[j - 1][k];
                    npR[j][k] = node->npoints_for_class[k] - npL[j][k];
                }

        for (j = 0; j < node->npoints - 1; j++) {
            totL = totR = 0;
            for (k = 0; k < nclasses; k++)
                totL += (double)npL[j][k];

            sumpriors = 0.;
            for (k = 0; k < nclasses; k++)
                sumpriors += costs[k] * npL[j][k];
            for (k = 0; k < nclasses; k++)
                prL[j][k] = costs[k] * npL[j][k] / sumpriors;

            for (k = 0; k < nclasses; k++)
                totR += (double)npR[j][k];

            sumpriors = 0.;
            for (k = 0; k < nclasses; k++)
                sumpriors += costs[k] * npR[j][k];
            for (k = 0; k < nclasses; k++)
                prR[j][k] = costs[k] * npR[j][k] / sumpriors;

            a = (double)totL / (double)node->npoints;
            b = (double)totR / (double)node->npoints;

            decrease_in_inpurity[j] = entropy(node->priors, nclasses) -
                                      a * entropy(prL[j], nclasses) -
                                      b * entropy(prR[j], nclasses);
        }

        if (i == 0) {
            splitvar = 0;
            splitvalue = 0;
            max_decrease = decrease_in_inpurity[0];

            for (k = 0; k < nclasses; k++)
                nodeL->priors[k] = prL[splitvalue][k];
            for (k = 0; k < nclasses; k++)
                nodeR->priors[k] = prR[splitvalue][k];

            for (k = 0; k < nclasses; k++)
                nodeL->npoints_for_class[k] = npL[splitvalue][k];
            for (k = 0; k < nclasses; k++)
                nodeR->npoints_for_class[k] = npR[splitvalue][k];
        }

        for (j = 0; j < node->npoints - 1; j++)
            if (decrease_in_inpurity[j] > max_decrease) {
                max_decrease = decrease_in_inpurity[j];

                splitvar = i;
                splitvalue = j;

                for (k = 0; k < nclasses; k++)
                    nodeL->priors[k] = prL[splitvalue][k];
                for (k = 0; k < nclasses; k++)
                    nodeR->priors[k] = prR[splitvalue][k];

                for (k = 0; k < nclasses; k++)
                    nodeL->npoints_for_class[k] = npL[splitvalue][k];
                for (k = 0; k < nclasses; k++)
                    nodeR->npoints_for_class[k] = npR[splitvalue][k];
            }
    }

    if (splitvar < 0 && splitvalue < 0) {
        node->value = 0;
        node->terminal = TRUE;
        nodeL->nclasses = node->nclasses;
        nodeL->npoints = 0;
        nodeL->terminal = TRUE;
        nodeL->class = -9999;
        nodeR->nclasses = node->nclasses;
        nodeR->npoints = 0;
        nodeR->terminal = TRUE;
        nodeR->class = -9999;
        return;
    }

    node->var = splitvar;
    node->value = (node->data[indx[splitvar][splitvalue]][node->var] +
                   node->data[indx[splitvar][splitvalue + 1]][node->var]) /
                  2.;

    nodeL->nvar = node->nvar;
    nodeL->nclasses = node->nclasses;
    nodeL->npoints = splitvalue + 1;

    nodeL->terminal = TRUE;
    if (entropy(nodeL->priors, nclasses) > 0)
        nodeL->terminal = FALSE;

    nodeL->data = (double **)G_calloc(nodeL->npoints, sizeof(double *));
    nodeL->classes = (int *)G_calloc(nodeL->npoints, sizeof(int));

    for (i = 0; i < nodeL->npoints; i++) {
        nodeL->data[i] = node->data[indx[splitvar][i]];
        nodeL->classes[i] = node->classes[indx[splitvar][i]];
    }

    morenumerous = 0;
    for (k = 0; k < nclasses; k++)
        if (nodeL->npoints_for_class[k] > morenumerous) {
            morenumerous = nodeL->npoints_for_class[k];
            nodeL->class = classes[k];
        }

    nodeR->nvar = node->nvar;
    nodeR->nclasses = node->nclasses;
    nodeR->npoints = node->npoints - nodeL->npoints;

    nodeR->terminal = TRUE;
    if (entropy(nodeR->priors, nclasses) > 0)
        nodeR->terminal = FALSE;

    nodeR->data = (double **)G_calloc(nodeR->npoints, sizeof(double *));
    nodeR->classes = (int *)G_calloc(nodeR->npoints, sizeof(int));

    for (i = 0; i < nodeR->npoints; i++) {
        nodeR->data[i] = node->data[indx[splitvar][nodeL->npoints + i]];
        nodeR->classes[i] = node->classes[indx[splitvar][nodeL->npoints + i]];
    }

    morenumerous = 0;
    for (k = 0; k < nclasses; k++)
        if (nodeR->npoints_for_class[k] > morenumerous) {
            morenumerous = nodeR->npoints_for_class[k];
            nodeR->class = classes[k];
        }

    for (i = 0; i < node->nvar; i++)
        G_free(indx[i]);
    G_free(indx);

    for (i = 0; i < node->npoints; i++)
        G_free(npL[i]);
    G_free(npL);
    for (i = 0; i < node->npoints; i++)
        G_free(npR[i]);
    G_free(npR);

    for (i = 0; i < node->npoints; i++)
        G_free(prL[i]);
    G_free(prL);
    for (i = 0; i < node->npoints; i++)
        G_free(prR[i]);
    G_free(prR);

    G_free(tmpvar);
    G_free(decrease_in_inpurity);
}

void write_tree(char *file, Tree *tree, Features *features)

/*
   write a tree model to a file
 */
{
    int i, j;
    FILE *fp;
    char tempbuf[500];

    fp = fopen(file, "w");
    if (fp == NULL) {
        sprintf(tempbuf, "write_tree-> Can't open file %s for writing", file);
        G_fatal_error(tempbuf);
    }

    write_header_features(fp, features);
    fprintf(fp, "#####################\n");
    fprintf(fp, "MODEL:\n");
    fprintf(fp, "#####################\n");
    fprintf(fp, "Model:\n");
    fprintf(fp, "ClassificationTree\n");
    fprintf(fp, "Number of nodes:\n");
    fprintf(fp, "%d\n", tree->nnodes);
    fprintf(fp, "Number of classes:\n");
    fprintf(fp, "%d\n", tree->node[0].nclasses);
    fprintf(fp, "Number of features:\n");
    fprintf(fp, "%d\n\n", tree->node[0].nvar);
    fprintf(fp, "Tree structure:\n");
    fprintf(fp, "terminal\tndata\t");
    for (j = 0; j < tree->node[0].nclasses; j++)
        fprintf(fp, "data_cl%d\t", j + 1);
    for (j = 0; j < tree->node[0].nclasses; j++)
        fprintf(fp, "prior_cl%d\t", j + 1);
    fprintf(fp,
            "class\tchild_left\tchild_right\tsplit_variable\tsplit_value\n");
    for (i = 0; i < tree->nnodes; i++) {
        fprintf(fp, "%d\t%d\t", tree->node[i].terminal, tree->node[i].npoints);
        for (j = 0; j < tree->node[i].nclasses; j++)
            fprintf(fp, "%d\t", tree->node[i].npoints_for_class[j]);
        for (j = 0; j < tree->node[i].nclasses; j++)
            fprintf(fp, "%f\t", tree->node[i].priors[j]);
        if (tree->node[i].terminal)
            fprintf(fp, "%d\n", tree->node[i].class);
        else
            fprintf(fp, "%d\t%d\t%d\t%d\t%f\n", tree->node[i].class,
                    tree->node[i].left, tree->node[i].right, tree->node[i].var,
                    tree->node[i].value);
    }
    if (features->f_pca[0]) {
        fprintf(fp, "#####################\n");
        fprintf(fp, "PRINC. COMP.:\n");
        fprintf(fp, "#####################\n");
        fprintf(fp, "Number of pc:\n");
        fprintf(fp, "%d\n", features->npc);

        for (i = 0; i < features->f_pca[1]; i++) {
            fprintf(fp, "PCA: Layer %d\n", i + 1);
            write_pca(fp, &(features->pca[i]));
        }
    }

    fclose(fp);
}

void compute_tree_boosting(BTree *btree, int boosting, double w, int nsamples,
                           int nvar, double **data, int *data_class,
                           int nclasses, int *classes, int stamps, int minsize,
                           int weights_boosting, double *costs)

/*
   receives in input training data of dimensions nsamples x nvar,
   with class labels data_class, the possible classes (of length nclasses)
   and computes a boosting tree model (number of models = boosting) using w

   optionally, the user can build stamps and decide the
   minimal number of cases within a node as stopping criteria.
 */
{
    int i, b;
    int *bsamples;
    double **xdata_training;
    int *xclasses_training;
    double *prob;
    double e00, e01, e10, e11, prior0, prior1;
    int *error;
    double eps, totprob;
    double totbeta;

    if (weights_boosting == 1) {
        btree->w_evolution = (double **)G_calloc(nsamples, sizeof(double *));
        for (i = 0; i < nsamples; i++)
            btree->w_evolution[i] =
                (double *)G_calloc(boosting + 3, sizeof(double));
    }

    btree->tree = (Tree *)G_calloc(boosting, sizeof(Tree));
    btree->ntrees = boosting;
    btree->weights = (double *)G_calloc(btree->ntrees, sizeof(double));
    btree->w = w;

    prob = (double *)G_calloc(nsamples, sizeof(double));
    bsamples = (int *)G_calloc(nsamples, sizeof(int));
    xdata_training = (double **)G_calloc(nsamples, sizeof(double *));
    xclasses_training = (int *)G_calloc(nsamples, sizeof(int));
    error = (int *)G_calloc(nsamples, sizeof(int));

    for (i = 0; i < nsamples; i++) {
        prob[i] = 1.0 / nsamples;
    }

    for (b = 0; b < btree->ntrees; b++) {
        if (weights_boosting == 1)
            for (i = 0; i < nsamples; i++)
                btree->w_evolution[i][b] = prob[i];

        Bootsamples(nsamples, prob, bsamples);
        /* QUESTA PARTE SERVE PER VEDERE GLI ESTRATTI
           AD OGNI RIPETIZIONE: AL MOMENTO LA DISABILITO,
           AGGIUNGERE OPZIONE NEL MAIN DI i.pr_model PER ATTIVARLA
           {
           int out,j;

           out=0;
           for(j=0;j<nsamples;j++)
           if(bsamples[j]==0){
           out=1;
           break;
           }
           fprintf(stderr,"%d",out);

           for(i=1;i<nsamples;i++){
           out=0;
           for(j=0;j<nsamples;j++)
           if(bsamples[j]==i){
           out=1;
           break;
           }
           fprintf(stderr,"\t%d",out);
           }
           fprintf(stderr,"\n");
           }
         */
        for (i = 0; i < nsamples; i++) {
            xdata_training[i] = data[bsamples[i]];
            xclasses_training[i] = data_class[bsamples[i]];
        }
        compute_tree(&(btree->tree[b]), nsamples, nvar, xdata_training,
                     xclasses_training, nclasses, classes, stamps, minsize,
                     costs);

        e00 = e01 = e10 = e11 = prior0 = prior1 = 0.0;
        for (i = 0; i < nsamples; i++) {
            if (data_class[i] == classes[0]) {
                if (predict_tree_multiclass(&(btree->tree[b]), data[i]) !=
                    data_class[i]) {
                    error[i] = TRUE;
                    e01 += prob[i];
                }
                else {
                    error[i] = FALSE;
                    e00 += prob[i];
                }
                prior0 += prob[i];
            }
            else {
                if (predict_tree_multiclass(&(btree->tree[b]), data[i]) !=
                    data_class[i]) {
                    error[i] = TRUE;
                    e10 += prob[i];
                }
                else {
                    error[i] = FALSE;
                    e11 += prob[i];
                }
                prior1 += prob[i];
            }
        }
        eps = (1.0 - e00 / (e00 + e01)) * prior0 * btree->w +
              (1.0 - e11 / (e10 + e11)) * prior1 * (2.0 - btree->w);
        if (eps > 0.0 && eps < 0.5) {
            btree->weights[b] = 0.5 * log((1.0 - eps) / eps);
            totprob = 0.0;
            for (i = 0; i < nsamples; i++) {
                if (error[i]) {
                    if (data_class[i] == classes[0]) {
                        prob[i] = prob[i] * exp(btree->weights[b] * btree->w);
                    }
                    else {
                        prob[i] =
                            prob[i] * exp(btree->weights[b] * (2.0 - btree->w));
                    }
                }
                else {
                    if (data_class[i] == classes[0]) {
                        prob[i] = prob[i] *
                                  exp(-btree->weights[b] * (2.0 - btree->w));
                    }
                    else {
                        prob[i] = prob[i] * exp(-btree->weights[b] * btree->w);
                    }
                }
                totprob += prob[i];
            }
            for (i = 0; i < nsamples; i++) {
                prob[i] /= totprob;
            }
        }
        else {
            btree->weights[b] = 0.0;
            for (i = 0; i < nsamples; i++) {
                prob[i] = 1.0 / nsamples;
            }
        }
    }

    totbeta = 0.0;
    for (b = 0; b < btree->ntrees; b++) {
        totbeta += btree->weights[b];
    }
    if (totbeta > 0) {
        for (b = 0; b < btree->ntrees; b++) {
            btree->weights[b] /= totbeta;
        }
    }
    else {
        fprintf(stderr, "WARNING: weights all null, set to 1/nmodels\n");
        for (b = 0; b < btree->ntrees; b++) {
            btree->weights[b] = 1. / btree->ntrees;
        }
    }

    G_free(bsamples);
    G_free(xclasses_training);
    G_free(prob);
    G_free(error);
    G_free(xdata_training);
}

/*########################Regularized adaboost################################
 */
/*        The following routines are written and tested by Mauro Martinelli */
void compute_tree_boosting_reg(BTree *btree, int boosting, double w,
                               int nsamples, int nvar, double **data,
                               int *data_class, int nclasses, int *classes,
                               int stamps, int minsize, int weights_boosting,
                               double *costs, double *misratio)

/*
   receives in input training data of dimensions nsamples x nvar,
   with class labels data_class, the possible classes (of length nclasses)
   and computes a boosting tree model (number of models = boosting) using w

   optionally, the user can build stamps and decide the
   minimal number of cases within a node as stopping criteria.
   It calculates the misclassification ratio for every training data.

 */
{
    int i, b, j;
    int *bsamples;
    double **xdata_training;
    int *xclasses_training;
    double *prob;
    double e00, e01, e10, e11, prior0, prior1;
    int *error;
    double eps, totprob;
    double totbeta;
    double *mis;
    double *notextracted;
    int *extracted;

    if (weights_boosting == 1) {
        btree->w_evolution = (double **)G_calloc(nsamples, sizeof(double *));
        for (i = 0; i < nsamples; i++)
            btree->w_evolution[i] =
                (double *)G_calloc(boosting + 3, sizeof(double));
    }

    btree->tree = (Tree *)G_calloc(boosting, sizeof(Tree));
    btree->ntrees = boosting;
    btree->weights = (double *)G_calloc(btree->ntrees, sizeof(double));
    btree->w = w;

    notextracted = (double *)G_calloc(nsamples, sizeof(double));
    extracted = (int *)G_calloc(nsamples, sizeof(int));
    mis = (double *)G_calloc(nsamples, sizeof(double));
    prob = (double *)G_calloc(nsamples, sizeof(double));
    bsamples = (int *)G_calloc(nsamples, sizeof(int));
    xdata_training = (double **)G_calloc(nsamples, sizeof(double *));
    xclasses_training = (int *)G_calloc(nsamples, sizeof(int));
    error = (int *)G_calloc(nsamples, sizeof(int));

    for (i = 0; i < nsamples; i++) {
        prob[i] = 1.0 / nsamples;
    }

    for (b = 0; b < btree->ntrees; b++) {
        if (weights_boosting == 1)
            for (i = 0; i < nsamples; i++)
                btree->w_evolution[i][b] = prob[i];

        Bootsamples(nsamples, prob, bsamples);
        for (i = 0; i < nsamples; i++) {
            xdata_training[i] = data[bsamples[i]];
            xclasses_training[i] = data_class[bsamples[i]];
        }
        compute_tree(&(btree->tree[b]), nsamples, nvar, xdata_training,
                     xclasses_training, nclasses, classes, stamps, minsize,
                     costs);

        e00 = e01 = e10 = e11 = prior0 = prior1 = 0.0;
        for (i = 0; i < nsamples; i++) {
            if (data_class[i] == classes[0]) {
                if (predict_tree_multiclass(&(btree->tree[b]), data[i]) !=
                    data_class[i]) {
                    error[i] = TRUE;
                    e01 += prob[i];
                }
                else {
                    error[i] = FALSE;
                    e00 += prob[i];
                }
                prior0 += prob[i];
            }
            else {
                if (predict_tree_multiclass(&(btree->tree[b]), data[i]) !=
                    data_class[i]) {
                    error[i] = TRUE;
                    e10 += prob[i];
                }
                else {
                    error[i] = FALSE;
                    e11 += prob[i];
                }
                prior1 += prob[i];
            }
        }
        eps = (1.0 - e00 / (e00 + e01)) * prior0 * btree->w +
              (1.0 - e11 / (e10 + e11)) * prior1 * (2.0 - btree->w);
        if (eps > 0.0 && eps < 0.5) {
            btree->weights[b] = 0.5 * log((1.0 - eps) / eps);
            totprob = 0.0;
            for (i = 0; i < nsamples; i++) {
                if (error[i]) {
                    if (data_class[i] == classes[0]) {
                        prob[i] = prob[i] * exp(btree->weights[b] * btree->w);
                    }
                    else {
                        prob[i] =
                            prob[i] * exp(btree->weights[b] * (2.0 - btree->w));
                    }
                }
                else {
                    if (data_class[i] == classes[0]) {
                        prob[i] = prob[i] *
                                  exp(-btree->weights[b] * (2.0 - btree->w));
                    }
                    else {
                        prob[i] = prob[i] * exp(-btree->weights[b] * btree->w);
                    }
                }
                totprob += prob[i];
            }
            for (i = 0; i < nsamples; i++) {
                prob[i] /= totprob;
            }
        }
        else {
            btree->weights[b] = 0.0;
            for (i = 0; i < nsamples; i++) {
                prob[i] = 1.0 / nsamples;
            }
        }
        /*Misclassification ratio */
        for (i = 0; i < nsamples; i++) {
            extracted[i] = 0;
            for (j = 0; j < nsamples; j++) {
                if (bsamples[j] == i) {
                    extracted[i] = 1;
                    break;
                }
            }
            if (extracted[i] == 0) {
                notextracted[i] += 1;
                if (error[i] == TRUE)
                    mis[i] += 1;
            }
        }
    }

    for (i = 0; i < nsamples; i++) {

        if (notextracted[i] == 0) {
            misratio[i] = 0;
            fprintf(stdout, "WARNING: the point %d is always extracted\n", i);
        }
        else {
            misratio[i] = mis[i] / notextracted[i];
        }
    }

    totbeta = 0.0;
    for (b = 0; b < btree->ntrees; b++) {
        totbeta += btree->weights[b];
    }
    if (totbeta > 0) {
        for (b = 0; b < btree->ntrees; b++) {
            btree->weights[b] /= totbeta;
        }
    }
    else {
        fprintf(stderr, "WARNING: weights all null, set to 1/nmodels\n");
        for (b = 0; b < btree->ntrees; b++) {
            btree->weights[b] = 1. / btree->ntrees;
        }
    }

    G_free(bsamples);
    G_free(xclasses_training);
    G_free(prob);
    G_free(error);
    G_free(xdata_training);
    G_free(mis);
    G_free(notextracted);
    G_free(extracted);
}

void regularized_boosting(int boosting, double w, int nsamples, int nvar,
                          double **data, int *data_class, int nclasses,
                          int *classes, int stamps, int minsize,
                          int weights_boosting, double *costs, double *misratio,
                          int reg, Features test_features, char *file,
                          Features validation_features, int reg_verbose,
                          char nametest[150], char nameval[150],
                          char modelout[150], Features train_features,
                          int testset)

/*
   compute btree model on the new trainng set extracted, test the btree model on
   the validation set and it calculates the best tree model. Write into the
   output file the best tree model.
 */
{
    BTree *btree;
    int i, j, k, run, t, z;
    double **xdata_training;
    int *xclasses_training;
    int *ncampioni;
    double r, regd, bestr;
    double *accuracy;
    double *toterror;
    double bestaccuracy;
    int vet;
    char testtrain[150];

    fprintf(stdout, "-----------------------------------\n");
    fprintf(stdout, "Training and prediction on validation data: %s\n",
            nameval);
    if (reg_verbose > 1) {
        fprintf(stdout,
                "Class of validation features (regularized boosting):%d\n",
                validation_features.nclasses);
        fprintf(stdout,
                "Interval number of misclassification ratio (regularized "
                "boosting):%d\n",
                reg);
        fprintf(stdout, "-----------------------------------\n");
    }

    btree = (BTree *)G_calloc(reg, sizeof(BTree));
    ncampioni = (int *)G_calloc(reg, sizeof(int));
    accuracy = (double *)G_calloc(reg, sizeof(double));
    toterror = (double *)G_calloc(reg, sizeof(double));

    xclasses_training = (int *)G_calloc(nsamples, sizeof(int));
    xdata_training = (double **)G_calloc(nsamples, sizeof(double *));
    for (k = 0; k < nsamples; k++) {
        xdata_training[k] = (double *)G_calloc(nvar, sizeof(double));
    }

    bestaccuracy = 0.0;
    r = 0;
    run = 0;
    bestr = 0;

    /*for each 'r' it's creating the new training set */
    for (i = 0; i < reg; i++) {
        regd = reg;
        r = (1 - (i * (1 / regd)));

        ncampioni[i] = 0;
        for (j = 0; j < nsamples; j++) {
            if (misratio[j] <= r)
                ncampioni[i] = ncampioni[i] + 1;
        }
        if ((i == 0) || ((ncampioni[i]) != (ncampioni[i - 1]))) {

            if (ncampioni[i] < 11) {
                if (reg_verbose > 1) {
                    fprintf(stdout,
                            "WARNING:at run %d the training set is too small\n",
                            i);
                }
                break;
            }
            else {
                if (reg_verbose > 1) {
                    fprintf(stdout,
                            "%d samples extracted at run %d and 'r' is: %e\n",
                            ncampioni[i], i, r);
                }
                vet = 0;
                for (j = 0; j < nsamples; j++) {
                    if (misratio[j] <= r) {
                        xdata_training[vet] = data[j];
                        xclasses_training[vet] = data_class[j];
                        vet = vet + 1;
                    }
                }

                compute_tree_boosting(&btree[i], boosting, w, ncampioni[i],
                                      nvar, xdata_training, xclasses_training,
                                      nclasses, classes, stamps, minsize,
                                      weights_boosting, costs);
                accuracy[i] =
                    test_regularized_boosting(&btree[i], &validation_features);

                if (reg_verbose == 1) {
                    toterror[i] = 1 - accuracy[i];
                    fprintf(stdout, "%e\t%e\n", r, toterror[i]);
                }

                if (reg_verbose > 1) {
                    fprintf(stdout, "Accuracy at run :%d is :%e\n", i,
                            accuracy[i]);
                    fprintf(stdout, "-----------------------------------\n");
                }

                if (accuracy[i] > bestaccuracy) {
                    bestaccuracy = accuracy[i];
                    run = i;
                    bestr = r;
                }
                else {
                    for (t = 0; t < btree[i].ntrees; t++) {
                        for (z = 0; z < btree[i].tree[t].nnodes; z++) {
                            G_free(btree[i].tree[t].node[z].priors);
                            G_free(btree[i].tree[t].node[z].npoints_for_class);
                        }

                        G_free(btree[i].tree[t].node);
                    }
                    G_free(btree[i].tree);
                    G_free(btree[i].weights);
                }
            }
        }
    }
    fprintf(stdout,
            "Best accuracy on the validation feautres= %e at run :%d (r= %e)\n",
            bestaccuracy, run, bestr);
    fprintf(stdout, "-----------------------------------\n");

    if (reg_verbose > 0) {
        sprintf(testtrain, "%s_tr_predshaved", modelout);

        fprintf(stdout, "Prediction on training data after shave:\n");
        test_btree(&btree[run], &train_features, testtrain);
        fprintf(stdout, "-----------------------------------\n");
    }

    if (testset == 1) {

        fprintf(stdout,
                "Test the standard tree model ('r'=1) on test data: %s\n",
                nametest);
        test_btree(&btree[0], &test_features, file);
        fprintf(stdout, "Test the best tree model on test data: %s\n",
                nametest);
        test_btree(&btree[run], &test_features, file);
    }

    fprintf(stdout, "Output file: %s\n", modelout);
    write_bagging_boosting_tree(modelout, &btree[run], &train_features);

    G_free(ncampioni);
    G_free(accuracy);
    G_free(xdata_training);
    G_free(xclasses_training);
}

double test_regularized_boosting(BTree *btree, Features *features)

/*
   test a btree model on a reduced set of original data
   (features) and return the accuracy of the btree model
 */
{
    int i, j;
    int *data_in_each_class;
    int predI;
    double predD;
    double accuracy;

    data_in_each_class = (int *)G_calloc(features->nclasses, sizeof(int));

    accuracy = 0.0;
    for (i = 0; i < features->nexamples; i++) {
        for (j = 0; j < features->nclasses; j++) {
            if (features->class[i] == features->p_classes[j]) {
                data_in_each_class[j] += 1;
                if (features->nclasses == 2) {
                    if ((predD =
                             predict_btree_2class(btree, features->value[i])) *
                            features->class[i] <=
                        0) {
                        accuracy += 1.0;
                    }
                }
                else {
                    if ((predI = predict_btree_multiclass(
                             btree, features->value[i], features->nclasses,
                             features->p_classes)) != features->class[i]) {
                        accuracy += 1.0;
                    }
                }
                break;
            }
        }
    }

    accuracy /= features->nexamples;
    accuracy = 1.0 - accuracy;

    G_free(data_in_each_class);
    return accuracy;
}

void test_btree_reg(BTree *btree, Features *features, char *file,
                    double *misratio)

/*
   test a btree model on a set of data
   (features) and write the results into a file. To standard output
   accuracy and error on each class
 */
{
    int i, j;
    int *data_in_each_class;
    FILE *fp;
    int predI;
    double predD;
    double *error;
    double accuracy;

    fp = fopen(file, "w");
    if (fp == NULL) {
        fprintf(stderr, "test_btree_reg-> Can't open file %s for writing",
                file);
        exit(-1);
    }
    data_in_each_class = (int *)G_calloc(features->nclasses, sizeof(int));
    error = (double *)G_calloc(features->nclasses, sizeof(double));

    accuracy = 0.0;
    for (i = 0; i < features->nexamples; i++) {
        if (features->examples_dim <
            3) { /*if examples_dim is small it's printing the training feature
                    on the outpu file */
            for (j = 0; j < features->examples_dim; j++) {
                fprintf(fp, "%e\t", features->value[i][j]);
            }
        }
        for (j = 0; j < features->nclasses; j++) {
            if (features->class[i] == features->p_classes[j]) {
                data_in_each_class[j] += 1;
                if (features->nclasses == 2) {
                    if ((predD =
                             predict_btree_2class(btree, features->value[i])) *
                            features->class[i] <=
                        0) {
                        error[j] += 1.0;
                        accuracy += 1.0;
                    }
                    fprintf(fp, "%d\t%f", features->class[i], predD);
                }
                else {
                    if ((predI = predict_btree_multiclass(
                             btree, features->value[i], features->nclasses,
                             features->p_classes)) != features->class[i]) {
                        error[j] += 1.0;
                        accuracy += 1.0;
                    }
                    fprintf(fp, "%d\t%d", features->class[i], predI);
                }
                break;
            }
        }
        fprintf(fp, "\t%e\n", misratio[i]);
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

void shaving_and_compute(int boosting, double w, int nsamples, int nvar,
                         double **data, int *data_class, int nclasses,
                         int *classes, int stamps, int minsize,
                         int weights_boosting, double *costs, double *misratio,
                         int reg_verbose, double misclass_ratio, char *outfile,
                         char modello[150], Features features,
                         Features test_features, char *outfile1, int testfile)

/*
   compute btree model on the shaved trainng set, test and write into the output
   file the tree model
 */
{
    BTree btree;
    int j, k, n, t;
    double **xdata_training;
    int *xclasses_training;
    int ncampioni;
    int vet, ind;
    int *shaved;
    int nshaved;

    fprintf(stdout, "-----------------------------------\n");

    if (reg_verbose > 0) {
        fprintf(stdout,
                "Max misclassification ratio on the new training "
                "set(regularized boosting):%f\n",
                misclass_ratio);
        fprintf(stdout, "-----------------------------------\n");
    }

    xclasses_training = (int *)G_calloc(nsamples, sizeof(int));
    xdata_training = (double **)G_calloc(nsamples, sizeof(double *));
    for (k = 0; k < nsamples; k++) {
        xdata_training[k] = (double *)G_calloc(nvar, sizeof(double));
    }

    ind = 0;
    vet = 0;
    ncampioni = 0;
    for (j = 0; j < nsamples; j++) {
        if (misratio[j] <= misclass_ratio)
            ncampioni++;
    }

    nshaved = nsamples - ncampioni;
    shaved = (int *)G_calloc(nshaved, sizeof(int));

    if (ncampioni < 11) {
        if (reg_verbose > 0) {
            fprintf(stdout, "WARNING:the training set is too small\n");
        }
        exit(1);
    }
    else {
        if (reg_verbose > 0) {
            fprintf(stdout, "%d samples extracted \n", ncampioni);
        }
        for (j = 0; j < nsamples; j++) {
            if (misratio[j] <= misclass_ratio) {
                for (n = 0; n < nvar; n++) {
                    xdata_training[vet][n] = data[j][n];
                }
                xclasses_training[vet] = data_class[j];
                vet = vet + 1;
            }
            else {
                shaved[ind] = j;
                ind = ind + 1;
            }
        }
        compute_tree_boosting(&btree, boosting, w, ncampioni, nvar,
                              xdata_training, xclasses_training, nclasses,
                              classes, stamps, minsize, weights_boosting,
                              costs);
    }
    if (reg_verbose > 0) {
        fprintf(stdout, "shaved %d samples :\n", nshaved);
        for (t = 0; t < nshaved; t++) {
            fprintf(stdout, "%d\n", shaved[t]);
        }
        fprintf(stdout, "-----------------------------------\n");
    }

    fprintf(stdout, "Prediction on training data \n");
    test_btree(&btree, &features, outfile);

    fprintf(stdout, "-----------------------------------\n");

    if (testfile == 1) {
        fprintf(stdout, "Prediction on test data \n");
        test_btree(&btree, &test_features, outfile1);
    }

    fprintf(stdout, "Output model: %s\n", modello);
    write_bagging_boosting_tree(modello, &btree, &features);

    G_free(xdata_training);
    G_free(xclasses_training);
    G_free(shaved);
}

/*############################################################################################
 */

void compute_tree_bagging(BTree *btree, int bagging, int nsamples, int nvar,
                          double **data, int *data_class, int nclasses,
                          int *classes, int stamps, int minsize, double *costs)

/*
   receives in input training data of dimensions nsamples x nvar,
   with class labels data_class, the possible classes (of length nclasses)

   optionally, the user can build stamps and decide the
   minimal number of cases within a node as stopping criteria.
 */
{
    int i, b;
    int *bsamples;
    double **xdata_training;
    int *xclasses_training;
    double *prob;

    btree->tree = (Tree *)G_calloc(bagging, sizeof(Tree));
    btree->ntrees = bagging;
    btree->weights = (double *)G_calloc(btree->ntrees, sizeof(double));
    btree->w = -1.0;

    for (b = 0; b < btree->ntrees; b++) {
        btree->weights[b] = 1.0 / btree->ntrees;
    }

    prob = (double *)G_calloc(nsamples, sizeof(double));
    bsamples = (int *)G_calloc(nsamples, sizeof(int));
    xdata_training = (double **)G_calloc(nsamples, sizeof(double *));
    xclasses_training = (int *)G_calloc(nsamples, sizeof(int));

    for (i = 0; i < nsamples; i++) {
        prob[i] = 1.0 / nsamples;
    }

    for (b = 0; b < btree->ntrees; b++) {
        Bootsamples(nsamples, prob, bsamples);
        for (i = 0; i < nsamples; i++) {
            xdata_training[i] = data[bsamples[i]];
            xclasses_training[i] = data_class[bsamples[i]];
        }
        compute_tree(&(btree->tree[b]), nsamples, nvar, xdata_training,
                     xclasses_training, nclasses, classes, stamps, minsize,
                     costs);
    }

    G_free(bsamples);
    G_free(xclasses_training);
    G_free(prob);
    G_free(xdata_training);
}

void write_bagging_boosting_tree(char *file, BTree *btree, Features *features)

/*
   write a bagging or boosting tree model to a file
 */
{
    int i, j;
    FILE *fp;
    char tempbuf[500];
    int b;

    fp = fopen(file, "w");
    if (fp == NULL) {
        sprintf(tempbuf,
                "write_bagging_boosting_tree-> Can't open file %s for writing",
                file);
        G_fatal_error(tempbuf);
    }

    write_header_features(fp, features);
    fprintf(fp, "#####################\n");
    fprintf(fp, "MODEL:\n");
    fprintf(fp, "#####################\n");

    fprintf(fp, "Model:\n");
    fprintf(fp, "B-ClassificationTree\n");
    fprintf(fp, "Cost parameter:\n");
    fprintf(fp, "%f\n", btree->w);
    fprintf(fp, "Number of models:\n");
    fprintf(fp, "%d\n", btree->ntrees);
    fprintf(fp, "Weights:\n");
    fprintf(fp, "%f", btree->weights[0]);
    for (b = 1; b < btree->ntrees; b++) {
        fprintf(fp, "\t%f", btree->weights[b]);
    }
    fprintf(fp, "\n");

    for (b = 0; b < btree->ntrees; b++) {
        fprintf(fp, "Number of nodes:\n");
        fprintf(fp, "%d\n", btree->tree[b].nnodes);
        fprintf(fp, "Number of classes:\n");
        fprintf(fp, "%d\n", btree->tree[b].node[0].nclasses);
        fprintf(fp, "Number of features:\n");
        fprintf(fp, "%d\n", btree->tree[b].node[0].nvar);
        fprintf(fp, "Tree structure:\n");
        fprintf(fp, "terminal\tndata\t");
        for (j = 0; j < btree->tree[b].node[0].nclasses; j++)
            fprintf(fp, "data_cl%d\t", j + 1);
        for (j = 0; j < btree->tree[b].node[0].nclasses; j++)
            fprintf(fp, "prior_cl%d\t", j + 1);
        fprintf(
            fp,
            "class\tchild_left\tchild_right\tsplit_variable\tsplit_value\n");
        for (i = 0; i < btree->tree[b].nnodes; i++) {
            fprintf(fp, "%d\t%d\t", btree->tree[b].node[i].terminal,
                    btree->tree[b].node[i].npoints);
            for (j = 0; j < btree->tree[b].node[i].nclasses; j++)
                fprintf(fp, "%d\t",
                        btree->tree[b].node[i].npoints_for_class[j]);
            for (j = 0; j < btree->tree[b].node[i].nclasses; j++)
                fprintf(fp, "%f\t", btree->tree[b].node[i].priors[j]);
            if (btree->tree[b].node[i].terminal)
                fprintf(fp, "%d\n", btree->tree[b].node[i].class);
            else
                fprintf(
                    fp, "%d\t%d\t%d\t%d\t%f\n", btree->tree[b].node[i].class,
                    btree->tree[b].node[i].left, btree->tree[b].node[i].right,
                    btree->tree[b].node[i].var, btree->tree[b].node[i].value);
        }
    }

    if (features->f_pca[0]) {
        fprintf(fp, "#####################\n");
        fprintf(fp, "PRINC. COMP.:\n");
        fprintf(fp, "#####################\n");

        fprintf(fp, "Number of pc:\n");
        fprintf(fp, "%d\n", features->npc);

        for (i = 0; i < features->f_pca[1]; i++) {
            fprintf(fp, "PCA: Layer %d\n", i + 1);
            write_pca(fp, &(features->pca[i]));
        }
    }
    fclose(fp);
}

int predict_tree_multiclass(Tree *tree, double *x)

/*
   multiclass problems: given a tree model, return the predicted class
   of a test point x
 */
{
    int act_node;

    act_node = 0;

    for (;;) {
        if (tree->node[act_node].terminal) {
            return tree->node[act_node].class;
        }
        else {
            if (x[tree->node[act_node].var] <= tree->node[act_node].value)
                act_node = tree->node[act_node].left;
            else
                act_node = tree->node[act_node].right;
        }
    }
}

double predict_tree_2class(Tree *tree, double *x)

/*
   2 class problems: given a tree model, return the proportion of data
   in the terminal node (with sign) of a test point x
 */
{
    int act_node;

    act_node = 0;

    for (;;) {
        if (tree->node[act_node].terminal) {
            if (tree->node[act_node].priors[0] >
                tree->node[act_node].priors[1]) {
                return tree->node[act_node].priors[0] *
                       tree->node[act_node].class;
            }
            else {
                return tree->node[act_node].priors[1] *
                       tree->node[act_node].class;
            }
        }
        else {
            if (x[tree->node[act_node].var] <= tree->node[act_node].value)
                act_node = tree->node[act_node].left;
            else
                act_node = tree->node[act_node].right;
        }
    }
}

void test_tree(Tree *tree, Features *features, char *file)

/*
   test a tree model on a set of data (features) and write the results
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
        sprintf(tempbuf, "test_tree-> Can't open file %s for writing", file);
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
                    if ((predD =
                             predict_tree_2class(tree, features->value[i])) *
                            features->class[i] <=
                        0) {
                        error[j] += 1.0;
                        accuracy += 1.0;
                    }
                    fprintf(fp, "%d\t%f\n", features->class[i], predD);
                }
                else {
                    if ((predI = predict_tree_multiclass(
                             tree, features->value[i])) != features->class[i]) {
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

double predict_btree_2class(BTree *btree, double *x)

/*
   for 2 classes problems: given a btree model, return the predicted
   margin of a test point x
 */
{
    int b;
    double predict;

    predict = 0.0;
    for (b = 0; b < btree->ntrees; b++) {
        predict +=
            predict_tree_multiclass(&(btree->tree[b]), x) * btree->weights[b];
    }
    return predict;
}

int predict_btree_multiclass(BTree *btree, double *x, int nclasses,
                             int *classes)

/*
   for multiclasses problems: given a btree model, return the predicted
   class of a test point x
 */
{
    int *predict;
    int b, j;
    int pred_class;
    int max_class;
    int max;

    predict = (int *)G_calloc(nclasses, sizeof(int));

    for (b = 0; b < btree->ntrees; b++) {
        pred_class = predict_tree_multiclass(&(btree->tree[b]), x);
        for (j = 0; j < nclasses; j++) {
            if (pred_class == classes[j]) {
                predict[j] += 1;
            }
        }
    }

    max = 0;
    max_class = 0;
    for (j = 0; j < nclasses; j++) {
        if (predict[j] > max) {
            max = predict[j];
            max_class = j;
        }
    }

    G_free(predict);
    return classes[max_class];
}

void test_btree(BTree *btree, Features *features, char *file)

/*
   test a btree model on a set of data
   (features) and write the results into a file. To standard output
   accuracy and error on each class
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
        sprintf(tempbuf, "test_btree-> Can't open file %s for writing", file);
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
                    if ((predD =
                             predict_btree_2class(btree, features->value[i])) *
                            features->class[i] <=
                        0) {
                        error[j] += 1.0;
                        accuracy += 1.0;
                    }
                    fprintf(fp, "%d\t%f\n", features->class[i], predD);
                }
                else {
                    if ((predI = predict_btree_multiclass(
                             btree, features->value[i], features->nclasses,
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

void test_btree_progressive(BTree *btree, Features *features, char *file)

/*
   test a btree model on a set of data
   (features) and write the results into a file. To standard output
   accuracy and error on each class
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
    int b;

    fp = fopen(file, "w");
    if (fp == NULL) {
        sprintf(tempbuf, "test_btree-> Can't open file %s for writing", file);
        G_fatal_error(tempbuf);
    }

    data_in_each_class = (int *)G_calloc(features->nclasses, sizeof(int));
    error = (double *)G_calloc(features->nclasses, sizeof(double));

    for (b = 1; b <= btree->ntrees; b++) {
        if ((b < 100 && b % 2 == 1) || (b >= 100) || (b == btree->ntrees)) {
            /*
               if((b<500 && b%10==0) || (b<5000 && b%100==0) || (b%1000==0)||
               (b==btree->ntrees)){
             */
            accuracy = 0.0;
            for (j = 0; j < features->nclasses; j++) {
                error[j] = .0;
                data_in_each_class[j] = 0;
            }
            for (i = 0; i < features->nexamples; i++) {
                for (j = 0; j < features->nclasses; j++) {
                    if (features->class[i] == features->p_classes[j]) {
                        data_in_each_class[j] += 1;
                        if (features->nclasses == 2) {
                            if ((predD = predict_btree_2class_progressive(
                                     btree, features->value[i], b)) *
                                    features->class[i] <=
                                0) {
                                error[j] += 1.0;
                                accuracy += 1.0;
                            }
                            if (b == btree->ntrees)
                                fprintf(fp, "%d\t%f\n", features->class[i],
                                        predD);
                        }
                        else {
                            if ((predI = predict_btree_multiclass_progressive(
                                     btree, features->value[i],
                                     features->nclasses, features->p_classes,
                                     b)) != features->class[i]) {
                                error[j] += 1.0;
                                accuracy += 1.0;
                            }
                            if (b == btree->ntrees)
                                fprintf(fp, "%d\t%d\n", features->class[i],
                                        predI);
                        }
                        break;
                    }
                }
            }
            accuracy /= features->nexamples;
            accuracy = 1.0 - accuracy;

            if (b == btree->ntrees)
                fclose(fp);

            fprintf(stdout, "nmodels = %d\n", b);
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
            fflush(stdout);
        }
    }
    G_free(data_in_each_class);
    G_free(error);
}

double predict_btree_2class_progressive(BTree *btree, double *x, int bmax)

/*
   for 2 classes problems: given a btree model, return the predicted
   margin of a test point x
 */
{
    int b;
    double predict;

    predict = 0.0;
    for (b = 0; b < bmax; b++) {
        predict +=
            predict_tree_multiclass(&(btree->tree[b]), x) * btree->weights[b];
    }
    return predict;
}

int predict_btree_multiclass_progressive(BTree *btree, double *x, int nclasses,
                                         int *classes, int bmax)

/*
   for multiclasses problems: given a btree model, return the predicted
   class of a test point x
 */
{
    int *predict;
    int b, j;
    int pred_class;
    int max_class;
    int max;

    predict = (int *)G_calloc(nclasses, sizeof(int));

    for (b = 0; b < bmax; b++) {
        pred_class = predict_tree_multiclass(&(btree->tree[b]), x);
        for (j = 0; j < nclasses; j++) {
            if (pred_class == classes[j]) {
                predict[j] += 1;
            }
        }
    }

    max = 0;
    max_class = 0;
    for (j = 0; j < nclasses; j++) {
        if (predict[j] > max) {
            max = predict[j];
            max_class = j;
        }
    }

    G_free(predict);
    return classes[max_class];
}

void compute_tree_boosting_parallel(BTree *btree, int boosting,
                                    int parallel_boosting, double w,
                                    int nsamples, int nvar, double **data,
                                    int *data_class, int nclasses, int *classes,
                                    int stamps, int minsize,
                                    int weights_boosting, double *costs)

/*
   receives in input training data of dimensions nsamples x nvar,
   with class labels data_class, the possible classes (of length nclasses)
   and computes a boosting tree model (number of models = boosting) using w

   optionally, the user can build stamps and decide the
   minimal number of cases within a node as stopping criteria.
 */
{
    int i, j, b;
    int *bsamples;
    double **xdata_training;
    int *xclasses_training;
    double *prob;
    double e00, e01, e10, e11, prior0, prior1;
    int *error;
    double eps, totprob;
    double totbeta;
    double mean, variance, alpha, beta;
    int idum = 1;

#ifdef LEAVEOUTEASYPOINTS
#undef LEAVEOUTEASYPOINTS
#endif

#ifdef LEAVEOUTEASYPOINTS
    int **correct;

    correct = (int **)G_calloc(nsamples, sizeof(int *));
    for (i = 0; i < nsamples; i++) {
        correct[i] = (int *)G_calloc(boosting, sizeof(int));
    }
#endif

    btree->w_evolution = (double **)G_calloc(nsamples, sizeof(double *));
    for (i = 0; i < nsamples; i++)
        btree->w_evolution[i] =
            (double *)G_calloc(parallel_boosting + 3, sizeof(double));

    btree->tree = (Tree *)G_calloc(parallel_boosting, sizeof(Tree));
    btree->ntrees = parallel_boosting;
    btree->weights = (double *)G_calloc(btree->ntrees, sizeof(double));
    btree->w = w;

    prob = (double *)G_calloc(nsamples, sizeof(double));
    bsamples = (int *)G_calloc(nsamples, sizeof(int));
    xdata_training = (double **)G_calloc(nsamples, sizeof(double *));
    xclasses_training = (int *)G_calloc(nsamples, sizeof(int));
    error = (int *)G_calloc(nsamples, sizeof(int));

    for (i = 0; i < nsamples; i++) {
        prob[i] = 1.0 / nsamples;
    }

    for (b = 0; b < boosting; b++) {
        for (i = 0; i < nsamples; i++)
            btree->w_evolution[i][b] = prob[i];

        Bootsamples(nsamples, prob, bsamples);
        for (i = 0; i < nsamples; i++) {
            xdata_training[i] = data[bsamples[i]];
            xclasses_training[i] = data_class[bsamples[i]];
        }
        compute_tree(&(btree->tree[b]), nsamples, nvar, xdata_training,
                     xclasses_training, nclasses, classes, stamps, minsize,
                     costs);

        e00 = e01 = e10 = e11 = prior0 = prior1 = 0.0;
        for (i = 0; i < nsamples; i++) {
            if (data_class[i] == classes[0]) {
                if (predict_tree_multiclass(&(btree->tree[b]), data[i]) !=
                    data_class[i]) {
#ifdef LEAVEOUTEASYPOINTS
                    correct[i][b] = FALSE;
#endif
                    error[i] = TRUE;
                    e01 += prob[i];
                }
                else {
#ifdef LEAVEOUTEASYPOINTS
                    correct[i][b] = TRUE;
#endif
                    error[i] = FALSE;
                    e00 += prob[i];
                }
                prior0 += prob[i];
            }
            else {
                if (predict_tree_multiclass(&(btree->tree[b]), data[i]) !=
                    data_class[i]) {
#ifdef LEAVEOUTEASYPOINTS
                    correct[i][b] = FALSE;
#endif
                    error[i] = TRUE;
                    e10 += prob[i];
                }
                else {
#ifdef LEAVEOUTEASYPOINTS
                    correct[i][b] = TRUE;
#endif
                    error[i] = FALSE;
                    e11 += prob[i];
                }
                prior1 += prob[i];
            }
        }
        eps = (1.0 - e00 / (e00 + e01)) * prior0 * btree->w +
              (1.0 - e11 / (e10 + e11)) * prior1 * (2.0 - btree->w);
        if (eps > 0.0 && eps < 0.5) {
            btree->weights[b] = 0.5 * log((1.0 - eps) / eps);
            totprob = 0.0;
            for (i = 0; i < nsamples; i++) {
                if (error[i]) {
                    if (data_class[i] == classes[0]) {
                        prob[i] = prob[i] * exp(btree->weights[b] * btree->w);
                    }
                    else {
                        prob[i] =
                            prob[i] * exp(btree->weights[b] * (2.0 - btree->w));
                    }
                }
                else {
                    if (data_class[i] == classes[0]) {
                        prob[i] = prob[i] *
                                  exp(-btree->weights[b] * (2.0 - btree->w));
                    }
                    else {
                        prob[i] = prob[i] * exp(-btree->weights[b] * btree->w);
                    }
                }
                totprob += prob[i];
            }
            for (i = 0; i < nsamples; i++) {
                prob[i] /= totprob;
            }
        }
        else {
            btree->weights[b] = 0.0;
            for (i = 0; i < nsamples; i++) {
                prob[i] = 1.0 / nsamples;
            }
        }
    }

    for (i = 0; i < nsamples; i++) {
#ifdef LEAVEOUTEASYPOINTS
        double p0, p1, p00, p11;

        p0 = p1 = p00 = p11 = 0.0;
        for (b = 20; b < boosting - 1; b++) {
            if (correct[i][b] == 0) {
                p0 += 1.0;
                if (correct[i][b + 1] == 0) {
                    p00 += 1.0;
                }
            }
            else {
                p1 += 1.0;
                if (correct[i][b + 1] == 1) {
                    p11 += 1.0;
                }
            }
        }
        fprintf(stdout, "%f\t%f\n", p11 / p1, p00 / p0);
#endif

        mean = mean_of_double_array(btree->w_evolution[i], boosting);
        variance = var_of_double_array(btree->w_evolution[i], boosting);
        alpha = mean * mean / variance;
        beta = variance / mean;

        for (j = boosting; j < parallel_boosting; j++)
            btree->w_evolution[i][j] = gamdev(alpha, beta, &idum);
    }

    for (b = boosting; b < parallel_boosting; b++) {
        for (i = 0; i < nsamples; i++)
            prob[i] = btree->w_evolution[i][b];
        Bootsamples(nsamples, prob, bsamples);
        for (i = 0; i < nsamples; i++) {
            xdata_training[i] = data[bsamples[i]];
            xclasses_training[i] = data_class[bsamples[i]];
        }
        compute_tree(&(btree->tree[b]), nsamples, nvar, xdata_training,
                     xclasses_training, nclasses, classes, stamps, minsize,
                     costs);

        e00 = e01 = e10 = e11 = prior0 = prior1 = 0.0;
        for (i = 0; i < nsamples; i++) {
            if (data_class[i] == classes[0]) {
                if (predict_tree_multiclass(&(btree->tree[b]), data[i]) !=
                    data_class[i]) {
                    error[i] = TRUE;
                    e01 += prob[i];
                }
                else {
                    error[i] = FALSE;
                    e00 += prob[i];
                }
                prior0 += prob[i];
            }
            else {
                if (predict_tree_multiclass(&(btree->tree[b]), data[i]) !=
                    data_class[i]) {
                    error[i] = TRUE;
                    e10 += prob[i];
                }
                else {
                    error[i] = FALSE;
                    e11 += prob[i];
                }
                prior1 += prob[i];
            }
        }
        eps = (1.0 - e00 / (e00 + e01)) * prior0 * btree->w +
              (1.0 - e11 / (e10 + e11)) * prior1 * (2.0 - btree->w);
        if (eps > 0.0 && eps < 0.5) {
            btree->weights[b] = 0.5 * log((1.0 - eps) / eps);
            totprob = 0.0;
            for (i = 0; i < nsamples; i++) {
                if (error[i]) {
                    if (data_class[i] == classes[0]) {
                        prob[i] = prob[i] * exp(btree->weights[b] * btree->w);
                    }
                    else {
                        prob[i] =
                            prob[i] * exp(btree->weights[b] * (2.0 - btree->w));
                    }
                }
                else {
                    if (data_class[i] == classes[0]) {
                        prob[i] = prob[i] *
                                  exp(-btree->weights[b] * (2.0 - btree->w));
                    }
                    else {
                        prob[i] = prob[i] * exp(-btree->weights[b] * btree->w);
                    }
                }
                totprob += prob[i];
            }
            for (i = 0; i < nsamples; i++) {
                prob[i] /= totprob;
            }
        }
        else {
            btree->weights[b] = 0.0;
            for (i = 0; i < nsamples; i++) {
                prob[i] = 1.0 / nsamples;
            }
        }
    }

    totbeta = 0.0;
    for (b = 0; b < btree->ntrees; b++) {
        totbeta += btree->weights[b];
    }
    for (b = 0; b < btree->ntrees; b++) {
        btree->weights[b] /= totbeta;
    }

    G_free(bsamples);
    G_free(xclasses_training);
    G_free(prob);
    G_free(error);
    G_free(xdata_training);
}
