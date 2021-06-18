/* This function is contributed by Bill Voss.    */

#include "all.h"

/*!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!*/
void 
READ_GAGE_FILE (
/*!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!*/

/*
  READ_RAINGAGE_FILE 
  takes
      rgint -- pointer to an array of double's
      nrg -- the number of values which may be stored in rgint 
      rain_fd -- file to read the line of data from.

  CAUTION: If there are more than nrg numbers on a line
           the excess numbers are silently ignored.
*/
    double *rgint,
    int nrg,
    FILE *rain_fd
)

{

#define BUFFER_SIZE 2000
#define LAST_ELEMENT (BUFFER_SIZE - 1)

  char *ptr, buffer[BUFFER_SIZE];
  int return_value=0;

  buffer[LAST_ELEMENT - 1] = '\000';  /* We will need to detect if we
					 over-ran our buffer, and thus need
					 to read again. */

  if (!((fgets(buffer,BUFFER_SIZE,rain_fd)))) {
  if (! buffer) {
    fprintf(stderr,"An input error occured or EOF was reached on an fgets call in %s at line %d\n",__FILE__,__LINE__);
    exit(1);
    }
  }

  /* We really should recover, instead of giving up here */
  if (buffer[LAST_ELEMENT - 1] != '\000') {
    fprintf(stderr,"Our fixed sized buffer was not big enough, we're sorry in %s at line %d\n",__FILE__,__LINE__);
    exit(1);
  }

/* PSEUDO-CODE:

  ptr = buffer;
  ptr gets scanned past whitespace;
  while not_done 
    sscanf of non-whitespace pointer points at;
    ptr gets scanned past what sscanf just looked at, and any white space;
*/

  ptr = strtok(buffer," \t");  /* Token Seperators are SPACE and TAB */
  while (ptr /* We have something to read */
	 && (return_value < nrg) /* We have more storage space */
 	 && (sscanf(ptr,"%lf",&rgint[return_value]) == 1)) /* We read A value */
    {
      return_value++;
      ptr = strtok(NULL," \t");
    }

  return;
}

