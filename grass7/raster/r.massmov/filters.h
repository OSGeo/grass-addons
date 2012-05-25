float gradx3(float **matrix, int row, int col, float dx, int abs);
float grady3(float **matrix, int row, int col, float dy, int abs);
float gradx2(float **matrix, int row, int col, float dx, int abs);
float grady2(float **matrix, int row, int col, float dy, int abs);
float lax(float **matrix, int row, int col, float laxfactor);
float filter_lax(float **matrix, int row, int col, float laxfactor, float **filter_matrix,float threshold,float val);
float gradPx2(float **matrix1, float **matrix2, float **matrix3, int row,
		int col, float dx);
float gradPy2(float **matrix1, float **matrix2, float **matrix3, int row,
		int col, float dy);
float isocell(float **matrix,int row,int col,float val);
float filter_lax_print(float **matrix, int row, int col, float laxfactor, float **filter_matrix,float threshold,float val);
