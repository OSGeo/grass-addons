
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
/***                   ( FINDING RULES )                                   ***/
/***                                                                       ***/
/***  part of the RSL system written by M.Gawrys J.Sienkiewicz             ***/
/***                                                                       ***/
/*****************************************************************************/


#include "rough.h"
#include <stdlib.h>
#include <string.h>

int AllRules(value_type ** rules, setA P, setA Q, int matrix_type)
{
    int obj, attr, n, red;
    int memo = _mainsys->objects_num;
    int count = 0;
    int size = _mainsys->setAsize;
    setA reducts = NULL;
    value_type *rule = NULL;

    *rules =
        (value_type *) malloc(memo * _mainsys->attributes_num *
                              sizeof(value_type));
    if (*rules == NULL)
        ERROR(3);
    if (!MatExist(_mainsys, MATA))
        ERROR(5);
    rule =
        (value_type *) malloc(_mainsys->attributes_num * sizeof(value_type));
    if (rule == NULL)
        ERROR(3);
    for (obj = 0; obj < _mainsys->objects_num; obj++)
    {
        if (InitXforObject(_mainsys, obj, P, Q, matrix_type) < 0)
        {
            free(rule);
            return (-_rerror);
        }
        else if (!MatExist(_mainsys, MATX))
            continue;
        n = Red(&reducts, MATX);
        CloseMat(_mainsys, MATX);
        if (memo < count + n)
        {
            memo = count + n;
            if ((*rules = (value_type *) realloc(*rules,
                                                 memo *
                                                 _mainsys->attributes_num *
                                                 sizeof(value_type))) ==
                    NULL)
            {
                free(reducts);
                free(rule);
                ERROR(3)
            }
        }
        for (red = 0; red < n; red++)
        {
            for (attr = _mainsys->attributes_num - 1; attr >= 0; attr--)
                if (ContSetA(reducts + red * size, attr) || ContSetA(Q, attr))
                    rule[attr] = GetA(obj, attr);
                else
                    rule[attr] = MINUS;
            AddRule(*rules, &count, rule);
        }
        if (n > 0)
            free(reducts);
        reducts = NULL;
    }
    free(rule);
    if ((*rules = (value_type *) realloc
                  (*rules,
                   count * _mainsys->attributes_num * sizeof(value_type))) == NULL)
        ERROR(3);
    return count;
}

int AllRulesForReducts(value_type ** rules, cluster_type * reducts,
                       int N, setA Q, int matrix_type)
{
    int red, num, i, count = 0;
    value_type *newrules = NULL;	/* rules for a single reduct */

    *rules = NULL;
    for (red = 0; red < N; red++)
    {
        num =
            AllRules(&newrules, reducts + red * _mainsys->setAsize, Q,
                     matrix_type);
        if ((*rules =
                    (value_type *) realloc(*rules,
                                           (count +
                                            num) * _mainsys->attributes_num *
                                           sizeof(value_type))) == NULL)
        {
            free(newrules);
            ERROR(3)
        }
        for (i = 0; i < num; i++)
            AddRule(*rules, &count, newrules + i * _mainsys->attributes_num);
        if (num > 0)
            free(newrules);
        newrules = NULL;
    }
    if ((*rules = (value_type *) realloc
                  (*rules,
                   count * _mainsys->attributes_num * sizeof(value_type))) == NULL)
        ERROR(3);
    return count;
}


int SelectRules(value_type ** rules, int *N, setO set, setA P, int option)
{
    int i, j, obj, find, newXsize,
    newN = 0, next = -1, size = _mainsys->attributes_num;
    setA red, newfull;
    SYSTEM *oldsys = _mainsys, *newsys = InitEmptySys();
    cluster_type *newX;
    value_type *newrules;

    SetParameters(newsys, *N, *N);
    newXsize = CardSetO(set) * (newsys->setAsize);
    newX = (cluster_type *) calloc(newXsize, _cluster_bytes);
    if (newX == NULL)
    {
        CloseSys(newsys);
        ERROR(3);
    }
    for (obj = 0; obj < _mainsys->objects_num; obj++)
        if (ContSetO(set, obj))
            for (i = 0, next++; i < *N; i++)
            {
                find = 1;
                for (j = 0; j < _mainsys->attributes_num; j++)
                {
                    if (!ContSetA(P, j))
                        continue;
                    if ((*rules + i * size)[j] != GetA(obj, j))
                        if ((*rules + i * size)[j] != MINUS)
                        {
                            find = 0;
                            break;
                        }
                }
                if (find)
                    newX[next * newsys->setAsize + i / _cluster_bits] |=
                        _mask[i % _cluster_bits];
            }
    UseSys(newsys);
    newsys->matX = newX;
    newsys->matXsize = newXsize;
    newfull = InitFullSetA();
    InitX(newsys, newfull, newfull, MATX);
    free(newX);
    CloseSetA(newfull);
    if (_rerror != 0)
    {
        free(newsys);
        UseSys(oldsys);
        ERROR(3);
    }
    if (option == BESTOPT)
    {
        i = Red(&red, MATX);
        j = SelectOneShort(red, i);
    }
    else
    {
        red = InitEmptySetA();
        RedOptim(red, MATX);
        j = 0;
    }
    newN = CardSetA(red + j * newsys->setAsize);
    newrules = (value_type *) malloc(newN * oldsys->attributes_num *
                                     sizeof(value_type));
    if (newrules == NULL)
    {
        CloseSys(newsys);
        UseSys(oldsys);
        ERROR(3);
    }
    for (i = 0, obj = 0; i < *N; i++)
        if (ContSetA(red + j * newsys->setAsize, i))
            memcpy(newrules + obj++ * oldsys->attributes_num,
                   *rules + i * oldsys->attributes_num,
                   oldsys->attributes_num * sizeof(value_type));
    if (option == BESTOPT)
        free(red);
    else
        CloseSetA(red);
    if (*N > 0)
        free(*rules);
    *N = newN;
    *rules = newrules;
    UseSys(oldsys);
    CloseSys(newsys);
    return 0;
}

int BestRules(value_type ** rules, setA P, setA Q, int matrix_type)
{
    int i, obj, num = 0,	/* total number of rules */
                      classnum = 0;		/* number of rules for class */
    setO processed,		/* already covered objects */
    newclass;			/* class */
    value_type *classrules = NULL;	/* rules for a single class */

    *rules = (value_type *) malloc(Asize(_mainsys) * sizeof(value_type));
    if (*rules == NULL)
        ERROR(3);
    if (!MatExist(_mainsys, MATA))
        ERROR(5);
    processed = InitEmptySetO();
    newclass = InitEmptySetO();
    for (obj = 0; obj < _mainsys->objects_num; obj++)
        if (!ContSetO(processed, obj))
        {
            ClassSetO(newclass, obj, Q);
            classnum = 0;
            OrSetO(processed, processed, newclass);
            classnum =
                BestRulesForClass(&classrules, newclass, P, Q, matrix_type);
            for (i = 0; i < classnum; i++)
                AddRule(*rules, &num,
                        classrules + i * _mainsys->attributes_num);
            if (classnum > 0)
                free(classrules);
            classrules = NULL;
        }
    CloseSetO(processed);
    CloseSetO(newclass);
    if ((*rules = (value_type *) realloc(*rules,
                                         num * _mainsys->attributes_num *
                                         sizeof(value_type))) == NULL)
        ERROR(3);
    return num;
}


int BestRulesForClass(value_type ** rules, setO set, setA P, setA Q,
                      int matrix_type)
{
    int n, attr, obj, red, num = 0;	/* total number of rules */
    int size = _mainsys->setAsize;
    setA fewred = NULL,		/* selected reducts */
                  allred = NULL;		/* all reducts */
    value_type *rule = NULL;	/* single rule */

    *rules = NULL;
    if (!MatExist(_mainsys, MATA))
        ERROR(5);
    rule =
        (value_type *) malloc(_mainsys->attributes_num * sizeof(value_type));
    if (rule == NULL)
        ERROR(3);
    for (obj = 0; obj < _mainsys->objects_num; obj++)
        if (ContSetO(set, obj))
        {
            if (InitXforObject(_mainsys, obj, P, Q, matrix_type) < 0)
            {
                free(rule);
                return (-_rerror);
            }
            else if (!MatExist(_mainsys, MATX))
                continue;
            n = Red(&allred, MATX);
            CloseMat(_mainsys, MATX);
            if (n > 0)
            {
                n = SelectAllShort(&fewred, allred, n);
                free(allred);
            }
            else
            {
                free(rule);
                return (-_rerror);
            }
            if ((*rules = (value_type *) realloc
                          (*rules,
                           (n +
                            num) * _mainsys->attributes_num * sizeof(value_type))) ==
                    NULL)
            {
                free(rule);
                free(fewred);
                return (-_rerror);
            }
            for (red = 0; red < n; red++)
            {
                for (attr = _mainsys->attributes_num - 1; attr >= 0; attr--)
                    if (ContSetA(fewred + red * size, attr) ||
                            ContSetA(Q, attr))
                        rule[attr] = GetA(obj, attr);
                    else
                        rule[attr] = MINUS;
                AddRule(*rules, &num, rule);
            }
        }
    if (n > 0)
        free(fewred);
    free(rule);
    if (SelectRules(rules, &num, set, P, BESTOPT) < 0)
        return (-_rerror);
    if ((*rules = (value_type *) realloc
                  (*rules,
                   num * _mainsys->attributes_num * sizeof(value_type))) == NULL)
        ERROR(3);
    return num;
}


int Rules(value_type ** rules, setA P, setA Q, int matrix_type)
{
    int i, obj, num = 0,	/* total number of rules */
                      classnum = 0;		/* number of rules for class */
    setO processed,		/* already covered objects */
    newclass;			/* class */
    value_type *rule = NULL,	/* single rule */
                       *classrules = NULL;	/* rules for class */

    *rules = (value_type *) malloc(Asize(_mainsys) * sizeof(value_type));
    if (*rules == NULL)
        ERROR(3);
    if (!MatExist(_mainsys, MATA))
        ERROR(5);
    rule =
        (value_type *) malloc(_mainsys->attributes_num * sizeof(value_type));
    if (rule == NULL)
        ERROR(3);
    processed = InitEmptySetO();
    newclass = InitEmptySetO();
    for (obj = 0; obj < _mainsys->objects_num; obj++)
        if (!ContSetO(processed, obj))
        {
            ClassSetO(newclass, obj, Q);
            classnum = 0;
            OrSetO(processed, processed, newclass);
            classnum =
                RulesForClass(&classrules, newclass, P, Q, matrix_type);
            for (i = 0; i < classnum; i++)
                AddRule(*rules, &num,
                        classrules + i * _mainsys->attributes_num);
            if (classnum > 0)
                free(classrules);
            classrules = NULL;
        }
    free(rule);
    CloseSetO(processed);
    CloseSetO(newclass);
    if ((*rules = (value_type *) realloc
                  (*rules,
                   num * _mainsys->attributes_num * sizeof(value_type))) == NULL)
        ERROR(3);
    return num;
}


int RulesForClass(value_type ** rules, setO set, setA P, setA Q,
                  int matrix_type)
{
    int j, n, obj, red, num = 0;	/* total number of rules */
    int size = _mainsys->setAsize;
    setA fewred = NULL,		/* selected reducts */
                  allred = NULL;		/* all reducts */
    value_type *rule = NULL;	/* single rule */

    *rules = NULL;
    if (!MatExist(_mainsys, MATA))
        ERROR(5);
    rule =
        (value_type *) malloc(_mainsys->attributes_num * sizeof(value_type));
    if (rule == NULL)
        ERROR(3);
    for (obj = 0; obj < _mainsys->objects_num; obj++)
        if (ContSetO(set, obj))
        {
            if (InitXforObject(_mainsys, obj, P, Q, matrix_type) < 0)
            {
                free(rule);
                return (-_rerror);
            }
            else if (!MatExist(_mainsys, MATX))
                continue;
            n = Red(&allred, MATX);
            CloseMat(_mainsys, MATX);
            if (n > 0)
            {
                n = SelectAllShort(&fewred, allred, n);
                free(allred);
            }
            else
            {
                free(rule);
                return (-_rerror);
            }
            if ((*rules = (value_type *) realloc
                          (*rules,
                           (n +
                            num) * _mainsys->attributes_num * sizeof(value_type))) ==
                    NULL)
            {
                free(rule);
                free(fewred);
                return (-_rerror);
            }
            for (red = 0; red < n; red++)
            {
                for (j = _mainsys->attributes_num - 1; j >= 0; j--)
                    if (ContSetA(fewred + red * size, j) || ContSetA(Q, j))
                        rule[j] = GetA(obj, j);
                    else
                        rule[j] = MINUS;
                AddRule(*rules, &num, rule);
            }
        }
    if (n > 0)
        free(fewred);
    free(rule);
    if (SelectRules(rules, &num, set, P, FASTOPT) < 0)
        return (-_rerror);
    if ((*rules = (value_type *) realloc
                  (*rules,
                   num * _mainsys->attributes_num * sizeof(value_type))) == NULL)
        ERROR(3);
    return num;
}


int FastRules(value_type ** rules, setA P, setA Q, int matrix_type)
{
    int obj, attr, n, red, count = 0;
    int size = _mainsys->setAsize;
    setA reducts = NULL;
    value_type *rule = NULL;

    *rules = (value_type *) malloc(Asize(_mainsys) * sizeof(value_type));
    if (*rules == NULL)
        ERROR(3);
    if (!MatExist(_mainsys, MATA))
        ERROR(5);
    rule =
        (value_type *) malloc(_mainsys->attributes_num * sizeof(value_type));
    if (rule == NULL)
        ERROR(3);
    for (obj = 0; obj < _mainsys->objects_num; obj++)
    {
        if (InitXforObject(_mainsys, obj, P, Q, matrix_type) < 0)
        {
            free(rule);
            return (-_rerror);
        }
        else if (!MatExist(_mainsys, MATX))
            continue;
        n = Red(&reducts, MATX);
        CloseMat(_mainsys, MATX);
        red = SelectOneShort(reducts, n);
        for (attr = _mainsys->attributes_num - 1; attr >= 0; attr--)
            if (ContSetA(reducts + red * size, attr) || ContSetA(Q, attr))
                rule[attr] = GetA(obj, attr);
            else
                rule[attr] = MINUS;
        AddRule(*rules, &count, rule);
        if (n > 0)
            free(reducts);
        reducts = NULL;
    }
    free(rule);
    if ((*rules = (value_type *) realloc
                  (*rules,
                   count * _mainsys->attributes_num * sizeof(value_type))) == NULL)
        ERROR(3);
    return count;
}


int VeryFastRules(value_type ** rules, setA P, setA Q, int matrix_type)
{
    int obj, attr, count = 0;
    setA reduct;
    value_type *rule = NULL;

    *rules = (value_type *) malloc(Asize(_mainsys) * sizeof(value_type));
    if (*rules == NULL)
        ERROR(3);
    if (!MatExist(_mainsys, MATA))
        ERROR(5);
    rule =
        (value_type *) malloc(_mainsys->attributes_num * sizeof(value_type));
    if (rule == NULL)
        ERROR(3);
    reduct = InitEmptySetA();
    for (obj = 0; obj < _mainsys->objects_num; obj++)
    {
        if (InitXforObject(_mainsys, obj, P, Q, matrix_type) < 0)
        {
            free(rule);
            return (-_rerror);
        }
        else if (!MatExist(_mainsys, MATX))
            continue;
        RedOptim(reduct, MATX);
        CloseMat(_mainsys, MATX);
        for (attr = _mainsys->attributes_num - 1; attr >= 0; attr--)
            if (ContSetA(reduct, attr) || ContSetA(Q, attr))
                rule[attr] = GetA(obj, attr);
            else
                rule[attr] = MINUS;
        AddRule(*rules, &count, rule);
    }
    free(rule);
    CloseSetA(reduct);
    if ((*rules = (value_type *) realloc
                  (*rules,
                   count * _mainsys->attributes_num * sizeof(value_type))) == NULL)
        ERROR(3);
    return count;
}


int ApprRules(value_type ** rules, setA P, setA Q, int option,
              int matrix_type)
{
    int i, obj, num = 0,	/* total number of rules */
                      classnum = 0;		/* number of rules for class */
    setO processed,		/* already covered objects */
    newclass;			/* class */
    value_type *rule = NULL,	/* single rule */
                       *classrules = NULL;	/* rules for class */

    *rules = (value_type *) malloc(Asize(_mainsys) * sizeof(value_type));
    if (*rules == NULL)
        ERROR(3);
    if (!MatExist(_mainsys, MATA))
        ERROR(5);
    rule =
        (value_type *) malloc(_mainsys->attributes_num * sizeof(value_type));
    if (rule == NULL)
        ERROR(3);
    processed = InitEmptySetO();
    newclass = InitEmptySetO();
    for (obj = 0; obj < _mainsys->objects_num; obj++)
        if (!ContSetO(processed, obj))
        {
            ClassSetO(newclass, obj, Q);
            classnum = 0;
            OrSetO(processed, processed, newclass);
            classnum = ApprRulesForClass(&classrules, newclass, P, Q,
                                         option, matrix_type);
            for (i = 0; i < classnum; i++)
                AddRule(*rules, &num,
                        classrules + i * _mainsys->attributes_num);
            if (classnum > 0)
                free(classrules);
            classrules = NULL;
        }
    free(rule);
    CloseSetO(processed);
    CloseSetO(newclass);
    if ((*rules = (value_type *) realloc
                  (*rules,
                   num * _mainsys->attributes_num * sizeof(value_type))) == NULL)
        ERROR(3);
    return num;
}



int ApprRulesForClass(value_type ** rules, setO set, setA P, setA Q,
                      int option, int matrix_type)
{
    int j, n, obj, red, num = 0;	/* total number of rules */
    int size = _mainsys->setAsize;
    setA fewred = NULL,		/* selected reducts */
                  allred = NULL;		/* all reducts */
    value_type *rule = NULL;	/* single rule */
    setO aclass;

    *rules = NULL;
    if (!MatExist(_mainsys, MATA))
        ERROR(5);
    rule =
        (value_type *) malloc(_mainsys->attributes_num * sizeof(value_type));
    if (rule == NULL)
        ERROR(3);
    aclass = InitEmptySetO();
    if (option == LOWER)
        LowAppr(aclass, set, P, matrix_type);
    else if (option == UPPER)
        UppAppr(aclass, set, P, matrix_type);
    else
        CopySetO(aclass, set);
    for (obj = 0; obj < _mainsys->objects_num; obj++)
        if (ContSetO(aclass, obj))
        {
            if (InitXforObjectFromClass(_mainsys, obj, P, aclass, matrix_type)
                    < 0)
            {
                free(rule);
                return (-_rerror);
            }
            else if (!MatExist(_mainsys, MATX))
                continue;
            n = Red(&allred, MATX);
            CloseMat(_mainsys, MATX);
            if (n > 0)
            {
                n = SelectAllShort(&fewred, allred, n);
                free(allred);
            }
            else
            {
                free(rule);
                return (-_rerror);
            }
            if ((*rules = (value_type *) realloc
                          (*rules,
                           (n +
                            num) * _mainsys->attributes_num * sizeof(value_type))) ==
                    NULL)
            {
                free(rule);
                free(fewred);
                return (-_rerror);
            }
            for (red = 0; red < n; red++)
            {
                for (j = _mainsys->attributes_num - 1; j >= 0; j--)
                    if (ContSetA(fewred + red * size, j) || ContSetA(Q, j))
                        rule[j] = GetA(obj, j);
                    else
                        rule[j] = MINUS;
                AddRule(*rules, &num, rule);
            }
        }
    if (n > 0)
        free(fewred);
    free(rule);
    if (SelectRules(rules, &num, set, P, FASTOPT) < 0)
        return (-_rerror);
    if ((*rules = (value_type *) realloc
                  (*rules,
                   num * _mainsys->attributes_num * sizeof(value_type))) == NULL)
        ERROR(3);
    return num;
}
