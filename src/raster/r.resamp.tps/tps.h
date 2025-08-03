struct tps_pnt {
    double r, c;  /* row, col in source window */
    double val;   /* value to interpolate */
    double *vars; /* values of covariables */
};

struct tps_out {
    double val;
    double wsum;
    double wmax;
};

int tps_nn(struct cache *in_seg, struct cache *var_seg, int n_vars,
           struct cache *out_seg, int out_fd, char *mask_name,
           struct Cell_head *src, struct Cell_head *dst, off_t n_points,
           int min_points, int max_points, double regularization,
           double overlap, int do_bfs, double lm_thresh, double ep_thresh);

int tps_window(struct cache *in_seg, struct cache *var_seg, int n_vars,
               struct cache *out_seg, int out_fd, char *mask_name,
               struct Cell_head *src, struct Cell_head *dst, off_t n_points,
               double regularization, double overlap, int radius,
               double lm_thresh);
