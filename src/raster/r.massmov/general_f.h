double **G_alloc_matrix(int rows, int cols);
int **G_alloc_imatrix(int rows, int cols);
void G_free_matrix(double **m);
void G_free_imatrix(int **mmm);
int check_rheol_par(int rheol_type, double chezy, double visco, double rho);
double t_frict(double **h, int row, int col, double b_frict);
double t_voellmy(double vel, double **h, int row, int col, double b_frict,
                 double chezy);
double t_visco(double v, double **h, int row, int col, double b_frict,
               double rho, double visco, double ystress);
double veldt(double ua, double t, double g_x, double p_x, double i_x,
             double t_x);
double shift0(double **m, int r, int c, int maxR, int maxC, int minR, int minC,
              int n, int w);
void out_print(double **matrix, char *name, int nr, int nc, double threshold);
void out_sum_print(double **matrix1, double **matrix2, double **matrix3,
                   double **matrix4, char *name, int nr, int nc, int mode,
                   double threshold);
double pearson(double **m_t1, double **m_t2, int nr, int nc);
void report_input(double ifrict, double rho, double ystress, double visco,
                  double chezy, double bfrict, double fluid, double STOP_thres,
                  int STEP_thres, int t, int delta, int threads);
