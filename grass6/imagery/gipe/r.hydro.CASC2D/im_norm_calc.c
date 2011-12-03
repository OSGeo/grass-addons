#include "all.h"

/*******************************************************************/
 void 
norm_calc (

/*-----------------------------------------------------------------------
    Fred L. Ogden, UCONN 10-8-94.

   This subroutine calculates the normal depth at the outlet given 
   an equilibrium discharge in the channel network.  The slope at the
   outlet is assumed to equal (bed elev. of the next to last node-
   bed elev. of last node)/delx.  If this slope is adverse, the program
   WILL bomb.  Make sure the outlet slope is POSITIVE.

   If yes_bkwater is 1, then the standard step backwater method is applied
   to the entire flow network.  DO NOT DRAIN if yes_bkwater=1.

   Variables passed to this subroutine:

     nl -       the number of links in the network (int)
     nx1 -      the 1-D array with the number of nodes for each links (int)  
     ltype -    the 1-D array of link type (int)
     qp -       1-D array of discharges in all nodes,links (float)
     bel -      1-D array of bed elevation at each node,link (float)
     xk -       1-D array of conveyance at each table_num, depth (float)
     numhts -   1-D array of number of height intervals per table (int)
     ht_spc -   1-D array of height intervals per table (float)
     table_num- the table number array (2-D) for each node,link, w/ltype=8
     delx -     the scalar distance between channel nodes (float)
     NUMBPTS -  the maximum number of breakpoints per table, for ltype 8 (int)
     sslope -   side slope for trapezoidal channel links
     bottom-    bottom width for trapezoidal channel links
     strick-    roughness coeff for trapezoidal links
     yes_bkwater  flag.  if 1, then do backwater draining.  Do not if 0
     grav-      gravity.

   Variables returned by this subroutine:

     normout = the normal depth at the outlet (float)

   NOTES:  This subroutine was written initially for ltype 8 by FLO on
           10-16-94.  Link type 1 was added later as well as type 2 for 
           backwater option.

           Need to warn user of supercritical channel slopes!!!!
 
------------------------------------------------------------------------*/
    int nl,
    int *nx1,
    int *ltype,
    int *backdep,
    float *yp,
    float *qp,
    float *bel,
    float *xarea,
    float *xtw,
    float *xk,
    int *numhts,
    float *ht_spc,
    int *table_num,
    double delx,
    int NUMBPTS,
    float *normout,
    float *sslope,
    float *bottom,
    float *strick,
    int yes_bkwater,
    double grav
)

{

/*
 *    LOCAL VARIABLES
 */
   float K,sout,tk,bk,dy,kslope,Q_out;
   int i,j,tnum_out;
   float sidsl,cz,width,mann;
   float depth,are,per,rhydr,q,dnq;
   int count;

   double guess;             /* changed from float to double, BS 6-16-95 */
   double tol,diff=100.0;
   double qds,yds,qus=0.0L,yus;
   double d_bel=0.0L,d_bottom=0.0L,d_sslope=0.0L,d_strick=0.0L;
   double ads,kds,d_dkdy,d_width,eds,sfds;
   double aus,kus,dkus,eus,f,dfus;
   int iter;
   float wconst,root2g,yw,wwidth,eps,rteps;

   root2g=sqrt((double)(2.0*grav)); 
   wconst=root2g*sqrt((double)(1.0/3.0))*2.0/3.0;
   eps=0.25*grav/32.2;
   rteps=0.5*grav/32.2;

   tol=0.0001;
   sout=( bel[ (nx1[nl]-1) + nl*NODES ]-bel[ nx1[nl] + nl*NODES ] )/delx;
   if(sout<=0.0) fprintf(stderr,"WARNING: zero or negative slope at outlet\n");
   *normout=-0.9;

   Q_out=qp[nx1[nl]+nl*NODES];
   fprintf(stderr,"Outlet discharge=%f\n",Q_out);
   tnum_out=table_num[nx1[nl]+nl*NODES];

   if(ltype[nl]==8) /* this is a breakpoint link */
      {
      K=Q_out/(sqrt(sout));
      dy=ht_spc[tnum_out];
      for(i=1;i<=numhts[tnum_out];i++)
         {
         /* search for the proper range of K(y) */
         if(i==1)
            {
            if(K < xk[i+tnum_out*NUMBPTS])
               {
               /* the normal depth at the outlet is in the first interval */
               bk=0.0;
               tk=xk[i+tnum_out*NUMBPTS];
               *normout=(dy/(tk-bk))*K;
               }
            }
         else
            {
            if((K>=xk[i-1+tnum_out*NUMBPTS])&&(K<xk[i+tnum_out*NUMBPTS]))
               {
               /* the normal depth at the outlet is in this interval */
               bk=xk[i-1+tnum_out*NUMBPTS];
               tk=xk[i+tnum_out*NUMBPTS];
               *normout=(i-1)*dy+(dy/(tk-bk))*(K-bk);
               }
            }
         }
      if(*normout<0.0)
         {
         /* the normal depth exceeds the range of the x-section data */
         /* So, normal depth must be calculated by extrapolation and */
         /* the user should be warned.                               */
         fprintf(stderr,"WARNING: Normal depth at outlet exceeds the range of the x-section data\n");
         kslope=dy/(xk[numhts[tnum_out]+tnum_out*NUMBPTS]-
                    xk[numhts[tnum_out]-1+tnum_out*NUMBPTS]);
         tk=K;
         bk=xk[numhts[tnum_out]+tnum_out*NUMBPTS];
         *normout=numhts[tnum_out]+dy+(tk-bk)*kslope;
         }
      }

   if(ltype[nl]==1)  /* this is a trapezoidal link */
      {
      guess=10.0;
      sidsl=sslope[nx1[nl]+nl*NODES];
      cz=2.0*sqrt(1.0+sidsl*sidsl);
      width=bottom[nx1[nl]+nl*NODES];
      mann=strick[nx1[nl]+nl*NODES];
      count=0;
      while(diff>tol)
         {
         depth=guess;
         are=width*depth+sidsl*depth*depth;
         per=width+depth*cz;
         rhydr=are/per;
         q=sqrt(sout)*mann*are*pow(rhydr,(2.0/3.0));
         dnq=sqrt(sout)*mann*(width+2.0*sidsl*depth)*
             pow(rhydr,(2.0/3.0))+sqrt(sout)*mann*are*(2./3.)*
             pow(rhydr,(-1./3.))*(((width+2.0*sidsl*depth)/per)-
             (are*cz)/(per*per));
         guess=depth+(Q_out-q)/dnq;
         diff=fabs(guess-depth);
         if(count>250)
            {
            fprintf (stdout,"WARNING NO CONVERGENCE IN NORMCALC!!!\n");
            fprintf (stdout,"AFTER 250 ITERATIONS.  PROGRAM WIL\n");
            fprintf (stdout,"FAIL.  CHECK OUTLET SLOPE.  MUST BE\n");
            fprintf (stdout,"POSITIVE.\n");
            exit(1);
            }
         count++;
         }
      *normout=guess;
      }
   if(*normout<0.0) fprintf(stderr,"WARNING: normal depth at outlet <0\n");

/*************************************************************************/
/**** THE REST IS USED ONLY FOR STANDARD-STEP BACKWATER CALCULATIONS *****/
/*************************************************************************/

   if(yes_bkwater==TRUE)  /* calculate normal depths in the rest of the 
                             network using standard step method */
      {
      tol=0.0001;
      yp[nx1[nl]+nl*NODES]=(*normout)+bel[nx1[nl]+nl*NODES];

      for(j=nl;j>=1;j--)
         {
         if(ltype[j]==2) 
            {     /* weir link */
            yw=bel[1+j*NODES];
            wwidth=sslope[1+j*NODES];
            qp[2+j*NODES]=qp[1+backdep[j]*NODES];
            qds=qp[2+j*NODES];
            qp[1+j*NODES]=qus;
            yp[2+j*NODES]=yp[1+backdep[j]*NODES];
            yds=yp[2+j*NODES];
            qus=qds;
            /* assume free flowing */
            yus=pow((qus/(wconst*wwidth)),2.0/3.0)+yw;
            if((fabs(yus-yds)>eps)&&((yds-yw)<2.0/3.0*(yus-yw)))
               {  /* it is free flowing */
               yp[1+j*NODES]=yus;
               continue;
               }
            /* assume flooded and singular */
            yus=qus*eps/(wwidth*root2g*(yds-yw)*sqrt(eps))+yds;
            if(fabs(yus-yds)<=eps)  /* it is flooded and singular */
               { 
               yp[1+j*NODES]=yus;
               continue;
               }
            /* it must be flooded but non-singular */
            yus=pow(qus/(wwidth*root2g*(yds-yw)),2.0)+yds;
            yp[1+j*NODES]=yus;
            if(yus<yw) fprintf (stdout,"problem at weir in link %d\n",j);
            continue;
            }
         for(i=nx1[j];i>=1;i--)
            {
            if((j==nl)&&(i==nx1[j])) continue;
            if(i==nx1[j])
               {
               yp[nx1[j]+j*NODES]=yp[1+backdep[j]*NODES];
               continue;
               }
            count=0;
            qds=(double)qp[i+1+j*NODES];
            qus=(double)qp[i+j*NODES];
            yds=(double)yp[i+1+j*NODES];
          
            if(ltype[j]==1)
               {
               d_bel=(double)bel[i+1+j*NODES];
               d_bottom=(double)bottom[i+1+j*NODES];
               d_sslope=(double)sslope[i+1+j*NODES];
               d_strick=(double)strick[i+1+j*NODES];
               
               trap_section(i+1,j,d_bottom,d_sslope,d_strick,yds,d_bel,
                   &ads,&kds,&d_dkdy,&d_width);
               }
            if(ltype[j]==8)
               {     /* breakpoint x-sections */
               brk_pnt_section(i+1,j,bel,yp,yds,table_num,ht_spc,numhts,NUMBPTS,
                               xarea,xtw,xk,&ads,&kds,&d_dkdy,&d_width);
               fprintf(stderr,"%d %d %9.3f %9.3f %9.3f %9.3f %9.3f\n",j,i,yds-bel[i+1+j*NODES],ads,kds,d_dkdy,d_width);
               }

            eds=yds+(qds*qds)/(ads*ads*(double)2.0*(double)grav);
            sfds=(qds*qds)/(kds*kds);
            guess=(double)(bel[i+j*NODES]+yds-bel[i+1+j*NODES]-0.1*
                  (yds-bel[i+1+j*NODES])); 

            /* use Newton-Raphson to find yus */
            if(ltype[j]==1)
               {
               d_bel=(double)bel[i+j*NODES];
               d_bottom=(double)bottom[i+j*NODES];
               d_sslope=(double)sslope[i+j*NODES];
               d_strick=(double)strick[i+j*NODES];
               }

            for(iter=1;iter<=250;iter++)
               {
               yus=guess;
               if(ltype[j]==1)
                  {
                  trap_section(i,j,d_bottom,d_sslope,d_strick,yus,d_bel,
                          &aus,&kus,&dkus,&d_width);
                  }
               if(ltype[j]==8)
                  {     /* breakpoint x-sections */
                        /* corrected downstream return values to upstream, BS */
                  brk_pnt_section(i,j,bel,yp,yus,table_num,ht_spc,numhts,NUMBPTS,
                                  xarea,xtw,xk,&aus,&kus,&dkus,&d_width);
               fprintf(stderr,"%d %d %9.3f %9.3f %9.3f %9.3f %9.3f %d\n",j,i,yus-bel[i+j*NODES],aus,kus,dkus,d_width,iter);
                  }
   

               eus=yus+((qus*qus)/(aus*aus))/((double)2.0*grav)-
                   (sfds+(qus*qus/(kus*kus))*delx/(double)2.0);

               f=yus+((qus/aus)*(qus/aus))/((double)2.0*grav)-
                 delx/2.0*(((qus/kus)*(qus/kus))+sfds)-eds;

               dfus=1-qus*qus/(grav*(aus*aus*aus))*d_width+  /*correction, BS */
                    ((delx*qus*qus)/(kus*kus*kus))*dkus;

               /* fprintf(stderr,"%f %f %f %f %f %f %f %f %f %f %f %f\n",
                  yus,eds,aus,kus,dkus,sfds,qus,grav,d_width,eus,f,dfus); */

               guess=yus-f/dfus;
               count++;
               diff=fabs(yus-guess);
               if(fabs(diff)<=tol) break;

               /* fprintf(stderr,"%d %d %d  %lf  %lf  %lf  %lf:\n",
                              j,i,iter,qds,qus,yds,guess);              */

               }
            if(fabs(diff)<=tol)
               {
               yp[i+j*NODES]=(float)guess;
               /* fprintf (stdout,"link %d node %d diff=%f iter=%d\n",j,i,diff,iter);*/
               continue;
               }
            else
               {
               fprintf (stdout,"no convergence in norm_calc, link %d node %d\n",j,i);
               exit(2);
               }
            }               
         }
      }
   return;
}

/*********************************************************************/
int trap_section (
    int i,
    int j,
    double d_bottom,
    double d_sslope,
    double d_strick,
    double y,
    double d_bel,
    double *d_area,
    double *d_konv,
    double *d_dkdy,
    double *d_width
)
/*********************************************************************/
{
   double ydep,perim,r;
   double fith;
   double foth;
   double toth;

   fith=(double)5.0/(double)3.0;
   foth=(double)4.0/(double)3.0;
   toth=(double)2.0/(double)3.0;

   ydep=y-d_bel;
   if(ydep<0.0)
      {
      fprintf (stdout,"zero depth in norm_calc, link %d, node %d\n",j,i);
      exit(2);
      }
   *d_width=d_bottom+(double)2.0*ydep*d_sslope;
   perim=d_bottom+(double)2.0*ydep*sqrt((double)1.0+d_sslope*d_sslope);
   *d_area=ydep*(d_bottom+ydep*d_sslope);
   r=(*d_area)/perim;
   *d_konv=d_strick*pow((*d_area),fith)/pow(perim,toth);
   *d_dkdy=d_strick*(fith*(d_bottom+(double)2.0*d_sslope*ydep)*
           pow(r,toth)-foth*sqrt((double)1.0+d_sslope*d_sslope)*
           pow(r,fith));
   return 0;
}

/*********************************************************************/
int 
brk_pnt_section (
/*********************************************************************/
    int i,
    int j,
    float *bel,
    float *yp,
    double y,
    int *table_num,
    float *ht_spc,
    int *numhts,
    int NUMBPTS,
    float *xarea,
    float *xtw,
    float *xk,
    double *ads,
    double *kds,
    double *d_dkdy,
    double *d_width
)

{
   int addr,taddr,maxbp,ldex,hdex,tnum,haddr,laddr;
   double ydep;
   double depc,ca,ca1,ct,ct1,ck,ck1,depn,xdy;
   double fith,toth;

   fith=(double)5.0/(double)3.0;
   toth=(double)2.0/(double)3.0;


   addr=i+j*NODES;
   /*       ydep=(double)yp[addr]-(double)bel[addr];    */
   ydep=y-(double)bel[addr];
   if(ydep<0.0)
      {
      fprintf (stdout,"program stopped for negative depth, node %d, link %d\n",i,j);
      exit(2);
      }
   tnum=table_num[addr];
   if(ydep<(double)ht_spc[tnum])
      {
      /* depth is in the shallowest range, use 5/3 pwr interp. */
      /* the use of 5/3 power in the shallowest range reduces  */
      /* the effect of diminishing hydraulic properties in     */
      /* shallow depths.         FLO 10-8-94                   */
      depc=pow((double)ht_spc[tnum],fith);
      ca=(double)xarea[1+tnum*NUMBPTS]/depc;
      ct=(double)xtw[1+tnum*NUMBPTS]/depc;
      ck=(double)xk[1+tnum*NUMBPTS]/depc;
      depn=pow(ydep,fith);
      *ads=ca*depn;
      *d_width=ct*depn;
      *kds=ck*depn;
      *d_dkdy=ck*pow(ydep,toth);
      return 0;
      }
   else
      {
      /* DEPTH IS DEEPER THAN SHALLOWEST RANGE, USE LINEAR INTERP */
      /* check to see if depth is greater than the range of data */
      maxbp=numhts[tnum];
      xdy=(double)ht_spc[tnum];
      if(ydep>((double)maxbp*xdy))
         {
         taddr=maxbp+tnum*NUMBPTS;
         ca=(double)xarea[taddr];
         ca1=(double)xarea[taddr-1];
         ct=(double)xtw[taddr];
         ct1=(double)xtw[taddr-1];
         ck=(double)xk[taddr];
         ck1=(double)xk[taddr-1];

         /* Use Linear EXTRAPOLATION (should warn user too!) */
         *ads=ca+(ydep-(double)maxbp*xdy)*(ca-ca1)/xdy;
         *d_width=ct+(ydep-(double)maxbp*xdy)*(ct-ct1)/xdy;
         *kds=ck+(ydep-(double)maxbp*xdy)*(ck-ck1)/xdy;
         *d_dkdy=(ck-ck1)/xdy;
         return 0;
         }
      else
         {
         /* use linear interpolation */
         ldex=(int)(ydep/xdy);
         hdex=ldex+1;
         haddr=hdex+tnum*NUMBPTS;
         laddr=ldex+tnum*NUMBPTS;
         ca=((double)xarea[haddr]-(double)xarea[laddr])/xdy;
         ct=((double)xtw[haddr]-(double)xtw[laddr])/xdy;
         ck=((double)xk[haddr]-(double)xk[laddr])/xdy;
         *ads=(double)xarea[laddr]+ca*(ydep-(double)ldex*xdy);
         *d_width=(double)xtw[laddr]+ct*(ydep-(double)ldex*xdy);
         *kds=(double)xk[laddr]+ck*(ydep-(double)ldex*xdy);
         *d_dkdy=ck;
   
         /* fprintf(stderr,"%d %d   %f %f \n",j,i,*ads,*kds); */
         return 0;
         }
      }
   fprintf (stdout,"error in im_norm_calc, function brk_pnt_section\n");
   exit(2);
}
