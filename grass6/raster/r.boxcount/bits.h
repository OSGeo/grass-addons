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
#ifndef BITSH
#define BITSH

unsigned Bits (unsigned int, int, int);
int Bits_available (char);
unsigned int Create_chunked_bit_string (unsigned int,
					unsigned int, int);
unsigned int Create_cyclic_bit_string (unsigned int,
				       unsigned int, int);
int Bits_in_pwr_two_can_sqr_and_store_in (char);

#endif
