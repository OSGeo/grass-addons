#include <grass/raster.h>

#define DIR_UNKNOWN 0
#define DIR_DEG 1
#define DIR_DEG45 2

#define NW 135
#define N 90
#define NE 45
#define E 360
#define SE 315
#define S 270
#define SW 225
#define W 180

typedef struct
{
    RASTER_MAP_TYPE type;
    int rows, cols;
    union
    {
	void **v;
	CELL **c;
	FCELL **f;
	DCELL **d;
    } map;
} RASTER_MAP;

/* raster.c */
void set(RASTER_MAP, int, int, double);
double get(RASTER_MAP, int, int);

/* accumulate.c */
double accumulate(CELL **, RASTER_MAP, RASTER_MAP, char **, int, int);
