/*
 * Our "standard" includes
 */

#include <stdlib.h>
#include <math.h>
#include <stdio.h>
#include <grass/gis.h>
#include <grass/glocale.h>
#include <string.h>

/*
 * Our "standard" defines
 */

#define sign(a) ((a)<0.0? -1.0:1.0)
#define abs(x)  ((x)<0.0? -(x):(x))
#define TRUE 1
#define FALSE 0

/*
 * "Global" shared variable declarations.
 */

/*!!!!!!!!!!!!!!!!!!!!!!!!!
@@
@@ GLOBAL Common Variables
@@
@@!!!!!!!!!!!!!!!!!!!!!!!*/

int   nrows,ncols;
int   GNUM,TNUM;
double w;

/*!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
@@
@@ GLOBAL Channel Routing Variables
@@
@@!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!*/

int   *con_vect, *con_link, *con_node;
int   nlinks,maxnodes;
int   NODES,LINKS,NUM;
float *qlat;

char  *channel_file,*chn_link_map,*chn_node_map;
int   chn_link_fd,chn_node_fd;
CELL  *chn_link_tmp,*chn_node_tmp;

/*!!!!!!!!!!!!!!!!!!!!!!!
@@
@@ GLOBAL Lake Variables
@@
@@!!!!!!!!!!!!!!!!!!!!!!*/

int   *lake_cat,*lake_cells;
double *lake_el, *qtolake;


/*!!!!!!!!!!!!!!!!!!!!!!!!!!!!
  List of Functions
    Prototypes added 6-25-1999 by WB Hughes
!!!!!!!!!!!!!!!!!!!!!!!!!!!!*/

void OV_FLOW(double, double, int, int, int, int,
            double, int, int, int, int,
            float *, float *, float *, float *, int **, double *);
void OV_LAKE(double, int, int, double, int, float *, float *, float *, float *);
void INF_NODIST(int,int,double,float *,float *,int,
                float *,float *,float *,float *,double *);
void INF_REDIST( int, int, double, float *, int, int   *, int   *, float *,
float *, int   , float *, int   , float *, int *, int   *,
float *,float *,float *,float *,float *,float *, double *);
void INTERCEPTION(int, double, float *, float *, float *, double, float *);
void RAIN_SQ_DIS(int, int **, int, int *, int *, double *, float *);
void RAIN_THIESSEN(int, int **, int, int *, int *, double *, float *);
void READ_GAGE_FILE(double *, int, FILE *);
void WRITE_FILES(char *, int, int, double, int, int, int *, char **, int,
     int *, char **, int, int *, char **, int, int *, char **, int, int,
     int *, char **, float *, int, int, int *, int *, int *, int *,
     float *, float *, float *, CELL *, CELL *, CELL *, CELL *,
     CELL *, int, float *, float *, float *, float *, int **, int,
     float *, struct Colors *);
double CH_DEPTH(int, int, FILE *, double, double, double, double,
                double, float *, double *);
void CH_FLOW(int, int, int, int, int, int *, double, double,
             int, float *, float *, float *, float *, float *, float *, double);
void CRASH(FILE *, int, int, int, int, int, int **, double,
           struct Cell_head, float *, float *, float *, int, int,
           double *, double *, int, double *, float *, double *);

void coeff(float *, float *, float *, float *, float *, float *, float *,
           double, double, float *, float *, int, int, float *, float *,
           float *, float *, float *, float *, float *, float *, float *,
           float *, float *, double, double, double, double, int);
void ddsqoy(float *, float *, float *, float *, double, float *, float *,
           int *, float *, int *, float *, float *, float *, float *,
           float *, float *, int *, float *, int *, int);
void dsqoy(float *, float *, float *, float *, double, float *, float *,
           int *, float *, int *, float *, float *, float *, float *,
           float *, float *, int *, float *, int *, int);
void dsyot(double, double *, int, double, double, double, double);
void flow_route(int, int, double, double, double, double, double, double,
     int *, int *, int *, float *, float *, float *, float *, float *,
     float *, float *, float *, int *, int *, double, double, double,
     float *, float *, float *, float *, float *, float *, float *,
     float *, float *, float *, float *, float *, int *, int, float *,
     float *, float *, int *, float *, int, int *, int,
     double, double, double, double);
void norm_calc(int, int *, int *, int *, float *, float *, float *,
     float *, float *, float *, int *, float *, int *, double, int,
     float *, float *, float *, float *, int, double);
int trap_section(int, int, double, double, double, double, double,
     double *, double *, double *, double *);
int brk_pnt_section(int, int, float *, float *, double, int *, float *,
     int *, int, float *, float *, float *,
     double *, double *, double *, double *);
void read_input(FILE *, FILE *, FILE *, float *, float *, float *,
     float *, float *, float *, float *, int *, int *, int *, int *,
     int **, int **, int **, float **, float **, float **, float **,
     float **, float **, float **, int **, int **, int *, float **,
     float **, float **, float **, float **, float **, float **,
     float **, float **, float **, float **, float **, float **,
     int **, int, int, int *, int **, float *, float *, float *);
void read_table(FILE *, int *, int *, int *,
     float **, float **, float **, int **, float **, int *);
void reservoir(int, int, int *, int *, float *, double, int *, double, float);
void section(float *, float *, float *, float *, float *, float *,
     float *, float *, float *, float *, int *, int *, float *, float *,
     float *, float *, float *, float *, float *, float *, float *,
     float *, float *, float *, float *, float *, float *, float *,
     int *, float *, int, int *, int);
void spill(double, float *, int, double, double, double, double,
     int *, int, int *, float *, float *, int);
void usqot(double, float *, int, double, int);
void weir_coeff(int, int, float *, float *, float *, float *, float *,
     float *, float *, float *, float *, float *, float *, float *,
     float *, float *, float *, float *, double);
