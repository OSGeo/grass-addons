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
 * PURPOSE: 
 * These functions manipuluate individual bits and might
 * need modification on a Big-Endian machine (e.g SPARC, 68xxx).  
 * This code was developed on an 80x86.
 *  
 *
 * COPYRIGHT:    (C) 2008 by the authors
 *  
 *               This program is free software under the GNU General Public
 *   	    	 License (>=v2). Read the file COPYING that comes with GRASS
 *   	    	 for details.
 *
 *****************************************************************************/




#include <stdlib.h>
#include <stdio.h>
#include <math.h>
#include <limits.h>
#include "bits.h"


/**************************************************************************/

unsigned Bits (unsigned int a, int k, int j)
{
  /* Return the j bits which occur k bits from 
     the right (i.e. the 8th bit occurs 7 bits
     from the right) */

  return (a >> k) & ~(~0 << j);
}


/**************************************************************************/

int Bits_available (char type)
{
  unsigned long int actual, expected;
  int bits;

  if (type == 'l')
    {
      actual = ULONG_MAX;
      expected = 4294967295UL;
      bits = 31;
    }

  if (type == 'i')
    {
      actual = UINT_MAX;
      expected = 4294967295UL;
      bits = 31;
    }

  if (type == 's')
    {
      actual = USHRT_MAX;
      expected = 65535;
      bits = 15;
    }

  if (actual != expected)
    {
      fprintf (stderr, "\n *** Word length of integer not as expected *** \n");
      fflush (stderr);
      bits = 0;
    }

  return bits;
}


/**************************************************************************/

unsigned int Create_chunked_bit_string (unsigned int a,
					unsigned int b, int k)
{
  /* This function takes 2 bit strings of length k and
     concatenates them.  For example if a=1101 (13) and 
     b=1001 (9) then the result will be 11011001 (217) 

     Left shift a by k positions and then add b */
  
  return ((a << k) + b);
}


/**************************************************************************/

unsigned int Create_cyclic_bit_string (unsigned int a,
				       unsigned int b, int k)
{
  /* This function combines 2 bit strings of length k
     into one string of length 2*k such that the individual
     bits of a and b are ordered:
     k   bit of a -> 2k   bit of bitstr
     k   bit of b -> 2k-1 bit of bitstr
     k-1 bit of a -> 2k-2 bit of bitstr
     k-1 bit of b -> 2k-3 bit of bitstr
     k-2 bit of a -> 2k-4 bit of bitstr
       ...
     k-(k-1) bit of b -> 2k-(2k-1) bit of bitstr */

  unsigned int bitstr;
  int bit, ls;

  bitstr = 0;
  ls = 2 * k;
  for (bit = k - 1; bit >= 0; bit --)
    {
      ls --;
      bitstr += Bits (a, bit, 1) << ls;
      ls --;
      bitstr += Bits (b, bit, 1) << ls;
    }
  return bitstr;
}


/**************************************************************************/

int Bits_in_pwr_two_can_sqr_and_store_in (char type)
{
  int bits;

  bits = Bits_available (type);


  /* Word which is an even no. of bits can store
     2^x * 2^x where x = bits / 2.  Word which is
     an odd no. of bits can store 2^x * 2^x where
     x = (bits + 1) / 2 */

  if (fmod (bits, 2) != 1)
    return (bits / 2);
  else
    return ((int) ((bits + 1) / 2));
}
