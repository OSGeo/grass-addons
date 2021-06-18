
/****************************************************************************
 *
 * MODULE:       r.roughset
 * AUTHOR(S):    GRASS module authors ad Rough Set Library (RSL) maintain:
 *			G.Massei (g_massa@libero.it)-A.Boggia (boggia@unipg.it)
 *			Rough Set Library (RSL) ver. 2 original develop:
 *		        M.Gawrys - J.Sienkiewicz
 *
 * PURPOSE:      Geographics rough set analisys and knowledge discovery
 *
 * COPYRIGHT:    (C) A.Boggia - G.Massei (2008)
 *
 *               This program is free software under the GNU General Public
 *   	    	 License (>=v2). Read the file COPYING that comes with GRASS
 *   	    	 for details.
 *
 *****************************************************************************

            FUNCTION OF ACCESS TO SYSTEM TABLES

 part of the ROUGH system written by M.Gawrys J. Sienkiewicz

****************************************************************************/


#include "rough.h"

setA _table_element = NULL;
setA _table_end = NULL;
int _table_row;
int _table_column;
int _table_no;

static void (*_current_next) (void);

void next_of_d(void)
{
    if (++_table_column >= _table_row)
        _table_column = 0, _table_row++;
    _table_element = (_mainsys->matD) + (_mainsys->setAsize * ++_table_no);
}

void next_of_x(void)
{
    _table_element += _mainsys->setAsize;
    ++_table_no;
}

void next_of_a(void)
{
    ++_table_no;
    if (++_table_column >= _table_row)
    {
        _table_column = 0;
        if (++_table_row >= _mainsys->objects_num)
        {
            CloseSetA(_table_element);
            _table_end = _table_element;
            _table_row = 0;
            return;
        }
    }
    GetDfromA(_table_element, _table_row, _table_column);
    return;
}


int start_of_tab(int matrix_type)
{
    if (matrix_type == MATD)
    {
        _table_no = 0;
        _table_row = 1;
        _table_column = 0;
        _table_element = _mainsys->matD;
        _table_end = _table_element + Dsize(_mainsys);
        _current_next = next_of_d;
    }
    else if (matrix_type == MATX)
    {
        START_OF_X;
        _table_no = 0;
        _current_next = next_of_x;
    }
    else if (matrix_type == MATA)
    {
        _table_no = 0;
        _table_row = 0;
        _table_column = 0;
        _table_element = InitEmptySetA();
        _table_end = _table_element + 1;
        _current_next = next_of_a;
        next_of_a();
    }
    if (_table_element == NULL)
        ERROR(3)
        return (1);
}

int end_of_tab(void)
{
    return (_table_element < _table_end);
}

void next_of_tab(void)
{
    (*_current_next) ();
}


setA GetD(int ob1, int ob2)
{
    int pom;

    if (ob2 > ob1)
    {
        pom = ob1;
        ob1 = ob2;
        ob2 = pom;
    }
    return (_mainsys->matD) + ((ob1 - 1) * ob1 / 2 +
                               ob2) * _mainsys->setAsize;
}

value_type GetA(int ob, int atr)
{
    return (_mainsys->matA)[ob * (_mainsys->attributes_num) + atr];
}

int GetDfromA(setA elem, int obj1, int obj2)
{
    int nby = (_mainsys->attributes_num) / _cluster_bits;	/* number of full clusters in element */
    int nbi = _mainsys->attributes_num % _cluster_bits;	/* number of bits in the last cluster */
    int atrnum = _mainsys->attributes_num;	/* number of attributes */
    value_type *A = _mainsys->matA;
    cluster_type val;
    int cluster, bit;

    for (cluster = 0; cluster < nby; cluster++)
    {
        val = 0;
        for (bit = 0; bit < _cluster_bits; bit++)
            if (A[obj1 * atrnum + _cluster_bits * cluster + bit] !=
                    A[obj2 * atrnum + _cluster_bits * cluster + bit] &&
                    A[obj1 * atrnum + _cluster_bits * cluster + bit] !=
                    (value_type) - 1 &&
                    A[obj2 * atrnum + _cluster_bits * cluster + bit] !=
                    (value_type) - 1)
                val = val | _mask[bit];
        elem[cluster] = val;
    }
    if (nbi)
    {
        val = 0;
        for (bit = 0; bit < nbi; bit++)
            if (A[obj1 * atrnum + _cluster_bits * cluster + bit] !=
                    A[obj2 * atrnum + _cluster_bits * cluster + bit] &&
                    A[obj1 * atrnum + _cluster_bits * cluster + bit] !=
                    (value_type) - 1 &&
                    A[obj2 * atrnum + _cluster_bits * cluster + bit] !=
                    (value_type) - 1)
                val = val | _mask[bit];
        elem[cluster] = val;
    }
    return 1;
}

int CompareA(int ob1, int ob2, setA P)
{
    int attr;

    for (attr = 0; attr < _mainsys->attributes_num; attr++)
        if (ContSetA(P, attr))
            if ((_mainsys->matA)[ob1 * (_mainsys->attributes_num) + attr] ==
                    (value_type) - 1 ||
                    (_mainsys->matA)[ob2 * (_mainsys->attributes_num) + attr] ==
                    (value_type) - 1)
                continue;
            else if ((_mainsys->matA)[ob1 * (_mainsys->attributes_num) +
                                      attr] !=
                     (_mainsys->matA)[ob2 * (_mainsys->attributes_num) +
                                      attr])
                return 0;
    return 1;
}

int CompareD(int ob1, int ob2, setA P)
{
    int pom;
    int cluster;
    setA elem;

    if (ob2 > ob1)
    {
        pom = ob1;
        ob1 = ob2;
        ob2 = pom;
    }
    elem =
        (_mainsys->matD) + ((ob1 - 1) * ob1 / 2 + ob2) * (_mainsys->setAsize);
    for (cluster = _mainsys->setAsize - 1; cluster >= 0; cluster--)
        if (elem[cluster] & P[cluster])
            return 0;
    return 1;
}

int SingCompA(int ob1, int ob2, int atr)
{
    return ((_mainsys->matA)[ob1 * (_mainsys->attributes_num) + atr] ==
            (_mainsys->matA)[ob2 * (_mainsys->attributes_num) + atr] ||
            (_mainsys->matA)[ob1 * (_mainsys->attributes_num) + atr] ==
            (value_type) - 1 ||
            (_mainsys->matA)[ob2 * (_mainsys->attributes_num) + atr] ==
            (value_type) - 1);
}

int SingCompD(int ob1, int ob2, int atr)
{
    int pom;

    if (ob2 > ob1)
    {
        pom = ob1;
        ob1 = ob2;
        ob2 = pom;
    }
    return !((_mainsys->matD)[((ob1 - 1) * ob1 / 2 + ob2)
                              * (_mainsys->setAsize) +
                              atr / _cluster_bits] & _mask[atr %
                                                           _cluster_bits]);
}
