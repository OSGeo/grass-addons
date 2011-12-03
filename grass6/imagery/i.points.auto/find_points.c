#include <unistd.h>
#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <signal.h>
#include <math.h>

#include <grass/config.h>
#ifdef HAVE_FFTW_H
#include <fftw.h>
#endif
#ifdef HAVE_DFFTW_H
#include <dfftw.h>
#endif

#include <grass/raster.h>
#include <grass/imagery.h>
#include <grass/gmath.h>
#include "globals.h"
#include "local_proto.h"

#ifdef NULL_VALUE
#undef NULL_VALUE
#endif
#define NULL_VALUE -1


double *fft_first[2];
double *fft_second[2];
double *fft_prod_con[2];
 
int n=1;   /*If (n==1) then the algorithm is searching the Overlapping-Area, if (n==2), it is searching the GCP's*/ 
int pos_point;
int dist;                                             
int ncols1, ncols2, nrows1, nrows2;
int nrows1_img, ncols1_img, nrows2_img, ncols2_img;
int r1, c1;                                          /* Central (or around the central) point of the first img    */
int r2, c2;                                          /* Corresponding point in the second img                     */
int r2c, c2c;                                        /* Central point of the first img                            */

char *group_name;
char *group_MAPSET;
char *group_LOCATION_NAME;
char *group_GISDBASE;
int q;
FILE *fp;
FILE *fp_old; 
/*int i;*/
char file_name[500];

char name1[100];
char name2[100];
char mapset[100];

int dist_r, dist_c;  

int z;


int n_points=0;           /* When "LESS_GCP's" is activated, then (n_points==0) */
int man_op=0;             /* Variable for the option "Manual_OP". It's 1 if the option is activated */
double e_man2, n_man2;     /* Coordinates for the manual_OP */
int man_m_s_op=0; 
double e_man1, n_man1;

View *m1, *m2; 




int min(int a, int b)
{
 
  if(a <= b)
    {
      return a;
    }
  else
    {
      return b;
    } 
}

static int main_menu();
static int cancel();
static int shift1();
static int shift2();

static int less_GCPs();
static int manual_op();
static int manual_op1();
static int mark_op(int x,int y,int button);
static int mark_point_op (View *view,int x, int y);

static int central();
static int top();
static int bottom();
static int left();
static int right();

static int manual_m_s_op();
static int manual_m_s_op1();
static int mark_m_s_op(int x,int y,int button);
static int mark_point_m_s_op (View *view,int x, int y);

/* variables for function "TRY_AGAIN" */
char name1_initial[100];
char name2_initial[100];
char mapset_initial[100];
static int try_again();
static int store_points();




/* Variables and functions for the Auto-Exclusion */
static int curp, first_point;
static double *xres, *yres, *gnd, *tres, *ures, *lgnd;
static int offsetx, offsety;
static int xmax, ymax, gmax;
static int tmax, umax, lgmax;
static double rms,l_rms;
static double th=2.5;                 /*Default threshold of the rms for the Auto-Exclusion.*/
char file_name1[500];
static int auto_exclusion();
static int change_rms_th();
static int compute_transformation(void);
static int th_1();
static int th_2();
static int th_3();
static int th_4();
static int th_5();
static int other_th();
static int pre_analyze();









int automated_search()
{

  static int use = 1;

  ask_original_map ("raster", group_list, name1,mapset, -1);      
  ask_original_map ("raster", group_list, name2,mapset, 1);       

  

  static Objects objects1[]=
    {   
      MENU(" MAIN MENU  ",cancel,&use),   
      INFO(" O.P. -> ",&use),
      MENU(" Central  ",central,&use),
      MENU(" Top  ",top,&use),
      MENU(" Bottom  ",bottom,&use),   
      MENU(" Left  ",left,&use),   
      MENU(" Right  ",right,&use),
      INFO("  ",&use),
      MENU(" LESS GCPs  ",less_GCPs,&use),
      MENU(" Mark Slave-O.P.  ",manual_op,&use),
      MENU(" Mark M&S-O.P.  ",manual_m_s_op,&use),
      {0}
    };

      
  Input_pointer (objects1);

  m=0;

  return 0;

}






void Extract_matrix()
{
  struct GModule *module;
  struct Control_Points *cp1;
  char buf[256];
  char *s;
  int rows, cols;
  
  char *first_map_R_mapset;
  char *first_map_R_name;
  int first_map_R_fd;
  char *second_map_R_mapset;
  char *second_map_R_name;
  int second_map_R_fd;
  
  int K;
  
  int correlation_window_dim;
  int search_window_dim;
  int search_window_dim1;
  int search_window_dim2;


  int squared_search_window_dim;
  int search_jump;
  
  int left1, top1, left2, top2;   
  int repeat;  

  int n_1, e_1, n_2, e_2, s_1, s_2, w_1, w_2;
  int r1_1, r1_2, r2_1, r2_2;
  int c1_1, c1_2, c2_1, c2_2;

  int i;

  int h1_r;
  int h1_c;
  int h2_r;
  int h2_c;

  
  DCELL *rowbuf1_R;
  DCELL *tf1_R;
  DCELL *rowbuf2_R;
  DCELL *tf2_R;
  double **search_window;
  double **mat1,**mat2;    
  int r,c;
  int search_border;
  int p1;
  int dim_win_c, dim_win_r;
  char first_sites[500];
  char second_sites[500];
  char file_name_old[500];
  FILE *first_fp;
  FILE *second_fp;  

  int xp1, yp1, xs1, ys1;
  int xp2, yp2, xs2, ys2;
  int nimg;
   
  static int use = 1;


 

  if(n==1)
    {
      m1=VIEW_MAP1;    
      m2=VIEW_MAP2;
    }

  else    
    {
               
      if( (r2 >= r1) && (c2 >= c1 ) )                         
	{
	  xp1 = (c1 - (min(c1,c2)))+1;           
	  xp2 = (c2 - (c1-xp1));        
	  xs2 = (c2 + min((ncols1-c1),(ncols2-c2)))-1;                                     
	  xs1 = (c1 + (xs2 - c2)); 
	  yp1 = (r1 - (min(r1,r2)))+1;    
	  yp2 = (r2 - (r1 - yp1));
	  ys2 = (r2 + min((nrows1-r1),(nrows2-r2)))-1;
	  ys1 = (r1 + (ys2 - r2));
	}     
      else if( (r2 <= r1) && (c2 <= c1) )                        
	{
	  xp2 = (c2 - (min(c2,c1)))+1;
	  xp1 = (c1 - (c2 - xp2));
	  xs1 = (c1 + min((ncols1-c1),(ncols2-c2)))-1;
	  xs2 = (c2 + (xs1 - c1));
	  yp2 = (r2 - min(r2,r1))+1; 
	  yp1 = (r1 - (r2 - yp2));
	  ys1 = (r1 + min((nrows1-r1),(nrows2-r2)))-1;
	  ys2 = (r2 + (ys1 - r1));
	}
      else if( (r2 >= r1) && (c2 <= c1) )    
	{    
	  xp2 = (c2 - min(c2,c1))+1;
	  xp1 = (c1 - (c2 - xp2));
	  xs1 = (c1 + min((ncols1-c1),(ncols2-c2)))-1;
	  xs2 = (c2 + (xs1 - c1));
	  yp1 = (r1 - min(r1,r2))+1;
	  yp2 = (r2 - (r1 - yp1));
	  ys2 = (r2 + min((nrows1-r1),(nrows2-r2)))-1;
	  ys1 = (r1 + (ys2 - r2));
	}
      else if( (r2 <= r1) && (c2 >= c1) )                          
	{ 
	  xp1 = (c1 - min(c1,c2))+1;
	  xp2 = (c2 - (c1 - xp1));
	  xs2 = (c2 + min((ncols2-c2),(ncols1-c1)))-1;
	  xs1 = (c1 + (xs2 - c2));
	  yp2 = (r2 - min(r1,r2))+1;
	  yp1 = (r1 - (r2 - yp2));
	  ys1 = (r1 + min((nrows1-r1),(nrows2-r2)))-1;
	  ys2 = (r2 + (ys1 - r1));
	}


      /* overlap_area(): function that extracts a window from the angle-points 
       * top_left (xp1, yp1) and down_right (xs1, ys1)  
       */
      nimg = 1;
      overlap_area(xp1, yp1, xs1, ys1, nimg, ncols1, nrows1);      
  
 
      nimg = 2;
      overlap_area(xp2, yp2, xs2, ys2, nimg, ncols2, nrows2);
  
  
      m1=VIEW_MAP1_ZOOM;   
      m2=VIEW_MAP2_ZOOM;   
  
    } 



  first_map_R_name=m1->cell.name;
  second_map_R_name=m2->cell.name;
 
 



  /* rows & cols of the view in m1 */
  n_1=m1->cell.head.north;
  e_1=m1->cell.head.east;
  s_1=m1->cell.head.south;
  w_1=m1->cell.head.west; 
  left1 = m1->cell.left;
  top1 = m1->cell.top;
  
  r1_1=s_1/m1->cell.ns_res;
  r1_2=n_1/m1->cell.ns_res;
  c1_1=w_1/m1->cell.ew_res; 
  c1_2=e_1/m1->cell.ew_res;
  
  nrows1=r1_2-r1_1;
  ncols1=c1_2-c1_1;


  /* rows & cols of the view in m2 */
  n_2=m2->cell.head.north;
  e_2=m2->cell.head.east; 
  s_2=m2->cell.head.south;
  w_2=m2->cell.head.west;    
  left2 = m2->cell.left;
  top2 = m2->cell.top; 
  
  r2_1=s_2/m2->cell.ns_res;
  r2_2=n_2/m2->cell.ns_res;
  c2_1=w_2/m2->cell.ew_res; 
  c2_2=e_2/m2->cell.ew_res;

  nrows2=r2_2-r2_1; 
  ncols2=c2_2-c2_1;
  
  
  if(n==1)
    {
      nrows1_img = nrows1;
      ncols1_img = ncols1;
      nrows2_img = nrows2;
      ncols2_img = ncols2;
    }
  
 
  /* Initialize the GIS calls */
  module = G_define_module();
  module->description = "Fine registration of two stereo images";
  
  /* Load environmental vars*/
  group_LOCATION_NAME=buf;
  group_LOCATION_NAME=G_getenv("LOCATION_NAME");
  group_GISDBASE=buf;
  group_GISDBASE=G_getenv("GISDBASE");
  group_MAPSET=buf;
  group_MAPSET=G_getenv("MAPSET");
  
   
  if(n==1)
    {  

      strcpy (name1_initial,first_map_R_name);
      strcpy (name2_initial,second_map_R_name);
      strcpy (mapset_initial,group_MAPSET);
     
    }


  /* Correlation parameters */
  if(n==1)
    {

      if(ncols1 <= nrows1)
	{  
	  search_window_dim1 = ncols1;                      
	} 
      else
	{
	  search_window_dim1 = nrows1;                      
	}

      if(ncols2 <= nrows2)
	{
	  search_window_dim2 = ncols2;                     
	}
      else
	{
	  search_window_dim2 = nrows2;                       
	}



      if(search_window_dim1 <= search_window_dim2)
	{
	  search_window_dim = search_window_dim1;
	} 
      else
	{  
	  search_window_dim = search_window_dim2;
	} 
    }


  else if(n==2)
    { 
      correlation_window_dim=((ncols1/10+nrows1/10)/4);


      
      if(n_points==1)
	{

	  K=((ncols1/4+nrows1/4)/3);    
	  search_window_dim = (correlation_window_dim + K);
	  n_points = 0;

	}
      else
	{

	  K=((ncols1/4+nrows1/4)/8);  
	  search_window_dim = G_math_max_pow2(correlation_window_dim + K);

	}


     
      search_jump=search_window_dim / 2; 
    }
  



  group_name=group.name;
  squared_search_window_dim=search_window_dim*search_window_dim;
  
  
  if(n==1)
    {
      Menu_msg ("Loading first image...");
    } 

  else
    {
      Menu_msg ("Loading first overlapping_image..."); 
    }

  /* Open first real map*/
  
  if((first_map_R_mapset = G_find_cell2(first_map_R_name, "")) == NULL)
    {
      sprintf(buf,"Raster map [%s] not available",first_map_R_name);
      G_fatal_error(buf);
    }
  
  
  if((first_map_R_fd = G_open_cell_old(first_map_R_name, 
				       first_map_R_mapset)) < 0)
    {
      sprintf(buf,"Error opening raster map [%s]", first_map_R_name);
      G_fatal_error(buf);
    }

  /* Set region to first map definition region  < m1 > */ 
  G_get_cellhd (first_map_R_name, first_map_R_mapset, &cellhd1);
  G_set_window(&cellhd1);
  h1_r=cellhd1.rows;
  h1_c=cellhd1.cols;
    

   
  /* Memory allocation for the first overlapping_map */
  
  mat1 = (DCELL **) G_calloc(nrows1,sizeof(DCELL *));
  for(r=0;r<nrows1;r++)
    mat1[r] = (DCELL *) G_calloc(ncols1,sizeof(DCELL)); 
  

  /* Load first map*/
  
  rowbuf1_R = (DCELL *)G_calloc(h1_r * h1_c,sizeof(DCELL));
  tf1_R=rowbuf1_R;
  
  for(r=h1_r-r1_2;r<h1_r-r1_1;r++)
    {  
      G_get_d_raster_row(first_map_R_fd, tf1_R, r);	
      if (G_is_d_null_value (tf1_R)) 
	*tf1_R = NULL_VALUE;	
      c=0;
      while(c<c1_1)
	{	
	  tf1_R++;
	  c++;
	}	
      for(c = c1_1; c < c1_2; c++)
	{
	  mat1[-h1_r+r1_2+r][c-c1_1] = *tf1_R;
	  tf1_R++;
	}
    }
  G_close_cell(first_map_R_fd);
  
  
  /* Open second map*/
  if((second_map_R_mapset = G_find_cell2(second_map_R_name, "")) == NULL)
    {
      sprintf(buf,"Raster map [%s] not available",second_map_R_name);
      G_fatal_error(buf);
    }
  
  if((second_map_R_fd = G_open_cell_old(second_map_R_name, 
					second_map_R_mapset)) < 0) 
    {
      sprintf(buf,"Error opening raster map [%s]", second_map_R_name);
      G_fatal_error(buf);
    } 
    
  /* Set region to second map definition region */
  G_get_cellhd (second_map_R_name, second_map_R_mapset, &cellhd2);
  G_set_window(&cellhd2);
  h2_r=cellhd2.rows;
  h2_c=cellhd2.cols;
  
  
  /* Memory allocation for the second overlapping_map */
  mat2 = (DCELL **) G_calloc(nrows2,sizeof(DCELL *));
  for(r=0;r<nrows2;r++)
    mat2[r] = (DCELL *) G_calloc(ncols2,sizeof(DCELL));

  /* Load second real map */
  if(n==1)
    {
      Menu_msg ("Loading second image...");
    }

  else
    {
      Menu_msg ("Loading second overlapping_image...");
    }
  
  rowbuf2_R=(DCELL *)G_calloc(h2_r * h2_c,sizeof(DCELL));
  tf2_R=rowbuf2_R;
  for(r=h2_r-r2_2;r<h2_r-r2_1;r++)
    
    {				
      G_get_d_raster_row(second_map_R_fd, tf2_R, r);	
      c=0;
      while(c<c2_1)
	{	
	  tf2_R++;
	  c++;
	}	
      for(c = c2_1; c < c2_2; c++)
	{
	  if (G_is_d_null_value (tf2_R)) 
	    *tf2_R = NULL_VALUE;
	  mat2[-h2_r+r2_2+r][c-c2_1] = *tf2_R;
	  tf2_R++;
	}
    }
  
  G_close_cell(second_map_R_fd);
  

  if( (n==1) && (man_op==0) )
    {
      Menu_msg ("Searching in the second image the corresponding point of the central point of the first one...");
    }
  else if(n==2)
    {
      Menu_msg ("Searching points...");
    }
 
  /* Memory allocation */
  search_window = (DCELL **) G_calloc(search_window_dim,
				      sizeof(DCELL *));
  for(r=0;r<search_window_dim;r++)
    search_window[r] = (DCELL *) G_calloc(search_window_dim,
					  sizeof(DCELL));
    
  fft_first[0] = (double *)G_calloc(squared_search_window_dim, sizeof(double));
  fft_first[1] = (double *)G_calloc(squared_search_window_dim, sizeof(double));
  fft_second[0] = (double *)G_calloc(squared_search_window_dim, sizeof(double));
  fft_second[1] = (double *)G_calloc(squared_search_window_dim, sizeof(double));
  fft_prod_con[0] = (double *)G_calloc(squared_search_window_dim, sizeof(double));
  fft_prod_con[1] = (double *)G_calloc(squared_search_window_dim, sizeof(double));
    

  /* Inizialize control points */
  if(n==1)  
    {
      sPoints.count=1;
      sPoints.e1=(double *) G_calloc(sPoints.count,sizeof(double));
      sPoints.n1=(double *) G_calloc(sPoints.count,sizeof(double));
      sPoints.e2=(double *) G_calloc(sPoints.count,sizeof(double));
      sPoints.n2=(double *) G_calloc(sPoints.count,sizeof(double));
      sPoints.status=(int *) G_calloc(sPoints.count,sizeof(int));
    }

  /* Sites file */
  sprintf(first_sites,"%s/%s/%s/site_lists/%s_%s",G__getenv("GISDBASE"),
	  G__getenv("LOCATION_NAME"),G__getenv("MAPSET"),
	  group_name,first_map_R_name);
  sprintf(second_sites,"%s/%s/%s/site_lists/%s_%s",G__getenv("GISDBASE"),
	  G__getenv("LOCATION_NAME"),G__getenv("MAPSET"),
	  group_name,second_map_R_name);
    
   
  /* Set cellhd1 to overlapping_map_1 */  
  cellhd1.rows=nrows1;
  cellhd1.cols=ncols1;
  cellhd1.north=r1_2*m1->cell.ns_res;
  cellhd1.south=r1_1*m1->cell.ns_res;
  cellhd1.east=c1_2*m1->cell.ew_res;
  cellhd1.west=c1_1*m1->cell.ew_res;
 
  /* Set cellhd2 to overlapping_map_2 */  
  cellhd2.rows=nrows2;
  cellhd2.cols=ncols2;
  cellhd2.north=r2_2*m2->cell.ns_res;
  cellhd2.south=r1_1*m2->cell.ns_res;
  cellhd2.east=c2_2*m2->cell.ew_res;
  cellhd2.west=c2_1*m2->cell.ew_res;
  
  /* Set windows to cellhd1 */
  G_set_window(&cellhd1);
 
  
    
  /******************************************/
  /* function --> Search_correlation_points */ 
  /******************************************/     
  Search_correlation_points(mat1, mat2,
			    search_window_dim, 
			    squared_search_window_dim,
			    search_jump,group_name, nrows1, ncols1,
			    search_window, r1_2, c1_1, r2_2, c2_1,
			    h1_r, h2_r, h1_c, h2_c, nrows2, ncols2, n );
    
  
 
  
  sprintf(file_name,"%s/%s/%s/group/%s/TARGET",group_GISDBASE,
	  group_LOCATION_NAME, group_MAPSET,group_name);
  fp = fopen(file_name,"w");
  fprintf(fp,"%s\n%s\n",group_LOCATION_NAME,group_MAPSET);
  fclose(fp);
    

  if(n==2)
    {
      
      G_get_cellhd (name1, mapset, &cellhd1);
      G_adjust_window_to_box (&cellhd1, &VIEW_MAP1->cell.head, VIEW_MAP1->nrows, VIEW_MAP1->ncols);
      Configure_view (VIEW_MAP1, name1, mapset, cellhd1.ns_res, cellhd1.ew_res);
      drawcell(VIEW_MAP1);
      display_points(1);
      R_flush();
      Curses_clear_window (PROMPT_WINDOW);
      

      G_get_cellhd (name2, mapset, &cellhd2);
      G_adjust_window_to_box (&cellhd2, &VIEW_MAP2->cell.head, VIEW_MAP2->nrows, VIEW_MAP2->ncols);
      Configure_view (VIEW_MAP2, name2, mapset, cellhd2.ns_res, cellhd2.ew_res);
      drawcell(VIEW_MAP2);
      display_points(1);
      R_flush();
      Curses_clear_window (PROMPT_WINDOW);
      
      nimg = 1;
      overlap_area(xp1, yp1, xs1, ys1, nimg, ncols1_img, nrows1_img);
     
      nimg = 2;
      overlap_area(xp2, yp2, xs2, ys2, nimg, ncols2_img, nrows2_img);

     
    }


    
  select_current_env ();

  
  display_points_in_view_diff_color (VIEW_MAP1, 1,
				     sPoints.e1, sPoints.n1,
				     sPoints.status, sPoints.count);
  
  
  display_points_in_view_diff_color (VIEW_MAP2, 1,
				     sPoints.e2, sPoints.n2,
				     sPoints.status, sPoints.count);

  
  
  
  display_points_in_view_diff_color (VIEW_MAP1_ZOOM, 1,
				     sPoints.e1, sPoints.n1,
				     sPoints.status, sPoints.count);
  
  
  
  display_points_in_view_diff_color (VIEW_MAP2_ZOOM, 1,
				     sPoints.e2, sPoints.n2,
				     sPoints.status, sPoints.count);  
  
  R_flush();   


 
  if(n==2)
    {
        
      static Objects objects[]=
	{
	  MENU(" MAIN MENU  ",main_menu,&use),   
	  MENU(" STORE POINTS IN FILE  ",store_points,&use),
	  MENU(" TRY AGAIN  ",try_again,&use),   
	  INFO("                ",&use),
	  MENU(" rms-th  ",change_rms_th,&use),
	  MENU(" Auto-Exclusion GCPs  ",auto_exclusion,&use),
	  {0}
	};

      Input_pointer (objects);


      return 0;  
    }





  /* Free memory */

  free( rowbuf1_R);
  free( rowbuf2_R);


  for(r=0;r<nrows1;r++)
    free( mat1[r]);
  free(mat1);
    
  for(r=0;r<nrows2;r++)
    free( mat2[r]);
  free(mat2);
    
  for(r=0;r<search_window_dim;r++)
    free(search_window[r]);
  free(search_window);
    
  for(r=0;r<2;r++) 
    {
      free(fft_first[r]);
      free(fft_second[r]);
      free(fft_prod_con[r]);
    }
    

  if(n==2)         
    {
      sPoints.e1[0];
      sPoints.n1[0];
      sPoints.e2[0];
      sPoints.n2[0];
      sPoints.status[0];
      
      free(sPoints.e1);
      free(sPoints.n1);
      free(sPoints.n2);
      free(sPoints.e2);
      free(sPoints.status);
    }


  
  
  if(n==1)
    {
      n=2;
      Extract_matrix();
    }
  else
    {
      man_op = 0;
      man_m_s_op = 0;

      return 0;
    }

}






void Search_correlation_points(DCELL **mat1_R, DCELL **mat2_R,
			       int search_window_dim, 
			       int squared_search_window_dim, 
			       int search_jump, char *group_name,
			       int dim_win_r, int dim_win_c,
			       DCELL **search_window, int r1_2,int c1_1,
			       int r2_2,int c2_1, int h1_r, int h2_r, 
			       int  h1_c, int h2_c, int nrows2, int ncols2,   int n  )
{
  int r,c;
  int i, j, search_border;
  char *group_MAPSET;
  char *group_LOCATION_NAME;
  char *group_GISDBASE;
  char first_sites[500];
  char second_sites[500];
  char file_name[500];    
  FILE *fp;
  FILE *first_fp;
  FILE *second_fp;  
  double cc;
  double north1,east1,north2,east2;
  int tmp_r,tmp_c;
  double mean;
  int index;
  
 
  

  if( (n==1) && (man_m_s_op==0) )   
    {
	
      r1 = (dim_win_r/2);
      c1 = (dim_win_c/2);
      
      
      if(man_op==0) 
	{	    
                
	  switch (pos_point)
	    {
	    case 0: dist = 0;
	      dist_r = 0;
	      dist_c = 0;
	      break;
	    case 1: r1 = ((dim_win_r/2)-dist);	          
	      break;
	    case 2: r1 = ((dim_win_r/2)+dist);	       
	      break;
	    case 3: c1 = ((dim_win_c/2)-dist);                    
	      break;
	    case 4: c1 = ((dim_win_c/2)+dist);	                     
	      break;
	    }
	  
	  
      
	  r2c = (nrows2 / 2);
	  c2c = (ncols2 / 2);
	  
	  
	  if(pos_point!=0)
	    {
	      search_window_dim = (search_window_dim - (2*dist));
	      squared_search_window_dim = (search_window_dim * search_window_dim);
	      search_jump = (search_window_dim / 2);
	    }
      
      
      
	  search_border =  search_window_dim / 2;
	  
	  
	  
	  /*  Reinizialize fft vectors */
	  
	  for(i=0;i<squared_search_window_dim;i++)
	    {
	      fft_first[0][i]=0.0;
	      fft_first[1][i]=0.0;
	      fft_second[0][i]=0.0;
	      fft_second[1][i]=0.0;
	      fft_prod_con[0][i]=0.0;
	      fft_prod_con[1][i]=0.0;
	    }
      
      
	  /* Coordinates of the "initial" point */
      
	  east1 = G_col_to_easting((double) c1, &cellhd1);
	  north1 = G_row_to_northing((double) r1, &cellhd1);
      
	 
      

	  
	
	  /* Real window in the first image */
	  
	  Extract_portion_of_double_matrix(r1,c1,search_border,search_border,
					   mat1_R,search_window);
      


	  mean = 0.0;
	  for(i=0;i<search_window_dim;i++)
	    {
	      for(j=0;j<search_window_dim;j++)
		{
		  mean +=  search_window[i][j];
		}
	    }
	  mean /= squared_search_window_dim;
      
	  for(i=0;i<search_window_dim;i++)
	    {
	      for(j=0;j<search_window_dim;j++)
		{
		  fft_first[0][i*search_window_dim+j]=search_window[i][j]-mean;
		}
	    }


	  

	  Extract_portion_of_double_matrix(r2c,c2c,search_border,search_border,
					   mat2_R,search_window);


	  mean = 0.0;
	  for(i=0;i<search_window_dim;i++)
	    {
	      for(j=0;j<search_window_dim;j++)
		{
		  mean +=  search_window[i][j];
		}
	    }
	  mean /= squared_search_window_dim;
	  for(i=0;i<search_window_dim;i++)
	    {
	      for(j=0;j<search_window_dim;j++)
		{
		  fft_second[0][i*search_window_dim+j]=search_window[i][j]-mean;
		}
	    }




	  /* fft of the 2 (complex) windows */
	  fft(-1,fft_first,squared_search_window_dim,search_window_dim,
	      search_window_dim);
	  fft(-1,fft_second,squared_search_window_dim,search_window_dim,
	      search_window_dim);



	  
	  /* product of the first fft for the coniugate of the second one */
	  for(i=0;i<squared_search_window_dim;i+=1)
	    {
	      fft_prod_con[0][i] = (fft_first[0][i] * fft_second[0][i]) +
		(fft_first[1][i] * fft_second[1][i]);
	      fft_prod_con[1][i] = (fft_first[1][i] * fft_second[0][i]) -
		(fft_first[0][i] * fft_second[1][i]);
	    }
	  



	  /* fft^{-1} of the product <==> cross-correlation at differnet lag
	     between the two orig. (complex) windows */
	  fft(1,fft_prod_con,squared_search_window_dim,search_window_dim,
	      search_window_dim);




	  /* Search the lag coresponding to the maximum correlation */
	  cc = 0.0;
	 
	  for(i=0;i<squared_search_window_dim;i++)
	    {
	      if(fft_prod_con[0][i] > cc)
		{
		  cc = fft_prod_con[0][i];
		  tmp_r=i/search_window_dim;
		  tmp_c=i%search_window_dim;
		
		}
	    } 


	
	 
	  /* Get coordinates of "ending" point  */
	  if((tmp_r <= search_window_dim/2) && (tmp_c <= search_window_dim/2))
	    {
	   
	      east2 = G_col_to_easting((double) c1  - tmp_c,&cellhd2) + dist_c;
	      north2 = G_row_to_northing((double) r1  - tmp_r,&cellhd2) + dist_r;
	   
	    }
	  if((tmp_r <= search_window_dim/2) && (tmp_c >= search_window_dim/2))
	    {
	      
	      east2 = G_col_to_easting((double) c1  - (tmp_c-search_window_dim-1),&cellhd2) + dist_c;
	      north2 = G_row_to_northing((double) r1 -  tmp_r,&cellhd2) + dist_r;
	   
	    }
	  if((tmp_r >= search_window_dim/2) && (tmp_c <= search_window_dim/2))
	    {
	     
	      east2 = G_col_to_easting((double) c1  - tmp_c,&cellhd2) + dist_c;
	      north2 = G_row_to_northing((double) r1 - (tmp_r-search_window_dim-1),&cellhd2) + dist_r;
	    
	    }
	  if((tmp_r >= search_window_dim/2) && (tmp_c >= search_window_dim/2))
	    {
	    
	      east2 = G_col_to_easting((double) c1  - (tmp_c-search_window_dim-1),&cellhd2) + dist_c;
	      north2 = G_row_to_northing((double) r1  - (tmp_r-search_window_dim-1),&cellhd2) + dist_r;
	    
	    }


	  	  
	  r2 = G_northing_to_row(north2,&cellhd2);
	  c2 = G_easting_to_col(east2,&cellhd2);

	  sPoints.e1[sPoints.count-1] = east1;
	  sPoints.n1[sPoints.count-1] = north1;
	  sPoints.e2[sPoints.count-1] = east2;
	  sPoints.n2[sPoints.count-1] = north2;
	}
 



      else if(man_op==1) 
	{
 
	  east1 = G_col_to_easting((double) c1, &cellhd1);
	  north1 = G_row_to_northing((double) r1, &cellhd1);
      
 
	  sPoints.e1[sPoints.count-1] = east1;
	  sPoints.n1[sPoints.count-1] = north1;
  
	 
	 
	  R_standard_color (BLUE);
	  display_one_point(VIEW_MAP1,east1,north1);
	 
	  
	  manual_op1();
	  
	 	  
	  east2 = e_man2;
	  north2 = n_man2;

  	  
	  r2 = G_northing_to_row(north2,&cellhd2);
	  c2 = G_easting_to_col(east2,&cellhd2);


	  sPoints.e2[sPoints.count-1] = east2;
	  sPoints.n2[sPoints.count-1] = north2;
	  
	  display_points_in_view_diff_color (VIEW_MAP2, 1,
					     sPoints.e2, sPoints.n2,
					     sPoints.status, sPoints.count);
      
	  
      
	  R_flush();   

      
	}
      

	  
  
      /* Fill the POINTS file*/	  
      sPoints.status[sPoints.count-1] = 1;
      sPoints.count += 1;
      sPoints.e1=(double *)G_realloc(sPoints.e1,sPoints.count*sizeof(double));
      sPoints.n1=(double *)G_realloc(sPoints.n1,sPoints.count*sizeof(double));
      sPoints.e2=(double *)G_realloc(sPoints.e2,sPoints.count*sizeof(double));
      sPoints.n2=(double *)G_realloc(sPoints.n2,sPoints.count*sizeof(double));
      sPoints.status=(int *)G_realloc(sPoints.status,sPoints.count*sizeof(int));
  

    }
  

  else if( (n==1) && (man_m_s_op==1) )
    {
      manual_m_s_op1();

      east1 = e_man1;
      north1 = n_man1;

      r1 = G_northing_to_row(north1,&cellhd1);
      c1 = G_easting_to_col(east1,&cellhd1);
      
      
      sPoints.e1[sPoints.count-1] = east1;
      sPoints.n1[sPoints.count-1] = north1;
      

      R_standard_color (BLUE);
      display_one_point(VIEW_MAP1,east1,north1);
	 
      
 
      manual_op1();
	  
	 	  
      east2 = e_man2;
      north2 = n_man2;

  	  
      r2 = G_northing_to_row(north2,&cellhd2);
      c2 = G_easting_to_col(east2,&cellhd2);


      sPoints.e2[sPoints.count-1] = east2;
      sPoints.n2[sPoints.count-1] = north2;
      

      display_points_in_view_diff_color (VIEW_MAP2, 1,
					 sPoints.e2, sPoints.n2,
					 sPoints.status, sPoints.count);
      
	  

      R_flush();   
	  
  
      /* Fill the POINTS file*/	  
      sPoints.status[sPoints.count-1] = 1;
      sPoints.count += 1;
      sPoints.e1=(double *)G_realloc(sPoints.e1,sPoints.count*sizeof(double));
      sPoints.n1=(double *)G_realloc(sPoints.n1,sPoints.count*sizeof(double));
      sPoints.e2=(double *)G_realloc(sPoints.e2,sPoints.count*sizeof(double));
      sPoints.n2=(double *)G_realloc(sPoints.n2,sPoints.count*sizeof(double));
      sPoints.status=(int *)G_realloc(sPoints.status,sPoints.count*sizeof(int));
  


    }   




  else
    {

    
      /*Begin computation*/
      search_border =  search_window_dim / 2;
  
      for(r = search_border; r < dim_win_r - search_border; r += search_jump)
	{
	  for(c = search_border; c < dim_win_c - search_border; c += search_jump)
	    {
  
	      /*  Reinizialize fft vectors */
	  
	      for(i=0;i<squared_search_window_dim;i++)
		{
		  fft_first[0][i]=0.0;
		  fft_first[1][i]=0.0;
		  fft_second[0][i]=0.0;
		  fft_second[1][i]=0.0;
		  fft_prod_con[0][i]=0.0;
		  fft_prod_con[1][i]=0.0;
		}
	  
	  
	      /* Coordinates of the "initial" point */
	  
	      east1 = G_col_to_easting((double) c, &cellhd1);
	      north1 = G_row_to_northing((double) r, &cellhd1);
	
	      /* Real window in the first image */
	  
	      Extract_portion_of_double_matrix(r,c,search_border,search_border,
					       mat1_R,search_window);
	  
	      mean = 0.0;
	      for(i=0;i<search_window_dim;i++)
		{
		  for(j=0;j<search_window_dim;j++)
		    {
		      mean +=  search_window[i][j];
		    }
		}
	      mean /= squared_search_window_dim;
	
	      for(i=0;i<search_window_dim;i++)
		{
		  for(j=0;j<search_window_dim;j++)
		    {
		      fft_first[0][i*search_window_dim+j]=search_window[i][j]-mean;
		    }
		}
	  
	  
	      /* Real window in the second image */
	      	
	      if((r-search_border+2*search_border>=nrows2)||(c-search_border+2*search_border>=ncols2))
		{
		  if (sPoints.count<=1)
		    {	   
		      Menu_msg("DEFINE A NEW REGION.");
		      sleep(3);
		      pause;
		    }
		  return 0;
		}

	      Extract_portion_of_double_matrix(r,c,search_border,search_border,
					       mat2_R,search_window);
	      mean = 0.0;
	      for(i=0;i<search_window_dim;i++)
		{
		  for(j=0;j<search_window_dim;j++)
		    {
		      mean +=  search_window[i][j];
		    }
		}
	      mean /= squared_search_window_dim;
	      for(i=0;i<search_window_dim;i++)
		{
		  for(j=0;j<search_window_dim;j++)
		    {
		      fft_second[0][i*search_window_dim+j]=search_window[i][j]-mean;
		    }
		}




	      /* fft of the 2 (complex) windows */
	      fft(-1,fft_first,squared_search_window_dim,search_window_dim,
		  search_window_dim);
	      fft(-1,fft_second,squared_search_window_dim,search_window_dim,
		  search_window_dim);




	  
	      /* product of the first fft for the coniugate of the second one */
	      for(i=0;i<squared_search_window_dim;i+=1)
		{
		  fft_prod_con[0][i] = (fft_first[0][i] * fft_second[0][i]) +
		    (fft_first[1][i] * fft_second[1][i]);
		  fft_prod_con[1][i] = (fft_first[1][i] * fft_second[0][i]) -
		    (fft_first[0][i] * fft_second[1][i]);
		}
	  
	  


	  
	      /* fft^{-1} of the product <==> cross-correlation at differnet lag
		 between the two orig. (complex) windows */
	      fft(1,fft_prod_con,squared_search_window_dim,search_window_dim,
		  search_window_dim);




	  
	      /* Search the lag coresponding to the maximum correlation */
	      cc = 0.0;
	 
	      for(i=0;i<squared_search_window_dim;i++)
		{
		  if(fft_prod_con[0][i] > cc)
		    {
		      cc = fft_prod_con[0][i];
		      tmp_r=i/search_window_dim;
		      tmp_c=i%search_window_dim;
		
		    }
		} 
	
	      /* Get coordinates of "ending" point  */
	      if((tmp_r <= search_window_dim/2) && (tmp_c <= search_window_dim/2))
		{
	   
		  east2 = G_col_to_easting((double) c  - tmp_c,&cellhd2);
		  north2 = G_row_to_northing((double) r  - tmp_r,&cellhd2);
	   
		}
	      if((tmp_r <= search_window_dim/2) && (tmp_c >= search_window_dim/2))
		{
	      
		  east2 = G_col_to_easting((double) c  - (tmp_c-search_window_dim-1),&cellhd2);
		  north2 = G_row_to_northing((double) r -  tmp_r,&cellhd2);
	   
		}
	      if((tmp_r >= search_window_dim/2) && (tmp_c <= search_window_dim/2))
		{
	     
		  east2 = G_col_to_easting((double) c  - tmp_c,&cellhd2);
		  north2 = G_row_to_northing((double) r  - (tmp_r-search_window_dim-1),&cellhd2);
	    
		}
	      if((tmp_r >= search_window_dim/2) && (tmp_c >= search_window_dim/2))
		{
	    
		  east2 = G_col_to_easting((double) c  - (tmp_c-search_window_dim-1),&cellhd2);
		  north2 = G_row_to_northing((double) r  - (tmp_r-search_window_dim-1),&cellhd2);
	    
		}
      
    

	      /* Fill the POINTS file*/
	      sPoints.e1[sPoints.count-1] = east1;
	      sPoints.n1[sPoints.count-1] = north1;
	      sPoints.e2[sPoints.count-1] = east2;
	      sPoints.n2[sPoints.count-1] = north2;
	
	      sPoints.status[sPoints.count-1] = 1;
	      sPoints.count += 1;
	      sPoints.e1=(double *)G_realloc(sPoints.e1,sPoints.count*sizeof(double));
	      sPoints.n1=(double *)G_realloc(sPoints.n1,sPoints.count*sizeof(double));
	      sPoints.e2=(double *)G_realloc(sPoints.e2,sPoints.count*sizeof(double));
	      sPoints.n2=(double *)G_realloc(sPoints.n2,sPoints.count*sizeof(double));
	      sPoints.status=(int *)G_realloc(sPoints.status,sPoints.count*sizeof(int));
	    }
	  G_percent (r,dim_win_r, 1);   
	}



    }

}

void Extract_portion_of_double_matrix(int r,int c,int br,int bc,DCELL **mat,DCELL **wind)
     /*
       extract a squared portion of a matrix mat
       given a the indeces of the center [r,c] 
       and the semilength of the borders [br,bc]
       Output to array wind
     */
{
  int i,j;
  for(i=0;(i <2*br);i++)
    for(j = 0;(j <2*bc);j++)
      {
	wind[i][j] = mat[r - br + i][c - bc +j];    
      }
}







static int less_GCPs()
{

  n_points = 1;

  return 0;
}





static int manual_op()
{
  man_op = 1;

  n=1;

  Extract_matrix();

  return 0;
}




static int manual_op1()
{

  static int use = 1;


  static Objects objects[] =
    {
      INFO(" Mark on the second img the Overlap-Point  ",&use),
      OTHER(mark_op, &use),
      {0}
    };
  
  Input_pointer (objects);
  Menu_msg ("");
  
  
  
  return 0;


}





static int mark_op(int x,int y,int button)
{

  static int use = 1;
  
  if (button != 1)
    return where (x,y);
    
  if (VIEW_MAP2->cell.configured && In_view (VIEW_MAP2, x, y))
    mark_point_op(VIEW_MAP2, x, y);
   
  else
    return 0;
  
  return -1 ; /* return but don't quit */
}




static int mark_point_op (View *view,int x, int y)
{

  /* convert x,y to east,north at center of cell */
  c2= view_to_col (view, x);
  e_man2 = col_to_easting (&view->cell.head, c2, 0.5);
  r2= view_to_row (view, y);
  n_man2 = row_to_northing (&view->cell.head, r2, 0.5);



  return 0 ; 


}



static int manual_m_s_op()
{
  man_m_s_op = 1;

  n=1;

  Extract_matrix();


  return 0;
}


static int manual_m_s_op1()
{

  static int use = 1;


  static Objects objects[] =
    {
      INFO(" Mark on the first img the Overlap-Point  ",&use),
      OTHER(mark_m_s_op, &use),
      {0}
    };
  
  Input_pointer (objects);
  Menu_msg ("");
  

  return 0;
}


static int mark_m_s_op(int x,int y,int button)
{

  static int use = 1;
  
  if (button != 1)
    return where (x,y);
    
  if (VIEW_MAP1->cell.configured && In_view (VIEW_MAP1, x, y))
    mark_point_m_s_op(VIEW_MAP1, x, y);
   
  else
    return 0;
  
  return -1 ; /* return but don't quit */
}




static int mark_point_m_s_op (View *view,int x, int y)
{

  /* convert x,y to east,north at center of cell */
  c1= view_to_col (view, x);
  e_man1 = col_to_easting (&view->cell.head, c1, 0.5);
  r1= view_to_row (view, y);
  n_man1 = row_to_northing (&view->cell.head, r1, 0.5);



  return 0 ; 


}




static int central()
{
  n=1;
  pos_point = 0;
  man_op=0; 

  Extract_matrix();

  return 0;

}


static int shift1()
{
  double nn_1,ee_1,ss_1,ww_1,rr1_1,rr1_2,cc1_1,cc1_2,nnrows1,nncols1;
  int shift1;

  nn_1=VIEW_MAP1->cell.head.north;
  ee_1=VIEW_MAP1->cell.head.east;
  ss_1=VIEW_MAP1->cell.head.south;
  ww_1=VIEW_MAP1->cell.head.west; 
 
  rr1_1=ss_1/VIEW_MAP1->cell.ns_res;
  rr1_2=nn_1/VIEW_MAP1->cell.ns_res;
  cc1_1=ww_1/VIEW_MAP1->cell.ew_res; 
  cc1_2=ee_1/VIEW_MAP1->cell.ew_res;
  
  nnrows1=rr1_2-rr1_1;
  nncols1=cc1_2-cc1_1;



  shift1 = (((nnrows1 + nncols1)/2)/100)*5;

  switch (pos_point)
    {
      
    case 1: dist = shift1;
      dist_r = -shift1;
      dist_c = 0;               
      break;
    case 2: dist = shift1;
      dist_r = shift1;
      dist_c = 0;
      break;
    case 3: dist = shift1;
      dist_c = shift1;
      dist_r = 0;            
      break;
    case 4: dist = shift1;
      dist_c = -shift1;
      dist_r = 0;               
      break;
    }
  


  Extract_matrix();

  return 0;
}




static int shift2()
{

  double nn_1,ee_1,ss_1,ww_1,rr1_1,rr1_2,cc1_1,cc1_2,nnrows1,nncols1;
  int shift2;

  nn_1=VIEW_MAP1->cell.head.north;
  ee_1=VIEW_MAP1->cell.head.east;
  ss_1=VIEW_MAP1->cell.head.south;
  ww_1=VIEW_MAP1->cell.head.west; 
 
  rr1_1=ss_1/VIEW_MAP1->cell.ns_res;
  rr1_2=nn_1/VIEW_MAP1->cell.ns_res;
  cc1_1=ww_1/VIEW_MAP1->cell.ew_res; 
  cc1_2=ee_1/VIEW_MAP1->cell.ew_res;
  
  nnrows1=rr1_2-rr1_1;
  nncols1=cc1_2-cc1_1;



  shift2 = (((nnrows1 + nncols1)/2)/100)*10;



  switch (pos_point)
    {
	
    case 1: dist = shift2;
      dist_r = -shift2;
      dist_c = 0;               
      break;
    case 2: dist = shift2;
      dist_r = shift2;
      dist_c = 0;
      break;
    case 3: dist = shift2;
      dist_c = shift2;
      dist_r = 0;            
      break;
    case 4: dist = shift2;
      dist_c = -shift2;
      dist_r = 0;               
      break;
    }
  

  
  Extract_matrix();

  return 0;
}





static int top()
{
  static int use = 1;
  
  n=1;
  pos_point = 1;
  man_op=0; 

  static Objects objects2[]=
    {   
      MENU(" MAIN MENU  ",main_menu,&use),  
      MENU(" <--  ",cancel,&use), 
      INFO("  Shift O.P. (% of map) -> ",&use),
      MENU(" 5%  ",shift1,&use),
      MENU(" 10%  ",shift2,&use),   
      {0}
    };

  Input_pointer (objects2);


  return 0;

}





static int bottom()
{
  static int use = 1;

  n=1;
  pos_point = 2;
  man_op=0; 

  static Objects objects3[]=
    {  
      MENU(" MAIN MENU  ",main_menu,&use),  
      MENU(" <--  ",cancel,&use), 
      INFO("  Shift O.P. (% of map) -> ",&use),
      MENU(" 5%  ",shift1,&use),
      MENU(" 10%  ",shift2,&use),   
      {0}
    };

  Input_pointer (objects3);


  return 0;

}



static int left()
{
  static int use = 1;
 
  n=1;
  pos_point = 3;
  man_op=0; 

  static Objects objects4[]=
    {        
      MENU(" MAIN MENU  ",main_menu,&use),  
      MENU(" <--  ",cancel,&use),
      INFO("  Shift O.P. (% of map) -> ",&use),
      MENU(" 5%  ",shift1,&use),
      MENU(" 10%  ",shift2,&use),   
      {0}
    };

  Input_pointer (objects4);


  return 0;

}



static int right()
{
  static int use = 1;

  n=1;
  pos_point = 4;
  man_op=0; 

  static Objects objects5[]=
    {     
      MENU(" MAIN MENU  ",main_menu,&use),  
      MENU(" <--  ",cancel,&use), 
      INFO("  Shift O.P. (% of map) -> ",&use),
      MENU(" 5%  ",shift1,&use),
      MENU(" 10%  ",shift2,&use),   
      {0}
    };

  Input_pointer (objects5);


  return 0;

}






static int try_again()
{

  static int use = 1;

  G_get_cellhd (name1_initial, mapset_initial, &cellhd1);
  G_adjust_window_to_box (&cellhd1, &VIEW_MAP1->cell.head, VIEW_MAP1->nrows, VIEW_MAP1->ncols);
  Configure_view (VIEW_MAP1, name1_initial, mapset_initial, cellhd1.ns_res, cellhd1.ew_res);
  drawcell(VIEW_MAP1);
  display_points(1);
  R_flush();
  Curses_clear_window (PROMPT_WINDOW);

  Erase_view (VIEW_MAP1_ZOOM);  

  
  G_get_cellhd (name2_initial, mapset_initial, &cellhd2);
  G_adjust_window_to_box (&cellhd2, &VIEW_MAP2->cell.head, VIEW_MAP2->nrows, VIEW_MAP2->ncols);
  Configure_view (VIEW_MAP2, name2_initial, mapset_initial, cellhd2.ns_res, cellhd2.ew_res);
  drawcell(VIEW_MAP2);
  display_points(1);
  R_flush();
  Curses_clear_window (PROMPT_WINDOW);

  Erase_view (VIEW_MAP2_ZOOM);  


  static Objects objects3[]=
    {   


      MENU(" MAIN MENU  ",cancel,&use),   
      INFO(" O.P. -> ",&use),
      MENU(" Central  ",central,&use),
      MENU(" Top  ",top,&use),
      MENU(" Bottom  ",bottom,&use),   
      MENU(" Left  ",left,&use),   
      MENU(" Right  ",right,&use),
      INFO("  ",&use),
      MENU(" LESS GCPs  ",less_GCPs,&use),
      MENU(" Mark Slave-O.P.  ",manual_op,&use),
      MENU(" Mark M&S-O.P.  ",manual_m_s_op,&use),
      {0}
    };

      
  Input_pointer (objects3);
  
  return 0;
}









static int store_points()
{

  int i;


  sPoints.count -= 1;
  if(sPoints.count > 0)
    {
      
      sprintf(file_name,"%s/%s/%s/group/%s/POINTS",group_GISDBASE,
	      group_LOCATION_NAME,group_MAPSET,group_name);
    
      fp = fopen(file_name,"w");                                
      fprintf (fp,"# %7s %15s %15s %15s %9s status\n","",
	       "provaimage","","target","");
      fprintf (fp,"# %15s %15s %15s %15s   (1=ok)\n",
	       "east","north","east","north");
      fprintf (fp,"#\n");
	    
      for (i = 1; i < sPoints.count; i++)            /* i=1 because the sPoints[0] is the O.P. */
	if ( sPoints.status[i] != -1)
	  fprintf (fp, "  %15f %15f %15f %15f %4d\n",
		   sPoints.e1[i],  sPoints.n1[i],  sPoints.e2[i],  sPoints.n2[i],  sPoints.status[i]);


      fclose (fp);
    }
  

    
  /* Load new control points */
     
  for (i = 1; i < sPoints.count; i++)   
    if ( sPoints.status[i] != -1)
      I_new_control_point (&group.points,sPoints.e1[i],  sPoints.n1[i],  
			 sPoints.e2[i],  sPoints.n2[i],  sPoints.status[i] );
  


  m=1;  /* To directly return to the main menu */
  

  return 0;

}





static int main_menu()
{
  m=1;

  return 0;
}


static int 
cancel (void)
{
  return -1; 
}






static int change_rms_th()
{
  static int use = 1;

  static Objects objects[]=
    {
      MENU(" MAIN MENU  ",main_menu,&use),   
      MENU(" <--  ",cancel,&use), 
      INFO("      ",&use),
      MENU(" 1  ",th_1,&use), 
      MENU(" 2  ",th_2,&use), 
      MENU(" 3  ",th_3,&use), 
      MENU(" 4  ",th_4,&use), 
      MENU(" 5  ",th_5,&use), 
      MENU(" OTHER  ",other_th,&use), 
      /*
	OPTION(" 1  ",   2, &after_OPTION_out),
	OPTION(" 2  ",   2, &temp_th_2),
	OPTION(" 3  ",   2, &temp_th_3),
	OPTION(" 4  ",   2, &temp_th_4),
	OPTION(" 5  ",   2, &temp_th_5),*/
      {0}
    };

 
  
  Input_pointer (objects);
  
    
  return 0;
}



static int after_th()
{  
  static int use = 1;

  
  static Objects objects3[]=
    {  
      MENU(" MAIN MENU  ",main_menu,&use),   
      MENU(" STORE POINTS IN FILE  ",store_points,&use),
      MENU(" TRY AGAIN  ",try_again,&use),   
      INFO("                ",&use),
      MENU(" rms-th  ",change_rms_th,&use),
      MENU(" Auto-Exclusion GCPs  ",auto_exclusion,&use),
      {0}
    };

      
  Input_pointer (objects3);
  


  return 0;
}






static int th_1()
{
  th=1;

  after_th();

  return 0;
}


static int th_2()
{
  th=2;

  after_th();

  return 0;
}


static int th_3()
{
  th=3;

  after_th();

  return 0;
}


static int th_4()
{
  th=4;

  after_th();

  return 0;
}

static int th_5()
{
  th=5;

  after_th();

  return 0;
}

 

static int other_th()
{
  char buf[100];
  double tmp_th;
  
  G_clear_screen();

  while(1)
    {
      Curses_prompt_gets ("Insert the rms-threshold desired: ", buf);
      sscanf (buf, "%lf", &tmp_th); 
      if(tmp_th!=0) break;
      
    }
  
  th = tmp_th;
  
  after_th();
  
  return 0;
}





int auto_exclusion(void)
{
  int k;
  int i;
  static int use = 1;

  sPoints.count = sPoints.count -1;   

  /* Load new control points */
     
  for (i = 1; i < sPoints.count; i++)   
    if ( sPoints.status[i] != -1)
      I_new_control_point (&group.points,sPoints.e1[i],  sPoints.n1[i],  
			 sPoints.e2[i],  sPoints.n2[i],  sPoints.status[i] );
  



  first_point = 0;

  /* allocate predicted values */
  xres = (double *) G_calloc (group.points.count, sizeof (double));
  yres = (double *) G_calloc (group.points.count, sizeof (double));
  gnd  = (double *) G_calloc (group.points.count, sizeof (double));
  
 
  compute_transformation();


  while(rms>=th)
    { 
      for(k=0; k < group.points.count; k++)
	{
	  
	  if(group.equation_stat > 0 && group.points.status[k]==1)
	    {
	      
	      if (k == xmax || k == ymax || k == gmax)
		{
		  group.points.status[k] = 0;		
		}
	    }
	  compute_transformation();

	}
    }
  display_points(1);

  
  
  static Objects objects[]=
    {
      MENU(" MAIN MENU  ",main_menu,&use),   
      MENU(" ANALYZE & STORE  ",pre_analyze,&use),
      {0}
    };
  
  Input_pointer (objects);


  free (xres); free (yres); free (gnd);

  return 0;
}



static int pre_analyze()
{    
  
  analyze();
 
  m=1;
  
  return 0;
}






static int compute_transformation (void)
{
  int n, count;
  double d,d1,d2,sum;
  double e1, e2, n1, n2;
  double t1, t2, u1, u2;
  double xval, yval, gval;
  double tval, uval, lgval;

  xmax = ymax = gmax = 0;
  xval = yval = gval = 0.0;

  Compute_equation();     

  /* compute the row,col error plus ground error
   * keep track of largest and second largest error
   */
  sum = 0.0;
  rms = 0.0;
  count = 0;
  for (n = 0; n < group.points.count && group.equation_stat>0; n++)
    {
      if (group.points.status[n] !=1) continue;
      count++;
      georef (group.points.e2[n], group.points.n2[n], &e1, &n1, group.E21, group.N21);
      georef (group.points.e1[n], group.points.n1[n], &e2, &n2, group.E12, group.N12);
      
      if((d = xres[n] = e1-group.points.e1[n]) < 0)
	d = -d;
      if (d > xval)
	{
	  xmax = n;
	  xval = d;
	}

      if ((d = yres[n] = n1-group.points.n1[n]) < 0)
	d = -d;
      if (d > yval)
	{
	  ymax = n;
	  yval = d;
	}

      /* compute ground error (ie along diagonal) */
      d1 = e2 - group.points.e2[n];
      d2 = n2 - group.points.n2[n];
      d = d1*d1 + d2*d2;
      sum += d;                 /* add it to rms sum, before taking sqrt */
      d = sqrt(d);
      gnd[n] = d;
      if (d > gval)             /* is this one the max? */
	{
	  gmax = n;
	  gval = d;
	}

    }
  /* compute overall rms error */
  if (count)
    rms = sqrt (sum/count);

    
  return 0;
}






