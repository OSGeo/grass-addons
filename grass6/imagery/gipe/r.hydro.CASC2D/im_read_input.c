
#include "all.h"

/*******************************************************************/
 void 
read_input (
    FILE *iunit,
    FILE *yunit,
    FILE *qunit,
    float *grav,
    float *alpha,
    float *beta,
    float *theta,
    float *delx,
    float *delt,
    float *tt,
    int *nlinks,
    int *LINKS,
    int *NODES,
    int *NUM,
    int **depend,
    int **backdep,
    int **nx1,
    float **strick,
    float **bottom,
    float **sslope,
    float **sslope2,
    float **bel,
    float **qp,
    float **yp,
    int **ltype,
    int **ndep,
    int *maxnodes,
    float **chn_dep,
    float **marea0,
    float **parea0,
    float **mtw0,
    float **ptw0,
    float **mk0,
    float **pk0,
    float **marea1,
    float **parea1,
    float **mtw1,
    float **ptw1,
    float **mk1,
    float **pk1,
    int **numqpipe,
    int yes_drain,
    int yes_bkwater,
    int *yes_table,
    int **table_num,             /* table_num added by FLO 10-8-94 */
    float *highspot,
    float *lowspot,
    float *qmin
)
{

/*
 *    LOCAL VARIABLES
 */
   float  Qa=0.0,mann;
   int    i,j,ii,jj,iitmp,itmp,jtmp;

   fscanf(iunit,"%f",grav);
   fscanf(iunit,"%f %f %f",alpha,beta,theta);
   fscanf(iunit,"%f",delx);
   fscanf(iunit,"%f %f",delt,tt);
   fscanf(iunit,"%f",qmin);
   fscanf(iunit,"%d",nlinks);
   fscanf(iunit,"%d",maxnodes);  

   (*NODES)=(*maxnodes)+1;
   (*LINKS)=(*nlinks)+1;
   (*NUM)=(*NODES)*(*LINKS); 

/*
 *    MEMORY ALLOCATION 
 */
      
   if((*yp=(float*) malloc(*NUM*sizeof(float))) == NULL) 
      {
      fprintf(stderr,"cannot allocate memory for yp array");
      exit(-2);
      }
   if((*qp=(float*) malloc(*NUM*sizeof(float))) == NULL) 
      {
      fprintf(stderr,"cannot allocate memory for qp array");
      exit(-2);
      }
   if((*bottom=(float*) malloc(*NUM*sizeof(float))) == NULL) 
      {
      fprintf(stderr,"cannot allocate memory for bottom array");
      exit(-2);
      }
   if((*chn_dep=(float*) malloc(*NUM*sizeof(float))) == NULL) 
      {
      fprintf(stderr,"cannot allocate memory for depth array");
      exit(-2);
      }
   if((*bel=(float*) malloc(*NUM*sizeof(float))) == NULL) 
      {
      fprintf(stderr,"cannot allocate memory for bel array");
      exit(-2);
      }
   if((*sslope=(float*) malloc(*NUM*sizeof(float))) == NULL) 
      {
      fprintf(stderr,"cannot allocate memory for sslope array");
      exit(-2);
      }
   if((*sslope2=(float*) malloc(*NUM*sizeof(float))) == NULL) 
      {
      fprintf(stderr,"cannot allocate memory for sslope2 array");
      exit(-2);
      }
   if((*strick=(float*) malloc(*NUM*sizeof(float))) == NULL) 
      {
      fprintf(stderr,"cannot allocate memory for strick array");
      exit(-2);
      }
   if((*depend=(int*) malloc(3*(*LINKS)*sizeof(int))) == NULL) 
      {
      fprintf(stderr,"cannot allocate memory for depend array");
      exit(-2);
      }
   if((*backdep=(int*) malloc(*LINKS*sizeof(int))) == NULL) 
      {
      fprintf(stderr,"cannot allocate memory for backdep array");
      exit(-2);
      }
   /******THIS WAS ADDED BY FLO 10-8-94 TO INCORP. BREAKPOINT X-SECTS */
   if((*table_num=(int*) malloc(*NUM*sizeof(int))) == NULL) 
      {
      fprintf(stderr,"cannot allocate memory for table_num array");
      exit(-2);
      }
   if((*ltype=(int*) malloc(*LINKS*sizeof(int))) == NULL) 
      {
      fprintf(stderr,"cannot allocate memory for ltype array");
      exit(-2);
      }
   if((*nx1=(int*) malloc(*LINKS*sizeof(int))) == NULL) 
      {
      fprintf(stderr,"cannot allocate memory for nx1 array");
      exit(-2);
      }
   if((*ndep=(int*) malloc(*LINKS*sizeof(int))) == NULL) 
      {
      fprintf(stderr,"cannot allocate memory for ndep array");
      exit(-2);
      }
   /**** the following variables are for APFA type II params ***/
   if((*marea0=(float*) malloc(*NUM*sizeof(float))) == NULL) 
      {
      fprintf(stderr,"cannot allocate memory for marea0 array");
      exit(-2);
      }
   if((*parea0=(float*) malloc(*NUM*sizeof(float))) == NULL) 
      {
      fprintf(stderr,"cannot allocate memory for parea0 array");
      exit(-2);
      }
   if((*mtw0=(float*) malloc(*NUM*sizeof(float))) == NULL) 
      {
      fprintf(stderr,"cannot allocate memory for mtw0 array");
      exit(-2);
      }
   if((*ptw0=(float*) malloc(*NUM*sizeof(float))) == NULL) 
      {
      fprintf(stderr,"cannot allocate memory for ptw0 array");
      exit(-2);
      }
   if((*mk0=(float*) malloc(*NUM*sizeof(float))) == NULL) 
      {
      fprintf(stderr,"cannot allocate memory for mk0 array");
      exit(-2);
      }
   if((*pk0=(float*) malloc(*NUM*sizeof(float))) == NULL) 
      {
      fprintf(stderr,"cannot allocate memory for pk0 array");
      exit(-2);
      }

      /**** the following variables are for APFA type III params ***/
   if((*marea1=(float*) malloc(*NUM*sizeof(float))) == NULL) 
      {
      fprintf(stderr,"cannot allocate memory for marea1 array");
      exit(-2);
      }
   if((*parea1=(float*) malloc(*NUM*sizeof(float))) == NULL) 
      {
      fprintf(stderr,"cannot allocate memory for parea1 array");
      exit(-2);
      }
   if((*mtw1=(float*) malloc(*NUM*sizeof(float))) == NULL) 
      {
      fprintf(stderr,"cannot allocate memory for mtw1 array");
      exit(-2);
      }
   if((*ptw1=(float*) malloc(*NUM*sizeof(float))) == NULL) 
      {
      fprintf(stderr,"cannot allocate memory for ptw1 array");
      exit(-2);
      }
   if((*mk1=(float*) malloc(*NUM*sizeof(float))) == NULL) 
      {
      fprintf(stderr,"cannot allocate memory for mk1 array");
      exit(-2);
      }
   if((*pk1=(float*) malloc(*NUM*sizeof(float))) == NULL) 
      {
      fprintf(stderr,"cannot allocate memory for pk1 array");
      exit(-2);
      }

   for(j=1;j<=*nlinks;j++)
      {
      fscanf(iunit,"%d %d %d %d %d %d\n", &iitmp,&((*ltype)[j]),
                &((*ndep)[j]),&((*depend)[j+1*(*LINKS)]),
		&((*depend)[j+2*(*LINKS)]),&((*backdep)[j]));
      if((*ltype)[j]==8) *yes_table=1; /* there are breakpoint channel 
                                          data links present, so prepare
                                          to read file table.dat */
      }
/* prepare to trap the highest elevation in the network for the drain
   function.  The lowest point in the network will be assumed as the
   elevation of the outlet NODE and LINK */

   *highspot=0.0;

   for(j=1;j<=(*nlinks);j++)
      {
      fscanf(iunit,"%d %d\n", &iitmp,&((*nx1)[j]));
      for(i=1;i<=(*nx1)[j];i++)
         {
         if((*ltype)[j]==5)
            {
            /* read in APFA type II parameters */
            fscanf(iunit,"%f %f %f %f %f %f %f %f\n",&((*marea0)[i+j*(*NODES)]),
			 &((*parea0)[i+j*(*NODES)]),
                         &((*mtw0)[i+j*(*NODES)]),&((*ptw0)[i+j*(*NODES)]),
                         &((*mk0)[i+j*(*NODES)]),&((*pk0)[i+j*(*NODES)]),
                         &((*chn_dep)[i+j*(*NODES)]),&((*bel)[i+j*(*NODES)]));
            }
         if((*ltype)[j]==6)
            {
            /*  read in APFA type III parameters */
            fscanf(iunit,"%f %f %f %f %f %f %f %f %f %f %f %f %f %f\n",
                  &((*marea0)[i+j*(*NODES)]),
                  &((*parea0)[i+j*(*NODES)]),
                  &((*mtw0)[i+j*(*NODES)]),
                  &((*ptw0)[i+j*(*NODES)]),
                  &((*mk0)[i+j*(*NODES)]),
                  &((*pk0)[i+j*(*NODES)]),
                  &((*marea1)[i+j*(*NODES)]),
                  &((*parea1)[i+j*(*NODES)]),
                  &((*mtw1)[i+j*(*NODES)]),
                  &((*ptw1)[i+j*(*NODES)]),
                  &((*mk1)[i+j*(*NODES)]),
                  &((*pk1)[i+j*(*NODES)]),
                  &((*chn_dep)[i+j*(*NODES)]),
                  &((*bel)[i+j*(*NODES)]));
            }
         if((*ltype)[j]==8) /* READ IN BREAKPOINT X-SECT TAB.NUM & bel */
            {   
            fscanf(iunit,"%d %f",
                  &((*table_num)[i+j*(*NODES)]),
                  &((*bel)[i+j*(*NODES)]));
            }
         if((*ltype)[j]==9) 
            {
            fscanf(iunit,"%f %f %f %f %f %f\n",&mann,
		    &((*bottom)[i+j*(*NODES)]),
		    &((*chn_dep)[i+j*(*NODES)]),
		    &((*sslope)[i+j*(*NODES)]),
		    &((*sslope2)[i+j*(*NODES)]),
		    &((*bel)[i+j*(*NODES)]));
            }

     /* Commented out by BS 6-02-95, doesn't agree with lakes!
      *    
      *   if((*ltype)[j]==4 && i>=2)
      *      {
      *      fscanf(iunit,"%f %f\n",&((*strick)[i+j*(*NODES)]),
      *             &((*bottom)[i+j*(*NODES)]));
      *      continue;
      *      }
      */

       /* Added by BS 6-02-95  */

         if((*ltype)[j]==4)
           {
           fscanf(iunit,"%f %f %f %f %f\n", &((*strick)[i+j*(*NODES)]),
                  &((*bottom)[i+j*(*NODES)]),&((*chn_dep)[i+j*(*NODES)]),
                  &((*sslope)[i+j*(*NODES)]),&((*bel)[i+j*(*NODES)]));
           }
  
	 if(((*ltype)[j]==1)||((*ltype)[j]==2)||((*ltype)[j]==3))
            {
            fscanf(iunit,"%f %f %f %f %f\n",&mann,
                         &((*bottom)[i+j*(*NODES)]),
	                 &((*chn_dep)[i+j*(*NODES)]),
                         &((*sslope)[i+j*(*NODES)]),&((*bel)[i+j*(*NODES)]));
            }
         /*  FLUVIAL LINK   */
         if((*ltype)[j]==1) (*strick)[i+j*(*NODES)]=1.0/mann;

         /* FLUVIAL MULTIPLE SIDE SLOPE LINK   */
         if((*ltype)[j]==9) (*strick)[i+j*(*NODES)]=1.0/mann;

         /*  WEIR LINK     */
         if((*ltype)[j]==2) (*strick)[i+j*(*NODES)]=mann;

         /*  LAKE LINK     */
         /* comented out by BS 06-02-95
	  * if((*ltype)[j]==4 && (*nx1)[j]==1)  (*strick)[i+j*(*NODES)]=mann;
          */

         /*  CULVERT       */
	 if((*ltype)[j]==3)  (*strick)[i+j*(*NODES)]=mann;

         /* This line was moved from after node loop closing bracket to here, BS*/
         if((*bel)[1+j*(*NODES)]>(*highspot)) *highspot=(*bel)[1+j*(*NODES)];

         }
      }
   *highspot=(*highspot)+14.9;
   /* why 14.9?  It works. FLO 10-26-94*/

/*  ASSUME THE LOW SPOT IN THE NETWORK IS THE BED ELEVATION AT THE OUTLET */
   ii=(*nx1)[(*nlinks)];
   *lowspot=(*bel)[ii+(*nlinks)*(*NODES)]; 

/*       WEIR LINK
 *       notes:
 *       for node #1:
 *            strick=free flowing (forward direction) weir coefficient
 *            bottom=flooded condition (reverse direction) weir coefficient
 *            chn_dep=maximum in-bank height (channel depth), meters
 *            sslope=crest length, meters
 *            bel=elevation of weir crest, meters
 *       for node #2: 
 *            strick, bottom, chn_dep, sslope=0 (for future expansion)
 *            bel=bed elevation, meters
 */

/*    
 *    SET THE NUMBER OF NODES FOR LAKE LINKS BACK TO ONE
 *    UNTIL THE SECOND NODE ENTRY FOR LAKES MEAN SOMETHING. BS 6-13-95
 */

   if((*numqpipe=(int*) malloc(*LINKS*sizeof(int))) == NULL)
      {
      fprintf(stderr,"cannot allocate memory for numqpipe array");
      exit(-2);
      }

   for(j=1;j<=*nlinks;j++)
      {
      (*numqpipe)[j]=0;
      if((*ltype)[j]==4 && (*nx1)[j]>1)  
         {
         (*numqpipe)[j]=(*nx1)[j]-1;
         (*nx1)[j]=1;                  /* # of nodes per lake links is
                                        * set back to one. So in qprof
                                        * and yprof we need only one entry.
                                        */
         }
      }

/*
 *    INITIALIZE THE DEPTHS
 */
   for(j=1;j<=(*nlinks);j++)
      {
      for(i=1;i<=(*nx1)[j];i++)
         {
         if(!yes_drain && !yes_bkwater)
            {
            fscanf(yunit,"%d %d %f\n",&itmp,&jtmp,&((*yp)[i+j*(*NODES)]));
            fscanf(qunit,"%d %d %f\n",&itmp,&jtmp,&((*qp)[i+j*(*NODES)]));
            if((*ltype)[j]!=4) 
              (*yp)[i+j*(*NODES)]=(*yp)[i+j*(*NODES)]+(*bel)[i+j*(*NODES)];
            }
         else
            {
            (*yp)[i+j*(*NODES)]=*highspot;
            }
         }
      }
/*
 *  INITIALIZE THE DISCHARGES IF DRAINING (FLO 10-28-94)
 */
   if(yes_drain || yes_bkwater)
      { 
      for(j=1;j<=*nlinks;j++)
         {
         for(i=1;i<=(*nx1)[j];i++)
            {
            if((*ndep)[j]==0) /* this is a first order link */
               {
               (*qp)[i+j*(*NODES)]=(*qmin);
               }
            if((*ndep)[j]==1) /* there is one upstream link, match Q's */
               {
               if(i==1)
                  {
                  jj=(*depend)[j+1*(*LINKS)];
                  ii=(*nx1)[jj];
                  Qa=(*qp)[ii+jj*(*NODES)];
                  } 
               (*qp)[i+j*(*NODES)]=Qa;
               }
            if((*ndep)[j]==2) /* there are two upstream links, sum Q's */
               {
               if(i==1)
                  {
                  jj=(*depend)[j+1*(*LINKS)];
                  ii=(*nx1)[jj];
                  Qa=(*qp)[ii+jj*(*NODES)];

                  jj=(*depend)[j+2*(*LINKS)];
                  ii=(*nx1)[jj];
                  Qa+=(*qp)[ii+jj*(*NODES)];
                  }
               (*qp)[i+j*(*NODES)]=Qa;
               }
            }
         }
      }
   return;
}
