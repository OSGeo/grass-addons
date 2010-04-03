
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

/***               SOME MORE QUERIES FOR SYSTEM                            ***/

/***                     ( CLASSIFICATION )                                ***/

/***                                                                       ***/

/***  part of the RSL system written by M.Gawrys J.Sienkiewicz             ***/

/***                                                                       ***/

/*****************************************************************************/


int DecisionEQ(value_type * rule1, value_type * rule2, setA Q);

	/* compares decisions of two rules */
	/* returns 1 if equal */

int StrengthOfRule(value_type * rule);

	/* return a number of objects covered by rule (strength) */

int *StrengthOfRules(value_type * rules, int N);

	/* creates a table of rules strengths */
	/* allocates memory, size = N * sizeof(int) */

int ObjectsForRule(setO set, value_type * rule);

	/* finds a set of objects covered by rule */

int CompareToRule(value_type * sample, value_type * rule, setA P);

	/* compares a sample with rule on a set of attributes */
	/* returns a number of dissimilar attributes (distance) */

int *CompareToRules(value_type * sample, value_type * rules, int N, setA P);

	/* compares a sample with rules on a set of attributes */
	/* creates a table of distances (number of dissimilar attributes) */
	/* allocates memory, size = N * sizeof(int) */

int Classify1(value_type * sample, value_type * rules, int N, setA P, setA Q);

	/* chooses the best rule to cover sample, strategy no. 1 */
	/* finds the most frequent decision among rules with minimal */
	/* distances from a given sample, returns index of a proper rule */

int Classify2(value_type * sample, value_type * rules, int N, setA P, setA Q);

	/* chooses the best rule to cover sample, strategy no. 2 */
	/* finds a decision that covers the largerst number of objects */
	/* among rules with minimal distances from a given sample */
	/* returns index of a proper rule */

int Classify3(value_type * sample, value_type * rules, int N,
	      int *strength, setA P, setA Q);
	/* chooses the best rule to cover sample, strategy no. 3 */
	/* finds a decision with the largest total strength among */
	/* rules with minimal distances from a given sample */
	/* returns index of a proper rule */
