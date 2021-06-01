
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
/***               BASIC QUERIES FOR ACTIVE SYSTEM                         ***/
/***                                                                       ***/
/***  part of the RSL system written by M.Gawrys J.Sienkiewicz             ***/
/***                                                                       ***/
/*****************************************************************************/


#include "rough.h"

int LowAppr(setO lowappr, setO X, setA P, int matrix_type)
{
    switch (matrix_type)
    {
    case MATA:
        return LowApprA(lowappr, X, P);
    case MATD:
        return LowApprD(lowappr, X, P);
    default:
        ERROR(8)
    }
}

int LowApprA(setO lowappr, setO X, setA P)
{
    setO notX;
    int ob1, ob2, disc;

    if (_mainsys->matA == NULL)
        ERROR(5);
    notX = InitEmptySetO();
    ClearSetO(lowappr);
    NotSetO(notX, X);
    for (ob1 = 0; ob1 < _mainsys->objects_num; ob1++)
        if (ContSetO(X, ob1))
        {
            disc = 1;
            for (ob2 = 0; ob2 < _mainsys->objects_num; ob2++)
                if (ContSetO(notX, ob2))
                    if (CompareA(ob1, ob2, P))
                    {
                        disc = 0;
                        break;
                    }
            if (disc)
                AddSetO(lowappr, ob1);
        }
    CloseSetO(notX);
    return 0;
}

int LowApprD(setO lowappr, setO X, setA P)
{
    setO notX;
    int ob1, ob2, disc;

    if (_mainsys->matD == NULL)
        ERROR(6);
    notX = InitEmptySetO();
    ClearSetO(lowappr);
    NotSetO(notX, X);
    for (ob1 = 0; ob1 < _mainsys->objects_num; ob1++)
        if (ContSetO(X, ob1))
        {
            disc = 1;
            for (ob2 = 0; ob2 < _mainsys->objects_num; ob2++)
                if (ContSetO(notX, ob2))
                    if (CompareD(ob1, ob2, P))
                    {
                        disc = 0;
                        break;
                    }
            if (disc)
                AddSetO(lowappr, ob1);
        }
    CloseSetO(notX);
    return 0;
}

int UppAppr(setO uppappr, setO X, setA P, int matrix_type)
{
    switch (matrix_type)
    {
    case MATA:
        return UppApprA(uppappr, X, P);
    case MATD:
        return UppApprD(uppappr, X, P);
    default:
        ERROR(8)
    }
}

int UppApprA(setO uppappr, setO X, setA P)
{
    setO notX;
    int ob1, ob2;

    if (_mainsys->matA == NULL)
        ERROR(5);
    CopySetO(uppappr, X);
    notX = InitEmptySetO();
    NotSetO(notX, X);
    for (ob1 = 0; ob1 < _mainsys->objects_num; ob1++)
        if (ContSetO(X, ob1))
            for (ob2 = 0; ob2 < _mainsys->objects_num; ob2++)
                if (ContSetO(notX, ob2))
                    if (CompareA(ob1, ob2, P))
                        AddSetO(uppappr, ob2);
    CloseSetO(notX);
    return 0;
}

int UppApprD(setO uppappr, setO X, setA P)
{
    setO notX;
    int ob1, ob2;

    if (_mainsys->matD == NULL)
        ERROR(6);
    CopySetO(uppappr, X);
    notX = InitEmptySetO();
    NotSetO(notX, X);
    for (ob1 = 0; ob1 < _mainsys->objects_num; ob1++)
        if (ContSetO(X, ob1))
            for (ob2 = 0; ob2 < _mainsys->objects_num; ob2++)
                if (ContSetO(notX, ob2))
                    if (CompareD(ob1, ob2, P))
                        AddSetO(uppappr, ob2);
    CloseSetO(notX);
    return 0;
}

int Bound(setO bound, setO X, setA P, int matrix_type)
{
    switch (matrix_type)
    {
    case MATA:
        return BoundA(bound, X, P);
    case MATD:
        return BoundD(bound, X, P);
    default:
        ERROR(8)
    }
}

int BoundA(setO bound, setO X, setA P)
{
    setO lower, upper;

    if (_mainsys->matA == NULL)
        ERROR(5);
    lower = InitEmptySetO();
    upper = InitEmptySetO();
    LowApprA(lower, X, P);
    UppApprA(upper, X, P);
    DifSetO(bound, upper, lower);
    CloseSetO(lower);
    CloseSetO(upper);
    return 0;
}

int BoundD(setO bound, setO X, setA P)
{
    setO lower, upper;

    if (_mainsys->matD == NULL)
        ERROR(6);
    lower = InitEmptySetO();
    upper = InitEmptySetO();
    LowApprD(lower, X, P);
    UppApprD(upper, X, P);
    DifSetO(bound, upper, lower);
    CloseSetO(lower);
    CloseSetO(upper);
    return 0;
}

float AccurCoef(setO X, setA P, int matrix_type)
{
    switch (matrix_type)
    {
    case MATA:
        return AccurCoefA(X, P);
    case MATD:
        return AccurCoefD(X, P);
    default:
        ERROR(8)
    }
}

float AccurCoefA(setO X, setA P)
{
    setO lower, upper;
    float coef;

    if (_mainsys->matA == NULL)
        ERROR(5);
    lower = InitEmptySetO();
    upper = InitEmptySetO();
    LowApprA(lower, X, P);
    UppApprA(upper, X, P);
    coef = (float)CardSetO(lower) / (float)CardSetO(upper);
    CloseSetO(lower);
    CloseSetO(upper);
    return coef;
}

float AccurCoefD(setO X, setA P)
{
    setO lower, upper;
    float coef;

    if (_mainsys->matD == NULL)
        ERROR(6);
    lower = InitEmptySetO();
    upper = InitEmptySetO();
    LowApprD(lower, X, P);
    UppApprD(upper, X, P);
    coef = (float)CardSetO(lower) / (float)CardSetO(upper);
    CloseSetO(lower);
    CloseSetO(upper);
    return coef;
}

float ClassCoef(setO X, setA P, int matrix_type)
{
    switch (matrix_type)
    {
    case MATA:
        return ClassCoefA(X, P);
    case MATD:
        return ClassCoefD(X, P);
    default:
        ERROR(8)
    }
}

float ClassCoefA(setO X, setA P)
{
    float coef;
    setO notX, pos;
    int ob1, ob2;

    if (_mainsys->matA == NULL)
        ERROR(5);
    notX = InitEmptySetO();
    pos = InitFullSetO();
    NotSetO(notX, X);
    for (ob1 = 0; ob1 < _mainsys->objects_num; ob1++)
        for (ob2 = 0; ob2 < _mainsys->objects_num; ob2++)
            if (ContSetO(X, ob1) && ContSetO(notX, ob2) &&
                    CompareA(ob1, ob2, P))
            {
                DelSetO(pos, ob1);
                DelSetO(pos, ob2);
            }
    coef = (float)CardSetO(pos) / _mainsys->objects_num;
    CloseSetO(notX);
    CloseSetO(pos);
    return coef;
}

float ClassCoefD(setO X, setA P)
{
    float coef;
    setO notX, pos;
    int ob1, ob2;

    if (_mainsys->matD == NULL)
        ERROR(6);
    notX = InitEmptySetO();
    pos = InitFullSetO();
    NotSetO(notX, X);
    for (ob1 = 0; ob1 < _mainsys->objects_num; ob1++)
        for (ob2 = 0; ob2 < _mainsys->objects_num; ob2++)
            if (ContSetO(X, ob1) && ContSetO(notX, ob2) &&
                    CompareD(ob1, ob2, P))
            {
                DelSetO(pos, ob1);
                DelSetO(pos, ob2);
            }
    CloseSetO(notX);
    coef = (float)CardSetO(pos) / _mainsys->objects_num;
    CloseSetO(pos);
    return coef;
}

int Pos(setO pos, setA P, setA Q, int matrix_type)
{
    switch (matrix_type)
    {
    case MATA:
        return PosA(pos, P, Q);
    case MATD:
        return PosD(pos, P, Q);
    default:
        ERROR(8)
    }
}

int PosA(setO pos, setA P, setA Q)
{
    int i, j;
    setA redQ;

    if (_mainsys->matA == NULL)
        ERROR(5);
    if (IsEmptySetA(P))
    {
        ClearSetO(pos);
        return 0;
    }
    redQ = InitEmptySetA();
    DifSetA(redQ, Q, P);
    FillSetO(pos);
    if (IsEmptySetA(redQ))
        return 0;
    for (i = _mainsys->objects_num - 1; i > 0; i--)
        for (j = i - 1; j >= 0; j--)
            if (!CompareA(i, j, redQ) && CompareA(i, j, P))
            {
                DelSetO(pos, i);
                DelSetO(pos, j);
            }
    return 0;
}

int PosD(setO pos, setA P, setA Q)
{
    int i, j;
    setA elem, redQ;

    if (_mainsys->matD == NULL)
        ERROR(6);
    if (IsEmptySetA(P))
    {
        ClearSetO(pos);
        return 0;
    }
    redQ = InitEmptySetA();
    DifSetA(redQ, Q, P);
    FillSetO(pos);
    if (IsEmptySetA(redQ))
        return 0;
    for (i = _mainsys->objects_num - 1; i > 0; i--)
        for (j = i - 1; j >= 0; j--)
        {
            elem = GetD(i, j);
            if (InterSetA(elem, redQ) && !InterSetA(elem, P))
            {
                DelSetO(pos, i);
                DelSetO(pos, j);
            }
        }
    CloseSetA(redQ);
    return 0;
}

float DependCoef(setA P, setA Q, int matrix_type)
{
    switch (matrix_type)
    {
    case MATA:
        return DependCoefA(P, Q);
    case MATD:
        return DependCoefD(P, Q);
    default:
        ERROR(8)
    }
}

float DependCoefA(setA P, setA Q)
{
    setO pos;
    float coef;

    if (_mainsys->matA == NULL)
        ERROR(5);
    pos = InitEmptySetO();
    PosA(pos, P, Q);
    coef = (float)CardSetO(pos) / (float)_mainsys->objects_num;
    CloseSetO(pos);
    return coef;
}

float DependCoefD(setA P, setA Q)
{
    setO pos;
    float coef;

    if (_mainsys->matD == NULL)
        ERROR(6);
    pos = InitEmptySetO();
    PosD(pos, P, Q);
    coef = (float)CardSetO(pos) / (float)_mainsys->objects_num;
    CloseSetO(pos);
    return coef;
}

float SignifCoef(int attr, setA P, int matrix_type)
{
    switch (matrix_type)
    {
    case MATA:
        return SignifCoefA(attr, P);
    case MATD:
        return SignifCoefD(attr, P);
    default:
        ERROR(8)
    }
}

float SignifCoefA(int attr, setA P)
{
    setO pos1, pos2;
    setA Pprim;
    int i, j;
    float coef;

    if (_mainsys->matA == NULL)
        ERROR(5);
    if (IsEmptySetA(P) || !ContSetA(P, attr))
        return 0;
    pos1 = InitFullSetO();
    pos2 = InitFullSetO();
    Pprim = InitEmptySetA();
    CopySetA(Pprim, P);
    DelSetA(Pprim, attr);
    for (i = _mainsys->objects_num - 1; i > 0; i--)
        for (j = i - 1; j >= 0; j--)
            if (CompareA(i, j, P))
            {
                DelSetO(pos1, i);
                DelSetO(pos2, i);
                DelSetO(pos1, j);
                DelSetO(pos2, j);
                continue;
            }
            else if (CompareA(i, j, Pprim))
            {
                DelSetO(pos2, i);
                DelSetO(pos2, j);
            }
    DifSetO(pos1, pos1, pos2);
    coef = (float)CardSetO(pos1) / (float)_mainsys->objects_num;
    CloseSetO(pos1);
    CloseSetO(pos2);
    CloseSetA(Pprim);
    return coef;
}

float SignifCoefD(int attr, setA P)
{
    setO pos1, pos2;
    setA Pprim, elem;
    int i, j;
    float coef;

    if (_mainsys->matD == NULL)
        ERROR(6);
    if (IsEmptySetA(P) || !ContSetA(P, attr))
        return 0;
    pos1 = InitFullSetO();
    pos2 = InitFullSetO();
    Pprim = InitEmptySetA();
    CopySetA(Pprim, P);
    DelSetA(Pprim, attr);
    for (i = _mainsys->objects_num - 1; i > 0; i--)
        for (j = i - 1; j >= 0; j--)
        {
            elem = GetD(i, j);
            if (!InterSetA(elem, P))
            {
                DelSetO(pos1, i);
                DelSetO(pos2, i);
                DelSetO(pos1, j);
                DelSetO(pos2, j);
                continue;
            }
            if (!InterSetA(elem, Pprim))
            {
                DelSetO(pos2, i);
                DelSetO(pos2, j);
            }
        }
    DifSetO(pos1, pos1, pos2);
    coef = (float)CardSetO(pos1) / (float)_mainsys->objects_num;
    CloseSetO(pos1);
    CloseSetO(pos2);
    CloseSetA(Pprim);
    return coef;
}

float SignifRelCoef(int attr, setA P, setA Q, int matrix_type)
{
    switch (matrix_type)
    {
    case MATA:
        return SignifRelCoefA(attr, P, Q);
    case MATD:
        return SignifRelCoefD(attr, P, Q);
    default:
        ERROR(8)
    }
}

float SignifRelCoefA(int attr, setA P, setA Q)
{
    setO pos1, pos2;
    setA Pprim, redQ;
    int i, j;
    float coef;

    if (_mainsys->matA == NULL)
        ERROR(5);
    Pprim = InitEmptySetA();
    redQ = InitEmptySetA();
    CopySetA(Pprim, P);
    DelSetA(Pprim, attr);
    DifSetA(redQ, Q, Pprim);
    if (IsEmptySetA(P) || !ContSetA(P, attr))
        return 0;
    if (IsEmptySetA(redQ))
        return 1;
    pos1 = InitFullSetO();
    pos2 = InitFullSetO();
    for (i = _mainsys->objects_num - 1; i > 0; i--)
        for (j = i - 1; j >= 0; j--)
            if (CompareA(i, j, redQ))
                continue;
            else if (CompareA(i, j, P))
            {
                DelSetO(pos1, i);
                DelSetO(pos2, i);
                DelSetO(pos1, j);
                DelSetO(pos2, j);
                continue;
            }
            else if (CompareA(i, j, Pprim))
            {
                DelSetO(pos2, i);
                DelSetO(pos2, j);
            }
    DifSetO(pos1, pos1, pos2);
    coef = (float)CardSetO(pos1) / (float)_mainsys->objects_num;
    CloseSetO(pos1);
    CloseSetO(pos2);
    CloseSetA(Pprim);
    CloseSetA(redQ);
    return coef;
}

float SignifRelCoefD(int attr, setA P, setA Q)
{
    setO pos1, pos2;
    setA Pprim, redQ, elem;
    int i, j;
    float coef;

    if (_mainsys->matD == NULL)
        ERROR(6);
    Pprim = InitEmptySetA();
    redQ = InitEmptySetA();
    CopySetA(Pprim, P);
    DelSetA(Pprim, attr);
    DifSetA(redQ, Q, Pprim);
    if (IsEmptySetA(P) || !ContSetA(P, attr))
        return 0;
    if (IsEmptySetA(redQ))
        return 1;
    pos1 = InitFullSetO();
    pos2 = InitFullSetO();
    for (i = _mainsys->objects_num - 1; i > 0; i--)
        for (j = i - 1; j >= 0; j--)
        {
            elem = GetD(i, j);
            if (!InterSetA(elem, redQ))
                continue;
            if (!InterSetA(elem, P))
            {
                DelSetO(pos1, i);
                DelSetO(pos2, i);
                DelSetO(pos1, j);
                DelSetO(pos2, j);
                continue;
            }
            if (!InterSetA(elem, Pprim))
            {
                DelSetO(pos2, i);
                DelSetO(pos2, j);
            }
        }
    DifSetO(pos1, pos1, pos2);
    coef = (float)CardSetO(pos1) / (float)_mainsys->objects_num;
    CloseSetO(pos1);
    CloseSetO(pos2);
    CloseSetA(Pprim);
    CloseSetA(redQ);
    return coef;
}


int CardCoef(setA P, int matrix_type)
{
    int res = 0;

    for (start_of_tab(matrix_type); end_of_tab(); next_of_tab())
        if (InterSetA(P, _table_element))
            res++;
    if (_rerror > 0)
        return -_rerror;
    return res;
}
