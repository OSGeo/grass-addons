/*
   tree.c
 */

void compute_tree();
void write_tree();
void compute_tree_boosting();
void compute_tree_boosting_reg();
void regularized_boosting();
double test_regularized_boosting();
void test_btree_reg();
void shaving_and_compute();
void compute_tree_bagging();
void write_bagging_boosting_tree();
int predict_tree_multiclass();
double predict_tree_2class();
void test_tree();
double predict_btree_2class();
int predict_btree_multiclass();
void test_btree();
void test_btree_progressive();
double predict_btree_2class_progressive();
int predict_btree_multiclass_progressive();
void compute_tree_boosting_parallel();

/*
   features_selection.c
 */

void compute_valoriDJ();
void free_svm();
void e_rfe_lin();
void e_rfe_gauss();
void one_rfe_lin();
void one_rfe_gauss();
void rfe_lin();
void rfe_gauss();
void write_matrix();
void compute_H();
void compute_H_perdiff();
void traslo();

/*
   soft_margin_boosting.c
 */

void maximize();

/*
   write_matrix.c
 */

void write_matrix();

/*
   entropy.c
 */

double Entropy();
double Clog();
void histo();
void histo1();

/*
   min_quadratic.c
 */

void mqc();

/*
   blob.c
 */

void extract_sites_from_blob();
void find_blob();

/*
   test.c
 */

void ksone_normal();
void kstwo();
double probks();
double probks2();
double normal_distribution();
double cumulative_normal_distribution();
double gammln();
double betacf();
double betai();
void tutest();

/*
   read_models.c
 */

int read_model();

/*
   nn.c
 */

void compute_nn();
void write_nn();
int predict_nn_multiclass();
double predict_nn_2class();
void test_nn();

/*
   svm.c
 */

void compute_svm();
void estimate_cv_error();
void write_svm();
void test_svm();
double predict_svm();
void compute_svm_bagging();
void write_bagging_boosting_svm();
void compute_svm_boosting();
double predict_bsvm();
void test_bsvm();
void test_bsvm_progressive();
double predict_bsvm_progressive();
double dot_product();

/*
   features.c
 */

void compute_features();
void write_features();
void standardize_features();
void write_header_features();
void read_features();
void read_header_features();

/*
   gm.c
 */

void compute_gm();
void write_gm();
void test_gm();
void compute_test_gm();
int predict_gm_multiclass();
double predict_gm_2class();

/*
   training.c
 */

void inizialize_training();
void read_training();

/*
   matrix.c
 */

void product_double_matrix_double_matrix();
void product_double_matrix_double_vector();
void product_double_vector_double_matrix();
void transpose_double_matrix();
void double_matrix_to_vector();
void extract_portion_of_double_matrix();
void transpose_double_matrix_rectangular();

/*
   pca.c
 */

void inizialize_pca();
void write_pca();
void read_pca();

/*
   random.c
 */

double ran1();
double gasdev();
double gamdev();
double expdev();

/*
   bootstrap.c
 */

void Bootsamples();
void Bootsamples_rseed();

/*
   dist.c
 */

double squared_distance();
double euclidean_distance();
double scalar_product();
double euclidean_norm();

/*
   open.c
 */

int open_new_CELL();
int open_new_DCELL();

/*
   percent.c
 */

void percent();

/*
   getline.c
 */

char *GetLine();

/*
   sort.c
 */

void shell();
void indexx_1();

/*
   integration.c
 */

double trapzd();
double trapzd1();
double trapzd2();
double qtrap();
double qtrap1();
double qtrap2();

/*
   eigen.c
 */

void tred2();
int tqli();
void eigen_of_double_matrix();
void eigsrt();

/*
   stats.c
 */

double mean_of_double_array();
double var_of_double_array();
double sd_of_double_array();
double var_of_double_array_given_mean();
double sd_of_double_array_given_mean();
void mean_and_var_of_double_matrix_by_row();
void mean_and_sd_of_double_matrix_by_row();
void mean_and_var_of_double_matrix_by_col();
void mean_and_sd_of_double_matrix_by_col();
double auto_covariance_of_2_double_array();
void covariance_of_double_matrix();
double entropy();
double gaussian_kernel();
double squared_gaussian_kernel();
double min();
double max();

/*
   lu.c
 */

void ludcmp();
void lubksb();
void inverse_of_double_matrix();
double determinant_of_double_matrix();
