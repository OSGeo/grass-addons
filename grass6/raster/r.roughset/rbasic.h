
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

/***                   BASIC QUERRIES FOR SYSTEM                           ***/

/***                                                                       ***/

/*** part of the RSL system written by M.Gawrys J.Sienkiewicz              ***/

/***                                                                       ***/

/*****************************************************************************/


/* If a function from this section value a set, this set should be */
/* first initialized and then given to the function as a first     */
/* argument. Functions from this group does not work on matrix X.  */

int LowAppr(setO appr, setO X, setA P, int matrix_type);
int LowApprA(setO appr, setO X, setA P);
int LowApprD(setO appr, setO X, setA P);

	/* P-lower approximation of X */

int UppAppr(setO appr, setO X, setA P, int matrix_type);
int UppApprA(setO appr, setO X, setA P);
int UppApprD(setO appr, setO X, setA P);

	/* P-upper appriximation of X */

int Bound(setO bound, setO X, setA P, int matrix_type);
int BoundA(setO bound, setO X, setA P);
int BoundD(setO bound, setO X, setA P);

	/* P-boundary of X */

float AccurCoef(setO X, setA P, int matrix_type);
float AccurCoefA(setO X, setA P);
float AccurCoefD(setO X, setA P);

	/* Accuracy coefficient of X with respect to P */

float ClassCoef(setO X, setA P, int matrix_type);
float ClassCoefA(setO X, setA P);
float ClassCoefD(setO X, setA P);

	/* quality of classification (X,not X) */
	/* with respect to P */

int Pos(setO pos, setA P, setA Q, int matrix_type);
int PosA(setO pos, setA P, setA Q);
int PosD(setO pos, setA P, setA Q);

	/* P-positive region of Q */

float DependCoef(setA P, setA Q, int matrix_type);
float DependCoefA(setA P, setA Q);
float DependCoefD(setA P, setA Q);

	/* degree of dependency Q from P */

float SignifCoef(int attr, setA P, int matrix_type);
float SignifCoefA(int attr, setA P);
float SignifCoefD(int attr, setA P);

	/* significance of attribute attr  */
	/* in the set P */

float SignifRelCoef(int attr, setA P, setA Q, int matrix_type);
float SignifRelCoefA(int attr, setA P, setA Q);
float SignifRelCoefD(int attr, setA P, setA Q);

	/* significance of attribute attr */
	/* in the set P, relatively to Q */


int CardCoef(setA P, int matrix_type);

	/* returns number of matrix fields */
	/* covered by P (MATA is treated as MATD) */
	/* but elements are evaluated "on-line" */
