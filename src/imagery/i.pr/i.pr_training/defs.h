#include <grass/imagery.h>

/* this is a graphics structure */
typedef struct {
    int top, bottom, left, right;
    int nrows, ncols;
    struct {
        int configured;
        struct Cell_head head;
        struct Colors colors;
        char name[100];
        char mapset[100];
        int top, bottom, left, right;
        double ew_res, ns_res; /* original map resolution */
    } cell;
} View;
