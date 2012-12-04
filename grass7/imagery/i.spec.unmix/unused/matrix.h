/**************************************************************************
**
** Copyright (C) 1993 David E. Steward & Zbigniew Leyk, all rights reserved.
**
**			     Meschach Library
** 
** This Meschach Library is provided "as is" without any express 
** or implied warranty of any kind with respect to this software. 
** In particular the authors shall not be liable for any direct, 
** indirect, special, incidental or consequential damages arising 
** in any way from use of the software.
** 
** Everyone is granted permission to copy, modify and redistribute this
** Meschach Library, provided:
**  1.  All copies contain this copyright notice.
**  2.  All modified copies shall carry a notice stating who
**      made the last modification and the date of such modification.
**  3.  No charge is made for this software or works derived from it.  
**      This clause shall not be construed as constraining other software
**      distributed on the same medium as this software, nor is a
**      distribution fee considered a charge.
**
***************************************************************************/


#ifndef	__MATRIX_H__
#define	__MATRIX_H__


#include <grass/config.h>
#include <grass/gis.h>

/* vector definition */
typedef	struct	{
	unsigned int	dim, max_dim;
	double	*ve;
} VEC;

/* matrix definition */
typedef	struct	{
	unsigned int	m, n;
	unsigned int	max_m, max_n, max_size;
	double	**me,*base;	/* base is base of alloc'd mem */
} MAT;

/* band matrix definition */
typedef struct {
       MAT   *mat;       /* matrix */
       int   lb,ub;    /* lower and upper bandwidth */
} BAND;


/* permutation definition */
typedef	struct	{
	unsigned int	size, max_size, *pe;
} PERM;

/* integer vector definition */
typedef struct	{
	unsigned int	dim, max_dim;
	int	*ive;
} IVEC;


void	m_version( void );

/* allocate one object of given type */
#define	NEW(type)	((type *)G_calloc((size_t)1, sizeof(type)))

/* allocate num objects of given type */
#define	NEW_A(num,type)	((type *)G_calloc((size_t)(num), sizeof(type)))

 /* re-allocate arry to have num objects of the given type */
#define	RENEW(var,num,type) \
    ((var)=(type *)((var) ? \
		    G_realloc((char *)(var), (num)*sizeof(type))) : \
		    G_calloc((size_t)(num), sizeof(type))))

#define	MEMCOPY(from,to,n_items,type) \
 MEM_COPY((char *)(from), (char *)(to), (unsigned)(n_items)*sizeof(type))


/* type independent min and max operations */
#ifndef max
#define	max(a,b)	((a) > (b) ? (a) : (b))
#endif
#ifndef min
#define	min(a,b)	((a) > (b) ? (b) : (a))
#endif


/* for input routines */
#define MAXLINE 81


#if 0
/* Dynamic memory allocation */
/* Should use M_FREE/V_FREE/PX_FREE in programs instead of m/v/px_free()
   as this is considerably safer -- also provides a simple type check ! */

/* get/resize vector to given dimension */
extern	VEC *v_get(int), *v_resize(VEC *,int);
/* get/resize matrix to be m x n */
extern	MAT *m_get(int,int), *m_resize(MAT *,int,int);
/* get/resize permutation to have the given size */
extern	PERM *px_get(int), *px_resize(PERM *,int);
/* get/resize an integer vector to given dimension */
extern	IVEC *iv_get(int), *iv_resize(IVEC *,int);
/* get/resize a band matrix to given dimension */
extern  BAND *bd_get(int,int,int), *bd_resize(BAND *,int,int,int);

/* free (de-allocate) (band) matrices, vectors, permutations and 
   integer vectors */
extern  int iv_free(IVEC *);
extern	int m_free(MAT *);
extern  int v_free(VEC *);
extern  int px_free(PERM *);
extern  int bd_free(BAND *);


/* MACROS */

/* macros that also check types and sets pointers to NULL */
#define	M_FREE(mat)	( m_free(mat),	(mat)=(MAT *)NULL )
#define V_FREE(vec)	( v_free(vec),	(vec)=(VEC *)NULL )
#define	PX_FREE(px)	( px_free(px),	(px)=(PERM *)NULL )
#define	IV_FREE(iv)	( iv_free(iv),	(iv)=(IVEC *)NULL )

#define MAXDIM  	2001

#endif

/* Entry level access to data structures */
#ifdef DEBUG

/* returns x[i] */
#define	v_entry(x,i)	(((i) < 0 || (i) >= (x)->dim) ? \
			 error(E_BOUNDS,"v_entry"), 0.0 : (x)->ve[i] )

/* x[i] <- val */
#define	v_set_val(x,i,val) ((x)->ve[i] = ((i) < 0 || (i) >= (x)->dim) ? \
			    error(E_BOUNDS,"v_set_val"), 0.0 : (val))

/* x[i] <- x[i] + val */
#define	v_add_val(x,i,val) ((x)->ve[i] += ((i) < 0 || (i) >= (x)->dim) ? \
			    error(E_BOUNDS,"v_add_val"), 0.0 : (val))

/* x[i] <- x[i] - val */
#define	v_sub_val(x,i,val) ((x)->ve[i] -= ((i) < 0 || (i) >= (x)->dim) ? \
			    error(E_BOUNDS,"v_sub_val"), 0.0 : (val))

/* returns A[i][j] */
#define	m_entry(A,i,j)	(((i) < 0 || (i) >= (A)->m || \
			  (j) < 0 || (j) >= (A)->n) ? \
			 error(E_BOUNDS,"m_entry"), 0.0 : (A)->me[i][j] )

/* A[i][j] <- val */
#define	m_set_val(A,i,j,val) ((A)->me[i][j] = ((i) < 0 || (i) >= (A)->m || \
					       (j) < 0 || (j) >= (A)->n) ? \
			      error(E_BOUNDS,"m_set_val"), 0.0 : (val) )

/* A[i][j] <- A[i][j] + val */
#define	m_add_val(A,i,j,val) ((A)->me[i][j] += ((i) < 0 || (i) >= (A)->m || \
						(j) < 0 || (j) >= (A)->n) ? \
			      error(E_BOUNDS,"m_add_val"), 0.0 : (val) )

/* A[i][j] <- A[i][j] - val */
#define	m_sub_val(A,i,j,val) ((A)->me[i][j] -= ((i) < 0 || (i) >= (A)->m || \
						(j) < 0 || (j) >= (A)->n) ? \
			      error(E_BOUNDS,"m_sub_val"), 0.0 : (val) )
#else

/* returns x[i] */
#define	v_entry(x,i)		((x)->ve[i])

/* x[i] <- val */
#define	v_set_val(x,i,val)	((x)->ve[i]  = (val))

/* x[i] <- x[i] + val */
#define	v_add_val(x,i,val)	((x)->ve[i] += (val))

 /* x[i] <- x[i] - val */
#define	v_sub_val(x,i,val)	((x)->ve[i] -= (val))

/* returns A[i][j] */
#define	m_entry(A,i,j)		((A)->me[i][j])

/* A[i][j] <- val */
#define	m_set_val(A,i,j,val)	((A)->me[i][j]  = (val) )

/* A[i][j] <- A[i][j] + val */
#define	m_add_val(A,i,j,val)	((A)->me[i][j] += (val) )

/* A[i][j] <- A[i][j] - val */
#define	m_sub_val(A,i,j,val)	((A)->me[i][j] -= (val) )

#endif


/* I/O routines */
/* print x on file fp */
void v_foutput(FILE *fp,VEC *x),
       /* print A on file fp */
	m_foutput(FILE *fp,MAT *A),
       /* print px on file fp */
	px_foutput(FILE *fp,PERM *px);
/* print ix on file fp */
void iv_foutput(FILE *fp,IVEC *ix);

/* Note: if out is NULL, then returned object is newly allocated;
        Also: if out is not NULL, then that size is assumed */

/* read in vector from fp */
VEC *v_finput(FILE *fp,VEC *out);
/* read in matrix from fp */
MAT *m_finput(FILE *fp,MAT *out);
/* read in permutation from fp */
PERM *px_finput(FILE *fp,PERM *out);
/* read in int vector from fp */
IVEC *iv_finput(FILE *fp,IVEC *out);

/* fy_or_n -- yes-or-no to question in string s
        -- question written to stderr, input from fp 
        -- if fp is NOT a tty then return y_n_dflt */
int fy_or_n(FILE *fp,char *s);

/* yn_dflt -- sets the value of y_n_dflt to val */
int yn_dflt(int val);

/* fin_int -- return integer read from file/stream fp
        -- prompt s on stderr if fp is a tty
        -- check that x lies between low and high: re-prompt if
                fp is a tty, error exit otherwise
        -- ignore check if low > high           */
int fin_int(FILE *fp,char *s,int low,int high);

/* fin_double -- return double read from file/stream fp
        -- prompt s on stderr if fp is a tty
        -- check that x lies between low and high: re-prompt if
                fp is a tty, error exit otherwise
        -- ignore check if low > high           */
double fin_double(FILE *fp,char *s,double low,double high);

/* it skips white spaces and strings of the form #....\n
   Here .... is a comment string */
int skipjunk(FILE *fp);


/* MACROS */

/* macros to use stdout and stdin instead of explicit fp */
#define	v_output(vec)	v_foutput(stdout,vec)
#define	v_input(vec)	v_finput(stdin,vec)
#define	m_output(mat)	m_foutput(stdout,mat)
#define	m_input(mat)	m_finput(stdin,mat)
#define	px_output(px)	px_foutput(stdout,px)
#define	px_input(px)	px_finput(stdin,px)
#define	iv_output(iv)	iv_foutput(stdout,iv)
#define	iv_input(iv)	iv_finput(stdin,iv)

/* general purpose input routine; skips comments # ... \n */
#define	finput(fp,prompt,fmt,var) \
	( ( isatty(fileno(fp)) ? fprintf(stderr,prompt) : skipjunk(fp) ), \
							fscanf(fp,fmt,var) )
#define	input(prompt,fmt,var)	finput(stdin,prompt,fmt,var)
#define	fprompter(fp,prompt) \
	( isatty(fileno(fp)) ? fprintf(stderr,prompt) : skipjunk(fp) )
#define	prompter(prompt)	fprompter(stdin,prompt)
#define	y_or_n(s)	fy_or_n(stdin,s)
#define	in_int(s,lo,hi)	fin_int(stdin,s,lo,hi)
#define	in_double(s,lo,hi)	fin_double(stdin,s,lo,hi)

/* Copying routines */
/* copy in to out starting at out[i0][j0] */
extern	MAT	*_m_copy(MAT *in,MAT *out,unsigned int i0,unsigned int j0),
		* m_move(MAT *in, int, int, int, int, MAT *out, int, int),
		*vm_move(VEC *in, int, MAT *out, int, int, int, int);
/* copy in to out starting at out[i0] */
extern	VEC	*_v_copy(VEC *in,VEC *out,unsigned int i0),
		* v_move(VEC *in, int, int, VEC *out, int),
		*mv_move(MAT *in, int, int, int, int, VEC *out, int);
extern	PERM	*px_copy(PERM *in,PERM *out);
extern	IVEC	*iv_copy(IVEC *in,IVEC *out),
		*iv_move(IVEC *in, int, int, IVEC *out, int);
extern  BAND    *bd_copy(BAND *in,BAND *out);


/* MACROS */
#define	m_copy(in,out)	_m_copy(in,out,0,0)
#define	v_copy(in,out)	_v_copy(in,out,0)


/* Initialisation routines -- to be zero, ones, random or identity */
extern	VEC     *v_zero(VEC *), *v_rand(VEC *), *v_ones(VEC *);
extern	MAT     *m_zero(MAT *), *m_ident(MAT *), *m_rand(MAT *),
						*m_ones(MAT *);
extern	PERM    *px_ident(PERM *);
extern  IVEC    *iv_zero(IVEC *);

/* Basic vector operations */
extern	VEC	*sv_mlt(double,VEC *,VEC *),	/* out <- s.x */
		*mv_mlt(MAT *,VEC *,VEC *),	/* out <- A.x */
		*vm_mlt(MAT *,VEC *,VEC *),	/* out^T <- x^T.A */
		*v_add(VEC *,VEC *,VEC *), 	/* out <- x + y */
                *v_sub(VEC *,VEC *,VEC *),	/* out <- x - y */
		*px_vec(PERM *,VEC *,VEC *),	/* out <- P.x */
		*pxinv_vec(PERM *,VEC *,VEC *),	  /* out <- P^{-1}.x */
		*v_mltadd(VEC *,VEC *,double,VEC *),   /* out <- x + s.y */
#ifdef PROTOTYPES_IN_STRUCT
		*v_map(double (*f)(double),VEC *,VEC *),  
                                                 /* out[i] <- f(x[i]) */
		*_v_map(double (*f)(void *,double),void *,VEC *,VEC *),
#else
		*v_map(double (*f)(),VEC *,VEC *), /* out[i] <- f(x[i]) */
		*_v_map(double (*f)(),void *,VEC *,VEC *),
#endif
		*v_lincomb(int,VEC **,double *,VEC *),   
                                                 /* out <- sum_i s[i].x[i] */
                *v_linlist(VEC *out,VEC *v1,double a1,...);
                                              /* out <- s1.x1 + s2.x2 + ... */

/* returns min_j x[j] (== x[i]) */
extern	double	v_min(VEC *, int *), 
     /* returns max_j x[j] (== x[i]) */		
        v_max(VEC *, int *), 
        /* returns sum_i x[i] */
        v_sum(VEC *);

/* Hadamard product: out[i] <- x[i].y[i] */
extern	VEC	*v_star(VEC *, VEC *, VEC *),
                 /* out[i] <- x[i] / y[i] */
		*v_slash(VEC *, VEC *, VEC *),
               /* sorts x, and sets order so that sorted x[i] = x[order[i]] */ 
		*v_sort(VEC *, PERM *);

/* returns inner product starting at component i0 */
extern	double	_in_prod(VEC *x,VEC *y,unsigned int i0), 
                /* returns sum_{i=0}^{len-1} x[i].y[i] */
                __ip__(double *,double *,int);

/* see v_mltadd(), v_add(), v_sub() and v_zero() */
extern	void	__mltadd__(double *,double *, double, int),
		__add__(double *, double *, double *, int),
		__sub__(double *, double *, double *, int),
                __smlt__(double *, double, double *, int),
		__zero__(double *,int);


/* MACRO */
/* usual way of computing the inner product */
#define	in_prod(a,b)	_in_prod(a,b,0)

/* Norms */
/* scaled vector norms -- scale == NULL implies unscaled */
               /* returns sum_i |x[i]/scale[i]| */
extern	double	_v_norm1(VEC *x,VEC *scale),   
               /* returns (scaled) Euclidean norm */
                _v_norm2(VEC *x,VEC *scale),
               /* returns max_i |x[i]/scale[i]| */
		_v_norm_inf(VEC *x,VEC *scale);

/* unscaled matrix norms */
extern double m_norm1(MAT *A), m_norm_inf(MAT *A), m_norm_frob(MAT *A);


/* MACROS */
/* unscaled vector norms */
#define	v_norm1(x)	_v_norm1(x,VNULL)
#define	v_norm2(x)	_v_norm2(x,VNULL)
#define	v_norm_inf(x)	_v_norm_inf(x,VNULL)

/* Basic matrix operations */
extern	MAT	*sm_mlt(double s,MAT *A,MAT *out), 	/* out <- s.A */
		*m_mlt(MAT *A,MAT *B,MAT *out),	/* out <- A.B */
		*mmtr_mlt(MAT *A,MAT *B,MAT *out),	/* out <- A.B^T */
		*mtrm_mlt(MAT *A,MAT *B,MAT *out),	/* out <- A^T.B */
		*m_add(MAT *A,MAT *B,MAT *out),	/* out <- A + B */
		*m_sub(MAT *A,MAT *B,MAT *out),	/* out <- A - B */
		*sub_mat(MAT *A,unsigned int,unsigned int,unsigned int,unsigned int,MAT *out),
		*m_transp(MAT *A,MAT *out),		/* out <- A^T */
                /* out <- A + s.B */ 
		*ms_mltadd(MAT *A,MAT *B,double s,MAT *out);   


extern  BAND    *bd_transp(BAND *in, BAND *out);   /* out <- A^T */
extern	MAT	*px_rows(PERM *px,MAT *A,MAT *out),	/* out <- P.A */
		*px_cols(PERM *px,MAT *A,MAT *out),	/* out <- A.P^T */
		*swap_rows(MAT *,int,int,int,int),
		*swap_cols(MAT *,int,int,int,int),
                 /* A[i][j] <- out[j], j >= j0 */
		*_set_col(MAT *A,unsigned int i,VEC *out,unsigned int j0),
                 /* A[i][j] <- out[i], i >= i0 */
		*_set_row(MAT *A,unsigned int j,VEC *out,unsigned int i0);

extern	VEC	*get_row(MAT *,unsigned int,VEC *),
		*get_col(MAT *,unsigned int,VEC *),
		*sub_vec(VEC *,int,int,VEC *),
                   /* out <- x + s.A.y */
		*mv_mltadd(VEC *x,VEC *y,MAT *A,double s,VEC *out),
                  /* out^T <- x^T + s.y^T.A */
		*vm_mltadd(VEC *x,VEC *y,MAT *A,double s,VEC *out);


/* MACROS */
/* row i of A <- vec */
#define	set_row(mat,row,vec)	_set_row(mat,row,vec,0) 
/* col j of A <- vec */
#define	set_col(mat,col,vec)	_set_col(mat,col,vec,0)


/* Basic permutation operations */
extern	PERM	*px_mlt(PERM *px1,PERM *px2,PERM *out),	/* out <- px1.px2 */
		*px_inv(PERM *px,PERM *out),	/* out <- px^{-1} */
                 /* swap px[i] and px[j] */
		*px_transp(PERM *px,unsigned int i,unsigned int j);

     /* returns sign(px) = +1 if px product of even # transpositions
                           -1 if ps product of odd  # transpositions */
extern	int	px_sign(PERM *);


/* Basic integer vector operations */
extern	IVEC	*iv_add(IVEC *ix,IVEC *iy,IVEC *out),  /* out <- ix + iy */
		*iv_sub(IVEC *ix,IVEC *iy,IVEC *out),  /* out <- ix - iy */
        /* sorts ix & sets order so that sorted ix[i] = old ix[order[i]] */
		*iv_sort(IVEC *ix, PERM *order);


/* miscellaneous functions */
double	square(double x), 	/* returns x^2 */
  cube(double x), 		/* returns x^3 */
  mrand(void);                  /* returns random # in [0,1) */

void	smrand(int seed),            /* seeds mrand() */
  mrandlist(double *x, int len);       /* generates len random numbers */

void    m_dump(FILE *fp,MAT *a), px_dump(FILE *,PERM *px),
        v_dump(FILE *fp,VEC *x), iv_dump(FILE *fp, IVEC *ix);

MAT *band2mat(BAND *bA, MAT *A);
BAND *mat2band(MAT *A, int lb,int ub, BAND *bA);


/* miscellaneous constants */
#define	VNULL	((VEC *)NULL)
#define	MNULL	((MAT *)NULL)
#define	PNULL	((PERM *)NULL)
#define	IVNULL	((IVEC *)NULL)
#define BDNULL  ((BAND *)NULL)


/* varying number of arguments */
#include <stdarg.h>

/* prototypes */

int v_get_vars(int dim,...);
int iv_get_vars(int dim,...);
int m_get_vars(int m,int n,...);
int px_get_vars(int dim,...);

int v_resize_vars(int new_dim,...);
int iv_resize_vars(int new_dim,...);
int m_resize_vars(int m,int n,...);
int px_resize_vars(int new_dim,...);

int v_free_vars(VEC **,...);
int iv_free_vars(IVEC **,...);
int px_free_vars(PERM **,...);
int m_free_vars(MAT **,...);


#endif /* __MATRIX_H__ */

