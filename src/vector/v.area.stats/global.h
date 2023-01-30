#include <grass/gis.h>
#include <grass/vector.h>

#define LENVALS    15
#define STRLEN     32

#define AREA_ID    0
#define CAT        1
#define NISLES     2
#define X_EXTENT   3
#define Y_EXTENT   4
#define IPERIMETER 5
#define IAREA      6
#define ICOMPACT   7
#define IFD        8
#define PERIMETER  9
#define AREA       10
#define BOUNDAREA  11
#define ARATIO     12
#define COMPACT    13
#define FD         14

struct value {
    int area_id;       /* area_id */
    int cat;           /* category */
    int nisles;        /* number of isles */
    double x_extent;   /* x extent */
    double y_extent;   /* y extent */
    double iperimeter; /* sum of isles perimeters */
    double iarea;      /* sum of isles area */
    double icompact;   /* sum of isles compact */
    double ifd;        /* sum of isles fd */
    double perimeter;  /* area perimeter */
    double area;       /* area area */
    double boundarea;  /* area of the boundary of the area */
    double aratio;  /* ratio between the the area of the external boundary and
                       the area of the isles */
    double compact; /* compact of the area */
    double fd;      /* fd of the area */
};

extern struct value *Values;

struct options {
    char *name;
    int field;
    const char *out;
    ;
    char *separator;
};

extern struct options options;

/* areas.c */
int read_areas(struct Map_info *, int);

/* parse.c */
int parse_command_line(int, char *[]);

/* export.c */
char *join(const char *, char **, int, char *);
int export2csv(int);
