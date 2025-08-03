/* analyze.c */
int analyze(void);
int points_to_line(double, double, double, double, double *, double *);

/* cellhd.c */
int set_target_window(void);

/* conv.c */
double row_to_northing(struct Cell_head *, int, double);
double col_to_easting(struct Cell_head *, int, double);
double northing_to_row(struct Cell_head *, double);
double easting_to_col(struct Cell_head *, double);

/* creat_rand.c */
void init_rand(void);
long make_rand(void);

/* equ.c */
int Compute_equation(void);

/* find_points.c */
void Extract_matrix_auto(void);
void Search_correlation_points_auto(DCELL *, DCELL *, int, int, double);

/* group.c */
int get_group(void);

/* target.c */
int get_target(void);
int select_env(int);
int select_current_env(void);
int select_target_env(void);

/* overlap.c */
int overlap(void);
