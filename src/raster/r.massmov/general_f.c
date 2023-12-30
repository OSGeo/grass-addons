#include <math.h>
#include <string.h>
#include <stdio.h>
#include <stdlib.h>
#include <grass/gis.h>
#include <grass/raster.h>
#include <grass/glocale.h>
#include <grass/linkm.h>

#define HBExp     1
#define verysmall 0.01
#define min(A, B) ((A) < (B) ? (A) : (B))
#define max(A, B) ((A) > (B) ? (A) : (B))

double **G_alloc_matrix(int rows, int cols)
{
    double **m;
    int i;
    m = (double **)G_calloc(rows, sizeof(double *));
    m[0] = (double *)G_calloc(rows * cols, sizeof(double));
    for (i = 1; i < rows; i++)
        m[i] = m[i - 1] + cols;
    return m;
}

int **G_alloc_imatrix(int rows, int cols)
{
    int **mmm;
    int i;
    mmm = (int **)G_calloc(rows, sizeof(int *));
    mmm[0] = (int *)G_calloc(rows * cols, sizeof(int));
    for (i = 1; i < rows; i++)
        mmm[i] = mmm[i - 1] + cols;
    return mmm;
}

void G_free_matrix(double **m)
{
    G_free(m[0]);
    G_free(m);
    m = NULL;
    return;
}

void G_free_imatrix(int **mmm)
{
    G_free(mmm[0]);
    G_free(mmm);
    mmm = NULL;
    return;
}

int check_rheol_par(int rheol_type, double chezy, double visco, double rho)
{
    if (rheol_type == 2) {
        if (chezy > 0)
            return 1;
        else
            return -2;
    }

    if (rheol_type == 3) {
        if (visco > 0 && rho > 0)
            return 1;
        else
            return -3;
    }
}

double t_frict(double **h, int row, int col, double b_frict)
{
    double t;

    if (h[row][col] > verysmall) {
        t = tan((M_PI * b_frict) / 180.0);
    }
    else {
        t = 5 * tan((M_PI * b_frict) / 180.0);
    }
    return t;
}

double t_voellmy(double v, double **h, int row, int col, double b_frict,
                 double chezy)
{
    double t;
    if (h[row][col] > verysmall) {
        t = tan((M_PI * b_frict) / 180.0) + pow(v, 2) / (chezy * h[row][col]);
    }
    else {
        t = 5 * tan((M_PI * b_frict) / 180.0);
    }
    return t;
}

double t_visco(double v, double **h, int row, int col, double b_frict,
               double rho, double visco, double ystress)
{
    double t;

    if (h[row][col] > verysmall) {
        if (ystress > 0) {
            t = tan((M_PI * b_frict) / 180.0) +
                (1.5 * ystress + (3 * visco * pow(v, HBExp) / h[row][col])) /
                    (rho * h[row][col]);
        }
        else {
            t = tan((M_PI * b_frict) / 180.0) +
                (3 * visco * pow(v, HBExp) / h[row][col] / h[row][col]);
        }
    }
    else {
        if (ystress > 0) {
            t = 5 * ystress;
        }
        else {
            t = 5 * tan((M_PI * b_frict) / 180.0); ///// CHECK settare a 0  ???
        }
    }
    return t;
}

double veldt(double ua, double t, double g_x, double p_x, double i_x,
             double t_x)
{
    double v;

    if (ua > 0)
        v = max(0, ua + t * (g_x + p_x + i_x - t_x));

    else if (ua < 0)
        v = min(ua + t * (g_x + p_x - i_x + t_x), 0);

    else {
        if ((g_x + p_x) > 0)
            v = max(0, t * (g_x + p_x + i_x - t_x));

        else if ((g_x + p_x) < 0) {
            v = min(t * (g_x + p_x - i_x + t_x), 0);
        }
        else
            v = 0;
    }

    return v;
}

double shift0(double **m, int r, int c, int maxR, int maxC, int minR, int minC,
              int n, int w)
{
    double v;

    if ((r + n < minR) || (r + n > maxR))
        v = 0;
    else if ((c + w < minC) || (c + w > maxC))
        v = 0;
    else
        v = m[r + n][c + w];

    return v;
}

void out_print(double **matrix, char *name, int nr, int nc, double threshold)
{
    int row, col;
    double *outrast;
    int outfd;

    outrast = Rast_allocate_d_buf();
    outfd = Rast_open_fp_new(name);
    for (row = 0; row < nr; row++) {
        for (col = 0; col < nc; col++) {
            if (matrix[row][col] < threshold)
                Rast_set_d_null_value(&outrast[col], 1);
            else
                ((DCELL *)outrast)[col] = matrix[row][col];
        }
        Rast_put_d_row(outfd, outrast);
    }
    G_free(outrast);
    Rast_close(outfd);
}

void out_sum_print(double **matrix1, double **matrix2, double **matrix3,
                   double **matrix4, char *name, int nr, int nc, int mode,
                   double threshold)
{
    int row, col;
    double *outrast;
    int outfd;

    outrast = Rast_allocate_d_buf();
    outfd = Rast_open_fp_new(name);
    for (row = 0; row < nr; row++) {
        for (col = 0; col < nc; col++) {
            if (mode == 1) {
                if (matrix1[row][col] + matrix2[row][col] > threshold)
                    ((DCELL *)outrast)[col] =
                        matrix1[row][col] + matrix2[row][col];
                else
                    Rast_set_d_null_value(&outrast[col], 1);
            }
            if (mode == 2) {
                if (matrix1[row][col] + matrix2[row][col] > threshold)
                    if (matrix2[row][col] > threshold)
                        ((DCELL *)outrast)[col] =
                            sqrt(pow(matrix3[row][col], 2) +
                                 pow(matrix4[row][col], 2));
                    else
                        ((DCELL *)outrast)[col] = 0.0;
                else
                    Rast_set_d_null_value(&outrast[col], 1);
            }
        }
        Rast_put_d_row(outfd, outrast);
    }
    G_free(outrast);
    Rast_close(outfd);
}

double pearson(double **m_t1, double **m_t2, int nr, int nc)
{
    double sum_den_1 = 0;
    double sum_den_2 = 0;
    double sum_den = 0;
    double sum_num = 0;
    double sum_ave_1 = 0;
    double sum_ave_2 = 0;
    int row, col, c = 0;
    double ns_res, ave1, ave2, pearson_val;

    for (row = 0; row < nr; row++) {
        for (col = 0; col < nc; col++) {
            sum_ave_1 += m_t1[row][col];
            sum_ave_2 += m_t2[row][col];
            c += 1;
        }
    }

    ave1 = sum_ave_1 / c;
    ave2 = sum_ave_2 / c;

    for (row = 0; row < nr; row++) {
        for (col = 0; col < nc; col++) {
            sum_num += (m_t1[row][col] - ave1) * (m_t2[row][col] - ave2);
            sum_den_1 += pow(m_t1[row][col] - ave1, 2);
            sum_den_2 += pow(m_t2[row][col] - ave2, 2);
        }
    }

    sum_den = sqrt(sum_den_1) * sqrt(sum_den_2);

    if (sum_den == 0) {
        pearson_val = -9999999;
    }
    else {
        pearson_val = (sum_num / sum_den);
    }
    return pearson_val;
}

void report_input(double ifrict, double rho, double ystress, double visco,
                  double chezy, double bfrict, double fluid, double STOP_thres,
                  int STEP_thres, int t, int delta, int threads)
{
    fprintf(stdout, "-----------Input data:-----------\n");
    fprintf(stdout, "Internal friction angle = %.2f\n", ifrict);
    if (rho != -1)
        fprintf(stdout, "Density = %.2f\n", rho);
    if (ystress != -1)
        fprintf(stdout, "Yield stress = %.2f\n", ystress);
    if (visco != -1)
        fprintf(stdout, "Viscosity = %.2f\n", visco);
    if (chezy != -1)
        fprintf(stdout, "Chézy coefficient = %.2f\n", chezy);
    if (bfrict != -1)
        fprintf(stdout, "Basal friction angle = %.2f\n", bfrict);
    fprintf(stdout, "Fluidization rate = %.2f\n", fluid);
    if (STOP_thres != -1) {
        fprintf(stdout, "Stop threshold for stopping simulation= %.4f\n",
                STOP_thres);
        fprintf(stdout, "Step calculation for stopping simulation = %i\n",
                STEP_thres);
    }
    fprintf(stdout, "Maximum timesteps number  = %i\n", t);
    if (delta != -1)
        fprintf(stdout, "Reporting time frequency = %i\n", delta);
    if (threads != -1)
        fprintf(stdout, "Number of threads = %i\n", threads);
    fprintf(stdout, "---------------------------------\n");
}
