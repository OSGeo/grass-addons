#include "strahler.h"

int StrahWriteToFile( DBBUF *dbbuf, int nlines, FILE *txout )
{
	int line;

	G_debug( 1, "Reached WriteToFile - writing %d lines", nlines);
	fprintf( txout, "== Result of Strahler Order ==\n" );
	fprintf( txout, " Line:   Basin:    Order:\n" );
	for ( line=1; line<=nlines; line++) {
		fprintf( txout, "%8d%8d%8d\n",dbbuf[line].line, dbbuf[line].bsnid, dbbuf[line].sorder);
	}
	return 1;
}
