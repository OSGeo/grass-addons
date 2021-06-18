
#include "all.h"

/*********************************************************************/
void flow_route (


/*
 *    DECLARE VARIABLES PASSED TO THE FUNCTION 
 */

 /*   Overland Connection Variables   */


 /*   Other Variables  */
    int iter,
    int itime,
    double delt,
    double delx,
    double alpha,
    double beta,
    double theta,
    double grav,
    int *depend,
    int *backdep,
    int *nx1,
    float *bel,
    float *yp,
    float *qp,
    float *strick,
    float *bottom,
    float *chn_dep,
    float *sslope,
    float *sslope2,
    int *ltype,
    int *ndep,
    double yfirst,
    double ystep,
    double qmin,
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
    int *numqpipe,
    int yes_drain,
    float *xarea,
    float *xtw,
    float *xk,
    int *numhts,
    float *ht_spc,
    int maxtab,
    int *table_num,
    int NUMBPTS,
    double lowspot,
    double highspot,
    double normout,
    double tdrain
)
{

/*
 *    DECLARE STATIC LOCAL VARIABLES
 */

   static float  *q=0,*y=0,*qn=0,
                 *yn=0,*area=0,
                 *areap=0,*rk=0,
                 *rkp=0,*rpk=0,
                 *width=0,*e=0,
                 *f=0,a,b,c,d,g,ap,bp,cp,dp,
                 gp,*l=0,*m=0,
                 *nn=0,*dy=0,
                 *dq=0,denom;

/*
 *      DECLARE OTHER LOCAL VARIABLES
 */

      int i=0,j,k,kk,uplinktype,downlinktype=0,lakenum;
      float qus,dqdy,be,dsdisch,ga,rr,froude,t;
      double ynew;
/*
 *    MEMORY ALLOCATION FOR THE FIRST TIME flow_route IS CALLED
 */
      if(q==NULL) if((q=(float*) malloc(NUM*sizeof(float))) == NULL)
        {
        fprintf(stderr,"cannot allocate memory for q array");
        exit(-2);
        }
      if(y==NULL) if((y=(float*) malloc(NUM*sizeof(float))) == NULL)
        {
        fprintf(stderr,"cannot allocate memory for y array");
        exit(-2);
        }
      if(qn==NULL) if((qn=(float*) malloc(NUM*sizeof(float))) == NULL)
        {
        fprintf(stderr,"cannot allocate memory for qn array");
        exit(-2);
        }
      if(yn==NULL) if((yn=(float*) malloc(NUM*sizeof(float))) == NULL)
        {
        fprintf(stderr,"cannot allocate memory for yn array");
        exit(-2);
        }
      if(area==NULL) if((area=(float*) malloc(NUM*sizeof(float))) == NULL)
        {
        fprintf(stderr,"cannot allocate memory for area array");
        exit(-2);
        }
      if(areap==NULL) if((areap=(float*) malloc(NUM*sizeof(float))) == NULL)
        {
        fprintf(stderr,"cannot allocate memory for areap array");
        exit(-2);
        }
      if(rk==NULL) if((rk=(float*) malloc(NUM*sizeof(float))) == NULL)
        {
        fprintf(stderr,"cannot allocate memory for rk array");
        exit(-2);
        }
      if(rkp==NULL) if((rkp=(float*) malloc(NUM*sizeof(float))) == NULL)
        {
        fprintf(stderr,"cannot allocate memory for rkp array");
        exit(-2);
        }
      if(rpk==NULL) if((rpk=(float*) malloc(NUM*sizeof(float))) == NULL)
        {
        fprintf(stderr,"cannot allocate memory for rpk array");
        exit(-2);
        }
      if(width==NULL) if((width=(float*) malloc(NUM*sizeof(float))) == NULL)
        {
        fprintf(stderr,"cannot allocate memory for width array");
        exit(-2);
        }
      if(e==NULL) if((e=(float*) malloc(NUM*sizeof(float))) == NULL)
        {
        fprintf(stderr,"cannot allocate memory for e array");
        exit(-2);
        }
      if(f==NULL) if((f=(float*) malloc(NUM*sizeof(float))) == NULL)
        {
        fprintf(stderr,"cannot allocate memory for f array");
        exit(-2);
        }
      if(l==NULL) if((l=(float*) malloc(NUM*sizeof(float))) == NULL)
        {
        fprintf(stderr,"cannot allocate memory for l array");
        exit(-2);
        }
      if(m==NULL) if((m=(float*) malloc(NUM*sizeof(float))) == NULL)
        {
        fprintf(stderr,"cannot allocate memory for m array");
        exit(-2);
        }
      if(nn==NULL) if((nn=(float*) malloc(NUM*sizeof(float))) == NULL)
        {
        fprintf(stderr,"cannot allocate memory for nn array");
        exit(-2);
        }
      if(dy==NULL) if((dy=(float*) malloc(NUM*sizeof(float))) == NULL)
        {
        fprintf(stderr,"cannot allocate memory for dy array");
        exit(-2);
        }
      if(dq==NULL) if((dq=(float*) malloc(NUM*sizeof(float))) == NULL)
        {
        fprintf(stderr,"cannot allocate memory for dq array");
        exit(-2);
        }

      t=(float)itime*delt;

/*
 *     SET FIRST ESTIMATE EQUAL TO OLD VALUES
 */
      for(j=1;j<=nlinks;j++)
         {
         for(i=1;i<=nx1[j];i++)
            {
            q[i+j*NODES]=qp[i+j*NODES];
            y[i+j*NODES]=yp[i+j*NODES];
            }
         }
/*
 *      BEGIN NEWTON-RAPHSON CONVERGENCE LOOP
 */

       for(k=1;k<=iter;k++)
          {
/*
 *      CALL SUBROUTINE SECTION TO CALCULATE SECTION PROPERTIES AT
 *      PREVIOUS TIME AND AT NEW TIME (sub does all nodes)
 */
        section(bottom,sslope,sslope2,strick,yp,bel,areap,
                    rkp,rpk,width,nx1,ltype,chn_dep,
		    marea0,parea0,mtw0,ptw0,mk0,pk0,
		    marea1,parea1,mtw1,ptw1,mk1,pk1,
                 /* added with breakpoint x-sect description */
                    xarea,xtw,xk,numhts,ht_spc,maxtab,table_num,NUMBPTS);
        section(bottom,sslope,sslope2,strick,y,bel,area,
                    rk,rpk,width,nx1,ltype,chn_dep,
		    marea0,parea0,mtw0,ptw0,mk0,pk0,
		    marea1,parea1,mtw1,ptw1,mk1,pk1,
                 /* added with breakpoint x-sect description */
                    xarea,xtw,xk,numhts,ht_spc,maxtab,table_num,NUMBPTS);
/*
 *      INCORPORATE UPSTREAM BOUNDARY CONDITIONS
 *        (must be done each iteration)
 */         
	for(j=1;j<=nlinks;j++)
        {
	if(ltype[j] != 4)
	  {
	  uplinktype=ltype[depend[j+1*LINKS]];
	  if(ndep[j]==0 || uplinktype==4)
	     {
/*        THIS IS A FIRST ORDER LINK, OR BELOW A RESERVOIR   */
	     if(uplinktype==4)
	        {
/*              BELOW A RESERVOIR     */
	        lakenum=depend[j+1*LINKS];

/*              ****** NOTES ON DATA TRANSFER AT RESERVOIRS *******
 *              bottom(1,lakenum)=spillway width
 *              sslope(1,lakenum)=present lake w.s.e
 *              bel(1,lakenum)=spillway crest elevation
 */
	        spill(t,&qus,j,bottom[1+lakenum*NODES],
		      chn_dep[1+lakenum*NODES],
		      bel[1+lakenum*NODES],qmin,depend,lakenum,
		      numqpipe,strick,bottom,yes_drain);
                }
	     else
	        {
/*              USE SPECIFIED INFLOW ON ALL FIRST ORDER LINKS   */
		usqot(t,&qus,j,qmin,yes_drain);
                }
             qn[1+j*NODES]=qus;
             e[1+j*NODES]=0.0;
             f[1+j*NODES]=qn[1+j*NODES]-q[1+j*NODES];
             }
           else
             {
             e[1+j*NODES]=0.0;
             f[1+j*NODES]=0.0;
             for(i=1;i<=ndep[j];i++)
                {
                kk=depend[j+i*LINKS];
                e[1+j*NODES]=e[1+j*NODES]+e[nx1[kk]+kk*NODES];
                f[1+j*NODES]=f[1+j*NODES]+q[nx1[kk]+kk*NODES]+e[nx1[kk]+kk*NODES]*
                    (y[1+j*NODES]-y[nx1[kk]+kk*NODES])+f[nx1[kk]+kk*NODES];
                }
             f[1+j*NODES]=f[1+j*NODES]-q[1+j*NODES];
             }
	  }
        }
/*
 *   BEGIN FORWARD SWEEP
 */
     for(j=1;j<=nlinks;j++)
        {
	if(ltype[j]!=4)
	  {
          for(i=1;i<=nx1[j]-1;i++)
             {
             if((ltype[j]==1)||(ltype[j]==8))
                {
/*              CALL SUBROUTINE COEFF TO CALCULATE FLUVIAL COEFFICIENTS  */
                 coeff(area,areap,yp,y,qp,q,width,alpha,beta,
                      rk,rkp,i,j,&a,&b,&c,&d,&g,rpk,
                      &ap,&bp,&cp,&dp,&gp,grav,theta,delt,delx,yes_drain);
                }
             if(ltype[j]==2)
                {
/*              CALL SUBROUTINE WEIR_COEFF TO CALCULATE WEIR COEFFS.   */
                weir_coeff(i,j,strick,bottom,sslope,bel,y,q,
                             &a,&b,&c,&d,&g,&ap,&bp,&cp,&dp,&gp,grav);           
                }

/*           CHECK THE FROUDE NUMBER   */
/*           Don't check internal b.c.'s such as weirs, etc.  because */
/*           flow is often supercritical there.                       */

             if(ltype[j]!=2) /* add to this list as necessary */
                {
	        froude=(qp[i+j*NODES]/(areap[i+j*NODES]))/
	   	    sqrt((double)(grav*(yp[i+j*NODES]-bel[i+j*NODES])));
  	        if(froude>0.9) fprintf(stderr,
	        "Supercritical Warning:node %d link %d FR= %f\n",i,j,froude);
                }

             l[i+j*NODES]= (a*dp-ap*d)/(c*dp-cp*d);
             m[i+j*NODES]= (b*dp-bp*d)/(c*dp-cp*d);
             nn[i+j*NODES]=(d*gp-dp*g)/(c*dp-cp*d);

             /* New way as per notes by FMH, FLO 1-1-95 */

             denom=b-m[i+j*NODES]*(c+d*e[i+j*NODES]);
             e[i+1+j*NODES]=(l[i+j*NODES]*(c+d*e[i+j*NODES])-a)/denom;
                           
             f[i+1+j*NODES]=(nn[i+j*NODES]*(c+d*e[i+j*NODES])+d*f[i+j*NODES]+g)/
                            denom;                            
/*
             e[i+1+j*NODES]=(-ap+cp*l[i+j*NODES]+dp*e[i+j*NODES]*l[i+j*NODES])/
                      (bp-cp*m[i+j*NODES]-dp*e[i+j*NODES]*m[i+j*NODES]);
             f[i+1+j*NODES]=(cp*nn[i+j*NODES]+dp*e[i+j*NODES]*nn[i+j*NODES]+dp*
		f[i+j*NODES]+gp)/(bp-cp*m[i+j*NODES]-dp*e[i+j*NODES]*m[i+j*NODES]); 
 */

             }
          }
       }
/*
 *      BEGIN BACKWARD SWEEP
 */
      for(j=nlinks;j>=1;j--)
         {
         if(ltype[j] !=  4)
            {
            if(j==nlinks) downlinktype=0;
            else downlinktype=ltype[backdep[j]];
            }
         if(j==nlinks || downlinktype==4)
            {
/*          INCORPORATE DOWNSTREAM BOUNDARY CONDITION   */
            if(j==nlinks)
               {
               if((!yes_drain)||(t>tdrain))
   	          {
                  /* NORMAL DEPTH BOUNDARY CONDITION */
                  ddsqoy(bottom,sslope,sslope2,strick,delx,yp,bel,
                             nx1,&dqdy,ltype,chn_dep,mk0,pk0,mk1,pk1,
                             /* added 10-8-94 brkpnt xsect descr. */
                             xk,numhts,ht_spc,table_num,NUMBPTS);
                  dqdy=-dqdy;
                  be=1.0;
                  dsqoy(bottom,sslope,sslope2,strick,delx,yp,bel,nx1,
			       &dsdisch,ltype,chn_dep,mk0,pk0,mk1,pk1,
                               /* added 10-8-94 brkpnt xsect descr. */
                               xk,numhts,ht_spc,table_num,NUMBPTS);
                  ga=dsdisch-q[nx1[j]+j*NODES];
                  rr=dqdy+be*e[nx1[j]+j*NODES];
                  dy[nx1[j]+j*NODES]=(ga-f[nx1[j]+j*NODES])/rr;
                  dq[nx1[j]+j*NODES]=e[nx1[j]+j*NODES]*dy[nx1[j]+j*NODES]+
				    f[nx1[j]+j*NODES];
	          }
               else
	          {
	          dsyot(t,&ynew,downlinktype,lowspot,highspot,tdrain,normout);
	          dy[nx1[j]+j*NODES]=ynew-y[nx1[j]+j*NODES];
	          dq[nx1[j]+j*NODES]=e[nx1[j]+j*NODES]*dy[nx1[j]+j*NODES]+
				     f[nx1[j]+j*NODES];
                  }
               }
             else
	       {
	       ynew=lake_el[lake_cat[con_vect[1+backdep[j]*NODES]]];
               dy[nx1[j]+j*NODES]=ynew-y[nx1[j]+j*NODES];
               dq[nx1[j]+j*NODES]=e[nx1[j]+j*NODES]*dy[nx1[j]+j*NODES]+
                                                  f[nx1[j]+j*NODES];
	       }
	    }
         else
            {
            dy[nx1[j]+j*NODES]=dy[1+backdep[j]*NODES];
            dq[nx1[j]+j*NODES]=e[nx1[j]+j*NODES]*dy[nx1[j]+
                                       j*NODES]+f[nx1[j]+j*NODES];
            }
         yn[nx1[j]+j*NODES]=y[nx1[j]+j*NODES]+dy[nx1[j]+j*NODES];
         if(yn[nx1[j]+j*NODES]-bel[nx1[j]+j*NODES]<0.0) fprintf(stderr,
		  "Negative depth in flow_route nx1[%d]=%d node=%d link=%d\n",
		   j,nx1[j],i,j);
         qn[nx1[j]+j*NODES]=q[nx1[j]+j*NODES]+dq[nx1[j]+j*NODES];
         for(i=nx1[j]-1;i>=1;i--)
            {
            dy[i+j*NODES]=l[i+j*NODES]*dy[i+1+j*NODES]+m[i+j*NODES]*
                                     dq[i+1+j*NODES]+nn[i+j*NODES];
            dq[i+j*NODES]=e[i+j*NODES]*dy[i+j*NODES]+f[i+j*NODES];
            yn[i+j*NODES]=y[i+j*NODES]+dy[i+j*NODES];
            if(yn[i+j*NODES]-bel[i+j*NODES]<0.0) fprintf(stderr,
		     "negative depth %d %d\n", i,j);
            qn[i+j*NODES]=q[i+j*NODES]+dq[i+j*NODES];
            }
         }
      for(j=1;j<=nlinks;j++)
         {
         if(ltype[j]!=4) 
            {
            for(i=1;i<=nx1[j];i++)
               {
               q[i+j*NODES]=qn[i+j*NODES];
               y[i+j*NODES]=yn[i+j*NODES];
               }
            }
         }
      }

/*  Iteration loop closes above   */

   for(j=1;j<=nlinks;j++)
      {
      if(ltype[j]!=4) 
         {
         for(i=1;i<=nx1[j];i++)
            {
            qp[i+j*NODES]=qn[i+j*NODES];
            yp[i+j*NODES]=yn[i+j*NODES];
            }
         }
      else
         {
         reservoir(j,ndep[j],depend,backdep,
		     qp,delt,nx1,qmin,*bel);
         }
     }
      /* fprintf(stderr,"yn[5][33]=%f yn[6][33]=%f\n",yn[5+33*NODES]-bel[5+33*NODES],
              yn[6+33*NODES]-bel[6+33*NODES]); */
      return;
}
