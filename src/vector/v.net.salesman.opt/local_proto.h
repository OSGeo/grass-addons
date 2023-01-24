#define MAX_CHAIN_LENGTH 11

typedef struct {
    int city;
    double cost;
} COST;

extern int ncities; /* number of cities */
extern int nnodes;  /* number of nodes */
extern int *cities; /* array of cities */
extern COST *
    *costs; /* pointer to array of pointers to arrays of sorted forward costs */
extern COST **bcosts; /* pointer to array of pointers to arrays of sorted
                         backward costs */
extern double *
    *cost_cache; /* pointer to array of pointers to arrays of cached costs */
extern int debug_level;

/* tour.c */
void add_city(int, int, int *, int *, int *);
int build_tour(int *cycle, int *cused, int *tncyc, int, int);

/* optimize.c */
int wrap_into(int i, int n);
int optimize_nbrs(int, int, int *);
int opt_2opt(int *tcycle, int *tcused, int tncyc);
int optimize_tour(int *, int *, int, int, int, int, int);
int optimize_tour_chains(int, int, int, int *, int *, int, int, int, int);

/* ga.c */
int ga_opt(int ntours, int nelim, int nopt, int ngen, int *);
void ga_add_city(int city, int after, int *tnc, int *tcycle, int *tused);
