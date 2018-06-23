#include <grass/raster.h>

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
double accumulate(CELL **, RASTER_MAP, RASTER_MAP, char **, char, int, int);
