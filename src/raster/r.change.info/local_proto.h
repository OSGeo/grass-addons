/* bufs.c */
extern int allocate_bufs(void);
extern int rotate_bufs(void);

/* mask */
extern void circle_mask(void);

/* gather */
int gather(int);
int set_alpha(double);
double eai(double);
double eah(double);
double shi(double);
double shh(double);

/* readcell.c */
extern int readcell(int, int, int);

/* gain.c */
DCELL pc(void);
DCELL gain1(void);
DCELL gain2(void);
DCELL gain3(void);

/* ratio.c */
DCELL ratio1(void);
DCELL ratio2(void);
DCELL ratio3(void);

/* gini.c */
DCELL gini1(void);
DCELL gini2(void);
DCELL gini3(void);

/* dist.c */
DCELL dist1(void);
DCELL dist2(void);
DCELL dist3(void);

/* chisq.c */
DCELL chisq1(void);
DCELL chisq2(void);
DCELL chisq3(void);
