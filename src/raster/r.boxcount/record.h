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
#ifndef RECORDH
#define RECORDH

typedef struct 
{
  unsigned long int occupied;
  float log_occupied;
  float size;
  float log_reciprocal_size;
  float d;
} tRecord;

#endif
