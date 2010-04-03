
#include "all.h"

/*!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!*/
void 
OV_LAKE (
/*!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!*/
    double rman,
    int vect,
    int vect2,
    double dmin,
    int yes_dist_rough,
    float *elev,
    float *rough,
    float *h,
    float *dqov
)

{
double  hh,dqq,mann = 0.0L;
double  sf,alfaov;
double  base,power;

if(lake_cat[vect] == 0) {
   sf=(elev[vect]+h[vect]-lake_el[lake_cat[vect2]])/w;
}
else {
   sf=(lake_el[lake_cat[vect]]-elev[vect2]-h[vect2])/w;
}
if(abs(sf)<1e-20) return;

if(!yes_dist_rough) mann=rman;
if(lake_cat[vect] == 0) 
{
   if(sf>0) 
   {
      hh=h[vect];
      if(hh<dmin) return;
      if(yes_dist_rough) mann=(double)rough[vect];
      alfaov=sqrt(abs(sf))/mann;
      dqq=sign(sf)*w*alfaov*pow((base=hh),(power=1.667));
   }
   else 
   {
      /* hh is the lake depth in excess of overland cell's elevation.  */
      hh=lake_el[lake_cat[vect2]] - elev[vect];
      if(h[vect]>=(2.*hh/3.))
      {
	 dqq=sign(sf)*w*sqrt((double)(2.*9.81))*
	     sqrt((double)(hh-h[vect]))*h[vect];
      }
      else
      {
	 dqq=sign(sf)*w*(2./3.)*sqrt((double)(2.*9.81/3.))*
	     pow((double)hh,(double)1.5);
      }
   }

/* To force dqq < current flow: cho
   if(dqq > 0 && dqov[vect] < dqq)
	dqq = dqov[vect];

   if(dqq < 0 && qtolake[lake_cat[vect2]] < abs(dqq))
	dqq = - qtolake[lake_cat[vect2]];
*/

   dqov[vect]=dqov[vect]-dqq;
   qtolake[lake_cat[vect2]]= qtolake[lake_cat[vect2]]+dqq;
}

if(lake_cat[vect] != 0) 
{
   if(sf>0) 
   {
      hh=lake_el[lake_cat[vect]] - elev[vect2];
      if(h[vect2]>=(2.*hh/3.))
      {
	 dqq=sign(sf)*w*sqrt((double)(2.*9.81))*
             sqrt((double)(hh-h[vect2]))*h[vect2];
      } 
      else
      {
	 dqq=sign(sf)*w*(2./3.)*sqrt((double)(2.*9.81/3.))*
	     pow((double)hh,(double)1.5);
      }
   }
   else 
   {
      hh=h[vect2];
      if(hh<dmin) return;
      if(yes_dist_rough) mann=(double)rough[vect2];
      alfaov=sqrt(abs(sf))/mann;
      dqq=sign(sf)*w*alfaov*pow((base=hh),(power=1.667));
   }
   dqov[vect2]=dqov[vect2]+dqq;
   qtolake[lake_cat[vect]]= qtolake[lake_cat[vect]]-dqq;
}
   
}
