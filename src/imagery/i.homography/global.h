/*****
      list of RASTERLISTTYPE1

      name1	class1
      name2	class2
      ...	...
*****/

/*****
      list of RASTERLISTTYPE2

      name1	additional_name1	moments1
      name2	additional_name2	moments2
      ...	...			...
*****/

/*****
      classification CLASSIFICATION1

      given a list RASTERLISTTYPE1, optionally build a filter,
      build the pca model, transform data in pc space,
      compute a gaussian mixture
*****/

/*****
      classification CLASSIFICATION2

      given a list RASTERLISTTYPE2, use a list of sites as training,
      build a window round each site, using the moments compute mean
      or mean and var of the value of the raster maps within the
      window to form predictor variables, compute a gaussian mixture
      or a nearest neighbour model
*****/


#include <grass/gis.h>
#include <grass/site.h>
#include "func.h"

#define PIG 3.141593

#define TRUE 1
#define FALSE 0

#define GaussianMixture 1
#define NearestNeighbour 2

#define TREE 1
#define BOOSTING 2
#define BAGGING 3

typedef struct
/*manegement of  list of type 1*/
{
  char **mapnames; /*array of raster map names*/
  char **mapclass; /*class of each raster map*/
  int nsamples; /*number of raster map*/
  int rows; /*rows number of each raster map*/
  int cols; /*cols number of each raster map*/
  double **samples; /*for each map, the values of the map stored in an array
		      of length rows x cols*/
} Maps;

typedef struct
/*manegement of  list of type 2*/
{
  char **mapnames; /*array of raster map names*/
  char **varnames; /*additional name for each raster map*/
  int nvar; /*number of raster maps*/
  int rows; /*rows number of each raster map*/
  int cols; /*cols number of each raster map*/
  int *moments; /*for each map, the number of moments of the distribution 
		  to be considered for the classification:
		  1 = mean
		  2 = mean and var*/
  double ***mapvalues; /*for each map, the values of the map stored in a matrix
			 of dimension rows x cols*/
} Variables;

typedef struct
/*manegement of lists of site files*/
{
  char *name; /*name of site file*/
  Site **sites; /*sites contained within the site file*/
  int nsites; /*number of sites*/
} ListSite;


typedef struct
/*filter structure, usually considered as average of matricial examples
  (usually small raster maps)*/
{
  int rows;  /*rows number of the filter*/
  int cols;  /*cols number of the filter*/
  double **values; /*values of the filter, stored in a matrix
		     of dimension rows x cols*/
} Filter;

typedef struct
/*principal components structure. Examples are in matricial form 
    (usually small raster maps) but matricial examples are here 
    considered as array of length rows x cols*/
{
  int rows; /*rows number of the raster maps used to build the PC model*/
  int cols; /*cols number of the raster maps used to build the PC model*/
  double *mean; /*the mean value of the examples, stored in an
		  array of dimension rows x cols*/
  double *sd; /*the standard deviation of the examples, stored in an
		array of dimension rows x cols*/
  double **covar; /*covariance matrix of the examples, stored in a
		    matrix of dimension (rows x cols)^2*/
  double *eigval; /*eigenvalues of the covariance matrix*/
  double **eigmat; /*eigenvectors matrix of the covariance matrix.
		     Each column is the eigenvector corresponding to  
		     an eigenvalues*/
  int correlation; /*boolean:
		     0 = covariance matrix computed
		     1 = correlation matrix computed*/
  int standardize; /*boolean:
		     0 = examples are not standardized
		     1 = examples are standardized: E <- (E-mean(E))/sd(E)*/
} Pca;

typedef struct
/*gaussian mixture models structure*/
{
  int nclasses; /*number of classes*/
  char **classes; /*array of the class names*/
  int *nsamples; /*number of examples contained in each class*/
  int nvars; /*number of predictor variables*/
  double **mean; /*for each class, the mean value of the examples stored
		   in an array of length nvars*/
  double ***covar; /*for each class, the covariance matrix of the esamples
		     stored in a matrix of dimension nvars x nvars*/
  double ***inv_covar; /*for each class, the inverse of the covariance matrix
			 stored in a matrix of dimension nvars x nvars*/
  double *priors; /* prior probabilities of each class*/
  double *det; /*for each class, the determinant of the inverse of the
		 covariance matrix*/
} NormalModel;

typedef struct
/*Non-intuitive structure: is almost always derived from 
  the ListSite and Variables structures*/
{
  int nclasses; /*number of classes*/
  int *number_of_data_for_class; /*number of elements of each class*/
  int rows; /*rows number to be considered for building the window 
	      around each site*/
  int cols;  /*cols number to be considered for building the window 
	       around each site*/
  int nsites; /*number of sites*/
  double ****trdata; /*for each raster map, for each class, 
		       for each sample within the class, 
		       the values of the raster map contained within the 
		       window and stored in an array of length rows*cols
		       = window size */
} Training;

typedef struct
/*nearest neighbour structure*/
{
  int nsites; /*number of examples*/
  int nvar; /*number of predictor variables*/
  double **values; /* for each example, the values of the predictors*/
  char **classes; /* array of the classes of each example*/
  int *num_classes; /*array of the classes of each example
		      in integer format (for compatibility)*/
} NN;

typedef struct
{
  double **data;
  char **classes;
  int npoints;
  int nvar;

  int nclasses;
  
  
  int *npoints_for_class;
  double *priors;
  char *class;


  int terminal;

  int left;
  int right;
  int var;
  double value;
} Node;

typedef struct
/*indeces of a matrix (row,col) and blob thay belog to (number)*/
{
  int row; /*row index of a point belonging to a blob*/
  int col; /*row index of a point belonging to a blob*/ 
  int number /* blob number the point belong to*/;
} Blob;

typedef struct
/*geographical coordinates of the center of a blob and minimum 
  value of the blob itself*/
{
  double east; /*east value of the center*/
  double north; /*north value of the center*/
  double min; /*minimum value of the blob*/
  int n; /*number of points whitin the blob*/
} BlobSites;


