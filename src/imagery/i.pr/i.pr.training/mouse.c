#include <grass/raster.h>
#include "globals.h"

void Mouse_pointer(int *x, int *y, int *button)
{
    static int curx, cury;

    R_get_location_with_pointer(&curx, &cury, button);
    *x = curx;
    *y = cury;
}
