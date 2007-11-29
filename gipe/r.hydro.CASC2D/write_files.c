#include "all.h"

/*!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!*/
 void WRITE_FILES (
/*!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!*/
    char buf[256],
    int windex,
    int itime,
    double dt,
    int num_w,
    int yes_w_surf_dep,
    int *depth_fd,
    char *depth_file[2000],
    int yes_w_inf_dep,
    int *inf_fd,
    char *inf_dep_file[2000],
    int yes_w_surf_moist,
    int *surf_moist_fd,
    char *surf_moist_file[2000],
    int yes_w_inf_rate,
    int *inf_rate_fd,
    char *inf_rate_file[2000],
    int yes_w_dis_rain,
    int rindex,
    int *dis_rain_fd,
    char *dis_rain_file[2000],
    float *h,
    int yes_channel,
    int yes_priess,
    int *ltype,
    int *nx1,
    int *chn_row,
    int *chn_col,
    float *hch,
    float *yp,
    float *bel,
    CELL *depth_tmp,
    CELL *inf_tmp,
    CELL *surf_moist_tmp,
    CELL *inf_rate_tmp,
    CELL *dis_rain_tmp,
    int nitrn,
    float *vinf,
    float *surf_moist,
    float *frate,
    float *rint,
    int **space,
    int yes_lake,
    float *elev,
    struct Colors *colors
)

/*  struct Categories *cats; */
/* char  *title;   */

{

int   nf,j,k,vectmp;
int   dmin,dmax,data1,data2;
float surf_dep;
char  *maps;

fprintf(stderr, " writing raster files for iteration %d\n",itime-1);
nf=(itime-1)/num_w;
if(windex==2) nf=nf+1;

if(yes_w_surf_dep) 
{
if((depth_fd[nf]=G_open_cell_new(depth_file[nf]))<0) 
{
    sprintf(buf,"cannot open [%s]\n",depth_file[nf]);
    G_fatal_error(buf);
    exit(1);
}

/*
 *else
 *{
 *  sprintf(title=buf,"r.hydro.CASC2D: surface depth map in mm at time=%f sec"
 *	   ,(itime-1)*dt); 
 *}
 */

}

if(yes_w_inf_dep) 
{
if((inf_fd[nf]=G_open_cell_new(inf_dep_file[nf]))<0) 
{
    sprintf(buf,"cannot open [%s]\n",inf_dep_file[nf]);
    G_fatal_error(buf);
    exit(1);
}
}

if(yes_w_surf_moist) 
{
if((surf_moist_fd[nf]=G_open_cell_new(surf_moist_file[nf]))<0) 
{
    sprintf(buf,"cannot open [%s]\n",surf_moist_file[nf]);
    G_fatal_error(buf);
    exit(1);
    }
}

if(yes_w_inf_rate) 
{
if((inf_rate_fd[nf]=G_open_cell_new(inf_rate_file[nf]))<0) 
{
    sprintf(buf,"cannot open [%s]\n",inf_rate_file[nf]);
    G_fatal_error(buf);
    exit(1);
}
}

if(yes_w_dis_rain && rindex==1) 
{
if((dis_rain_fd[nf]=G_open_cell_new(dis_rain_file[nf]))<0) 
{
    sprintf(buf,"cannot open [%s]\n",dis_rain_file[nf]);
    G_fatal_error(buf);
    exit(1);
    }
}

dmin=0;
dmax=1000;
for(j=0; j<nrows; j++)
{
   for(k=0; k<ncols; k++)
   {
       vectmp=space[j][k];
       if(vectmp==0)
       {
	  if(yes_w_surf_dep) depth_tmp[k]=0;
	  if(yes_w_inf_dep) inf_tmp[k]=0;
	  if(yes_w_surf_moist) surf_moist_tmp[k]=0;
	  if(yes_w_inf_rate) inf_rate_tmp[k]=0;
          if(yes_w_dis_rain) dis_rain_tmp[k]=0;
       }
       else
       {
          if(yes_w_surf_dep) 
          {
             surf_dep=h[vectmp];
	     if(yes_lake && lake_cat[vectmp] !=0) 
	     {
	        surf_dep=lake_el[lake_cat[vectmp]]-elev[vectmp];
             }
	     else
	     {
                if(yes_channel || yes_priess) 
	        {
	           if(con_link[vectmp]==0) goto OUT;
	           if(ltype[con_link[vectmp]]==4) continue;   
					       /* The lake depth will be
					        * taken care of separately. */
                   if(yes_channel)
	           {
	              surf_dep=hch[con_node[vectmp]+con_link[vectmp]*NODES];
                   }
	           else
	           {
	              surf_dep=yp[con_node[vectmp]+con_link[vectmp]*NODES]-
			 bel[con_node[vectmp]+con_link[vectmp]*NODES];
                   }   
                }
             }

OUT:
             depth_tmp[k]=1000*surf_dep; 
				/* Surface depth in mm */
             if(depth_tmp[k]>dmax) dmax=depth_tmp[k];
             
          }

          if(yes_w_inf_dep) inf_tmp[k]=10000*vinf[vectmp];
				/* Infiltration depth in tenth of mm */

          if(yes_w_surf_moist) surf_moist_tmp[k]=1000*surf_moist[vectmp];

          if(yes_w_inf_rate) inf_rate_tmp[k]=1000*3600*frate[vectmp]; 
				/* Infiltration rate in  mm/hr */

          if(yes_w_dis_rain && itime < nitrn) dis_rain_tmp[k]=
					   1000*3600*rint[vectmp];
				         /* Rainfall intensity in mm/hr */
          if(yes_w_dis_rain && itime >= nitrn) dis_rain_tmp[k]=0;
      }
   }

   if(yes_w_surf_dep) G_put_raster_row(depth_fd[nf], depth_tmp, CELL_TYPE);
   if(yes_w_inf_dep)  G_put_raster_row(inf_fd[nf], inf_tmp, CELL_TYPE);
   if(yes_w_surf_moist)  G_put_raster_row(surf_moist_fd[nf], surf_moist_tmp, CELL_TYPE);
   if(yes_w_inf_rate)  G_put_raster_row(inf_rate_fd[nf], inf_rate_tmp, CELL_TYPE);
   if(yes_w_dis_rain && rindex==1) G_put_raster_row(dis_rain_fd[nf], dis_rain_tmp, CELL_TYPE);

}

if(yes_w_surf_dep) G_close_cell(depth_fd[nf]);
if(yes_w_inf_dep) G_close_cell(inf_fd[nf]);
if(yes_w_surf_moist) G_close_cell(surf_moist_fd[nf]);
if(yes_w_inf_rate) G_close_cell(inf_rate_fd[nf]);
if(yes_w_dis_rain && rindex==1) G_close_cell(dis_rain_fd[nf]);

G_init_colors (colors);
if(yes_w_surf_dep)
{
    if(depth_file[nf] != NULL)
    {
    maps = G_find_cell(depth_file[nf],"");
    if(maps==NULL)
    {
       sprintf(buf,"file [%s] not found", depth_file[nf]);
       G_fatal_error(buf);
    }
    data1 = dmin;
    data2 = dmax;
    G_add_color_rule (    0, 255, 255, 255,      5, 255, 255,   0, colors);
    G_add_color_rule (    5, 255, 255,   0,     30,   0, 255, 255, colors);
    G_add_color_rule (   30,   0, 255, 255,    100,   0, 127, 255, colors);
    G_add_color_rule (  100,   0, 127, 255,   1000,   0,   0, 255, colors);
    G_add_color_rule ( 1000,   0,   0, 255,  data2, 255,   0,   0, colors);
    G_write_colors (depth_file[nf],maps,colors);
    
    }
}

return;
}

