/*
   The following routines are written and tested by Stefano Merler

   for

   structures SupportVectorMachine adn  BSupportVectorMachine management
 */


#include <grass/gis.h>
#include "global.h"
#include <stdio.h>
#include <math.h>
#include <stdlib.h>

static void svm_smo();
static double learned_func_linear();
static double learned_func_nonlinear();
static double rbf_kernel();
static double direct_kernel();
static double dot_product_func();
static int examineExample();
static int takeStep();
static int distance_from_span_sv();
double dot_product();

void compute_svm(SupportVectorMachine * svm, int n, int d, double **x, int *y,
		 int svm_kernel, double svm_kp, double svm_C, double svm_tol,
		 double svm_eps, int svm_maxloops, int svm_verbose,
		 double *svm_W)
{
    int i, j;

    svm->N = n;
    svm->d = d;
    svm->C = svm_C;
    svm->tolerance = svm_tol;
    svm->eps = svm_eps;
    svm->two_sigma_squared = svm_kp;
    svm->kernel_type = svm_kernel;
    svm->maxloops = svm_maxloops;
    svm->verbose = svm_verbose;
    svm->b = .0;

    if (svm_kernel != SVM_KERNEL_DIRECT) {
	svm->dense_points = (double **)G_calloc(n, sizeof(double *));
	for (i = 0; i < n; i++)
	    svm->dense_points[i] = (double *)G_calloc(d, sizeof(double));

	for (i = 0; i < n; i++)
	    for (j = 0; j < d; j++)
		svm->dense_points[i][j] = x[i][j];

	svm->w = (double *)G_calloc(d, sizeof(double));
    }

    svm->target = (int *)G_calloc(n, sizeof(int));
    for (i = 0; i < n; i++)
	svm->target[i] = y[i];

    svm->Cw = (double *)G_calloc(n, sizeof(double));
    svm->alph = (double *)G_calloc(n, sizeof(double));
    svm->error_cache = (double *)G_calloc(n, sizeof(double));
    for (i = 0; i < n; i++)
	svm->error_cache[i] = -y[i];

    svm->precomputed_self_dot_product = (double *)G_calloc(n, sizeof(double));

    for (i = 0; i < n; i++)
	svm->Cw[i] = svm->C * svm_W[i];

    if (svm_kernel == SVM_KERNEL_DIRECT) {
	int p_class;
	int n_class = 0;
	int index;
	int i1, i2;

	for (i = 0; i < n; i++)
	    if (y[i] == -1)
		n_class++;

	p_class = n - n_class;
	svm->d = p_class * n_class;
	svm->orig_d = d;

	svm->dense_points = (double **)G_calloc(n, sizeof(double *));
	for (i = 0; i < n; i++)
	    svm->dense_points[i] = (double *)G_calloc(svm->d, sizeof(double));

	svm->w = (double *)G_calloc(svm->d, sizeof(double));

	svm->dot_prod = (double **)G_calloc(n, sizeof(double *));
	for (i = 0; i < n; i++)
	    svm->dot_prod[i] = (double *)G_calloc(n, sizeof(double));

	for (i = 0; i < n; i++)
	    svm->dot_prod[i][i] = dot_product(x[i], x[i], d);

	for (i = 0; i < n; i++)
	    for (j = i + 1; j < n; j++)
		svm->dot_prod[j][i] = svm->dot_prod[i][j] =
		    dot_product(x[i], x[j], d);

	svm->models = (SVM_direct_kernel *)
	    G_calloc(svm->d, sizeof(SVM_direct_kernel));

	index = 0;
	for (i = 0; i < n; i++)
	    if (y[i] == -1)
		for (j = 0; j < n; j++)
		    if (y[j] == 1) {
			svm->models[index].i1 = i;
			svm->models[index].x1 = x[i];
			svm->models[index].y1 = y[i];
			svm->models[index].i2 = j;
			svm->models[index].x2 = x[j];
			svm->models[index].y2 = y[j];
			svm->models[index].d = d;
			svm->models[index].w_coeff = (y[j] - y[i]) /
			    (y[j] * svm->dot_prod[j][j] -
			     y[i] * svm->dot_prod[i][i] - (y[j] - y[i])
			     * svm->dot_prod[i][j]);
			svm->models[index].b =
			    y[i] -
			    svm->models[index].w_coeff * (y[i] *
							  svm->dot_prod[i][i]
							  +
							  y[j] *
							  svm->dot_prod[i]
							  [j]);
			index++;
		    }

	for (i = 0; i < n; i++)
	    for (j = 0; j < svm->d; j++) {
		i1 = svm->models[j].i1;
		i2 = svm->models[j].i2;

		svm->dense_points[i][j] = svm->models[j].w_coeff *
		    (y[i1] * svm->dot_prod[i1][i] +
		     y[i2] * svm->dot_prod[i2][i])
		    + svm->models[j].b;

		if (svm->dense_points[i][j] > 1.0)
		    svm->dense_points[i][j] = 1.0;
		else if (svm->dense_points[i][j] < -1.0)
		    svm->dense_points[i][j] = -1.0;
	    }

	svm->H = (double **)G_calloc(n, sizeof(double *));
	for (j = 0; j < n; j++)
	    svm->H[j] = (double *)G_calloc(n, sizeof(double));

	for (i = 0; i < n; i++)
	    svm->H[i][i] = dot_product_func(i, i, svm);

	for (i = 0; i < n; i++)
	    for (j = i + 1; j < n; j++)
		svm->H[j][i] = svm->H[i][j] = dot_product_func(i, j, svm);

    }

    svm_smo(svm);

    svm->non_bound_support = svm->bound_support = 0;
    for (i = 0; i < n; i++) {
	if (svm->alph[i] > 0) {
	    if (svm->alph[i] < svm->Cw[i])
		svm->non_bound_support++;
	    else
		svm->bound_support++;
	}
    }
}


static void svm_smo(SupportVectorMachine * SVM)
{
    int i, k;
    int numChanged;
    int examineAll;
    int nloops = 0;

    SVM->end_support_i = SVM->N;

    if (SVM->kernel_type == SVM_KERNEL_LINEAR) {
	SVM->kernel_func = dot_product_func;
	SVM->learned_func = learned_func_linear;
    }

    if (SVM->kernel_type == SVM_KERNEL_GAUSSIAN) {
	/*
	   SVM->precomputed_self_dot_product=(double *)G_calloc (SVM->N,sizeof(double));
	 */
	for (i = 0; i < SVM->N; i++)
	    SVM->precomputed_self_dot_product[i] =
		dot_product_func(i, i, SVM);
	SVM->kernel_func = rbf_kernel;
	SVM->learned_func = learned_func_nonlinear;
    }

    if (SVM->kernel_type == SVM_KERNEL_DIRECT) {
	SVM->kernel_func = dot_product_func;
	SVM->learned_func = learned_func_linear;
    }

    numChanged = 0;
    examineAll = 1;

    SVM->convergence = 1;
    while (SVM->convergence == 1 && (numChanged > 0 || examineAll)) {
	numChanged = 0;
	if (examineAll) {
	    for (k = 0; k < SVM->N; k++)
		numChanged += examineExample(k, SVM);
	}
	else {
	    for (k = 0; k < SVM->N; k++)
		if (SVM->alph[k] > 0 && SVM->alph[k] < SVM->Cw[k])
		    numChanged += examineExample(k, SVM);
	}
	if (examineAll == 1)
	    examineAll = 0;
	else if (numChanged == 0)
	    examineAll = 1;

	nloops += 1;
	if (nloops == SVM->maxloops)
	    SVM->convergence = 0;
	if (SVM->verbose == 1)
	    fprintf(stderr, "%6d\b\b\b\b\b\b\b", nloops);
    }
}


static double learned_func_linear(int k, SupportVectorMachine * SVM)
{
    double s = 0.0;
    int i;

    for (i = 0; i < SVM->d; i++)
	s += SVM->w[i] * SVM->dense_points[k][i];

    s -= SVM->b;

    return s;
}

static double learned_func_nonlinear(int k, SupportVectorMachine * SVM)
{
    double s = 0.0;
    int i;

    for (i = 0; i < SVM->end_support_i; i++)
	if (SVM->alph[i] > 0)
	    s += SVM->alph[i] * SVM->target[i] * SVM->kernel_func(i, k, SVM);

    s -= SVM->b;

    return s;
}

static double rbf_kernel(int i1, int i2, SupportVectorMachine * SVM)
{
    double s;

    s = dot_product_func(i1, i2, SVM);

    s *= -2;

    s += SVM->precomputed_self_dot_product[i1] +
	SVM->precomputed_self_dot_product[i2];

    return exp(-s / SVM->two_sigma_squared);
}


static double dot_product_func(int i1, int i2, SupportVectorMachine * SVM)
{
    double dot = 0.0;
    int i;

    for (i = 0; i < SVM->d; i++)
	dot += SVM->dense_points[i1][i] * SVM->dense_points[i2][i];

    return dot;
}

static int examineExample(int i1, SupportVectorMachine * SVM)
{
    double y1, alph1, E1, r1;

    y1 = SVM->target[i1];
    alph1 = SVM->alph[i1];

    if (alph1 > 0 && alph1 < SVM->Cw[i1])
	E1 = SVM->error_cache[i1];
    else
	E1 = SVM->learned_func(i1, SVM) - y1;

    r1 = y1 * E1;

    if ((r1 < -SVM->tolerance && alph1 < SVM->Cw[i1]) ||
	(r1 > SVM->tolerance && alph1 > 0)) {
	{
	    int k, i2;
	    double tmax;

	    for (i2 = (-1), tmax = 0, k = 0; k < SVM->end_support_i; k++)
		if (SVM->alph[k] > 0 && SVM->alph[k] < SVM->Cw[k]) {
		    double E2, temp;

		    E2 = SVM->error_cache[k];

		    temp = fabs(E1 - E2);

		    if (temp > tmax) {
			tmax = temp;
			i2 = k;
		    }
		}

	    if (i2 >= 0) {
		if (takeStep(i1, i2, SVM))
		    return 1;
	    }
	}
	{
	    int k0, k, i2;

	    for (k0 = (int)(G_drand48() * SVM->end_support_i), k = k0;
		 k < SVM->end_support_i + k0; k++) {
		i2 = k % SVM->end_support_i;
		if (SVM->alph[i2] > 0 && SVM->alph[i2] < SVM->Cw[i2]) {
		    if (takeStep(i1, i2, SVM))
			return 1;
		}
	    }
	}
	{
	    int k0, k, i2;

	    for (k0 = (int)(G_drand48() * SVM->end_support_i), k = k0;
		 k < SVM->end_support_i + k0; k++) {
		i2 = k % SVM->end_support_i;
		if (takeStep(i1, i2, SVM))
		    return 1;
	    }
	}
    }
    return 0;
}


static int takeStep(int i1, int i2, SupportVectorMachine * SVM)
{
    int y1, y2, s;
    double alph1, alph2;
    double a1, a2;
    double E1, E2, L, H, k11, k12, k22, eta, Lobj, Hobj;

    if (i1 == i2)
	return 0;

    alph1 = SVM->alph[i1];
    y1 = SVM->target[i1];
    if (alph1 > 0 && alph1 < SVM->Cw[i1])
	E1 = SVM->error_cache[i1];
    else
	E1 = SVM->learned_func(i1, SVM) - y1;


    alph2 = SVM->alph[i2];
    y2 = SVM->target[i2];
    if (alph2 > 0 && alph2 < SVM->Cw[i2])
	E2 = SVM->error_cache[i2];
    else
	E2 = SVM->learned_func(i2, SVM) - y2;

    s = y1 * y2;

    if (y1 == y2) {
	double gamma;

	gamma = alph1 + alph2;
	if (gamma - SVM->Cw[i1] > 0)
	    L = gamma - SVM->Cw[i1];
	else
	    L = 0.0;

	if (gamma < SVM->Cw[i2])
	    H = gamma;
	else
	    H = SVM->Cw[i2];


    }
    else {
	double gamma;

	gamma = alph2 - alph1;

	if (gamma > 0)
	    L = gamma;
	else
	    L = 0.0;

	if (SVM->Cw[i1] + gamma < SVM->Cw[i2])
	    H = SVM->Cw[i1] + gamma;
	else
	    H = SVM->Cw[i2];
    }

    if (L == H)
	return 0;

    if (SVM->kernel_type != SVM_KERNEL_DIRECT) {
	k11 = SVM->kernel_func(i1, i1, SVM);
	k12 = SVM->kernel_func(i1, i2, SVM);
	k22 = SVM->kernel_func(i2, i2, SVM);
    }
    else {
	k11 = SVM->H[i1][i1];
	k12 = SVM->H[i1][i2];
	k22 = SVM->H[i2][i2];
    }


    eta = 2 * k12 - k11 - k22;

    if (eta < 0) {
	a2 = alph2 + y2 * (E2 - E1) / eta;
	if (a2 < L)
	    a2 = L;
	else if (a2 > H)
	    a2 = H;
    }
    else {
	{
	    double c1, c2;

	    c1 = eta / 2;
	    c2 = y2 * (E1 - E2) - eta * alph2;
	    Lobj = c1 * L * L + c2 * L;
	    Hobj = c1 * H * H + c2 * H;
	}
	if (Lobj > Hobj + SVM->eps)
	    a2 = L;
	else if (Lobj < Hobj - SVM->eps)
	    a2 = H;
	else
	    a2 = alph2;
    }

    if (fabs(a2 - alph2) < SVM->eps * (a2 + alph2 + SVM->eps))
	return 0;

    a1 = alph1 - s * (a2 - alph2);

    if (a1 < 0) {
	a2 += s * a1;
	a1 = 0;
    }
    else if (a1 > SVM->Cw[i1]) {
	double t;

	t = a1 - SVM->Cw[i1];
	a2 += s * t;
	a1 = SVM->Cw[i1];
    }

    {
	double b1, b2, bnew;

	if (a1 > 0 && a1 < SVM->Cw[i1])
	    bnew =
		SVM->b + E1 + y1 * (a1 - alph1) * k11 + y2 * (a2 -
							      alph2) * k12;
	else {
	    if (a2 > 0 && a2 < SVM->Cw[i2])
		bnew =
		    SVM->b + E2 + y1 * (a1 - alph1) * k12 + y2 * (a2 -
								  alph2) *
		    k22;
	    else {
		b1 = SVM->b + E1 + y1 * (a1 - alph1) * k11 + y2 * (a2 -
								   alph2) *
		    k12;
		b2 = SVM->b + E2 + y1 * (a1 - alph1) * k12 + y2 * (a2 -
								   alph2) *
		    k22;
		bnew = (b1 + b2) / 2;
	    }
	}

	SVM->delta_b = bnew - SVM->b;
	SVM->b = bnew;
    }

    if (SVM->kernel_type == SVM_KERNEL_LINEAR ||
	SVM->kernel_type == SVM_KERNEL_DIRECT) {
	double t1, t2;
	int i;

	t1 = y1 * (a1 - alph1);
	t2 = y2 * (a2 - alph2);

	for (i = 0; i < SVM->d; i++)
	    SVM->w[i] +=
		SVM->dense_points[i1][i] * t1 + SVM->dense_points[i2][i] * t2;
    }

    {
	double t1, t2;
	int i;

	t1 = y1 * (a1 - alph1);
	t2 = y2 * (a2 - alph2);

	if (SVM->kernel_type != SVM_KERNEL_DIRECT) {
	    for (i = 0; i < SVM->end_support_i; i++)
		SVM->error_cache[i] +=
		    t1 * SVM->kernel_func(i1, i,
					  SVM) + t2 * SVM->kernel_func(i2, i,
								       SVM) -
		    SVM->delta_b;
	}
	else {
	    for (i = 0; i < SVM->end_support_i; i++)
		SVM->error_cache[i] +=
		    t1 * SVM->H[i1][i] + t2 * SVM->H[i2][i] - SVM->delta_b;
	}

    }

    SVM->alph[i1] = a1;
    SVM->alph[i2] = a2;

    return 1;


}

static int distance_from_span_sv(double **M, double *m, int n, double Const,
				 double **H, double *h, int mH,
				 double **K, double *k, int mK,
				 double eps, double threshold)
{
    int i, j, l;

    double **invM = NULL;
    double **HM = NULL, **HMH = NULL, *tnH = NULL, **HMK = NULL, **KM =
	NULL, **KMK = NULL, *tnK = NULL, **tH = NULL, **tK = NULL;
    double mMm;
    double gap;
    double *alpha = NULL, *beta = NULL;
    double L, f;
    double tmpalpha, tmpbeta, tmpL, tmpf;

    /*alloc memory */
    invM = (double **)G_calloc(n, sizeof(double *));
    for (i = 0; i < n; i++)
	invM[i] = (double *)G_calloc(n, sizeof(double));

    if (mH > 0) {
	HM = (double **)G_calloc(mH, sizeof(double *));
	for (i = 0; i < mH; i++)
	    HM[i] = (double *)G_calloc(n, sizeof(double));

	HMH = (double **)G_calloc(mH, sizeof(double *));
	for (i = 0; i < mH; i++)
	    HMH[i] = (double *)G_calloc(mH, sizeof(double));

	tnH = (double *)G_calloc(mH, sizeof(double));

	tH = (double **)G_calloc(n, sizeof(double *));
	for (i = 0; i < n; i++)
	    tH[i] = (double *)G_calloc(mH, sizeof(double));

	for (i = 0; i < mH; i++)
	    for (j = 0; j < n; j++)
		tH[j][i] = H[i][j];
    }

    if (mH > 0 && mK > 0) {
	HMK = (double **)G_calloc(mH, sizeof(double *));
	for (i = 0; i < mH; i++)
	    HMK[i] = (double *)G_calloc(mK, sizeof(double));
    }

    if (mK > 0) {
	KM = (double **)G_calloc(mK, sizeof(double *));
	for (i = 0; i < mK; i++)
	    KM[i] = (double *)G_calloc(n, sizeof(double));

	KMK = (double **)G_calloc(mK, sizeof(double *));
	for (i = 0; i < mK; i++)
	    KMK[i] = (double *)G_calloc(mK, sizeof(double));

	tnK = (double *)G_calloc(mK, sizeof(double));

	tK = (double **)G_calloc(n, sizeof(double *));
	for (i = 0; i < n; i++)
	    tK[i] = (double *)G_calloc(mK, sizeof(double));

	for (i = 0; i < mK; i++)
	    for (j = 0; j < n; j++)
		tK[j][i] = K[i][j];
    }

    /*compute inverse of M */
    inverse_of_double_matrix(M, invM, n);

    /*compute matrices products */
    if (mH > 0) {
	product_double_matrix_double_matrix(H, invM, mH, n, n, HM);
	product_double_matrix_double_matrix(HM, tH, mH, n, mH, HMH);
	product_double_matrix_double_vector(HM, m, mH, n, tnH);
	for (i = 0; i < mH; i++)
	    tnH[i] += 2. * h[i];
    }

    if (mH > 0 && mK > 0)
	product_double_matrix_double_matrix(HM, tK, mH, n, mK, HMK);

    if (mK > 0) {
	product_double_matrix_double_matrix(K, invM, mK, n, n, KM);
	product_double_matrix_double_matrix(KM, tK, mK, n, mK, KMK);
	product_double_matrix_double_vector(KM, m, mK, n, tnK);
	for (i = 0; i < mK; i++)
	    tnK[i] += 2. * k[i];
    }


    mMm = 0.0;
    for (i = 0; i < n; i++)
	for (j = 0; j < n; j++)
	    mMm += m[i] * m[j] * invM[i][j];
    mMm *= -.5;

    if (mH > 0)
	alpha = (double *)G_calloc(mH, sizeof(double));
    if (mK > 0)
	beta = (double *)G_calloc(mK, sizeof(double));

    gap = eps + 1;
    /*gradient ascendent on the dual Lagrangian */
    while (gap > eps) {
	if (mH > 0 && mK > 0) {
	    for (l = 0; l < mH; l++) {

		tmpalpha = .0;
		for (i = 0; i < mH; i++)
		    if (alpha[i] > 0)
			tmpalpha += HMH[i][l] * alpha[i];

		tmpalpha += tnH[l];


		for (i = 0; i < mK; i++)
		    tmpalpha += HMK[l][i] * beta[i];

		alpha[l] -= tmpalpha / HMH[l][l];

		if (alpha[l] < .0)
		    alpha[l] = .0;
	    }

	    for (l = 0; l < mK; l++) {
		tmpbeta = .0;
		for (i = 0; i < mK; i++)
		    tmpbeta += KMK[i][l] * beta[i];

		tmpbeta += tnK[l];


		for (i = 0; i < mH; i++)
		    if (alpha[i] > 0)
			tmpbeta += HMK[i][l] * alpha[i];

		beta[l] -= tmpbeta / KMK[l][l];

	    }
	}
	else if (mH > 0 && mK == 0) {
	    for (l = 0; l < mH; l++) {

		tmpalpha = .0;
		for (i = 0; i < mH; i++)
		    if (alpha[i] > 0)
			tmpalpha += HMH[i][l] * alpha[i];

		tmpalpha += tnH[l];

		alpha[l] -= tmpalpha / HMH[l][l];
		if (alpha[l] < .0)
		    alpha[l] = .0;
	    }
	}
	else if (mH == 0 && mK > 0) {
	    for (l = 0; l < mK; l++) {
		tmpbeta = .0;
		for (i = 0; i < mK; i++)
		    tmpbeta += KMK[i][l] * beta[i];

		tmpbeta += tnK[l];

		beta[l] -= tmpbeta / KMK[l][l];

	    }
	}

	/*value of the dual Lagrangian */
	L = mMm;

	tmpL = .0;
	for (i = 0; i < mH; i++)
	    if (alpha[i] > 0)
		for (j = 0; j < mH; j++)
		    if (alpha[j] > 0)
			tmpL += alpha[i] * alpha[j] * HMH[i][j];
	L -= .5 * tmpL;

	tmpL = .0;
	for (i = 0; i < mH; i++)
	    if (alpha[i] > 0)
		tmpL += alpha[i] * tnH[i];
	L -= tmpL;

	tmpL = .0;
	for (i = 0; i < mK; i++)
	    for (j = 0; j < mK; j++)
		tmpL += beta[i] * beta[j] * KMK[i][j];
	L -= .5 * tmpL;

	tmpL = .0;
	for (i = 0; i < mK; i++)
	    tmpL += beta[i] * tnK[i];
	L -= tmpL;

	tmpL = .0;
	for (i = 0; i < mH; i++)
	    if (alpha[i] > 0)
		for (j = 0; j < mK; j++)
		    tmpL += alpha[i] * beta[j] * HMK[i][j];
	L -= tmpL;

	L *= .5;

	/*value of the objective function */
	f = mMm - L;

	tmpf = .0;
	for (i = 0; i < mH; i++)
	    if (alpha[i] > 0)
		tmpf += alpha[i] * tnH[i];
	f -= .5 * tmpf;

	tmpf = .0;
	for (i = 0; i < mK; i++)
	    tmpf += beta[i] * tnK[i];
	f -= .5 * tmpf;

	/* gap between dual Lagrangian and objective function (stopping criteria) */
	gap = fabs((f - L) / (f + 1.));
	//    printf("%f\n",gap);

	f += Const;
	if (f < threshold)
	    break;

    }


    /*free memory */
    for (i = 0; i < n; i++)
	G_free(invM[i]);
    G_free(invM);

    if (mH > 0) {
	G_free(alpha);
	G_free(tnH);
	for (i = 0; i < mH; i++) {
	    G_free(HM[i]);
	    G_free(HMH[i]);
	}
	G_free(HM);
	G_free(HMH);
	for (i = 0; i < n; i++)
	    G_free(tH[i]);
	G_free(tH);
    }

    if (mK > 0) {
	G_free(beta);
	G_free(tnK);
	for (i = 0; i < mK; i++) {
	    G_free(KM[i]);
	    G_free(KMK[i]);
	}
	G_free(KM);
	G_free(KMK);
	for (i = 0; i < n; i++)
	    G_free(tK[i]);
	G_free(tK);
    }

    if (mK > 0 && mH > 0) {
	for (i = 0; i < mH; i++)
	    G_free(HMK[i]);
	G_free(HMK);
    }

    if (f < threshold)
	return 0;
    else
	return 1;

}

void estimate_cv_error(SupportVectorMachine * SVM)
{
    double **M, *m, **H, *h, **K, *k;
    int indx1, indx2, p, n_span;
    double threshold;
    double Const;
    int i, j;
    int neg_samples;
    double en, ep, et;

    M = (double **)G_calloc(SVM->non_bound_support, sizeof(double *));
    for (i = 0; i < SVM->non_bound_support; i++)
	M[i] = (double *)G_calloc(SVM->non_bound_support, sizeof(double));
    m = (double *)G_calloc(SVM->non_bound_support, sizeof(double));
    H = (double **)G_calloc(2 * SVM->non_bound_support, sizeof(double *));
    for (i = 0; i < 2 * SVM->non_bound_support; i++)
	H[i] = (double *)G_calloc(SVM->non_bound_support, sizeof(double));
    h = (double *)G_calloc(2 * SVM->non_bound_support, sizeof(double));
    K = (double **)G_calloc(1, sizeof(double *));
    K[0] = (double *)G_calloc(SVM->non_bound_support, sizeof(double));
    k = (double *)G_calloc(1, sizeof(double));
    for (i = 0; i < SVM->non_bound_support; i++)
	K[0][i] = 1.;
    k[0] = 1.;

    et = en = ep = .0;
    neg_samples = 0;
    for (p = 0; p < SVM->N; p++) {
	if (SVM->target[p] < 0)
	    neg_samples += 1;
	if (SVM->alph[p] > 0) {
	    if (SVM->learned_func(p, SVM) * SVM->target[p] < 0) {
		fprintf(stderr, "Data %d: training error\n", p);
		et += 1.;
		if (SVM->target[p] < 0)
		    en += 1.;
		else
		    ep += 1.;
	    }
	    else {
		if (SVM->alph[p] < SVM->Cw[p])
		    n_span = SVM->non_bound_support - 1;
		else
		    n_span = SVM->non_bound_support;
		indx1 = 0;
		indx2 = 0;
		for (i = 0; i < SVM->N; i++)
		    if (i != p && SVM->alph[i] > 0 &&
			SVM->alph[i] < SVM->Cw[i]) {
			for (j = i; j < SVM->N; j++)
			    if (j != p && SVM->alph[j] > 0 &&
				SVM->alph[j] < SVM->Cw[j]) {
				M[indx1][indx2] = M[indx2][indx1] =
				    SVM->kernel_func(i, j, SVM);
				indx2++;
			    }
			indx1++;
			indx2 = indx1;
		    }

		if (n_span > SVM->d)
		    for (i = 0; i < n_span; i++)
			M[i][i] += G_drand48() * M[i][i] / 100.;

		indx1 = 0;
		for (i = 0; i < SVM->N; i++)
		    if (i != p && SVM->alph[i] > 0 &&
			SVM->alph[i] < SVM->Cw[i]) {
			m[indx1] = -2. * SVM->kernel_func(i, p, SVM);
			indx1++;
		    }

		indx1 = 0;
		for (i = 0; i < 2 * n_span; i++)
		    for (j = 0; j < n_span; j++)
			H[i][j] = .0;
		for (i = 0; i < SVM->N; i++)
		    if (i != p && SVM->alph[i] > 0 &&
			SVM->alph[i] < SVM->Cw[i]) {
			H[indx1][indx1] = 1.;
			H[indx1 + n_span][indx1] = -1.;
			if (SVM->target[i] == SVM->target[p]) {
			    h[indx1] =
				(SVM->Cw[i] - SVM->alph[i]) / SVM->alph[p];
			    h[indx1 + n_span] = SVM->alph[i] / SVM->alph[p];
			    indx1++;
			}
			else {
			    h[indx1] = SVM->alph[i] / SVM->alph[p];
			    h[indx1 + n_span] =
				(SVM->Cw[i] - SVM->alph[i]) / SVM->alph[p];
			    indx1++;
			}
		    }

		threshold =
		    SVM->learned_func(p, SVM) * SVM->target[p] / SVM->alph[p];
		Const = SVM->kernel_func(p, p, SVM);
		if (distance_from_span_sv
		    (M, m, n_span, Const, H, h, 2 * n_span, K, k, 1, SVM->eps,
		     threshold) == 1) {
		    fprintf(stderr, "Data %d: cv error\n", p);
		    et += 1.;
		    if (SVM->target[p] < 0)
			en += 1.;
		    else
			ep += 1.;
		}
		else
		    fprintf(stderr, "Data %d: correctly classified\n", p);
	    }
	}
    }
    et /= SVM->N;
    en /= neg_samples;
    ep /= (SVM->N - neg_samples);

    fprintf(stdout, "Accuracy: %f\n", 1 - et);
    fprintf(stdout, "Perrors\tclass +1: %f\tclass -1: %f\n", ep, en);

}

void write_svm(char *file, SupportVectorMachine * svm, Features * features)

     /*
        write svm structure to a file 
      */
{
    FILE *fpout;
    int i, j;
    char tempbuf[500];
    int np_weights = 0;

    for (i = 0; i < svm->N; i++) {
	if (svm->alph[i] > 0.0) {
	    np_weights += 1;
	}
    }

    if ((fpout = fopen(file, "w")) == NULL) {
	sprintf(tempbuf, "write_svm-> Can't open file %s for writing", file);
	G_fatal_error(tempbuf);
    }

    write_header_features(fpout, features);
    fprintf(fpout, "#####################\n");
    fprintf(fpout, "MODEL:\n");
    fprintf(fpout, "#####################\n");

    fprintf(fpout, "Model:\n");
    fprintf(fpout, "SupportVectorMachine\n");
    fprintf(fpout, "Convergence:\n");
    fprintf(fpout, "%d\n", svm->convergence);
    fprintf(fpout, "Kernel Type:\n");
    if (svm->kernel_type == SVM_KERNEL_LINEAR) {
	fprintf(fpout, "linear_kernel\n");
    }
    if (svm->kernel_type == SVM_KERNEL_GAUSSIAN) {
	fprintf(fpout, "gaussian_kernel\n");
    }
    if (svm->kernel_type == SVM_KERNEL_DIRECT) {
	fprintf(fpout, "2pbk_kernel\n");
    }
    fprintf(fpout, "Kernel parameter:\n");
    fprintf(fpout, "%f\n", svm->two_sigma_squared);

    fprintf(fpout, "Optimization parameter:\n");
    fprintf(fpout, "%f\n", svm->C);

    fprintf(fpout, "Cost parameter:\n");
    fprintf(fpout, "%f\n", svm->cost);

    fprintf(fpout, "Convergence parameters:\n");
    fprintf(fpout, "tol\teps\tmaxloops\n");
    fprintf(fpout, "%e\t%e\t%d\n", svm->tolerance, svm->eps, svm->maxloops);

    fprintf(fpout, "Number of kernel:\n");
    fprintf(fpout, "%d\n", np_weights);
    fprintf(fpout, "Dimension:\n");
    fprintf(fpout, "%d\n", svm->d);

    fprintf(fpout, "Offset:\n");
    fprintf(fpout, "%f\n", svm->b);

    if (svm->kernel_type == SVM_KERNEL_GAUSSIAN) {
	fprintf(fpout, "Kernel - Label - Weight:\n");
	for (i = 0; i < svm->N; i++) {
	    if (svm->alph[i] > 0.0) {
		for (j = 0; j < svm->d; j++) {
		    fprintf(fpout, "%f\t", svm->dense_points[i][j]);
		}
		fprintf(fpout, "%d\t%e\n", svm->target[i], svm->alph[i]);
	    }
	}
    }
    if (svm->kernel_type == SVM_KERNEL_LINEAR ||
	svm->kernel_type == SVM_KERNEL_DIRECT) {
	fprintf(fpout, "Weight:\n");
	fprintf(fpout, "%f", svm->w[0]);
	for (i = 1; i < svm->d; i++) {
	    fprintf(fpout, "\t%f", svm->w[i]);
	}
	fprintf(fpout, "\n");
    }

    if (svm->kernel_type == SVM_KERNEL_DIRECT) {
	fprintf(fpout, "Support Vector:\n");
	for (i = 0; i < svm->N; i++)
	    fprintf(fpout, "%f\n", svm->alph[i]);
    }

    if (features->f_pca[0]) {
	fprintf(fpout, "#####################\n");
	fprintf(fpout, "PRINC. COMP.:\n");
	fprintf(fpout, "#####################\n");

	fprintf(fpout, "Number of pc:\n");
	fprintf(fpout, "%d\n", features->npc);

	for (i = 0; i < features->f_pca[1]; i++) {
	    fprintf(fpout, "PCA: Layer %d\n", i + 1);
	    write_pca(fpout, &(features->pca[i]));
	}
    }
    fclose(fpout);
}

void test_svm(SupportVectorMachine * svm, Features * features, char *file)

     /*
        test svm model on a set of data (features) and write the results
        into a file. To standard output accuracy and error on each class
      */
{
    int i, j;
    int *data_in_each_class;
    FILE *fp;
    char tempbuf[500];
    double pred;
    double *error;
    double accuracy;


    fp = fopen(file, "w");
    if (fp == NULL) {
	sprintf(tempbuf, "test_svm-> Can't open file %s for writing", file);
	G_fatal_error(tempbuf);
    }

    data_in_each_class = (int *)G_calloc(features->nclasses, sizeof(int));
    error = (double *)G_calloc(features->nclasses, sizeof(double));

    accuracy = 0.0;
    for (i = 0; i < features->nexamples; i++) {
	for (j = 0; j < features->nclasses; j++) {
	    if (features->class[i] == features->p_classes[j]) {
		data_in_each_class[j] += 1;
		if ((pred =
		     predict_svm(svm,
				 features->value[i])) * features->class[i] <=
		    0.0) {
		    error[j] += 1.0;
		    accuracy += 1.0;
		}
		fprintf(fp, "%d\t%f\n", features->class[i], pred);
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

double predict_svm(SupportVectorMachine * svm, double *x)

     /* 
        given a svm model, return the predicted margin of a test point x
      */
{
    int i, j;
    double y = 0.0;
    double K;

    if (svm->kernel_type == SVM_KERNEL_GAUSSIAN) {
	for (i = 0; i < svm->N; i++) {
	    if (svm->alph[i] > 0) {
		K = 0.0;
		for (j = 0; j < svm->d; j++)
		    K += (svm->dense_points[i][j] -
			  x[j]) * (svm->dense_points[i][j] - x[j]);
		y += svm->alph[i] * svm->target[i] * exp(-K /
							 svm->
							 two_sigma_squared);
	    }
	}
	y -= svm->b;
    }

    if (svm->kernel_type == SVM_KERNEL_LINEAR) {
	K = 0.0;
	for (j = 0; j < svm->d; j++)
	    K += svm->w[j] * x[j];
	y = K - svm->b;
    }

    if (svm->kernel_type == SVM_KERNEL_DIRECT) {
	double *models;
	double x1, x2;
	int t;

	models = (double *)G_calloc(svm->d, sizeof(double));


	for (t = 0; t < svm->d; t++) {
	    models[t] = 0.0;
	    x1 = dot_product(x, svm->models[t].x1, svm->orig_d);
	    x2 = dot_product(x, svm->models[t].x2, svm->orig_d);
	    models[t] = svm->models[t].w_coeff *
		(svm->models[t].y1 * x1 + svm->models[t].y2 * x2) +
		svm->models[t].b;
	    if (models[t] > 1)
		models[t] = 1.0;
	    else if (models[t] < -1)
		models[t] = -1.0;
	}

	y = 0.0;
	for (i = 0; i < svm->N; i++)
	    if (svm->alph[i] > 0)
		for (t = 0; t < svm->d; t++)
		    y += svm->alph[i] * svm->target[i] *
			svm->dense_points[i][t] * models[t];

	y -= svm->b;
	G_free(models);
    }

    return y;
}



void compute_svm_bagging(BSupportVectorMachine * bsvm, int bagging,
			 int nsamples, int nvar, double **data,
			 int *data_class, int svm_kernel, double kp, double C,
			 double tol, double eps, int maxloops,
			 int svm_verbose, double *svm_W)
{
    int i, b;
    int *bsamples;
    double **xdata_training;
    int *xclasses_training;
    double *prob;
    int nk;
    int *extracted;
    int index;


    bsvm->svm = (SupportVectorMachine *) G_calloc(bagging,
						  sizeof
						  (SupportVectorMachine));
    bsvm->nsvm = bagging;
    bsvm->weights = (double *)G_calloc(bsvm->nsvm, sizeof(double));

    for (b = 0; b < bsvm->nsvm; b++) {
	bsvm->weights[b] = 1.0 / bsvm->nsvm;
    }


    extracted = (int *)G_calloc(nsamples, sizeof(int));
    prob = (double *)G_calloc(nsamples, sizeof(double));
    bsamples = (int *)G_calloc(nsamples, sizeof(int));
    xdata_training = (double **)G_calloc(nsamples, sizeof(double *));
    xclasses_training = (int *)G_calloc(nsamples, sizeof(int));

    for (i = 0; i < nsamples; i++) {
	prob[i] = 1.0 / nsamples;
    }

    for (b = 0; b < bsvm->nsvm; b++) {
	for (i = 0; i < nsamples; i++) {
	    extracted[i] = 0;
	}
	Bootsamples(nsamples, prob, bsamples);
	for (i = 0; i < nsamples; i++) {
	    extracted[bsamples[i]] = 1;
	}
	nk = 0;
	for (i = 0; i < nsamples; i++) {
	    if (extracted[i]) {
		nk += 1;
	    }
	}

	index = 0;
	for (i = 0; i < nsamples; i++) {
	    if (extracted[i]) {
		xdata_training[index] = data[i];
		xclasses_training[index++] = data_class[i];
	    }
	}

	compute_svm(&(bsvm->svm[b]), nk, nvar, xdata_training,
		    xclasses_training, svm_kernel, kp, C, tol,
		    eps, maxloops, svm_verbose, svm_W);

    }

    G_free(bsamples);
    G_free(xclasses_training);
    G_free(prob);
    G_free(extracted);
    G_free(xdata_training);
}


void write_bagging_boosting_svm(char *file, BSupportVectorMachine * bsvm,
				Features * features)

     /*
        write a bagging or boosting svm to a file
      */
{
    int i, j;
    FILE *fp;
    char tempbuf[500];
    int b;
    int np_weights;

    fp = fopen(file, "w");
    if (fp == NULL) {
	sprintf(tempbuf,
		"write_bagging_boosting_svm-> Can't open file %s for writing",
		file);
	G_fatal_error(tempbuf);
    }

    write_header_features(fp, features);
    fprintf(fp, "#####################\n");
    fprintf(fp, "MODEL:\n");
    fprintf(fp, "#####################\n");

    fprintf(fp, "Model:\n");
    fprintf(fp, "B-SupportVectorMachine\n");
    fprintf(fp, "Cost parameter:\n");
    fprintf(fp, "%f\n", bsvm->w);
    fprintf(fp, "Number of models:\n");
    fprintf(fp, "%d\n", bsvm->nsvm);
    fprintf(fp, "Weights:\n");
    fprintf(fp, "%f", bsvm->weights[0]);
    for (b = 1; b < bsvm->nsvm; b++) {
	fprintf(fp, "\t%f", bsvm->weights[b]);
    }
    fprintf(fp, "\n");
    for (b = 0; b < bsvm->nsvm; b++) {

	np_weights = 0;
	for (i = 0; i < bsvm->svm[b].N; i++) {
	    if (bsvm->svm[b].alph[i] > 0.0) {
		np_weights += 1;
	    }
	}
	fprintf(fp, "Convergence:\n");
	fprintf(fp, "%d\n", bsvm->svm[b].convergence);

	fprintf(fp, "Kernel Type:\n");
	if (bsvm->svm[b].kernel_type == SVM_KERNEL_GAUSSIAN) {
	    fprintf(fp, "gaussian_kernel\n");
	}
	if (bsvm->svm[b].kernel_type == SVM_KERNEL_LINEAR) {
	    fprintf(fp, "linear_kernel\n");
	}
	fprintf(fp, "Kernel parameter:\n");
	fprintf(fp, "%f\n", bsvm->svm[b].two_sigma_squared);

	fprintf(fp, "Optimization parameter:\n");
	fprintf(fp, "%f\n", bsvm->svm[b].C);

	fprintf(fp, "Cost parameter:\n");
	fprintf(fp, "%f\n", bsvm->svm[b].cost);

	fprintf(fp, "Convergence parameters:\n");
	fprintf(fp, "tol\teps\tmaxloops\n");
	fprintf(fp, "%e\t%e\t%d\n", bsvm->svm[b].tolerance,
		bsvm->svm[b].eps, bsvm->svm[b].maxloops);

	fprintf(fp, "Number of kernel:\n");
	fprintf(fp, "%d\n", np_weights);
	fprintf(fp, "Dimension:\n");
	fprintf(fp, "%d\n", bsvm->svm[b].d);

	fprintf(fp, "Offset:\n");
	fprintf(fp, "%f\n", bsvm->svm[b].b);



	if (bsvm->svm[b].kernel_type == SVM_KERNEL_GAUSSIAN) {
	    fprintf(fp, "Kernel - Label - Weight:\n");
	    for (i = 0; i < bsvm->svm[b].N; i++) {
		if (bsvm->svm[b].alph[i] > 0.0) {
		    for (j = 0; j < bsvm->svm[b].d; j++) {
			fprintf(fp, "%f\t", bsvm->svm[b].dense_points[i][j]);
		    }
		    fprintf(fp, "%d\t%f\n", bsvm->svm[b].target[i],
			    bsvm->svm[b].alph[i]);
		}
	    }
	}
	if (bsvm->svm[b].kernel_type == SVM_KERNEL_LINEAR) {
	    fprintf(fp, "Weight:\n");
	    fprintf(fp, "%f", bsvm->svm[b].w[0]);
	    for (i = 1; i < bsvm->svm[b].d; i++) {
		fprintf(fp, "\t%f", bsvm->svm[b].w[i]);
	    }
	    fprintf(fp, "\n");
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


void compute_svm_boosting(BSupportVectorMachine * bsvm, int boosting,
			  double w, int nsamples, int nvar, double **data,
			  int *data_class, int nclasses, int *classes,
			  int svm_kernel, double kp, double C, double tol,
			  double svm_eps, int maxloops, int svm_verbose,
			  double *svm_W, int weights_boosting)
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
    int nk;
    int *extracted;
    int index;

    if (weights_boosting == 1) {
	bsvm->w_evolution = (double **)G_calloc(nsamples, sizeof(double *));
	for (i = 0; i < nsamples; i++)
	    bsvm->w_evolution[i] =
		(double *)G_calloc(boosting + 3, sizeof(double));
    }

    bsvm->svm = (SupportVectorMachine *) G_calloc(boosting,
						  sizeof
						  (SupportVectorMachine));
    bsvm->nsvm = boosting;
    bsvm->weights = (double *)G_calloc(bsvm->nsvm, sizeof(double));
    bsvm->w = w;

    extracted = (int *)G_calloc(nsamples, sizeof(int));
    prob = (double *)G_calloc(nsamples, sizeof(double));
    bsamples = (int *)G_calloc(nsamples, sizeof(int));
    xdata_training = (double **)G_calloc(nsamples, sizeof(double *));
    xclasses_training = (int *)G_calloc(nsamples, sizeof(int));
    error = (int *)G_calloc(nsamples, sizeof(int));

    for (i = 0; i < nsamples; i++) {
	prob[i] = 1.0 / nsamples;
    }

    for (b = 0; b < bsvm->nsvm; b++) {
	if (weights_boosting == 1)
	    for (i = 0; i < nsamples; i++)
		bsvm->w_evolution[i][b] = prob[i];


	for (i = 0; i < nsamples; i++) {
	    extracted[i] = 0;
	}
	Bootsamples(nsamples, prob, bsamples);
	for (i = 0; i < nsamples; i++) {
	    extracted[bsamples[i]] = 1;
	}
	nk = 0;
	for (i = 0; i < nsamples; i++) {
	    if (extracted[i]) {
		nk += 1;
	    }
	}

	index = 0;
	for (i = 0; i < nsamples; i++) {
	    if (extracted[i]) {
		xdata_training[index] = data[i];
		xclasses_training[index++] = data_class[i];
	    }
	}

	compute_svm(&(bsvm->svm[b]), nk, nvar, xdata_training,
		    xclasses_training, svm_kernel, kp, C, tol,
		    svm_eps, maxloops, svm_verbose, svm_W);

	e00 = e01 = e10 = e11 = prior0 = prior1 = 0.0;
	for (i = 0; i < nsamples; i++) {
	    if (data_class[i] == classes[0]) {
		if (predict_svm(&(bsvm->svm[b]), data[i]) * data_class[i] <=
		    0.0) {
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
		if (predict_svm(&(bsvm->svm[b]), data[i]) * data_class[i] <=
		    0.0) {
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
	eps = (1.0 - e00 / (e00 + e01)) * prior0 * bsvm->w +
	    (1.0 - e11 / (e10 + e11)) * prior1 * (2.0 - bsvm->w);
	if (eps > 0.0 && eps < 0.5) {
	    bsvm->weights[b] = 0.5 * log((1.0 - eps) / eps);
	    totprob = 0.0;
	    for (i = 0; i < nsamples; i++) {
		if (error[i]) {
		    if (data_class[i] == classes[0]) {
			prob[i] = prob[i] * exp(bsvm->weights[b] * bsvm->w);
		    }
		    else {
			prob[i] =
			    prob[i] * exp(bsvm->weights[b] * (2.0 - bsvm->w));
		    }
		}
		else {
		    if (data_class[i] == classes[0]) {
			prob[i] =
			    prob[i] * exp(-bsvm->weights[b] *
					  (2.0 - bsvm->w));
		    }
		    else {
			prob[i] = prob[i] * exp(-bsvm->weights[b] * bsvm->w);
		    }
		}
		totprob += prob[i];
	    }
	    for (i = 0; i < nsamples; i++) {
		prob[i] /= totprob;
	    }
	}
	else {
	    bsvm->weights[b] = 0.0;
	    for (i = 0; i < nsamples; i++) {
		prob[i] = 1.0 / nsamples;
	    }
	}

    }

    totbeta = 0.0;
    for (b = 0; b < bsvm->nsvm; b++) {
	totbeta += bsvm->weights[b];
    }
    for (b = 0; b < bsvm->nsvm; b++) {
	bsvm->weights[b] /= totbeta;
    }


    G_free(bsamples);
    G_free(xclasses_training);
    G_free(prob);
    G_free(extracted);
    G_free(xdata_training);
    G_free(error);

}

double predict_bsvm(BSupportVectorMachine * bsvm, double *x)

     /* 
        given a bsvm model, return the predicted margin of a test point x
      */
{
    int b;
    int predict;
    double out;
    double pred;

    out = 0.0;
    for (b = 0; b < bsvm->nsvm; b++) {
	pred = predict_svm(&(bsvm->svm[b]), x);
	if (pred < 0.0) {
	    predict = -1;
	}
	else if (pred > 0.0) {
	    predict = 1;
	}
	else {
	    predict = 0;
	}
	out += predict * bsvm->weights[b];
    }
    return out;
}

void test_bsvm(BSupportVectorMachine * bsvm, Features * features, char *file)

     /*
        test bagging or boosting svm model on a set of data (features) 
        and write the results into a file. To standard output accuracy 
        and error on each class
      */
{
    int i, j;
    int *data_in_each_class;
    FILE *fp;
    char tempbuf[500];
    double pred;
    double *error;
    double accuracy;


    fp = fopen(file, "w");
    if (fp == NULL) {
	sprintf(tempbuf, "test_bsvm-> Can't open file %s for writing", file);
	G_fatal_error(tempbuf);
    }

    data_in_each_class = (int *)G_calloc(features->nclasses, sizeof(int));
    error = (double *)G_calloc(features->nclasses, sizeof(double));

    accuracy = 0.0;
    for (i = 0; i < features->nexamples; i++) {
	for (j = 0; j < features->nclasses; j++) {
	    if (features->class[i] == features->p_classes[j]) {
		data_in_each_class[j] += 1;
		if ((pred =
		     predict_bsvm(bsvm,
				  features->value[i])) * features->class[i] <=
		    0.0) {
		    error[j] += 1.0;
		    accuracy += 1.0;
		}
		fprintf(fp, "%d\t%f\n", features->class[i], pred);
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


void test_bsvm_progressive(BSupportVectorMachine * bsvm, Features * features,
			   char *file)

     /*
        test bagging or boosting svm model on a set of data (features) 
        and write the results into a file. To standard output accuracy 
        and error on each class
      */
{
    int i, j;
    int *data_in_each_class;
    FILE *fp;
    char tempbuf[500];
    double pred;
    double *error;
    double accuracy;
    int b;

    fp = fopen(file, "w");
    if (fp == NULL) {
	sprintf(tempbuf, "test_bsvm-> Can't open file %s for writing", file);
	G_fatal_error(tempbuf);
    }

    data_in_each_class = (int *)G_calloc(features->nclasses, sizeof(int));
    error = (double *)G_calloc(features->nclasses, sizeof(double));

    for (b = 1; b <= bsvm->nsvm; b++) {
	if ((b < 100 && b % 2 == 1) || (b >= 100) || (b == bsvm->nsvm)) {
	    accuracy = 0.0;
	    for (j = 0; j < features->nclasses; j++) {
		error[j] = .0;
		data_in_each_class[j] = 0;
	    }
	    for (i = 0; i < features->nexamples; i++) {
		for (j = 0; j < features->nclasses; j++) {
		    if (features->class[i] == features->p_classes[j]) {
			data_in_each_class[j] += 1;
			if ((pred =
			     predict_bsvm_progressive(bsvm,
						      features->value[i], b))
			    * features->class[i] <= 0.0) {
			    error[j] += 1.0;
			    accuracy += 1.0;
			}
			if (b == bsvm->nsvm)
			    fprintf(fp, "%d\t%f\n", features->class[i], pred);
			break;
		    }
		}
	    }

	    accuracy /= features->nexamples;
	    accuracy = 1.0 - accuracy;

	    if (b == bsvm->nsvm)
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
	}
    }
    G_free(data_in_each_class);
    G_free(error);
}

double predict_bsvm_progressive(BSupportVectorMachine * bsvm, double *x,
				int bmax)

     /* 
        given a bsvm model, return the predicted margin of a test point x
      */
{
    int b;
    int predict;
    double out;
    double pred;

    out = 0.0;
    for (b = 0; b < bmax; b++) {
	pred = predict_svm(&(bsvm->svm[b]), x);
	if (pred < 0.0) {
	    predict = -1;
	}
	else if (pred > 0.0) {
	    predict = 1;
	}
	else {
	    predict = 0;
	}
	out += predict * bsvm->weights[b];
    }
    return out;
}

double dot_product(double *x, double *y, int n)
{
    double out = .0;

    n--;
    while (n >= 0)
	out += x[n] * y[n--];

    return out;
}
