
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
/***                   ( FINDING REDUCTS )                                 ***/
/***                                                                       ***/
/*** part of the RSL system written by M.Gawrys J.Sienkiewicz              ***/
/***                                                                       ***/
/*****************************************************************************/


#include "rough.h"
#include <stdlib.h>


int RedRel(setA * reducts, setA P, setA Q, int matrix_type)
{
    int MEMOKWANT = _mainsys->attributes_num * _mainsys->attributes_num, j, atr, over, size = _mainsys->setAsize, memoryN = 1, memoryO = 1,	/* size of the allocated memory    */
                    newcount = 0, oldcount;	/* number of new/old reducts       */
    int no_A = _mainsys->attributes_num;
    setA arg,			/* arguments are elements of matrix */
    oldhead,			/* head of static list of reducts  */
    oldtail,			/* tail ends the old reducts list  */
    el, el1,			/* elements of this list           */
    new_el,			/* probably new element of the list */
    newhead,			/* begin of new reducts            */
    newtail;			/* tail of the list of new reducts */
    setA CORE, keep;

    CORE = InitEmptySetA();
    _rerror = 0;
    CoreRel(CORE, P, Q, matrix_type);
    if (_rerror != 0)
    {
        CloseSetA(CORE);
        return (-_rerror);
    }
    if ((oldhead = (setA) malloc(MEMOKWANT)) == NULL)
    {
        CloseSetA(CORE);
        ERROR(3);
    }
    if ((newhead = (setA) malloc(MEMOKWANT)) == NULL)
    {
        free(oldhead);
        CloseSetA(CORE);
        ERROR(3);
    }
    new_el = InitEmptySetA();
    arg = InitEmptySetA();
    oldtail = oldhead;
    newtail = newhead;
    start_of_tab(matrix_type);	/* initializing the reducts list */
    if (!IsEmptySetA(CORE))
    {
        CopySetA(oldtail, CORE);
        oldtail += size, oldcount = 1;
    }
    else
        do
        {
            AndSetA(arg, _table_element, P);
            oldcount = 0;
            if (InterSetA(_table_element, Q))
                for (atr = 0; atr < no_A; atr++)
                    if (ContSetA(arg, atr))
                    {
                        ClearSetA(oldtail);
                        AddSetA(oldtail, atr);
                        oldtail += size;
                        oldcount++;
                    }
            next_of_tab();
        }
        while ((oldcount == 0) && end_of_tab());
    for (; end_of_tab(); next_of_tab())  	/* for each element of matD do  */
    {
        AndSetA(arg, _table_element, P);	/* take next element */
        over = 0;
        if (InterSetA(CORE, arg))
            continue;
        if (!InterSetA(_table_element, Q))
            continue;
        if (IsEmptySetA(arg))
            continue;
        el = oldhead;
        while (el < oldtail)  	/* compare arg to all the old reducts  */
        {
            if (!InterSetA(el, arg))
            {
                for (atr = 0; atr < no_A; atr++)	/* for each atribute of arg  */
                    if (ContSetA(arg, atr))
                    {
                        CopySetA(new_el, el);	/* creating potentialy new reduct */
                        AddSetA(new_el, atr);
                        over = 0;
                        el1 = oldhead;
                        while ((el1 != el) && !over)  	/* comparing new reduct to old reducts */
                        {
                            over = InSetA(new_el, el1);
                            el1 += size;
                        }
                        el1 = el + size;
                        while ((el1 != oldtail) && !over)
                        {
                            over = InSetA(new_el, el1);
                            el1 += size;
                        }
                        if (!over)  	/* appending new reduct */
                        {
                            newcount++;
                            if (newcount * size * _cluster_bytes >
                                    memoryN * MEMOKWANT)
                            {
                                keep = newhead;
                                if ((newhead =
                                            (setA) realloc(keep,
                                                           MEMOKWANT *
                                                           (++memoryN))) == NULL)
                                {
                                    free(oldhead);
                                    CloseSetA(new_el);
                                    CloseSetA(arg);
                                    CloseSetA(CORE);
                                    ERROR(3);
                                }
                                if (keep != newhead)
                                    newtail = newhead + (newcount - 1) * size;
                            }
                            CopySetA(newtail, new_el);
                            newtail += size;
                        }
                    }
            }
            else  		/* if reduct covers arg - rewrite it */
            {
                newcount++;
                if (newcount * size * _cluster_bytes > memoryN * MEMOKWANT)
                {
                    keep = newhead;
                    if ((newhead =
                                (setA) realloc(keep,
                                               MEMOKWANT * (++memoryN))) == NULL)
                    {
                        free(oldhead);
                        CloseSetA(new_el);
                        CloseSetA(arg);
                        CloseSetA(CORE);
                        ERROR(3);
                    }
                    if (keep != newhead)
                        newtail = newhead + (newcount - 1) * size;
                }
                CopySetA(newtail, el);
                newtail += size;
            }
            el += size;
        }
        oldtail = newhead;	/* new reducts list becomes old */
        newhead = oldhead;
        oldhead = oldtail;
        oldtail = newtail;
        newtail = newhead;
        oldcount = newcount;
        newcount = 0;
        j = memoryO;
        memoryO = memoryN;
        memoryN = j;
    }
    if (oldcount == 0)
    {
        free(oldhead);
        *reducts = NULL;
    }
    else
        *reducts = oldhead;
    free(newhead);
    CloseSetA(CORE);
    CloseSetA(arg);
    CloseSetA(new_el);
    return (oldcount);
}

int Red(setA * reducts, int matrix_type)
{
    int j, MEMOKWANT = _mainsys->attributes_num * _mainsys->attributes_num, atr, over, size = _mainsys->setAsize, memoryN = 1, memoryO = 1,	/* size of the allocated memory    */
                       newcount = 0, oldcount;	/* number of new/old reducts       */
    int no_A = _mainsys->attributes_num;
    setA oldhead,		/* head of static list of reducts  */
    oldtail,			/* tail ends the old reducts list  */
    el, el1,			/* elements of this list           */
    new_el,			/* probably new element of the list */
    newhead,			/* begin of new reducts            */
    newtail;			/* tail of the list of new reducts */
    setA CORE, keep, and, redprim;

    CORE = InitEmptySetA();
    _rerror = 0;
    Core(CORE, matrix_type);
    if (_rerror != 0)
    {
        CloseSetA(CORE);
        return (-_rerror);
    }
    if ((oldhead = (setA) malloc(MEMOKWANT)) == NULL)
    {
        CloseSetA(CORE);
        keep = NULL;
        ERROR(3);
    }
    if ((newhead = (setA) malloc(MEMOKWANT)) == NULL)
    {
        free(oldhead);
        CloseSetA(CORE);
        ERROR(3);
    }
    new_el = InitEmptySetA();
    and = InitEmptySetA();
    redprim = InitEmptySetA();
    oldtail = oldhead;
    newtail = newhead;
    start_of_tab(matrix_type);
    if (!IsEmptySetA(CORE))  	/* initializing of the reducts list */
    {
        CopySetA(oldtail, CORE);
        oldtail += size, oldcount = 1;
    }
    else
        do
        {
            oldcount = 0;
            for (atr = 0; atr < no_A; atr++)
                if (ContSetA(_table_element, atr))
                {
                    ClearSetA(oldtail);
                    AddSetA(oldtail, atr);
                    oldtail += size;
                    oldcount++;
                }
            next_of_tab();
        }
        while ((oldcount == 0) && end_of_tab());
    for (; end_of_tab(); next_of_tab())  	/* for each element of matrix */
    {
        over = 0;
        if (InterSetA(CORE, _table_element))
            continue;
        if (IsEmptySetA(_table_element))
            continue;
        el = oldhead;
        while (el < oldtail)  	/* compare _table_element to all the old reducts  */
        {
            if (!InterSetA(el, _table_element))  	/* old reduct does not cover new element */
            {
                for (atr = 0; atr < no_A; atr++)	/* for each atribute of _table_element  */
                    if (ContSetA(_table_element, atr))
                    {
                        CopySetA(new_el, el);	/* creating potentialy new reduct */
                        AddSetA(new_el, atr);
                        over = 0;
                        el1 = oldhead;
                        /*  if ( matrix_type==MATX && (_mainsys->matXsize<(oldtail-oldhead)))
                           { ClearSetA( redprim );
                           for(el1=_mainsys->matX;el1<_table_end;el1+=size)
                           { AndSetA( and, el1, new_el );
                           if ( CardSetA( and ) == 1 ) OrSetA( redprim, redprim, and );
                           }
                           over = !CompSetA( redprim, new_el );
                           }
                           else
                         */
                        {
                            while ((el1 != el) && !over)  	/* comparing new reduct to all the old reducts */
                            {
                                over = InSetA(new_el, el1);
                                el1 += size;
                            }
                            el1 = el + size;
                            while ((el1 != oldtail) && !over)
                            {
                                over = InSetA(new_el, el1);
                                el1 += size;
                            }
                        }
                        if (!over)  	/* appending new reduct */
                        {
                            newcount++;
                            if (newcount * size * _cluster_bytes >
                                    memoryN * MEMOKWANT)
                            {
                                keep = newhead;
                                if ((newhead =
                                            (setA) realloc(keep,
                                                           MEMOKWANT *
                                                           (++memoryN))) == NULL)
                                {
                                    free(oldhead);
                                    CloseSetA(new_el);
                                    CloseSetA(CORE);
                                    ERROR(3);
                                }
                                if (keep != newhead)
                                    newtail = newhead + (newcount - 1) * size;
                            }
                            CopySetA(newtail, new_el);
                            newtail += size;
                        }
                    }
            }
            else  		/* old reduct covers new element */
            {
                newcount++;
                if (newcount * size * _cluster_bytes > memoryN * MEMOKWANT)
                {
                    keep = newhead;
                    if ((newhead =
                                (setA) realloc(keep,
                                               MEMOKWANT * (++memoryN))) == NULL)
                    {
                        free(oldhead);
                        CloseSetA(new_el);
                        CloseSetA(CORE);
                        ERROR(3);
                    }
                    if (keep != newhead)
                        newtail = newhead + (newcount - 1) * size;
                }
                CopySetA(newtail, el);
                newtail += size;
            }
            el += size;
        }
        oldtail = newhead;	/* new reducts list becomes old */
        newhead = oldhead;
        oldhead = oldtail;
        oldtail = newtail;
        newtail = newhead;
        oldcount = newcount;
        newcount = 0;
        j = memoryO;
        memoryO = memoryN;
        memoryN = j;
    }
    if (oldcount == 0)
    {
        free(oldhead);
        *reducts = NULL;
    }
    else
        *reducts = oldhead;
    free(newhead);
    CloseSetA(CORE);
    CloseSetA(new_el);
    CloseSetA(redprim);
    CloseSetA(and);
    return (oldcount);
}


int RedRelLess(setA * reducts, setA P, setA Q, int N, int matrix_type)
{
    int j, MEMOKWANT = _mainsys->attributes_num * _mainsys->attributes_num, atr, over, size = _mainsys->setAsize, memoryN = 1, memoryO = 1,	/* size of the allocated memory    */
                       newcount = 0, oldcount;	/* number of new/old reducts       */
    int no_A = _mainsys->attributes_num;
    setA arg,			/* arguments are elements of matrix */
    oldhead,			/* head of static list of reducts  */
    oldtail,			/* tail ends the old reducts list  */
    el, el1,			/* elements of this list           */
    new_el,			/* probably new element of the list */
    newhead,			/* begin of new reducts            */
    newtail;			/* tail of the list of new reducts */
    setA CORE, keep;

    CORE = InitEmptySetA();
    _rerror = 0;
    CoreRel(CORE, P, Q, matrix_type);
    if (_rerror != 0)
    {
        CloseSetA(CORE);
        return (-_rerror);
    }
    if (CardSetA(CORE) > N)
    {
        free(CORE);
        return (0);
    }
    if ((oldhead = (setA) malloc(MEMOKWANT)) == NULL)
    {
        CloseSetA(CORE);
        ERROR(3);
    }
    if ((newhead = (setA) malloc(MEMOKWANT)) == NULL)
    {
        free(oldhead);
        CloseSetA(CORE);
        ERROR(3);
    }
    new_el = InitEmptySetA();
    arg = InitEmptySetA();
    oldtail = oldhead;
    newtail = newhead;
    start_of_tab(matrix_type);
    if (!IsEmptySetA(CORE))
    {
        CopySetA(oldtail, CORE);
        oldtail += size, oldcount = 1;
    }
    else
        do
        {
            AndSetA(arg, _table_element, P);
            oldcount = 0;
            if (InterSetA(_table_element, Q))
                for (atr = 0; atr < no_A; atr++)
                    if (ContSetA(arg, atr))
                    {
                        ClearSetA(oldtail);
                        AddSetA(oldtail, atr);
                        oldtail += size;
                        oldcount++;
                    }
            next_of_tab();
        }
        while ((oldcount == 0) && end_of_tab());
    for (; end_of_tab(); next_of_tab())  	/* for each element of matrix do  */
    {
        AndSetA(arg, _table_element, P);	/* take next element */
        over = 0;
        if (InterSetA(CORE, arg))
            continue;
        if (!InterSetA(_table_element, Q))
            continue;
        if (IsEmptySetA(arg))
            continue;
        el = oldhead;
        while (el < oldtail)  	/* compare arg to all old reducts  */
        {
            if (!InterSetA(el, arg))  	/* old reduct does not cover new element */
            {
                if (CardSetA(el) < N)	/* shorter elements should be corected */
                    for (atr = 0; atr < no_A; atr++)	/* for each atribute of arg  */
                        if (ContSetA(arg, atr))
                        {
                            CopySetA(new_el, el);	/* creating potentialy new reduct */
                            AddSetA(new_el, atr);
                            over = 0;
                            el1 = oldhead;
                            while ((el1 != el) && !over)  	/* comparing new reduct to all the old list */
                            {
                                over = InSetA(new_el, el1);
                                el1 += size;
                            }
                            el1 = el + size;
                            while ((el1 != oldtail) && !over)
                            {
                                over = InSetA(new_el, el1);
                                el1 += size;
                            }
                            if (!over)  	/* appending to new list */
                            {
                                newcount++;
                                if (newcount * size * _cluster_bytes >
                                        memoryN * MEMOKWANT)
                                {
                                    keep = newhead;
                                    if ((newhead =
                                                (setA) realloc(keep,
                                                               MEMOKWANT *
                                                               (++memoryN))) ==
                                            NULL)
                                    {
                                        free(oldhead);
                                        CloseSetA(new_el);
                                        CloseSetA(arg);
                                        CloseSetA(CORE);
                                        ERROR(3);
                                    }
                                    if (keep != newhead)
                                        newtail =
                                            newhead + (newcount - 1) * size;
                                }
                                CopySetA(newtail, new_el);
                                newtail += size;
                            }
                        }
            }
            else  		/* old reduct covers new element */
            {
                newcount++;
                if (newcount * size * _cluster_bytes > memoryN * MEMOKWANT)
                {
                    keep = newhead;
                    if ((newhead =
                                (setA) realloc(keep,
                                               MEMOKWANT * (++memoryN))) == NULL)
                    {
                        free(oldhead);
                        CloseSetA(new_el);
                        CloseSetA(arg);
                        CloseSetA(CORE);
                        ERROR(3);
                    }
                    if (keep != newhead)
                        newtail = newhead + (newcount - 1) * size;
                }
                CopySetA(newtail, el);
                newtail += size;
            }
            el += size;
        }
        oldtail = newhead;	/* new list becomes old */
        newhead = oldhead;
        oldhead = oldtail;
        oldtail = newtail;
        newtail = newhead;
        oldcount = newcount;
        newcount = 0;
        j = memoryO;
        memoryO = memoryN;
        memoryN = j;
    }
    if (oldcount == 0)
    {
        free(oldhead);
        *reducts = NULL;
    }
    else
        *reducts = oldhead;
    free(newhead);
    CloseSetA(CORE);
    CloseSetA(arg);
    CloseSetA(new_el);
    return (oldcount);
}


int RedLess(setA * reducts, int N, int matrix_type)
{
    int j, MEMOKWANT = _mainsys->attributes_num * _mainsys->attributes_num, atr, over, size = _mainsys->setAsize, memoryN = 1, memoryO = 1,	/* size of the allocated memory    */
                       newcount = 0, oldcount;	/* number of new/old reducts       */
    int no_A = _mainsys->attributes_num;
    setA oldhead,		/* head of static list of reducts  */
    oldtail,			/* tail ends the old reducts list  */
    el, el1,			/* elements of this list           */
    new_el,			/* probably new element of the list */
    newhead,			/* begin of new reducts            */
    newtail;			/* tail of the list of new reducts */
    setA CORE, keep;

    CORE = InitEmptySetA();
    _rerror = 0;
    Core(CORE, matrix_type);
    if (_rerror != 0)
    {
        CloseSetA(CORE);
        return (-_rerror);
    }
    if (CardSetA(CORE) > N)
    {
        free(CORE);
        return (0);
    }
    if ((oldhead = (setA) malloc(MEMOKWANT)) == NULL)
    {
        CloseSetA(CORE);
        ERROR(3);
    }
    if ((newhead = (setA) malloc(MEMOKWANT)) == NULL)
    {
        free(oldhead);
        CloseSetA(CORE);
        ERROR(3);
    }
    new_el = InitEmptySetA();
    oldtail = oldhead;
    newtail = newhead;
    start_of_tab(matrix_type);
    if (!IsEmptySetA(CORE))  	/*initializing the reducts list  */
    {
        CopySetA(oldtail, CORE);
        oldtail += size;
        oldcount = 1;
    }
    else
        do
        {
            oldcount = 0;
            for (atr = 0; atr < no_A; atr++)
                if (ContSetA(_table_element, atr))
                {
                    ClearSetA(oldtail);
                    AddSetA(oldtail, atr);
                    oldtail += size;
                    oldcount++;
                }
            next_of_tab();
        }
        while ((oldcount == 0) && end_of_tab());
    for (; end_of_tab(); next_of_tab())  	/* for each element of matD do  */
    {
        over = 0;
        if (InterSetA(_table_element, CORE))
            continue;
        if (IsEmptySetA(_table_element))
            continue;
        el = oldhead;
        while (el < oldtail)  	/* compare _table_element to all the old reducts  */
        {
            if (!InterSetA(el, _table_element))  	/* old reduct does not cover new element */
            {
                if (CardSetA(el) < N)
                    for (atr = 0; atr < no_A; atr++)	/* for each atribute of element */
                        if (ContSetA(_table_element, atr))
                        {
                            CopySetA(new_el, el);	/* creating potentialy new reduct */
                            AddSetA(new_el, atr);
                            over = 0;
                            el1 = oldhead;	/* comparing new reduct to the old reducts */
                            while ((el1 != el) && !over)
                            {
                                over = InSetA(new_el, el1);
                                el1 += size;
                            }
                            el1 = el + size;
                            while ((el1 != oldtail) && !over)
                            {
                                over = InSetA(new_el, el1);
                                el1 += size;
                            }
                            if (!over)  	/* appending new reduct to list */
                            {
                                newcount++;
                                if (newcount * size * _cluster_bytes >
                                        memoryN * MEMOKWANT)
                                {
                                    keep = newhead;
                                    if ((newhead =
                                                (setA) realloc(keep,
                                                               MEMOKWANT *
                                                               (++memoryN))) ==
                                            NULL)
                                    {
                                        free(oldhead);
                                        CloseSetA(new_el);
                                        CloseSetA(CORE);
                                        ERROR(3);
                                    }
                                    if (keep != newhead)
                                        newtail =
                                            newhead + (newcount - 1) * size;
                                }
                                CopySetA(newtail, new_el);
                                newtail += size;
                            }
                        }
            }
            else  		/* old reduct covers new element */
            {
                newcount++;
                if (newcount * size * _cluster_bytes > memoryN * MEMOKWANT)
                {
                    keep = newhead;
                    if ((newhead =
                                (setA) realloc(keep,
                                               MEMOKWANT * (++memoryN))) == NULL)
                    {
                        free(oldhead);
                        CloseSetA(new_el);
                        CloseSetA(CORE);
                        ERROR(3);
                    }
                    if (keep != newhead)
                        newtail = newhead + (newcount - 1) * size;
                }
                CopySetA(newtail, el);
                newtail += size;
            }
            el += size;
        }
        oldtail = newhead;	/* new list becomes old */
        newhead = oldhead;
        oldhead = oldtail;
        oldtail = newtail;
        newtail = newhead;
        oldcount = newcount;
        newcount = 0;
        j = memoryO;
        memoryO = memoryN;
        memoryN = j;
    }
    if (oldcount == 0)
    {
        free(oldhead);
        *reducts = NULL;
    }
    else
        *reducts = oldhead;
    free(newhead);
    CloseSetA(CORE);
    CloseSetA(new_el);
    return (oldcount);
}


int RedRelSetA(setA * reducts, setA quasicore, setA P, setA Q,
               int matrix_type)
{
    int j, MEMOKWANT = _mainsys->attributes_num * _mainsys->attributes_num, atr, over, size = _mainsys->setAsize, memoryN = 1, memoryO = 1,	/* size of the allocated memory    */
                       newcount = 0, oldcount;	/* number of new/old reducts       */
    int no_A = _mainsys->attributes_num;
    setA arg,			/* arguments are elements of matrix */
    oldhead,			/* head of static list of reducts  */
    oldtail,			/* tail ends the old reducts list  */
    el, el1,			/* elements of this list           */
    new_el,			/* probably new element of the list */
    newhead,			/* begin of new reducts            */
    newtail;			/* tail of the list of new reducts */
    setA CORE, keep;

    CORE = InitEmptySetA();
    _rerror = 0;
    CoreRel(CORE, P, Q, matrix_type);
    if (_rerror != 0)
    {
        CloseSetA(CORE);
        return (-_rerror);
    }
    OrSetA(CORE, CORE, quasicore);
    if ((oldhead = (setA) malloc(MEMOKWANT)) == NULL)
    {
        CloseSetA(CORE);
        ERROR(3);
    }
    if ((newhead = (setA) malloc(MEMOKWANT)) == NULL)
    {
        free(oldhead);
        CloseSetA(CORE);
        ERROR(3);
    }
    new_el = InitEmptySetA();
    arg = InitEmptySetA();
    oldtail = oldhead;
    newtail = newhead;
    start_of_tab(matrix_type);
    if (!IsEmptySetA(CORE))  	/*initializing the reducts list */
    {
        CopySetA(oldtail, CORE);
        oldtail += size;
        oldcount = 1;
    }
    else
        do
        {
            AndSetA(arg, _table_element, P);
            oldcount = 0;
            if (InterSetA(_table_element, Q))
                for (atr = 0; atr < no_A; atr++)
                    if (ContSetA(arg, atr))
                    {
                        ClearSetA(oldtail);
                        AddSetA(oldtail, atr);
                        oldtail += size;
                        oldcount++;
                    }
            next_of_tab();
        }
        while ((oldcount == 0) && end_of_tab());
    for (; end_of_tab(); next_of_tab())  	/* for each element of matrix do  */
    {
        AndSetA(arg, _table_element, P);	/* take next element */
        over = 0;
        if (InterSetA(CORE, arg))
            continue;
        if (!InterSetA(_table_element, Q))
            continue;
        if (IsEmptySetA(arg))
            continue;
        el = oldhead;
        while (el < oldtail)  	/* compare element to all the old reducts  */
        {
            if (!InterSetA(el, arg))  	/* old reduct does not cover new element */
            {
                for (atr = 0; atr < no_A; atr++)	/* for each atribute of element */
                    if (ContSetA(arg, atr))
                    {
                        CopySetA(new_el, el);	/* creating potentialy new reduct */
                        AddSetA(new_el, atr);
                        over = 0;
                        el1 = oldhead;
                        while ((el1 != el) && !over)  	/* comparing new reduct to all the old reducts */
                        {
                            over = InSetA(new_el, el1);
                            el1 += size;
                        }
                        el1 = el + size;
                        while ((el1 != oldtail) && !over)
                        {
                            over = InSetA(new_el, el1);
                            el1 += size;
                        }
                        if (!over)  	/* appending new reduct to list */
                        {
                            newcount++;
                            if (newcount * size * _cluster_bytes >
                                    memoryN * MEMOKWANT)
                            {
                                keep = newhead;
                                if ((newhead =
                                            (setA) realloc(keep,
                                                           MEMOKWANT *
                                                           (++memoryN))) == NULL)
                                {
                                    free(oldhead);
                                    CloseSetA(new_el);
                                    CloseSetA(arg);
                                    CloseSetA(CORE);
                                    ERROR(3);
                                }
                                if (keep != newhead)
                                    newtail = newhead + (newcount - 1) * size;
                            }
                            CopySetA(newtail, new_el);
                            newtail += size;
                        }
                    }
            }
            else  		/* old reduct covers new elemet */
            {
                newcount++;
                if (newcount * size * _cluster_bytes > memoryN * MEMOKWANT)
                {
                    keep = newhead;
                    if ((newhead =
                                (setA) realloc(keep,
                                               MEMOKWANT * (++memoryN))) == NULL)
                    {
                        free(oldhead);
                        CloseSetA(new_el);
                        CloseSetA(arg);
                        CloseSetA(CORE);
                        ERROR(3);
                    }
                    if (keep != newhead)
                        newtail = newhead + (newcount - 1) * size;
                }
                CopySetA(newtail, el);
                newtail += size;
            }
            el += size;
        }
        oldtail = newhead;	/*  new list becomes old */
        newhead = oldhead;
        oldhead = oldtail;
        oldtail = newtail;
        newtail = newhead;
        oldcount = newcount;
        newcount = 0;
        j = memoryO;
        memoryO = memoryN;
        memoryN = j;
    }
    if (oldcount == 0)
    {
        free(oldhead);
        *reducts = NULL;
    }
    else
        *reducts = oldhead;
    free(newhead);
    CloseSetA(CORE);
    CloseSetA(arg);
    CloseSetA(new_el);
    return (oldcount);
}

int RedSetA(setA * reducts, setA quasicore, int matrix_type)
{
    int j, MEMOKWANT = _mainsys->attributes_num * _mainsys->attributes_num, atr, over, size = _mainsys->setAsize, memoryN = 1, memoryO = 1,	/* size of the allocated memory  */
                       newcount = 0, oldcount;	/* number of new/old reducts  */
    int no_A = _mainsys->attributes_num;
    setA oldhead,		/* head of static list of reducts  */
    oldtail,			/* tail ends the old reducts list  */
    el, el1,			/* elements of this list           */
    new_el,			/* probably new element of the list */
    newhead,			/* begin of new reducts            */
    newtail;			/* tail of the list of new reducts */
    setA CORE, keep;

    CORE = InitEmptySetA();
    _rerror = 0;
    Core(CORE, matrix_type);
    if (_rerror != 0)
    {
        CloseSetA(CORE);
        return (-_rerror);
    }
    OrSetA(CORE, CORE, quasicore);
    if ((oldhead = (setA) malloc(MEMOKWANT)) == NULL)
    {
        CloseSetA(CORE);
        ERROR(3);
    }
    if ((newhead = (setA) malloc(MEMOKWANT)) == NULL)
    {
        free(oldhead);
        CloseSetA(CORE);
        ERROR(3);
    }
    new_el = InitEmptySetA();
    oldtail = oldhead;
    newtail = newhead;
    start_of_tab(matrix_type);
    if (!IsEmptySetA(CORE))  	/*initializing  the reducts list */
    {
        CopySetA(oldtail, CORE);
        oldtail += size, oldcount = 1;
    }
    else
        do
        {
            oldcount = 0;
            for (atr = 0; atr < no_A; atr++)
                if (ContSetA(_table_element, atr))
                {
                    ClearSetA(oldtail);
                    AddSetA(oldtail, atr);
                    oldtail += size;
                    oldcount++;
                }
            next_of_tab();
        }
        while ((oldcount == 0) && end_of_tab());
    for (; end_of_tab(); next_of_tab())  	/* for each element of matrix do  */
    {
        over = 0;
        if (InterSetA(_table_element, CORE))
            continue;
        if (IsEmptySetA(_table_element))
            continue;
        el = oldhead;
        while (el < oldtail)  	/* compare elment to all the old reducts  */
        {
            if (!InterSetA(el, _table_element))  	/* old reduct does not cover element */
            {
                for (atr = 0; atr < no_A; atr++)	/* for each atribute of element  */
                    if (ContSetA(_table_element, atr))
                    {
                        CopySetA(new_el, el);	/* creating potentialy new reduct */
                        AddSetA(new_el, atr);
                        over = 0;
                        el1 = oldhead;
                        while ((el1 != el) && !over)  	/* comparing new reduct to all the old reducts */
                        {
                            over = InSetA(new_el, el1);
                            el1 += size;
                        }
                        el1 = el + size;
                        while ((el1 != oldtail) && !over)
                        {
                            over = InSetA(new_el, el1);
                            el1 += size;
                        }
                        if (!over)  	/* appending new reduct to list */
                        {
                            newcount++;
                            if (newcount * size * _cluster_bytes >
                                    memoryN * MEMOKWANT)
                            {
                                keep = newhead;
                                if ((newhead =
                                            (setA) realloc(keep,
                                                           MEMOKWANT *
                                                           (++memoryN))) == NULL)
                                {
                                    free(oldhead);
                                    CloseSetA(new_el);
                                    CloseSetA(CORE);
                                    ERROR(3);
                                }
                                if (keep != newhead)
                                    newtail = newhead + (newcount - 1) * size;
                            }
                            CopySetA(newtail, new_el);
                            newtail += size;
                        }
                    }
            }
            else  		/* old reduct covers new element */
            {
                newcount++;
                if (newcount * size * _cluster_bytes > memoryN * MEMOKWANT)
                {
                    keep = newhead;
                    if ((newhead =
                                (setA) realloc(keep,
                                               MEMOKWANT * (++memoryN))) == NULL)
                    {
                        free(oldhead);
                        CloseSetA(new_el);
                        CloseSetA(CORE);
                        ERROR(3);
                    }
                    if (keep != newhead)
                        newtail = newhead + (newcount - 1) * size;
                }
                CopySetA(newtail, el);
                newtail += size;
            }
            el += size;
        }
        oldtail = newhead;	/* new list becomes old */
        newhead = oldhead;
        oldhead = oldtail;
        oldtail = newtail;
        newtail = newhead;
        oldcount = newcount;
        newcount = 0;
        j = memoryO;
        memoryO = memoryN;
        memoryN = j;
    }
    if (oldcount == 0)
    {
        free(oldhead);
        *reducts = NULL;
    }
    else
        *reducts = oldhead;
    free(newhead);
    CloseSetA(CORE);
    CloseSetA(new_el);
    return (oldcount);
}

int RedRelFirst(setA * reducts, setA P, setA Q, int N, int matrix_type)
{
    int atr, over, size = _mainsys->setAsize, newcount = 0, oldcount;	/* number of new,old reducts       */
    int no_A = _mainsys->attributes_num;
    setA arg,			/* arguments are elements of matrix */
    oldhead,			/* head of static list of reducts  */
    oldtail,			/* tail ends the old reducts list  */
    el, el1,			/* elements of this list           */
    new_el,			/* probably new element of the list */
    newhead,			/* begin of new reducts            */
    newtail;			/* tail of the list of new reducts */
    setA CORE;

    if (N == 0)
        return 0;
    CORE = InitEmptySetA();
    _rerror = 0;
    CoreRel(CORE, P, Q, matrix_type);
    if (_rerror != 0)
    {
        CloseSetA(CORE);
        return (-_rerror);
    }
    if ((oldhead = (setA) malloc(N * size * _cluster_bytes)) == NULL)
    {
        CloseSetA(CORE);
        ERROR(3);
    }
    if ((newhead = (setA) malloc(N * size * _cluster_bytes)) == NULL)
    {
        free(oldhead);
        CloseSetA(CORE);
        ERROR(3);
    }
    new_el = InitEmptySetA();
    arg = InitEmptySetA();
    oldtail = oldhead;
    newtail = newhead;
    start_of_tab(matrix_type);
    if (!IsEmptySetA(CORE))  	/* initializing  the reducts list  */
    {
        CopySetA(oldtail, CORE);
        oldtail += size, oldcount = 1;
    }
    else
        do
        {
            AndSetA(arg, _table_element, P);
            oldcount = 0;
            if (InterSetA(_table_element, Q))
                for (atr = 0; atr < no_A; atr++)
                    if (ContSetA(arg, atr) && (oldcount < N))
                    {
                        ClearSetA(oldtail);
                        AddSetA(oldtail, atr);
                        oldtail += size;
                        oldcount++;
                    }
            next_of_tab();
        }
        while ((oldcount == 0) && end_of_tab());
    for (; end_of_tab(); next_of_tab())  	/* for each element of matrix do */
    {
        AndSetA(arg, _table_element, P);	/* take next element */
        over = 0;
        if (InterSetA(CORE, arg))
            continue;
        if (!InterSetA(_table_element, Q))
            continue;
        if (IsEmptySetA(arg))
            continue;
        el = oldhead;
        while (el < oldtail)  	/* compare element to all the old reducts  */
        {
            if (!InterSetA(el, arg))  	/* old reduct does not cover element */
            {
                for (atr = 0; atr < no_A; atr++)	/* for each atribute of elememt */
                    if (ContSetA(arg, atr) && (newcount < N))
                    {
                        CopySetA(new_el, el);	/* creating potentialy new reduct */
                        AddSetA(new_el, atr);
                        over = 0;
                        el1 = oldhead;
                        while ((el1 != el) && !over)  	/* comparing new reduct to all the old reducts */
                        {
                            over = InSetA(new_el, el1);
                            el1 += size;
                        }
                        el1 = el + size;
                        while ((el1 != oldtail) && !over)
                        {
                            over = InSetA(new_el, el1);
                            el1 += size;
                        }
                        if (!over)  	/* appending new reduct to list */
                        {
                            CopySetA(newtail, new_el);
                            newtail += size;
                            newcount++;
                        }
                    }
            }
            else if (newcount < N)
            {
                CopySetA(newtail, el);
                newtail += size;
                newcount++;
            }
            el += size;
        }
        oldtail = newhead;	/* new list becomes old */
        newhead = oldhead;
        oldhead = oldtail;
        oldtail = newtail;
        newtail = newhead;
        oldcount = newcount;
        newcount = 0;
    }
    if (oldcount == 0)
    {
        free(oldhead);
        *reducts = NULL;
    }
    else
        *reducts = oldhead;
    free(newhead);
    CloseSetA(CORE);
    CloseSetA(arg);
    CloseSetA(new_el);
    return (oldcount);
}

int RedFirst(setA * reducts, int N, int matrix_type)
{
    int atr, over, size = _mainsys->setAsize, newcount = 0, oldcount;	/* sizes of reduct lists */
    int no_A = _mainsys->attributes_num;
    setA oldhead,		/* head of static list of reducts  */
    oldtail,			/* tail ends the old reducts list  */
    el, el1,			/* elements of this list           */
    new_el,			/* probably new element of the list */
    newhead,			/* begin of new reducts            */
    newtail;			/* tail of the list of new reducts */
    setA CORE;

    if (N == 0)
        return 0;
    CORE = InitEmptySetA();
    _rerror = 0;
    Core(CORE, matrix_type);
    if (_rerror != 0)
    {
        CloseSetA(CORE);
        return (-_rerror);
    }
    if ((oldhead = (setA) malloc(N * size * _cluster_bytes)) == NULL)
    {
        CloseSetA(CORE);
        ERROR(3);
    }
    if ((newhead = (setA) malloc(N * size * _cluster_bytes)) == NULL)
    {
        free(oldhead);
        CloseSetA(CORE);
        ERROR(3);
    }
    new_el = InitEmptySetA();
    oldtail = oldhead;
    newtail = newhead;
    start_of_tab(matrix_type);
    if (!IsEmptySetA(CORE))  	/*initializing  the reducts list */
    {
        CopySetA(oldtail, CORE);
        oldtail += size, oldcount = 1;
    }
    else
        do
        {
            oldcount = 0;
            for (atr = 0; atr < no_A; atr++)
                if (ContSetA(_table_element, atr) && (oldcount < N))
                {
                    ClearSetA(oldtail);
                    AddSetA(oldtail, atr);
                    oldtail += size;
                    oldcount++;
                }
            next_of_tab();
        }
        while ((oldcount == 0) && end_of_tab());
    for (; end_of_tab(); next_of_tab())  	/* for each element of matrix do  */
    {
        over = 0;
        if (InterSetA(_table_element, CORE))
            continue;
        if (IsEmptySetA(_table_element))
            continue;
        el = oldhead;
        while (el < oldtail)  	/* compare element to all the old reducts  */
        {
            if (!InterSetA(el, _table_element))  	/* old reduct does not cover element */
            {
                for (atr = 0; atr < no_A; atr++)	/* for each atribute of element  */
                    if (ContSetA(_table_element, atr) && (newcount < N))
                    {
                        CopySetA(new_el, el);	/* creating potentialy new element */
                        AddSetA(new_el, atr);
                        over = 0;
                        el1 = oldhead;
                        while ((el1 != el) && !over)  	/* comparing new reduct to old list */
                        {
                            over = InSetA(new_el, el1);
                            el1 += size;
                        }
                        el1 = el + size;
                        while ((el1 != oldtail) && !over)
                        {
                            over = InSetA(new_el, el1);
                            el1 += size;
                        }
                        if (!over)
                        {
                            CopySetA(newtail, new_el);
                            newtail += size;
                            newcount++;
                        }
                    }
            }
            else if (newcount < N)
            {
                CopySetA(newtail, el);	/* rewriting reduct from old list */
                newtail += size;
                newcount++;
            }
            el += size;
        }
        oldtail = newhead;	/* new list becomes old */
        newhead = oldhead;
        oldhead = oldtail;
        oldtail = newtail;
        newtail = newhead;
        oldcount = newcount;
        newcount = 0;
    }
    if (oldcount == 0)
    {
        free(oldhead);
        *reducts = NULL;
    }
    else
        *reducts = oldhead;
    free(newhead);
    CloseSetA(CORE);
    CloseSetA(new_el);
    return (oldcount);
}
