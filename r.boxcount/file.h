/****************************************************************************
 *
 * MODULE:       r.boxcount
 * AUTHOR(S):    
 *
 *  Original author:
 *  Mark Lake  14/5/99
 *  
 *  University College London
 *  Institute of Archaeology
 *  31-34 Gordon Square
 *  London.  WC1H 0PY
 *  email: mark.lake@ucl.ac.uk
 * 
 *  Adaptations for grass63:
 *  Florian Kindl, 2006-10-02
 *  University of Innsbruck
 *  Institute of Geography
 *  email: florian.kindl@uibk.ac.at
 *
 *
 * COPYRIGHT:    (C) 2008 by the authors
 *  
 *               This program is free software under the GNU General Public
 *   	    	 License (>=v2). Read the file COPYING that comes with GRASS
 *   	    	 for details.
 *
 *****************************************************************************/
#ifndef FILEH
#define FILEH

#include <stdio.h>
#include "record.h"

FILE* Create_file (char*, char*, char*, int);
void Pretty_print (FILE*, tRecord*, int, int, int, float*);
void Functional_print (FILE*, tRecord*, int, float*);
void Print_gnuplot_commands (FILE*, char*, tRecord*, int, int, int, float*);
void Terse_print (FILE*, int, int, float*);

#endif
