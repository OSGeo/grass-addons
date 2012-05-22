#include <grass/gis.h>
#include <libxml/parser.h>
#include <libxml/tree.h>


#include "defs.h"

#ifndef _STRUCTS_H
#define _STRUCTS_H

/* put a 
#define LOCAL
into main.c ! */

#ifdef LOCAL
#define EXTERN
#else
#define EXTERN extern
#endif


typedef struct vector
{
	double x;
	double y;
	double z;
}Svector;

typedef struct raster
{
	int x;
	int y;
}Sraster;

typedef struct matrix4
{
	float m[4][4];
}Smatrix4;

typedef struct matrix3
{
	double m[3][3];
}Smatrix3;

typedef struct hypothesis
{
	BOOL *type; /** the ones set to TRUE are the ones in that hypothesis **/
	double bel; /* belief */
	double pl;  /* plausability */
	double bint; /* belief interval = |Pl-Bel| = measure of uncertainty */
	double doubt; /* doubt */
	double common; /* commonality */	
	double bpn; /* basic probability number assignment */
	double bpa; /* the bpa as read from the original input map */
	double minbpn;
	double maxbpn;
	int minbpnev;
	int maxbpnev;
	int isNull;
} Shypothesis;

/* global file pointers for access to evidence maps */
typedef struct fp_struct 
{
	int *fp; /* array of int file handles */
	char **filename; /* array to store names of GRASS maps */
} Sfp_struct;

typedef struct result_struct
{
	char valname[6];
	unsigned short use;
	DCELL **row;
	CELL **crow;
	char **filename;
	int *fd;
	long *hyp_idx;
	struct Colors **colors;
} Sresult_struct;

/* some global vars to keep track of min and max values */
EXTERN double WOC_MIN;
EXTERN double WOC_MAX;

#endif /* _STRUCTS_H */
