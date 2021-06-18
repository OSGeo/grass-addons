/*****************************************************************************
*
* MODULE:     i.points.auto
* AUTHOR(S):  based on i.points; additions by 
*              Ivan Michelazzi, Luca Miori (MSc theses at ITC-irst)
*             http://gisws.media.osaka-cu.ac.jp/grass04/viewpaper.php?id=37  
*             Supervisors: Markus Neteler, Stefano Merler, ITC-irst 2003, 2004
*            
* PURPOSE:    semi-automated image registration based in FFT correlation
* COPYRIGHT: GPL >=2
*
*****************************************************************************/

#define GLOBAL
#include <unistd.h>
#include <stdlib.h>
#include <string.h>
#include <signal.h>
#include <grass/gis.h>
#include <grass/raster.h>
#include <grass/glocale.h>
#include "globals.h"
#include "local_proto.h"

#ifdef __GNUC_MINOR__
int quit (int) __attribute__ ((__noreturn__));
#else
int quit (int);
#endif
int error (char *, int);



int main (int argc, char *argv[])
{
    char name[GNAME_MAX], mapset[GMAPSET_MAX];
    struct Cell_head cellhd;
    struct GModule *module;

    G_gisinit (argv[0]);
    module = G_define_module();
    module->description =
	_("Mark or search ground control points on image to be rectified.");

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
	G_fatal_error(_("No graphics device selected"));

    /* temporary parser code: */
    if(argc == 2) {
	strncpy(group.name, argv[1], GNAME_MAX);
	if(group.name[0] == '-')
	    G_fatal_error(_("The parser doesn't work here."));
    }
    else {
	if (!I_ask_group_old (_("Enter imagery group to be registered"), group.name))
	    exit(EXIT_FAILURE);
    }

    if (!I_get_group_ref (group.name, &group.ref))
        G_fatal_error ( _("Group [%s] contains no files"), group.name);

    if (group.ref.nfiles <= 0)
	G_fatal_error ( _( "Group [%s] contains no files"), group.name);

/* write group files to group list file */
    prepare_group_list();
    G_debug(3,"prepare_group_list done");

/* get target info and enviroment */
    get_target();
    find_target_files();
    G_debug(3,"find_target_files done");

/* read group control points, if any */
    G_suppress_warnings(1);
    if (!I_get_control_points (group.name, &group.points))
	group.points.count = 0;
    G_suppress_warnings(0);

/* determine tranformation equation */
    G_debug(3, "starting Compute_equation()");
    Compute_equation();

    signal (SIGINT, SIG_IGN);
/*  signal (SIGQUIT, SIG_IGN); */

    R_standard_color (BLUE);

    Init_graphics();
    display_title (VIEW_MAP1);

    G_debug(3, "select_target_env");
    select_target_env ();
    display_title (VIEW_MAP2);
    select_current_env ();
    G_debug(3, "select_target_env done");

    Begin_curses();
    G_debug(3, "Begin_curses done");
    G_set_error_routine (error);

/*
#ifdef SIGTSTP
    signal (SIGTSTP, SIG_IGN);
#endif
*/

/* ask user for group file to be displayed */
    G_debug(3, "ask user for group file to be displayed");
    do
    {
	if(!choose_groupfile (name, mapset))
	    quit(0);
     
/* display this file in "map1" */
    }
    while (G_get_cellhd (name, mapset, &cellhd) < 0);
    G_adjust_window_to_box (&cellhd, &VIEW_MAP1->cell.head, VIEW_MAP1->nrows, VIEW_MAP1->ncols);
    Configure_view (VIEW_MAP1, name, mapset, cellhd.ns_res, cellhd.ew_res);

    drawcell(VIEW_MAP1);
    display_points(1);
    R_flush();

    Curses_clear_window (PROMPT_WINDOW);

    Erase_view (VIEW_MAP1_ZOOM);          


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

