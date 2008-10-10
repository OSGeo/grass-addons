/************************************************************************
EXTRACT RULE FROM GEOGRAPHICS THEMES (Based on Rough Set Library 
     		written by M.Gawrys J.Sienkiewiczbrary )	  		

The RSL defines three types to be used in applications:
     setA - set of attributes,
     setO - set of objects and
     SYSTEM - information system descriptor.
					
The descriptor contains pointers to the information system data matrices:
- MATRIX A, is the attribute-value table.
- MATRIX D, is the discernibility matrix
- MATRIX X, is called a reduced discernibility matrix.
                          
/***********************************************************************/

#include "rough.h"
#include "localproto.h"



int RulsExtraction(char *name, struct input *attributes, int strgy);
void fPrintSetA( FILE *f, setA set );
void fPrintSetO( FILE *f, setO set );
void fPrintRules( FILE *file, value_type* rules, int N, int *opr, setA P, setA Q, struct input *attributes);
void fPrintToScript( FILE *file, value_type* rules, int N, int *opr, setA P, setA Q, struct input *attributes);
float MeanAttrInRule( value_type *rules, int N, setA P );
int LowRules( value_type **rules, setA P, setA Q, int mat );
int UppRules( value_type **rules, setA P, setA Q, int mat );
int NormRules( value_type **rules, setA P, setA Q, int mat );



int RulsExtraction(char *name,struct input *attributes, int strgy)  /*old MAIN*/
{
  SYSTEM *sys1, *sys2, *trainsys, *testsys; /* Information system descriptor structures. It contains information about the 							system parameters (number of objects, number of attributes, system name. */
  value_type *buf,*rules; /* stores a single value of attribute (used for attribute-value table and rule implementation)*/
  char c;
  int ob,at,at2,n,j,i,work=1,good,r;
  int *opr;
  setA beg,P,Q,full,core; /*set of attributes*/
  setO train;		  /*set of object*/
  FILE *file, *file2, *file3;
  int (*genrules)( value_type**, setA, setA, int );
  int p30, sample;
  clock_t time1, time2;
  int inf;
  char *nameFILE; /*storage root file names*/
   

  sys1=InitEmptySys();  /* Allocates memory for a system descriptor and returns a pointer.*/


  FileToSys(sys1,name); /* Imports a system from a file of the special format.*/
  
  
  if (_rerror>0) 
  	{  G_fatal_error("  Can't open data file \n");
  		return(1); }
  		
  	
  strcat(name,".out");
  
  if (!(file2=fopen(name,"a"))) 					/*output text file*/
  	{G_fatal_error("  Can't open output file \n");
  		return(1);}
  		
  strcat(name,".sh");  	
  	
  if (!(file3=fopen(name,"w"))) 					/*output mapcalc file*/
  	{G_fatal_error("  Can't open output file \n");	
  		return(1);}	
  	
  	
  UseSys(sys1); /* Activates a system. All routines will work on this indicated system data and parameters.*/
  full=InitFullSetA(); /*Initialize a full set. Allocates memory for a set and initialize it with all elements of
        		domain based on the active information system */
        		
  InitD(sys1); /*Generates MATRIX D from MATRIX A.Connected to sys and filled*/
   
  P=InitEmptySetA(); /* Initialize an empty set. Memory size determined by active information system parameters */
  Q=InitEmptySetA();
  

  
  /* define attribute */
  for(i=0;i<(AttributesNum(sys1)-1);i++)  
    { 
    	AddSetA(P,i); /* Adds a single element to a set */
    }
    
    
   /* define decision */
   AddSetA(Q,(AttributesNum(sys1)-1));
   
   
  /*printf("number of objects: %i \n",ObjectsNum(sys1)); 		Returns number of objects in a system*/
  /*printf("number of attributes: %i \n",AttributesNum(sys1));  Returns a number of attributes in a system.*/
  
    
  fprintf(file2,"Condition attributes are\n");   
        fPrintSetA(file2,P);
        PrintSetA(P);  /* Writes a formatted condition set to the standard output.Prints elements in brackets. */
  fprintf(file2,"\nDecision attributes are\n");   
        fPrintSetA(file2,Q);
        PrintSetA(Q);  /* Writes a formatted decision set to the standard output.Prints elements in brackets. */
  fprintf(file2,"\nDependCoef = %f\n",DependCoef(P,Q,MATD)); /* Returns degree of dependency Q from P in the active information system.*/

  InitX(sys1,P,Q,MATD); /*Generates MATRIX X from another matrix designed for use in core and reducts queries. */
  core=InitEmptySetA();
  Core(core,MATX); /* Puts a core of the active information system to core. */	
  fprintf(file2,"CORE = ");   
  fPrintSetA(file2,core);  
  RedOptim( core, MATX ); /* Provides the optimized heuristic search for a single reduct */
  fprintf(file2,"\nRedOptim = ");
  fPrintSetA(file2,core);
  CloseSetA(core);  /* Frees memory allocated for a set */
  n=RedFew(&beg,MATX); /*Finds all reducts shorter than the first one found.*/
  CloseMat(sys1,MATX); /* Closes a matrix. */

  fprintf( file2,"\nFew reducts ( %i ):\n", n );
  for (i=0;i<n;i++)
  { 
     fPrintSetA( file2, beg+i*sys1->setAsize );
     fprintf(file2,"\n");
  }
  if ( n>0 ) free( beg );





  fprintf(file2, "%d strategy of generating rules\n", strgy);
    
  switch ( strgy )
     {
	case 0: genrules = VeryFastRules;
	   break;
	case 1: genrules = FastRules;
	   break;
        case 2: genrules = Rules;  
	   break;
	case 3: genrules = BestRules;
	   break;
	case 4: genrules = AllRules;
	   break;
        case 5: genrules = LowRules;  
	   break;
	case 6: genrules = UppRules;
	   break;   
	default: genrules = NormRules;
	   break;
     }

/*****************************************************************************/
  time1 = clock();
  r = genrules ( &rules, P, Q, MATD );
  time2 = clock();
  if (r>0)
  {  fprintf(file2,"Time of generating rules = %ds\n", time2, (time2-time1)/CLOCKS_PER_SEC );
     opr = StrengthOfRules( rules, r ); /* Creates a table of rules strengths*/
     fprintf(file2,"Rules ( %i )\n", r );
     fPrintRules( file2, rules, r, opr, P, Q, attributes ); /*print to file generated rules*/
     fPrintToScript( file3, rules, r, opr, P, Q, attributes );/*build mapcalc file*/
     fprintf(file2,"Mean number of attributes in rule = %.1f\n",MeanAttrInRule( rules, r, P ));
     free( rules );
     free( opr );
  }
/******************************************************************************/
  
  
  CloseSetA(P);
  CloseSetA(Q);
  CloseSetA(full);
  CloseSys(sys1);
  fclose(file2);
  fclose(file3);
  G_message("O.K. output placed to files");
  return (0);
}


void fPrintSetA( FILE *f, setA set )
{  int attr;
   fprintf(f,"{");
   for (attr=0; attr<_mainsys->attributes_num ;attr++)
      if (ContSetA(set,attr))
      {  fprintf(f," %d",attr);
	 attr++;
	 break;
      }
   for (; attr<_mainsys->attributes_num ;attr++)
      if (ContSetA(set,attr)) fprintf(f,",%d",attr);
   fprintf(f," }");
}

void fPrintSetO( FILE *f, setO set )
{  int obj;
   fprintf(f,"{");
   for (obj=0; obj<_mainsys->objects_num ;obj++)
      if (ContSetO(set,obj))
      {  fprintf(f," %d",obj);
	 obj++;
	 break;
      }
   for (; obj<_mainsys->objects_num ;obj++)
      if (ContSetO(set,obj)) fprintf(f,",%d",obj);
   fprintf(f," }");
}

void fPrintRules( FILE *file, value_type* rules,
		 int N, int *opr, setA P, setA Q, struct input *attributes  )
{  int n,j;
   
   for (n=0;n<N;n++) 
   {  for (j=0;j<_mainsys->attributes_num;j++)
	 if ( ContSetA( P,j ) )
	   if (rules[n*_mainsys->attributes_num+j]!=MINUS)
	       fprintf(file,"%s=%d  ", attributes[j].name,rules[n*_mainsys->attributes_num+j]);
      fprintf(file," => ");
      for (j=0;j<_mainsys->attributes_num;j++)
	 if ( ContSetA( Q, j ) )
	   if ((rules+n*_mainsys->attributes_num)[j]!=MINUS)
	     fprintf(file,"%s=%d  ", attributes[j].name,(rules+n*_mainsys->attributes_num)[j]);
      fprintf(file," ( %i objects )\n", opr[n] );
   }
   return;
}


void fPrintToScript( FILE *file, value_type* rules, int N, int *opr, setA P, setA Q, struct input *attributes )
{  
	int n,j,i;
   fprintf(file,"#!/bin/bash\nRASTERrule=${1}\nif [ $# -ne 1 ]; then\n\techo 'Output file named roughmap, "
				"Consider renaming'\n\tRASTERrule=roughmap\nfi\n");
   	for (n=0;n<N;n++) 
   	{  
   	  	i=0;
   	  	for (j=0;j<_mainsys->attributes_num;j++)
   	  		{
	 		if ( ContSetA( P,j ) ) /*Tests if a set contains an element*/
	   			if (rules[n*_mainsys->attributes_num+j]!=MINUS) /*Missing values are coded by MINUS*/
	   				{
	   				if(i==0) /*if the role is only one or the firsth ...*/
	   					fprintf(file,"r.mapcalc 'maprule%d=if(%s==%d",n,attributes[j].name,rules[n*_mainsys->attributes_num+j]);
	   				else /*... otherwise ...*/
	   					fprintf(file," && %s==%d",attributes[j].name,rules[n*_mainsys->attributes_num+j]);
	   				i++;
	   				}   		
	   		}	   			
      	for (j=0;j<_mainsys->attributes_num;j++)
	 		if ( ContSetA( Q,j ) ) /*Tests if a set contains an element*/
	   			if ((rules+n*_mainsys->attributes_num)[j]!=MINUS) /*Missing values are coded by MINUS*/
	     			fprintf(file,",%d,null())'\n",(rules+n*_mainsys->attributes_num)[j]);
   	}

	
   	fprintf(file,"\nr.patch --overwrite input=");
   	for (n=0;n<N;n++) 
   		{
   			fprintf(file,"maprule%d",n);
   			if(n<N-1)	{fprintf(file,",");}
   		}
   	fprintf(file," output=$RASTERrule");
   		
   	fprintf(file,"\ng.remove rast=");
   	for (n=0;n<N;n++) 
   		{
   			fprintf(file,"maprule%d",n);
   			if(n<N-1)	{fprintf(file,",");}
   		}	
		
	fprintf(file,"\nr.colors map=$RASTERrule color=ryg ");

   	return;
}

/*
void fPrintToScript( FILE *file, value_type* rules,
		 int N, int *opr, setA P, setA Q, struct input *attributes )
{  int n,j,i;
   
   fprintf(file,"roughmap=");
   for (n=0;n<N;n++) 
   {  
   	  i=0;
   	  for (j=0;j<_mainsys->attributes_num;j++)
   	  	{
	 	if ( ContSetA( P,j ) ) 
	   		if (rules[n*_mainsys->attributes_num+j]!=MINUS) 
	   			{
	   			if(i==0) 
	   				fprintf(file,"if(%s==%d",attributes[j].name,rules[n*_mainsys->attributes_num+j]);
	   			else 
	   				fprintf(file," && %s==%d",attributes[j].name,rules[n*_mainsys->attributes_num+j]);
	   			i++;
	   			}
	   		
	   	}
	   			
      for (j=0;j<_mainsys->attributes_num;j++)
	 	if ( ContSetA( Q,j ) ) 
	   		if ((rules+n*_mainsys->attributes_num)[j]!=MINUS) 
	     		fprintf(file,",%d)",(rules+n*_mainsys->attributes_num)[j]);
      if(n<N-1)
	 fprintf(file,"\\ \n + ");
   }
	   			
   fprintf(file,"\nend\n");
   return;
}
*/

   
float MeanAttrInRule( value_type *rules, int N, setA P )
{  int counter=0;
   int i,j;
   int size=_mainsys->attributes_num;
   for (i=0; i<N; i++)
      for (j=0; j<size; j++)
	 if ( ContSetA( P, j ) )
	    if ( (rules+i*size)[j]!=MINUS ) counter++;
   return (float)counter/N;
}

int LowRules( value_type **rules, setA P, setA Q, int mat )
{
   return ApprRules( rules, P, Q, LOWER, mat );
}

int UppRules( value_type **rules, setA P, setA Q, int mat )
{
  return ApprRules( rules, P, Q, UPPER, mat );
}

int NormRules( value_type **rules, setA P, setA Q, int mat )
{
  return ApprRules( rules, P, Q, NORMAL, mat );
}


   


