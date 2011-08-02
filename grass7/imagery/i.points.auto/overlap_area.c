#include <grass/raster.h>
#include "globals.h"
#include "local_proto.h"

static View *pick_view, *zoom_view, *main_view; 
static int target_flag;


int overlap_area(int xp, int yp, int xs, int ys, int n_img, int ncols, int nrows)   
{
  
  int x_1, y_1, x_2, y_2;
  int tmp_right, tmp_left;
  int tmp_bottom, tmp_top;
  int tmp_ncols; 
  int tmp_nrows; 

  int top, bottom, left, right;
  int row,col;
  struct Cell_head cellhd;


 
  if(n_img==1)
    {
      pick_view = VIEW_MAP1;
      main_view = VIEW_MAP1;
      zoom_view = VIEW_MAP1_ZOOM;
      target_flag = 0;
      printf("info VIEW_MAP1_ZOOM: nrows=%d ncols=%d",zoom_view->nrows,zoom_view->ncols);
    }  
  
  else if (n_img==2)
    {
      pick_view = VIEW_MAP2;
      main_view = VIEW_MAP2;
      zoom_view = VIEW_MAP2_ZOOM;
      target_flag = 1;
    }
    
  else
    return 0;  
  if (!pick_view->cell.configured) return 0;             /*	just to be sure */


  tmp_right = pick_view->cell.right;
  tmp_left = pick_view->cell.left;
  tmp_ncols = (tmp_right - tmp_left);

  tmp_bottom = pick_view->cell.bottom;
  tmp_top = pick_view->cell.top;
  tmp_nrows = (tmp_bottom - tmp_top);


  x_1 = ((tmp_ncols*xp)/ncols);
  y_1 = (((pick_view->nrows)*yp)/nrows);
  x_2 = ((tmp_ncols*xs)/ncols);
  y_2 = (((pick_view->nrows)*ys)/nrows);



  
  if (x_1 == x_2 || y_1 == y_2) return 0;      /* ignore event */


    
  top = row_to_view (pick_view, y_1);
  left = col_to_view (pick_view, x_1);
  bottom = row_to_view (pick_view, y_2);
  right = col_to_view (pick_view, x_2);
 

  if (!In_view (pick_view,right,bottom)) return 0; 
    

  Menu_msg("");

  
  G_copy (&cellhd, &pick_view->cell.head, sizeof(cellhd)); 


  col = view_to_col(pick_view,left);
  row = view_to_row(pick_view,top);
  cellhd.north = row_to_northing (&pick_view->cell.head,row,0.0);
  cellhd.west  = col_to_easting  (&pick_view->cell.head,col,0.0);


  col = view_to_col(pick_view,right);
  row = view_to_row(pick_view,bottom);
  cellhd.south = row_to_northing (&pick_view->cell.head,row,1.0);
  cellhd.east  = col_to_easting  (&pick_view->cell.head,col,1.0);

  
    
  cellhd.rows = bottom-top+1;
  cellhd.cols = right-left+1;
  cellhd.ns_res = (cellhd.north-cellhd.south)/cellhd.rows;
  cellhd.ew_res = (cellhd.east-cellhd.west)/cellhd.cols;
  
  if (zoom_view->cell.configured)
    {
      R_standard_color (GREY);
      Outline_cellhd (main_view, &zoom_view->cell.head);    
    }
  R_standard_color (RED);              
  Outline_cellhd (main_view, &cellhd);       
  
  if (target_flag)
    select_target_env();
  G_adjust_window_to_box (&cellhd, &zoom_view->cell.head, zoom_view->nrows, 
			  zoom_view->ncols);
  Configure_view (zoom_view, pick_view->cell.name, pick_view->cell.mapset,
		  pick_view->cell.ns_res, pick_view->cell.ew_res);
  
    
  drawcell (zoom_view);   
  select_current_env();
  display_points(1);


  return 0;

}


static int 

cancel (void)
{
    return -1;
}










