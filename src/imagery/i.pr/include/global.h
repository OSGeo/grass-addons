#include <grass/gis.h>
#include "func.h"

#define PIG                     M_PI

#define TRUE                    1
#define FALSE                   0

#define TRAINING_MAX_INPUTFILES 50
#define TRAINING_MAX_LAYERS     25
#define TRAINING_MAX_EXAMPLES   100000
#define BUFFSIZE                500000 /* MAX NUMBER OF BITES FOR EACH ROW */

#define NN_model                1
#define GM_model                2
#define CT_model                3
#define SVM_model               4
#define BCT_model               5
#define BSVM_model              6

#define GRASS_data              1
#define TABLE_data              2

#define SVM_KERNEL_LINEAR       1
#define SVM_KERNEL_GAUSSIAN     2
#define SVM_KERNEL_DIRECT       3

#define FS_RFE                  1
#define FS_E_RFE                2
#define FS_ONE_RFE              3
#define FS_SQRT_RFE             4

typedef struct {
    char *file;       /*source data */
    int data_type;    /*GRASS_data or TABLE_data */
    int nlayers;      /*number of layers (for GRASS_data) */
    int nexamples;    /*number of examples */
    char ***mapnames; /*name of the raster maps (for GRASS_data)
                         nlayers maps in each row */
    int *class;       /*class label of the examples */
    double *east;  /*east coordinate of centers of the maps (for GRASS_data) */
    double *north; /*north coordinate of centers of the maps (for GRASS_data) */
    double **data; /*matrix of data (for TABLE_data) */
    double ew_res; /*resolution e-w (for GRASS_data) */
    double ns_res; /*resolution n-s (for GRASS_data) */
    int rows;      /*rows of the examples (1 for for GRASS_data) */
    int cols;      /*number of colums of the examples */
} Training;

typedef struct {
    int n;           /*number of elements */
    double *mean;    /*the mean value of the examples, stored in an
                        array of dimension rows x cols */
    double *sd;      /*the standard deviation of the examples, stored in an
                        array of dimension rows x cols */
    double **covar;  /*covariance matrix of the examples, stored in a
                        matrix of dimension (rows x cols)^2 */
    double *eigval;  /*eigenvalues of the covariance matrix */
    double **eigmat; /*eigenvectors matrix of the covariance matrix.
                        Each column is the eigenvector corresponding to
                        an eigenvalues */
} Pca;

typedef struct {
    char *file;         /*source data */
    int nexamples;      /*number of examples */
    int examples_dim;   /*dimension of the examples */
    double **value;     /*matrix of the data */
    int *class;         /*class labels */
    int *p_classes;     /*all the class present in the class array */
    int nclasses;       /*number of classes */
    double *mean;       /*mean of the vars (in case of standardization) */
    double *sd;         /*sd of the vars (in case of standardization) */
    int *f_normalize;   /*for normalising a datum: TRUE or FALSE */
    int *f_standardize; /*for standardize variables: TRUE or FALSE */
    int *f_mean;        /*for computing the mean of a datum: TRUE or FALSE */
    int *f_variance;   /*for computing the variance of a datum: TRUE or FALSE */
    int *f_pca;        /*for computing pc on the data: TRUE or FALSE */
    int *pca_class;    /*use only this classes for computing the pc */
    Pca *pca;          /*the pc structure (if f_pca) */
    Training training; /*some information regarding training data */
    int npc; /* number of pc to be (eventually) used for the model development
              */
} Features;

typedef struct {
    double **data;          /*data contained into the node */
    int *classes;           /*classes of the data */
    int npoints;            /*number of data into the data */
    int nvar;               /*dimension of the data */
    int nclasses;           /*number of classes */
    int *npoints_for_class; /*number of elements for each class */
    double *priors;         /*prior probabilities for each class */
    int class;              /*class associated to the ciurrent node */
    int terminal;           /*is the node terminal? TRUE or FALSE */
    int left;               /*his left child */
    int right;              /*his right child */
    int var;      /*variable used to split this node (if not terminal) */
    double value; /*value of the variable for splitting the data */
} Node;

typedef struct {
    Node *node;        /*the nodes */
    int nnodes;        /*number of nodes */
    int stamps;        /*if it is stamps: TRUE or FALSE */
    int minsize;       /*minsize for splitting a node */
    Features features; /*the features used for the model development */
} Tree;

typedef struct {
    Tree *tree;      /*the trees */
    int ntrees;      /*number of trees */
    double *weights; /*their wieghts */
    double w;        /*cost-sensitive parameter use (for boosting) */
    double **w_evolution;
    Features features; /*the features used for the model development */
} BTree;

typedef struct {
    int nclasses;           /*number of classes */
    int *classes;           /*array of the class names */
    int *npoints_for_class; /*number of examples contained in each class */
    int nvars;              /*number of predictor variables */
    double **mean;       /*for each class, the mean value of the examples stored
                            in an array of length nvars */
    double ***covar;     /*for each class, the covariance matrix of the esamples
                            stored in a matrix of dimension nvars x nvars */
    double ***inv_covar; /*for each class, the inverse of the covariance matrix
                            stored in a matrix of dimension nvars x nvars */
    double *priors;      /* prior probabilities of each class */
    double *det;         /*for each class, the determinant of the inverse of the
                            covariance matrix */
    Features features;   /*the features used for the model development */
} GaussianMixture;

typedef struct {
    int nsamples;  /*number of examples */
    int nvars;     /*number of variables */
    double **data; /*the data */
    int *class;    /*their classes */
    int k;
    Features features; /*the features used for the model development */
} NearestNeighbor;

typedef struct {
    int d;
    int i1;
    double *x1;
    int y1;
    int i2;
    double *x2;
    int y2;
    double w_coeff;
    double b;
} SVM_direct_kernel;

typedef struct {
    int N; /*number of examples */
    int d; /*number of features */
    int orig_d;
    double C;         /*bias/variance parameter */
    double tolerance; /*tolerance for testing KKT conditions */
    double
        eps; /*convergence parameters:used in both takeStep and mqc functions */
    double two_sigma_squared; /*kernel parameter */
    double *alph;             /*lagrangian coefficients */
    double b;                 /*offset */
    double *w;             /*hyperplane parameters (linearly separable  case) */
    double *error_cache;   /*error for each training point */
    double **dense_points; /*training data */
    int *target;           /*class labels */
    int kernel_type;   /*kernel type:1 linear, 2 gaussian, 3 squared gaussian */
    int end_support_i; /*set to N, never changed */
    double (*learned_func)(); /*the SVM */
    double (*kernel_func)();  /*the kernel */
    double delta_b;           /*gap between old and updated offset */
    double *precomputed_self_dot_product; /*squared norm of the training data */
    double *Cw; /*weighted bias/variance parameter (sen/spe tuning) */
    SVM_direct_kernel *models;
    double **dot_prod;
    double **H;
    int n_direct_kernel;
    int non_bound_support; /*number of non bound SV */
    int bound_support;     /*number of bound SV */
    int maxloops;
    int convergence;
    int verbose;
    double cost;       /*sen/spe cost (only for single svm) */
    Features features; /*the features used for the model development */
} SupportVectorMachine;

typedef struct {
    SupportVectorMachine *svm; /*the svm */
    int nsvm;                  /*number of svm */
    double *weights;           /*their weights */
    double w;                  /*cost-sensitive parameter use (for boosting) */
    double **w_evolution;
    Features features; /*the features used for the model development */
} BSupportVectorMachine;

typedef struct
/*indeces of a matrix (row,col) and blob thay belog to (number) */
{
    int row; /*row index of a point belonging to a blob */
    int col; /*row index of a point belonging to a blob */
    int number /* blob number the point belong to */;
} Blob;

typedef struct
/*geographical coordinates of the center of a blob and minimum
   value of the blob itself */
{
    double east;  /*east value of the center */
    double north; /*north value of the center */
    double min;   /*minimum value of the blob */
    double max;   /*minimum value of the blob */
    int n;        /*number of points whitin the blob */
} BlobSites;
