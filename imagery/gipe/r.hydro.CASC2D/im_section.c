#include "all.h"

/*******************************************************************/
 void 
section (

/*
 *    THIS SUB CALCULATES AREA, CONVEYANCE,AND WIDTH OF
 *    FLUVIAL REACH.
 */
    float *bottom,
    float *sslope,
    float *sslope2,
    float *strick,
    float *yp,
    float *bel,
    float *areap,
    float *rkp,
    float *rpk,
    float *width,
    int *nx1,
    int *ltype,
    float *chn_dep,
    float *marea0,
    float *parea0,
    float *mtw0,
    float *ptw0,
    float *mk0,
    float *pk0,
    float *marea1,
    float *parea1,
    float *mtw1,
    float *ptw1,
    float *mk1,
    float *pk1,
    float *xarea,
    float *xtw,
    float *xk,
    int *numhts,
    float *ht_spc,
    int maxtab,
    int *table_num,
    int NUMBPTS
)

{
  /* FRED: check local variables  */

  int  i,j,addr,taddr,tnum;
  float r,perim,ydep,yabf,ocdep;
  float depc,ca,ct,ck,depn,xdy;
  int maxbp,ldex,hdex;

  for(j=1;j<=nlinks;j++)
     {
     if(ltype[j]==1) /* only do the fluvial reaches */
        {
	/* do trapezoidal calculations */
        for(i=1;i<=nx1[j];i++)
           {
           ydep=yp[i+j*NODES]-bel[i+j*NODES];
           width[i+j*NODES]=bottom[i+j*NODES]+2.0*ydep*sslope[i+j*NODES];
           perim=bottom[i+j*NODES]+2.0*ydep*
              sqrt((double)(1.0+sslope[i+j*NODES]*sslope[i+j*NODES]));
              areap[i+j*NODES]=ydep*(bottom[i+j*NODES]+ydep*sslope[i+j*NODES]);
           r=areap[i+j*NODES]/perim;
           rpk[i+j*NODES]=strick[i+j*NODES]*(1.66667*(bottom[i+j*NODES]+
              2.0*sslope[i+j*NODES]*ydep)*
              pow((double)r,(double)0.6666667)-
              1.33333*sqrt(1+sslope[i+j*NODES]*sslope[i+j*NODES])*
              pow((double)r,(double)1.6666667));
           rkp[i+j*NODES]=strick[i+j*NODES]*pow((double)areap[i+j*NODES],
              (double)1.666667)/pow((double)perim,(double)0.666667);
           }
        } 
     else
	{
	if(ltype[j]==5)
	   {
	   /* do APFA type II calculations */
	   for(i=1;i<=nx1[j];i++)
	      {
	      addr=i+j*NODES;
	      ydep=yp[addr]-bel[addr];
	      width[addr]=mtw0[addr]*pow((double)ydep,(double)ptw0[addr]);
	      areap[addr]=marea0[addr]*pow((double)ydep,(double)parea0[addr]);
	      rkp[addr]=mk0[addr]*pow((double)ydep,(double)pk0[addr]);
	      rpk[addr]=pk0[addr]*mk0[addr]*
                                    pow((double)ydep,(double)(pk0[addr]-1.0));
	      }
           }
        else if (ltype[j]==6)
           {
           /* do APFA type III calculations */
	   for(i=1;i<=nx1[j];i++)
	      {
	      addr=i+j*NODES;
	      ydep=yp[addr]-bel[addr];
              ocdep=chn_dep[addr];
              if(ydep>ocdep)
                {
                yabf=ydep-ocdep;
	         width[addr]=mtw0[addr]*pow((double)ocdep,(double)ptw0[addr])+
                             mtw1[addr]*pow((double)yabf,(double)ptw1[addr]);
	         areap[addr]=marea0[addr]*
                             pow((double)ocdep,(double)parea0[addr])+
                             marea1[addr]*
                             pow((double)yabf,(double)parea1[addr]);
	         rkp[addr]=mk0[addr]*pow((double)ocdep,(double)pk0[addr])+
                           mk1[addr]*pow((double)yabf,(double)pk1[addr]);
	         rpk[addr]=pk1[addr]*mk1[addr]*
                                 pow((double)yabf,(double)(pk1[addr]-1.0));
                }
              else
                {
	        width[addr]=mtw0[addr]*pow((double)ydep,(double)ptw0[addr]);
	        areap[addr]=marea0[addr]*pow((double)ydep,(double)parea0[addr]);
	        rkp[addr]=mk0[addr]*pow((double)ydep,(double)pk0[addr]);
                rpk[addr]=pk0[addr]*mk0[addr]*
                                pow((double)ydep,(double)(pk0[addr]-1.0));
                }
	      }
           }
        else if (ltype[j]==8)
           {
           /* do breakpoint x-sections */
           for(i=1;i<=nx1[j];i++)
              {
              addr=i+j*NODES;
              ydep=yp[addr]-bel[addr];
              tnum=table_num[addr];
              if(tnum>maxtab) fprintf(stderr,
      "Error in section: Request for table beyond max. table number.\n"); 
              if(ydep<ht_spc[tnum])
                 {
                 /* depth is in the shallowest range, use 5/3 pwr interp. */
                 /* the use of 5/3 power in the shallowest range reduces  */
                 /* the effect of diminishing hydraulic properties in     */
                 /* shallow depths.         FLO 10-8-94                   */
                 depc=pow(ht_spc[tnum],5.0/3.0);
                 ca=xarea[1+tnum*NUMBPTS]/depc;
                 ct=xtw[1+tnum*NUMBPTS]/depc;
                 ck=xk[1+tnum*NUMBPTS]/depc;
                 depn=pow(ydep,5.0/3.0);
                 areap[addr]=ca*depn;
                 width[addr]=ct*depn;
                 rkp[addr]=ck*depn;
                 rpk[addr]=ck*pow(ydep,2.0/3.0);
                 }
              else
                 {
                 /* DEPTH IS DEEPER THAN SHALLOWEST RANGE, USE LINEAR INTERP */
                 /* check to see if depth is greater than the range of data */
                 maxbp=numhts[tnum];
                 xdy=ht_spc[tnum];
                 if(ydep>(maxbp*xdy))
                   {
                   taddr=maxbp+tnum*NUMBPTS;
                   /* Use Linear EXTRAPOLATION (should warn user too!) */
                   areap[addr]=xarea[taddr]+(ydep-maxbp*xdy)*
                      (xarea[taddr]-xarea[taddr-1])/xdy;
                   width[addr]=xtw[taddr]+(ydep-maxbp*xdy)*
                      (xtw[taddr]-xtw[taddr-1])/xdy;
                   rkp[addr]=xk[taddr]+(ydep-maxbp*xdy)*
                      (xk[taddr]-xk[taddr-1])/xdy;
                   rpk[addr]=(xk[taddr]-xk[taddr-1])/xdy;
                   }
                else
                   {
                   /* use linear interpolation */
                   ldex=(int)(ydep/xdy);
                   hdex=ldex+1;
                   ca=(xarea[hdex+tnum*NUMBPTS]-xarea[ldex+tnum*NUMBPTS])/xdy;
                   ct=(xtw[hdex+tnum*NUMBPTS]-xtw[ldex+tnum*NUMBPTS])/xdy;
                   ck=(xk[hdex+tnum*NUMBPTS]-xk[ldex+tnum*NUMBPTS])/xdy;
                   areap[addr]=xarea[ldex+tnum*NUMBPTS]+ca*
                               (ydep-(float)ldex*xdy);
                   width[addr]=xtw[ldex+tnum*NUMBPTS]+ct*
                               (ydep-(float)ldex*xdy);
                   rkp[addr]=xk[ldex+tnum*NUMBPTS]+ck*
                               (ydep-(float)ldex*xdy);
                   rpk[addr]=ck;
                   }
                 }
              }
           }
        else if (ltype[j]==9)
           {
           /* do multiple side slope trapezoidal calculations */
	   for(i=1;i<=nx1[j];i++)
	      {
	      addr=i+j*NODES;
	      ydep=yp[addr]-bel[addr];
              ocdep=chn_dep[addr];
              if(ydep>ocdep)
                {
                yabf=ydep-ocdep;
                width[addr]=bottom[addr]+2.0*ocdep*sslope[addr]+
			    2.0*sslope2[addr]*yabf;
                perim=bottom[addr]+2.0*ocdep*sqrt((double)(1.0+sslope[addr]*
		      sslope[addr]))+2.*yabf*sqrt((double)(1.0+sslope2[addr]*
		      sslope2[addr]));
                areap[addr]=ocdep*(bottom[addr]+ocdep*sslope[addr])+
			    0.5*yabf*(bottom[addr]+2.0*ocdep*sslope[addr]+
			    width[addr]);
                r=areap[addr]/perim;
                rpk[addr]=(5./3.)*strick[addr]*pow((double)r,(double)0.6666667)*
			  (bottom[addr]+2.0*ocdep*sslope[addr]+2.0*sslope2[addr]*yabf)
			  -(4./3.)*strick[addr]*pow((double)r,(double)1.6666667)*
			  sqrt((double)(1.0+sslope2[addr]*sslope2[addr]));
                rkp[addr]=strick[addr]*pow((double)areap[addr],
                   (double)1.666667)/pow((double)perim,(double)0.666667);
                }
              else
                {
                width[i+j*NODES]=bottom[i+j*NODES]+2.0*ydep*sslope[i+j*NODES];
                perim=bottom[i+j*NODES]+2.0*ydep*
                     sqrt((double)(1.0+sslope[i+j*NODES]*sslope[i+j*NODES]));
                areap[i+j*NODES]=ydep*(bottom[i+j*NODES]+
         	     ydep*sslope[i+j*NODES]);
                r=areap[i+j*NODES]/perim;
                rpk[i+j*NODES]=strick[i+j*NODES]*(1.66667*(bottom[i+j*NODES]+
                   2.0*sslope[i+j*NODES]*ydep)*
                   pow((double)r,(double)0.6666667)-
                   1.33333*sqrt(1+sslope[i+j*NODES]*sslope[i+j*NODES])*
                   pow((double)r,(double)1.6666667));
                rkp[i+j*NODES]=strick[i+j*NODES]*pow((double)areap[i+j*NODES],
                   (double)1.666667)/pow((double)perim,(double)0.666667);
	        }
              }
           }
        }
     }
  return;
}
