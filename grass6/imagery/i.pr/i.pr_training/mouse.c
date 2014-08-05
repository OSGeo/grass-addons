#include <grass/raster.h>
#include "globals.h"


void Mouse_pointer(x, y, button)
     int *x, *y, *button;
{
    static int curx, cury;

    R_get_location_with_pointer(&curx, &cury, button);
    *x = curx;
    *y = cury;
}
