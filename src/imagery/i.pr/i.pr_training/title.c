#include <grass/raster.h>
#include "globals.h"
#include "loc_func.h"

void display_title(View *view)
{
    View *title;
    char center[100];
    int size;
    double magnification();

    *center = 0;

    if (view->cell.configured) {
        sprintf(center, "(mag %.1lf)", magnification(view));
    }

    if (view == VIEW_MAP1) {
        title = VIEW_TITLE1;
    }
    else if (view == VIEW_MAP1_ZOOM) {
        title = VIEW_TITLE1_ZOOM;
    }

    if (view == VIEW_IMAGE) {
        title = VIEW_TITLE_IMAGE;
    }

    Erase_view(title);
    size = title->nrows - 4;
    R_text_size(size, size);
    if (*center) {
        R_standard_color(YELLOW);
        Text(center, title->top, title->bottom,
             (title->left + title->right - Text_width(center)) / 2,
             title->right, 2);
    }
    R_standard_color(WHITE);
}
