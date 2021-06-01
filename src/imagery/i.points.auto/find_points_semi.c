#include <unistd.h>
#include <stdlib.h>
#include <stdio.h>
#include <signal.h>

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


#ifdef DEBUG
#undef DEBUG
#endif

double *fft_first_s[2];
double *fft_second_s[2];
double *fft_prod_con_s[2];
 
View *ms1, *ms2; 

void Extract_matrix_semi()
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

  int squared_search_window_dim;
  int search_jump;
  
  int ncols1, ncols2, nrows1, nrows2;
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

  
  char *group_name;
  char *group_MAPSET;
  char *group_LOCATION_NAME;
  char *group_GISDBASE;
  DCELL *rowbuf1_R;
  DCELL *tf1_R;
  DCELL *rowbuf2_R;
  DCELL *tf2_R;
  double **search_window;
  double **mat1,**mat2;    
  int r,c;
  int search_border;
  int q;
  int p1;
  int dim_win_c, dim_win_r;
  char first_sites[500];
  char second_sites[500];
  char file_name[500];
  char file_name_old[500];
  FILE *first_fp;
  FILE *second_fp;  
  FILE *fp;
  FILE *fp_old; 
  
 
  
  /* Read VIEW_MAP1_ZOOM & VIEW_MAP2_ZOOM informations */
  
  
  ms1=VIEW_MAP1_ZOOM;
  ms2=VIEW_MAP2_ZOOM;
  
  first_map_R_name=ms1->cell.name;
  second_map_R_name=ms2->cell.name;
 
  /* rows & cols of VIEW_MAP1_ZOOM */
  n_1=ms1->cell.head.north;
  e_1=ms1->cell.head.east;
  s_1=ms1->cell.head.south;
  w_1=ms1->cell.head.west; 
  left1 = ms1->cell.left;
  top1 = ms1->cell.top;
  
  r1_1=s_1/ms1->cell.ns_res;
  r1_2=n_1/ms1->cell.ns_res;
  c1_1=w_1/ms1->cell.ew_res; 
  c1_2=e_1/ms1->cell.ew_res;
  
  nrows1=r1_2-r1_1;
  ncols1=c1_2-c1_1;


  /* rows & cols of VIEW_MAP2_ZOOM */
  n_2=ms2->cell.head.north;
  e_2=ms2->cell.head.east; 
  s_2=ms2->cell.head.south;
  w_2=ms2->cell.head.west;    
  left2 = ms2->cell.left;
  top2 = ms2->cell.top; 
  
  r2_1=s_2/ms2->cell.ns_res;
  r2_2=n_2/ms2->cell.ns_res;
  c2_1=w_2/ms2->cell.ew_res; 
  c2_2=e_2/ms2->cell.ew_res;

  nrows2=r2_2-r2_1; 
  ncols2=c2_2-c2_1;
  
  
 
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
  
  
  /* Correlation parameters */
  correlation_window_dim=((ncols1/10+nrows1/10)/2);
  K=((ncols1/4+nrows1/4)/2);

  search_window_dim = G_math_max_pow2(correlation_window_dim + K);
  group_name=group.name;
  squared_search_window_dim=search_window_dim*search_window_dim;
  search_jump=search_window_dim / 2; 
  
 
  
  Menu_msg ("Loading first zoom_image..."); 
  
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

  /* Set region to first map definition region  < ms1 > */ 
  G_get_cellhd (first_map_R_name, first_map_R_mapset, &cellhd1);
  G_set_window(&cellhd1);
  h1_r=cellhd1.rows;
  h1_c=cellhd1.cols;
    

   
  /* Memory allocation for zoom_map_1 */
  
  mat1 = (DCELL **) G_calloc(nrows1,sizeof(DCELL *));
  for(r=0;r<nrows1;r++)
    mat1[r] = (DCELL *) G_calloc(ncols1,sizeof(DCELL)); 
  

  /* Load first  map*/
  
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
  
  
  /* Open second  map*/
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
  
  
  /* Memory allocation for zoom_map_2 */
  mat2 = (DCELL **) G_calloc(nrows2,sizeof(DCELL *));
  for(r=0;r<nrows2;r++)
    mat2[r] = (DCELL *) G_calloc(ncols2,sizeof(DCELL));

  /* Load second real map */
  Menu_msg ("Loading second zoom_image...");
  
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
  
  
  Menu_msg ("Searching points...");
  
  /* Memory allocation */
  search_window = (DCELL **) G_calloc(search_window_dim,
				      sizeof(DCELL *));
  for(r=0;r<search_window_dim;r++)
    search_window[r] = (DCELL *) G_calloc(search_window_dim,
					  sizeof(DCELL));
    
  fft_first_s[0] = (double *)G_calloc(squared_search_window_dim, sizeof(double));
  fft_first_s[1] = (double *)G_calloc(squared_search_window_dim, sizeof(double));
  fft_second_s[0] = (double *)G_calloc(squared_search_window_dim, sizeof(double));
  fft_second_s[1] = (double *)G_calloc(squared_search_window_dim, sizeof(double));
  fft_prod_con_s[0] = (double *)G_calloc(squared_search_window_dim, sizeof(double));
  fft_prod_con_s[1] = (double *)G_calloc(squared_search_window_dim, sizeof(double));
    

  /* Inizialize control points */
  sPoints.count=1;
  sPoints.e1=(double *) G_calloc(sPoints.count,sizeof(double));
  sPoints.n1=(double *) G_calloc(sPoints.count,sizeof(double));
  sPoints.e2=(double *) G_calloc(sPoints.count,sizeof(double));
  sPoints.n2=(double *) G_calloc(sPoints.count,sizeof(double));
  sPoints.status=(int *) G_calloc(sPoints.count,sizeof(int));

  /* Sites file */
  sprintf(first_sites,"%s/%s/%s/site_lists/%s_%s",G__getenv("GISDBASE"),
	  G__getenv("LOCATION_NAME"),G__getenv("MAPSET"),
	  group_name,first_map_R_name);
  sprintf(second_sites,"%s/%s/%s/site_lists/%s_%s",G__getenv("GISDBASE"),
	  G__getenv("LOCATION_NAME"),G__getenv("MAPSET"),
	  group_name,second_map_R_name);
    
   
  /* Set cellhd1 to zoom_map_1 */  
  cellhd1.rows=nrows1;
  cellhd1.cols=ncols1;
  cellhd1.north=r1_2*ms1->cell.ns_res;
  cellhd1.south=r1_1*ms1->cell.ns_res;
  cellhd1.east=c1_2*ms1->cell.ew_res;
  cellhd1.west=c1_1*ms1->cell.ew_res;
 
  /* Set cellhd2 to zoom_map_2 */  
  cellhd2.rows=nrows2;
  cellhd2.cols=ncols2;
  cellhd2.north=r2_2*ms2->cell.ns_res;
  cellhd2.south=r1_1*ms2->cell.ns_res;
  cellhd2.east=c2_2*ms2->cell.ew_res;
  cellhd2.west=c2_1*ms2->cell.ew_res;
  
  /* Set windows to cellhd1 */
  G_set_window(&cellhd1);
 
    
    
  /******************************************/
  /* function --> Search_correlation_points */ 
  /******************************************/     
  Search_correlation_points_semi(mat1, mat2,
			    search_window_dim, 
			    squared_search_window_dim,
			    search_jump,group_name, nrows1, ncols1,
			    search_window, r1_2, c1_1, r2_2, c2_1,
			    h1_r, h2_r, h1_c, h2_c, nrows2, ncols2 );
    
   
  
   
  /* Build group/POINTS file */ 
  sPoints.count -= 1;
  if(sPoints.count > 0)
    {
      sprintf(file_name,"%s/%s/%s/group/%s/POINTS",group_GISDBASE,
	      group_LOCATION_NAME,group_MAPSET,group_name);
      fp_old = fopen(file_name,"r");
     if( fp_old==NULL)
	{	   
	  q=0;
	}
      else
	{
	  q=1;
	  fclose(fp_old);
	}
      
      if (q==0)
	{
	  fp = fopen(file_name,"a");
	  fprintf (fp,"# %7s %15s %15s %15s %9s status\n","",
		   "image","","target","");
	  fprintf (fp,"# %15s %15s %15s %15s   (1=ok)\n",
		   "east","north","east","north");
	  fprintf (fp,"#\n");
	    
	  for (i = 0; i < sPoints.count; i++)
	    if ( sPoints.status[i] != -1)
	      fprintf (fp, "  %15f %15f %15f %15f %4d\n",
		       sPoints.e1[i],  sPoints.n1[i],  sPoints.e2[i],  sPoints.n2[i],  sPoints.status[i]);
	    
	}
      if(q==1)
	{
	  fp = fopen(file_name,"a");
	  for (i = 0; i <  sPoints.count; i++)
	    if ( sPoints.status[i] != -1)
	      fprintf (fp, "  %15f %15f %15f %15f %4d\n", sPoints.e1[i],  sPoints.n1[i],  sPoints.e2[i],  sPoints.n2[i],  sPoints.status[i]);
	}
      fclose (fp);
    }
    
  /* Load new control points */
   
  for (i = 0; i < sPoints.count; i++)
    if ( sPoints.status[i] != -1)
      I_new_control_point (&group.points,sPoints.e1[i],  sPoints.n1[i],  
			 sPoints.e2[i],  sPoints.n2[i],  sPoints.status[i] );
    
  /* Build group/REF file */
  /* 
  sprintf(file_name,"%s/%s/%s/group/%s/REF",group_GISDBASE,
	  group_LOCATION_NAME, group_MAPSET,group_name);
  fp = fopen(file_name,"w");
  fprintf(fp,"%s %s\n",first_map_R_name,first_map_R_mapset);
    
  fclose(fp);
  */    

  /* Build group/TARGET file */ 
  sprintf(file_name,"%s/%s/%s/group/%s/TARGET",group_GISDBASE,
	  group_LOCATION_NAME, group_MAPSET,group_name);
  fp = fopen(file_name,"w");
  fprintf(fp,"%s\n%s\n",group_LOCATION_NAME,group_MAPSET);
  fclose(fp);
    
  /* Display new points */   
  select_current_env ();
  display_points_in_view (VIEW_MAP1, 1,
			  group.points.e1, group.points.n1,
			  group.points.status, group.points.count);
    
  display_points_in_view (VIEW_MAP1_ZOOM, 1,
			  group.points.e1, group.points.n1,
			  group.points.status, group.points.count);
    
  display_points_in_view (VIEW_MAP2, 1,
			  group.points.e2, group.points.n2,
			  group.points.status, group.points.count);
    
  display_points_in_view (VIEW_MAP2_ZOOM, 1,
			  group.points.e2, group.points.n2,
			  group.points.status, group.points.count);
  R_flush();   
    
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
      free(fft_first_s[r]);
      free(fft_second_s[r]);
      free(fft_prod_con_s[r]);
    }
    
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
    

    
  return 0;
}


void Search_correlation_points_semi(DCELL **mat1_R, DCELL **mat2_R,
			       int search_window_dim, 
			       int squared_search_window_dim, 
			       int search_jump, char *group_name,
			       int dim_win_r, int dim_win_c,
			       DCELL **search_window, int r1_2,int c1_1,
			       int r2_2,int c2_1, int h1_r, int h2_r, 
			       int  h1_c, int h2_c, int nrows2, int ncols2  )
{
  int r,c,i, j,search_border;
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
  
  
  
  
  
  /*Begin computation*/
  search_border =  search_window_dim / 2;
  
  
  for(r = search_border; r < dim_win_r - search_border; r += search_jump)
    {
      for(c = search_border; c < dim_win_c - search_border; c += search_jump)
	{
	  /*  Reinizialize fft vectors */
	  
	  for(i=0;i<squared_search_window_dim;i++)
	    {
	      fft_first_s[0][i]=0.0;
	      fft_first_s[1][i]=0.0;
	      fft_second_s[0][i]=0.0;
	      fft_second_s[1][i]=0.0;
	      fft_prod_con_s[0][i]=0.0;
	      fft_prod_con_s[1][i]=0.0;
	    }
	  
	  
	  /* Coordinates of the "initial" point */
	  
	  east1 = G_col_to_easting((double) c, &cellhd1);
	  north1 = G_row_to_northing((double) r, &cellhd1);
	
	  /* Real window in the first image */
	  
	  Extract_portion_of_double_matrix_semi(r,c,search_border,search_border,
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
		  fft_first_s[0][i*search_window_dim+j]=search_window[i][j]-mean;
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

	  Extract_portion_of_double_matrix_semi(r,c,search_border,search_border,
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
		  fft_second_s[0][i*search_window_dim+j]=search_window[i][j]-mean;
		}
	    }
	  
#ifdef DEBUG
	  for(i=0;i<squared_search_window_dim;i++)
	    {
	      fprintf(stderr,"%f\t",fft_first_s[0][i]);
	    }
	  fprintf(stderr,"\n\n");
	  for(i=0;i<squared_search_window_dim;i++)
	    {
	      fprintf(stderr,"%f\t",fft_first_s[1][i]);
	    }
	  fprintf(stderr,"\n\n");
	  for(i=0;i<squared_search_window_dim;i++)
	    {
	      fprintf(stderr,"%f\t",fft_second_s[0][i]);
	    }
	  fprintf(stderr,"\n\n");
	  for(i=0;i<squared_search_window_dim;i++)
	    {
	      fprintf(stderr,"%f\t",fft_second_s[1][i]);
	    }
	  fprintf(stderr,"\n\n");
#endif
	  /* fft of the 2 (complex) windows */
	  fft(-1,fft_first_s,squared_search_window_dim,search_window_dim,
	      search_window_dim);
	  fft(-1,fft_second_s,squared_search_window_dim,search_window_dim,
	      search_window_dim);
	
	  
#ifdef DEBUG
	  for(i=0;i<squared_search_window_dim;i++)
	    {
	      fprintf(stderr,"%f\t",fft_first_s[0][i]);
	    }
	  fprintf(stderr,"\n\n");
	  for(i=0;i<squared_search_window_dim;i++)
	    {
	      fprintf(stderr,"%f\t",fft_first_s[1][i]);
	    }
	  fprintf(stderr,"\n\n");
	  for(i=0;i<squared_search_window_dim;i++)
	    {
	      fprintf(stderr,"%f\t",fft_second_s[0][i]);
	    }
	  fprintf(stderr,"\n\n");
	  for(i=0;i<squared_search_window_dim;i++)
	    {
	      fprintf(stderr,"%f\t",fft_second_s[1][i]);
	    }
	  fprintf(stderr,"\n\n");
#endif
	  
	  /* product of the first fft for the coniugate of the second one */
	  for(i=0;i<squared_search_window_dim;i+=1)
	    {
	      fft_prod_con_s[0][i] = (fft_first_s[0][i] * fft_second_s[0][i]) +
		(fft_first_s[1][i] * fft_second_s[1][i]);
	      fft_prod_con_s[1][i] = (fft_first_s[1][i] * fft_second_s[0][i]) -
		(fft_first_s[0][i] * fft_second_s[1][i]);
	    }
	  
	  
#ifdef DEBUG
	  for(i=0;i<squared_search_window_dim;i++)
	    {
	      fprintf(stderr,"%f\t",fft_prod_con_s[0][i]);
	    }
	  fprintf(stderr,"\n\n");
	  for(i=0;i<squared_search_window_dim;i++)
	    {
	      fprintf(stderr,"%f\t",fft_prod_con_s[1][i]);
	    }
	  fprintf(stderr,"\n\n");
#endif
	  
	  /* fft^{-1} of the product <==> cross-correlation at differnet lag
	     between the two orig. (complex) windows */
	  fft(1,fft_prod_con_s,squared_search_window_dim,search_window_dim,
	      search_window_dim);
	  
#ifdef DEBUG
	  for(i=0;i<squared_search_window_dim;i++)
	    {
	      fprintf(stderr,"%f\t",fft_prod_con_s[0][i]);
	    }
	  fprintf(stderr,"\n\n");
	  for(i=0;i<squared_search_window_dim;i++)
	    {
	      fprintf(stderr,"%f\t",fft_prod_con_s[1][i]);
	    }
	  fprintf(stderr,"\n\n");
#endif
	  
	  /* Search the lag coresponding to the maximum correlation */
	  cc = 0.0;
	 
	  for(i=0;i<squared_search_window_dim;i++)
	    {
	      if(fft_prod_con_s[0][i] > cc)
		{
		  cc = fft_prod_con_s[0][i];
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


void Extract_portion_of_double_matrix_semi(int r,int c,int br,int bc,DCELL **mat,DCELL **wind)
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






















