/*
bootstrap.c
*/

int Bootsamples();

/*
random.c
*/

double ran1();
double gasdev();

/*
blob.c
*/

void extract_sites_from_blob();
void find_blob();

/*
tree.c
*/

int  build_maximal_tree();
void write_tree();
int read_tree();
int godown();
void write_Btree();
int read_Btree();
double evaluateB();
int evaluateB_multiclass();
void classify_image_TREE();

/*
training.c
*/

void build_training();

/*
percent.c
*/

void percent ();

/*
open.c
*/

int open_new_CELL();
int open_new_DCELL();

/*
pca.c
*/

void alloc_pca();
void write_pca();
void read_pca();

/*
dist.c
*/

double squared_distance();
double euclidean_distance();
double scalar_product();
double euclidean_norm();

/*
getline.c
*/

char *GetLine();

/*
pi.c
*/

void linear_solve();

/*
read_list.c
*/

void read_list_of_type_1_and_load_raster_maps();
void read_list_of_type_2();
void read_list_of_type_2_and_load_raster_maps();
int read_list_of_sites();

/*
filter.c
*/

void write_filter();
void read_filter();

/*
test.c
*/

void ksone_normal();
void kstwo();
double normal_distribution();
double cumulative_normal_distribution();

/*
nn.c
*/

void classify_image_NN();
void write_nn();
void read_nn();
void compute_NN_from_training();
void read_matrix();

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
gm.c
*/

void compute_gm();
void write_gm();
void read_gm();
double ComputeDelta();
void classify_image_GM();

/*
sort.c
*/

void shell();
void indexx_1();
void indexx();

/*
eigen.c
*/

void tred2();
int tqli();
int eigen_of_double_matrix();
void eigsrt();

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
lu.c
*/

void ludcmp();
void lubksb();
void inverse_of_double_matrix();
double determinant_of_double_matrix();

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
