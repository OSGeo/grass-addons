#include "globals.h"
#include <grass/raster.h>
#include <grass/display.h>
#include "loc_func.h"

static View *makeview(double bottom, double top, double left, double right)
{
    View *view;

    view = (View *)G_malloc(sizeof(View));

    top = 100 - top;
    bottom = 100 - bottom;

    view->top = SCREEN_TOP + (SCREEN_BOTTOM - SCREEN_TOP) * top / 100.0;
    view->bottom = SCREEN_TOP + (SCREEN_BOTTOM - SCREEN_TOP) * bottom / 100.0;
    view->left = SCREEN_LEFT + (SCREEN_RIGHT - SCREEN_LEFT) * left / 100.0;
    view->right = SCREEN_LEFT + (SCREEN_RIGHT - SCREEN_LEFT) * right / 100.0;

    if (view->top < SCREEN_TOP)
        view->top = SCREEN_TOP;
    if (view->bottom > SCREEN_BOTTOM)
        view->bottom = SCREEN_BOTTOM;
    if (view->left < SCREEN_LEFT)
        view->left = SCREEN_LEFT;
    if (view->right > SCREEN_RIGHT)
        view->right = SCREEN_RIGHT;

    Outline_box(view->top, view->bottom, view->left, view->right);

    view->top++;
    view->bottom--;
    view->left++;
    view->right--;

    view->nrows = view->bottom - view->top + 1;
    view->ncols = view->right - view->left + 1;
    view->cell.configured = 0;

    return view;
}

void Init_graphics2()
{
    /*
       R_color_table_fixed();
     */
    /*    R_color_offset (0);

       Dscreen();
     */

    SCREEN_TOP = R_screen_top();
    SCREEN_BOTTOM = R_screen_bot();
    SCREEN_LEFT = R_screen_left();
    SCREEN_RIGHT = R_screen_rite();

    BLACK = D_translate_color("black");
    BLUE = D_translate_color("blue");
    BROWN = D_translate_color("brown");
    GREEN = D_translate_color("green");
    GREY = D_translate_color("grey");
    ORANGE = D_translate_color("orange");
    PURPLE = D_translate_color("purple");
    RED = D_translate_color("red");
    WHITE = D_translate_color("white");
    YELLOW = D_translate_color("yellow");

    R_standard_color(WHITE);

    VIEW_TITLE1 = makeview(97.5, 100.0, 0.0, 100.0);
    VIEW_TITLE_IMAGE = makeview(97.5, 100.0, 50.0, 100.0);
    VIEW_MAP1 = makeview(0.0, 97.5, 0.0, 100.0);
    VIEW_IMAGE = makeview(51.0, 97.5, 50.0, 100.0);
    VIEW_TITLE1_ZOOM = makeview(47.5, 51.0, 0.0, 50.0);
    VIEW_EMPTY = makeview(47.5, 51.0, 50.0, 100.0);
    VIEW_MAP1_ZOOM = makeview(2.5, 47.5, 0.0, 50.0);
    VIEW_EXIT = makeview(2.5, 5.0, 90.0, 100.0);
    VIEW_INFO = makeview(7.5, 45.0, 52.5, 97.5);
    VIEW_MENU = makeview(0.0, 2.5, 0.0, 100.0);

    Rast_init_colors(&VIEW_MAP1->cell.colors);
    Rast_init_colors(&VIEW_IMAGE->cell.colors);
}

void Init_graphics()
{
    /*
       R_color_table_fixed();
     */
    /*    R_color_offset (0);

       Dscreen();
     */

    SCREEN_TOP = R_screen_top();
    SCREEN_BOTTOM = R_screen_bot();
    SCREEN_LEFT = R_screen_left();
    SCREEN_RIGHT = R_screen_rite();

    BLACK = D_translate_color("black");
    BLUE = D_translate_color("blue");
    BROWN = D_translate_color("brown");
    GREEN = D_translate_color("green");
    GREY = D_translate_color("grey");
    ORANGE = D_translate_color("orange");
    PURPLE = D_translate_color("purple");
    RED = D_translate_color("red");
    WHITE = D_translate_color("white");
    YELLOW = D_translate_color("yellow");

    R_standard_color(WHITE);

    VIEW_TITLE1 = makeview(97.5, 100.0, 0.0, 50.0);
    VIEW_TITLE_IMAGE = makeview(97.5, 100.0, 50.0, 100.0);
    VIEW_MAP1 = makeview(51.0, 97.5, 0.0, 50.0);
    VIEW_IMAGE = makeview(51.0, 97.5, 50.0, 100.0);
    VIEW_TITLE1_ZOOM = makeview(47.5, 51.0, 0.0, 50.0);
    VIEW_EMPTY = makeview(47.5, 51.0, 50.0, 100.0);
    VIEW_MAP1_ZOOM = makeview(2.5, 47.5, 0.0, 50.0);
    VIEW_EXIT = makeview(2.5, 5.0, 90.0, 100.0);
    VIEW_INFO = makeview(7.5, 45.0, 52.5, 97.5);
    VIEW_MENU = makeview(0.0, 2.5, 0.0, 100.0);

    Rast_init_colors(&VIEW_MAP1->cell.colors);
    Rast_init_colors(&VIEW_IMAGE->cell.colors);
}

void Outline_box(top, bottom, left, right)
{
    R_move_abs(left, top);
    R_cont_abs(left, bottom);
    R_cont_abs(right, bottom);
    R_cont_abs(right, top);
    R_cont_abs(left, top);
}

int Text_width(text)
char *text;
{
    int top, bottom, left, right;

    R_get_text_box(text, &top, &bottom, &left, &right);

    if (right > left)
        return right - left + 1;
    else
        return left - right + 1;
}

void Text(text, top, bottom, left, right, edge) char *text;
{
    R_set_window(top, bottom, left, right);
    R_move_abs(left + edge, bottom - edge);
    R_text(text);
    R_set_window(SCREEN_TOP, SCREEN_BOTTOM, SCREEN_LEFT, SCREEN_RIGHT);
}

void Uparrow(top, bottom, left, right)
{
    R_move_abs((left + right) / 2, bottom);
    R_cont_abs((left + right) / 2, top);
    R_cont_rel((left - right) / 2, (bottom - top) / 2);
    R_move_abs((left + right) / 2, top);
    R_cont_rel((right - left) / 2, (bottom - top) / 2);
}

void Downarrow(top, bottom, left, right)
{
    R_move_abs((left + right) / 2, top);
    R_cont_abs((left + right) / 2, bottom);
    R_cont_rel((left - right) / 2, (top - bottom) / 2);
    R_move_abs((left + right) / 2, bottom);
    R_cont_rel((right - left) / 2, (top - bottom) / 2);
}

void display_map(cellhd, view, name, mapset) struct Cell_head *cellhd;
View *view;
char *name;
char *mapset;
{

    G_adjust_window_to_box(cellhd, &view->cell.head, view->nrows, view->ncols);
    Configure_view(view, name, mapset, cellhd->ns_res, cellhd->ew_res);
    drawcell(view);
}

void drawcell(view) View *view;
{
    int fd;
    int left, top;
    int ncols, nrows;
    int row;
    CELL *cell;
    int repeat;
    struct Colors *colors;
    int read_colors;
    char msg[100];

    if (!view->cell.configured)
        return 0;
    if (view == VIEW_MAP1 || view == VIEW_MAP1_ZOOM) {
        colors = &VIEW_MAP1->cell.colors;
        read_colors = view == VIEW_MAP1;
    }
    else {
        colors = &VIEW_IMAGE->cell.colors;
        read_colors = view == VIEW_IMAGE;
    }
    if (read_colors) {
        Rast_free_colors(colors);
        if (Rast_read_colors(view->cell.name, view->cell.mapset, colors) < 0)
            return 0;
    }

    display_title(view);

    /*    D_set_colors (colors); */

    G_set_window(&view->cell.head);
    nrows = Rast_window_rows();
    ncols = Rast_window_cols();

    left = view->cell.left;
    top = view->cell.top;

    Outline_box(top, top + nrows - 1, left, left + ncols - 1);

    {
        char *getenv();

        if (getenv("NO_DRAW"))
            return 1;
    }

    fd = Rast_open_old(view->cell.name, view->cell.mapset);
    if (fd < 0)
        return 0;
    cell = G_allocate_cell_buf();

    /*
       sprintf (msg, "Plotting %s ...", view->cell.name);
       Menu_msg(msg);
     */

    for (row = 0; row < nrows; row += repeat) {
        R_move_abs(left, top + row);
        if (G_get_map_row_nomask(fd, cell, row) < 0)
            break;
        repeat = G_row_repeat_nomask(fd, row);
        /*      D_raster (cell, ncols, repeat, colors); */
    }
    Rast_close(fd);
    G_free(cell);
    /*    if(colors != &VIEW_MAP1->cell.colors)
       D_set_colors(&VIEW_MAP1->cell.colors);
     */
    return row == nrows;
}

void exit_button()
{
    int size;

    Erase_view(VIEW_EXIT);
    R_standard_color(RED);
    size = VIEW_EXIT->nrows - 4;
    R_text_size(size, size);
    Text("exit", VIEW_EXIT->top, VIEW_EXIT->bottom, VIEW_EXIT->left,
         VIEW_EXIT->right, 2);
    R_standard_color(WHITE);
}

void info_button()
{
    int size;

    Erase_view(VIEW_INFO);
    R_standard_color(GREEN);
    size = VIEW_INFO->nrows / 13;
    R_text_size(size, size);
    Text("UPPER LEFT PANEL:", VIEW_INFO->top, VIEW_INFO->top + size,
         VIEW_INFO->left, VIEW_INFO->right, 1);
    R_standard_color(YELLOW);
    Text("left: mark 1", VIEW_INFO->top + size, VIEW_INFO->top + 2 * size,
         VIEW_INFO->left, VIEW_INFO->right, 1);
    Text("left: mark 2", VIEW_INFO->top + 2 * size, VIEW_INFO->top + 3 * size,
         VIEW_INFO->left, VIEW_INFO->right, 1);
    Text("", VIEW_INFO->top + 4 * size, VIEW_INFO->top + 5 * size,
         VIEW_INFO->left, VIEW_INFO->right, 1);
    R_standard_color(GREEN);
    Text("LOWER LEFT PANEL:", VIEW_INFO->top + 5 * size,
         VIEW_INFO->top + 6 * size, VIEW_INFO->left, VIEW_INFO->right, 1);
    R_standard_color(YELLOW);
    Text("left(double): select", VIEW_INFO->top + 6 * size,
         VIEW_INFO->top + 7 * size, VIEW_INFO->left, VIEW_INFO->right, 1);
    Text("", VIEW_INFO->top + 8 * size, VIEW_INFO->top + 9 * size,
         VIEW_INFO->left, VIEW_INFO->right, 1);
    R_standard_color(GREEN);
    Text("UPPER RIGHT PANEL:", VIEW_INFO->top + 9 * size,
         VIEW_INFO->top + 10 * size, VIEW_INFO->left, VIEW_INFO->right, 1);
    R_standard_color(YELLOW);
    Text("right(double): save", VIEW_INFO->top + 10 * size,
         VIEW_INFO->top + 11 * size, VIEW_INFO->left, VIEW_INFO->right, 1);
    R_standard_color(WHITE);
}
