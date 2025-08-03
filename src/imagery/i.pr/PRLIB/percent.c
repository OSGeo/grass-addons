/*
   The following routines are written and tested by Stefano Merler

   for

   status of a loop computation
 */

#include <stdio.h>

static int prev = -1;

void percent(int n, int d, int s)

/*
   compute percentage (and print to stderr)
   of work done within a loop.
   n actual number, d total number, s step
 */
{
    register int x;

    if (d <= 0 || s <= 0)
        x = 100;
    else {
        x = n * 100 / d;
        if (x % s)
            return;
    }
    if (n <= 0 || n >= d || x != prev) {
        prev = x;
        fprintf(stderr, "%4d%%\b\b\b\b\b", x);
        fflush(stderr);
    }
    if (x >= 100) {
        fprintf(stderr, "\n");
        prev = -1;
    }
}
