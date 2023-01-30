#ifndef __V_ELLIPSE_PROTO__
#define __V_ELLIPSE_PROTO__

/* struct with ellipse parameters */
struct Parameters {
    double a;     /* main semi-axis */
    double b;     /* second semi-axis */
    double xc;    /* x of center of ellipse */
    double yc;    /* y of center of ellipse */
    double angle; /* rotation */
};

/* read.c */
void load_points(struct Map_info *, struct line_pnts *, struct line_cats *);

/* write.c */
void write_ellipse(struct Map_info *, struct line_pnts *, struct line_cats *);

/* ellipse.c */
void create_ellipse(struct Parameters *, struct line_pnts *, struct line_cats *,
                    double);
int fitting_ellipse(struct line_pnts *, struct Parameters *);

#endif
