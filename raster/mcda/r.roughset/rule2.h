
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

/***                   ( FINDING RULES )                                   ***/

/***                                                                       ***/

/***  part of the RSL system written by M.Gawrys J.Sienkiewicz             ***/

/***                                                                       ***/

/*****************************************************************************/

#define BESTOPT 0
#define FASTOPT 1

#define NORMAL  0
#define LOWER   1
#define UPPER   2

int AllRules(value_type ** rules, setA P, setA Q, int matrix_type);

	/* finds all possible rules for condition attributes P */
	/* and decision Q, allocates memory, returns number of rules */

int AllRulesForReducts(value_type ** rules, cluster_type * reducts,
		       int N, setA Q, int matrix_type);
	/* finds all possible rules for each reduct separatly */
	/* allocates memory, returns number of rules */

int SelectRules(value_type ** rules, int *N, setO set, setA P, int option);

	/* reduce set of rules to cover only some objects */
	/* on attributes P, reallocates memory and decrease N */
	/* option: FASTOPT for shortcomings      */
	/*         BESTOPT for optimal computing */

int BestRules(value_type ** rules, setA P, setA Q, int matrix_type);

	/* finds minimal set of rules, allocates memory */
	/* P - condition attributes; Q - decision attributes */
	/* returns number of rules */

int BestRulesForClass(value_type ** rules, setO set, setA P, setA Q,
		      int matrix_type);
	/* finds minimal set of rules to cover objects from set */
	/* P - condition attributes; Q - decision attributes */
	/* allocates memory, returns number of rules */

int Rules(value_type ** rules, setA P, setA Q, int matrix_type);

	/* finds set of rules, allocates memory */
	/* P - condition attributes; Q - decision attributes */
	/* returns number of rules */

int RulesForClass(value_type ** rules, setO set, setA P, setA Q,
		  int matrix_type);
	/* finds set of rules to cover objects from set */
	/* P - condition attributes; Q - decision attributes */
	/* allocates memory, returns number of rules */

int FastRules(value_type ** rules, setA P, setA Q, int matrix_type);

	/* finds quickly set of rules, allocates memory */
	/* P - condition attributes; Q - decision attributes */
	/* returns number of rules */

int VeryFastRules(value_type ** rules, setA P, setA Q, int matrix_type);

	/* finds very quickly set of rules, allocates memory */
	/* P - condition attributes; Q - decision attributes */
	/* returns number of rules */

int ApprRules(value_type ** rules, setA P, setA Q, int option,
	      int matrix_type);
	/* finds set of rules for approximated classes */
	/* P - condition attributes; Q - decision attributes */
	/* option: LOWER - lower approximation - certain rules */
	/*         UPPER - upper approximation - possible rules */
	/*         NORMAL - no approximation - normal rules */
	/* allocates memory, returns number of rules */

int ApprRulesForClass(value_type ** rules, setO set, setA P, setA Q,
		      int option, int matrix_type);
	/* finds set of rules for approximated class (set) */
	/* P - condition attributes; Q - decision attributes */
	/* option: LOWER - lower approximation - certain rules */
	/*         UPPER - upper approximation - possible rules */
	/*         NORMAL - no approximation - normal rules */
	/* allocates memory, returns number of rules */
