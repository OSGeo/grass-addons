
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
/***       OPERATIONS ON SETS OF ATTRIBUTES AND OBJECTS                    ***/
/***                                                                       ***/
/***  part of the RSL system written by M.Gawrys J. Sienkiewicz            ***/
/***                                                                       ***/
/*****************************************************************************/


#include "rough.h"
#include <stdlib.h>


int _cluster_bytes = sizeof(cluster_type);
int _cluster_bits = 8 * sizeof(cluster_type);
cluster_type _mask[8 * sizeof(cluster_type)];

setA InitEmptySetA(void)
{
    int cluster;
    setA set;

    set = (setA) malloc(_mainsys->setAsize * _cluster_bytes);
    for (cluster = _mainsys->setAsize - 1; cluster >= 0; cluster--)
        set[cluster] = 0;
    return set;
}

setO InitEmptySetO(void)
{
    int cluster;
    setO set;

    set = (setA) malloc(_mainsys->setOsize * _cluster_bytes);
    for (cluster = _mainsys->setOsize - 1; cluster >= 0; cluster--)
        set[cluster] = 0;
    return set;
}

setA InitFullSetA(void)
{
    int attr, cluster;
    setA set;

    set = (setA) malloc(_mainsys->setAsize * _cluster_bytes);
    for (cluster = _mainsys->setAsize - 2; cluster >= 0; cluster--)
        set[cluster] = ~(cluster_type) 0;
    set[_mainsys->setAsize - 1] = 0;
    for (attr = _mainsys->attributes_num - 1;
            attr >= _cluster_bits * (_mainsys->setAsize - 1); attr--)
        AddSetA(set, attr);
    return set;
}

setO InitFullSetO(void)
{
    int cluster, attr;
    setO set;

    set = (setA) malloc(_mainsys->setOsize * _cluster_bytes);
    for (cluster = _mainsys->setOsize - 2; cluster >= 0; cluster--)
        set[cluster] = ~(cluster_type) 0;
    set[_mainsys->setOsize - 1] = 0;
    for (attr = _mainsys->objects_num - 1;
            attr >= _cluster_bits * (_mainsys->setOsize - 1); attr--)
        AddSetO(set, attr);
    return set;
}

void TabToSetA(setA set, int num, int tab[])
{
    int atr;

    ClearSetA(set);
    for (atr = 0; atr < num; atr++)
        AddSetA(set, tab[atr]);
}

void TabToSetO(setO set, int num, int tab[])
{
    int obj;

    ClearSetO(set);
    for (obj = 0; obj < num; obj++)
        AddSetO(set, tab[obj]);
}

void ArgToSetA(setA set, int num, ...)
{
    int atr;
    va_list list;

    ClearSetA(set);
    va_start(list, num);
    for (atr = 0; atr < num; atr++)
        AddSetA(set, va_arg(list, int));

    va_end(list);
}

void ArgToSetO(setO set, int num, ...)
{
    int obj;
    va_list list;

    ClearSetO(set);
    va_start(list, num);
    for (obj = 0; obj < num; obj++)
        AddSetO(set, va_arg(list, int));

    va_end(list);
}

void CloseSetA(setA set)
{
    free(set);
}

void CloseSetO(setA set)
{
    free(set);
}

void OrSetO(setO or, setO s1, setO s2)
{
    int cluster;

    for (cluster = _mainsys->setOsize - 1; cluster >= 0; cluster--)
        or[cluster] = s1[cluster] | s2[cluster];
    return;
}

void OrSetA(setA or, setA s1, setA s2)
{
    int cluster;

    for (cluster = _mainsys->setAsize - 1; cluster >= 0; cluster--)
        or[cluster] = s1[cluster] | s2[cluster];
    return;
}

void AndSetO(setO and, setO s1, setO s2)
{
    int cluster;

    for (cluster = _mainsys->setOsize - 1; cluster >= 0; cluster--)
        and[cluster] = s1[cluster] & s2[cluster];
    return;
}

void AndSetA(setA and, setA s1, setA s2)
{
    int cluster;

    for (cluster = _mainsys->setAsize - 1; cluster >= 0; cluster--)
        and[cluster] = s1[cluster] & s2[cluster];
    return;
}

void DifSetO(setO dif, setO s1, setO s2)
{
    int cluster;

    for (cluster = _mainsys->setOsize - 1; cluster >= 0; cluster--)
        dif[cluster] = s1[cluster] & ~s2[cluster];
    return;
}

void DifSetA(setA dif, setA s1, setA s2)
{
    int cluster;

    for (cluster = _mainsys->setAsize - 1; cluster >= 0; cluster--)
        dif[cluster] = s1[cluster] & ~s2[cluster];
    return;
}


void NotSetO(setO not, setO set)
{
    int cluster, obj;

    for (cluster = _mainsys->setOsize - 2; cluster >= 0; cluster--)
        not[cluster] = ~set[cluster];
    cluster = _mainsys->setOsize - 1;
    for (obj =
                _mainsys->objects_num - 1 - _cluster_bits * (_mainsys->setOsize - 1);
            obj >= 0; obj--)
        if (set[cluster] & _mask[obj])
            not[cluster] &= ~_mask[obj];
        else
            not[cluster] |= _mask[obj];
    return;
}

void NotSetA(setA not, setA set)
{
    int cluster, attr;

    for (cluster = _mainsys->setAsize - 2; cluster >= 0; cluster--)
        not[cluster] = ~set[cluster];
    cluster = _mainsys->setAsize - 1;
    for (attr =
                _mainsys->attributes_num - 1 - _cluster_bits * (_mainsys->setAsize -
                        1); attr >= 0;
            attr--)
        if (set[cluster] & _mask[attr])
            not[cluster] &= ~_mask[attr];
        else
            not[cluster] |= _mask[attr];
    return;
}

void ClearSetO(setO set)
{
    int cluster;

    for (cluster = _mainsys->setOsize - 1; cluster >= 0; cluster--)
        set[cluster] = 0;
    return;
}

void ClearSetA(setA set)
{
    int cluster;

    for (cluster = _mainsys->setAsize - 1; cluster >= 0; cluster--)
        set[cluster] = 0;
    return;
}

void FillSetO(setO set)
{
    int cluster, obj;

    for (cluster = _mainsys->setOsize - 2; cluster >= 0; cluster--)
        set[cluster] = ~(cluster_type) 0;
    set[_mainsys->setOsize - 1] = 0;
    for (obj = _mainsys->objects_num - 1;
            obj >= _cluster_bits * (_mainsys->setOsize - 1); obj--)
        AddSetO(set, obj);
    return;
}

void FillSetA(setA set)
{
    int cluster, attr;

    for (cluster = _mainsys->setAsize - 2; cluster >= 0; cluster--)
        set[cluster] = ~(cluster_type) 0;
    set[_mainsys->setAsize - 1] = 0;
    for (attr = _mainsys->attributes_num - 1;
            attr >= _cluster_bits * (_mainsys->setAsize - 1); attr--)
        AddSetA(set, attr);
    return;
}

int AddSetO(setO set, int obj)
{
    if (obj >= _mainsys->objects_num)
        ERROR(9)
        set[obj / _cluster_bits] |= _mask[obj % _cluster_bits];
    return 0;
}

int AddSetA(setA set, int attr)
{
    if (attr >= _mainsys->attributes_num)
        ERROR(9)
        set[attr / _cluster_bits] |= _mask[attr % _cluster_bits];
    return 0;
}

int DelSetO(setO set, int obj)
{
    if (obj >= _mainsys->objects_num)
        ERROR(9)
        set[obj / _cluster_bits] &= ~_mask[obj % _cluster_bits];
    return 0;
}

int DelSetA(setA set, int attr)
{
    if (attr >= _mainsys->attributes_num)
        ERROR(9)
        set[attr / _cluster_bits] &= ~_mask[attr % _cluster_bits];
    return 0;
}

int InSetO(setO big, setO small)
{
    int cluster;

    for (cluster = _mainsys->setOsize - 1; cluster >= 0; cluster--)
        if (big[cluster] != (big[cluster] | small[cluster]))
            return 0;
    return 1;
}

int InSetA(setA big, setA small)
{
    int cluster;

    for (cluster = _mainsys->setAsize - 1; cluster >= 0; cluster--)
        if (big[cluster] != (big[cluster] | small[cluster]))
            return 0;
    return 1;
}

int ContSetA(setA set, int attr)
{
    if (attr >= _mainsys->attributes_num)
        ERROR(9)
        return (_mask[attr % _cluster_bits] & set[attr / _cluster_bits]);
}

int ContSetO(setO set, int obj)
{
    if (obj >= _mainsys->objects_num)
        ERROR(9)
        return (_mask[obj % _cluster_bits] & set[obj / _cluster_bits]);
}

int InterSetO(setO s1, setO s2)
{
    int cluster;

    for (cluster = _mainsys->setOsize - 1; cluster >= 0; cluster--)
        if (s1[cluster] & s2[cluster])
            return 1;
    return 0;
}

int InterSetA(setA s1, setA s2)
{
    int cluster;

    for (cluster = _mainsys->setAsize - 1; cluster >= 0; cluster--)
        if (s1[cluster] & s2[cluster])
            return 1;
    return 0;
}


int IsEmptySetO(setO set)
{
    int cluster;

    for (cluster = _mainsys->setOsize - 1; cluster >= 0; cluster--)
        if (set[cluster])
            return 0;
    return 1;
}

int IsEmptySetA(setA set)
{
    int cluster;

    for (cluster = _mainsys->setAsize - 1; cluster >= 0; cluster--)
        if (set[cluster])
            return 0;
    return 1;
}

int CardSetO(setO set)
{
    int obj, card = 0;

    for (obj = _mainsys->objects_num - 1; obj >= 0; obj--)
        if (ContSetO(set, obj))
            card++;
    return card;
}

int CardSetA(setA set)
{
    int cluster, attr, card = 0;

    for (cluster = _mainsys->setAsize - 2; cluster >= 0; cluster--)
        for (attr = _cluster_bits - 1; attr >= 0; attr--)
            if (_mask[attr] & set[cluster])
                card++;
    cluster = _mainsys->setAsize - 1;
    for (attr =
                _mainsys->attributes_num - 1 - _cluster_bits * (_mainsys->setAsize -
                        1); attr >= 0;
            attr--)
        if (_mask[attr] & set[cluster])
            card++;
    return card;
}

void CopySetO(setO dest, setO source)
{
    int cluster;

    for (cluster = _mainsys->setOsize - 1; cluster >= 0; cluster--)
        dest[cluster] = source[cluster];
    return;
}

void CopySetA(setA dest, setA source)
{
    int cluster;

    for (cluster = _mainsys->setAsize - 1; cluster >= 0; cluster--)
        dest[cluster] = source[cluster];
    return;
}

int CompSetO(setO set1, setO set2)
{
    int cluster;

    for (cluster = _mainsys->setOsize - 1; cluster >= 0; cluster--)
        if (set1[cluster] != set2[cluster])
            return 0;
    return 1;
}

int CompSetA(setA set1, setA set2)
{
    int cluster;

    for (cluster = _mainsys->setAsize - 1; cluster >= 0; cluster--)
        if (set1[cluster] != set2[cluster])
            return 0;
    return 1;
}

int SizeSetO(void)
{
    return _mainsys->setOsize;
}

int SizeSetA(void)
{
    return _mainsys->setAsize;
}

void AttrValSetO(setO set, int attr, value_type val)
{
    int obj;

    ClearSetO(set);
    for (obj = 0; obj < _mainsys->objects_num; obj++)
        if (val == GetA(obj, attr))
            AddSetO(set, obj);
}

int ClassSetO(setO aclass, int obj, setA Q)
{
    int i;

    ClearSetO(aclass);
    for (i = 0; i < _mainsys->objects_num; i++)
        if (CompareA(i, obj, Q))
            AddSetO(aclass, i);
    return 0;
}


void PrintSetO(setO set)
{
    int obj, i = 0;

    printf("{");
    for (obj = 0; obj < _mainsys->objects_num; obj++)
        if (ContSetO(set, obj))
            printf("%c%i", (i++ > 0 ? ',' : ' '), obj);
    printf(" }\n");
}

void PrintSetA(setA set)
{
    int attr, i = 0;

    printf("{");
    for (attr = 0; attr < _mainsys->attributes_num; attr++)
        if (ContSetA(set, attr))
            printf("%c%i", (i++ > 0 ? ',' : ' '), attr);
    printf(" }\n");
}
