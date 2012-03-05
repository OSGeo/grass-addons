#ifndef BOOL
	typedef unsigned short BOOL;
#endif

#ifndef TRUE
	#define TRUE 1
#endif

#ifndef FALSE 
	#define FALSE 0
#endif

#ifndef ON
	#define ON 1
#endif

#ifndef OFF
	#define OFF 0
#endif

#ifndef STATE
	typedef BOOL STATE;
#endif

#ifndef Uint
	typedef unsigned int Uint;
#endif

#ifndef Ushort
	typedef unsigned short Ushort;
#endif

#ifndef Ulong
	typedef unsigned long Ulong;
#endif

#ifndef YES
	#define YES 1
#endif

#ifndef NO
	#define NO 0
#endif


#define MALLOC_ERROR 1
#define FILE_OPEN_ERROR 2

#ifndef BIG_NUM
	#define BIG_NUM 1000000
#endif

/* global variables (yuck!) */
#ifdef LOCAL
#define EXTERN
#else
#define EXTERN extern
#endif

#include <stdio.h>

#define PROGVERSION 1.5

#define CONST_MODE 0
#define RAST_MODE 1
#define VECT_MODE 2
#define SITE_MODE 3

/* possible DST values to output */

#define NUMVALS 10 /* how many different DST values have we got? */

#define BEL 0
#define PL 1
#define DOUBT 2
#define COMMON 3
#define BINT 4
#define WOC 5
#define MAXBPA 6
#define MINBPA 7
#define MAXSRC 8
#define MINSRC 9

/* possible warnings for combining evidence */
#define WARN_NOT_ONE 1

EXTERN int NO_SINGLETONS; /* number of singleton hypotheses in Theta */
EXTERN int N; /* number of evidence maps to combine */

EXTERN int NULL_SIGNAL; /* set to 1 to signal a copy-thru */

EXTERN struct GModule *module;
EXTERN struct
{
	struct Option *file;
	struct Option *groups; /* combine all or selected groups (data sources) */
	struct Option *type; /* type of evidence to combine */
	struct Option *output; /* basename of output maps */
	struct Option *vals; /* which DST metrics to output */
	struct Option *hyps; /* which hypotheses to output */
	struct Option *logfile; /* file to store logging output */
	struct Option *warnings; /* name of site list to store locations of warnings */	
}
parm;

EXTERN struct
{
	struct Flag *norm;	/* used to switch off automatic normalisation of evidence */
	struct Flag *quiet; /* do not show progress display */
	struct Flag *append;	
}
flag;

EXTERN FILE *lp; /* this defines where program output goes to */
EXTERN FILE *warn; /* stores locations of warnings, if desired  */

EXTERN long ReadX, ReadY; /* current position to read from all raster evidence maps */

EXTERN long no_assigns;
