#include <stdlib.h>
#include <string.h>
#include <stdio.h>
#include <math.h>
#include <grass/gis.h>
#include <grass/glocale.h>

#ifdef MAIN
#  define GLOBAL
#else
#  define GLOBAL extern
#endif

/*
   PI2= PI/2
   PI4= PI/4
 */
#ifndef PI2
#define PI2 (2*atan(1))
#endif

#ifndef PI4
#define PI4 (atan(1))
#endif

#define STACKMAX 50
#define VARMAX 31

#define MAX(a,b) ((a) > (b) ? (a) : (b))
#define MIN(a,b) ((a) < (b) ? (a) : (b))


typedef char *STRING;

typedef enum
{
    l_ZADEH,
    l_PRODUCT,
    l_DRASTIC,
    l_LUKASIEWICZ,
    l_FODOR,
    l_HAMACHER
} logics;

typedef enum
{
    s_LINEAR,
    s_SSHAPE,
    s_JSHAPE,
    s_GSHAPE
} shapes;

typedef enum
{
    s_BOTH,
    s_LEFT,
    s_RIGHT
} sides;

typedef enum
{
    i_MIN,
    i_PROD
} implications;

typedef enum
{
    d_CENTEROID,
    d_BISECTOR,
    d_MINOFHIGHEST,
    d_MAXOFHIGHEST,
    d_MEANOFHIGHEST
} defuzz;

typedef enum
{
    E,				/* ERROR */
    S,				/* SHIFT */
    R,				/* REDUCE */
    A				/* ACCEPT */
} actions;

typedef enum
{
    t_START,			/* { */
    t_AND,			/* & */
    t_OR,			/* | */
    t_IS_NOT,			/* ~ */
    t_IS,			/* = */
    t_LBRC,			/* ( */
    t_RBRC,			/* ) */
    t_STOP,			/* } */
    t_size,			/* number of tokens */
    t_VAL			/* value a product of MAP and VARIABLE */
} tokens;

typedef struct _sets
{				/* membership definition */
    char setname[21];
    sides side;
    float points[4];
    shapes shape;
    int hedge;
    float height;
} SETS;

typedef struct map
{
    char name[30];
    int nsets;
    int output;			/* is output map? */
    RASTER_MAP_TYPE raster_type;
    fpos_t position;
    void *in_buf;
    float cell;
    int cfd;			/* file descriptor */
    SETS *sets;
} MAPS;

typedef struct valuestacks
{
    float *value;
    SETS *set;
    char oper;
} VALUES;


typedef struct rule
{
    char outname[20];
    int output_set_index;
    char parse_stack[STACKMAX][VARMAX];
    int work_stack[STACKMAX];
    VALUES value_stack[STACKMAX];
    float weight;
} RULES;

typedef struct _outs
{
    char output_name[52];
    int ofd;			/* output file descriptor */
    float *out_buf;
} OUTPUTS;


STRING var_name_file;
STRING rule_name_file;
STRING output;
MAPS *s_maps;
RULES *s_rules;
OUTPUTS *m_outputs;
float **visual_output;
float *universe;
float *antecedents;
int nmaps, nrules, output_index, multiple, coor_proc;
int resolution;
implications implication;
defuzz defuzzyfication;
logics family;

char **rules;

int char_strip(char *buf, char rem);
int char_copy(const char *buf, char *res, int start, int stop);
int get_nsets(FILE * fd, fpos_t position);
int get_universe(void);

int parse_map_file(STRING file);
int parse_rule_file(STRING file);
int parser(void);
int open_maps(void);
int create_output_maps(void);
int get_rows(int row);
int get_cols(int col);


int parse_sets(SETS * set, char buf[], const char mapname[]);
int parse_rules(int rule_num, int n, char buf[]);
int process_coors(char *answer);

float implicate(void);
float parse_expression(int n);
float defuzzify(float *agregate, int defuzzification, float max_antecedent);

float f_and(float cellx, float celly, int family);
float f_or(float cellx, float celly, int family);
float f_not(float cellx, int family);
float fuzzy(FCELL cell, SETS * set);


int parse(void);



void display(void);
