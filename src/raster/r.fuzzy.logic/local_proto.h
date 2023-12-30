#include <stdlib.h>
#include <string.h>
#include <stdio.h>
#include <math.h>
#include <grass/gis.h>
#include <grass/raster.h>
#include <grass/glocale.h>

#define _AND        1
#define _OR         2
#define _NOT        3
#define _IMP        4

#define ZADEH       1
#define PRODUCT     2
#define DRASTIC     3
#define LUKASIEWICZ 4
#define FODOR       5
#define HAMACHER    6

#undef MIN
#undef MAX
#define MIN(a, b) ((a) < (b) ? (a) : (b))
#define MAX(a, b) ((a) > (b) ? (a) : (b))

float f_and(float cellx, float celly, int family);
float f_or(float cellx, float celly, int family);
float f_imp(float cellx, float celly, int family);
float f_not(float cellx, int family);
