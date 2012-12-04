
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

/***              (AUXILIARY REDUCTS ROUTINES)                             ***/

/***                                                                       ***/

/*** part of the RSL system written by M.Gawrys J.Sienkiewicz              ***/

/***                                                                       ***/

/*****************************************************************************/


int RedSingle(setA red, int matrix_type);

	/* heuristicly searches for a single reduct and stores it in red */

int RedRelSingle(setA red, setA P, setA Q, int matrix_type);

	/* heuristicly searches for a single Q-relative reduct of P */
	/* and stores it in red */

int RedOptim(setA red, int matrix_type);

	/* heuristicly searches for a single reduct and stores it in red */
	/* dependency coefficient is used to select */
	/* attributes for search optimization */

int RedRelOptim(setA red, setA P, setA Q, int matrix_type);

	/* heuristicly searches for a single Q-relative reduct of P */
	/* and stores it in red; dependency coefficient is used to select */
	/* attributes for search optimization */

int RedFew(setA * reds, int matrix_type);

	/* finds all reducts shortesest or equal in size to the first */
	/* reduct found by the heuristic algorithm */

int RedRelFew(setA * reds, setA P, setA Q, int matrix_type);

	/* finds all Q-relative P-reducts shortesest or equal in size */
	/* to the first reduct found by the heuristic algorithm */

int SelectOneShort(setA reds, int num);

	/* returns index of the single shortest reduct */
	/* from the table of num reducts pointed by reds */

int SelectAllShort(setA * newreds, setA reds, int num);

	/* copies all the shortest reducts */
	/* from the table of num reducts pointed by reds */
