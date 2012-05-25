#include <math.h>
#include <string.h>
#include <stdio.h>
#include <stdlib.h>
#include <grass/gis.h>
#include <grass/raster.h>
#include <grass/glocale.h>


#define nullo -999.9f

float gradx3(float **matrix, int row, int col, float dx, int abs) {
	float v;

	if (matrix[row][col] != nullo && matrix[row][col + 1] != nullo
			&& matrix[row - 1][col + 1] != nullo
			&& matrix[row + 1][col + 1] != nullo
			&& matrix[row][col - 1] != nullo
			&& matrix[row - 1][col - 1] != nullo
			&& matrix[row + 1][col - 1] != nullo) {

		if (abs == 1){
			v = (fabs((matrix[row - 1][col + 1]) + 2 * fabs(matrix[row][col + 1])
							+ fabs(matrix[row + 1][col + 1]))
							- (fabs(matrix[row - 1][col - 1]) + 2 * fabs(matrix[row][col - 1])
									+ fabs(matrix[row + 1][col - 1]))) / (8 * dx);
			return v;
		}
		else{
			v = ((matrix[row - 1][col + 1] + 2 * matrix[row][col + 1]
										+ matrix[row + 1][col + 1])
										- (matrix[row - 1][col - 1] + 2 * matrix[row][col - 1]
												+ matrix[row + 1][col - 1])) / (8 * dx);
			return v;
		}
	} else {
		return nullo;
	}
}

float grady3(float **matrix, int row, int col, float dy, int abs) {
	float v;

	if (matrix[row][col] != nullo && matrix[row - 1][col - 1] != nullo
			&& matrix[row - 1][col] != nullo
			&& matrix[row - 1][col + 1] != nullo
			&& matrix[row + 1][col - 1] != nullo
			&& matrix[row + 1][col] != nullo
			&& matrix[row + 1][col + 1] != nullo) {

		if (abs == 1){
			v = ((fabs(matrix[row - 1][col - 1]) + 2 * fabs(matrix[row - 1][col])
							+ fabs(matrix[row - 1][col + 1]))
							- fabs((matrix[row + 1][col - 1]) + 2 * fabs(matrix[row + 1][col])
									+ fabs(matrix[row + 1][col + 1]))) / (8 * dy);
			return v;
		}
		else {
			v = ((matrix[row - 1][col - 1] + 2 * matrix[row - 1][col]
										+ matrix[row - 1][col + 1])
										- (matrix[row + 1][col - 1] + 2 * matrix[row + 1][col]
												+ matrix[row + 1][col + 1])) / (8 * dy);
			return v;
		}

	} else {
		return nullo;
	}
}

float gradx2(float **matrix, int row, int col, float dx, int abs) {
	float v;

	if (matrix[row][col] != nullo && matrix[row][col + 1] != nullo
			&& matrix[row][col - 1] != nullo) {

		if (abs == 1){
			v = (fabs(matrix[row][col + 1]) - fabs(matrix[row][col - 1])) / (2 * dx);
			return v;
		}
		else {
			v = (matrix[row][col + 1] - matrix[row][col - 1]) / (2 * dx);
			return v;
		}
	} else {
		return nullo;
	}
}

float gradPx2(float **matrix1, float **matrix2, float **matrix3, int row,
		int col, float dx) {
	float v;

	if (matrix1[row][col] != nullo && matrix2[row][col] != nullo
			&& (cos(atan(matrix3[row][col]))) != nullo
			&& matrix1[row][col + 1] != nullo && matrix2[row][col + 1] != nullo
			&& (cos(atan(matrix3[row][col + 1]))) != nullo
			&& matrix1[row][col - 1] != nullo && matrix2[row][col - 1] != nullo
			&& (cos(atan(matrix3[row][col - 1]))) != nullo) {
		v = ((9.8 * (matrix1[row][col + 1] + matrix2[row][col + 1])
				* (cos(atan(matrix3[row][col + 1]))))
				- (9.8 * (matrix1[row][col - 1] + matrix2[row][col - 1])
						* (cos(atan(matrix3[row][col - 1]))))) / (2 * dx);
		return v;

	} else
		return nullo;
}

float grady2(float **matrix, int row, int col, float dy, int abs) {
	float v;

	if (matrix[row][col] != nullo && matrix[row + 1][col] != nullo
			&& matrix[row - 1][col] != nullo) {

		if (abs == 1){
			v = (fabs(matrix[row - 1][col]) - fabs(matrix[row + 1][col])) / (2 * dy);
			return v;
		}

		else {
			v = (matrix[row - 1][col] - matrix[row + 1][col]) / (2 * dy);
			return v;
		}
	} else {
		return nullo;
	}
}

/* calcolo del gradiente combinato della somma di 2 matrici (usato per P)
 * gradPy2 (pendenza y, matrice 1, matrice 2, riga, col, res y)
 *
 * */
float gradPy2(float **matrix1, float **matrix2, float **matrix3, int row,
		int col, float dy) {
	float v;

	if (matrix1[row][col] != nullo && matrix2[row][col] != nullo
			&& (cos(atan(matrix3[row][col]))) != nullo
			&& matrix1[row + 1][col] != nullo && matrix2[row + 1][col] != nullo
			&& (cos(atan(matrix3[row + 1][col]))) != nullo
			&& matrix1[row - 1][col] != nullo && matrix2[row - 1][col] != nullo
			&& (cos(atan(matrix3[row - 1][col]))) != nullo) {
		v = ((9.8 * (matrix1[row - 1][col] + matrix2[row - 1][col])
				* (cos(atan(matrix3[row - 1][col]))))
				- (9.8 * (matrix1[row + 1][col] + matrix2[row + 1][col])
						* (cos(atan(matrix3[row + 1][col]))))) / (2 * dy);
		return v;

	} else
		return nullo;
}

float lax(float **matrix, int row, int col, float laxfactor) {

	float gg = 0.0;
	float hh = 0.0;
	float v;

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

float filter_lax(float **matrix, int row, int col, float laxfactor, float **filter_matrix,float threshold,float val) {


	float gg = 0.0;
	float hh = 0.0;
	float v;


	if (matrix[row][col] != nullo && (filter_matrix[row][col] > threshold)) {

		if ((matrix[row - 1][col - 1] != nullo)&&(filter_matrix[row - 1][col - 1] > threshold)) {
			gg = gg + 2 * matrix[row - 1][col - 1];
			hh = hh + 2;
		}


		if ((matrix[row - 1][col] != nullo)&&(filter_matrix[row - 1][col] > threshold)) {
			gg = gg + 3 * matrix[row - 1][col];
			hh = hh + 3;
		}

		if ((matrix[row - 1][col + 1] != nullo)&&(filter_matrix[row - 1][col + 1] > threshold)) {
			gg = gg + 2 * matrix[row - 1][col + 1];
			hh = hh + 2;
		}

		if ((matrix[row][col - 1] != nullo)&&(filter_matrix[row][col - 1] > threshold)) {
			gg = gg + 3 * matrix[row][col - 1];
			hh = hh + 3;
		}

		if ((matrix[row][col + 1] != nullo)&&(filter_matrix[row][col + 1] > threshold)) {
			gg = gg + 3 * matrix[row][col + 1];
			hh = hh + 3;
		}

		if ((matrix[row + 1][col - 1] != nullo)&&(filter_matrix[row + 1][col - 1] > threshold)) {
			gg = gg + 2 * matrix[row + 1][col - 1];
			hh = hh + 2;
		}

		if ((matrix[row + 1][col] != nullo)&&(filter_matrix[row + 1][col] > threshold)) {
			gg = gg + 3 * matrix[row + 1][col];
			hh = hh + 3;
		}

		if ((matrix[row + 1][col + 1] != nullo)&&(filter_matrix[row + 1][col + 1] > threshold)) {
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
		v=val;
		return v;
	}

}


float filter_lax_print(float **matrix, int row, int col, float laxfactor, float **filter_matrix,float threshold,float val) {


	float gg = 0.0;
	float hh = 0.0;
	float v;

	if (matrix[row][col] != nullo && (filter_matrix[row][col] > threshold)) {
		if ((matrix[row - 1][col - 1] != nullo)&&(filter_matrix[row - 1][col - 1] > threshold)) {
			gg = gg + 2 * matrix[row - 1][col - 1];
			hh = hh + 2;
			while (getchar() != 'y') {}
		}


		if ((matrix[row - 1][col] != nullo)&&(filter_matrix[row - 1][col] > threshold)) {
			gg = gg + 3 * matrix[row - 1][col];
			hh = hh + 3;
			while (getchar() != 'y') {}
		}

		if ((matrix[row - 1][col + 1] != nullo)&&(filter_matrix[row - 1][col + 1] > threshold)) {
			gg = gg + 2 * matrix[row - 1][col + 1];
			hh = hh + 2;
			while (getchar() != 'y') {}
		}

		if ((matrix[row][col - 1] != nullo)&&(filter_matrix[row][col - 1] > threshold)) {
			gg = gg + 3 * matrix[row][col - 1];
			hh = hh + 3;
			while (getchar() != 'y') {}
		}

		if ((matrix[row][col + 1] != nullo)&&(filter_matrix[row][col + 1] > threshold)) {
			gg = gg + 3 * matrix[row][col + 1];
			hh = hh + 3;
			while (getchar() != 'y') {}
		}

		if ((matrix[row + 1][col - 1] != nullo)&&(filter_matrix[row + 1][col - 1] > threshold)) {
			gg = gg + 2 * matrix[row + 1][col - 1];
			hh = hh + 2;
			while (getchar() != 'y') {}
		}

		if ((matrix[row + 1][col] != nullo)&&(filter_matrix[row + 1][col] > threshold)) {
			gg = gg + 3 * matrix[row + 1][col];
			hh = hh + 3;
			while (getchar() != 'y') {}
		}

		if ((matrix[row + 1][col + 1] != nullo)&&(filter_matrix[row + 1][col + 1] > threshold)) {
			gg = gg + 2 * matrix[row + 1][col + 1];
			hh = hh + 2;
			while (getchar() != 'y') {}
		}

		if (/*gg != 0.0 &&*/ hh != 0.0)
			v = ((1 - laxfactor) * matrix[row][col] + laxfactor * (gg / hh));
		else
			v = matrix[row][col];

		return v;
	}

	else {
		v=val;
		return v;
	}
}
