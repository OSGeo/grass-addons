float **G_alloc_fmatrix(int rows, int cols);
int **G_alloc_imatrix(int rows, int cols);
void G_free_fmatrix(float **m);
void G_free_imatrix(int **mmm);
int check_rheol_par(int rheol_type, float chezy, float visco, float rho);
float t_frict(float **h, int row, int col, float b_frict);
float t_voellmy(float vel, float **h, int row, int col, float b_frict,
		float chezy);
float t_visco(float v, float **h, int row, int col, float b_frict, float rho,
		float visco, float ystress);
float veldt(float ua, float t, float g_x, float p_x, float i_x, float t_x);
float shift0(float **m, int r, int c, int maxR, int maxC, int minR, int minC, int n, int w);
void out_print (float **matrix,char *name, int nr, int nc);
void out_sum_print (float **matrix1,float **matrix2,float **matrix3,float **matrix4, char *name, int nr, int nc, int mode, float threshold);
float nash_sutcliffe(float **m_t1,float**m_t2, int nr, int nc);
void report_input(float ifrict,float rho,float ystress,float visco,float chezy,float bfrict,float fluid,float NS_thres,int t,int delta);
