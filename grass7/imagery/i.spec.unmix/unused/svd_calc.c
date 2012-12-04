/* Matrix inversion with Singular Value Decomposition
 * (c) 1998 Markus Neteler, Hannover
 *
 * 20. Nov. 1998 - V 1.0
 *
 ****************************************************************************
 ** Based on Meschach Library
 ** Copyright (C) 1993 David E. Steward & Zbigniew Leyk, all rights reserved.
 ****************************************************************************
 *
 * Cited references are from
 *    Steward, D.E, Leyk, Z. 1994: Meschach: Matrix computations in C.
 *       Proceedings of the centre for Mathematics and its Applicaions.
 *       The Australian National University. Vol. 32.
 *       ISBN 0 7315 1900 0
 * 
 *****/


#define abs(x) ((x)<0?-(x):(x))

#define GLOBAL
#define errmesg(mesg)   fprintf(stderr,"Error: %s error: line %d\n",mesg,__LINE__)

#include <stdio.h>
#include <math.h>
#include "matrix.h"
#include "matrix2.h"
#include "global.h"


void calc_inverse(M) /* returns inverted matrix MM_inverse, which is globally defined*/
MAT *M;
{
   MAT *U, *U_trans, *V, *Temp1, *Temp2, *MM_inverse_pre, *Svdvals_mat_inv, *C, *D;
   VEC *svdvals;
   int i, j, m_dim, n_dim;

   m_dim = M->m;
   n_dim = M->n;
   U= m_get(m_dim,m_dim);  /* create empty matrices */
   V= m_get(n_dim,n_dim);
   svdvals = svd(M,U,V,VNULL);

/* check singular values of Matrix A
 * Ref: Boardman, J.W. 1989: Inversion of imaging spectrometry data
 *           using singular value decomposition.  IGARSS 1989: 12th Canadian
 *           symposium on Remote Sensing. Vol.4 pp.2069-2072
 */

   /* debug output */
   if (!flag.quiet->answer)
   {
    fprintf(stderr, "SVD-Vector of M: ");
    v_output(svdvals); 
   }
  
/* Now we have U, V, svdvals */

/* convert vector svdvals to diagonal matrix 1/W: */
   Svdvals_mat_inv = m_get(m_dim,n_dim);
   for (i=0; i < m_dim; i++)
	Svdvals_mat_inv->me[i][i] = (double)(1/svdvals->ve[i]);

/* calculate transpose of U */
   U_trans = m_transp(U, MNULL);

   Temp1   = m_mlt(Svdvals_mat_inv, V, MNULL);
   Temp2   = m_mlt(U_trans, Temp1, MNULL);    /* why that? no idea */
   MM_inverse_pre = m_transp(Temp2, MNULL);
   MM_inverse = m_get(m_dim,n_dim);

/* set values nearly zero to to zero */

   for (i=0; i < MM_inverse_pre->m ; i++)   /*  rowwise */
     for (j=0; j < MM_inverse_pre->n; j++)  /*  colwise */
       {
         if (abs(MM_inverse_pre->me[i][j]) > 0.00000000000001)
            MM_inverse->me[i][j]= MM_inverse_pre->me[i][j];
        else 
            MM_inverse->me[i][j]= 0;
       }

   M_FREE(Svdvals_mat_inv);
   M_FREE(U_trans);
   M_FREE(Temp1);
   M_FREE(Temp2);
   M_FREE(MM_inverse_pre);

  /***************************************************************
   * Error check for SVD
   * check reconstruction of M - taken from torture.c (Meschach)
   ****/

    C = m_get(M->m,M->n);
    D = m_get(M->m,M->n);
    for ( i = 0; i < min(M->m,M->n); i++ )
	m_set_val(D,i,i,v_entry(svdvals,i));
    mtrm_mlt(U,D,C);
    m_mlt(C,V,D);
    m_sub(M,D,D);
    if ( m_norm1(D) >= MACHEPS*m_norm1(V)*m_norm_inf(U)*m_norm1(M) )
	if (!flag.quiet->answer)
		fprintf(stderr, "ERROR: SVD reconstruction error = %g [allowed MACHEPS = %g]\n",\
			m_norm1(D), MACHEPS);
               
    /* check orthogonality of U and V */
    M_FREE(D);
    D = m_resize(D,U->n,U->n);
    mtrm_mlt(U,U,D);
    for ( i = 0; i < D->m; i++ )
	m_set_val(D,i,i,m_entry(D,i,i)-1.0);
    if ( m_norm1(D) >= MACHEPS*m_norm1(U)*m_norm_inf(U)*5 )
    	if (!flag.quiet->answer)
 		fprintf(stderr, "ERROR: SVD orthogonality error (V) = %g [allowed MACHEPS = %g\n",\
	   	    m_norm1(D), MACHEPS);

    M_FREE(D);
    D = m_resize(D,V->n,V->n);
    mtrm_mlt(V,V,D);
    for ( i = 0; i < D->m; i++ )
	m_set_val(D,i,i,m_entry(D,i,i)-1.0);
    if ( m_norm1(D) >= MACHEPS*m_norm1(V)*m_norm_inf(V)*5 )
	if (!flag.quiet->answer)
		fprintf(stderr, "ERROR: SVD orthogonality error (U) = %g [allowed MACHEPS = %g\n",\
			m_norm1(D), MACHEPS);

    for ( i = 0; i < svdvals->dim; i++ )
	if ( v_entry(svdvals,i) < 0 || (i < svdvals->dim-1 &&
				  v_entry(svdvals,i+1) > v_entry(svdvals,i)) )
	    break;
	    
    /* check next only, when svdvals->dim high enough: */
    if (( i < svdvals->dim ) && (svdvals->dim > 2))
	if (!flag.quiet->answer)
		fprintf(stderr, "ERROR: SVD sorting error\n");


   /*free the memory*/
   M_FREE(V);
   M_FREE(U);
   V_FREE(svdvals);
   M_FREE(C);
   M_FREE(D);
}
