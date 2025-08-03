#include <stdio.h>
#include <stdlib.h>

/*Create 1D arrays*/
int *ai1d(int X)
{
    int *A = (int *)malloc(X * sizeof(int *));
    return A;
}

float *af1d(int X)
{
    float *A = (float *)malloc(X * sizeof(float *));
    return A;
}

double *ad1d(int X)
{
    double *A = (double *)malloc(X * sizeof(double *));
    return A;
}

/*Create 2D arrays*/
int **ai2d(int X, int Y)
{
    int i;
    int **A = (int **)malloc(X * sizeof(int *));
    for (i = 0; i < X; i++)
        A[i] = (int *)malloc(Y * sizeof(int));
    return A;
}

float **af2d(int X, int Y)
{
    int i;
    float **A = (float **)malloc(X * sizeof(float *));
    for (i = 0; i < X; i++)
        A[i] = (float *)malloc(Y * sizeof(float));
    return A;
}

double **ad2d(int X, int Y)
{
    int i;
    double **A = (double **)malloc(X * sizeof(double *));
    for (i = 0; i < X; i++)
        A[i] = (double *)malloc(Y * sizeof(double));
    return A;
}
