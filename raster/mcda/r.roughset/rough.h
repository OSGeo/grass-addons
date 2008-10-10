/*******************************************************************/
/*******************************************************************/
/***                                                             ***/
/***       OBLIGATORY FILE TO INCLUDE IN APPLICATION SOURCE      ***/
/***             (DATA TYPES, CONSTANTS AND HEADERS)	         ***/
/***                                                             ***/
/***  part of the RSL system written by M.Gawrys J.Sienkiewicz   ***/
/***                                                             ***/
/*******************************************************************/
/*******************************************************************/

/********************* CONSTANTS AND TYPES *************************/

#define MATA 0
#define MATD 1
#define MATX 2

#define ERROR(a)     { _rerror=a; return -a; }

typedef unsigned int cluster_type;
typedef unsigned int value_type;
typedef cluster_type *setO;
typedef cluster_type *setA;

typedef struct {
       char     name[50];
       int      objects_num;
       int      attributes_num;
       int      descr_size;
       void    *description;
       int      setAsize;
       int      setOsize;
       value_type      *matA;
       cluster_type    *matD;
       cluster_type    *matX;
       unsigned int  matXsize;
 } SYSTEM;

/************** H-FILES CONTAINING DECLARATIONS OF FUNCTIONS *********/

#include "rset.h"
#include "rsystem.h"
#include "raccess.h"
#include "rbasic.h"
#include "rcore.h"
#include "reduct1.h"
#include "reduct2.h" 
#include "rule1.h"
#include "rule2.h"
#include "rclass.h"
