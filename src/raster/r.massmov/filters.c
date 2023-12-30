#include <math.h>
#include <string.h>
#include <stdio.h>
#include <stdlib.h>
#include <grass/gis.h>
#include <grass/raster.h>
#include <grass/glocale.h>

#define nullo -999.9f

double gradx3(double **matrix, int row, int col, double dx, int abs)
{
    double v;

    if (matrix[row][col] != nullo && matrix[row][col + 1] != nullo &&
        matrix[row - 1][col + 1] != nullo &&
        matrix[row + 1][col + 1] != nullo && matrix[row][col - 1] != nullo &&
        matrix[row - 1][col - 1] != nullo &&
        matrix[row + 1][col - 1] != nullo) {

        if (abs == 1) {
            v = (fabs((matrix[row - 1][col + 1]) +
                      2 * fabs(matrix[row][col + 1]) +
                      fabs(matrix[row + 1][col + 1])) -
                 (fabs(matrix[row - 1][col - 1]) +
                  2 * fabs(matrix[row][col - 1]) +
                  fabs(matrix[row + 1][col - 1]))) /
                (8 * dx);
            return v;
        }
        else {
            v = ((matrix[row - 1][col + 1] + 2 * matrix[row][col + 1] +
                  matrix[row + 1][col + 1]) -
                 (matrix[row - 1][col - 1] + 2 * matrix[row][col - 1] +
                  matrix[row + 1][col - 1])) /
                (8 * dx);
            return v;
        }
    }
    else {
        return nullo;
    }
}

double grady3(double **matrix, int row, int col, double dy, int abs)
{
    double v;

    if (matrix[row][col] != nullo && matrix[row - 1][col - 1] != nullo &&
        matrix[row - 1][col] != nullo && matrix[row - 1][col + 1] != nullo &&
        matrix[row + 1][col - 1] != nullo && matrix[row + 1][col] != nullo &&
        matrix[row + 1][col + 1] != nullo) {

        if (abs == 1) {
            v = ((fabs(matrix[row - 1][col - 1]) +
                  2 * fabs(matrix[row - 1][col]) +
                  fabs(matrix[row - 1][col + 1])) -
                 fabs((matrix[row + 1][col - 1]) +
                      2 * fabs(matrix[row + 1][col]) +
                      fabs(matrix[row + 1][col + 1]))) /
                (8 * dy);
            return v;
        }
        else {
            v = ((matrix[row - 1][col - 1] + 2 * matrix[row - 1][col] +
                  matrix[row - 1][col + 1]) -
                 (matrix[row + 1][col - 1] + 2 * matrix[row + 1][col] +
                  matrix[row + 1][col + 1])) /
                (8 * dy);
            return v;
        }
    }
    else {
        return nullo;
    }
}

double gradx2(double **matrix, int row, int col, double dx, int abs)
{
    double v;

    if (matrix[row][col] != nullo && matrix[row][col + 1] != nullo &&
        matrix[row][col - 1] != nullo) {

        if (abs == 1) {
            v = (fabs(matrix[row][col + 1]) - fabs(matrix[row][col - 1])) /
                (2 * dx);
            return v;
        }
        else {
            v = (matrix[row][col + 1] - matrix[row][col - 1]) / (2 * dx);
            return v;
        }
    }
    else {
        return nullo;
    }
}

double gradPx2(double **matrix1, double **matrix2, double **matrix3, int row,
               int col, double dx)
{
    double v;

    if (matrix1[row][col] != nullo && matrix2[row][col] != nullo &&
        (cos(atan(matrix3[row][col]))) != nullo &&
        matrix1[row][col + 1] != nullo && matrix2[row][col + 1] != nullo &&
        (cos(atan(matrix3[row][col + 1]))) != nullo &&
        matrix1[row][col - 1] != nullo && matrix2[row][col - 1] != nullo &&
        (cos(atan(matrix3[row][col - 1]))) != nullo) {
        v = ((9.8 * (matrix1[row][col + 1] + matrix2[row][col + 1]) *
              (cos(atan(matrix3[row][col + 1])))) -
             (9.8 * (matrix1[row][col - 1] + matrix2[row][col - 1]) *
              (cos(atan(matrix3[row][col - 1]))))) /
            (2 * dx);
        return v;
    }
    else
        return nullo;
}

double grady2(double **matrix, int row, int col, double dy, int abs)
{
    double v;

    if (matrix[row][col] != nullo && matrix[row + 1][col] != nullo &&
        matrix[row - 1][col] != nullo) {

        if (abs == 1) {
            v = (fabs(matrix[row - 1][col]) - fabs(matrix[row + 1][col])) /
                (2 * dy);
            return v;
        }

        else {
            v = (matrix[row - 1][col] - matrix[row + 1][col]) / (2 * dy);
            return v;
        }
    }
    else {
        return nullo;
    }
}

/* calcolo del gradiente combinato della somma di 2 matrici (usato per P)
 * gradPy2 (pendenza y, matrice 1, matrice 2, riga, col, res y)
 *
 * */
double gradPy2(double **matrix1, double **matrix2, double **matrix3, int row,
               int col, double dy)
{
    double v;

    if (matrix1[row][col] != nullo && matrix2[row][col] != nullo &&
        (cos(atan(matrix3[row][col]))) != nullo &&
        matrix1[row + 1][col] != nullo && matrix2[row + 1][col] != nullo &&
        (cos(atan(matrix3[row + 1][col]))) != nullo &&
        matrix1[row - 1][col] != nullo && matrix2[row - 1][col] != nullo &&
        (cos(atan(matrix3[row - 1][col]))) != nullo) {
        v = ((9.8 * (matrix1[row - 1][col] + matrix2[row - 1][col]) *
              (cos(atan(matrix3[row - 1][col])))) -
             (9.8 * (matrix1[row + 1][col] + matrix2[row + 1][col]) *
              (cos(atan(matrix3[row + 1][col]))))) /
            (2 * dy);
        return v;
    }
    else
        return nullo;
}

double lax(double **matrix, int row, int col, double laxfactor)
{

    double gg = 0.0;
    double hh = 0.0;
    double v;

    if (matrix[row][col] != nullo) {

        if (matrix[row - 1][col - 1] != nullo) {
            gg = gg + 2 * matrix[row - 1][col - 1];
            hh = hh + 2;
        }

        if (matrix[row - 1][col] != nullo) {
            gg = gg + 3 * matrix[row - 1][col];
            hh = hh + 3;
        }

        if (matrix[row - 1][col + 1] != nullo) {
            gg = gg + 2 * matrix[row - 1][col + 1];
            hh = hh + 2;
        }

        if (matrix[row][col - 1] != nullo) {
            gg = gg + 3 * matrix[row][col - 1];
            hh = hh + 3;
        }

        if (matrix[row][col + 1] != nullo) {
            gg = gg + 3 * matrix[row][col + 1];
            hh = hh + 3;
        }

        if (matrix[row + 1][col - 1] != nullo) {
            gg = gg + 2 * matrix[row + 1][col - 1];
            hh = hh + 2;
        }

        if (matrix[row + 1][col] != nullo) {
            gg = gg + 3 * matrix[row + 1][col];
            hh = hh + 3;
        }

        if (matrix[row + 1][col + 1] != nullo) {
            gg = gg + 2 * matrix[row + 1][col + 1];
            hh = hh + 2;
        }

        if (/*gg != 0.0 &&*/ hh != 0.0)
            v = ((1 - laxfactor) * matrix[row][col] + laxfactor * (gg / hh));
        else
            v = matrix[row][col];

        return v;
    }

    else {
        return nullo;
    }
}

double filter_lax(double **matrix, int row, int col, double laxfactor,
                  double **filter_matrix, double threshold, double val)
{

    double gg = 0.0;
    double hh = 0.0;
    double v;

    if (matrix[row][col] != nullo && (filter_matrix[row][col] > threshold)) {

        if ((matrix[row - 1][col - 1] != nullo) &&
            (filter_matrix[row - 1][col - 1] > threshold)) {
            gg = gg + 2 * matrix[row - 1][col - 1];
            hh = hh + 2;
        }

        if ((matrix[row - 1][col] != nullo) &&
            (filter_matrix[row - 1][col] > threshold)) {
            gg = gg + 3 * matrix[row - 1][col];
            hh = hh + 3;
        }

        if ((matrix[row - 1][col + 1] != nullo) &&
            (filter_matrix[row - 1][col + 1] > threshold)) {
            gg = gg + 2 * matrix[row - 1][col + 1];
            hh = hh + 2;
        }

        if ((matrix[row][col - 1] != nullo) &&
            (filter_matrix[row][col - 1] > threshold)) {
            gg = gg + 3 * matrix[row][col - 1];
            hh = hh + 3;
        }

        if ((matrix[row][col + 1] != nullo) &&
            (filter_matrix[row][col + 1] > threshold)) {
            gg = gg + 3 * matrix[row][col + 1];
            hh = hh + 3;
        }

        if ((matrix[row + 1][col - 1] != nullo) &&
            (filter_matrix[row + 1][col - 1] > threshold)) {
            gg = gg + 2 * matrix[row + 1][col - 1];
            hh = hh + 2;
        }

        if ((matrix[row + 1][col] != nullo) &&
            (filter_matrix[row + 1][col] > threshold)) {
            gg = gg + 3 * matrix[row + 1][col];
            hh = hh + 3;
        }

        if ((matrix[row + 1][col + 1] != nullo) &&
            (filter_matrix[row + 1][col + 1] > threshold)) {
            gg = gg + 2 * matrix[row + 1][col + 1];
            hh = hh + 2;
        }

        if (/*gg != 0.0 &&*/ hh != 0.0)
            v = ((1 - laxfactor) * matrix[row][col] + laxfactor * (gg / hh));
        else
            v = matrix[row][col];

        return v;
    }

    else {
        v = val;
        return v;
    }
}

double filter_lax_print(double **matrix, int row, int col, double laxfactor,
                        double **filter_matrix, double threshold, double val)
{

    double gg = 0.0;
    double hh = 0.0;
    double v;

    if (matrix[row][col] != nullo && (filter_matrix[row][col] > threshold)) {
        if ((matrix[row - 1][col - 1] != nullo) &&
            (filter_matrix[row - 1][col - 1] > threshold)) {
            gg = gg + 2 * matrix[row - 1][col - 1];
            hh = hh + 2;
            while (getchar() != 'y') {
            }
        }

        if ((matrix[row - 1][col] != nullo) &&
            (filter_matrix[row - 1][col] > threshold)) {
            gg = gg + 3 * matrix[row - 1][col];
            hh = hh + 3;
            while (getchar() != 'y') {
            }
        }

        if ((matrix[row - 1][col + 1] != nullo) &&
            (filter_matrix[row - 1][col + 1] > threshold)) {
            gg = gg + 2 * matrix[row - 1][col + 1];
            hh = hh + 2;
            while (getchar() != 'y') {
            }
        }

        if ((matrix[row][col - 1] != nullo) &&
            (filter_matrix[row][col - 1] > threshold)) {
            gg = gg + 3 * matrix[row][col - 1];
            hh = hh + 3;
            while (getchar() != 'y') {
            }
        }

        if ((matrix[row][col + 1] != nullo) &&
            (filter_matrix[row][col + 1] > threshold)) {
            gg = gg + 3 * matrix[row][col + 1];
            hh = hh + 3;
            while (getchar() != 'y') {
            }
        }

        if ((matrix[row + 1][col - 1] != nullo) &&
            (filter_matrix[row + 1][col - 1] > threshold)) {
            gg = gg + 2 * matrix[row + 1][col - 1];
            hh = hh + 2;
            while (getchar() != 'y') {
            }
        }

        if ((matrix[row + 1][col] != nullo) &&
            (filter_matrix[row + 1][col] > threshold)) {
            gg = gg + 3 * matrix[row + 1][col];
            hh = hh + 3;
            while (getchar() != 'y') {
            }
        }

        if ((matrix[row + 1][col + 1] != nullo) &&
            (filter_matrix[row + 1][col + 1] > threshold)) {
            gg = gg + 2 * matrix[row + 1][col + 1];
            hh = hh + 2;
            while (getchar() != 'y') {
            }
        }

        if (/*gg != 0.0 &&*/ hh != 0.0)
            v = ((1 - laxfactor) * matrix[row][col] + laxfactor * (gg / hh));
        else
            v = matrix[row][col];

        return v;
    }

    else {
        v = val;
        return v;
    }
}
