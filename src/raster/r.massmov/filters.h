double gradx3(double **matrix, int row, int col, double dx, int abs);
double grady3(double **matrix, int row, int col, double dy, int abs);
double gradx2(double **matrix, int row, int col, double dx, int abs);
double grady2(double **matrix, int row, int col, double dy, int abs);
double lax(double **matrix, int row, int col, double laxfactor);
double filter_lax(double **matrix, int row, int col, double laxfactor,
                  double **filter_matrix, double threshold, double val);
double gradPx2(double **matrix1, double **matrix2, double **matrix3, int row,
               int col, double dx);
double gradPy2(double **matrix1, double **matrix2, double **matrix3, int row,
               int col, double dy);
double isocell(double **matrix, int row, int col, double val);
double filter_lax_print(double **matrix, int row, int col, double laxfactor,
                        double **filter_matrix, double threshold, double val);
