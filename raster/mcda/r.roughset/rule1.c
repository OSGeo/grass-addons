
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
 * COPYRIGHT:    (C) A.Boggia - G.Massei (2008)
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
/*** part of the ROUGH system written by M.Gawrys J.Sienkiewicz            ***/
/***                                                                       ***/
/*****************************************************************************/


#include <stdlib.h>
#include <string.h>
#include "rough.h"

void RuleCopy(value_type * dest, value_type * source)
{
    memcpy(dest, source, _mainsys->attributes_num * sizeof(value_type));
}

int RuleEQ(value_type * first, value_type * second)
{
    return !memcmp(first, second,
                   _mainsys->attributes_num * sizeof(value_type));
}


void AddRule(value_type * rules, int *count, value_type * rule)
{
    int i;
    int size = _mainsys->attributes_num;

    for (i = 0; i < *count; i++)
        if (RuleEQ(rules + i * size, rule))
            return;
    RuleCopy(rules + (*count) * size, rule);
    *count += 1;
    return;
}
