#include "all.h"

/**************************************************************/
void 
dsqoy (

/*
 *    THIS SUBROUTINE CALCULATES THE DOWNSTREAM Q(Y) B.C.
 *
 */
    float *bottom,
    float *sslope,
    float *sslope2,
    float *strick,
    double delx,
    float *yp,
    float *bel,
    int *nx1,
    float *dsdisch,
    int *ltype,
    float *chn_dep,
    float *mk0,
    float *pk0,
    float *mk1,
    float *pk1,
    float *xk,
    int *numhts,
    float *ht_spc,
    int *table_num,
    int NUMBPTS
)

{
   int nl,endaddr;
   float dslope,depth1,area,per,rhydr;
   float yabf,convey,ocdep;
   int tnum,interv,last;
   float conv,slope,ck;

   nl=nlinks;
   endaddr=nx1[nl]+nl*NODES;
   dslope=(bel[nx1[nl]+nl*NODES-1]-bel[nx1[nl]+nl*NODES])/delx;
   depth1=yp[endaddr]-bel[endaddr];
   if(ltype[nl]==1)
      {
      /* do trapezoidal calculations */
      area=bottom[endaddr]*depth1+sslope[endaddr]*depth1*depth1;
      per=bottom[endaddr]+2.0*depth1*sqrt(1.0+sslope[endaddr]*
          sslope[endaddr]);
      rhydr=area/per;
      *dsdisch=sqrt(dslope)*strick[endaddr]*area*pow((double)rhydr,(double)2./3.);
      } 
   if(ltype[nl]==5)
      {
      /* do APFA type II calculations */
      *dsdisch=sqrt(dslope)*mk0[endaddr]*
                                   pow((double)depth1,(double)pk0[endaddr]);
      }
    if(ltype[nl]==6)
      {
      /* do APFA type III calculations */
      ocdep=chn_dep[endaddr];
      if(depth1>ocdep)
         {
         yabf=depth1-ocdep;
         convey=mk0[endaddr]*pow((double)ocdep,(double)pk0[endaddr])+
                mk1[endaddr]*pow((double)yabf,(double)pk1[endaddr]);
         *dsdisch=sqrt(dslope)*convey;
         }
      else
         {
         convey=mk0[endaddr]*pow((double)depth1,(double)pk0[endaddr]);
         *dsdisch=sqrt(dslope)*convey;
         }
      }
    if(ltype[nl]==8)
      {
      /* do breakpoint x-sect calculations */
      tnum=table_num[endaddr];
      interv=(int)(depth1/ht_spc[tnum]);
      if(interv>=numhts[tnum])
        {
        /* OUTSIDE DATA RANGE, SO EXTRAPOLATE (SHOULD WARN USER TOO!) */
        last=numhts[tnum];
        slope=(xk[last+tnum*NUMBPTS]-xk[last+tnum*NUMBPTS-1])/ht_spc[tnum];
        conv=xk[last+tnum*NUMBPTS]+(depth1-(float)last*ht_spc[tnum])*slope;
        }
      else  
        {
        /* INSIDE DATA RANGE, SO INTERPOLATE */
        if(interv!=0)
          {
          /* This depth is not in the first interval */
          conv=xk[interv+1+tnum*NUMBPTS]-xk[interv+tnum*NUMBPTS];
          conv=xk[interv+tnum*NUMBPTS]+(conv/ht_spc[tnum]*
               (depth1-(float)interv*ht_spc[tnum]));
          }
        else
          {
          /* This depth is in the first interval, use 5/3 pwr interp. */
          ck=xk[1+tnum*NUMBPTS]/pow(ht_spc[tnum],(5.0/3.0));
          conv=ck*pow(depth1,5.0/3.0);
          }
        }
      *dsdisch=conv*sqrt(dslope);
      }
    if(ltype[nl]==9)
      {
      /* do multiple side slope calculations */
      ocdep=chn_dep[endaddr];
      if(depth1>ocdep)
         {
         yabf=depth1-ocdep;
	 area=ocdep*(bottom[endaddr]+ocdep*sslope[endaddr])+
	      0.5*yabf*(bottom[endaddr]+2.0*ocdep*sslope[endaddr]+
	      bottom[endaddr]+2.0*ocdep*sslope[endaddr]+2.0*sslope2[endaddr]*yabf);
         per=bottom[endaddr]+2.0*ocdep*sqrt((double)(1.0+sslope[endaddr]*
	     sslope[endaddr]))+2.*yabf*sqrt((double)(1.0+sslope2[endaddr]*
	     sslope2[endaddr]));
         rhydr=area/per;
         *dsdisch=sqrt(dslope)*strick[endaddr]*area*pow((double)rhydr,(double)2./3.);
         }
      else
         {
         area=depth1*(bottom[endaddr]+depth1*sslope[endaddr]);
         per=bottom[endaddr]+2.0*depth1*sqrt(1.0+sslope[endaddr]*
             sslope[endaddr]);
         rhydr=area/per;
         *dsdisch=sqrt(dslope)*strick[endaddr]*area*pow((double)rhydr,(double)2./3.);
         }
      }
   return;
}
