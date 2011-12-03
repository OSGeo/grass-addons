
/****************************************************************************
 *
 * MODULE:       r.roughset
 * AUTHOR(S):    GRASS module authors ad Rough Set Library (RSL) maintain:
 *					G.Massei (g_massa@libero.it)-A.Boggia (boggia@unipg.it)		
 *				 Rough Set Library (RSL) ver. 2 original develop:
 *		         	M.Gawrys - J.Sienkiewicz 
 *
 * PURPOSE:      Geographics rough set analisys and knowledge discovery 
 *
 * COPYRIGHT:    (C) GRASS Development Team (2008)
 *
 *               This program is free software under the GNU General Public
 *   	    	 License (>=v2). Read the file COPYING that comes with GRASS
 *   	    	 for details.
 *
 *****************************************************************************/

/***                                                                       ***/

/***                 SYSTEM HANDLING FUNCTIONS                             ***/

/***                                                                       ***/

/*** part of the RSL system written by M.Gawrys J.Sienkiewicz              ***/

/***                                                                       ***/

/*****************************************************************************/

#include <stdio.h>

extern SYSTEM *_mainsys;

	/* active information system */

extern int _rerror;

	/* error code */

SYSTEM *InitEmptySys(void);

	/* allocates memory for a new system descriptor */
	/* and clears all parameters, no matrices connected */

void SetParameters(SYSTEM * sys, int objects_num, int attributes_num);

	/* puts system parameters to the system descriptor */

void ConnectDescr(SYSTEM * sys, void *descr, int size);

	/* connects additional description to the system descriptor */

void SetName(SYSTEM * sys, char *name);

	/* puts system name to the system descriptor */

int FileToSys(SYSTEM * sys, char *filename);

	/* imports system from the special format file */
	/* including parameters, desicripton and matrix A */
	/* other matrices are left uninitialed */

int SysToFile(SYSTEM * sys, char *filename);

	/* exports system descriptor, additional description */
	/* and matrix A to a special format file */

void ConnectA(SYSTEM * sys, value_type * buf);

	/* connects matrix A (it may be empty) with */
	/* the system descriptor */

void PutToA(SYSTEM * sys, int object, int attribute, value_type value);

	/* sets value to element of matrix A */

int FillAfromAscii(SYSTEM * sys, FILE * file);

	/* fills matrix A with the values from Ascii file */

int InitD(SYSTEM * sys);

	/* fills matrix D from A, allocates memory  */
	/* and connects it with the system descriptor */
	/* matrix A must already exist */

int InitX(SYSTEM * sys, setA P, setA Q, int matrix_type);

	/* fills matrix X, allocates memory for it and */
	/* connects it with the system descriptor */
	/* matrix_type indicates the source matrix */
	/* initialization is done with respect to Q from P */

int InitXforObject(SYSTEM * sys, int obj, setA P, setA Q, int matrix_type);

	/* works like InitX but considers only single column of MATD */

int InitXforObjects(SYSTEM * sys, setO objects, setA P, setA Q,
		    int matrix_type);
	/* works like InitX but concider only columns of MATD */
	/* belonging to objects */

int InitXforObjectFromClass(SYSTEM * sys, int obj, setA P, setO aclass,
			    int matrix_type);
	/* works like InitX, conciders only specified objects */
	/* initialization is done with respect to objects from */
	/* outside of aclass */

void UseSys(SYSTEM * sys);

	/* makes indicated system active, from now on */
	/* all query routines will operate only on it */

void CloseSys(SYSTEM * sys);

	/* frees memory allocated for all matrixes, */
	/* system descriptor and additional description */

void CloseMat(SYSTEM * sys, int matrix_type);

	/* disconnects matrix X from the system descriptor */
	/* and frees memory  */

void DisconMat(SYSTEM * sys, int matrix_type);

	/* disconnects matrix from the system descriptor */
	/* does not free memory */

unsigned int Asize(SYSTEM * sys);

	/* returns number of elements in matrix A */
	/* memory size = Asize * sizeof(value_type) */
	/* system parameters should be valued */

unsigned int Dsize(SYSTEM * sys);

	/* returns number of memory clusters for matrix D */
	/* memory size = Dsize * sizeof(cluster_type) */
	/* system parameters should be valued */

unsigned int Xsize(SYSTEM * sys);

	/* returns number of memory cluster used by matrix X */
	/* memory size = Xsize * sizeof(cluster_type) */
	/* matrix X should be generated */

unsigned int MatMemSize(SYSTEM * sys, int matrix_type);

	/* returns the size of memory used by specified matrix */

void *MatExist(SYSTEM * sys, int matrix_type);

	/* return specified matrix if exist */
	/* otherwise returns NULL */

int ObjectsNum(SYSTEM * sys);

	/* returns number of objects in the system */

int AttributesNum(SYSTEM * sys);

	/* returns number of attributes in the system */

void *Description(SYSTEM * sys);

	/* returns pointer to additional description */

char *SysName(SYSTEM * sys);

	/* returns system name */
