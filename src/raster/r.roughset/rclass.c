
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
/***                     ( CLASSIFICATION )                                ***/
/***                                                                       ***/
/***  part of the RSL system written by M.Gawrys J.Sienkiewicz             ***/
/***                                                                       ***/
/*****************************************************************************/


#include <stdlib.h>
#include "rough.h"


int DecisionEQ(value_type * rule1, value_type * rule2, setA Q)
{
    int i;

    for (i = 0; i < _mainsys->attributes_num; i++)
        if (ContSetA(Q, i))
            if (rule1[i] != rule2[i])
                return 0;
    return 1;
}


int StrengthOfRule(value_type * rule)
{
    int obj, attr, find, result = 0, size = _mainsys->attributes_num;

    for (obj = 0; obj < _mainsys->objects_num; obj++)
    {
        find = 1;
        for (attr = 0; attr < size; attr++)
            if (rule[attr] != GetA(obj, attr))
                if (rule[attr] != MINUS && GetA(obj, attr) != MINUS)
                {
                    find = 0;
                    break;
                }
        if (find)
            result++;
    }
    return result;
}

int *StrengthOfRules(value_type * rules, int N)
{
    int *result;
    int i, size = _mainsys->attributes_num;

    if (N <= 0)
        return NULL;
    result = (int *)calloc(N, sizeof(int));
    for (i = 0; i < N; i++)
        result[i] = StrengthOfRule(rules + i * size);
    return result;
}


int ObjectsForRule(setO set, value_type * rule)
{
    int i, j, find, size = _mainsys->attributes_num;

    for (i = 0; i < _mainsys->objects_num; i++)
    {
        find = 1;
        for (j = 0; j < size; j++)
            if (rule[j] != GetA(i, j))
                if (rule[j] != MINUS && GetA(i, j) != MINUS)
                {
                    find = 0;
                    break;
                }
        if (find)
            AddSetO(set, i);
    }
    return CardSetO(set);
}


int CompareToRule(value_type * sample, value_type * rule, setA P)
{
    int j, result = 0, size = _mainsys->attributes_num;

    for (j = 0; j < size; j++)
    {
        if (!ContSetA(P, j))
            continue;
        if (rule[j] != sample[j])
            if (rule[j] != MINUS && sample[j] != MINUS)
                result++;
    }
    return result;
}


int *CompareToRules(value_type * sample, value_type * rules, int N, setA P)
{
    int *result;
    int i, size = _mainsys->attributes_num;

    if (N <= 0)
        return NULL;
    result = (int *)calloc(N, sizeof(int));
    for (i = 0; i < N; i++)
        result[i] = CompareToRule(sample, rules + i * size, P);
    return result;
}


int Classify1(value_type * sample, value_type * rules, int N, setA P, setA Q)
{
    int done = 0,
               result = -1,
                        count = 0,
                                *diff, minDiff = _mainsys->attributes_num,
                                                 i, j = 0, max = 0, size = _mainsys->attributes_num;
    diff = CompareToRules(sample, rules, N, P);
    for (i = 0; i < N; i++)
        if (diff[i] < minDiff)
            minDiff = diff[i];
    while (!done)  		/* while there is an unprocessed rule */
    {
        while (diff[j] != minDiff)
            j++;		/* to find the rule with new decision */
        done = 1;
        diff[j]++;
        count = 1;
        for (i = j; i < N; i++)
            if (diff[i] == minDiff)
                if (DecisionEQ(rules + i * size, rules + j * size, Q))
                {
                    diff[j]++;	/* to protect from next use */
                    count++;
                }
                else
                    done = 0;
        if (count > max)
            max = count, result = j;
    }
    free(diff);
    return result;
}


int Classify2(value_type * sample, value_type * rules, int N, setA P, setA Q)
{
    int i,
    *diff,
    first = 0, maxindex,
            size = _mainsys->attributes_num,
                   minDiff = _mainsys->attributes_num, done = 0;
    setO cover, maxcover, rulecover;

    cover = InitEmptySetO();
    maxcover = InitEmptySetO();
    rulecover = InitEmptySetO();
    diff = CompareToRules(sample, rules, N, P);
    for (i = 0; i < N; i++)
        if (diff[i] < minDiff)
            minDiff = diff[i];
    while (!done)  		/* while there is an unprocessed rule */
    {
        while (diff[first] != minDiff)
            first++;		/* to find the rule with new decision */
        done = 1;
        diff[first]++;		/* to protect from next use */
        ObjectsForRule(cover, rules + first * size);
        for (i = first; i < N; i++)
            if (diff[i] == minDiff)
                if (DecisionEQ(rules + first * size, rules + i * size, Q))
                {
                    diff[i]++;
                    ObjectsForRule(rulecover, rules + i * size);
                    OrSetO(cover, cover, rulecover);
                }
                else
                    done = 0;
        if (CardSetO(maxcover) < CardSetO(cover))
        {
            CopySetO(maxcover, cover);
            maxindex = first;
        }
    }
    free(diff);
    CloseSetO(cover);
    CloseSetO(maxcover);
    CloseSetO(rulecover);
    return maxindex;
}

int Classify3(value_type * sample, value_type * rules, int N,
              int *strength, setA P, setA Q)
{
    int i,
    *diff,
    first = 0, maxindex,
            size = _mainsys->attributes_num,
                   minDiff = _mainsys->attributes_num, done = 0;
    int cover, maxcover = 0;

    diff = CompareToRules(sample, rules, N, P);
    for (i = 0; i < N; i++)
        if (diff[i] < minDiff)
            minDiff = diff[i];
    while (!done)  		/* while there is an unprocessed rule */
    {
        while (diff[first] != minDiff)
            first++;		/* to find the rule with new decision */
        done = 1;
        diff[first]++;		/* to protect from next use */
        cover = strength[first];
        for (i = first; i < N; i++)
            if (diff[i] == minDiff)
                if (DecisionEQ(rules + first * size, rules + i * size, Q))
                {
                    diff[i]++;
                    cover += strength[i];
                }
                else
                    done = 0;
        if (maxcover < cover)
        {
            maxcover = cover;
            maxindex = first;
        }
    }
    free(diff);
    return maxindex;
}
