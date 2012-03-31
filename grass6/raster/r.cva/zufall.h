#include "config.h"

#define min(a,b) ((a) <= (b) ? (a) : (b))

/* clock cycle for machine */
/* #define CYCLE 2.9e-9 cycle for SX-3: */
/* #define CYCLE 6.0e-9 cycle for Y-MP: */
/* #define CYCLE 3.2e-9 cycle for VP2200 */

# define MIN_SEED 0
#define  MAX_SEED 31328
 
struct klotz0 {
    double buff[607];
    int ptr;
};
 
struct klotz1 {
    double xbuff[1024];
    int first, xptr;
};
 
int normal00();
int normalen();
int normalrs();
int normalsv();
int fische();
int zufall();
int zufalli();
int zufallrs();
int zufallsv();
