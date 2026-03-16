#pragma once

/*
   tree.c
 */

void compute_tree(Tree *, int, int, double **, int *, int, int *, int, int,
                  double *);
void write_tree(char *, Tree *, Features *);
void compute_tree_boosting(BTree *, int, double, int, int, double **, int *,
                           int, int *, int, int, int, double *);
void compute_tree_boosting_reg(BTree *, int, double, int, int, double **, int *,
                               int, int *, int, int, int, double *, double *);
void regularized_boosting(int, double, int, int, double **, int *, int, int *,
                          int, int, int, double *, double *, int, Features,
                          char *, Features, int, char[150], char[150],
                          char[150], Features, int);
double test_regularized_boosting(BTree *, Features *);
void test_btree_reg(BTree *, Features *, char *, double *);
void shaving_and_compute(int, double, int, int, double **, int *, int, int *,
                         int, int, int, double *, double *, int, double, char *,
                         char[150], Features, Features, char *, int);
void compute_tree_bagging(BTree *, int, int, int, double **, int *, int, int *,
                          int, int, double *);
void write_bagging_boosting_tree(char *, BTree *, Features *);
int predict_tree_multiclass(Tree *, double *);
double predict_tree_2class(Tree *, double *);
void test_tree(Tree *, Features *, char *);
double predict_btree_2class(BTree *, double *);
int predict_btree_multiclass(BTree *, double *, int, int *);
void test_btree(BTree *, Features *, char *);
void test_btree_progressive(BTree *, Features *, char *);
double predict_btree_2class_progressive(BTree *, double *, int);
int predict_btree_multiclass_progressive(BTree *, double *, int, int *, int);
void compute_tree_boosting_parallel(BTree *, int, int, double, int, int,
                                    double **, int *, int, int *, int, int, int,
                                    double *);

/*
   features_selection.c
 */

void compute_valoriDJ(SupportVectorMachine *, Features *, double **, double **,
                      double **);
void free_svm(SupportVectorMachine *);
void e_rfe_lin(SupportVectorMachine *, Features *, int *, int *, int, int *,
               FILE *, FILE *);
void e_rfe_gauss(double *, Features *, int *, int *, int, double **, double **,
                 int *, double, FILE *, FILE *);
void one_rfe_lin(SupportVectorMachine *, int *, int *, FILE *);
void one_rfe_gauss(double *, int *, int *, int, FILE *);
void rfe_lin(SupportVectorMachine *, Features *, int *, int *, int, FILE *);
void rfe_gauss(double *, Features *, int *, int *, int, double **, double **,
               double, FILE *);
void compute_H(double **, double **, int *, int, int, double);
void compute_H_perdiff(double **, double **, double **, int, double, int);
void traslo(double *, int);

/*
   soft_margin_boosting.c
 */

void maximize(double *, int, double *, int, double **);

/*
   write_matrix.c
 */

void write_matrix(char *, double **, int, int);

/*
   entropy.c
 */

double Entropy(double *, int, double);
double Clog(double, double);
void histo(double *, int, double *, int);
void histo1(double *, int, int *, int);

/*
   min_quadratic.c
 */

void mqc(double **, double *, int, double **, double *, int, double **,
         double *, int, double, double *, double *);

/*
   blob.c
 */

void extract_sites_from_blob(Blob *, int, int, struct Cell_head *, BlobSites *,
                             double **);
void find_blob(double **, int, int, Blob **, int *, int *, double, double);

/*
   test.c
 */

void ksone_normal(double *, int, double, double, double *, double *);
void kstwo(double *, int, double *, int, double *, double *);
double probks(double);
double probks2(double, int);
double normal_distribution(double, double, double);
double cumulative_normal_distribution(double, double, double);
double gammln(double);
double betacf(double, double, double);
double betai(double, double, double);
void tutest(double *, int, double *, int, double *, double *);

/*
   read_models.c
 */

int read_model(char *, Features *, NearestNeighbor *, GaussianMixture *, Tree *,
               SupportVectorMachine *, BTree *, BSupportVectorMachine *);

/*
   nn.c
 */

void compute_nn(NearestNeighbor *, int, int, double **, int *);
void write_nn(char *, NearestNeighbor *, Features *);
int predict_nn_multiclass(NearestNeighbor *, double *, int, int, int *);
double predict_nn_2class(NearestNeighbor *, double *, int, int, int *);
void test_nn(NearestNeighbor *, Features *, int, char *);

/*
   svm.c
 */

void compute_svm(SupportVectorMachine *, int, int, double **, int *, int,
                 double, double, double, double, int, int, double *);
void estimate_cv_error(SupportVectorMachine *);
void write_svm(char *file, SupportVectorMachine *, Features *);
void test_svm(SupportVectorMachine *, Features *, char *);
double predict_svm(SupportVectorMachine *, double *);
void compute_svm_bagging(BSupportVectorMachine *, int, int, int, double **,
                         int *, int, double, double, double, double, int, int,
                         double *);
void write_bagging_boosting_svm(char *, BSupportVectorMachine *, Features *);
void compute_svm_boosting(BSupportVectorMachine *, int, double, int, int,
                          double **, int *, int, int *, int, double, double,
                          double, double, int, int, double *, int);
double predict_bsvm(BSupportVectorMachine *, double *);
void test_bsvm(BSupportVectorMachine *, Features *, char *);
void test_bsvm_progressive(BSupportVectorMachine *, Features *, char *);
double predict_bsvm_progressive(BSupportVectorMachine *, double *, int);
double dot_product(double *, double *, int);

/*
   features.c
 */

void compute_features(Features *);
void write_features(char *, Features *);
void standardize_features(Features *);
void write_header_features(FILE *, Features *);
void read_features(char *, Features *, int);
void read_header_features(FILE *, Features *);

/*
   gm.c
 */

void compute_gm(GaussianMixture *, int, int, double **, int *, int, int *);
void write_gm(char *, GaussianMixture *, Features *);
void test_gm(GaussianMixture *, Features *, char *);
void compute_test_gm(GaussianMixture *);
int predict_gm_multiclass(GaussianMixture *, double *);
double predict_gm_2class(GaussianMixture *, double *);

/*
   training.c
 */

void inizialize_training(Training *);
void read_training(char *, Training *);

/*
   matrix.c
 */

void product_double_matrix_double_matrix(double **, double **, int, int, int,
                                         double **);
void product_double_matrix_double_vector(double **, double *, int, int,
                                         double *);
void product_double_vector_double_matrix(double **, double *, int, int,
                                         double *);
void transpose_double_matrix(double **, int);
void double_matrix_to_vector(double **, int, int, double *);
void extract_portion_of_double_matrix(int, int, int, int, double **, double **);
void transpose_double_matrix_rectangular(double **, int, int, double ***);

/*
   pca.c
 */

void inizialize_pca(Pca *, int);
void write_pca(FILE *, Pca *);
void read_pca(FILE *, Pca *);

/*
   random.c
 */

double ran1(int *);
double gasdev(int *);
double gamdev(double, double, int *);
double expdev(int *);

/*
   bootstrap.c
 */

void Bootsamples(int, double *, int *);
void Bootsamples_rseed(int, double *, int *, int *);

/*
   dist.c
 */

double squared_distance(double *, double *, int);
double euclidean_distance(double *, double *, int);
double scalar_product(double *, double *, int);
double euclidean_norm(double *, int);

/*
   open.c
 */

int open_new_CELL(char *);
int open_new_DCELL(char *);

/*
   percent.c
 */

void percent(int, int, int);

/*
   getline.c
 */

char *GetLine(FILE *);

/*
   sort.c
 */

void shell(int, double *);
void indexx_1(int, double[], int[]);

/*
   integration.c
 */

double trapzd(double (*)(double), double, double, int);
double trapzd1(double (*)(double, double), double, double, double, int);
double trapzd2(double (*)(double, double, double), double, double, double,
               double, int);
double qtrap(double (*)(double), double, double);
double qtrap1(double (*)(double), double, double, double);
double qtrap2(double (*)(double), double, double, double, double);

/*
   eigen.c
 */

void tred2(double **, int, double[], double[]);
int tqli(double[], double[], int, double **);
void eigen_of_double_matrix(double **, double **, double *, int);
void eigsrt(double *, double **, int);

/*
   stats.c
 */

double mean_of_double_array(double *, int);
double var_of_double_array(double *, int);
double sd_of_double_array(double *, int);
double var_of_double_array_given_mean(double *, int, double);
double sd_of_double_array_given_mean(double *, int, double);
void mean_and_var_of_double_matrix_by_row(double **, int, int, double *,
                                          double *);
void mean_and_sd_of_double_matrix_by_row(double **, int, int, double *,
                                         double *);
void mean_and_var_of_double_matrix_by_col(double **, int, int, double *,
                                          double *);
void mean_and_sd_of_double_matrix_by_col(double **, int, int, double *,
                                         double *);
double auto_covariance_of_2_double_array(double *, double *, int);
void covariance_of_double_matrix(double **, int, int, double **);
double entropy(double *, int);
double gaussian_kernel(double *, double *, int, double);
double squared_gaussian_kernel(double *, double *, int, double);
double min(double *, int);
double max(double *, int);

/*
   lu.c
 */

void ludcmp(double **, int, int *, double *);
void lubksb(double **, int, int *, double[]);
void inverse_of_double_matrix(double **, double **, int);
double determinant_of_double_matrix(double **, int);
