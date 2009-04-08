/* 

   Copyright (C) 2006 Thomas Hazel, Laura Toma, Jan Vahrenhold and
   Rajiv Wickremesinghe

   This program is free software; you can redistribute it and/or
   modify it under the terms of the GNU General Public License as
   published by the Free Software Foundation; either version 2 of the
   License, or (at your option) any later version.

   This program is distributed in the hope that it will be useful, but
   WITHOUT ANY WARRANTY; without even the implied warranty of
   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
   General Public License for more details.

*/

#include <stdio.h>

#if __FreeBSD__ &&  __i386__
# define LDFMT "%qd"
#else
# if __linux__
#   define LDFMT "%lld"
# else
#   ifdef  __APPLE__
#     define LDFMT "%lld"
#   else
#     define LDFMT "%ld"
#   endif
# endif
#endif
char *
formatNumber(char *buf, long long val) {
  static char sbuf[BUFSIZ];

  // use the non-reentrant static buffer if we got passed a NULL
  if(!buf) {
    buf = sbuf;
  }

  if(val > (1<<30)) {
	sprintf(buf, "%.2fG (" LDFMT ")", (double)val/(1<<30), val);
  } else if(val > (1<<20)) {
	sprintf(buf, "%.2fM (" LDFMT ")", (double)val/(1<<20), val);
  } else if(val > (1<<10)) {
	sprintf(buf, "%.2fK (" LDFMT ")", (double)val/(1<<10), val);
  } else {
	sprintf(buf, LDFMT, val);
  }
  return buf;
}
