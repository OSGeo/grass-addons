/* type and size of each patch */
struct pst {
    CELL type; /* patch type */
    int size;  /* patch size (number of cells) */
};

/* clumping helper */
struct c_h {
    struct pst *pst;
    int palloc; /* alloc'd patches */
    int np;     /* number of patches */

    CELL up, left, curr;
    int *pid_curr, *pid_prev;
    int pid;
};

/* size bins: 1 - < 2, 2 - < 4, 4 - < 8, 8 - < 16, etc */
struct changeinfo {
    /* globals */
    int nsizebins; /* number of bins for patch sizes */
    int ntypes;    /* number of different patch types */
    int dts_size;  /* dts size */
    int tmin;      /* smallest patch type number */

    int nchanges; /* number of type changes */

    /* for each input map */
    int *n;       /* number of valid cells */
    double **dt;  /* distribution over types */
    double **ds;  /* distribution over size bins */
    double **dts; /* distribution over types and size bins */
    double *ht;   /* entropy for dt */
    double *hs;   /* entropy for ds */
    double *hts;  /* entropy for dts */

    struct c_h *ch; /* clumping helper */
};

extern struct changeinfo ci;

extern double (*entropy)(double);
extern double (*entropy_p)(double);
