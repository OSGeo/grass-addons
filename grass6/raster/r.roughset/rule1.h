
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

/***                   ( MENAGING RULES )                                  ***/

/***                                                                       ***/

/***  part of the RSL system written by M.Gawrys J.Sienkiewicz             ***/

/***                                                                       ***/

/*****************************************************************************/


#define MINUS ((value_type)-1)

void RuleCopy(value_type * dest, value_type * source);

	/* copies a rule from source to dest */

int RuleEQ(value_type * first, value_type * second);

	/* returns 1 if first rule is equal to second */

void AddRule(value_type * rules, int *size, value_type * rule);

	/* adds new rule to array of rules */
	/* if the rule is unique size is incremented */
