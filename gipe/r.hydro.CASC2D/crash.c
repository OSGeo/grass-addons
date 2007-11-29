#include "all.h"

/*!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!*/
void CRASH(
FILE    *discharge_fd,int coindex,int vect,
int     link,int node, int itime, int **space,double  dt,
struct  Cell_head window, float *Inter,float *h,float *vinf,
int     yes_intercep,int yes_inf,
double *vintercep,double *vsur2,int yes_lake,
double *vlake2, float *elev,double *vinftot)
/*!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!*/

{

int     j,k;
double  dj,dk,east,north;

for(j=0; j<nrows; j++)
{
   for(k=0; k<ncols; k++)
   {
       if(space[j][k] != vect) continue;
       dj=(double)j+0.5;
       dk=(double)k+0.5;
       east=G_col_to_easting(dk,&window);
       north=G_row_to_northing(dj,&window);

       if(coindex==1)
       {
          fprintf(discharge_fd, "program crashed due to oscillations resulting in negative depth at overland cell: \n row= %d \n col= %d \n northing= %f \n easting= %f \n time= %7.1f  (min).\n Time step must be reduced or the surface slopes in the neighborhood of above location be smoothed.\n",j,k,north,east,(float)itime*dt/60.);

          fprintf(stderr, "program crashed due to oscillations resulting in negative depth at overland cell: \n row= %d \n col= %d \n northing= %f \n easting= %f \n time= %7.1f  (min).\n Time step must be reduced or the surface slopes in the neighborhood of above location be smoothed.\n",j,k,north,east,(float)itime*dt/60.);
       }
       else
       {
          fprintf(discharge_fd, "program crashed due to oscillations resulting in negative channel depth at link= %d \n node= %d \n which is embedded in cell: \n row= %d \n col= %d \n northing= %f \n easting= %f \n time= %7.1f  (min).\n Time step must be reduced or the surface slopes in the neighborhood of above location be smoothed.\n",link,node,j,k,north,east,(float)itime*dt/60.);

          fprintf(stderr, "program crashed due to oscillations resulting in negative channel depth at link= %d \n node= %d \n which is embedded in cell: \n row= %d \n col= %d \n northing= %f \n easting= %f \n time= %7.1f  (min).\n Time step must be reduced or the surface slopes in the neighborhood of above location be smoothed.\n",link,node,j,k,north,east,(float)itime*dt/60.);
       }
    }
}

for(j=1; j<=GNUM; j++)
{
   if(yes_intercep) (*vintercep)=(*vintercep)+Inter[j]*w*w;
   if(yes_inf) (*vinftot)=(*vinftot)+vinf[j]*w*w;
   if(yes_lake)
   {
     if(lake_cat[j]!=0) 
     {
	(*vlake2)=(*vlake2)+(lake_el[lake_cat[j]]-(double)elev[j])*w*w;
     }
     else
     {
	(*vsur2)=(*vsur2)+h[j]*w*w;
     }
   }
   else
   {
      (*vsur2)=(*vsur2)+h[j]*w*w;
   }

}

return;
}
