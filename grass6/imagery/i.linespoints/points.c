#include "globals.h"
#include "local_proto.h"
#include <grass/raster.h>

int display_line (View *view, double *east, double *north,int *status,int count);

int display_points (int in_color)
{
    display_points_in_view (VIEW_MAP1, in_color,
	    group.points.e1, group.points.n1,
	    group.points.status, group.points.count);

    display_points_in_view (VIEW_MAP1_ZOOM, in_color,
	    group.points.e1, group.points.n1,
	    group.points.status, group.points.count);

    display_points_in_view (VIEW_MAP2, in_color,
	    group.points.e2, group.points.n2,
	    group.points.status, group.points.count);

    display_points_in_view (VIEW_MAP2_ZOOM, in_color,
	    group.points.e2, group.points.n2,
	    group.points.status, group.points.count);

    return 0;
}

int display_points_in_view (View *view, int in_color,
    double *east, double *north, int *status, int count)
{
    if (!view->cell.configured) return 1;
    D_cell_draw_setup(view->top, view->bottom,  view->left, view->right);
    D_set_clip_window(view->top, view->bottom,  view->left, view->right);
    while (count-- > 0)
    {
                if (in_color && ((*status ==2)||(*status ==-2)))
                       display_line(view,east,  north, status,count);
                if (in_color && (*status > 0))
	    R_standard_color (GREEN);
	else if (in_color && ((*status == 0)||(*status <= -2)))
	    R_standard_color (RED);
	else
	    R_standard_color (GREY);
	status++;
	display_one_point (view, *east++, *north++);
    }

    return 0;
}

int display_one_point (View *view, double east, double north)
{
    int row, col, x, y;

    row = northing_to_row (&view->cell.head, north) + .5;
    col = easting_to_col  (&view->cell.head, east) + .5;
    y = row_to_view (view, row);
    x = col_to_view (view, col);
    if (In_view(view, x, y))
	dot (x,y);

    return 0;
}


int display_line (View *view, double *east, double *north,int *status,int count)
   {
      int row, col, x[2], y[2];

      if (count==0) return 1;
      if ((*(status +1)!=3) && (*(status+1)!=-3)) return 1;

   row = northing_to_row (&view->cell.head, *north) + .5;
    col = easting_to_col  (&view->cell.head, *east) + .5;
    y[0] = row_to_view (view, row);
    x[0] = col_to_view (view, col);

    row = northing_to_row (&view->cell.head, *(north+1)) + .5;
    col = easting_to_col  (&view->cell.head, *(east+1)) + .5;
    y[1] = row_to_view (view, row);
    x[1] = col_to_view (view, col);
    if (*status == 2 )
        R_standard_color (GREEN);

    else   R_standard_color (RED);
    D_move_abs(x[0],y[0]);
    D_cont_abs(x[1],y[1]);
    /*  R_polyline_abs (x,y,2); */
    /*plot_line(*east,*north,*(east+1),*(north+1)); */
    R_flush();
      }


