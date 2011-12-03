
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
/***          ( FINDING CORES AND CHECKING REDUCTS )                       ***/
/***                                                                       ***/
/***  part of the RSL system written by M.Gawrys J.Sienkiewicz             ***/
/***                                                                       ***/
/*****************************************************************************/


#include "rough.h"
#include <stdlib.h>


int Core(setA core, int matrix_type)
{
    switch (matrix_type)
    {
    case MATA:
        return CoreA(core);
    case MATD:
        return CoreDX(core, matrix_type);
    case MATX:
        return CoreDX(core, matrix_type);
    default:
        ERROR(8)
    }
}

int CoreA(setA core)
{
    int ob1, ob2, attr, no1, pattr;

    if (_mainsys->matA == NULL)
        ERROR(5)
        ClearSetA(core);
    for (ob1 = _mainsys->objects_num - 1; ob1 > 0; ob1--)
        for (ob2 = ob1 - 1; ob2 >= 0; ob2--)
        {
            no1 = 0;
            for (attr = _mainsys->attributes_num - 1; attr >= 0; attr--)
                if (!SingCompA(ob1, ob2, attr))
                {
                    no1++;
                    if (no1 > 1)
                        break;
                    else
                        pattr = attr;
                }
            if (no1 == 1)
                AddSetA(core, pattr);
        }
    return 0;
}

int CoreDX(setA core, int matrix_type)
{
    int cluster, bit, flag, no1, pcluster;

    ClearSetA(core);
    if (matrix_type == MATD)
    {
        if (_mainsys->matD == NULL)
            ERROR(6)
            START_OF_D;
    }
    else
    {
        if (_mainsys->matX == NULL)
            ERROR(7)
            START_OF_X;
    }
    for (; END_OF_MAT; NEXT_OF_MAT)
    {
        flag = 0;
        no1 = 0;
        for (cluster = _mainsys->setAsize - 1; cluster >= 0; cluster--)
        {
            for (bit = 0; bit < _cluster_bits; bit++)
                if (_mask[bit] & ELEM_OF_MAT[cluster])
                {
                    no1++;
                    if (no1 > 1)
                    {
                        flag = 1;
                        break;
                    }
                    else
                        pcluster = cluster;
                }
            if (flag)
                break;
        }
        if (no1 == 1)
            core[pcluster] |= ELEM_OF_MAT[pcluster];
    }
    return 0;
}

int CoreRel(setA core, setA P, setA Q, int matrix_type)
{
    switch (matrix_type)
    {
    case MATA:
        return CoreRelA(core, P, Q);
    case MATD:
        return CoreRelD(core, P, Q);
    default:
        ERROR(8)
    }
}

int CoreRelA(setA core, setA P, setA Q)
{
    int ob1, ob2, attr, no1, pattr;

    if (_mainsys->matA == NULL)
        ERROR(5)
        ClearSetA(core);
    for (ob1 = _mainsys->objects_num - 1; ob1 > 0; ob1--)
        for (ob2 = ob1 - 1; ob2 >= 0; ob2--)
            if (!CompareA(ob1, ob2, Q))
            {
                no1 = 0;
                for (attr = _mainsys->attributes_num - 1; attr >= 0; attr--)
                    if (ContSetA(P, attr))
                        if (!SingCompA(ob1, ob2, attr))
                        {
                            no1++;
                            if (no1 > 1)
                                break;
                            else
                                pattr = attr;
                        }
                if (no1 == 1)
                    AddSetA(core, pattr);
            }
    return 0;
}

int CoreRelD(setA core, setA P, setA Q)
{
    int cluster, bit, flag, no1, pcluster;
    setA elem;

    if (_mainsys->matD == NULL)
        ERROR(6)
        ClearSetA(core);
    elem = InitEmptySetA();
    for (START_OF_D; END_OF_MAT; NEXT_OF_MAT)
    {
        AndSetA(elem, ELEM_OF_MAT, P);
        flag = 0;
        no1 = 0;
        if (!InterSetA(Q, ELEM_OF_MAT))
            continue;
        for (cluster = _mainsys->setAsize - 1; cluster >= 0; cluster--)
        {
            for (bit = 0; bit < _cluster_bits; bit++)
                if (_mask[bit] & elem[cluster])
                {
                    no1++;
                    if (no1 > 1)
                    {
                        flag = 1;
                        break;
                    }
                    else
                        pcluster = cluster;
                }
            if (flag)
                break;
        }
        if (no1 == 1)
            core[pcluster] |= elem[pcluster];
    }
    CloseSetA(elem);
    return 0;
}

int IsOrtho(setA red, setA over, int matrix_type)
{
    setA and, redprim;

    and = InitEmptySetA();
    redprim = InitEmptySetA();
    for (start_of_tab(matrix_type); end_of_tab(); next_of_tab())
    {
        AndSetA(and, _table_element, red);
        if (CardSetA(and) == 1)
            OrSetA(redprim, redprim, and);
    }
    CloseSetA(and);
    DifSetA(over, red, redprim);
    CloseSetA(redprim);
    return IsEmptySetA(over);
}

int IsOrthoRel(setA red, setA over, setA P, setA Q, int matrix_type)
{
    setA and, redprim;

    and = InitEmptySetA();
    redprim = InitEmptySetA();
    for (start_of_tab(matrix_type); end_of_tab(); next_of_tab())
        if (InterSetA(_table_element, Q))
        {
            AndSetA(and, _table_element, red);
            AndSetA(and, and, P);
            if (CardSetA(and) == 1)
                OrSetA(redprim, redprim, and);
        }
    CloseSetA(and);
    DifSetA(over, red, redprim);
    CloseSetA(redprim);
    return IsEmptySetA(over);
}

int IsCover(setA red, int matrix_type)
{
    switch (matrix_type)
    {
    case MATA:
        return IsCoverA(red);
    case MATD:
        return IsCoverDX(red, matrix_type);
    case MATX:
        return IsCoverDX(red, matrix_type);
    default:
        ERROR(8)
    }
}

int IsCoverA(setA red)
{
    int ob1, ob2;
    setA P = InitFullSetA();

    DifSetA(P, P, red);
    if (_mainsys->matA == NULL)
        ERROR(5);
    for (ob1 = _mainsys->objects_num - 1; ob1 > 0; ob1--)
        for (ob2 = ob1 - 1; ob2 >= 0; ob2--)
            if (CompareA(ob1, ob2, red))
                if (!CompareA(ob1, ob2, P))
                {
                    CloseSetA(P);
                    return 0;
                }
    CloseSetA(P);
    return 1;
}

int IsCoverDX(setA red, int matrix_type)
{
    if (matrix_type == MATD)
    {
        if (_mainsys->matD == NULL)
            ERROR(6)
            START_OF_D;
    }
    else
    {
        if (_mainsys->matX == NULL)
            ERROR(7)
            START_OF_X;
    }
    for (; END_OF_MAT; NEXT_OF_MAT)
        if (!IsEmptySetA(ELEM_OF_MAT))
            if (!InterSetA(ELEM_OF_MAT, red))
                return 0;
    return 1;
}

int IsCoverRel(setA red, setA P, setA Q, int matrix_type)
{
    switch (matrix_type)
    {
    case MATA:
        return IsCoverRelA(red, P, Q);
    case MATD:
        return IsCoverRelD(red, P, Q);
    default:
        ERROR(8)
    }
}

int IsCoverRelA(setA red, setA P, setA Q)
{
    int ob1, ob2;
    setA Pprim;

    if (_mainsys->matA == NULL)
        ERROR(5);
    Pprim = InitEmptySetA();
    DifSetA(Pprim, P, red);
    for (ob1 = _mainsys->objects_num - 1; ob1 > 0; ob1--)
        for (ob2 = ob1 - 1; ob2 >= 0; ob2--)
            if (!CompareA(ob1, ob2, Q))
                if (CompareA(ob1, ob2, red))
                    if (!CompareA(ob1, ob2, Pprim))
                    {
                        CloseSetA(Pprim);
                        return 0;
                    }
    CloseSetA(Pprim);
    return 1;
}

int IsCoverRelD(setA red, setA P, setA Q)
{
    if (_mainsys->matD == NULL)
        ERROR(6);
    for (START_OF_D; END_OF_MAT; NEXT_OF_MAT)
        if (InterSetA(ELEM_OF_MAT, Q))
            if (!InterSetA(ELEM_OF_MAT, red))
                if (InterSetA(ELEM_OF_MAT, P))
                    return 0;
    return 1;
}

int IsRed(setA red, int matrix_type)
{
    int result;
    setA over;

    if (!IsCover(red, matrix_type))
        return 0;
    over = InitEmptySetA();
    result = IsOrtho(red, over, matrix_type);
    CloseSetA(over);
    return result;
}


int IsRedRel(setA red, setA P, setA Q, int matrix_type)
{
    int result;
    setA over;

    if (!IsCoverRel(red, P, Q, matrix_type))
        return 0;
    over = InitEmptySetA();
    result = IsOrthoRel(red, over, P, Q, matrix_type);
    CloseSetA(over);
    return result;
}
