//#include <grass/gis.h>
#include <grass/Vect.h>

/* aspect flavours */
#define TYPE_GRASS 0
#define TYPE_COMPASS 1

/* barb flavours */
#define TYPE_STRAW 0
#define TYPE_BARB 1
#define TYPE_SMLBARB 2
#define TYPE_ARROW 3

#define RpD ((2 * M_PI) / 360.)	/* radians/degree */
#define D2R(d) (double)(d * RpD)	/* degrees->radians */
#define R2D(d) (double)(d / RpD)	/* radians->degrees */

/* grid.c */
void do_barb_grid(char *, char *, int, int, int, double, double, int, int, int);

/* points.c */
void do_barb_points(char *, int, char *, char *, int, int, int, double, double,
		    int, int);
int count_pts_in_region(struct Map_info *);
void fill_arrays(struct Map_info *, int, char *, char *, int, double *,
		 double *, double *, double *);
double max_magnitude(double *, int);

/* draw.c */
void draw_barb(double, double, double, double, int, double, int);
void unknown_(double, double);
void arrow_mag(double, double, double, double, int);
void arrow_360(double, double, double, int, double, int);
void mark_the_spot(double, double);
void draw_circle(double, double, double, int);
void draw_feather(double, double, double, double, double);

/* legend.c */
void do_legend(char **, char **, int, double, int, double, double, int);
