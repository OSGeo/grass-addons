struct MATRIX {
    int n; /* SIZE OF THIS MATRIX (N x N) */
    double **v;
};

#define M(m, row, col) (m)->v[(row)][(col)]

int solvemat(struct MATRIX *m, double a[], double B[]);
