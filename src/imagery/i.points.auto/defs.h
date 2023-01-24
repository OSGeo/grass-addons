#include <grass/imagery.h>

#define SRC_ENV 0
#define TGT_ENV 1

typedef struct {
    char *name;
    char *img, *tgt_img;
    struct Ref ref;
    struct Control_Points points;
    double E12[10], N12[10], E21[10], N21[10];
    int equation_stat;
} Group;

typedef struct {
    double *t1;
    double *u1;
    double *t2;
    double *u2;
    int *status;
    double E12[10], N12[10], E21[10], N21[10];
    int count;
    int line_stat;
} Lines;
