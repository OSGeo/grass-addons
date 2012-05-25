#include <math.h>
#include <string.h>
#include <stdio.h>
#include <stdlib.h>
#include <grass/gis.h>
#include <grass/raster.h>
#include <grass/glocale.h>
#include <grass/linkm.h>

#define HBExp 1
#define verysmall 0.01
#define min(A,B) ((A) < (B) ? (A):(B))
#define max(A,B) ((A) > (B) ? (A):(B))

float **G_alloc_fmatrix(int rows, int cols) {
	float **m;
	int i;
	m = (float **) G_calloc(rows, sizeof(float *));
	m[0] = (float *) G_calloc(rows * cols, sizeof(float));
	for (i = 1; i < rows; i++)
		m[i] = m[i - 1] + cols;
	return m;
}

int **G_alloc_imatrix(int rows, int cols) {
	int **mmm;
	int i;
	mmm = (int **) G_calloc(rows, sizeof(int *));
	mmm[0] = (int *) G_calloc(rows * cols, sizeof(int));
	for (i = 1; i < rows; i++)
		mmm[i] = mmm[i - 1] + cols;
	return mmm;
}

void G_free_fmatrix(float **m) {
	G_free(m[0]);
	G_free(m);
	m = NULL;
	return;
}

void G_free_imatrix(int **mmm) {
	G_free(mmm[0]);
	G_free(mmm);
	mmm = NULL;
	return;
}

int check_rheol_par(int rheol_type, float chezy, float visco, float rho) {
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

float t_frict(float **h, int row, int col, float b_frict) {
	float t;

	if (h[row][col] > verysmall) {
		t = tan((M_PI * b_frict) / 180.0);
	} else {
		t = 5 * tan((M_PI * b_frict) / 180.0);
	}
	return t;
}

float t_voellmy(float v, float **h, int row, int col, float b_frict,
		float chezy) {
	float t;
	if (h[row][col] > verysmall) {
		t = tan((M_PI * b_frict) / 180.0) + pow(v, 2) / (chezy * h[row][col]);
	} else {
		t = 5 * tan((M_PI * b_frict) / 180.0);
	}
	return t;
}

float t_visco(float v, float **h, int row, int col, float b_frict, float rho,
		float visco, float ystress) {
	float t;

	if (h[row][col] > verysmall) {
		if (ystress > 0) {
			t =
					tan((M_PI * b_frict) / 180.0)
							+ (1.5 * ystress
									+ (3 * visco * pow(v, HBExp) / h[row][col]))
									/ (rho * h[row][col]);
		} else {
			t = tan((M_PI * b_frict) / 180.0)
					+ (3 * visco * pow(v, HBExp) / h[row][col] / h[row][col]);
		}
	} else {
		if (ystress > 0) {
			t = 5 * ystress;
		} else {
			t = 5 * tan((M_PI * b_frict) / 180.0);  ///// CHECK settare a 0  ???
		}
	}
	return t;
}


float veldt(float ua, float t, float g_x, float p_x, float i_x, float t_x) {
	float v;

	if (ua>0)
		v = max(0, ua + t * (g_x + p_x + i_x - t_x));

	else if (ua<0)
		v = min(ua + t * (g_x + p_x - i_x + t_x),0);

	else {
		if ((g_x+p_x)>0)
			v = max(0, t * (g_x + p_x + i_x - t_x));

		else if ((g_x+p_x)<0){
			v = min(t * (g_x + p_x - i_x + t_x),0);
		}
		else
			v=0;
	}

	return v;
}

float shift0(float **m, int r, int c, int maxR, int maxC, int minR, int minC, int n, int w) {
	float v;

	if ((r+n<minR) || (r+n>maxR))
		v=0;
	else if ((c+w<minC)|| (c+w>maxC))
		v=0;
	else
		v = m[r+n][c+w];

	return v;
}


void out_print (float **matrix,char *name, int nr, int nc){
	int row,col;
	float *outrast;
	int outfd;

	outrast = Rast_allocate_f_buf();
	outfd = Rast_open_fp_new(name);
	for (row = 0; row < nr; row++) {
		for (col = 0; col < nc; col++) {
			if (matrix[row][col]==0)
				Rast_set_f_null_value(&outrast[col], 1);
			else
				((FCELL *) outrast)[col] = matrix[row][col];
		}
		Rast_put_f_row(outfd, outrast);
	}
	G_free(outrast);
	Rast_close(outfd);
}


void out_sum_print (float **matrix1, float **matrix2, float **matrix3, float **matrix4,char *name, int nr, int nc, int mode, float threshold){
	int row,col;
	float *outrast;
	int outfd;
	/*struct History history; * holds meta-data */
	
	outrast = Rast_allocate_f_buf();
	outfd = Rast_open_fp_new(name);
	for (row = 0; row < nr; row++) {
		for (col = 0; col < nc; col++) {
			if (mode==1){
				if (matrix1[row][col]+matrix2[row][col]>0)
					((FCELL *) outrast)[col] = matrix1[row][col]+matrix2[row][col];
				else
					Rast_set_f_null_value(&outrast[col], 1);
				}
			if (mode==2){
				if (matrix1[row][col]+matrix2[row][col]>0)
					if (matrix2[row][col]>threshold)
						((FCELL *) outrast)[col] = sqrt(pow(matrix3[row][col],2)+pow(matrix4[row][col],2));
					else
						((FCELL *) outrast)[col] = 0.0;
				else
					Rast_set_f_null_value(&outrast[col], 1);
				}
			}
		Rast_put_f_row(outfd, outrast);
		/**
		Rast_short_history(name, "raster", &history);
		Rast_command_history(&history);
		Rast_write_history(name, &history);
		**/
	}
	G_free(outrast);
	Rast_close(outfd);
}

float nash_sutcliffe(float **m_t1,float**m_t2, int nr, int nc){
	float sum_den=0;
	float sum_num=0;
	float sum_ave=0;
	int row,col,c=0;
	float ns_res,ave;

	for (row = 0; row < nr; row++) {
		for (col = 0; col < nc; col++) {
			sum_ave +=m_t1[row][col];
			c+=1;
		}
	}

	ave = sum_ave/c;

	for (row = 0; row < nr; row++) {
		for (col = 0; col < nc; col++) {
			sum_num += pow(m_t1[row][col]-m_t2[row][col],2);
			sum_den += pow(m_t1[row][col]-ave,2);
		}
	}
	if (sum_den==0){
		ns_res = -9999999;
		G_message("WARNING: -inf value obtained for NS coefficient; the new value -9999999 has been set");
	} else {
		ns_res = 1 - (sum_num/sum_den);
	}
	return ns_res;
}


void report_input(float ifrict,float rho,float ystress,float visco,float chezy,float bfrict,float fluid,float NS_thres,int t,int delta){
	fprintf(stdout, "-----------Input data:-----------\n");
	fprintf(stdout, "Internal friction angle = %.2f\n",ifrict);
	if (rho!=-1)
		fprintf(stdout, "Density = %.2f\n",rho);
	if (ystress!=-1)
		fprintf(stdout, "Yield stress = %.2f\n",ystress);
	if (visco!=-1)
		fprintf(stdout, "Viscosity = %.2f\n",visco);
	if (chezy!=-1)
		fprintf(stdout, "Chézy coefficient = %.2f\n",chezy);
	if (bfrict!=-1)
		fprintf(stdout, "Basal friction angle = %.2f\n",bfrict);
	if (fluid!=-1)
		fprintf(stdout, "Fluidization rate = %.2f\n",fluid);
	if (NS_thres!=-1)
		fprintf(stdout, "Nash-Sutcliffe threshold = %.4f\n",NS_thres);
	fprintf(stdout, "Maximum timesteps number  = %i\n",t);
	if (delta!=-1)
		fprintf(stdout, "Reporting time frequency = %i\n",delta);
	fprintf(stdout, "---------------------------------\n");
}
