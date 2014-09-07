/*
****************************************************************************
*
* MODULE:       i.linespoints 
* AUTHOR(S):    Daniel Grasso, Bolzano, Italy
*               based on i.points by Michael Shapiro, U.S.Army CERL
*
* PURPOSE:      An imagery function that enables the user to mark coordinate
*               system points as well as lines on an image to be rectified
*               and then input the coordinates of each point for creation of
*               a coordinate transformation matrix. The transformation
*               matrix is needed as input for the GRASS program i.pr.homolp
* COPYRIGHT:    (C) 2003 by the GRASS Development Team
*
*               This program is free software under the GNU General Public
*   	    	License (>=v2). Read the file COPYING that comes with GRASS
*   	    	for details.
*
*****************************************************************************/

#define GLOBAL
#include <unistd.h>
#include <stdlib.h>
#include <signal.h>
#include "globals.h"
#include "local_proto.h"
#include <grass/raster.h>

#ifdef __GNUC_MINOR__
int quit (int) __attribute__ ((__noreturn__));
#else
int quit (int);
#endif
int error (char *, int);
int main (int argc, char *argv[])
{
    char name[100], mapset[100];
    struct Cell_head cellhd;

    G_gisinit (argv[0]);
    G_suppress_masking();	/* need to do this for target location */

    interrupt_char = G_intr_char();
    tempfile1 = G_tempfile();
    tempfile2 = G_tempfile();
    tempfile3 = G_tempfile();
    cell_list = G_tempfile();
    vect_list = G_tempfile();
    group_list = G_tempfile();
    digit_points = G_tempfile();
    digit_results = G_tempfile();

   if (R_open_driver() != 0)
	G_fatal_error ("No graphics device selected");

    if (!I_ask_group_old ("Enter imagery group to be registered", group.name))
	exit(0);
    if (!I_get_group_ref (group.name, &group.ref))
    {
        fprintf (stderr, "Group [%s] contains no files\n", group.name);
	exit(1);
    }
    if (group.ref.nfiles <= 0)
    {
	fprintf (stderr, "Group [%s] contains no files\n", group.name);
	sleep(3);
	exit(1);
    }
/* write group files to group list file */
    prepare_group_list();

/* get target info and enviroment */
    get_target();
    find_target_files();

/* read group control points, if any */
    G_suppress_warnings(1);
    if (!get_control_points (group.name, &group.points))
	group.points.count = 0;
    G_suppress_warnings(0);

/* determine tranformation equation */
    Compute_equation();


    signal (SIGINT, SIG_IGN);
/*  signal (SIGQUIT, SIG_IGN); */

    Init_graphics();
    display_title (VIEW_MAP1);
    select_target_env ();
    display_title (VIEW_MAP2);
    select_current_env ();

    Begin_curses();
    G_set_error_routine (error);

/*
#ifdef SIGTSTP
    signal (SIGTSTP, SIG_IGN);
#endif
*/


/* ask user for group file to be displayed */
    do
    {
	if(!choose_groupfile (name, mapset))
	    quit(0);
/* display this file in "map1" */
    }
    while (G_get_cellhd (name, mapset, &cellhd) < 0);
    G_adjust_window_to_box (&cellhd, &VIEW_MAP1->cell.head, VIEW_MAP1->nrows, VIEW_MAP1->ncols);
    R_standard_color (BLACK);
    Configure_view (VIEW_MAP1, name, mapset, cellhd.ns_res, cellhd.ew_res);

    drawcell(VIEW_MAP1);
    display_points(1);
    R_flush();

    Curses_clear_window (PROMPT_WINDOW);

    /* control if the image in the left side is in xy projection */

    if ((G_projection() != PROJECTION_XY))
    {
         char msg[256];
         sprintf(msg,"this raster is already georeferenced!\n (not in xy-projection)");
         G_fatal_error (msg);
         exit(1);
    }
/* determine initial input method. */
    setup_digitizer();
    if (use_digitizer)
    {
	from_digitizer = 1;
	from_keyboard  = 0;
	from_flag = 1;
    }

/* go do the work */
    driver();

    quit(0);
}

int quit (int n)
{
    char command[1024];

    End_curses();
    R_close_driver();
    if (use_digitizer)
    {
	sprintf (command, "%s/etc/geo.unlock %s",
	    G_gisbase(), digit_points);
	system (command);
    }
    unlink (tempfile1);
    unlink (tempfile2);
    unlink (tempfile3);
    unlink (cell_list);
    unlink (group_list);
    unlink (vect_list);
    unlink (digit_points);
    unlink (digit_results);
    exit(n);
}

int error (char *msg, int fatal)
{
    char buf[200];
    int x,y,button;

Curses_clear_window (PROMPT_WINDOW);
Curses_write_window (PROMPT_WINDOW,1,1, "LOCATION:\n");
Curses_write_window (PROMPT_WINDOW,1,12,G_location());
Curses_write_window (PROMPT_WINDOW,2,1, "MAPSET:\n");
Curses_write_window (PROMPT_WINDOW,2,12,G_location());
    Beep();
    if (fatal)
	sprintf (buf, "ERROR: %s", msg);
    else
	sprintf (buf, "WARNING: %s (click mouse to continue)", msg);
    Menu_msg (buf);

    if (fatal)
	quit(1);
    Mouse_pointer (&x, &y, &button);
Curses_clear_window (PROMPT_WINDOW);

    return 0;
}

