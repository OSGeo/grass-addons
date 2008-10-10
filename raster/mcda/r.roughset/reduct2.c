/*******************************************************************/
/*******************************************************************/
/***                                                             ***/
/***               SOME MORE QUERIES FOR SYSTEM                  ***/
/***              ( AUXILIARY  REDUCTS ROUTINES )                ***/
/***                                                             ***/
/***  part of the RSL system written by M.Gawrys J.Sienkiewicz   ***/
/***                                                             ***/
/*******************************************************************/
/*******************************************************************/

#include <stdlib.h>
#include "rough.h"

int RedSingle( setA red, int matrix_type)
 {
    int i;
    int cont=1;
    setA over;
    over = InitEmptySetA();
    Core( red, matrix_type );
    for (i=0;(i<_mainsys->attributes_num)&&cont;i++)
       if ( IsCover( red, matrix_type ) ) cont=0;
       else  AddSetA( red, i );
    cont=1;
    while(cont)
       if ( IsOrtho( red, over, matrix_type ) ) cont=0;
       else
	  for (i=0;i<_mainsys->attributes_num;i++)
	     if (ContSetA( over, i )) 
	        { DelSetA( red, i ); break; }
    CloseSetA( over );
    return 1;
 }
 
int RedRelSingle( setA red, setA P, setA Q, int matrix_type)
{ int i;
  int cont=1;
  setA over;
  over = InitEmptySetA();
  CoreRel( red, P, Q, matrix_type );
  for (i=0;(i<_mainsys->attributes_num)&&cont;i++)
   {
     if ( IsCoverRel( red, P, Q, matrix_type ) ) cont=0;
     else  AddSetA( red, i );
   }
  cont=1;
  while(cont)
   {
     if ( IsOrthoRel( red, over, P, Q, matrix_type ) ) cont=0;
     else
       for (i=0;i<_mainsys->attributes_num;i++)
         if (ContSetA( over, i )) { DelSetA( red, i ); break; }
   }
  CloseSetA( over );
  return 1;
}



int RedOptim( setA red, int matrix_type)
{ int max, f, fmax;
  int i, atr;
  int cont=1;
  setA over;

  over = InitFullSetA();
  Core( red, matrix_type );
  fmax = CardCoef( over, matrix_type );
  max = CardCoef( red, matrix_type );
  while ( max < fmax )
   { for( i=0; i<_mainsys->attributes_num; i++ )
       if ( !ContSetA( red, i) )
	{ AddSetA( red, i );
	   f = CardCoef( red, matrix_type );
	   if ( f >= max ) max = f, atr = i;
	   DelSetA( red, i );
	}
     AddSetA( red, atr );
   }
  cont=1;
  while( cont )
   { if ( IsOrtho( red, over, matrix_type ) ) cont=0;
     else
      for( i=0; i<_mainsys->attributes_num; i++ )
	if ( ContSetA( over, i ) ) 
	 { DelSetA( red, i ); break; }
   }
  CloseSetA( over );
  return 1;
 }

int RedRelOptim( setA red, setA P, setA Q, int matrix_type)
 { float max, f, fmax;
   int i, atr;
   int cont=1;
   setA over;
   over = InitEmptySetA();
   CoreRel( red, P, Q, matrix_type );
   fmax = DependCoef( P, Q, matrix_type );
   while (cont)
    { max = 0;
      for (i=0;i<_mainsys->attributes_num;i++)
	if (ContSetA( P, i ) && !ContSetA( red, i))
	 { AddSetA( red, i );
	   f = DependCoef( red, Q, matrix_type );
	   if ( f >= max ) max = f, atr = i;
	   DelSetA( red, i );
	 }
     AddSetA( red, atr );
     if ( max==fmax ) cont=0;
    }
   cont=1;
   while(cont)
    { if ( IsOrthoRel( red, over, P, Q, matrix_type ) ) cont=0;
      else
	for (i=0;i<_mainsys->attributes_num;i++)
	   if (ContSetA( over, i )) { DelSetA( red, i ); break; }
    }
   CloseSetA( over );
   return 1;
 }
 
int RedFew( setA *reds, int matrix_type)
 { setA r;
   int n;
   r = InitEmptySetA();
   RedSingle( r, matrix_type );
   n = RedLess( reds, CardSetA(r), matrix_type );
   CloseSetA( r );
   return n;
 }

int RedRelFew( setA *reds, setA P, setA Q, int matrix_type)
 { setA r;
   int n;
   r = InitEmptySetA();
   RedRelSingle( r, P, Q, matrix_type );
   n = RedRelLess( reds, P, Q, CardSetA(r), matrix_type );
   CloseSetA( r );
   return n;
 }
 
int SelectOneShort( setA reds, int N )
 { int min, m, i, num=0;
   min = _mainsys->attributes_num;
   for( i=0,START_OF_MAT(reds,N); END_OF_MAT; i++,NEXT_OF_MAT )
     if ( min > (m=CardSetA( ELEM_OF_MAT )) )
       min = m, num = i;
  return num;
 }

int SelectAllShort( setA *newreds, setA reds, int N)
 { int num, m, min;
   int size = _mainsys->setAsize;
   min = _mainsys->attributes_num+1;
   *newreds = (cluster_type *)malloc( N*size*_cluster_bytes );
   for( START_OF_MAT(reds,N); END_OF_MAT; NEXT_OF_MAT )
     if ( min > (m=CardSetA( ELEM_OF_MAT )) )
      {  min = m;
         num = 0;
         CopySetA( *newreds+num*size, ELEM_OF_MAT );
      }
     else if ( min==m )
      {  num++;
         CopySetA( *newreds+num*size, ELEM_OF_MAT );
      }
   *newreds = (cluster_type *)realloc( *newreds, (num+1)*size*_cluster_bytes );
   if ( *newreds==0 ) num=-1;
   return num+1;
 }


