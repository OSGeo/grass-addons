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
