#include "all.h"

/*!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!*/
void 
OV_FLOW (
/*!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!*/
    double dt,
    double rman,
    int row,
    int col,
    int vect,
    int vect2,
    double dmin,
    int vectout,
    int yes_dist_rough,
    int yes_flow_out,
    int set_flow_out_basin,
    float *elev,
    float *rough,
    float *h,
    float *dqov,
    int **space,
    double *vout_region
)

{
double  hh,dqq,mann = 0.0L;
double  dhdx,s0,sf,alfaov;
double  sqrt(),pow(),base,power;

s0=(elev[vect]-elev[vect2])/w;
dhdx=(h[vect2]-h[vect])/w;
sf=s0-dhdx;
if(abs(sf)<1e-20) return;

if(!yes_dist_rough) mann=rman;
hh=h[vect];
if(yes_dist_rough) mann=(double)rough[vect];
if(sf<0) {
   hh=h[vect2];
   if(yes_dist_rough) mann=(double)rough[vect2];
}

if(hh<dmin) return;            /* for very small depth do not route  */

alfaov=sqrt(abs(sf))/mann;

dqq=sign(sf)*w*alfaov*pow((base=hh),(power=1.667));

/* To force dqq < current flow: cho
if(dqq > 0 && dqov[vect] < dqq)
	dqq = dqov[vect];

if(dqq < 0 && dqov[vect2] < abs(dqq))
	dqq = - dqov[vect2];
*/

dqov[vect]=dqov[vect]-dqq;
dqov[vect2]=dqov[vect2]+dqq;

dqq=0;
if(yes_flow_out && set_flow_out_basin!=0) {
   if(vect2==vectout) return;
   if( set_flow_out_basin==1 && sf<0) {
	 hh=h[vect];
         if(yes_dist_rough) mann=rough[vect]; 
         dqq=sqrt(abs(sf))*w*pow((base=hh),(power=1.667))/mann;
	 dqov[vect]=dqov[vect]-dqq;
	 }
   if( set_flow_out_basin==2 && sf>0) {
	 hh=h[space[row][col+1]];
         if(yes_dist_rough) mann=rough[space[row][col+1]]; 
         dqq=sqrt(abs(sf))*w*pow((base=hh),(power=1.667))/mann;
	 dqov[space[row][col+1]]=dqov[space[row][col+1]]-dqq;
         }

   if( set_flow_out_basin==3 && sf<0) {
	 hh=h[vect];
         if(yes_dist_rough) mann=rough[vect]; 
         dqq=sqrt(abs(sf))*w*pow((base=hh),(power=1.667))/mann;
	 dqov[vect]=dqov[vect]-dqq;
         }
   if( set_flow_out_basin==4 && sf>0) {
	 hh=h[space[row+1][col]];
         if(yes_dist_rough) mann=rough[space[row+1][col]]/100.;   
         dqq=sqrt(abs(sf))*w*pow((base=hh),(power=1.667))/mann;
	 dqov[space[row+1][col]]=dqov[space[row+1][col]]-dqq;
         }

(*vout_region)=(*vout_region)+dqq*dt;
}
   
}
