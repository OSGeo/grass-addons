#include <stdlib.h>
#include <string.h>
#include <search.h>
#include <time.h>
#include "grass/gis.h"
#include "grass/Vect.h"
#include "grass/dgl.h"
#include "grass/dbmi.h"

/*! \typedef DBBUF
   \brief Buffer to keep track of assigned tree and Strahler order for each line
 */

/*! \typedef NODEV
   \brief Buffer to keep track of valency for each node
 */

/*! \typedef OUTLETS
   \brief Buffer to determine lowest leaf of each tree
 */

typedef struct
{				/* collect lines in Strahler order */
    int category;
    int line;			/* line number */
    int bsnid;			/* basin ID */
    int sorder;			/* Strahler order */
} DBBUF;

typedef struct
{				/* visited nodes */
    int node;			/* node number */
    int degree;			/* valency */
    int visited;		/* is between 0 and degr(node) */
} NODEV;

typedef struct
{				/* keep track of lowest leaf (=outlet) of each tree */
    double z;			/* z-value of leaf */
    int leaf;			/* line-id of outlet leaf */
} OUTLETS;

/* in forest2tree.c */
/*! \fn int StrahForestToTrees( struct Map_info *In, struct Map_info *Out, DBBUF *dbbuf );
   \brief Returns the number of trees in *In
   \param *In The input map
   \param *Out The output map
   \param *dbbuf The buffer table for line orders
 */


/* in strahler.c */
/*! \fn int StrahFindLeaves( struct Map_info *In, DBBUF *dbbuf, NODEV *nodev, int ntrees, int fdrast );
   \brief Identifies all leaves of each tree and the one that lies lowest
   \param *In The input map
   \param *dbbuf The buffer table for line orders
   \param *nodev The buffer table for node valency
   \param ntrees Number of trees in map
   \param fdrast File descriptor of DEM raster map
 */

/*! \fn int StrahOrder( struct Map_info *In, DBBUF *dbbuf, NODEV *nodev );
   \brief Calculates the Strahler order of each line
   \param *In The input map
   \param *dbbuf The buffer table for line orders
   \param *nodev The buffer table for node valency
 */


/* in write.c */
/*! \fn int StrahWriteToFile( DBBUF *dbbuf, int nlines, FILE *txout );
   \brief Writes ASCII representation of calculated order to file
   \param *dbbuf The buffer table for line orders
   \param nlines Number of lines in *In map
   \param *txout ASCII output file name
 */


/* in helper.c */
/*! \fn int StrahGetDegr( struct Map_info *In, int node );
   \brief Get degree of node (for sloppy mode)
   \param *In The input map
   \param node Node number in *In
 */

/*! \fn int StrahNodeLine( struct Map_info *In, int node, int d );
   \brief Get lines connected in node (for sloppy mode)
   \param *In The input map
   \param node Node number in *In
   \param d n-th line connected to node
 */

int StrahForestToTrees(struct Map_info *In, struct Map_info *Out,
		       DBBUF * dbbuf);
int StrahFindLeaves(struct Map_info *In, DBBUF * dbbuf, NODEV * nodev,
		    int ntrees, int fdrast);
int StrahOrder(struct Map_info *In, DBBUF * dbbuf, NODEV * nodev);
int StrahWriteToFile(DBBUF * dbbuf, int nlines, FILE * txout);
int StrahGetDegr(struct Map_info *In, int node);
int StrahGetNodeLine(struct Map_info *In, int node, int d);
