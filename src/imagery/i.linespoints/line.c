#include "globals.h"
#include "local_proto.h"

static int cancel();
static int select(int x1,int y1,int button);


//static int get_point2 (double *,double *, double *,double *);
//static int screen (int,int,int);


double temp_e1,temp_e2,temp_n1,temp_n2;
static int flag;
void find_position (int *x1, int *x2,int *y1,int *y2);
int xtemp[2],ytemp[2], first_linex[2],first_liney[2];

int
line (void)
{
    int stat,row,col,i;
    static int use = 1;
    double e1,e2,e3,e4,n1,n2,n3,n4;
 //   int x1,x2,x3,x4,y1,y2,y3,y4;
    static Objects objects1[]=
    {
	MENU("CANCEL",cancel,&use),
	INFO("select first line (left side) ",&use),
                 OTHER(select, &use),
	{0}
    };

     static Objects objects2[]=
    {
	MENU("CANCEL",cancel,&use),
	INFO("select second line (right side) ",&use),
                 OTHER(select, &use),
	{0}
    };


    flag =0;
    stat= Input_pointer (objects1);
    if (stat==-1) return 0;

    e1=temp_e1;
    e2=temp_e2;
    n1=temp_n1;
    n2=temp_n2;
    flag = 1;

    for (i=0;i<2;i++)
        {
         first_linex[i]=xtemp[i];
         first_liney[i]=ytemp[i];
          }

    stat=Input_pointer (objects2);
     if (stat==-1)
    {
         R_panel_restore (tempfile2);   /* serve al ripristino del quadrato che contiene la linea collogante i 2 punti */
         R_panel_restore (tempfile3);    /*  serve al ripristino del secondo punto*/
         R_panel_restore (tempfile1);    /*  serve al ripristino del primo punto*/
         R_panel_delete (tempfile1);
         R_panel_delete (tempfile2);
         R_panel_delete (tempfile3);

         return 0;
    }


    e3=temp_e1;
    e4=temp_e2;
    n3=temp_n1;
    n4=temp_n2;
     I_new_control_point (&group.points, e1, n1, e3, n3, 2);
     put_control_points (group.name, &group.points);
     Compute_equation();
     display_points(1) ;
     I_new_control_point (&group.points, e2, n2, e4, n4, 3);
     put_control_points (group.name, &group.points);
     Compute_equation();
     display_points(1) ;
     R_standard_color (GREEN);
     R_polyline_abs (first_linex ,first_liney,2);
     R_polyline_abs (xtemp ,ytemp,2);
     R_flush();

    return 0;	/* return, but don't QUIT */
}

static int select(int x,int y,int button)
{
        if (button != 1)
          return where (x,y);

        if (flag==0) {
                                         if (VIEW_MAP1->cell.configured && In_view (VIEW_MAP1, x, y))
                                                select_line (VIEW_MAP1, x, y);
                                        else if (VIEW_MAP1_ZOOM->cell.configured && In_view (VIEW_MAP1_ZOOM, x, y))
                                                select_line (VIEW_MAP1_ZOOM, x, y);
                                        else return 0;
                                     }
         if (flag==1) {
                                        if (VIEW_MAP2->cell.configured && In_view (VIEW_MAP2, x, y))
                                                select_line (VIEW_MAP2, x, y);
                                        else if (VIEW_MAP2_ZOOM->cell.configured && In_view (VIEW_MAP2_ZOOM, x, y))
                                                select_line (VIEW_MAP2_ZOOM, x, y);
                                         else return 0;
                                      }
          return 1 ; /* return but don't quit */

};

int select_line (View *view,int x1, int y1)
{
    int col, row;
    int x2,y2,button=0;
    char buf[50];



    col = view_to_col (view, x1);
    temp_e1 = col_to_easting (&view->cell.head, col, 0.5);
    row = view_to_row (view, y1);
    temp_n1 = row_to_northing (&view->cell.head, row, 0.5);

    if (flag== 0)
                {
                         Curses_clear_window (INFO_WINDOW);
                         Curses_clear_window (MENU_WINDOW);
                         sprintf (buf, "Point  %d marked on image at", group.points.count+1);
                         Curses_write_window (MENU_WINDOW, 1, 1, buf);
                         sprintf (buf, "East:  %10.2f", temp_e1);
                         Curses_write_window (MENU_WINDOW, 3, 3, buf);
                         sprintf (buf, "North: %10.2f", temp_n1);
                         Curses_write_window (MENU_WINDOW, 4, 3, buf);
                }
     else
              {

                         sprintf (buf, "Point  %d marked on target image at", group.points.count+1);
                         Curses_write_window (INFO_WINDOW, 1, 1, buf);
                         sprintf (buf, "East:  %10.2f",temp_e1);
                         Curses_write_window (INFO_WINDOW, 3, 3, buf);
                         sprintf (buf, "North: %10.2f", temp_n1);
                         Curses_write_window (INFO_WINDOW, 4, 3, buf);
               }

    R_standard_color (ORANGE);
    R_panel_save (tempfile1, y1-dotsize, y1+dotsize, x1-dotsize, x1+dotsize);
     dot(x1,y1);

         while (button!=1)
        {
        R_get_location_with_line (x1,y1,&x2,&y2,&button);
        if( button!=1)
            where (x2,y2);
         if (!(view->cell.configured && In_view (view, x2, y2)))
                                  button=0;
          }

    col = view_to_col (view, x2);
   temp_e2 = col_to_easting (&view->cell.head, col, 0.5);
    row = view_to_row (view, y2);
    temp_n2 = row_to_northing (&view->cell.head, row, 0.5);

   if (flag== 0)
                {
                         sprintf (buf, "Point  %d marked on image at", group.points.count+2);
                         Curses_write_window (MENU_WINDOW, 6, 1, buf);
                         sprintf (buf, "East:  %10.2f", temp_e2);
                         Curses_write_window (MENU_WINDOW, 8, 3, buf);
                         sprintf (buf, "North: %10.2f", temp_n2);
                         Curses_write_window (MENU_WINDOW, 9, 3, buf);
                  }
     else
              {
                         sprintf (buf, "Point  %d marked on target image at", group.points.count+2);
                         Curses_write_window (INFO_WINDOW, 6, 1, buf);
                         sprintf (buf, "East:  %10.2f",temp_e2);
                         Curses_write_window (INFO_WINDOW, 8, 3, buf);
                         sprintf (buf, "North: %10.2f", temp_n2);
                         Curses_write_window (INFO_WINDOW, 9, 3, buf);
                 }

    R_standard_color (ORANGE);
    R_panel_save (tempfile3, y2-dotsize, y2+dotsize, x2-dotsize, x2+dotsize);
     dot(x2,y2);

     xtemp[0]= x1;
     xtemp[1]= x2;
     ytemp[0]= y1;
     ytemp[1]= y2;

    find_position (&x1,&x2,&y1,&y2);
    R_panel_save (tempfile2, y1, y2, x1, x2);
    R_polyline_abs (xtemp ,ytemp,2);

    return 1 ;

 }

 void find_position (int *x1, int *x2,int *y1,int *y2)
  { int temp;
    if (*y2<*y1) {
                         temp=*y1;
                         *y1=*y2;
                         *y2= temp;
                         }
     else if (*y2==*y1) { *y2= *y2+dotsize;
                                  *y1= *y1 - dotsize ;
                                  }
     if (*x2<*x1) {
                         temp=*x1;
                         *x1=*x2;
                         *x2= temp;
                         }
     else if (*x2==*x1) { *x2= *x2+dotsize;
                                  *x1= *x1 - dotsize ;
                                  }
 }


   static int cancel()
 {
    return -1 ;
}


