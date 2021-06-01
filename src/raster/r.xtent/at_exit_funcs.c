/***************************************************************************
 *            at_exit_funcs.c
 *
 *  Mon Apr 18 14:52:20 2005
 *  Copyright  2005  Benjamin Ducke
 ****************************************************************************/

/*
 *  This program is free software; you can redistribute it and/or modify
 *  it under the terms of the GNU General Public License as published by
 *  the Free Software Foundation; either version 2 of the License, or
 *  (at your option) any later version.
 *
 *  This program is distributed in the hope that it will be useful,
 *  but WITHOUT ANY WARRANTY; without even the implied warranty of
 *  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 *  GNU Library General Public License for more details.
 *
 *  You should have received a copy of the GNU General Public License
 *  along with this program; if not, write to the Free Software
 *  Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.
 */


#include <stdlib.h>
#include <stdio.h>
#include <errno.h>
#include <string.h>
 
#include <grass/gis.h>
#include <grass/glocale.h>
 
#include "globals.h"
#include "tools.h"


void clean_tmpfiles ( void ) {
	
	int i;
	char tmp[5000];
	static int done = 0;
	
	
	/* make sure this gets only run once */
	if ( done  > 0 ) {
	 return;
  }
	
	done ++;
	
	if ( PROGRESS )
		fprintf ( stdout, "Deleting temporary maps.\n");	
	
	/* clean up temp files: delete temporary maps */
	if ( ( DISTANCE == COST ) && (COSTMODE == ADHOC) ) {
		for ( i=0; i<num_centers; i ++ ) {
			sprintf ( tmp, "g.remove rast=%s", tmapnames[i] );
			if ( !VERBOSE ) {
				strcat ( tmp," --q" );
			}						
			run_cmd ( tmp );			
		}
		if ( make_error ) {
			sprintf ( tmp, "g.remove rast=%s", temapname );
			if ( !VERBOSE ) {
					strcat ( tmp," --q" );
			}		
			run_cmd ( tmp );			
		}		
		/* TODO: check, if all maps were successfully removed */	
	}
	
}

