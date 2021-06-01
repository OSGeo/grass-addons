
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

/***         OPTIONAL ERROR HANDLING AND ERROR MESSAGES                    ***/

/***                                                                       ***/

/*** part of the RSL system written by M.Gawrys J. Sienkiewicz             ***/

/***                                                                       ***/

/*****************************************************************************/


char *errcodes[10] = { "everything O.K.",
    "Cannot open file",
    "Wrong format of file",
    "Not enough memory",
    "Cannot write to file",
    "Matrix A not initialized",
    "Matrix D not initialized",
    "Matrix X not initialized",
    "Wrong matrix type",
    "Set element out of domain"
};

#define ErrorPrint() {printf("ERROR no: %i: %s\n",_rerror,errcodes[_rerror]);_rerror=0;}
