#include <grass/gis.h>
#include "global.h"


void linear_solve(A,y,x,r,c)
     /* solve linear system Ax=y, where A is a matrix of r x c
	dimension. Memory for x stored
     */
     double **A,*y,**x;
     int r,c;
{

  double **tA,**B, **inv_B;
  double *C,*D;
  int i;


  transpose_double_matrix_rectangular(A,r,c,&tA);
  
  
  B=(double**)G_calloc(c,sizeof(double*));
  for(i=0;i<c;i++)
    B[i]=(double*)G_calloc(c,sizeof(double));

  product_double_matrix_double_matrix(tA,A,c,r,c,B);

  inv_B=(double**)G_calloc(c,sizeof(double*));
  for(i=0;i<c;i++)
    inv_B[i]=(double*)G_calloc(c,sizeof(double));

  inverse_of_double_matrix(B,inv_B,c);

  C=(double*)G_calloc(c,sizeof(double));
  product_double_matrix_double_vector(tA,y,c,r,C);

  *x=(double*)G_calloc(c,sizeof(double));
  product_double_matrix_double_vector(inv_B,C,c,c,*x);
}
