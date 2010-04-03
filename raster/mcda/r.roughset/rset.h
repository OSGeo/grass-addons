
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

/***       OPERATIONS ON SETS OF ATTRIBUTES AND OBJECTS                    ***/

/***                                                                       ***/

/*** part of the RSL system written by M.Gawrys J. Sienkiewicz             ***/

/***                                                                       ***/

/*****************************************************************************/


#include <stdarg.h>

extern cluster_type _mask[];
extern int _cluster_bytes;
extern int _cluster_bits;

setO InitEmptySetO(void);
setA InitEmptySetA(void);

	/* allocates memory for set and initializes it */
	/* as empty, returns allocated set */

setO InitFullSetO(void);
setO InitFullSetA(void);

	/* allocates memory for set and initializes it */
	/* as full, returns newly allocated set */

void TabToSetO(setO set, int num, int tab[]);
void TabToSetA(setA set, int num, int tab[]);

	/* sets a set with num elements of table tab */

void ArgToSetO(setO set, int num, ...);
void ArgToSetA(setA set, int num, ...);

	/* sets a set with num arguments of function */

void CloseSetO(setO set);
void CloseSetA(setA set);

	/* free memory used by set */

void OrSetO(setO or, setO s1, setO s2);
void OrSetA(setA or, setA s1, setA s2);

	/* puts union of s1 and s2 to or */

void AndSetO(setO and, setO s1, setO s2);
void AndSetA(setA and, setA s1, setA s2);

	/* puts product of s1 and s2 to and */

void DifSetO(setO dif, setO s1, setO s2);
void DifSetA(setA dif, setA s1, setA s2);

	/* puts complement of s1 in s2 to dif */

void NotSetO(setO not, setO set);
void NotSetA(setO not, setA set);

	/* puts a complement of set to not */

void ClearSetO(setO set);
void ClearSetA(setA set);

	/* clears set */

void FillSetO(setO set);
void FillSetA(setA set);

	/* fills set with domain */

int AddSetO(setO set, int obj);
int AddSetA(setA set, int attr);

	/* adds element to set */

int DelSetO(setO set, int obj);
int DelSetA(setA set, int attr);

	/* deletes element from set */

int InSetO(setO big, setO small);
int InSetA(setA big, setA small);

	/* return 1 if set big contains set small */
	/* otherwise returns 0 */

int ContSetO(setO set, int obj);
int ContSetA(setA set, int attr);

	/* returns 1 if set contains element */
	/* otherwise returns 0 */

int InterSetO(setO s1, setO s2);
int InterSetA(setA s1, setA s2);

	/* returns 1 if s1 and s2 have nonempty product */
	/* otherwise returns 0 */

int IsEmptySetO(setO set);
int IsEmptySetA(setA set);

	/* returns 1 if set is empty */
	/* otherwise returns 0 */

int CardSetO(setO set);
int CardSetA(setA set);

	/* returns cardinality of set */

void CopySetO(setO dest, setO source);
void CopySetA(setA dest, setO source);

	/* copy source to dest */

int CompSetO(setO set1, setO set2);
int CompSetA(setA set1, setA set2);

	/* returns 1 if set1 and set2 are identical */
	/* otherwise returns 0 */

int SizeSetO(void);
int SizeSetA(void);

	/* returns number of clusters in set representation */
	/* in the active system sizeof(cluster_type)=_cluster_bytes */

void AttrValSetO(setO set, int attr, value_type val);

	/* puts into set all object that have value val */
	/* on attribute attr */

int ClassSetO(setO aclass, int obj, setA Q);

	/* fills class with all object that have the same values */
	/* on all attributes from Q as the object obj, uses MATA */

void PrintSetO(setO set);
void PrintSetA(setA set);

	/* outputs set to screen */
