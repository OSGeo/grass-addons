#include "all.h"

/*******************************************************************/
void read_table (

/*-----------------------------------------------------------------------
    Fred L. Ogden, UCONN 10-8-94.

    This subroutine reads in table breakpoint cross-section data if
    this data is present (link type 8).

    The following variables are passed to this subroutine:
     
       tunit:  The file pointer to the input table file.

    The following variables are read by this subroutine:

       maxtab: The number of tables in the file. scalar.
       ht_spc: The vertical distance between hydraulic property 
               values.  1-D array of size NUMTBL.
       xarea:  2-D array of cross-sectional area of dimension
               [NUMBPTS][NUMTBL]
       xtw:    2-D array of cross-sectional top-width of dimension
               [NUMBPTS][NUMTBL]
       xk:     2-D array of cross-sectional conveyance of dimension
               [NUMBPTS][NUMTBL] 
       numhts: 1-D array of dimension [NUMTBL] which contains the 
               number of discrete heights (rows in table) for each
               cross-section.

       NUMTBL: The max. dimension of number of tables.
       NUMBPTS: The max. number of table entries (heights)
                per cross-section. 
       TBNUM:    Maximum array dimension for 2-D table data.
------------------------------------------------------------------------*/
    FILE *tunit,
    int *NUMTBL,
    int *NUMBPTS,
    int *TBNUM,
    float **xarea,
    float **xtw,
    float **xk,
    int **numhts,
    float **ht_spc,
    int *maxtab
)

{

/*
 *    LOCAL VARIABLES
 */
      float  ftmp,jnk1,jnk2,jnk3,jnk4;
      int    tnum,maxbpts,i,j;

      fscanf(tunit,"%d %d",maxtab,&maxbpts);

      (*NUMTBL)=(*maxtab)+1;
      (*NUMBPTS)=maxbpts+1;
      (*TBNUM)=(*NUMTBL)*(*NUMBPTS); 

/*
 *    MEMORY ALLOCATION 
 */
      
      if((*xarea=(float*) malloc(*TBNUM*sizeof(float))) == NULL) 
	{
	fprintf(stderr,"cannot allocate memory for xarea array");
	exit(-2);
	}
      if((*xtw=(float*) malloc(*TBNUM*sizeof(float))) == NULL) 
	{
	fprintf(stderr,"cannot allocate memory for xtw array");
	exit(-2);
	}
      if((*xk=(float*) malloc(*TBNUM*sizeof(float))) == NULL) 
	{
	fprintf(stderr,"cannot allocate memory for xk array");
	exit(-2);
	}
      if((*numhts=(int*) malloc((*NUMTBL)*sizeof(int))) == NULL) 
	{
	fprintf(stderr,"cannot allocate memory for numhts array");
	exit(-2);
	}
      if((*ht_spc=(float*) malloc(*NUMTBL*sizeof(float))) == NULL) 
	{
	fprintf(stderr,"cannot allocate memory for ht_spc array");
	exit(-2);
	}

      for(j=1;j<=(*maxtab);j++)
         {
         fscanf(tunit,"%d",&tnum);
         fscanf(tunit,"%d %f",&((*numhts)[j]),&((*ht_spc)[j]));
         for(i=0;i<(*numhts)[j];i++)
            {
            if(i==0) /* don't save first row, it is trivial {0 0 0 0} */
               {
               fscanf(tunit,"%f %f %f %f",&jnk1,&jnk2,&jnk3,&jnk4);
               }
            else /* save the area, topwidth, and conveyance values */
               { 
               fscanf(  tunit,"%f %f %f %f",&ftmp,
                             &((*xarea)[i+j*(*NUMBPTS)]),
                               &((*xtw)[i+j*(*NUMBPTS)]),
                                &((*xk)[i+j*(*NUMBPTS)])  ); 
               }
            }
         (*numhts)[j]--; /* we didn't save the first row, so decrement numhts */
         }
      return;
}
