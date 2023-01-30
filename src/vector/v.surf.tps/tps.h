struct tps_pnt {
    int r, c;     /* row, col in target window */
    double val;   /* value to interpolate */
    double *vars; /* values of covariables */
};

int global_tps(int out_fd, int *var_fd, int n_vars, int mask_fd,
               struct tps_pnt *pnts, int n_points, double regularization);
int local_tps(int out_fd, int *var_fd, int n_vars, int mask_fd,
              struct tps_pnt *pnts, int n_points, int min_points,
              double regularization, double overlap, double pthin, int do_bfs,
              double segs_mb);
