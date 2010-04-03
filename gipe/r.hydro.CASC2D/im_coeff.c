
#include "all.h"

/*********************************COEFF SUB FROM CHARIMA *********
 *       ----------- COEFF.FOR ---------------               12/28/91
 *
 */
   void 
coeff (
/*
 *   THIS SUBROUTINE CALCULATES THE COEFFICIENTS FOR PRIESSMANN'S 
 *   DOUBLE SWEEP METHOD.  VERSION BY J.C. YANG FROM CHARIMA CODE
 */
    float *area,
    float *areap,
    float *yp,
    float *y,
    float *qp,
    float *q,
    float *width,
    double alpha,
    double beta,
    float *rk,
    float *rkp,
    int i,
    int j,
    float *a,
    float *b,
    float *c,
    float *d,
    float *g,
    float *rpk,
    float *ap,
    float *bp,
    float *cp,
    float *dp,
    float *gp,
    double grav,
    double theta,
    double delt,
    double delx,
    int yes_drain
)
{

/*
 *     DEFINE LOCAL VARIABLES 
 */
      int i1;
      float delts,arepi,arepi1,ypi,ypi1,arei,areis,areic,
          arei1,arei1s,yi,yi1,rki,rkis,rkic,rki1,rki1s,
          rki1c,rkpi,rkpis,rkpi1,rkpi1s,rpki,rpki1,qpi,
          qpi1,qi,qis,qi1,wi,wi1,alpi,phi,vi,vi1,bet = 0.0;

      delts=delt*60.0;
/*      IF(IUNST.NE.0.AND.ITIME.GT.0) delts=DELTB*TCONST
 *     CALL SECPRO(TALWEG,area,RH,FFACT,width,Y,NSEC,ISECAD,SEGEOM,
 *    1 SEGEOM,DRYBED,LNKNAM,RK,RPK,RKP,RPKP,areap,l,i,
 *    2  ltype,mu,md,ll,ii)
 */
      i1=i+1;

/*      CALL SECPRO(TALWEG,area,RH,FFACT,width,Y,NSEC,ISECAD,SEGEOM,
 *    1 SEGEOM,DRYBED,LNKNAM,RK,RPK,RKP,RPKP,areap,l,i1,
 *    2  ltype,mu,md,ll,ii)
 *
 *                TRANSFER THE ARRAY VARIABLES TO SCALAR FOR
 *                THE CONVENIENCE OF CODING THE FOLLOWING
 *                FORMULATION
 */

      arepi=areap[i+j*NODES];
      arepi1=areap[i+1+j*NODES];
      ypi=yp[i+j*NODES];
      ypi1=yp[i+1+j*NODES];
      arei=area[i+j*NODES];
      areis=arei*arei;
      areic=areis*arei;
      arei1=area[i+1+j*NODES];
      arei1s=arei1*arei1;
      yi=y[i+j*NODES];
      yi1=y[i+1+j*NODES];
      rki=rk[i+j*NODES];
      rkis=rki*rki;
      rkic=rkis*rki;
      rki1=rk[i+1+j*NODES];
      rki1s=rki1*rki1;
      rki1c=rki1s*rki1;
      rkpi=rkp[i+j*NODES];
      rkpis=rkpi*rkpi;
      rkpi1=rkp[i+1+j*NODES];
      rkpi1s=rkpi1*rkpi1;
      rpki=rpk[i+j*NODES];
      rpki1=rpk[i+1+j*NODES];
      qpi=qp[i+j*NODES];
      qpi1=qp[i+1+j*NODES];
      qi=q[i+j*NODES];
      qis=qi*qi;
      qi1=q[i+1+j*NODES];
      wi=width[i+j*NODES];
      wi1=width[i+1+j*NODES];
      alpi=alpha;
      phi=0.5;

/*     THE FOLLOWING VARIABLES WERE DEFINED TO INCREASE READABILITY  */
      vi=qi/arei;
      vi1=qi1/arei1;

/*
 *                DURING THE FIRST-LEVEL ITERATION FOR THE QUASI-
 *                STEADY SIMULATION, ALPHA IS SET TO 0.0 (IDT<=10)
 *                TO AVOID THE INSTABILITY CAUSED BY SUPERCRITICAL
 *                FLOW
 */
      if(q[i+j*NODES]*(y[i1+j*NODES]-y[i+j*NODES])<=0.0 || q[i1+j*NODES]*(y[i1+j*NODES]-y[i+j*NODES])
         <=0.0) bet=0.5;
      if(q[i+j*NODES]<0.0 && q[i1+j*NODES]<0.0) bet=1.0-bet;
/*      delx=-reach(i,L)
 *
 *                COMPUTE A,B,C,-----------ETC.
 */
      *a=phi*wi1/delts;
      *b=theta/delx;
      *c=-(1.-phi)*wi/delts;
      *d=(*b);
/*
 *    ADD LATERAL INFLOW (qlat[i+j*NODES]) 
 *    TO THE g COEFFICIENT BELOW BUT !!!NOT!!! IF DRAINING!!!!!!!!!!
 *
 *    THIS BUG WAS HUNTED DOWN AND KILLED BY FLO 10-30-94
 *    this is a problem, because when draining, qlat is undefined.
 */
      if(!yes_drain)
	 {
         *g=-phi/delts*(arei1-arepi1)-(1-phi)/delts*(arei-arepi)-
            theta/delx*(qi1-qi)-(1-theta)/delx*(qpi1-qpi)+qlat[i+j*NODES];
	 }
      else
	 {
         *g=-phi/delts*(arei1-arepi1)-(1-phi)/delts*(arei-arepi)-
            theta/delx*(qi1-qi)-(1-theta)/delx*(qpi1-qpi);
	 }

      *ap=-alpi*theta*wi1/arei1s*qi1*(theta/delx*(qi1-qi)+
         (1-theta)/delx*(qpi1-qpi))-alpi*theta*wi1/delx*
         (theta/4*pow((double)(vi+vi1),2.)+(1-theta)/4*pow((double)
         (qpi/arepi+qpi1/arepi1),2.))+alpi*theta*wi1/2/arei1s*qi1*(vi+
         vi1)*(theta/delx*(arei1-arei)+(1-theta)/delx*(arepi1-
         arepi))+theta*grav/delx*(theta/2*(arei+arei1)+(1-theta)/2*
         (arepi+arepi1))+theta*grav*wi1/2*(theta/delx*(yi1-yi)+
         (1-theta)/delx*(ypi1-ypi))-theta*grav*(1-bet)*rpki1/rki1c*qi1*
         abs(qi1)*(theta*(arei+arei1)+(1-theta)*(arepi+arepi1));

      *ap=(*ap)+theta*grav*wi1/2*(theta*(bet*qi*abs(qi)/rkis+
         (1-bet)*qi1*abs(qi1)/rki1s)+(1-theta)*(bet*qpi*abs(qpi)/rkpis+
         (1-bet)*qpi1*abs(qpi1)/rkpi1s));

      *bp=phi/delts+(theta/delx*alpi*(theta/2*(2*vi+2*qi1/
         arei1)+(1-theta)/2*(2*qpi/arepi+2*qpi1/arepi1))
         +alpi*theta/arei1*(theta/delx*(qi1-qi)+(1-theta)/delx*(
         qpi1-qpi))-alpi*theta/2/arei1*
         (vi+vi1)*(theta/delx*
         (arei1-arei)+(1-theta)/delx*
         (arepi1-arepi)))+grav*theta*(1-bet)*
         abs(qi1)/rki1s*(theta*(arei+arei1)+(1-theta)*(arepi+arepi1));
      *cp=-alpi*theta*wi*qi/areis*(theta/delx*(qi1-qi)+(1-theta)/
         delx*(qpi1-qpi))+alpi*theta*wi/delx*(theta/4*pow((double)(vi+
         vi1),2.)+(1-theta)/4*pow((double)(qpi/arepi+qpi1/arepi1),2.))+alpi*
         theta/2*(wi*qis/areic+wi*qi*qi1/(arei1*areis))*
         (theta/delx*(arei1-arei)+
         (1-theta)/delx*(arepi1-arepi))-theta*
         grav/delx*(theta/2*(arei+arei1)+(1-theta)/2*(arepi+arepi1))+
         theta*grav*wi/2/delx*(theta*(yi1-yi)+(1-theta)*(ypi1-
         ypi))-grav*theta*bet*rpki*qi*abs(qi)/rkic*(theta*(arei+arei1)+
         (1-theta)*(arepi+arepi1));
      *cp=(*cp)+theta*grav*wi/2*(theta*(bet*qi*abs(qi)/rkis+
         (1-bet)*qi1*abs(qi1)/rki1s)+(1-theta)*(bet*qpi*abs(qpi)/
         rkpis+(1-bet)*qpi1*abs(qpi1)/rkpi1s));
      *cp=-(*cp);

      *dp=(1-phi)/delts+(-theta/delx*alpi*(theta*(vi+qi1/
         arei1)+(1-theta)*(qpi/arepi+qpi1/arepi1))
         +alpi*theta/arei*(theta/delx*(qi1-qi)+(1-theta)/
         delx*(qpi1-qpi))-alpi*theta/2/arei*(vi+vi1)*
        (theta/delx*(arei1-arei)+
        (1-theta)/delx*(arepi1-arepi)))+
        grav*theta*bet*abs(qi)/rkis*(theta*(arei+arei1)+(1-theta)*
        (arepi+arepi1));
      *dp=-(*dp);

      *gp=phi/delts*(qi1-qpi1)+(1-phi)/delts*(qi-qpi)+alpi*(
         theta*(vi+vi1)+(1-theta)*(qpi/arepi+
         qpi1/arepi1))*(theta/delx*(qi1-qi)+(1-theta)/delx*(
         qpi1-qpi))-alpi*(theta/4*pow((double)(vi+vi1),2.)+
         (1-theta)/4*pow((double)(qpi/arepi+qpi1/arepi1),2.))*(theta/delx*
         (arei1-arei)+(1-theta)/delx*
         (arepi1-arepi))+grav*
         (theta/2*(arei+arei1)+(1-theta)/2*(arepi+arepi1))*
         (theta/delx*(yi1-yi)+(1-theta)/delx*(ypi1-ypi));

      *gp=(*gp)+ grav*(theta/2*(arei+arei1)+(1-theta)/2*(arepi+arepi1))*
         (theta*(bet*qi*abs(qi)/rkis+(1-bet)*qi1*abs(qi1)/rki1s)+
         (1-theta)*(bet*qpi*abs(qpi)/rkpis+(1-bet)*qpi1*abs(qpi1)/
         rkpi1s));
      *gp=-(*gp);
/*      write(6,cfchk1) */
     return;
}
