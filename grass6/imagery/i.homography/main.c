/*
****************************************************************************
*
* MODULE:       i.pr.homolp
* AUTHOR(S):    2004, Daniel Grasso, Bolzano, Italy
*               based on code written by Stefano Merler, ITC-irst, Italy
*               http://gisws.media.osaka-cu.ac.jp/grass04/viewpaper.php?id=37
*
* PURPOSE:      rectifies an image by computing a coordinate transformation
*               for each pixel in the image based on the control points created by
*               i.linespoints. The approach uses homography extended for corresponding
*               lines.
*
* COPYRIGHT:    (C) 2004 by the GRASS Development Team
*
*               This program is free software under the GNU General Public
*   	    	License (>=v2). Read the file COPYING that comes with GRASS
*   	    	for details.
*
*****************************************************************************/
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <math.h>
#include <grass/gis.h>
#include <grass/gmath.h>
#include <grass/imagery.h>
#include <grass/gprojects.h>
#include "global.h"
#include "local_proto.h"

/* #define DEBUG 1 */

#define ITMAX 20000
#define CGOLD 0.3819660
#define ZEPS 1.0e-10

#define SIGN(a,b) ((b) > 0.0 ? fabs(a) : -fabs(a))
#define SHFT(a,b,c,d) (a)=(b); (b)=(c); (c)=(d);

void coords();
void show_env();
void select_target_env();
void select_current_env();
void proj();
void georef_window ();
void points_to_line (double e1, double n1, double e2, double n2, double *t, double *u);

static int which_env = -1;

static double offsetx /*= 1660000.0*/;
static double offsety/* = 5100000.0*/;

FILE *file_test;




int main(int argc, char *argv[])
{
  struct Option *opt1;
  struct Option *opt2;
  struct Option *opt3;
  struct Option *opt4;
  struct Option *opt5;
  char risp[100];
  char *input_name;
  char *output_name;
  char *output_location;
  char *output_mapset;
  char *input_group;
  char *data_location;
  int i,j,k;
  int permissions;
  char *setname;
  char tempbuf[1000];
  double PROJECTIVE[9];
  double I_PROJECTIVE[9];
  char *input_mapset;
  char *input_location;
  struct Cell_head input_cellhd;
  struct Cell_head output_cellhd;
  int outfd,infd;
  DCELL *output_cell;
  CELL *rowbuf;
  int **matrix;
  double e,n;
  int x,y;
  double translated_n;
  double translated_w;
  struct Control_Points cp;
  int r,c,rp;
  double **A;
  double *X,*Y;
  double newE,newN;
  double error;
  double t1, u1,t2,u2;
  double err_test_RMS=0;
  double x1,y1,x2,y2,homography_x2,homography_y2, diff_x2,diff_y2;
  double p_optimal;
  double parziale;
  int stampa=0;

  double estimate (double parameter) {

  j=0;
  for(i=0;i<cp.count;i++)
  {
    if(cp.status[i]==1){
      A[j][0]=cp.e1[i];
      A[j][1]=cp.n1[i];
      A[j][2]=1.0;
      A[j][3]=0.0;
      A[j][4]=0.0;
      A[j][5]=0.0;
      A[j][6]=-1.0*cp.e1[i]*cp.e2[i];
      A[j][7]=-1.0*cp.n1[i]*cp.e2[i];
      Y[j]=cp.e2[i];
      A[j+1][0]=0.0;
      A[j+1][1]=0.0;
      A[j+1][2]=0.0;
      A[j+1][3]=cp.e1[i];
      A[j+1][4]=cp.n1[i];
      A[j+1][5]=1.0;
      A[j+1][6]=-1.0*cp.e1[i]*cp.n2[i];
      A[j+1][7]=-1.0*cp.n1[i]*cp.n2[i];
      Y[j+1]=cp.n2[i];
      j += 2;
    }
    else if (cp.status[i]==2){

      points_to_line(cp.e1[i],cp.n1[i], cp.e1[i+1],cp.n1[i+1], &t1,&u1);
      points_to_line(cp.e2[i],cp.n2[i], cp.e2[i+1],cp.n2[i+1], &t2,&u2);
      t1=parameter*t1;
      u1=parameter*u1;
      t2=parameter*t2;
      u2=parameter*u2;

      A[j][0]=t2;
      A[j][1]=0.0;
      A[j][2]=-1.0*(t1)*(t2)/parameter;
      A[j][3]=u2;
      A[j][4]=0.0;
      A[j][5]=-1.0*(t1)*(u2)/parameter;
      A[j][6]=parameter;
      A[j][7]=0.0;
      Y[j]=t1;
      A[j+1][0]=0.0;
      A[j+1][1]=t2;
      A[j+1][2]=-1.0*(u1)*(t2)/parameter;
      A[j+1][3]=0.0;
      A[j+1][4]=u2;
      A[j+1][5]=-1.0*(u1)*(u2)/parameter;
      A[j+1][6]=0.0;
      A[j+1][7]=parameter;
      Y[j+1]=u1;
      j += 2;
      i++;
    }
  }

#ifdef DEBUG
 if(stampa){
  for(i=0;i<2*r;i++){
    for(j=0;j<8;j++)
      fprintf(stderr,"%e\t",A[i][j]);
    fprintf(stderr,"%e\n",Y[i]);
  }
 }
#endif

  linear_solve(A,Y,&X,2*r,c);

  PROJECTIVE[0] = X[0];
  PROJECTIVE[1] = X[3];
  PROJECTIVE[2] = X[6];
  PROJECTIVE[3] = X[1];
  PROJECTIVE[4] = X[4];
  PROJECTIVE[5] = X[7];
  PROJECTIVE[6] = X[2];
  PROJECTIVE[7] = X[5];
  PROJECTIVE[8] = 1.0;



 if(stampa){
  /*RESULTS TO STDOUT*/
  fprintf(stdout,"Homography:\n\nx' = (%ex + %ey + %e)/(%ex + %ey + 1)\n",
	  PROJECTIVE[0],
	  PROJECTIVE[3],PROJECTIVE[6],PROJECTIVE[2],PROJECTIVE[5]);
  fprintf(stdout,"y' = (%ex + %ey + %e)/(%ex + %ey + 1)\n", PROJECTIVE[1],
	  PROJECTIVE[4],PROJECTIVE[7],PROJECTIVE[2],PROJECTIVE[5]);
 }

   error = 0.0;
  rp = 0;
  for(i=0;i<cp.count;i++){
    if(cp.status[i] == 1){
      rp+= 1;
      proj(cp.e1[i],cp.n1[i],&newE,&newN,PROJECTIVE);
      error+=sqrt((newE-cp.e2[i])*(newE-cp.e2[i])+
		  (newN-cp.n2[i])*(newN-cp.n2[i]));
      }

  }
 
 if(stampa){
  fprintf(stdout,"\n parameter determined:%g \n", parameter);
   error =error /  rp;

  fprintf(stdout,"\n Mean squared Error = %f \n",error);
  return error;
 }

}


  /* Define the different options */
  G_gisinit(argv[0]);

  opt1              = G_define_option();
  opt1->key         = "input";
  opt1->type        = TYPE_STRING;
  opt1->required    = YES;
  opt1->gisprompt   = "old,cell,raster" ;
  opt1->description = "input raster map to be rectified";

  opt2              = G_define_option();
  opt2->key         = "output";
  opt2->type        = TYPE_STRING;
  opt2->required    = YES;
  opt2->gisprompt   = "new,cell,raster" ;
  opt2->description = "output raster map of the rectified map";

  opt3              = G_define_option();
  opt3->key         = "location";
  opt3->type        = TYPE_STRING;
  opt3->required    = YES;
  opt3->description = "location of the rectified raster map";

  opt4              = G_define_option();
  opt4->key         = "mapset";
  opt4->type        = TYPE_STRING;
  opt4->required    = YES;
  opt4->description = "mapset of the rectified raster map";

  opt5 = G_define_option() ;
  opt5->key        = "group";
  opt5->type       = TYPE_STRING;
  opt5->required   = YES;
  opt5->description= "input group containing points for homography computation";


  /***** Start of main *****/

  if (G_parser(argc, argv))
    exit(-1);

  input_name = opt1->answer;
  output_name = opt2->answer;
  output_location = opt3->answer;
  output_mapset = opt4->answer;
  input_group = opt5->answer;

  input_mapset=G_find_cell2 (input_name, "");
  setname = output_location ? output_mapset : G_store(G_mapset());
  input_location=G_location();
  data_location=G_gisdbase();

  /*sprintf(tempbuf,"cp %s/%s/%s/colr/%s %s/%s/%s/colr/%s",data_location,
	  input_location, input_mapset,input_name,data_location,
	  output_location,output_mapset,output_name);  */
  G_debug(3,"%s/%s/%s/cell/%s %s/%s/%s/cell/%s",data_location,
	  input_location, input_mapset,input_name,data_location,
	  output_location,output_mapset,output_name); 

  /* READ POINTS*/
  if(!I_find_group(input_group)){
    fprintf(stderr,"Group %s not in current mapset\n",input_group);
    exit(0);
  }

  I_get_control_points(input_group,&cp);

#ifdef DEBUG
  for(i=0;i<cp.count;i++){
    fprintf(stderr,"%f %f %f %f %d\n",cp.e1[i],cp.n1[i],cp.e2[i],cp.n2[i],
	    cp.status[i]);
  }
#endif


 fprintf(stdout,"\nExecute the quality test (requires file 'TEST_SET')?\n y --> yes, everything else --> no \n");
 scanf("%1c",risp);

 if (risp[0] == 'y')
   {
     file_test=fopen ("TEST_SET","r");
     if(file_test==NULL) G_fatal_error("File 'TEST_SET' not found.");
    }
 while (risp[0]!='\n') scanf("%1c",risp);



  /*COMPUTE PROJECTIVE PARAMETERS*/

  if (cp.count == 0)
     exit(-1);

/*offsetx = cp.e2[0] - 10000;
 offsety = cp.n2[0] - 10000;*/

  i=0;
  while(cp.status[i]!=1 && i < cp.count)
        i++;
  if(i >=cp.count && cp.status[i]!=1)
        i=0;
  offsetx = cp.e2[i] - cp.e1[i];
  offsety = cp.n2[i] - cp.n1[i];

  r=0;
  for(i=0;i<cp.count;i++){
    if(cp.status[i]==1){
      r += 1;
      cp.e2[i] -= offsetx;
      cp.n2[i] -= offsety;

      /*printf( " \n  i points after offset est %f e  nord %f  \n", cp.e2[i], cp.n2[i]);*/

    }
    else if (cp.status[i]==2){
            r+=1;
            cp.e2[i] -= offsetx;
            cp.n2[i] -= offsety;
            cp.e2[i+1] -= offsetx;
            cp.n2[i+1] -= offsety;

           /* printf( " \n points of lines after offset est[i=1]= %f,  nord[i=1]= %f, est[i=2] =%f, nord[i=2]= %f  \n", cp.e2[i], cp.n2[i], cp.e2[i+1], cp.n2[i+1]);*/
           }
    }

  c=8;
  A=(double**)G_calloc(2*r,sizeof(double*));
  for(i=0;i<2*r;i++)
    A[i]=(double*)G_calloc(c,sizeof(double));

  Y=(double*)G_calloc(2*r,sizeof(double));

  p_optimal = brent_iterate ( estimate, 1.0e3, 1.0e10, ITMAX); 

  stampa =1;
  
  estimate (p_optimal);

   fprintf(stdout,"\n Mean squared Error = %f \n",error);
  /*fprintf(stdout,"\n number of used points = %i \n",rp);*/


   rp=0;
   if (file_test!=NULL) {
  while(fgets(risp,100,file_test)!=NULL)
  {
    rp+=1;
    x1=atof(strtok(risp," "));
    y1=atof(strtok(NULL," "));
    x2=atof(strtok(NULL," "));
    y2=atof(strtok(NULL," "));
    homography_x2 = ((PROJECTIVE[0]*x1 + PROJECTIVE[3] * y1 +  PROJECTIVE[6]) / (PROJECTIVE[2]*x1 + PROJECTIVE[5] * y1 + 1));
    homography_y2 = ((PROJECTIVE[1]*x1 + PROJECTIVE[4] * y1 +  PROJECTIVE[7]) / (PROJECTIVE[2]*x1 + PROJECTIVE[5] * y1 + 1));
    fprintf(stdout," x2=%f     y2=%f     o_x2=%f     o_y2=%f\n",x2,y2, homography_x2+offsetx,homography_y2+offsety);
    diff_x2 = x2 -  homography_x2 - offsetx;
    diff_y2 = y2 -  homography_y2 - offsety;
    err_test_RMS+=((diff_x2)*(diff_x2))+((diff_y2)*(diff_y2));
    }
  err_test_RMS=sqrt(err_test_RMS)/rp;
  fprintf(stdout, "test error= %f \n", err_test_RMS);
   }


  /*COMPUTE INVERSE PARAMETERS*/
  I_PROJECTIVE[2]=PROJECTIVE[1]*PROJECTIVE[5] - PROJECTIVE[2]*PROJECTIVE[4];
  I_PROJECTIVE[5]=PROJECTIVE[2]*PROJECTIVE[3] - PROJECTIVE[0]*PROJECTIVE[5];
  I_PROJECTIVE[8]=PROJECTIVE[0]*PROJECTIVE[4] - PROJECTIVE[1]*PROJECTIVE[3];
  I_PROJECTIVE[0]=PROJECTIVE[4]- PROJECTIVE[5]*PROJECTIVE[7];
  I_PROJECTIVE[3]=PROJECTIVE[5]*PROJECTIVE[6]-PROJECTIVE[3];
  I_PROJECTIVE[6]=PROJECTIVE[3]*PROJECTIVE[7] - PROJECTIVE[4]*PROJECTIVE[6];
  I_PROJECTIVE[1]=PROJECTIVE[2]*PROJECTIVE[7]-PROJECTIVE[1];
  I_PROJECTIVE[4]=PROJECTIVE[0]- PROJECTIVE[2]*PROJECTIVE[6];
  I_PROJECTIVE[7]=PROJECTIVE[1]*PROJECTIVE[6] - PROJECTIVE[0]*PROJECTIVE[7];


  /* READ INPUT MAP HEADER FILE,READ MAP TO BE TRANSFORMED
     AND COMPUTE OUTPUT REGION*/
  if (G_get_cellhd (input_name, input_mapset, &input_cellhd) < 0)
        exit(-1);

  G_set_window(&input_cellhd);
  matrix=(int **)calloc(input_cellhd.rows,sizeof(int*));
  for(i=0;i<input_cellhd.rows;i++)
    matrix[i] = (int *)calloc(input_cellhd.cols,sizeof(int));
  infd = G_open_cell_old(input_name, input_mapset);
  rowbuf = G_allocate_cell_buf();
  for(j = 0; j < input_cellhd.rows; j++){
    if(G_get_map_row(infd, rowbuf, j) == -1){
      sprintf(tempbuf,"error reading raster map [%s]", input_name);
      G_fatal_error(tempbuf);
    }
    for(k = 0; k < input_cellhd.cols; k++){
      matrix[j][k] =rowbuf[k];
    }

  }
  G_close_cell(infd);
  free(rowbuf);

  /* check if target location exists etc */
  G__setenv ("LOCATION_NAME", output_location);
  G__setenv ("MAPSET", output_mapset);
  permissions = G__mapset_permissions(setname);
  if (permissions < 0)    /* can't access mapset   */
     G_fatal_error("Mapset [%s] in output location [%s] - %s\n",
       setname, output_location,
       permissions == 0
       ? "permission denied"
       : "not found");

  /****** get the output projection/zone parameters ******/
  select_target_env();
  G__get_window (&output_cellhd,"","WIND","PERMANENT");

  georef_window (&input_cellhd, &output_cellhd, PROJECTIVE);

  if(G_put_window (&output_cellhd)>=0)
    fprintf (stdout,"Computing...\n");

  /*OPEN RASTER FILE IN THE TARGET LOCATION*/
  G_get_window (&output_cellhd);
  G_set_window (&output_cellhd);
  outfd = open_new_DCELL(output_name);
  if (outfd < 0)
    return 0;
  output_cell=G_allocate_d_raster_buf();


  /*COMPUTE RECTIFICATION*/
  translated_n = output_cellhd.north - offsety;
  translated_w = output_cellhd.west - offsetx;
  for(i=0;i<output_cellhd.rows;i++){
    G_zero_raster_buf(output_cell, DCELL_TYPE); /* better NULL ?! */
    for(j=0;j<output_cellhd.cols;j++){
      proj(translated_w + (j+0.5)*output_cellhd.ew_res,
	   translated_n - (i+0.5)*output_cellhd.ns_res,
	   &e,&n,I_PROJECTIVE);
      coords(e,n,&x,&y,&input_cellhd);
      if((x>=0)&&(x<input_cellhd.rows)&&(y>=0)&&(y<input_cellhd.cols))
	output_cell[j]=matrix[x][y];
    }
    G_percent(i,output_cellhd.rows, 5);
    G_put_d_raster_row(outfd,output_cell);
  }
  G_close_cell(outfd);

  system(tempbuf);

  return 0;
}

/*PROJECTIVE TRANSFORMATION OF A POINT*/
void proj(e1,n1,e,n,param)
double e1;  /* EASTINGS TO BE TRANSFORMED */
double n1;  /* NORTHINGS TO BE TRANSFORMED */
double *e;  /* EASTINGS TO BE TRANSFORMED */
double *n;  /* NORTHINGS TO BE TRANSFORMED */
double param[]; /* (Inverse) PROJECTIVE COEFFICIENTS */
{
  double tmp;
  tmp = param[2] * e1 +  param[5]* n1 + param[8];
  *e = (param[6] + param[0] * e1 + param[3] * n1)/tmp;
  *n = (param[7] + param[1] * e1 + param[4] * n1)/tmp;
}

/*PROJECTIVE TRANSFORMATION OF A WINDOW (THE CORNERS OF A)*/
void georef_window (w1, w2, param)
    struct Cell_head *w1, *w2;
    double param[];

{
    double n,e;

    proj (w1->west, w1->north, &e, &n, param);
    n += offsety;
    e += offsetx;
    w2->north = w2->south = n;
    w2->west  = w2->east  = e;

    proj (w1->east, w1->north, &e, &n, param);
    n += offsety;
    e += offsetx;
    if (n > w2->north) w2->north = n;
    if (n < w2->south) w2->south = n;
    if (e > w2->east ) w2->east  = e;
    if (e < w2->west ) w2->west  = e;

    proj (w1->west, w1->south, &e, &n, param);
    n += offsety;
    e += offsetx;
    if (n > w2->north) w2->north = n;
    if (n < w2->south) w2->south = n;
    if (e > w2->east ) w2->east  = e;
    if (e < w2->west ) w2->west  = e;

    proj (w1->east, w1->south, &e, &n, param);
    n += offsety;
    e += offsetx;
    if (n > w2->north) w2->north = n;
    if (n < w2->south) w2->south = n;
    if (e > w2->east ) w2->east  = e;
    if (e < w2->west ) w2->west  = e;

    w2->ns_res = (w2->north - w2->south) / w1->rows;
    w2->ew_res = (w2->east  - w2->west ) / w1->cols;
    w2->cols=w1->cols;
    w2->rows=w1->rows;
}

/*SELECT CURRENT ENV*/
void select_current_env()
{
    if (which_env < 0)
    {
        G__create_alt_env();
        which_env = 0;
    }
    if (which_env != 0)
    {
        G__switch_env();
        which_env = 0;
    }
}

/*SELECT TARGET ENV*/
void select_target_env()
{
    if (which_env < 0)
    {
        G__create_alt_env();
        which_env = 1;
    }
    if (which_env != 1)
    {
        G__switch_env();
        which_env = 1;
    }
}
/*PRINT ENV*/
void show_env()
{
  fprintf (stdout,"env(%d) switch to LOCATION %s, MAPSET %s\n", which_env,
	  G__getenv("LOCATION_NAME")==NULL ? "?" : G__getenv("LOCATION_NAME"),
	  G__getenv("MAPSET")==NULL ? "?" : G__getenv("MAPSET"));
  sleep(2);
}

void coords(e,n,x,y,win)
     double e,n;
     int *x,*y;
     struct Cell_head *win;
{
  *y=(int)(e - win->west) / win->ew_res;
  *x=(int)(win->north - n) / win->ns_res;
}

void points_to_line (double e1, double n1, double e2, double n2, double *t, double *u)
{
        double a,b,c;
        a=(n1 - n2);
        b= (e2 - e1);
        c= (n2*e1 - n1*e2);
        *t= a/c;
        *u=b/c;
   /* printf( " \n a %f  b %f  c %f  t %f  u %f  \n\n",a,b,c,*t,*u);  */
}
