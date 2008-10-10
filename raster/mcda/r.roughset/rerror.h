/*******************************************************************/
/*******************************************************************/
/***                                                             ***/
/***         OPTIONAL ERROR HANDLING AND ERROR MESSAGES          ***/
/***                                                             ***/
/*** part of the RSL system written by M.Gawrys J. Sienkiewicz   ***/
/***                                                             ***/
/*******************************************************************/
/*******************************************************************/

char *errcodes[10]={   "everything O.K.",
		       "Cannot open file",
		       "Wrong format of file",
		       "Not enough memory",
		       "Cannot write to file",
		       "Matrix A not initialized",
		       "Matrix D not initialized",
		       "Matrix X not initialized",
		       "Wrong matrix type",
		       "Set element out of domain"
		   };

#define ErrorPrint() {printf("ERROR no: %i: %s\n",_rerror,errcodes[_rerror]);_rerror=0;}

