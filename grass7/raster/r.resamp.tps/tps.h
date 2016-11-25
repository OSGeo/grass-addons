
struct tps_pnt
{
    double r, c;	/* row, col in source window */
    double val;		/* value to interpolate */
    double *vars;	/* values of covariables */
};

struct tps_out {
    double val;
    double wsum;
    double wmax;
};

int tps_nn(SEGMENT *in_seg, SEGMENT *var_seg, int n_vars,
           SEGMENT *out_seg, int out_fd, char *mask_name,
           struct Cell_head *src, struct Cell_head *dst,
	   off_t n_points, int min_points,
	   double regularization, double overlap, int do_bfs);

int tps_window(SEGMENT *in_seg, SEGMENT *var_seg, int n_vars,
               SEGMENT *out_seg, int out_fd, char *mask_name,
               struct Cell_head *src, struct Cell_head *dst,
	       off_t n_points,
	       double regularization, double overlap, int radius);
