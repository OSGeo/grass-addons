#ifndef GLOBAL_H
#define GLOBAL_H

#define PROGVERSION 0.55
#define PROGNAME    "r.vol.dem"

/* if DEBUG > 1 we will dump even more details */
#define DEBUG       0

/* NULL valued cells */
#define NULLVALUE   -1
/* masked cells */
#define MASKVALUE   -2
/* unset cells */
#define UNSET       -3

/* value to represent NULL in VTK files */
#define DNULLVALUE  -99999.99

#define TMPFILE     "voxeltmp.tmp"

#ifdef MAIN
/* number of decimal places with which coordinates are stored */
double PRECISION;

/* verbose output includes progress display */
int VERBOSE;

/* number of DEMs in the input */
int NSLICES;

#else

extern double PRECISION;
extern int VERBOSE;
extern int NSLICES;

#endif /* MAIN */

#endif /* GLOBAL_H */
