
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

/***              SOME MORE QUERIES FOR SYSTEM                             ***/

/***          ( FINDING CORES AND CHECKING REDUCTS )                       ***/

/***                                                                       ***/

/*** part of the RSL system written by M.Gawrys J.Sienkiewicz              ***/

/***                                                                       ***/

/*****************************************************************************/



int Core(setA core, int matrix_type);
int CoreA(setA core);
int CoreDX(setA core, int matrix_type);

	/* finds a core of all attributes */

int CoreRel(setA core, setA P, setA Q, int matrix_type);
int CoreRelA(setA core, setA P, setA Q);
int CoreRelD(setA core, setA P, setA Q);

	/* finds a core of P relativly to Q */

int IsOrtho(setA red, setA over, int matrix_type);

	/* return 1 if red is orthogonal */
	/* otherwise returns 0 */

int IsOrthoRel(setA red, setA over, setA P, setA Q, int matrix_type);

	/* return 1 if red is Q-orthogonal in P */
	/* otherwise returns 0 */

int IsCover(setA red, int matrix_type);
int IsCoverA(setA red);
int IsCoverDX(setA red, int matrix_type);

	/* return 1 if red is a cover */
	/* otherwise returns 0 */

int IsCoverRel(setA red, setA P, setA Q, int matrix_type);
int IsCoverRelA(setA red, setA P, setA Q);
int IsCoverRelD(setA red, setA P, setA Q);

	/* return 1 if red is Q-cover in P */
	/* otherwise returns 0 */

int IsRed(setA red, int matrix_type);

	/* returns 1 if red is a reduct */
	/* otherwise returns 0 */

int IsRedRel(setA red, setA P, setA Q, int matrix_type);

	/* returns 1 if red is a Q-relative reduct of P */
	/* otherwise returns 0 */
