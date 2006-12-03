#include <stdlib.h>
#include <string.h>
#include <search.h>
#include <time.h>
#include "grass/gis.h"
#include "grass/Vect.h"
#include "grass/dgl.h"
#include "grass/dbmi.h"

typedef struct { /* collect lines in Strahler order */
	int  line;     /* line number */
	int  bsnid;     /* basin ID */
    int  sorder;     /* Strahler order */
} DBBUF;

typedef struct { /* visited nodes */
	int  node;	/* node number */
	int  degree;  /* valency */
	int  visited; /* is between 0 and degr(node) */
} NODEV;

typedef struct {	/* keep track of lowest leaf (=outlet) of each tree */
	double z;		/* z-value of leaf */
	int    leaf;		/* line-id of outlet leaf */
} OUTLETS;

/**
StrahForestToTrees returns number of trees
*/
int StrahForestToTrees( struct Map_info *In, struct Map_info *Out, DBBUF *dbbuf );
int StrahFindLeaves( struct Map_info *In, DBBUF *dbbuf, NODEV *nodev, int ntrees, int fdrast );
int StrahOrder( struct Map_info *In, DBBUF *dbbuf, NODEV *nodev );
int StrahWriteToFile( DBBUF *dbbuf, int nlines, FILE *txout );
int StrahGetDegr( struct Map_info *In, int node );
int StrahGetNodeLine( struct Map_info *In, int node, int d );
